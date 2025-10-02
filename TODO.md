You are Cursor acting as a meticulous refactor assistant for the Local Video Server repository.

MANDATES (from product owner):

- Keep dark mode. Remove glassmorphism and neomorphism everywhere.
- Remove VR mode and any VR/WebXR/device-detection branches; rely on the browser on Quest 2.
- Use ONE shared video player on all pages with ±10 seconds skip (buttons + keyboard).
- Keep pages: Home, Watch, Random, Best-of, Favorites, Tags, Tag videos.
- Reduce duplication and delete dead assets/docs.

REPO FACTS (from current tree and docs):

- Duplicate CSS exists: static/style.css and static/styles.css; plus theme.css tokens.
- Templates present: index.html, watch.html, tags.html, tag_videos.html. README mentions favorites.
- Routes to keep: /watch/<filename>, /video/<filename> (range), /random.
- Glass/neo classes exist only by design docs and previous attempts; purge them if found.
- JSON stores: ratings.json, tags.json, views.json.

DELIVERABLE:
Apply the concrete steps from the file named **“tasklist.md — Local Video Server Refactor”** (open in this workspace). Execute them EXACTLY, with these guardrails:

GUARDRAILS:

1) DO NOT introduce any new frameworks or build steps. Vanilla Flask + vanilla JS only.
2) Consolidate CSS to static/css/app.css (+ keep static/theme.css). After merging, DELETE static/style.css and static/styles.css.
3) Create a reusable player partial templates/_player.html and a single controller static/js/player.js:
   - Buttons: Back 10s, Play/Pause, Forward 10s, Mute, Volume, Seek, Fullscreen.
   - Keyboard: J/L = ±10s, K/Space = Play/Pause, F = fullscreen, M = mute, ArrowUp/Down = volume.
   - Support ?t=SECONDS start time and last-position resume via localStorage.
4) Wire the shared player into watch.html and any place that previously embedded a video (index, tags, tag_videos, favorites, best_of).
5) Create or restore pages: favorites.html and best_of.html, both using the shared player partial.
6) Strip ALL glass/neomorphic references:
   - Remove selectors/classes: .glass*, .neo*, .hybrid* from CSS/templates.
   - Remove any theme manager enabling those modes.
   - DELETE GLASSMORPHIC_NEOMORPHIC_DESIGN.md.
7) Strip ALL VR mode code/flags and VR-specific CSS. If files like device-detection.js/adaptive-streaming*.js/network-monitor.js exist, do not load them; if truly unused, remove or move to docs/deferred/.
8) Keep hover preview ONLY if it is lightweight and does not conflict with the shared player. If it adds complexity, remove it from templates for now.
9) Ensure Random redirects to /watch/<file>. Implement Best-of sorting (rating desc, then views desc). Keep JSON data sources intact.
10) Update README to reflect: dark mode only; pages present; single player; keyboard shortcuts.

ACCEPTANCE TESTS:

- Only static/css/app.css + static/theme.css are loaded.
- No class names matching /(glass|neo|hybrid)/ remain in codebase.
- No VR/WebXR or device-detection code is referenced.
- All of: Home, Watch, Random, Best-of, Favorites, Tags, Tag videos render; Watch plays; ±10s works (buttons + keyboard).
- README updated accordingly.

WORKFLOW:

- Implement in small commits as listed in the “Suggested commits” section of tasklist.md.
- When deleting files, search before remove: ripgrep patterns:
  - glass|neo|hybrid
  - webxr|vr|device-detection
  - style.css|styles.css references
- Run the app, manually verify pages: /, /watch/<any>, /random, /best-of, /favorites, /tags.

If any referenced file does not exist, adapt by creating the minimum viable version as the tasklist describes rather than inventing new features.

Proceed now.
