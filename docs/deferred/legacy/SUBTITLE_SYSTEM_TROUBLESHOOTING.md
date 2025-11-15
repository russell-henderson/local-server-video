````markdown
# Archived: Subtitle System Troubleshooting Guide

## Issue Resolution: API Route 404 Errors ✅ RESOLVED

### Problem

After implementing the subtitle generation system, API endpoints were returning 404 errors:

- `Failed to load resource: the server responded with a status of 404 (NOT FOUND)`
- `Could not check subtitle status: SyntaxError: Unexpected token '<', "<!doctype "... is not valid JSON`

### Root Cause

The issue was with Flask route registration timing. The subtitle API routes were not being properly registered with the Flask application instance due to import order and module structure.

### Solution

1. **Refactored Route Registration**: Changed from direct `@app.route` decorators to a function-based approach:

   ```python
   # In app_subs_integration.py
   def register_subtitle_routes(app):
       @app.route("/api/subtitles/<path:video_path>", methods=["GET"])
   ```

This troubleshooting guide has been archived and moved to `docs/deferred/legacy/SUBTITLE_SYSTEM_TROUBLESHOOTING.md`.

The subtitle generation system has been removed from the repository. For historical troubleshooting notes and implementation details see the archived copy in `docs/deferred/legacy/`.

````
