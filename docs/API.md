# Local Video Server API

**Last updated:** 2026-04-23

HTTP surface for the Flask app: HTML pages, JSON APIs, and admin/maintenance endpoints.  
**Source of truth for registration:** `backend/app/factory.py` (plus blueprint modules and `legacy_runtime` view functions).

**Stable public contracts** also summarized in `docs/SOURCE_OF_TRUTH.md`.

---

## 1. Purpose and scope

This document describes the HTTP API of Local Video Server for:

- Human-facing HTML routes
- JSON APIs used by the browser UI and compatible clients
- Admin cache and optional analytics/admin tools

For **product intent** and requirement IDs, see `docs/PRD.md`.  
For **how routes are wired**, see `docs/ARCHITECTURE.md`.

---

## 2. Stable compatibility routes

These URLs are treated as long-lived contracts for bookmarks and integrations:

| Method | Path | Notes |
|--------|------|--------|
| `GET` | `/watch/<path:filename>` | Watch page |
| `GET` | `/video/<path:filename>` | Stream / video delivery |
| `GET` | `/tag/<tag>` | Videos for a tag |
| `GET` \| `POST` | `/api/ratings/<media_hash>` | Canonical ratings JSON |
| `GET` | `/admin/cache/status` | Cache / metadata status |
| `POST` | `/admin/cache/refresh` | Trigger cache refresh |

**Search (navbar + results):**

| Method | Path | Notes |
|--------|------|--------|
| `GET` | `/search` | Query param **`q`** (optional). Token-AND, case-insensitive match over filename / title / tags; relevance sort. |

---

## 3. Health

| Method | Path | Response |
|--------|------|----------|
| `GET` | `/ping` | JSON `{ "status": "ok", ... }` |

| Method | Path | Response |
|--------|------|----------|
| `GET` | `/favicon.ico` | Empty `204` (no body) |

---

## 4. Core HTML / navigation routes

| Method | Path | Endpoint name (Flask) |
|--------|------|------------------------|
| `GET` | `/` | `index` |
| `GET` | `/popular` | `popular_page` |
| `GET` | `/favorites` | `favorites_page` |
| `GET` | `/tags` | `tags_page` |
| `GET` | `/best-of` | `best_of` |
| `GET` | `/links` | `links` |
| `GET` | `/search` | `search_page` |
| `GET` | `/random` | `random_video` |
| `GET` | `/gallery` | `gallery` |
| `GET` | `/gallery/groups/<slug>` | `gallery_group` |
| `GET` | `/gallery/image/<path:filename>` | `serve_gallery_image` |

---

## 5. Ratings API

Canonical JSON surface for the rating widget and compatible clients.

### `GET /api/ratings/<media_hash>`

- **Path:** `media_hash` — stable opaque id for the media item.
- **Headers:** `Accept: application/json`
- **200** body example:

```json
{
  "average": 4.0,
  "count": 1,
  "user": { "value": 4 }
}
```

- **404** if hash cannot be resolved.

### `POST /api/ratings/<media_hash>`

- **Body:**

```json
{ "value": 4 }
```

- **201** on success (summary shape aligned with GET).
- **400** invalid payload/value.
- **404** unknown hash.
- **429** when write rate limit applies.

---

## 6. Legacy compatibility route

### `POST /rate`

- Intentional compatibility wrapper during migration.
- **Body:**

```json
{ "filename": "example.mp4", "rating": 4 }
```

- **Response:**

```json
{ "success": true, "rating": 4 }
```

---

## 7. Tags and favorites (JSON / actions)

| Method | Path | Role |
|--------|------|------|
| `POST` | `/tag` | Add tag (JSON body) |
| `POST` | `/delete_tag` | Remove tag |
| `GET` | `/api/tags/popular` | Popular tags |
| `GET` | `/api/tags/video` | Query: `filename` |
| `POST` | `/favorite` | Toggle favorite |

---

## 8. Views and analytics

| Method | Path | Role |
|--------|------|------|
| `GET` | `/get_views` | Views data route |
| `POST` | `/view` | Record view |
| `POST` | `/analytics/save` | Save analytics payload |
| `GET` | `/analytics/get/<path:filename>` | Per-file analytics |
| `GET` | `/analytics/export` | Export |
| `GET` | `/analytics/stats` | Stats summary |

---

## 9. Gallery JSON APIs

| Method | Path | Role |
|--------|------|------|
| `GET` | `/api/gallery` | List images |
| `GET` \| `POST` | `/api/gallery/groups` | List or create groups |
| `POST` | `/api/gallery/groups/similar` | Similarity helper |
| `GET` | `/api/similar/<kind>/<path:filename>` | Similar media |
| `POST` | `/api/gallery/groups/<int:group_id>/images` | Add images to group |
| `DELETE` | `/api/gallery/groups/<int:group_id>/images/<path:image_path>` | Remove image path |
| `DELETE` | `/api/gallery/groups/<int:group_id>/items/<int:item_id>` | Remove item |
| `PUT` \| `DELETE` | `/api/gallery/groups/<int:group_id>` | Modify or delete group |

---

## 10. Admin / maintenance

| Method | Path | Role |
|--------|------|------|
| `GET` | `/admin/cache/status` | Status JSON |
| `POST` | `/admin/cache/refresh` | Refresh e.g. `{ "success": true, "message": "Cache refreshed" }` |
| `POST` | `/admin/metadata/prune` | Metadata prune (guarded operation) |

Additional admin capabilities may be registered via `register_admin_routes` in `backend/app/admin/routes.py` — consult that module for endpoints beyond the table above.

---

## 11. Related documents

- `docs/PRD.md` — requirements traceability  
- `docs/ARCHITECTURE.md` — module and blueprint layout  
- `docs/SOURCE_OF_TRUTH.md` — runtime DB policy + stable route list  
- `docs/ADMIN_API_SPEC.md` — extended admin dashboard API notes (if present)  
