# Latest Changes (Past 24h)

Date: 2025-12-09

- Gallery favorites unified across all images: heart icons now appear on loose images and those inside groups, and the Favorites filter aggregates every favorited item.
- Gallery tiles simplified: removed filename overlays for a cleaner grid while keeping selection mode and group actions intact.
- Favorites filtering made robust: selection ranges, lightbox navigation, and toggle states now track the active filtered list correctly.
- Group view refinements: group images show favorite hearts, retaining cover selection and delete controls without altering grouping behavior.

Notes:
- Favorites are stored locally (browser `localStorage`), so they persist per browser/device.
- Grouping remains virtual; adding to a group removes it from the loose grid but favorites still surface everywhere via the Favorites filter.
