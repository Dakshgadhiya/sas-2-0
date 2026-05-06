import sqlite3

conn = sqlite3.connect('backend/app.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print('Tables in database:')
for table in tables:
    print(f'  - {table[0]}')

# Check if we have data
if tables:
    for table_name in [t[0] for t in tables]:
        try:
            cur.execute(f'SELECT COUNT(*) FROM {table_name}')
            count = cur.fetchone()[0]
            print(f'  {table_name}: {count} records')
        except Exception as e:
            print(f'  {table_name}: error - {e}')

conn.close()