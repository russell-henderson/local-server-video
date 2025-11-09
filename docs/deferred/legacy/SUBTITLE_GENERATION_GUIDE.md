````markdown
# Automatic Subtitle Generation System (Archived)

This document describes the automatic subtitle generation system using faster-whisper.

## Overview

The subtitle generation system provided:

- **Local AI transcription** using Whisper via faster-whisper
- **WebVTT and SRT format support**
- **Background processing** to avoid blocking the web interface
- **Command-line management tools** for batch operations
- **Flask API integration** for web-based controls

## Components (historical)

- `config_subtitles.py` - Configuration settings for subtitle generation
- `subtitles.py` - Core subtitle generation logic (removed)
- `manage_subs.py` - CLI for subtitle management (removed)
- `app_subs_integration.py` - Flask API endpoints (removed)

This guide has been archived and moved to `docs/deferred/legacy/SUBTITLE_GENERATION_GUIDE.md`.

If you need to restore the feature or inspect historical implementation notes, see the archived copy in `docs/deferred/legacy/`.

````
