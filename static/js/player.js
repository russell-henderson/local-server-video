/**
 * static/js/player.js
 * Shared video player controller with ±10s skip, keyboard shortcuts, and position saving
 */

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
    
    this.seekBar = root.querySelector('[data-role="seek"]');
    this.volumeBar = root.querySelector('[data-role="volume"]');
    
    this.currentTimeEl = root.querySelector('[data-current-time]');
    this.durationEl = root.querySelector('[data-duration]');
    
    this.init();
  }
  
  init() {
    this.bindEvents();
    this.setupKeyboardShortcuts();
    this.loadSavedPosition();
    this.handleStartTime();
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
    
    this.seekBar.addEventListener('input', () => this.seek());
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
  }
  
  updateDuration() {
    this.durationEl.textContent = this.formatTime(this.video.duration);
    this.seekBar.max = 100;
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
}

// Auto-initialize players when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const players = document.querySelectorAll('[data-player]');
  players.forEach(player => new VideoPlayer(player));
});

// Export for manual initialization
window.VideoPlayer = VideoPlayer;