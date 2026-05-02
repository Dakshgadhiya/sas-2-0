from datetime import datetime
from backend.database import get_db

def create_notification(student_id, message, type_='info', related_session_id=None):
    """Create a new notification for a student"""
    conn = get_db()
    cur = conn.cursor()
    created_at = datetime.now().isoformat()
    
    cur.execute("""
        INSERT INTO notifications (student_id, message, type, related_session_id, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (student_id, message, type_, related_session_id, created_at))
    
    conn.commit()
    notification_id = cur.lastrowid
    conn.close()
    
    return notification_id

def get_student_notifications(student_id, limit=50):
    """Get recent notifications for a student"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, student_id, message, type, related_session_id, is_read, created_at
        FROM notifications
        WHERE student_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (student_id, limit))
    
    rows = cur.fetchall()
    conn.close()
    
    return [dict(row) for row in rows] if rows else []

def mark_notification_read(notification_id):
    """Mark a notification as read"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE notifications SET is_read = 1 WHERE id = ?
    """, (notification_id,))
    
    conn.commit()
    conn.close()

def get_unread_count(student_id):
    """Get count of unread notifications"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT COUNT(*) as count FROM notifications
        WHERE student_id = ? AND is_read = 0
    """, (student_id,))
    
    result = cur.fetchone()
    conn.close()
    
    return result['count'] if result else 0
