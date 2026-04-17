from flask import Blueprint, request, jsonify
from auth import Auth
from database import db
from services.map_service import MapService
from services.suggestion_service import SuggestionService
from utils import check_profanity

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/feed', methods=['GET'])
def get_feed():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    
    posts = db.get_feed_posts(per_page, offset)
    return jsonify({'posts': posts, 'page': page}), 200

@customer_bp.route('/posts', methods=['POST'])
def create_post():
    data = request.get_json()
    content = data.get('content')
    images = data.get('images')
    user_id = data.get('user_id')
    user_role = data.get('user_role', 'customer')
    
    profanity = check_profanity(content)
    if profanity['has_profanity']:
        return jsonify({'error': 'Post contains inappropriate language'}), 400
    
    post_id = db.create_post(user_id, user_role, content, images)
    
    return jsonify({'id': post_id, 'message': 'Post created'}), 201

@customer_bp.route('/posts/<post_id>/like', methods=['POST'])
def like_post(post_id):
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    
    liked = db.like_post(post_id, user_id)
    return jsonify({'liked': liked}), 200

@customer_bp.route('/posts/<post_id>/replies', methods=['GET'])
def get_replies(post_id):
    replies = db.get_post_replies(post_id)
    return jsonify({'replies': replies}), 200

@customer_bp.route('/posts/<post_id>/replies', methods=['POST'])
def create_reply(post_id):
    data = request.get_json()
    user_id = data.get('user_id') or request.args.get('user_id')
    
    data = request.get_json()
    content = data.get('content')
    
    reply_id = db.create_post(user['id'], user['role'], content, parent_id=post_id)
    return jsonify({'id': reply_id}), 201

@customer_bp.route('/vendors/nearby', methods=['GET'])
def get_nearby_vendors():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', 10, type=float)
    category = request.args.get('category')
    
    vendors = MapService.get_nearby_vendors(lat, lng, radius, category)
    return jsonify({'vendors': vendors}), 200

@customer_bp.route('/vendors/<vendor_id>', methods=['GET'])
def get_vendor(vendor_id):
    token = request.headers.get('X-Session-Token')
    user = Auth.get_user_by_token(token)
    
    vendor = db.get_vendor_by_id(vendor_id)
    if not vendor:
        return jsonify({'error': 'Vendor not found'}), 404
    
    db.increment_traffic(vendor_id)
    
    if user:
        db.log_traffic(vendor_id, user['id'], user.get('latitude'), user.get('longitude'), 'view')
    
    products = db.get_products_by_vendor(vendor_id)
    reviews = db.get_reviews_by_vendor(vendor_id)
    
    is_shortlisted = False
    if user:
        is_shortlisted = db.is_shortlisted(user['id'], vendor_id)
    
    return jsonify({
        'vendor': vendor,
        'products': products,
        'reviews': reviews,
        'is_shortlisted': is_shortlisted
    }), 200

@customer_bp.route('/reviews', methods=['POST'])
def create_review():
    token = request.headers.get('X-Session-Token')
    user = Auth.get_user_by_token(token)
    
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    vendor_id = data.get('vendor_id')
    rating = data.get('rating')
    title = data.get('title')
    comment = data.get('comment')
    product_id = data.get('product_id')
    
    if not vendor_id or not rating:
        return jsonify({'error': 'Vendor ID and rating required'}), 400
    
    profanity = check_profanity(comment)
    if profanity['has_profanity']:
        return jsonify({'error': 'Review contains inappropriate language'}), 400
    
    review_id = db.create_review(user['id'], vendor_id, rating, title, comment, product_id)
    db.log_activity(user['id'], user['role'], 'create_review', target_type='review', target_id=review_id)
    
    return jsonify({'id': review_id}), 201

@customer_bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')
    
    results = {}
    if search_type in ['all', 'vendors']:
        results['vendors'] = db.search_vendors(query)
    if search_type in ['all', 'products']:
        results['products'] = db.search_products(query)
    
    return jsonify(results), 200

@customer_bp.route('/shortlist', methods=['GET'])
def get_shortlist():
    token = request.headers.get('X-Session-Token')
    user = Auth.get_user_by_token(token)
    
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    vendors = db.get_shortlist(user['id'])
    return jsonify({'shortlist': vendors}), 200

@customer_bp.route('/shortlist/<vendor_id>', methods=['POST'])
def add_to_shortlist(vendor_id):
    token = request.headers.get('X-Session-Token')
    user = Auth.get_user_by_token(token)
    
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    added = db.add_to_shortlist(user['id'], vendor_id)
    return jsonify({'added': added}), 200

@customer_bp.route('/shortlist/<vendor_id>', methods=['DELETE'])
def remove_from_shortlist(vendor_id):
    token = request.headers.get('X-Session-Token')
    user = Auth.get_user_by_token(token)
    
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    db.remove_from_shortlist(user['id'], vendor_id)
    return jsonify({'removed': True}), 200

@customer_bp.route('/activities', methods=['GET'])
def get_activities():
    token = request.headers.get('X-Session-Token')
    user = Auth.get_user_by_token(token)
    
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    limit = request.args.get('limit', 50, type=int)
    activities = db.get_user_activities(user['id'], limit)
    return jsonify({'activities': activities}), 200

@customer_bp.route('/suggestions', methods=['GET'])
def get_suggestions():
    token = request.headers.get('X-Session-Token')
    user = Auth.get_user_by_token(token)
    
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get vendor suggestions based on preferences
    vendor_suggestions = SuggestionService.get_vendor_suggestions(user['id'], limit=10)
    
    # Get product suggestions based on preferences
    product_suggestions = SuggestionService.get_product_suggestions(user['id'], limit=10)
    
    return jsonify({
        'vendors': vendor_suggestions,
        'products': product_suggestions
    }), 200

@customer_bp.route('/heatmap', methods=['GET'])
def get_heatmap():
    data = MapService.get_heatmap_data()
    return jsonify({'points': data}), 200