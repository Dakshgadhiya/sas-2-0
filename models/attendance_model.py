import sqlite3
from backend.database import get_db, row_to_dict


def create_attendance(student_id, session_id, latitude, longitude, status, timestamp, start_time=None, end_time=None):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO attendance (student_id, session_id, latitude, longitude, status, start_time, end_time, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (student_id, session_id, latitude, longitude, status, start_time, end_time, timestamp),
        )
        conn.commit()
        attendance_id = cur.lastrowid
    except sqlite3.IntegrityError:
        cur.execute(
            """
            UPDATE attendance
            SET latitude = ?, longitude = ?, status = ?, start_time = ?, end_time = ?, timestamp = ?
            WHERE student_id = ? AND session_id = ?
            """,
            (latitude, longitude, status, start_time, end_time, timestamp, student_id, session_id),
        )
        conn.commit()
        cur.execute(
            "SELECT id FROM attendance WHERE student_id = ? AND session_id = ?",
            (student_id, session_id),
        )
        attendance_id = cur.fetchone()[0]
    finally:
        conn.close()
    return attendance_id


def get_attendance_by_student(student_id):
    conn = get_db()
    cur = conn.cursor()
    
    # First, get the student's semester
    cur.execute("SELECT semester FROM students WHERE id = ?", (student_id,))
    student_row = cur.fetchone()
    if not student_row:
        conn.close()
        return []
    
    student_semester = student_row[0]
    
    # Get all lectures for the student's semester
    cur.execute("""
        SELECT 
            l.id,
            l.title AS lecture_title,
            l.subject AS lecture_subject,
            l.date AS lecture_date,
            l.faculty_id,
            u.name AS faculty_name,
            ls.id AS session_id,
            ls.start_time,
            ls.end_time,
            ls.attendance_type,
            ls.threshold,
            ls.semester
        FROM lectures l
        JOIN lecture_sessions ls ON ls.lecture_id = l.id
        LEFT JOIN users u ON u.id = l.faculty_id
        WHERE ls.semester = ?
        ORDER BY l.date DESC, ls.start_time DESC
    """, (student_semester,))
    
    all_lectures = cur.fetchall()
    
    # Get attendance records for this student
    cur.execute("""
        SELECT session_id, status, COALESCE(start_time, timestamp) as joining_time, end_time, timestamp
        FROM attendance
        WHERE student_id = ?
    """, (student_id,))
    
    attendance_map = {}
    for row in cur.fetchall():
        attendance_map[row[0]] = {
            'status': row[1],
            'joining_time': row[2],
            'end_time': row[3],
            'timestamp': row[4]
        }
    
    conn.close()
    
    # Combine lectures with attendance data
    results = []
    for lecture in all_lectures:
        session_id = lecture[6]
        attendance_data = attendance_map.get(session_id, {})
        
        result = {
            'id': lecture[0],
            'student_id': student_id,
            'lecture_title': lecture[1],
            'lecture_subject': lecture[2],
            'lecture_date': lecture[3],
            'faculty_id': lecture[4],
            'faculty_name': lecture[5],
            'session_id': session_id,
            'start_time': lecture[7],
            'end_time': lecture[8],
            'attendance_type': lecture[9],
            'threshold': lecture[10],
            'semester': lecture[11],
            'status': attendance_data.get('status', 'absent'),  # Default to absent if no record
            'joining_time': attendance_data.get('joining_time'),
            'timestamp': attendance_data.get('timestamp'),
            'end_time_actual': attendance_data.get('end_time')
        }
        results.append(result)
    
    return results


def get_attendance_by_session(session_id):
    conn = get_db()
    cur = conn.cursor()
    
    # First get the semester for this session
    cur.execute("SELECT semester FROM lecture_sessions WHERE id = ?", (session_id,))
    session_row = cur.fetchone()
    if not session_row:
        conn.close()
        return []
    
    semester = session_row[0]
    
    # Get all students with their attendance status for this session, filtered by semester
    # If no attendance record exists, mark as absent
    cur.execute(
        """
        SELECT 
            COALESCE(a.id, -1) as id,
            COALESCE(a.latitude, NULL) as latitude,
            COALESCE(a.longitude, NULL) as longitude,
            COALESCE(a.status, 'absent') as status,
            COALESCE(a.start_time, NULL) as start_time,
            COALESCE(a.end_time, NULL) as end_time,
            COALESCE(a.timestamp, NULL) as timestamp,
            s.id as student_id,
            s.roll_number,
            u.name as student_name,
            a.session_id
        FROM students s
        JOIN users u ON u.id = s.user_id
        LEFT JOIN attendance a ON a.student_id = s.id AND a.session_id = ?
        WHERE s.semester = ?
        ORDER BY s.roll_number ASC
        """,
        (session_id, semester),
    )
    rows = cur.fetchall()
    conn.close()
    
    # Add color coding based on status
    results = []
    for r in rows:
        row_dict = row_to_dict(r)
        status = row_dict.get('status', 'absent')
        if status == 'present':
            row_dict['color'] = 'green'  # Green for Present
        elif status == 'late':
            row_dict['color'] = 'orange'  # Orange for Late
        else:  # absent or other
            row_dict['color'] = 'red'  # Red for Absent
        results.append(row_dict)
    
    return results


def get_attendance_stats(student_id):
    conn = get_db()
    cur = conn.cursor()
    
    # Get student's semester first
    cur.execute("SELECT semester FROM students WHERE id = ?", (student_id,))
    student_row = cur.fetchone()
    if not student_row:
        conn.close()
        return 0, 0
    
    student_semester = student_row[0]
    
    # Count only lectures from student's semester
    cur.execute("SELECT COUNT(*) AS total FROM lecture_sessions WHERE semester = ?", (student_semester,))
    total = cur.fetchone()[0]
    cur.execute(
        "SELECT COUNT(*) AS attended FROM attendance WHERE student_id = ? AND status IN ('present', 'late')",
        (student_id,),
    )
    attended = cur.fetchone()[0]
    conn.close()
    return total, attended
