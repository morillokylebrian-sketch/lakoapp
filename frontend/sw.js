// Lako PWA Service Worker
// Provides offline functionality and intelligent caching

const CACHE_NAME = 'lako-v1';
const RUNTIME_CACHE = 'lako-runtime-v1';
const IMAGE_CACHE = 'lako-images-v1';
const API_CACHE = 'lako-api-v1';

const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/css/universal.css',
  '/css/main.css',
  '/css/components.css',
  '/css/guest.css',
  '/css/customer.css',
  '/css/vendor.css',
  '/css/admin.css',
  '/css/auth.css',
  '/css/dashboard.css',
  '/css/mobile-first.css',
  '/js/api.js',
  '/js/app.js',
  '/js/auth.js',
  '/js/utils.js',
  '/js/localDB.js',
  '/js/sync.js',
  '/js/imageHandler.js',
  '/js/map.js',
  '/js/heatmap.js',
  '/js/chart.js',
  '/js/pwa.js',
  '/js/chat.js',
  '/pages/landing.html',
  '/pages/login.html',
  '/pages/register.html',
  '/pages/reset-password.html',
  '/pages/guest/browse.html',
  '/pages/customer/dashboard.html',
  '/pages/customer/news-feed.html',
  '/pages/customer/map.html',
  '/pages/customer/search.html',
  '/pages/customer/shortlist.html',
  '/pages/customer/suggestions.html',
  '/pages/customer/activities.html',
  '/pages/customer/profile.html',
  '/pages/customer/chat.html',
  '/pages/customer/chat-list.html',
  '/pages/vendor/dashboard.html',
  '/pages/vendor/products.html',
  '/pages/vendor/analytics.html',
  '/pages/vendor/orders.html',
  '/pages/vendor/settings.html',
  '/pages/vendor/login.html',
  '/pages/vendor/register.html',
  '/pages/admin/dashboard.html',
  '/pages/admin/login.html',
  '/pages/admin/users.html',
  '/pages/admin/vendors.html',
  '/pages/admin/products.html',
  '/pages/admin/posts.html',
  '/pages/admin/reviews.html',
  '/pages/admin/media.html',
  '/pages/admin/reports.html',
  '/pages/admin/settings.html',
  '/components/header.html',
  '/components/footer.html',
  '/components/bottom-nav.html',
  '/components/sidebar.html',
  '/components/modal.html',
  '/assets/images/logo-192.png',
  '/assets/images/logo-512.png',
  '/assets/images/logo.svg'
];

// Install event - cache essential assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('[SW] Caching app shell');
      return cache.addAll(ASSETS_TO_CACHE).catch(err => {
        console.warn('[SW] Some assets failed to cache (expected during development):', err);
      });
    })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME && 
              cacheName !== RUNTIME_CACHE && 
              cacheName !== IMAGE_CACHE && 
              cacheName !== API_CACHE) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - intelligent caching strategy
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // For non-GET requests (POST, PUT, DELETE, etc), always use network
  if (request.method !== 'GET') {
    event.respondWith(
      fetch(request).catch(() => {
        return new Response(
          JSON.stringify({ error: 'Network request failed' }),
          { status: 503, headers: { 'Content-Type': 'application/json' } }
        );
      })
    );
    return;
  }

  // API calls - network first, fallback to cache
  if (url.pathname.startsWith('/api')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          if (!response || response.status !== 200 || response.type === 'error') {
            return response;
          }
          // Clone and store successful API responses
          const responseClone = response.clone();
          caches.open(API_CACHE).then(cache => {
            cache.put(request, responseClone);
          });
          return response;
        })
        .catch(() => {
          // Return cached API response if available
          return caches.match(request).then(response => {
            return response || new Response(
              JSON.stringify({ error: 'offline', cache: true }),
              { 
                status: 200,
                headers: { 'Content-Type': 'application/json' }
              }
            );
          });
        })
    );
    return;
  }

  // Images - cache first, fallback to network
  if (request.url.match(/\.(png|jpg|jpeg|svg|gif|webp)$/)) {
    event.respondWith(
      caches.open(IMAGE_CACHE).then(cache => {
        return cache.match(request).then(response => {
          return response || fetch(request).then(response => {
            if (response && response.status === 200) {
              cache.put(request, response.clone());
            }
            return response;
          }).catch(() => {
            return new Response(null, { status: 404 });
          });
        });
      })
    );
    return;
  }

  // HTML, CSS, JS - stale while revalidate
  if (request.destination === 'document' || 
      request.destination === 'style' || 
      request.destination === 'script') {
    event.respondWith(
      caches.match(request).then(cached => {
        const fetched = fetch(request).then(response => {
          if (response && response.status === 200) {
            const responseClone = response.clone();
            caches.open(RUNTIME_CACHE).then(cache => {
              cache.put(request, responseClone);
            });
          }
          return response;
        }).catch(err => {
          console.warn('[SW] Fetch failed:', err);
          return cached || new Response('Offline', { status: 503 });
        });

        return cached || fetched;
      })
    );
    return;
  }

  // Default strategy - cache first, network fallback
  event.respondWith(
    caches.match(request)
      .then(response => {
        if (response) return response;
        return fetch(request).then(response => {
          if (!response || response.status !== 200) {
            return response;
          }
          const responseClone = response.clone();
          caches.open(RUNTIME_CACHE).then(cache => {
            cache.put(request, responseClone);
          });
          return response;
        });
      })
      .catch(() => new Response('Offline', { status: 503 }))
  );
});

// Background sync for offline actions (optional enhancement)
self.addEventListener('sync', event => {
  if (event.tag === 'sync-actions') {
    event.waitUntil(
      caches.open(API_CACHE).then(cache => {
        // Process any pending actions when back online
        return cache.keys().then(requests => {
          return Promise.all(
            requests.map(request => {
              return fetch(request).catch(() => {
                // If still failing, keep it for next sync
                return null;
              });
            })
          );
        });
      })
    );
  }
});

// Message handling for cache management
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    caches.keys().then(cacheNames => {
      Promise.all(
        cacheNames.map(cacheName => caches.delete(cacheName))
      ).then(() => {
        event.ports[0].postMessage({ cleared: true });
      });
    });
  }
});
