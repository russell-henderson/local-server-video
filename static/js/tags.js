// Shared tag management (add/delete) for watch pages
(function(){
  'use strict';

  function renderTags(container, tags) {
    container.innerHTML = '';
    tags.forEach(t => {
      const span = document.createElement('span');
      span.className = 'badge tag-badge';
      span.dataset.tag = t;
      span.innerHTML = `${t} <span class="delete-tag">&times;</span>`;
      container.appendChild(span);
    });
  }

  // Find filename for current watch page from common places
  function findFilename(contextEl) {
    // prefer data-filename on container; fallback to player/rating
    if (!contextEl) contextEl = document;
    const byData = contextEl.querySelector('[data-filename]');
    if (byData) return byData.dataset.filename;
    const player = contextEl.querySelector('[data-player] video') || document.querySelector('[data-player] video');
    if (player) return player.dataset.filename || null;
    return null;
  }

  document.addEventListener('click', (e) => {
    const del = e.target.closest && e.target.closest('.delete-tag');
    if (!del) return;
    const badge = del.closest('.tag-badge');
    const tag = badge && badge.dataset.tag;
    if (!tag) return;
    // find the tags container and filename
    const container = badge.closest('#existing-tags') || document.getElementById('existing-tags');
    const filename = container && (container.dataset.filename || findFilename(container));
    if (!filename) return;

    fetch('/delete_tag', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ filename, tag })
    })
    .then(r => r.json())
    .then(d => {
      if (d.success && Array.isArray(d.tags)) {
        renderTags(container, d.tags);
      }
    })
    .catch(console.error);
  });

  // Add tag via Enter in the input with id new-tag
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter') return;
    const input = document.activeElement;
    if (!input || input.id !== 'new-tag') return;
    const tag = input.value.trim();
    if (!tag) return;
    const container = document.getElementById('existing-tags');
    const filename = container && (container.dataset.filename || findFilename(container));
    if (!filename) return;

    fetch('/tag', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ filename, tag })
    })
    .then(r => r.json())
    .then(d => {
      if (d.success && Array.isArray(d.tags)) {
        renderTags(container, d.tags);
        input.value = '';
      }
    })
    .catch(console.error);
  });

  // On load: ensure delete handlers are effectively delegated (server-rendered tags stay usable)
  document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('existing-tags');
    if (container && container.dataset.tags) {
      try {
        const tags = JSON.parse(container.dataset.tags);
        renderTags(container, tags);
      } catch (e) {
        // ignore parse errors and leave server rendered markup
      }
    }
  });

  // Expose helper for programmatic render
  window.__tags = { renderTags };
})();
