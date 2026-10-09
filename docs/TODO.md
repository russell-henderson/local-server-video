Implement the following **Image Gallery UX modernization** for the Local Video Server.

## Scope

Primary files:

* `templates/gallery.html`
* `templates/gallery_group.html`

Inspect any related routes, JavaScript, CSS, image-group logic, favorites logic, similarity logic, and persistence code before modifying them.

Do **not redesign or remove existing functionality**. This is an additive modernization of the current gallery experience.

Preserve:

* Existing image groups
* Group creation and editing
* Existing group cover-image functionality
* Existing image-to-group assignment
* Existing favorites behavior
* Existing similarity/find-similar behavior
* Existing image routing
* Existing mobile behavior unless specifically improved below
* Current data persistence model
* Existing glassmorphic/neomorphic theme system

Do not create a parallel gallery architecture if the existing implementation can be extended cleanly.

---

# 1. Introduce a centralized gallery UI state

Before adding multiple disconnected event handlers, establish a coherent client-side gallery state.

Use an implementation appropriate to the existing vanilla JavaScript architecture.

The state should represent at minimum:

```javascript
{
    viewMode: 'masonry',
    density: 'medium',
    query: '',
    sort: 'date-added',
    format: 'all',
    favoriteOnly: false,
    activeTags: [],
    selectionMode: false,
    selectedImages: new Set(),
    currentImageIndex: null,
    inspectorOpen: false,
    filmstripOpen: true
}
```

The exact implementation may differ, but the gallery grid, filters, selection system, and lightbox must operate from a consistent state rather than maintaining unrelated copies of UI state.

Persist user display preferences in `localStorage`:

* `gallery.viewMode`
* `gallery.density`
* `gallery.sort`
* `gallery.inspector`
* `gallery.filmstrip`

Do not persist transient state such as selected images.

---

# 2. Gallery layout upgrade

The existing fixed-height image presentation should no longer be the only viewing mode.

Implement two modes:

### Masonry / natural aspect ratio

* Preserve native image aspect ratios.
* Avoid cropping portrait and panoramic images.
* Make this the preferred modern gallery experience.

### Uniform grid

* Preserve the existing predictable thumbnail-card style as an alternate mode.

Add a compact view-mode control in the gallery toolbar.

Also add density controls:

* Compact
* Medium
* Showcase

Density should affect grid width/column sizing rather than arbitrarily distorting image aspect ratio.

Both view mode and density must remain responsive.

---

# 3. Apply the existing Local Video Server design system

Bring the gallery visually in line with the existing glassmorphic/neomorphic interface.

Use:

* Glassmorphism for structural UI:

  * Search/filter toolbar
  * Floating selection bar
  * Lightbox inspector
  * Dropdown/menu surfaces
* Tactile/neomorphic styling selectively for:

  * Buttons
  * Toggles
  * View-mode controls
  * Interactive actions

Do **not** apply `backdrop-filter` blur to every image card.

Keep the image grid itself visually clean and content-focused.

Avoid hundreds of simultaneous blurred surfaces because this can create unnecessary rendering cost.

Continue respecting:

* `prefers-reduced-motion`
* Reduced transparency/accessibility behavior if already implemented
* Existing theme variables
* Existing responsive breakpoints where practical

Do not create a separate independent theme just for the image gallery.

---

# 4. Search, sorting, and filtering toolbar

Add a compact gallery discovery toolbar.

Implement live filtering by:

* Filename
* File extension
* Group membership where existing data permits it
* Existing image metadata/tags if available in the current implementation

Add sorting options based only on data that actually exists.

Prefer:

* Date added
* Name A-Z
* Name Z-A
* Favorites first
* Group count, only if group membership counts are readily available without introducing expensive queries

Add format filtering:

* All
* Static
* Motion / Animated
* JPG/JPEG
* PNG
* GIF
* WebP

Do not fabricate metadata that the backend does not currently expose.

---

# 5. Dynamic quick-filter pills

Add horizontally scrollable quick-filter pills near the toolbar.

Do not hardcode semantic content categories such as:

* Blonde
* Dark Hair
* Motion

unless those are actual stored tags in the current data.

Generate useful filters from real metadata.

Potential pills:

* All
* Favorites
* Grouped
* Ungrouped
* GIF
* WebP
* PNG
* JPG

If the image system already has tags or equivalent metadata, dynamically surface commonly used tags rather than creating hardcoded categories.

---

# 6. Replace the current selection panel UX

The current selection-mode controls should no longer push the entire gallery downward.

Replace the large static top selection panel with a **floating glassmorphic bottom action bar**.

Show the bar when one or more images are selected.

It should contain:

* Selected count, e.g. `12 selected`
* Add to Group control
* Remove from Group where contextually valid
* Favorite selected
* Find Similar where existing functionality supports it
* Clear / Done

Preserve all existing backend actions.

Do not rewrite working grouping APIs simply to support the new toolbar.

---

# 7. Improve multi-selection

Implement:

### Standard click selection

Preserve existing behavior.

### Shift + Click range selection

When a user selects one image and then Shift-clicks another, select the contiguous range between them in the currently displayed gallery order.

Range selection must operate on the **currently filtered/sorted order**, not an unrelated original array.

### Do not implement drag-marquee selection yet

Desktop drag-box selection is intentionally deferred.

Do not add it in this pass.

---

# 8. Upgrade group cards

For image-group cards, replace single-cover-only discovery with a **2x2 image collage preview** where enough images exist.

Behavior:

* 4+ images: show first/preferred 4
* 3 images: intelligently fill the 2x2 presentation
* 2 images: balanced split
* 1 image: use the single image
* 0 images: use the current placeholder behavior

Important:

The existing user-selected **group cover image functionality must remain intact**.

If an explicit cover image currently exists, preserve its semantic role.

The collage is for visual discovery and must not silently remove or redefine cover-image behavior.

---

# 9. Lightbox redesign

Refactor the lightbox so the image receives maximum viewport space.

The image should be the primary surface.

Move secondary information into a **collapsible right-side inspector drawer**.

Inspector content should use data that already exists, such as:

* Filename
* Dimensions, if available
* File type
* File size, if already exposed or easily available
* Favorite state
* Group membership
* Group assignment controls
* Existing similarity actions

Do not introduce expensive backend metadata extraction during every lightbox open.

---

# 10. Lightbox keyboard controls

Implement keyboard shortcuts:

* `Left Arrow`: previous
* `Right Arrow`: next
* `F`: toggle favorite
* `Esc`: close lightbox
* `I`: toggle inspector

If `S` can safely trigger the existing similarity function without conflicting with text-input focus:

* `S`: Find Similar

Keyboard shortcuts must not fire when the user is typing in an input, textarea, or editable element.

---

# 11. Filmstrip

Add a collapsible thumbnail filmstrip at the bottom of the lightbox.

Requirements:

* Shows nearby/current gallery images
* Current image clearly highlighted
* Clicking a thumbnail jumps to that image
* Synchronizes with previous/next navigation
* Operates on the currently active filtered/sorted gallery collection
* Does not load every original high-resolution image at once

Persist filmstrip open/closed preference in `localStorage`.

---

# 12. Zoom and pan

Implement useful image inspection controls.

Required behavior:

* Fit image to available viewport by default
* Double-click toggles between:

  * Fit
  * 100%
* When zoomed:

  * Drag to pan
* Provide visible zoom controls if appropriate
* `0`: fit to viewport
* `1`: 100%

Do not hijack normal page scrolling when the lightbox is not active.

Do not make ordinary mouse-wheel scrolling unexpectedly zoom the image unless there is a modifier key or explicit zoom mode.

---

# 13. Slideshow

Slideshow is optional in this implementation.

Only add it after the core gallery, selection, and lightbox changes are stable.

If implemented:

* Start/stop control
* Sensible default interval
* Pause on manual navigation
* Do not autoplay unexpectedly when opening the lightbox

Do not allow slideshow work to delay the core implementation.

---

# 14. Image loading and performance

Improve gallery loading without overengineering.

Implement:

```html
loading="lazy"
decoding="async"
```

where appropriate.

Use progressive/incremental loading or `IntersectionObserver` if the existing page benefits from it.

Avoid layout shift by reserving image dimensions/aspect ratio where practical.

Do **not** introduce full DOM virtualization in this pass.

Do **not** add a major third-party gallery framework unless inspection proves the existing architecture cannot reasonably support the requested functionality.

Do not add unnecessary runtime dependencies.

---

# 15. Preserve mobile and constrained-device usability

The gallery must remain usable on:

* Desktop
* Tablet
* Mobile
* Touch devices
* Meta Quest / VR browser where the existing application already supports it

On smaller screens:

* Collapse the inspector appropriately
* Keep touch targets large enough
* Allow the bottom selection toolbar to wrap or horizontally scroll cleanly
* Avoid hover-dependent actions
* Ensure the filmstrip remains usable without consuming excessive viewport height

Use progressive enhancement rather than desktop-only assumptions.

---

# 16. Accessibility requirements

Maintain or improve:

* Semantic buttons
* `aria-label` where icon meaning is otherwise unclear
* Visible keyboard focus
* Keyboard-accessible toolbar actions
* Sufficient contrast
* Reduced-motion support
* Reduced-transparency behavior where applicable
* Proper modal/lightbox focus handling

When the lightbox closes, return keyboard focus to the image/card that opened it.

---

# 17. Architecture and code organization

Do not turn `gallery.html` into an even larger monolithic script if functionality can be separated cleanly.

Inspect the existing static asset architecture first.

If appropriate, move substantial gallery logic into a dedicated file such as:

```text
static/gallery.js
```

and gallery-specific styling into the most appropriate existing stylesheet or a dedicated gallery stylesheet if that matches the current project organization.

Do not reorganize unrelated frontend code.

Keep changes localized.

---

# 18. Explicitly out of scope

Do not implement:

* Drag-box/marquee selection
* Full DOM virtualization
* AI-generated tagging
* New database architecture
* New group semantics
* New image metadata persistence system
* New image editor
* New authentication model
* Major backend redesign
* Replacement of existing group editing
* Removal of explicit group-cover behavior

---

# 19. Implementation discipline

Before editing, inspect the actual current implementation and determine:

1. Which requested capabilities already partially exist.
2. Which existing functions/routes should be reused.
3. Which event handlers would conflict with the new behavior.
4. How group covers currently work.
5. How group membership is persisted.
6. How favorites are persisted.
7. How Find Similar currently works.
8. Whether gallery data already exposes dimensions, file type, dates, or other metadata.

Do not assume missing functionality without checking the source.

Make the **minimum necessary backend changes**.

The majority of this work should be frontend unless source inspection proves additional backend data is necessary.

---

# 20. Verification

After implementation, verify:

### Gallery

* Masonry mode works
* Uniform mode works
* Density controls work
* Preferences survive refresh
* Portrait images are no longer unnecessarily cropped in masonry mode
* Filtering and sorting work together

### Groups

* Existing groups still load
* Existing cover images still work
* Group editing still works
* Images can still be added and removed
* New collage previews render correctly

### Selection

* Single selection works
* Shift-range selection works
* Bottom toolbar appears/disappears correctly
* Existing batch operations still persist correctly

### Lightbox

* Previous/next works
* Filmstrip stays synchronized
* Inspector opens/closes
* Favorite action persists
* Group actions persist
* Zoom/pan works
* Keyboard shortcuts work
* Focus returns correctly after close

### Responsive

* Desktop
* Narrow desktop
* Tablet
* Mobile/touch layout

### Performance

* Images remain lazy loaded
* No mass eager loading of full-resolution assets
* No excessive number of simultaneous blur surfaces
* No obvious console errors
* No duplicate event handlers

---

# Deliverable

Implement the changes in the existing project.

When finished, report:

1. Files changed
2. What changed in each file
3. Existing functionality reused
4. Any backend changes required and why
5. Anything intentionally deferred
6. Verification performed
7. Any remaining issue that requires an actual product decision

Do not propose another redesign or planning phase unless source inspection reveals a concrete blocker.
