# TODO — UI polish and component workflow

## Purpose

This document is the canonical root task queue for the next pass of work. It focuses on polishing the existing UI, making the main components behave consistently, and improving the workflow so the product feels intentional, premium, and efficient across desktop, tablet, and mobile.

The goal is not to rebuild the app from scratch. The goal is to tighten the experience around the parts that already work: the home page, gallery, watch flow, recommendation system, metadata actions, and selection interactions.

---

## Current checklist status

- [x] Homepage sort and recommendation clarity
- [x] Gallery filter and selection-state clarity
- [x] Lightbox context and detail-view clarity
- [x] Watch page metadata and mobile control polish
- [x] Mobile-first action ergonomics
- [x] Empty/loading and recovery states
- [x] Grouping and organization workflow polish
- [x] Cross-page visual consistency pass
- [x] Recommendation intelligence and trust layer
- [x] Accessibility and keyboard flow
- [x] Performance perception and speed polish
- [x] Documentation and regression verification
- [x] 2026-10-21: Ran Flask development server for testing and validation
- [x] 2026-10-21: Closed Flask server and updated session documentation
- [x] 2026-10-23: Performance Sprint A - completed baseline inspection, audit findings documented, and TODO reconciliation
- [x] 2026-10-23: Performance Sprint B - measurement and repair: updated baseline to 599 videos and 599 thumbnails, repaired missing thumbnail for "Big Tits Mother Id Like to Copulate Doggie Style with Creampie.mp4", measured home/gallery response times (p50/p95)
- [ ] Performance Sprint B: implement thumbnail warming system for missing thumbnails (see docs/SPRINT_B_RECOMMENDATION.md)

### Active milestone

- Release quality pass: the app now includes the finished accessibility, focus, and performance polish needed for a smooth browsing experience.

---

## Design and workflow principles

### 1) Use a shared component language

The app should feel like one product, not a collection of separate pages. This means:

- consistent card shapes and spacing
- consistent button, pill, and badge treatments
- consistent empty/loading states across pages
- consistent metadata row layouts for video and image items
- one vocabulary for actions: view, favorite, tag, play, group, inspect

### 2) Prioritize behavior over cosmetic changes

The best polish does not just look nicer; it reduces confusion and friction. Good UI here means:

- users always know what they are viewing
- filters and sort state are visible and legible
- actions are discoverable without guesswork
- selection states, favorites, and group membership are obvious
- navigation is predictable across pages

### 3) Use a fast, low-risk implementation loop

For this project, the most efficient workflow is:

1. fix the specific component in context
2. confirm the data contract and route contract
3. validate in the browser against the real page state
4. only then move to the next component
5. keep the task scope narrow and high value

This avoids the churn that comes from redesigning multiple surfaces at once without verifying the actual behavior.

---

## Priority order

### P0 — Core trust and usability

#### 1) Home page sort and recommendation clarity

Scope:

- [templates/index.html](templates/index.html)
- [static/styles.css](static/styles.css)

Tasks:

- make sorting state visually explicit across all sorts
- ensure recommendation sort reads as a true personalized view, not a duplicate of rating
- keep the current order direction obvious
- unify sort labels and sort chip behavior across home and gallery surfaces

Definition of done:

- every sort option is clearly labeled and distinguishable
- recommendation view has a clear explanation and feels intentional
- current sort state is visible without hunting through the UI

Status: complete — the homepage sort summary and recommendation explanation are in place and validated in the live UI.

#### 2) Gallery filter and selection-state clarity

Scope:

- [templates/gallery.html](templates/gallery.html)
- [static/js/gallery.js](static/js/gallery.js)

Tasks:

- clarify active filter state, query state, and selection mode at a glance
- make reset actions obvious and easy to trigger
- improve the visual distinction between view mode, filter mode, and selection mode
- keep selection state consistent between cards, toolbar, and lightbox

Definition of done:

- user always knows what subset is on screen
- selection mode reads as a temporary work state, not a hidden mode
- active filter and search state are visible with one quick glance

Status: complete — active filter, query, and selection state are visible and better differentiated in the gallery and lightbox.

#### 3) Lightbox and detail-view polish

Scope:

- [templates/gallery.html](templates/gallery.html)
- [static/js/gallery.js](static/js/gallery.js)

Tasks:

- make details drawer feel clearer and less crowded
- improve keyboard navigation and visual state for next/previous image flow
- tighten zoom, fit, and close behavior so the interaction feels smooth
- ensure favorite and group actions are obvious within the lightbox context

Definition of done:

- moving through images feels focused and intentional
- metadata helps the user understand what is being viewed
- close and navigation flows are consistent and predictable

Status: complete — the active gallery context is now visible in the lightbox header, and the state remains legible while browsing filtered and grouped images.

---

### P1 — Workflow and component consistency

#### 4) Watch page polish and metadata flow

Status: complete — the watch page now has a clearer metadata summary, better tag hierarchy, and a more mobile-friendly action strip that reads as a deliberate media detail surface instead of a bare player shell.

Scope:

- [templates/watch.html](templates/watch.html)
- [templates/_player.html](templates/_player.html)
- [static/js/player.js](static/js/player.js)

Tasks:

- make metadata, tags, rating, and view actions read clearly and consistently
- improve the layout so the page feels like a media hub, not a raw player shell
- add stronger hierarchy around title, metadata, tags, and related content
- improve mobile controls and fullscreen behavior

Definition of done:

- video information is easy to parse on first glance
- tags and metadata feel integrated, not bolted on
- player controls remain usable on small screens

Implementation note:

- a dedicated watch metadata panel groups the video title, action buttons, view count, and tag summary into one clean surface
- the tag editor now reads as a proper metadata block and stacks cleanly on mobile, reducing crowding and improving discoverability during quick browsing sessions

#### 5) Mobile-first action ergonomics

Scope:

- [templates/gallery.html](templates/gallery.html)
- [static/styles.css](static/styles.css)

Tasks:

- make floating action bars more thumb-friendly
- reduce crowded controls on smaller screens
- improve sticky behavior and spacing for touch use
- ensure selection and favorite controls have large hit targets

Definition of done:

- the app remains comfortable in portrait mode
- actions do not feel cramped or accidental
- primary actions remain reachable without awkward hand movement

Status: complete — the floating gallery action bar now stacks into a touch-friendly grid on narrow screens and preserves large tap targets while selection mode is active.

#### 6) Empty/loading and recovery states

Scope:

- [templates/index.html](templates/index.html)
- [templates/gallery.html](templates/gallery.html)
- [static/styles.css](static/styles.css)

Tasks:

- add cleaner empty states for no results, no favorites, empty groups, and stale library states
- add more purposeful loading messages for gallery refresh and metadata scan states
- keep recovery messaging short and actionable

Definition of done:

- users know when the app is loading versus empty versus failed
- status copy is concise and helpful
- users know what action to take next

---

### P2 — Product polish and design maturity

#### 7) Cross-page visual consistency pass

Status: complete — the media cards and action surfaces now share a more intentional visual language across the home page and gallery, with the same card rhythm and emphasis applied consistently.

Scope:

- [templates](templates)
- [static/styles.css](static/styles.css)

Tasks:

- unify card treatment across home page and gallery
- align button, chip, badge, and panel styles across all major surfaces
- reduce visual drift between media surfaces
- tighten spacing and typography hierarchy on cards and metadata blocks

Definition of done:

- the interface looks coherent across all screens
- repeated patterns feel intentional rather than ad hoc
- visual hierarchy supports scanning and action discovery

Implementation note:

- cards now share a stronger border, shadow, and radius language, which makes the library feel like one cohesive product instead of multiple disconnected media surfaces
- home page and gallery list views read with the same structural rhythm, improving perceived quality and clarity at a glance

#### 8) Recommendation intelligence and trust layer

Status: complete — the recommendation logic has been upgraded from a generic popularity and recency ordering into a behavior-aware prediction model that combines recent viewing patterns, tag similarity, title subject overlap, rating signals, and popularity without over-weighting raw view counts alone.

Scope:

- [cache_manager.py](cache_manager.py)
- [database_migration.py](database_migration.py)
- [backend/app/legacy_runtime.py](backend/app/legacy_runtime.py)
- [templates/index.html](templates/index.html)

Tasks:

- deepen recommendation logic around ratings, tags, favorites, and recent plays
- build predictive scoring from recent-view behavior rather than just last-view ordering
- use shared tag and subject overlap as a stronger signal than raw view count alone
- keep recommendations diverse enough to feel useful without repeating the same content pattern
- expose lightweight reasoning to the user without clutter
- ensure the recommendation rail stays trustworthy and useful

Definition of done:

- recommendation behavior feels personal and predictable
- ranked items are not obviously duplicated or mislabeled
- recommendations act as a useful discovery layer, not a dead weight feature
- the recommendation score visibly reflects real behavioral signals and not only the most popular item

Implementation note:

- the new scoring model gives more weight to tag overlap, recent-view behavior, and filename-subject similarity, then adds rating and current popularity as supporting signals
- this makes recommendations feel more intelligent while still favoring genuinely strong content rather than simply the most watched video in the library
- regression verification confirms a similar content match outranks a generic high-view outlier, which keeps the recommendation rail trustworthy and useful

#### 9) Grouping and organization workflow polish

Status: complete — the grouping panel now renders cleaner, more legible cards and clearer Open/Manage actions, reducing the risk of the organization flow feeling hidden or secondary.

Scope:

- [templates/gallery.html](templates/gallery.html)
- [static/js/gallery.js](static/js/gallery.js)
- [database_migration.py](database_migration.py)

Tasks:

- improve legibility of group actions and group counts
- make creating and editing groups more obvious and low-friction
- improve flows for adding/removing images from groups
- ensure states remain visible when newly created or edited groups are saved

Definition of done:

- grouping feels like a purposeful organization flow
- users can understand what group they are in and how to leave it
- the view is not confusing when selection mode is used with groups

Implementation note:

- group cards now include a clearer preview collage, item counts, and explicit Open/Manage actions
- empty states inside the grouping drawer now provide a direct path to create a new group instead of leaving the user with a blank panel

---

### P3 — Accessibility, performance, and maintainability

#### 10) Accessibility and keyboard flow

Scope:

- all interactive templates and JS files

Tasks:

- add visible focus states to cards, pills, dialogs, and action controls
- ensure keyboard users can reach major flows without pointer input
- improve aria labeling on important controls and dialogs
- create consistent focus traps and focus restoration behavior in overlays

Definition of done:

- keyboard navigation works across gallery and lightbox flows
- controls do not disappear or become ambiguous when focused
- screen-reader labels make the UI understandable

#### 11) Performance perception and speed polish

Scope:

- [static/js/gallery.js](static/js/gallery.js)
- [templates/index.html](templates/index.html)
- [templates/gallery.html](templates/gallery.html)

Tasks:

- use debouncing for heavy search and filter updates
- keep the UI responsive while metadata refreshes happen
- optimize perceived loading through skeleton or staggered rendering patterns
- avoid blocking the interface on background operations

Definition of done:

- interactive controls feel immediate
- refresh and search activity does not feel janky or slow
- the app maintains a smooth browsing rhythm

#### 12) Documentation and regression verification

Scope:

- root docs, README, and relevant implementation notes

Tasks:

- keep root task tracking current
- record before/after notes for each component change
- validate major UI flows in the browser after each milestone
- keep implementation notes concise and tied to real behavior

Definition of done:

- each feature update is documented with actual behavior changes
- regressions are caught early by repeatable browser checks
- tasks remain clear and concrete for the next agent or developer

---

## Recommended implementation workflow

### Component-by-component workflow

For each UI element:

1. inspect the actual rendered page and data contract
2. identify the user pain point and the component responsibility
3. make the smallest change that reduces friction
4. validate the result against the live page
5. only then move to the next component

This approach keeps the app stable while producing highly visible improvements.

### Best practice for this project

The best pattern is:

- keep logic and DOM behavior close to the component that owns it
- avoid broad redesigns before the current page is stable
- fix one high-friction set of controls at a time
- prefer readability and consistency over decorative complexity
- verify with real user flows instead of assumptions from static code

---

## Acceptance criteria for the final polish pass

The project should meet the following before considering the UI pass complete:

- the homepage and gallery feel like one product, not disconnected surfaces
- sort and recommendation states are trustworthy and clear
- gallery actions, favorites, and selection state are obvious
- lightbox navigation and metadata are polished and usable
- watch page feel and player behavior are improved for mobile and desktop
- empty, loading, and error states are understandable
- keyboard and accessibility basics are working
- the app feels responsive and intentional rather than utilitarian

---

## Recommended milestone structure

### Milestone 1 — clarity and trust

- homepage sort state
- recommendation explanation
- gallery filter state
- selection mode clarity

### Milestone 2 — flow quality

- lightbox polish
- watch page polish
- mobile action ergonomics
- empty/loading states

### Milestone 3 — design maturity

- cross-page consistency
- group workflow polish
- recommendation trust layer
- accessibility pass

### Milestone 4 — performance foundation

- performance baseline established (see docs/PERFORMANCE_BASELINE.md)
- performance audit completed (see docs/PERFORMANCE_AUDIT_FINDINGS.md)
- MKV streaming and thumbnail generation verified
- performance optimization backlog refined (PERFORMANCE_TODO.md)

### Milestone 5 — release readiness

- performance polish
- regression checks
- final QA and documentation sync

---

## Immediate next steps

1. continue the gallery detail polish and make the active state and lightbox flow clearer
2. tighten the selection and floating action bar on mobile
3. validate the app visually after each change before moving to the next component
4. keep the root task list in sync with what is actually verified in the browser

This keeps the team moving efficiently while preserving the high standard of polish the app already has.
