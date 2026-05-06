import os
import sys
import sqlite3
from datetime import datetime, timedelta
import random

# Ensure project root is in path
BASE_DIR = os.getcwd()
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Add the backend directory to path
sys.path.append(os.path.join(BASE_DIR, 'backend'))

from database import get_db

def create_past_lectures():
    print("Creating past lectures with attendance data...")

    conn = get_db()
    cur = conn.cursor()

    try:
        # Get existing faculty
        cur.execute("SELECT f.id, f.user_id, f.faculty_id FROM faculty f")
        faculty_list = cur.fetchall()

        # Get students by semester
        students_by_semester = {}
        for sem in range(1, 7):
            cur.execute("SELECT id FROM students WHERE semester = ?", (str(sem),))
            students_by_semester[str(sem)] = [row[0] for row in cur.fetchall()]

        # Create 5 past lectures per faculty (last 5 days)
        lecture_count = 0
        attendance_count = 0

        for faculty in faculty_list[:3]:  # Only first 3 faculty for speed
            faculty_db_id = faculty[0]  # faculty.id
            faculty_user_id = faculty[1]  # faculty.user_id (references users.id)

            # Get faculty subjects
            cur.execute("SELECT semester, subject FROM faculty_subjects WHERE faculty_id = ?", (faculty_db_id,))
            subjects = cur.fetchall()

            for i in range(2):  # Only 2 lectures per faculty for speed
                # Random past date (1-5 days ago)
                past_date = datetime.now() - timedelta(days=random.randint(1, 5))
                lecture_date = past_date.strftime("%Y-%m-%d")

                # Random subject from faculty's subjects
                if subjects:
                    semester, subject = random.choice(subjects)
                else:
                    semester = "1"
                    subject = "Test Subject"

                # Insert lecture
                cur.execute("""
                    INSERT INTO lectures (title, subject, date, faculty_id, latitude, longitude, radius)
                    VALUES (?, ?, ?, ?, 21.1702, 72.8311, 50)
                """, (f"{subject} - Past Lecture {i+1}", subject, lecture_date, faculty_user_id))

                lecture_id = cur.lastrowid

                # Random time slot
                start_hour = random.randint(9, 14)
                start_time = f"{start_hour:02d}:{random.choice(['00', '30'])}:00"
                end_time = f"{start_hour+1:02d}:{random.choice(['00', '30'])}:00"

                # Insert lecture session (already ended)
                cur.execute("""
                    INSERT INTO lecture_sessions (lecture_id, start_time, end_time, attendance_type, threshold, status, mode, join_url, semester)
                    VALUES (?, ?, ?, 'LOCATION', 0, 'closed', 'OFFLINE', '', ?)
                """, (lecture_id, start_time, end_time, semester))

                session_id = cur.lastrowid

                # Create attendance for students in this semester
                semester_students = students_by_semester.get(semester, [])
                for student_id in semester_students:
                    # BETTER distribution: 70% present, 15% late, 15% absent
                    attendance_type = random.choices(
                        ["present", "late", "absent"],
                        weights=[70, 15, 15],
                        k=1
                    )[0]

                    if attendance_type == "absent":
                        # Still create absent record
                        cur.execute("""
                            INSERT INTO attendance (student_id, session_id, latitude, longitude, status, timestamp)
                            VALUES (?, ?, 21.1702, 72.8311, ?, ?)
                        """, (student_id, session_id, attendance_type, join_time))
                        attendance_count += 1
                        continue

                    # Generate join time
                    start_dt = datetime.strptime(start_time, "%H:%M:%S")
                    if attendance_type == "present":
                        join_delay = random.randint(0, 5)
                    else:  # late
                        join_delay = random.randint(6, 20)

                    join_time = (start_dt + timedelta(minutes=join_delay)).strftime("%H:%M:%S")
                    end_time_actual = (start_dt + timedelta(minutes=join_delay + random.randint(45, 60))).strftime("%H:%M:%S")

                    # Insert attendance
                    cur.execute("""
                        INSERT INTO attendance (student_id, session_id, latitude, longitude, status, start_time, end_time, timestamp)
                        VALUES (?, ?, 21.1702, 72.8311, ?, ?, ?, ?)
                    """, (student_id, session_id, attendance_type, join_time, end_time_actual, join_time))

                    attendance_count += 1

                lecture_count += 1

        conn.commit()
        print(f"✅ Created {lecture_count} past lectures")
        print(f"✅ Created {attendance_count} attendance records")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    create_past_lectures()