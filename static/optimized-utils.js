/**
 * Optimized Utilities - Shared functions and performance improvements
 * Consolidates common patterns and reduces code duplication
 */

class OptimizedUtils {
    constructor() {
        this.elementCache = new Map();
        this.eventListeners = new Map();
        this.debounceTimers = new Map();
        this.init();
    }

    init() {
        // Batch DOM operations
        this.batchDOMOperations();
        
        // Setup global event delegation
        this.setupEventDelegation();
        
        // Optimize existing scripts
        this.optimizeExistingScripts();
        
        console.log('⚡ Optimized utilities initialized');
    }

    // Cached element selection with automatic cleanup
    getElement(selector, useCache = true) {
        if (!useCache) {
            return document.querySelector(selector);
        }

        if (this.elementCache.has(selector)) {
            const element = this.elementCache.get(selector);
            // Verify element is still in DOM
            if (document.contains(element)) {
                return element;
            } else {
                this.elementCache.delete(selector);
            }
        }

        const element = document.querySelector(selector);
        if (element) {
            this.elementCache.set(selector, element);
        }
        return element;
    }

    getElements(selector, useCache = true) {
        const cacheKey = `${selector}:all`;
        
        if (useCache && this.elementCache.has(cacheKey)) {
            const elements = this.elementCache.get(cacheKey);
            // Check if all elements are still in DOM
            if (elements.every(el => document.contains(el))) {
                return elements;
            } else {
                this.elementCache.delete(cacheKey);
            }
        }

        const elements = Array.from(document.querySelectorAll(selector));
        if (useCache && elements.length > 0) {
            this.elementCache.set(cacheKey, elements);
        }
        return elements;
    }

    // Debounced function execution
    debounce(key, func, delay = 250) {
        if (this.debounceTimers.has(key)) {
            clearTimeout(this.debounceTimers.get(key));
        }

        const timer = setTimeout(() => {
            func();
            this.debounceTimers.delete(key);
        }, delay);

        this.debounceTimers.set(key, timer);
    }

    // Throttled function execution
    throttle(key, func, delay = 250) {
        if (this.debounceTimers.has(key)) {
            return; // Already running
        }

        func();
        const timer = setTimeout(() => {
            this.debounceTimers.delete(key);
        }, delay);

        this.debounceTimers.set(key, timer);
    }

    // Optimized event listener management
    addEventListenerOptimized(element, event, handler, options = {}) {
        const key = `${element.tagName}-${event}-${handler.name}`;
        
        // Remove existing listener if it exists
        this.removeEventListenerOptimized(key);
        
        // Add new listener
        element.addEventListener(event, handler, options);
        
        // Store for cleanup
        this.eventListeners.set(key, { element, event, handler, options });
    }

    removeEventListenerOptimized(key) {
        if (this.eventListeners.has(key)) {
            const { element, event, handler } = this.eventListeners.get(key);
            element.removeEventListener(event, handler);
            this.eventListeners.delete(key);
        }
    }

    // Global event delegation for common patterns
    setupEventDelegation() {
        // Delegate video clicks
        document.addEventListener('click', (e) => {
            // Video link clicks
            const videoLink = e.target.closest('a[href*="/watch/"]');
            if (videoLink) {
                this.handleVideoClick(videoLink);
            }

            // Favorite button clicks
            const favoriteBtn = e.target.closest('.favorite-btn');
            if (favoriteBtn) {
                this.handleFavoriteClick(favoriteBtn, e);
            }

            // Rating star clicks
            const ratingStar = e.target.closest('.rating i[data-value]');
            if (ratingStar) {
                this.handleRatingClick(ratingStar, e);
            }
        });

        // Delegate video events
        document.addEventListener('play', (e) => {
            if (e.target.tagName === 'VIDEO') {
                this.handleVideoPlay(e.target);
            }
        }, true);

        // Delegate input events with debouncing
        document.addEventListener('input', (e) => {
            if (e.target.matches('.search-input, .tag-input')) {
                this.debounce(`input-${e.target.id}`, () => {
                    this.handleInputChange(e.target);
                });
            }
        });
    }

    // Consolidated video click handler
    handleVideoClick(link) {
        const href = link.getAttribute('href');
        const filename = href.split('/watch/')[1];
        
        if (filename && window.recentlyPlayed) {
            window.recentlyPlayed.addItem({
                type: 'video',
                name: decodeURIComponent(filename),
                url: href,
                timestamp: Date.now()
            });
        }
    }

    // Consolidated favorite handler
    handleFavoriteClick(button, event) {
        event.preventDefault();
        event.stopPropagation();
        
        const filename = button.dataset.filename;
        if (!filename) return;

        this.throttle(`favorite-${filename}`, () => {
            fetch('/favorite', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    // Update all favorite buttons for this video
                    this.updateFavoriteButtons(filename, data.favorites.includes(filename));
                }
            })
            .catch(console.error);
        });
    }

    // Consolidated rating handler
    handleRatingClick(star, event) {
        event.preventDefault();
        event.stopPropagation();
        
        const rating = parseInt(star.dataset.value);
        const container = star.closest('.rating');
        const filename = container.dataset.filename;
        
        if (!filename) return;

        this.throttle(`rating-${filename}`, () => {
            fetch('/rate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename, rating })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    this.updateRatingDisplay(container, rating);
                }
            })
            .catch(console.error);
        });
    }

    // Consolidated video play handler
    handleVideoPlay(video) {
        // Record view
        this.throttle(`view-${video.src}`, () => {
            const filename = this.extractFilenameFromSrc(video.src);
            if (filename) {
                fetch('/view', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename })
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        this.updateViewCounts(filename, data.views);
                    }
                })
                .catch(console.error);
            }
        });
    }

    // Batch DOM operations for better performance
    batchDOMOperations() {
        // Use DocumentFragment for multiple DOM insertions
        this.createDocumentFragment = () => document.createDocumentFragment();
        
        // Batch style updates
        this.batchStyleUpdate = (element, styles) => {
            const originalDisplay = element.style.display;
            element.style.display = 'none';
            
            Object.assign(element.style, styles);
            
            element.style.display = originalDisplay;
        };
    }

    // Optimize existing scripts by removing redundant event listeners
    optimizeExistingScripts() {
        // Remove duplicate DOMContentLoaded listeners
        this.consolidateDOMContentLoaded();
        
        // Optimize video element queries
        this.optimizeVideoQueries();
        
        // Consolidate similar event handlers
        this.consolidateEventHandlers();
    }

    consolidateDOMContentLoaded() {
        // Store all DOMContentLoaded callbacks
        const callbacks = [];
        
        // Override addEventListener for DOMContentLoaded
        const originalAddEventListener = document.addEventListener;
        document.addEventListener = function(type, listener, options) {
            if (type === 'DOMContentLoaded') {
                callbacks.push(listener);
                return;
            }
            return originalAddEventListener.call(this, type, listener, options);
        };
        
        // Execute all callbacks once
        if (document.readyState === 'loading') {
            // Use originalAddEventListener to ensure our listener is actually registered
            originalAddEventListener.call(document, 'DOMContentLoaded', () => {
                callbacks.forEach(callback => {
                    try {
                        callback();
                    } catch (error) {
                        console.error('DOMContentLoaded callback error:', error);
                    }
                });
            });
        } else {
            // DOM already loaded, execute immediately
            callbacks.forEach(callback => {
                try {
                    callback();
                } catch (error) {
                    console.error('DOMContentLoaded callback error:', error);
                }
            });
        }

        // Restore original addEventListener
        document.addEventListener = originalAddEventListener;
    }

    optimizeVideoQueries() {
        // Cache video elements and update when DOM changes
        let videoCache = null;
        let videoCacheTime = 0;
        const CACHE_DURATION = 5000; // 5 seconds
        
        window.getVideosOptimized = () => {
            const now = Date.now();
            if (!videoCache || (now - videoCacheTime) > CACHE_DURATION) {
                videoCache = Array.from(document.querySelectorAll('video'));
                videoCacheTime = now;
            }
            return videoCache;
        };
        
        // Invalidate cache when DOM changes
        const observer = new MutationObserver(() => {
            videoCache = null;
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    consolidateEventHandlers() {
        // Remove redundant click handlers and use delegation instead
        this.removeRedundantHandlers();
    }

    removeRedundantHandlers() {
        // This would remove existing handlers that are now handled by delegation
        // Implementation depends on specific existing handlers
    }

    // Utility functions
    extractFilenameFromSrc(src) {
        if (src.includes('/video/')) {
            return decodeURIComponent(src.split('/video/')[1]);
        }
        return null;
    }

    updateFavoriteButtons(filename, isFavorite) {
        const buttons = this.getElements(`[data-filename="${filename}"].favorite-btn`);
        // Debug: log the attempt so we can trace per-theme issues
        try {
            console.debug('[OptimizedUtils] updateFavoriteButtons', { filename, isFavorite, count: buttons.length });
        } catch (e) { /* ignore logging errors in older consoles */ }

        buttons.forEach(btn => {
            const icon = btn.querySelector('i');
            if (!icon) return;

            // Preserve any existing classes (e.g., fa-heart, text-danger) and only toggle the style family
            // Remove existing style families if present
            icon.classList.remove('fas', 'far', 'fal', 'fab', 'fad');
            // Add the requested family and ensure base heart class exists
            icon.classList.add(isFavorite ? 'fas' : 'far');
            if (!icon.classList.contains('fa-heart')) icon.classList.add('fa-heart');
            if (!icon.classList.contains('text-danger')) icon.classList.add('text-danger');

            // Set ARIA and data attributes for easier visual debugging and CSS hooks
            try { btn.setAttribute('aria-pressed', isFavorite ? 'true' : 'false'); } catch (e) {}
            try { icon.setAttribute('data-favorited', isFavorite ? 'true' : 'false'); } catch (e) {}

            // Debug: report the icon classes after change
            try {
                console.debug('[OptimizedUtils] favorite-button-updated', { filename, btn, className: icon.className });
            } catch (e) {}
        });
    }

    updateRatingDisplay(container, rating) {
        const stars = container.querySelectorAll('i');
        stars.forEach((star, index) => {
            star.className = (index + 1) <= rating ? 'fas fa-star' : 'far fa-star';
        });
    }

    updateViewCounts(filename, views) {
        const elements = this.getElements(`[id*="view-count"][id*="${filename.replace(/\./g, '-')}"]`);
        elements.forEach(el => {
            el.textContent = `Views: ${views}`;
        });
    }

    // Performance monitoring
    measurePerformance(name, func) {
        const start = performance.now();
        const result = func();
        const end = performance.now();
        console.log(`⚡ ${name}: ${(end - start).toFixed(2)}ms`);
        return result;
    }

    // Memory cleanup
    cleanup() {
        // Clear caches
        this.elementCache.clear();
        
        // Clear timers
        this.debounceTimers.forEach(timer => clearTimeout(timer));
        this.debounceTimers.clear();
        
        // Remove event listeners
        this.eventListeners.forEach(({ element, event, handler }) => {
            element.removeEventListener(event, handler);
        });
        this.eventListeners.clear();
    }

    // Static initialization
    static init() {
        if (!window.optimizedUtils) {
            window.optimizedUtils = new OptimizedUtils();
        }
        return window.optimizedUtils;
    }
}

// Auto-initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        OptimizedUtils.init();
    });
} else {
    OptimizedUtils.init();
}

// Export for manual use
window.OptimizedUtils = OptimizedUtils;