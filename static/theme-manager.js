/**
 * Theme Manager for Local Video Server
 * Handles switching between glassmorphic, neomorphic, and hybrid themes
 */

class ThemeManager {
    constructor() {
        this.themes = {
            default: 'Default Theme',
            glassmorphic: 'Glassmorphic',
            neomorphic: 'Neomorphic', 
            hybrid: 'Hybrid Glass + Neo'
        };
        
        this.currentTheme = this.getStoredTheme() || 'default';
        this.darkMode = this.getStoredDarkMode();
        
        this.init();
    }

    init() {
        this.createThemeControls();
        this.applyTheme(this.currentTheme);
        this.applyDarkMode(this.darkMode);
        this.bindEvents();
        
        console.log('🎨 Theme Manager initialized');
        console.log(`Current theme: ${this.themes[this.currentTheme]}`);
        console.log(`Dark mode: ${this.darkMode ? 'enabled' : 'disabled'}`);
    }

    createThemeControls() {
        // Check if there's already a dark mode toggle in the navbar
        const existingDarkToggle = document.getElementById('toggle-dark-mode');
        
        // Create theme switcher container (without dark mode toggle)
        const themeSwitcher = document.createElement('div');
        themeSwitcher.className = 'theme-switcher';
        themeSwitcher.innerHTML = `
            <div class="theme-toggle">
                <button class="theme-option" data-theme="default" title="Default Theme">
                    <i class="fas fa-palette"></i>
                </button>
                <button class="theme-option" data-theme="glassmorphic" title="Glassmorphic Theme">
                    <i class="fas fa-gem"></i>
                </button>
                <button class="theme-option" data-theme="neomorphic" title="Neomorphic Theme">
                    <i class="fas fa-cube"></i>
                </button>
                <button class="theme-option" data-theme="hybrid" title="Hybrid Theme">
                    <i class="fas fa-layer-group"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(themeSwitcher);
        
        // If there's an existing dark mode toggle, integrate with it
        if (existingDarkToggle) {
            this.integrateWithExistingDarkMode(existingDarkToggle);
        }
        
        // Update active theme button
        this.updateActiveTheme();
    }

    bindEvents() {
        // Theme switching
        document.querySelectorAll('.theme-option[data-theme]').forEach(button => {
            button.addEventListener('click', (e) => {
                const theme = e.currentTarget.dataset.theme;
                this.switchTheme(theme);
            });
        });

        // Dark mode toggle (only if we created our own)
        const darkToggle = document.querySelector('.dark-toggle');
        if (darkToggle) {
            darkToggle.addEventListener('click', () => {
                this.toggleDarkMode();
            });
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case '1':
                        e.preventDefault();
                        this.switchTheme('default');
                        break;
                    case '2':
                        e.preventDefault();
                        this.switchTheme('glassmorphic');
                        break;
                    case '3':
                        e.preventDefault();
                        this.switchTheme('neomorphic');
                        break;
                    case '4':
                        e.preventDefault();
                        this.switchTheme('hybrid');
                        break;
                    case 'd':
                        e.preventDefault();
                        this.toggleDarkMode();
                        break;
                }
            }
        });
    }

    switchTheme(themeName) {
        if (this.themes[themeName]) {
            this.currentTheme = themeName;
            this.applyTheme(themeName);
            this.storeTheme(themeName);
            this.updateActiveTheme();
            this.showThemeNotification(this.themes[themeName]);
            
            console.log(`🎨 Switched to ${this.themes[themeName]}`);
        }
    }

    applyTheme(themeName) {
        // Remove existing theme classes
        document.body.classList.remove('glassmorphic-theme', 'neomorphic-theme', 'hybrid-theme');
        
        // Remove existing theme stylesheets
        this.removeThemeStylesheets();
        
        // Apply new theme
        switch(themeName) {
            case 'glassmorphic':
                document.body.classList.add('glassmorphic-theme');
                this.loadStylesheet('glassmorphic-theme.css');
                this.applyGlassmorphicClasses();
                break;
                
            case 'neomorphic':
                document.body.classList.add('neomorphic-theme');
                this.loadStylesheet('neomorphic-theme.css');
                this.applyNeomorphicClasses();
                break;
                
            case 'hybrid':
                document.body.classList.add('hybrid-theme');
                this.loadStylesheet('glassmorphic-theme.css');
                this.loadStylesheet('neomorphic-theme.css');
                this.loadStylesheet('hybrid-theme.css');
                this.applyHybridClasses();
                break;
                
            default:
                // Default theme - remove all theme classes
                this.removeThemeClasses();
                break;
        }
    }

    applyGlassmorphicClasses() {
        // Apply glassmorphic classes to existing elements
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            navbar.classList.add('glassmorphic-nav');
        }

        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            card.classList.add('glassmorphic-card');
        });

        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(btn => {
            if (!btn.classList.contains('theme-option')) {
                btn.classList.add('glass-btn');
            }
        });

        const inputs = document.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.classList.add('glass-input');
        });
    }

    applyNeomorphicClasses() {
        // Apply neomorphic classes to existing elements
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            navbar.classList.add('neo-nav');
        }

        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            card.classList.add('neo-card');
        });

        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(btn => {
            if (!btn.classList.contains('theme-option')) {
                btn.classList.add('neo-btn');
            }
        });

        const inputs = document.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.classList.add('neo-input');
        });

        // Apply neomorphic background
        document.body.style.background = 'var(--neo-bg)';
    }

    applyHybridClasses() {
        // Apply hybrid classes to existing elements
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            navbar.classList.add('hybrid-nav');
        }

        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            card.classList.add('hybrid-video-card');
        });

        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(btn => {
            if (!btn.classList.contains('theme-option')) {
                btn.classList.add('hybrid-btn');
            }
        });

        const inputs = document.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.classList.add('hybrid-input');
        });
    }

    removeThemeClasses() {
        // Remove all theme-specific classes
        const elements = document.querySelectorAll('*');
        elements.forEach(el => {
            el.classList.remove(
                'glassmorphic-nav', 'glassmorphic-card', 'glass-btn', 'glass-input',
                'neo-nav', 'neo-card', 'neo-btn', 'neo-input',
                'hybrid-nav', 'hybrid-video-card', 'hybrid-btn', 'hybrid-input'
            );
        });

        // Reset body background
        document.body.style.background = '';
    }

    loadStylesheet(filename) {
        const existingLink = document.querySelector(`link[href*="${filename}"]`);
        if (!existingLink) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = `/static/${filename}`;
            link.className = 'theme-stylesheet';
            document.head.appendChild(link);
        }
    }

    removeThemeStylesheets() {
        const themeStylesheets = document.querySelectorAll('.theme-stylesheet');
        themeStylesheets.forEach(sheet => sheet.remove());
    }

    toggleDarkMode() {
        this.darkMode = !this.darkMode;
        this.applyDarkMode(this.darkMode);
        this.storeDarkMode(this.darkMode);
        this.updateDarkModeIcon();
        
        const mode = this.darkMode ? 'dark' : 'light';
        this.showThemeNotification(`${mode.charAt(0).toUpperCase() + mode.slice(1)} mode`);
        
        console.log(`🌙 Dark mode ${this.darkMode ? 'enabled' : 'disabled'}`);
    }

    toggleHighContrast() {
        const html = document.documentElement;
        const current = html.getAttribute('data-contrast') || 'normal';
        const newMode = current === 'high' ? 'normal' : 'high';
        html.setAttribute('data-contrast', newMode);
        localStorage.setItem('high-contrast', newMode);
        
        // Show notification
        this.showThemeNotification(`High contrast ${newMode === 'high' ? 'enabled' : 'disabled'}`);
    }

    applyDarkMode(isDark) {
        if (isDark) {
            document.documentElement.classList.add('dark-mode');
            document.body.classList.add('dark-mode');
        } else {
            document.documentElement.classList.remove('dark-mode');
            document.body.classList.remove('dark-mode');
        }
        
        this.updateDarkModeIcon();
    }

    updateDarkModeIcon() {
        const darkToggle = document.querySelector('.dark-toggle i');
        if (darkToggle) {
            darkToggle.className = this.darkMode ? 'fas fa-sun' : 'fas fa-moon';
        }
    }

    integrateWithExistingDarkMode(existingToggle) {
        // Listen to the existing dark mode toggle
        existingToggle.addEventListener('click', () => {
            // Small delay to let the existing dark mode logic run first
            setTimeout(() => {
                // Sync our dark mode state with the existing one
                const isDarkMode = document.documentElement.classList.contains('dark-mode') || 
                                 document.body.classList.contains('dark-mode');
                
                if (isDarkMode !== this.darkMode) {
                    this.darkMode = isDarkMode;
                    this.storeDarkMode(this.darkMode);
                    
                    // Apply theme-specific dark mode styles
                    this.applyTheme(this.currentTheme);
                }
            }, 50);
        });
        
        // Initial sync
        const isDarkMode = document.documentElement.classList.contains('dark-mode') || 
                          document.body.classList.contains('dark-mode');
        this.darkMode = isDarkMode;
        this.storeDarkMode(this.darkMode);
    }

    updateActiveTheme() {
        document.querySelectorAll('.theme-option[data-theme]').forEach(button => {
            button.classList.remove('active');
        });
        
        const activeButton = document.querySelector(`[data-theme="${this.currentTheme}"]`);
        if (activeButton) {
            activeButton.classList.add('active');
        }
    }

    showThemeNotification(themeName) {
        // Remove existing notification
        const existing = document.querySelector('.theme-notification');
        if (existing) existing.remove();

        // Create notification
        const notification = document.createElement('div');
        notification.className = 'theme-notification';
        notification.textContent = `Theme: ${themeName}`;
        
        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(0, 0, 0, 0.8)',
            color: 'white',
            padding: '0.75rem 1.5rem',
            borderRadius: '25px',
            fontSize: '0.9rem',
            fontWeight: '500',
            zIndex: '9999',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            opacity: '0',
            transition: 'all 0.3s ease'
        });

        document.body.appendChild(notification);

        // Animate in
        requestAnimationFrame(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(-50%) translateY(0)';
        });

        // Remove after 2 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(-50%) translateY(-20px)';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }

    // Storage methods
    storeTheme(theme) {
        localStorage.setItem('video-server-theme', theme);
    }

    getStoredTheme() {
        return localStorage.getItem('video-server-theme');
    }

    storeDarkMode(isDark) {
        localStorage.setItem('video-server-dark-mode', isDark.toString());
    }

    getStoredDarkMode() {
        const stored = localStorage.getItem('video-server-dark-mode');
        return stored === 'true';
    }

    // Public API
    getCurrentTheme() {
        return this.currentTheme;
    }

    getAvailableThemes() {
        return { ...this.themes };
    }

    isDarkMode() {
        return this.darkMode;
    }

    // Theme presets for different use cases
    applyPreset(presetName) {
        const presets = {
            'cinema': () => {
                this.switchTheme('glassmorphic');
                this.applyDarkMode(true);
            },
            'modern': () => {
                this.switchTheme('hybrid');
                this.applyDarkMode(false);
            },
            'minimal': () => {
                this.switchTheme('neomorphic');
                this.applyDarkMode(false);
            },
            'classic': () => {
                this.switchTheme('default');
                this.applyDarkMode(false);
            }
        };

        if (presets[presetName]) {
            presets[presetName]();
            this.showThemeNotification(`${presetName.charAt(0).toUpperCase() + presetName.slice(1)} preset applied`);
        }
    }

    // Auto theme based on time of day
    enableAutoTheme() {
        const hour = new Date().getHours();
        const isDayTime = hour >= 6 && hour < 18;
        
        this.applyDarkMode(!isDayTime);
        this.showThemeNotification(`Auto theme: ${isDayTime ? 'Day' : 'Night'} mode`);
    }
}

// Enhanced CSS for theme controls
const themeControlsCSS = `
    .theme-switcher {
        position: fixed;
        top: 25px;
        right: 120px;
        z-index: 1100;
        opacity: 0.9;
        transition: opacity 0.3s ease;
        pointer-events: auto;
    }

    .theme-switcher:hover {
        opacity: 1;
    }

    .theme-toggle {
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 50px;
        padding: 0.5rem;
        display: flex;
        gap: 0.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }

    .theme-option {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 50%;
        color: rgba(255, 255, 255, 0.8);
        cursor: pointer;
        height: 40px;
        transition: all 0.3s ease;
        width: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.9rem;
    }

    .theme-option:hover {
        background: rgba(255, 255, 255, 0.2);
        color: rgba(255, 255, 255, 1);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }

    .theme-option.active {
        background: linear-gradient(145deg, #4a90e2, #74b9ff);
        color: white;
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.4);
    }

    .theme-option:active {
        transform: translateY(0);
    }

    @media (max-width: 768px) {
        .theme-switcher {
            top: 70px;
            right: 10px;
        }
        
        .theme-option {
            height: 32px;
            width: 32px;
            font-size: 0.8rem;
        }
    }
`;

// Inject theme controls CSS
const styleSheet = document.createElement('style');
styleSheet.textContent = themeControlsCSS;
document.head.appendChild(styleSheet);

// Initialize theme manager when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.themeManager = new ThemeManager();
    });
} else {
    window.themeManager = new ThemeManager();
}

// Export for global use
window.ThemeManager = ThemeManager;

// === Keyboard Shortcuts ===
// Ctrl+1..4 switch theme; Ctrl+D toggles dark mode
(() => {
  const map = {
    "1": "default",
    "2": "glassmorphic",
    "3": "neomorphic",
    "4": "hybrid",
  };

  const isCtrl = (e) => e.ctrlKey || e.metaKey; // allow Cmd on macOS

  const tm = window.ThemeManager || null;
  if (!tm || typeof tm.switchTheme !== "function") return;

  window.addEventListener("keydown", (e) => {
    const key = e.key.toLowerCase();

    // Ctrl + D -> toggle dark mode
    if (isCtrl(e) && key === "d") {
      e.preventDefault();
      if (typeof tm.toggleDarkMode === "function") {
        tm.toggleDarkMode();
      } else {
        // Fallback: flip data-theme to dark/light
        const html = document.documentElement;
        const isDark = html.getAttribute("data-color-scheme") === "dark";
        html.setAttribute("data-color-scheme", isDark ? "light" : "dark");
        localStorage.setItem("color-scheme", isDark ? "light" : "dark");
      }
      window.dispatchEvent(new CustomEvent("ux:themeShortcut", { detail: { action: "toggleDark" } }));
      return;
    }

    // Ctrl + 1..4 -> switch theme
    if (isCtrl(e) && map[key]) {
      e.preventDefault();
      tm.switchTheme(map[key]);
      window.dispatchEvent(new CustomEvent("ux:themeShortcut", { detail: { action: "switchTheme", theme: map[key] } }));
    }
  });
})();