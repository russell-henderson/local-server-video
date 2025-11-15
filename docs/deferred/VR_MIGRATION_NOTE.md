# VR Migration Note

Date: 2025-10-31

Summary
-------

Removed stale references to archived VR support scripts from templates. The removed script includes were:

- `static/device-detection.js`
- `static/vr-support.js`
- `static/vr-video-player.js` (archived)

Reason
------

VR-specific code (WebXR helpers and a separate VR video player) was previously archived/moved out of the active codebase. Templates still referenced these static files which no longer exist in `static/` and caused confusion and 404s. The VR feature set itself is intentionally not part of the current deployment; the code was documented and archived in `docs/deferred/`.

What changed
------------

- Removed script tag includes for `device-detection.js` and `vr-support.js` from templates:
  - `templates/index.html`
  - `templates/favorites.html`
  - `templates/best_of.html`

- Added small compatibility stubs to `static/` to avoid 404s and provide a clear message that VR features are archived:
  - `static/device-detection.js` (no-op)
  - `static/vr-support.js` (no-op)

- Kept a short migration note here and referenced the archived docs that describe the VR code (see `docs/VR_RATINGS_FAVORITES_FIX.md` and `docs/deferred/README.md`).

Why this is safe
-----------------

- The runtime behavior for favorites/ratings is centralized in `static/optimized-utils.js` and `static/favorites.js`. Those modules remain loaded and functional.
- The removal only affects references to files that are intentionally archived; no functional code was deleted from `static/` by this change.

How to restore VR features (if desired)
---------------------------------------

1. Restore the archived static files (`vr-support.js`, `vr-video-player.js`, `device-detection.js`) into `static/` and re-add the script tags.
2. Or re-implement a minimal compatibility script that provides just the overlay behavior: ensure the VR overlay moves the full player controls (favorites/ratings) into the immersive container.

Notes & references
------------------

- Archived VR implementation details: `docs/VR_RATINGS_FAVORITES_FIX.md`
- Deferred files list: `docs/deferred/README.md`

If you want, I can also remove the remaining references in other templates or add a small compatibility stub that safely no-ops when VR is not present.
