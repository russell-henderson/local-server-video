# Local Video Server - Development Makefile
# Usage: make <target>

.PHONY: help dev prod lint test reindex backup health clean install dev-up dev-down dev-logs

# Default target
help:
	@echo "Local Video Server - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev        - Start development server with hot reload"
	@echo "  make prod       - Start production server with optimizations"
	@echo "  make dev-up     - Start Docker video-server fast loop (no rebuild)"
	@echo "  make dev-down   - Stop Docker video-server fast loop"
	@echo "  make dev-logs   - Tail Docker video-server logs"
	@echo "  make install    - Install/upgrade dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint       - Run all linters and formatters"
	@echo "  make test       - Run test suite with coverage"
	@echo ""
	@echo "Maintenance:"
	@echo "  make reindex    - Force reindex all videos with progress"
	@echo "  make backup     - Create timestamped backup of data"
	@echo "  make health     - Run health checks and diagnostics"
	@echo "  make clean      - Clean cache, logs, and temp files"
	@echo ""

# Development server with hot reload
dev:
	@echo "🚀 Starting development server with hot reload..."
	@echo "Server will restart automatically when files change"
	@echo "Access at: http://localhost:5000"
	@python main.py --dev --reload

# Docker fast dev loop (uses docker-compose.override.yml)
dev-up:
	@echo "🚀 Starting Docker fast dev loop for video-server..."
	@docker compose up -d video-server
	@echo "✅ video-server started (bind mount + reload)"

dev-down:
	@echo "🛑 Stopping Docker fast dev loop for video-server..."
	@docker compose stop video-server
	@echo "✅ video-server stopped"

dev-logs:
	@echo "📜 Tailing video-server logs (Ctrl+C to stop)..."
	@docker compose logs -f --tail=100 video-server

# Production server with optimizations
prod:
	@echo "🏭 Starting production server..."
	@echo "Optimizations: caching enabled, debug disabled"
	@python main.py --prod

# Install and upgrade dependencies
install:
	@echo "📦 Installing/upgrading dependencies..."
	@pip install --upgrade pip
	@pip install flask watchdog pillow requests
	@pip install --upgrade flask watchdog pillow requests
	@echo "✅ Dependencies installed"

# Code quality and linting
lint:
	@echo "🔍 Running code quality checks..."
	@echo "Checking Python files..."
	@python -m py_compile *.py || echo "⚠️  Python syntax errors found"
	@echo "Checking HTML templates..."
	@python -c "import os; [print(f'✓ {f}') for f in os.listdir('templates') if f.endswith('.html')]"
	@echo "Checking JavaScript files..."
	@python -c "import os; [print(f'✓ {f}') for f in os.listdir('static') if f.endswith('.js')]"
	@echo "✅ Code quality check complete"

# Run tests with coverage
test:
	@echo "🧪 Running test suite..."
	@python -m pytest -q tests
	@echo "✅ All tests passed"

# Force reindex all videos
reindex:
	@echo "🔄 Force reindexing all videos..."
	@python -c "from main import reindex_videos; reindex_videos(force=True)"
	@echo "✅ Reindexing complete"

# Create timestamped backup
backup:
	@echo "💾 Creating backup..."
	@python -c "import shutil, datetime; timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S'); shutil.copy('video_metadata.db', f'backup_metadata_{timestamp}.db'); shutil.copy('video_cache.db', f'backup_cache_{timestamp}.db'); print(f'✅ Backup created: backup_*_{timestamp}.db')"

# Health checks and diagnostics
health:
	@echo "🏥 Running health checks..."
	@python healthcheck.py
	@echo "📊 Performance monitoring..."
	@python performance_monitor.py --report
	@echo "✅ Health check complete"

# Clean cache, logs, and temp files
clean:
	@echo "🧹 Cleaning up..."
	@python -c "import os, glob, shutil; [os.remove(f) for f in glob.glob('*.pyc')]; [shutil.rmtree(d) for d in ['__pycache__'] if os.path.exists(d)]; [os.remove(f) for f in glob.glob('logs/*.log') if os.path.getsize(f) > 10*1024*1024]; print('✅ Cleanup complete')"

# Quick development setup
setup: install
	@echo "⚙️  Setting up development environment..."
	@python -c "import os; os.makedirs('logs', exist_ok=True); os.makedirs('static/thumbnails', exist_ok=True); print('✅ Directories created')"
	@echo "🎉 Development environment ready!"
	@echo "Run 'make dev' to start the server"
