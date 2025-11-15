Got it, that makes sense. Group creation/editing is already working, we are only tightening up the layout and card sizing in `gallery.html` and its inline CSS.

Here is an updated `TODO.md` that matches the actual state of the project and what you showed in the screenshots. You can drop this straight into the repo for Copilot.

This pass only updates templates/gallery.html layout and its inline CSS. Styling for gallery_group.html will be handled in a separate TODO.

````md
# TODO - Gallery layout and sizing polish

## Goal

Refine the Gallery UI so that:

- Group cards under **My Groups** are smaller and denser.
- Image thumbnails under **All Images** are smaller and show more items per row.
- The layout stays consistent with the existing dark theme and lightbox behavior.
- No backend, database, or grouping logic is changed.

All work happens in the existing `templates/gallery.html` file and its inline `<style>` block, plus any minimal related tweaks in `static/styles.css` if absolutely required.

---

## 1. Confirm current structure (read only)

Files to inspect:

- `templates/gallery.html`
- `static/styles.css` (for any global gallery related styles)

Important existing pieces:

- Header:

  ```html
  <div class="gallery-header">
    <h1 class="mb-0">Gallery</h1>
    <div class="gallery-controls">
      <button class="selection-toggle-btn" id="selectionToggle">📋 Selection Mode</button>
      <span class="selection-info" id="selectionInfo">
        Selected: <strong id="selectedCount">0</strong>
      </span>
    </div>
  </div>
````

* Actions panel (create group, add to group, clear selection): `.selection-actions`, `.action-section`, `.action-btn`, `.action-inputs`.

* Groups container:

  ```html
  <div id="groupsSection">
    <h2 class="mt-4 mb-3">My Groups</h2>
    <div class="gallery-grid" id="groupsGrid"></div>
  </div>
  ```

* Images container:

  ```html
  <h2 class="mt-4 mb-3">All Images</h2>
  <div class="gallery-grid" id="galleryGrid">
    <!-- .gallery-item cards go here -->
  </div>
  ```

* Group cards are created in JS with:

  * `class="group-card"`
  * Inner elements: `.group-card-image` and `.group-card-info`

* Image cards use:

  * `class="gallery-item"`
  * Inner elements: `.gallery-item-checkbox`, `<img>`, `.gallery-item-overlay`, `.gallery-item-title`

Do not change this structure or any JS logic that creates or manages groups. Only adjust styles and, if needed, add CSS classes or wrappers that do not break the existing behavior.

---

## 2. Separate layout rules for groups and images

Current problem: both groups and images share `.gallery-grid` and similar card dimensions, which makes everything look oversized.

### 2.1. Adjust `.gallery-grid` to be a base helper

* In the `<style>` block of `gallery.html`, change `.gallery-grid` to a base grid helper:

  ```css
  .gallery-grid {
    display: grid;
    gap: 20px;
    padding: 16px 0;
  }
  ```

  Keep it simple. Remove the hard coded `grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));` from this base rule.

### 2.2. Add specific rules for groups and images

* Add separate grid configuration for the two sections:

  ```css
  /* My Groups layout */
  #groupsGrid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
    padding-bottom: 24px;
  }

  /* All Images layout */
  #galleryGrid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 16px;
    padding-bottom: 40px;
  }
  ```

* If needed, tweak the `minmax` values slightly to make the page feel well balanced on a 1080p desktop, but keep groups a bit wider than individual image tiles.

---

## 3. Resize group cards

Group cards currently feel as tall as image thumbnails. The goal is a compact card with name and count.

### 3.1. Reduce group image height

* Locate and update:

  ```css
  .group-card-image {
    width: 100%;
    height: 280px;  /* current */
    overflow: hidden;
    border-radius: 12px 12px 0 0;
  }
  ```

* Change to something like:

  ```css
  .group-card-image {
    width: 100%;
    height: 200px;
    overflow: hidden;
    border-radius: 12px 12px 0 0;
  }
  ```

  If supported in this CSS context, you can use `aspect-ratio: 4 / 3` instead of a fixed height, but keep it visually shorter than the old 280px.

### 3.2. Compact group info panel

* Locate `.group-card-info` and adjust padding and text sizes to be slightly smaller:

  ```css
  .group-card-info {
    padding: 12px;
    background: rgba(25, 25, 25, 0.8);
  }

  .group-card-info h3 {
    margin: 0 0 4px;
    font-size: 1rem;
  }

  .group-card-info small {
    font-size: 0.85rem;
    color: #aaa;
  }
  ```

* Keep hover effect and click behavior unchanged, only lighten the visual weight if needed (for example slightly smaller shadow).

---

## 4. Resize image thumbnails

The **All Images** tiles should be smaller so more images fit on screen.

### 4.1. Reduce image height

* Locate the existing rule for image tiles:

  ```css
  .gallery-item img {
    width: 100%;
    height: 280px;  /* current */
    object-fit: cover;
    display: block;
  }
  ```

* Change to:

  ```css
  .gallery-item img {
    width: 100%;
    height: 200px;
    object-fit: cover;
    display: block;
  }
  ```

  Use a similar height to group images so the two sections feel related.

### 4.2. Keep selection and overlay intact

* Ensure that these existing pieces still work with the new size:

  * `.gallery-item-checkbox` (selection checkbox in a corner)
  * `.gallery-item-overlay` and `.gallery-item-title`

If the overlay text starts to feel cramped:

* Slightly reduce the font size of `.gallery-item-title`.
* Make sure the overlay still has enough padding to remain legible.

---

## 5. Visual separation between sections

Make it very clear where **My Groups** ends and **All Images** begins.

* Add margin below the groups section:

  ```css
  #groupsSection {
    margin-bottom: 16px;
  }
  ```

* Ensure headings use a consistent scale:

  * `h1` for "Gallery" (already present)
  * `h2` for "My Groups" and "All Images"

No need to change heading tags in the HTML, just make sure CSS keeps them visually consistent.

If needed, you may add a very subtle divider line above "All Images" using a border or pseudo element attached to that section, but stay in line with the existing theme styling.

---

## 6. Selection Mode sizing

Selection Mode is already wired up and working. Only adjust its visual weight.

* Keep the header structure as is. Do not move elements or add new toolbars.
* Optionally tighten the button and label:

  * Slightly reduce padding on `.selection-toggle-btn`.
  * Slightly reduce the font size on `.selection-info`.

Make sure the button remains clearly interactive and matches existing button styling used elsewhere in the app.

---

## 7. Responsive adjustments

There are existing `@media` rules in the gallery `<style>` block.

* Update the mobile and small tablet breakpoints so they match the new component sizes.

Guidelines:

* On large desktop widths, both My Groups and All Images should show multiple columns.
* On tablets, two or three columns is acceptable.
* On narrow phones, one card per row is fine.

Double check that:

* Checkboxes remain usable on smaller screens.
* Hover-only states are not required to understand selection; the checkbox must always be visible in Selection Mode.

---

## 8. Do not change these

For this task, do not modify:

* Any Python backend code.
* Any database tables or grouping logic.
* The logic that creates or edits groups in JavaScript.
* Lightbox open and close logic, except for size and positioning that may be affected by the new card dimensions.

Focus only on CSS and minimal template level styling so the existing behavior looks cleaner and more compact.
