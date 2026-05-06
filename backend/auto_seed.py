"""
Auto-seed database on startup if empty.
This ensures deployed instances have test data.
"""
import json
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


def auto_seed_if_empty(db_conn):
    """Seed database with test data if empty"""
    cur = db_conn.cursor()
    
    # Check if data already exists
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    
    if user_count > 0:
        print("[DB] Database already populated, skipping auto-seed")
        return
    
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
            
            # Add subjects
            subjects = ["Mathematics", "Python Programming", "System Design"]
            for sem, subj in enumerate(subjects, start=1):
                cur.execute(
                    "INSERT INTO faculty_subjects (faculty_id, semester, subject) VALUES (?, ?, ?)",
                    (faculty_id, str(sem), subj)
                )
        
        # Insert past lectures
        cur.execute("SELECT id, user_id FROM faculty")
        faculty_list = cur.fetchall()
        
        for faculty_id, faculty_user_id in faculty_list:
            # Create 3 past lectures per faculty
            for lec_num in range(3):
                past_date = datetime.now() - timedelta(days=random.randint(2, 20))
                lec_date = past_date.strftime("%Y-%m-%d")
                
                cur.execute(
                    "INSERT INTO lectures (title, subject, date, faculty_id, latitude, longitude, radius) VALUES (?, ?, ?, ?, 21.1702, 72.8311, 50)",
                    (f"Lecture {lec_num+1}", "Mathematics", lec_date, faculty_user_id)
                )
                lecture_id = cur.lastrowid
                
                # Create session
                cur.execute(
                    "INSERT INTO lecture_sessions (lecture_id, start_time, end_time, attendance_type, threshold, status, mode, join_url, semester) VALUES (?, ?, ?, 'LOCATION', 0, 'closed', 'OFFLINE', '', '1')",
                    (lecture_id, "09:00:00", "10:00:00")
                )
                session_id = cur.lastrowid
                
                # Add attendance records
                cur.execute("SELECT id FROM students LIMIT 3")
                students = cur.fetchall()
                
                for student_id, in students:
                    status = random.choice(["present", "late", "absent"])
                    cur.execute(
                        "INSERT INTO attendance (student_id, session_id, latitude, longitude, status, start_time, end_time, timestamp) VALUES (?, ?, 21.1702, 72.8311, ?, ?, ?, ?)",
                        (student_id, session_id, status, "09:00:00", "10:00:00", "09:00:00")
                    )
        
        db_conn.commit()
        print("[DB] Auto-seed completed successfully")
        
    except Exception as e:
        db_conn.rollback()
        print(f"[DB] Auto-seed failed: {e}")
        raise
