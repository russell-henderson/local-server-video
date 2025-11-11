# Copilot Work Plan and Checklist Protocol

## Objective

Deliver a clean, scalable Local Video Server with:

1) Ratings working on Quest 2
2) Consolidated docs and code
3) Fast, stable runtime with clear tests and CI

## Sources of truth

- Primary: `TODO.md` in repo root
- Secondary: files referenced by tasks inside `TODO.md`
- Never invent files or paths. If a referenced path is missing, propose the minimal file with correct content.

## Workflow

1) Read `TODO.md` from top to bottom.
2) Pick the highest priority unchecked task whose dependencies are met.
3) Create or update files to complete the task with the smallest correct change set.
4) Run and update tests in the same branch.
5) Update `TODO.md` by checking the completed box and add a brief note that links to the commit or PR.
6) Open or update a PR with a clear description and acceptance checks.
7) Repeat.

## Task selection rules

- Respect task order unless a later task unblocks many items at once with low risk.
- If a task lists Acceptance steps, implement them exactly.
- If a task lists canonical files, prefer those and remove duplicates.

## Editing rules

- Rewrite entire affected files when touched so diffs are coherent.
- Remove dead code, throwaway scripts, and duplicate styles when a task instructs it.
- Keep a single CSS entry point `static/styles.css`.
- Keep one `templates/watch.html` and one `templates/partials/rating.html`.

## Ratings on Quest 2

- Always render the rating partial on `watch.html`.
- Input handlers must support pointer, click, and keyboard.
- Do not rely on hover for any required interaction.
- Do not hide ratings in any VR container.
- Add Playwright coverage with a Quest-like user agent.
- Update `TODO.md` Acceptance checks as you pass them.

## Tests and CI

- Add or update unit, integration, and Playwright tests for each feature changed.
- All tests must pass locally and in CI before checking boxes in `TODO.md`.

## Commit strategy

Use small, descriptive commits:

- `chore(repo): normalize static css to styles.css`
- `feat(ratings): add accessible pointer and keyboard handlers`
- `fix(vr): always render rating partial on watch page`
- `test(e2e): add Quest UA rating interaction`

## PR protocol

Title format:

- `[scope] short summary` for example `ratings: make stars work on Quest`

Body checklist:

- Summary of change
- Linked TODO items
- Acceptance results
- Test evidence

## Updating TODO.md

When completing an item:

- Change `- [ ]` to `- [x]`
- Add a short line after the item with a commit link or PR number, for example:
  - `Completed in #1234 (commit abc123).`
- If you split a task, indent sub-items and check them. Check the parent only when all sub-items are done.

## Definition of Done

- Code compiles, tests pass, CI green
- `TODO.md` updated with checked box and link
- No duplicate files left behind
- Docs updated if behavior changed
- Accessibility preserved or improved

## Safety rails

- Do not remove files unless the task instructs it or a duplicate replacement exists.
- Do not change public API shapes without updating tests and docs.
- Prefer small PRs that map one-to-one with TODO items.

## Project hygiene

- Use pre-commit hooks if present.
- Keep `archive/` for non-runtime materials.
- Keep `docs/` minimal and current. Move outdated notes to `archive/` with a short reason.

## First actions to take

1) Normalize directory layout and static assets per `TODO.md`.
2) Implement `partials/rating.html`, `static/js/rating.js`, and the platform utility, then wire into `watch.html`.
3) Add Playwright tests for desktop, mobile, and Quest user agent paths.
4) Update `TODO.md` checkboxes with links to your PRs.

## When unsure

- Propose the smallest safe change.
- Add a short comment in the PR with the decision and why it is reversible.
