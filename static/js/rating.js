/**
 * static/js/rating.js
 * Unified rating widget controller (library + watch page)
 * - Supports multiple rating widgets on the same page
 * - Syncs widgets that point to the same media hash/filename
 * - Uses the /rate endpoint for write-through cache updates
 */

const widgets = [];

const getKey = (el) => el.dataset.filename || el.dataset.mediaHash;

const setVisual = (starEl, isActive) => {
  starEl.classList.toggle('is-active', isActive);
  if (starEl.getAttribute('role') === 'radio') {
    starEl.setAttribute('aria-checked', isActive ? 'true' : 'false');
  }
  const icon = starEl.querySelector('.fa-star');
  if (icon) {
    icon.classList.toggle('fas', isActive);
    icon.classList.toggle('far', !isActive);
  }
};

const initWidget = (ratingEl) => {
  const key = getKey(ratingEl);
  if (!key) return;

  const stars = Array.from(ratingEl.querySelectorAll('[data-value]'));
  if (!stars.length) return;

  const setChecked = (value) => {
    stars.forEach((star, idx) => setVisual(star, idx + 1 <= value));
    ratingEl.dataset.current = value;
  };

  const initial =
    parseInt(ratingEl.dataset.current || ratingEl.dataset.rating || 0, 10) ||
    stars.filter((s) => s.classList.contains('is-active')).length;
  if (initial) setChecked(initial);

  const syncPeers = (value) => {
    widgets.forEach((w) => {
      if (w.key === key && w.el !== ratingEl) {
        w.setChecked(value);
      }
    });
  };

  const sendRating = async (value) => {
    const filename = ratingEl.dataset.filename || key;
    try {
      const res = await fetch('/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename, rating: value }),
      });
      if (!res.ok) {
        console.error('Failed to save rating', res.status);
      }
    } catch (err) {
      console.error('Error saving rating', err);
    }
  };

  const onSelect = (value) => {
    setChecked(value);
    syncPeers(value);
    sendRating(value);
  };

  stars.forEach((star) => {
    const value = parseInt(star.dataset.value, 10);
    star.setAttribute('tabindex', '0');
    star.addEventListener('click', () => onSelect(value));
    star.addEventListener('pointerdown', () => onSelect(value), {
      passive: true,
    });
    star.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        onSelect(value);
      }
    });
  });

  widgets.push({ el: ratingEl, key, setChecked });
};

const initAllRatings = () => {
  document.querySelectorAll('.rating').forEach(initWidget);
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAllRatings);
} else {
  initAllRatings();
}

export { initAllRatings };
