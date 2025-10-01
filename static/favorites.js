// If OptimizedUtils is present it already delegates favorite clicks; avoid double-binding.
document.addEventListener('DOMContentLoaded', () => {
  if (window.optimizedUtils) {
    // OptimizedUtils delegates clicks; just provide a small compatibility helper
    // so templates that expect data.is_favorite get updated when backend returns.
    window.updateFavoriteButtons = function(filename, isFavorite) {
      document.querySelectorAll(`[data-filename="${filename}"].favorite-btn`).forEach(btn => {
        const icon = btn.querySelector('i');
        if (!icon) return;
        icon.className = isFavorite ? 'fas fa-heart text-danger' : 'far fa-heart text-danger';
      });
    };
    return;
  }

  // Fallback: attach per-button handlers when OptimizedUtils isn't active
  document.querySelectorAll('.favorite-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const filename = btn.dataset.filename;
      fetch('/favorite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename })
      })
      .then(res => res.json())
      .then(data => {
        if (data && data.success) {
          const icon = btn.querySelector('i');
          if (!icon) return;

          // Support both response shapes: { is_favorite: bool } or { favorites: [...] }
          let isFavorited = false;
          if (typeof data.is_favorite === 'boolean') {
            isFavorited = data.is_favorite;
          } else if (Array.isArray(data.favorites)) {
            isFavorited = data.favorites.includes(filename);
          }

          // Update heart icon state
          icon.className = isFavorited ? 'fas fa-heart text-danger' : 'far fa-heart text-danger';

          // Optional: Remove card if unfavorited from /favorites page
          if (window.location.pathname === '/favorites' && icon.classList.contains('far')) {
            const card = btn.closest('.col-sm-6, .col-md-4, .col-lg-3');
            if (card) card.remove();
          }
        }
      })
      .catch(console.error);
    });
  });
});
