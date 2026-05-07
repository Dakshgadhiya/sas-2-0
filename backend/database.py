import sqlite3
from datetime import datetime, timedelta
from backend import config


def get_db():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _dedupe_attendance(cur):
    cur.execute(
        """
        DELETE FROM attendance
        WHERE id NOT IN (
            SELECT MIN(id) FROM attendance GROUP BY student_id, session_id
        )
        """
    )


def _fix_zero_length_sessions(cur):
    cur.execute(
        "SELECT id, start_time, end_time FROM lecture_sessions WHERE start_time IS NOT NULL AND end_time IS NOT NULL AND start_time = end_time"
    )
    rows = cur.fetchall()
    for row in rows:
        try:
            start_dt = datetime.fromisoformat(row["start_time"])
            corrected_end = (start_dt + timedelta(hours=1)).replace(microsecond=0).isoformat()
            cur.execute(
                "UPDATE lecture_sessions SET end_time = ? WHERE id = ?",
                (corrected_end, row["id"])
            )
        except Exception:
            pass

    cur.execute(
        "SELECT id, start_time, end_time FROM attendance WHERE start_time IS NOT NULL AND end_time IS NOT NULL AND start_time = end_time"
    )
    rows = cur.fetchall()
    for row in rows:
        try:
            start_dt = datetime.fromisoformat(row["start_time"])
            corrected_end = (start_dt + timedelta(hours=1)).replace(microsecond=0).isoformat()
            cur.execute(
                "UPDATE attendance SET end_time = ? WHERE id = ?",
                (corrected_end, row["id"])
            )
        except Exception:
            pass


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student', 'faculty'))
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            roll_number TEXT NOT NULL UNIQUE,
            department TEXT,
            semester TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS faculty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            faculty_id TEXT NOT NULL UNIQUE,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    # Create table for faculty teaching assignments (semester + subject pairs)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS faculty_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faculty_id INTEGER NOT NULL,
            semester TEXT NOT NULL,
            subject TEXT NOT NULL,
            FOREIGN KEY(faculty_id) REFERENCES faculty(id) ON DELETE CASCADE,
            UNIQUE(faculty_id, semester, subject)
        )
        """
    )

    # Migration: add department column to faculty if missing
    cur.execute("PRAGMA table_info(faculty)")
    faculty_columns = [row[1] for row in cur.fetchall()]
    if "department" not in faculty_columns:
        cur.execute("ALTER TABLE faculty ADD COLUMN department TEXT")
    
    # Migration: handle old faculty schema
    if "subject" in faculty_columns:
        # Old schema had subject in faculty table, migrate it
        try:
            cur.execute("""
                INSERT OR IGNORE INTO faculty_subjects (faculty_id, semester, subject)
                SELECT f.id, '1', f.subject FROM faculty f WHERE f.subject IS NOT NULL
            """)
            conn.commit()
        except:
            pass
    if "semesters" in faculty_columns:
        # Old schema had semesters, drop it
        try:
            cur.execute("ALTER TABLE faculty DROP COLUMN semesters")
        except:
            pass

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS lectures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            date TEXT NOT NULL,
            faculty_id INTEGER,
            latitude REAL,
            longitude REAL,
            radius INTEGER,
            FOREIGN KEY(faculty_id) REFERENCES users(id) ON DELETE SET NULL
        )
        """
    )

    # Migration: add faculty_id column if missing
    cur.execute("PRAGMA table_info(lectures)")
    lecture_columns = [row[1] for row in cur.fetchall()]
    if "faculty_id" not in lecture_columns:
        cur.execute("ALTER TABLE lectures ADD COLUMN faculty_id INTEGER")
    if "latitude" not in lecture_columns:
        cur.execute("ALTER TABLE lectures ADD COLUMN latitude REAL")
    if "longitude" not in lecture_columns:
        cur.execute("ALTER TABLE lectures ADD COLUMN longitude REAL")
    if "radius" not in lecture_columns:
        cur.execute("ALTER TABLE lectures ADD COLUMN radius INTEGER")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS lecture_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lecture_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            attendance_type TEXT NOT NULL DEFAULT 'LOCATION',
            threshold INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL CHECK(status IN ('scheduled', 'active', 'closed')),
            mode TEXT NOT NULL DEFAULT 'ONLINE',
            join_url TEXT,
            FOREIGN KEY(lecture_id) REFERENCES lectures(id) ON DELETE CASCADE
        )
        """
    )

    # Migration: add mode, join_url, semester columns if missing
    cur.execute("PRAGMA table_info(lecture_sessions)")
    session_columns = [row[1] for row in cur.fetchall()]
    if "mode" not in session_columns:
        cur.execute("ALTER TABLE lecture_sessions ADD COLUMN mode TEXT NOT NULL DEFAULT 'ONLINE'")
    if "join_url" not in session_columns:
        cur.execute("ALTER TABLE lecture_sessions ADD COLUMN join_url TEXT")
    if "semester" not in session_columns:
        cur.execute("ALTER TABLE lecture_sessions ADD COLUMN semester TEXT")

    # Migration: update attendance_type CHECK constraint to include 'LOCATION'
    try:
        cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='lecture_sessions'")
        table_sql = cur.fetchone()[0]
        if "CHECK(attendance_type IN ('QUIZ', 'SUBMISSION', 'BOTH'))" in table_sql:
            # Recreate table with updated constraint
            cur.execute("PRAGMA foreign_keys = OFF")
            cur.execute("ALTER TABLE lecture_sessions RENAME TO lecture_sessions_old")
            cur.execute(
                """
                CREATE TABLE lecture_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lecture_id INTEGER NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    attendance_type TEXT NOT NULL DEFAULT 'LOCATION' CHECK(attendance_type IN ('QUIZ', 'SUBMISSION', 'BOTH', 'LOCATION')),
                    threshold INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL CHECK(status IN ('scheduled', 'active', 'closed')),
                    mode TEXT NOT NULL DEFAULT 'ONLINE',
                    join_url TEXT,
                    FOREIGN KEY(lecture_id) REFERENCES lectures(id) ON DELETE CASCADE
                )
                """
            )
            cur.execute(
                """
                INSERT INTO lecture_sessions (id, lecture_id, start_time, end_time, attendance_type, threshold, status, mode, join_url)
                SELECT id, lecture_id, start_time, end_time, attendance_type, threshold, status, mode, join_url FROM lecture_sessions_old
                """
            )
            cur.execute("DROP TABLE lecture_sessions_old")
            cur.execute("PRAGMA foreign_keys = ON")
    except:
        pass  # Table might not exist yet or constraint already updated

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            session_id INTEGER NOT NULL,
            latitude REAL,
            longitude REAL,
            status TEXT NOT NULL CHECK(status IN ('present', 'absent', 'late')),
            start_time TEXT,
            end_time TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY(session_id) REFERENCES lecture_sessions(id) ON DELETE CASCADE
        )
        """
    )

    # Migration: Update attendance table to include end_time and 'late' status
    try:
        cur.execute("PRAGMA table_info(attendance)")
        attendance_columns = {row[1]: row for row in cur.fetchall()}
        
        needs_migration = False
        if "end_time" not in attendance_columns:
            cur.execute("ALTER TABLE attendance ADD COLUMN end_time TEXT")
            needs_migration = True
        if "start_time" not in attendance_columns:
            cur.execute("ALTER TABLE attendance ADD COLUMN start_time TEXT")
            needs_migration = True
        
        # Check if status needs updating (old constraint might not include 'late')
        cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='attendance'")
        table_sql = cur.fetchone()[0]
        if "CHECK(status IN ('present', 'absent'))" in table_sql and "late" not in table_sql:
            # Need to recreate table with updated status constraint
            cur.execute("PRAGMA foreign_keys = OFF")
            cur.execute("ALTER TABLE attendance RENAME TO attendance_old")
            cur.execute("""
                CREATE TABLE attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    session_id INTEGER NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    status TEXT NOT NULL CHECK(status IN ('present', 'absent', 'late')),
                    start_time TEXT,
                    end_time TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
                    FOREIGN KEY(session_id) REFERENCES lecture_sessions(id) ON DELETE CASCADE
                )
            """)
            cur.execute("""
                INSERT INTO attendance (id, student_id, session_id, latitude, longitude, status, timestamp)
                SELECT id, student_id, session_id, latitude, longitude, status, timestamp FROM attendance_old
            """)
            cur.execute("DROP TABLE attendance_old")
            cur.execute("PRAGMA foreign_keys = ON")
    except Exception as e:
        pass  # Migration might not be needed or table doesn't exist yet

    # Fix any seeded sessions or attendance rows where end_time was accidentally written equal to start_time
    _fix_zero_length_sessions(cur)

    # Cleanup lectures older than 1 day (and related sessions)
    # cutoff = (datetime.now().date() - timedelta(days=1)).isoformat()
    # cur.execute("DELETE FROM lectures WHERE date < ?", (cutoff,))

    # Remove duplicate attendance rows before enforcing unique index
    _dedupe_attendance(cur)

    # Prevent duplicate attendance for same student & session
    cur.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_attendance_unique ON attendance(student_id, session_id)"
    )

    # Create notifications table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('success', 'error', 'info', 'warning')),
            related_session_id INTEGER,
            is_read INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY(related_session_id) REFERENCES lecture_sessions(id) ON DELETE SET NULL
        )
        """
    )

    conn.commit()
    conn.close()


def row_to_dict(row):
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}
