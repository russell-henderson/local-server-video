/**
 * VR Video Player Enhancements
 * Adds VR-specific video playback features
 */

class VRVideoPlayer {
    constructor(videoElement) {
        this.video = videoElement;
        this.isVR = window.vrSupport?.isVR || false;
        this.init();
    }

    init() {
        if (this.isVR) {
            this.addVRControls();
            this.optimizeForVR();
            this.addImmersiveFeatures();
        }
    }

    addVRControls() {
        // Add VR-friendly video controls
        const controlsContainer = document.createElement('div');
        controlsContainer.className = 'vr-video-controls';
        controlsContainer.innerHTML = `
            <div class="vr-control-panel">
                <button class="vr-btn vr-play-pause" title="Play/Pause">⏯️</button>
                <button class="vr-btn vr-rewind" title="Rewind 10s">⏪</button>
                <button class="vr-btn vr-forward" title="Forward 10s">⏩</button>
                <button class="vr-btn vr-fullscreen" title="Fullscreen">🔳</button>
                <button class="vr-btn vr-immersive" title="VR Mode">🥽</button>
            </div>
        `;

        // Insert after video element
        this.video.parentNode.insertBefore(controlsContainer, this.video.nextSibling);

        // Add event listeners
        this.attachVRControlEvents(controlsContainer);
        this.addVRControlStyles();
    }

    attachVRControlEvents(container) {
        const playPauseBtn = container.querySelector('.vr-play-pause');
        const rewindBtn = container.querySelector('.vr-rewind');
        const forwardBtn = container.querySelector('.vr-forward');
        const fullscreenBtn = container.querySelector('.vr-fullscreen');
        const immersiveBtn = container.querySelector('.vr-immersive');

        playPauseBtn.addEventListener('click', () => {
            if (this.video.paused) {
                this.video.play();
            } else {
                this.video.pause();
            }
        });

        rewindBtn.addEventListener('click', () => {
            this.video.currentTime = Math.max(0, this.video.currentTime - 10);
        });

        forwardBtn.addEventListener('click', () => {
            this.video.currentTime = Math.min(this.video.duration, this.video.currentTime + 10);
        });

        fullscreenBtn.addEventListener('click', () => {
            if (this.video.requestFullscreen) {
                this.video.requestFullscreen();
            }
        });

        immersiveBtn.addEventListener('click', () => {
            this.enterVRMode();
        });
    }

    addVRControlStyles() {
        const styles = document.createElement('style');
        styles.textContent = `
            .vr-video-controls {
                margin-top: 1rem;
                text-align: center;
            }

            .vr-control-panel {
                display: inline-flex;
                gap: 1rem;
                background: rgba(0, 0, 0, 0.8);
                padding: 1rem;
                border-radius: 12px;
                backdrop-filter: blur(10px);
            }

            .vr-btn {
                background: rgba(255, 255, 255, 0.2);
                border: 2px solid rgba(255, 255, 255, 0.3);
                color: white;
                padding: 1rem;
                border-radius: 8px;
                font-size: 1.2rem;
                cursor: pointer;
                transition: all 0.3s ease;
                min-width: 60px;
                min-height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .vr-btn:hover {
                background: rgba(255, 255, 255, 0.3);
                border-color: rgba(255, 255, 255, 0.5);
                transform: scale(1.05);
            }

            .vr-btn:active {
                transform: scale(0.95);
            }

            /* VR-specific video enhancements */
            .vr-mode .video-js {
                border-radius: 12px;
                overflow: hidden;
            }

            .vr-mode .vjs-control-bar {
                background: rgba(0, 0, 0, 0.8);
                backdrop-filter: blur(10px);
            }

            .vr-mode .vjs-button {
                font-size: 1.2em;
            }

            /* Immersive mode styles */
            .vr-immersive-video {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                z-index: 9999;
                background: black;
            }

            .vr-immersive-video video {
                width: 100%;
                height: 100%;
                object-fit: contain;
            }

            .vr-ui-overlay {
                position: absolute;
                bottom: 80px;
                left: 50%;
                transform: translateX(-50%);
                display: flex;
                gap: 2rem;
                background: rgba(0, 0, 0, 0.9);
                padding: 1.5rem;
                border-radius: 16px;
                backdrop-filter: blur(20px);
                border: 2px solid rgba(255, 255, 255, 0.1);
                max-width: 90vw;
                flex-wrap: wrap;
                justify-content: center;
            }

            .vr-video-info {
                text-align: center;
                color: white;
                min-width: 200px;
            }

            .vr-video-title {
                font-size: 1.2rem;
                margin: 0 0 0.5rem 0;
                color: #fff;
                text-overflow: ellipsis;
                overflow: hidden;
                white-space: nowrap;
                max-width: 300px;
            }

            .vr-view-count {
                font-size: 0.9rem;
                color: #ccc;
            }

            .vr-rating-container {
                text-align: center;
                min-width: 200px;
            }

            .vr-ui-title {
                color: white;
                font-size: 1rem;
                margin-bottom: 1rem;
                font-weight: 600;
            }

            .vr-rating {
                display: flex;
                gap: 0.75rem;
                justify-content: center;
            }

            .vr-rating i {
                color: #ffb300;
                font-size: 2rem;
                cursor: pointer;
                transition: all 0.2s ease;
                min-width: 50px;
                min-height: 50px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.1);
            }

            .vr-rating i:hover {
                transform: scale(1.2);
                background: rgba(255, 179, 0, 0.2);
                box-shadow: 0 0 20px rgba(255, 179, 0, 0.4);
            }

            .vr-favorite-container {
                display: flex;
                align-items: center;
                min-width: 200px;
            }

            .vr-favorite-btn {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.2);
                color: white;
                padding: 1rem 1.5rem;
                border-radius: 12px;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                gap: 0.75rem;
                font-size: 1rem;
                width: 100%;
                justify-content: center;
            }

            .vr-favorite-btn:hover {
                background: rgba(255, 255, 255, 0.2);
                border-color: rgba(255, 255, 255, 0.4);
                transform: scale(1.05);
            }

            .vr-favorite-btn i {
                font-size: 1.5rem;
                transition: all 0.2s ease;
            }

            .vr-exit-immersive {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                border: none;
                padding: 1rem;
                border-radius: 8px;
                cursor: pointer;
                font-size: 1rem;
            }
        `;
        document.head.appendChild(styles);
    }

    optimizeForVR() {
        // Optimize video settings for VR
        this.video.setAttribute('playsinline', 'true');
        this.video.setAttribute('webkit-playsinline', 'true');
        
        // Preload for smoother VR experience
        this.video.preload = 'metadata';

        // Add VR-friendly video events
        this.video.addEventListener('loadstart', () => {
            console.log('🥽 VR video loading optimized');
        });

        // Optimize for VR frame rates
        this.video.addEventListener('loadedmetadata', () => {
            // Ensure smooth playback for VR
            if (this.video.videoWidth && this.video.videoHeight) {
                console.log(`🥽 VR video loaded: ${this.video.videoWidth}x${this.video.videoHeight}`);
            }
        });
    }

    addImmersiveFeatures() {
        // Add gesture controls for VR
        this.addVRGestures();
        
        // Add spatial audio if available
        this.addSpatialAudio();
        
        // Add VR-specific keyboard shortcuts
        this.addVRKeyboardControls();
    }

    addVRGestures() {
        let touchStartX = 0;
        let touchStartY = 0;
        let touchStartTime = 0;

        this.video.addEventListener('touchstart', (e) => {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
            touchStartTime = Date.now();
        });

        this.video.addEventListener('touchend', (e) => {
            const touchEndX = e.changedTouches[0].clientX;
            const touchEndY = e.changedTouches[0].clientY;
            const touchDuration = Date.now() - touchStartTime;
            
            const deltaX = touchEndX - touchStartX;
            const deltaY = touchEndY - touchStartY;
            
            // Swipe gestures for VR controllers
            if (Math.abs(deltaX) > 50 && touchDuration < 500) {
                if (deltaX > 0) {
                    // Swipe right - forward 10s
                    this.video.currentTime = Math.min(this.video.duration, this.video.currentTime + 10);
                } else {
                    // Swipe left - rewind 10s
                    this.video.currentTime = Math.max(0, this.video.currentTime - 10);
                }
            }
            
            // Tap to play/pause
            if (Math.abs(deltaX) < 10 && Math.abs(deltaY) < 10 && touchDuration < 300) {
                if (this.video.paused) {
                    this.video.play();
                } else {
                    this.video.pause();
                }
            }
        });
    }

    addSpatialAudio() {
        // Add spatial audio context if available
        if ('AudioContext' in window || 'webkitAudioContext' in window) {
            try {
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                const audioContext = new AudioContext();
                
                // Create spatial audio nodes
                const source = audioContext.createMediaElementSource(this.video);
                const panner = audioContext.createPanner();
                
                // Configure spatial audio for VR
                panner.panningModel = 'HRTF';
                panner.distanceModel = 'inverse';
                panner.refDistance = 1;
                panner.maxDistance = 10000;
                panner.rolloffFactor = 1;
                
                // Connect audio nodes
                source.connect(panner);
                panner.connect(audioContext.destination);
                
                console.log('🥽 Spatial audio enabled for VR');
            } catch (error) {
                console.log('Spatial audio not available:', error);
            }
        }
    }

    addVRKeyboardControls() {
        document.addEventListener('keydown', (e) => {
            // Only handle if video is focused or in VR mode
            if (!document.body.classList.contains('vr-mode')) return;
            
            switch(e.key) {
                case ' ':
                    e.preventDefault();
                    if (this.video.paused) {
                        this.video.play();
                    } else {
                        this.video.pause();
                    }
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    this.video.currentTime = Math.max(0, this.video.currentTime - 10);
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.video.currentTime = Math.min(this.video.duration, this.video.currentTime + 10);
                    break;
                case 'f':
                case 'F':
                    if (!e.ctrlKey) {
                        e.preventDefault();
                        if (this.video.requestFullscreen) {
                            this.video.requestFullscreen();
                        }
                    }
                    break;
                case 'Escape':
                    this.exitVRMode();
                    break;
            }
        });
    }

    enterVRMode() {
        // Create immersive video container
        const immersiveContainer = document.createElement('div');
        immersiveContainer.className = 'vr-immersive-video';
        
        // Create exit button
        const exitBtn = document.createElement('button');
        exitBtn.className = 'vr-exit-immersive';
        exitBtn.textContent = '✕ Exit VR Mode';
        exitBtn.onclick = () => this.exitVRMode();
        
        // Move video to immersive container
        const originalParent = this.video.parentNode;
        const originalNextSibling = this.video.nextSibling;
        
        // Store original elements for restoration
        this.originalParent = originalParent;
        this.originalNextSibling = originalNextSibling;
        
        // Create VR UI overlay with ratings and favorites
        const vrOverlay = this.createVROverlay();
        
        immersiveContainer.appendChild(this.video);
        immersiveContainer.appendChild(vrOverlay);
        immersiveContainer.appendChild(exitBtn);
        document.body.appendChild(immersiveContainer);
        
        // Add keyboard shortcuts for VR mode
        this.addVRModeKeyboardShortcuts();
        
        // Enter fullscreen if available
        if (immersiveContainer.requestFullscreen) {
            immersiveContainer.requestFullscreen();
        }
        
        console.log('🥽 Entered VR immersive mode with ratings & favorites');
    }

    exitVRMode() {
        const immersiveContainer = document.querySelector('.vr-immersive-video');
        if (immersiveContainer && this.originalParent) {
            // Restore video to original position
            if (this.originalNextSibling) {
                this.originalParent.insertBefore(this.video, this.originalNextSibling);
            } else {
                this.originalParent.appendChild(this.video);
            }
            
            // Remove immersive container and all VR-specific event listeners
            immersiveContainer.remove();
            this.cleanupVRModeListeners();
            
            // Exit fullscreen
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
            
            console.log('🥽 Exited VR immersive mode');
        }
    }

    createVROverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'vr-ui-overlay';
        
        // Get current video filename for ratings/favorites
        const filename = this.getVideoFilename();
        if (!filename) return overlay;
        
        // Create VR-optimized rating interface
        const ratingSection = this.createVRRating(filename);
        
        // Create VR-optimized favorite interface  
        const favoriteSection = this.createVRFavorite(filename);
        
        // Create video info section
        const infoSection = this.createVRVideoInfo(filename);
        
        overlay.appendChild(infoSection);
        overlay.appendChild(ratingSection);
        overlay.appendChild(favoriteSection);
        
        return overlay;
    }

    createVRRating(filename) {
        const container = document.createElement('div');
        container.className = 'vr-rating-container';
        
        const title = document.createElement('div');
        title.className = 'vr-ui-title';
        title.textContent = 'Rate Video';
        
        const ratingDiv = document.createElement('div');
        ratingDiv.className = 'vr-rating';
        ratingDiv.setAttribute('data-filename', filename);
        
        // Get current rating from DOM or fetch from server
        const currentRating = this.getCurrentRating(filename);
        
        for (let i = 1; i <= 5; i++) {
            const star = document.createElement('i');
            star.className = i <= currentRating ? 'fas fa-star' : 'far fa-star';
            star.setAttribute('data-value', i);
            star.setAttribute('role', 'button');
            star.setAttribute('tabindex', '0');
            star.setAttribute('aria-label', `Rate ${i} star${i !== 1 ? 's' : ''}`);
            
            // Add VR-optimized click handler with debouncing
            star.addEventListener('click', this.debounce(`vr-rating-${i}`, () => {
                this.handleVRRating(filename, i, ratingDiv);
            }, 300));
            
            ratingDiv.appendChild(star);
        }
        
        container.appendChild(title);
        container.appendChild(ratingDiv);
        return container;
    }

    createVRFavorite(filename) {
        const container = document.createElement('div');
        container.className = 'vr-favorite-container';
        
        const favoriteBtn = document.createElement('button');
        favoriteBtn.className = 'vr-favorite-btn';
        favoriteBtn.setAttribute('data-filename', filename);
        favoriteBtn.setAttribute('aria-label', 'Toggle favorite');
        
        const isFavorited = this.getCurrentFavoriteStatus(filename);
        
        const icon = document.createElement('i');
        icon.className = isFavorited ? 'fas fa-heart' : 'far fa-heart';
        icon.style.color = '#ff4757';
        
        const label = document.createElement('span');
        label.textContent = isFavorited ? 'Remove from Favorites' : 'Add to Favorites';
        
        favoriteBtn.appendChild(icon);
        favoriteBtn.appendChild(label);
        
        // Add VR-optimized click handler with debouncing
        favoriteBtn.addEventListener('click', this.debounce(`vr-favorite-${filename}`, () => {
            this.handleVRFavorite(filename, favoriteBtn);
        }, 300));
        
        container.appendChild(favoriteBtn);
        return container;
    }

    createVRVideoInfo(filename) {
        const container = document.createElement('div');
        container.className = 'vr-video-info';
        
        const title = document.createElement('h3');
        title.className = 'vr-video-title';
        title.textContent = decodeURIComponent(filename);
        
        const viewCount = document.createElement('div');
        viewCount.className = 'vr-view-count';
        viewCount.textContent = this.getCurrentViewCount(filename);
        
        container.appendChild(title);
        container.appendChild(viewCount);
        return container;
    }

    // Utility methods
    getVideoFilename() {
        const src = this.video.src || this.video.getAttribute('src');
        if (src && src.includes('/video/')) {
            return decodeURIComponent(src.split('/video/')[1]);
        }
        
        // Fallback: try to get from page context
        const videoInfo = document.querySelector('.video-info');
        const favoriteBtn = videoInfo?.querySelector('.favorite-btn');
        return favoriteBtn?.getAttribute('data-filename') || null;
    }

    getCurrentRating(filename) {
        const ratingElement = document.querySelector(`.rating[data-filename="${filename}"]`);
        if (ratingElement) {
            const filledStars = ratingElement.querySelectorAll('.fas.fa-star');
            return filledStars.length;
        }
        return 0;
    }

    getCurrentFavoriteStatus(filename) {
        const favoriteBtn = document.querySelector(`.favorite-btn[data-filename="${filename}"]`);
        if (favoriteBtn) {
            const icon = favoriteBtn.querySelector('i');
            return icon?.classList.contains('fas');
        }
        return false;
    }

    getCurrentViewCount(filename) {
        const viewElement = document.querySelector('#video-view-count');
        return viewElement?.textContent || 'Views: 0';
    }

    // VR-specific event handlers
    handleVRRating(filename, rating, ratingDiv) {
        fetch('/rate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename, rating })
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                // Update VR rating display
                const stars = ratingDiv.querySelectorAll('i');
                stars.forEach((star, index) => {
                    star.className = (index + 1) <= rating ? 'fas fa-star' : 'far fa-star';
                });
                
                // Update main page rating if visible
                if (window.optimizedUtils) {
                    window.optimizedUtils.updateRatingDisplay(
                        document.querySelector(`.rating[data-filename="${filename}"]`), 
                        rating
                    );
                }
                
                console.log('🥽 VR rating updated:', rating);
            }
        })
        .catch(console.error);
    }

    handleVRFavorite(filename, favoriteBtn) {
        fetch('/favorite', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                const isFavorited = data.favorites.includes(filename);
                
                // Update VR favorite display
                const icon = favoriteBtn.querySelector('i');
                const label = favoriteBtn.querySelector('span');
                
                icon.className = isFavorited ? 'fas fa-heart' : 'far fa-heart';
                label.textContent = isFavorited ? 'Remove from Favorites' : 'Add to Favorites';
                
                // Update main page favorite buttons if visible
                if (window.optimizedUtils) {
                    window.optimizedUtils.updateFavoriteButtons(filename, isFavorited);
                }
                
                console.log('🥽 VR favorite updated:', isFavorited);
            }
        })
        .catch(console.error);
    }

    addVRModeKeyboardShortcuts() {
        this.vrKeyboardHandler = (e) => {
            if (!document.querySelector('.vr-immersive-video')) return;
            
            switch(e.key) {
                case '1':
                case '2':
                case '3':
                case '4':
                case '5':
                    e.preventDefault();
                    const filename = this.getVideoFilename();
                    if (filename) {
                        this.handleVRRating(filename, parseInt(e.key), 
                            document.querySelector('.vr-rating'));
                    }
                    break;
                case 'f':
                case 'F':
                    if (!e.ctrlKey) {
                        e.preventDefault();
                        const filename = this.getVideoFilename();
                        if (filename) {
                            const favoriteBtn = document.querySelector('.vr-favorite-btn');
                            this.handleVRFavorite(filename, favoriteBtn);
                        }
                    }
                    break;
            }
        };
        
        document.addEventListener('keydown', this.vrKeyboardHandler);
    }

    cleanupVRModeListeners() {
        if (this.vrKeyboardHandler) {
            document.removeEventListener('keydown', this.vrKeyboardHandler);
            this.vrKeyboardHandler = null;
        }
    }

    // Debounce utility
    debounce(key, func, delay = 250) {
        if (!this.debounceTimers) this.debounceTimers = new Map();
        
        if (this.debounceTimers.has(key)) {
            clearTimeout(this.debounceTimers.get(key));
        }

        const timer = setTimeout(() => {
            func();
            this.debounceTimers.delete(key);
        }, delay);

        this.debounceTimers.set(key, timer);
        return func; // Return the function for the event listener
    }

    // Static method to initialize VR video player
    static init(videoSelector = 'video') {
        const videos = document.querySelectorAll(videoSelector);
        videos.forEach(video => {
            if (!video.vrPlayer) {
                video.vrPlayer = new VRVideoPlayer(video);
            }
        });
    }
}

// Auto-initialize for video.js players
document.addEventListener('DOMContentLoaded', () => {
    // Wait for video.js to initialize
    setTimeout(() => {
        VRVideoPlayer.init('#my-video');
    }, 1000);
});

// Export for manual use
window.VRVideoPlayer = VRVideoPlayer;