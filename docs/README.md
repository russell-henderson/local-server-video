# Local Video Server documentation

Last updated: 2026-10-09

This folder contains the deeper technical and product docs for the app. For the project quick-start and release summary, use the root [README.md](../README.md). The root README is the canonical entry point for developers and git-facing summary updates.

## Documentation guide

| Document | Purpose |
|----------|---------|
| [../README.md](../README.md) | Root project overview, quick start, and release summary |
| [PRD.md](PRD.md) | Product goals and scope |
| [SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md) | Runtime constraints and source-of-truth rules |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture and data flow |
| [API.md](API.md) | route and API reference |
| [DEPLOYMENT.md](DEPLOYMENT.md) | local and deployment workflows |
| [TESTING.md](TESTING.md) | test and validation guidance |
| [DATA_BACKEND.md](DATA_BACKEND.md) | SQLite/data backend detail |
| [UI.md](UI.md) | UI patterns and design notes |
| [PROJECT.md](PROJECT.md) | broader project overview and indexes |
| [TODOS.md](TODOS.md) | supplemental docs-side checklist |
| [CHANGELOG.md](CHANGELOG.md) | git-facing changelog |

## Current state

The app is in an active release-quality pass. The current emphasis is on verifying the live UI, stabilizing the gallery flow, and keeping the recommendation and accessibility work aligned with actual runtime behavior.

## Root project entry points

- root README: [../README.md](../README.md)
- active task list: [../TODO.md](../TODO.md)
- docs changelog: [CHANGELOG.md](CHANGELOG.md)

## Release note

Recent verified work includes:

- live gallery page and image-serving validation
- gallery render and keyboard-flow stabilization
- recommendation intelligence refinement based on behavioral signals
- accessibility and performance polish pass
- updated documentation and changelog sync
