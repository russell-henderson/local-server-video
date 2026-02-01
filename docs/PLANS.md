# Video Streaming Optimization Plans

## Overview

This document outlines comprehensive strategies to optimize video streaming performance for larger files in the Local Video Server. The plans build on the existing architecture while implementing advanced streaming techniques to reduce latency, improve quality adaptation, and enhance user experience across all devices.

## Current State Analysis

### Existing Optimizations
- HTTP range requests for partial content delivery
- Basic thumbnail generation and caching
- Metadata caching with SQLite/JSON fallback
- Service worker for static asset caching
- Touch-optimized UI with 44px+ targets

### Performance Bottlenecks
- Single bitrate streaming (no adaptive quality)
- No transcoding pipeline for multiple formats
- Limited client-side buffering strategies
- No hardware acceleration for encoding
- Basic HTTP/1.1 without advanced features

## Phase 1: Immediate Server Optimizations

### 1.1 HTTP/2 and Connection Optimization

**Goal**: Reduce connection overhead and improve multiplexing

**Implementation**:
- Upgrade Flask to support HTTP/2 (requires WSGI server like Gunicorn with HTTP/2)
- Enable connection keep-alive for persistent connections
- Implement gzip compression for text assets

**Code Changes**:
```python
# In main.py - video streaming route
response = Response(stream_video(filename), mimetype=mime_type)
response.headers.update({
    'Cache-Control': 'public, max-age=3600',
    'Accept-Ranges': 'bytes',
    'Connection': 'keep-alive',
    'Content-Encoding': 'gzip'  # For compressible responses
})
```

### 1.2 Enhanced Caching Strategy

**Goal**: Reduce redundant I/O operations

**Implementation**:
- Implement ETags for video files
- Add Last-Modified headers
- Cache video metadata more aggressively
- Preload frequently accessed video metadata

**Benefits**:
- 50-70% reduction in metadata loading time
- Better browser caching for repeated visits
- Reduced server load

### 1.3 Resource Hints and Preloading

**Goal**: Improve initial page load performance

**Implementation**:
```html
<!-- In templates/_base.html -->
<link rel="preload" href="{{ url_for('static', filename='js/player.js') }}" as="script">
<link rel="dns-prefetch" href="//fonts.googleapis.com">
<link rel="preconnect" href="{{ url_for('static', filename='') }}">
```

## Phase 2: Video Encoding and Transcoding

### 2.1 Adaptive Bitrate Streaming (ABR) Implementation

**Goal**: Dynamic quality adjustment based on network conditions

**Architecture**:
- HLS (HTTP Live Streaming) for broad compatibility
- Multiple quality levels: 240p, 360p, 480p, 720p, 1080p, 1440p, 4K
- Manifest files (.m3u8) for quality selection
- Segment-based delivery (10-second chunks)

**Transcoding Pipeline**:
```bash
# HLS generation command
ffmpeg -i input.mp4 \
  -vf scale=w=1920:h=1080:force_original_aspect_ratio=decrease \
  -c:a aac -ar 48000 \
  -c:v h264 -profile:v main -crf 20 \
  -hls_time 10 -hls_playlist_type vod \
  -b:v 5000k -maxrate 5350k -bufsize 7500k \
  -hls_segment_filename '1080p_%03d.ts' \
  1080p.m3u8
```

### 2.2 Hardware-Accelerated Transcoding

**Goal**: 5-10x faster encoding for large files

**Implementation**:
- NVIDIA NVENC for GPU acceleration
- AMD AMF support
- Intel Quick Sync Video
- Background processing queue

**Code Structure**:
```python
# New file: transcoding_manager.py
class TranscodingManager:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.queue = deque()

    def transcode_video(self, input_path, output_dir, qualities):
        """Queue video for multi-quality transcoding"""
        self.executor.submit(self._transcode_hls, input_path, output_dir, qualities)

    def _transcode_hls(self, input_path, output_dir, qualities):
        """FFmpeg HLS transcoding with hardware acceleration"""
        for quality in qualities:
            cmd = self._build_ffmpeg_cmd(input_path, output_dir, quality)
            subprocess.run(cmd, check=True)
```

### 2.3 Smart Transcoding Triggers

**Goal**: On-demand transcoding to save storage and processing

**Strategies**:
- Transcode on first access
- Progressive quality generation (start with low quality)
- Skip already optimized files
- Background transcoding for popular videos

## Phase 3: Client-Side Optimizations

### 3.1 Enhanced Video Preloading

**Goal**: Reduce buffering and improve startup time

**Implementation**:
```javascript
// In player.js
class SmartPreloader {
    constructor(video) {
        this.video = video;
        this.bufferTarget = 30; // seconds
        this.preloadWindow = 60; // seconds ahead
    }

    start() {
        this.video.addEventListener('timeupdate', () => {
            this.checkBufferHealth();
            this.prefetchAhead();
        });
    }

    checkBufferHealth() {
        const buffered = this.video.buffered;
        if (buffered.length > 0) {
            const bufferEnd = buffered.end(buffered.length - 1);
            const currentTime = this.video.currentTime;
            const bufferHealth = bufferEnd - currentTime;

            if (bufferHealth < this.bufferTarget) {
                this.requestMoreData();
            }
        }
    }
}
```

### 3.2 Service Worker Video Caching

**Goal**: Cache video segments for offline viewing

**Extension of existing SW**:
```javascript
// In static/sw.js
const VIDEO_CACHE = 'video-segments-v1';

self.addEventListener('fetch', event => {
  if (event.request.url.includes('/stream/') &&
      event.request.headers.get('range')) {
    event.respondWith(handleVideoRangeRequest(event.request));
  }
});

async function handleVideoRangeRequest(request) {
  const cache = await caches.open(VIDEO_CACHE);
  const cachedResponse = await cache.match(request);

  if (cachedResponse) {
    return cachedResponse;
  }

  const response = await fetch(request);
  if (response.ok) {
    cache.put(request, response.clone());
  }
  return response;
}
```

### 3.3 Network-Aware Buffering

**Goal**: Adjust buffer size based on connection quality

**Implementation**:
- Real-time bandwidth measurement
- Dynamic buffer target adjustment
- Quality prediction algorithms
- Connection type detection (WiFi, cellular, etc.)

## Phase 4: Infrastructure Improvements

### 4.1 Local CDN Setup

**Goal**: Distribute load and improve concurrent streaming

**Architecture**:
- Nginx reverse proxy with caching
- Multiple Flask instances
- Load balancing
- Static file optimization

**Docker Compose Enhancement**:
```yaml
# In docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - video-server

  video-server:
    build: .
    deploy:
      replicas: 3
    depends_on:
      - redis
```

### 4.2 Database Optimization

**Goal**: Faster metadata access for large libraries

**Improvements**:
- Index optimization for video queries
- Connection pooling
- Query result caching
- Asynchronous metadata loading

### 4.3 Monitoring and Analytics

**Goal**: Track performance and identify bottlenecks

**Metrics to Track**:
- Video startup time
- Buffering events
- Quality switch frequency
- Bandwidth utilization
- Cache hit rates
- Concurrent viewer count

## Implementation Roadmap

### Week 1-2: Foundation
- [ ] HTTP/2 enablement
- [ ] Enhanced caching headers
- [ ] Resource hints implementation
- [ ] Basic HLS transcoding for new videos

### Month 1: Core Streaming
- [ ] Complete ABR system from existing docs
- [ ] Hardware acceleration setup
- [ ] Client-side buffering improvements
- [ ] Service worker video caching

### Month 2: Advanced Features
- [ ] Local CDN infrastructure
- [ ] Performance monitoring dashboard
- [ ] Machine learning quality prediction
- [ ] Advanced analytics

### Month 3: Optimization
- [ ] A/B testing for different strategies
- [ ] Performance benchmarking
- [ ] User experience validation
- [ ] Documentation updates

## Quick Wins (1-3 days each)

### 1. Enable sendfile
```python
# In main.py
return send_file(file_path, conditional=True, mimetype=mime_type)
```

### 2. Optimize FFmpeg Presets
- Use faster encoding presets
- Enable hardware acceleration flags
- Optimize keyframe intervals

### 3. Connection Pooling
- Implement database connection reuse
- Add Redis for session caching
- Optimize thread pool usage

### 4. Video Metadata Caching
- Cache video duration and codec info
- Avoid repeated ffprobe calls
- Store in SQLite for fast access

## Success Metrics

### Performance Targets
- **Startup Time**: < 2 seconds for HD videos
- **Buffering**: < 5% of playback time
- **Quality Switches**: Smooth transitions < 1 second
- **Concurrent Users**: Support 10+ simultaneous streams

### User Experience
- **Adaptive Quality**: Automatic quality adjustment
- **Seamless Playback**: No interruptions on stable networks
- **Device Optimization**: Best quality for each device type
- **Offline Capability**: Basic offline viewing support

## Dependencies and Prerequisites

### Required Libraries
- `ffmpeg` with hardware acceleration support
- `gunicorn` for HTTP/2 support
- `redis` for advanced caching
- `nginx` for reverse proxy

### Hardware Requirements
- GPU with encoding acceleration (optional but recommended)
- SSD storage for video files
- Sufficient RAM for concurrent transcoding

### Testing Requirements
- Multiple network conditions (WiFi, cellular, slow connections)
- Various devices (desktop, mobile, VR)
- Large video files (4K, high bitrate)
- Concurrent load testing

## Risk Assessment

### High Risk
- Transcoding pipeline complexity
- Hardware acceleration compatibility
- Storage requirements for multiple qualities

### Medium Risk
- HTTP/2 implementation challenges
- Service worker video caching edge cases
- Database performance under load

### Low Risk
- Caching header improvements
- Resource hints
- Basic monitoring

## Future Enhancements

### AI-Powered Optimization
- Machine learning for quality prediction
- User behavior analysis
- Content-aware encoding

### Advanced Streaming
- WebRTC for peer-to-peer streaming
- Low-latency DASH
- 360° video support

### Cloud Integration
- Hybrid local/cloud transcoding
- CDN fallback options
- Cross-device sync

---

*This plan provides a comprehensive roadmap for video streaming optimization, building on the existing Local Video Server architecture while implementing industry-standard streaming techniques.*