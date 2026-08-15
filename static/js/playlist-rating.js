(function(){
  'use strict';

  document.addEventListener('click', (e) => {
    const star = e.target.closest && e.target.closest('.playlist-rating-widget .star');
    if (!star) return;
    
    const widget = star.closest('.playlist-rating-widget');
    const playlistId = widget.dataset.playlistId;
    const rating = parseInt(star.dataset.value, 10);
    if (!playlistId || !rating) return;

    fetch(`/api/playlists/${playlistId}/rating`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rating })
    })
    .then(r => r.json())
    .then(data => {
      if (data && data.success) {
        // Update the UI
        const stars = Array.from(widget.querySelectorAll('.star'));
        stars.forEach((s, idx) => {
          if ((idx + 1) <= rating) {
            s.classList.remove('text-muted');
            s.classList.add('text-warning');
          } else {
            s.classList.remove('text-warning');
            s.classList.add('text-muted');
          }
        });
      }
    })
    .catch(console.error);
  }, false);

  // Keyboard accessibility
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    const active = document.activeElement;
    if (!active) return;
    const star = active.closest && active.closest('.playlist-rating-widget .star');
    if (!star) return;
    star.click();
    e.preventDefault();
  }, false);
})();
