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

Comprehensive, consolidated documentation is available in the `docs/` folder. For most developer and maintenance tasks, start with these top-level documents:

- **[Implementation & Architecture](docs/IMPLEMENTATION.md)** — code structure, key components, and developer guidance
- **[Performance & Optimization](docs/PERFORMANCE.md)** — profiling results, optimization notes, and action items
- **[UI & Player Guide](docs/UI.md)** — UI patterns, player behavior, and theme details
- **[Project Todos & Roadmap](docs/TODOS.md)** — high-level tasks and remaining work

More specialized or historical documents have been archived under `docs/deferred/` for reference.

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
