# Project Documentation: Local Video Server

## Overview

This project is a local video server designed to manage, serve, and organize a collection of video files. It provides features for video metadata management, user favorites, ratings, tagging, thumbnail generation, performance monitoring, and more. The project is structured to be modular and maintainable, with clear separation of concerns across scripts, static assets, templates, and data files.

## Project Structure

.
├── cache_manager.py
├── database_migration.py
├── favorites.json
├── main.py
├── performance_monitor.py
├── project_structure.txt
├── ratings.json
├── regenerate_thumbnails.py
├── sanitize_video_filenames.py
├── Sort-DesktopFiles.ps1
├── tags.json
├── terminal.log
├── test_db.py
├── video_metadata.db
├── views.json
├── __pycache__/
├── docs/
│   ├── code_descriptions.txt
│   ├── OPENAI_COST_ANALYSIS.md
│   ├── PERFORMANCE_ANALYSIS_SUMMARY.md
│   ├── PERFORMANCE_OPTIMIZATION_GUIDE.md
│   ├── project_structure.txt
│   ├── README.md
│   ├── VIDEO_PREVIEW_FEATURE.md
├── images/
│   └── gallery/
├── scratchoff/
│   └── index.html
├── scripts/
│   ├── analyze_thumbnails.py
│   ├── export-code-descriptions-openai.ps1
│   ├── export-code-descriptions.ps1
│   ├── export-project-structure-no-media.ps1
│   ├── export-project-structure.ps1
├── static/
│   ├── chat.js
│   ├── dark.js
│   ├── favorites.js
│   ├── style.css
│   ├── styles.css
│   ├── theme.css
│   └── thumbnails/
├── templates/
│   ├── favorites.html
│   ├── image_gallery.html
│   ├── index.html
│   ├── navbar.html
│   ├── tag_videos.html
│   ├── tags.html
│   └── watch.html
├── videos/
│   └── *.mp4

## Key Components

### Python Scripts

- __main.py__: Entry point for the server. Handles routing, video serving, and core logic.
- __cache_manager.py__: Manages caching of video metadata and thumbnails for performance.
- __database_migration.py__: Handles database schema migrations and updates.
- __performance_monitor.py__: Monitors server performance and logs metrics.
- __regenerate_thumbnails.py__: Script to regenerate video thumbnails in bulk.
- __sanitize_video_filenames.py__: Cleans and standardizes video filenames.
- __test_db.py__: Contains database tests and validation scripts.

### Data Files

- __video_metadata.db__: SQLite database storing video metadata (title, tags, ratings, etc.).
- __favorites.json__: Stores user favorite videos.
- __ratings.json__: Stores user ratings for videos.
- __tags.json__: Stores tags and their associations with videos.
- __views.json__: Tracks video view counts and statistics.

### Static Assets

- __static/__: Contains JavaScript, CSS, and thumbnail images for the web interface.
  - __chat.js, favorites.js, dark.js__: JS modules for UI features.
  - __style.css, styles.css, theme.css__: Stylesheets for theming and layout.
  - __thumbnails/__: Generated video thumbnail images.

### Templates

- __templates/__: HTML templates for rendering web pages.
  - __index.html__: Main landing page.
  - __favorites.html__: User favorites view.
  - __image_gallery.html__: Gallery view for images/videos.
  - __navbar.html__: Navigation bar partial.
  - __tag_videos.html, tags.html__: Tag management and browsing.
  - __watch.html__: Video player page.

### Scripts

- __scripts/__: Utility scripts for analysis and export.
  - __analyze_thumbnails.py__: Analyzes thumbnail quality and coverage.
  - **export-code-descriptions*.ps1**: PowerShell scripts for exporting code documentation.
  - **export-project-structure*.ps1**: Scripts for exporting project structure.

### Documentation

- __docs/__: Contains documentation and analysis files.
  - __README.md__: General project overview and setup instructions.
  - __PERFORMANCE_ANALYSIS_SUMMARY.md__: Performance analysis results.
  - __PERFORMANCE_OPTIMIZATION_GUIDE.md__: Guide for optimizing server performance.
  - __VIDEO_PREVIEW_FEATURE.md__: Details on video preview implementation.
  - __code_descriptions.txt__: Descriptions of code modules and functions.

### Media

- __videos/__: Directory containing all video files served by the application.
- __images/gallery/__: Image assets for gallery features.

### Miscellaneous

- ____pycache__/__: Compiled Python bytecode for faster execution.
- __terminal.log__: Log file for terminal output and debugging.
- __project_structure.txt__: Text export of the project structure.
- __Sort-DesktopFiles.ps1__: PowerShell script for sorting desktop files.
- __scratchoff/index.html__: Standalone HTML demo or feature page.

## Features

- __Video Serving__: Stream and download videos from the local server.
- __Metadata Management__: Store and edit video metadata, including tags, ratings, and favorites.
- __Thumbnail Generation__: Automatically generate and manage video thumbnails.
- __Tagging System__: Organize videos with tags for easy browsing and filtering.
- __Favorites & Ratings__: Users can mark favorites and rate videos.
- __Performance Monitoring__: Track server performance and optimize resource usage.
- __Database Migration__: Update and maintain the database schema as features evolve.
- __Web Interface__: Responsive UI for browsing, searching, and watching videos.
- __Documentation__: Comprehensive docs for setup, features, and optimization.

## Setup & Usage

1. __Install Python 3.13+ and required packages.__
2. __Run `main.py` to start the server.__
3. __Access the web interface via browser.__
4. __Use utility scripts for maintenance and analysis as needed.__

## Extending the Project

- Add new features by creating scripts and updating templates/static assets.
- Update the database schema using `database_migration.py`.
- Document changes in the `docs/` folder for maintainability.

## Contribution Guidelines

- Follow PEP8 for Python code.
- Keep documentation up to date.
- Use modular design for new features.
- Test changes with `test_db.py` and review logs in `terminal.log`.

## License

Specify your license here (e.g., MIT, GPL, etc.).

---
For more details, see the documentation in the `docs/` folder.
