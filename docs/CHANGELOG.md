# CHANGELOG

## 2026-02-01

### Cross-Device Enhancements
- **Touch Targets**: Enlarged rating stars and favorite buttons to 44px minimum for mobile/VR accessibility.
- **Interaction Styles**: Replaced hover-dependent styles with :active/:focus for touch compatibility.
- **Favorites Page**: Added dedicated `/favorites` route with sorting, pagination, and responsive UI.
- **Popular Page**: Added `/popular` route displaying videos sorted by view count.
- **Video Player**: Added Picture-in-Picture support with keyboard shortcut (P).
- **PWA Features**: Implemented service worker for caching static assets, improving mobile performance.

## 2025-12-09

### Gallery UX and Favorites
- Added favorites hearts to all gallery images (loose and grouped) with a Favorites filter that aggregates every favorited item.
- Simplified gallery tiles by removing filename overlays for a cleaner visual grid.
- Updated lightbox and selection handling to respect favorites filtering and maintain correct navigation/selection ranges.

## 2025-12-07

### Search Enhancements

- **Automated Search Re-indexing**: Real-time updates for video metadata, ensuring search results are always current.
- **Advanced Search Filters**: Added filters for duration, rating, and date to refine search queries.
- **Semantic Search Integration**: Introduced AI-powered semantic search capabilities using embeddings and a new AI gateway (mocked for now).
- **Improved Search UI**: Enhanced the user interface for search results, including new filter options and better display of video metadata and relevance.
