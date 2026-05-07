from flask import Blueprint, request, jsonify, g
from backend.auth_utils import hash_password, verify_password, generate_token, auth_required
from backend.database import get_db
from models.user_model import create_user, get_user_by_email, get_user_by_id, delete_user
from models.faculty_model import create_faculty

import json
import sqlite3
from backend.database import DBIntegrityError

auth_routes = Blueprint("auth_routes", __name__)


def _normalize_role(role):
    return (role or "").strip().lower()


@auth_routes.route("/api/auth/register", methods=["POST"])
def register():
    data = request.json or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = _normalize_role(data.get("role", "student"))

    if not name or not email or not password or role not in ["student", "faculty"]:
        return jsonify({"error": "Invalid payload"}), 400

    # Check if email already exists (for any role)
    existing_user = get_user_by_email(email)
    if existing_user:
        return jsonify({"error": "Email already registered. Please login."}), 409

    user_id = create_user(name, email, hash_password(password), role)

    if role == "student":
        enrollment_number = data.get("enrollment_number") or data.get("roll_number")
        department = data.get("department") or "Information Technology"
        semester = data.get("semester") or "1"
        if not enrollment_number:
            delete_user(user_id)
            return jsonify({"error": "Enrollment number is required"}), 400

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO students (user_id, roll_number, department, semester) VALUES (?, ?, ?, ?)",
                (user_id, enrollment_number, department, semester),
            )
            conn.commit()
        except (sqlite3.IntegrityError, DBIntegrityError):
            conn.rollback()
            # remove created user in same connection to avoid lock
            cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()
            return jsonify({"error": "Enrollment number already exists"}), 409
        finally:
            try:
                conn.close()
            except Exception:
                pass

    if role == "faculty":
        faculty_id = data.get("faculty_id")
        # Accept either new 'subjects' array of objects OR legacy 'subject' + 'semesters' fields
        subjects = data.get("subjects") or []  # List of {semester, subject} objects
        if not subjects and data.get("subject") and data.get("semesters"):
            try:
                legacy_semesters = data.get("semesters") or []
                subjects = [{"semester": str(s), "subject": data.get("subject")} for s in legacy_semesters]
            except Exception:
                subjects = []
        department = data.get("department") or "Information Technology"
        
        if not faculty_id:
            delete_user(user_id)
            return jsonify({"error": "Faculty ID is required"}), 400
        
        # Validate odd/even semester constraints
        for subj in subjects:
            semester = subj.get("semester", "1")
            # Odd semesters: 1, 3, 5; Even semesters: 2, 4, 6
            sem_num = int(semester) if semester.isdigit() else 1
            if sem_num % 2 == 1:  # Odd semester
                if sem_num not in [1, 3, 5]:
                    delete_user(user_id)
                    return jsonify({"error": f"Invalid odd semester: {semester}"}), 400
            else:  # Even semester
                if sem_num not in [2, 4, 6]:
                    delete_user(user_id)
                    return jsonify({"error": f"Invalid even semester: {semester}"}), 400
        
        try:
            conn = get_db()
            cur = conn.cursor()
            # Create faculty record with department
            cur.execute(
                "INSERT INTO faculty (user_id, faculty_id, department) VALUES (?, ?, ?)",
                (user_id, faculty_id, department),
            )
            faculty_db_id = cur.lastrowid
            
            # Insert subject assignments for each semester
            for subj in subjects:
                semester = subj.get("semester", "1")
                subject = subj.get("subject", "General")
                cur.execute(
                    "INSERT OR IGNORE INTO faculty_subjects (faculty_id, semester, subject) VALUES (?, ?, ?)",
                    (faculty_db_id, semester, subject),
                )

            # If faculty table has a 'subject' column, populate it with legacy single-subject value
            try:
                cur.execute("PRAGMA table_info(faculty)")
                cols = [r[1] for r in cur.fetchall()]
                if 'subject' in cols and data.get('subject'):
                    cur.execute("UPDATE faculty SET subject = ? WHERE id = ?", (data.get('subject'), faculty_db_id))
            except Exception:
                pass
            
            conn.commit()
            conn.close()
        except (sqlite3.IntegrityError, DBIntegrityError):
            delete_user(user_id)
            return jsonify({"error": "Faculty ID already exists"}), 409

    token = generate_token(user_id, role)
    return jsonify({"token": token, "user_id": user_id, "role": role})


@auth_routes.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")

    user = get_user_by_email(email)
    if not user or not verify_password(password, user["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    role = (user["role"] or "").lower()
    token = generate_token(user["id"], role)
    return jsonify({"token": token, "user": {"id": user["id"], "name": user["name"], "role": role}})


@auth_routes.route("/api/auth/me", methods=["GET"])
@auth_required()
def me():
    user = get_user_by_id(g.user_id)
    if user and "role" in user:
        user["role"] = (user["role"] or "").lower()
    return jsonify({"user": user})


@auth_routes.route("/api/student/profile", methods=["GET"])
@auth_required(role="student")
def student_profile_get():
    """Get student profile including personal and academic details"""
    conn = get_db()
    cur = conn.cursor()
    
    # Get user info
    user = get_user_by_id(g.user_id)
    
    # Get student info
    cur.execute("""
        SELECT roll_number, department, semester
        FROM students
        WHERE user_id = ?
    """, (g.user_id,))
    student_row = cur.fetchone()
    conn.close()
    
    if not student_row:
        return jsonify({"error": "Student record not found"}), 404
    
    profile = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "roll_number": student_row[0],
        "department": student_row[1],
        "semester": student_row[2]
    }
    
    return jsonify({"profile": profile})


@auth_routes.route("/api/student/profile", methods=["PUT"])
@auth_required(role="student")
def student_profile_put():
    """Update student profile - ONLY name and email can be edited"""
    data = request.json or {}
    
    conn = get_db()
    cur = conn.cursor()
    
    # Only allow name and email updates (lock department, semester, enrollment number)
    if "name" in data or "email" in data:
        updates = []
        params = []
        if "name" in data:
            updates.append("name = ?")
            params.append(data["name"])
        if "email" in data:
            updates.append("email = ?")
            params.append(data["email"])
        
        params.append(g.user_id)
        cur.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", tuple(params))
    
    # Silently ignore attempts to update department, semester, or enrollment_number
    # These fields are locked and cannot be changed after signup
    
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Profile updated successfully"})


@auth_routes.route("/api/faculty/profile", methods=["GET"])
@auth_required(role="faculty")
def faculty_profile_get():
    """Get faculty profile including subject assignments by semester"""
    conn = get_db()
    cur = conn.cursor()
    
    # Get user info
    user = get_user_by_id(g.user_id)
    
    # Get faculty info
    cur.execute("""
        SELECT id, faculty_id, department FROM faculty WHERE user_id = ?
    """, (g.user_id,))
    faculty_row = cur.fetchone()
    
    if not faculty_row:
        conn.close()
        return jsonify({"error": "Faculty record not found"}), 404
    
    faculty_id_db = faculty_row[0]
    faculty_id = faculty_row[1]
    department = faculty_row[2]
    
    # Get all subject assignments (semester + subject pairs)
    cur.execute("""
        SELECT semester, subject FROM faculty_subjects WHERE faculty_id = ? ORDER BY semester
    """, (faculty_id_db,))
    subjects = [{"semester": row[0], "subject": row[1]} for row in cur.fetchall()]
    
    conn.close()
    
    profile = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "faculty_id": faculty_id,
        "department": department,
        "subjects": subjects
    }
    # Provide legacy compatibility fields: single 'subject' and 'semesters' string
    legacy_subject = subjects[0]["subject"] if subjects else None
    legacy_semesters = ", ".join([s["semester"] for s in subjects]) if subjects else None

    # Attach legacy keys for older clients/tests
    profile["subject"] = legacy_subject
    profile["semesters"] = legacy_semesters

    return jsonify({"profile": profile})


@auth_routes.route("/api/faculty/profile", methods=["PUT"])
@auth_required(role="faculty")
def faculty_profile_put():
    """Update faculty profile - name, email, department, and subject assignments"""
    data = request.json or {}
    
    conn = get_db()
    cur = conn.cursor()
    
    # Update name and email in users table
    if "name" in data or "email" in data:
        updates = []
        params = []
        if "name" in data:
            updates.append("name = ?")
            params.append(data["name"])
        if "email" in data:
            updates.append("email = ?")
            params.append(data["email"])
        
        params.append(g.user_id)
        cur.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", tuple(params))
    
    # Update faculty details (department)
    if "department" in data:
        cur.execute("UPDATE faculty SET department = ? WHERE user_id = ?", (data["department"], g.user_id))
    
    # Update subject assignments if provided
    if "subjects" in data:
        cur.execute("SELECT id FROM faculty WHERE user_id = ?", (g.user_id,))
        faculty_row = cur.fetchone()
        if faculty_row:
            faculty_id_db = faculty_row[0]
            
            # Validate odd/even semester constraints
            for subj in data["subjects"]:
                semester = subj.get("semester", "1")
                sem_num = int(semester) if semester.isdigit() else 1
                if sem_num % 2 == 1:  # Odd semester
                    if sem_num not in [1, 3, 5]:
                        conn.close()
                        return jsonify({"error": f"Invalid odd semester: {semester}"}), 400
                else:  # Even semester
                    if sem_num not in [2, 4, 6]:
                        conn.close()
                        return jsonify({"error": f"Invalid even semester: {semester}"}), 400
            
            # Clear existing subjects and insert new ones
            cur.execute("DELETE FROM faculty_subjects WHERE faculty_id = ?", (faculty_id_db,))
            for subj in data["subjects"]:
                semester = subj.get("semester", "1")
                subject = subj.get("subject", "General")
                cur.execute(
                    "INSERT OR IGNORE INTO faculty_subjects (faculty_id, semester, subject) VALUES (?, ?, ?)",
                    (faculty_id_db, semester, subject)
                )
    
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Profile updated successfully"})


@auth_routes.route("/api/user/delete-account", methods=["DELETE"])
@auth_required()
def delete_account():
    """Permanently delete user account and all related data"""
    user_id = g.user_id
    role = g.role.lower() if g.role else "student"
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        if role == "student":
            # Get student_id from students table
            cur.execute("SELECT id FROM students WHERE user_id = ?", (user_id,))
            student_row = cur.fetchone()
            
            if student_row:
                student_id = student_row[0]
                # Delete attendance records for this student
                cur.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
                # Delete student record
                cur.execute("DELETE FROM students WHERE id = ?", (student_id,))
        
        elif role == "faculty":
            # Get faculty_id from faculty table
            cur.execute("SELECT id FROM faculty WHERE user_id = ?", (user_id,))
            faculty_row = cur.fetchone()
            
            if faculty_row:
                faculty_id = faculty_row[0]
                
                # Delete attendance records from all this faculty's lectures
                cur.execute("""
                    DELETE FROM attendance WHERE session_id IN (
                        SELECT ls.id FROM lecture_sessions ls
                        JOIN lectures l ON l.id = ls.lecture_id
                        WHERE l.faculty_id = ?
                    )
                """, (faculty_id,))
                
                # Delete all lecture_sessions from this faculty's lectures
                cur.execute("""
                    DELETE FROM lecture_sessions WHERE lecture_id IN (
                        SELECT id FROM lectures WHERE faculty_id = ?
                    )
                """, (faculty_id,))
                
                # Delete all lectures created by this faculty
                cur.execute("DELETE FROM lectures WHERE faculty_id = ?", (faculty_id,))
                
                # Delete faculty_subjects assignments
                cur.execute("DELETE FROM faculty_subjects WHERE faculty_id = ?", (faculty_id,))
                
                # Delete faculty record
                cur.execute("DELETE FROM faculty WHERE id = ?", (faculty_id,))
        
        # Finally, delete the user record
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Account deleted successfully"}), 200
    
    except Exception as e:
        conn.close()
        return jsonify({"error": f"Failed to delete account: {str(e)}"}), 500

