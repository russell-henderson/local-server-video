/**
 * Adaptive Bitrate Streaming Controller
 * Automatically adjusts video quality based on network conditions and device capabilities
 */

class AdaptiveStreamingController {
    constructor() {
        this.qualities = [
            { label: 'Auto', value: 'auto', bitrate: 0 },
            { label: '4K', value: '2160p', bitrate: 25000000, width: 3840, height: 2160 },
            { label: '1440p', value: '1440p', bitrate: 16000000, width: 2560, height: 1440 },
            { label: '1080p', value: '1080p', bitrate: 8000000, width: 1920, height: 1080 },
            { label: '720p', value: '720p', bitrate: 5000000, width: 1280, height: 720 },
            { label: '480p', value: '480p', bitrate: 2500000, width: 854, height: 480 },
            { label: '360p', value: '360p', bitrate: 1000000, width: 640, height: 360 },
            { label: '240p', value: '240p', bitrate: 500000, width: 426, height: 240 }
        ];
        
        this.currentQuality = 'auto';
        this.autoMode = true;
        this.networkMonitor = new NetworkMonitor();
        this.deviceCapabilities = this.detectDeviceCapabilities();
        this.qualityHistory = [];
        this.bufferHealthThreshold = 10; // seconds
        this.switchCooldown = 5000; // 5 seconds between switches
        this.lastSwitchTime = 0;
        
        this.init();
    }

    init() {
        this.createQualityControls();
        this.bindEvents();
        this.startNetworkMonitoring();
        
        console.log('🎬 Adaptive Streaming Controller initialized');
        console.log('Device capabilities:', this.deviceCapabilities);
    }

    detectDeviceCapabilities() {
        const screen = window.screen;
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        
        return {
            maxResolution: this.getMaxSupportedResolution(),
            screenWidth: screen.width,
            screenHeight: screen.height,
            devicePixelRatio: window.devicePixelRatio || 1,
            connectionType: connection ? connection.effectiveType : 'unknown',
            downlink: connection ? connection.downlink : null,
            saveData: connection ? connection.saveData : false,
            hardwareConcurrency: navigator.hardwareConcurrency || 4,
            memory: navigator.deviceMemory || 4
        };
    }

    getMaxSupportedResolution() {
        const screen = window.screen;
        const width = screen.width * (window.devicePixelRatio || 1);
        const height = screen.height * (window.devicePixelRatio || 1);
        
        if (width >= 3840 && height >= 2160) return '2160p';
        if (width >= 2560 && height >= 1440) return '1440p';
        if (width >= 1920 && height >= 1080) return '1080p';
        if (width >= 1280 && height >= 720) return '720p';
        if (width >= 854 && height >= 480) return '480p';
        return '360p';
    }

    createQualityControls() {
        // Create quality selector for video players
        const qualitySelector = document.createElement('div');
        qualitySelector.className = 'quality-selector';
        qualitySelector.innerHTML = `
            <div class="quality-dropdown">
                <button class="quality-btn" id="quality-toggle">
                    <i class="fas fa-cog"></i>
                    <span class="quality-label">Auto</span>
                </button>
                <div class="quality-menu" id="quality-menu">
                    ${this.qualities.map(quality => `
                        <div class="quality-option" data-quality="${quality.value}">
                            <span class="quality-name">${quality.label}</span>
                            ${quality.bitrate > 0 ? `<span class="quality-bitrate">${this.formatBitrate(quality.bitrate)}</span>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
            <div class="quality-indicator">
                <div class="network-status">
                    <i class="fas fa-wifi"></i>
                    <span class="connection-speed">--</span>
                </div>
                <div class="buffer-status">
                    <div class="buffer-bar">
                        <div class="buffer-fill"></div>
                    </div>
                </div>
            </div>
        `;

        // Add to video containers
        document.querySelectorAll('video').forEach(video => {
            const container = video.closest('.video-container') || video.parentElement;
            if (container && !container.querySelector('.quality-selector')) {
                container.appendChild(qualitySelector.cloneNode(true));
            }
        });
    }

    bindEvents() {
        // Quality selector events
        document.addEventListener('click', (e) => {
            if (e.target.closest('.quality-btn')) {
                const menu = e.target.closest('.quality-dropdown').querySelector('.quality-menu');
                menu.classList.toggle('show');
            }
            
            if (e.target.closest('.quality-option')) {
                const quality = e.target.closest('.quality-option').dataset.quality;
                this.setQuality(quality);
                
                // Close menu
                document.querySelectorAll('.quality-menu').forEach(menu => {
                    menu.classList.remove('show');
                });
            }
        });

        // Close quality menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.quality-dropdown')) {
                document.querySelectorAll('.quality-menu').forEach(menu => {
                    menu.classList.remove('show');
                });
            }
        });

        // Video events for adaptive streaming
        document.addEventListener('loadstart', (e) => {
            if (e.target.tagName === 'VIDEO') {
                this.attachVideoEvents(e.target);
            }
        });

        // Network change events
        if (navigator.connection) {
            navigator.connection.addEventListener('change', () => {
                this.handleNetworkChange();
            });
        }
    }

    attachVideoEvents(video) {
        video.addEventListener('loadedmetadata', () => {
            if (this.autoMode) {
                this.selectOptimalQuality(video);
            }
        });

        video.addEventListener('progress', () => {
            this.updateBufferStatus(video);
        });

        video.addEventListener('waiting', () => {
            this.handleBuffering(video);
        });

        video.addEventListener('canplay', () => {
            this.handleBufferRecovery(video);
        });

        video.addEventListener('error', () => {
            this.handleVideoError(video);
        });
    }

    setQuality(quality) {
        this.currentQuality = quality;
        this.autoMode = quality === 'auto';
        
        // Update UI
        document.querySelectorAll('.quality-label').forEach(label => {
            const qualityObj = this.qualities.find(q => q.value === quality);
            label.textContent = qualityObj ? qualityObj.label : 'Auto';
        });

        // Update quality options
        document.querySelectorAll('.quality-option').forEach(option => {
            option.classList.toggle('active', option.dataset.quality === quality);
        });

        // Apply to all videos
        document.querySelectorAll('video').forEach(video => {
            this.applyQualityToVideo(video, quality);
        });

        this.showQualityNotification(quality);
        console.log(`🎬 Quality set to: ${quality}`);
    }

    applyQualityToVideo(video, quality) {
        if (!video.src) return;

        const currentSrc = video.src;
        const currentTime = video.currentTime;
        const wasPlaying = !video.paused;

        if (quality === 'auto') {
            // Let adaptive algorithm choose
            this.selectOptimalQuality(video);
            return;
        }

        // Generate quality-specific URL
        const newSrc = this.generateQualityUrl(currentSrc, quality);
        
        if (newSrc !== currentSrc) {
            video.src = newSrc;
            video.currentTime = currentTime;
            
            if (wasPlaying) {
                video.play().catch(() => {
                    console.log('Failed to resume playback after quality change');
                });
            }
        }
    }

    generateQualityUrl(originalUrl, quality) {
        // This would typically involve server-side support for multiple quality streams
        // For now, we'll add quality parameters to the URL
        const url = new URL(originalUrl, window.location.origin);
        url.searchParams.set('quality', quality);
        return url.toString();
    }

    selectOptimalQuality(video) {
        if (!this.autoMode) return;

        const networkSpeed = this.networkMonitor.getCurrentSpeed();
        const bufferHealth = this.getBufferHealth(video);
        const deviceCaps = this.deviceCapabilities;
        
        let optimalQuality = this.calculateOptimalQuality(networkSpeed, bufferHealth, deviceCaps);
        
        // Apply quality switching logic
        if (this.shouldSwitchQuality(optimalQuality)) {
            this.applyQualityToVideo(video, optimalQuality);
            this.recordQualitySwitch(optimalQuality);
        }
    }

    calculateOptimalQuality(networkSpeed, bufferHealth, deviceCaps) {
        // Start with device capability limits
        let maxQuality = this.qualities.find(q => q.value === deviceCaps.maxResolution);
        
        // Filter qualities based on network speed (with safety margin)
        const availableQualities = this.qualities.filter(quality => {
            if (quality.value === 'auto') return false;
            return quality.bitrate <= (networkSpeed * 0.8); // 80% of available bandwidth
        });

        if (availableQualities.length === 0) {
            return '240p'; // Fallback to lowest quality
        }

        // Consider buffer health
        let targetQuality;
        if (bufferHealth < 5) {
            // Low buffer - choose conservative quality
            targetQuality = availableQualities[Math.floor(availableQualities.length * 0.3)];
        } else if (bufferHealth > 15) {
            // Good buffer - can try higher quality
            targetQuality = availableQualities[availableQualities.length - 1];
        } else {
            // Medium buffer - balanced approach
            targetQuality = availableQualities[Math.floor(availableQualities.length * 0.6)];
        }

        // Don't exceed device capabilities
        if (maxQuality && targetQuality.bitrate > maxQuality.bitrate) {
            targetQuality = maxQuality;
        }

        return targetQuality.value;
    }

    shouldSwitchQuality(newQuality) {
        const now = Date.now();
        
        // Respect cooldown period
        if (now - this.lastSwitchTime < this.switchCooldown) {
            return false;
        }

        // Don't switch if already at target quality
        if (newQuality === this.currentQuality) {
            return false;
        }

        return true;
    }

    recordQualitySwitch(quality) {
        this.lastSwitchTime = Date.now();
        this.qualityHistory.push({
            quality,
            timestamp: this.lastSwitchTime,
            networkSpeed: this.networkMonitor.getCurrentSpeed(),
            reason: 'adaptive'
        });

        // Keep only recent history
        if (this.qualityHistory.length > 50) {
            this.qualityHistory = this.qualityHistory.slice(-25);
        }
    }

    getBufferHealth(video) {
        if (!video.buffered.length) return 0;
        
        const currentTime = video.currentTime;
        const buffered = video.buffered;
        
        for (let i = 0; i < buffered.length; i++) {
            if (currentTime >= buffered.start(i) && currentTime <= buffered.end(i)) {
                return buffered.end(i) - currentTime;
            }
        }
        
        return 0;
    }

    updateBufferStatus(video) {
        const bufferHealth = this.getBufferHealth(video);
        const bufferPercentage = Math.min((bufferHealth / this.bufferHealthThreshold) * 100, 100);
        
        document.querySelectorAll('.buffer-fill').forEach(fill => {
            fill.style.width = `${bufferPercentage}%`;
            fill.className = `buffer-fill ${this.getBufferHealthClass(bufferHealth)}`;
        });
    }

    getBufferHealthClass(bufferHealth) {
        if (bufferHealth < 3) return 'buffer-critical';
        if (bufferHealth < 8) return 'buffer-low';
        if (bufferHealth < 15) return 'buffer-medium';
        return 'buffer-good';
    }

    handleBuffering(video) {
        console.log('🔄 Video buffering detected');
        
        if (this.autoMode) {
            // Consider downgrading quality if buffering frequently
            setTimeout(() => {
                if (video.readyState < 3) { // Still buffering
                    this.selectOptimalQuality(video);
                }
            }, 2000);
        }
    }

    handleBufferRecovery(video) {
        console.log('✅ Buffer recovered');
        
        if (this.autoMode) {
            // Consider upgrading quality if buffer is healthy
            setTimeout(() => {
                const bufferHealth = this.getBufferHealth(video);
                if (bufferHealth > 10) {
                    this.selectOptimalQuality(video);
                }
            }, 5000);
        }
    }

    handleVideoError(video) {
        console.log('❌ Video error detected, trying lower quality');
        
        if (this.autoMode) {
            // Try lower quality on error
            const currentQualityIndex = this.qualities.findIndex(q => q.value === this.currentQuality);
            if (currentQualityIndex > 1) {
                const lowerQuality = this.qualities[currentQualityIndex + 1];
                this.applyQualityToVideo(video, lowerQuality.value);
            }
        }
    }

    handleNetworkChange() {
        console.log('🌐 Network conditions changed');
        
        if (this.autoMode) {
            // Re-evaluate quality for all videos
            setTimeout(() => {
                document.querySelectorAll('video').forEach(video => {
                    this.selectOptimalQuality(video);
                });
            }, 1000);
        }
    }

    startNetworkMonitoring() {
        this.networkMonitor.start();
        
        // Update network status display
        setInterval(() => {
            const speed = this.networkMonitor.getCurrentSpeed();
            const speedText = this.formatBitrate(speed);
            
            document.querySelectorAll('.connection-speed').forEach(element => {
                element.textContent = speedText;
            });
        }, 2000);
    }

    formatBitrate(bitrate) {
        if (bitrate >= 1000000) {
            return `${(bitrate / 1000000).toFixed(1)} Mbps`;
        } else if (bitrate >= 1000) {
            return `${(bitrate / 1000).toFixed(0)} Kbps`;
        }
        return `${bitrate} bps`;
    }

    showQualityNotification(quality) {
        const qualityObj = this.qualities.find(q => q.value === quality);
        const message = `Quality: ${qualityObj ? qualityObj.label : quality}`;
        
        // Remove existing notification
        const existing = document.querySelector('.quality-notification');
        if (existing) existing.remove();

        // Create notification
        const notification = document.createElement('div');
        notification.className = 'quality-notification';
        notification.textContent = message;
        
        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            bottom: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(0, 0, 0, 0.8)',
            color: 'white',
            padding: '0.75rem 1.5rem',
            borderRadius: '25px',
            fontSize: '0.9rem',
            fontWeight: '500',
            zIndex: '9999',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            opacity: '0',
            transition: 'all 0.3s ease'
        });

        document.body.appendChild(notification);

        // Animate in
        requestAnimationFrame(() => {
            notification.style.opacity = '1';
        });

        // Remove after 2 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }

    // Public API
    getCurrentQuality() {
        return this.currentQuality;
    }

    getQualityHistory() {
        return [...this.qualityHistory];
    }

    getNetworkStats() {
        return this.networkMonitor.getStats();
    }

    enableAutoMode() {
        this.setQuality('auto');
    }

    disableAutoMode() {
        if (this.autoMode) {
            this.setQuality('1080p'); // Default to 1080p when disabling auto
        }
    }
}

// Export for global use
window.AdaptiveStreamingController = AdaptiveStreamingController;