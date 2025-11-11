# UI — Local Video Server

Consolidated UI documentation (design, player, and preview system). Original files archived to docs/deferred/.

## Design & Patterns

- Hybrid approach: glassmorphism for panels, neumorphism for controls where appropriate.
- Accessibility: WCAG AA contrast, keyboard navigation, clear focus states, reduced-motion respect.

## Player & Controls

- Single shared player across pages (	emplates/_player.html).
- Controls: play/pause, volume, scrub, fullscreen, skip ±10s, keyboard bindings.
- Favorites and rating UI updated via centralized optimized-utils.js to sync controls across DOM.

## Preview System

- Adaptive preview strategies: hover-based on desktop, tap/long-press for touch and VR, disabled for low-memory/slow connections.
- Key files: static/video-preview-enhanced.js, static/video-preview-debug.js and capability detection helper static/device-detection.js (stubbed compatibility file exists).

---

See docs/deferred/Local Video Server UI.md and docs/deferred/VIDEO_PREVIEW_IMPROVEMENTS.md for the full original text.
