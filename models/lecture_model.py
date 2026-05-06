from backend.database import get_db, row_to_dict


def create_lecture(title, subject, date, faculty_id, latitude=None, longitude=None, radius=None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO lectures (title, subject, date, faculty_id, latitude, longitude, radius) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (title, subject, date, faculty_id, latitude, longitude, radius),
    )
    conn.commit()
    lecture_id = cur.lastrowid
    conn.close()
    return lecture_id


def create_session(lecture_id, start_time, end_time, attendance_type, threshold, status, mode, join_url=None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO lecture_sessions (lecture_id, start_time, end_time, attendance_type, threshold, status, mode, join_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (lecture_id, start_time, end_time, attendance_type, threshold, status, mode, join_url),
    )
    conn.commit()
    session_id = cur.lastrowid
    conn.close()
    return session_id


def refresh_session_statuses(now_iso=None):
    if now_iso is None:
        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE lecture_sessions SET status = 'active' WHERE start_time <= ? AND end_time >= ? AND status != 'active'",
        (now_iso, now_iso),
    )
    cur.execute(
        "UPDATE lecture_sessions SET status = 'closed' WHERE end_time < ? AND status != 'closed'",
        (now_iso,),
    )
    conn.commit()
    conn.close()


def get_active_session(now_iso, mode=None, student_semester=None):
    refresh_session_statuses(now_iso)

    conn = get_db()
    cur = conn.cursor()

    base_query = """
        SELECT ls.*, l.title AS lecture_title, l.subject AS lecture_subject, l.date AS lecture_date,
               l.latitude AS latitude, l.longitude AS longitude, l.radius AS radius,
               l.faculty_id AS faculty_id, u.name AS faculty_name
        FROM lecture_sessions ls
        JOIN lectures l ON l.id = ls.lecture_id
        LEFT JOIN users u ON u.id = l.faculty_id
        WHERE ls.start_time <= ? AND ls.end_time >= ?
    """

    params = [now_iso, now_iso]
    if mode:
        base_query += " AND ls.mode = ?"
        params.append(mode)
    if student_semester is not None:
        base_query += " AND ls.semester = ?"
        params.append(student_semester)

    base_query += " ORDER BY ls.start_time DESC LIMIT 1"

    cur.execute(base_query, tuple(params))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)


def set_session_status(session_id, status):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE lecture_sessions SET status = ? WHERE id = ?", (status, session_id))
    conn.commit()
    conn.close()


def list_sessions(mode=None, include_closed=False, faculty_id=None, student_semester=None):
    refresh_session_statuses()

    conn = get_db()
    cur = conn.cursor()
    base_query = """
        SELECT ls.*, l.title AS lecture_title, l.subject AS lecture_subject, l.date AS lecture_date,
               l.latitude AS latitude, l.longitude AS longitude, l.radius AS radius,
               l.faculty_id AS faculty_id, u.name AS faculty_name,
               COALESCE(attendance_counts.count, 0) AS attendance_count
        FROM lecture_sessions ls
        JOIN lectures l ON l.id = ls.lecture_id
        LEFT JOIN users u ON u.id = l.faculty_id
        LEFT JOIN (
            SELECT session_id, COUNT(*) AS count
            FROM attendance
            WHERE status IN ('present', 'late')
            GROUP BY session_id
        ) attendance_counts ON attendance_counts.session_id = ls.id
    """
    params = []
    conditions = []
    if mode:
        conditions.append("ls.mode = ?")
        params.append(mode)
    if not include_closed:
        conditions.append("ls.status != 'closed'")
    if faculty_id is not None:
        conditions.append("l.faculty_id = ?")
        params.append(faculty_id)
    if student_semester is not None:
        conditions.append("ls.semester = ?")
        params.append(student_semester)
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    base_query += " ORDER BY ls.start_time DESC"

    cur.execute(base_query, tuple(params))
    rows = cur.fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]
