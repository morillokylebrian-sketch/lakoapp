from flask import Blueprint, request, jsonify
from database import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/stats', methods=['GET'])
def get_stats():
    stats = db.get_stats()
    return jsonify(stats), 200

@admin_bp.route('/users', methods=['GET'])
def get_users():
    role = request.args.get('role')
    users = db.get_all_users(role)
    return jsonify({'users': users}), 200

@admin_bp.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = db.get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user}), 200

@admin_bp.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    db.delete_user(user_id)
    # db.log_activity: auth removed
    return jsonify({'deleted': True}), 200

@admin_bp.route('/users/<user_id>/suspend', methods=['POST'])
def suspend_user(user_id):
    data = request.get_json()
    reason = data.get('reason', 'Violation of terms')
    days = data.get('days')
    
    db.suspend_user(user_id, reason, days)
    # db.log_activity: auth removed
    return jsonify({'suspended': True}), 200

@admin_bp.route('/users/<user_id>/unsuspend', methods=['POST'])
def unsuspend_user(user_id):
    db.unsuspend_user(user_id)
    db.log_activity(request.user['id'], 'admin', 'unsuspend_user', target_type='user', target_id=user_id)
    return jsonify({'unsuspended': True}), 200

@admin_bp.route('/vendors', methods=['GET'])
def get_vendors():
    vendors = db.get_all_vendors()
    return jsonify({'vendors': vendors}), 200

@admin_bp.route('/vendors/<vendor_id>/toggle', methods=['POST'])
def toggle_vendor(vendor_id):
    data = request.get_json()
    is_active = data.get('is_active', True)
    
    db.toggle_vendor_active(vendor_id, 1 if is_active else 0)
    db.log_activity(request.user['id'], 'admin', 'toggle_vendor', target_type='vendor', target_id=vendor_id)
    return jsonify({'active': is_active}), 200

@admin_bp.route('/reviews', methods=['GET'])
def get_all_reviews():
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('''SELECT r.*, u.full_name as customer_name, v.business_name as vendor_name 
                 FROM reviews r JOIN users u ON r.customer_id = u.id 
                 JOIN vendors v ON r.vendor_id = v.id ORDER BY r.created_at DESC''')
    reviews = c.fetchall()
    conn.close()
    return jsonify({'reviews': [dict(r) for r in reviews]}), 200

@admin_bp.route('/reviews/<review_id>/hide', methods=['POST'])
def hide_review(review_id):
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('UPDATE reviews SET is_hidden = 1 WHERE id = ?', (review_id,))
    conn.commit()
    conn.close()
    db.log_activity(request.user['id'], 'admin', 'hide_review', target_type='review', target_id=review_id)
    return jsonify({'hidden': True}), 200

@admin_bp.route('/reviews/<review_id>/unhide', methods=['POST'])
def unhide_review(review_id):
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('UPDATE reviews SET is_hidden = 0 WHERE id = ?', (review_id,))
    conn.commit()
    conn.close()
    return jsonify({'unhidden': True}), 200

@admin_bp.route('/posts', methods=['GET'])
def get_all_posts():
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('''SELECT p.*, u.full_name as user_name FROM posts p 
                 JOIN users u ON p.user_id = u.id ORDER BY p.created_at DESC''')
    posts = c.fetchall()
    conn.close()
    return jsonify({'posts': [dict(p) for p in posts]}), 200

@admin_bp.route('/posts/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    db.delete_post(post_id)
    db.log_activity(request.user['id'], 'admin', 'delete_post', target_type='post', target_id=post_id)
    return jsonify({'deleted': True}), 200

@admin_bp.route('/activities', methods=['GET'])
def get_all_activities():
    limit = request.args.get('limit', 100, type=int)
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM activities ORDER BY created_at DESC LIMIT ?', (limit,))
    activities = c.fetchall()
    conn.close()
    return jsonify({'activities': [dict(a) for a in activities]}), 200