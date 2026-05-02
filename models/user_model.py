from backend.database import get_db, row_to_dict


def create_user(name, email, password, role):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
        (name, email, password, role),
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return user_id


def delete_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_user_by_email(email):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)


def get_user_by_id(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)


def get_all_students():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.name, u.email, s.roll_number, s.department, s.semester
        FROM users u
        JOIN students s ON u.id = s.user_id
        WHERE u.role = 'student'
    """)
    rows = cur.fetchall()
    conn.close()
    return [row_to_dict(row) for row in rows]
