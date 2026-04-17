// Authentication Manager
class AuthManager {
    constructor() {
        this.user = null;
        this.loadUser();
    }

    loadUser() {
        const userData = localStorage.getItem('user');
        if (userData) {
            try {
                this.user = JSON.parse(userData);
            } catch (e) {
                this.user = null;
            }
        }
    }

    saveUser(user) {
        this.user = user;
        localStorage.setItem('user', JSON.stringify(user));
    }

    async register(userData) {
        try {
            const response = await api.register(userData);
            if (response.session_token) {
                api.setToken(response.session_token);
                this.saveUser(response.user);
                return { success: true, user: response.user };
            }
            return { success: false, error: 'Registration failed' };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async login(email, password) {
        try {
            const response = await api.login(email, password);
            if (response.session_token) {
                api.setToken(response.session_token);
                this.saveUser(response.user);
                
                // Store vendor info if applicable
                if (response.vendor) {
                    localStorage.setItem('vendor', JSON.stringify(response.vendor));
                }
                
                return { success: true, user: response.user };
            }
            return { success: false, error: response.error };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async logout() {
        try {
            await api.logout();
        } catch (e) {
            // Ignore logout errors
        }
        this.clear();
    }

    clear() {
        this.user = null;
        api.setToken(null);
        localStorage.removeItem('user');
        localStorage.removeItem('vendor');
        localStorage.removeItem('user_role');
    }

    isAuthenticated() {
        // No auth required - always return true
        return true;
    }

    getUser() {
        return this.user;
    }

    getUserRole() {
        return this.user?.role || localStorage.getItem('user_role') || 'guest';
    }

    getVendor() {
        const vendor = localStorage.getItem('vendor');
        return vendor ? JSON.parse(vendor) : null;
    }

    redirectBasedOnRole() {
        // Auth not required - no redirect needed
        return true;
    }

    requireAuth() {
        // Auth not required - always return true
        return true;
    }

    requireRole(allowedRoles) {
        // Auth not required - always return true
        return true;
    }
}

// Create global instance
const auth = new AuthManager();