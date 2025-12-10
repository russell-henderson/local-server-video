# Release notes index

This page lists releases for Local Video Server.

## v1.03.0 - Post-PR #2 improvements (released 2025-11-11)

- Link: [v1.03.0 release page](./v1.03.0.md)
- Features: CORS for LAN, performance metrics (P95), non-blocking scripts, rate limiting tuning
- Test coverage: 13 CORS tests, 9 rate limiting tests
- Key improvements: Ratings API now accessible from Quest/mobile, admin dashboard P95 latency tracking, script defer optimization

## v1.02.1 - Documentation audit (released 2025-11-09)

- Link: [v1.02.1 release page](https://github.com/russell-henderson/local-server-video/releases/tag/v1.02.1)
- Note: Patch release verifying documentation integrity; no runtime changes.

### Verification Artifacts

- Commit: `bedc4bf` (full SHA: `bedc4bf5805f4e3fd674799e45b5ba96a60d37fd`)
- Commit checksum (SHA256 of commit id string): `57706054454537FC80A2B759B1B0571DF45A1C762CA92A4BDA0B5712857BABF6`
- Verification summary: [docs/releases/v1.02.md](./v1.02.md) and the GitHub release page above.
- Test & link-check results: All tests passed in isolated mode; 9 missing documentation links remain under review.
