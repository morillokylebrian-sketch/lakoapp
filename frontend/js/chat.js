// Chat System for Lako
class ChatManager {
    constructor() {
        this.socket = null;
        this.currentConversation = null;
        this.messages = [];
        this.typingTimeout = null;
        this.listeners = [];
        this.unreadCount = 0;
    }

    connect() {
        // Check if socket.io is available
        if (typeof io === 'undefined') {
            console.warn('socket.io not loaded, chat functionality unavailable');
            return;
        }
        
        try {
            // Get the base URL without /api
            const baseURL = API_BASE.replace('/api', '');
            const token = api.getToken();
            
            this.socket = io(baseURL, {
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionDelay: 1000,
                reconnectionDelayMax: 5000,
                reconnectionAttempts: 5,
                auth: { token: token || 'anonymous' }
            });
            
            this.socket.on('connect', () => {
                console.log('[Chat] Connected to server');
                this.notifyListeners('connected');
                showToast('Chat connected', 'success', 2000);
            });
            
            this.socket.on('disconnect', () => {
                console.log('[Chat] Disconnected from server');
                this.notifyListeners('disconnected');
            });
            
            this.socket.on('error', (error) => {
                console.error('[Chat] Socket error:', error);
                showToast('Chat connection error', 'error');
            });
            
            this.socket.on('message', (data) => {
                this.handleIncomingMessage(data);
            });
            
            this.socket.on('typing', (data) => {
                this.notifyListeners('typing', data);
            });
            
            this.socket.on('message_read', (data) => {
                this.notifyListeners('read', data);
            });
        } catch (error) {
            console.error('[Chat] Failed to initialize socket:', error);
            showToast('Failed to connect to chat', 'error');
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            console.log('[Chat] Disconnected');
        }
    }

    joinConversation(userId) {
        if (this.socket && this.socket.connected) {
            this.socket.emit('join', { user_id: userId });
            this.currentConversation = userId;
            console.log('[Chat] Joined conversation with', userId);
        }
    }

    leaveConversation() {
        if (this.socket && this.currentConversation) {
            this.socket.emit('leave', { user_id: this.currentConversation });
            console.log('[Chat] Left conversation');
            this.currentConversation = null;
        }
    }

    sendMessage(receiverId, message, images = null) {
        return new Promise((resolve, reject) => {
            if (!this.socket || !this.socket.connected) {
                console.warn('[Chat] Socket not connected, using API for persistence');
                // Still save via API even if socket not connected
                api.sendMessage(receiverId, message, images)
                    .then(resolve)
                    .catch(reject);
                return;
            }
            
            const messageData = {
                receiver_id: receiverId,
                message,
                images,
                timestamp: new Date().toISOString()
            };
            
            this.socket.emit('message', messageData, (response) => {
                if (response.error) {
                    reject(new Error(response.error));
                } else {
                    resolve(response);
                }
            });
            
            // Also save via API for persistence
            api.sendMessage(receiverId, message, images)
                .then(() => console.log('[Chat] Message saved via API'))
                .catch(err => console.error('[Chat] API save error:', err));
        });
    }

    sendTyping(receiverId, isTyping) {
        if (this.socket && this.socket.connected) {
            this.socket.emit('typing', {
                receiver_id: receiverId,
                typing: isTyping
            });
        }
    }

    markAsRead(senderId) {
        if (this.socket && this.socket.connected) {
            this.socket.emit('read', { sender_id: senderId });
        }
    }

    handleIncomingMessage(data) {
        this.messages.push(data);
        this.notifyListeners('message', data);
    }

    onMessage(callback) {
        this.listeners.push((event, data) => {
            if (event === 'message') callback(data);
        });
    }

    onTyping(callback) {
        this.listeners.push((event, data) => {
            if (event === 'typing') callback(data);
        });
    }

    onConnectionChange(callback) {
        this.listeners.push((event, data) => {
            if (event === 'connected' || event === 'disconnected') callback(event);
        });
    }

    notifyListeners(event, data = null) {
        this.listeners.forEach(listener => listener(event, data));
    }

    getUnreadCount() {
        return this.unreadCount;
    }

    clearUnreadCount(userId) {
        if (userId === this.currentConversation) {
            this.unreadCount = 0;
        }
    }

    resetUnreadCount() {
        this.unreadCount = 0;
    }

    requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }

    formatMessageTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 86400000) {
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } else if (diff < 604800000) {
            return date.toLocaleDateString([], { weekday: 'short' });
        } else {
            return date.toLocaleDateString();
        }
    }

    async loadMessages(userId, limit = 50) {
        try {
            const data = await api.getMessages(userId);
            this.messages = data.messages || [];
            return this.messages;
        } catch (error) {
            console.error('Error loading messages:', error);
            return [];
        }
    }

    async loadConversations() {
        try {
            return await api.getConversations();
        } catch (error) {
            console.error('Error loading conversations:', error);
            return { conversations: [] };
        }
    }

    showNotification(data) {
        if (Notification.permission === 'granted') {
            new Notification('New Message', {
                body: data.message || 'Sent you a message',
                icon: '/assets/images/logo.png'
            });
        }
    }

    on(event, callback) {
        this.listeners.push({ event, callback });
    }

    off(event, callback) {
        this.listeners = this.listeners.filter(l => 
            !(l.event === event && l.callback === callback)
        );
    }

    groupMessagesByDate(messages) {
        const groups = {};
        messages.forEach(msg => {
            const date = new Date(msg.created_at).toLocaleDateString();
            if (!groups[date]) groups[date] = [];
            groups[date].push(msg);
        });
        return groups;
    }
}

// Create global instance
const chatManager = new ChatManager();

// Initialize chat when DOM is ready (no auth required)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        chatManager.connect();
        chatManager.requestNotificationPermission();
    });
} else {
    chatManager.connect();
    chatManager.requestNotificationPermission();
}