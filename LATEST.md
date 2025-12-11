# Latest Changes (Past 24h)

Date: 2025-12-10

- Front-end polish: simplified library hero meta line, enlarged video cards/grids, refreshed tags page (count badge + pill chips), and restyled navbar/random CTA.
- Ratings unified: shared rating partial used across library, player, and watch; synced via one JS module so ratings stay consistent everywhere.
- Player VR-friendliness: larger hit targets, thicker seek/volume bars, persistent controls on Quest/touch without hover, and VR-only preview text suppression.
- Nginx proxy added: serves static/images with caching + gzip and proxies dynamic routes to Flask for faster loads in Docker deployments.
- Assets housekeeping: moved root UI PNGs into `archive/images/`.
