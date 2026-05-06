from datetime import datetime, timedelta, timezone
import os
from flask import Blueprint, request, jsonify, g
from backend.auth_utils import auth_required
from backend.database import get_db
from backend import config
from models.attendance_model import create_attendance, get_attendance_by_student, get_attendance_by_session, get_attendance_stats
from services.attendance_service import haversine_distance, evaluate_attendance_location

attendance_routes = Blueprint("attendance_routes", __name__)

# Use UTC for server-side time handling; frontend displays IST
UTC = timezone.utc


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

    # Get active session for the lecture (must be currently happening)
    conn = get_db()
    cur = conn.cursor()
    now_utc = datetime.now(UTC).replace(microsecond=0)
    now_iso = now_utc.isoformat()
    cur.execute(
        """
        SELECT id, status, start_time, end_time FROM lecture_sessions
        WHERE lecture_id = ? AND start_time <= ? AND end_time >= ?
        """,
        (lecture_id, now_iso, now_iso),
    )
    session = cur.fetchone()
    if session:
        if session[1] != 'active':
            cur.execute("UPDATE lecture_sessions SET status = 'active' WHERE id = ?", (session[0],))
            conn.commit()
    else:
        conn.close()
        return jsonify({"error": "Lecture has not started yet or already ended"}), 403

    session_id = session[0]
    session_end_time = session[3]
    conn.close()

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

    # Mark attendance with current UTC time and session end time for duration
    current_utc = datetime.now(UTC).replace(microsecond=0).isoformat()
    attendance_id = create_attendance(
        student_id,
        session_id,
        latitude,
        longitude,
        "present",
        current_utc,
        end_time=session_end_time,
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

    # Verify session exists and get times
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

    # CRITICAL: Validate attendance time window
    session_id_val, session_start_time, session_end_time, session_status = session
    now = datetime.now(UTC)
    
    try:
        # Parse session times
        if isinstance(session_start_time, str):
            start_dt = datetime.fromisoformat(session_start_time)
        else:
            start_dt = session_start_time
            
        if isinstance(session_end_time, str):
            end_dt = datetime.fromisoformat(session_end_time)
        else:
            end_dt = session_end_time
        
        # Make timezone-aware if needed (assume stored times are UTC)
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=UTC)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=UTC)
        
        # STRICT TIME VALIDATION: Prevent marking after session end, but allow marking before start
        if now > end_dt:
            return jsonify({"error": "Lecture has ended. Attendance can no longer be marked."}), 403
    except Exception as e:
        print(f"ERROR: Time validation failed - {e}")
        return jsonify({"error": "Invalid session times"}), 400

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
    if status == "present":
        try:
            late_threshold = start_dt.replace(microsecond=0) + timedelta(minutes=15)
            if now > late_threshold:
                status = "late"
        except:
            pass

    # Use session end_time if not provided by client
    if not end_time:
        end_time = session_end_time

    # Record attendance with current UTC timestamp
    current_utc = datetime.now(UTC).replace(microsecond=0).isoformat()
    attendance_id = create_attendance(
        student_id,
        session_id,
        None,  # No latitude for offline
        None,  # No longitude for offline
        status,
        current_utc,
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


@attendance_routes.route("/api/attendance/live/<int:session_id>", methods=["GET"])
@auth_required(role="faculty")
def attendance_live(session_id):
    """
    Real-time attendance report for ongoing lectures.
    Returns attendance data for all students in the session with live updates.
    """
    try:
        # Verify session exists and belongs to faculty
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, faculty_id, start_time, end_time, status FROM lecture_sessions WHERE id = ?",
            (session_id,)
        )
        session = cur.fetchone()
        
        if not session:
            conn.close()
            return jsonify({"error": "Session not found"}), 404
        
        # Verify faculty owns this session
        if session["faculty_id"] != g.user_id:
            conn.close()
            return jsonify({"error": "Unauthorized"}), 403
        
        # Get current time in UTC (server) and interpret stored session end as UTC
        now = datetime.now(UTC)
        session_end = datetime.fromisoformat(session["end_time"])
        if session_end.tzinfo is None:
            session_end = session_end.replace(tzinfo=UTC)
        
        # Check if lecture is still active
        is_active = now <= session_end
        
        # Get all attendance records for this session (live data)
        cur.execute("""
            SELECT 
                a.id,
                a.student_id,
                s.roll_number,
                u.name as student_name,
                a.status,
                a.timestamp as join_time,
                a.end_time as exit_time
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            JOIN users u ON s.user_id = u.id
            WHERE a.session_id = ?
            ORDER BY a.timestamp DESC
        """, (session_id,))
        
        records = []
        for row in cur.fetchall():
            join_time_str = row["join_time"]
            exit_time_str = row["exit_time"]

            # Calculate real-time duration if student hasn't exited yet
            if row["status"] in ["present", "late"] and not exit_time_str:
                join_time = datetime.fromisoformat(join_time_str)
                if join_time.tzinfo is None:
                    join_time = join_time.replace(tzinfo=UTC)
                duration = int((now - join_time).total_seconds() / 60)
            else:
                # If student has exit time, calculate duration
                if join_time_str and exit_time_str:
                    join_time = datetime.fromisoformat(join_time_str)
                    exit_time = datetime.fromisoformat(exit_time_str)
                    if join_time.tzinfo is None:
                        join_time = join_time.replace(tzinfo=UTC)
                    if exit_time.tzinfo is None:
                        exit_time = exit_time.replace(tzinfo=UTC)
                    duration = int((exit_time - join_time).total_seconds() / 60)
                else:
                    duration = 0
            
            records.append({
                "id": row["id"],
                "student_id": row["student_id"],
                "roll_number": row["roll_number"],
                "student_name": row["student_name"],
                "status": row["status"],
                "join_time": join_time_str,
                "exit_time": exit_time_str,
                "duration_minutes": duration or 0
            })
        
        conn.close()
        
        return jsonify({
            "session_id": session_id,
            "is_active": is_active,
            "current_time": now.isoformat(),
            "session_end_time": session["end_time"],
            "report": records,
            "total_marked": len(records),
            "present_count": sum(1 for r in records if r["status"] in ["present", "late"]),
            "late_count": sum(1 for r in records if r["status"] == "late"),
            "absent_count": sum(1 for r in records if r["status"] == "absent")
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

