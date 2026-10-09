/**
 * static/js/gallery.js
 * Centralized Client-Side State & Modernized UI Controller for Image Gallery
 */

(function () {
  'use strict';

  // ────────────────────────────────────────────────────────────────────────
  // 1. CENTRALIZED GALLERY UI STATE
  // ────────────────────────────────────────────────────────────────────────

  const state = {
    viewMode: localStorage.getItem('gallery.viewMode') || 'masonry',
    density: localStorage.getItem('gallery.density') || 'medium',
    query: '',
    sort: localStorage.getItem('gallery.sort') || 'date-added',
    format: 'all',
    favoriteOnly: false,
    activePill: 'all',
    selectionMode: false,
    selectedImages: new Set(),
    lastSelectedIndex: null,
    lightboxImage: null,
    lightboxIndex: -1,
    inspectorOpen: localStorage.getItem('gallery.inspector') === 'true',
    filmstripOpen: localStorage.getItem('gallery.filmstrip') !== 'false',
    zoomLevel: 1, // 1 = fit, >1 = zoomed
    panX: 0,
    panY: 0,
    isPanning: false,
    startX: 0,
    startY: 0,
    slideshowRunning: false,
    slideshowTimer: null,
    lastActiveElement: null,
    renderLimit: 80
  };

  let allGroups = [];
  let serverImages = []; // raw from template
  let fullImageListAll = []; // from /api/gallery
  let imageMeta = {};
  let currentRenderList = [];
  let favoriteImages = new Set(loadFavoriteImages());
  let groupedImagesSet = new Set();

  function escapeHtml(str) {
    return String(str ?? '').replace(/[&<>"']/g, ch => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[ch]));
  }

  function thumbUrl(image, size = 320) {
    return `/gallery/thumb/${size}/${encodeURIComponent(image)}`;
  }

  function originalUrl(image) {
    return `/gallery/image/${encodeURIComponent(image)}`;
  }

  function loadFavoriteImages() {
    try {
      const raw = localStorage.getItem('gallery-favorites');
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      console.error('Failed to load favorites', e);
      return [];
    }
  }

  function saveFavoriteImages() {
    localStorage.setItem('gallery-favorites', JSON.stringify(Array.from(favoriteImages)));
  }

  // ────────────────────────────────────────────────────────────────────────
  // 2. DATA INITIALIZATION & FETCHING
  // ────────────────────────────────────────────────────────────────────────

  async function initGallery(initialImages) {
    serverImages = Array.isArray(initialImages) ? initialImages : [];
    fullImageListAll = [...serverImages];
    
    bindDOM();
    bindEvents();
    syncUIControlsFromState();

    await Promise.all([loadGroups(), loadAllImages()]);
    applyFiltersAndRender();
  }

  async function loadGroups({ refresh = false } = {}) {
    try {
      const suffix = refresh ? `?refresh=${Date.now()}` : '';
      const resp = await fetch(`/api/gallery/groups${suffix}`, { cache: refresh ? 'no-store' : 'default' });
      allGroups = await resp.json();
      
      groupedImagesSet.clear();
      allGroups.forEach(g => {
        if (Array.isArray(g.image_paths)) {
          g.image_paths.forEach(img => groupedImagesSet.add(img));
        } else if (Array.isArray(g.preview_images)) {
          g.preview_images.forEach(img => groupedImagesSet.add(img));
        }
      });

      renderGroups();
      populateGroupSelects();
    } catch (err) {
      console.error('Error loading gallery groups:', err);
      allGroups = [];
    }
  }

  async function loadAllImages({ refresh = false } = {}) {
    try {
      const suffix = refresh ? `?refresh=${Date.now()}` : '';
      const resp = await fetch(`/api/gallery${suffix}`, { cache: refresh ? 'no-store' : 'default' });
      const data = await resp.json();
      if (Array.isArray(data.images)) {
        fullImageListAll = [...data.images];
      }
      imageMeta = data.image_meta || {};
    } catch (err) {
      console.error('Error loading full image list:', err);
      fullImageListAll = [...serverImages];
    }
  }

  /**
   * Cross-check the in-memory image list against the server filesystem.
   * Silently removes any filename whose physical file no longer exists.
   * Called once on init, and re-called when the page regains focus.
   */
  async function validateAgainstFilesystem() {
    if (fullImageListAll.length === 0) return;
    try {
      const resp = await fetch('/api/gallery/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filenames: fullImageListAll })
      });
      if (!resp.ok) return;
      const data = await resp.json();
      if (Array.isArray(data.existing)) {
        const existingSet = new Set(data.existing);
        const before = fullImageListAll.length;
        fullImageListAll = fullImageListAll.filter(f => existingSet.has(f));
        if (fullImageListAll.length !== before) {
          console.info(`[Gallery] Pruned ${before - fullImageListAll.length} missing file(s) from image list.`);
          applyFiltersAndRender();
        }
      }
    } catch (err) {
      // Non-critical — stay silent; images will handle their own onerror below
      console.warn('[Gallery] Filesystem validation unavailable:', err.message);
    }
  }

  // ────────────────────────────────────────────────────────────────────────
  // 3. FILTERING, SORTING & RENDERING PIPELINE
  // ────────────────────────────────────────────────────────────────────────

  function applyFiltersAndRender() {
    let list = [...fullImageListAll];

    // Search Query
    if (state.query) {
      const q = state.query.toLowerCase().trim();
      list = list.filter(name => name.toLowerCase().includes(q));
    }

    // Format Filtering
    if (state.format !== 'all') {
      if (state.format === 'static') {
        list = list.filter(name => /\.(jpg|jpeg|png)$/i.test(name));
      } else if (state.format === 'motion') {
        list = list.filter(name => /\.(gif|webp)$/i.test(name));
      } else {
        const ext = `.${state.format}`;
        list = list.filter(name => name.toLowerCase().endsWith(ext));
      }
    }

    // Favorites Only
    if (state.favoriteOnly || state.activePill === 'favorites') {
      list = list.filter(name => favoriteImages.has(name));
    }

    // Quick-Filter Pill
    if (state.activePill === 'grouped') {
      list = list.filter(name => groupedImagesSet.has(name));
    } else if (state.activePill === 'ungrouped') {
      list = list.filter(name => !groupedImagesSet.has(name));
    } else if (state.activePill.startsWith('group:')) {
      const gId = parseInt(state.activePill.split(':')[1], 10);
      const group = allGroups.find(g => g.id === gId);
      if (group && Array.isArray(group.image_paths)) {
        list = list.filter(name => group.image_paths.includes(name));
      } else if (group && Array.isArray(group.preview_images)) {
        list = list.filter(name => group.preview_images.includes(name));
      }
    }

    // Sorting
    if (state.sort === 'name-asc') {
      list.sort((a, b) => a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' }));
    } else if (state.sort === 'name-desc') {
      list.sort((a, b) => b.localeCompare(a, undefined, { numeric: true, sensitivity: 'base' }));
    } else if (state.sort === 'favorites-first') {
      list.sort((a, b) => (favoriteImages.has(b) ? 1 : 0) - (favoriteImages.has(a) ? 1 : 0));
    }

    currentRenderList = list;
    state.renderLimit = 80;
    renderImagesGrid();
    updatePillsActiveState();
    updateFloatingActionBar();
  }

  // ────────────────────────────────────────────────────────────────────────
  // 4. GROUP CARDS (2x2 COLLAGE PREVIEWS)
  // ────────────────────────────────────────────────────────────────────────

  function renderGroups() {
    const container = document.getElementById('groupsGrid');
    const section = document.getElementById('groupsSection');
    if (!container) return;

    if (allGroups.length === 0) {
      if (section) section.style.display = 'none';
      return;
    }
    if (section) section.style.display = 'block';

    container.innerHTML = '';
    allGroups.forEach(group => {
      const card = document.createElement('article');
      card.className = 'group-card';
      card.dataset.groupId = group.id;
      card.tabIndex = 0;
      card.setAttribute('role', 'button');
      card.setAttribute('aria-label', `Open group ${group.name}`);

      // Prepare preview images for collage
      let previews = Array.isArray(group.preview_images) ? [...group.preview_images] : [];
      if (group.cover_image && !previews.includes(group.cover_image)) {
        previews.unshift(group.cover_image);
      }
      previews = previews.slice(0, 4);

      const collageDiv = document.createElement('div');
      collageDiv.className = 'group-collage';

      if (previews.length > 0) {
        const gridDiv = document.createElement('div');
        gridDiv.className = `group-collage-grid count-${previews.length}`;

        previews.forEach((imgSrc) => {
          const item = document.createElement('div');
          item.className = 'collage-item';
          const img = document.createElement('img');
          img.src = thumbUrl(imgSrc, 320);
          img.alt = group.name;
          img.loading = 'lazy';
          img.decoding = 'async';
          img.onerror = () => {
            // Silently remove this collage cell; no broken icon
            item.style.display = 'none';
          };
          item.appendChild(img);
          gridDiv.appendChild(item);
        });
        collageDiv.appendChild(gridDiv);
      } else {
        collageDiv.innerHTML = `<div class="group-collage-empty"><i class="fas fa-layer-group"></i></div>`;
      }

      if (group.cover_image) {
        const badge = document.createElement('span');
        badge.className = 'group-cover-badge';
        badge.innerHTML = `<i class="fas fa-bookmark"></i> Cover`;
        collageDiv.appendChild(badge);
      }

      const infoDiv = document.createElement('div');
      infoDiv.className = 'group-card-info';
      infoDiv.innerHTML = `
        <div class="group-card-heading">
          <h3 class="group-card-title">${escapeHtml(group.name)}</h3>
          <span class="group-card-count">${group.image_count} ${group.image_count === 1 ? 'item' : 'items'}</span>
        </div>
        <div class="group-card-actions">
          <button type="button" class="group-card-action" data-group-action="filter" aria-label="Filter to ${escapeHtml(group.name)}">
            <i class="fas fa-filter"></i> Filter
          </button>
          <button type="button" class="group-card-action primary" data-group-action="manage" aria-label="Manage ${escapeHtml(group.name)}">
            <i class="fas fa-sliders"></i> Manage
          </button>
        </div>
      `;

      card.appendChild(collageDiv);
      card.appendChild(infoDiv);

      card.addEventListener('click', () => {
        window.location.href = `/gallery/groups/${encodeURIComponent(group.slug || group.id)}`;
      });
      infoDiv.querySelector('[data-group-action="filter"]')?.addEventListener('click', (event) => {
        event.stopPropagation();
        state.activePill = `group:${group.id}`;
        state.favoriteOnly = false;
        state.format = 'all';
        applyFiltersAndRender();
        document.getElementById('galleryGrid')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
      infoDiv.querySelector('[data-group-action="manage"]')?.addEventListener('click', (event) => {
        event.stopPropagation();
        window.location.href = `/gallery/groups/${encodeURIComponent(group.slug || group.id)}`;
      });
      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          window.location.href = `/gallery/groups/${encodeURIComponent(group.slug || group.id)}`;
        }
      });

      container.appendChild(card);
    });
  }

  // ────────────────────────────────────────────────────────────────────────
  // 5. IMAGE GRID (MASONRY & UNIFORM)
  // ────────────────────────────────────────────────────────────────────────

  function renderImagesGrid() {
    const grid = document.getElementById('galleryGrid');
    const countDisplay = document.getElementById('galleryTotalCount');
    if (!grid) return;

    if (countDisplay) {
      countDisplay.textContent = `${currentRenderList.length} items`;
    }

    grid.className = `gallery-container-grid view-${state.viewMode} density-${state.density}`;

    if (currentRenderList.length === 0) {
      grid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1; text-align: center; padding: 3rem 1rem;">
          <i class="fas fa-images fa-3x mb-3" style="opacity: 0.3;"></i>
          <h3>No images matched your filters</h3>
          <p class="subtle-text">Try changing your search terms or resetting filters.</p>
        </div>
      `;
      return;
    }

    grid.innerHTML = '';
    const visibleImages = currentRenderList.slice(0, state.renderLimit);
    visibleImages.forEach((image, index) => {
      const item = document.createElement('div');
      item.className = 'gallery-item';
      item.dataset.image = image;
      item.dataset.index = index;
      item.tabIndex = 0;
      item.setAttribute('role', 'button');
      item.setAttribute('aria-label', `View ${image}`);

      if (state.selectedImages.has(image)) {
        item.classList.add('selected');
      }
      if (state.selectionMode) {
        item.classList.add('selection-mode');
      }

      // Checkbox
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.className = 'gallery-item-checkbox';
      checkbox.checked = state.selectedImages.has(image);
      checkbox.setAttribute('aria-label', `Select ${image}`);
      checkbox.addEventListener('click', (e) => {
        e.stopPropagation();
        handleItemSelection(image, index, e.shiftKey);
      });

      // Favorite Heart
      const favBtn = document.createElement('button');
      favBtn.type = 'button';
      favBtn.className = `image-fav-btn ${favoriteImages.has(image) ? 'active' : ''}`;
      favBtn.innerHTML = `<i class="fas fa-heart"></i>`;
      favBtn.setAttribute('aria-label', `Favorite ${image}`);
      favBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleFavorite(image, favBtn);
      });

      // Image element
      const img = document.createElement('img');
      img.src = thumbUrl(image, 320);
      img.srcset = `${thumbUrl(image, 160)} 160w, ${thumbUrl(image, 320)} 320w, ${thumbUrl(image, 640)} 640w`;
      img.sizes = '(max-width: 576px) 50vw, (max-width: 992px) 33vw, 25vw';
      img.alt = image;
      img.loading = 'lazy';
      img.decoding = 'async';
      img.onerror = () => {
        // File is gone — remove from live list and collapse this card
        fullImageListAll = fullImageListAll.filter(f => f !== image);
        currentRenderList = currentRenderList.filter(f => f !== image);
        item.style.transition = 'opacity 0.3s ease';
        item.style.opacity = '0';
        setTimeout(() => item.remove(), 320);
      };

      // Format Badge (e.g. GIF, WEBP)
      const ext = image.split('.').pop()?.toUpperCase() || '';
      const badge = document.createElement('span');
      badge.className = 'image-format-badge';
      badge.textContent = ext;

      item.appendChild(checkbox);
      item.appendChild(favBtn);
      item.appendChild(img);
      item.appendChild(badge);

      item.addEventListener('click', (e) => {
        if (e.target === checkbox || e.target === favBtn || favBtn.contains(e.target)) return;
        if (state.selectionMode || e.shiftKey) {
          handleItemSelection(image, index, e.shiftKey);
        } else {
          state.lastActiveElement = item;
          openLightbox(image, index);
        }
      });

      item.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          if (state.selectionMode) {
            handleItemSelection(image, index, e.shiftKey);
          } else {
            state.lastActiveElement = item;
            openLightbox(image, index);
          }
        }
      });

      grid.appendChild(item);
    });

    if (visibleImages.length < currentRenderList.length) {
      const more = document.createElement('div');
      more.className = 'gallery-load-more';
      more.style.gridColumn = '1 / -1';
      more.innerHTML = `<button type="button" class="gallery-load-more-btn">Load more <span>(${visibleImages.length} of ${currentRenderList.length})</span></button>`;
      more.querySelector('button').addEventListener('click', () => {
        state.renderLimit += 80;
        renderImagesGrid();
      });
      grid.appendChild(more);
    }
  }

  // ────────────────────────────────────────────────────────────────────────
  // 6. SELECTION & FLOATING ACTION BAR
  // ────────────────────────────────────────────────────────────────────────

  function handleItemSelection(image, index, isShift) {
    if (isShift && state.lastSelectedIndex !== null) {
      const start = Math.min(state.lastSelectedIndex, index);
      const end = Math.max(state.lastSelectedIndex, index);
      const shouldSelect = !state.selectedImages.has(image);

      for (let i = start; i <= end; i++) {
        const item = currentRenderList[i];
        if (item) {
          if (shouldSelect) state.selectedImages.add(item);
          else state.selectedImages.delete(item);
        }
      }
    } else {
      if (state.selectedImages.has(image)) {
        state.selectedImages.delete(image);
      } else {
        state.selectedImages.add(image);
      }
      state.lastSelectedIndex = index;
    }

    // Auto-enable selection mode if items selected
    if (state.selectedImages.size > 0) {
      state.selectionMode = true;
    }

    updateSelectionDOM();
    updateFloatingActionBar();
  }

  function updateSelectionDOM() {
    const items = document.querySelectorAll('.gallery-item');
    items.forEach(item => {
      const name = item.dataset.image;
      const isSel = state.selectedImages.has(name);
      item.classList.toggle('selected', isSel);
      item.classList.toggle('selection-mode', state.selectionMode);
      const cb = item.querySelector('.gallery-item-checkbox');
      if (cb) cb.checked = isSel;
    });

    const toggleBtn = document.getElementById('selectionToggle');
    if (toggleBtn) {
      toggleBtn.classList.toggle('active', state.selectionMode);
    }
  }

  function updateFloatingActionBar() {
    const bar = document.getElementById('galleryFloatingActionBar');
    const countBadge = document.getElementById('floatingSelectedCount');
    if (!bar) return;

    const count = state.selectedImages.size;
    if (count > 0) {
      bar.classList.add('active');
      if (countBadge) countBadge.textContent = `${count} selected`;
    } else {
      bar.classList.remove('active');
    }
  }

  function clearSelection() {
    state.selectedImages.clear();
    state.lastSelectedIndex = null;
    state.selectionMode = false;
    updateSelectionDOM();
    updateFloatingActionBar();
  }

  function toggleFavorite(image, btn) {
    if (favoriteImages.has(image)) {
      favoriteImages.delete(image);
      if (btn) btn.classList.remove('active');
    } else {
      favoriteImages.add(image);
      if (btn) btn.classList.add('active');
    }
    saveFavoriteImages();

    // If currently filtering favorites, update grid
    if (state.favoriteOnly || state.activePill === 'favorites') {
      applyFiltersAndRender();
    }
  }

  // ────────────────────────────────────────────────────────────────────────
  // 7. BATCH OPERATIONS
  // ────────────────────────────────────────────────────────────────────────

  async function batchAddToGroup(groupId) {
    if (!groupId || state.selectedImages.size === 0) return;
    const images = Array.from(state.selectedImages);

    try {
      const resp = await fetch(`/api/gallery/groups/${groupId}/images`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ images })
      });
      const data = await resp.json();
      if (resp.ok) {
        alert(`Successfully added ${images.length} images to group!`);
        clearSelection();
        await loadGroups();
        applyFiltersAndRender();
      } else {
        alert(data.error || 'Failed to add images to group');
      }
    } catch (err) {
      console.error('Batch add error:', err);
      alert('Connection error');
    }
  }

  async function batchCreateGroup(name) {
    if (!name || state.selectedImages.size === 0) return;
    const images = Array.from(state.selectedImages);

    try {
      const resp = await fetch('/api/gallery/groups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, images, cover_image: images[0] })
      });
      const data = await resp.json();
      if (resp.ok) {
        alert(`Group "${name}" created with ${images.length} images!`);
        clearSelection();
        await loadGroups();
        applyFiltersAndRender();
      } else {
        alert(data.error || 'Failed to create group');
      }
    } catch (err) {
      console.error('Batch create error:', err);
      alert('Connection error');
    }
  }

  function batchFavoriteSelected() {
    if (state.selectedImages.size === 0) return;
    state.selectedImages.forEach(img => favoriteImages.add(img));
    saveFavoriteImages();
    applyFiltersAndRender();
  }

  async function batchFindSimilar() {
    if (state.selectedImages.size === 0) return;
    const seed = Array.from(state.selectedImages)[0];
    const groupName = prompt('Enter a name for the similar images group (or leave blank):');
    
    try {
      const resp = await fetch('/api/gallery/groups/similar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: seed, name: groupName || 'Similar Images', limit: 16 })
      });
      const data = await resp.json();
      if (resp.ok) {
        alert(`Group created with ${data.added?.length || 0} similar images!`);
        clearSelection();
        await loadGroups();
        applyFiltersAndRender();
      } else {
        alert(data.error || 'Failed to find similar images');
      }
    } catch (err) {
      console.error('Similar search error:', err);
      alert('Connection error');
    }
  }

  // ────────────────────────────────────────────────────────────────────────
  // 8. LIGHTBOX & COLLAPSIBLE INSPECTOR
  // ────────────────────────────────────────────────────────────────────────

  function openLightbox(image, index) {
    state.lightboxImage = image;
    state.lightboxIndex = index ?? currentRenderList.indexOf(image);
    state.zoomLevel = 1;
    state.panX = 0;
    state.panY = 0;

    const modal = document.getElementById('galleryLightbox');
    if (!modal) return;

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';

    renderLightboxContent();
    renderFilmstrip();
  }

  function closeLightbox() {
    stopSlideshow();
    const modal = document.getElementById('galleryLightbox');
    if (modal) {
      modal.classList.remove('active');
    }
    document.body.style.overflow = '';
    state.lightboxImage = null;
    state.lightboxIndex = -1;

    // Return focus to thumbnail card that opened it
    if (state.lastActiveElement && typeof state.lastActiveElement.focus === 'function') {
      state.lastActiveElement.focus();
    }
  }

  function navigateLightbox(delta) {
    if (currentRenderList.length === 0) return;
    let nextIdx = state.lightboxIndex + delta;
    if (nextIdx < 0) nextIdx = currentRenderList.length - 1;
    if (nextIdx >= currentRenderList.length) nextIdx = 0;

    state.lightboxIndex = nextIdx;
    state.lightboxImage = currentRenderList[nextIdx];
    state.zoomLevel = 1;
    state.panX = 0;
    state.panY = 0;

    renderLightboxContent();
    renderFilmstrip();
    syncFilmstripActive();
  }

  function renderLightboxContent() {
    const imgEl = document.getElementById('lightboxImg');
    const filenameEl = document.getElementById('lightboxFilename');
    const indexEl = document.getElementById('lightboxIndexBadge');
    const favBtn = document.getElementById('lightboxFavBtn');
    const imageWrapper = document.getElementById('lightboxImageWrapper');
    const image = state.lightboxImage;
    if (!image || !imgEl) return;

    imgEl.src = thumbUrl(image, 1280);
    imgEl.dataset.fullSrc = originalUrl(image);
    imgEl.alt = image;

    if (filenameEl) filenameEl.textContent = image;
    if (indexEl) indexEl.textContent = `${state.lightboxIndex + 1} / ${currentRenderList.length}`;
    if (favBtn) {
      favBtn.classList.toggle('active', favoriteImages.has(image));
    }

    applyZoomAndPan();
    loadInspectorMetadata(image);
  }

  function applyZoomAndPan() {
    const imgEl = document.getElementById('lightboxImg');
    const wrapper = document.getElementById('lightboxImageWrapper');
    if (!imgEl || !wrapper) return;

    if (state.zoomLevel > 1) {
      wrapper.classList.add('zoomed');
      imgEl.style.transform = `translate(${state.panX}px, ${state.panY}px) scale(${state.zoomLevel})`;
    } else {
      wrapper.classList.remove('zoomed');
      imgEl.style.transform = 'none';
      state.panX = 0;
      state.panY = 0;
    }
  }

  function toggleZoom100() {
    state.zoomLevel = state.zoomLevel === 1 ? 2.5 : 1;
    state.panX = 0;
    state.panY = 0;
    applyZoomAndPan();
  }

  async function loadInspectorMetadata(image) {
    const metaFilename = document.getElementById('inspectorFilename');
    const metaFormat = document.getElementById('inspectorFormat');
    const metaDims = document.getElementById('inspectorDimensions');
    const groupsContainer = document.getElementById('inspectorGroupsList');
    const imgEl = document.getElementById('lightboxImg');

    if (metaFilename) metaFilename.textContent = image;
    const ext = image.split('.').pop()?.toUpperCase() || 'UNKNOWN';
    if (metaFormat) metaFormat.textContent = ext;

    if (metaDims && imgEl) {
      if (imgEl.naturalWidth) {
        metaDims.textContent = `${imgEl.naturalWidth} × ${imgEl.naturalHeight} px`;
      } else {
        imgEl.onload = () => {
          if (metaDims) metaDims.textContent = `${imgEl.naturalWidth} × ${imgEl.naturalHeight} px`;
        };
      }
    }

    // Load group memberships
    if (groupsContainer) {
      groupsContainer.innerHTML = '<span class="subtle-text">Loading groups…</span>';
      try {
        const resp = await fetch(`/api/gallery/images/${encodeURIComponent(image)}/groups`);
        const data = await resp.json();
        const groups = data.groups || [];
        if (groups.length === 0) {
          groupsContainer.innerHTML = '<span class="subtle-text">None</span>';
        } else {
          groupsContainer.innerHTML = '';
          groups.forEach(g => {
            const tag = document.createElement('span');
            tag.className = 'inspector-group-tag';
            tag.innerHTML = `
              <span>${escapeHtml(g.name)}</span>
              <button class="inspector-tag-remove" title="Remove from group" data-group-id="${g.id}">&times;</button>
            `;
            tag.querySelector('.inspector-tag-remove').addEventListener('click', async (e) => {
              e.stopPropagation();
              await removeImageFromGroup(g.id, image);
            });
            groupsContainer.appendChild(tag);
          });
        }
      } catch (err) {
        groupsContainer.innerHTML = '<span class="subtle-text">Unable to load</span>';
      }
    }
  }

  async function removeImageFromGroup(groupId, image) {
    try {
      const resp = await fetch(`/api/gallery/groups/${groupId}/images/${encodeURIComponent(image)}`, {
        method: 'DELETE'
      });
      if (resp.ok) {
        await loadGroups();
        loadInspectorMetadata(image);
        applyFiltersAndRender();
      }
    } catch (e) {
      console.error(e);
    }
  }

  // ────────────────────────────────────────────────────────────────────────
  // 9. FILMSTRIP & SLIDESHOW
  // ────────────────────────────────────────────────────────────────────────

  function renderFilmstrip() {
    const track = document.getElementById('lightboxFilmstripTrack');
    if (!track) return;

    track.innerHTML = '';
    const windowStart = Math.max(0, state.lightboxIndex - 20);
    const windowEnd = Math.min(currentRenderList.length, state.lightboxIndex + 21);
    currentRenderList.slice(windowStart, windowEnd).forEach((img, localIndex) => {
      const idx = windowStart + localIndex;
      const thumb = document.createElement('div');
      thumb.className = `filmstrip-thumb ${idx === state.lightboxIndex ? 'active' : ''}`;
      thumb.dataset.index = idx;
      thumb.innerHTML = `<img src="${thumbUrl(img, 160)}" alt="${escapeHtml(img)}" loading="lazy" decoding="async">`;
      thumb.addEventListener('click', () => {
        state.lightboxIndex = idx;
        state.lightboxImage = img;
        state.zoomLevel = 1;
        renderLightboxContent();
        syncFilmstripActive();
      });
      track.appendChild(thumb);
    });

    syncFilmstripActive();
  }

  function syncFilmstripActive() {
    const track = document.getElementById('lightboxFilmstripTrack');
    if (!track) return;

    const thumbs = track.querySelectorAll('.filmstrip-thumb');
    thumbs.forEach(t => {
      const isActive = parseInt(t.dataset.index, 10) === state.lightboxIndex;
      t.classList.toggle('active', isActive);
      if (isActive) {
        t.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
      }
    });
  }

  function toggleSlideshow() {
    if (state.slideshowRunning) {
      stopSlideshow();
    } else {
      startSlideshow();
    }
  }

  function startSlideshow() {
    state.slideshowRunning = true;
    const btn = document.getElementById('lightboxSlideshowBtn');
    if (btn) {
      btn.innerHTML = `<i class="fas fa-pause"></i> Pause`;
      btn.classList.add('active');
    }
    state.slideshowTimer = setInterval(() => {
      navigateLightbox(1);
    }, 3200);
  }

  function stopSlideshow() {
    state.slideshowRunning = false;
    if (state.slideshowTimer) {
      clearInterval(state.slideshowTimer);
      state.slideshowTimer = null;
    }
    const btn = document.getElementById('lightboxSlideshowBtn');
    if (btn) {
      btn.innerHTML = `<i class="fas fa-play"></i> Slideshow`;
      btn.classList.remove('active');
    }
  }

  // ────────────────────────────────────────────────────────────────────────
  // 10. DOM BINDINGS & KEYBOARD CONTROLS
  // ────────────────────────────────────────────────────────────────────────

  function bindDOM() {
    // Populate select elements
    populateGroupSelects();
  }

  function populateGroupSelects() {
    const floatingSelect = document.getElementById('floatingGroupSelect');
    const inspectorSelect = document.getElementById('inspectorGroupSelect');

    const fill = (el, placeholder) => {
      if (!el) return;
      el.innerHTML = `<option value="">${placeholder}</option>`;
      allGroups.forEach(g => {
        const opt = document.createElement('option');
        opt.value = g.id;
        opt.textContent = `${g.name} (${g.image_count})`;
        el.appendChild(opt);
      });
    };

    fill(floatingSelect, 'Add to group…');
    fill(inspectorSelect, 'Add to group…');
  }

  function syncUIControlsFromState() {
    // View mode segmented
    document.querySelectorAll('[data-view-mode]').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.viewMode === state.viewMode);
    });

    // Density segmented
    document.querySelectorAll('[data-density]').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.density === state.density);
    });

    // Sort select
    const sortSelect = document.getElementById('gallerySortSelect');
    if (sortSelect) sortSelect.value = state.sort;

    // Search input
    const searchInput = document.getElementById('gallerySearchInput');
    if (searchInput) searchInput.value = state.query;

    // Inspector
    const inspector = document.getElementById('lightboxInspector');
    const inspectorBtn = document.getElementById('lightboxInspectorBtn');
    if (inspector) inspector.classList.toggle('collapsed', !state.inspectorOpen);
    if (inspectorBtn) inspectorBtn.classList.toggle('active', state.inspectorOpen);

    // Filmstrip
    const filmstripTray = document.getElementById('lightboxFilmstripTray');
    if (filmstripTray) filmstripTray.classList.toggle('collapsed', !state.filmstripOpen);
  }

  function updatePillsActiveState() {
    document.querySelectorAll('.gallery-filter-pill').forEach(pill => {
      const target = pill.dataset.filterPill || 'all';
      pill.classList.toggle('active', target === state.activePill);
    });
  }

  function bindEvents() {
    // View Mode
    document.querySelectorAll('[data-view-mode]').forEach(btn => {
      btn.addEventListener('click', () => {
        state.viewMode = btn.dataset.viewMode;
        localStorage.setItem('gallery.viewMode', state.viewMode);
        syncUIControlsFromState();
        applyFiltersAndRender();
      });
    });

    // Density
    document.querySelectorAll('[data-density]').forEach(btn => {
      btn.addEventListener('click', () => {
        state.density = btn.dataset.density;
        localStorage.setItem('gallery.density', state.density);
        syncUIControlsFromState();
        applyFiltersAndRender();
      });
    });

    // Sort
    const sortSelect = document.getElementById('gallerySortSelect');
    if (sortSelect) {
      sortSelect.addEventListener('change', () => {
        state.sort = sortSelect.value;
        localStorage.setItem('gallery.sort', state.sort);
        applyFiltersAndRender();
      });
    }

    // Search
    const searchInput = document.getElementById('gallerySearchInput');
    const searchClear = document.getElementById('gallerySearchClear');
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        state.query = searchInput.value;
        applyFiltersAndRender();
      });
    }
    if (searchClear && searchInput) {
      searchClear.addEventListener('click', () => {
        searchInput.value = '';
        state.query = '';
        applyFiltersAndRender();
      });
    }

    // Selection Mode Toggle Button
    const selectionToggle = document.getElementById('selectionToggle');
    if (selectionToggle) {
      selectionToggle.addEventListener('click', () => {
        state.selectionMode = !state.selectionMode;
        if (!state.selectionMode) {
          clearSelection();
        } else {
          updateSelectionDOM();
        }
      });
    }

    document.getElementById('refreshGroupsBtn')?.addEventListener('click', async (event) => {
      const button = event.currentTarget;
      button.disabled = true;
      button.classList.add('is-refreshing');
      try {
        await Promise.all([loadGroups({ refresh: true }), loadAllImages({ refresh: true })]);
        applyFiltersAndRender();
      } finally {
        button.disabled = false;
        button.classList.remove('is-refreshing');
      }
    });

    // Quick-Filter Pills
    document.querySelectorAll('.gallery-filter-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        const filter = pill.dataset.filterPill || 'all';
        state.activePill = filter;
        if (filter === 'favorites') {
          state.favoriteOnly = true;
          state.format = 'all';
        } else if (['gif', 'webp', 'png', 'jpg'].includes(filter)) {
          state.format = filter;
          state.favoriteOnly = false;
        } else {
          state.format = 'all';
          state.favoriteOnly = false;
        }
        applyFiltersAndRender();
      });
    });

    // Floating Action Bar Events
    document.getElementById('floatingClearBtn')?.addEventListener('click', clearSelection);
    document.getElementById('floatingFavBtn')?.addEventListener('click', batchFavoriteSelected);
    document.getElementById('floatingSimilarBtn')?.addEventListener('click', batchFindSimilar);

    const floatingSelect = document.getElementById('floatingGroupSelect');
    document.getElementById('floatingAddToGroupBtn')?.addEventListener('click', () => {
      if (floatingSelect && floatingSelect.value) {
        batchAddToGroup(parseInt(floatingSelect.value, 10));
      } else {
        alert('Please select a group from the dropdown.');
      }
    });

    document.getElementById('floatingCreateGroupBtn')?.addEventListener('click', () => {
      const name = prompt('Enter new group name:');
      if (name && name.trim()) {
        batchCreateGroup(name.trim());
      }
    });

    // Lightbox Header Tools
    document.getElementById('lightboxCloseBtn')?.addEventListener('click', closeLightbox);
    document.getElementById('lightboxPrevBtn')?.addEventListener('click', () => navigateLightbox(-1));
    document.getElementById('lightboxNextBtn')?.addEventListener('click', () => navigateLightbox(1));
    document.getElementById('lightboxSlideshowBtn')?.addEventListener('click', toggleSlideshow);

    document.getElementById('lightboxFavBtn')?.addEventListener('click', () => {
      if (state.lightboxImage) {
        toggleFavorite(state.lightboxImage, document.getElementById('lightboxFavBtn'));
      }
    });

    document.getElementById('lightboxInspectorBtn')?.addEventListener('click', () => {
      state.inspectorOpen = !state.inspectorOpen;
      localStorage.setItem('gallery.inspector', state.inspectorOpen ? 'true' : 'false');
      syncUIControlsFromState();
    });

    document.getElementById('lightboxFilmstripToggleBtn')?.addEventListener('click', () => {
      state.filmstripOpen = !state.filmstripOpen;
      localStorage.setItem('gallery.filmstrip', state.filmstripOpen ? 'true' : 'false');
      syncUIControlsFromState();
    });

    // Lightbox Zoom & Pan
    const imgEl = document.getElementById('lightboxImg');
    const wrapper = document.getElementById('lightboxImageWrapper');

    document.getElementById('lightboxZoomInBtn')?.addEventListener('click', () => {
      state.zoomLevel = Math.min(state.zoomLevel + 0.5, 4);
      applyZoomAndPan();
    });
    document.getElementById('lightboxZoomOutBtn')?.addEventListener('click', () => {
      state.zoomLevel = Math.max(state.zoomLevel - 0.5, 1);
      applyZoomAndPan();
    });
    document.getElementById('lightboxZoomFitBtn')?.addEventListener('click', () => {
      state.zoomLevel = 1;
      state.panX = 0;
      state.panY = 0;
      applyZoomAndPan();
    });
    document.getElementById('lightboxZoom100Btn')?.addEventListener('click', toggleZoom100);

    if (imgEl) {
      imgEl.addEventListener('dblclick', toggleZoom100);
      imgEl.addEventListener('mousedown', (e) => {
        if (state.zoomLevel <= 1) return;
        state.isPanning = true;
        state.startX = e.clientX - state.panX;
        state.startY = e.clientY - state.panY;
        wrapper?.classList.add('panning');
        e.preventDefault();
      });
    }

    window.addEventListener('mousemove', (e) => {
      if (!state.isPanning) return;
      state.panX = e.clientX - state.startX;
      state.panY = e.clientY - state.startY;
      applyZoomAndPan();
    });

    window.addEventListener('mouseup', () => {
      if (state.isPanning) {
        state.isPanning = false;
        wrapper?.classList.remove('panning');
      }
    });

    // Inspector Actions
    const inspSelect = document.getElementById('inspectorGroupSelect');
    document.getElementById('inspectorAddGroupBtn')?.addEventListener('click', async () => {
      if (inspSelect && inspSelect.value && state.lightboxImage) {
        const gId = parseInt(inspSelect.value, 10);
        await fetch(`/api/gallery/groups/${gId}/images`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ images: [state.lightboxImage] })
        });
        await loadGroups();
        loadInspectorMetadata(state.lightboxImage);
        applyFiltersAndRender();
      }
    });

    document.getElementById('inspectorCreateGroupBtn')?.addEventListener('click', async () => {
      const input = document.getElementById('inspectorNewGroupName');
      if (input && input.value.trim() && state.lightboxImage) {
        const name = input.value.trim();
        await fetch('/api/gallery/groups', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, images: [state.lightboxImage], cover_image: state.lightboxImage })
        });
        input.value = '';
        await loadGroups();
        loadInspectorMetadata(state.lightboxImage);
        applyFiltersAndRender();
      }
    });

    document.getElementById('inspectorSimilarBtn')?.addEventListener('click', async () => {
      if (!state.lightboxImage) return;
      const groupName = prompt('Enter a name for the similar images group:');
      try {
        const resp = await fetch('/api/gallery/groups/similar', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename: state.lightboxImage, name: groupName || 'Similar Images', limit: 16 })
        });
        const data = await resp.json();
        if (resp.ok) {
          alert(`Created group with ${data.added?.length || 0} similar images!`);
          await loadGroups();
          loadInspectorMetadata(state.lightboxImage);
          applyFiltersAndRender();
        } else {
          alert(data.error || 'Failed to find similar images');
        }
      } catch (err) {
        alert('Connection error');
      }
    });

    // Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
      const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
      if (activeTag === 'input' || activeTag === 'textarea' || activeTag === 'select') {
        return;
      }

      const modal = document.getElementById('galleryLightbox');
      const isLightboxActive = modal && modal.classList.contains('active');

      if (!isLightboxActive) {
        if (e.key === 'Escape' && state.selectionMode) {
          clearSelection();
        }
        return;
      }

      switch (e.key) {
        case 'ArrowLeft':
          e.preventDefault();
          navigateLightbox(-1);
          break;
        case 'ArrowRight':
          e.preventDefault();
          navigateLightbox(1);
          break;
        case 'Escape':
          e.preventDefault();
          closeLightbox();
          break;
        case 'f':
        case 'F':
          e.preventDefault();
          if (state.lightboxImage) {
            toggleFavorite(state.lightboxImage, document.getElementById('lightboxFavBtn'));
          }
          break;
        case 'i':
        case 'I':
          e.preventDefault();
          state.inspectorOpen = !state.inspectorOpen;
          localStorage.setItem('gallery.inspector', state.inspectorOpen ? 'true' : 'false');
          syncUIControlsFromState();
          break;
        case 's':
        case 'S':
          e.preventDefault();
          document.getElementById('inspectorSimilarBtn')?.click();
          break;
        case '0':
          e.preventDefault();
          state.zoomLevel = 1;
          state.panX = 0;
          state.panY = 0;
          applyZoomAndPan();
          break;
        case '1':
          e.preventDefault();
          toggleZoom100();
          break;
        case ' ':
          e.preventDefault();
          toggleSlideshow();
          break;
      }
    });
  }

  // Export to window
  window.initGallery = initGallery;

})();
