from flask import Blueprint, request, jsonify
from database import db

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/conversations', methods=['GET'])
def get_conversations():
    user_id = request.args.get('user_id')
    conversations = db.get_conversations(user_id) if user_id else []
    return jsonify({'conversations': conversations}), 200

@chat_bp.route('/messages/<user_id>', methods=['GET'])
def get_messages(user_id):
    limit = request.args.get('limit', 50, type=int)
    my_id = request.args.get('my_id')
    messages = db.get_messages(my_id, user_id, limit) if my_id else []
    return jsonify({'messages': messages}), 200

@chat_bp.route('/send', methods=['POST'])
def send_message():
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    message = data.get('message')
    images = data.get('images')
    
    if not receiver_id:
        return jsonify({'error': 'Receiver ID required'}), 400
    
    if not message and not images:
        return jsonify({'error': 'Message or image required'}), 400
    
    sender_id = data.get('sender_id')
    message_id = db.send_message(sender_id, receiver_id, message, images) if sender_id else None
    return jsonify({'id': message_id, 'sent': True}), 201

@chat_bp.route('/mark-read/<sender_id>', methods=['POST'])
def mark_as_read(sender_id):
    receiver_id = request.args.get('receiver_id')
    if not receiver_id:
        return jsonify({'error': 'receiver_id required'}), 400
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('''UPDATE messages SET is_read = 1 
                 WHERE sender_id = ? AND receiver_id = ? AND is_read = 0''',
              (sender_id, receiver_id))
    conn.commit()
    conn.close()
    return jsonify({'marked': True}), 200

@chat_bp.route('/unread-count', methods=['GET'])
def get_unread_count():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('SELECT SUM(unread_count) FROM conversations WHERE user1_id = ? OR user2_id = ?',
              (user_id, user_id))
    result = c.fetchone()
    conn.close()
    return jsonify({'unread': result[0] or 0}), 200