/* Enhanced Video Preview System
 * Plays short previews on hover/focus/touch, seeking to a specified range.
 */

class VideoPreviewManager {
    constructor(opts = {}) {
        this.previewTimeout = opts.previewTimeout || 250;
        this.loadTimeout = opts.loadTimeout || 3000;
        this.previewStartSec = opts.previewStartSec || 120;
        this.previewEndSec = opts.previewEndSec || 215;
        this.maxConcurrentPreviews = opts.maxConcurrentPreviews || 2;
        this.activePreviewsCount = 0;

        this.deviceCapabilities = this.detectDeviceCapabilities();
        this.init();
    }

    detectDeviceCapabilities() {
        const ua = (navigator.userAgent || '').toLowerCase();
        const isMobile = /android|iphone|ipad|ipod|mobile/i.test(ua);
        const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        const hasHover = window.matchMedia && window.matchMedia('(hover: hover)').matches;
        const isVR = /oculus|quest|vr|vive|index/i.test(ua) || ('xr' in navigator);

        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        const isSlowConnection = connection && (connection.effectiveType === '2g' || connection.saveData === true);
        const memoryGB = navigator.deviceMemory || 4;
        const isLowMemory = memoryGB < 4;

        const shouldUsePreview = !isLowMemory && !isSlowConnection && (hasHover || isVR) && !isMobile;

        return {
            isMobile,
            hasTouch,
            hasHover,
            isVR,
            isLowMemory,
            isSlowConnection,
            shouldUsePreview,
            previewStrategy: isVR ? 'vr-touch' : (hasHover ? 'hover' : (hasTouch ? 'touch' : 'disabled'))
        };
    }

    init() {
        if (!this.deviceCapabilities.shouldUsePreview) { this.addFallbackIndicators(); return; }
        this.setupPreviewContainers();
        this.addPerformanceMonitoring();
    }

    setupPreviewContainers() { document.querySelectorAll('.video-preview-container').forEach(c => this.enhanceContainer(c)); }

    enhanceContainer(container) {
        const strategy = this.deviceCapabilities.previewStrategy;
        if (strategy === 'hover') this.setupHoverPreview(container);
        else if (strategy === 'vr-touch') this.setupVRPreview(container);
        else if (strategy === 'touch') this.setupTouchPreview(container);
        else this.setupFallback(container);
    }

    setupHoverPreview(container) {
        let hoverTimer = null, loadTimer = null, video = null, hasLoaded = false, isPlaying = false;

        const start = (trigger) => {
            if (this.activePreviewsCount >= this.maxConcurrentPreviews) return;
            clearTimeout(hoverTimer);
            hoverTimer = setTimeout(() => {
                if (trigger === 'hover' && !container.matches(':hover')) return;
                const preview = container.querySelector('.video-preview');
                video = preview && preview.querySelector('video');
                if (!video) return;
                this.activePreviewsCount++;
                this.showLoadingIndicator(container);
                loadTimer = setTimeout(() => this.handleLoadTimeout(container, video), this.loadTimeout);

                const play = () => { clearTimeout(loadTimer); this.hideLoadingIndicator(container); this.playPreview(video, container, () => { isPlaying = false; this.activePreviewsCount = Math.max(0, this.activePreviewsCount - 1); }); isPlaying = true; };

                if (!hasLoaded) { video.addEventListener('loadedmetadata', () => { hasLoaded = true; play(); }, { once: true }); video.addEventListener('error', () => this.handleVideoError(container, video), { once: true }); try { video.load(); } catch (e) {} }
                else play();
            }, this.previewTimeout);
        };

        const stop = () => { clearTimeout(hoverTimer); clearTimeout(loadTimer); if (video && isPlaying) { try { video.pause(); } catch (e) {} try { if (video.duration && video.duration >= this.previewStartSec) video.currentTime = Math.min(this.previewStartSec, video.duration); else video.currentTime = 0; } catch (e) {} isPlaying = false; this.activePreviewsCount = Math.max(0, this.activePreviewsCount - 1); } this.hideLoadingIndicator(container); };

        container.addEventListener('mouseenter', () => start('hover'));
        container.addEventListener('mouseleave', stop);
        container.addEventListener('focusin', () => start('focus'));
        container.addEventListener('focusout', stop);
        container.addEventListener('touchstart', () => start('touch'), { passive: true });
        container.addEventListener('touchend', stop, { passive: true });
        container.addEventListener('click', stop);
    }

    setupVRPreview(container) { this.addPreviewButton(container); }
    setupTouchPreview(container) { this.addPreviewButton(container); }
    setupFallback(container) { this.addStaticPreviewIndicator(container); }

    async startVRPreview(container) {
        const preview = container.querySelector('.video-preview');
        const video = preview && preview.querySelector('video');
        if (!video) throw new Error('Video element not found');
        if (this.activePreviewsCount >= this.maxConcurrentPreviews) throw new Error('Too many previews');
        this.activePreviewsCount++; this.showLoadingIndicator(container);
        return new Promise((resolve, reject) => {
            const loadTimer = setTimeout(() => { this.handleLoadTimeout(container, video); reject(new Error('load timeout')); }, this.loadTimeout);
            video.addEventListener('loadedmetadata', () => { clearTimeout(loadTimer); this.hideLoadingIndicator(container); this.playPreview(video, container, () => { this.activePreviewsCount = Math.max(0, this.activePreviewsCount - 1); }); resolve(video); }, { once: true });
            video.addEventListener('error', () => { clearTimeout(loadTimer); this.handleVideoError(container, video); reject(new Error('video error')); }, { once: true });
            try { video.load(); } catch (e) { clearTimeout(loadTimer); reject(e); }
        });
    }

    stopVRPreview(video, container) { if (video) try { video.pause(); video.currentTime = 0; } catch (e) {} this.activePreviewsCount = Math.max(0, this.activePreviewsCount - 1); this.hideLoadingIndicator(container); }

    playPreview(video, container, onEnd = null) {
        if (!video) return;
        const duration = Number.isFinite(video.duration) ? video.duration : 0;
        let start = Math.min(this.previewStartSec, Math.max(0, duration || this.previewStartSec));
        let end = Math.min(this.previewEndSec, duration || this.previewEndSec);
        if (duration && end <= start) { end = duration; start = Math.max(0, duration - Math.min(10, duration)); }

        const onTimeUpdate = () => { if (!video) return; if (video.currentTime >= (end - 0.05)) { video.removeEventListener('timeupdate', onTimeUpdate); try { video.pause(); } catch (e) {} if (typeof onEnd === 'function') onEnd(); } };
        const safetyMs = Math.max(0, (end - start) * 1000) + 1500;
        const safetyTimer = setTimeout(() => { video.removeEventListener('timeupdate', onTimeUpdate); try { video.pause(); } catch (e) {} if (typeof onEnd === 'function') onEnd(); }, safetyMs);

        try { video.currentTime = start; } catch (e) {}
        video.play().then(() => { video.addEventListener('timeupdate', onTimeUpdate); }).catch((err) => { clearTimeout(safetyTimer); this.handleVideoError(container, video); if (typeof onEnd === 'function') onEnd(); });
    }

    showLoadingIndicator(container) { let indicator = container.querySelector('.preview-loading'); if (!indicator) { indicator = document.createElement('div'); indicator.className = 'preview-loading'; indicator.textContent = '⏳'; container.appendChild(indicator); } indicator.style.display = 'block'; }
    hideLoadingIndicator(container) { const indicator = container.querySelector('.preview-loading'); if (indicator) indicator.style.display = 'none'; }
    handleLoadTimeout(container, video) { this.activePreviewsCount = Math.max(0, this.activePreviewsCount - 1); this.hideLoadingIndicator(container); this.showErrorIndicator(container, 'Load timeout'); }
    handleVideoError(container, video) { this.activePreviewsCount = Math.max(0, this.activePreviewsCount - 1); this.hideLoadingIndicator(container); this.showErrorIndicator(container, 'Preview unavailable'); }
    showErrorIndicator(container, message) { let indicator = container.querySelector('.preview-error'); if (!indicator) { indicator = document.createElement('div'); indicator.className = 'preview-error'; container.appendChild(indicator); } indicator.textContent = message; indicator.style.display = 'block'; setTimeout(() => { if (indicator) indicator.style.display = 'none'; }, 2000); }

    addPreviewButton(container) { if (container.querySelector('.preview-btn')) return; const button = document.createElement('button'); button.className = 'preview-btn'; button.setAttribute('aria-label', 'Preview'); button.textContent = '▶'; button.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); this.startVRPreview(container).then((video) => { setTimeout(() => this.stopVRPreview(video, container), (this.previewEndSec - this.previewStartSec) * 1000); }).catch(() => {}); }); container.appendChild(button); }

    addStaticPreviewIndicator(container) { if (container.querySelector('.preview-disabled')) return; const indicator = document.createElement('div'); indicator.className = 'preview-disabled'; indicator.textContent = '📱'; indicator.title = 'Preview disabled on this device'; container.appendChild(indicator); }
    addFallbackIndicators() { const style = document.createElement('style'); style.textContent = `.preview-disabled { position:absolute; top:8px; left:8px; background:rgba(0,0,0,0.7); color:#fff; padding:4px 8px; border-radius:4px; font-size:12px; z-index:5; }`; document.head.appendChild(style); document.querySelectorAll('.video-preview-container').forEach(c => this.addStaticPreviewIndicator(c)); }
    addPerformanceMonitoring() { setInterval(() => { if (this.activePreviewsCount > 0) console.log(`🎬 Active previews: ${this.activePreviewsCount}/${this.maxConcurrentPreviews}`); }, 5000); }
    static init(opts) { return new VideoPreviewManager(opts); }
}

const enhancedStyles = document.createElement('style');
enhancedStyles.textContent = `
    .preview-loading{ position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); background:rgba(0,0,0,0.8); color:#fff; padding:8px 12px; border-radius:8px; z-index:15; display:none; }
    .preview-error{ position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); background:rgba(220,53,69,0.9); color:#fff; padding:6px 10px; border-radius:6px; z-index:15; display:none; }
    .preview-btn{ position:absolute; top:8px; right:8px; background:rgba(0,123,255,0.9); color:#fff; border:none; border-radius:50%; width:32px; height:32px; cursor:pointer; z-index:10; }
    @media(max-width:768px){ .video-preview{ display:none !important; } }
`;
document.head.appendChild(enhancedStyles);

window.VideoPreviewManager = VideoPreviewManager;

(function(){
    const supportsHover = window.matchMedia && window.matchMedia('(hover: hover)').matches;
    const getDelay = (el) => { const v = parseInt(el?.dataset?.previewDelay || '500', 10); return Number.isFinite(v) ? Math.max(0, v) : 500; };
    const bindCard = (card) => {
        let hoverTimer = null;
        if (supportsHover) { card.addEventListener('mouseenter', () => { hoverTimer = setTimeout(() => card.dispatchEvent(new CustomEvent('preview:start',{bubbles:true})), getDelay(card)); }); card.addEventListener('mouseleave', () => { if (hoverTimer) clearTimeout(hoverTimer); card.dispatchEvent(new CustomEvent('preview:stop',{bubbles:true})); }); return; }
        let touchActive = false;
        const onTap = (e) => { e.stopPropagation(); if (!touchActive) { touchActive = true; setTimeout(() => card.dispatchEvent(new CustomEvent('preview:start',{bubbles:true})), getDelay(card)); } else { touchActive = false; card.dispatchEvent(new CustomEvent('preview:stop',{bubbles:true})); } };
        card.addEventListener('touchstart', onTap, { passive:true }); card.addEventListener('click', onTap); document.addEventListener('touchstart', (e)=> { if (!card.contains(e.target)) { touchActive = false; card.dispatchEvent(new CustomEvent('preview:stop',{bubbles:true})); } }, { passive:true });
    };
    document.addEventListener('DOMContentLoaded', () => { document.querySelectorAll('[data-role="video-card"]').forEach(bindCard); });
})();

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => { window.videoPreviewManager = VideoPreviewManager.init(); });
else window.videoPreviewManager = VideoPreviewManager.init();