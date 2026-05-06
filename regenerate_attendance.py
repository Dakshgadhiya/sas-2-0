import os
import sys
import sqlite3
from datetime import datetime, timedelta
import random

# Ensure project root is in path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

sys.path.append(os.path.join(BASE_DIR, 'backend'))

from database import get_db

def regenerate_past_lectures():
    print("Regenerating past lectures with better attendance data...")

    conn = get_db()
    cur = conn.cursor()

    try:
        # Check if data already exists
        cur.execute("SELECT COUNT(*) FROM lectures")
        existing_lectures = cur.fetchone()[0]
        
        if existing_lectures > 0:
            print(f"Found {existing_lectures} existing lectures. Clearing old data...")
        else:
            print("No existing data found, creating fresh data...")

        # Clear ALL existing lecture data (not just past)
        print("  Clearing ALL existing lecture data...")
        cur.execute("DELETE FROM attendance")
        cur.execute("DELETE FROM lecture_sessions") 
        cur.execute("DELETE FROM lectures")
        conn.commit()
        print("  Cleared all existing lecture data")

        # Get all faculty
        cur.execute("SELECT f.id, f.user_id FROM faculty f")
        faculty_list = cur.fetchall()

        # Get students by semester
        students_by_semester = {}
        for sem in range(1, 7):
            cur.execute("SELECT id FROM students WHERE semester = ?", (str(sem),))
            students_by_semester[str(sem)] = [row[0] for row in cur.fetchall()]

        lecture_count = 0
        attendance_count = 0

        # Create 3 past lectures for each faculty_subject mapping, ensuring faculty has lectures for every semester they teach
        for faculty_db_id, faculty_user_id in faculty_list:
            # Get faculty subjects
            cur.execute("SELECT semester, subject FROM faculty_subjects WHERE faculty_id = ?", (faculty_db_id,))
            subjects = cur.fetchall()
            
            if not subjects:
                continue

            for semester, subject in subjects:
                for lecture_num in range(3):  # 3 lectures per faculty-subject mapping
                    # Random past date (2-20 days ago)
                    past_date = datetime.now() - timedelta(days=random.randint(2, 20))
                    lecture_date = past_date.strftime("%Y-%m-%d")

                    # Insert lecture for the specific subject and semester
                    cur.execute("""
                        INSERT INTO lectures (title, subject, date, faculty_id, latitude, longitude, radius)
                        VALUES (?, ?, ?, ?, 21.1702, 72.8311, 50)
                    """, (f"{subject} - Lecture {lecture_num+1}", subject, lecture_date, faculty_user_id))

                    lecture_id = cur.lastrowid

                    # Fixed time slots (manually set)
                    time_slots = [
                        ("09:00:00", "10:00:00"),
                        ("10:15:00", "11:15:00"),
                        ("12:00:00", "13:00:00"),
                        ("14:00:00", "15:00:00"),
                        ("15:15:00", "16:15:00"),
                    ]
                    start_time, end_time = random.choice(time_slots)

                    # Create session as CLOSED (already completed)
                    cur.execute("""
                        INSERT INTO lecture_sessions (lecture_id, start_time, end_time, attendance_type, threshold, status, mode, join_url, semester)
                        VALUES (?, ?, ?, 'LOCATION', 0, 'closed', 'OFFLINE', '', ?)
                    """, (lecture_id, start_time, end_time, semester))

                    session_id = cur.lastrowid

                    # Create attendance with BETTER distribution
                    semester_students = students_by_semester.get(semester, [])
                    
                    for student_id in semester_students:
                        # BETTER: 70% present, 15% late, 15% absent
                        rand = random.random()
                        if rand < 0.70:
                            attendance_type = "present"
                        elif rand < 0.85:
                            attendance_type = "late"
                        else:
                            attendance_type = "absent"

                        # Generate join times
                        start_dt = datetime.strptime(start_time, "%H:%M:%S")
                        
                        if attendance_type == "present":
                            # Join within 0-5 minutes of start
                            join_delay = random.randint(0, 5)
                        elif attendance_type == "late":
                            # Join 6-25 minutes after start
                            join_delay = random.randint(6, 25)
                        else:
                            # Absent - no valid join time, use start time
                            join_delay = 0

                        join_time = (start_dt + timedelta(minutes=join_delay)).strftime("%H:%M:%S")
                        
                        # Exit time - stay for 45-60 minutes (or full lecture if present)
                        if attendance_type in ["present", "late"]:
                            exit_delay = random.randint(45, 60)
                            exit_time = (start_dt + timedelta(minutes=join_delay + exit_delay)).strftime("%H:%M:%S")
                        else:
                            exit_time = start_time  # No exit for absent

                        # Insert attendance record
                        cur.execute("""
                            INSERT INTO attendance (student_id, session_id, latitude, longitude, status, start_time, end_time, timestamp)
                            VALUES (?, ?, 21.1702, 72.8311, ?, ?, ?, ?)
                        """, (student_id, session_id, attendance_type, join_time, exit_time, join_time))

                        attendance_count += 1

                    lecture_count += 1

        conn.commit()
        
        # Get updated counts
        cur.execute("SELECT COUNT(*) FROM lectures")
        total_lectures = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM attendance")
        total_attendance = cur.fetchone()[0]
        
        # Check attendance distribution
        cur.execute("SELECT status, COUNT(*) FROM attendance GROUP BY status")
        distribution = cur.fetchall()
        
        print(f"\nSuccessfully regenerated attendance data!")
        print(f"   Created {lecture_count} new lectures")
        print(f"   Created {attendance_count} new attendance records")
        print(f"\nDatabase Summary:")
        print(f"   Total Lectures: {total_lectures}")
        print(f"   Total Attendance Records: {total_attendance}")
        print(f"\nAttendance Distribution:")
        for status, count in distribution:
            percentage = (count / total_attendance * 100) if total_attendance > 0 else 0
            print(f"   {status.upper()}: {count} ({percentage:.1f}%)")

    except Exception as e:
        conn.rollback()
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    regenerate_past_lectures()
