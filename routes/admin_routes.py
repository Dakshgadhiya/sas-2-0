from flask import Blueprint, jsonify, request
from backend.database import get_db
import sqlite3

admin_routes = Blueprint("admin_routes", __name__)

@admin_routes.route("/api/admin/reset-database", methods=["POST"])
def reset_database():
    """
    DANGEROUS: Delete all students, faculty, lectures, attendance data.
    Keeps the schema intact for fresh testing.
    """
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Delete data in order to respect foreign keys
        cur.execute("DELETE FROM attendance")
        cur.execute("DELETE FROM lecture_sessions")
        cur.execute("DELETE FROM lectures")
        cur.execute("DELETE FROM faculty_subjects")
        cur.execute("DELETE FROM faculty")
        cur.execute("DELETE FROM students")
        cur.execute("DELETE FROM users WHERE role IN ('student', 'faculty')")
        
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Database reset successfully. All user data deleted."}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to reset database: {str(e)}"}), 500
