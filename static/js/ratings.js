// Delegated rating handler
(function(){
  'use strict';

  function updateRatingDisplays(filename, rating) {
    // Update all rating widgets that reference the filename
    document.querySelectorAll('.rating').forEach(container => {
      if (container.dataset.filename !== filename) return;
      const stars = Array.from(container.querySelectorAll('i'));
      stars.forEach((s, idx) => {
        s.className = (idx + 1) <= rating ? 'fas fa-star' : 'far fa-star';
      });
    });
  }

  // Click delegation for rating stars
  document.addEventListener('click', (e) => {
    const star = e.target.closest && e.target.closest('.rating i');
    if (!star) return;
    const rating = parseInt(star.dataset.value, 10);
    const container = star.closest('.rating');
    const filename = container && container.dataset.filename;
    if (!filename || !rating) return;

    fetch('/rate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename, rating })
    })
    .then(r => r.json())
    .then(data => {
      if (data && data.success) {
        updateRatingDisplays(filename, rating);
      }
    })
    .catch(console.error);
  }, false);

  // Keyboard accessibility: Enter or Space when a star has focus
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    const active = document.activeElement;
    if (!active) return;
    const star = active.closest && active.closest('.rating i');
    if (!star) return;
    // emulate click
    star.click();
    e.preventDefault();
  }, false);

  // Expose helper for programmatic updates
  window.__ratings = { updateRatingDisplays };
})();
