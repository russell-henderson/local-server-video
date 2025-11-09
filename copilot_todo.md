# ✅ CoPilot TODO.md — Local Video Server v1.01

## 🎯 Objective

Align CoPilot's next set of automated actions with the finalized project architecture, ensuring subtitle system removal, player control improvements, and cross-system consistency between this and the aligned Local Video Server build.

---

## 🧩 1. Subtitle System Full Decommission

### ✅ Tasks Completed

- Archived original subtitle documentation to `docs/deferred/`
- Created stubs for `SUBTITLE_GENERATION_GUIDE.md` and `SUBTITLE_GENERATION_COMPLETE.md`

### ⚠️ Tasks Pending

1. **Replace the remaining `SUBTITLE_SYSTEM_TROUBLESHOOTING.md`** with stub version (retry archive-stub operation).
2. **Purge all subtitle-related code from source:**
   - [ ] `main.py`: remove subtitle/caption routes and imports.
   - [ ] `templates/watch.html`: delete `<track kind="subtitles">` elements.
   - [ ] `static/`: delete any subtitle-related JS or CSS (`subtitle.js`, `captions.css`, etc.).
   - [ ] Verify no `.srt`, `.vtt`, `.ass` files remain in repo or generation routines.
3. **Add neutral confirmation note** to README under Deprecated Features section.

### 🔍 Validation Checklist

- [ ] `grep -Ri "subtitle" ./` returns only references in archived docs.
- [ ] Server runs successfully after removal.
- [ ] No missing import or route errors in Flask logs.

---

## 🎬 2. Video Player Controls Auto-Hide

### 🎨 UI/UX Objective

Make player controls invisible by default during playback, visible only on hover or movement, including fullscreen.

### 🧠 Implementation Steps

1. Add a new JS module: `static/video-player-controls.js`.
2. Integrate event listeners:
   - `mousemove` → show controls.
   - `mouseleave` → hide controls.
   - `fullscreenchange` → toggle visibility logic.
3. Update CSS:
   - Add transition and opacity states for `.player-controls`.
   - Maintain responsiveness under all themes (Glassmorphic / Neomorphic / Hybrid).
4. Add import link in `templates/watch.html` below video.js initialization.
5. Test across browsers and VR view modes.

### ✅ Acceptance Criteria

- [ ] Controls fade after 2 seconds of idle.
- [ ] Controls return on hover/movement.
- [ ] No flickering or overlap in fullscreen.
- [ ] Behavior consistent across Chrome, Edge, Firefox, and Quest browser.

---

## ⚡ 3. Performance and Integration Checks

1. Confirm no regressions in:
   - Video preview on hover (`VIDEO_PREVIEW_FEATURE.md`).
   - Adaptive streaming (`ADAPTIVE_STREAMING_SYSTEM.md`).
   - Cache and performance behavior (`PERFORMANCE_OPTIMIZATION_GUIDE.md`).
2. Run `main.py` smoke test:

   ```bash
   flask run
   ```

   - [ ] Verify homepage loads thumbnails and previews.
   - [ ] Verify watch page streams video normally.
   - [ ] Confirm absence of subtitle-related errors.

3. Execute performance validation:

   ```bash
   curl -s -o /dev/null -w '%{time_total}\n' http://localhost:5000
   ```

   - Expected average: **< 0.1s response time** (post-cache).

---

## 🧱 4. Documentation Updates

- [ ] Create `docs/PLAYER_CONTROL_BEHAVIOR.md` summarizing new behavior.
- [ ] Update `README.md` Features section to reflect auto-hide player controls.
- [ ] Append reference in `GLASSMORPHIC_NEOMORPHIC_DESIGN.md` for player overlay interaction style.
- [ ] Update `CHANGELOG.md` with entries:

  ```text
  [1.01.1] — Subtitle System Fully Removed, Player Controls Auto-Hide Added
  ```

---

## 🧪 5. QA & Cross-System Alignment

1. Compare with the aligned Local Video Server build:
   - [ ] Ensure unified theme assets under `/static/`.
   - [ ] Confirm design consistency in `styles.css` and `theme.css`.
   - [ ] Verify shared performance configurations and cache tuning.
2. Optional regression test:

   ```bash
   pytest tests/ui/test_player_behavior.py
   ```

---

## 🗂 6. Deployment Readiness

### Pre-Deployment Checks

- [ ] `git diff --stat` shows only intended UI and removal changes.
- [ ] `ffmpeg` installed and functional.
- [ ] Cache and thumbnails directories accessible.
- [ ] Database migration (if enabled) tested.

### Deployment Script

```bash
# Commit patch
 git add .
 git commit -m "Subtitle purge + auto-hide controls implemented"
 git push origin main
```

### Post-Deployment Verification

- [ ] Application service restarts successfully.
- [ ] Watch page responsive and clean.
- [ ] No console or network errors in browser.
- [ ] Video previews and ratings functional.

---

## 🧭 Summary

**Purpose:** Finalize transition to subtitle-free, immersive video experience.
**Outcome:** Cleaner UI, better fullscreen focus, reduced code complexity.
**Owner:** CoPilot
**Target Completion:** Next release cycle (v1.02)
**Risk Level:** Low — backward compatible with all recent optimizations.
