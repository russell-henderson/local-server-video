"""
Configuration system for Local Video Server
Supports environment variables, .env files, and JSON config with validation
"""

import os
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path

@dataclass
class ServerConfig:
    """Server configuration with validation and defaults"""
    
    # Server settings
    host: str = "127.0.0.1"
    port: int = 5000
    debug: bool = False
    
    # Video settings
    video_directory: str = "videos"
    thumbnail_directory: str = "static/thumbnails"
    max_thumbnail_size: tuple = (320, 240)
    supported_formats: list = field(default_factory=lambda: ['.mp4', '.avi', '.mkv', '.mov', '.wmv'])
    
    # Database settings
    metadata_db: str = "video_metadata.db"
    cache_db: str = "video_cache.db"
    
    # Performance settings
    cache_timeout: int = 3600  # 1 hour
    max_cache_size: int = 1000
    enable_thumbnails: bool = True
    thumbnail_quality: int = 85
    
    # Search settings
    search_enabled: bool = True
    search_index_on_startup: bool = True
    
    # Monitoring settings
    enable_analytics: bool = True
    log_level: str = "INFO"
    max_log_size: int = 10 * 1024 * 1024  # 10MB
    
    # Security settings
    enable_cors: bool = False
    allowed_origins: list = field(default_factory=list)
    
    # Feature flags
    feature_vr_simplify: bool = True
    feature_previews: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration values"""
        if self.port < 1 or self.port > 65535:
            raise ValueError(f"Invalid port: {self.port}. Must be between 1-65535")
        
        if self.thumbnail_quality < 1 or self.thumbnail_quality > 100:
            raise ValueError(f"Invalid thumbnail quality: {self.thumbnail_quality}. Must be between 1-100")
        
        if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            raise ValueError(f"Invalid log level: {self.log_level}")
        
        # Ensure directories exist
        Path(self.video_directory).mkdir(exist_ok=True)
        Path(self.thumbnail_directory).mkdir(parents=True, exist_ok=True)

class ConfigManager:
    """Manages configuration loading with cascade: env vars → .env → config.json → defaults"""
    
    def __init__(self, config_file: str = "config.json", env_file: str = ".env"):
        self.config_file = config_file
        self.env_file = env_file
        self._config = None
    
    def load_config(self) -> ServerConfig:
        """Load configuration with cascade priority"""
        if self._config is not None:
            return self._config
        
        # Start with defaults
        config_data = {}
        
        # 1. Load from JSON config file
        config_data.update(self._load_json_config())
        
        # 2. Load from .env file
        config_data.update(self._load_env_file())
        
        # 3. Override with environment variables
        config_data.update(self._load_env_vars())
        
        # Create config object with validation
        try:
            self._config = ServerConfig(**config_data)
            print(f"✅ Configuration loaded successfully")
            return self._config
        except Exception as e:
            print(f"❌ Configuration error: {e}")
            print("Using default configuration...")
            self._config = ServerConfig()
            return self._config
    
    def _load_json_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if not os.path.exists(self.config_file):
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                print(f"📄 Loaded config from {self.config_file}")
                return data
        except Exception as e:
            print(f"⚠️  Error loading {self.config_file}: {e}")
            return {}
    
    def _load_env_file(self) -> Dict[str, Any]:
        """Load configuration from .env file"""
        if not os.path.exists(self.env_file):
            return {}
        
        config_data = {}
        try:
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove LVS_ prefix if present
                        if key.startswith('LVS_'):
                            key = key[4:]
                        config_data[key.lower()] = self._parse_env_value(value)
            
            if config_data:
                print(f"🔧 Loaded config from {self.env_file}")
            return config_data
        except Exception as e:
            print(f"⚠️  Error loading {self.env_file}: {e}")
            return {}
    
    def _load_env_vars(self) -> Dict[str, Any]:
        """Load configuration from environment variables with LVS_ prefix"""
        config_data = {}
        prefix = "LVS_"
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                config_data[config_key] = self._parse_env_value(value)
        
        if config_data:
            print(f"🌍 Loaded config from environment variables")
        return config_data
    
    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type"""
        value = value.strip().strip('"\'')
        
        # Boolean values
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # Numeric values
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # List values (comma-separated)
        if ',' in value:
            return [item.strip() for item in value.split(',')]
        
        # String value
        return value
    
    def save_config(self, config: ServerConfig) -> bool:
        """Save current configuration to JSON file"""
        try:
            config_dict = {
                'host': config.host,
                'port': config.port,
                'debug': config.debug,
                'video_directory': config.video_directory,
                'thumbnail_directory': config.thumbnail_directory,
                'max_thumbnail_size': config.max_thumbnail_size,
                'supported_formats': config.supported_formats,
                'metadata_db': config.metadata_db,
                'cache_db': config.cache_db,
                'cache_timeout': config.cache_timeout,
                'max_cache_size': config.max_cache_size,
                'enable_thumbnails': config.enable_thumbnails,
                'thumbnail_quality': config.thumbnail_quality,
                'search_enabled': config.search_enabled,
                'search_index_on_startup': config.search_index_on_startup,
                'enable_analytics': config.enable_analytics,
                'log_level': config.log_level,
                'max_log_size': config.max_log_size,
                'enable_cors': config.enable_cors,
                'allowed_origins': config.allowed_origins,
                'feature_vr_simplify': config.feature_vr_simplify,
                'feature_previews': config.feature_previews
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            print(f"💾 Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")
            return False
    
    def reload_config(self) -> ServerConfig:
        """Reload configuration from files"""
        self._config = None
        return self.load_config()

# Global configuration instance
config_manager = ConfigManager()

def get_config() -> ServerConfig:
    """Get the current configuration"""
    return config_manager.load_config()

def reload_config() -> ServerConfig:
    """Reload configuration from files"""
    return config_manager.reload_config()

if __name__ == "__main__":
    # Test configuration loading
    print("Testing configuration system...")
    config = get_config()
    print(f"Server will run on {config.host}:{config.port}")
    print(f"Video directory: {config.video_directory}")
    print(f"Debug mode: {config.debug}")
    print(f"Log level: {config.log_level}")