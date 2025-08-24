/**
 * Theme Integration Script
 * Ensures smooth integration between new theme system and existing dark mode
 */

document.addEventListener('DOMContentLoaded', () => {
    // Wait for both theme manager and existing dark mode to initialize
    setTimeout(() => {
        if (window.themeManager) {
            // Check if there's an existing dark mode system
            const existingDarkToggle = document.getElementById('toggle-dark-mode');
            
            if (existingDarkToggle) {
                console.log('🔗 Integrating with existing dark mode system');
                
                // Override the theme manager's dark mode methods to work with existing system
                const originalToggleDarkMode = window.themeManager.toggleDarkMode;
                
                window.themeManager.toggleDarkMode = function() {
                    // Trigger the existing dark mode toggle instead
                    existingDarkToggle.click();
                };
                
                // Sync initial state
                const isDarkMode = document.documentElement.classList.contains('dark-mode') || 
                                 document.body.classList.contains('dark-mode');
                window.themeManager.darkMode = isDarkMode;
                
                console.log('✅ Theme integration complete');
            }
        }
    }, 100);
});

// Add some helper styles to ensure themes work well with existing navbar
const integrationStyles = `
    /* Ensure theme controls don't interfere with existing navbar */
    .theme-switcher {
        position: fixed !important;
        top: 25px !important;
        right: 120px !important;
        z-index: 1100 !important;
    }
    
    /* Ensure theme controls have solid background */
    .theme-toggle {
        background: rgba(0, 0, 0, 0.85) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
    }
    
    /* On mobile, position below navbar */
    @media (max-width: 768px) {
        .theme-switcher {
            top: 70px !important;
            right: 10px !important;
        }
    }
    
    /* Ensure content doesn't get covered by theme controls */
    .container {
        padding-top: 1rem;
    }
    
    /* Add some breathing room for the theme controls */
    .theme-switcher::before {
        content: '';
        position: absolute;
        top: -10px;
        left: -10px;
        right: -10px;
        bottom: -10px;
        background: transparent;
        pointer-events: none;
    }
    
    /* Ensure themes work with existing navbar styles */
    .glassmorphic-theme .navbar,
    .hybrid-theme .navbar {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .neomorphic-theme .navbar {
        background: var(--neo-surface) !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Ensure existing dark mode toggle works with themes */
    .glassmorphic-theme #toggle-dark-mode,
    .hybrid-theme #toggle-dark-mode {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .neomorphic-theme #toggle-dark-mode {
        background: var(--neo-surface);
        box-shadow: var(--neo-shadow-outset);
        border: none;
        border-radius: 8px;
        transition: var(--neo-transition);
    }
    
    .neomorphic-theme #toggle-dark-mode:hover {
        box-shadow: var(--neo-shadow-hover);
        transform: translateY(-1px);
    }
`;

// Inject integration styles
const integrationStyleSheet = document.createElement('style');
integrationStyleSheet.textContent = integrationStyles;
document.head.appendChild(integrationStyleSheet);