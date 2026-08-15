You are beginning **P04: Responsive Multi-Screen UI Validation** for the Local Video Server.

This phase is **inspection and evidence collection only**.

Do not redesign the interface.
Do not make code changes.
Do not invent breakpoints or responsive behavior before inspecting the actual implementation.

# Objective

Inspect the real Local Video Server templates, CSS, JavaScript, and runtime assumptions to determine where responsiveness currently succeeds, where it fails, and where behavior is uncertain across:

- small phones
- large phones
- tablets
- laptops
- standard desktops
- large desktops
- ultrawide displays
- televisions / large-format displays
- Meta Quest 2 browser

The goal is to return a **responsive-gap report grounded in the current source and runtime**, with no speculative redesign assumptions.

# Canonical P04 Status

Project: P04 Responsive Multi-Screen UI
Status: IN PROGRESS
Phase: Responsive implementation inspection

Current authority boundary:

- inspection: AUTHORIZED
- runtime validation: AUTHORIZED
- source modification: NOT AUTHORIZED
- redesign: NOT AUTHORIZED
- breakpoint redesign: NOT AUTHORIZED
- component replacement: NOT AUTHORIZED
- major UX/layout decisions: require Russell only if inspection proves they are materially necessary

# Required Inspection Scope

Inspect the current versions of the relevant project files.

At minimum inspect:

templates/_base.html
templates/index.html
templates/watch.html
templates/playlist_view.html
templates/playlists_hub.html
templates/tags.html
templates/favorites.html
templates/gallery.html
templates/gallery_group.html

static/styles.css
static/css/*.css

static/js/player.js
static/js/playlists.js
static/js/ratings.js

docker-compose.yml
docker-compose.override.yml if present

Also inspect any additional template, stylesheet, JavaScript, or configuration file that materially affects layout, navigation, viewport behavior, player sizing, grids, or responsive interaction.

Do not assume the listed files are exhaustive.

# What to Inspect

## 1. Global layout behavior

Identify:

- body/page width rules
- max-width containers
- full-width regions
- gutters
- margins
- horizontal padding
- vertical spacing
- centered vs left-aligned page regions
- fixed-position elements
- sticky elements
- viewport-height assumptions
- `overflow-x`
- `overflow-y`
- hard-coded dimensions
- layout rules that behave differently across viewport widths

Flag anything likely to produce:

- horizontal scrolling
- clipped content
- excessive empty space
- content stretched too wide
- content compressed too tightly
- unusable viewport-height layouts

## 2. Existing responsive breakpoints

Inventory every meaningful:

- `@media`
- `min-width`
- `max-width`
- `min-height`
- `max-height`
- orientation rule
- aspect-ratio rule
- container-query rule if any

For each breakpoint identify:

file:
selector/component:
condition:
behavior changed:

Also identify overlapping or conflicting media queries.

Do not recommend replacing breakpoints yet.

## 3. Fixed-size assumptions

Identify important uses of:

- fixed `px` widths
- fixed heights
- `min-width`
- `min-height`
- absolute positioning
- large fixed margins
- fixed font sizes
- fixed thumbnail sizes
- fixed control widths
- `100vh`
- `100vw`
- hard-coded player dimensions

Distinguish between:

- harmless fixed values
- intentional design constraints
- potentially problematic responsive assumptions

Do not label every pixel value as a defect.

## 4. Navigation

Inspect the current navigation and header system.

Determine:

- how it behaves on small widths
- whether menu items wrap
- whether there is mobile collapse behavior
- whether content remains centered
- whether branding collides with navigation
- whether controls become too small
- whether there are hover-only interactions
- whether keyboard focus remains visible
- whether large-screen layouts stretch awkwardly

Report actual implementation behavior, not preferred design behavior.

## 5. Video player and watch experience

Inspect the video player layout carefully.

Determine:

- width behavior
- height behavior
- aspect-ratio behavior
- portrait phone behavior
- landscape phone behavior
- tablet behavior
- desktop behavior
- large-screen behavior
- fullscreen assumptions
- surrounding metadata layout
- control wrapping
- overlays
- player container constraints

Identify any JS calculations that depend on viewport dimensions.

Do not change playback logic.

## 6. Playlist viewer

Inspect:

- player/queue relationship
- queue width
- queue height
- scrolling behavior
- thumbnails
- titles
- rating controls
- metadata
- current-playing state
- touch/click targets
- keyboard targets
- narrow viewport behavior
- wide viewport behavior

The recently completed P03 rating architecture is canonical and must not be redesigned.

Only report responsive issues involving those controls.

## 7. Content grids and cards

Inspect:

- main video grid
- playlist cards
- favorites
- tags
- gallery
- gallery groups
- search/results where applicable

For each determine:

- how columns are selected
- minimum card width
- wrapping behavior
- image sizing
- text truncation
- overflow
- extreme-wide behavior
- extreme-narrow behavior

## 8. Component-level responsiveness

Inspect significant shared components such as:

- buttons
- rating stars
- tags/chips
- forms
- dropdowns
- modals
- cards
- search fields
- metadata rows
- playlist controls
- thumbnails
- headers
- empty states

Flag components that materially risk unusable layout or interaction at certain viewport sizes.

## 9. Input-method assumptions

Inspect whether interactions depend on:

- hover
- precise mouse positioning
- tiny targets
- mouse-specific events
- touch-specific events
- keyboard access
- focus states

Consider intended environments:

desktop:
mouse + keyboard

phone/tablet:
touch

TV / large display:
mouse, keyboard, remote-like or pointer-based input may be used

Quest 2:
browser/controller pointer interaction

Do not claim Quest 2 compatibility from CSS inspection alone.

## 10. JavaScript responsive assumptions

Inspect JS for behavior dependent on:

- `window.innerWidth`
- `window.innerHeight`
- resize events
- orientation events
- hard-coded dimensions
- CSS class changes by viewport size
- dynamic player sizing
- touch detection
- hover detection
- mobile user-agent assumptions

Report any fragile or duplicated responsive logic.

# Runtime Inspection

Use the existing Docker environment.

Do not modify source.

Confirm the running application and use the real UI where practical.

Evaluate representative viewport classes such as:

Small phone:
approximately 360 × 800

Modern phone:
approximately 390 × 844

Large phone:
approximately 430 × 932

Tablet portrait:
approximately 768 × 1024

Tablet landscape:
approximately 1024 × 768

Laptop:
approximately 1366 × 768

Desktop:
approximately 1920 × 1080

Large desktop:
approximately 2560 × 1440

Ultrawide:
approximately 3440 × 1440

4K / TV:
approximately 3840 × 2160

These are inspection targets, not authorized CSS breakpoint definitions.

If browser tooling allows viewport emulation, use it for evidence collection.

# Quest 2 Boundary

Quest 2 is explicitly in scope, but desktop emulation must not be reported as actual Quest 2 runtime validation.

During this inspection classify Quest-related findings as one of:

SOURCE-VERIFIED
DESKTOP-EMULATION-OBSERVED
ACTUAL-QUEST-2-VALIDATION-REQUIRED

Identify which behaviors will eventually require testing on the physical Quest 2 browser.

# Evidence Standard

For every reported gap, provide evidence.

Good evidence includes:

- exact file
- selector or component
- relevant code excerpt
- viewport where observed
- actual runtime behavior
- screenshot reference if available
- why it is a responsiveness problem

Avoid statements such as:

"this should probably be more responsive"

Instead use:

"At 390px width, `.example` retains `min-width: 600px`, producing horizontal document overflow."

# Gap Classification

Classify every meaningful finding as:

CONFIRMED GAP
POTENTIAL GAP
WORKING AS INTENDED
RUNTIME VALIDATION REQUIRED
RUSSELL DECISION MAY BE REQUIRED

Use `RUSSELL DECISION MAY BE REQUIRED` only when source/runtime inspection proves that there is a genuine UX or layout choice with materially different valid options.

Do not escalate ordinary implementation choices unnecessarily.

# Severity

For confirmed gaps, assign:

CRITICAL
HIGH
MEDIUM
LOW

Use severity based on actual usability impact.

Examples:

CRITICAL:
core page or player unusable at intended screen class

HIGH:
major controls inaccessible, clipped, or functionally broken

MEDIUM:
significant layout degradation but functionality remains available

LOW:
minor spacing, visual balance, or polish issue

# Required Return Format

Return exactly this structure.

## P04 Responsive Gap Report

### 1. Environment

machine:
repository path:
Docker service:
container:
application URL:
runtime status:

### 2. Files Inspected

List every relevant file inspected.

### 3. Existing Responsive Architecture

Summarize the responsive system that actually exists.

Include:

- layout approach
- breakpoint strategy
- shared containers
- grid behavior
- player behavior
- navigation behavior
- responsive JS behavior

Do not propose changes in this section.

### 4. Breakpoint Inventory

For each meaningful breakpoint:

file:
condition:
affected component:
actual behavior:

### 5. Confirmed Working Areas

List responsive behavior that inspection shows is already functioning acceptably.

This is important so later implementation does not unnecessarily rewrite working behavior.

### 6. Confirmed Responsive Gaps

For each gap use:

ID:
severity:
screen class:
page/component:
file:
selector/code:
evidence:
observed behavior:
expected functional outcome:
scope of likely correction:

Do not prescribe redesign unless the correction is obvious and purely technical.

### 7. Potential Gaps Requiring More Validation

For each:

ID:
screen/environment:
reason uncertain:
validation needed:

### 8. Large-Screen / TV Findings

Report specifically on:

- 1920×1080
- 2560×1440
- ultrawide
- 3840×2160 / TV-class layouts

Identify excessive stretching, undersized UI, poor content density, or large-format interaction concerns only where observed.

### 9. Phone and Tablet Findings

Report separately on:

- small phone
- modern phone
- large phone
- tablet portrait
- tablet landscape

### 10. Quest 2 Findings

Separate:

SOURCE-VERIFIED:
DESKTOP-EMULATION-OBSERVED:
ACTUAL-QUEST-2-VALIDATION-REQUIRED:

Do not claim actual Quest 2 validation unless performed on the physical device.

### 11. Input and Accessibility Findings

Report responsive interaction concerns involving:

- touch targets
- hover dependency
- keyboard focus
- pointer/controller suitability
- clipping or inaccessible controls

### 12. Proposed Change Categories

Do not implement anything.

Group validated gaps into likely categories such as:

- global layout correction
- navigation correction
- player sizing correction
- grid correction
- component reflow
- large-format scaling
- input-target correction
- Quest-specific validation

For each category list the validated gaps it would address.

### 13. Russell Decisions Potentially Required

If none:

None.

If genuine decisions are required, provide:

decision ID:
validated reason:
option A:
option B:
material tradeoff:

Do not ask Russell to decide implementation details that can be resolved technically.

### 14. Risks

Identify any implementation risks discovered by inspection.

Do not invent risks without evidence.

### 15. Recommended Implementation Boundary

Provide the smallest evidence-based implementation scope that would address the confirmed gaps.

Do not begin implementation.

### 16. Final Inspection Status

Use exactly one:

INSPECTION COMPLETE
INSPECTION COMPLETE WITH RUNTIME GAPS
BLOCKED

# Stop Condition

Do not modify any source file.

Do not begin responsive implementation.

Do not redesign.

Return the inspection evidence to CoS for reconciliation first.

The next authorized step after this report will be:

CoS reconciliation
→ Russell decisions only if genuinely necessary
→ approved P04 implementation scope
→ implementation