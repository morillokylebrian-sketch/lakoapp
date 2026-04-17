// Main Application Controller
class App {
    constructor() {
        this.currentPage = null;
        this.init();
    }

    async init() {
        // Auth not required - skip authentication check
        // Hide loading screen
        const loading = document.querySelector('.loading-screen');
        if (loading) {
            loading.style.display = 'none';
        }
        
        this.route();
    }

    route() {
        const path = window.location.pathname;
        const role = auth.getUserRole();
        
        // Handle root path
        if (path === '/' || path === '/index.html') {
            // No auth required - allow all
            return;
        }
        
        // No auth redirects - allow all roles access
        
        if (path.includes('/vendor/') && role !== 'vendor' && role !== 'admin') {
            window.location.href = '/pages/login.html';
            return;
        }
        
        if (path.includes('/admin/') && role !== 'admin') {
            window.location.href = '/pages/admin/login.html';
            return;
        }
    }

    showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        const bgColor = type === 'error' ? '#dc2626' : type === 'success' ? '#10b981' : '#0f5c2f';
        toast.className = `app-toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            background: ${bgColor};
            color: white;
            padding: 12px 24px;
            border-radius: 40px;
            font-size: 14px;
            font-weight: 500;
            z-index: 9999;
            animation: slideUp 0.3s ease;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        `;
        
        document.body.appendChild(toast);
        
        if (duration) {
            setTimeout(() => {
                toast.style.animation = 'slideDown 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }
        
        return toast;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});

// Global showToast function - accessible from anywhere
function showToast(message, type = 'info', duration = 3000) {
    if (window.app) {
        return window.app.showToast(message, type, duration);
    }
    // Fallback if app not initialized yet
    const toast = document.createElement('div');
    const bgColor = type === 'error' ? '#dc2626' : type === 'success' ? '#10b981' : type === 'warning' ? '#f97316' : '#0f5c2f';
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 24px;
        left: 50%;
        transform: translateX(-50%);
        background: ${bgColor};
        color: white;
        padding: 12px 24px;
        border-radius: 40px;
        font-size: 14px;
        font-weight: 500;
        z-index: 9999;
        animation: slideUp 0.3s ease;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    `;
    
    document.body.appendChild(toast);
    
    if (duration) {
        setTimeout(() => {
            toast.style.animation = 'slideDown 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
    
    return toast;
}

// Ensure API_BASE is globally available
if (!window.API_BASE) {
    window.API_BASE = 'http://localhost:5000/api';
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideUp {
        from { opacity: 0; transform: translateX(-50%) translateY(20px); }
        to { opacity: 1; transform: translateX(-50%) translateY(0); }
    }
    @keyframes slideDown {
        from { opacity: 1; transform: translateX(-50%) translateY(0); }
        to { opacity: 0; transform: translateX(-50%) translateY(20px); }
    }
`;
document.head.appendChild(style);