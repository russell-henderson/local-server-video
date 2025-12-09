# 🎬 Local Video Server

A modern, professional-grade local video streaming application with intelligent caching, responsive design, and cross-platform support. Built with Flask (Python backend) and vanilla JavaScript for maximum performance and simplicity.

![Python](https://img.shields.io/badge/Python-3.13+-green?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-red?style=for-the-badge&logo=flask)
![JavaScript](https://img.shields.io/badge/JavaScript-Vanilla-yellow?style=for-the-badge&logo=javascript)
![SQLite](https://img.shields.io/badge/SQLite-Database-blue?style=for-the-badge&logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

## ✨ Features

### 📺 Video Streaming
- **Unified Video Player** - Consistent player across all pages
- **Range-Based Streaming** - Efficient HTTP range requests for large files
- **Resume Playback** - Automatic position saving and resume prompts
- **Keyboard Controls** - J/L (±10s), K/Space (play/pause), F (fullscreen), M (mute), ↑/↓ (volume)
- **URL Time Parameters** - Start at specific time with `?t=SECONDS`
- **Multiple Format Support** - MP4, MKV, WebM, MOV, AVI and more

### 🎨 User Interface
- **Responsive Design** - Desktop, mobile, tablet, and VR support
- **Dark/Light Themes** - Modern glassmorphic and neomorphic designs
- **Touch-Friendly Controls** - 44px+ minimum touch targets for accessibility
- **Theme Customization** - Switch between multiple visual themes
- **High Contrast Mode** - Enhanced accessibility for vision impaired users

### 🎥 Video Management
- **5-Star Rating System** - Rate and track video quality
- **Favorites** - Quick-save your favorite videos
- **Custom Tags** - Organize videos with flexible tagging system
- **View Analytics** - Track watch counts and engagement
- **Smart Search** - Find videos by name, tags, and metadata
- **Related Videos** - Intelligent content discovery recommendations

### 📊 Performance & Data
- **Intelligent Caching** - Dual-backend cache (SQLite + JSON fallback)
- **Automatic Thumbnail Generation** - Background FFmpeg thumbnail extraction
- **File Monitoring** - Real-time detection of new videos with debouncing
- **Database Authority** - Single source of truth for all metadata
- **Performance Monitoring** - Real-time route profiling and metrics
- **Concurrent Processing** - ThreadPoolExecutor for background tasks

### 🖼️ Gallery System (New!)
- **Image Gallery** - Organize loose images into virtual groups with selection mode
- **Favorites Everywhere** - Heart any image (loose or grouped) and filter to see all favorites at once
- **Covers & Management** - Set cover images, create/edit/delete groups without touching files
- **Clean Grid & Lightbox** - Filename-free tiles, lazy loading, keyboard/lightbox navigation, quick add-to-group/create-group actions

### 🔒 Privacy & Security
- **Local-Only Storage** - All data stored locally, no cloud required
- **User Metadata Protected** - Personal ratings and favorites kept private
- **No Tracking** - Zero external analytics or telemetry
- **CORS Support** - Optional cross-origin resource sharing
- **SQLite Encryption Ready** - Database security for sensitive deployments

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ (recommend 3.13)
- FFmpeg (for thumbnail generation)
- Windows, macOS, or Linux

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/russell-henderson/local-server-video.git
cd local-video-server
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the server:**
```bash
# Development mode (auto-reload)
.\dev.ps1 dev

# Production mode
.\dev.ps1 prod

# Or directly
python main.py
```

4. **Open in browser:**
```
http://localhost:5000
```

5. **Add your videos:**
   - Place video files in the `videos/` folder
   - Server auto-discovers and indexes them
   - Thumbnails generate automatically on demand

## ⚙️ Configuration

### Environment Variables

Configuration is loaded from (highest to lowest priority):
1. Environment variables (`LVS_*` prefix)
2. `.env` file
3. `config.json` file
4. Built-in defaults

**Example `.env` file:**
```bash
# Server
LVS_HOST=0.0.0.0
LVS_PORT=5000
LVS_DEBUG=false

# Directories
LVS_VIDEO_DIRECTORY=videos
LVS_THUMBNAIL_DIRECTORY=static/thumbnails

# Cache
LVS_CACHE_TIMEOUT=3600
LVS_CACHE_ENABLED=true

# Features
LVS_ANALYTICS_ENABLED=true
```

### Configuration File (`config.py`)

Edit `config.py` to customize:
- Server host and port
- Video and thumbnail directories
- Database paths
- Cache TTL and size limits
- Feature flags (analytics, VR mode)
- CORS settings

## 📁 Project Structure

```
local-video-server/
├── main.py                    # Flask app with all routes
├── config.py                  # Configuration management
├── cache_manager.py           # Metadata caching (SQLite + JSON)
├── database_migration.py      # SQLite schema and queries
├── file_watcher.py            # Directory monitoring for new files
├── thumbnail_manager.py       # Thumbnail generation and sync
├── performance_monitor.py     # Route latency tracking
├── healthcheck.py             # System health check utility
├── static/                    # Frontend assets
│   ├── styles.css            # Main stylesheet
│   ├── js/                   # JavaScript modules
│   │   ├── player.js         # Video player class
│   │   ├── ratings.js        # Rating interactions
│   │   ├── tags.js           # Tag management
│   │   └── favorites.js      # Favorite toggling
│   └── thumbnails/           # Generated thumbnails
├── templates/                 # Jinja2 templates
│   ├── index.html            # Video list
│   ├── watch.html            # Video player
│   ├── gallery.html          # Image gallery
│   ├── tags.html             # Tag browsing
│   ├── best_of.html          # High-rated videos
│   └── favorites.html        # Favorited videos
├── docs/                     # Comprehensive documentation
│   ├── IMPLEMENTATION.md     # Architecture & patterns
│   ├── PERFORMANCE.md        # Optimization notes
│   ├── UI.md                 # UI design & player behavior
│   ├── PYTHON_UPDATE.md      # Python files audit
│   └── ARCHIVE_INDEX.md      # Archived systems index
├── archive/                  # Legacy and deprecated code
├── videos/                   # Your video collection
├── images/                   # Gallery images
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies
└── dev.ps1                   # Windows development helper
```

## 🔧 Development

### Getting Started

1. **Read the architecture guide:**
   ```
   docs/IMPLEMENTATION.md - Essential reading for developers
   ```

2. **Understand key components:**
   - **cache_manager.py** - Metadata caching system
   - **database_migration.py** - SQLite database schema
   - **main.py** - Flask route handlers and API endpoints
   - **thumbnail_manager.py** - Thumbnail orchestration

3. **Code patterns:**
   - Use `@performance_monitor("route_name")` decorator on routes
   - Bulk-load metadata from cache (don't call cache.get_* multiple times)
   - Always validate file existence before serving
   - Use database as single source of truth

### Running Quality Checks

```bash
# Windows PowerShell:
.\dev.ps1 lint          # Check syntax and style
.\dev.ps1 test          # Run test suite
.\dev.ps1 health        # System health check
.\dev.ps1 clean         # Clean cache/logs

# Database maintenance:
.\dev.ps1 reindex       # Force video reindexing
.\dev.ps1 backup        # Backup databases
```

### Testing

```bash
# Test specific components
python -c "from cache_manager import cache; print('Cache OK')"
python -c "from database_migration import VideoDatabase; db = VideoDatabase(); print('DB OK')"

# Run linting
python -m pylint main.py
flake8 *.py

# Check database
sqlite3 video_metadata.db ".tables"
```

### Adding Features

1. **Create feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes:**
   - Follow existing code patterns
   - Add docstrings and type hints
   - Update `docs/` if changing architecture

3. **Test thoroughly:**
   - Test on desktop and mobile
   - Verify performance impact
   - Check database consistency

4. **Submit pull request:**
   - Reference related issues
   - Include test evidence
   - Update documentation

## 📚 Documentation

Start here for different tasks:

- **[IMPLEMENTATION.md](docs/IMPLEMENTATION.md)** - Architecture, design patterns, development workflow
- **[PERFORMANCE.md](docs/PERFORMANCE.md)** - Optimization strategies, profiling results
- **[UI.md](docs/UI.md)** - UI patterns, player behavior, theme system
- **[PYTHON_UPDATE.md](docs/PYTHON_UPDATE.md)** - Python files inventory and audit

**Maintenance & Utilities:**
- **[ARCHIVE_INDEX.md](docs/ARCHIVE_INDEX.md)** - Index of archived/deprecated systems
- **[copilot-instructions.md](.github/copilot-instructions.md)** - Copilot guidelines for this project

## 🛣️ Roadmap

### ✅ Completed

- [x] Unified video player with resume playback
- [x] Rating and tagging system
- [x] Favorite collection
- [x] 5-star rating system
- [x] SQLite backend with JSON fallback
- [x] Thumbnail auto-generation
- [x] File monitoring with debouncing
- [x] Performance monitoring and metrics
- [x] Responsive mobile/tablet support
- [x] Gallery system with image grouping
- [x] Multi-theme support
- [x] Accessibility compliance

### 🚧 In Progress / Planned

- [ ] Playlist management
- [ ] Mini-player (PiP)
- [ ] User authentication (multi-user support)
- [ ] Cloud backup integration
- [ ] Mobile app (iOS/Android)
- [ ] Live streaming support

## 🐛 Troubleshooting

### Server won't start
```bash
# Check if port is in use
lsof -i :5000              # macOS/Linux
netstat -ano | findstr :5000  # Windows

# Check Python version
python --version            # Should be 3.11+
```

### Missing thumbnails
```bash
# Regenerate all thumbnails
.\dev.ps1 health            # Check thumbnail status
.\dev.ps1 reindex           # Force regeneration
```

### Database issues
```bash
# Check database integrity
sqlite3 video_metadata.db ".tables"
sqlite3 video_metadata.db "PRAGMA integrity_check;"

# Backup before maintenance
.\dev.ps1 backup
```

### Performance problems
```bash
# Check performance metrics
# Visit: http://localhost:5000/admin/performance

# Monitor cache status
# Visit: http://localhost:5000/admin/cache/status

# Check system health
.\dev.ps1 health
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Areas for Contribution

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
- **SQLite** - Reliable embedded database
- **FFmpeg** - Powerful multimedia toolkit
- **Bootstrap** - Responsive CSS framework
- **Font Awesome** - Beautiful icon library
- **WCAG** - Web accessibility guidelines

## 📞 Support & Resources

- **Issues** - Report bugs or request features on [GitHub](https://github.com/russell-henderson/local-server-video/issues)
- **Documentation** - Check the `docs/` folder for detailed guides
- **Architecture** - See `docs/IMPLEMENTATION.md` for system design
- **Maintenance** - See `docs/PERFORMANCE.md` for optimization tips

---

**Made with ❤️ for video enthusiasts and developers**

*Transform your local video collection into a professional streaming experience!*
