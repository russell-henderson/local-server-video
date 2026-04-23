Here is an updated `TODO_GROUP_DELETE.md` that matches what you just described.

````md
# TODO_GROUP_DELETE - Refine Group Delete UX

## Goal

Keep the current delete behavior for gallery groups, but make the user experience safer and clearer:

- Delete is no longer always visible on group cards.
- Delete is accessed through an Edit Group workflow.
- Deleting a group still removes only the group and memberships, never the underlying image files.
- Images from a deleted group return to the loose "All Images" gallery.

Backend and API behavior are already correct. This task is front end only.

---

## 1. Current behavior (do not change logic)

Already implemented:

- `DELETE /api/gallery/groups/<id>` removes the group and its rows in `gallery_group_items` (via CASCADE).
- Files in `images/gallery` are not deleted.
- `/gallery` route rebuilds `My Groups` and `All Images`, so images from deleted groups automatically reappear as loose images.
- Front end:
  - `gallery.html` shows each group card with a visible trash icon and a click handler that calls DELETE and reloads the page.
  - `gallery_group.html` header shows both "Edit Group" and "Delete Group" buttons side by side.

These behaviors are correct functionally. We are changing only how and where Delete is exposed in the UI.

---

## 2. Update gallery.html - remove always visible delete icon

File:

- `templates/gallery.html`

### 2.1 Remove delete icon from group cards

In `displayGroups(groups)`:

- Remove the trash button from the group card markup.
- Remove any per-card delete click handlers attached directly to `.group-delete-btn` on the gallery cards.

The group card in the Gallery view should return to being simple navigation:

- Cover image.
- Group name.
- Image count.

No visible delete control on this card.

If a shared `deleteGroup` function is defined in this file and still used elsewhere, keep it. Otherwise, simplify it so that only the group detail page uses it (see section 3).

### 2.2 Keep layout styling

- Keep `.group-card-info`, `.group-card-text`, and grid sizing as currently tuned.
- Only remove or repurpose `.group-delete-btn` styles if they are no longer needed for gallery cards.

The goal is to preserve the compact layout you just achieved.

---

## 3. Update gallery_group.html - delete only inside Edit Group

File:

- `templates/gallery_group.html`

### 3.1 Header buttons

In the group header:

- Keep **Edit Group** as the primary button.
- Remove the separate **Delete Group** button from the header.

The header should show:

- Group name.
- Image count.
- One main action button: "Edit Group" (or whatever label you are already using).

### 3.2 Place Delete inside Edit Group section

Find the existing Edit Group UI in `gallery_group.html` (the section that already lets you:

- Toggle edit mode.
- Remove images from the group.
- Possibly add or manage images).

Inside that edit area:

- Add a visually separated "Danger zone" or destructive action block at the bottom of the edit panel.

Example structure:

```html
<div class="group-edit-danger">
  <h3>Danger zone</h3>
  <p>Delete this group. Images will not be deleted. They will return to All Images.</p>
  <button id="deleteGroupBtn" class="btn btn-danger btn-sm">
    🗑 Delete Group
  </button>
</div>
````

You can reuse your existing button classes for styling, but the key is that this block appears only when Edit mode is active.

### 3.3 Wire up delete handler in edit mode

Attach the delete handler to the new `deleteGroupBtn` in the script block of `gallery_group.html`:

* When clicked:

  1. Show a confirmation dialog that includes the group name and clearly states that images will not be deleted, for example:

     `Delete group "<group name>"? This removes the group and its memberships only. The images will stay in your gallery and return to All Images.`

  2. If confirmed, call `DELETE /api/gallery/groups/<id>` using `fetch`.

  3. On success, redirect to `/gallery`:

     ```js
     window.location.href = '/gallery';
     ```

  4. On error, log to console and show an alert.

Important:

* This logic can reuse any existing `deleteGroup` function you already wrote, but update it to be called from the new button instead of the old header button.
* Make sure the delete handler is only available when the page knows the current `groupId`.

---

## 4. Keep existing image edit behavior

Inside the group edit UI:

* Keep the current ability to remove images from the group.
* When an image is removed from the group, it should already return to the loose gallery via the existing backend and `/gallery` route logic.
* Do not change this behavior, only ensure it remains part of Edit Group.

At a conceptual level:

* Edit Group controls image membership and group metadata.
* Delete Group is the final destructive action within that same edit context.

---

## 5. Styling and UX guidelines

* The delete controls must not appear unless Edit mode is active.
* The delete button should use a clear red style to communicate it is destructive, but it should be visually secondary to the rest of the edit controls.
* Text should always reassure the user that:

  * Images are not deleted.
  * Only the group container is removed.

---

## 6. Acceptance criteria

* Gallery view (`/gallery`):

  * Group cards in "My Groups" have no visible trash icon.
  * Clicking a card still navigates to the group detail page.

* Group detail view (`/gallery/groups/<slug>`):

  * Header shows only "Edit Group" (no always visible Delete Group button).
  * When Edit Group mode is active, a "Danger zone" section appears with a red Delete Group button and explanation text.
  * Clicking Delete Group prompts for confirmation, calls `DELETE /api/gallery/groups/<id>`, and on success redirects back to `/gallery`.
  * After deletion, the group no longer appears in My Groups, and its images appear again as loose items in All Images.

* No image files are removed from disk.

* No changes are made to backend Python logic or database schema.
