import sqlite3
from datetime import datetime

db_path = r'c:\Users\User\Downloads\SAS_2.0 (3)\SAS_2.0\backend\app.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print('=== LECTURES TABLE ===')
cur.execute('SELECT id, title, subject, date, faculty_id FROM lectures')
lectures = cur.fetchall()
if lectures:
    for lec in lectures:
        print(f'  ID: {lec[0]}, Title: {lec[1]}, Subject: {lec[2]}, Date: {lec[3]}, Faculty: {lec[4]}')
else:
    print('  No lectures found')

print()
print('=== LECTURE_SESSIONS TABLE ===')
cur.execute('SELECT id, lecture_id, start_time, end_time, status FROM lecture_sessions')
sessions = cur.fetchall()
if sessions:
    for ses in sessions:
        print(f'  ID: {ses[0]}, Lecture: {ses[1]}, Start: {ses[2]}, End: {ses[3]}, Status: {ses[4]}')
else:
    print('  No sessions found')

print()
print('=== USERS TABLE (FACULTY) ===')
cur.execute('SELECT id, name, email, role FROM users WHERE role = ?', ('faculty',))
users = cur.fetchall()
if users:
    for user in users:
        print(f'  ID: {user[0]}, Name: {user[1]}, Email: {user[2]}, Role: {user[3]}')
else:
    print('  No faculty found')

conn.close()
