from .auth_routes import auth_bp
from .customer_routes import customer_bp
from .vendor_routes import vendor_bp
from .admin_routes import admin_bp
from .guest_routes import guest_bp
from .chat_routes import chat_bp
from .upload_routes import upload_bp
from .sync_routes import sync_bp

def register_routes(app):
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(customer_bp, url_prefix='/api/customer')
    app.register_blueprint(vendor_bp, url_prefix='/api/vendor')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(guest_bp, url_prefix='/api/guest')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(sync_bp, url_prefix='/api/sync')