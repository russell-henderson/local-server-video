# TODO: Playlist UI Expansion Without Breaking Existing Playback

## Purpose

Add the requested playlist page improvements while preserving the current working behavior:

- Existing playlists must still render.
- Existing playlist videos must still load from the playlist page.
- Existing `Watch Now` behavior must remain intact.
- Playlist creation must continue to work.
- No existing data should be destroyed or silently migrated without a backup.

This is an additive feature pass. Refactor only where required to safely expose new playlist metadata and UI controls.

---

## Screenshot Region Map

Use the annotated screenshot as the page layout contract.

| Region | Requested Role | Implementation Target |
|---|---|---|
| A | Page title area containing `Collections`, `My Playlists`, and `+ Create New` | Create a compact hero/header card. Move `+ Create New` into this region only. |
| B | Additional playlist functionality | Add a `Playlist Tools` panel with actionable controls. |
| C | Secondary playlist component | Add a `Playlist Insights` panel with recent activity, popular tags, or playlist stats. |
| D | Current individual playlist card structure | Preserve card grid and existing `Watch Now` routing. Add fields inside current structure. |
| E | Editable playlist image/thumbnail | Add playlist cover image upload, preview, replacement, and fallback placeholder. |
| F1 | Editable description | Add edit support for playlist description. |
| F2 | Created date | Keep created date display as-is unless formatting is currently inconsistent. |
| G | Description text area in card | Same as F1. Make it editable through modal or inline edit mode. |
| H | Total number of items | Keep item count display. Do not change count logic. |
| I | Editable green component area with another playlist feature | Add an editable `Spotlight Bar` with a label plus optional quick action. |

Note: The prompt used `F` for both the editable description and created date. Treat these as `F1` and `F2` to avoid implementation ambiguity.

---

## Guardrails

### Do not break

- Existing playlist routes.
- Existing playlist detail page that loads videos added to the playlist.
- Existing playlist create flow.
- Existing item count display.
- Existing created date display.
- Existing delete behavior.
- Existing navbar highlighting.
- Existing dark mode.
- Existing responsive layout.

### Do not do yet

- Do not rewrite the whole playlist system.
- Do not replace Flask/Jinja with a new frontend framework.
- Do not introduce authentication.
- Do not move video files.
- Do not change video streaming routes.
- Do not change how playlist membership works unless required for a bug fix discovered during testing.

### Required implementation style

- Make small, reversible changes.
- Add metadata fields with backward-compatible defaults.
- Use progressive enhancement for JavaScript.
- Make all new controls work with keyboard and mouse.
- Keep the page usable if JavaScript fails.
- Prefer existing theme variables and component patterns.
- Keep expensive blur and animation effects limited.

---

## Phase 0: Baseline Audit Before Editing

### 0.1 Find current playlist implementation

Run these from the project root:

```powershell
Get-ChildItem -Recurse -File | Select-String -Pattern "playlist|playlists|Playlist|Playlists" | Select-Object Path, LineNumber, Line
```

Also inspect:

```powershell
Get-ChildItem -Recurse -File templates,static | Where-Object { $_.Name -match "playlist|styles|script|app|main|theme" }
```

### 0.2 Identify current files

Document the actual current files before changing anything:

- Playlist template file, likely `templates/playlists.html` or equivalent.
- Playlist detail template file, likely `templates/playlist_detail.html` or equivalent.
- Backend playlist routes in `main.py` or another Flask module.
- Playlist storage file or table.
- Current JavaScript file used by the playlist page, if any.
- Current stylesheet used by playlist cards.

### 0.3 Create backups

Before editing:

```powershell
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Force -Path ".\backup-playlist-ui-$stamp"
Copy-Item .\main.py ".\backup-playlist-ui-$stamp\main.py" -ErrorAction SilentlyContinue
Copy-Item .\templates\*playlist* ".\backup-playlist-ui-$stamp\" -ErrorAction SilentlyContinue
Copy-Item .\static\*.css ".\backup-playlist-ui-$stamp\" -ErrorAction SilentlyContinue
Copy-Item .\static\*.js ".\backup-playlist-ui-$stamp\" -ErrorAction SilentlyContinue
Copy-Item .\*.json ".\backup-playlist-ui-$stamp\" -ErrorAction SilentlyContinue
```

### 0.4 Baseline smoke test

Start the server and verify before editing:

- `/playlists` loads.
- `+ Create New` creates a playlist.
- Existing playlists display.
- Clicking `Watch Now` opens the correct playlist video page.
- Playlist delete still works.
- Navbar active state still works.
- Browser console has no playlist page errors.

Record the current behavior in the PR notes or implementation log.

---

## Phase 1: Data Model Additions

### 1.1 Add backward-compatible playlist metadata fields

Every playlist should support these fields:

```json
{
  "id": "existing-or-generated-id",
  "name": "Playlist name",
  "description": "No description provided.",
  "created_at": "existing-created-date",
  "videos": [],
  "cover_image": null,
  "spotlight_label": "",
  "spotlight_action": "continue",
  "spotlight_enabled": true,
  "sort_mode": "manual",
  "autoplay_next": false,
  "shuffle_default": false,
  "last_played_video": null,
  "last_opened_at": null,
  "updated_at": null
}
```

Requirements:

- Existing playlists that lack these fields must render with safe defaults.
- Do not require a destructive migration.
- If the app uses JSON, normalize fields when reading and write them only after an explicit update or safe save operation.
- If the app uses SQLite, add nullable columns with defaults. Do not drop or recreate playlist tables.
- If the app has a cache layer, invalidate or refresh playlist cache after metadata edits.

### 1.2 Add safe normalization helper

Create or update a helper similar to:

```python
def normalize_playlist(raw):
    playlist = dict(raw or {})
    playlist.setdefault("description", "No description provided.")
    playlist.setdefault("cover_image", None)
    playlist.setdefault("spotlight_label", "")
    playlist.setdefault("spotlight_action", "continue")
    playlist.setdefault("spotlight_enabled", True)
    playlist.setdefault("sort_mode", "manual")
    playlist.setdefault("autoplay_next", False)
    playlist.setdefault("shuffle_default", False)
    playlist.setdefault("last_played_video", None)
    playlist.setdefault("last_opened_at", None)
    playlist.setdefault("updated_at", None)
    playlist.setdefault("videos", [])
    return playlist
```

Adjust names to match current code style.

### 1.3 Add metadata update endpoint

Add a route that updates only editable metadata:

```http
PATCH /api/playlists/<playlist_id>/metadata
```

Accepted payload fields:

```json
{
  "name": "optional string",
  "description": "optional string",
  "spotlight_label": "optional string",
  "spotlight_action": "continue | shuffle | newest | highest_rated | custom",
  "spotlight_enabled": true,
  "sort_mode": "manual | name | created_at | rating | views",
  "autoplay_next": false,
  "shuffle_default": false
}
```

Backend validation:

- Strip whitespace from strings.
- Reject names that are empty after trimming.
- Limit description to 500 characters.
- Limit spotlight label to 80 characters.
- Reject unknown enum values.
- Return JSON with updated normalized playlist.
- Return `404` if playlist does not exist.
- Return `400` for invalid payloads.

---

## Phase 2: Cover Image Upload for Region E

### 2.1 Storage location

Create:

```text
static/playlist_covers/
```

Do not store uploaded images inside `videos/`.

### 2.2 Upload route

Add:

```http
POST /api/playlists/<playlist_id>/cover
```

Form data:

```text
cover=<file>
```

Allowed file types:

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`

Recommended max file size:

- 5 MB hard limit.

Processing requirements:

- Sanitize playlist id and file extension.
- Generate deterministic filename such as `<playlist_id>.<ext>` or versioned filename such as `<playlist_id>-<timestamp>.<ext>`.
- Delete older cover files for the same playlist after successful replacement.
- Store the relative path in `cover_image`, for example `/static/playlist_covers/<file>`.
- Return JSON with the updated cover path.

### 2.3 Delete cover route

Add:

```http
DELETE /api/playlists/<playlist_id>/cover
```

Requirements:

- Remove cover file if it exists.
- Set `cover_image` to `null`.
- Return updated normalized playlist.
- Do not fail if the file is missing but metadata references it.

### 2.4 Card display

In each playlist card:

- If `cover_image` exists, display it in Region E.
- If no `cover_image`, display a styled fallback block with an icon or initials.
- Add an edit button overlay visible on hover and focus.
- Use `object-fit: cover`.
- Keep consistent aspect ratio, recommended `4 / 3` or `16 / 9` depending on card width.

Accessibility:

- `alt="Cover image for {{ playlist.name }}"`
- Upload control must have a visible label in the edit modal.

---

## Phase 3: Region A Header Redesign

### 3.1 Header layout

Replace the current wide single-row create bar with a 3-column top grid:

```text
[A: Playlist Hero] [B: Playlist Tools] [C: Playlist Insights]
```

Desktop:

- Use CSS Grid with `grid-template-columns: minmax(320px, 1fr) minmax(320px, 1fr) minmax(320px, 1fr)`.
- Keep all three panels aligned and visually balanced.

Tablet:

- Two columns where reasonable.
- C can wrap below.

Mobile:

- Stack A, B, C vertically.

### 3.2 A panel content

A must contain:

- Small eyebrow text: `Collections`.
- Page title: `My Playlists`.
- Optional subtitle: `Organize, style, and replay your local video sets.`
- `+ Create New` button inside A only.

The `+ Create New` button must call the existing create flow if one exists. Do not replace a working create route unless required.

---

## Phase 4: Region B Playlist Tools Panel

B should be immediately useful, not decorative.

### 4.1 Add tools

Implement `Playlist Tools` with these controls:

1. `Edit Mode` toggle
   - Reveals edit affordances on playlist cards.
   - Allows cover upload, description edit, and spotlight edit.

2. `Search playlists` input
   - Filters visible cards client-side by playlist name and description.
   - Does not change backend data.

3. `Sort playlists` select
   - Options: Name, Created Date, Item Count, Last Opened.
   - Client-side sort is acceptable for this pass.

4. `Compact cards` toggle
   - Stores preference in `localStorage`.
   - Reduces card padding and hides long descriptions after one line.

5. Optional safe action: `Export playlists JSON`
   - Downloads the current playlist metadata as JSON.
   - Must not include video binary data.

### 4.2 B panel non-goals

Do not add destructive batch delete in this pass. Keep destructive actions per-card until the new metadata features are stable.

---

## Phase 5: Region C Playlist Insights Panel

C should surface helpful context using existing data where possible.

### 5.1 Recommended C content

Implement `Playlist Insights` with:

- Total playlists.
- Total videos across playlists.
- Largest playlist by item count.
- Recently opened playlist, if `last_opened_at` is available.
- Popular tags from videos inside playlists, if tag data is available.

### 5.2 Data source rules

- Use existing tag metadata if available.
- If recent activity tracking is not available yet, show `No recent playlist activity yet`.
- Do not scan the entire video directory for C on every request if cached playlist/video metadata already exists.
- Use the existing cache manager when available.

### 5.3 Optional endpoint

Add only if needed:

```http
GET /api/playlists/summary
```

Response shape:

```json
{
  "total_playlists": 3,
  "total_videos": 33,
  "largest_playlist": { "id": "...", "name": "...", "count": 25 },
  "recently_opened": [],
  "popular_tags": []
}
```

---

## Phase 6: Playlist Card Enhancements for Regions D Through I

### 6.1 Preserve card skeleton

Keep the current card hierarchy:

- Playlist name.
- Description.
- Item count.
- Created date.
- `Watch Now` button.
- Delete button.

Add new elements without removing these.

### 6.2 Region E cover component

Suggested markup:

```html
<div class="playlist-cover" data-playlist-cover="{{ playlist.id }}">
  {% if playlist.cover_image %}
    <img src="{{ playlist.cover_image }}" alt="Cover image for {{ playlist.name }}">
  {% else %}
    <div class="playlist-cover-fallback" aria-hidden="true">
      <span>{{ playlist.name[:1] }}</span>
    </div>
  {% endif %}
  <button class="playlist-cover-edit" type="button" data-action="edit-cover" data-playlist-id="{{ playlist.id }}">
    Edit Cover
  </button>
</div>
```

Adjust syntax to match the project template.

### 6.3 Region F1/G editable description

Add an edit button or make edit available through the card edit modal.

Rules:

- Default display remains `No description provided.`.
- Empty submitted description should revert to default or store empty and display default. Choose one consistent approach.
- Persist edits through the metadata route.
- Update the card without a full page reload when JavaScript is available.
- Full page reload fallback is acceptable after successful form submit.

### 6.4 Region H item count

Keep the existing item-count badge.

Rules:

- Do not change count source.
- Do not calculate count from DOM.
- Count should remain accurate after playlist edits and page refresh.

### 6.5 Region F2 created date

Keep the existing created date.

Allowed improvement:

- Add `<time datetime="...">Created YYYY-MM-DD</time>` if current template uses plain text.

Do not change the actual stored created date.

### 6.6 Region I Spotlight Bar

Add an editable bottom card component:

```text
[ Spotlight label ] [optional quick-action icon]
```

Purpose:

- Gives each playlist a small custom identity and quick action.
- Uses the green marked area from the screenshot as the location.

Fields:

- `spotlight_label`: user-editable label, for example `Weekend queue`, `Favorites`, `Finish this set`.
- `spotlight_action`: enum, one of `continue`, `shuffle`, `newest`, `highest_rated`, `custom`.
- `spotlight_enabled`: show/hide toggle.

Behavior:

- `continue`: opens `last_played_video` if available, otherwise opens the playlist page.
- `shuffle`: opens a random video from that playlist.
- `newest`: opens newest-added video in that playlist, if video metadata supports it.
- `highest_rated`: opens highest-rated video in that playlist, if rating metadata supports it.
- `custom`: displays label only and opens playlist page.

Backend support:

- Use existing playlist video list.
- Use existing rating metadata for `highest_rated` if available.
- If the selected action cannot resolve a video, fall back to the playlist detail page.

Suggested endpoint:

```http
GET /playlists/<playlist_id>/quick/<action>
```

Return:

- Redirect to a watch page if a video resolves.
- Redirect to playlist detail if no video resolves.

---

## Phase 7: Edit Modal

### 7.1 One modal per page, not one modal per card

Add a reusable modal or dialog that is populated from the selected playlist card.

Fields:

- Playlist name.
- Description.
- Cover image upload.
- Remove cover button.
- Spotlight enabled.
- Spotlight label.
- Spotlight action.
- Shuffle default.
- Autoplay next.
- Sort mode.

### 7.2 Save behavior

On save:

1. Validate client-side for empty name and max lengths.
2. Submit metadata via `PATCH /api/playlists/<playlist_id>/metadata`.
3. If a new cover file was selected, submit cover upload after metadata succeeds.
4. Update the card DOM with returned metadata.
5. Show success feedback.
6. Keep modal open only if upload fails after metadata succeeds, so the user can retry.

### 7.3 Error behavior

- Show backend validation messages near the relevant field.
- Do not discard user input on failure.
- Log detailed errors to console only in debug mode.

---

## Phase 8: Styling

### 8.1 CSS files

Use existing stylesheet conventions. Likely targets:

- `static/styles.css`
- `static/theme.css`
- Existing playlist-specific CSS if present.

Do not scatter playlist CSS across unrelated templates.

### 8.2 Required classes

Add or adapt these classes:

```css
.playlists-dashboard
.playlist-hero-panel
.playlist-tools-panel
.playlist-insights-panel
.playlists-top-grid
.playlist-card
.playlist-card-main
.playlist-cover
.playlist-cover img
.playlist-cover-fallback
.playlist-cover-edit
.playlist-meta-row
.playlist-item-count
.playlist-created-date
.playlist-spotlight-bar
.playlist-edit-mode .playlist-editable
.playlist-modal
.playlist-modal-field
```

### 8.3 Visual rules

- Keep dark theme first.
- Use existing border radius, shadows, and theme variables where possible.
- Preserve text contrast.
- Avoid large transparent blur layers in every card.
- New panels should look premium but not overpower the cards.
- Buttons must have clear hover, active, and focus states.

### 8.4 Responsive behavior

- Desktop: top A/B/C grid, playlist cards in 3 columns if width allows.
- Tablet: top grid wraps, playlist cards in 2 columns.
- Mobile: all panels and cards stack, cover image full width above card text if needed.

---

## Phase 9: JavaScript

### 9.1 Add playlist page script

Create a dedicated file if one does not already exist:

```text
static/playlists.js
```

Load it only on the playlist page.

### 9.2 Required functions

Implement:

```javascript
initPlaylistPage()
initPlaylistTools()
initPlaylistSearch()
initPlaylistSort()
initPlaylistEditMode()
openPlaylistEditModal(playlistId)
collectPlaylistMetadataForm()
savePlaylistMetadata(playlistId, payload)
uploadPlaylistCover(playlistId, file)
deletePlaylistCover(playlistId)
updatePlaylistCard(playlist)
showPlaylistToast(message, type)
```

Use current project JavaScript style. Avoid large dependencies.

### 9.3 Progressive enhancement

- Cards must still render without JavaScript.
- `Watch Now` links must remain real links.
- Delete must keep existing behavior.
- Edit controls may require JavaScript, but the page itself must remain usable.

### 9.4 LocalStorage preferences

Use namespaced keys:

```text
localVideoServer.playlists.editMode
localVideoServer.playlists.compactCards
localVideoServer.playlists.sortMode
```

---

## Phase 10: Backend Implementation Details

### 10.1 Route checklist

Add or confirm:

```http
GET    /playlists
GET    /playlists/<playlist_id>
POST   /playlists/create                  existing route may differ
PATCH  /api/playlists/<playlist_id>/metadata
POST   /api/playlists/<playlist_id>/cover
DELETE /api/playlists/<playlist_id>/cover
GET    /api/playlists/summary             optional
GET    /playlists/<playlist_id>/quick/<action>
```

Do not rename existing public routes unless aliases are retained.

### 10.2 File upload security

- Use `werkzeug.utils.secure_filename` or equivalent.
- Validate extension using a whitelist.
- Validate MIME type if practical.
- Enforce max upload size.
- Never execute or parse uploaded files as code.
- Store only under `static/playlist_covers/`.

### 10.3 Cache invalidation

After metadata edit, cover upload, cover delete, or playlist creation:

- Refresh playlist cache if cache exists.
- Do not refresh full video cache unless necessary.
- Ensure updated card data is visible after reload.

---

## Phase 11: Testing Checklist

### 11.1 Manual tests

Run these in browser:

- Load `/playlists` with existing playlist data.
- Create a new playlist from A.
- Search playlists from B.
- Sort playlists from B.
- Toggle compact mode from B.
- Open edit mode from B.
- Edit playlist description.
- Upload a cover image.
- Replace a cover image.
- Remove a cover image.
- Edit spotlight label.
- Change spotlight action to `shuffle`.
- Click spotlight action.
- Click `Watch Now` and confirm existing behavior still works.
- Delete a playlist and confirm existing delete behavior still works.
- Reload page and confirm all edits persist.
- Test with a playlist that has no description, no cover, and no videos.
- Test with a playlist that has 25+ videos.
- Test dark mode.
- Test mobile width in DevTools.

### 11.2 Backend tests

If the project has pytest, add tests for:

- Metadata PATCH success.
- Metadata PATCH invalid enum.
- Metadata PATCH empty name rejection.
- Description max length validation.
- Cover upload success.
- Cover upload invalid extension rejection.
- Cover delete when file exists.
- Cover delete when file is already missing.
- Quick action fallback when playlist is empty.
- Existing playlist detail route still returns 200.

### 11.3 Regression checks

Verify these still work:

- Home page.
- Tags page.
- Favorites page.
- Popular page if present.
- Gallery page if present.
- Search in navbar.
- Random button.
- Existing video streaming.
- Existing thumbnail display.

### 11.4 Performance checks

- Playlist page should not scan every video file repeatedly if cached metadata exists.
- Cover images should be browser-cacheable static files.
- `Playlist Insights` must use cached metadata or precomputed summaries where possible.
- No per-card duplicate modal markup.
- No per-card large base64 image data in HTML.

---

## Phase 12: Acceptance Criteria

The implementation is complete when all of these are true:

- A contains `Collections`, `My Playlists`, and `+ Create New`.
- B contains working playlist tools.
- C contains useful playlist insights with safe empty states.
- Each playlist card still opens the playlist/videos correctly.
- E supports cover upload, replacement, display, and removal.
- F1/G description is editable and persists.
- H item count still displays accurately.
- F2 created date still displays.
- I displays an editable spotlight bar with at least one working quick action.
- Existing playlist data loads without a required migration step.
- Browser console is clean during normal use.
- No existing playlist operation is broken.
- Mobile layout remains usable.
- Dark mode remains readable.

---

## Suggested Implementation Order for Codex

1. Audit existing playlist files and routes.
2. Add metadata normalization with defaults.
3. Add metadata PATCH route.
4. Add cover upload/delete routes.
5. Update playlist template with A/B/C top grid.
6. Add Region E cover display to cards.
7. Add Region I spotlight bar to cards.
8. Add edit modal.
9. Add `static/playlists.js`.
10. Add CSS for dashboard, cards, cover, modal, and responsive behavior.
11. Add summary data for C.
12. Add quick action route.
13. Run manual regression checklist.
14. Add tests if the test framework exists.
15. Update README or project notes with the new playlist metadata fields.

---

## Implementation Notes

- The UI direction should follow the existing local video server aesthetic: dark, polished, compact, and media-focused.
- Use the design system’s hybrid approach where containers can be glass-like and interactive controls can feel tactile.
- Keep accessibility and performance in view. The playlist page can look premium without adding heavy blur to every card.
- The current playlist feature already works. Treat this as a controlled expansion, not a rebuild.
