/**
 * Comprehensive Device Detection Utility
 * Provides accurate detection for mobile, VR, and other device capabilities
 */

class DeviceDetector {
    constructor() {
        this.userAgent = navigator.userAgent.toLowerCase();
        this.capabilities = this.detectCapabilities();
    }

    detectCapabilities() {
        return {
            // Basic device types
            isMobile: this.detectMobile(),
            isTablet: this.detectTablet(),
            isDesktop: this.detectDesktop(),
            isVR: this.detectVR(),
            
            // Input capabilities
            hasTouch: this.detectTouch(),
            hasHover: this.detectHover(),
            hasPointer: this.detectPointer(),
            
            // Performance indicators
            memoryGB: this.detectMemory(),
            isLowMemory: this.detectLowMemory(),
            connectionType: this.detectConnection(),
            isSlowConnection: this.detectSlowConnection(),
            
            // Browser capabilities
            supportsWebGL: this.detectWebGL(),
            supportsWebXR: this.detectWebXR(),
            supportsVideoPreload: this.detectVideoPreload(),
            
            // Platform specifics
            platform: this.detectPlatform(),
            browser: this.detectBrowser(),
            
            // Computed recommendations
            shouldUseVideoPreview: false, // Will be set after all detection
            recommendedPreviewStrategy: 'disabled' // Will be set after all detection
        };
    }

    detectMobile() {
        // Comprehensive mobile detection
        const mobilePatterns = [
            /android/i,
            /iphone/i,
            /ipod/i,
            /blackberry/i,
            /iemobile/i,
            /opera mini/i,
            /mobile/i,
            /phone/i
        ];
        
        return mobilePatterns.some(pattern => pattern.test(this.userAgent)) ||
               (navigator.maxTouchPoints > 0 && window.screen.width < 768);
    }

    detectTablet() {
        // Tablet detection (including iPad)
        const tabletPatterns = [
            /ipad/i,
            /android(?!.*mobile)/i,
            /tablet/i
        ];
        
        return tabletPatterns.some(pattern => pattern.test(this.userAgent)) ||
               (navigator.maxTouchPoints > 0 && window.screen.width >= 768 && window.screen.width < 1024);
    }

    detectDesktop() {
        return !this.detectMobile() && !this.detectTablet() && !this.detectVR();
    }

    detectVR() {
        // Enhanced VR detection
        const vrPatterns = [
            /oculusbrowser/i,
            /quest/i,
            /oculus/i,
            /vr/i,
            /pico/i,
            /htc/i,
            /valve/i
        ];
        
        const hasVRAPI = 'xr' in navigator || 
                        'getVRDisplays' in navigator ||
                        'webkitGetVRDisplays' in navigator;
        
        const hasVRUserAgent = vrPatterns.some(pattern => pattern.test(this.userAgent));
        
        // Check for VR-specific screen dimensions (Quest 2: 1832x1920 per eye)
        const hasVRDimensions = (window.screen.width === 3664 && window.screen.height === 1920) ||
                               (window.screen.width === 1832 && window.screen.height === 1920);
        
        return hasVRAPI || hasVRUserAgent || hasVRDimensions;
    }

    detectTouch() {
        return 'ontouchstart' in window || 
               navigator.maxTouchPoints > 0 || 
               navigator.msMaxTouchPoints > 0;
    }

    detectHover() {
        // True hover capability (not just touch simulation)
        return window.matchMedia('(hover: hover)').matches && 
               window.matchMedia('(pointer: fine)').matches;
    }

    detectPointer() {
        if (window.matchMedia('(pointer: fine)').matches) return 'fine';
        if (window.matchMedia('(pointer: coarse)').matches) return 'coarse';
        return 'none';
    }

    detectMemory() {
        // Device memory in GB
        return navigator.deviceMemory || 4; // Default to 4GB if unknown
    }

    detectLowMemory() {
        const memory = this.detectMemory();
        const isMobile = this.detectMobile();
        
        // Consider mobile devices with <4GB or any device with <2GB as low memory
        return (isMobile && memory < 4) || memory < 2;
    }

    detectConnection() {
        const connection = navigator.connection || 
                          navigator.mozConnection || 
                          navigator.webkitConnection;
        
        if (!connection) return 'unknown';
        
        return {
            effectiveType: connection.effectiveType,
            downlink: connection.downlink,
            rtt: connection.rtt,
            saveData: connection.saveData
        };
    }

    detectSlowConnection() {
        const connection = this.detectConnection();
        
        if (connection === 'unknown') return false;
        
        return connection.effectiveType === 'slow-2g' || 
               connection.effectiveType === '2g' ||
               connection.saveData === true ||
               (connection.downlink && connection.downlink < 1.5);
    }

    detectWebGL() {
        try {
            const canvas = document.createElement('canvas');
            return !!(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'));
        } catch (e) {
            return false;
        }
    }

    detectWebXR() {
        return 'xr' in navigator;
    }

    detectVideoPreload() {
        // Test if video preload is supported and reliable
        const video = document.createElement('video');
        return 'preload' in video && 
               typeof video.canPlayType === 'function';
    }

    detectPlatform() {
        if (/windows/i.test(this.userAgent)) return 'windows';
        if (/macintosh|mac os x/i.test(this.userAgent)) return 'macos';
        if (/linux/i.test(this.userAgent)) return 'linux';
        if (/android/i.test(this.userAgent)) return 'android';
        if (/iphone|ipad|ipod/i.test(this.userAgent)) return 'ios';
        return 'unknown';
    }

    detectBrowser() {
        if (/oculusbrowser/i.test(this.userAgent)) return 'oculus';
        if (/edg/i.test(this.userAgent)) return 'edge';
        if (/chrome/i.test(this.userAgent)) return 'chrome';
        if (/firefox/i.test(this.userAgent)) return 'firefox';
        if (/safari/i.test(this.userAgent)) return 'safari';
        return 'unknown';
    }

    // Compute final recommendations
    computeRecommendations() {
        const caps = this.capabilities;
        
        // Determine if video preview should be enabled
        caps.shouldUseVideoPreview = this.shouldEnableVideoPreview();
        
        // Determine preview strategy
        caps.recommendedPreviewStrategy = this.getRecommendedPreviewStrategy();
        
        return caps;
    }

    shouldEnableVideoPreview() {
        const caps = this.capabilities;
        
        // Disable for constrained devices
        if (caps.isLowMemory || caps.isSlowConnection) {
            return false;
        }
        
        // Disable for mobile browsers (too unreliable)
        if (caps.isMobile && !caps.isVR) {
            return false;
        }
        
        // Enable for desktop with proper hover
        if (caps.isDesktop && caps.hasHover) {
            return true;
        }
        
        // Enable for VR devices with special handling
        if (caps.isVR) {
            return true;
        }
        
        // Enable for tablets with good specs
        if (caps.isTablet && !caps.isLowMemory && !caps.isSlowConnection) {
            return true;
        }
        
        return false;
    }

    getRecommendedPreviewStrategy() {
        const caps = this.capabilities;
        
        if (!caps.shouldUseVideoPreview) {
            return 'disabled';
        }
        
        if (caps.isVR) {
            return 'vr-touch';
        }
        
        if (caps.hasHover && caps.isDesktop) {
            return 'hover';
        }
        
        if (caps.hasTouch && (caps.isTablet || caps.isMobile)) {
            return 'touch-button';
        }
        
        return 'click-to-preview';
    }

    // Public API
    getCapabilities() {
        return this.computeRecommendations();
    }

    isDevice(type) {
        const caps = this.getCapabilities();
        switch (type.toLowerCase()) {
            case 'mobile': return caps.isMobile;
            case 'tablet': return caps.isTablet;
            case 'desktop': return caps.isDesktop;
            case 'vr': return caps.isVR;
            default: return false;
        }
    }

    canUseFeature(feature) {
        const caps = this.getCapabilities();
        switch (feature.toLowerCase()) {
            case 'video-preview': return caps.shouldUseVideoPreview;
            case 'hover': return caps.hasHover;
            case 'touch': return caps.hasTouch;
            case 'webxr': return caps.supportsWebXR;
            case 'webgl': return caps.supportsWebGL;
            default: return false;
        }
    }

    getRecommendation(feature) {
        const caps = this.getCapabilities();
        switch (feature.toLowerCase()) {
            case 'video-preview': return caps.recommendedPreviewStrategy;
            case 'memory-usage': return caps.isLowMemory ? 'conservative' : 'normal';
            case 'connection': return caps.isSlowConnection ? 'optimized' : 'full';
            default: return 'unknown';
        }
    }

    // Debug information
    getDebugInfo() {
        return {
            userAgent: this.userAgent,
            capabilities: this.getCapabilities(),
            screen: {
                width: window.screen.width,
                height: window.screen.height,
                availWidth: window.screen.availWidth,
                availHeight: window.screen.availHeight
            },
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            mediaQueries: {
                hover: window.matchMedia('(hover: hover)').matches,
                pointer: window.matchMedia('(pointer: fine)').matches,
                touch: window.matchMedia('(pointer: coarse)').matches
            }
        };
    }

    // Static factory method
    static detect() {
        return new DeviceDetector().getCapabilities();
    }

    static create() {
        return new DeviceDetector();
    }
}

// Export for global use
window.DeviceDetector = DeviceDetector;

// Create global instance
window.deviceDetector = DeviceDetector.create();

// Log detection results in development
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    console.group('🔍 Device Detection Results');
    console.table(window.deviceDetector.getCapabilities());
    console.log('Debug Info:', window.deviceDetector.getDebugInfo());
    console.groupEnd();
}