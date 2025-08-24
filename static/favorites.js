document.addEventListener('DOMContentLoaded', () => {
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
        if (data.success) {
          const icon = btn.querySelector('i');
          const isFavorited = data.is_favorite;
          
          // Update heart icon state
          if (isFavorited) {
            icon.className = 'fas fa-heart text-danger'; // Filled red heart
          } else {
            icon.className = 'far fa-heart text-danger'; // Outline red heart
          }

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
