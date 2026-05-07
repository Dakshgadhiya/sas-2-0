"""
Auto-seed database on startup if empty.
This ensures deployed instances have test data.
"""
import os
import sys
import hashlib
import secrets
from datetime import datetime, timedelta
import random

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(BASE_DIR)

PBKDF2_ITERATIONS = 200_000
PBKDF2_ALGORITHM = "sha256"


def hash_password(password):
    """Hash password using PBKDF2"""
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def _iso_date_time(date_obj, hour=9, minute=0, second=0):
    return date_obj.replace(hour=hour, minute=minute, second=second, microsecond=0).isoformat()


def _seed_lecture_sessions(cur, faculty_user_id, subject, student_ids):
    for lec_num in range(3):
        past_date = datetime.now() - timedelta(days=random.randint(2, 20))
        start_time = _iso_date_time(past_date, hour=9)
        end_time = _iso_date_time(past_date, hour=10)

        cur.execute(
            "INSERT INTO lectures (title, subject, date, faculty_id, latitude, longitude, radius) VALUES (?, ?, ?, ?, 21.1702, 72.8311, 50)",
            (f"Lecture {lec_num+1}", subject, past_date.strftime("%Y-%m-%d"), faculty_user_id)
        )
        lecture_id = cur.lastrowid

        cur.execute(
            "INSERT INTO lecture_sessions (lecture_id, start_time, end_time, attendance_type, threshold, status, mode, join_url, semester) VALUES (?, ?, ?, 'LOCATION', 0, 'closed', 'OFFLINE', '', '1')",
            (lecture_id, start_time, end_time)
        )
        session_id = cur.lastrowid

        for student_id in student_ids:
            status = random.choice(["present", "late", "absent"])
            cur.execute(
                "INSERT INTO attendance (student_id, session_id, latitude, longitude, status, start_time, end_time, timestamp) VALUES (?, ?, 21.1702, 72.8311, ?, ?, ?, ?)",
                (student_id, session_id, status, start_time, end_time, start_time)
            )


def auto_seed_if_empty(db_conn):
    """Seed database with test data if empty or if there are no lecture sessions."""
    cur = db_conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM lecture_sessions")
    session_count = cur.fetchone()[0]

    if user_count > 0 and session_count > 0:
        print("[DB] Database already populated, skipping auto-seed")
        return

    if user_count > 0 and session_count == 0:
        print("[DB] Database has users but no lectures/sessions. Auto-seeding sample lectures and attendance...")
        try:
            cur.execute("SELECT id FROM students")
            students = [row[0] for row in cur.fetchall()]
            cur.execute("SELECT id, user_id FROM faculty")
            faculty_list = cur.fetchall()

            if not students or not faculty_list:
                print("[DB] No students or faculty records available to seed sample sessions.")
                return

            for faculty_id, faculty_user_id in faculty_list:
                cur.execute("SELECT subject FROM faculty_subjects WHERE faculty_id = ? LIMIT 1", (faculty_id,))
                row = cur.fetchone()
                subject = row[0] if row else "General"
                _seed_lecture_sessions(cur, faculty_user_id, subject, students[:3])

            db_conn.commit()
            print("[DB] Auto-seed completed successfully")
            return
        except Exception as e:
            db_conn.rollback()
            print(f"[DB] Auto-seed failed: {e}")
            raise

    print("[DB] Database empty, auto-seeding with test data...")
    try:
        # Insert core test users (sample)
        test_students = [
            ("Shaileh Agrawal", "shailesh@gmail.com", "266120316001", "1"),
            ("Gaurav Aniyaliya", "gaurav@gmail.com", "266120316002", "1"),
            ("Dravy Bhadani", "dravy@gmail.com", "266120316004", "1"),
        ]

        for name, email, enrollment, semester in test_students:
            hashed_pwd = hash_password("12345678")
            cur.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, 'student')",
                (name, email, hashed_pwd)
            )
            user_id = cur.lastrowid

            cur.execute(
                "INSERT INTO students (user_id, roll_number, department, semester) VALUES (?, ?, 'Information Technology', ?)",
                (user_id, enrollment, semester)
            )

        # Insert test faculty
        test_faculty = [
            ("Prof. Mathematics", "prof.math@college.edu", "F001"),
            ("Prof. Programming", "prof.prog@college.edu", "F002"),
            ("Prof. Systems", "prof.sys@college.edu", "F003"),
        ]

        for fname, femail, fid in test_faculty:
            hashed_pwd = hash_password("12345678")
            cur.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, 'faculty')",
                (fname, femail, hashed_pwd)
            )
            user_id = cur.lastrowid

            cur.execute(
                "INSERT INTO faculty (user_id, faculty_id, department) VALUES (?, ?, 'Information Technology')",
                (user_id, fid)
            )
            faculty_id = cur.lastrowid

            subjects = ["Mathematics", "Python Programming", "System Design"]
            for sem, subj in enumerate(subjects, start=1):
                cur.execute(
                    "INSERT INTO faculty_subjects (faculty_id, semester, subject) VALUES (?, ?, ?)",
                    (faculty_id, str(sem), subj)
                )

        # Insert past lectures and sessions
        cur.execute("SELECT id, user_id FROM faculty")
        faculty_list = cur.fetchall()
        for faculty_id, faculty_user_id in faculty_list:
            _seed_lecture_sessions(cur, faculty_user_id, "Mathematics", [1, 2, 3])

        db_conn.commit()
        print("[DB] Auto-seed completed successfully")

    except Exception as e:
        db_conn.rollback()
        print(f"[DB] Auto-seed failed: {e}")
        raise
