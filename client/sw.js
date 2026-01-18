/**
 * Service Worker for PWA
 */

const CACHE_NAME = 'mindx-voice-v1';
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/css/style.css',
    '/js/api.js',
    '/js/auth.js',
    '/js/router.js',
    '/js/app.js',
    '/manifest.json',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css',
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        })
    );
    self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Skip API requests - always go to network
    if (url.pathname.startsWith('/api') || url.origin !== location.origin) {
        // For API requests, try network first
        if (url.pathname.startsWith('/api')) {
            event.respondWith(
                fetch(event.request).catch(() => {
                    return new Response(JSON.stringify({ error: 'Offline' }), {
                        status: 503,
                        headers: { 'Content-Type': 'application/json' }
                    });
                })
            );
            return;
        }
    }

    // For static assets - cache first, then network
    event.respondWith(
        caches.match(event.request).then((response) => {
            if (response) {
                return response;
            }

            return fetch(event.request).then((fetchResponse) => {
                // Don't cache non-successful responses
                if (!fetchResponse || fetchResponse.status !== 200) {
                    return fetchResponse;
                }

                // Clone and cache the response
                const responseToCache = fetchResponse.clone();
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, responseToCache);
                });

                return fetchResponse;
            });
        }).catch(() => {
            // Return offline page for navigation requests
            if (event.request.mode === 'navigate') {
                return caches.match('/index.html');
            }
        })
    );
});

// Background sync for offline messages (future feature)
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-messages') {
        // Handle offline message sync
    }
});
