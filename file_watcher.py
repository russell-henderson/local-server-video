"""
Enhanced File Watcher for Local Video Server
Provides intelligent monitoring with debouncing, batch processing, and duplicate detection
"""

import os
import time
import threading
from pathlib import Path
from typing import Set, Dict, Callable, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import hashlib

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("⚠️  Watchdog not available. Install with: pip install watchdog")

@dataclass
class FileChange:
    """Represents a file system change event"""
    path: str
    event_type: str  # 'created', 'modified', 'deleted', 'moved'
    timestamp: float
    size: int = 0
    checksum: str = ""

class VideoFileWatcher:
    """
    Intelligent file watcher with features:
    - Debouncing to handle rapid file changes
    - Batch processing for efficiency
    - Duplicate detection
    - Background processing
    - Integration with existing cache system
    """
    
    def __init__(self, 
                 video_directory: str = "videos",
                 thumbnail_directory: str = "static/thumbnails",
                 debounce_seconds: float = 2.0,
                 batch_size: int = 10,
                 supported_extensions: Set[str] = None):
        
        self.video_directory = Path(video_directory)
        self.thumbnail_directory = Path(thumbnail_directory)
        self.debounce_seconds = debounce_seconds
        self.batch_size = batch_size
        
        if supported_extensions is None:
            self.supported_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
        else:
            self.supported_extensions = supported_extensions
        
        # Internal state
        self._observer = None
        self._is_running = False
        self._pending_changes: Dict[str, FileChange] = {}
        self._change_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="FileWatcher")
        self._known_files: Dict[str, str] = {}  # path -> checksum for duplicate detection
        
        # Callbacks
        self._callbacks: Dict[str, Callable] = {
            'on_video_added': self._default_on_video_added,
            'on_video_removed': self._default_on_video_removed,
            'on_video_modified': self._default_on_video_modified,
            'on_batch_processed': self._default_on_batch_processed
        }
        
        # Start background processing thread
        self._processing_thread = threading.Thread(target=self._process_changes_loop, daemon=True)
        self._processing_thread.start()
    
    def set_callback(self, event_type: str, callback: Callable):
        """Set custom callback for file events"""
        if event_type in self._callbacks:
            self._callbacks[event_type] = callback
        else:
            raise ValueError(f"Unknown event type: {event_type}")
    
    def start_watching(self) -> bool:
        """Start watching the video directory"""
        if not WATCHDOG_AVAILABLE:
            print("❌ Cannot start file watcher: watchdog library not available")
            return False
        
        if self._is_running:
            print("⚠️  File watcher is already running")
            return True
        
        try:
            # Ensure video directory exists
            self.video_directory.mkdir(exist_ok=True)
            
            # Initialize known files
            self._scan_existing_files()
            
            # Set up file system observer
            event_handler = VideoFileEventHandler(self)
            self._observer = Observer()
            self._observer.schedule(event_handler, str(self.video_directory), recursive=True)
            self._observer.start()
            
            self._is_running = True
            print(f"👁️  File watcher started for: {self.video_directory}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start file watcher: {e}")
            return False
    
    def stop_watching(self):
        """Stop watching the video directory"""
        if not self._is_running:
            return
        
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        
        self._is_running = False
        self._executor.shutdown(wait=True)
        print("🛑 File watcher stopped")
    
    def _scan_existing_files(self):
        """Scan existing files to build checksum database"""
        print("🔍 Scanning existing video files...")
        count = 0
        
        for file_path in self.video_directory.rglob("*"):
            if (file_path.is_file() and 
                file_path.suffix.lower() in self.supported_extensions):
                
                try:
                    checksum = self._calculate_checksum(file_path)
                    self._known_files[str(file_path)] = checksum
                    count += 1
                except Exception as e:
                    print(f"⚠️  Error scanning {file_path}: {e}")
        
        print(f"✅ Scanned {count} existing video files")
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file (first 1MB for speed)"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                # Read first 1MB for speed
                chunk = f.read(1024 * 1024)
                hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _is_video_file(self, file_path: str) -> bool:
        """Check if file is a supported video format"""
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def handle_file_event(self, event_type: str, file_path: str):
        """Handle a file system event with debouncing"""
        if not self._is_video_file(file_path):
            return
        
        with self._change_lock:
            # Create file change record
            try:
                size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                checksum = self._calculate_checksum(Path(file_path)) if os.path.exists(file_path) else ""
            except Exception:
                size = 0
                checksum = ""
            
            change = FileChange(
                path=file_path,
                event_type=event_type,
                timestamp=time.time(),
                size=size,
                checksum=checksum
            )
            
            # Store with debouncing (latest event wins)
            self._pending_changes[file_path] = change
    
    def _process_changes_loop(self):
        """Background thread that processes pending changes"""
        while True:
            try:
                time.sleep(self.debounce_seconds)
                self._process_pending_changes()
            except Exception as e:
                print(f"❌ Error in change processing loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _process_pending_changes(self):
        """Process all pending changes in batches"""
        if not self._pending_changes:
            return
        
        with self._change_lock:
            # Get changes that are old enough (debounced)
            current_time = time.time()
            ready_changes = []
            
            for path, change in list(self._pending_changes.items()):
                if current_time - change.timestamp >= self.debounce_seconds:
                    ready_changes.append(change)
                    del self._pending_changes[path]
            
            if not ready_changes:
                return
        
        # Process changes in batches
        for i in range(0, len(ready_changes), self.batch_size):
            batch = ready_changes[i:i + self.batch_size]
            self._executor.submit(self._process_batch, batch)
    
    def _process_batch(self, changes: list):
        """Process a batch of file changes"""
        print(f"🔄 Processing batch of {len(changes)} file changes...")
        
        processed_count = 0
        for change in changes:
            try:
                # Check for duplicates
                if self._is_duplicate_file(change):
                    print(f"🔍 Duplicate detected: {Path(change.path).name}")
                    continue
                
                # Process based on event type
                if change.event_type in ['created', 'moved']:
                    self._callbacks['on_video_added'](change)
                    self._known_files[change.path] = change.checksum
                elif change.event_type == 'modified':
                    self._callbacks['on_video_modified'](change)
                    self._known_files[change.path] = change.checksum
                elif change.event_type == 'deleted':
                    self._callbacks['on_video_removed'](change)
                    self._known_files.pop(change.path, None)
                
                processed_count += 1
                
            except Exception as e:
                print(f"❌ Error processing {change.path}: {e}")
        
        # Notify batch completion
        if processed_count > 0:
            self._callbacks['on_batch_processed'](changes, processed_count)
    
    def _is_duplicate_file(self, change: FileChange) -> bool:
        """Check if this file is a duplicate based on checksum"""
        if not change.checksum:
            return False
        
        for existing_path, existing_checksum in self._known_files.items():
            if (existing_checksum == change.checksum and 
                existing_path != change.path and 
                os.path.exists(existing_path)):
                return True
        
        return False
    
    # Default callback implementations
    def _default_on_video_added(self, change: FileChange):
        """Default handler for new video files"""
        print(f"➕ Video added: {Path(change.path).name} ({change.size:,} bytes)")
        
        # Trigger thumbnail generation
        self._executor.submit(self._generate_thumbnail_async, change.path)
        
        # Invalidate cache if available
        try:
            from cache_manager import cache
            cache.invalidate_pattern("video_*")
        except ImportError:
            pass
    
    def _default_on_video_removed(self, change: FileChange):
        """Default handler for removed video files"""
        print(f"➖ Video removed: {Path(change.path).name}")
        
        # Remove thumbnail if it exists
        try:
            thumbnail_path = self.thumbnail_directory / f"{Path(change.path).stem}.jpg"
            if thumbnail_path.exists():
                thumbnail_path.unlink()
                print(f"🗑️  Removed thumbnail: {thumbnail_path.name}")
        except Exception as e:
            print(f"⚠️  Error removing thumbnail: {e}")
        
        # Invalidate cache
        try:
            from cache_manager import cache
            cache.invalidate_pattern("video_*")
        except ImportError:
            pass
    
    def _default_on_video_modified(self, change: FileChange):
        """Default handler for modified video files"""
        print(f"✏️  Video modified: {Path(change.path).name}")
        
        # Regenerate thumbnail
        self._executor.submit(self._generate_thumbnail_async, change.path)
    
    def _default_on_batch_processed(self, changes: list, processed_count: int):
        """Default handler for batch completion"""
        print(f"✅ Processed {processed_count}/{len(changes)} file changes")
    
    def _generate_thumbnail_async(self, video_path: str):
        """Generate thumbnail for video file"""
        try:
            from thumbnail_manager import generate_async
            generate_async(video_path)
        except ImportError:
            print(f"⚠️  Cannot generate thumbnail: thumbnail_manager not available")
        except Exception as e:
            print(f"❌ Error generating thumbnail for {video_path}: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current watcher status"""
        return {
            'is_running': self._is_running,
            'pending_changes': len(self._pending_changes),
            'known_files': len(self._known_files),
            'video_directory': str(self.video_directory),
            'supported_extensions': list(self.supported_extensions)
        }

class VideoFileEventHandler(FileSystemEventHandler):
    """Watchdog event handler that delegates to VideoFileWatcher"""
    
    def __init__(self, watcher: VideoFileWatcher):
        super().__init__()
        self.watcher = watcher
    
    def on_created(self, event):
        if not event.is_directory:
            self.watcher.handle_file_event('created', event.src_path)
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.watcher.handle_file_event('deleted', event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            self.watcher.handle_file_event('modified', event.src_path)
    
    def on_moved(self, event):
        if not event.is_directory:
            self.watcher.handle_file_event('deleted', event.src_path)
            self.watcher.handle_file_event('moved', event.dest_path)

# Global watcher instance
_global_watcher = None

def get_file_watcher() -> VideoFileWatcher:
    """Get the global file watcher instance"""
    global _global_watcher
    if _global_watcher is None:
        _global_watcher = VideoFileWatcher()
    return _global_watcher

def start_file_watcher() -> bool:
    """Start the global file watcher"""
    return get_file_watcher().start_watching()

def stop_file_watcher():
    """Stop the global file watcher"""
    if _global_watcher:
        _global_watcher.stop_watching()

if __name__ == "__main__":
    # Test the file watcher
    print("Testing Video File Watcher...")
    
    watcher = VideoFileWatcher()
    
    # Set custom callbacks
    def on_video_added(change):
        print(f"🎬 New video detected: {change.path}")
    
    watcher.set_callback('on_video_added', on_video_added)
    
    # Start watching
    if watcher.start_watching():
        print("File watcher started. Press Ctrl+C to stop...")
        try:
            while True:
                time.sleep(1)
                status = watcher.get_status()
                if status['pending_changes'] > 0:
                    print(f"Pending changes: {status['pending_changes']}")
        except KeyboardInterrupt:
            print("\nStopping file watcher...")
            watcher.stop_watching()
    else:
        print("Failed to start file watcher")