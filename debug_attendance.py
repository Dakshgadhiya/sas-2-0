import sqlite3

conn = sqlite3.connect('backend/app.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get all students
print("=== STUDENTS ===")
cur.execute("SELECT id, user_id, semester, roll_number FROM students LIMIT 5")
students = cur.fetchall()
for s in students:
    print(f"Student ID: {s['id']}, User: {s['user_id']}, Semester: {s['semester']}, Roll: {s['roll_number']}")

# For first student, check their lectures
if students:
    student_id = students[0]['id']
    semester = students[0]['semester']
    print(f"\n=== LECTURES FOR SEMESTER {semester} ===")
    cur.execute("""
        SELECT l.id, l.title, l.subject, l.date, ls.id as session_id, ls.semester
        FROM lectures l
        JOIN lecture_sessions ls ON ls.lecture_id = l.id
        WHERE ls.semester = ?
        LIMIT 5
    """, (semester,))
    lectures = cur.fetchall()
    if lectures:
        for lec in lectures:
            print(f"Lecture: {lec['title']}, Subject: {lec['subject']}, Session: {lec['session_id']}")
    else:
        print("NO LECTURES FOUND FOR THIS SEMESTER")
    
    # Check attendance records for this student
    print(f"\n=== ATTENDANCE FOR STUDENT {student_id} ===")
    cur.execute("SELECT id, session_id, status FROM attendance WHERE student_id = ? LIMIT 5", (student_id,))
    attendance = cur.fetchall()
    if attendance:
        for att in attendance:
            print(f"Attendance: Session {att['session_id']}, Status: {att['status']}")
    else:
        print("NO ATTENDANCE RECORDS")

conn.close()
