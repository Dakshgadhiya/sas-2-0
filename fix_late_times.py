import sqlite3
from datetime import datetime, timedelta
import random

conn = sqlite3.connect('backend/app.db')
cur = conn.cursor()

cur.execute('SELECT a.id, ls.start_time, a.start_time FROM attendance a JOIN lecture_sessions ls ON a.session_id = ls.id WHERE a.status = "late" AND a.start_time IS NOT NULL')
late_records = cur.fetchall()
print(f'Found {len(late_records)} late records')

updated = 0
for record_id, session_start, current_start in late_records:
    start_dt = datetime.fromisoformat(session_start)
    if current_start == session_start:
        late_minutes = random.randint(5, 25)
        late_seconds = random.randint(0, 59)
        late_dt = start_dt + timedelta(minutes=late_minutes, seconds=late_seconds)
        new_start = late_dt.isoformat()
        cur.execute('UPDATE attendance SET start_time = ?, timestamp = ? WHERE id = ?', (new_start, new_start, record_id))
        updated += 1

conn.commit()
conn.close()
print(f'Updated {updated} late attendance times')