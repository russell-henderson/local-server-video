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
    quiet_hours: tuple[int, int] = (1, 6)  # 1am–6am preferred window
    videos_root: str = "videos"        # adjust if different
    subs_ext: str = ".vtt"            # default track for player
```

### Model Sizes

- **tiny**: ~39 MB, fastest, lowest accuracy
- **base**: ~74 MB, good balance of speed and accuracy
- **small**: ~244 MB, better accuracy
- **medium**: ~769 MB, high accuracy (recommended)
- **large-v3**: ~1550 MB, highest accuracy, slowest

### Compute Types

- **auto**: Automatically detect best available (CUDA > CPU)
- **int8**: 8-bit quantization for faster inference
- **float16**: Half precision (GPU only)
- **float32**: Full precision

## Command Line Usage

### Check Subtitle Status

```bash
python manage_subs.py --root videos check
```

Shows how many videos have subtitles vs. missing subtitles.

### Generate Missing Subtitles

```bash
python manage_subs.py --root videos generate
```

Generates subtitles for all videos that don't have them.

### Generate for Specific File

```bash
python manage_subs.py --root videos generate --file "specific_video.mp4"
```

### Batch Generation with Multiple Workers

```bash
python manage_subs.py --root videos batch --workers 2
```

**Warning**: Multiple workers consume significant CPU/GPU resources.

### Respect Quiet Hours

```bash
python manage_subs.py --root videos generate --quiet-check
```

Skips generation if current time is within configured quiet hours.

## API Endpoints

### Check Subtitle Status

```http
GET /api/subtitles/<video_path>
```

Returns JSON with subtitle availability:
```json
{
  "video": "example.mp4",
  "has_subtitles": true
}
```

### Trigger Background Generation

```http
POST /api/subtitles/<video_path>/generate
```

Starts subtitle generation in background thread:
```json
{
  "status": "started",
  "message": "Subtitle generation started in background"
}
```

## Template Integration

### Check Subtitle Status in Templates

```html
{% set sub_info = subtitle_status(video.path) %}
{% if sub_info.has_subtitles %}
  <span class="subtitle-available">📝 Subtitles Available</span>
{% else %}
  <span class="subtitle-missing">❌ No Subtitles</span>
{% endif %}
```

### Enhance Video Context

```python
from app_subs_integration import enhance_video_context

video_info = {"path": "example.mp4", "title": "Example"}
enhanced = enhance_video_context(video_info)
# Now includes: enhanced["has_subtitles"] = True/False
```

## File Formats

### WebVTT (.vtt)
- Web standard for video subtitles
- Supported by HTML5 video players
- Better formatting options

### SubRip (.srt)
- Universal subtitle format
- Supported by most video players
- Simple text-based format

## Performance Considerations

### Resource Usage
- **CPU**: Whisper models are CPU-intensive
- **GPU**: CUDA acceleration significantly improves speed
- **RAM**: Medium model requires ~2GB RAM
- **Storage**: Generated subtitle files are small (~1% of video size)

### Processing Times
- **tiny model**: ~1/10 of video duration
- **base model**: ~1/5 of video duration  
- **medium model**: ~1/3 of video duration
- **large model**: ~1/2 of video duration

### Optimization Tips
1. Use GPU acceleration when available
2. Set `max_concurrent = 1` to avoid system overload
3. Schedule batch processing during off-peak hours
4. Use smaller models for initial processing, upgrade selectively

## Troubleshooting

### Common Issues

**"Module 'faster_whisper' not found"**
```bash
pip install faster-whisper
```

**GPU not detected**
- Install CUDA toolkit
- Verify GPU compatibility
- Set `compute_type = "float32"` for CPU-only

**Out of memory errors**
- Reduce model size (medium → base → tiny)
- Set `compute_type = "int8"` for quantization
- Reduce `max_concurrent` to 1

**Poor transcription quality**
- Try larger model size
- Set specific language instead of auto-detect
- Enable `translate_to_english = True` for non-English content

### Debugging

Enable verbose logging:
```bash
python manage_subs.py --root videos check --verbose
```

Test specific video:
```bash
python test_subtitles.py
```

## Integration Examples

### Automatic Generation on Upload

```python
from subtitles import generate_for_file
from config_subtitles import SUBTITLES

def handle_video_upload(video_path):
    if SUBTITLES.enabled:
        # Generate subtitles in background
        threading.Thread(
            target=generate_for_file,
            args=(video_path,),
            daemon=True
        ).start()
```

### Batch Processing Script

```python
from subtitles import generate_missing, within_quiet_hours
from config_subtitles import SUBTITLES

def nightly_subtitle_generation():
    if not within_quiet_hours():
        return
    
    results = generate_missing(SUBTITLES.videos_root)
    print(f"Generated subtitles for {len(results)} videos")
```

### Player Integration

```html
<video controls>
  <source src="/video/example.mp4" type="video/mp4">
  {% if subtitle_status(video.path).has_subtitles %}
    <track kind="subtitles" src="/video/example.vtt" 
           srclang="en" label="English" default>
  {% endif %}
</video>
```

## Security Considerations

- Subtitle generation processes video files locally
- No data is sent to external services
- Generated subtitle files contain transcribed speech
- Consider privacy implications for sensitive content

## Future Enhancements

- Speaker diarization (identifying different speakers)
- Custom model fine-tuning for specific domains
- Real-time subtitle generation during streaming
- Integration with translation services
- Subtitle editing interface
- Quality scoring and automatic re-processing