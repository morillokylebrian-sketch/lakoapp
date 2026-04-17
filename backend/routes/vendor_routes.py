from flask import Blueprint, request, jsonify
from database import db
from services.map_service import MapService
from services.suggestion_service import SuggestionService

vendor_bp = Blueprint('vendor', __name__)

@vendor_bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    vendor_id = request.args.get('vendor_id')
    if not vendor_id:
        vendors = db.get_all_vendors() if hasattr(db, 'get_all_vendors') else []
        if vendors:
            vendor = vendors[0]
        else:
            return jsonify({'error': 'No vendor found'}), 404
    else:
        vendor = db.get_vendor_by_id(vendor_id)
    
    if not vendor:
        return jsonify({'error': 'Vendor not found'}), 404
    
    products = db.get_products_by_vendor(vendor['id']) if hasattr(db, 'get_products_by_vendor') else []
    reviews = db.get_reviews_by_vendor(vendor['id']) if hasattr(db, 'get_reviews_by_vendor') else []
    
    stats = {
        'total_products': len(products),
        'total_reviews': len(reviews),
        'average_rating': vendor.get('rating', 0),
        'traffic_count': vendor.get('traffic_count', 0),
        'review_count': vendor.get('review_count', 0)
    }
    
    return jsonify({
        'vendor': vendor,
        'stats': stats,
        'recent_products': products[:5] if products else [],
        'recent_reviews': reviews[:5] if reviews else []
    }), 200

@vendor_bp.route('/products', methods=['GET'])
def get_products():
    vendor_id = request.args.get('vendor_id')
    if not vendor_id:
        return jsonify({'error': 'vendor_id required'}), 400
    
    products = db.get_products_by_vendor(vendor_id) if hasattr(db, 'get_products_by_vendor') else []
    return jsonify({'products': products}), 200

@vendor_bp.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    vendor_id = data.get('vendor_id')
    name = data.get('name')
    description = data.get('description')
    category = data.get('category')
    price = data.get('price')
    moq = data.get('moq')
    stock = data.get('stock', 0)
    images = data.get('images')
    
    if not name or not vendor_id:
        return jsonify({'error': 'Product name and vendor_id required'}), 400
    
    product_id = db.create_product(vendor_id, name, description, category, price, moq, stock, images)
    
    return jsonify({'id': product_id}), 201

@vendor_bp.route('/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json()
    db.update_product(product_id, **data)
    return jsonify({'updated': True}), 200

@vendor_bp.route('/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    db.delete_product(product_id)
    return jsonify({'deleted': True}), 200

@vendor_bp.route('/reviews', methods=['GET'])
def get_reviews():
    vendor_id = request.args.get('vendor_id')
    if not vendor_id:
        return jsonify({'error': 'vendor_id required'}), 400
    
    reviews = db.get_reviews_by_vendor(vendor_id) if hasattr(db, 'get_reviews_by_vendor') else []
    return jsonify({'reviews': reviews}), 200

@vendor_bp.route('/traffic', methods=['GET'])
def get_traffic():
    vendor_id = request.args.get('vendor_id')
    if not vendor_id:
        return jsonify({'error': 'vendor_id required'}), 400
    
    vendor = db.get_vendor_by_id(vendor_id)
    if not vendor:
        return jsonify({'error': 'Vendor not found'}), 404
    
    traffic_level = MapService.get_traffic_level(vendor_id) if hasattr(MapService, 'get_traffic_level') else 0
    
    return jsonify({
        'traffic_count': vendor.get('traffic_count', 0),
        'traffic_level': traffic_level
    }), 200

@vendor_bp.route('/profile', methods=['PUT'])
def update_profile():
    data = request.get_json()
    vendor_id = data.get('vendor_id')
    if not vendor_id:
        return jsonify({'error': 'vendor_id required'}), 400
    
    conn = db.get_connection()
    c = conn.cursor()
    
    fields = []
    values = []
    for k, v in data.items():
        if k in ['business_name', 'category', 'subcategory', 'description', 'address', 'phone', 'email', 'website', 'business_hours', 'logo', 'cover_image']:
            fields.append(f"{k} = ?")
            values.append(v)
    
    if fields:
        values.extend([vendor_id])
        c.execute(f"UPDATE vendors SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)
        conn.commit()
    
    conn.close()
    return jsonify({'updated': True}), 200

@vendor_bp.route('/analytics', methods=['GET'])
def get_analytics():
    vendor_id = request.args.get('vendor_id')
    if not vendor_id:
        return jsonify({'error': 'vendor_id required'}), 400
    
    vendor = db.get_vendor_by_id(vendor_id)
    if not vendor:
        return jsonify({'error': 'Vendor not found'}), 404
    
    products = db.get_products_by_vendor(vendor_id) if hasattr(db, 'get_products_by_vendor') else []
    reviews = db.get_reviews_by_vendor(vendor_id) if hasattr(db, 'get_reviews_by_vendor') else []
    
    return jsonify({
        'profile_views': vendor.get('traffic_count', 0),
        'total_products': len(products),
        'total_reviews': len(reviews),
        'average_rating': vendor.get('rating', 0),
        'top_products': sorted(products, key=lambda x: x.get('review_count', 0), reverse=True)[:5] if products else []
    }), 200

@vendor_bp.route('/suggestions', methods=['GET'])
def get_operation_suggestions():
    vendor_id = request.args.get('vendor_id')
    if not vendor_id:
        return jsonify({'error': 'vendor_id required'}), 400
    
    suggestions = SuggestionService.get_vendor_operation_suggestions(vendor_id) if hasattr(SuggestionService, 'get_vendor_operation_suggestions') else []
    return jsonify(suggestions), 200