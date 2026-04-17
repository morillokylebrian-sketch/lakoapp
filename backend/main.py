from flask import Flask, send_from_directory, jsonify
from flask_socketio import SocketIO
import os
from config import config
from database import db
from routes import register_routes

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = config.MAX_IMAGE_SIZE

socketio = SocketIO(app)

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

# Register all routes
register_routes(app)

# Serve frontend
@app.route('/')
def serve_index():
    return send_from_directory('../frontend', 'index.html')

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