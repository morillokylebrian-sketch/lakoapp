// API Service for Lako Backend
// Dynamically detect API base URL for both localhost and 127.0.0.1
const getAPIBase = () => {
    const hostname = window.location.hostname;
    const port = window.location.port || '5000';
    
    // Support both localhost and 127.0.0.1
    const host = (hostname === 'localhost' || hostname === '127.0.0.1') 
        ? hostname 
        : 'localhost';
    
    return `http://${host}:${port}/api`;
};

const API_BASE = getAPIBase();

// Make API_BASE globally available
if (typeof window !== 'undefined') {
    window.API_BASE = API_BASE;
}

class ApiService {
    constructor() {
        this.baseUrl = API_BASE;
        this.token = localStorage.getItem('session_token');
    }

    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('session_token', token);
        } else {
            localStorage.removeItem('session_token');
        }
    }

    getToken() {
        return this.token || localStorage.getItem('session_token');
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const token = this.getToken();
        
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (token) {
            headers['X-Session-Token'] = token;
        }
        
        const config = {
            ...options,
            headers
        };
        
        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                if (response.status === 401) {
                    this.setToken(null);
                    window.location.href = '/pages/login.html';
                }
                throw new Error(data.error || 'API request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Auth endpoints
    async register(userData) {
        const endpoint = userData.role === 'vendor' 
            ? '/auth/register/vendor' 
            : '/auth/register/customer';
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    }

    async login(email, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
    }

    async logout() {
        return this.request('/auth/logout', { method: 'POST' });
    }

    async getCurrentUser() {
        return this.request('/auth/me');
    }

    async updateLocation(lat, lng) {
        return this.request('/auth/update-location', {
            method: 'POST',
            body: JSON.stringify({ latitude: lat, longitude: lng })
        });
    }

    // Customer endpoints
    async getFeed(page = 1) {
        return this.request(`/customer/feed?page=${page}`);
    }

    async createPost(content, images = null) {
        return this.request('/customer/posts', {
            method: 'POST',
            body: JSON.stringify({ content, images })
        });
    }

    async likePost(postId) {
        return this.request(`/customer/posts/${postId}/like`, {
            method: 'POST'
        });
    }

    async getNearbyVendors(lat, lng, radius = 10) {
        return this.request(`/customer/vendors/nearby?lat=${lat}&lng=${lng}&radius=${radius}`);
    }

    async getVendor(vendorId) {
        return this.request(`/customer/vendors/${vendorId}`);
    }

    async search(query, type = 'all') {
        return this.request(`/customer/search?q=${encodeURIComponent(query)}&type=${type}`);
    }

    async getShortlist() {
        return this.request('/customer/shortlist');
    }

    async addToShortlist(vendorId) {
        return this.request(`/customer/shortlist/${vendorId}`, {
            method: 'POST'
        });
    }

    async removeFromShortlist(vendorId) {
        return this.request(`/customer/shortlist/${vendorId}`, {
            method: 'DELETE'
        });
    }

    async createReview(vendorId, rating, title, comment) {
        return this.request('/customer/reviews', {
            method: 'POST',
            body: JSON.stringify({ vendor_id: vendorId, rating, title, comment })
        });
    }

    async getSuggestions(lat, lng) {
        return this.request(`/customer/suggestions?lat=${lat}&lng=${lng}`);
    }

    async getHeatmap() {
        return this.request('/customer/heatmap');
    }

    // Vendor endpoints
    async getVendorDashboard() {
        return this.request('/vendor/dashboard');
    }

    async getVendorProducts() {
        return this.request('/vendor/products');
    }

    async createProduct(productData) {
        return this.request('/vendor/products', {
            method: 'POST',
            body: JSON.stringify(productData)
        });
    }

    async updateProduct(productId, productData) {
        return this.request(`/vendor/products/${productId}`, {
            method: 'PUT',
            body: JSON.stringify(productData)
        });
    }

    async deleteProduct(productId) {
        return this.request(`/vendor/products/${productId}`, {
            method: 'DELETE'
        });
    }

    async getVendorReviews() {
        return this.request('/vendor/reviews');
    }

    async getVendorTraffic() {
        return this.request('/vendor/traffic');
    }

    async updateVendorProfile(profileData) {
        return this.request('/vendor/profile', {
            method: 'PUT',
            body: JSON.stringify(profileData)
        });
    }

    async getVendorAnalytics() {
        return this.request('/vendor/analytics');
    }

    // Guest endpoints
    async getGuestVendors(lat, lng) {
        return this.request(`/guest/vendors?lat=${lat}&lng=${lng}`);
    }

    async getGuestVendor(vendorId) {
        return this.request(`/guest/vendors/${vendorId}`);
    }

    async getMapConfig() {
        return this.request('/guest/map/config');
    }

    // Admin endpoints
    async getAdminStats() {
        return this.request('/admin/stats');
    }

    async getAdminUsers() {
        return this.request('/admin/users');
    }

    async suspendUser(userId, reason) {
        return this.request(`/admin/users/${userId}/suspend`, {
            method: 'POST',
            body: JSON.stringify({ reason })
        });
    }

    async getAdminVendors() {
        return this.request('/admin/vendors');
    }

    async toggleVendor(vendorId, isActive) {
        return this.request(`/admin/vendors/${vendorId}/toggle`, {
            method: 'POST',
            body: JSON.stringify({ is_active: isActive })
        });
    }

    // Chat endpoints
    async getConversations() {
        return this.request('/chat/conversations');
    }

    async getMessages(userId) {
        return this.request(`/chat/messages/${userId}`);
    }

    async sendMessage(receiverId, message, images = null) {
        return this.request('/chat/send', {
            method: 'POST',
            body: JSON.stringify({ receiver_id: receiverId, message, images })
        });
    }

    // Sync endpoints
    async pullChanges() {
        return this.request('/sync/pull');
    }

    async pushChanges(changes) {
        return this.request('/sync/push', {
            method: 'POST',
            body: JSON.stringify({ changes })
        });
    }

    async getSyncStatus() {
        return this.request('/sync/status');
    }
}

// Create global instance
const api = new ApiService();