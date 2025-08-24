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
        
        immersiveContainer.appendChild(this.video);
        immersiveContainer.appendChild(exitBtn);
        document.body.appendChild(immersiveContainer);
        
        // Store original position for restoration
        this.originalParent = originalParent;
        this.originalNextSibling = originalNextSibling;
        
        // Enter fullscreen if available
        if (immersiveContainer.requestFullscreen) {
            immersiveContainer.requestFullscreen();
        }
        
        console.log('🥽 Entered VR immersive mode');
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
            
            // Remove immersive container
            immersiveContainer.remove();
            
            // Exit fullscreen
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
            
            console.log('🥽 Exited VR immersive mode');
        }
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