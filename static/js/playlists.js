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
                    fetchAndRenderPlaylists(); // Refresh list
                } else {
                    showToast(data.error || 'Failed to create playlist', 'error');
                }
            } catch (err) {
                showToast('Connection error', 'error');
            }
        });
    }
});
