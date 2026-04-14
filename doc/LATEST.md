# Latest Changes

Date: April 14, 2026

- Completed stabilization/cleanup phases 0-3 (tests, optional deps, ratings contract, deprecation cleanup).
- Ratings API contract is now explicit for unknown hashes (`404`) with invalid payloads preserved as `400`.
- Optional `psutil` handling now degrades gracefully without import-time failures.
- Documentation reconciled; canonical implementation reference established at `docs/SOURCE_OF_TRUTH.md`.
