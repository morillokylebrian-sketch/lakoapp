import os
import uuid
from PIL import Image
from config import config

class ImageService:
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS
    
    @staticmethod
    def compress(file, upload_type='general'):
        try:
            img = Image.open(file)
            
            # Convert RGBA to RGB
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            
            # Generate filename
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4()}.{ext}"
            
            # Save compressed
            compressed_path = ImageService.save_compressed(img, filename, upload_type)
            
            # Create thumbnail
            thumbnail_path = ImageService.create_thumbnail(img, filename, upload_type)
            
            file_size = os.path.getsize(compressed_path) if compressed_path else 0
            
            return {
                'success': True,
                'filename': filename,
                'compressed_path': compressed_path,
                'thumbnail_path': thumbnail_path,
                'size': file_size,
                'width': img.width,
                'height': img.height
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def save_compressed(img, filename, upload_type):
        upload_path = os.path.join(config.UPLOAD_FOLDER, 'compressed', upload_type)
        os.makedirs(upload_path, exist_ok=True)
        
        # Resize if needed
        if img.width > config.COMPRESSED_SIZE[0] or img.height > config.COMPRESSED_SIZE[1]:
            img.thumbnail(config.COMPRESSED_SIZE, Image.Resampling.LANCZOS)
        
        filepath = os.path.join(upload_path, filename)
        img.save(filepath, 'JPEG', quality=config.IMAGE_QUALITY, optimize=True)
        return filepath
    
    @staticmethod
    def create_thumbnail(img, filename, upload_type):
        thumb_path = os.path.join(config.UPLOAD_FOLDER, 'thumbnails', upload_type)
        os.makedirs(thumb_path, exist_ok=True)
        
        thumb = img.copy()
        thumb.thumbnail(config.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        
        filepath = os.path.join(thumb_path, filename)
        thumb.save(filepath, 'JPEG', quality=70)
        return filepath
    
    @staticmethod
    def save_original(file, upload_type='general'):
        try:
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4()}.{ext}"
            
            upload_path = os.path.join(config.UPLOAD_FOLDER, 'originals', upload_type)
            os.makedirs(upload_path, exist_ok=True)
            
            filepath = os.path.join(upload_path, filename)
            file.save(filepath)
            
            return {
                'success': True,
                'filename': filename,
                'path': filepath
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def delete_image(filename, upload_type='general'):
        paths = [
            os.path.join(config.UPLOAD_FOLDER, 'originals', upload_type, filename),
            os.path.join(config.UPLOAD_FOLDER, 'compressed', upload_type, filename),
            os.path.join(config.UPLOAD_FOLDER, 'thumbnails', upload_type, filename)
        ]
        
        deleted = False
        for path in paths:
            if os.path.exists(path):
                os.remove(path)
                deleted = True
        
        return {'deleted': deleted}
    
    @staticmethod
    def get_image_path(filename, upload_type='general', quality='compressed'):
        if quality == 'original':
            folder = 'originals'
        elif quality == 'thumbnail':
            folder = 'thumbnails'
        else:
            folder = 'compressed'
        
        return os.path.join(config.UPLOAD_FOLDER, folder, upload_type, filename)
    
    @staticmethod
    def upload_image(file, upload_type='general'):
        """Upload an image file and return the URL path"""
        if not file or not ImageService.allowed_file(file.filename):
            return None
        
        try:
            # Save all versions (original, compressed, thumbnail)
            original_result = ImageService.save_original(file, upload_type)
            if not original_result['success']:
                return None
            
            # Reset file pointer for compression
            file.seek(0)
            
            # Compress and create thumbnail
            compress_result = ImageService.compress(file, upload_type)
            if not compress_result['success']:
                return None
            
            # Return the compressed image URL
            filename = compress_result['filename']
            return f"/uploads/compressed/{upload_type}/{filename}"
        except Exception as e:
            print(f"Error uploading image: {str(e)}")
            return None