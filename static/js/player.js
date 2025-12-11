/**
 * static/js/player.js
 * Shared video player controller with ±10s skip, keyboard shortcuts, and position saving
 */

const detectInputMode = () => {
  const isTouch = matchMedia('(pointer: coarse)').matches;
  const hasHover = matchMedia('(hover: hover)').matches;
  const isQuest = /OculusBrowser|Quest|Oculus/i.test(navigator.userAgent);

  if (isQuest) return 'vr';
  if (isTouch && !hasHover) return 'touch-no-hover';
  if (isTouch) return 'touch';
  return 'pointer';
};

class VideoPlayer {
  constructor(root) {
    this.root = root;
    this.video = root.querySelector('video');
    this.controls = root.querySelector('[data-controls]');
    this.filename = this.video.dataset.filename;
    
    // Bind UI elements
    this.playBtn = root.querySelector('[data-action="play"]');
    this.backBtn = root.querySelector('[data-action="back10"]');
    this.fwdBtn = root.querySelector('[data-action="fwd10"]');
    this.muteBtn = root.querySelector('[data-action="mute"]');
    this.fullscreenBtn = root.querySelector('[data-action="fullscreen"]');
    this.speedDownBtn = root.querySelector('[data-action="speed-down"]');
    this.speedUpBtn = root.querySelector('[data-action="speed-up"]');
    this.loopBtn = root.querySelector('[data-action="loop"]');
    
    this.seekBar = root.querySelector('[data-role="seek"]');
    this.volumeBar = root.querySelector('[data-role="volume"]');
    
    this.currentTimeEl = root.querySelector('[data-current-time]');
    this.durationEl = root.querySelector('[data-duration]');
    this.previewEl = root.querySelector('[data-preview]');
    this.speedDisplay = root.querySelector('[data-speed-display]');

    this.playbackRate = 1.0;
    this.speedSteps = [0.75, 1.0, 1.25, 1.5, 2.0];
    this.loopStart = null;
    this.loopEnd = null;
    this.inputMode = detectInputMode();
    
    this.init();
  }
  
  init() {
    this.bindEvents();
    this.setupKeyboardShortcuts();
    this.loadSavedPosition();
    this.handleStartTime();
    this.configureForInputMode();
  }
  
  bindEvents() {
    // Video events
    this.video.addEventListener('loadedmetadata', () => this.updateDuration());
    this.video.addEventListener('timeupdate', () => this.updateProgress());
    this.video.addEventListener('ended', () => this.onVideoEnded());
    this.video.addEventListener('play', () => this.updatePlayButton());
    this.video.addEventListener('pause', () => this.updatePlayButton());
    this.video.addEventListener('volumechange', () => this.updateVolumeButton());
    
    // Control events
    this.playBtn.addEventListener('click', () => this.togglePlay());
    this.backBtn.addEventListener('click', () => this.skipBackward());
    this.fwdBtn.addEventListener('click', () => this.skipForward());
    this.muteBtn.addEventListener('click', () => this.toggleMute());
    this.fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
    if (this.speedDownBtn) this.speedDownBtn.addEventListener('click', () => this.adjustSpeed(-1));
    if (this.speedUpBtn) this.speedUpBtn.addEventListener('click', () => this.adjustSpeed(1));
    if (this.loopBtn) this.loopBtn.addEventListener('click', () => this.toggleLoop());
    
    this.seekBar.addEventListener('input', () => this.seek());
    this.seekBar.addEventListener('pointermove', (e) => this.updatePreviewFromEvent(e));
    this.seekBar.addEventListener('mousemove', (e) => this.updatePreviewFromEvent(e));
    this.seekBar.addEventListener('touchmove', (e) => this.updatePreviewFromEvent(e));
    this.volumeBar.addEventListener('input', () => this.setVolume());
    
    // Save position periodically
    this.video.addEventListener('timeupdate', () => this.savePosition());
  }
  
  setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Only handle shortcuts when the player is focused or no input is focused
      if (document.activeElement.tagName === 'INPUT' || 
          document.activeElement.tagName === 'TEXTAREA') {
        return;
      }
      
      switch (e.key.toLowerCase()) {
        case 'j':
          e.preventDefault();
          this.skipBackward();
          break;
        case 'l':
          e.preventDefault();
          this.skipForward();
          break;
        case 'k':
        case ' ':
          e.preventDefault();
          this.togglePlay();
          break;
        case 'f':
          e.preventDefault();
          this.toggleFullscreen();
          break;
        case 'b':
          e.preventDefault();
          this.toggleLoop();
          break;
        case '[':
          e.preventDefault();
          this.adjustSpeed(-1);
          break;
        case ']':
          e.preventDefault();
          this.adjustSpeed(1);
          break;
        case 'r':
          e.preventDefault();
          this.setSpeed(1.0);
          break;
        case 'm':
          e.preventDefault();
          this.toggleMute();
          break;
        case 'arrowup':
          e.preventDefault();
          this.adjustVolume(0.1);
          break;
        case 'arrowdown':
          e.preventDefault();
          this.adjustVolume(-0.1);
          break;
      }
    });
  }
  
  handleStartTime() {
    const urlParams = new URLSearchParams(window.location.search);
    const startTime = urlParams.get('t');
    
    if (startTime) {
      const seconds = parseInt(startTime, 10);
      if (!isNaN(seconds)) {
        this.video.addEventListener('loadedmetadata', () => {
          this.video.currentTime = seconds;
        }, { once: true });
      }
    }
  }
  
  loadSavedPosition() {
    if (!this.filename) return;
    
    const savedPosition = localStorage.getItem(`video-position-${this.filename}`);
    if (savedPosition) {
      const position = parseFloat(savedPosition);
      if (position > 5) { // Only resume if more than 5 seconds in
        this.video.addEventListener('loadedmetadata', () => {
          if (confirm(`Resume from ${this.formatTime(position)}?`)) {
            this.video.currentTime = position;
          }
        }, { once: true });
      }
    }
  }
  
  savePosition() {
    if (!this.filename || this.video.duration - this.video.currentTime < 30) {
      // Don't save if near end (less than 30 seconds remaining)
      return;
    }
    
    localStorage.setItem(`video-position-${this.filename}`, this.video.currentTime);
  }
  
  togglePlay() {
    if (this.video.paused) {
      this.video.play();
    } else {
      this.video.pause();
    }
  }
  
  skipBackward() {
    this.video.currentTime = Math.max(0, this.video.currentTime - 10);
  }
  
  skipForward() {
    this.video.currentTime = Math.min(this.video.duration, this.video.currentTime + 10);
  }
  
  toggleMute() {
    this.video.muted = !this.video.muted;
  }
  
  toggleFullscreen() {
    if (!document.fullscreenElement) {
      this.root.requestFullscreen().catch(err => {
        console.log('Error attempting to enable fullscreen:', err);
      });
    } else {
      document.exitFullscreen();
    }
  }
  
  seek() {
    const seekTime = (this.seekBar.value / 100) * this.video.duration;
    this.video.currentTime = seekTime;
  }
  
  setVolume() {
    this.video.volume = this.volumeBar.value;
    this.video.muted = this.video.volume === 0;
  }
  
  adjustVolume(delta) {
    const newVolume = Math.max(0, Math.min(1, this.video.volume + delta));
    this.video.volume = newVolume;
    this.volumeBar.value = newVolume;
    this.video.muted = newVolume === 0;
  }
  
  updatePlayButton() {
    this.playBtn.textContent = this.video.paused ? '▶️' : '⏸️';
    this.playBtn.setAttribute('aria-label', this.video.paused ? 'Play' : 'Pause');
  }
  
  updateVolumeButton() {
    if (this.video.muted || this.video.volume === 0) {
      this.muteBtn.textContent = '🔇';
    } else if (this.video.volume < 0.5) {
      this.muteBtn.textContent = '🔉';
    } else {
      this.muteBtn.textContent = '🔊';
    }
  }
  
  updateProgress() {
    const progress = (this.video.currentTime / this.video.duration) * 100;
    this.seekBar.value = progress || 0;
    
    this.currentTimeEl.textContent = this.formatTime(this.video.currentTime);
    this.updatePreviewDisplay(this.video.currentTime);
    this.enforceLoopWindow();
  }
  
  updateDuration() {
    this.durationEl.textContent = this.formatTime(this.video.duration);
    this.seekBar.max = 100;
    this.setSpeed(this.playbackRate);
  }
  
  formatTime(seconds) {
    if (isNaN(seconds)) return '0:00';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
      return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
  }
  
  onVideoEnded() {
    // Clear saved position when video ends
    if (this.filename) {
      localStorage.removeItem(`video-position-${this.filename}`);
    }
  }

  setSpeed(rate) {
    const closest = this.speedSteps.reduce((prev, curr) =>
      Math.abs(curr - rate) < Math.abs(prev - rate) ? curr : prev
    );
    this.playbackRate = closest;
    this.video.playbackRate = closest;
    if (this.speedDisplay) {
      const label = `${closest.toFixed(2).replace(/0+$/, '').replace(/\.$/, '')}x`;
      this.speedDisplay.textContent = label;
    }
  }

  adjustSpeed(direction) {
    const idx = this.speedSteps.findIndex(s => s === this.playbackRate);
    let newIdx = idx === -1 ? 1 : idx + direction;
    newIdx = Math.max(0, Math.min(this.speedSteps.length - 1, newIdx));
    this.setSpeed(this.speedSteps[newIdx]);
  }

  toggleLoop() {
    // Cycle through: set start -> set end -> clear
    if (this.loopStart === null) {
      this.loopStart = this.video.currentTime;
      this.loopEnd = null;
      this.video.loop = false;
      this.updateLoopButton('start');
      return;
    }

    if (this.loopEnd === null) {
      let end = this.video.currentTime;
      if (end <= this.loopStart + 0.5) {
        end = this.loopStart + 1;
      }
      const duration = this.video.duration || end;
      this.loopEnd = Math.min(duration, end);
      this.video.loop = false;
      this.updateLoopButton('ab');
      return;
    }

    // Clear loop
    this.loopStart = null;
    this.loopEnd = null;
    this.video.loop = false;
    this.updateLoopButton('off');
  }

  updatePreviewFromEvent(evt) {
    if (!this.previewEl || !this.video.duration) return;
    const rect = this.seekBar.getBoundingClientRect();
    const clientX = evt.clientX || (evt.touches && evt.touches[0] && evt.touches[0].clientX);
    if (!clientX && clientX !== 0) return;
    const percent = (clientX - rect.left) / rect.width;
    const clamped = Math.max(0, Math.min(1, percent));
    const time = clamped * this.video.duration;
    this.updatePreviewDisplay(time);
  }

  updatePreviewDisplay(seconds) {
    if (this.previewEl) {
      this.previewEl.textContent = `Seek: ${this.formatTime(seconds)}`;
    }
  }

  updateLoopButton(state) {
    if (!this.loopBtn) return;
    switch (state) {
      case 'start':
        this.loopBtn.textContent = 'Loop A…';
        this.loopBtn.title = 'Set loop end (B)';
        this.loopBtn.setAttribute('aria-pressed', 'true');
        this.loopBtn.classList.add('active');
        break;
      case 'ab':
        this.loopBtn.textContent = 'Loop A-B';
        this.loopBtn.title = 'Loop section (click to clear)';
        this.loopBtn.setAttribute('aria-pressed', 'true');
        this.loopBtn.classList.add('active');
        break;
      default:
        this.loopBtn.textContent = 'Loop';
        this.loopBtn.title = 'Toggle loop (B)';
        this.loopBtn.setAttribute('aria-pressed', 'false');
        this.loopBtn.classList.remove('active');
        break;
    }
  }

  enforceLoopWindow() {
    if (this.loopStart === null || this.loopEnd === null) return;
    const end = this.loopEnd;
    if (this.video.currentTime >= end - 0.05) {
      this.video.currentTime = this.loopStart;
    }
  }

  configureForInputMode() {
    // Quest or touch-without-hover: keep controls visible and avoid hover-only UX
    if (this.inputMode === 'vr' || this.inputMode === 'touch-no-hover') {
      this.root.classList.add('controls-visible', 'controls-persistent');
    }

    // Hide seek preview text in VR to reduce noise
    if (this.inputMode === 'vr' && this.previewEl) {
      this.previewEl.style.display = 'none';
    }
  }
}

// Auto-initialize players when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const players = document.querySelectorAll('[data-player]');
  players.forEach(player => new VideoPlayer(player));
});

// Export for manual initialization
window.VideoPlayer = VideoPlayer;
