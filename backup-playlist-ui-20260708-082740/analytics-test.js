/**
 * Video Analytics Testing Suite
 * Tools to test and debug the video analytics system
 */

class AnalyticsTest {
    constructor() {
        this.testResults = [];
        this.debugMode = false;
        this.init();
    }

    init() {
        // Analytics test panel UI removed
        console.log('🧪 Analytics Test Suite initialized (UI removed)');
    }

    // createTestPanel removed

    addTestStyles() {
        const styles = document.createElement('style');
        styles.textContent = `
            .analytics-test-panel {
                position: fixed;
                top: 20px;
                left: 20px;
                width: 320px;
                max-height: 80vh;
                background: white;
                border: 2px solid #007bff;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                z-index: 10000;
                font-family: monospace;
                font-size: 0.8rem;
                overflow: hidden;
            }

            .test-panel-header {
                background: #007bff;
                color: white;
                padding: 0.5rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .test-panel-header h6 {
                margin: 0;
                font-size: 0.9rem;
            }

            .test-panel-toggle {
                background: none;
                border: none;
                color: white;
                cursor: pointer;
                font-size: 1.2rem;
                padding: 0;
                width: 20px;
                height: 20px;
            }

            .test-panel-content {
                max-height: 70vh;
                overflow-y: auto;
                padding: 0.5rem;
            }

            .test-panel-content.collapsed {
                display: none;
            }

            .test-section {
                margin-bottom: 1rem;
                padding-bottom: 0.5rem;
                border-bottom: 1px solid #eee;
            }

            .test-section h7 {
                font-weight: bold;
                font-size: 0.8rem;
                color: #333;
                display: block;
                margin-bottom: 0.5rem;
            }

            .test-buttons {
                display: flex;
                flex-wrap: wrap;
                gap: 0.25rem;
            }

            .test-btn {
                font-size: 0.7rem;
                padding: 0.25rem 0.5rem;
            }

            .analytics-status {
                background: #f8f9fa;
                padding: 0.5rem;
                border-radius: 4px;
                font-size: 0.7rem;
            }

            .status-item {
                display: flex;
                justify-content: space-between;
                margin-bottom: 0.25rem;
            }

            .status-label {
                font-weight: bold;
            }

            .status-value {
                color: #666;
            }

            .status-value.success {
                color: #28a745;
            }

            .status-value.error {
                color: #dc3545;
            }

            .status-value.warning {
                color: #ffc107;
            }

            .test-results {
                background: #f8f9fa;
                padding: 0.5rem;
                border-radius: 4px;
                font-size: 0.7rem;
                max-height: 150px;
                overflow-y: auto;
            }

            .test-result {
                margin-bottom: 0.25rem;
                padding: 0.25rem;
                border-radius: 3px;
            }

            .test-result.success {
                background: #d4edda;
                color: #155724;
            }

            .test-result.error {
                background: #f8d7da;
                color: #721c24;
            }

            .test-result.info {
                background: #d1ecf1;
                color: #0c5460;
            }

            /* Dark mode support */
            .dark-mode .analytics-test-panel {
                background: #2d3748;
                color: white;
                border-color: #4299e1;
            }

            .dark-mode .analytics-status,
            .dark-mode .test-results {
                background: #1a202c;
            }

            .dark-mode .test-section {
                border-bottom-color: #4a5568;
            }
        `;
        document.head.appendChild(styles);
    }

    addTestControls() {
        // Toggle panel
        const toggleBtn = document.querySelector('.test-panel-toggle');
        const content = document.querySelector('.test-panel-content');
        
        toggleBtn.addEventListener('click', () => {
            content.classList.toggle('collapsed');
            toggleBtn.textContent = content.classList.contains('collapsed') ? '+' : '−';
        });

        // Keyboard shortcut to toggle panel
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'T') {
                e.preventDefault();
                const panel = document.getElementById('analytics-test-panel');
                panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
            }
        });

        // Auto-update status every 2 seconds
        setInterval(() => {
            this.updateStatus();
        }, 2000);
    }

    updateStatus() {
        // Check if analytics system is loaded
        const systemStatus = document.getElementById('system-status');
        if (window.videoAnalytics) {
            systemStatus.textContent = 'Loaded ✓';
            systemStatus.className = 'status-value success';
        } else {
            systemStatus.textContent = 'Not Loaded ✗';
            systemStatus.className = 'status-value error';
        }

        // Check current video
        const currentVideoStatus = document.getElementById('current-video-status');
        const video = document.querySelector('video');
        if (video && video.src) {
            const videoName = this.getVideoName(video.src);
            currentVideoStatus.textContent = videoName;
            currentVideoStatus.className = 'status-value success';
        } else {
            currentVideoStatus.textContent = 'None';
            currentVideoStatus.className = 'status-value';
        }

        // Check tracking status
        const trackingStatus = document.getElementById('tracking-status');
        if (window.videoAnalytics && window.videoAnalytics.trackingInterval) {
            trackingStatus.textContent = 'Yes ✓';
            trackingStatus.className = 'status-value success';
        } else {
            trackingStatus.textContent = 'No';
            trackingStatus.className = 'status-value';
        }
    }

    updateDebugStatus() {
        const debugStatus = document.getElementById('debug-status');
        debugStatus.textContent = this.debugMode ? 'On ✓' : 'Off';
        debugStatus.className = this.debugMode ? 'status-value success' : 'status-value';
        
        if (this.debugMode) {
            this.addResult('Debug mode enabled - verbose logging active', 'info');
        } else {
            this.addResult('Debug mode disabled', 'info');
        }
    }

    testBasicTracking() {
        this.addResult('Starting basic tracking test...', 'info');
        
        // Test 1: Check if analytics system exists
        if (!window.videoAnalytics) {
            this.addResult('❌ VideoAnalytics not found', 'error');
            return;
        }
        this.addResult('✅ VideoAnalytics system loaded', 'success');

        // Test 2: Check if video element exists
        const video = document.querySelector('video');
        if (!video) {
            this.addResult('❌ No video element found', 'error');
            return;
        }
        this.addResult('✅ Video element found', 'success');

        // Test 3: Check if video has analytics initialized
        if (!video.analyticsInitialized) {
            this.addResult('❌ Video analytics not initialized', 'error');
            return;
        }
        this.addResult('✅ Video analytics initialized', 'success');

        // Test 4: Check local storage
        try {
            const stored = localStorage.getItem('video_server_analytics');
            if (stored) {
                const data = JSON.parse(stored);
                this.addResult(`✅ Found analytics data for ${Object.keys(data).length} videos`, 'success');
            } else {
                this.addResult('ℹ️ No stored analytics data (this is normal for new videos)', 'info');
            }
        } catch (error) {
            this.addResult('❌ Error reading stored analytics', 'error');
        }

        this.addResult('Basic tracking test completed', 'info');
    }

    simulateViewing() {
        const video = document.querySelector('video');
        if (!video) {
            this.addResult('❌ No video found to simulate', 'error');
            return;
        }

        this.addResult('Starting viewing simulation...', 'info');

        // Simulate different viewing patterns
        const patterns = [
            { start: 0, end: 30, description: 'Watch first 30 seconds' },
            { start: 60, end: 90, description: 'Skip to 1 minute, watch 30 seconds' },
            { start: 120, end: 180, description: 'Skip to 2 minutes, watch 1 minute' },
            { start: 30, end: 60, description: 'Rewatch 30-60 seconds' }
        ];

        let patternIndex = 0;
        const simulatePattern = () => {
            if (patternIndex >= patterns.length) {
                this.addResult('✅ Viewing simulation completed', 'success');
                return;
            }

            const pattern = patterns[patternIndex];
            this.addResult(`Simulating: ${pattern.description}`, 'info');

            // Set video time and trigger events
            video.currentTime = pattern.start;
            video.dispatchEvent(new Event('seeking'));
            video.dispatchEvent(new Event('seeked'));

            setTimeout(() => {
                video.dispatchEvent(new Event('play'));
                
                // Simulate watching for the duration
                const watchDuration = (pattern.end - pattern.start) * 100; // 100ms per second for speed
                setTimeout(() => {
                    video.currentTime = pattern.end;
                    video.dispatchEvent(new Event('pause'));
                    
                    patternIndex++;
                    setTimeout(simulatePattern, 500);
                }, watchDuration);
            }, 100);
        };

        simulatePattern();
    }

    testTimeline() {
        const video = document.querySelector('video');
        if (!video) {
            this.addResult('❌ No video found for timeline test', 'error');
            return;
        }

        this.addResult('Testing timeline visualization...', 'info');

        // Check if overlay exists
        let overlay = video.parentNode?.querySelector('.video-analytics-overlay');
        if (!overlay) {
            this.addResult('⚠️ Analytics overlay not found, attempting to create...', 'info');
            
            // Try to force create overlay
            if (window.videoAnalytics && window.videoAnalytics.forceCreateOverlay) {
                const created = window.videoAnalytics.forceCreateOverlay();
                if (created) {
                    overlay = video.parentNode?.querySelector('.video-analytics-overlay');
                    this.addResult('✅ Analytics overlay created successfully', 'success');
                } else {
                    this.addResult('❌ Failed to create analytics overlay', 'error');
                    return;
                }
            } else {
                this.addResult('❌ Analytics system not available', 'error');
                return;
            }
        } else {
            this.addResult('✅ Analytics overlay found', 'success');
        }

        // Check if canvas exists
        const canvas = overlay.querySelector('.analytics-timeline-canvas');
        if (!canvas) {
            this.addResult('❌ Timeline canvas not found', 'error');
            return;
        }
        this.addResult('✅ Timeline canvas found', 'success');

        // Check canvas dimensions
        if (canvas.width > 0 && canvas.height > 0) {
            this.addResult(`✅ Canvas dimensions: ${canvas.width}x${canvas.height}`, 'success');
        } else {
            this.addResult('⚠️ Canvas has zero dimensions, attempting to initialize...', 'info');
            
            // Try to initialize canvas
            if (window.videoAnalytics) {
                window.videoAnalytics.initializeCanvas(video, overlay);
                if (canvas.width > 0 && canvas.height > 0) {
                    this.addResult(`✅ Canvas initialized: ${canvas.width}x${canvas.height}`, 'success');
                } else {
                    this.addResult('❌ Canvas initialization failed', 'error');
                }
            }
        }

        // Check stats display
        const stats = overlay.querySelector('.analytics-stats');
        if (stats) {
            this.addResult('✅ Stats display found', 'success');
        } else {
            this.addResult('❌ Stats display not found', 'error');
        }

        // Test visualization update
        if (window.videoAnalytics) {
            try {
                window.videoAnalytics.updateTimelineVisualization(video);
                this.addResult('✅ Timeline visualization updated', 'success');
            } catch (error) {
                this.addResult(`❌ Timeline visualization failed: ${error.message}`, 'error');
            }
        }

        this.addResult('Timeline test completed', 'info');
    }

    showStoredData() {
        try {
            const stored = localStorage.getItem('video_server_analytics');
            if (!stored) {
                this.addResult('No analytics data stored', 'info');
                return;
            }

            const data = JSON.parse(stored);
            const videoCount = Object.keys(data).length;
            
            this.addResult(`Found data for ${videoCount} videos:`, 'info');
            
            Object.keys(data).forEach(videoId => {
                const videoData = data[videoId];
                const completion = Math.round(videoData.completionPercentage || 0);
                const watchTime = Math.round((videoData.totalWatchTime || 0) / 60);
                this.addResult(`• ${videoId}: ${completion}% complete, ${watchTime}m watched`, 'info');
            });

            // Also log to console for detailed inspection
            console.log('📊 Analytics Data:', data);
            this.addResult('Full data logged to console', 'info');

        } catch (error) {
            this.addResult(`Error reading stored data: ${error.message}`, 'error');
        }
    }

    clearAnalytics() {
        if (confirm('Clear all analytics data? This cannot be undone.')) {
            try {
                localStorage.removeItem('video_server_analytics');
                if (window.videoAnalytics) {
                    window.videoAnalytics.watchData = {};
                }
                this.addResult('✅ Analytics data cleared', 'success');
            } catch (error) {
                this.addResult(`Error clearing data: ${error.message}`, 'error');
            }
        }
    }

    forceCreateOverlay() {
        if (window.videoAnalytics && window.videoAnalytics.forceCreateOverlay) {
            const success = window.videoAnalytics.forceCreateOverlay();
            if (success) {
                this.addResult('✅ Analytics overlay force-created', 'success');
            } else {
                this.addResult('❌ Failed to force-create overlay', 'error');
            }
        } else {
            this.addResult('❌ Analytics system not available', 'error');
        }
    }

    exportTestData() {
        try {
            const video = document.querySelector('video');
            const overlay = video?.parentNode?.querySelector('.video-analytics-overlay');
            
            const testData = {
                timestamp: new Date().toISOString(),
                testResults: this.testResults,
                analyticsData: JSON.parse(localStorage.getItem('video_server_analytics') || '{}'),
                systemInfo: {
                    userAgent: navigator.userAgent,
                    videoElements: document.querySelectorAll('video').length,
                    analyticsLoaded: !!window.videoAnalytics,
                    overlayExists: !!overlay,
                    videoSrc: video?.src || video?.currentSrc || 'none'
                }
            };

            const blob = new Blob([JSON.stringify(testData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `analytics-test-${Date.now()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.addResult('✅ Test data exported', 'success');
        } catch (error) {
            this.addResult(`Export failed: ${error.message}`, 'error');
        }
    }

    addResult(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const result = {
            timestamp,
            message,
            type
        };
        
        this.testResults.push(result);
        
        // Keep only last 20 results
        if (this.testResults.length > 20) {
            this.testResults = this.testResults.slice(-20);
        }

        // Update display
        const resultsDiv = document.getElementById('test-results');
        if (resultsDiv) {
            resultsDiv.innerHTML = this.testResults.map(r => 
                `<div class="test-result ${r.type}">[${r.timestamp}] ${r.message}</div>`
            ).join('');
            resultsDiv.scrollTop = resultsDiv.scrollHeight;
        }

        // Log to console if debug mode
        if (this.debugMode) {
            console.log(`[Analytics Test] ${message}`);
        }
    }

    getVideoName(src) {
        try {
            if (src.includes('/video/')) {
                return decodeURIComponent(src.split('/video/')[1]);
            }
            return src.split('/').pop() || 'Unknown';
        } catch {
            return 'Unknown';
        }
    }

    // Static initialization
    static init() {
        if (!window.analyticsTest) {
            window.analyticsTest = new AnalyticsTest();
        }
        return window.analyticsTest;
    }
}

// Auto-initialize after a delay to ensure other systems are loaded
// Auto-initialization of analytics test panel removed

// Export for manual use
window.AnalyticsTest = AnalyticsTest;