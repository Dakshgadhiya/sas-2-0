import os
import sys
import sqlite3

# Ensure project root is in path
BASE_DIR = os.getcwd()
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Add the backend directory to path
sys.path.append(os.path.join(BASE_DIR, 'backend'))

from database import get_db

def verify_specific_faculty():
    print("🔍 Verifying Specific Faculty Data")
    print("=" * 50)

    conn = get_db()
    cur = conn.cursor()

    try:
        # Get all faculty with their subjects
        cur.execute("""
            SELECT u.name, f.faculty_id, u.email, fs.semester, fs.subject
            FROM users u
            JOIN faculty f ON u.id = f.user_id
            JOIN faculty_subjects fs ON f.id = fs.faculty_id
            WHERE u.role = 'faculty'
            ORDER BY u.name, fs.semester, fs.subject
        """)

        faculty_data = cur.fetchall()

        # Group by faculty
        faculty_groups = {}
        for row in faculty_data:
            name, faculty_id, email, semester, subject = row
            key = (name, faculty_id, email)
            if key not in faculty_groups:
                faculty_groups[key] = []
            faculty_groups[key].append((semester, subject))

        print(f"✅ Found {len(faculty_groups)} faculty members:")
        print()

        for (name, faculty_id, email), subjects in faculty_groups.items():
            print(f"👨‍🏫 {name} ({faculty_id})")
            print(f"   📧 {email}")
            print("   📚 Subjects:")
            for semester, subject in sorted(subjects, key=lambda x: int(x[0])):
                print(f"      • Sem {semester}: {subject}")
            print()

        # Count students
        cur.execute("SELECT COUNT(*) FROM students")
        student_count = cur.fetchone()[0]

        # Count lectures
        cur.execute("SELECT COUNT(*) FROM lectures")
        lecture_count = cur.fetchone()[0]

        # Count attendance
        cur.execute("SELECT COUNT(*) FROM attendance")
        attendance_count = cur.fetchone()[0]

        print("=" * 50)
        print("📊 Database Summary:")
        print(f"   • Students: {student_count}")
        print(f"   • Faculty: {len(faculty_groups)}")
        print(f"   • Lectures: {lecture_count}")
        print(f"   • Attendance Records: {attendance_count}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    verify_specific_faculty()