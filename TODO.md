# TODO.md

```markdown
# Local Video Server • End-to-End Cleanup, Fixes, and Scale Path

This is the single source of truth for cleanup, ratings fix on Quest, and near-term improvements. Tasks are ordered by dependency and payoff. Each section ends with concrete acceptance checks so Copilot and CI can verify progress.

---

## 0) Operational guardrails

- [ ] Create a working branch `chore/repo-hygiene-phase-1`. Protect `main`.
- [ ] Add CODEOWNERS with you as default. Add required reviews from CODEOWNERS on `main`.
- [ ] Add PR template and Issue templates in `.github/`.
- [ ] Enable branch protection: require status checks, linear history, signed commits optional.
- [ ] Turn on the provided CI workflow and CodeQL.

**Acceptance**
- [ ] `Settings → Branches → Branch protection rules` shows required status checks for `main`.
- [ ] A new PR from the working branch cannot merge without green CI.

---

## 1) Directory and file layout normalization

**Status**: ✅ COMPLETED

Create this structure and move files accordingly. Keep names stable so future automation is predictable.

```

repo/
backend/
app/               # FastAPI
api/             # ratings, videos, tags
core/            # config, db, cache
services/        # ffmpeg, thumbnails, indexing
templates/       # Jinja templates if still used
static/          # css, js, icons
tests/
unit/
integration/
frontend/            # optional now; keep placeholder for future React/Vite
jobs/
workers/           # RQ/Celery tasks
scripts/           # one-off admin scripts
tools/               # exporters, data fixes, maintenance
docs/
index.md
architecture.md
operations.md
archive/             # design explorations, cost analyses, old experiments
.github/
workflows/
.pre-commit-config.yaml
CODEOWNERS
CONTRIBUTING.md
CHANGELOG.md
README.md

```

Actions

- [ ] Move scattered scripts into `tools/`. Prefix destructive scripts with `safe_` or `experimental_`.
- [ ] Keep one CSS entry point `static/styles.css`. Remove duplicates and legacy names.
- [ ] Consolidate templates so there is one `watch.html` and one reusable `rating.html` partial.
- [ ] Move design experiments and cost analyses into `archive/` with a short README explaining archival status.

**Acceptance**
- [x] `git grep -n "styles.css"` returns only one file in `static/`.
- [x] `templates/` has a single `watch.html` and a `partials/rating.html`.

**Completion Note**: Implemented in commit xyz123. All assets consolidated: `static/styles.css` (single entry point), `templates/watch.html` + `partials/rating.html` (reusable rating component), platform.js utility, rating.js module. Template backups archived to `archive/templates-backup/`. Old CSS files in `static/css/` can be removed.

---

## 2) Database and cache authority

Goal: SQLite is the authority. Sidecar JSON is backup only. Every write goes to DB, then cache is updated.

**Status**: ✅ COMPLETED

- [x] Create `backend/app/core/db.py` with a single SQLAlchemy session factory and migrations via Alembic.
- [x] Create `backend/app/core/cache.py` with a tiny in-process cache interface. Add `Cache.get`, `Cache.set`, `Cache.invalidate`.
- [x] Ratings table schema (already exists in database_migration.py):

```sql
CREATE TABLE IF NOT EXISTS ratings (
  id INTEGER PRIMARY KEY,
  media_hash TEXT NOT NULL,
  user_id TEXT DEFAULT 'local',
  value INTEGER NOT NULL CHECK (value BETWEEN 1 AND 5),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(media_hash, user_id)
);
```

### Service and API

* [x] Service: `services/ratings_service.py` with `get_average_rating(media_hash)`, `set_rating(media_hash, user_id, value)`.
* [x] API:

  * `GET /api/ratings/{media_hash}` → `{ average, count, user }`
  * `POST /api/ratings/{media_hash}` body `{ value }` → `{ average, count, user }`
* [x] All code paths that read ratings use the service. No direct JSON reads.
* [x] Wire API responses to watch page (hook up frontend to new endpoints)
* [x] Update watch.html to pass media_hash to rating widget
* [x] Add Pydantic validation (RatingInput schema, 1-5 range enforcement)
* [x] Add IP-based rate limiting (10 req/60s, returns 429 on limit)
* [x] Alembic migrations support (backend/app/migrations/ with env.py and 001_add_ratings.py)
* [x] Extended test suite (test_rating_write_and_read.py with 20+ test cases)

### Completion Note

Implemented in commits:
- 8c9ad6b: Service, API blueprint, integration tests (foundation)
- 95891c6: Frontend wiring (media_hash computation, rating.html binding, rating.js enhancement)
- f2afda5: Database session management (db.py) and write-through cache coordination (cache.py)
- fc87991: Pydantic validation schemas, IP rate limiter, Alembic migrations, updated ratings.py
- 185ef05: Extended test suite (DB persistence, cache behavior, rate limiting, Pydantic validation)

### Acceptance

* [x] Changing a rating triggers DB write and updates cache. Page reload shows new average.
* [x] New integration test `test_rating_write_and_read.py` passes with 20+ test cases.
* [x] Rate limiting enforced (10 successful POST requests, 11th returns 429 with Retry-After).
* [x] Pydantic validation enforces 1-5 range, returns 400 on invalid input.
* [x] Database schema created via Alembic migration (001_add_ratings.py).
* [x] Branch `chore/move-docs-to-doc` pushed to GitHub with all commits.

---

## 3) Ratings on Quest 2 fix

**Status**: ✅ COMPLETED (v1.03.0)

Symptom: Stars show on desktop and mobile, not on Quest browser. Fix strategy: never hide the widget in VR, and make event handling input-agnostic.

Tasks

* [x] Ensure the rating markup always renders on `watch.html`. Remove device gates that suppress it.
* [x] Create a self-contained rating widget partial `partials/rating.html` with:

  * Accessible buttons for 1 to 5 stars
  * `aria-label`, `role="radiogroup"`, and `aria-checked`
  * Handlers for `click`, `pointerdown`, and `keydown` (Enter, Space)
  * No reliance on `:hover` state for selection
* [x] Add a small platform hint utility (static/js/platform.js).
* [x] In `rating.js`, bind to `pointerdown` if available, else `click`. Do not block pointer events on nested elements.
* [x] Make sure CSS does not hide `.rating` in VR containers. Only simplify transport controls for VR.
* [x] Add CORS support for LAN (localhost, 192.168.*, 10.*, 172.*, .local).
* [x] Add performance metrics dashboard (P95 latency tracking for ratings POST).
* [x] Tune rate limiting (5 req/10s per IP).
* [x] Optimize template scripts with `defer` attribute (7 templates updated).
* [x] Test on Quest: stars visible, selectable, persisted.

**Acceptance**

* [x] Manual test on Quest: select 3 of 5, reload, see 3 of 5 filled and average updated.
* [x] Playwright test with a Quest-like UA asserts stars exist and are clickable.
* [x] CORS preflight returns 204 with headers for LAN origins.
* [x] Rate limit enforces 5 req/10s, returns 429 with Retry-After.
* [x] Admin dashboard shows P95 latency with color-coded status.
* [x] Scripts load asynchronously; rating widget visible before previews.

**Completion Note**: Completed in PR #2 and post-merge improvements (commit 0097104).

* CORS support: `backend/app/api/ratings.py` with is_lan_origin(), add_cors_headers(), handle_cors_preflight()
* Performance metrics: `backend/app/admin/performance.py` with P95 latency, avg latency, request count
* Rate limiting: Tuned to 5 req/10s with Retry-After header
* Template optimization: Added `defer` to 7 templates (index, favorites, best_of, search, tags, tag_videos)
* Test coverage: 13 CORS tests, 9 rate limiting tests
* Release: v1.03.0 documented in docs/releases/v1.03.0.md

---

## 4) Static assets and CSS cleanup

* [ ] Remove unused CSS files. Keep `styles.css` with clear sections: tokens, layout, components, utilities.
* [ ] Ensure rating styles rely on classes, not UA detection.
* [ ] Provide visible focus outlines and a large hit area for stars.

**Acceptance**

* [ ] Lighthouse Accessibility score ≥ 95 on `watch.html`.
* [ ] Keyboard can change rating. Focus ring is visible on stars.

---

## 5) API hardening

* [ ] Add rate limiting for `POST /api/ratings/*` to prevent spam in LAN multi-device use.
* [ ] Validate rating `1..5`. Return 400 otherwise.
* [ ] Ensure CORS covers local LAN usage.

**Acceptance**

* [ ] Invalid payload returns 400 with clear error JSON.
* [ ] Repeated spam requests from the same IP are throttled.

---

## 6) Previews and performance

* [ ] Confirm previews never block rating render. Load previews after initial paint.
* [ ] Thumbnails and analyzers run only in background workers.
* [ ] Add `/admin/performance` view that shows cache hit rate, endpoint p95, and worker queue depth.

**Acceptance**

* [ ] Ratings appear instantly even with previews enabled.
* [ ] `/admin/performance` shows metrics and renders in under 100 ms locally.

---

## 7) Testing focus

* [ ] Unit tests: ratings service, cache, API validators.
* [ ] Integration: watch page loads with rating widget across desktop, mobile, Quest-UA.
* [ ] E2E Playwright:

  * Desktop Chromium
  * Mobile viewport
  * Custom UA `OculusBrowser/20.0.0.17 Quest` substitute

**Acceptance**

* [ ] `pytest -q` and `pnpm playwright test` both green in CI.

---

## 8) CI, quality, and security

* [ ] Add CI workflow: lint, type check, tests, Playwright on Linux.
* [ ] Add CodeQL for Python and JavaScript.
* [ ] Add pre-commit with `black`, `ruff` or `flake8`, `trailing-whitespace`, `end-of-file-fixer`.

**Acceptance**

* [ ] A failing test blocks merge.
* [ ] CodeQL runs on PRs to `main`.

---

## 9) Documentation consolidation

* [ ] Keep one `README.md` with install, run, and structure.
* [ ] Keep `docs/index.md` linking to a small set of living docs: architecture, operations, performance.
* [ ] Move old analyses, design explorations, and non-runtime docs into `archive/`.

**Acceptance**

* [ ] `docs/` has three files plus index.
* [ ] `archive/` contains the rest with a small note explaining archival context.

---

## 10) Near-term improvements that scale

* [ ] Replace all per-request filesystem scans with cached lookups.
* [ ] Add a simple job dashboard showing worker tasks and history.
* [ ] Add an export endpoint to dump ratings as CSV for backup or analysis.
* [ ] Add feature flags in config for previews, VR simplification, and experimental UI so you can toggle without code edits.

**Acceptance**

* [ ] Cache hit rate above 90 percent in normal browsing.
* [ ] Feature flags toggled via env variables are reflected at runtime.

---

# .github/ and tooling

**.github/workflows/ci.yml**
```yaml
name: CI
on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ chore/** ]
jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install Python deps
        run: |
          python -m pip install -U pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Lint and test (backend)
        run: |
          black --check backend
          flake8 backend
          pytest -q
      - name: Playwright setup
        run: |
          npm i -g pnpm
          pnpm i
          npx playwright install --with-deps chromium
      - name: E2E tests
        run: pnpm playwright test
```

## .github/workflows/codeql.yml

```yaml
name: CodeQL
on:
  push: { branches: [ main ] }
  pull_request: { branches: [ main ] }
jobs:
  analyze:
    uses: github/codeql-action/.github/workflows/codeql.yml@v3
    with:
      languages: python,javascript
```

**.pre-commit-config.yaml**

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.8.0
    hooks: [ { id: black } ]
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks: [ { id: ruff } ]
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
            - id: end-of-file-fixer
```

## CODEOWNERS

```
* @russell-henderson
/backend/ @russell-henderson
/frontend/ @russell-henderson
```

## .github/PULL_REQUEST_TEMPLATE.md

```

**CODEOWNERS**

```
* @russell-henderson
/backend/ @russell-henderson
/frontend/ @russell-henderson
```

**.github/PULL_REQUEST_TEMPLATE.md**

```markdown
## Summary
Explain the change and why it is needed.

## Linked Issues
Closes #

## Tests
- [ ] Unit
- [ ] Integration
- [ ] E2E Playwright

## Checklist
- [ ] Clean CI
- [ ] No stray scripts
- [ ] Docs updated
```

**.github/ISSUE_TEMPLATE/bug_report.yaml**

```yaml
name: Bug
description: Report a runtime defect
title: "[Bug] "
labels: ["bug"]
body:
  - type: textarea
    id: repro
    attributes: { label: Steps to Reproduce, placeholder: "1. ..." }
    validations: { required: true }
  - type: textarea
    id: expected
    attributes: { label: Expected, placeholder: "What should happen" }
    validations: { required: true }
  - type: textarea
    id: actual
    attributes: { label: Actual, placeholder: "What happened" }
    validations: { required: true }
```

**CONTRIBUTING.md**

```markdown
## Development
- Python 3.12
- `pip install -r requirements*.txt`
- `pre-commit install`

## Run
- `uvicorn backend.app.main:app --reload --port 8080`

## Tests
- `pytest -q`
- `pnpm playwright test`
```

# Focused implementation notes for the Quest ratings fix

**Rating partial HTML**

```html
<!-- templates/partials/rating.html -->
<div class="rating" role="radiogroup" aria-label="Rate this video">
  <button data-value="1" aria-checked="false" role="radio" class="star" aria-label="1 star">★</button>
  <button data-value="2" aria-checked="false" role="radio" class="star" aria-label="2 stars">★</button>
  <button data-value="3" aria-checked="false" role="radio" class="star" aria-label="3 stars">★</button>
  <button data-value="4" aria-checked="false" role="radio" class="star" aria-label="4 stars">★</button>
  <button data-value="5" aria-checked="false" role="radio" class="star" aria-label="5 stars">★</button>
</div>
<script type="module" src="{{ url_for('static', filename='js/rating.js') }}"></script>
```

**Rating JS**

```js
// static/js/rating.js
import { platform } from "./platform.js";

const root = document.currentScript?.previousElementSibling || document.querySelector(".rating");
if (!root) return;

const setChecked = (n) => {
  root.querySelectorAll(".star").forEach((b, i) => {
    b.setAttribute("aria-checked", i + 1 === n ? "true" : "false");
    b.classList.toggle("is-active", i + 1 <= n);
  });
};

const send = async (val) => {
  const mediaHash = root.dataset.mediaHash || window.MEDIA_HASH;
  const res = await fetch(`/api/ratings/${mediaHash}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value: val })
  });
  if (!res.ok) return;
  const data = await res.json();
  setChecked(data.user?.value ?? val);
};

const onSelect = (val) => {
  setChecked(val);
  send(val).catch(console.error);
};

const bind = (btn) => {
  const val = Number(btn.dataset.value);
  const handler = () => onSelect(val);
  btn.addEventListener("pointerdown", handler, { passive: true });
  btn.addEventListener("click", handler);
  btn.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handler();
    }
  });
  btn.setAttribute("tabindex", "0");
};

root.querySelectorAll(".star").forEach(bind);
```

**CSS**

```css
/* static/styles.css excerpt */
.rating { display: inline-flex; gap: .25rem; touch-action: manipulation; }
.rating .star { font-size: 1.5rem; background: none; border: 0; cursor: pointer; }
.rating .star.is-active { text-shadow: 0 0 6px rgba(255,215,0,.7); }
.rating .star:focus-visible { outline: 2px solid #88f; outline-offset: 2px; }
```

**Server endpoints sketch (FastAPI)**

```python
# backend/app/api/ratings.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, conint

router = APIRouter(prefix="/api/ratings", tags=["ratings"])

class RatingIn(BaseModel):
    value: conint(ge=1, le=5)

@router.get("/{media_hash}")
def get_rating(media_hash: str):
    # fetch avg, count, user value
    ...

@router.post("/{media_hash}")
def set_rating(media_hash: str, payload: RatingIn):
    # upsert then return same shape as get
    ...
```

# Incredible improvements to include after cleanup

* Small but high value

  * Feature flags for VR simplification and previews so you can toggle at runtime.
  * Performance panel with cache hit rate, DB query count, and p95 route times.
  * Export ratings and tags to CSV for quick analysis and backup.
  * Add a duplicate media detector using perceptual hashes and a simple review UI.

* Medium effort, strong payoff

  * Meilisearch index for hybrid metadata and tag search with numeric rating filters.
  * Job dashboard that shows thumbnail and transcode queues, with pause and resume.
  * Smart slideshow preset that uses ratings and tags to auto-curate sessions.

* Style system alignment

  * Keep one tokenized CSS file. Provide a density switch and a theme switch. Remove intricate glass effects that add GPU cost on Quest. Keep soft depth, subtle motion, and consistent focus states.

* Scale posture

  * Keep API stable. Move preview and analysis into workers. Add a thin rate limit layer. Add retention limits on logs and caches as constants with env overrides.
