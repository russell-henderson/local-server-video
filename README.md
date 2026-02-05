# 🎬 Local Video Server

A modern, professional-grade local video streaming application with intelligent caching, responsive design, and cross-platform support. Built with Flask (Python backend) and vanilla JavaScript for maximum performance and simplicity.

![Python](https://img.shields.io/badge/Python-3.13+-green?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-red?style=for-the-badge&logo=flask)
![JavaScript](https://img.shields.io/badge/JavaScript-Vanilla-yellow?style=for-the-badge&logo=javascript)
![SQLite](https://img.shields.io/badge/SQLite-Database-blue?style=for-the-badge&logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

## ✨ Features

### 📺 Video Streaming
- **Unified Video Player** - Consistent player across all pages with picture-in-picture support
# Local Video Server

This repository contains a Flask-based local video and image server for managing a personal media library. It provides thumbnailing, metadata caching, ratings/favorites, a responsive UI (desktop/mobile/VR), and a Next.js admin dashboard for performance insights.

Key components:

- `main.py`: Flask application and route handlers.
- `cache_manager.py`: In-memory + SQLite metadata cache with JSON fallback.
- `database_migration.py`: SQLite schema and migration helpers.
- `file_watcher.py`: Debounced directory monitoring and discovery.
- `thumbnail_manager.py`: Async thumbnail generation and deduping (FFmpeg-backed).
- `config.py`: Dataclass-based configuration cascade (env → .env → config.json → defaults).
- `performance_monitor.py`: Optional route latency profiling decorator.
- `admin-dashboard/`: Next.js admin UI for metrics and dashboards.
- `static/` and `templates/`: Frontend assets and Jinja2 templates.
- `docs/`: Project documentation and TODOs (start at `docs/TODO.md`).

Quick start (Windows PowerShell):

```powershell
# Install
pip install -r requirements.txt

# Development (auto-reload)
.\dev.ps1 dev

# Production
.\dev.ps1 prod

# Admin dashboard (local)
cd admin-dashboard
npm install
npm run dev
```

Configuration:

- Set environment variables using the `LVS_` prefix, or edit `.env` / `config.json`.
- Important variables: `LVS_PORT`, `LVS_VIDEO_DIRECTORY`, `LVS_THUMBNAIL_DIRECTORY`, `LVS_CACHE_TIMEOUT`.

Notes for contributors:

- Follow patterns in `docs/IMPLEMENTATION.md` and `docs/TODO.md`.
- Use `@performance_monitor("route_name")` on new routes.
- Bulk-load metadata from `cache_manager` rather than per-file calls.

Useful commands:

- Linting & tests: `.\dev.ps1 lint`, `.\dev.ps1 test`
- Reindex videos: `.\dev.ps1 reindex`
- Backup DBs: `.\dev.ps1 backup`

License: MIT — see the `LICENSE` file.

For full, detailed documentation see the `docs/` folder. If you want, I can expand this concise README into the more detailed version currently present in the repository.
