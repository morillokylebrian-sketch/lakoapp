from flask import Blueprint, request, jsonify
from database import db

sync_bp = Blueprint('sync', __name__)

@sync_bp.route('/pull', methods=['GET'])
def pull_changes():
    """Pull all changed data from server"""
    try:
        since = request.args.get('since', None)
        
        changes = {
            'posts': db.get_posts(since=since) if hasattr(db, 'get_posts') else [],
            'vendors': db.get_vendors(since=since) if hasattr(db, 'get_vendors') else [],
            'products': db.get_products(since=since) if hasattr(db, 'get_products') else [],
            'reviews': db.get_reviews(since=since) if hasattr(db, 'get_reviews') else [],
            'timestamp': db.get_current_timestamp() if hasattr(db, 'get_current_timestamp') else None
        }
        
        return jsonify(changes), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/push', methods=['POST'])
def push_changes():
    """Push local changes to server"""
    try:
        data = request.get_json()
        changes = data.get('changes', [])
        
        results = []
        for change in changes:
            action = change.get('action')
            model = change.get('model')
            obj_data = change.get('data', {})
            
            try:
                if action == 'create':
                    if model == 'post':
                        result = db.create_post(obj_data)
                    elif model == 'review':
                        result = db.create_review(obj_data)
                    else:
                        result = {'error': f'Unknown model: {model}'}
                
                elif action == 'update':
                    if model == 'post':
                        result = db.update_post(obj_data.get('id'), obj_data)
                    elif model == 'profile':
                        result = db.update_user_profile(obj_data)
                    else:
                        result = {'error': f'Unknown model: {model}'}
                
                elif action == 'delete':
                    if model == 'post':
                        result = db.delete_post(obj_data.get('id'))
                    else:
                        result = {'error': f'Cannot delete {model}'}
                
                else:
                    result = {'error': f'Unknown action: {action}'}
                
                results.append({'success': True, **result})
            
            except Exception as e:
                results.append({'success': False, 'error': str(e)})
        
        return jsonify({'results': results}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/status', methods=['GET'])
def sync_status():
    """Get sync status"""
    try:
        status = {
            'synced': True,
            'last_sync': db.get_user_last_sync() if hasattr(db, 'get_user_last_sync') else None,
            'pending_changes': db.get_pending_changes() if hasattr(db, 'get_pending_changes') else [],
            'timestamp': db.get_current_timestamp() if hasattr(db, 'get_current_timestamp') else None
        }
        
        return jsonify(status), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

