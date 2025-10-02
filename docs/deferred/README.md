# Deferred Features

This folder contains documentation and files for features that were removed during the refactor but may be re-implemented later:

## Removed Features

### Adaptive Streaming

- **Files removed**: `adaptive-streaming.css`, `adaptive-streaming.js`, `adaptive-streaming-init.js`, `network-monitor.js`
- **Reason**: Complexity reduction, focus on core video player functionality
- **Future consideration**: Could be re-added as an optional enhancement

### VR/WebXR Support

- **Files removed**: `vr-support.js`, `vr-video-player.js`, `device-detection.js`
- **Reason**: Rely on Quest 2 browser for VR presentation instead of custom VR code
- **Future consideration**: Native browser VR support is sufficient

### Glassmorphism/Neomorphism Themes

- **Files removed**: `glassmorphic-theme.css`, `neomorphic-theme.css`, `hybrid-theme.css`, `theme-manager.js`, `theme-integration.js`
- **Documentation removed**: `GLASSMORPHIC_NEOMORPHIC_DESIGN.md`
- **Reason**: Focus on clean dark mode only
- **Future consideration**: Could be re-added as theme options

### Legacy CSS

- **Files removed**: `style.css`, `styles.css`
- **Reason**: Consolidated into `static/css/app.css`
- **Note**: Functionality preserved, just reorganized

## What Was Kept

- Dark mode theme system (`theme.css`)
- Core video functionality
- Lightweight video preview on hover
- All page templates (updated to use new structure)
- Shared video player component
