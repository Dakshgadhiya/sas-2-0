from backend.database import get_db, row_to_dict


def create_faculty(user_id, faculty_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO faculty (user_id, faculty_id) VALUES (?, ?)",
        (user_id, faculty_id),
    )
    conn.commit()
    faculty_row_id = cur.lastrowid
    conn.close()
    return faculty_row_id


def get_faculty_by_user_id(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM faculty WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)
