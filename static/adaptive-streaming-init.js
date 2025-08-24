/**
 * Adaptive Streaming Initialization
 * Initializes the adaptive streaming system when videos are loaded
 */

class AdaptiveStreamingManager {
    constructor() {
        this.controller = null;
        this.isInitialized = false;
        this.debugMode = false;
        
        this.init();
    }

    init() {
        // Wait for dependencies to load
        if (typeof NetworkMonitor === 'undefined' || typeof AdaptiveStreamingController === 'undefined') {
            setTimeout(() => this.init(), 100);
            return;
        }

        this.controller = new AdaptiveStreamingController();
        this.isInitialized = true;
        
        this.bindGlobalEvents();
        this.enhanceExistingVideos();
        
        // Enable debug mode if URL parameter is present
        if (window.location.search.includes('streaming-debug=true')) {
            this.enableDebugMode();
        }
        
        console.log('🎬 Adaptive Streaming Manager initialized');
    }

    bindGlobalEvents() {
        // Handle dynamically added videos
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const videos = node.tagName === 'VIDEO' ? [node] : node.querySelectorAll('video');
                        videos.forEach(video => this.enhanceVideo(video));
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        // Handle page navigation (for SPAs)
        window.addEventListener('popstate', () => {
            setTimeout(() => this.enhanceExistingVideos(), 100);
        });

        // Handle visibility changes (pause monitoring when tab is hidden)
        document.addEventListener('visibilitychange', () => {
            if (this.controller && this.controller.networkMonitor) {
                if (document.hidden) {
                    this.controller.networkMonitor.stop();
                } else {
                    this.controller.networkMonitor.start();
                }
            }
        });
    }

    enhanceExistingVideos() {
        document.querySelectorAll('video').forEach(video => {
            this.enhanceVideo(video);
        });
    }

    enhanceVideo(video) {
        // Skip if already enhanced
        if (video.hasAttribute('data-adaptive-streaming')) return;
        
        video.setAttribute('data-adaptive-streaming', 'true');
        
        // Ensure video container exists
        let container = video.closest('.video-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'video-container';
            video.parentNode.insertBefore(container, video);
            container.appendChild(video);
        }

        // Add quality controls if not already present
        if (!container.querySelector('.quality-selector')) {
            this.addQualityControls(container);
        }

        // Attach adaptive streaming events
        this.attachAdaptiveEvents(video);
        
        console.log('🎬 Enhanced video with adaptive streaming');
    }

    addQualityControls(container) {
        const qualitySelector = document.createElement('div');
        qualitySelector.className = 'quality-selector';
        qualitySelector.innerHTML = `
            <div class="quality-dropdown">
                <button class="quality-btn" type="button" aria-label="Quality Settings">
                    <i class="fas fa-cog" aria-hidden="true"></i>
                    <span class="quality-label">Auto</span>
                </button>
                <div class="quality-menu" role="menu">
                    ${this.controller.qualities.map(quality => `
                        <div class="quality-option" role="menuitem" data-quality="${quality.value}" tabindex="0">
                            <span class="quality-name">${quality.label}</span>
                            ${quality.bitrate > 0 ? `<span class="quality-bitrate">${this.formatBitrate(quality.bitrate)}</span>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
            <div class="quality-indicator">
                <div class="network-status">
                    <i class="fas fa-wifi" aria-hidden="true"></i>
                    <span class="connection-speed">--</span>
                </div>
                <div class="buffer-status" role="progressbar" aria-label="Buffer Status">
                    <div class="buffer-fill"></div>
                </div>
            </div>
        `;

        container.appendChild(qualitySelector);
    }

    attachAdaptiveEvents(video) {
        // Monitor video events for adaptive streaming
        video.addEventListener('loadstart', () => {
            if (this.controller.autoMode) {
                this.controller.selectOptimalQuality(video);
            }
        });

        video.addEventListener('progress', () => {
            this.controller.updateBufferStatus(video);
        });

        video.addEventListener('waiting', () => {
            this.controller.handleBuffering(video);
        });

        video.addEventListener('canplay', () => {
            this.controller.handleBufferRecovery(video);
        });

        video.addEventListener('error', () => {
            this.controller.handleVideoError(video);
        });

        // Keyboard navigation for quality controls
        const container = video.closest('.video-container');
        const qualityOptions = container.querySelectorAll('.quality-option');
        
        qualityOptions.forEach(option => {
            option.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    option.click();
                }
            });
        });
    }

    formatBitrate(bitrate) {
        if (bitrate >= 1000000) {
            return `${(bitrate / 1000000).toFixed(1)} Mbps`;
        } else if (bitrate >= 1000) {
            return `${(bitrate / 1000).toFixed(0)} Kbps`;
        }
        return `${bitrate} bps`;
    }

    enableDebugMode() {
        this.debugMode = true;
        this.createDebugPanel();
        console.log('🐛 Adaptive streaming debug mode enabled');
    }

    createDebugPanel() {
        const debugPanel = document.createElement('div');
        debugPanel.className = 'streaming-stats';
        debugPanel.innerHTML = `
            <h4>Streaming Stats</h4>
            <div class="stat-row">
                <span class="stat-label">Quality:</span>
                <span class="stat-value" id="debug-quality">Auto</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Speed:</span>
                <span class="stat-value" id="debug-speed">-- Mbps</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Buffer:</span>
                <span class="stat-value" id="debug-buffer">-- s</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Switches:</span>
                <span class="stat-value" id="debug-switches">0</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Connection:</span>
                <span class="stat-value" id="debug-connection">--</span>
            </div>
        `;

        document.body.appendChild(debugPanel);

        // Update debug panel periodically
        setInterval(() => {
            this.updateDebugPanel();
        }, 1000);
    }

    updateDebugPanel() {
        if (!this.debugMode || !this.controller) return;

        const stats = this.controller.getNetworkStats();
        const history = this.controller.getQualityHistory();

        document.getElementById('debug-quality').textContent = this.controller.getCurrentQuality();
        document.getElementById('debug-speed').textContent = this.formatBitrate(stats.currentSpeed);
        document.getElementById('debug-switches').textContent = history.length;
        document.getElementById('debug-connection').textContent = stats.connectionType || 'unknown';

        // Update buffer status for first video
        const firstVideo = document.querySelector('video');
        if (firstVideo) {
            const bufferHealth = this.controller.getBufferHealth(firstVideo);
            document.getElementById('debug-buffer').textContent = `${bufferHealth.toFixed(1)}s`;
        }
    }

    // Public API
    getController() {
        return this.controller;
    }

    setQuality(quality) {
        if (this.controller) {
            this.controller.setQuality(quality);
        }
    }

    enableAutoMode() {
        if (this.controller) {
            this.controller.enableAutoMode();
        }
    }

    disableAutoMode() {
        if (this.controller) {
            this.controller.disableAutoMode();
        }
    }

    getStats() {
        return this.controller ? this.controller.getNetworkStats() : null;
    }

    // Preset configurations
    applyPreset(preset) {
        const presets = {
            'high-quality': () => {
                this.setQuality('1080p');
                console.log('🎬 Applied high quality preset');
            },
            'data-saver': () => {
                this.setQuality('480p');
                console.log('🎬 Applied data saver preset');
            },
            'auto-adaptive': () => {
                this.enableAutoMode();
                console.log('🎬 Applied auto adaptive preset');
            },
            'mobile-optimized': () => {
                this.setQuality('720p');
                console.log('🎬 Applied mobile optimized preset');
            }
        };

        if (presets[preset]) {
            presets[preset]();
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.adaptiveStreamingManager = new AdaptiveStreamingManager();
    });
} else {
    window.adaptiveStreamingManager = new AdaptiveStreamingManager();
}

// Export for global use
window.AdaptiveStreamingManager = AdaptiveStreamingManager;