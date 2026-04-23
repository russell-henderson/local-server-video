# TODO

## Final target architecture

Your selected architecture is the right one for this repo:

* Keep **Flask + Docker Compose**
* Keep `main.py` as a **thin bootstrap entrypoint only**
* Move route families into **blueprints under `backend/app/`**
* Move runtime DB usage to **`data/` only**
* Remove automatic JSON fallback from runtime
* Keep JSON only as **explicit export/backup**
* Use **one rating client controller** and **one backend contract**
* Make **ratings / favorites / tags** the first stabilization lane
* Move `doc/` into `docs/` and archive the rest

That direction matches the actual repo shape, which currently contains:

* a broad Flask surface plus `backend/` partial modularization,
* both `data/` and root-level DB/backup clutter,
* duplicate rating JS files,
* a real `admin-dashboard/`,
* a large docs surface split across `doc/` and `docs/`, and
* a meaningful `tests/` tree that should be reduced to two reporting surfaces, not expanded further.

The README still documents a hybrid DB + JSON runtime model and root-level DB assumptions, which is one of the things that now needs to be corrected to match the new design.  

---

## Audit conclusion

### What is actually wrong

1. **Architecture drift**

   * `main.py` is still too large and owns too many concerns.
   * `backend/` exists but is only partially authoritative.

2. **Metadata path drift**

   * The repo currently has `data/video_metadata.db` and `data/video_search.db`, but also root-level DB files and backup DB files.
   * That makes it too easy for runtime, scripts, docs, and Docker mounts to disagree.

3. **Ratings UI drift**

   * The repo contains both `static/js/rating.js` and `static/js/ratings.js`.
   * The current behavior strongly suggests they are overlapping and competing.
   * This is the most likely cause of the broken stars.

4. **Favorites page bug surface**

   * Favorites behavior is not stable enough today and should be fixed in the first lane alongside ratings and tags.

5. **Docs drift**

   * `doc/` and `docs/` both exist.
   * `docs/` also contains archive and deferred content while `doc/` still holds active-looking material.

6. **Testing surface is too noisy**

   * There are many targeted pytest files now.
   * You do not need more files. You need fewer suite entry points and cleaner categorization.

---

## Recommended target file structure

```text
local-video-server/
├── admin-dashboard/
├── backend/
│   ├── app/
│   │   ├── factory.py
│   │   ├── extensions.py
│   │   ├── media/
│   │   │   └── routes.py
│   │   ├── metadata/
│   │   │   └── routes.py
│   │   ├── tags/
│   │   │   └── routes.py
│   │   ├── gallery/
│   │   │   └── routes.py
│   │   ├── admin/
│   │   │   └── routes.py
│   │   └── api/
│   │       └── ratings.py
│   ├── repositories/
│   │   ├── metadata_repository.py
│   │   ├── video_repository.py
│   │   ├── gallery_repository.py
│   │   └── search_repository.py
│   ├── services/
│   │   ├── metadata_service.py
│   │   ├── ratings_service.py
│   │   ├── video_catalog.py
│   │   ├── gallery_service.py
│   │   └── metadata_cache.py
│   └── db/
│       ├── migrations.py
│       └── bootstrap.py
├── data/
│   ├── video_metadata.db
│   └── video_search.db
├── backups/
│   └── ...
├── docs/
│   ├── archive/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   ├── SOURCE_OF_TRUTH.md
│   ├── TODOS.md
│   └── TESTING.md
├── nginx/
├── scripts/
│   ├── dev/
│   ├── maintenance/
│   ├── audit/
│   └── test/
├── static/
│   ├── css/
│   │   ├── app.css
│   │   ├── theme.css
│   │   ├── player-controls.css
│   │   └── links.css
│   ├── js/
│   │   ├── features/
│   │   │   ├── ratings.js
│   │   │   ├── favorites.js
│   │   │   ├── tags.js
│   │   │   └── player.js
│   │   ├── pages/
│   │   │   ├── home.js
│   │   │   ├── watch.js
│   │   │   ├── favorites.js
│   │   │   ├── gallery.js
│   │   │   └── admin.js
│   │   └── lib/
│   │       ├── dom.js
│   │       └── api.js
│   └── thumbnails/
├── templates/
│   ├── partials/
│   │   ├── icons.html
│   │   └── rating.html
│   ├── _base.html
│   ├── _navbar.html
│   ├── _player.html
│   ├── index.html
│   ├── watch.html
│   ├── favorites.html
│   ├── tags.html
│   ├── gallery.html
│   ├── gallery_group.html
│   └── admin/
├── tests/
│   ├── test_smoke_suite.py
│   └── test_regression_suite.py
├── main.py
├── docker-compose.yml
├── docker-compose.override.yml
├── Dockerfile
├── Makefile
└── requirements.txt
```

---

## Reorganization plan

## Phase 1. Stabilization first

Do this before larger internal moves.

### Ratings

* Remove duplicate/competing client rating logic.
* Keep a single rating controller.
* Standardize one DOM contract for the reusable rating partial.
* Ensure ratings appear and function on:

  * home/index cards
  * watch page main video
  * favorites cards
  * recommendation/related cards
  * any other video thumbnail surface

### Favorites

* Fix route/template mismatches.
* Ensure the favorites page uses the correct endpoint names.
* Ensure toggle behavior and persistence are DB-first and reflected on all pages.

### Tags

* Import sidecar tags into DB.
* Keep DB as the only runtime read/write source after import.
* Remove runtime sidecar merge logic once import is complete and verified.

## Phase 2. Backend modularization

* Keep `main.py`, but reduce it to app bootstrap only.
* Create blueprints for:

  * media
  * metadata
  * tags
  * gallery
  * admin
* Move runtime DB operations out of `database_migration.py`.
* Keep migrations/bootstrap there only.

## Phase 3. Data/runtime cleanup

* Move runtime authority to:

  * `data/video_metadata.db`
  * `data/video_search.db`
* Remove root-level runtime DB usage.
* Disable automatic JSON fallback.
* Keep explicit export/backup scripts only.
* Standardize backup snapshots under `backups/`.

## Phase 4. Frontend cleanup

* Move inline CSS out of templates.
* Standardize shared template partials.
* Reorganize JS into `features/`, `pages/`, and `lib/`.
* Keep the visual design consistent. Clean internals, not the look.

## Phase 5. Docs consolidation

* Move active content into `docs/`.
* Archive `doc/`.
* Create or refresh:

  * `docs/ARCHITECTURE.md`
  * `docs/API.md`
  * `docs/DEPLOYMENT.md`
  * `docs/TESTING.md`
  * `docs/SOURCE_OF_TRUTH.md`
  * `docs/TODOS.md`

## Phase 6. Test consolidation

Do not just smash all assertions into one giant file blindly.
Best approach:

* reduce the reporting surface to **two suites**
* collapse redundant tests where practical
* keep coverage high on the critical contract

### Smoke suite

Covers:

* app boots
* home loads
* watch loads
* stream route works
* ratings API round-trip
* favorites toggle
* tags read/write baseline
* admin health/cache endpoints

### Regression suite

Covers:

* metadata persistence correctness
* rating mapping/hash invariants
* tag import + DB-only read path
* favorites persistence
* watch page rating widget presence
* gallery/group behavior
* prune guards / admin guards
* CORS/rate-limiting contract where still relevant

---

## Non-negotiable acceptance criteria

Cursor should treat these as hard requirements:

1. **Public routes remain stable**

   * `/watch/<filename>`
   * `/video/<filename>`
   * `/tag/<tag>`
   * `/api/ratings/<media_hash>`
   * `/admin/cache/status`
   * `/admin/cache/refresh`

2. **Ratings must work everywhere**

   * thumbnail cards
   * watch page
   * favorites
   * recommendations

3. **DB-only runtime**

   * no automatic JSON fallback at runtime

4. **Tag truth**

   * sidecars imported once
   * DB authoritative afterward

5. **Compose remains the baseline**

   * Flask app
   * nginx proxy
   * admin dashboard preserved

6. **Visual design remains consistent**

   * no gratuitous redesign
   * internal cleanup only

---

## Cursor prompt

Use this exactly or with only minor local-path edits:

```text
You are working on the Local Video Server repo.

Objective:
Perform a full structural cleanup and stabilization pass in one branch, but preserve the current product identity and public route contract. The highest-priority lane is ratings, favorites, and tags reliability. Do not do a visual redesign. Keep Flask + Docker Compose. Keep main.py, but convert it into a thin bootstrap entrypoint only.

Authoritative decisions already made:
1. Keep Flask + Docker Compose.
2. Keep main.py as a thin bootstrap/shim only.
3. Move route families into blueprints under backend/app/.
4. Move runtime DB usage to data/ only.
5. Remove automatic JSON fallback from runtime.
6. Keep JSON only as explicit export/backup.
7. Import sidecar tags into DB, then use DB only at runtime.
8. Consolidate rating logic into one client controller and one backend contract.
9. Make ratings/favorites/tags the first stabilization lane before larger cleanup.
10. Move active doc/ content into docs/ and archive the rest.
11. Reduce tests to two reporting surfaces: smoke suite and regression suite.
12. Preserve existing public route contracts unless a compatibility wrapper is added.

Hard guardrails:
- Do not break these routes:
  - /watch/<filename>
  - /video/<filename>
  - /tag/<tag>
  - /api/ratings/<media_hash>
  - /admin/cache/status
  - /admin/cache/refresh
- Preserve current dark premium UI direction.
- Do not introduce a new framework.
- Do not remove Docker Compose.
- Do not silently change runtime DB file paths without updating config, Docker mounts, docs, and code together.
- No automatic JSON fallback at runtime after this refactor.
- Ratings must work on every video surface:
  - home/index cards
  - watch page main video
  - favorites page cards
  - related/recommended video cards
  - any reusable thumbnail/card component

Current repo issues to address:
1. main.py still owns too many concerns and must be reduced to bootstrap only.
2. Runtime data paths are split across root and data/.
3. The repo contains both static/js/rating.js and static/js/ratings.js. Consolidate to one rating controller only.
4. Favorites page behavior is unstable and likely has route/template mismatch problems.
5. Tag truth is mixed. Import sidecar tags into the DB, then switch runtime reads/writes to DB only.
6. doc/ and docs/ are both active enough to create confusion.
7. Tests are fragmented and should report through two suites only.

Target architecture:
- backend/app/factory.py
- backend/app/media/routes.py
- backend/app/metadata/routes.py
- backend/app/tags/routes.py
- backend/app/gallery/routes.py
- backend/app/admin/routes.py
- backend/repositories/
- backend/services/
- backend/db/
- main.py as bootstrap only
- data/video_metadata.db and data/video_search.db as runtime DBs
- docs/ as the only active docs root
- tests/test_smoke_suite.py
- tests/test_regression_suite.py

Execution order:
Phase 1: stabilize ratings/favorites/tags first
Phase 2: modularize backend routes into blueprints
Phase 3: move runtime DB usage to data/ only
Phase 4: remove runtime JSON fallback and convert JSON to explicit export/backup only
Phase 5: consolidate docs into docs/
Phase 6: consolidate tests into smoke + regression suites

Required backend work:
- Create an app factory and blueprint registration flow.
- Keep main.py but make it a thin bootstrap file only.
- Move runtime DB operations out of database_migration.py into repositories/services.
- Keep database_migration.py for schema/bootstrap/migration utilities only.
- Split cache_manager.py by responsibility only where it materially improves maintainability:
  - metadata cache
  - video catalog
  - gallery service
  - metadata service if needed
- Do not over-fragment for vanity.

Required frontend work:
- Use one rating JS controller only.
- Standardize one DOM/API contract for rating widgets.
- Reuse the rating partial everywhere.
- Remove inline or duplicate rating logic.
- Fix favorites page route/template wiring.
- Keep the current UI look and layout feel.

Required data work:
- Import sidecar tags into the DB.
- Add or use an explicit migration/import path.
- After successful import, remove runtime sidecar merge logic.
- Runtime reads/writes for tags/favorites/ratings/views must be DB-first and DB-only.
- Keep JSON only as explicit export/backup output, not fallback behavior.

Required docs work:
- Move active material from doc/ into docs/.
- Archive or remove obsolete material.
- Refresh:
  - docs/SOURCE_OF_TRUTH.md
  - docs/ARCHITECTURE.md
  - docs/API.md
  - docs/DEPLOYMENT.md
  - docs/TESTING.md
  - docs/TODOS.md
- Make docs reflect DB-only runtime, data/ DB paths, current Compose topology, and the actual blueprint structure.

Required tests:
- Consolidate reporting to:
  - tests/test_smoke_suite.py
  - tests/test_regression_suite.py
- Preserve meaningful coverage for:
  - app boot
  - home route
  - watch route
  - video stream route
  - ratings API read/write
  - ratings widget presence on key pages
  - favorites toggle and favorites page behavior
  - tag import + DB-only read path
  - admin cache endpoints
  - gallery/group baseline behavior
- Prefer fewer clearer suites over many tiny files.

Output requirements:
1. First, print a concise audit summary of what you found and what you are changing.
2. Then implement the changes.
3. Then print the final file move summary.
4. Then print the final route blueprint map.
5. Then print any archived/deleted files list.
6. Then print the exact commands to run:
   - smoke suite
   - regression suite
   - local Flask run
   - Docker Compose run
7. Then print any known risks still remaining.

Success criteria:
- App boots locally and in Docker Compose.
- Public routes remain stable.
- Ratings work everywhere.
- Favorites page works.
- Tags are DB-authoritative at runtime.
- main.py is bootstrap only.
- docs are consolidated into docs/.
- Tests report through two suites only.
```

---

## Best implementation stance

Even though you chose a full reorg path, the safest interpretation is:

* **single branch**
* **single coordinated pass**
* but executed in the order above so the metadata lane is fixed before deeper movement

That gives you the reorg you want without turning the first patch into chaos.

## Highest-priority fixes to expect first

1. Remove duplicate rating JS and standardize one rating widget contract.
2. Fix favorites page route/template bug.
3. Ensure rating partial is used on related/recommended cards too.
4. Lock metadata runtime to DB.
5. Then modularize backend routes.
6. Then consolidate docs/tests.

That is the strongest version of the plan for this repo as it exists today.
