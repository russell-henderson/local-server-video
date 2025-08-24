/**
 * Enhanced Video Preview System
 * Handles cross-platform compatibility issues, especially for mobile browsers and VR devices
 */

class VideoPreviewManager {
    constructor() {
        this.previewTimeout = 500; // ms delay before starting preview
        this.loadTimeout = 3000; // ms timeout for video loading
        this.previewDuration = 5000; // ms duration for auto-stop
        this.maxConcurrentPreviews = 2; // limit concurrent video loads
        this.activePreviewsCount = 0;
        this.deviceCapabilities = this.getDeviceCapabilities();
        this.init();
    }

    getDeviceCapabilities() {
        // Use the global device detector if available, otherwise fallback to basic detection
        if (window.deviceDetector) {
            const caps = window.deviceDetector.getCapabilities();
            return {
                isMobile: caps.isMobile,
                isTablet: caps.isTablet,
                isVR: caps.isVR,
                hasTouch: caps.hasTouch,
                hasHover: caps.hasHover,
                isLowMemory: caps.isLowMemory,
                isSlowConnection: caps.isSlowConnection,
                shouldUsePreview: caps.shouldUseVideoPreview,
                previewStrategy: caps.recommendedPreviewStrategy
            };
        }
        
        return this.detectDeviceCapabilities();
    }

    detectDeviceCapabilities() {
        const userAgent = navigator.userAgent.toLowerCase();
        
        // Enhanced device detection
        const isMobile = /android|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
        const isTablet = /ipad|android(?!.*mobile)/i.test(userAgent);
        const isVR = /oculusbrowser|quest|oculus|vr/i.test(userAgent) || 
                     'xr' in navigator || 
                     'getVRDisplays' in navigator;
        
        // Touch capability detection
        const hasTouch = 'ontouchstart' in window || 
                        navigator.maxTouchPoints > 0 || 
                        navigator.msMaxTouchPoints > 0;
        
        // Hover capability detection
        const hasHover = window.matchMedia('(hover: hover)').matches;
        
        // Memory estimation (rough)
        const memoryGB = navigator.deviceMemory || 4; // default to 4GB if unknown
        const isLowMemory = memoryGB < 4;
        
        // Connection quality
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        const isSlowConnection = connection && (
            connection.effectiveType === 'slow-2g' || 
            connection.effectiveType === '2g' ||
            connection.saveData === true
        );

        return {
            isMobile,
            isTablet,
            isVR,
            hasTouch,
            hasHover,
            isLowMemory,
            isSlowConnection,
            shouldUsePreview: this.shouldEnablePreview(hasHover, isMobile, isVR, isLowMemory, isSlowConnection),
            previewStrategy: this.getPreviewStrategy(hasHover, hasTouch, isVR, isMobile)
        };
    }

    shouldEnablePreview(hasHover, isMobile, isVR, isLowMemory, isSlowConnection) {
        // Disable preview for constrained devices
        if (isLowMemory || isSlowConnection) {
            console.log('📱 Video preview disabled: Low memory or slow connection');
            return false;
        }
        
        // Enable for desktop with hover
        if (hasHover && !isMobile) {
            return true;
        }
        
        // Enable for VR with touch controls
        if (isVR) {
            return true;
        }
        
        // Disable for mobile browsers (too unreliable)
        if (isMobile) {
            console.log('📱 Video preview disabled: Mobile device detected');
            return false;
        }
        
        return false;
    }

    getPreviewStrategy(hasHover, hasTouch, isVR, isMobile) {
        if (isVR) return 'vr-touch';
        if (hasHover && !isMobile) return 'hover';
        if (hasTouch) return 'touch';
        return 'disabled';
    }

    init() {
        console.log('🎬 Video Preview Manager initialized', this.deviceCapabilities);
        
        if (!this.deviceCapabilities.shouldUsePreview) {
            this.addFallbackIndicators();
            return;
        }

        this.setupPreviewContainers();
        this.addPerformanceMonitoring();
    }

    setupPreviewContainers() {
        document.querySelectorAll('.video-preview-container').forEach(container => {
            this.enhanceContainer(container);
        });
    }

    enhanceContainer(container) {
        const strategy = this.deviceCapabilities.previewStrategy;
        
        switch (strategy) {
            case 'hover':
                this.setupHoverPreview(container);
                break;
            case 'vr-touch':
                this.setupVRPreview(container);
                break;
            case 'touch':
                this.setupTouchPreview(container);
                break;
            default:
                this.setupFallback(container);
        }
    }

    setupHoverPreview(container) {
        let hoverTimer;
        let loadTimer;
        let video;
        let hasLoaded = false;
        let isPlaying = false;

        const startPreview = () => {
            if (this.activePreviewsCount >= this.maxConcurrentPreviews) {
                console.log('🎬 Preview skipped: Too many active previews');
                return;
            }

            hoverTimer = setTimeout(() => {
                if (!container.matches(':hover')) return;
                
                const preview = container.querySelector('.video-preview');
                video = preview?.querySelector('video');
                
                if (!video) return;

                this.activePreviewsCount++;
                this.showLoadingIndicator(container);

                // Set loading timeout
                loadTimer = setTimeout(() => {
                    this.handleLoadTimeout(container, video);
                }, this.loadTimeout);

                if (!hasLoaded) {
                    video.load();
                    hasLoaded = true;
                    
                    video.addEventListener('loadedmetadata', () => {
                        clearTimeout(loadTimer);
                        this.hideLoadingIndicator(container);
                        
                        if (container.matches(':hover')) {
                            this.playPreview(video, container);
                            isPlaying = true;
                        } else {
                            this.activePreviewsCount--;
                        }
                    }, { once: true });

                    video.addEventListener('error', () => {
                        this.handleVideoError(container, video);
                    }, { once: true });
                } else {
                    clearTimeout(loadTimer);
                    this.hideLoadingIndicator(container);
                    this.playPreview(video, container);
                    isPlaying = true;
                }
            }, this.previewTimeout);
        };

        const stopPreview = () => {
            clearTimeout(hoverTimer);
            clearTimeout(loadTimer);
            
            if (video && isPlaying) {
                video.pause();
                video.currentTime = 0;
                isPlaying = false;
                this.activePreviewsCount--;
            }
            
            this.hideLoadingIndicator(container);
        };

        container.addEventListener('mouseenter', startPreview);
        container.addEventListener('mouseleave', stopPreview);
        
        // Prevent preview from interfering with clicks
        container.addEventListener('click', stopPreview);
    }

    setupVRPreview(container) {
        let video;
        let hasLoaded = false;
        let isPlaying = false;
        let previewTimer;

        const togglePreview = (e) => {
            e.preventDefault();
            
            if (isPlaying) {
                this.stopVRPreview(video, container);
                isPlaying = false;
            } else {
                this.startVRPreview(container).then((v) => {
                    video = v;
                    isPlaying = true;
                    
                    // Auto-stop after duration
                    previewTimer = setTimeout(() => {
                        this.stopVRPreview(video, container);
                        isPlaying = false;
                    }, this.previewDuration);
                }).catch(() => {
                    console.log('🥽 VR preview failed to start');
                });
            }
        };

        // Long press for VR controllers
        let touchStartTime = 0;
        
        container.addEventListener('touchstart', (e) => {
            touchStartTime = Date.now();
        });

        container.addEventListener('touchend', (e) => {
            const touchDuration = Date.now() - touchStartTime;
            if (touchDuration > 500) { // Long press
                togglePreview(e);
            }
        });

        // Context menu for secondary VR controller button
        container.addEventListener('contextmenu', togglePreview);
    }

    setupTouchPreview(container) {
        // For touch devices, show a preview button instead of auto-preview
        this.addPreviewButton(container);
    }

    setupFallback(container) {
        // Add static preview indicator
        this.addStaticPreviewIndicator(container);
    }

    async startVRPreview(container) {
        return new Promise((resolve, reject) => {
            if (this.activePreviewsCount >= this.maxConcurrentPreviews) {
                reject(new Error('Too many active previews'));
                return;
            }

            const preview = container.querySelector('.video-preview');
            const video = preview?.querySelector('video');
            
            if (!video) {
                reject(new Error('Video element not found'));
                return;
            }

            this.activePreviewsCount++;
            this.showLoadingIndicator(container);

            const loadTimer = setTimeout(() => {
                this.handleLoadTimeout(container, video);
                reject(new Error('Load timeout'));
            }, this.loadTimeout);

            video.addEventListener('loadedmetadata', () => {
                clearTimeout(loadTimer);
                this.hideLoadingIndicator(container);
                this.playPreview(video, container);
                resolve(video);
            }, { once: true });

            video.addEventListener('error', () => {
                clearTimeout(loadTimer);
                this.handleVideoError(container, video);
                reject(new Error('Video load error'));
            }, { once: true });

            video.load();
        });
    }

    stopVRPreview(video, container) {
        if (video) {
            video.pause();
            video.currentTime = 0;
            this.activePreviewsCount--;
        }
        this.hideLoadingIndicator(container);
    }

    playPreview(video, container) {
        const previewTime = Math.min(video.duration * 0.05, 10);
        video.currentTime = previewTime || 10;
        
        video.play().catch((error) => {
            console.log('🎬 Preview play failed:', error);
            this.handleVideoError(container, video);
        });
    }

    showLoadingIndicator(container) {
        let indicator = container.querySelector('.preview-loading');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'preview-loading';
            indicator.innerHTML = '⏳';
            container.appendChild(indicator);
        }
        indicator.style.display = 'block';
    }

    hideLoadingIndicator(container) {
        const indicator = container.querySelector('.preview-loading');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    handleLoadTimeout(container, video) {
        console.log('🎬 Preview load timeout');
        this.activePreviewsCount--;
        this.hideLoadingIndicator(container);
        this.showErrorIndicator(container, 'Load timeout');
    }

    handleVideoError(container, video) {
        console.log('🎬 Preview video error');
        this.activePreviewsCount--;
        this.hideLoadingIndicator(container);
        this.showErrorIndicator(container, 'Preview unavailable');
    }

    showErrorIndicator(container, message) {
        let indicator = container.querySelector('.preview-error');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'preview-error';
            container.appendChild(indicator);
        }
        indicator.textContent = message;
        indicator.style.display = 'block';
        
        // Hide after 2 seconds
        setTimeout(() => {
            indicator.style.display = 'none';
        }, 2000);
    }

    addPreviewButton(container) {
        const button = document.createElement('button');
        button.className = 'preview-btn';
        button.innerHTML = '▶️';
        button.title = 'Tap to preview';
        
        button.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            this.startVRPreview(container).then((video) => {
                setTimeout(() => {
                    this.stopVRPreview(video, container);
                }, this.previewDuration);
            }).catch(() => {
                console.log('📱 Touch preview failed');
            });
        });
        
        container.appendChild(button);
    }

    addStaticPreviewIndicator(container) {
        const indicator = document.createElement('div');
        indicator.className = 'preview-disabled';
        indicator.innerHTML = '📱';
        indicator.title = 'Preview disabled on this device';
        container.appendChild(indicator);
    }

    addFallbackIndicators() {
        // Add CSS for fallback states
        const style = document.createElement('style');
        style.textContent = `
            .preview-disabled {
                position: absolute;
                top: 8px;
                left: 8px;
                background: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                z-index: 5;
            }
        `;
        document.head.appendChild(style);

        document.querySelectorAll('.video-preview-container').forEach(container => {
            this.addStaticPreviewIndicator(container);
        });
    }

    addPerformanceMonitoring() {
        // Monitor preview performance
        setInterval(() => {
            if (this.activePreviewsCount > 0) {
                console.log(`🎬 Active previews: ${this.activePreviewsCount}/${this.maxConcurrentPreviews}`);
            }
        }, 5000);
    }

    // Public API
    static init() {
        return new VideoPreviewManager();
    }

    static getDeviceCapabilities() {
        return new VideoPreviewManager().deviceCapabilities;
    }
}

// Enhanced CSS for all preview states
const enhancedStyles = document.createElement('style');
enhancedStyles.textContent = `
    /* Enhanced video preview styles */
    .preview-loading {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 16px;
        z-index: 15;
        display: none;
    }

    .preview-error {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(220, 53, 69, 0.9);
        color: white;
        padding: 6px 10px;
        border-radius: 6px;
        font-size: 12px;
        z-index: 15;
        display: none;
    }

    .preview-btn {
        position: absolute;
        top: 8px;
        right: 8px;
        background: rgba(0, 123, 255, 0.9);
        color: white;
        border: none;
        border-radius: 50%;
        width: 32px;
        height: 32px;
        font-size: 12px;
        cursor: pointer;
        z-index: 10;
        transition: all 0.3s ease;
    }

    .preview-btn:hover {
        background: rgba(0, 123, 255, 1);
        transform: scale(1.1);
    }

    /* VR-specific enhancements */
    .vr-mode .preview-btn {
        width: 44px;
        height: 44px;
        font-size: 16px;
    }

    /* Mobile-specific adjustments */
    @media (max-width: 768px) {
        .video-preview {
            display: none !important;
        }
        
        .preview-btn {
            width: 40px;
            height: 40px;
            font-size: 14px;
        }
    }

    /* Reduced motion for accessibility */
    @media (prefers-reduced-motion: reduce) {
        .video-preview,
        .preview-loading,
        .preview-error {
            transition: none !important;
            animation: none !important;
        }
    }
`;
document.head.appendChild(enhancedStyles);

// Export for global use
window.VideoPreviewManager = VideoPreviewManager;

// === Mobile Tap-to-Preview System ===
// Add tap support (no hover on touch), with per‑card delay via data-preview-delay
(() => {
  const supportsHover = window.matchMedia("(hover: hover)").matches;

  const getDelay = (el) => {
    const v = parseInt(el?.dataset?.previewDelay || "500", 10);
    return Number.isFinite(v) ? Math.max(0, v) : 500;
  };

  const startPreview = (card) => {
    if (!card || card.__previewActive) return;
    card.__previewActive = true;
    card.dispatchEvent(new CustomEvent("preview:start", { bubbles: true }));
  };

  const stopPreview = (card) => {
    if (!card || !card.__previewActive) return;
    card.__previewActive = false;
    card.dispatchEvent(new CustomEvent("preview:stop", { bubbles: true }));
  };

  const bindCard = (card) => {
    let hoverTimer = null;

    // Hover path (desktop)
    if (supportsHover) {
      card.addEventListener("mouseenter", () => {
        hoverTimer = window.setTimeout(() => startPreview(card), getDelay(card));
      });
      card.addEventListener("mouseleave", () => {
        if (hoverTimer) window.clearTimeout(hoverTimer);
        stopPreview(card);
      });
      return;
    }

    // Touch path (mobile/VR)
    let touchActive = false;

    const onTap = (e) => {
      // Single tap toggles preview; second tap within the card will stop
      if (!touchActive) {
        touchActive = true;
        setTimeout(() => startPreview(card), getDelay(card));
      } else {
        touchActive = false;
        stopPreview(card);
      }
      e.stopPropagation();
    };

    card.addEventListener("touchstart", onTap, { passive: true });
    card.addEventListener("click", (e) => {
      // Allow click to also toggle on non‑hover devices
      onTap(e);
    });

    // Close preview when tapping outside
    document.addEventListener("touchstart", (e) => {
      if (!card.contains(e.target)) {
        touchActive = false;
        stopPreview(card);
      }
    }, { passive: true });
  };

  // Bind all preview cards
  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-role='video-card']").forEach(bindCard);
  });
})();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.videoPreviewManager = VideoPreviewManager.init();
    });
} else {
    window.videoPreviewManager = VideoPreviewManager.init();
}