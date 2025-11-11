/**
 * static/js/rating.js
 * Rating widget controller
 * Handles input via click, pointerdown, and keyboard (Enter/Space)
 * Works on desktop, mobile, and VR (Quest)
 * No reliance on :hover state
 */

import { platform } from './platform.js';

/**
 * Initialize rating widget on the page
 * Finds the rating div and binds event handlers
 */
function initRating() {
  const rating = document.querySelector('.rating');
  if (!rating) return;

  const mediaHash = rating.dataset.mediaHash;
  if (!mediaHash) {
    console.warn('Rating widget found but no data-media-hash attribute');
    return;
  }

  // Helper: Update visual state based on rating value
  const setChecked = (value) => {
    rating.querySelectorAll('.star').forEach((btn, index) => {
      const isChecked = index + 1 <= value;
      btn.setAttribute('aria-checked', isChecked ? 'true' : 'false');
      btn.classList.toggle('is-active', isChecked);
    });
  };

  // Helper: Send rating to server
  const sendRating = async (value) => {
    try {
      const response = await fetch(
        `/api/ratings/${encodeURIComponent(mediaHash)}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ value }),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        console.error(
          `Failed to save rating: ${response.status}`,
          error
        );
        return;
      }

      const data = await response.json();
      // Update UI with server response
      if (data.user?.value !== undefined) {
        setChecked(data.user.value);
      }
      // Log average for debugging
      if (data.average !== undefined) {
        console.debug(
          `Rating saved. Average: ${data.average}, Count: ${data.count}`
        );
      }
    } catch (error) {
      console.error('Error saving rating:', error);
    }
  };

  // Helper: Handle rating selection
  const onSelect = (value) => {
    setChecked(value);
    sendRating(value);
  };

  // Bind event handlers to each star button
  rating.querySelectorAll('.star').forEach((btn) => {
    const value = parseInt(btn.dataset.value, 10);

    // Make button keyboard-accessible
    btn.setAttribute('tabindex', '0');

    // Click handler (always works)
    btn.addEventListener('click', () => onSelect(value), { capture: false });

    // Pointer down handler (works on touch, mouse, and Quest controller)
    btn.addEventListener('pointerdown', (e) => {
      // Don't prevent default to allow focus
      onSelect(value);
    }, { passive: true });

    // Keyboard handler (Enter or Space to activate)
    btn.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        onSelect(value);
      }
    });
  });

  // Initialize with any existing rating from the page
  const currentRating = rating.querySelectorAll('.star.is-active').length;
  if (currentRating > 0) {
    setChecked(currentRating);
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initRating);
} else {
  initRating();
}

// Export for use in other modules
export { initRating };
