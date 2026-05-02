#!/usr/bin/env python3
"""
Script to clear all student, faculty, and lecture records from the database.
Keeps the database structure but removes all data records.
"""

import sqlite3
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "backend", "sas.db")

def clear_database():
    """Clear all student, faculty, and lecture records from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("Clearing database records...")
        
        # Disable foreign key constraints temporarily
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # List of tables to clear (if they exist)
        tables_to_clear = [
            "attendance",
            "lecture_sessions",
            "faculty_subjects",
            "faculty",
            "students",
            "notifications"
        ]
        
        # Get existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        # Clear each table that exists
        for table in tables_to_clear:
            if table in existing_tables:
                cursor.execute(f"DELETE FROM {table}")
                print(f"✓ Cleared {table} records")
            else:
                print(f"- {table} table doesn't exist (skipped)")
        
        # Re-enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("\n✅ Database successfully cleared!")
        print("Database structure preserved, all records removed.")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Database file not found at: {DB_PATH}")
        print("Note: Run the backend application first to create the database.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    confirm = input("⚠️  WARNING: This will delete ALL student, faculty, and lecture records!\nType 'YES' to confirm: ")
    if confirm == "YES":
        clear_database()
    else:
        print("❌ Operation cancelled.")
