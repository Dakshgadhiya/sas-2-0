import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from backend.auth_utils import hash_password, verify_password, generate_token
from backend.database import get_db, row_to_dict
from backend import config
from models.user_model import create_user, get_user_by_email, get_user_by_id, delete_user
from models.faculty_model import create_faculty, get_faculty_by_user_id
from models.attendance_model import (
    create_attendance,
    get_attendance_by_student,
    get_attendance_by_session,
    get_attendance_stats,
)
from models.lecture_model import create_lecture, get_active_session, list_sessions
from models.notifications_model import create_notification
from services.attendance_service import haversine_distance, evaluate_attendance_location
from api.common import (
    auth_required,
    error_response,
    get_query_param,
    json_response,
    parse_json,
    get_path,
)

UTC = timezone.utc


def _normalize_role(role: Optional[str]) -> str:
    return (role or "").strip().lower()


def get_student_id(user_id: int) -> Optional[int]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM students WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def get_faculty_db_id(user_id: int) -> Optional[int]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM faculty WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def register(request: Any) -> Dict[str, Any]:
    data = parse_json(request) or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = _normalize_role(data.get("role", "student"))

    if not name or not email or not password or role not in ["student", "faculty"]:
        return error_response("Invalid payload", 400)

    existing_user = get_user_by_email(email)
    if existing_user:
        return error_response("Email already registered. Please login.", 409)

    user_id = create_user(name, email, hash_password(password), role)

    if role == "student":
        enrollment_number = data.get("enrollment_number") or data.get("roll_number")
        department = data.get("department") or "Information Technology"
        semester = data.get("semester") or "1"
        if not enrollment_number:
            delete_user(user_id)
            return error_response("Enrollment number is required", 400)

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO students (user_id, roll_number, department, semester) VALUES (?, ?, ?, ?)",
                (user_id, enrollment_number, department, semester),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()
            return error_response("Enrollment number already exists", 409)
        finally:
            try:
                conn.close()
            except Exception:
                pass

    if role == "faculty":
        faculty_id = data.get("faculty_id")
        subjects = data.get("subjects") or []
        if not subjects and data.get("subject") and data.get("semesters"):
            try:
                legacy_semesters = data.get("semesters") or []
                subjects = [{"semester": str(s), "subject": data.get("subject")} for s in legacy_semesters]
            except Exception:
                subjects = []

        department = data.get("department") or "Information Technology"
        if not faculty_id:
            delete_user(user_id)
            return error_response("Faculty ID is required", 400)

        for subj in subjects:
            semester = subj.get("semester", "1")
            sem_num = int(semester) if isinstance(semester, str) and semester.isdigit() else 1
            if sem_num % 2 == 1:
                if sem_num not in [1, 3, 5]:
                    delete_user(user_id)
                    return error_response(f"Invalid odd semester: {semester}", 400)
            else:
                if sem_num not in [2, 4, 6]:
                    delete_user(user_id)
                    return error_response(f"Invalid even semester: {semester}", 400)

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO faculty (user_id, faculty_id, department) VALUES (?, ?, ?)",
                (user_id, faculty_id, department),
            )
            faculty_db_id = cur.lastrowid

            for subj in subjects:
                semester = subj.get("semester", "1")
                subject = subj.get("subject", "General")
                cur.execute(
                    "INSERT OR IGNORE INTO faculty_subjects (faculty_id, semester, subject) VALUES (?, ?, ?)",
                    (faculty_db_id, semester, subject),
                )

            try:
                cur.execute("PRAGMA table_info(faculty)")
                cols = [r[1] for r in cur.fetchall()]
                if "subject" in cols and data.get("subject"):
                    cur.execute("UPDATE faculty SET subject = ? WHERE id = ?", (data.get("subject"), faculty_db_id))
            except Exception:
                pass

            conn.commit()
            conn.close()
        except Exception:
            delete_user(user_id)
            return error_response("Faculty ID already exists", 409)

    token = generate_token(user_id, role)
    return json_response({"token": token, "user_id": user_id, "role": role})


def login(request: Any) -> Dict[str, Any]:
    data = parse_json(request) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return error_response("Email and password required", 400)

    user = get_user_by_email(email)
    if not user or not verify_password(password, user["password"]):
        return error_response("Invalid credentials", 401)

    role = (user.get("role") or "").lower()
    token = generate_token(user["id"], role)
    return json_response({"token": token, "user": {"id": user["id"], "name": user["name"], "role": role}})


def me(request: Any) -> Dict[str, Any]:
    payload, error = auth_required(request)
    if error:
        return error

    user = get_user_by_id(payload["sub"])
    if user and "role" in user:
        user["role"] = (user["role"] or "").lower()
    return json_response({"user": user})


def student_profile_get(request: Any) -> Dict[str, Any]:
    payload, error = auth_required(request, role="student")
    if error:
        return error

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT roll_number, department, semester FROM students WHERE user_id = ?",
        (payload["sub"],),
    )
    student_row = cur.fetchone()
    conn.close()

    if not student_row:
        return error_response("Student record not found", 404)

    user = get_user_by_id(payload["sub"])
    profile = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "roll_number": student_row[0],
        "department": student_row[1],
        "semester": student_row[2],
    }
    return json_response({"profile": profile})


def student_profile_put(request: Any) -> Dict[str, Any]:
    payload, error = auth_required(request, role="student")
    if error:
        return error

    data = parse_json(request) or {}
    updates = []
    params = []

    if "name" in data:
        updates.append("name = ?")
        params.append(data["name"])
    if "email" in data:
        updates.append("email = ?")
        params.append(data["email"])

    if not updates:
        return json_response({"message": "Nothing to update"})

    params.append(payload["sub"])
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", tuple(params))
    conn.commit()
    conn.close()
    return json_response({"message": "Profile updated successfully"})


def faculty_profile_get(request: Any) -> Dict[str, Any]:
    payload, error = auth_required(request, role="faculty")
    if error:
        return error

    user = get_user_by_id(payload["sub"])
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, faculty_id, department FROM faculty WHERE user_id = ?", (payload["sub"],))
    faculty_row = cur.fetchone()
    if not faculty_row:
        conn.close()
        return error_response("Faculty record not found", 404)

    faculty_id_db, faculty_id, department = faculty_row
    cur.execute(
        "SELECT semester, subject FROM faculty_subjects WHERE faculty_id = ? ORDER BY semester",
        (faculty_id_db,),
    )
    subjects = [{"semester": row[0], "subject": row[1]} for row in cur.fetchall()]
    conn.close()

    profile = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "faculty_id": faculty_id,
        "department": department,
        "subjects": subjects,
    }
    return json_response({"profile": profile})


def mark_location_attendance(request: Any) -> Dict[str, Any]:
    payload, error = auth_required(request, role="student")
    if error:
        return error

    data = parse_json(request) or {}
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    lecture_id = data.get("lecture_id")

    if not all([latitude, longitude, lecture_id]):
        return error_response("latitude, longitude, and lecture_id required", 400)

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT latitude, longitude, radius FROM lectures WHERE id = ?", (lecture_id,))
    lecture = cur.fetchone()
    conn.close()

    if not lecture or lecture[0] is None or lecture[1] is None or lecture[2] is None:
        return error_response("Lecture location not set", 400)

    lecture_lat, lecture_lon, radius = lecture
    distance = haversine_distance(latitude, longitude, lecture_lat, lecture_lon)
    if not evaluate_attendance_location(distance, radius):
        return error_response("You are not within the classroom location.", 403)

    conn = get_db()
    cur = conn.cursor()
    now_utc = datetime.now(UTC).replace(microsecond=0).isoformat()
    cur.execute(
        """
        SELECT id, status, start_time, end_time FROM lecture_sessions
        WHERE lecture_id = ? AND start_time <= ? AND end_time >= ?
        """,
        (lecture_id, now_utc, now_utc),
    )
    session = cur.fetchone()
    if session and session[1] != "active":
        cur.execute("UPDATE lecture_sessions SET status = 'active' WHERE id = ?", (session[0],))
        conn.commit()
    conn.close()

    if not session:
        return error_response("Lecture has not started yet or already ended", 403)

    session_id = session[0]
    session_end_time = session[3]
    student_id = get_student_id(payload["sub"])
    if student_id is None:
        return error_response("Student not found", 404)

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM attendance WHERE student_id = ? AND session_id = ?",
        (student_id, session_id),
    )
    existing = cur.fetchone()
    conn.close()
    if existing:
        return error_response("already_marked", 409)

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

    return json_response({"attendance_id": attendance_id, "status": "present"})


def mark_attendance(request: Any) -> Dict[str, Any]:
    payload, error = auth_required(request, role="student")
    if error:
        return error

    data = parse_json(request) or {}
    session_id = data.get("session_id")
    status = (data.get("status", "present") or "present").lower()
    start_time = data.get("start_time")
    end_time = data.get("end_time")

    if not session_id:
        return error_response("session_id required", 400)
    if status not in ["present", "absent", "late"]:
        return error_response("status must be 'present', 'absent', or 'late'", 400)

    student_id = get_student_id(payload["sub"])
    if student_id is None:
        return error_response("Student not found", 404)

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT ls.id, ls.start_time, ls.end_time, ls.status FROM lecture_sessions ls WHERE ls.id = ?",
        (session_id,),
    )
    session = cur.fetchone()
    conn.close()

    if not session:
        return error_response("Session not found", 400)

    session_start_time = session[1]
    session_end_time = session[2]

    try:
        start_dt = datetime.fromisoformat(session_start_time) if isinstance(session_start_time, str) else session_start_time
        end_dt = datetime.fromisoformat(session_end_time) if isinstance(session_end_time, str) else session_end_time
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=UTC)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=UTC)
        now = datetime.now(UTC)
        if now > end_dt:
            return error_response("Lecture has ended. Attendance can no longer be marked.", 403)
    except Exception:
        return error_response("Invalid session times", 400)

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM attendance WHERE student_id = ? AND session_id = ?",
        (student_id, session_id),
    )
    existing = cur.fetchone()
    conn.close()
    if existing:
        return error_response("already_marked", 409)

    if status == "present":
        try:
            late_threshold = start_dt.replace(microsecond=0) + timedelta(minutes=15)
            if datetime.now(UTC) > late_threshold:
                status = "late"
        except Exception:
            pass

    if not end_time:
        end_time = session_end_time

    current_utc = datetime.now(UTC).replace(microsecond=0).isoformat()
    attendance_id = create_attendance(
        student_id,
        session_id,
        None,
        None,
        status,
        current_utc,
        start_time=start_time,
        end_time=end_time,
    )

    return json_response({"attendance_id": attendance_id, "status": status})


def attendance_history(request: Any) -> Dict[str, Any]:
    payload, error = auth_required(request, role="student")
    if error:
        return error

    student_id = get_student_id(payload["sub"])
    if student_id is None:
        return error_response("Student not found", 404)
    rows = get_attendance_by_student(student_id)
    return json_response({"history": rows})


def attendance_stats(request: Any) -> Dict[str, Any]:
    payload, error = auth_required(request, role="student")
    if error:
        return error

    student_id = get_student_id(payload["sub"])
    if student_id is None:
        return error_response("Student not found", 404)

    total, attended = get_attendance_stats(student_id)
    percentage = (attended / total * 100) if total > 0 else 0
    return json_response({"total_lectures": total, "lectures_attended": attended, "attendance_percentage": percentage})


def attendance_report(request: Any, session_id: str) -> Dict[str, Any]:
    payload, error = auth_required(request, role="faculty")
    if error:
        return error

    try:
        session_id_int = int(session_id)
    except ValueError:
        return error_response("Invalid session id", 400)

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT l.faculty_id FROM lecture_sessions ls
        JOIN lectures l ON l.id = ls.lecture_id
        WHERE ls.id = ?
        """,
        (session_id_int,),
    )
    result = cur.fetchone()
    conn.close()

    if not result:
        return error_response("Session not found", 404)

    if result[0] != payload["sub"]:
        return error_response("Forbidden", 403)

    rows = get_attendance_by_session(session_id_int)
    return json_response({"report": rows})


def create_lecture_session(request: Any) -> Dict[str, Any]:
    payload, error = auth_required(request, role="faculty")
    if error:
        return error

    data = parse_json(request) or {}
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
        return error_response("Missing fields", 400)

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT semester FROM faculty_subjects WHERE faculty_id = (
            SELECT id FROM faculty WHERE user_id = ?
        )
        """,
        (payload["sub"],),
    )
    rows = cur.fetchall()
    faculty_semesters = [str(row[0]) for row in rows]
    had_assignments = len(faculty_semesters) > 0
    conn.close()

    if not faculty_semesters:
        faculty_semesters = ["1"]
    auto_assigned = False
    if str(semester) not in faculty_semesters:
        if had_assignments:
            return error_response(
                f"You are not authorized to teach semester {semester}. Your semesters: {', '.join(faculty_semesters)}",
                403,
            )
        try:
            conn2 = get_db()
            cur2 = conn2.cursor()
            cur2.execute("SELECT id FROM faculty WHERE user_id = ?", (payload["sub"],))
            frow = cur2.fetchone()
            if frow:
                faculty_db_id = frow[0]
                cur2.execute(
                    "INSERT OR IGNORE INTO faculty_subjects (faculty_id, semester, subject) VALUES (?, ?, ?)",
                    (faculty_db_id, semester, subject or "General"),
                )
                conn2.commit()
                auto_assigned = True
                faculty_semesters.append(str(semester))
            conn2.close()
        except Exception:
            return error_response(
                f"You are not authorized to teach semester {semester}. Your semesters: {', '.join(faculty_semesters)}",
                403,
            )

    def _parse_iso(dt_str: Any):
        if isinstance(dt_str, datetime):
            return dt_str
        if not isinstance(dt_str, str):
            return None
        s = dt_str.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(s)
        except Exception:
            from datetime import datetime as _dt
            fmts = [
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S",
            ]
            for f in fmts:
                try:
                    return _dt.strptime(s, f)
                except Exception:
                    continue
            try:
                if "." in s:
                    parts = s.split(".")
                    base = parts[0]
                    return datetime.fromisoformat(base)
            except Exception:
                pass
            return None

    start_dt = _parse_iso(start_time)
    end_dt = _parse_iso(end_time)
    if not start_dt or not end_dt:
        return error_response(
            "Invalid start_time or end_time format. Expected ISO format (YYYY-MM-DDTHH:MM:SS).",
            400,
        )

    try:
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=UTC)
        else:
            start_dt = start_dt.astimezone(UTC)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=UTC)
        else:
            end_dt = end_dt.astimezone(UTC)
    except Exception:
        return error_response("Invalid start_time or end_time format.", 400)

    if end_dt <= start_dt:
        return error_response("End time must be after start time", 400)

    lecture_id = create_lecture(title, subject, date, payload["sub"], latitude, longitude, radius)
    now = datetime.now(UTC)
    status = "scheduled"
    if start_dt <= now <= end_dt:
        status = "active"

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO lecture_sessions (lecture_id, start_time, end_time, attendance_type, threshold, status, mode, join_url, semester)
        VALUES (?, ?, ?, 'LOCATION', 0, ?, 'OFFLINE', '', ?)
        """,
        (lecture_id, start_time, end_time, status, semester),
    )
    conn.commit()
    session_id = cur.lastrowid
    cur.execute("SELECT id FROM students WHERE semester = ?", (semester,))
    students = cur.fetchall()
    conn.close()

    notification_message = f"New lecture scheduled: {subject} at {start_time}"
    for student_row in students:
        create_notification(student_row[0], notification_message, type_="info", related_session_id=session_id)

    return json_response({"session_id": session_id, "status": status, "notifications_sent": len(students)})


def active_session(request: Any) -> Dict[str, Any]:
    payload, error = auth_required(request)
    if error:
        return error

    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    mode = get_query_param(request, "mode")
    student_semester = None
    if (payload.get("role") or "").lower() == "student":
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT semester FROM students WHERE user_id = ?", (payload["sub"],))
        row = cur.fetchone()
        conn.close()
        if row:
            student_semester = row[0]

    session = get_active_session(now, mode=mode.upper() if mode else None, student_semester=student_semester)
    if not session:
        return json_response({"active": False})
    return json_response({"active": True, "session": session})


def list_all_sessions(request: Any) -> Dict[str, Any]:
    payload, error = auth_required(request)
    if error:
        return error

    mode = get_query_param(request, "mode")
    faculty_id = payload["sub"] if (payload.get("role") or "").lower() == "faculty" else None
    student_semester = None
    if (payload.get("role") or "").lower() == "student":
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT semester FROM students WHERE user_id = ?", (payload["sub"],))
        row = cur.fetchone()
        conn.close()
        if row:
            student_semester = row[0]

    return json_response(
        {"sessions": list_sessions(mode=mode.upper() if mode else None, include_closed=True, faculty_id=faculty_id, student_semester=student_semester)}
    )


def faculty_summary(request: Any) -> Dict[str, Any]:
    payload, error = auth_required(request, role="faculty")
    if error:
        return error

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]
    cur.execute(
        "SELECT DISTINCT semester FROM faculty_subjects WHERE faculty_id = (SELECT id FROM faculty WHERE user_id = ?)",
        (payload["sub"],),
    )
    semesters = [str(row[0]) for row in cur.fetchall()]
    conn.close()
    return json_response({"total_students": total_students, "semesters": semesters})


def handle_api(method: str, path: str, request: Any) -> Dict[str, Any]:
    normalized_path = path.rstrip("/") or "/"
    if normalized_path == "/api/auth/register" and method == "POST":
        return register(request)
    if normalized_path == "/api/auth/login" and method == "POST":
        return login(request)
    if normalized_path == "/api/auth/me" and method == "GET":
        return me(request)
    if normalized_path == "/api/student/profile" and method == "GET":
        return student_profile_get(request)
    if normalized_path == "/api/student/profile" and method == "PUT":
        return student_profile_put(request)
    if normalized_path == "/api/faculty/profile" and method == "GET":
        return faculty_profile_get(request)
    if normalized_path == "/api/attendance/mark-location" and method == "POST":
        return mark_location_attendance(request)
    if normalized_path == "/api/attendance/mark" and method == "POST":
        return mark_attendance(request)
    if normalized_path == "/api/attendance/history" and method == "GET":
        return attendance_history(request)
    if normalized_path == "/api/attendance/stats" and method == "GET":
        return attendance_stats(request)
    if normalized_path.startswith("/api/attendance/report/") and method == "GET":
        session_id = normalized_path.split("/")[-1]
        return attendance_report(request, session_id)
    if normalized_path == "/api/lectures/sessions" and method == "POST":
        return create_lecture_session(request)
    if normalized_path == "/api/lectures/sessions/active" and method == "GET":
        return active_session(request)
    if normalized_path == "/api/lectures/sessions" and method == "GET":
        return list_all_sessions(request)
    if normalized_path == "/api/faculty/summary" and method == "GET":
        return faculty_summary(request)

    return error_response("Not found", 404)
