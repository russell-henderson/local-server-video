/**
 * static/js/playlists.js
 * Frontend controller for video playlists management.
 * Handles async playlist selection and assignment via glassmorphic modal.
 */

document.addEventListener('DOMContentLoaded', () => {
    const modalOverlay = document.getElementById('playlist-modal-overlay');
    const modalClose = document.getElementById('playlist-modal-close');
    const playlistListContainer = document.getElementById('playlist-list-container');
    const createPlaylistBtn = document.getElementById('btn-create-playlist');
    
    let currentVideoFilename = null;

    // Toast Notification System
    const toastContainer = document.createElement('div');
    toastContainer.className = 'playlist-toast-container';
    document.body.appendChild(toastContainer);

    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `playlist-toast ${type}`;
        const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
        toast.innerHTML = `<i class="fas ${icon}"></i> <span>${message}</span>`;
        
        toastContainer.appendChild(toast);
        
        // Trigger reflow for animation
        setTimeout(() => toast.classList.add('active'), 10);
        
        setTimeout(() => {
            toast.classList.remove('active');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, (ch) => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }[ch]));
    }

    // Modal Control Logic
    function openPlaylistModal() {
        modalOverlay.classList.add('active');
        fetchAndRenderPlaylists();
    }

    function closePlaylistModal() {
        modalOverlay.classList.remove('active');
        currentVideoFilename = null;
    }

    // Global listener for "Add to Playlist" buttons
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.playlist-add-btn');
        if (btn) {
            e.preventDefault();
            e.stopPropagation();
            currentVideoFilename = btn.dataset.filename;
            if (currentVideoFilename) {
                openPlaylistModal();
            }
        }
    });

    if (modalClose) modalClose.addEventListener('click', closePlaylistModal);
    if (modalOverlay) {
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) closePlaylistModal();
        });
    }

    // Playlist API Operations
    async function fetchAndRenderPlaylists() {
        playlistListContainer.innerHTML = `
            <div class="text-center p-5 subtle-text">
                <i class="fas fa-spinner fa-spin fa-2x mb-3"></i>
                <p>Loading your collections...</p>
            </div>
        `;
        
        try {
            const response = await fetch('/api/playlists');
            const data = await response.json();
            
            if (data.success) {
                renderPlaylistItems(data.playlists);
            } else {
                playlistListContainer.innerHTML = `
                    <div class="text-danger p-4 text-center">
                        <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                        <p>${data.error || 'Failed to load playlists'}</p>
                    </div>`;
            }
        } catch (err) {
            console.error('Playlist Fetch Error:', err);
            playlistListContainer.innerHTML = '<div class="text-danger p-4 text-center">Connection error</div>';
        }
    }

    function renderPlaylistItems(playlists) {
        if (playlists.length === 0) {
            playlistListContainer.innerHTML = `
                <div class="text-center p-5 subtle-text">
                    <i class="fas fa-folder-open fa-2x mb-3" style="opacity:0.3"></i>
                    <p>You haven't created any playlists yet.</p>
                </div>`;
            return;
        }

        const list = document.createElement('ul');
        list.className = 'playlist-list';

        playlists.forEach(p => {
            const item = document.createElement('li');
            item.className = 'playlist-item';
            item.dataset.id = p.id;
            
            const dateStr = p.created_at ? p.created_at.split(' ')[0] : 'Recently';
            
            item.innerHTML = `
                <i class="fas fa-list-ul"></i>
                <span class="playlist-item-name">${p.name}</span>
                <span class="playlist-item-meta">${dateStr}</span>
            `;
            
            item.addEventListener('click', () => assignVideoToPlaylist(p.id, p.name));
            list.appendChild(item);
        });

        playlistListContainer.innerHTML = '';
        playlistListContainer.appendChild(list);
    }

    async function assignVideoToPlaylist(playlistId, playlistName) {
        if (!currentVideoFilename) return;

        try {
            const response = await fetch(`/api/playlists/${playlistId}/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ video_filename: currentVideoFilename })
            });
            const data = await response.json();

            if (data.success) {
                showToast(`Added to "${playlistName}"`, 'success');
                closePlaylistModal();
            } else {
                showToast(data.error || 'Failed to add video', 'error');
            }
        } catch (err) {
            console.error('Add to Playlist Error:', err);
            showToast('Connection error', 'error');
        }
    }

    // Create New Playlist Interaction
    if (createPlaylistBtn) {
        createPlaylistBtn.addEventListener('click', async () => {
            const name = prompt("Enter new playlist name:");
            if (!name || name.trim() === "") return;

            try {
                const response = await fetch('/api/playlists', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name.trim() })
                });
                const data = await response.json();

                if (data.success) {
                    showToast(`Playlist "${name}" created!`, 'success');
                    if (!currentVideoFilename && document.querySelector('[data-playlists-dashboard]')) {
                        setTimeout(() => location.reload(), 350);
                        return;
                    }
                    fetchAndRenderPlaylists(); // Refresh list
                } else {
                    showToast(data.error || 'Failed to create playlist', 'error');
                }
            } catch (err) {
                showToast('Connection error', 'error');
            }
        });
    }

    initPlaylistPage();

    function initPlaylistPage() {
        const dashboard = document.querySelector('[data-playlists-dashboard]');
        if (!dashboard) return;

        initPlaylistTools(dashboard);
        initPlaylistSearch(dashboard);
        initPlaylistSort(dashboard);
        initPlaylistEditMode(dashboard);
        initPlaylistEditModal(dashboard);
    }

    function initPlaylistTools(dashboard) {
        const compactToggle = document.getElementById('playlist-compact-toggle');
        const exportBtn = document.getElementById('playlist-export-json');
        const compactKey = 'localVideoServer.playlists.compactCards';

        if (compactToggle) {
            const enabled = localStorage.getItem(compactKey) === 'true';
            compactToggle.checked = enabled;
            dashboard.classList.toggle('playlist-compact', enabled);
            compactToggle.addEventListener('change', () => {
                localStorage.setItem(compactKey, compactToggle.checked ? 'true' : 'false');
                dashboard.classList.toggle('playlist-compact', compactToggle.checked);
            });
        }

        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                const cards = getPlaylistCards().map(card => cardToMetadata(card));
                const blob = new Blob([JSON.stringify({ playlists: cards }, null, 2)], {
                    type: 'application/json'
                });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'playlists-export.json';
                link.click();
                URL.revokeObjectURL(url);
            });
        }
    }

    function initPlaylistSearch() {
        const input = document.getElementById('playlist-search');
        if (!input) return;
        input.addEventListener('input', () => {
            const query = input.value.trim().toLowerCase();
            getPlaylistCards().forEach(card => {
                const text = `${card.dataset.name || ''} ${card.dataset.description || ''}`.toLowerCase();
                card.hidden = query && !text.includes(query);
            });
        });
    }

    function initPlaylistSort() {
        const select = document.getElementById('playlist-sort');
        const grid = document.getElementById('playlist-grid');
        const sortKey = 'localVideoServer.playlists.sortMode';
        if (!select || !grid) return;

        const saved = localStorage.getItem(sortKey);
        if (saved) select.value = saved;
        const applySort = () => {
            localStorage.setItem(sortKey, select.value);
            const cards = getPlaylistCards();
            cards.sort((a, b) => comparePlaylistCards(a, b, select.value));
            cards.forEach(card => grid.appendChild(card));
        };
        select.addEventListener('change', applySort);
        applySort();
    }

    function initPlaylistEditMode(dashboard) {
        const toggle = document.getElementById('playlist-edit-mode-toggle');
        const editKey = 'localVideoServer.playlists.editMode';
        if (!toggle) return;
        const enabled = localStorage.getItem(editKey) === 'true';
        toggle.checked = enabled;
        dashboard.classList.toggle('playlist-edit-mode', enabled);
        toggle.addEventListener('change', () => {
            localStorage.setItem(editKey, toggle.checked ? 'true' : 'false');
            dashboard.classList.toggle('playlist-edit-mode', toggle.checked);
        });
    }

    function initPlaylistEditModal() {
        const overlay = document.getElementById('playlist-edit-modal-overlay');
        const form = document.getElementById('playlist-edit-form');
        const closeBtn = document.getElementById('playlist-edit-modal-close');
        const cancelBtn = document.getElementById('playlist-edit-cancel');
        const removeCoverBtn = document.getElementById('playlist-remove-cover');
        if (!overlay || !form) return;

        document.addEventListener('click', (event) => {
            const editBtn = event.target.closest('[data-action="edit-playlist"], [data-action="edit-cover"]');
            if (!editBtn) return;
            event.preventDefault();
            openPlaylistEditModal(editBtn.dataset.playlistId);
        });

        const close = () => {
            overlay.classList.remove('active');
            overlay.setAttribute('aria-hidden', 'true');
            setEditError('');
            form.reset();
        };
        closeBtn?.addEventListener('click', close);
        cancelBtn?.addEventListener('click', close);
        overlay.addEventListener('click', (event) => {
            if (event.target === overlay) close();
        });

        removeCoverBtn?.addEventListener('click', async () => {
            const id = document.getElementById('playlist-edit-id').value;
            if (!id) return;
            const result = await deletePlaylistCover(id);
            if (result?.success && result.playlist) {
                updatePlaylistCard(result.playlist);
                showToast('Cover removed', 'success');
            } else {
                setEditError(result?.error || 'Failed to remove cover');
            }
        });

        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            setEditError('');
            const playlistId = document.getElementById('playlist-edit-id').value;
            const payload = collectPlaylistMetadataForm();
            if (!payload.name.trim()) {
                setEditError('Playlist name is required.');
                return;
            }
            if (payload.description.length > 500) {
                setEditError('Description must be 500 characters or less.');
                return;
            }
            if (payload.spotlight_label.length > 80) {
                setEditError('Spotlight label must be 80 characters or less.');
                return;
            }

            const metadata = await savePlaylistMetadata(playlistId, payload);
            if (!metadata?.success) {
                setEditError(metadata?.error || 'Failed to save playlist');
                return;
            }
            updatePlaylistCard(metadata);

            const coverInput = document.getElementById('playlist-edit-cover');
            if (coverInput.files && coverInput.files[0]) {
                const coverResult = await uploadPlaylistCover(playlistId, coverInput.files[0]);
                if (!coverResult?.success) {
                    setEditError(coverResult?.error || 'Metadata saved, but cover upload failed.');
                    return;
                }
                if (coverResult.playlist) updatePlaylistCard(coverResult.playlist);
            }

            showToast('Playlist updated', 'success');
            close();
        });
    }

    function getPlaylistCards() {
        return Array.from(document.querySelectorAll('.playlist-card[data-playlist-id]'));
    }

    function comparePlaylistCards(a, b, mode) {
        if (mode === 'count') {
            return Number(b.dataset.count || 0) - Number(a.dataset.count || 0);
        }
        if (mode === 'created') {
            return String(b.dataset.created || '').localeCompare(String(a.dataset.created || ''));
        }
        if (mode === 'last_opened') {
            return String(b.dataset.lastOpened || '').localeCompare(String(a.dataset.lastOpened || ''));
        }
        return String(a.dataset.name || '').localeCompare(String(b.dataset.name || ''));
    }

    function cardToMetadata(card) {
        return {
            id: Number(card.dataset.playlistId),
            name: card.dataset.name || '',
            description: card.dataset.description || '',
            item_count: Number(card.dataset.count || 0),
            created_at: card.dataset.created || null,
            cover_image: card.dataset.cover || null,
            spotlight_label: card.dataset.spotlightLabel || '',
            spotlight_action: card.dataset.spotlightAction || 'continue',
            spotlight_enabled: card.dataset.spotlightEnabled !== 'false',
            sort_mode: card.dataset.sortMode || 'manual',
            autoplay_next: card.dataset.autoplayNext === 'true',
            shuffle_default: card.dataset.shuffleDefault === 'true',
            last_opened_at: card.dataset.lastOpened || null
        };
    }

    function openPlaylistEditModal(playlistId) {
        const card = document.getElementById(`playlist-${playlistId}`);
        const overlay = document.getElementById('playlist-edit-modal-overlay');
        if (!card || !overlay) return;
        const data = cardToMetadata(card);
        document.getElementById('playlist-edit-id').value = data.id;
        document.getElementById('playlist-edit-name').value = data.name;
        document.getElementById('playlist-edit-description').value =
            data.description === 'No description provided.' ? '' : data.description;
        document.getElementById('playlist-edit-spotlight-enabled').checked = data.spotlight_enabled;
        document.getElementById('playlist-edit-spotlight-label').value = data.spotlight_label;
        document.getElementById('playlist-edit-spotlight-action').value = data.spotlight_action;
        document.getElementById('playlist-edit-sort-mode').value = data.sort_mode;
        document.getElementById('playlist-edit-shuffle-default').checked = data.shuffle_default;
        document.getElementById('playlist-edit-autoplay-next').checked = data.autoplay_next;
        document.getElementById('playlist-edit-cover').value = '';
        overlay.classList.add('active');
        overlay.setAttribute('aria-hidden', 'false');
        document.getElementById('playlist-edit-name').focus();
    }

    function collectPlaylistMetadataForm() {
        return {
            name: document.getElementById('playlist-edit-name').value.trim(),
            description: document.getElementById('playlist-edit-description').value.trim(),
            spotlight_enabled: document.getElementById('playlist-edit-spotlight-enabled').checked,
            spotlight_label: document.getElementById('playlist-edit-spotlight-label').value.trim(),
            spotlight_action: document.getElementById('playlist-edit-spotlight-action').value,
            sort_mode: document.getElementById('playlist-edit-sort-mode').value,
            shuffle_default: document.getElementById('playlist-edit-shuffle-default').checked,
            autoplay_next: document.getElementById('playlist-edit-autoplay-next').checked
        };
    }

    async function savePlaylistMetadata(playlistId, payload) {
        const response = await fetch(`/api/playlists/${playlistId}/metadata`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return response.json();
    }

    async function uploadPlaylistCover(playlistId, file) {
        const formData = new FormData();
        formData.append('cover', file);
        const response = await fetch(`/api/playlists/${playlistId}/cover`, {
            method: 'POST',
            body: formData
        });
        return response.json();
    }

    async function deletePlaylistCover(playlistId) {
        const response = await fetch(`/api/playlists/${playlistId}/cover`, {
            method: 'DELETE'
        });
        return response.json();
    }

    function updatePlaylistCard(playlist) {
        const card = document.getElementById(`playlist-${playlist.id}`);
        if (!card) return;
        const description = playlist.description || 'No description provided.';
        const spotlightLabel = playlist.spotlight_label || 'Open playlist';
        const spotlightAction = playlist.spotlight_action || 'continue';
        const coverImage = playlist.cover_image || '';

        card.dataset.name = playlist.name || '';
        card.dataset.description = description;
        card.dataset.cover = coverImage;
        card.dataset.spotlightLabel = playlist.spotlight_label || '';
        card.dataset.spotlightAction = spotlightAction;
        card.dataset.spotlightEnabled = playlist.spotlight_enabled ? 'true' : 'false';
        card.dataset.sortMode = playlist.sort_mode || 'manual';
        card.dataset.autoplayNext = playlist.autoplay_next ? 'true' : 'false';
        card.dataset.shuffleDefault = playlist.shuffle_default ? 'true' : 'false';
        card.dataset.lastOpened = playlist.last_opened_at || '';

        const title = card.querySelector('.playlist-title');
        const desc = card.querySelector('.playlist-desc');
        if (title) title.textContent = playlist.name || '';
        if (desc) desc.textContent = description;

        const cover = card.querySelector('.playlist-cover');
        if (cover) {
            cover.innerHTML = coverImage
                ? `<img src="${escapeHtml(coverImage)}" alt="Cover image for ${escapeHtml(playlist.name || 'playlist')}">`
                : `<div class="playlist-cover-fallback" aria-hidden="true"><span>${escapeHtml((playlist.name || '?').slice(0, 1))}</span></div>`;
            const button = document.createElement('button');
            button.className = 'playlist-cover-edit';
            button.type = 'button';
            button.dataset.action = 'edit-cover';
            button.dataset.playlistId = playlist.id;
            button.textContent = 'Edit';
            cover.appendChild(button);
        }

        const oldSpotlight = card.querySelector('.playlist-spotlight-bar');
        if (oldSpotlight) {
            if (playlist.spotlight_enabled) {
                oldSpotlight.outerHTML = `<a class="playlist-spotlight-bar playlist-editable" href="/playlists/${playlist.id}/quick/${encodeURIComponent(spotlightAction)}"><span>${escapeHtml(spotlightLabel)}</span><i class="fas fa-bolt" aria-hidden="true"></i></a>`;
            } else {
                oldSpotlight.outerHTML = '<div class="playlist-spotlight-bar playlist-spotlight-muted playlist-editable"><span>Spotlight hidden</span></div>';
            }
        }
    }

    function setEditError(message) {
        const error = document.getElementById('playlist-edit-error');
        if (error) error.textContent = message || '';
    }

    window.initPlaylistPage = initPlaylistPage;
    window.initPlaylistTools = initPlaylistTools;
    window.initPlaylistSearch = initPlaylistSearch;
    window.initPlaylistSort = initPlaylistSort;
    window.initPlaylistEditMode = initPlaylistEditMode;
    window.openPlaylistEditModal = openPlaylistEditModal;
    window.collectPlaylistMetadataForm = collectPlaylistMetadataForm;
    window.savePlaylistMetadata = savePlaylistMetadata;
    window.uploadPlaylistCover = uploadPlaylistCover;
    window.deletePlaylistCover = deletePlaylistCover;
    window.updatePlaylistCard = updatePlaylistCard;
    window.showPlaylistToast = showToast;
});
