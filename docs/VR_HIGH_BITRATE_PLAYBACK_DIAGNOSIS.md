# Local Video Server: High-Resolution VR Playback Diagnosis & Throughput Verification

**Date:** 2026-10-23  
**Status:** Resolved & Validated on Real Devices (Windows Desktop, Mobile Phone, Meta Quest 2)  
**Environment:** Native Windows 11 Pro (`10.0.26300`), Python 3.14.6, Flask 3.1.3, Werkzeug 3.1.9 (Docker/WSL not active)  
**Primary Target Media:** `videos/Naughty Stepmom - Ava Addams -VR.mp4` (6144×3072 @ 59.94 FPS HEVC, ~9.63 GB)

---

## 1. Executive Summary

Earlier diagnosis hypothesized that playback interruptions were caused by an inherent throughput ceiling in the Flask development server (~34.85 Mbps measured vs. 43.7 Mbps video bitrate). 

Rigorous multi-sample benchmarking has **refuted** this hypothesis:
- The local Python/Flask/Werkzeug server on native Windows sustains **1,000 to 8,800+ Mbps** across 10 MB, 64 MB, and 256 MB HTTP Range requests, with TTFB dropping to **2–4 milliseconds**.
- Direct filesystem read speed exceeds **24,000 Mbps** (~3 GB/s).
- The earlier 34.85 Mbps figure was an artifact of a single 2.4-second test sample (impacted by cold startup or cache warming), not a systemic network transfer limit.

However, in-depth inspection of `stream_video()` in `backend/app/legacy_runtime.py` uncovered a **critical architectural memory flaw**:
1. When clients (browsers, media players, headsets) issue standard open-ended range requests (`Range: bytes=0-` or `Range: bytes=<offset>-`), `byte2` was defaulted to `size - 1`.
2. The server executed `data = fh.read(length)` and returned `Response(data, 206)`. For a 9.63 GB file, this attempted to read **up to 9.63 GB into a single monolithic Python memory allocation**, blocking the worker thread and creating massive memory pressure.
3. Out-of-bounds ranges crashed with `ValueError` (HTTP 500) rather than returning HTTP 416 (Range Not Satisfiable). Suffix ranges (`bytes=-N`) were ignored.

A narrowly scoped, bounded streaming generator (`STREAMING_CHUNK_SIZE = 256 KB`) and robust RFC 9110 range parser have been implemented. Memory footprint is now strictly bounded, TTFB is near-instant, seek operations respond cleanly, and zero regressions were introduced to existing URLs, MIME types, or application features.

---

## 2. Media Properties & Container Verification

Inspected via `ffprobe` and structural MP4 box parser:

| Property | Value | Notes |
|---|---|---|
| **Container** | MP4 (`isom` / `mp42`) | 64-bit large file container (`co64` chunk offsets) |
| **Video Stream** | HEVC / H.265 (`hvc1`) | Main Profile, Level 186 (Level 6.2), yuv420p |
| **Resolution** | 6144 × 3072 | 2:1 Equirectangular VR projection |
| **Frame Rate** | 59.94 FPS (`60000/1001`) | High frame rate |
| **Video Bitrate** | 43,387,099 bps (~43.39 Mbps) | Variable / high bitrate stream |
| **Audio Stream** | AAC-LC | 48 kHz stereo, 317,375 bps (~0.32 Mbps) |
| **Total Bitrate** | **43,710,330 bps (~43.71 Mbps)** | Combined audio + video |
| **Duration** | 1,892.61 seconds (~31.54 minutes) | Full feature length |
| **File Size** | **10,340,811,843 bytes** (~9.63 GB) | Large file |

### MP4 Atom Offsets & Ordering

```text
Atom: ftyp   offset:            0 size: 24 bytes
Atom: moov   offset:           24 size: 1,059,436 bytes (~1.06 MB)
Atom: uuid   offset:      1059460 size: 324,162 bytes (~324 KB)
Atom: mdat   offset:      1383622 size: 10,339,428,220 bytes (~10.34 GB, 64-bit)
```

**Verification:** The `moov` header atom is located immediately after the 24-byte `ftyp` header at byte 24 and is only ~1.06 MB. Media players downloading the first 2 MB receive all index metadata upfront, fully supporting progressive playback and rapid seeking.

---

## 3. Benchmark Measurements & Control Data

### A. Direct Filesystem Read Control
Measured raw disk-to-memory throughput for `videos/Naughty Stepmom - Ava Addams -VR.mp4` on the host storage:

- **10 MB:** 0.0031 s (**27,025 Mbps** / 3,221 MB/s)
- **64 MB:** 0.0200 s (**26,778 Mbps** / 3,192 MB/s)
- **256 MB:** 0.0866 s (**24,793 Mbps** / 2,955 MB/s)

*Conclusion:* Storage I/O is not a bottleneck.

### B. HTTP Range Benchmark Table (Native Windows Development Server on `127.0.0.1:8000`)
Benchmarked across 3 consecutive runs per size:

| Range Request | Run | Status | TTFB (s) | Total Time (s) | Throughput (MB/s) | Throughput (Mbps) | Headroom vs. 43.7 Mbps Bitrate |
|---|---|---|---|---|---|---|---|
| **10 MB** (`bytes=0-10485759`) | 1 | 206 | 0.0549 | 0.0810 | 123.45 MB/s | 1,035.58 Mbps | **23.7×** |
| **10 MB** (`bytes=0-10485759`) | 2 | 206 | 0.0027 | 0.0156 | 640.25 MB/s | 5,370.81 Mbps | **122.9×** |
| **10 MB** (`bytes=0-10485759`) | 3 | 206 | 0.0021 | 0.0228 | 438.68 MB/s | 3,679.91 Mbps | **84.2×** |
| **64 MB** (`bytes=0-67108863`) | 1 | 206 | 0.0025 | 0.1931 | 331.42 MB/s | 2,780.13 Mbps | **63.6×** |
| **64 MB** (`bytes=0-67108863`) | 2 | 206 | 0.0028 | 0.1560 | 410.25 MB/s | 3,441.40 Mbps | **78.7×** |
| **64 MB** (`bytes=0-67108863`) | 3 | 206 | 0.0036 | 0.1979 | 323.46 MB/s | 2,713.41 Mbps | **62.1×** |
| **256 MB** (`bytes=0-268435455`) | 1 | 206 | 0.0034 | 1.8739 | 136.61 MB/s | 1,145.97 Mbps | **26.2×** |
| **256 MB** (`bytes=0-268435455`) | 2 | 206 | 0.0041 | 1.7376 | 147.33 MB/s | 1,235.91 Mbps | **28.3×** |
| **256 MB** (`bytes=0-268435455`) | 3 | 206 | 0.0042 | 1.7908 | 142.95 MB/s | 1,199.17 Mbps | **27.4×** |

### C. curl Test Commands & Verification
```powershell
# 10 MB Range Request
curl.exe -s -o NUL -w "Status: %{http_code} | TTFB: %{time_starttransfer}s | Total: %{time_total}s | Speed: %{speed_download} B/s\n" -H "Range: bytes=0-10485759" "http://127.0.0.1:8000/video/Naughty%20Stepmom%20-%20Ava%20Addams%20-VR.mp4"

# Mid-stream Seek (10 MB starting at 5 GB offset)
curl.exe -I -H "Range: bytes=5000000000-5010485759" "http://127.0.0.1:8000/video/Naughty%20Stepmom%20-%20Ava%20Addams%20-VR.mp4"

# Suffix Range (last 10 MB)
curl.exe -I -H "Range: bytes=-10485760" "http://127.0.0.1:8000/video/Naughty%20Stepmom%20-%20Ava%20Addams%20-VR.mp4"

# Unsatisfiable Range (returns HTTP 416)
curl.exe -I -H "Range: bytes=99999999999-" "http://127.0.0.1:8000/video/Naughty%20Stepmom%20-%20Ava%20Addams%20-VR.mp4"
```

---

## 4. Root Cause Analysis

### Identified Architectural Bottlenecks (Server Side)
1. **Unbounded Memory Loading on Open-Ended Range Requests:**
   Browsers and VR video players routinely initiate media requests with `Range: bytes=0-` or `Range: bytes=<seek_offset>-`. In the prior implementation:
   ```python
   # Defective prior code:
   if byte2 is None or byte2 >= size:
       byte2 = size - 1
   length = byte2 - byte1 + 1
   with file_path.open("rb") as fh:
       fh.seek(byte1)
       data = fh.read(length) # <-- Reads up to 9.63 GB into RAM!
   rv = Response(data, 206, ...)
   ```
   This allocated multi-gigabyte memory blocks in Python, stalled thread execution, and risked Out-Of-Memory (OOM) failures or aggressive garbage collection stalls whenever a user sought or paused.
2. **Defective Range Edge Cases:**
   - Out-of-bounds ranges (`bytes=999999999-`) caused `length` to be negative, triggering `ValueError: read length must be non-negative or -1` and HTTP 500 error responses.
   - Suffix ranges (`bytes=-N`) were not parsed and defaulted to returning the whole file.

### Identified Client-Side Factors (Meta Quest 2 & Network)
1. **Snapdragon XR2 Gen 1 Hardware Decoder Limits:**
   - Meta Quest 2's chipset has an official hardware decoding ceiling of 4096×2048 @ 60 FPS or 8192×4096 @ 30 FPS.
   - Playing a 6144×3072 video at **59.94 FPS** in an HTML5 browser `<video>` tag stresses or exceeds the mobile decoder's capabilities, causing stuttering, frame drops, and perceived buffering even when data transfer is instantaneous. Dedicated VR players (Skybox, DeoVR) with native ExoPlayer/ffmpeg pipelines generally handle high-resolution VR video much more effectively than browser WebGL/<video> tags.
2. **Wi-Fi Link Fluctuations:**
   - While wired gigabit network throughput is >1,000 Mbps, Wi-Fi 5 (802.11ac) or 2.4 GHz connections on mobile headsets can fluctuate below the 43.7 Mbps video requirement during interference or poor signal conditions.

---

## 5. Implemented Solution

In [backend/app/legacy_runtime.py](file:///z:/local-video-server/backend/app/legacy_runtime.py):

1. **Bounded Incremental Delivery:** Replaced monolithic `fh.read(length)` with `_iter_file_range()` generator using `STREAMING_CHUNK_SIZE = 256 * 1024` (256 KB). Memory consumption per active streaming connection is capped at under 1 MB regardless of file size.
2. **Clean Resource Reclamation:** Generator uses `try ... finally: fh.close()`. When a client disconnects or pauses, Werkzeug closes the response iterator, instantly closing the underlying file handle without resource leakage.
3. **Robust Range Parsing:** Implemented `_parse_byte_range()` supporting:
   - Explicit ranges: `bytes=start-end`
   - Open-ended ranges: `bytes=start-`
   - Suffix ranges: `bytes=-N` (clamped to file size)
   - Unsatisfiable and malformed ranges cleanly return **HTTP 416 (Range Not Satisfiable)** with `Content-Range: bytes */{size}` and `Accept-Ranges: bytes`.
4. **Zero URL or API Breakage:** Preserved all existing endpoints (`/video/<path:filename>`), MIME types, `Content-Range`, `Content-Length`, `Accept-Ranges`, and HTTP 206 status codes.

---

## 6. Validation & Regression Testing

1. **Unit & Edge Case Test Suite:** Created [tests/test_video_streaming.py](file:///z:/local-video-server/tests/test_video_streaming.py) covering 10 distinct streaming scenarios:
   - `test_stream_video_no_range`: HTTP 200 full file delivery
   - `test_stream_video_bounded_range`: HTTP 206 partial content with exact byte verification
   - `test_stream_video_open_ended_range`: Open-ended range with exact offset-to-EOF verification
   - `test_stream_video_suffix_range`: Correct trailing byte extraction
   - `test_stream_video_suffix_larger_than_file`: Graceful clamping to full file
   - `test_stream_video_unsatisfiable_range`: Correct HTTP 416 responses
   - `test_stream_video_malformed_range`: Malformed and multi-range validation (HTTP 416)
   - `test_stream_video_not_found`: HTTP 404 for missing media
   - `test_stream_video_early_client_disconnect`: Verification that file handle closes upon early abort
   - `test_stream_video_bounded_memory`: Verification that chunks never exceed 256 KB
   - **Result:** `10 passed in 0.37s`.
2. **Repository Regression Suite:** Executed full test suite (`python -m pytest -q`):
   - **Result:** `65 passed in 5.48s` (0 failures, 0 warnings).

---

## 7. Rollback Procedure

If any unexpected regression occurs:
1. Revert lines 685–768 in `backend/app/legacy_runtime.py` to git commit baseline (`git checkout backend/app/legacy_runtime.py`).
2. Remove `tests/test_video_streaming.py`.
3. Changes are isolated exclusively to `stream_video` and its helper functions; no database schemas, configuration files, or external routes are touched.

---

## 8. Real-Device Field Validation Results

Field testing of the 10 GB, 6144×3072 @ 59.94 FPS HEVC video with the bounded streaming fix yielded the following confirmed results across devices:

1. **Windows Desktop Browser:**
   - **Result:** Confirmed continuous playback without interruptions.
   - Seeking, pausing, and resuming function smoothly with near-instantaneous response.
2. **Mobile Phone (LAN/Wi-Fi):**
   - **Result:** Dramatically improved playback consistency and responsive seeking over the pre-fix state.
3. **Meta Quest 2 (VR Headset):**
   - **Result:** Dramatically improved playback and responsive seek behavior compared to the pre-fix failure state where playback stalled repeatedly.
   - *Note on device capabilities:* Zero buffering is not claimed on mobile or Quest 2; the Snapdragon XR2 Gen 1 mobile hardware decoder and browser rendering pipeline continue to operate near their upper performance ceiling when decoding 6K @ 60 FPS HEVC content in an HTML5 browser context, and wireless conditions can still introduce momentary variances. However, server-side network starvation and memory exhaustion have been conclusively eliminated.

---

## 9. Conclusion

The P0 high-bitrate streaming defect has been resolved. The server now delivers high-bitrate media reliably with bounded memory usage and high sustained throughput headroom, while preserving all HTTP Range semantics and client workflows.