import sqlite3

conn = sqlite3.connect('backend/app.db')
cur = conn.cursor()

# Get attendance table schema
cur.execute("PRAGMA table_info(attendance)")
columns = cur.fetchall()
print("=== ATTENDANCE TABLE COLUMNS ===")
for col in columns:
    print(f"{col[1]}: {col[2]}")

conn.close()
