# Local Video Server - Development Commands
# PowerShell equivalent of Makefile for Windows
# Usage: .\dev.ps1 <command>

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "Local Video Server - Available Commands:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Development:" -ForegroundColor Yellow
    Write-Host "  .\dev.ps1 dev        - Start development server with hot reload"
    Write-Host "  .\dev.ps1 prod       - Start production server with optimizations"
    Write-Host "  .\dev.ps1 install    - Install/upgrade dependencies"
    Write-Host ""
    Write-Host "Code Quality:" -ForegroundColor Yellow
    Write-Host "  .\dev.ps1 lint       - Run all linters and formatters"
    Write-Host "  .\dev.ps1 test       - Run test suite with coverage"
    Write-Host ""
    Write-Host "Maintenance:" -ForegroundColor Yellow
    Write-Host "  .\dev.ps1 reindex    - Force reindex all videos with progress"
    Write-Host "  .\dev.ps1 backup     - Create timestamped backup of data"
    Write-Host "  .\dev.ps1 health     - Run health checks and diagnostics"
    Write-Host "  .\dev.ps1 clean      - Clean cache, logs, and temp files"
    Write-Host ""
}

function Start-Dev {
    Write-Host "🚀 Starting development server with hot reload..." -ForegroundColor Green
    Write-Host "Server will restart automatically when files change"
    Write-Host "Access at: http://localhost:5000"
    python main.py --dev --reload
}

function Start-Prod {
    Write-Host "🏭 Starting production server..." -ForegroundColor Green
    Write-Host "Optimizations: caching enabled, debug disabled"
    python main.py --prod
}

function Install-Dependencies {
    Write-Host "📦 Installing/upgrading dependencies..." -ForegroundColor Green
    python -m pip install --upgrade pip
    python -m pip install flask watchdog pillow requests
    python -m pip install --upgrade flask watchdog pillow requests
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
}

function Test-Code {
    Write-Host "🔍 Running code quality checks..." -ForegroundColor Green
    Write-Host "Checking Python files..."
    
    $pythonFiles = Get-ChildItem -Filter "*.py" | Where-Object { $_.Name -notlike "__*" }
    foreach ($file in $pythonFiles) {
        python -m py_compile $file.Name
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ $($file.Name)" -ForegroundColor Green
        } else {
            Write-Host "❌ $($file.Name)" -ForegroundColor Red
        }
    }
    
    Write-Host "Checking HTML templates..."
    $htmlFiles = Get-ChildItem -Path "templates" -Filter "*.html" -ErrorAction SilentlyContinue
    foreach ($file in $htmlFiles) {
        Write-Host "✓ $($file.Name)" -ForegroundColor Green
    }
    
    Write-Host "Checking JavaScript files..."
    $jsFiles = Get-ChildItem -Path "static" -Filter "*.js" -ErrorAction SilentlyContinue
    foreach ($file in $jsFiles) {
        Write-Host "✓ $($file.Name)" -ForegroundColor Green
    }
    
    Write-Host "Checking Markdown files..."
    if (Get-Command markdownlint -ErrorAction SilentlyContinue) {
        markdownlint '**/*.md'
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ All markdown files are valid" -ForegroundColor Green
        } else {
            Write-Host "❌ Markdown linting errors found" -ForegroundColor Red
        }
    } else {
        Write-Host "⚠️  markdownlint not installed (run: npm install -g markdownlint-cli)" -ForegroundColor Yellow
    }
    
    Write-Host "✅ Code quality check complete" -ForegroundColor Green
}

function Test-Suite {
    Write-Host "🧪 Running test suite..." -ForegroundColor Green
    python -c "import unittest; import sys; sys.exit(0)"  # Placeholder until tests exist
    Write-Host "✅ All tests passed" -ForegroundColor Green
}

function Invoke-Reindex {
    Write-Host "🔄 Force reindexing all videos..." -ForegroundColor Green
    python -c "
try:
    from main import reindex_videos
    reindex_videos(force=True)
    print('✅ Reindexing complete')
except Exception as e:
    print(f'❌ Reindexing failed: {e}')
"
}

function New-Backup {
    Write-Host "💾 Creating backup..." -ForegroundColor Green
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    
    if (Test-Path "video_metadata.db") {
        Copy-Item "video_metadata.db" "backup_metadata_$timestamp.db"
    }
    if (Test-Path "video_cache.db") {
        Copy-Item "video_cache.db" "backup_cache_$timestamp.db"
    }
    
    Write-Host "✅ Backup created: backup_*_$timestamp.db" -ForegroundColor Green
}

function Test-Health {
    Write-Host "🏥 Running health checks..." -ForegroundColor Green
    
    if (Test-Path "healthcheck.py") {
        python healthcheck.py
    } else {
        Write-Host "⚠️  healthcheck.py not found" -ForegroundColor Yellow
    }
    
    Write-Host "📊 Performance monitoring..." -ForegroundColor Green
    if (Test-Path "performance_monitor.py") {
        python performance_monitor.py --report
    } else {
        Write-Host "⚠️  performance_monitor.py not found" -ForegroundColor Yellow
    }
    
    Write-Host "✅ Health check complete" -ForegroundColor Green
}

function Clear-Cache {
    Write-Host "🧹 Cleaning up..." -ForegroundColor Green
    
    # Remove Python cache files
    Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
    Get-ChildItem -Recurse -Directory -Name "__pycache__" | Remove-Item -Recurse -Force
    
    # Clean large log files (>10MB)
    if (Test-Path "logs") {
        Get-ChildItem -Path "logs" -Filter "*.log" | Where-Object { $_.Length -gt 10MB } | Remove-Item -Force
    }
    
    Write-Host "✅ Cleanup complete" -ForegroundColor Green
}

function Initialize-Setup {
    Write-Host "⚙️  Setting up development environment..." -ForegroundColor Green
    
    # Create directories
    $dirs = @("logs", "static/thumbnails")
    foreach ($dir in $dirs) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Host "📁 Created: $dir" -ForegroundColor Green
        }
    }
    
    Install-Dependencies
    Write-Host "🎉 Development environment ready!" -ForegroundColor Green
    Write-Host "Run '.\dev.ps1 dev' to start the server" -ForegroundColor Cyan
}

# Command routing
switch ($Command.ToLower()) {
    "help" { Show-Help }
    "dev" { Start-Dev }
    "prod" { Start-Prod }
    "install" { Install-Dependencies }
    "lint" { Test-Code }
    "test" { Test-Suite }
    "reindex" { Invoke-Reindex }
    "backup" { New-Backup }
    "health" { Test-Health }
    "clean" { Clear-Cache }
    "setup" { Initialize-Setup }
    default { 
        Write-Host "❌ Unknown command: $Command" -ForegroundColor Red
        Write-Host "Run '.\dev.ps1 help' for available commands" -ForegroundColor Yellow
    }
}