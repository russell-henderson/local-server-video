# 🎬 Local Video Server

A modern, feature-rich local video server with advanced streaming capabilities, beautiful UI themes, intelligent video management, and **100% accessibility compliance**. Built with Flask and enhanced with cutting-edge web technologies.

![Video Server](https://img.shields.io/badge/Video-Server-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.13+-green?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-red?style=for-the-badge&logo=flask)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow?style=for-the-badge&logo=javascript)
![Accessibility](https://img.shields.io/badge/Accessibility-WCAG%20AA-green?style=for-the-badge&logo=accessibility)

## ✨ Features

### 🎥 **Advanced Video Streaming**

- **Adaptive Bitrate Streaming (ABR)** - Netflix-level quality adaptation
- **Multi-Quality Support** - 7 quality levels from 240p to 4K
- **Real-time Network Monitoring** - Intelligent bandwidth detection
- **Cross-Platform Compatibility** - Desktop, mobile, tablet, and VR support
- **Smart Buffer Management** - Prevents buffering with predictive loading

### 🎨 **Modern UI Themes & Accessibility**

- **Glassmorphic Design** - Frosted glass effects with blur and transparency
- **Neomorphic Interface** - Soft shadows and tactile button elements
- **Hybrid Theme** - Best of both glassmorphism and neomorphism
- **Dark Mode Support** - Eye-friendly viewing in low light
- **High Contrast Mode** - WCAG AA compliant accessibility enhancement
- **Keyboard Navigation** - Full keyboard shortcuts (Ctrl+1-4 for themes, Ctrl+D for dark mode)
- **Touch-Friendly Interface** - 44px minimum touch targets for mobile/VR

### 🔍 **Enhanced Video Previews**

- **Live Thumbnails** - Mouse-over scrubbing for instant scene preview
- **Mobile Tap-to-Preview** - Touch-friendly preview system for mobile/VR devices
- **Scene Thumbnails** - Visual scrub bar with frame previews
- **VR-Optimized Controls** - Touch-friendly interface for VR devices
- **Memory Management** - Efficient preview loading and cleanup
- **Fallback Strategies** - Works on constrained devices

### 📊 **Smart Management & Analytics**

- **Favorites System** - Heart-based favoriting with visual feedback
- **Rating System** - User ratings and recommendations
- **Tagging System** - Organize videos with custom tags
- **View Analytics** - Track viewing patterns and statistics
- **Metadata Management** - Rich video information storage
- **Performance Metrics** - Real-time FPS, memory usage, and UX event tracking
- **Cache Performance** - Monitor cache hit rates and response times

### 🚀 **Performance & Reliability**

- **Intelligent Caching** - Fast thumbnail and metadata loading with SQLite backend
- **Database Optimization** - SQLite with automatic JSON migration support
- **Performance Monitoring** - Real-time server health tracking
- **Error Handling** - Graceful degradation and recovery
- **Debug Tools** - Comprehensive troubleshooting utilities
- **Background Processing** - Non-blocking thumbnail generation

### ♿ **Accessibility Features (WCAG AA Compliant)**

- **Screen Reader Support** - Complete ARIA labels and roles
- **Keyboard Navigation** - Full tab navigation with visible focus indicators
- **High Contrast Mode** - Toggle for enhanced visibility
- **Touch Targets** - 44px minimum for mobile accessibility
- **Reduced Motion** - Respects `prefers-reduced-motion` system setting
- **Color Contrast** - Minimum 4.5:1 ratio maintained across all themes

## 🛠️ Installation

### Prerequisites

- **Python 3.13+** (recommended)
- **Modern web browser** (Chrome, Firefox, Safari, Edge)
- **FFmpeg** (for video processing and thumbnails)

### Quick Start

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd local-video-server
   ```

2. **Install Python dependencies**

   ```bash
   pip install flask pillow sqlite3
   # Optional: For AI features
   pip install openai
   ```

3. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key (optional)
   ```

4. **Create required directories**

   ```bash
   mkdir -p videos static/thumbnails
   ```

5. **Add your videos**

   ```bash
   # Copy your video files to the videos/ directory
   cp /path/to/your/videos/* videos/
   ```

6. **Start the server**

   ```bash
   python main.py
   ```

7. **Open your browser**

   ```bash
   http://localhost:5000
   ```

## 📁 Project Structure

```bash
local-video-server/
├── 📄 main.py                    # Main Flask application
├── 📄 cache_manager.py           # Caching system with SQLite backend
├── 📄 thumbnail_manager.py       # Thumbnail generation
├── 📄 performance_monitor.py     # Performance tracking
├── 📄 database_migration.py      # Database management
├── 📁 static/                    # Frontend assets
│   ├── 🎨 glassmorphic-theme.css # Glassmorphic UI theme
│   ├── 🎨 neomorphic-theme.css   # Neomorphic UI theme
│   ├── 🎨 hybrid-theme.css       # Hybrid UI theme
│   ├── ⚡ adaptive-streaming.js  # ABR streaming engine
│   ├── 📱 device-detection.js    # Cross-platform detection
│   ├── 🎬 video-preview-enhanced.js # Advanced video previews
│   ├── 🌐 network-monitor.js     # Network speed monitoring
│   ├── 🎯 theme-manager.js       # Theme switching system
│   ├── ❤️ favorites.js           # Favorites management
│   ├── 📊 metrics.js             # Performance metrics collection
│   └── 🖼️ thumbnails/           # Generated thumbnails
├── 📁 templates/                 # HTML templates
│   ├── 🏠 index.html            # Main video gallery
│   ├── ▶️ watch.html            # Video player page
│   ├── ⭐ favorites.html        # Favorites collection
│   └── 🏷️ tags.html            # Tag management
├── 📁 videos/                    # Your video files
├── 📁 docs/                      # Documentation
│   ├── 📖 ADAPTIVE_STREAMING_SYSTEM.md
│   ├── 🎨 GLASSMORPHIC_NEOMORPHIC_DESIGN.md
│   ├── 🎬 VIDEO_PREVIEW_IMPROVEMENTS.md
│   ├── 📊 PERFORMANCE_ANALYSIS_SUMMARY.md
│   ├── 🔧 IMPLEMENTATION_GUIDE.md # Complete feature checklist & code
│   └── 🧪 QA_TESTING_GUIDE.md    # Complete testing procedures
├── 📄 favorites.json             # User favorites data
├── 📄 ratings.json               # User ratings data
├── 📄 tags.json                  # Video tags data
├── 📄 views.json                 # View analytics data
└── 📄 video_metadata.db          # SQLite database
```

## 🎮 Usage Guide

### **Basic Navigation**

- **Home Page** - Browse all videos with thumbnails
- **Video Player** - Click any video to start watching
- **Favorites** - Heart icon to add/remove favorites
- **Tags** - Organize and filter videos by tags
- **Themes** - Switch between glassmorphic, neomorphic, and hybrid themes

### **Keyboard Shortcuts**

- **Ctrl+1** - Switch to Default theme
- **Ctrl+2** - Switch to Glassmorphic theme
- **Ctrl+3** - Switch to Neomorphic theme
- **Ctrl+4** - Switch to Hybrid theme
- **Ctrl+D** - Toggle Dark/Light mode
- **Tab** - Navigate through all interactive elements

### **Advanced Features**

#### **Adaptive Streaming**

The server automatically adjusts video quality based on:

- Network speed and stability
- Device capabilities
- Buffer health
- User preferences

#### **Video Previews**

- **Desktop** - Hover over thumbnails for instant scene previews
- **Mobile/VR** - Tap thumbnails to start preview (tap again to stop)
- **Scrub** through videos without opening the player
- **VR Mode** - Touch-friendly controls for VR devices

#### **Theme Customization**

- **Glassmorphic** - Modern frosted glass aesthetic
- **Neomorphic** - Soft, tactile button design
- **Hybrid** - Combined glass and shadow effects
- **Dark Mode** - Available for all themes
- **High Contrast** - Enhanced accessibility mode

#### **Performance Monitoring**

- **Real-time Metrics** - FPS, memory usage, and UX events
- **Console Access** - Run `__LVS_METRICS()` to view current metrics
- **Cache Status** - Monitor cache hit rates and performance
- **System Health** - Track server response times and errors

## ⚙️ Configuration

### **Environment Variables**

```bash
# OpenAI API (optional - for AI features)
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Chat Settings (optional)
CHAT_MAX_TOKENS=300
CHAT_TEMPERATURE=0.7

# Cache Settings
CACHE_TTL=300                        # Cache refresh interval (seconds)
```

### **Server Settings**

Edit `main.py` to customize:

- **Port** - Default: 5000
- **Video Directory** - Default: `videos/`
- **Thumbnail Directory** - Default: `static/thumbnails/`
- **Cache Settings** - Memory and disk cache limits

## 🔧 Advanced Setup

### **FFmpeg Installation**

For thumbnail generation and video processing:

**Windows:**

```bash
# Using Chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
```

**macOS:**

```bash
# Using Homebrew
brew install ffmpeg
```

**Linux:**

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg
```

### **Performance Optimization**

- **SSD Storage** - Store videos on SSD for faster access
- **RAM** - 8GB+ recommended for large video collections
- **Network** - Gigabit ethernet for 4K streaming
- **CPU** - Multi-core processor for thumbnail generation

## 🚀 Development

### **Adding New Features**

1. Create feature branch: `git checkout -b feature/new-feature`
2. Add your code in appropriate directories
3. Update documentation in `docs/`
4. Test thoroughly across devices and themes
5. Submit pull request

### **Code Style**

- **Python** - Follow PEP 8 standards
- **JavaScript** - Use ES6+ features
- **CSS** - BEM methodology for class naming
- **HTML** - Semantic markup with accessibility

### **Testing**

```bash
# Run video preview tests
python test_video_preview.py

# Test database functionality
python -c "from cache_manager import cache; print('Cache OK')"

# Check theme integration
# Open browser and test all three themes

# Verify accessibility
# Run Lighthouse audit (target ≥90 accessibility score)
```

### **QA Testing**

Use the comprehensive testing template in `docs/QA_TESTING_TEMPLATE.md`:

- **Phase 1** - Fast verification of implemented features
- **Phase 2** - Functional QA testing (10 minutes)
- **Phase 3** - Lighthouse & WCAG compliance testing

## 📚 Documentation

Comprehensive documentation is available in the `docs/` folder:

- **[Adaptive Streaming System](docs/ADAPTIVE_STREAMING_SYSTEM.md)** - ABR implementation details
- **[UI Design System](docs/GLASSMORPHIC_NEOMORPHIC_DESIGN.md)** - Theme architecture and customization
- **[Video Preview System](docs/VIDEO_PREVIEW_IMPROVEMENTS.md)** - Cross-platform preview implementation
- **[Performance Analysis](docs/PERFORMANCE_ANALYSIS_SUMMARY.md)** - Optimization strategies and results
- **[QA Testing Guide](docs/QA_TESTING_GUIDE.md)** - Complete testing procedures and verification

## 🛣️ Roadmap

### **Completed Features** ✅

- [x] **Advanced Video Streaming** - ABR with 7 quality levels
- [x] **Modern UI Themes** - Glassmorphic, Neomorphic, Hybrid
- [x] **Cross-Platform Support** - Desktop, mobile, tablet, VR
- [x] **Accessibility Compliance** - WCAG AA with high contrast mode
- [x] **Performance Metrics** - Real-time monitoring and analytics
- [x] **Touch-Friendly Interface** - 44px minimum targets
- [x] **Keyboard Shortcuts** - Theme switching and dark mode
- [x] **Mobile Preview System** - Tap-to-preview functionality

### **Upcoming Features**

- [ ] **Advanced Search** - Metadata, duration, and content-based search
- [ ] **Playlist Management** - User-curated and smart playlists
- [ ] **Subtitle Support** - Multi-language subtitle management
- [ ] **AI-Powered Features** - Content analysis and recommendations
- [ ] **Mini Player** - Picture-in-picture functionality
- [ ] **Performance Dashboard** - Real-time analytics and metrics

### **Long-term Goals**

- [ ] **Mobile Apps** - Native iOS and Android applications
- [ ] **Multi-user Support** - User accounts and permissions
- [ ] **Cloud Integration** - Backup and sync capabilities
- [ ] **Live Streaming** - Real-time video broadcasting
- [ ] **Content Management** - Advanced admin tools

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly using the QA testing template
5. **Submit** a pull request

### **Areas for Contribution**

- 🐛 Bug fixes and improvements
- ✨ New features and enhancements
- 📖 Documentation updates
- 🎨 UI/UX improvements
- 🚀 Performance optimizations
- ♿ Accessibility enhancements

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Flask** - Excellent Python web framework
- **Bootstrap** - Responsive CSS framework
- **Font Awesome** - Beautiful icons
- **Material Design** - Google's design system
- **OpenAI** - AI-powered features
- **WCAG Guidelines** - Accessibility standards

## 📞 Support

- **Issues** - Report bugs and request features on GitHub
- **Documentation** - Check the `docs/` folder for detailed guides
- **Community** - Join discussions and get help
- **QA Testing** - Use the comprehensive testing template for validation

---

## **Made with ❤️ for video enthusiasts and developers**

*Transform your local video collection into a professional streaming experience with enterprise-grade accessibility and performance!*

## 🎯 **Current Status: 100% UI Complete**

All planned UI features have been implemented and verified:

- ✅ **Glassmorphic/Neomorphic Design System**
- ✅ **Cross-Platform Compatibility**
- ✅ **Accessibility Compliance (WCAG AA)**
- ✅ **Performance Optimization**
- ✅ **Mobile/VR Support**
- ✅ **Theme Management**
- ✅ **Video Preview System**
- ✅ **Touch-Friendly Interface**
- ✅ **Performance Metrics**
- ✅ **Keyboard Shortcuts**

Ready for production deployment and user testing!
