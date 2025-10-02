// subtitle-controls.js - Enhanced subtitle controls for video player
document.addEventListener('DOMContentLoaded', function() {
    const subtitleManager = {
        init() {
            this.videoElement = document.querySelector('video[data-filename]');
            this.filename = this.videoElement?.dataset.filename;
            this.subtitleOverlay = document.getElementById('subtitle-overlay');
            this.subtitles = [];
            this.subtitlesEnabled = false;
            this.setupEventHandlers();
            this.checkSubtitleStatus();
        },

        setupEventHandlers() {
            if (!this.videoElement || !this.filename) return;

            // Find existing buttons in the player controls
            const toggleBtn = document.querySelector('[data-action="subtitle-toggle"]');
            const generateBtn = document.querySelector('[data-action="subtitle-generate"]');

            if (toggleBtn) {
                toggleBtn.addEventListener('click', () => this.toggleSubtitles());
            }

            if (generateBtn) {
                generateBtn.addEventListener('click', () => this.generateSubtitles());
            }

            // Video timeupdate for subtitle synchronization
            this.videoElement.addEventListener('timeupdate', () => this.updateSubtitleDisplay());

            // Keyboard shortcut
            document.addEventListener('keydown', (e) => {
                if (e.target.tagName === 'INPUT') return;
                if (e.key === 'c' || e.key === 'C') {
                    e.preventDefault();
                    this.toggleSubtitles();
                }
            });
        },

        async checkSubtitleStatus() {
            if (!this.filename) return;

            try {
                const response = await fetch(`/api/subtitles/${encodeURIComponent(this.filename)}`);
                const data = await response.json();
                
                if (data.has_subtitles) {
                    await this.loadSubtitles();
                    this.updateSubtitleButton(true);
                } else {
                    this.showGenerateOption();
                }
            } catch (error) {
                console.warn('Could not check subtitle status:', error);
                this.showGenerateOption();
            }
        },

        async loadSubtitles() {
            if (!this.videoElement || !this.filename) return;

            // Get video filename without extension
            const baseName = this.filename.substring(0, this.filename.lastIndexOf('.'));
            
            try {
                // Try loading VTT file
                const vttSrc = `/video/${baseName}.vtt`;
                const response = await fetch(vttSrc);
                
                if (response.ok) {
                    const vttContent = await response.text();
                    this.parseVTT(vttContent);
                    return;
                }
            } catch (error) {
                console.warn('Could not load VTT subtitles:', error);
            }

            try {
                // Fallback to SRT file
                const srtSrc = `/video/${baseName}.srt`;
                const response = await fetch(srtSrc);
                
                if (response.ok) {
                    const srtContent = await response.text();
                    this.parseSRT(srtContent);
                    return;
                }
            } catch (error) {
                console.warn('Could not load SRT subtitles:', error);
            }
        },

        parseVTT(content) {
            this.subtitles = [];
            const lines = content.split('\n');
            let i = 0;

            // Skip WEBVTT header
            while (i < lines.length && !lines[i].includes('-->')) {
                i++;
            }

            while (i < lines.length) {
                const timeLine = lines[i];
                if (timeLine && timeLine.includes('-->')) {
                    const [startTime, endTime] = timeLine.split('-->').map(t => t.trim());
                    
                    i++;
                    let text = '';
                    while (i < lines.length && lines[i].trim() !== '') {
                        if (text) text += ' ';
                        text += lines[i].trim();
                        i++;
                    }

                    if (text) {
                        this.subtitles.push({
                            start: this.parseTimeVTT(startTime),
                            end: this.parseTimeVTT(endTime),
                            text: text
                        });
                    }
                }
                i++;
            }
        },

        parseSRT(content) {
            this.subtitles = [];
            const blocks = content.split('\n\n');

            for (const block of blocks) {
                const lines = block.trim().split('\n');
                if (lines.length >= 3) {
                    const timeLine = lines[1];
                    if (timeLine && timeLine.includes('-->')) {
                        const [startTime, endTime] = timeLine.split('-->').map(t => t.trim());
                        const text = lines.slice(2).join(' ').trim();

                        if (text) {
                            this.subtitles.push({
                                start: this.parseTimeSRT(startTime),
                                end: this.parseTimeSRT(endTime),
                                text: text
                            });
                        }
                    }
                }
            }
        },

        parseTimeVTT(timeStr) {
            const parts = timeStr.split(':');
            const hours = parseInt(parts[0]) || 0;
            const minutes = parseInt(parts[1]) || 0;
            const secondsParts = parts[2].split('.');
            const seconds = parseInt(secondsParts[0]) || 0;
            const milliseconds = parseInt(secondsParts[1]) || 0;
            return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000;
        },

        parseTimeSRT(timeStr) {
            const parts = timeStr.split(':');
            const hours = parseInt(parts[0]) || 0;
            const minutes = parseInt(parts[1]) || 0;
            const secondsParts = parts[2].split(',');
            const seconds = parseInt(secondsParts[0]) || 0;
            const milliseconds = parseInt(secondsParts[1]) || 0;
            return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000;
        },

        updateSubtitleDisplay() {
            if (!this.subtitlesEnabled || !this.subtitles.length || !this.subtitleOverlay) {
                return;
            }

            const currentTime = this.videoElement.currentTime;
            let currentSubtitle = null;

            for (const subtitle of this.subtitles) {
                if (currentTime >= subtitle.start && currentTime <= subtitle.end) {
                    currentSubtitle = subtitle;
                    break;
                }
            }

            if (currentSubtitle) {
                this.subtitleOverlay.textContent = currentSubtitle.text;
                this.subtitleOverlay.classList.add('visible');
            } else {
                this.subtitleOverlay.classList.remove('visible');
            }
        },

        toggleSubtitles() {
            this.subtitlesEnabled = !this.subtitlesEnabled;
            this.updateSubtitleButton(this.subtitlesEnabled);
            
            if (!this.subtitlesEnabled) {
                this.subtitleOverlay.classList.remove('visible');
            }
        },

        updateSubtitleButton(available) {
            const toggleBtn = document.querySelector('[data-action="subtitle-toggle"]');
            const generateBtn = document.querySelector('[data-action="subtitle-generate"]');
            
            if (toggleBtn) {
                if (available) {
                    toggleBtn.style.display = 'block';
                    toggleBtn.classList.toggle('active', this.subtitlesEnabled);
                } else {
                    toggleBtn.style.display = 'none';
                }
            }

            if (generateBtn) {
                generateBtn.style.display = available ? 'none' : 'block';
            }
        },

        showGenerateOption() {
            this.updateSubtitleButton(false);
        },

        async generateSubtitles() {
            if (!this.filename) return;

            const generateBtn = document.querySelector('[data-action="subtitle-generate"]');
            if (!generateBtn) return;

            // Show loading state
            generateBtn.classList.add('loading');
            generateBtn.disabled = true;

            try {
                const response = await fetch(`/api/subtitles/${encodeURIComponent(this.filename)}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(`HTTP ${response.status}: ${errorData.error || 'Unknown error'}`);
                }

                const data = await response.json();
                console.log('Subtitles generated:', data);

                // Reload subtitles and update UI
                await this.loadSubtitles();
                this.updateSubtitleButton(true);

            } catch (error) {
                console.error('Error generating subtitles:', error);
                alert(`Failed to generate subtitles: ${error.message}`);
            } finally {
                // Reset loading state
                generateBtn.classList.remove('loading');
                generateBtn.disabled = false;
            }
        }
    };

    // Initialize the subtitle manager
    subtitleManager.init();
});