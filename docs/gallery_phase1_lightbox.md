# Gallery Phase 1 Lightbox Improvements

## What Changed

- The main gallery lightbox now shows filename, position, group memberships, and inline status messages.
- The main gallery lightbox supports favorite toggling, multi-group add, group creation, and pHash "Find Similar" from the open image.
- The group detail lightbox now supports previous/next navigation, favorite toggling, setting the current image as cover, and removing the current image from the group.
- Lightbox panels are constrained to the viewport and scroll internally so controls remain reachable on shorter screens.
- `GET /api/gallery/images/<filename>/groups` returns group memberships for one gallery image.
- Group item deletion is now scoped by both `group_id` and `item_id`, so an item ID cannot remove an image from the wrong group.

## Current Shortcuts

- Main gallery lightbox: `ArrowLeft`, `ArrowRight`, `F`, `G`, `Escape`.
- Group detail lightbox: `ArrowLeft`, `ArrowRight`, `F`, `C`, `Delete`, `Escape`.

