import sqlite3

# Delete from source database
db_path = r'c:\Users\User\Downloads\SAS_2.0 (3)\SAS_2.0\backend\app.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Delete the lecture and its sessions
cur.execute('DELETE FROM attendance WHERE session_id IN (SELECT id FROM lecture_sessions WHERE lecture_id = 14)')
cur.execute('DELETE FROM lecture_sessions WHERE lecture_id = 14')
cur.execute('DELETE FROM lectures WHERE id = 14')

conn.commit()
conn.close()
print('✅ Lecture deleted from source database')

# Delete from target database
db_path2 = r'D:\L.B.A.S\SAS_2.0\backend\app.db'
conn = sqlite3.connect(db_path2)
cur = conn.cursor()

cur.execute('DELETE FROM attendance WHERE session_id IN (SELECT id FROM lecture_sessions WHERE lecture_id = 14)')
cur.execute('DELETE FROM lecture_sessions WHERE lecture_id = 14')
cur.execute('DELETE FROM lectures WHERE id = 14')

conn.commit()
conn.close()
print('✅ Lecture deleted from target database')
