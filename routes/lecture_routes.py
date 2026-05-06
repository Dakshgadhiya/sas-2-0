from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, g
from backend.auth_utils import auth_required
from backend.database import get_db
from models.lecture_model import create_lecture, create_session, get_active_session, list_sessions
from models.user_model import get_all_students
from models.notifications_model import create_notification
import json
import os


def _log_debug(msg):
    try:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
        path = os.path.join(base, 'debug_logs.txt')
        with open(path, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    except Exception:
        pass

lecture_routes = Blueprint("lecture_routes", __name__)

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))
UTC = timezone.utc


def _parse_iso(dt_str):
    # Accept datetime objects directly
    if isinstance(dt_str, datetime):
        return dt_str
    if not isinstance(dt_str, str):
        return None
    s = dt_str.strip()
    # Normalize trailing Z to +00:00 for fromisoformat
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'
    try:
        return datetime.fromisoformat(s)
    except Exception as e:
        # Try known strptime formats as fallback
        from datetime import datetime as _dt
        fmts = ["%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"]
        for f in fmts:
            try:
                return _dt.strptime(s, f)
            except Exception:
                continue
        # last-resort: try trimming fractional seconds
        try:
            if '.' in s:
                parts = s.split('.')
                base = parts[0]
                return datetime.fromisoformat(base)
        except Exception:
            pass
        print(f"DEBUG: Failed to parse datetime '{dt_str}': {e}")
        return None


def _normalize_mode(mode):
    if not mode:
        return "ONLINE"
    mode = mode.upper()
    return mode if mode in ["ONLINE", "OFFLINE"] else "ONLINE"


@lecture_routes.route("/api/lectures/sessions", methods=["POST"])
@auth_required(role="faculty")
def create_lecture_session():
    data = request.json or {}
    title = data.get("lecture_title")
    subject = data.get("subject")
    date = data.get("date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    semester = data.get("semester") or "1"
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    radius = data.get("radius")

    if not all([title, subject, date, start_time, end_time]):
        return jsonify({"error": "Missing fields"}), 400

    # Validate that faculty teaches this semester and get available subjects
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT semester FROM faculty_subjects WHERE faculty_id = (
            SELECT id FROM faculty WHERE user_id = ?
        )
    """, (g.user_id,))
    rows = cur.fetchall()
    faculty_semesters = [str(row[0]) for row in rows]
    had_assignments = len(faculty_semesters) > 0
    conn.close()

    if not faculty_semesters:
        faculty_semesters = ["1"]

    auto_assigned = False
    if str(semester) not in faculty_semesters:
        # Only auto-add if the faculty currently has NO assignments (helpful default)
        if had_assignments:
            return jsonify({"error": f"You are not authorized to teach semester {semester}. Your semesters: {', '.join(faculty_semesters)}"}), 403
        try:
            conn2 = get_db()
            cur2 = conn2.cursor()
            cur2.execute("SELECT id FROM faculty WHERE user_id = ?", (g.user_id,))
            frow = cur2.fetchone()
            if frow:
                faculty_db_id = frow[0]
                cur2.execute(
                    "INSERT OR IGNORE INTO faculty_subjects (faculty_id, semester, subject) VALUES (?, ?, ?)",
                    (faculty_db_id, semester, subject or 'General')
                )
                conn2.commit()
                auto_assigned = True
                # reflect change locally
                faculty_semesters.append(str(semester))
            conn2.close()
        except Exception:
            return jsonify({"error": f"You are not authorized to teach semester {semester}. Your semesters: {', '.join(faculty_semesters)}"}), 403

    # Validate start and end times
    print(f"DEBUG: Parsing times - start_time: {start_time}, end_time: {end_time}")
    start_dt = _parse_iso(start_time)
    end_dt = _parse_iso(end_time)
    
    if not start_dt or not end_dt:
        print(f"DEBUG: Time parsing failed - start_dt: {start_dt}, end_dt: {end_dt}")
        return jsonify({
            "error": f"Invalid start_time or end_time format. Expected ISO format (YYYY-MM-DDTHH:MM:SS). Got: start_time='{start_time}', end_time='{end_time}'"
        }), 400
    
    # Normalize to timezone-aware UTC datetimes for safe comparison
    try:
        _log_debug(f"DEBUG: pre-normalize start_dt={repr(start_dt)} ({type(start_dt)}), end_dt={repr(end_dt)} ({type(end_dt)})")
        if start_dt is None or end_dt is None:
            raise ValueError("Invalid start or end datetime")

        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=UTC)
        else:
            start_dt = start_dt.astimezone(UTC)

        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=UTC)
        else:
            end_dt = end_dt.astimezone(UTC)

        _log_debug(f"DEBUG: post-normalize start_dt={repr(start_dt)} tz={start_dt.tzinfo}, end_dt={repr(end_dt)} tz={end_dt.tzinfo}")
    except Exception as e:
        _log_debug(f"DEBUG: Time parsing failed - start_dt: {start_dt}, end_dt: {end_dt}, error: {e}")
        return jsonify({
            "error": f"Invalid start_time or end_time format. Expected ISO format (YYYY-MM-DDTHH:MM:SS). Got: start_time='{start_time}', end_time='{end_time}'"
        }), 400

    # Validate that end_time is after start_time
    if end_dt <= start_dt:
        return jsonify({"error": "End time must be after start time"}), 400

    lecture_id = create_lecture(title, subject, date, g.user_id, latitude, longitude, radius)
    # Use UTC for status checks
    now = datetime.now(UTC)
    status = "scheduled"
    if start_dt <= now <= end_dt:
        status = "active"
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO lecture_sessions (lecture_id, start_time, end_time, attendance_type, threshold, status, mode, join_url, semester)
        VALUES (?, ?, ?, 'LOCATION', 0, ?, 'OFFLINE', '', ?)
    """, (lecture_id, start_time, end_time, status, semester))
    conn.commit()
    session_id = cur.lastrowid
    
    # Send notifications to all students of this semester
    cur.execute("""
        SELECT id FROM students WHERE semester = ?
    """, (semester,))
    students = cur.fetchall()
    conn.close()
    
    # Create notification for each student
    notification_message = f"New lecture scheduled: {subject} at {start_time}"
    for student_row in students:
        student_id = student_row[0]
        create_notification(
            student_id,
            notification_message,
            type_='info',
            related_session_id=session_id
        )
    
    return jsonify({
        "session_id": session_id,
        "status": status,
        "notifications_sent": len(students)
    })


@lecture_routes.route("/api/lectures/sessions/active", methods=["GET"])
@auth_required()
def active_session():
    """Get only currently active sessions (for marking attendance)"""
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    mode = request.args.get("mode")
    
    # Students should only see active sessions for their semester
    student_semester = None
    if g.role == "student":
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT semester FROM students WHERE user_id = ?", (g.user_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            student_semester = row[0]
    
    session = get_active_session(now, mode=mode.upper() if mode else None, student_semester=student_semester)
    if not session:
        return jsonify({"active": False})
    return jsonify({"active": True, "session": session})


@lecture_routes.route("/api/lectures/sessions", methods=["GET"])
@auth_required()
def list_all_sessions():
    mode = request.args.get("mode")
    # Faculty members only see their own lectures
    # Students see only lectures for their semester
    faculty_id = g.user_id if g.role == "faculty" else None
    student_semester = None
    
    if g.role == "student":
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT semester FROM students WHERE user_id = ?", (g.user_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            student_semester = row[0]
    
    # Include closed sessions so students can see past lectures
    return jsonify({"sessions": list_sessions(mode=mode.upper() if mode else None, include_closed=True, faculty_id=faculty_id, student_semester=student_semester)})


@lecture_routes.route("/api/faculty/summary", methods=["GET"])
@auth_required(role="faculty")
def faculty_summary():
    conn = get_db()
    cur = conn.cursor()
    
    # Count all registered students (not just those who attended)
    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]
    
    # Count today's attendance for THIS faculty's lectures only
    today = datetime.now().date().isoformat()
    cur.execute("""
        SELECT COUNT(*) FROM attendance a
        JOIN lecture_sessions ls ON ls.id = a.session_id
        JOIN lectures l ON l.id = ls.lecture_id
        WHERE l.date = ? AND a.status = 'present' AND l.faculty_id = ?
    """, (today, g.user_id))
    today_attendance = cur.fetchone()[0]
    
    # Count THIS faculty's lecture sessions only
    cur.execute("SELECT COUNT(*) FROM lecture_sessions ls JOIN lectures l ON l.id = ls.lecture_id WHERE l.faculty_id = ?", (g.user_id,))
    total_sessions = cur.fetchone()[0]
    
    conn.close()
    return jsonify({
        "total_students": total_students,
        "today_attendance": today_attendance,
        "total_sessions": total_sessions
    })


@lecture_routes.route("/api/admin/students", methods=["GET"])
@auth_required(role="faculty")
def get_students():
    students = get_all_students()
    return jsonify(students)


@lecture_routes.route("/api/students", methods=["GET"])
@auth_required()
def list_students():
    """Get all students with their details"""
    students = get_all_students()
    return jsonify({"students": students})


@lecture_routes.route("/api/faculty/list", methods=["GET"])
@auth_required()
def get_faculty_list():
    """Get all faculty members with their department and teaching assignments"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            u.id,
            u.name,
            u.email,
            f.id,
            f.faculty_id,
            f.department
        FROM users u
        LEFT JOIN faculty f ON u.id = f.user_id
        WHERE u.role = 'faculty'
        ORDER BY u.name ASC
    """)
    rows = cur.fetchall()
    
    faculty_list = []
    for row in rows:
        user_id = row[0]
        faculty_db_id = row[3]
        
        # Get teaching assignments for this faculty
        cur.execute("""
            SELECT semester, subject FROM faculty_subjects WHERE faculty_id = ? ORDER BY semester
        """, (faculty_db_id,))
        subjects = [{"semester": s[0], "subject": s[1]} for s in cur.fetchall()]
        
        faculty_list.append({
            "id": user_id,
            "name": row[1],
            "email": row[2],
            "faculty_id": row[4],
            "department": row[5] or "General",
            "teaching_assignments": subjects
        })
    
    conn.close()
    return jsonify({"faculty": faculty_list})


@lecture_routes.route("/api/admin/clear-lectures", methods=["DELETE"])
@auth_required(role="faculty")
def clear_all_lectures():
    """Delete all lectures and related attendance records - ADMIN ONLY"""
    conn = get_db()
    cur = conn.cursor()
    try:
        # Delete attendance records first (foreign key constraint)
        cur.execute("DELETE FROM attendance")
        # Delete lecture sessions
        cur.execute("DELETE FROM lecture_sessions")
        # Delete lectures
        cur.execute("DELETE FROM lectures")
        conn.commit()
        conn.close()
        return jsonify({"message": "All lectures and attendance records deleted successfully"}), 200
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


@lecture_routes.route("/api/faculty/profile", methods=["GET"])
@auth_required(role="faculty")
def get_faculty_profile():
    """Get current faculty member's profile"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.id, u.name, u.email, f.faculty_id, f.subject, f.semesters
        FROM users u
        LEFT JOIN faculty f ON u.id = f.user_id
        WHERE u.id = ?
        LIMIT 1
    """, (g.user_id,))
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"error": "Faculty profile not found"}), 404
    
    semesters_json = row[5] or "1"
    try:
        semesters = json.loads(semesters_json)
    except:
        semesters = [1]
    
    profile = {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "faculty_id": row[3] or "",
        "subject": row[4] or "",
        "semesters": semesters
    }
    return jsonify({"profile": profile})


@lecture_routes.route("/api/faculty/profile", methods=["PUT"])
@auth_required(role="faculty")
def update_faculty_profile():
    """Update faculty profile (name, email, subject, semesters)"""
    data = request.json or {}
    name = data.get("name")
    email = data.get("email")
    faculty_id = data.get("faculty_id")
    subject = data.get("subject")
    semesters = data.get("semesters")  # Array of semesters
    
    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Update user info (name, email)
        cur.execute("""
            UPDATE users SET name = ?, email = ? WHERE id = ?
        """, (name, email, g.user_id))
        
        # Update subject and semesters in faculty table
        if subject is not None:
            cur.execute("""
                UPDATE faculty SET subject = ? WHERE user_id = ?
            """, (subject, g.user_id))
            
            # Also update subject in existing lectures
            cur.execute("""
                UPDATE lectures SET subject = ? WHERE faculty_id = ?
            """, (subject, g.user_id))
        
        if semesters is not None:
            semesters_json = json.dumps(semesters)
            cur.execute("""
                UPDATE faculty SET semesters = ? WHERE user_id = ?
            """, (semesters_json, g.user_id))
        
        conn.commit()
        conn.close()
        return jsonify({"message": "Profile updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
