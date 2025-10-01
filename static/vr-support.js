/**
 * VR Support for Video Server
 * Provides enhanced support for VR headsets like Oculus Quest 2
 */

class VRSupport {
    constructor() {
        this.isVR = this.detectVR();
        this.touchStartTime = 0;
        this.longPressThreshold = 500; // ms for long press
        this.debounceTimers = new Map();
        this.eventListeners = new Map();
        this.init();
    }

    detectVR() {
        // Detect VR browsers and devices
        const userAgent = navigator.userAgent.toLowerCase();
        const isOculusBrowser = userAgent.includes('oculusbrowser');
        const isVRMode = 'xr' in navigator || 'getVRDisplays' in navigator;
        const isMobile = /android|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
        
        // Check for VR-specific indicators
        const hasVRIndicators = isOculusBrowser || isVRMode || 
                               userAgent.includes('vr') || 
                               userAgent.includes('quest') ||
                               userAgent.includes('oculus');
        
        return hasVRIndicators;
    }

    init() {
        if (this.isVR) {
            console.log('🥽 VR mode detected - Enabling VR optimizations');
            this.addVRStyles();
            this.enhanceVideoInteractions();
            this.addVRControls();
            this.optimizeForVR();
        }
    }

    addVRStyles() {
        const vrStyles = document.createElement('style');
        vrStyles.id = 'vr-styles';
        vrStyles.textContent = `
            /* VR-specific styles */
            .vr-mode {
                --card-hover-scale: 1.05;
                --button-min-size: 44px;
                --text-size-boost: 1.2;
            }

            /* Larger touch targets for VR controllers */
            .vr-mode .btn,
            .vr-mode .favorite-btn,
            .vr-mode .rating i {
                min-width: var(--button-min-size);
                min-height: var(--button-min-size);
                font-size: calc(1rem * var(--text-size-boost));
                padding: 0.75rem;
            }

            /* Enhanced hover effects for VR */
            .vr-mode .card:hover {
                transform: scale(var(--card-hover-scale));
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                z-index: 10;
                position: relative;
            }

            /* VR-friendly video preview */
            .vr-mode .video-preview-container {
                border-radius: 12px;
                overflow: hidden;
            }

            /* Larger text for VR readability */
            .vr-mode .card-title {
                font-size: calc(0.9rem * var(--text-size-boost));
                line-height: 1.4;
            }

            .vr-mode .view-count {
                font-size: calc(0.8rem * var(--text-size-boost));
            }

            /* VR navigation improvements */
            .vr-mode .navbar {
                padding: 1rem 0;
            }

            .vr-mode .nav-link {
                font-size: calc(1rem * var(--text-size-boost));
                padding: 0.75rem 1rem;
            }

            /* VR video player enhancements */
            .vr-mode .video-js {
                border-radius: 12px;
            }

            .vr-mode .vjs-control-bar {
                font-size: calc(1rem * var(--text-size-boost));
            }

            /* VR-specific indicators */
            .vr-indicator {
                position: fixed;
                top: 10px;
                right: 10px;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 0.5rem;
                border-radius: 8px;
                font-size: 0.8rem;
                z-index: 1000;
            }

            /* Immersive mode button */
            .vr-immersive-btn {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 50%;
                width: 60px;
                height: 60px;
                font-size: 1.5rem;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                z-index: 1000;
                transition: all 0.3s ease;
            }

            .vr-immersive-btn:hover {
                transform: scale(1.1);
                background: #0056b3;
            }
        `;
        document.head.appendChild(vrStyles);
        document.body.classList.add('vr-mode');
    }

    enhanceVideoInteractions() {
        // Enhanced video interactions are now handled by VideoPreviewManager
        // This method now focuses on VR-specific UI enhancements
        console.log('🥽 VR video interactions enhanced by VideoPreviewManager');
    }

    addVRVideoPreview(container) {
        let video;
        let hasLoaded = false;
        let previewTimer;
        let isPlaying = false;

        // Touch/click handler for VR controllers
        const startPreview = () => {
            if (isPlaying) return;
            
            const preview = container.querySelector('.video-preview');
            video = preview?.querySelector('video');
            
            if (video && !hasLoaded) {
                video.load();
                hasLoaded = true;
                
                video.addEventListener('loadedmetadata', () => {
                    const previewTime = Math.min(video.duration * 0.05, 10);
                    video.currentTime = previewTime || 10;
                    video.play().then(() => {
                        isPlaying = true;
                        // Auto-stop after 5 seconds
                        previewTimer = setTimeout(stopPreview, 5000);
                    }).catch(() => {});
                }, { once: true });
            } else if (video && hasLoaded) {
                const previewTime = Math.min(video.duration * 0.05, 10);
                video.currentTime = previewTime || 10;
                video.play().then(() => {
                    isPlaying = true;
                    previewTimer = setTimeout(stopPreview, 5000);
                }).catch(() => {});
            }
        };

        const stopPreview = () => {
            if (video && isPlaying) {
                video.pause();
                video.currentTime = 0;
                isPlaying = false;
            }
            if (previewTimer) {
                clearTimeout(previewTimer);
                previewTimer = null;
            }
        };

        // Long press detection for VR controllers
        let touchStartTime = 0;
        
        container.addEventListener('touchstart', (e) => {
            touchStartTime = Date.now();
        });

        container.addEventListener('touchend', (e) => {
            const touchDuration = Date.now() - touchStartTime;
            if (touchDuration > this.longPressThreshold) {
                e.preventDefault();
                this.throttle(`preview-${container.dataset.filename || 'unknown'}`, startPreview, 1000);
            }
        });

        // Click handler for VR controllers (secondary button) - debounced
        container.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.debounce(`context-preview-${container.dataset.filename || 'unknown'}`, () => {
                if (isPlaying) {
                    stopPreview();
                } else {
                    startPreview();
                }
            }, 300);
        });

        // Fallback hover for desktop users - throttled
        if (!this.isVR) {
            container.addEventListener('mouseenter', () => {
                this.throttle(`hover-preview-${container.dataset.filename || 'unknown'}`, startPreview, 500);
            });
            container.addEventListener('mouseleave', stopPreview);
        }
    }

    addVRControls() {
        // Add VR indicator
        const vrIndicator = document.createElement('div');
        vrIndicator.className = 'vr-indicator';
        vrIndicator.textContent = '🥽 VR Mode';
        document.body.appendChild(vrIndicator);

        // Add immersive mode button if WebXR is available
        if ('xr' in navigator) {
            this.addImmersiveModeButton();
        }

        // Add VR-specific keyboard shortcuts
        this.addVRKeyboardShortcuts();
    }

    addImmersiveModeButton() {
        const immersiveBtn = document.createElement('button');
        immersiveBtn.className = 'vr-immersive-btn';
        immersiveBtn.innerHTML = '🥽';
        immersiveBtn.title = 'Enter VR Immersive Mode';
        
        const clickHandler = async () => {
            this.debounce('immersive-mode', async () => {
                try {
                    if (navigator.xr) {
                        const session = await navigator.xr.requestSession('immersive-vr');
                        console.log('🥽 Entered VR immersive mode');
                        
                        // Handle VR session
                        session.addEventListener('end', () => {
                            console.log('🥽 Exited VR immersive mode');
                        });
                    }
                } catch (error) {
                    console.log('VR immersive mode not available:', error);
                    // Fallback to fullscreen
                    if (document.documentElement.requestFullscreen) {
                        document.documentElement.requestFullscreen();
                    }
                }
            }, 500);
        };
        
        immersiveBtn.addEventListener('click', clickHandler);
        this.eventListeners.set('immersive-btn', { 
            element: immersiveBtn, 
            event: 'click', 
            handler: clickHandler 
        });

        document.body.appendChild(immersiveBtn);
    }

    addVRKeyboardShortcuts() {
        const keyHandler = (e) => {
            // VR-specific shortcuts with debouncing
            switch(e.key) {
                case 'v':
                case 'V':
                    if (e.ctrlKey) {
                        e.preventDefault();
                        this.debounce('toggle-vr', () => this.toggleVROptimizations(), 300);
                    }
                    break;
                case 'f':
                case 'F':
                    if (e.ctrlKey && e.shiftKey) {
                        e.preventDefault();
                        this.debounce('vr-fullscreen', () => this.enterFullscreen(), 300);
                    }
                    break;
            }
        };

        document.addEventListener('keydown', keyHandler);
        this.eventListeners.set('vr-keyboard', { 
            element: document, 
            event: 'keydown', 
            handler: keyHandler 
        });
    }

    toggleVROptimizations() {
        document.body.classList.toggle('vr-mode');
        const indicator = document.querySelector('.vr-indicator');
        if (indicator) {
            indicator.textContent = document.body.classList.contains('vr-mode') 
                ? '🥽 VR Mode' 
                : '🖥️ Desktop Mode';
        }
    }

    enterFullscreen() {
        if (document.documentElement.requestFullscreen) {
            document.documentElement.requestFullscreen();
        }
    }

    optimizeForVR() {
        // Optimize performance for VR
        this.optimizeAnimations();
        this.optimizeImages();
        this.addVRMetaTags();
    }

    optimizeAnimations() {
        // Reduce motion for VR comfort
        const style = document.createElement('style');
        style.textContent = `
            .vr-mode * {
                animation-duration: 0.2s !important;
                transition-duration: 0.2s !important;
            }
        `;
        document.head.appendChild(style);
    }

    optimizeImages() {
        // Preload visible thumbnails for smoother VR experience
        const thumbnails = document.querySelectorAll('.video-thumbnail');
        thumbnails.forEach(img => {
            if (img.loading !== 'lazy') {
                img.loading = 'eager';
            }
        });
    }

    addVRMetaTags() {
        // Add VR-friendly meta tags
        const metaTags = [
            { name: 'viewport', content: 'width=device-width, initial-scale=1.0, user-scalable=no' },
            { name: 'mobile-web-app-capable', content: 'yes' },
            { name: 'apple-mobile-web-app-capable', content: 'yes' },
            { name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent' }
        ];

        metaTags.forEach(tag => {
            const existing = document.querySelector(`meta[name="${tag.name}"]`);
            if (!existing) {
                const meta = document.createElement('meta');
                meta.name = tag.name;
                meta.content = tag.content;
                document.head.appendChild(meta);
            }
        });
    }

    // Public API for manual control
    static init() {
        return new VRSupport();
    }

    static isVRDevice() {
        return new VRSupport().detectVR();
    }

    // Performance utilities
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

    // Cleanup method for memory management
    cleanup() {
        // Clear timers
        this.debounceTimers.forEach(timer => clearTimeout(timer));
        this.debounceTimers.clear();
        
        // Remove event listeners
        this.eventListeners.forEach(({ element, event, handler }) => {
            element.removeEventListener(event, handler);
        });
        this.eventListeners.clear();
        
        // Remove VR-specific DOM elements
        const vrIndicator = document.querySelector('.vr-indicator');
        if (vrIndicator) vrIndicator.remove();
        
        const vrBtn = document.querySelector('.vr-immersive-btn');
        if (vrBtn) vrBtn.remove();
        
        const vrStyles = document.querySelector('#vr-styles');
        if (vrStyles) vrStyles.remove();
    }
}

// Auto-initialize VR support
document.addEventListener('DOMContentLoaded', () => {
    window.vrSupport = VRSupport.init();
});

// Export for manual use
window.VRSupport = VRSupport;