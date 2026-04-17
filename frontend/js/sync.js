// Cache Service for Offline-First Operations
class SyncService {
    constructor() {
        this.isOnline = navigator.onLine;
        this.cacheInProgress = false;
        this.listeners = [];
        this.cacheTTL = 3600000; // 1 hour default
        this.init();
    }

    init() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.notifyListeners('online');
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.notifyListeners('offline');
        });
    }

    onStatusChange(callback) {
        this.listeners.push(callback);
    }

    notifyListeners(status) {
        this.listeners.forEach(cb => cb(status));
    }

    async cache() {
        if (this.cacheInProgress) return;
        
        this.cacheInProgress = true;
        showToast('Caching data...', 'info', 2000);
        
        try {
            // Cache data from server
            await this.cacheData();
            
            // Push local changes to server if online
            if (this.isOnline) {
                await this.pushChanges();
            }
            
            showToast('Cache complete', 'success', 2000);
        } catch (error) {
            console.error('Cache error:', error);
            showToast('Cache failed', 'error');
        } finally {
            this.cacheInProgress = false;
        }
    }

    async cacheData() {
        try {
            // Cache vendors
            const vendors = await api.getNearbyVendors(14.5995, 120.9842, 50);
            await localDB.cacheData('vendors', vendors.vendors || [], 7200000);
            
            // Cache products
            const products = await api.request('/customer/products');
            await localDB.cacheData('products', products.products || [], 7200000);
            
            // Cache posts/feed
            const feed = await api.request('/customer/feed');
            await localDB.cacheData('feed', feed.posts || [], 3600000);
            
            // Cache user preferences
            const settings = await api.request('/customer/settings');
            await localDB.cacheData('user_settings', settings, 86400000);
            
        } catch (error) {
            console.error('Data cache error:', error);
            throw error;
        }
    }

    async pushChanges() {
        const unsynced = await localDB.getUnsynced();
        if (!unsynced.length) return;
        
        try {
            await api.pushChanges(unsynced);
            
            for (const item of unsynced) {
                await localDB.markSynced(item.id);
            }
        } catch (error) {
            console.error('Push error:', error);
            throw error;
        }
    }

    async queueAction(action, data) {
        await localDB.addToSyncQueue({ action, data });
        if (this.isOnline) {
            this.cache();
        }
    }

    startPeriodicCache(intervalMs = 300000) {
        setInterval(() => {
            this.cache();
        }, intervalMs);
    }

    async getCached(key) {
        return await localDB.getCached(key);
    }

    async clearCache() {
        await localDB.clear('cache');
        await localDB.clear('vendors');
        await localDB.clear('products');
        await localDB.clear('feed');
        showToast('Cache cleared', 'success');
    }
}

// Create global instance
const sync = new SyncService();

const syncService = new SyncService();
syncService.startPeriodicCache();