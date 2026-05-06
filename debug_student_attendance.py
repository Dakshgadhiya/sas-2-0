import sqlite3

conn = sqlite3.connect('backend/app.db')
cur = conn.cursor()

# Get unique student IDs with attendance records
cur.execute('SELECT DISTINCT student_id FROM attendance ORDER BY student_id LIMIT 15')
students_with_records = [row[0] for row in cur.fetchall()]
print(f'Students with attendance records: {students_with_records}')

# Get all student IDs
cur.execute('SELECT id FROM students ORDER BY id LIMIT 15')
all_students = [row[0] for row in cur.fetchall()]
print(f'All students (first 15): {all_students}')

# Check attendance record sample
cur.execute('SELECT student_id, session_id, status FROM attendance LIMIT 3')
for row in cur.fetchall():
    print(f'  Attendance: student={row[0]}, session={row[1]}, status={row[2]}')

# Get attendance count by student
cur.execute('SELECT student_id, COUNT(*) FROM attendance GROUP BY student_id')
records = cur.fetchall()
print(f'\nTotal students with records: {len(records)}')
if len(records) < 10:
    for row in records:
        print(f'  Student {row[0]}: {row[1]} records')

conn.close()
