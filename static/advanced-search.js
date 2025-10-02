/**
 * Advanced Search Interface for Local Video Server
 * Provides real-time search with debouncing, filters, and suggestions
 */

class AdvancedSearch {
    constructor() {
        this.searchInput = document.getElementById('search-input');
        this.searchFilters = document.getElementById('search-filters');
        this.searchResults = document.getElementById('search-results');
        this.searchSuggestions = document.getElementById('search-suggestions');
        this.searchStats = document.getElementById('search-stats');
        
        this.debounceTimer = null;
        this.currentQuery = '';
        this.searchHistory = JSON.parse(localStorage.getItem('searchHistory') || '[]');
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadSearchHistory();
        this.initializeFilters();
        
        // Load search stats
        this.updateSearchStats();
        
        // Focus search input if present
        if (this.searchInput) {
            this.searchInput.focus();
        }
    }
    
    setupEventListeners() {
        // Real-time search with debouncing
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.debounceSearch(e.target.value);
            });
            
            this.searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.performSearch(this.searchInput.value);
                }
                
                // Navigate suggestions with arrow keys
                if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                    this.navigateSuggestions(e.key === 'ArrowDown' ? 1 : -1);
                    e.preventDefault();
                }
            });
            
            // Show suggestions on focus
            this.searchInput.addEventListener('focus', () => {
                this.showSuggestions();
            });
            
            // Hide suggestions when clicking outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.search-container')) {
                    this.hideSuggestions();
                }
            });
        }
        
        // Filter change handlers
        document.querySelectorAll('.search-filter').forEach(filter => {
            filter.addEventListener('change', () => {
                this.applyFilters();
            });
        });
        
        // Sort option handlers
        document.querySelectorAll('.sort-option').forEach(option => {
            option.addEventListener('click', (e) => {
                e.preventDefault();
                this.setSortOption(option.dataset.sort, option.dataset.order);
            });
        });
    }
    
    debounceSearch(query) {
        clearTimeout(this.debounceTimer);
        
        this.debounceTimer = setTimeout(() => {
            if (query.trim() !== this.currentQuery) {
                this.currentQuery = query.trim();
                
                if (this.currentQuery.length >= 2) {
                    this.getSuggestions(this.currentQuery);
                    this.performSearch(this.currentQuery);
                } else if (this.currentQuery.length === 0) {
                    this.clearResults();
                    this.hideSuggestions();
                }
            }
        }, 300); // 300ms debounce
    }
    
    async performSearch(query) {
        if (!query.trim()) {
            this.clearResults();
            return;
        }
        
        this.showSearchLoading();
        
        try {
            // Build search parameters
            const searchParams = this.buildSearchParams(query);
            
            // Perform search request
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(searchParams)
            });
            
            if (!response.ok) {
                throw new Error(`Search failed: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Display results
            this.displayResults(data.results);
            this.updateSearchStats(data.stats);
            
            // Add to search history
            this.addToSearchHistory(query);
            
        } catch (error) {
            console.error('Search error:', error);
            this.showSearchError(error.message);
        }
    }
    
    buildSearchParams(query) {
        const params = {
            query: query,
            tags: this.getSelectedTags(),
            sort_by: this.getSortBy(),
            sort_order: this.getSortOrder(),
            limit: this.getResultLimit(),
            include_fuzzy: this.getFuzzySearchEnabled()
        };
        
        // Duration filters
        const minDuration = document.getElementById('min-duration')?.value;
        const maxDuration = document.getElementById('max-duration')?.value;
        if (minDuration) params.min_duration = parseInt(minDuration) * 60; // Convert to seconds
        if (maxDuration) params.max_duration = parseInt(maxDuration) * 60;
        
        // Rating filter
        const minRating = document.getElementById('min-rating')?.value;
        if (minRating) params.min_rating = parseFloat(minRating);
        
        // Date filters
        const dateFrom = document.getElementById('date-from')?.value;
        const dateTo = document.getElementById('date-to')?.value;
        if (dateFrom) params.date_from = dateFrom;
        if (dateTo) params.date_to = dateTo;
        
        return params;
    }
    
    async getSuggestions(query) {
        try {
            const response = await fetch(`/api/search/suggestions?q=${encodeURIComponent(query)}`);
            const suggestions = await response.json();
            
            this.displaySuggestions(suggestions);
        } catch (error) {
            console.error('Error getting suggestions:', error);
        }
    }
    
    displaySuggestions(suggestions) {
        if (!this.searchSuggestions || suggestions.length === 0) {
            this.hideSuggestions();
            return;
        }
        
        const html = suggestions.map((suggestion, index) => `
            <div class="suggestion-item ${index === 0 ? 'active' : ''}" 
                 data-suggestion="${suggestion}">
                <i class="fas fa-search"></i>
                <span>${this.highlightQuery(suggestion, this.currentQuery)}</span>
            </div>
        `).join('');
        
        this.searchSuggestions.innerHTML = html;
        this.searchSuggestions.classList.add('visible');
        
        // Add click handlers
        this.searchSuggestions.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                this.searchInput.value = item.dataset.suggestion;
                this.performSearch(item.dataset.suggestion);
                this.hideSuggestions();
            });
        });
    }
    
    displayResults(results) {
        if (!this.searchResults) return;
        
        this.hideSearchLoading();
        
        if (results.length === 0) {
            this.searchResults.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search-minus"></i>
                    <h3>No videos found</h3>
                    <p>Try adjusting your search terms or filters</p>
                </div>
            `;
            return;
        }
        
        const html = results.map(result => this.renderSearchResult(result)).join('');
        this.searchResults.innerHTML = html;
        
        // Update result count
        const resultCount = document.getElementById('result-count');
        if (resultCount) {
            resultCount.textContent = `${results.length} video${results.length !== 1 ? 's' : ''} found`;
        }
    }
    
    renderSearchResult(result) {
        const tags = result.tags ? result.tags.map(tag => 
            `<span class="tag">${tag}</span>`
        ).join('') : '';
        
        const duration = this.formatDuration(result.duration);
        const fileSize = this.formatFileSize(result.size);
        const rating = this.renderRating(result.rating);
        
        return `
            <div class="search-result-card" data-video-path="${result.video_path}">
                <div class="result-thumbnail">
                    <img src="/thumbnail/${encodeURIComponent(result.filename)}" 
                         alt="${result.title}" 
                         loading="lazy"
                         onerror="this.src='/static/images/no-thumbnail.png'">
                    <div class="result-duration">${duration}</div>
                    <div class="result-match-type">${result.match_type}</div>
                </div>
                
                <div class="result-content">
                    <h3 class="result-title">
                        <a href="/watch/${encodeURIComponent(result.filename)}">${result.title}</a>
                    </h3>
                    
                    <div class="result-metadata">
                        <span class="result-size">${fileSize}</span>
                        <span class="result-views">${result.view_count} views</span>
                        <div class="result-rating">${rating}</div>
                    </div>
                    
                    <div class="result-tags">${tags}</div>
                    
                    <div class="result-relevance">
                        <div class="relevance-bar">
                            <div class="relevance-fill" 
                                 style="width: ${result.relevance_score * 100}%"></div>
                        </div>
                        <span class="relevance-score">${Math.round(result.relevance_score * 100)}% match</span>
                    </div>
                </div>
                
                <div class="result-actions">
                    <button class="btn-play" onclick="playVideo('${result.video_path}')">
                        <i class="fas fa-play"></i>
                    </button>
                    <button class="btn-favorite" onclick="toggleFavorite('${result.video_path}')">
                        <i class="far fa-heart"></i>
                    </button>
                    <button class="btn-info" onclick="showVideoInfo('${result.video_path}')">
                        <i class="fas fa-info"></i>
                    </button>
                </div>
            </div>
        `;
    }
    
    // Utility methods
    formatDuration(seconds) {
        if (!seconds) return '0:00';
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
    
    formatFileSize(bytes) {
        if (!bytes) return '0 B';
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
    }
    
    renderRating(rating) {
        if (!rating) return '<span class="no-rating">No rating</span>';
        
        const stars = [];
        for (let i = 1; i <= 5; i++) {
            const filled = i <= rating;
            stars.push(`<i class="fa${filled ? 's' : 'r'} fa-star"></i>`);
        }
        return stars.join('');
    }
    
    highlightQuery(text, query) {
        if (!query) return text;
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }
    
    // Search history management
    addToSearchHistory(query) {
        if (!query.trim()) return;
        
        // Remove duplicate if exists
        this.searchHistory = this.searchHistory.filter(item => item.query !== query);
        
        // Add to beginning
        this.searchHistory.unshift({
            query: query,
            timestamp: new Date().toISOString()
        });
        
        // Keep only last 50 searches
        this.searchHistory = this.searchHistory.slice(0, 50);
        
        // Save to localStorage
        localStorage.setItem('searchHistory', JSON.stringify(this.searchHistory));
    }
    
    loadSearchHistory() {
        const historyContainer = document.getElementById('search-history');
        if (!historyContainer || this.searchHistory.length === 0) return;
        
        const html = this.searchHistory.slice(0, 10).map(item => `
            <div class="history-item" data-query="${item.query}">
                <i class="fas fa-history"></i>
                <span>${item.query}</span>
                <button class="remove-history" data-query="${item.query}">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');
        
        historyContainer.innerHTML = html;
        
        // Add event listeners
        historyContainer.querySelectorAll('.history-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.remove-history')) {
                    this.searchInput.value = item.dataset.query;
                    this.performSearch(item.dataset.query);
                }
            });
        });
        
        historyContainer.querySelectorAll('.remove-history').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeFromHistory(btn.dataset.query);
            });
        });
    }
    
    removeFromHistory(query) {
        this.searchHistory = this.searchHistory.filter(item => item.query !== query);
        localStorage.setItem('searchHistory', JSON.stringify(this.searchHistory));
        this.loadSearchHistory();
    }
    
    // Filter and sort methods
    getSelectedTags() {
        const tagCheckboxes = document.querySelectorAll('input[name="tag"]:checked');
        return Array.from(tagCheckboxes).map(checkbox => checkbox.value);
    }
    
    getSortBy() {
        const sortSelect = document.getElementById('sort-by');
        return sortSelect ? sortSelect.value : 'relevance';
    }
    
    getSortOrder() {
        const orderSelect = document.getElementById('sort-order');
        return orderSelect ? orderSelect.value : 'desc';
    }
    
    getResultLimit() {
        const limitSelect = document.getElementById('result-limit');
        return limitSelect ? parseInt(limitSelect.value) : 50;
    }
    
    getFuzzySearchEnabled() {
        const fuzzyCheckbox = document.getElementById('fuzzy-search');
        return fuzzyCheckbox ? fuzzyCheckbox.checked : true;
    }
    
    // UI state methods
    showSearchLoading() {
        const loadingElement = document.getElementById('search-loading');
        if (loadingElement) {
            loadingElement.classList.add('visible');
        }
    }
    
    hideSearchLoading() {
        const loadingElement = document.getElementById('search-loading');
        if (loadingElement) {
            loadingElement.classList.remove('visible');
        }
    }
    
    showSearchError(message) {
        this.hideSearchLoading();
        if (this.searchResults) {
            this.searchResults.innerHTML = `
                <div class="search-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Search Error</h3>
                    <p>${message}</p>
                </div>
            `;
        }
    }
    
    clearResults() {
        if (this.searchResults) {
            this.searchResults.innerHTML = '';
        }
        
        const resultCount = document.getElementById('result-count');
        if (resultCount) {
            resultCount.textContent = '';
        }
    }
    
    showSuggestions() {
        if (this.searchSuggestions && this.searchInput.value.length >= 2) {
            this.getSuggestions(this.searchInput.value);
        }
    }
    
    hideSuggestions() {
        if (this.searchSuggestions) {
            this.searchSuggestions.classList.remove('visible');
        }
    }
    
    navigateSuggestions(direction) {
        const suggestions = this.searchSuggestions?.querySelectorAll('.suggestion-item');
        if (!suggestions || suggestions.length === 0) return;
        
        const current = this.searchSuggestions.querySelector('.suggestion-item.active');
        const currentIndex = Array.from(suggestions).indexOf(current);
        
        let newIndex = currentIndex + direction;
        if (newIndex < 0) newIndex = suggestions.length - 1;
        if (newIndex >= suggestions.length) newIndex = 0;
        
        suggestions.forEach(item => item.classList.remove('active'));
        suggestions[newIndex].classList.add('active');
        
        // Update search input
        this.searchInput.value = suggestions[newIndex].dataset.suggestion;
    }
    
    updateSearchStats(stats) {
        if (!this.searchStats || !stats) return;
        
        this.searchStats.innerHTML = `
            <div class="stat-item">
                <span class="stat-value">${stats.total_videos || 0}</span>
                <span class="stat-label">Videos Indexed</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">${stats.total_searches || 0}</span>
                <span class="stat-label">Total Searches</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">${stats.avg_execution_time || 0}s</span>
                <span class="stat-label">Avg Search Time</span>
            </div>
        `;
    }
    
    initializeFilters() {
        // Set default values for filters
        const fuzzyCheckbox = document.getElementById('fuzzy-search');
        if (fuzzyCheckbox) {
            fuzzyCheckbox.checked = true;
        }
        
        // Load saved filter preferences
        const savedFilters = JSON.parse(localStorage.getItem('searchFilters') || '{}');
        Object.keys(savedFilters).forEach(filterId => {
            const element = document.getElementById(filterId);
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = savedFilters[filterId];
                } else {
                    element.value = savedFilters[filterId];
                }
            }
        });
    }
    
    saveFilterPreferences() {
        const filters = {};
        document.querySelectorAll('.search-filter').forEach(filter => {
            if (filter.type === 'checkbox') {
                filters[filter.id] = filter.checked;
            } else {
                filters[filter.id] = filter.value;
            }
        });
        
        localStorage.setItem('searchFilters', JSON.stringify(filters));
    }
    
    applyFilters() {
        this.saveFilterPreferences();
        
        if (this.currentQuery) {
            this.performSearch(this.currentQuery);
        }
    }
    
    setSortOption(sortBy, sortOrder) {
        const sortBySelect = document.getElementById('sort-by');
        const sortOrderSelect = document.getElementById('sort-order');
        
        if (sortBySelect) sortBySelect.value = sortBy;
        if (sortOrderSelect) sortOrderSelect.value = sortOrder;
        
        this.applyFilters();
    }
}

// Global search instance
let advancedSearch;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    advancedSearch = new AdvancedSearch();
});

// Export for external use
window.AdvancedSearch = AdvancedSearch;