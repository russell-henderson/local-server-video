````markdown
# Subtitle System Troubleshooting Guide

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
       def get_subtitle_status(video_path):
           # ... implementation

       @app.route("/api/subtitles/<path:video_path>", methods=["POST"])
       def generate_subtitles(video_path):
           # ... implementation
   ```

2. **Main App Integration**: Updated main.py to call the registration function:

   ```python
   # In main.py
   try:
       import app_subs_integration
       app_subs_integration.register_subtitle_routes(app)
       print("✅ Subtitle system loaded")
   except ImportError as e:
       print(f"⚠️  Subtitle system not available: {e}")
   ```

### Verification

- Test route works: `http://127.0.0.1:5000/api/test` ✅
- Subtitle status API: `http://127.0.0.1:5000/api/subtitles/Scene02.mp4` ✅
- Video page with controls: `http://127.0.0.1:5000/watch/Scene02.mp4` ✅

## Issue Resolution: 500 Internal Server Error ✅ RESOLVED

### Problem

When attempting to generate subtitles, the API returned:

- `Failed to load resource: the server responded with a status of 500 (INTERNAL SERVER ERROR)`
- `Error generating subtitles: Error: HTTP 500: INTERNAL SERVER ERROR`

### Root Cause

The issue was with CUDA device selection in the faster-whisper model initialization. The logic was incorrectly trying to force CUDA when compute_type was "auto", causing a CUDA driver version mismatch error:

### Solution

Fixed the device selection logic in `subtitles.py`:

```python
# Before (problematic):

device="cuda" if SUBTITLES.compute_type == "auto" else "auto"

# After (fixed):

device="auto"
```

This allows the system to auto-detect the best available compute device (CPU/GPU) based on system capabilities.

### Verification

- Subtitle generation API working: POST to `/api/subtitles/Scene02.mp4` returns 200 ✅
- Subtitle files created: `Scene02.vtt` and `Scene02.srt` generated ✅
- Video page integration: Subtitles load automatically in video player ✅

### Key Learnings

- Flask route registration must happen after app instance creation
- Import order matters for proper route registration
- Function-based route registration provides better control over timing
- Testing with simple endpoints helps isolate registration issues
- CUDA auto-detection is more reliable than forced device selection
- Always test API endpoints directly to isolate errors from frontend issues

### System Components Status

✅ **Subtitle Generation**: faster-whisper AI transcription system
✅ **API Endpoints**: GET/POST routes for subtitle status and generation
✅ **Frontend Controls**: JavaScript integration with video player
✅ **File Management**: WebVTT/SRT subtitle file handling
✅ **Error Handling**: Proper HTTP status codes and error responses
✅ **Device Compatibility**: Auto-detection of CPU/GPU for transcription

## Usage

The subtitle system is now fully operational:

1. Navigate to any video page
2. Click "Generate Subtitles" button
3. System will use AI to transcribe audio and create subtitle files
4. Subtitles are automatically loaded when available

````
