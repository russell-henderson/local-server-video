# 🎬 Local Video Server

A modern, feature-rich local video server with a unified video player, clean dark mode interface, and comprehensive video management. Built with Flask and vanilla JavaScript for maximum performance and simplicity.

![Video Server](https://img.shields.io/badge/Video-Server-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.13+-green?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-red?style=for-the-badge&logo=flask)
![JavaScript](https://img.shields.io/badge/JavaScript-Vanilla-yellow?style=for-the-badge&logo=javascript)
![Dark Mode](https://img.shields.io/badge/Dark%20Mode-Only-black?style=for-the-badge)

## ✨ Features

### 🎥 **Unified Video Player**

- **Shared Player Component** - Single video player used across all pages
- **±10 Second Skip** - Quick navigation with buttons and keyboard shortcuts
- **Keyboard Controls** - Full keyboard support (J/L = ±10s, K/Space = play/pause, F = fullscreen, M = mute, ↑/↓ = volume)
- **Resume Playback** - Automatic position saving and resume prompts via localStorage
- **URL Time Parameters** - Support for `?t=SECONDS` to start at specific time
- **Range Streaming** - Efficient HTTP range requests for large video files

### 🎨 **Clean Dark Mode Interface**

- **Dark Mode Only** - Optimized for comfortable viewing
- **Consistent Styling** - Single CSS framework across all pages
- **Responsive Design** - Works on desktop, mobile, and Quest 2 browser
- **Bootstrap Integration** - Grid system and utilities for responsive layouts
- **Font Awesome Icons** - Professional iconography throughout

### 📊 **Smart Video Management**

- **Favorites System** - Heart-based favoriting with instant visual feedback
- **5-Star Rating System** - User ratings with click-to-rate interface
- **Tagging System** - Organize videos with custom tags (add/remove dynamically)
- **View Analytics** - Track view counts and engagement
- **Sorting Options** - Sort by rating, title, views, or date added
- **Best of Collection** - Automatically curated high-rated videos (4+ stars)

### 🔍 **Enhanced Video Previews**

- **Hover Preview** - Mouse-over video preview on thumbnails (desktop)
- **Touch-Friendly** - Disabled on touch devices for better mobile experience
- **Play Overlays** - Visual feedback on thumbnail hover
- **Fallback Thumbnails** - Graceful handling of missing thumbnails

### 🚀 **Performance & Architecture**

- **Framework-Free Architecture** - Vanilla JavaScript for maximum performance
- **Modular Design** - Shared components and templates
- **Efficient Caching** - Fast thumbnail and metadata loading with SQLite backend
- **Database Optimization** - SQLite with automatic JSON migration support
- **Error Handling** - Graceful degradation and recovery
- **Background Processing** - Non-blocking thumbnail generation

## 📺 **Available Pages**

- **Home** - Video gallery with sorting and filtering options
- **Watch** - Dedicated video player page with rating, tagging, and related videos
- **Random** - Redirects to a random video for discovery
- **Best of** - Curated collection of highest-rated videos (4+ stars)
- **Favorites** - Personal collection of hearted videos
- **Tags** - Browse all available tags
- **Tag Videos** - View videos filtered by specific tag

## ⌨️ **Keyboard Shortcuts**

### Video Player Controls

- **J** - Skip backward 10 seconds
- **L** - Skip forward 10 seconds  
- **K** or **Space** - Play/Pause toggle
- **F** - Toggle fullscreen
- **M** - Toggle mute
- **↑/↓** - Volume up/down

### General Navigation

- **Tab** - Navigate through interactive elements
- **Enter** - Activate buttons and links

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
│   ├── 📁 css/                   # Stylesheets
│   │   ├── 🎨 theme.css         # Dark mode theme variables
│   │   └── 🎨 app.css           # Main application styles
│   ├── � js/                    # JavaScript modules
│   │   ├── ⚡ player.js         # Shared video player component
│   │   └── � ui.js             # UI helpers and interactions
│   ├── 📁 thumbnails/           # Generated video thumbnails
│   └── 🎬 video-preview-enhanced.js # Lightweight video previews
├── 📁 templates/                 # HTML templates
│   ├── � _base.html            # Base template with shared layout
│   ├── � _navbar.html          # Navigation component
│   ├── � _player.html          # Shared video player component
│   ├── 🏠 index.html            # Main video gallery
│   ├── ▶️ watch.html            # Video player page
│   ├── ⭐ favorites.html        # Favorites collection
│   ├── 🏆 best_of.html          # Best rated videos
│   ├── 🏷️ tags.html            # All tags overview
│   └── 📁 tag_videos.html       # Videos by tag
├── 📁 videos/                    # Video files directory
├── 📁 docs/                      # Documentation
│   └── 📁 deferred/             # Removed features documentation
└── 🗄️ *.json                   # Data files (ratings, favorites, tags, views)


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



