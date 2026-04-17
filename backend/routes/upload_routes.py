from flask import Blueprint, request, jsonify, send_file
from image_handler import ImageHandler
from database import db
import os
from config import config

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    upload_type = request.form.get('type', 'general')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not ImageHandler.allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    result = ImageHandler.compress_image(file, upload_type)
    
    if result['success']:
        return jsonify({
            'filename': result['filename'],
            'url': f"/api/upload/image/{result['filename']}",
            'thumbnail_url': f"/api/upload/thumbnail/{result['filename']}",
            'size': result['size']
        }), 201
    
    return jsonify({'error': result['error']}), 500

@upload_bp.route('/images', methods=['POST'])
def upload_multiple():
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    upload_type = request.form.get('type', 'general')
    
    results = []
    for file in files:
        if file and ImageHandler.allowed_file(file.filename):
            result = ImageHandler.compress_image(file, upload_type)
            if result['success']:
                results.append({
                    'filename': result['filename'],
                    'url': f"/api/upload/image/{result['filename']}",
                    'thumbnail_url': f"/api/upload/thumbnail/{result['filename']}"
                })
    
    return jsonify({'uploaded': results}), 201

@upload_bp.route('/image/<filename>', methods=['GET'])
def get_image(filename):
    upload_type = request.args.get('type', 'general')
    quality = request.args.get('quality', 'compressed')
    
    if quality == 'original':
        path = os.path.join(config.UPLOAD_FOLDER, 'originals', upload_type, filename)
    elif quality == 'thumbnail':
        path = os.path.join(config.UPLOAD_FOLDER, 'thumbnails', upload_type, filename)
    else:
        path = os.path.join(config.UPLOAD_FOLDER, 'compressed', upload_type, filename)
    
    if os.path.exists(path):
        return send_file(path)
    
    return jsonify({'error': 'Image not found'}), 404

@upload_bp.route('/thumbnail/<filename>', methods=['GET'])
def get_thumbnail(filename):
    upload_type = request.args.get('type', 'general')
    path = os.path.join(config.UPLOAD_FOLDER, 'thumbnails', upload_type, filename)
    
    if os.path.exists(path):
        return send_file(path)
    
    return jsonify({'error': 'Thumbnail not found'}), 404

@upload_bp.route('/image/<filename>', methods=['DELETE'])
def delete_image(filename):
    upload_type = request.args.get('type', 'general')
    
    paths = [
        os.path.join(config.UPLOAD_FOLDER, 'originals', upload_type, filename),
        os.path.join(config.UPLOAD_FOLDER, 'compressed', upload_type, filename),
        os.path.join(config.UPLOAD_FOLDER, 'thumbnails', upload_type, filename)
    ]
    
    for path in paths:
        if os.path.exists(path):
            os.remove(path)
    
    return jsonify({'deleted': True}), 200