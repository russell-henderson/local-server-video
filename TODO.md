Continue P03 from the targeted runtime defect discovered during final sign-off.

This is NOT a redesign or reopening of the rating implementation.

# Current Canonical State

Already accepted and complete:

- playlist-level rating implementation
- global video rating architecture
- database migration
- playlist rating API/service/UI
- video rating hydration in playlists
- cross-scope isolation
- Docker runtime
- Check 1: queue item playback PASS
- Check 2: autoplay behavior PASS
- Check 3: queue navigation PASS

Only Check 4 failed.

# Targeted Defect

Inside `templates/playlist_view.html`, each playlist queue entry is clickable to invoke `playAtIndex(...)`.

The existing video rating component is now rendered inside those clickable queue entries.

When a user clicks a `.rating .star` button inside a non-current queue item, that click bubbles into the parent queue-item playback handler.

Observed behavior:

- rating star clicked;
- parent queue click handler also executes;
- playback switches to that queue item;
- intended rating interaction fails.

Example:

Current:
`Jocelyn Baker - Mommy wants a baby.mp4`

Rating clicked on:
`Jocelyn Baker - Mommy Needs.mp4`

Expected:
- rating updates;
- current video continues playing.

Observed:
- playback switches to `Jocelyn Baker - Mommy Needs.mp4`;
- rating does not update.

# Required Fix

Implement the smallest safe event-isolation fix.

Preferred behavior:

- clicks inside the video `.rating` control must be handled by the existing `static/js/ratings.js`;
- those clicks must not invoke playlist queue playback;
- ordinary clicks elsewhere on the queue item must continue to invoke `playAtIndex(...)`;
- keyboard accessibility of the rating buttons must remain intact;
- do not alter the `/rate` endpoint or global rating semantics;
- do not modify playlist-level rating architecture.

Inspect the existing queue event implementation before choosing the exact solution.

A valid minimal approach may be to make the queue click handler ignore events originating inside `.rating`, for example conceptually:

if (event.target.closest('.rating')) {
    return;
}

Alternatively, stop propagation at the playlist rating interaction boundary if that is safer in the existing implementation.

Choose whichever produces the smallest, clearest fix without altering unrelated behavior.

# Scope

Likely affected:

- `templates/playlist_view.html`

Possibly affected only if necessary:

- `static/js/ratings.js`

Prefer not to modify `ratings.js` if the defect can be isolated locally in the playlist viewer.

Do not touch:

- database schema
- migrations
- playlist service
- rating service
- `/rate`
- playlist rating API
- playlist-rating.js
- unrelated playlist UI
- playlist editing

# Validation Required

After applying the fix, validate inside the active Docker environment.

Run the existing playlist rating tests to confirm no regression.

Then manually repeat Check 4.

Test at least two non-current queue items.

For each test record:

Current playing video:
Queue item whose rating was clicked:
Rating selected:
Rating before:
Rating after:
Playing video after click:

Required result:

- rating successfully changes;
- playback remains on the original current video.

Then perform one ordinary click on a non-current queue item and confirm:

- queue playback still works normally.

This proves that event isolation did not disable legitimate queue navigation.

# Required Return

Return:

## P03 Targeted Defect Closeout

### Root Cause
Brief technical explanation.

### Files Changed
path:
exact change:

### Validation

#### Rating click isolation test 1
current video:
rated video:
rating before:
rating selected:
rating after:
playing video afterward:
result:

#### Rating click isolation test 2
current video:
rated video:
rating before:
rating selected:
rating after:
playing video afterward:
result:

#### Normal queue click
selected video:
playback switched correctly:
result:

### Automated Tests
exact command:
result:

### Docker Runtime
container:
status:

### Scope Confirmation
Confirm no database, API, persistence, playlist-level rating, or unrelated playlist behavior was changed.

### Final Status

Use exactly one:

TARGETED DEFECT CLOSED
TARGETED DEFECT REMAINS OPEN

If all validation passes, state:

P03 is ready for full closure.