#!/usr/bin/env python3
"""
Migration script: normalize stored timestamps to UTC.

What it does:
- Backs up the current SQLite DB to app.db.bak
- For selected tables/columns, converts timestamps with non-UTC offsets (e.g. +05:30)
  to canonical UTC ISO strings (with +00:00).
- For timestamps that already include an offset, they are converted to UTC.
- For naive timestamps (no offset), this script will append +00:00 to mark them as UTC.

Run: python migrate_timestamps_to_utc.py
"""
from datetime import datetime, timezone, timedelta
import sqlite3
import shutil
import os
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BASE_DIR, "backend", "app.db")

IST = timezone(timedelta(hours=5, minutes=30))

TABLE_COLUMNS = {
    'lecture_sessions': ['start_time', 'end_time'],
    'attendance': ['timestamp', 'start_time', 'end_time'],
    'notifications': ['created_at']
}


def parse_iso_with_guess(s: str):
    """Parse an ISO timestamp string, guessing timezone when needed.

    Rules:
    - If string contains '+05:30' (or +0530 variant) treat as IST and convert to UTC.
    - If string contains any offset (e.g. +02:00, -07:00) parse and convert to UTC.
    - If string ends with 'Z' parse as UTC.
    - If string has no offset, assume it's UTC and append +00:00.
    """
    if s is None:
        return None
    t = s.strip()
    if t == "":
        return None

    # Normalize +0530 -> +05:30
    t = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", t)

    # If contains +05:30 specifically, parse as aware then convert to UTC
    try:
        if '+05:30' in t:
            dt = datetime.fromisoformat(t)
            return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()

        # If has any offset or Z
        if re.search(r"[Zz]$|[+-]\d{2}:\d{2}$", t):
            dt = datetime.fromisoformat(t)
            if dt.tzinfo is None:
                # Assume UTC
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()

        # Naive datetime: assume UTC and append +00:00
        dt = datetime.fromisoformat(t)
        dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()
    except Exception:
        return None


def backup_db(db_path):
    bak = db_path + '.bak'
    shutil.copy2(db_path, bak)
    print(f"Backed up DB to {bak}")


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return

    backup_db(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    total_updates = 0

    for table, cols in TABLE_COLUMNS.items():
        # Check table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if not cur.fetchone():
            continue

        col_list = ", ".join(cols)
        cur.execute(f"SELECT id, {col_list} FROM {table}")
        rows = cur.fetchall()
        updates = 0
        for row in rows:
            id_ = row['id']
            updates_set = {}
            for col in cols:
                val = row[col]
                if val is None:
                    continue
                new = parse_iso_with_guess(val)
                if new and new != val:
                    updates_set[col] = new
            if updates_set:
                set_clause = ", ".join([f"{c} = ?" for c in updates_set.keys()])
                params = list(updates_set.values()) + [id_]
                sql = f"UPDATE {table} SET {set_clause} WHERE id = ?"
                cur.execute(sql, params)
                updates += 1
        if updates:
            print(f"Updated {updates} rows in {table}")
        total_updates += updates

    conn.commit()
    conn.close()
    print(f"Migration complete. Total rows updated: {total_updates}")


if __name__ == '__main__':
    migrate()
