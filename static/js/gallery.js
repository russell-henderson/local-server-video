/* Shared collection/group controller. Originals are fetched only on explicit request. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const storage = {
    get(key, fallback) { try { return localStorage.getItem(key) ?? fallback; } catch { return fallback; } },
    set(key, value) { try { localStorage.setItem(key, value); } catch { /* Private/blocked storage is optional. */ } }
  };
  const html = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let favorites;
  try { const saved = JSON.parse(storage.get('gallery-favorites', '[]')); favorites = new Set(Array.isArray(saved) ? saved : []); }
  catch { favorites = new Set(); }
  const state = {
    images: [], meta: {}, groups: [], filtered: [], selected: new Set(), limit: 80,
    query: '', filter: 'all', sort: 'date-added', selection: false, lastIndex: null,
    view: storage.get('gallery.viewMode', 'masonry'), density: storage.get('gallery.density', 'medium'),
    image: null, zoom: 1, panX: 0, panY: 0, original: false, busy: false,
    inspector: storage.get('gallery.inspector', 'false') === 'true',
    filmstrip: storage.get('gallery.filmstrip', 'true') !== 'false'
  };
  let pollTimer, slideTimer, requestNumber = 0, opener, renderScheduled = false;
  const thumb = (name, size) => '/gallery/thumb/' + size + '/' + encodeURIComponent(name) + '?v=' + (state.meta[name]?.revision || '');
  const original = name => '/gallery/image/' + encodeURIComponent(name) + '?v=' + (state.meta[name]?.revision || '');
  function scheduleGridRender() {
    if (renderScheduled) return;
    renderScheduled = true;
    requestAnimationFrame(() => {
      renderScheduled = false;
      renderGrid();
    });
  }
  function status(message, error = false, loading = false) {
    const el = $('galleryStatus');
    if (!el) return;
    el.textContent = message;
    el.classList.toggle('gallery-error', error);
    el.classList.toggle('is-loading', loading && !error);
  }
  async function api(url, options = {}) {
    const response = await fetch(url, {cache: 'no-cache', ...options,
      headers: {'Content-Type': 'application/json', ...options.headers}});
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || data.description || 'Request failed (' + response.status + ')');
    return data;
  }
  function readURL(initialGroup) {
    const params = new URLSearchParams(location.search);
    state.query = params.get('q') || '';
    state.sort = params.get('sort') || 'date-added';
    if (!['date-added','name-asc','name-desc','favorites-first'].includes(state.sort)) state.sort = 'date-added';
    state.filter = params.get('filter') || (initialGroup ? 'group:' + initialGroup : 'all');
    $('gallerySearchInput').value = state.query;
    $('gallerySortSelect').value = state.sort;
  }
  function writeURL() {
    const url = new URL(location.href);
    for (const [key, value] of [['q', state.query], ['filter', state.filter], ['sort', state.sort]]) {
      if (value) url.searchParams.set(key, value); else url.searchParams.delete(key);
    }
    if (url.href !== location.href) history.pushState({}, '', url);
  }
  async function load() {
    const number = ++requestNumber;
    status('Loading library…', false, true);
    try {
      const data = await api('/api/gallery?groups=1');
      if (number !== requestNumber) return;
      const previousRevision = state.revision;
      const previousGroups = JSON.stringify(state.groups);
      state.images = data.images; state.meta = data.image_meta; state.groups = data.groups || [];
      state.revision = data.version;
      state.selected = new Set([...state.selected].filter(name => state.images.includes(name)));
      renderGroups(); populateGroups();
      if (previousRevision !== data.version || previousGroups !== JSON.stringify(state.groups)) filter(false);
      renderFilterPills();
      if (state.image && !state.images.includes(state.image)) closeViewer();
      else if (state.image) renderInspector();
      if (data.status?.error) status('Library unavailable: ' + data.status.error + '. Showing the last successful index.', true);
      else status(data.status?.refreshing ? 'Refreshing library…' : state.images.length + ' images indexed');
      clearTimeout(pollTimer);
      pollTimer = setTimeout(load, data.status?.refreshing ? 750 : 30000);
    } catch (error) {
      status(error.message + '. Use Refresh to retry.', true);
      clearTimeout(pollTimer); pollTimer = setTimeout(load, 30000);
    }
  }
  function renderFilterPills() {
    const available = new Set();
    Object.values(state.meta).forEach(meta => {
      if (meta.animated) available.add('motion');
      const format = String(meta.format || '').toLowerCase();
      if (format === 'jpeg') available.add('jpg');
      else if (['gif', 'webp', 'png', 'jpg'].includes(format)) available.add(format);
    });
    document.querySelectorAll('.gallery-filter-pill').forEach(button => {
      const key = button.dataset.filterPill;
      const visible = ['all', 'favorites', 'grouped', 'ungrouped'].includes(key) || available.has(key);
      button.hidden = !visible;
      button.setAttribute('aria-pressed', String(button.classList.contains('active')));
    });
  }
  function filter(push = true) {
    let result = state.images.filter(name => name.toLowerCase().includes(state.query.trim().toLowerCase()));
    const grouped = new Set(state.groups.flatMap(group => group.image_paths));
    const group = state.groups.find(g => 'group:' + g.id === state.filter);
    if (state.filter.startsWith('group:')) {
      const members = new Set(group?.image_paths || []);
      result = result.filter(name => members.has(name));
    } else if (state.filter === 'favorites') result = result.filter(name => favorites.has(name));
    else if (state.filter === 'grouped') result = result.filter(name => grouped.has(name));
    else if (state.filter === 'ungrouped') result = result.filter(name => !grouped.has(name));
    else if (state.filter === 'motion') result = result.filter(name => state.meta[name]?.animated);
    else if (['jpg','png','webp','gif'].includes(state.filter)) {
      result = result.filter(name => (state.meta[name]?.format || '').replace('jpeg','jpg') === state.filter);
    }
    const byName = (a,b) => a.localeCompare(b, undefined, {numeric: true, sensitivity: 'base'});
    result.sort((a,b) => {
      if (state.sort === 'name-asc') return byName(a,b);
      if (state.sort === 'name-desc') return byName(b,a);
      if (state.sort === 'favorites-first') return Number(favorites.has(b)) - Number(favorites.has(a)) || byName(a,b);
      return (state.meta[b]?.added || 0) - (state.meta[a]?.added || 0) || byName(a,b);
    });
    state.filtered = result; state.limit = 80; state.lastIndex = null;

    const filterLabel = group?.name || (state.filter === 'all' ? 'All images' : state.filter.replace(/-/g, ' '));
    const queryLabel = state.query.trim() ? 'Search: ' + state.query.trim() : 'No search';
    const filterEl = $('activeGalleryFilter');
    if (filterEl) filterEl.textContent = filterLabel;
    const queryEl = $('galleryStateQuery');
    if (queryEl) {
      queryEl.textContent = queryLabel;
      queryEl.classList.toggle('is-empty', !state.query.trim());
    }
    document.querySelectorAll('[data-filter-pill]').forEach(button => {
      const active = button.dataset.filterPill === state.filter;
      button.classList.toggle('active', active); button.setAttribute('aria-pressed', active);
    });
    scheduleGridRender();
    syncSelection();
    if (push) writeURL();
  }
  function button(label, action, className = 'gallery-btn-pill') {
    const element = document.createElement('button');
    element.type = 'button'; element.className = className; element.textContent = label;
    element.addEventListener('click', action);
    return element;
  }
  function loadImage(image, name, size, failed) {
    let attempts = 0;
    const token = String(Number(image.dataset.request || 0) + 1);
    image.dataset.request = token;
    const revision = state.meta[name]?.revision;
    image.onload = () => { image.classList.remove('image-unavailable'); failed?.(false); };
    image.onerror = () => {
      image.classList.add('image-unavailable'); failed?.(true);
      if (++attempts <= 5 && !state.meta[name]?.error) {
        setTimeout(() => {
          if (image.isConnected && image.dataset.request === token && revision === state.meta[name]?.revision && image.dataset.source === name) image.src = thumb(name, size);
        }, Math.min(1000 * attempts, 5000));
      }
    };
    image.dataset.source = name;
    image.src = thumb(name, size);
  }
  function renderGrid(append = false) {
    const grid = $('galleryGrid');
    grid.className = 'gallery-container-grid view-' + state.view + ' density-' + state.density;
    grid.querySelector('.gallery-load-more')?.remove();
    const start = append ? grid.querySelectorAll('.gallery-item').length : 0;
    if (!append) grid.replaceChildren();
    if (!state.filtered.length) {
      const emptyState = document.createElement('div');
      emptyState.className = 'gallery-empty-state';
      emptyState.innerHTML = `
        <div class="gallery-empty-state__icon">⌕</div>
        <div>
          <h3>No images match this view</h3>
          <p>Try clearing the search, resetting the filter, or refreshing the library to bring the collection back into view.</p>
        </div>
        <button type="button" class="gallery-btn-pill" id="galleryEmptyResetBtn">Reset filters</button>
      `;
      emptyState.querySelector('#galleryEmptyResetBtn').addEventListener('click', () => {
        state.filter = 'all'; state.query = ''; if ($('gallerySearchInput')) $('gallerySearchInput').value = ''; filter();
      });
      grid.append(emptyState);
      return;
    }
    const fragment = document.createDocumentFragment();
    state.filtered.slice(start, state.limit).forEach((name, offset) => {
      const index = start + offset, meta = state.meta[name] || {};
      const card = document.createElement('article');
      card.className = 'gallery-item';
      card.dataset.image = name;
      card.tabIndex = 0;
      card.setAttribute('role', 'button');
      card.setAttribute('aria-label', 'Open image ' + name);
      card.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ' || event.key === 'Spacebar') {
          event.preventDefault();
          if (state.selection) {
            select(name, index, event.shiftKey);
            return;
          }
          openViewer(name, open);
        }
      });
      const open = document.createElement('button');
      open.type = 'button';
      open.className = 'gallery-image-open';
      open.addEventListener('click', (event) => {
        if (state.selection) {
          select(name, index, event.shiftKey);
          return;
        }
        openViewer(name, open);
      });
      open.setAttribute('aria-label', 'View ' + name);
      const image = document.createElement('img');
      image.alt = name; image.loading = index < 8 ? 'eager' : 'lazy'; image.decoding = 'async';
      image.width = meta.width || 320; image.height = meta.height || 240;
      const retry = button('Retry image', () => loadImage(image, name, 640, failed => retry.hidden = !failed), 'image-retry');
      retry.hidden = true;
      loadImage(image, name, 640, failed => retry.hidden = !failed);
      open.append(image);
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox'; checkbox.className = 'gallery-item-checkbox';
      checkbox.setAttribute('aria-label', 'Select ' + name);
      checkbox.addEventListener('click', event => select(name, index, event.shiftKey));
      const favorite = button('♥', () => toggleFavorite(name), 'image-fav-btn');
      favorite.setAttribute('aria-label', 'Favorite ' + name);
      favorite.setAttribute('aria-pressed', favorites.has(name));
      favorite.classList.toggle('active', favorites.has(name));
      const badge = document.createElement('span');
      badge.className = 'image-format-badge'; badge.textContent = meta.animated ? 'MOTION' : (meta.format || '').toUpperCase();
      card.append(open, checkbox, favorite, badge, retry); fragment.append(card);
    });
    grid.append(fragment);
    if (!state.filtered.length) grid.innerHTML = '<p class="empty-state">No images match. Reset filters or refresh the library.</p>';
    const count = Math.min(state.limit, state.filtered.length);
    $('galleryTotalCount').textContent = count + ' of ' + state.filtered.length + ' items';
    if (count < state.filtered.length) {
      const more = button('Load more (' + count + ' of ' + state.filtered.length + ')', () => {
        state.limit += 80; renderGrid(true);
        grid.querySelectorAll('.gallery-image-open')[count]?.focus({preventScroll: true});
      }, 'gallery-load-more gallery-load-more-btn');
      grid.append(more);
    }
    syncSelection();
  }
  function select(name, index, range = false) {
    if (range && state.lastIndex !== null && state.lastIndex !== index) {
      const from = Math.min(index, state.lastIndex);
      const to = Math.max(index, state.lastIndex);
      const names = state.filtered.slice(from, to + 1);
      const selected = new Set(state.selected);
      names.forEach(item => selected.add(item));
      state.selected = selected;
      state.lastIndex = index;
      state.selection = true;
      syncSelection();
      return;
    }

    const remove = state.selected.has(name);
    if (remove) {
      state.selected.delete(name);
    } else {
      state.selected.add(name);
    }
    state.lastIndex = index;
    state.selection = true;
    syncSelection();
  }
  function syncSelection() {
    document.querySelectorAll('.gallery-item').forEach(card => {
      const selected = state.selected.has(card.dataset.image);
      card.classList.toggle('selected', selected); card.classList.toggle('selection-mode', state.selection);
      card.querySelector('input').checked = selected;
    });
    const page = document.querySelector('.gallery-page-container');
    if (page) page.classList.toggle('selection-mode', state.selection);
    const toggle = $('selectionToggle');
    if (toggle) {
      toggle.classList.toggle('active', state.selection);
      toggle.setAttribute('aria-pressed', state.selection);
      const label = toggle.querySelector('span');
      if (label) label.textContent = state.selection ? 'Selection Active' : 'Select Mode';
    }

    const selectedCount = state.selected.size;
    const selectionText = selectedCount ? selectedCount + ' selected' : 'No selection';
    const selectionPill = $('galleryStateSelection');
    if (selectionPill) {
      selectionPill.textContent = selectionText;
      selectionPill.classList.toggle('is-selected', selectedCount > 0);
    }

    const floatingBar = $('galleryFloatingActionBar');
    if (floatingBar) floatingBar.classList.toggle('active', state.selected.size > 0);
    const floatingCount = $('floatingSelectedCount');
    if (floatingCount) floatingCount.textContent = selectionText;
    const floatingRemoveBtn = $('floatingRemoveBtn');
    if (floatingRemoveBtn) floatingRemoveBtn.hidden = !state.filter.startsWith('group:');
  }
  function toggleFavorite(name) {
    if (favorites.has(name)) favorites.delete(name); else favorites.add(name);
    storage.set('gallery-favorites', JSON.stringify([...favorites]));
    document.querySelectorAll('.gallery-item').forEach(card => {
      const active = favorites.has(card.dataset.image), control = card.querySelector('.image-fav-btn');
      control.classList.toggle('active', active); control.setAttribute('aria-pressed', active);
    });
    if (state.filter === 'favorites' || state.sort === 'favorites-first') filter(false);
    $('lightboxFavBtn').classList.toggle('active', favorites.has(state.image));
    $('lightboxFavBtn').setAttribute('aria-pressed', favorites.has(state.image));
  }
  function renderGroups() {
    const query = $('groupSearch').value.toLowerCase();
    const grid = $('groupsGrid');
    grid.replaceChildren();
    for (const group of state.groups.filter(g => g.name.toLowerCase().includes(query))) {
      const row = document.createElement('article'); row.className = 'group-card';
      row.dataset.groupId = String(group.id);

      const collage = document.createElement('div'); collage.className = 'group-collage';
      const collageGrid = document.createElement('div');
      collageGrid.className = 'group-collage-grid count-' + Math.min(4, Math.max(1, group.preview_images.length || 1));

      const previewNames = group.preview_images.slice(0, 4);
      if (!previewNames.length) {
        const empty = document.createElement('div'); empty.className = 'group-collage-empty'; empty.innerHTML = '<i class="fas fa-folder-open"></i>';
        collage.append(empty);
      } else {
        previewNames.forEach(name => {
          const item = document.createElement('div'); item.className = 'collage-item';
          const img = document.createElement('img'); img.alt = name; img.loading = 'lazy'; img.width = 160; img.height = 160;
          loadImage(img, name, 160);
          item.append(img);
          collageGrid.append(item);
        });
        collage.append(collageGrid);
      }

      const badge = document.createElement('span'); badge.className = 'group-cover-badge'; badge.textContent = group.image_count + ' items';
      collage.append(badge);

      const info = document.createElement('div'); info.className = 'group-card-info';
      const heading = document.createElement('div'); heading.className = 'group-card-heading';
      const title = document.createElement('h3'); title.className = 'group-card-title'; title.textContent = group.name;
      const count = document.createElement('span'); count.className = 'group-card-count'; count.textContent = group.image_count + ' images';
      heading.append(title, count);

      const actions = document.createElement('div'); actions.className = 'group-card-actions';
      const open = button('Open', () => {
        state.filter = 'group:' + group.id; filter(); if ($('groupsDrawer')) $('groupsDrawer').close();
      }, 'group-card-action primary');
      const manage = button('Manage', () => manageGroup(group), 'group-card-action');
      actions.append(open, manage);

      info.append(heading, actions);
      row.append(collage, info);
      grid.append(row);
    }
    if (!state.groups.length) {
      const empty = document.createElement('div');
      empty.className = 'gallery-empty-state';
      empty.innerHTML = `
        <div class="gallery-empty-state__icon"><i class="fas fa-folder-plus"></i></div>
        <div>
          <h3>No groups yet</h3>
          <p>Create a group or select images to start organizing your collection.</p>
        </div>
        <button type="button" class="gallery-btn-pill" id="galleryCreateGroupEmptyBtn">Create group</button>
      `;
      empty.querySelector('#galleryCreateGroupEmptyBtn').addEventListener('click', () => createGroup());
      grid.append(empty);
    }
  }
  function populateGroups() {
    const query = $('destinationSearch').value.toLowerCase();
    for (const id of ['floatingGroupSelect', 'inspectorGroupSelect']) {
      const select = $(id), value = select.value;
      select.innerHTML = '<option value="">Choose group…</option>';
      state.groups.filter(g => id !== 'floatingGroupSelect' || g.name.toLowerCase().includes(query)).forEach(group => {
        const option = document.createElement('option'); option.value = group.id; option.textContent = group.name;
        select.append(option);
      });
      select.value = value;
    }
  }
  async function mutate(action, success = 'Saved') {
    if (state.busy) return false;
    state.busy = true;
    document.querySelectorAll('#galleryActionDialog button, .gallery-floating-action-bar button, #inspectorAddGroupBtn, #inspectorCreateGroupBtn').forEach(b => b.disabled = true);
    try { await action(); await load(); status(success); return true; }
    catch (error) { status(error.message, true); const errorBox = $('galleryDialogError'); if (errorBox) errorBox.textContent = error.message; return false; }
    finally {
      state.busy = false;
      document.querySelectorAll('#galleryActionDialog button, .gallery-floating-action-bar button, #inspectorAddGroupBtn, #inspectorCreateGroupBtn').forEach(b => b.disabled = false);
    }
  }
  function dialog(title, body, submit, label = 'Save') {
    const modal = $('galleryActionDialog');
    modal.innerHTML = '<form><h2 id="galleryDialogTitle">' + html(title) + '</h2>' + body +
      '<p id="galleryDialogError" role="alert"></p><div class="dialog-actions"><button type="button" data-cancel>Cancel</button>' +
      '<button type="submit">' + html(label) + '</button></div></form>';
    modal.querySelector('[data-cancel]').onclick = () => modal.close();
    modal.querySelector('form').onsubmit = async event => { event.preventDefault(); if (await submit(new FormData(event.target))) modal.close(); };
    modal.showModal();
  }
  function createGroup(images = [...state.selected], similar = null) {
    dialog(similar ? 'Group similar images' : 'New group',
      '<label for="groupNameInput">Group name</label><input id="groupNameInput" name="name" maxlength="160" required autofocus>',
      form => mutate(() => api(similar ? '/api/gallery/groups/similar' : '/api/gallery/groups', {
        method: 'POST', body: JSON.stringify(similar ? {name: form.get('name'), filename: similar, limit: 16} : {name: form.get('name'), images})
      }), 'Group created'));
  }
  function manageGroup(group) {
    dialog('Manage ' + group.name,
      '<label for="groupNameInput">Group name</label><input id="groupNameInput" name="name" maxlength="160" required value="' + html(group.name) + '">' +
      '<label for="groupCoverInput">Cover image</label><select id="groupCoverInput" name="cover_image"><option value="">Keep automatic cover</option>' +
      group.image_paths.map(name => '<option value="' + html(name) + '"' + (name === group.cover_image ? ' selected' : '') + '>' + html(name) + '</option>').join('') +
      '</select><button type="button" id="deleteOrganizedGroup">Delete group…</button>',
      form => mutate(() => api('/api/gallery/groups/' + group.id, {method: 'PUT', body: JSON.stringify(Object.fromEntries(form))})));
    $('deleteOrganizedGroup').onclick = () => {
      $('galleryActionDialog').close();
      dialog('Delete ' + group.name + '?', '<p>Only this group and its memberships will be removed. Original images remain untouched.</p>',
        () => mutate(() => api('/api/gallery/groups/' + group.id, {method: 'DELETE'}), 'Group deleted'), 'Delete group');
    };
  }
  async function addImages(group, images) {
    if (!group) { status('Choose a destination group first.', true); return; }
    await mutate(() => api('/api/gallery/groups/' + group + '/images', {method: 'POST', body: JSON.stringify({images})}));
  }
  function fit() { state.zoom = 1; state.panX = state.panY = 0; transform(); }
  function transform() {
    const image = $('lightboxImg');
    image.style.transform = 'translate(' + state.panX + 'px,' + state.panY + 'px) scale(' + state.zoom + ')';
    $('lightboxImageWrapper').classList.toggle('zoomed', state.zoom > 1);
    image.style.cursor = state.zoom > 1 ? 'grab' : 'zoom-in';
  }
  function openViewer(name, source) {
    opener = source; state.image = name;
    $('galleryLightbox').showModal(); $('galleryLightbox').classList.add('active');
    document.body.style.overflow = 'hidden'; renderViewer();
    $('lightboxCloseBtn').focus();
  }
  function closeViewer() { $('galleryLightbox').close(); }
  function move(delta) {
    if (!state.filtered.length) return closeViewer();
    const index = state.filtered.indexOf(state.image);
    state.image = state.filtered[(index + delta + state.filtered.length) % state.filtered.length]; renderViewer();
  }
  function galleryContextLabel() {
    if (state.filter.startsWith('group:')) {
      const match = state.groups.find(group => 'group:' + group.id === state.filter);
      return match ? 'Group • ' + match.name : 'Group view';
    }
    const labels = {
      all: 'All images',
      favorites: 'Favorites',
      grouped: 'Grouped',
      ungrouped: 'Ungrouped',
      motion: 'Motion',
      jpg: 'JPG',
      png: 'PNG',
      webp: 'WebP',
      gif: 'GIF'
    };
    const cleanFilter = labels[state.filter] || (state.filter || 'All images').replace(/[-_]+/g, ' ');
    return state.query.trim() ? cleanFilter + ' • search: ' + state.query.trim() : cleanFilter;
  }
  function renderViewer() {
    const name = state.image, meta = state.meta[name] || {};
    state.original = false; fit();
    const image = $('lightboxImg'); image.alt = name;
    loadImage(image, name, 1280, failed => $('lightboxRetryBtn').hidden = !failed);
    $('lightboxFilename').textContent = name;
    $('lightboxContextBadge').textContent = galleryContextLabel();
    $('lightboxIndexBadge').textContent = (state.filtered.indexOf(name) + 1) + ' / ' + state.filtered.length;
    $('lightboxAnimationBtn').hidden = !meta.animated;
    $('lightboxOriginalBtn').textContent = 'Original resolution';
    $('lightboxFavBtn').classList.toggle('active', favorites.has(name));
    $('lightboxFavBtn').setAttribute('aria-pressed', favorites.has(name));
    renderInspector(); renderFilmstrip(); syncViewer();
  }
  function renderInspector() {
    const name = state.image, meta = state.meta[name] || {};
    $('inspectorFilename').textContent = name;
    $('inspectorFormat').textContent = (meta.format || '').toUpperCase() + (meta.animated ? ' · animated' : '');
    $('inspectorDimensions').textContent = meta.width + ' × ' + meta.height + ' px';
    const groups = state.groups.filter(g => g.image_paths.includes(name));
    $('inspectorGroupsList').replaceChildren();
    groups.forEach(group => {
      const tag = document.createElement('span'); tag.className = 'inspector-group-tag'; tag.textContent = group.name;
      const remove = button('Remove', () => mutate(() => api('/api/gallery/groups/' + group.id + '/images/' + encodeURIComponent(name), {method: 'DELETE'})));
      remove.setAttribute('aria-label', 'Remove from ' + group.name); tag.append(remove); $('inspectorGroupsList').append(tag);
    });
    if (!groups.length) $('inspectorGroupsList').textContent = 'No groups';
  }
  function renderFilmstrip() {
    const index = state.filtered.indexOf(state.image), track = $('lightboxFilmstripTrack');
    track.replaceChildren();
    state.filtered.slice(Math.max(0,index - 20), index + 21).forEach(name => {
      const control = button('', () => { state.image = name; renderViewer(); }, 'filmstrip-thumb');
      control.setAttribute('aria-label', 'View ' + name); control.setAttribute('aria-current', String(name === state.image));
      control.classList.toggle('active', name === state.image);
      const img = document.createElement('img'); img.alt = ''; img.loading = 'lazy'; loadImage(img, name, 160);
      control.append(img); track.append(control);
    });
    track.querySelector('[aria-current="true"]')?.scrollIntoView({block: 'nearest', inline: 'center'});
  }
  function syncViewer() {
    $('lightboxInspector').classList.toggle('collapsed', !state.inspector);
    $('lightboxInspector').inert = !state.inspector;
    $('lightboxInspectorBtn').setAttribute('aria-expanded', state.inspector);
    $('lightboxFilmstripTray').classList.toggle('collapsed', !state.filmstrip);
    $('lightboxFilmstripTrack').inert = !state.filmstrip;
    $('lightboxFilmstripToggleBtn').setAttribute('aria-expanded', state.filmstrip);
  }
  async function showOriginal(pixelSize = false) {
    const name = state.image, image = $('lightboxImg');
    image.dataset.request = String(Number(image.dataset.request || 0) + 1);
    state.original = true; image.onerror = () => $('lightboxRetryBtn').hidden = false;
    image.onload = () => {
      $('lightboxRetryBtn').hidden = true;
      if (pixelSize && state.image === name) {
        state.zoom = Math.max(1, image.naturalWidth / image.clientWidth); transform();
      }
    };
    image.src = original(name); $('lightboxOriginalBtn').textContent = 'Original loaded';
  }
  function bind() {
    const on = (id, action) => $(id)?.addEventListener('click', action);
    document.querySelectorAll('[data-view-mode], [data-density]').forEach(control => {
      control.onclick = () => {
        if (control.dataset.viewMode) { state.view = control.dataset.viewMode; storage.set('gallery.viewMode', state.view); }
        else { state.density = control.dataset.density; storage.set('gallery.density', state.density); }
        syncControls(); scheduleGridRender();
      };
    });
    document.querySelectorAll('[data-filter-pill]').forEach(control => control.onclick = () => { state.filter = control.dataset.filterPill; filter(); });
    let searchTimer;
    const gallerySearchInput = $('gallerySearchInput');
    if (gallerySearchInput) {
      gallerySearchInput.oninput = event => {
        clearTimeout(searchTimer); state.query = event.target.value; searchTimer = setTimeout(() => filter(), 120);
      };
    }
    const gallerySortSelect = $('gallerySortSelect');
    if (gallerySortSelect) {
      gallerySortSelect.onchange = event => { state.sort = event.target.value; filter(); };
    }
    on('gallerySearchClear', () => { state.query = ''; if ($('gallerySearchInput')) $('gallerySearchInput').value = ''; filter(); });
    on('resetGalleryFilters', () => { state.filter = 'all'; state.query = ''; if ($('gallerySearchInput')) $('gallerySearchInput').value = ''; filter(); });
    const selectionToggle = $('selectionToggle');
    if (selectionToggle) {
      selectionToggle.addEventListener('click', () => {
        state.selection = !state.selection;
        if (!state.selection) state.selected.clear();
        syncSelection();
      });
      selectionToggle.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          selectionToggle.click();
        }
      });
    }
    on('selectLoadedBtn', () => { state.filtered.slice(0,state.limit).forEach(n => state.selected.add(n)); state.selection = true; syncSelection(); });
    on('selectMatchingBtn', () => { state.filtered.forEach(n => state.selected.add(n)); state.selection = true; syncSelection(); });
    on('floatingClearBtn', () => { state.selection = false; state.selected.clear(); syncSelection(); });
    on('floatingFavBtn', () => { state.selected.forEach(n => favorites.add(n)); storage.set('gallery-favorites', JSON.stringify([...favorites])); renderGrid(); });
    on('floatingAddToGroupBtn', () => addImages($('floatingGroupSelect').value, [...state.selected]));
    on('floatingCreateGroupBtn', () => createGroup());
    on('createEmptyGroupBtn', () => createGroup([]));
    on('floatingSimilarBtn', () => createGroup([], [...state.selected][0]));
    on('floatingRemoveBtn', () => dialog('Remove selected images?', '<p>Remove selected images from this group only. Original files are kept.</p>',
      () => mutate(() => api('/api/gallery/groups/' + state.filter.slice(6) + '/images/remove', {
        method: 'POST', body: JSON.stringify({images: [...state.selected]})
      })), 'Remove'));
    const groupSearchInput = $('groupSearch');
    if (groupSearchInput) groupSearchInput.oninput = renderGroups;
    const destinationSearchInput = $('destinationSearch');
    if (destinationSearchInput) destinationSearchInput.oninput = populateGroups;
    on('refreshGroupsBtn', async () => {
      $('refreshGroupsBtn').disabled = true;
      try { await api('/api/gallery/refresh', {method: 'POST'}); await load(); }
      catch (error) { status(error.message, true); }
      finally { $('refreshGroupsBtn').disabled = false; }
    });
    on('openGroupsBtn', () => { $('groupsDrawer').append($('groupsSection')); $('groupsDrawer').showModal(); });
    on('closeGroupsBtn', () => $('groupsDrawer').close());
    $('groupsDrawer').onclose = () => document.querySelector('.gallery-workspace').prepend($('groupsSection'));
    matchMedia('(min-width: 992px)').addEventListener('change', event => { if (event.matches) $('groupsDrawer').close(); });
    on('lightboxCloseBtn', closeViewer);
    $('galleryLightbox').addEventListener('close', () => {
      clearInterval(slideTimer); slideTimer = null; $('lightboxSlideshowBtn').textContent = 'Slideshow';
      $('galleryLightbox').classList.remove('active'); document.body.style.overflow = ''; state.image = null;
      const image = $('lightboxImg'); image.onload = image.onerror = null; image.removeAttribute('src'); image.dataset.source = '';
      (opener?.isConnected ? opener : $('gallerySearchInput')).focus({preventScroll: true});
    });
    on('lightboxPrevBtn', () => move(-1)); on('lightboxNextBtn', () => move(1));
    on('lightboxFavBtn', () => toggleFavorite(state.image));
    on('lightboxInspectorBtn', () => { state.inspector = !state.inspector; storage.set('gallery.inspector', state.inspector); syncViewer(); });
    on('lightboxFilmstripToggleBtn', () => { state.filmstrip = !state.filmstrip; storage.set('gallery.filmstrip', state.filmstrip); syncViewer(); });
    on('lightboxOriginalBtn', () => showOriginal()); on('lightboxAnimationBtn', () => showOriginal());
    on('lightboxRetryBtn', () => state.original ? showOriginal() : renderViewer());
    on('lightboxZoom100Btn', () => showOriginal(true));
    on('lightboxZoomFitBtn', fit);
    on('lightboxZoomInBtn', () => { state.zoom = Math.min(12,state.zoom + .5); transform(); });
    on('lightboxZoomOutBtn', () => { state.zoom = Math.max(1,state.zoom - .5); transform(); });
    on('lightboxSlideshowBtn', () => {
      if (slideTimer) { clearInterval(slideTimer); slideTimer = null; }
      else slideTimer = setInterval(() => move(1), 3200);
      $('lightboxSlideshowBtn').textContent = slideTimer ? 'Pause slideshow' : 'Slideshow';
    });
    on('inspectorAddGroupBtn', () => addImages($('inspectorGroupSelect').value, [state.image]));
    on('inspectorCreateGroupBtn', () => mutate(() => api('/api/gallery/groups', {
      method: 'POST', body: JSON.stringify({name: $('inspectorNewGroupName').value, images: [state.image]})
    })));
    on('inspectorSimilarBtn', () => createGroup([], state.image));
    const image = $('lightboxImg'); let drag;
    if (image) {
      image.onclick = () => {
        if (!state.image) return;
        if (state.zoom <= 1) {
          state.zoom = 2;
          transform();
        } else {
          fit();
        }
      };
      image.onpointerdown = event => {
        if (state.zoom <= 1) return;
        image.setPointerCapture(event.pointerId); drag = [event.clientX - state.panX, event.clientY - state.panY];
      };
      image.onpointermove = event => { if (drag) { state.panX = event.clientX - drag[0]; state.panY = event.clientY - drag[1]; transform(); } };
      image.onpointerup = image.onpointercancel = () => drag = null;
      image.ondblclick = () => state.zoom > 1 ? fit() : showOriginal(true);
    }
    document.addEventListener('keydown', event => {
      const target = event.target instanceof Element ? event.target : document.activeElement;
      if (!$('galleryLightbox').open || $('galleryActionDialog').open || (target instanceof Element && target.closest('input,textarea,select,[contenteditable]'))) return;
      const key = event.key.toLowerCase();
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') { event.preventDefault(); move(event.key === 'ArrowLeft' ? -1 : 1); }
      if (key === 'f') { event.preventDefault(); toggleFavorite(state.image); }
      if (key === 'i') { event.preventDefault(); state.inspector = !state.inspector; storage.set('gallery.inspector', state.inspector); syncViewer(); }
      if (event.key === 'Escape') { event.preventDefault(); closeViewer(); }
      if (key === 's') { event.preventDefault(); createGroup([], state.image); }
      if (event.key === '0') { event.preventDefault(); fit(); }
      if (event.key === '1') { event.preventDefault(); showOriginal(true); }
    });
    window.addEventListener('popstate', () => { readURL(state.initialGroup); filter(false); });
    document.addEventListener('visibilitychange', () => { if (!document.hidden) load(); });
  }
  function syncControls() {
    document.querySelectorAll('[data-view-mode], [data-density]').forEach(control => {
      const active = control.dataset.viewMode === state.view || control.dataset.density === state.density;
      control.classList.toggle('active', active); control.setAttribute('aria-pressed', active);
    });
  }
  window.initGallery = async initialGroup => {
    state.initialGroup = initialGroup;
    if (!['masonry','uniform'].includes(state.view)) state.view = 'masonry';
    if (!['compact','medium','showcase'].includes(state.density)) state.density = 'medium';
    readURL(initialGroup); bind(); syncControls(); status('Loading library…'); await load();
  };
})();
