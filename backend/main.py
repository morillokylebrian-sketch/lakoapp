from flask import Flask, render_template, jsonify, session, redirect, request, flash
from flask_socketio import SocketIO
import os
from config import config
from database import db
from routes import register_routes
from functools import wraps
from services.auth_service import AuthService

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static',
            static_url_path='/static')
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = config.MAX_IMAGE_SIZE
app.config['SESSION_COOKIE_SECURE'] = not config.DEBUG
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

socketio = SocketIO(app)
auth_service = AuthService()

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first', 'error')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first', 'error')
                return redirect('/login')
            if session.get('user_role') != role:
                flash('You do not have permission to access this page', 'error')
                return redirect('/login')
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Health check
@app.route('/api/health')
def health():
    return jsonify({"status": "healthy", "message": "Lako API is running"})

@app.route('/api')
def api_index():
    return jsonify({
        "name": "Lako API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/auth",
            "customer": "/api/customer",
            "vendor": "/api/vendor",
            "admin": "/api/admin",
            "guest": "/api/guest",
            "chat": "/api/chat"
        }
    })

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "Lako - Food & Local Services",
        "short_name": "Lako",
        "description": "Discover local vendors and services in your area",
        "start_url": "/",
        "display": "standalone",
        "theme_color": "#0f5c2f",
        "background_color": "#ffffff"
    })

# Register all routes
register_routes(app)

# ============================================
# AUTHENTICATION PAGES
# ============================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        result = auth_service.login(email, password, role)
        if result['success']:
            session['user_id'] = result['user_id']
            session['user_role'] = result['user_role']
            session['user_name'] = result.get('user_name', '')
            
            # Redirect based on role
            if result['user_role'] == 'admin':
                return redirect('/admin')
            elif result['user_role'] == 'vendor':
                return redirect('/vendor')
            else:
                return redirect('/customer')
        else:
            flash(result['message'], 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        result = auth_service.register(email, password, first_name, last_name, role)
        if result['success']:
            flash('Account created successfully. Please log in.', 'success')
            return redirect('/login')
        else:
            flash(result['message'], 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect('/login')

# ============================================
# CUSTOMER PAGES
# ============================================
@app.route('/customer')
@login_required
@role_required('customer')
def customer_dashboard():
    from services.feed_service import FeedService
    
    feed_service = FeedService()
    stats = feed_service.get_customer_stats(session['user_id'])
    feed = feed_service.get_feed(session['user_id'], limit=10)
    
    return render_template(
        'customer_dashboard.html',
        stats=stats,
        feed=feed,
        user_name=session.get('user_name', '')
    )

@app.route('/messages')
@login_required
def messages():
    return render_template('messages.html', user_id=session['user_id'])

@app.route('/suggestions')
@login_required
def suggestions():
    from services.suggestion_service import SuggestionService
    
    suggestion_service = SuggestionService()
    vendor_suggestions = suggestion_service.get_suggested_vendors(session.get('user_id'), limit=15)
    product_suggestions = suggestion_service.get_suggested_products(session.get('user_id'), limit=15)
    
    return render_template(
        'suggestions.html',
        vendors=vendor_suggestions or [],
        products=product_suggestions or []
    )

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    
    if query:
        from services.suggestion_service import SuggestionService
        service = SuggestionService()
        results = service.search_vendors(query)
    else:
        results = []
    
    return render_template('search.html', query=query, results=results)

@app.route('/profile')
@login_required
def profile():
    from models.user import User
    
    user = db.session.query(User).filter(User.id == session['user_id']).first()
    
    user_stats = {
        'total_orders': 0,
        'saved_items': 0
    }
    
    return render_template('profile.html', user=user, user_stats=user_stats)

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    from models.user import User
    
    user = db.session.query(User).filter(User.id == session['user_id']).first()
    if not user:
        flash('User not found', 'error')
        return redirect('/profile')
    
    user.first_name = request.form.get('first_name')
    user.last_name = request.form.get('last_name')
    user.phone = request.form.get('phone')
    user.address = request.form.get('address')
    user.bio = request.form.get('bio')
    
    db.session.commit()
    flash('Profile updated successfully', 'success')
    return redirect('/profile')

# ============================================
# VENDOR PAGES
# ============================================
@app.route('/vendor')
@login_required
@role_required('vendor')
def vendor_dashboard():
    from services.analytics_service import AnalyticsService
    
    analytics_service = AnalyticsService()
    dashboard = analytics_service.get_vendor_dashboard(session['user_id'])
    products = analytics_service.get_vendor_products(session['user_id'], limit=5)
    recent_products = products[:5] if products else []
    
    return render_template(
        'vendor_dashboard.html',
        dashboard=dashboard,
        products=products,
        recent_products=recent_products,
        user_name=session.get('user_name', '')
    )

# ============================================
# ADMIN PAGES
# ============================================
@app.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    from models.user import User
    from models.vendor import Vendor
    from database import db
    import sqlalchemy as sa
    
    stats = {
        'total_users': db.session.query(User).filter(User.role == 'customer').count(),
        'total_vendors': db.session.query(Vendor).count(),
        'total_products': 0,  # TODO: Query from products table
        'total_views': 0  # TODO: Get from analytics
    }
    
    users = db.session.query(User).filter(User.role == 'customer').all()
    vendors = db.session.query(Vendor).all()
    
    return render_template(
        'admin_dashboard.html',
        stats=stats,
        users=users,
        vendors=vendors,
        user_name=session.get('user_name', '')
    )

# ============================================
# ROOT AND REDIRECTS
# ============================================
@app.route('/')
def index():
    if 'user_id' in session:
        role = session.get('user_role')
        if role == 'admin':
            return redirect('/admin')
        elif role == 'vendor':
            return redirect('/vendor')
        elif role == 'customer':
            return redirect('/customer')
    return redirect('/browse')

# ============================================
# BROWSE & DISCOVER (GUEST ACCESSIBLE)
# ============================================
@app.route('/browse')
def browse():
    from services.suggestion_service import SuggestionService
    
    search_query = request.args.get('search', '')
    category = request.args.get('category', '')
    
    suggestion_service = SuggestionService()
    
    if search_query:
        vendors = suggestion_service.search_vendors(search_query)
    else:
        vendors = suggestion_service.get_suggested_vendors(session.get('user_id'), limit=100)
    
    categories = ['Food & Beverages', 'Goods', 'Services', 'Technology']
    
    return render_template(
        'browse.html',
        vendors=vendors,
        categories=categories,
        search_query=search_query
    )

@app.route('/vendor/<vendor_id>')
def vendor_profile(vendor_id):
    from models.vendor import Vendor
    from database import db
    
    vendor = db.session.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        flash('Vendor not found', 'error')
        return redirect('/browse')
    
    # Get vendor's products and posts
    products = db.session.execute(
        db.text('SELECT * FROM products WHERE vendor_id = ? LIMIT 20'),
        [vendor_id]
    ).fetchall()
    
    posts = db.session.execute(
        db.text('SELECT * FROM posts WHERE user_id = ? ORDER BY created_at DESC LIMIT 10'),
        [vendor_id]
    ).fetchall()
    
    reviews = db.session.execute(
        db.text('SELECT * FROM reviews WHERE vendor_id = ? ORDER BY created_at DESC LIMIT 10'),
        [vendor_id]
    ).fetchall()
    
    return render_template(
        'vendor_profile.html',
        vendor=vendor.__dict__ if hasattr(vendor, '__dict__') else vendor,
        products=products,
        posts=posts,
        reviews=reviews
    )

@app.route('/product/<product_id>')
def product_detail(product_id):
    from database import db
    
    product = db.session.execute(
        db.text('SELECT * FROM products WHERE id = ?'),
        [product_id]
    ).fetchone()
    
    if not product:
        flash('Product not found', 'error')
        return redirect('/browse')
    
    vendor = db.session.execute(
        db.text('SELECT * FROM vendors WHERE id = ?'),
        [product['vendor_id']]
    ).fetchone()
    
    reviews = db.session.execute(
        db.text('SELECT * FROM reviews WHERE product_id = ? ORDER BY created_at DESC LIMIT 20'),
        [product_id]
    ).fetchall()
    
    return render_template(
        'product_detail.html',
        product=product,
        vendor=vendor,
        reviews=reviews
    )

@app.route('/map')
def map_view():
    """Display interactive map of nearby vendors"""
    from services.map_service import MapService
    from services.suggestion_service import SuggestionService
    
    map_service = MapService()
    suggestion_service = SuggestionService()
    
    # Get user location if authenticated
    user_id = session.get('user_id')
    
    # Get nearby vendors with distance
    vendors = suggestion_service.get_nearby_vendors(user_id, radius=25)
    
    return render_template(
        'map.html',
        vendors=vendors or []
    )

# ============================================
# POST & FEED CREATION
# ============================================
@app.route('/create-post', methods=['GET', 'POST'])
@login_required
def create_post():
    """Create a new post with optional images"""
    if request.method == 'POST':
        from services.feed_service import FeedService
        from services.image_service import ImageService
        
        content = request.form.get('content', '').strip()
        if not content:
            flash('Post content cannot be empty', 'error')
            return redirect('/create-post')
        
        if len(content) > 500:
            content = content[:500]
        
        # Handle image uploads
        image_urls = []
        if 'images' in request.files:
            image_service = ImageService()
            files = request.files.getlist('images')
            
            for file in files[:5]:  # Max 5 images
                if file and file.filename:
                    result = image_service.upload_image(file, 'posts')
                    if result:
                        image_urls.append(result)
        
        # Create post
        feed_service = FeedService()
        post = feed_service.create_post(
            user_id=session['user_id'],
            content=content,
            image_urls=image_urls
        )
        
        flash('Post created successfully!', 'success')
        return redirect('/customer')
    
    return render_template(
        'create_post.html',
        user_name=session.get('user_name', ''),
        user_role=session.get('user_role', '')
    )

# ============================================
# REVIEW & RATING
# ============================================
@app.route('/product/<product_id>/review', methods=['GET', 'POST'])
@login_required
def product_review(product_id):
    """Create or update a product review with images"""
    from database import db
    
    # Get product
    product = db.session.execute(
        db.text('SELECT * FROM products WHERE id = ?'),
        [product_id]
    ).fetchone()
    
    if not product:
        flash('Product not found', 'error')
        return redirect('/browse')
    
    if request.method == 'POST':
        from services.image_service import ImageService
        
        rating = request.form.get('rating', 0, type=int)
        content = request.form.get('content', '').strip()
        
        if not content or not (1 <= rating <= 5):
            flash('Please provide a rating and review text', 'error')
            return redirect(f'/product/{product_id}/review')
        
        if len(content) > 500:
            content = content[:500]
        
        # Handle image uploads
        image_urls = []
        if 'photos' in request.files:
            image_service = ImageService()
            files = request.files.getlist('photos')
            
            for file in files[:5]:  # Max 5 images
                if file and file.filename:
                    result = image_service.upload_image(file, 'reviews')
                    if result:
                        image_urls.append(result)
        
        # Create review in database
        try:
            db.session.execute(
                db.text('''
                    INSERT INTO reviews (product_id, user_id, rating, text_content, image_urls, created_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                '''),
                [product_id, session['user_id'], rating, content, ','.join(image_urls)]
            )
            db.session.commit()
            
            flash('Review posted successfully!', 'success')
            return redirect(f'/product/{product_id}')
        except Exception as e:
            db.session.rollback()
            flash(f'Error posting review: {str(e)}', 'error')
            return redirect(f'/product/{product_id}/review')
    
    return render_template(
        'review.html',
        product=product
    )

# Socket.IO events
@socketio.on('connect')
def handle_connect():
    print('Client connected')

if __name__ == '__main__':
    print("=" * 50)
    print("📍 LAKO Server Starting...")
    print("=" * 50)
    print(f"🌐 Local: http://localhost:{config.PORT}")
    print("=" * 50)
    
    if config.IS_RENDER:
        socketio.run(app, host='0.0.0.0', port=config.PORT)
    else:
        socketio.run(app, host='0.0.0.0', port=config.PORT, debug=config.DEBUG)