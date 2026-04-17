// PWA Installation and Update Handling
class PWAManager {
  constructor() {
    this.registration = null;
    this.init();
  }

  init() {
    // Unregister old service workers first
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.getRegistrations().then(registrations => {
        registrations.forEach(registration => {
          registration.unregister();
          console.log('[PWA] Unregistered old service worker');
        });
        
        // Then register new service worker when DOM is ready
        document.addEventListener('DOMContentLoaded', () => {
          this.registerServiceWorker();
        });
      });
    }

    // Handle install prompt
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      window.deferredPrompt = e;
      this.showInstallPrompt();
    });

    // Handle successful install
    window.addEventListener('appinstalled', () => {
      console.log('[PWA] App installed successfully');
      localStorage.setItem('pwa_installed', 'true');
      if (window.deferredPrompt) {
        window.deferredPrompt = null;
      }
    });

    // Handle online/offline status
    window.addEventListener('online', () => {
      console.log('[PWA] Back online');
      this.showNotification('Online', 'You are back online!');
    });

    window.addEventListener('offline', () => {
      console.log('[PWA] Offline');
      this.showNotification('Offline', 'You are now offline. Some features may be limited.');
    });
  }

  async registerServiceWorker() {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'
      });

      this.registration = registration;
      console.log('[PWA] Service Worker registered:', registration);

      // Check for updates periodically
      setInterval(() => {
        registration.update();
      }, 60000); // Check every minute

      // Listen for updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'activated') {
            this.showUpdateNotification();
          }
        });
      });
    } catch (error) {
      console.error('[PWA] Service Worker registration failed:', error);
    }
  }

  showInstallPrompt() {
    // Check if already installed
    if (localStorage.getItem('pwa_installed')) {
      return;
    }

    // Optionally show custom install button
    const installBtn = document.getElementById('pwa-install-btn');
    if (installBtn) {
      installBtn.style.display = 'block';
      installBtn.addEventListener('click', () => {
        if (window.deferredPrompt) {
          window.deferredPrompt.prompt();
          window.deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
              console.log('[PWA] User accepted install prompt');
            }
            window.deferredPrompt = null;
          });
        }
      });
    }
  }

  showUpdateNotification() {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('Lako Updated', {
        body: 'A new version is available. Please refresh the page.',
        icon: '/assets/images/logo-192.png',
        badge: '/assets/images/logo-192.png'
      });
    }
  }

  showNotification(title, message) {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(title, {
        body: message,
        icon: '/assets/images/logo-192.png',
        badge: '/assets/images/logo-192.png'
      });
    }
  }

  async requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }
    return Notification.permission === 'granted';
  }

  async clearCache() {
    if ('caches' in window) {
      const names = await caches.keys();
      return Promise.all(names.map(name => caches.delete(name)));
    }
  }

  getCacheSize() {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      return navigator.storage.estimate();
    }
    return null;
  }
}

// Initialize PWA manager
const pwa = new PWAManager();
