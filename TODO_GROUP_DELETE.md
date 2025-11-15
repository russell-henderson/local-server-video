You are thinking about it the right way.

Groups should be virtual containers only. Deleting a group should:

* Remove the group record and its group_items rows in SQLite
* Leave the actual files in `images/gallery` untouched
* Let those files show up again in **All Images** the next time the gallery loads

Good news: your backend is already set up for this.

* `DELETE /api/gallery/groups/<group_id>` exists
* `VideoDatabase.delete_gallery_group()` deletes from `gallery_groups`
* `gallery_group_items` has `ON DELETE CASCADE`, so it only drops memberships
* The `/gallery` route builds `grouped_images` from all current groups and filters them out of the loose list

So once a group is deleted, its images are no longer in any group, which means the `grouped_images` set no longer contains them and they automatically return to the loose gallery.

What you need now is just front end wiring. Here is a `TODO_GROUP_DELETE.md` you can hand to Copilot.

````md
# TODO - Gallery group delete behavior

## Goal

Add a way to delete gallery groups from the UI without deleting any image files.

Behavior:

- Deleting a group removes only the group and its membership rows in SQLite.
- Image files in `images/gallery` are never removed.
- After deleting a group, its images show up again under **All Images**.

Backend and database logic for this already exists. This task is front end only.

---

## 1. Confirm existing endpoints and behavior

Files to inspect:

- `main.py`
  - `@app.route('/api/gallery/groups/<int:group_id>', methods=['PUT', 'DELETE'])`
- `database_migration.py`
  - `delete_gallery_group(self, group_id: int)`
  - `gallery_groups` and `gallery_group_items` schema (ON DELETE CASCADE)

Expected behavior (do not change):

- `DELETE /api/gallery/groups/<group_id>` calls `delete_gallery_group`.
- `delete_gallery_group` deletes only from `gallery_groups`.
- `gallery_group_items` rows are removed by `ON DELETE CASCADE`.
- No image files in `images/gallery` are touched.
- `/gallery` route:
  - Loads all filenames from `images/gallery`.
  - Builds `grouped_images` set from `db.get_gallery_groups()` and `db.get_group_images(id)`.
  - Filters `images = [img for img in images if img not in grouped_images]`.

This logic already guarantees that once a group is gone, its images are treated as loose again.

---

## 2. Add delete control on group cards in gallery.html

File:

- `templates/gallery.html` (script section and group card rendering in `displayGroups(groups)`)

### 2.1 Update group card markup

In `displayGroups(groups)`, update the `groupCard.innerHTML` so that:

- It still links to `/gallery/groups/${group.slug}` when clicking the main card.
- It includes a small delete button in the card footer.

Example structure:

```js
groupCard.innerHTML = `
  <div class="group-card-image">
    ... existing img logic ...
  </div>
  <div class="group-card-info">
    <div class="group-card-text">
      <h3>${group.name}</h3>
      <small>${group.image_count || 0} images</small>
    </div>
    <button
      type="button"
      class="group-delete-btn"
      data-group-id="${group.id}"
      aria-label="Delete group ${group.name}"
    >
      🗑
    </button>
  </div>
`;
````

Notes:

* Keep `groupCard` as an `<a>` so the card is still clickable.
* The delete button is inside the card but will use `stopPropagation()` so it does not navigate.

### 2.2 Hook up delete click handler

After appending each `groupCard` to `groupsGrid`, attach a listener to the delete button:

```js
const deleteBtn = groupCard.querySelector('.group-delete-btn');
deleteBtn.addEventListener('click', async (event) => {
  event.preventDefault();
  event.stopPropagation();

  const groupId = deleteBtn.dataset.groupId;
  const confirmed = window.confirm(
    `Delete group "${group.name}"?\nImages will not be deleted; they will return to the main gallery.`
  );
  if (!confirmed) return;

  try {
    const resp = await fetch(`/api/gallery/groups/${groupId}`, {
      method: 'DELETE'
    });
    if (!resp.ok) {
      throw new Error(`Failed with ${resp.status}`);
    }

    // Reload the gallery so:
    // - Group card disappears
    // - Images from that group show up again in "All Images"
    window.location.reload();
  } catch (err) {
    console.error('Delete group error:', err);
    alert('Failed to delete group: ' + err.message);
  }
});
```

Key points:

* Use `preventDefault` and `stopPropagation` so the click does not trigger navigation.
* Confirm with the user before sending the DELETE.
* On success, reload the page to refresh both groups and All Images.

### 2.3 Styling the delete button

In the `<style>` block of `gallery.html`:

* Add a small control that fits into the existing group card info row.

Example:

```css
.group-card-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: rgba(25, 25, 25, 0.9);
}

.group-card-text h3 {
  margin: 0 0 4px;
  font-size: 1rem;
}

.group-card-text small {
  font-size: 0.85rem;
  color: #aaa;
}

.group-delete-btn {
  border: none;
  background: transparent;
  color: #ff6b81;
  padding: 4px 6px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.95rem;
}

.group-delete-btn:hover {
  background: rgba(255, 107, 129, 0.15);
}
```

Make sure it looks consistent with the dark theme and other controls.

---

## 3. Optional: delete from group detail page

File:

* `templates/gallery_group.html`

Add a secondary button next to **Edit Group**:

```html
<button id="deleteGroupBtn" class="btn btn-outline-danger btn-sm">
  🗑 Delete Group
</button>
```

In the script block:

```js
const deleteGroupBtn = document.getElementById('deleteGroupBtn');
deleteGroupBtn.addEventListener('click', async () => {
  const confirmed = window.confirm(
    `Delete group "${groupName}"?\nImages will not be deleted; they will return to the main gallery.`
  );
  if (!confirmed) return;

  try {
    const resp = await fetch(`/api/gallery/groups/${groupId}`, {
      method: 'DELETE'
    });
    if (!resp.ok) {
      throw new Error(`Failed with ${resp.status}`);
    }
    window.location.href = '/gallery';
  } catch (error) {
    console.error('Error deleting group:', error);
    alert('Failed to delete group: ' + error.message);
  }
});
```

This gives a clear delete entry point while editing a specific group.

---

## 4. Acceptance criteria

* Clicking the trash icon on a group card:

  * Prompts for confirmation.
  * On confirm, calls `DELETE /api/gallery/groups/<id>`.
  * Group card disappears from **My Groups**.
  * Images that used to be in the group appear in **All Images**, as long as they are not in any other group.
* Deleting from the group detail page (if implemented) behaves the same and redirects back to `/gallery`.
* No image files are removed from disk.
* No new backend or database changes are introduced.
