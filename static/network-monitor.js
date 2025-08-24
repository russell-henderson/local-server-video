/**
 * Network Monitor
 * Monitors network conditions for adaptive streaming
 */

class NetworkMonitor {
    constructor() {
        this.measurements = [];
        this.currentSpeed = 0;
        this.isMonitoring = false;
        this.measurementInterval = 10000; // 10 seconds
        this.maxMeasurements = 10;
        this.testImageSize = 100000; // 100KB test image
        this.failureCount = 0;
        this.maxFailures = 3; // Stop trying after 3 consecutive failures
        
        this.connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    }

    start() {
        if (this.isMonitoring) return;
        
        this.isMonitoring = true;
        this.initialMeasurement();
        this.startPeriodicMeasurements();
        
        console.log('📡 Network monitoring started');
    }

    stop() {
        this.isMonitoring = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        console.log('📡 Network monitoring stopped');
    }

    async initialMeasurement() {
        // Get initial speed estimate from Connection API if available
        if (this.connection && this.connection.downlink) {
            this.currentSpeed = this.connection.downlink * 1000000; // Convert Mbps to bps
            console.log(`📡 Initial speed from Connection API: ${this.formatSpeed(this.currentSpeed)}`);
        } else {
            // Set a reasonable default if no Connection API
            this.currentSpeed = 5000000; // 5 Mbps default
        }
        
        // Perform actual measurement with error handling
        try {
            const speed = await this.measureNetworkSpeed();
            this.addMeasurement(speed);
        } catch (error) {
            console.log('📡 Initial network measurement failed, using fallback:', error.message);
            // Use the current speed (from Connection API or default) as fallback
            this.addMeasurement(this.currentSpeed);
        }
    }

    startPeriodicMeasurements() {
        this.intervalId = setInterval(async () => {
            if (!this.isMonitoring) return;
            
            try {
                const speed = await this.measureNetworkSpeed();
                this.addMeasurement(speed);
                this.failureCount = 0; // Reset failure count on success
            } catch (error) {
                this.failureCount++;
                console.log(`📡 Network measurement failed (${this.failureCount}/${this.maxFailures}):`, error.message);
                
                if (this.failureCount >= this.maxFailures) {
                    console.log('📡 Too many measurement failures, switching to Connection API only');
                    this.measurementInterval = 30000; // Reduce frequency to every 30 seconds
                }
                
                // If measurement fails, use the current speed as a fallback
                if (this.currentSpeed > 0) {
                    this.addMeasurement(this.currentSpeed);
                }
            }
        }, this.measurementInterval);
    }

    async measureNetworkSpeed() {
        // Try multiple measurement methods for better reliability
        try {
            // Method 1: Use Connection API if available and reliable
            if (this.connection && this.connection.downlink && this.connection.downlink > 0) {
                const connectionSpeed = this.connection.downlink * 1000000; // Convert Mbps to bps
                console.log(`📡 Using Connection API speed: ${this.formatSpeed(connectionSpeed)}`);
                return connectionSpeed;
            }
            
            // Method 2: Try image-based measurement with local resources
            return await this.measureWithImage();
        } catch (imageError) {
            console.log('📡 Image measurement failed, using fallback methods');
            
            // Method 3: Use fetch-based measurement
            try {
                return await this.measureWithFetch();
            } catch (fetchError) {
                // Method 4: Estimate based on device and connection type
                return this.estimateSpeed();
            }
        }
    }

    async measureWithImage() {
        return new Promise((resolve, reject) => {
            const startTime = performance.now();
            const testImage = new Image();
            
            // Add random parameter to prevent caching
            const testUrl = this.generateTestUrl();
            
            testImage.onload = () => {
                const endTime = performance.now();
                const duration = (endTime - startTime) / 1000; // Convert to seconds
                const speed = (this.testImageSize * 8) / duration; // bits per second
                
                resolve(speed);
            };
            
            testImage.onerror = () => {
                reject(new Error('Failed to load test image'));
            };
            
            // Timeout after 10 seconds for faster fallback
            setTimeout(() => {
                reject(new Error('Network measurement timeout'));
            }, 10000);
            
            testImage.src = testUrl;
        });
    }

    async measureWithFetch() {
        const startTime = performance.now();
        const testUrl = this.generateTestUrl();
        
        try {
            const response = await fetch(testUrl, {
                method: 'HEAD', // Just get headers, not the full content
                cache: 'no-cache'
            });
            
            const endTime = performance.now();
            const duration = (endTime - startTime) / 1000;
            
            // Estimate speed based on response time (rough approximation)
            const estimatedSize = 50000; // Assume 50KB for HEAD request overhead
            const speed = (estimatedSize * 8) / duration;
            
            return speed;
        } catch (error) {
            throw new Error('Fetch measurement failed');
        }
    }

    estimateSpeed() {
        // Fallback estimation based on connection type and device
        if (this.connection) {
            const connectionTypeMap = {
                'slow-2g': 250000,    // 0.25 Mbps
                '2g': 500000,         // 0.5 Mbps
                '3g': 2000000,        // 2 Mbps
                '4g': 10000000,       // 10 Mbps
                '5g': 50000000        // 50 Mbps
            };
            
            const estimatedSpeed = connectionTypeMap[this.connection.effectiveType] || 5000000; // Default 5 Mbps
            console.log(`📡 Estimated speed based on ${this.connection.effectiveType}: ${this.formatSpeed(estimatedSpeed)}`);
            return estimatedSpeed;
        }
        
        // Ultimate fallback - assume moderate broadband
        console.log('📡 Using default speed estimate: 5 Mbps');
        return 5000000; // 5 Mbps
    }

    generateTestUrl() {
        // Use a local resource for network testing instead of external services
        const timestamp = Date.now();
        const random = Math.random().toString(36).substring(7);
        
        // Try to use a local video thumbnail or fallback to a data URL
        const thumbnails = document.querySelectorAll('img[src*="thumbnails"]');
        if (thumbnails.length > 0) {
            const thumbnail = thumbnails[Math.floor(Math.random() * thumbnails.length)];
            return `${thumbnail.src}?t=${timestamp}&r=${random}`;
        }
        
        // Fallback to testing with the current page's favicon or a small data URL
        return `${window.location.origin}/favicon.ico?t=${timestamp}&r=${random}`;
    }

    addMeasurement(speed) {
        const measurement = {
            speed,
            timestamp: Date.now(),
            connectionType: this.connection ? this.connection.effectiveType : 'unknown'
        };
        
        this.measurements.push(measurement);
        
        // Keep only recent measurements
        if (this.measurements.length > this.maxMeasurements) {
            this.measurements = this.measurements.slice(-this.maxMeasurements);
        }
        
        // Update current speed with weighted average
        this.updateCurrentSpeed();
        
        console.log(`📡 Network speed: ${this.formatSpeed(speed)} (avg: ${this.formatSpeed(this.currentSpeed)})`);
    }

    updateCurrentSpeed() {
        if (this.measurements.length === 0) return;
        
        // Calculate weighted average (recent measurements have more weight)
        let totalWeight = 0;
        let weightedSum = 0;
        
        this.measurements.forEach((measurement, index) => {
            const weight = index + 1; // More recent = higher weight
            totalWeight += weight;
            weightedSum += measurement.speed * weight;
        });
        
        this.currentSpeed = weightedSum / totalWeight;
        
        // Apply Connection API data if available and reasonable
        if (this.connection && this.connection.downlink) {
            const connectionSpeed = this.connection.downlink * 1000000;
            
            // Use Connection API speed if it's within reasonable range of measured speed
            if (Math.abs(connectionSpeed - this.currentSpeed) / this.currentSpeed < 0.5) {
                this.currentSpeed = (this.currentSpeed + connectionSpeed) / 2;
            }
        }
    }

    getCurrentSpeed() {
        return this.currentSpeed;
    }

    getAverageSpeed(timeWindow = 60000) { // Default: last 60 seconds
        const cutoffTime = Date.now() - timeWindow;
        const recentMeasurements = this.measurements.filter(m => m.timestamp > cutoffTime);
        
        if (recentMeasurements.length === 0) return this.currentSpeed;
        
        const sum = recentMeasurements.reduce((total, m) => total + m.speed, 0);
        return sum / recentMeasurements.length;
    }

    getSpeedTrend() {
        if (this.measurements.length < 3) return 'stable';
        
        const recent = this.measurements.slice(-3);
        const speeds = recent.map(m => m.speed);
        
        const isIncreasing = speeds[2] > speeds[1] && speeds[1] > speeds[0];
        const isDecreasing = speeds[2] < speeds[1] && speeds[1] < speeds[0];
        
        if (isIncreasing) return 'improving';
        if (isDecreasing) return 'degrading';
        return 'stable';
    }

    getConnectionQuality() {
        const speed = this.currentSpeed;
        
        if (speed >= 25000000) return 'excellent'; // 25+ Mbps
        if (speed >= 10000000) return 'good';      // 10+ Mbps
        if (speed >= 5000000) return 'fair';       // 5+ Mbps
        if (speed >= 1000000) return 'poor';       // 1+ Mbps
        return 'very-poor';                        // < 1 Mbps
    }

    getStats() {
        return {
            currentSpeed: this.currentSpeed,
            averageSpeed: this.getAverageSpeed(),
            trend: this.getSpeedTrend(),
            quality: this.getConnectionQuality(),
            measurementCount: this.measurements.length,
            connectionType: this.connection ? this.connection.effectiveType : 'unknown',
            saveData: this.connection ? this.connection.saveData : false,
            measurements: [...this.measurements]
        };
    }

    formatSpeed(bps) {
        if (bps >= 1000000) {
            return `${(bps / 1000000).toFixed(1)} Mbps`;
        } else if (bps >= 1000) {
            return `${(bps / 1000).toFixed(0)} Kbps`;
        }
        return `${Math.round(bps)} bps`;
    }

    // Event-based network change detection
    onNetworkChange(callback) {
        if (this.connection) {
            this.connection.addEventListener('change', () => {
                callback(this.getStats());
            });
        }
        
        // Also listen for online/offline events
        window.addEventListener('online', () => {
            callback(this.getStats());
        });
        
        window.addEventListener('offline', () => {
            callback({ ...this.getStats(), offline: true });
        });
    }

    // Bandwidth estimation for specific content types
    estimateBandwidthForQuality(quality) {
        const qualityBandwidthMap = {
            '240p': 500000,    // 0.5 Mbps
            '360p': 1000000,   // 1 Mbps
            '480p': 2500000,   // 2.5 Mbps
            '720p': 5000000,   // 5 Mbps
            '1080p': 8000000,  // 8 Mbps
            '1440p': 16000000, // 16 Mbps
            '2160p': 25000000  // 25 Mbps
        };
        
        return qualityBandwidthMap[quality] || 1000000;
    }

    canSupportQuality(quality) {
        const requiredBandwidth = this.estimateBandwidthForQuality(quality);
        const availableBandwidth = this.currentSpeed * 0.8; // 80% safety margin
        
        return availableBandwidth >= requiredBandwidth;
    }

    getRecommendedQuality() {
        const qualities = ['2160p', '1440p', '1080p', '720p', '480p', '360p', '240p'];
        
        for (const quality of qualities) {
            if (this.canSupportQuality(quality)) {
                return quality;
            }
        }
        
        return '240p'; // Fallback
    }
}

// Export for global use
window.NetworkMonitor = NetworkMonitor;