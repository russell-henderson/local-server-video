// Basic service worker for caching static assets
const CACHE_NAME = 'local-video-server-v1';
const STATIC_CACHE_URLS = [
  '/',
  '/static/styles.css',
  '/static/js/rating.js',
  '/static/js/optimized-utils.js',
  '/static/js/video-preview-enhanced.js',
  // Add other critical static assets
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(STATIC_CACHE_URLS))
  );
});

self.addEventListener('fetch', event => {
  // Only cache GET requests for static assets
  if (event.request.method === 'GET' && event.request.url.includes('/static/')) {
    event.respondWith(
      caches.match(event.request)
        .then(response => response || fetch(event.request))
    );
  }
});

self.addEventListener('activate', event => {
  // Clean up old caches
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});