# Lako Frontend - Implementation Examples

## Quick Start Examples

These examples show how to use the fixed JavaScript with your backend.

### 1. Login & Authentication

```javascript
// Login
async function handleLogin() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    try {
        const result = await auth.login(email, password);
        if (result.success) {
            showToast('Login successful!', 'success', 2000);
            // Redirect happens automatically in auth module
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast('Login failed: ' + error.message, 'error');
    }
}

// Check if user is logged in
if (auth.isAuthenticated()) {
    const user = auth.getUser();
    console.log('Welcome, ' + user.full_name);
} else {
    window.location.href = '/pages/login.html';
}

// Check if user has specific role
if (auth.getUserRole() === 'vendor') {
    // Show vendor dashboard
} else if (auth.getUserRole() === 'customer') {
    // Show customer dashboard
}

// Logout
async function handleLogout() {
    await auth.logout();
    showToast('Logged out', 'success', 2000);
    window.location.href = '/pages/';
}
```

### 2. Getting User Data

```javascript
// Get current user
const user = auth.getUser();
console.log(user.id, user.email, user.role);

// Fetch fresh user data from server
const freshUser = await api.getCurrentUser();

// Update location (for vendor/customer tracking)
await api.updateLocation(14.5995, 120.9842);
```

### 3. Creating Posts

```javascript
async function createPost() {
    const content = document.getElementById('postContent').value;
    const imageFiles = document.getElementById('images').files;
    
    try {
        // Upload images first if provided
        let imageUrls = [];
        if (imageFiles.length > 0) {
            const uploadResult = await imageHandler.uploadMultipleImages(
                Array.from(imageFiles),
                'post'
            );
            imageUrls = uploadResult.uploaded.map(img => img.url);
        }
        
        // Create post
        const post = await api.createPost(content, imageUrls);
        showToast('Post created!', 'success', 2000);
        
        // Refresh feed
        await loadFeed();
    } catch (error) {
        showToast('Failed to create post: ' + error.message, 'error');
    }
}
```

### 4. Loading & Managing Feed

```javascript
async function loadFeed() {
    try {
        const feedData = await api.getFeed(1);
        renderFeedPosts(feedData.posts);
    } catch (error) {
        showToast('Failed to load feed', 'error');
    }
}

function renderFeedPosts(posts) {
    const feedContainer = document.getElementById('feed');
    feedContainer.innerHTML = '';
    
    posts.forEach(post => {
        const postDiv = document.createElement('div');
        postDiv.className = 'feed-post';
        postDiv.innerHTML = `
            <div class="post-header">
                <strong>${post.author_name}</strong>
                <small>${formatTime(post.created_at)}</small>
            </div>
            <p>${escapeHtml(post.content)}</p>
            ${post.images ? `<img src="${post.images[0]}" style="max-width:100%">` : ''}
            <div class="post-actions">
                <button onclick="likePost('${post.id}')">♥ Like</button>
            </div>
        `;
        feedContainer.appendChild(postDiv);
    });
}

async function likePost(postId) {
    try {
        await api.likePost(postId);
        showToast('Liked!', 'success', 1000);
        // Refresh to see updated count
        loadFeed();
    } catch (error) {
        showToast('Failed to like post', 'error');
    }
}
```

### 5. Finding Nearby Vendors

```javascript
async function findNearbyVendors() {
    try {
        // Get user location
        const location = await mapManager.getCurrentLocation();
        
        // Get vendors within 5km
        const vendors = await api.getNearbyVendors(
            location.lat,
            location.lng,
            5  // 5km radius
        );
        
        if (vendors.vendors.length > 0) {
            showToast(`Found ${vendors.vendors.length} vendors nearby!`, 'success');
            displayVendors(vendors.vendors);
        } else {
            showToast('No vendors found nearby', 'info');
        }
    } catch (error) {
        showToast('Failed to find vendors: ' + error.message, 'error');
    }
}

function displayVendors(vendors) {
    const vendorList = document.getElementById('vendorList');
    vendorList.innerHTML = '';
    
    vendors.forEach(vendor => {
        const vendorCard = document.createElement('div');
        vendorCard.className = 'vendor-card';
        vendorCard.innerHTML = `
            <img src="${vendor.image || '/assets/images/vendor-placeholder.png'}" 
                 alt="${vendor.business_name}" class="vendor-image">
            <div class="vendor-info">
                <h3>${vendor.business_name}</h3>
                <p>${vendor.category}</p>
                <p class="rating">★ ${vendor.rating || 0} (${vendor.review_count || 0} reviews)</p>
                <p class="distance">${calculateDistance(
                    mapManager.currentLocation.lat,
                    mapManager.currentLocation.lng,
                    vendor.latitude,
                    vendor.longitude
                ).toFixed(2)} km away</p>
            </div>
            <button onclick="viewVendor('${vendor.id}')">View Details →</button>
        `;
        vendorList.appendChild(vendorCard);
    });
}
```

### 6. Managing the Map

```javascript
// Initialize map on page load
async function initMap() {
    // Initialize map on specific element
    mapManager.init('map', {
        center: [14.5995, 120.9842],
        zoom: 13
    });
    
    // Center on user
    const userLocation = await mapManager.centerOnUser();
    
    // Load nearby vendors on map
    const vendors = await mapManager.loadNearbyVendors(
        userLocation.lat,
        userLocation.lng,
        10  // 10km radius
    );
    
    // Toggle heatmap
    await mapManager.toggleHeatmap();
}

// Add search to map
function addMapSearch() {
    mapManager.addSearchControl();
}

// Get route between two points
async function showRoute(vendorId) {
    const vendor = await api.getVendor(vendorId);
    const route = await mapManager.getRoute(
        mapManager.currentLocation.lat,
        mapManager.currentLocation.lng,
        vendor.latitude,
        vendor.longitude,
        'driving'
    );
    
    if (route) {
        showToast(
            `Route: ${route.distance.toFixed(2)} km, ~${Math.round(route.duration)} min`,
            'info'
        );
    }
}
```

### 7. Uploading Images

```javascript
// Single image upload
async function uploadProfileImage() {
    const file = document.getElementById('imageInput').files[0];
    
    if (!file) {
        showToast('Please select an image', 'error');
        return;
    }
    
    try {
        // Compress and upload
        const result = await imageHandler.uploadImage(file, 'profile');
        
        showToast('Image uploaded!', 'success', 2000);
        
        // Update profile image
        document.getElementById('profileImage').src = result.url;
        
        // Save to profile
        await api.updateProfile({ avatar: result.url });
    } catch (error) {
        showToast('Failed to upload: ' + error.message, 'error');
    }
}

// Multiple images upload
async function uploadPostImages() {
    const files = document.getElementById('imagesInput').files;
    
    if (files.length === 0) {
        showToast('Please select images', 'error');
        return;
    }
    
    try {
        const result = await imageHandler.uploadMultipleImages(
            Array.from(files),
            'post'
        );
        
        showToast(`Uploaded ${result.uploaded.length} images!`, 'success', 2000);
        
        // Use URLs for post creation
        return result.uploaded.map(img => img.url);
    } catch (error) {
        showToast('Failed to upload images: ' + error.message, 'error');
    }
}

// Create thumbnail
async function createAndUploadThumbnail(file) {
    try {
        const thumbnail = await imageHandler.createThumbnail(file, 200);
        return await imageHandler.uploadImage(thumbnail, 'thumbnail');
    } catch (error) {
        console.error('Thumbnail error:', error);
    }
}
```

### 8. Chat Functionality

```javascript
// Initialize chat
function initChat() {
    // Only for authenticated users
    if (!auth.isAuthenticated()) return;
    
    // Connect to chat server
    chat.connect();
    
    // Listen for messages
    chat.onMessage((message) => {
        console.log('New message:', message);
        displayMessage(message);
    });
    
    // Listen for typing indicators
    chat.onTyping((data) => {
        showTypingIndicator(data);
    });
    
    // Listen for connection changes
    chat.onConnectionChange((status) => {
        console.log('Chat status:', status);
    });
}

// Send message
async function sendMessage(receiverId) {
    const messageText = document.getElementById('messageInput').value;
    
    if (!messageText.trim()) {
        return;
    }
    
    try {
        // Send message
        const result = await chat.sendMessage(receiverId, messageText, null);
        
        // Clear input
        document.getElementById('messageInput').value = '';
        
        // Display sent message
        displayMessage({
            ...result,
            sender_id: auth.getUser().id,
            is_sent: true
        });
    } catch (error) {
        showToast('Failed to send message: ' + error.message, 'error');
    }
}

// Start conversation
function startConversation(userId) {
    chat.joinConversation(userId);
    loadMessages(userId);
}

// Load conversation messages
async function loadMessages(userId) {
    try {
        const messages = await api.getMessages(userId);
        
        const messagesDiv = document.getElementById('messages');
        messagesDiv.innerHTML = '';
        
        messages.forEach(msg => {
            displayMessage(msg);
        });
        
        // Scroll to bottom
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    } catch (error) {
        console.error('Failed to load messages:', error);
    }
}
```

### 9. Creating Reviews

```javascript
async function submitReview(vendorId) {
    const rating = document.getElementById('rating').value;
    const title = document.getElementById('reviewTitle').value;
    const comment = document.getElementById('reviewComment').value;
    
    if (!rating || !title) {
        showToast('Please fill all required fields', 'error');
        return;
    }
    
    try {
        const review = await api.createReview(
            vendorId,
            parseInt(rating),
            title,
            comment
        );
        
        showToast('Review submitted! Thank you!', 'success', 2000);
        
        // Clear form
        document.getElementById('reviewForm').reset();
        
        // Reload vendor data
        await loadVendor(vendorId);
    } catch (error) {
        showToast('Failed to submit review: ' + error.message, 'error');
    }
}
```

### 10. Offline Support & Sync

```javascript
// Cache data for offline use
async function cacheAllData() {
    try {
        await sync.cache();
        showToast('Data cached for offline use!', 'success', 2000);
    } catch (error) {
        showToast('Failed to cache data', 'error');
    }
}

// Queue action for later sync
async function createPostOffline(content) {
    // Queue the action
    await sync.queueAction('create', {
        model: 'post',
        action: 'create',
        data: { content }
    });
    
    showToast(
        sync.isOnline 
            ? 'Post created!' 
            : 'Offline: Post will sync when online',
        'success'
    );
}

// Listen to sync status
sync.onStatusChange((status) => {
    if (status === 'online') {
        showToast('Back online! Syncing data...', 'info', 2000);
        sync.cache();  // Sync everything
    } else {
        showToast('You are offline. Changes will sync when back online.', 'warning');
    }
});

// Start periodic cache (every 5 minutes)
sync.startPeriodicCache(300000);

// Clear cache when needed
async function clearAllCache() {
    await sync.clearCache();
    showToast('Cache cleared', 'success', 2000);
}

// Get cached data
async function loadFromCache() {
    const cachedVendors = await sync.getCached('vendors');
    if (cachedVendors) {
        console.log('Using cached vendors:', cachedVendors);
    }
}
```

### 11. Admin Dashboard

```javascript
async function loadAdminDashboard() {
    try {
        // Check if admin
        if (auth.getUserRole() !== 'admin') {
            window.location.href = '/pages/';
            return;
        }
        
        // Load stats
        const stats = await api.getAdminStats();
        
        // Display stats
        document.getElementById('totalUsers').textContent = stats.total_users;
        document.getElementById('totalVendors').textContent = stats.total_vendors;
        document.getElementById('totalPosts').textContent = stats.total_posts;
        document.getElementById('revenue').textContent = formatCurrency(stats.revenue);
        
        // Load lists
        const users = await api.getAdminUsers();
        const vendors = await api.getAdminVendors();
        
        displayAdminUsers(users);
        displayAdminVendors(vendors);
    } catch (error) {
        showToast('Failed to load dashboard: ' + error.message, 'error');
    }
}

// Suspend user
async function suspendUser(userId) {
    const reason = prompt('Why are you suspending this user?');
    if (!reason) return;
    
    try {
        await api.suspendUser(userId, reason);
        showToast('User suspended', 'success');
        loadAdminDashboard();
    } catch (error) {
        showToast('Failed to suspend user: ' + error.message, 'error');
    }
}

// Toggle vendor active status
async function toggleVendor(vendorId, isCurrentlyActive) {
    try {
        await api.toggleVendor(vendorId, !isCurrentlyActive);
        showToast(
            isCurrentlyActive ? 'Vendor deactivated' : 'Vendor activated',
            'success'
        );
        loadAdminDashboard();
    } catch (error) {
        showToast('Failed to toggle vendor: ' + error.message, 'error');
    }
}
```

## Error Handling Pattern

Always use this pattern for robust error handling:

```javascript
async function robustApiCall() {
    const loadingIndicator = document.getElementById('loading');
    
    try {
        loadingIndicator.style.display = 'block';
        
        // Your API call
        const result = await api.someMethod();
        
        // Success
        showToast('Operation successful!', 'success', 2000);
        return result;
        
    } catch (error) {
        // Error
        console.error('Operation failed:', error);
        
        if (error.message.includes('401')) {
            showToast('Session expired. Please login again.', 'error');
            auth.clear();
            window.location.href = '/pages/login.html';
        } else if (error.message.includes('Network')) {
            showToast('Network error. Check your connection.', 'error');
        } else {
            showToast('Error: ' + (error.message || 'Something went wrong'), 'error');
        }
        
    } finally {
        loadingIndicator.style.display = 'none';
    }
}
```

---

These examples cover the most common operations. All functions use the fixed, verified connection to your backend!
