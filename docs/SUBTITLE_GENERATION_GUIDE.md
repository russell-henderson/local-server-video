# Automatic Subtitle Generation System

This document describes the automatic subtitle generation system using faster-whisper AI transcription.

## Overview

The subtitle generation system provides:

- **Local AI transcription** using OpenAI's Whisper models via faster-whisper
- **WebVTT and SRT format support** for broad compatibility
- **Background processing** to avoid blocking the web interface
- **Command-line management tools** for batch operations
- **Flask API integration** for web-based controls
- **Quiet hours scheduling** to avoid resource-intensive operations during peak usage

## Components

### Core Files

- **`config_subtitles.py`** - Configuration settings for subtitle generation
- **`subtitles.py`** - Core subtitle generation logic using faster-whisper
- **`manage_subs.py`** - Command-line interface for subtitle management
- **`app_subs_integration.py`** - Flask API endpoints and template helpers
- **`test_subtitles.py`** - Test script to validate the subtitle system

### Dependencies

The system requires the `faster-whisper` package, which provides:

- Local AI transcription (no internet required)
- Multiple model sizes (tiny, base, small, medium, large)
- GPU acceleration support (CUDA)
- Voice Activity Detection (VAD) for better accuracy

## Configuration

Edit `config_subtitles.py` to customize:

```python
@dataclass
class SubtitleConfig:
    enabled: bool = True
    model_size: str = "medium"         # tiny, base, small, medium, large-v3
    compute_type: str = "auto"         # auto, int8, float16, float32
    language: str | None = None        # None = auto-detect
    translate_to_english: bool = False
    out_format: list[str] | None = None  # ["vtt", "srt"]
    max_concurrent: int = 1            # keep low to avoid CPU spikes
    # Archived: Automatic Subtitle Generation System

    This document has been archived and moved to `docs/deferred/SUBTITLE_GENERATION_GUIDE.md`.

    The automatic subtitle generation system has been removed from this repository. For the current status see the top-level `SUBTITLE_GENERATION_COMPLETE.md` file.

    If you need to restore the feature or inspect historical implementation notes, see `docs/deferred/SUBTITLE_GENERATION_GUIDE.md`.


