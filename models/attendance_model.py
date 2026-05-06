from datetime import datetime, timezone, timedelta
import sqlite3
from backend.database import get_db, row_to_dict

# Use UTC for all stored timestamps
UTC = timezone.utc


def create_attendance(student_id, session_id, latitude, longitude, status, timestamp, start_time=None, end_time=None):
    # Ensure timestamp has timezone offset; assume UTC for naive timestamps
    if timestamp:
        ts = str(timestamp).strip()
        if '+' not in ts and not ts.endswith('Z'):
            timestamp = f"{ts}+00:00"
        else:
            timestamp = ts
    else:
        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    
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
    now_iso = datetime.now(UTC).replace(microsecond=0).isoformat()
    
    # Get ALL lectures (past and present) for the student's semester, prioritize past
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
        SELECT session_id, status, timestamp, end_time
        FROM attendance
        WHERE student_id = ?
    """, (student_id,))
    
    attendance_map = {}
    for row in cur.fetchall():
        attendance_map[row[0]] = {
            'status': row[1],
            'joining_time': row[2],
            'end_time': row[3],
            'timestamp': row[2]
        }
    
    conn.close()
    
    # Combine lectures with attendance data
    results = []
    
    for lecture in all_lectures:
        session_id = lecture[6]
        attendance_data = attendance_map.get(session_id, {})
        end_time = lecture[8]  # end_time from session
        
        # Determine attendance status
        if attendance_data:
            status = attendance_data.get('status')
        else:
            # No attendance record and lecture is completed = absent
            status = 'absent'

        # Get join and exit times
        joining_time = attendance_data.get('joining_time') or attendance_data.get('timestamp')
        end_time_actual = attendance_data.get('end_time')

        # Normalize naive timestamps: assume UTC if no offset present
        def _norm(ts):
            if not ts:
                return None
            t = str(ts).strip()
            if '+' not in t and not t.endswith('Z'):
                return f"{t}+00:00"
            return t

        joining_time = _norm(joining_time)
        end_time_actual = _norm(end_time_actual)
        
        # For completed lectures, use session end_time if student didn't record exit
        if status in ['present', 'late'] and not end_time_actual:
            end_time_actual = end_time

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
            'status': status,
            'joining_time': joining_time,
            'timestamp': joining_time,
            'end_time_actual': end_time_actual
        }
        results.append(result)
    
    return results


def get_attendance_by_session(session_id):
    conn = get_db()
    cur = conn.cursor()
    
    # First get the semester and end_time for this session
    cur.execute("SELECT semester, end_time FROM lecture_sessions WHERE id = ?", (session_id,))
    session_row = cur.fetchone()
    if not session_row:
        conn.close()
        return []
    
    semester = session_row[0]
    end_time = session_row[1]
    
    # Check if session has ended
    now_iso = datetime.now(UTC).replace(microsecond=0).isoformat()
    session_ended = end_time and end_time < now_iso
    
    # Get all students with their attendance status for this session, filtered by semester
    cur.execute(
        """
        SELECT 
            COALESCE(a.id, -1) as id,
            COALESCE(a.latitude, NULL) as latitude,
            COALESCE(a.longitude, NULL) as longitude,
            a.status,
            COALESCE(a.timestamp, NULL) as join_time,
            COALESCE(a.end_time, NULL) as exit_time,
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
    
    # Add color coding based on status and calculate duration
    results = []
    for r in rows:
        row_dict = row_to_dict(r)
        status = row_dict.get('status')
        join_time = row_dict.get('join_time')
        exit_time = row_dict.get('exit_time')
        
        # Get join time from timestamp field if join_time is NULL
        if not join_time and row_dict.get('timestamp'):
            join_time = row_dict.get('timestamp')
            row_dict['join_time'] = join_time

        # Normalize naive timestamps to explicit UTC
        def _norm(ts):
            if not ts:
                return None
            t = str(ts).strip()
            if '+' not in t and not t.endswith('Z'):
                return f"{t}+00:00"
            return t

        join_time = _norm(join_time)
        exit_time = _norm(exit_time)
        row_dict['join_time'] = join_time
        row_dict['exit_time'] = exit_time

        # For completed sessions: mark absent ONLY if no attendance record exists
        if status is None and session_ended:
            status = 'absent'
        elif status is None:
            # Session is ongoing - do NOT show any attendance status yet
            status = None
        
        # Fill exit_time from session end_time for completed sessions
        if status in ['present', 'late'] and not exit_time and session_ended:
            exit_time = end_time
            row_dict['exit_time'] = exit_time
        
        row_dict['status'] = status
        
        # Calculate attendance duration (in minutes)
        duration_minutes = None
        if join_time and exit_time and status in ['present', 'late']:
            try:
                join_dt = datetime.fromisoformat(join_time)
                exit_dt = datetime.fromisoformat(exit_time)
                duration = (exit_dt - join_dt).total_seconds() / 60
                duration_minutes = int(round(duration))
            except:
                duration_minutes = None
        
        row_dict['duration_minutes'] = duration_minutes
        
        if status == 'present':
            row_dict['color'] = 'green'  # Green for Present
        elif status == 'late':
            row_dict['color'] = 'orange'  # Orange for Late
        elif status == 'absent':
            row_dict['color'] = 'red'  # Red for Absent
        else:
            row_dict['color'] = 'gray'  # Gray for no status (ongoing/future)
        
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
