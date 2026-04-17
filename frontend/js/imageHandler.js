// Image Handler for Compression and Upload
class ImageHandler {
    constructor() {
        this.maxSize = 5 * 1024 * 1024;
        this.quality = 0.85;
        this.maxWidth = 1200;
        this.maxHeight = 1200;
    }

    async compressImage(file, options = {}) {
        const { maxWidth = this.maxWidth, maxHeight = this.maxHeight, quality = this.quality } = options;
        
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const img = new Image();
                img.onload = () => {
                    const canvas = document.createElement('canvas');
                    let width = img.width;
                    let height = img.height;
                    
                    if (width > maxWidth) {
                        height = (maxWidth / width) * height;
                        width = maxWidth;
                    }
                    if (height > maxHeight) {
                        width = (maxHeight / height) * width;
                        height = maxHeight;
                    }
                    
                    canvas.width = width;
                    canvas.height = height;
                    
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, width, height);
                    
                    canvas.toBlob((blob) => {
                        const compressedFile = new File([blob], file.name, {
                            type: 'image/jpeg',
                            lastModified: Date.now()
                        });
                        resolve(compressedFile);
                    }, 'image/jpeg', quality);
                };
                img.onerror = reject;
                img.src = e.target.result;
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    async uploadImage(file, type = 'general') {
        if (file.size > this.maxSize) {
            file = await this.compressImage(file);
        }
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', type);
        
        try {
            const response = await fetch(`${API_BASE}/upload/image`, {
                method: 'POST',
                headers: { 'X-Session-Token': api.getToken() },
                body: formData
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Upload failed');
            }
            
            return data;
        } catch (error) {
            console.error('Image upload error:', error);
            throw error;
        }
    }

    async uploadMultipleImages(files, type = 'general') {
        const formData = new FormData();
        
        for (const file of files) {
            let processedFile = file;
            if (file.size > this.maxSize) {
                processedFile = await this.compressImage(file);
            }
            formData.append('files', processedFile);
        }
        formData.append('type', type);
        
        try {
            const response = await fetch(`${API_BASE}/upload/images`, {
                method: 'POST',
                headers: { 'X-Session-Token': api.getToken() },
                body: formData
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Upload failed');
            }
            
            return data;
        } catch (error) {
            console.error('Multiple images upload error:', error);
            throw error;
        }
    }

    createThumbnail(file, size = 200) {
        return this.compressImage(file, { maxWidth: size, maxHeight: size, quality: 0.7 });
    }

    previewImage(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }
}

const imageHandler = new ImageHandler();