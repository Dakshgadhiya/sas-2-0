import os
import sys
import json
import hashlib
import hmac
import secrets
from datetime import datetime

# Ensure project root is in path
BASE_DIR = os.getcwd()
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Add the backend directory to path
sys.path.append(os.path.join(BASE_DIR, 'backend'))

from database import get_db

PBKDF2_ITERATIONS = 200_000
PBKDF2_ALGORITHM = "sha256"

def hash_password(password):
    """Hash password using PBKDF2 (same as backend)"""
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"

def insert_test_data():
    print("Loading test data...")
    with open("sas_test_data.json", "r") as f:
        data = json.load(f)

    conn = get_db()
    cur = conn.cursor()

    try:
        print("Inserting students...")
        student_count = 0
        for semester, students in data["students"].items():
            for student in students:
                # Insert user
                hashed_password = hash_password(student["password"])
                cur.execute("""
                    INSERT INTO users (name, email, password, role)
                    VALUES (?, ?, ?, 'student')
                """, (student["name"], student["email"], hashed_password))

                user_id = cur.lastrowid

                # Insert student
                cur.execute("""
                    INSERT INTO students (user_id, roll_number, department, semester)
                    VALUES (?, ?, 'Information Technology', ?)
                """, (user_id, student["enrollment"], semester))

                student_count += 1

        print(f"Inserted {student_count} students")

        print("Inserting faculty...")
        faculty_count = 0
        for faculty in data["faculty"]:
            # Insert user
            hashed_password = hash_password(faculty["password"])
            cur.execute("""
                INSERT INTO users (name, email, password, role)
                VALUES (?, ?, ?, 'faculty')
            """, (faculty["name"], faculty["email"], hashed_password))

            user_id = cur.lastrowid

            # Insert faculty
            cur.execute("""
                INSERT INTO faculty (user_id, faculty_id, department)
                VALUES (?, ?, ?)
            """, (user_id, faculty["faculty_id"], faculty["department"]))

            faculty_id_db = cur.lastrowid

            # Insert faculty subjects
            for subject in faculty["subjects"]:
                cur.execute("""
                    INSERT INTO faculty_subjects (faculty_id, semester, subject)
                    VALUES (?, ?, ?)
                """, (faculty_id_db, subject["semester"], subject["subject"]))

            faculty_count += 1

        print(f"Inserted {faculty_count} faculty members")

        print("Inserting lectures...")
        lecture_count = 0
        for lecture in data["lectures"]:
            # Convert date from DD-MM-YYYY to YYYY-MM-DD
            date_parts = lecture["date"].split("-")
            db_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"

            # Get faculty user_id
            cur.execute("SELECT user_id FROM faculty WHERE faculty_id = ?", (lecture["faculty_id"],))
            faculty_user_id = cur.fetchone()[0]

            # Insert lecture
            cur.execute("""
                INSERT INTO lectures (title, subject, date, faculty_id, latitude, longitude, radius)
                VALUES (?, ?, ?, ?, 21.1702, 72.8311, 50)
            """, (lecture["title"], lecture["subject"], db_date, faculty_user_id))

            lecture_id = cur.lastrowid

            # Insert lecture session
            cur.execute("""
                INSERT INTO lecture_sessions (lecture_id, start_time, end_time, attendance_type, threshold, status, mode, join_url, semester)
                VALUES (?, ?, ?, 'LOCATION', 0, 'scheduled', 'OFFLINE', '', ?)
            """, (lecture_id, lecture["start_time"], lecture["end_time"], lecture["semester"]))

            lecture_count += 1

        print(f"Inserted {lecture_count} lectures")

        print("Inserting attendance records...")
        attendance_count = 0
        for attendance in data["attendance"]:
            # Get student ID
            cur.execute("SELECT id FROM students WHERE roll_number = ?", (attendance["student_enrollment"],))
            student_result = cur.fetchone()
            if not student_result:
                continue
            student_id = student_result[0]

            # Get session ID for this lecture
            cur.execute("""
                SELECT ls.id FROM lecture_sessions ls
                JOIN lectures l ON l.id = ls.lecture_id
                WHERE l.id = ?
            """, (attendance["lecture_id"],))
            session_result = cur.fetchone()
            if not session_result:
                continue
            session_id = session_result[0]

            # Insert attendance
            cur.execute("""
                INSERT INTO attendance (student_id, session_id, latitude, longitude, status, start_time, end_time, timestamp)
                VALUES (?, ?, 21.1702, 72.8311, ?, ?, ?, ?)
            """, (student_id, session_id, attendance["status"], attendance["join_time"], attendance["exit_time"], attendance["join_time"]))

            attendance_count += 1

        print(f"Inserted {attendance_count} attendance records")

        conn.commit()
        print("All test data inserted successfully!")

        # Print summary
        print("\n=== SUMMARY ===")
        print(f"Students: {student_count}")
        print(f"Faculty: {faculty_count}")
        print(f"Lectures: {lecture_count}")
        print(f"Attendance Records: {attendance_count}")

    except Exception as e:
        conn.rollback()
        print(f"Error inserting data: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    insert_test_data()