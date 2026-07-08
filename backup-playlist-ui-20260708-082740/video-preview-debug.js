/**
 * Video Preview Debug Utility
 * Helps diagnose video preview issues across different platforms
 */

class VideoPreviewDebugger {
    constructor() {
        this.testResults = {};
        this.init();
    }

    init() {
        // Add debug panel if in development
        if (this.isDevelopment()) {
            this.createDebugPanel();
        }
        
        // Log device capabilities
        this.logDeviceInfo();
    }

    isDevelopment() {
        return window.location.hostname === 'localhost' || 
               window.location.hostname === '127.0.0.1' ||
               window.location.search.includes('debug=true');
    }

    createDebugPanel() {
        const panel = document.createElement('div');
        panel.id = 'video-preview-debug';
        panel.innerHTML = `
            <div style="position: fixed; top: 10px; left: 10px; background: rgba(0,0,0,0.9); color: white; padding: 10px; border-radius: 8px; font-family: monospace; font-size: 12px; z-index: 9999; max-width: 300px;">
                <h4>Video Preview Debug</h4>
                <button onclick="window.videoDebugger.runTests()">Run Tests</button>
                <button onclick="window.videoDebugger.togglePanel()">Toggle</button>
                <div id="debug-results"></div>
            </div>
        `;
        document.body.appendChild(panel);
    }

    logDeviceInfo() {
        if (window.deviceDetector) {
            console.group('🎬 Video Preview Debug Info');
            console.table(window.deviceDetector.getCapabilities());
            console.log('Full Debug:', window.deviceDetector.getDebugInfo());
            console.groupEnd();
        }
    }

    async runTests() {
        console.log('🧪 Running video preview tests...');
        
        const tests = [
            this.testVideoElementCreation,
            this.testVideoLoading,
            this.testVideoPlayback,
            this.testDeviceCapabilities,
            this.testNetworkConditions
        ];

        for (const test of tests) {
            try {
                await test.call(this);
            } catch (error) {
                console.error(`Test failed: ${test.name}`, error);
            }
        }

        this.displayResults();
    }

    async testVideoElementCreation() {
        const video = document.createElement('video');
        this.testResults.videoCreation = {
            success: !!video,
            canPlayType: typeof video.canPlayType === 'function',
            supportsPreload: 'preload' in video
        };
    }

    async testVideoLoading() {
        // Test with a small sample video
        const video = document.createElement('video');
        video.muted = true;
        video.preload = 'metadata';
        
        return new Promise((resolve) => {
            const timeout = setTimeout(() => {
                this.testResults.videoLoading = { success: false, error: 'timeout' };
                resolve();
            }, 5000);

            video.addEventListener('loadedmetadata', () => {
                clearTimeout(timeout);
                this.testResults.videoLoading = { 
                    success: true, 
                    duration: video.duration,
                    readyState: video.readyState
                };
                resolve();
            });

            video.addEventListener('error', (e) => {
                clearTimeout(timeout);
                this.testResults.videoLoading = { 
                    success: false, 
                    error: e.message || 'load error'
                };
                resolve();
            });

            // Use first available video from the page
            const firstVideo = document.querySelector('.video-preview video');
            if (firstVideo && firstVideo.src) {
                video.src = firstVideo.src;
            }
        });
    }

    displayResults() {
        const resultsDiv = document.getElementById('debug-results');
        if (resultsDiv) {
            resultsDiv.innerHTML = '<pre>' + JSON.stringify(this.testResults, null, 2) + '</pre>';
        }
        console.log('🧪 Test Results:', this.testResults);
    }
}

// Initialize debugger
window.videoDebugger = new VideoPreviewDebugger();