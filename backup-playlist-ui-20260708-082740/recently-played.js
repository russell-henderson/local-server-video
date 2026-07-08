/**
 * Recently Played Sidebar
 * Tracks and displays recently played videos
 */

class RecentlyPlayed {
  constructor() {
    this.maxItems = 15;
    this.storageKey = "video_server_recently_played";
    this.recentItems = this.loadFromStorage();
    this.init();
  }

  init() {
    this.createSidebar();
    this.attachEvents();
    this.updateDisplay();
    console.log("📺 Recently Played sidebar initialized");
  }

  createSidebar() {
    // Create sidebar HTML structure
    const sidebar = document.createElement("div");
    sidebar.id = "recently-played-sidebar";
    sidebar.className = "recently-played-sidebar";
    sidebar.innerHTML = `
            <div class="recently-played-header">
                <h5 class="recently-played-title">Recently Played</h5>
                <button class="recently-played-toggle" title="Toggle Recently Played">
                    <i class="fas fa-chevron-left"></i>
                </button>
            </div>
            <div class="recently-played-content">
                <div class="recently-played-list" id="recently-played-list">
                    <!-- Items will be populated here -->
                </div>
                <div class="recently-played-actions">
                    <button class="btn btn-sm btn-outline-secondary clear-recent" title="Clear History">
                        <i class="fas fa-trash"></i> Clear
                    </button>
                </div>
            </div>
        `;

    // Insert sidebar into page
    document.body.appendChild(sidebar);
    this.addStyles();
  }

  addStyles() {
    const styles = document.createElement("style");
    styles.textContent = `
            /* Recently Played Sidebar */
            .recently-played-sidebar {
                position: fixed;
                top: 0;
                right: 0;
                width: 320px;
                height: 100vh;
                background: var(--card-background, #fff);
                border-left: 2px solid var(--accent-color, #007bff);
                box-shadow: -4px 0 12px rgba(0, 0, 0, 0.15);
                z-index: 1000;
                transform: translateX(100%);
                transition: transform 0.3s ease;
                display: flex;
                flex-direction: column;
            }

            .recently-played-sidebar.open {
                transform: translateX(0);
            }

            .recently-played-header {
                background: var(--accent-color, #007bff);
                color: white;
                padding: 1rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
                min-height: 60px;
            }

            .recently-played-title {
                margin: 0;
                font-size: 1.1rem;
                font-weight: 600;
            }

            .recently-played-toggle {
                background: none;
                border: none;
                color: white;
                font-size: 1.2rem;
                cursor: pointer;
                padding: 0.5rem;
                border-radius: 4px;
                transition: background 0.2s ease;
            }

            .recently-played-toggle:hover {
                background: rgba(255, 255, 255, 0.2);
            }

            .recently-played-sidebar.open .recently-played-toggle i {
                transform: rotate(180deg);
            }

            .recently-played-content {
                flex: 1;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }

            .recently-played-list {
                flex: 1;
                overflow-y: auto;
                padding: 0.5rem;
            }

            .recently-played-item {
                display: flex;
                align-items: center;
                padding: 0.75rem;
                margin-bottom: 0.5rem;
                background: var(--background-color, #f8f9fa);
                border: 1px solid var(--border-color, #dee2e6);
                border-radius: 6px;
                cursor: pointer;
                transition: all 0.2s ease;
                position: relative;
            }

            .recently-played-item:hover {
                background: var(--accent-color, #007bff);
                color: white;
                transform: translateX(-2px);
                box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.1);
            }



            .recently-played-item.video-item {
                border-left: 4px solid #28a745;
            }

            .recently-played-icon {
                font-size: 1.2rem;
                margin-right: 0.75rem;
                min-width: 24px;
                text-align: center;
            }

            .recently-played-info {
                flex: 1;
                min-width: 0;
            }

            .recently-played-name {
                font-weight: 500;
                font-size: 0.9rem;
                margin-bottom: 0.25rem;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .recently-played-time {
                font-size: 0.75rem;
                opacity: 0.7;
            }

            .recently-played-type {
                position: absolute;
                top: 4px;
                right: 4px;
                font-size: 0.7rem;
                background: rgba(0, 0, 0, 0.1);
                padding: 0.1rem 0.3rem;
                border-radius: 3px;
            }

            .recently-played-actions {
                padding: 1rem;
                border-top: 1px solid var(--border-color, #dee2e6);
                text-align: center;
            }

            .clear-recent {
                width: 100%;
            }

            /* Sidebar trigger button */
            .recently-played-trigger {
                position: fixed;
                top: 50%;
                right: 0;
                transform: translateY(-50%);
                background: var(--accent-color, #007bff);
                color: white;
                border: none;
                padding: 1rem 0.5rem;
                border-radius: 6px 0 0 6px;
                cursor: pointer;
                z-index: 999;
                transition: all 0.3s ease;
                box-shadow: -2px 0 8px rgba(0, 0, 0, 0.2);
            }

            .recently-played-trigger:hover {
                background: var(--accent-hover, #0056b3);
                transform: translateY(-50%) translateX(-2px);
            }

            .recently-played-trigger.hidden {
                transform: translateY(-50%) translateX(100%);
            }

            /* Empty state */
            .recently-played-empty {
                text-align: center;
                padding: 2rem 1rem;
                color: var(--text-muted, #6c757d);
            }

            .recently-played-empty-icon {
                font-size: 2rem;
                margin-bottom: 1rem;
                opacity: 0.5;
            }

            /* Responsive */
            @media (max-width: 768px) {
                .recently-played-sidebar {
                    width: 100%;
                    max-width: 320px;
                }
            }

            /* Dark mode support */
            .dark-mode .recently-played-sidebar {
                background: var(--card-background);
                color: var(--text-color);
            }

            .dark-mode .recently-played-item {
                background: var(--background-color);
                border-color: var(--border-color);
            }

            .dark-mode .recently-played-item:hover {
                background: var(--accent-color);
            }
        `;
    document.head.appendChild(styles);
  }

  attachEvents() {
    // Toggle sidebar
    const toggleBtn = document.querySelector(".recently-played-toggle");
    const sidebar = document.getElementById("recently-played-sidebar");

    toggleBtn.addEventListener("click", () => {
      this.toggleSidebar();
    });

    // Create trigger button
    const trigger = document.createElement("button");
    trigger.className = "recently-played-trigger";
    trigger.innerHTML = '<i class="fas fa-history"></i>';
    trigger.title = "Recently Played";
    trigger.addEventListener("click", () => {
      this.openSidebar();
    });
    document.body.appendChild(trigger);

    // Clear history
    const clearBtn = document.querySelector(".clear-recent");
    clearBtn.addEventListener("click", () => {
      this.clearHistory();
    });

    // Close on outside click
    document.addEventListener("click", (e) => {
      if (!sidebar.contains(e.target) && !trigger.contains(e.target)) {
        if (sidebar.classList.contains("open")) {
          this.closeSidebar();
        }
      }
    });

    // Track video plays
    this.trackVideoPlays();

  }

  trackVideoPlays() {
    // Track regular video plays
    document.addEventListener("click", (e) => {
      const videoLink = e.target.closest('a[href*="/watch/"]');
      if (videoLink) {
        const href = videoLink.getAttribute("href");
        const filename = href.split("/watch/")[1];
        if (filename) {
          this.addItem({
            type: "video",
            name: decodeURIComponent(filename),
            url: href,
            timestamp: Date.now(),
          });
        }
      }
    });

    // Track video.js plays
    document.addEventListener(
      "play",
      (e) => {
        if (e.target.tagName === "VIDEO") {
          const videoSrc = e.target.currentSrc || e.target.src;
          if (videoSrc && videoSrc.includes("/video/")) {
            const filename = videoSrc.split("/video/")[1];
            if (filename) {
              this.addItem({
                type: "video",
                name: decodeURIComponent(filename),
                url: videoSrc,
                timestamp: Date.now(),
              });
            }
          }
        }
      },
      true
    );
  }



  addItem(item) {
    // Remove existing item if it exists
    this.recentItems = this.recentItems.filter(
      (existing) => existing.url !== item.url
    );

    // Add to beginning
    this.recentItems.unshift(item);

    // Limit to max items
    if (this.recentItems.length > this.maxItems) {
      this.recentItems = this.recentItems.slice(0, this.maxItems);
    }

    this.saveToStorage();
    this.updateDisplay();
  }

  updateDisplay() {
    const listContainer = document.getElementById("recently-played-list");

    if (this.recentItems.length === 0) {
      listContainer.innerHTML = `
                <div class="recently-played-empty">
                    <div class="recently-played-empty-icon">📺</div>
                    <p>No recent videos</p>
                    <small>Videos you play will appear here</small>
                </div>
            `;
      return;
    }

    listContainer.innerHTML = this.recentItems
      .map(
        (item) => `
            <div class="recently-played-item ${item.type}-item" data-url="${
          item.url
        }" data-type="${item.type}">
                <div class="recently-played-icon">
                    🎬
                </div>
                <div class="recently-played-info">
                    <div class="recently-played-name" title="${item.name}">
                        ${item.name}
                    </div>
                    <div class="recently-played-time">
                        ${this.formatTime(item.timestamp)}
                    </div>
                </div>
                <div class="recently-played-type">
                    ${item.type.toUpperCase()}
                </div>
            </div>
        `
      )
      .join("");

    // Add click handlers
    listContainer.querySelectorAll(".recently-played-item").forEach((item) => {
      item.addEventListener("click", () => {
        const url = item.dataset.url;
        const type = item.dataset.type;

        if (type === "video") {
          window.location.href = url;
        }

        this.closeSidebar();
      });
    });
  }



  formatTime(timestamp) {
    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return "Just now";
  }

  toggleSidebar() {
    const sidebar = document.getElementById("recently-played-sidebar");
    const trigger = document.querySelector(".recently-played-trigger");

    if (sidebar.classList.contains("open")) {
      this.closeSidebar();
    } else {
      this.openSidebar();
    }
  }

  openSidebar() {
    const sidebar = document.getElementById("recently-played-sidebar");
    const trigger = document.querySelector(".recently-played-trigger");

    sidebar.classList.add("open");
    trigger.classList.add("hidden");
  }

  closeSidebar() {
    const sidebar = document.getElementById("recently-played-sidebar");
    const trigger = document.querySelector(".recently-played-trigger");

    sidebar.classList.remove("open");
    trigger.classList.remove("hidden");
  }

  clearHistory() {
    if (confirm("Clear all recently played items?")) {
      this.recentItems = [];
      this.saveToStorage();
      this.updateDisplay();
    }
  }

  loadFromStorage() {
    try {
      const stored = localStorage.getItem(this.storageKey);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  }

  saveToStorage() {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.recentItems));
    } catch (error) {
      console.warn("Failed to save recently played items:", error);
    }
  }

  // Static initialization
  static init() {
    if (!window.recentlyPlayed) {
      window.recentlyPlayed = new RecentlyPlayed();
    }
    return window.recentlyPlayed;
  }
}

// Auto-initialize
document.addEventListener("DOMContentLoaded", () => {
  // Wait for other components to load
  setTimeout(() => {
    RecentlyPlayed.init();
  }, 1000);
});

// Export for manual use
window.RecentlyPlayed = RecentlyPlayed;
