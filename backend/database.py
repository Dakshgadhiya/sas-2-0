import os
import sqlite3
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError as SQLAlchemyIntegrityError
from backend import config

# Create a shared SQLAlchemy engine configured by DATABASE_URL.
engine = create_engine(config.DB_URL, future=True)
dialect_name = engine.dialect.name

# Support compatibility with both SQLite and external databases.
DBIntegrityError = SQLAlchemyIntegrityError


def _convert_qmark_query(sql, params):
    if not params or "?" not in sql or dialect_name == "sqlite":
        return sql, params

    if isinstance(params, dict):
        return sql, params

    fragments = sql.split("?")
    named_params = {f"p{i}": params[i] for i in range(len(params))}
    sql = "".join(fragments[i] + f":p{i}" for i in range(len(params))) + fragments[-1]
    return sql, named_params


def _normalize_sql(sql):
    upper_sql = sql.strip().upper()
    if dialect_name != "sqlite" and upper_sql.startswith("INSERT OR IGNORE INTO"):
        sql = sql.replace("INSERT OR IGNORE INTO", "INSERT INTO")
        if "ON CONFLICT" not in sql.upper():
            sql = sql.rstrip(";") + " ON CONFLICT DO NOTHING"
    return sql


class DBConnection:
    def __init__(self):
        self._conn = engine.connect()
        self._transaction = self._conn.begin()
        self._result = None

    def cursor(self):
        return self

    def execute(self, sql, params=None):
        sql = _normalize_sql(sql)
        if params is None:
            self._result = self._conn.exec_driver_sql(sql)
        else:
            sql, params = _convert_qmark_query(sql, params)
            self._result = self._conn.exec_driver_sql(sql, params)
        return self._result

    def fetchall(self):
        return self._result.fetchall() if self._result is not None else []

    def fetchone(self):
        return self._result.fetchone() if self._result is not None else None

    @property
    def lastrowid(self):
        if self._result is None:
            return None
        if hasattr(self._result, "lastrowid") and self._result.lastrowid is not None:
            return self._result.lastrowid
        if hasattr(self._result, "inserted_primary_key") and self._result.inserted_primary_key:
            return self._result.inserted_primary_key[0]
        return None

    def commit(self):
        try:
            self._transaction.commit()
        finally:
            self._transaction = self._conn.begin()

    def rollback(self):
        try:
            self._transaction.rollback()
        finally:
            self._transaction = self._conn.begin()

    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass


def get_db():
    conn = DBConnection()
    if dialect_name == "sqlite":
        conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row):
    if row is None:
        return None
    try:
        return dict(row)
    except Exception:
        try:
            return {column: row[column] for column in row.keys()}
        except Exception:
            return {str(i): value for i, value in enumerate(row)}


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


def _get_table_columns(cur, table_name):
    if dialect_name == "sqlite":
        cur.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cur.fetchall()]

    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = ?
        ORDER BY ordinal_position
        """,
        (table_name,)
    )
    return [row[0] for row in cur.fetchall()]


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

    faculty_columns = _get_table_columns(cur, "faculty")
    if "department" not in faculty_columns:
        cur.execute("ALTER TABLE faculty ADD COLUMN department TEXT")

    if dialect_name == "sqlite" and "subject" in faculty_columns:
        try:
            cur.execute(
                """
                INSERT OR IGNORE INTO faculty_subjects (faculty_id, semester, subject)
                SELECT f.id, '1', f.subject FROM faculty f WHERE f.subject IS NOT NULL
                """
            )
            conn.commit()
        except Exception:
            pass

    if "semesters" in faculty_columns:
        try:
            cur.execute("ALTER TABLE faculty DROP COLUMN semesters")
        except Exception:
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

    lecture_columns = _get_table_columns(cur, "lectures")
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

    session_columns = _get_table_columns(cur, "lecture_sessions")
    if "mode" not in session_columns:
        cur.execute("ALTER TABLE lecture_sessions ADD COLUMN mode TEXT NOT NULL DEFAULT 'ONLINE'")
    if "join_url" not in session_columns:
        cur.execute("ALTER TABLE lecture_sessions ADD COLUMN join_url TEXT")
    if "semester" not in session_columns:
        cur.execute("ALTER TABLE lecture_sessions ADD COLUMN semester TEXT")

    if dialect_name == "sqlite":
        try:
            cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='lecture_sessions'")
            table_sql = cur.fetchone()[0]
            if "CHECK(attendance_type IN ('QUIZ', 'SUBMISSION', 'BOTH'))" in table_sql:
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
        except Exception:
            pass

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

    attendance_columns = _get_table_columns(cur, "attendance")
    if "end_time" not in attendance_columns:
        cur.execute("ALTER TABLE attendance ADD COLUMN end_time TEXT")
    if "start_time" not in attendance_columns:
        cur.execute("ALTER TABLE attendance ADD COLUMN start_time TEXT")

    if dialect_name == "sqlite":
        try:
            cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='attendance'")
            table_sql = cur.fetchone()[0]
            if "CHECK(status IN ('present', 'absent'))" in table_sql and "late" not in table_sql:
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
        except Exception:
            pass

    _fix_zero_length_sessions(cur)
    _dedupe_attendance(cur)

    cur.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_attendance_unique ON attendance(student_id, session_id)"
    )

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
