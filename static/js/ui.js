/**
 * static/js/ui.js
 * Simple UI helpers - dark mode toggle (keep dark mode as default)
 */

document.addEventListener('DOMContentLoaded', () => {
  // Ensure dark mode is always on
  document.documentElement.classList.add('dark-mode');
  document.body.classList.add('dark-mode');
  
  // Dark mode toggle button (mostly decorative now)
  const darkModeToggle = document.getElementById('toggle-dark-mode');
  if (darkModeToggle) {
    darkModeToggle.addEventListener('click', () => {
      // Keep dark mode on, just provide feedback
      const icon = darkModeToggle.querySelector('i');
      if (icon) {
        // Brief visual feedback
        icon.style.transform = 'scale(1.2)';
        setTimeout(() => {
          icon.style.transform = 'scale(1)';
        }, 150);
      }
    });
  }
});