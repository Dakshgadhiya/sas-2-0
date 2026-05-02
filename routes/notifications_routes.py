from flask import Blueprint, request, jsonify, g
from backend.auth_utils import auth_required
from backend.database import get_db
from models.notifications_model import (
    create_notification,
    get_student_notifications,
    mark_notification_read,
    get_unread_count
)

notifications_routes = Blueprint('notifications_routes', __name__)

@notifications_routes.route('/api/notifications', methods=['GET'], endpoint='list_notifications')
@auth_required
def get_notifications():
    """Fetch all notifications for a student with optional limit"""
    try:
        limit = request.args.get('limit', 50, type=int)
        notifications = get_student_notifications(g.user_id, limit=limit)
        return jsonify({
            'success': True,
            'notifications': notifications
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_routes.route('/api/notifications/unread-count', methods=['GET'], endpoint='unread_count')
@auth_required
def get_unread_notifications_count():
    """Get count of unread notifications for a student"""
    try:
        count = get_unread_count(g.user_id)
        return jsonify({
            'success': True,
            'unread_count': count
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_routes.route('/api/notifications/<int:notification_id>/read', methods=['POST'], endpoint='mark_read')
@auth_required
def mark_as_read(notification_id):
    """Mark a notification as read (with ownership verification)"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Verify ownership
        cursor.execute('SELECT student_id FROM notifications WHERE id = ?', (notification_id,))
        notification = cursor.fetchone()
        
        if not notification or notification[0] != g.user_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        mark_notification_read(notification_id)
        return jsonify({'success': True, 'message': 'Notification marked as read'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_routes.route('/api/notifications/broadcast', methods=['POST'], endpoint='broadcast')
@auth_required(role='faculty')
def broadcast_notification():
    """Admin endpoint to send notifications to all students of a semester"""
    try:
        data = request.get_json()
        semester = data.get('semester')
        message = data.get('message')
        notification_type = data.get('type', 'info')
        
        if not semester or not message:
            return jsonify({'success': False, 'error': 'Missing semester or message'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        # Get all students in semester
        cursor.execute('SELECT id FROM students WHERE semester = ?', (semester,))
        students = cursor.fetchall()
        
        count = 0
        for student in students:
            create_notification(student[0], message, notification_type)
            count += 1
        
        return jsonify({
            'success': True,
            'message': f'Broadcast to {count} students',
            'count': count
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
