from datetime import datetime, timedelta
import os
from flask import Blueprint, request, jsonify, g
from backend.auth_utils import auth_required
from backend.database import get_db
from backend import config
from models.attendance_model import create_attendance, get_attendance_by_student, get_attendance_by_session, get_attendance_stats
from services.attendance_service import haversine_distance, evaluate_attendance_location

attendance_routes = Blueprint("attendance_routes", __name__)


def get_student_id(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM students WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def get_attendance_row(student_id, session_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM attendance WHERE student_id = ? AND session_id = ?",
        (student_id, session_id),
    )
    row = cur.fetchone()
    conn.close()
    return row



@attendance_routes.route("/api/attendance/mark-location", methods=["POST"])
@auth_required(role="student")
def mark_location_attendance():
    data = request.json or {}
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    lecture_id = data.get("lecture_id")

    if not all([latitude, longitude, lecture_id]):
        return jsonify({"error": "latitude, longitude, and lecture_id required"}), 400

    # Get lecture location
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT latitude, longitude, radius FROM lectures WHERE id = ?", (lecture_id,))
    lecture = cur.fetchone()
    conn.close()

    if not lecture or lecture[0] is None or lecture[1] is None or lecture[2] is None:
        return jsonify({"error": "Lecture location not set"}), 400

    lecture_lat, lecture_lon, radius = lecture

    # Calculate distance
    distance = haversine_distance(latitude, longitude, lecture_lat, lecture_lon)

    # Check if within radius
    if not evaluate_attendance_location(distance, radius):
        return jsonify({"error": "You are not within the classroom location."}), 403

    # Get active session for the lecture
    conn = get_db()
    cur = conn.cursor()
    now_iso = datetime.now().replace(microsecond=0).isoformat()
    cur.execute(
        """
        SELECT id, status FROM lecture_sessions
        WHERE lecture_id = ? AND start_time <= ? AND end_time >= ?
        """,
        (lecture_id, now_iso, now_iso),
    )
    session = cur.fetchone()
    if session and session[1] != 'active':
        cur.execute("UPDATE lecture_sessions SET status = 'active' WHERE id = ?", (session[0],))
        conn.commit()
    conn.close()

    if not session:
        return jsonify({"error": "No active session for this lecture"}), 400

    session_id = session[0]

    student_id = get_student_id(g.user_id)
    if student_id is None:
        return jsonify({"error": "Student not found"}), 404

    # Check if already marked
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM attendance WHERE student_id = ? AND session_id = ?",
        (student_id, session_id),
    )
    existing = cur.fetchone()
    conn.close()

    if existing:
        return jsonify({"status": "already_marked"}), 409

    # Mark attendance
    attendance_id = create_attendance(
        student_id,
        session_id,
        latitude,
        longitude,
        "present",
        datetime.utcnow().isoformat(),
    )

    return jsonify({"attendance_id": attendance_id, "status": "present"})


@attendance_routes.route("/api/attendance/mark", methods=["POST"])
@auth_required(role="student")
def mark_attendance():
    """Mark attendance for offline lectures with optional start/end times and status"""
    data = request.json or {}
    session_id = data.get("session_id")
    status = data.get("status", "present").lower()  # present, absent, or late
    start_time = data.get("start_time")
    end_time = data.get("end_time")

    if not session_id:
        return jsonify({"error": "session_id required"}), 400
    
    if status not in ["present", "absent", "late"]:
        return jsonify({"error": "status must be 'present', 'absent', or 'late'"}), 400

    student_id = get_student_id(g.user_id)
    if student_id is None:
        return jsonify({"error": "Student not found"}), 404

    # Verify session exists
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT ls.id, ls.start_time, ls.end_time, ls.status FROM lecture_sessions ls
        WHERE ls.id = ?
    """, (session_id,))
    session = cur.fetchone()
    conn.close()

    if not session:
        return jsonify({"error": "Session not found"}), 400

    # Check if already marked
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM attendance WHERE student_id = ? AND session_id = ?",
        (student_id, session_id),
    )
    existing = cur.fetchone()
    conn.close()

    if existing:
        return jsonify({"status": "already_marked"}), 409

    # Determine if late (marked after 15 minutes from session start time)
    session_start_time = session[1]
    session_end_time = session[2]  # Get session end_time
    now = datetime.now()
    current_iso = now.isoformat()
    
    if status == "present":
        try:
            session_start_dt = datetime.fromisoformat(session_start_time)
            # Calculate 15 minutes after session start
            late_threshold = session_start_dt.replace(microsecond=0) + timedelta(minutes=15)
            
            # If current time is after the 15-minute threshold, mark as late
            if now > late_threshold:
                status = "late"
        except:
            pass

    # Use session end_time if not provided by client
    if not end_time and session_end_time:
        end_time = session_end_time

    # Mark attendance with timestamps
    attendance_id = create_attendance(
        student_id,
        session_id,
        None,  # No latitude for offline
        None,  # No longitude for offline
        status,
        current_iso,
        start_time=start_time,
        end_time=end_time
    )

    return jsonify({"attendance_id": attendance_id, "status": status})


@attendance_routes.route("/api/attendance/history", methods=["GET"])
@auth_required(role="student")
def attendance_history():
    student_id = get_student_id(g.user_id)
    rows = get_attendance_by_student(student_id)
    return jsonify({"history": rows})


@attendance_routes.route("/api/attendance/stats", methods=["GET"])
@auth_required(role="student")
def attendance_stats():
    student_id = get_student_id(g.user_id)
    total, attended = get_attendance_stats(student_id)
    percentage = (attended / total * 100) if total > 0 else 0
    return jsonify({"total_lectures": total, "lectures_attended": attended, "attendance_percentage": percentage})


@attendance_routes.route("/api/attendance/report/<int:session_id>", methods=["GET"])
@auth_required(role="faculty")
def attendance_report(session_id):
    # Verify this session belongs to the current faculty
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT l.faculty_id FROM lecture_sessions ls
        JOIN lectures l ON l.id = ls.lecture_id
        WHERE ls.id = ?
    """, (session_id,))
    result = cur.fetchone()
    conn.close()
    
    if not result:
        return jsonify({"error": "Session not found"}), 404
    
    faculty_id = result[0]
    if faculty_id != g.user_id:
        return jsonify({"error": "Unauthorized - this lecture is not yours"}), 403
    
    rows = get_attendance_by_session(session_id)
    return jsonify({"report": rows})


@attendance_routes.route("/api/attendance/status/<int:session_id>", methods=["GET"])
@auth_required(role="student")
def attendance_status(session_id):
    student_id = get_student_id(g.user_id)
    if student_id is None:
        return jsonify({"error": "Student not found"}), 404
    row = get_attendance_row(student_id, session_id)
    if not row:
        return jsonify({"marked": False})
    return jsonify({"marked": True, "status": row["status"]})
