# Smart Search Pro - Architecture v2.0

> Complete system architecture for advanced file search and management application
> Integrates Everything SDK, multi-pass hashing, TeraCopy operations, and modern UI

**Date**: 2025-12-12
**Version**: 2.0.0
**Status**: Design Phase

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Module Structure](#module-structure)
3. [Database Schema](#database-schema)
4. [Configuration System](#configuration-system)
5. [Plugin Architecture](#plugin-architecture)
6. [Class Diagrams](#class-diagrams)
7. [Data Flow](#data-flow)
8. [API Contracts](#api-contracts)
9. [Technology Stack](#technology-stack)
10. [Scaling Considerations](#scaling-considerations)

---

## System Overview

### Architecture Pattern
**Layered Architecture** with **Plugin System**

```
┌─────────────────────────────────────────────────────────┐
│                    UI Layer (PyQt6)                     │
│  MainWindow │ SearchView │ DuplicatesView │ SettingsView│
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│                  Application Layer                      │
│    Controllers │ Coordinators │ State Management        │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│                   Service Layer                         │
│  Search │ Duplicates │ Operations │ Preview │ Export    │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┘
│                    Core Layer                           │
│   Database │ Config │ Cache │ EventBus │ Logging        │
└─────────────────────────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│               External Integration Layer                │
│  Everything SDK │ Windows API │ File System             │
└─────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns**: Clear boundaries between layers
2. **Dependency Injection**: Services injected via constructor
3. **Event-Driven**: Loosely coupled components via EventBus
4. **Plugin-First**: Extensible via plugin system
5. **Performance**: Async operations, caching, worker pools
6. **Testability**: Interface-based design, mockable dependencies

---

## Module Structure

### Directory Layout

```
smart_search/
├── core/                    # Core services and utilities
│   ├── __init__.py
│   ├── database.py          # SQLite database manager
│   ├── config.py            # Configuration management
│   ├── cache.py             # Multi-level caching system
│   ├── eventbus.py          # Event-driven communication
│   ├── logging.py           # Structured logging
│   ├── exceptions.py        # Custom exceptions
│   ├── utils.py             # Common utilities
│   └── constants.py         # Application constants
│
├── search/                  # Search engine module
│   ├── __init__.py
│   ├── engine.py            # Main search engine
│   ├── everything.py        # Everything SDK integration
│   ├── query_parser.py      # Query parsing and building
│   ├── filters.py           # Advanced filters (size, date, type)
│   ├── indexer.py           # Custom indexing for non-NTFS
│   ├── history.py           # Search history management
│   └── favorites.py         # Saved searches and favorites
│
├── duplicates/              # Duplicate finder module
│   ├── __init__.py
│   ├── scanner.py           # Duplicate scanning coordinator
│   ├── hasher.py            # Multi-pass hashing strategy
│   ├── comparator.py        # File comparison algorithms
│   ├── grouper.py           # Duplicate grouping logic
│   ├── cache.py             # Hash cache management
│   └── strategies.py        # Detection strategies (name, size, content)
│
├── operations/              # File operations module
│   ├── __init__.py
│   ├── manager.py           # Operations coordinator
│   ├── copy.py              # TeraCopy-style copying
│   ├── move.py              # Move operations
│   ├── delete.py            # Safe deletion with recycle bin
│   ├── rename.py            # Batch renaming
│   ├── buffer.py            # Buffer management
│   ├── verification.py      # CRC32/MD5 verification
│   └── queue.py             # Operation queue with priorities
│
├── preview/                 # File preview module
│   ├── __init__.py
│   ├── manager.py           # Preview coordinator
│   ├── text.py              # Text file preview
│   ├── image.py             # Image preview with thumbnails
│   ├── video.py             # Video preview (first frame)
│   ├── audio.py             # Audio metadata and waveform
│   ├── document.py          # PDF, Office previews
│   ├── archive.py           # ZIP, RAR contents
│   └── cache.py             # Preview cache
│
├── export/                  # Export module
│   ├── __init__.py
│   ├── exporter.py          # Export coordinator
│   ├── csv.py               # CSV export
│   ├── excel.py             # Excel export (openpyxl)
│   ├── html.py              # HTML report generation
│   ├── json.py              # JSON export
│   └── templates/           # HTML templates
│       └── report.html
│
├── ui/                      # PyQt6 UI components
│   ├── __init__.py
│   ├── main_window.py       # Main application window
│   ├── search_view.py       # Search interface
│   ├── duplicates_view.py   # Duplicates interface
│   ├── operations_view.py   # File operations queue
│   ├── preview_panel.py     # Preview panel
│   ├── settings_dialog.py   # Settings dialog
│   ├── widgets/             # Custom widgets
│   │   ├── __init__.py
│   │   ├── search_bar.py    # Smart search bar with autocomplete
│   │   ├── file_list.py     # High-performance file list
│   │   ├── filter_panel.py  # Advanced filters panel
│   │   ├── progress_bar.py  # Enhanced progress bar
│   │   └── toast.py         # Toast notifications
│   ├── dialogs/             # Dialogs
│   │   ├── __init__.py
│   │   ├── rename.py        # Batch rename dialog
│   │   ├── filter.py        # Filter builder dialog
│   │   └── about.py         # About dialog
│   └── styles/              # Qt stylesheets
│       ├── dark.qss
│       └── light.qss
│
├── system/                  # System integration module
│   ├── __init__.py
│   ├── tray.py              # System tray integration
│   ├── hotkeys.py           # Global hotkey registration
│   ├── admin.py             # UAC elevation helpers
│   ├── startup.py           # Windows startup integration
│   ├── clipboard.py         # Clipboard operations
│   └── shell.py             # Shell context menu integration
│
├── plugins/                 # Plugin system
│   ├── __init__.py
│   ├── manager.py           # Plugin manager
│   ├── base.py              # Base plugin class
│   ├── loader.py            # Dynamic plugin loading
│   ├── api.py               # Plugin API
│   └── examples/            # Example plugins
│       ├── custom_filter.py
│       └── custom_exporter.py
│
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── core/
│   ├── search/
│   ├── duplicates/
│   ├── operations/
│   └── conftest.py          # Pytest configuration
│
├── resources/               # Application resources
│   ├── icons/
│   ├── images/
│   └── translations/
│
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── setup.py                 # Installation script
├── pyproject.toml          # Build configuration
└── README.md               # Documentation
```

---

## Database Schema

### SQLite Database: `smart_search.db`

#### 1. Search History

```sql
CREATE TABLE search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    query_type TEXT NOT NULL,           -- 'simple', 'advanced', 'regex'
    filters_json TEXT,                  -- JSON: filters applied
    result_count INTEGER DEFAULT 0,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_query (query),
    INDEX idx_created_at (created_at DESC)
);
```

#### 2. Saved Searches / Favorites

```sql
CREATE TABLE saved_searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    query TEXT NOT NULL,
    query_type TEXT NOT NULL,
    filters_json TEXT,
    color TEXT,                         -- Tag color
    icon TEXT,                          -- Icon identifier
    shortcut TEXT,                      -- Keyboard shortcut
    is_pinned BOOLEAN DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_name (name),
    INDEX idx_is_pinned (is_pinned)
);
```

#### 3. Hash Cache

```sql
CREATE TABLE hash_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    modified_time INTEGER NOT NULL,     -- Unix timestamp
    quick_hash TEXT,                    -- First 8KB + Last 8KB hash
    full_hash TEXT,                     -- Full file MD5/SHA256
    hash_algorithm TEXT DEFAULT 'md5',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(file_path, file_size, modified_time),
    INDEX idx_file_path (file_path),
    INDEX idx_quick_hash (quick_hash),
    INDEX idx_full_hash (full_hash),
    INDEX idx_file_size (file_size)
);
```

#### 4. File Tags

```sql
CREATE TABLE file_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    tag TEXT NOT NULL,
    color TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(file_path, tag),
    INDEX idx_file_path (file_path),
    INDEX idx_tag (tag)
);

CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    color TEXT DEFAULT '#808080',
    description TEXT,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_name (name)
);
```

#### 5. Application Settings

```sql
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    type TEXT NOT NULL,                 -- 'string', 'int', 'bool', 'json'
    category TEXT,                      -- 'search', 'duplicates', 'operations', etc.
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 6. Operation History

```sql
CREATE TABLE operation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_type TEXT NOT NULL,       -- 'copy', 'move', 'delete', 'rename'
    source_paths TEXT NOT NULL,         -- JSON array
    destination_path TEXT,
    file_count INTEGER DEFAULT 0,
    total_size INTEGER DEFAULT 0,
    status TEXT NOT NULL,               -- 'completed', 'failed', 'cancelled'
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,

    INDEX idx_operation_type (operation_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at DESC)
);
```

#### 7. Preview Cache Metadata

```sql
CREATE TABLE preview_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    file_size INTEGER NOT NULL,
    modified_time INTEGER NOT NULL,
    preview_type TEXT NOT NULL,         -- 'thumbnail', 'text', 'metadata'
    cache_path TEXT NOT NULL,
    cache_size INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_file_path (file_path),
    INDEX idx_accessed_at (accessed_at)
);
```

#### Database Maintenance

```sql
-- Cleanup old search history (keep last 1000)
DELETE FROM search_history
WHERE id NOT IN (
    SELECT id FROM search_history
    ORDER BY created_at DESC
    LIMIT 1000
);

-- Cleanup stale hash cache (files modified or deleted)
DELETE FROM hash_cache
WHERE created_at < datetime('now', '-30 days');

-- Cleanup preview cache for deleted files
DELETE FROM preview_cache
WHERE accessed_at < datetime('now', '-7 days');
```

---

## Configuration System

### Configuration Architecture

```
┌─────────────────────────────────────────┐
│         ConfigManager                   │
│  ┌───────────────────────────────────┐  │
│  │  Default Config (embedded)        │  │
│  └───────────────────────────────────┘  │
│              ↓ override                 │
│  ┌───────────────────────────────────┐  │
│  │  User Config (YAML/JSON)          │  │
│  └───────────────────────────────────┘  │
│              ↓ override                 │
│  ┌───────────────────────────────────┐  │
│  │  Database Settings (runtime)      │  │
│  └───────────────────────────────────┘  │
│              ↓ merge                    │
│  ┌───────────────────────────────────┐  │
│  │  Final Configuration              │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Configuration Files

#### `config.yaml` (User Configuration)

```yaml
application:
  name: "Smart Search Pro"
  version: "2.0.0"
  data_dir: "%APPDATA%/SmartSearchPro"
  log_level: "INFO"
  max_recent_files: 1000

search:
  engine: "everything"          # 'everything' or 'builtin'
  everything_sdk_path: "C:/Program Files/Everything/Everything64.dll"
  max_results: 10000
  auto_search_delay_ms: 300     # Debounce delay
  case_sensitive: false
  match_whole_word: false
  regex_enabled: true
  indexing:
    enabled: true
    paths:
      - "D:/Data"
      - "E:/Projects"
    exclude_patterns:
      - "**/.git/**"
      - "**/node_modules/**"
      - "**/__pycache__/**"
    file_types:
      - "*.txt"
      - "*.md"
      - "*.py"
      - "*.js"

duplicates:
  hash_algorithm: "md5"         # 'md5', 'sha1', 'sha256'
  quick_hash_size: 8192         # First/last bytes for quick scan
  min_file_size: 1024           # Skip files < 1KB
  max_file_size: 10737418240    # Skip files > 10GB
  compare_by:
    - "size"
    - "quick_hash"
    - "full_hash"
  cache:
    enabled: true
    max_entries: 100000
    ttl_days: 30
  skip_system_files: true
  skip_hidden_files: false

operations:
  buffer_size: 1048576          # 1MB buffer for copy/move
  verify_after_copy: true       # CRC32 verification
  use_recycle_bin: true         # Safe delete to recycle bin
  overwrite_policy: "ask"       # 'ask', 'skip', 'overwrite', 'rename'
  max_concurrent_operations: 3
  speed_limit_mbps: 0           # 0 = unlimited
  pause_threshold_percent: 95   # Auto-pause if disk > 95%

preview:
  enabled: true
  max_file_size_mb: 50          # Max file size for preview
  thumbnail_size: 256
  cache:
    enabled: true
    max_size_mb: 500
    location: "%TEMP%/SmartSearchPro/previews"
  supported_formats:
    text: [".txt", ".md", ".log", ".json", ".xml", ".csv"]
    image: [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
    video: [".mp4", ".avi", ".mkv", ".mov"]
    audio: [".mp3", ".wav", ".flac", ".m4a"]
    document: [".pdf", ".docx", ".xlsx", ".pptx"]
    archive: [".zip", ".rar", ".7z", ".tar", ".gz"]

export:
  default_format: "csv"
  csv:
    delimiter: ","
    encoding: "utf-8-sig"       # With BOM for Excel
  excel:
    max_rows_per_sheet: 1000000
    include_formatting: true
  html:
    template: "default"
    include_thumbnails: true
    embed_css: true

ui:
  theme: "dark"                 # 'dark' or 'light'
  font_family: "Segoe UI"
  font_size: 10
  show_hidden_files: false
  double_click_action: "open"  # 'open', 'preview', 'explore'
  column_order:
    - "name"
    - "path"
    - "size"
    - "modified"
    - "type"
  window:
    width: 1200
    height: 800
    maximized: false
    position: [100, 100]

system:
  tray:
    enabled: true
    minimize_to_tray: true
    close_to_tray: false
  hotkeys:
    show_window: "Ctrl+Alt+F"
    quick_search: "Ctrl+Alt+S"
  startup:
    run_on_startup: false
    start_minimized: false
  admin:
    auto_elevate: false         # Request admin on startup

plugins:
  enabled: true
  auto_load: true
  plugin_dirs:
    - "%APPDATA%/SmartSearchPro/plugins"
    - "./plugins"
  enabled_plugins:
    - "custom_filter"
    - "cloud_export"
```

### Configuration Class Structure

```python
# core/config.py

from dataclasses import dataclass, field
from typing import Dict, List, Any
from pathlib import Path
import yaml
import json

@dataclass
class SearchConfig:
    engine: str = "everything"
    everything_sdk_path: str = ""
    max_results: int = 10000
    auto_search_delay_ms: int = 300
    case_sensitive: bool = False
    match_whole_word: bool = False
    regex_enabled: bool = True

@dataclass
class DuplicatesConfig:
    hash_algorithm: str = "md5"
    quick_hash_size: int = 8192
    min_file_size: int = 1024
    max_file_size: int = 10 * 1024 * 1024 * 1024
    compare_by: List[str] = field(default_factory=lambda: ["size", "quick_hash", "full_hash"])
    cache_enabled: bool = True
    cache_max_entries: int = 100000
    cache_ttl_days: int = 30

@dataclass
class OperationsConfig:
    buffer_size: int = 1048576
    verify_after_copy: bool = True
    use_recycle_bin: bool = True
    overwrite_policy: str = "ask"
    max_concurrent_operations: int = 3
    speed_limit_mbps: int = 0

@dataclass
class PreviewConfig:
    enabled: bool = True
    max_file_size_mb: int = 50
    thumbnail_size: int = 256
    cache_enabled: bool = True
    cache_max_size_mb: int = 500
    cache_location: str = ""

@dataclass
class UIConfig:
    theme: str = "dark"
    font_family: str = "Segoe UI"
    font_size: int = 10
    show_hidden_files: bool = False
    double_click_action: str = "open"
    column_order: List[str] = field(default_factory=lambda: ["name", "path", "size", "modified", "type"])

@dataclass
class AppConfig:
    name: str = "Smart Search Pro"
    version: str = "2.0.0"
    data_dir: Path = field(default_factory=Path)
    log_level: str = "INFO"

    search: SearchConfig = field(default_factory=SearchConfig)
    duplicates: DuplicatesConfig = field(default_factory=DuplicatesConfig)
    operations: OperationsConfig = field(default_factory=OperationsConfig)
    preview: PreviewConfig = field(default_factory=PreviewConfig)
    ui: UIConfig = field(default_factory=UIConfig)

class ConfigManager:
    """Manages application configuration with layered overrides."""

    def __init__(self, config_path: Path = None):
        self.config_path = config_path or self._default_config_path()
        self.config = self._load_config()

    def _default_config_path(self) -> Path:
        return Path.home() / ".config" / "smart_search" / "config.yaml"

    def _load_config(self) -> AppConfig:
        """Load configuration from YAML file with defaults."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
                return self._dict_to_config(data)
        return AppConfig()

    def save(self):
        """Save current configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(self._config_to_dict(), f, default_flow_style=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation (e.g., 'search.max_results')."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """Set configuration value by dot notation."""
        keys = key.split('.')
        obj = self.config
        for k in keys[:-1]:
            obj = getattr(obj, k)
        setattr(obj, keys[-1], value)
```

---

## Plugin Architecture

### Plugin System Design

```
┌──────────────────────────────────────────────────────────┐
│                    Plugin Manager                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │  Loader    │  │  Registry  │  │  Lifecycle │        │
│  └────────────┘  └────────────┘  └────────────┘        │
└──────────────────────┬───────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
    ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
    │ Filter  │   │ Export  │   │ Preview │
    │ Plugin  │   │ Plugin  │   │ Plugin  │
    └─────────┘   └─────────┘   └─────────┘
```

### Plugin Base Class

```python
# plugins/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class PluginMetadata:
    name: str
    version: str
    author: str
    description: str
    requires: List[str] = None  # Required plugin dependencies
    api_version: str = "2.0"

class PluginBase(ABC):
    """Base class for all plugins."""

    def __init__(self, api: 'PluginAPI'):
        self.api = api
        self.enabled = True

    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize plugin. Return True on success."""
        pass

    @abstractmethod
    def shutdown(self):
        """Cleanup plugin resources."""
        pass

    def configure(self, config: Dict[str, Any]):
        """Configure plugin with settings."""
        pass

class FilterPlugin(PluginBase):
    """Plugin for custom file filters."""

    @abstractmethod
    def filter(self, file_info: Dict[str, Any]) -> bool:
        """Return True if file matches filter criteria."""
        pass

    @abstractmethod
    def get_ui_widget(self) -> Any:
        """Return PyQt6 widget for filter configuration."""
        pass

class ExporterPlugin(PluginBase):
    """Plugin for custom export formats."""

    @abstractmethod
    def export(self, data: List[Dict[str, Any]], output_path: str) -> bool:
        """Export data to custom format. Return True on success."""
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """Return file extension (e.g., '.xml')."""
        pass

    @abstractmethod
    def get_format_name(self) -> str:
        """Return human-readable format name (e.g., 'XML Report')."""
        pass

class PreviewPlugin(PluginBase):
    """Plugin for custom file preview."""

    @abstractmethod
    def can_preview(self, file_path: str) -> bool:
        """Return True if plugin can preview this file."""
        pass

    @abstractmethod
    def generate_preview(self, file_path: str) -> Any:
        """Generate preview widget or data."""
        pass

class SearchProviderPlugin(PluginBase):
    """Plugin for custom search providers."""

    @abstractmethod
    def search(self, query: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform search and return results."""
        pass

    @abstractmethod
    def supports_realtime(self) -> bool:
        """Return True if provider supports real-time search."""
        pass
```

### Plugin API

```python
# plugins/api.py

from typing import Dict, Any, List, Callable
from core.eventbus import EventBus
from core.database import Database
from core.config import ConfigManager

class PluginAPI:
    """API exposed to plugins for interacting with application."""

    def __init__(self, eventbus: EventBus, db: Database, config: ConfigManager):
        self.eventbus = eventbus
        self.db = db
        self.config = config
        self._hooks: Dict[str, List[Callable]] = {}

    # Event System
    def emit_event(self, event_name: str, data: Any = None):
        """Emit an event to the event bus."""
        self.eventbus.emit(event_name, data)

    def subscribe_event(self, event_name: str, callback: Callable):
        """Subscribe to an event."""
        self.eventbus.subscribe(event_name, callback)

    # Database Access
    def query(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        return self.db.query(sql, params)

    def execute(self, sql: str, params: tuple = None) -> int:
        """Execute a statement and return affected rows."""
        return self.db.execute(sql, params)

    # Configuration
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any):
        """Set configuration value."""
        self.config.set(key, value)

    # Hooks System
    def register_hook(self, hook_name: str, callback: Callable):
        """Register a hook callback."""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)

    def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute all callbacks for a hook."""
        results = []
        if hook_name in self._hooks:
            for callback in self._hooks[hook_name]:
                results.append(callback(*args, **kwargs))
        return results

    # UI Integration
    def add_menu_item(self, menu_path: str, label: str, callback: Callable):
        """Add a menu item to the UI."""
        self.emit_event('ui.add_menu_item', {
            'menu_path': menu_path,
            'label': label,
            'callback': callback
        })

    def add_toolbar_button(self, label: str, icon: str, callback: Callable):
        """Add a toolbar button."""
        self.emit_event('ui.add_toolbar_button', {
            'label': label,
            'icon': icon,
            'callback': callback
        })

    def show_notification(self, title: str, message: str, level: str = 'info'):
        """Show a notification to the user."""
        self.emit_event('ui.notification', {
            'title': title,
            'message': message,
            'level': level
        })

    # File Operations
    def add_context_menu_action(self, label: str, callback: Callable):
        """Add an action to file context menu."""
        self.emit_event('context_menu.add_action', {
            'label': label,
            'callback': callback
        })
```

### Plugin Manager

```python
# plugins/manager.py

from pathlib import Path
from typing import Dict, List, Type
import importlib.util
import sys

class PluginManager:
    """Manages plugin lifecycle and registration."""

    def __init__(self, api: PluginAPI, plugin_dirs: List[Path]):
        self.api = api
        self.plugin_dirs = plugin_dirs
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_classes: Dict[str, Type[PluginBase]] = {}

    def discover_plugins(self) -> List[str]:
        """Discover all available plugins."""
        discovered = []

        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue

            for plugin_file in plugin_dir.glob("*.py"):
                if plugin_file.stem.startswith("_"):
                    continue

                try:
                    module_name = f"plugins.{plugin_file.stem}"
                    spec = importlib.util.spec_from_file_location(module_name, plugin_file)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)

                    # Find plugin class
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and
                            issubclass(attr, PluginBase) and
                            attr != PluginBase):
                            self.plugin_classes[plugin_file.stem] = attr
                            discovered.append(plugin_file.stem)
                            break

                except Exception as e:
                    print(f"Error loading plugin {plugin_file.stem}: {e}")

        return discovered

    def load_plugin(self, plugin_name: str) -> bool:
        """Load and initialize a plugin."""
        if plugin_name in self.plugins:
            return True  # Already loaded

        if plugin_name not in self.plugin_classes:
            return False  # Not found

        try:
            plugin_class = self.plugin_classes[plugin_name]
            plugin = plugin_class(self.api)

            if plugin.initialize():
                self.plugins[plugin_name] = plugin
                self.api.emit_event('plugin.loaded', {
                    'name': plugin_name,
                    'metadata': plugin.metadata()
                })
                return True

        except Exception as e:
            print(f"Error initializing plugin {plugin_name}: {e}")

        return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin."""
        if plugin_name not in self.plugins:
            return False

        try:
            plugin = self.plugins[plugin_name]
            plugin.shutdown()
            del self.plugins[plugin_name]

            self.api.emit_event('plugin.unloaded', {'name': plugin_name})
            return True

        except Exception as e:
            print(f"Error unloading plugin {plugin_name}: {e}")
            return False

    def get_plugins_by_type(self, plugin_type: Type[PluginBase]) -> List[PluginBase]:
        """Get all loaded plugins of a specific type."""
        return [p for p in self.plugins.values() if isinstance(p, plugin_type)]

    def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a plugin."""
        if self.unload_plugin(plugin_name):
            return self.load_plugin(plugin_name)
        return False
```

### Example Plugin

```python
# plugins/examples/custom_filter.py

from plugins.base import FilterPlugin, PluginMetadata
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel

class VideoSizeFilterPlugin(FilterPlugin):
    """Example: Filter video files by resolution."""

    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Video Size Filter",
            version="1.0.0",
            author="Smart Search Pro",
            description="Filter video files by resolution (e.g., 1920x1080)"
        )

    def initialize(self) -> bool:
        self.min_width = 0
        self.min_height = 0
        return True

    def shutdown(self):
        pass

    def configure(self, config: dict):
        self.min_width = config.get('min_width', 0)
        self.min_height = config.get('min_height', 0)

    def filter(self, file_info: dict) -> bool:
        """Return True if video meets resolution requirements."""
        if not file_info.get('is_video'):
            return True

        width = file_info.get('video_width', 0)
        height = file_info.get('video_height', 0)

        return width >= self.min_width and height >= self.min_height

    def get_ui_widget(self) -> QWidget:
        """Return configuration widget."""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Minimum Width:"))
        width_input = QLineEdit(str(self.min_width))
        layout.addWidget(width_input)

        layout.addWidget(QLabel("Minimum Height:"))
        height_input = QLineEdit(str(self.min_height))
        layout.addWidget(height_input)

        widget.setLayout(layout)
        return widget
```

---

## Class Diagrams

### Core Layer

```
┌─────────────────────────────────────────────────────────┐
│                    Core Layer                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐         ┌──────────────┐            │
│  │  Database    │         │ ConfigManager│            │
│  ├──────────────┤         ├──────────────┤            │
│  │ -connection  │         │ -config_path │            │
│  │ -pool        │         │ -config      │            │
│  ├──────────────┤         ├──────────────┤            │
│  │ +query()     │         │ +get()       │            │
│  │ +execute()   │         │ +set()       │            │
│  │ +transaction│         │ +save()      │            │
│  └──────────────┘         └──────────────┘            │
│                                                         │
│  ┌──────────────┐         ┌──────────────┐            │
│  │  EventBus    │         │  Cache       │            │
│  ├──────────────┤         ├──────────────┤            │
│  │ -subscribers │         │ -lru_cache   │            │
│  │ -queue       │         │ -disk_cache  │            │
│  ├──────────────┤         ├──────────────┤            │
│  │ +emit()      │         │ +get()       │            │
│  │ +subscribe() │         │ +set()       │            │
│  │ +unsubscribe│         │ +invalidate()│            │
│  └──────────────┘         └──────────────┘            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Search Module

```
┌─────────────────────────────────────────────────────────┐
│                   Search Module                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────────────────────────────────────┐     │
│  │            SearchEngine                       │     │
│  ├───────────────────────────────────────────────┤     │
│  │ -provider: SearchProvider                     │     │
│  │ -filters: List[Filter]                        │     │
│  │ -history: SearchHistory                       │     │
│  ├───────────────────────────────────────────────┤     │
│  │ +search(query, filters) -> Results            │     │
│  │ +search_async(query, callback)                │     │
│  │ +cancel_search()                              │     │
│  └───────────────────────────────────────────────┘     │
│               △                                          │
│               │ uses                                     │
│               │                                          │
│  ┌────────────┴──────────┐  ┌──────────────────┐      │
│  │  EverythingProvider   │  │  BuiltinProvider │      │
│  ├───────────────────────┤  ├──────────────────┤      │
│  │ -dll_handle           │  │ -indexer         │      │
│  ├───────────────────────┤  ├──────────────────┤      │
│  │ +search()             │  │ +search()        │      │
│  │ +is_available()       │  │ +build_index()   │      │
│  └───────────────────────┘  └──────────────────┘      │
│                                                         │
│  ┌──────────────┐         ┌──────────────┐            │
│  │ QueryParser  │         │ FilterEngine │            │
│  ├──────────────┤         ├──────────────┤            │
│  │ +parse()     │         │ +apply()     │            │
│  │ +tokenize()  │         │ +combine()   │            │
│  └──────────────┘         └──────────────┘            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Duplicates Module

```
┌─────────────────────────────────────────────────────────┐
│                 Duplicates Module                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────────────────────────────────────┐     │
│  │          DuplicateScanner                     │     │
│  ├───────────────────────────────────────────────┤     │
│  │ -hasher: FileHasher                           │     │
│  │ -comparator: FileComparator                   │     │
│  │ -grouper: DuplicateGrouper                    │     │
│  │ -cache: HashCache                             │     │
│  ├───────────────────────────────────────────────┤     │
│  │ +scan(paths, strategy) -> Groups              │     │
│  │ +scan_async(paths, progress_callback)         │     │
│  │ +cancel_scan()                                │     │
│  └───────────────────────────────────────────────┘     │
│                                                         │
│  ┌──────────────┐    ┌─────────────────┐              │
│  │  FileHasher  │    │ HashCache       │              │
│  ├──────────────┤    ├─────────────────┤              │
│  │ -algorithm   │    │ -db: Database   │              │
│  │ -buffer_size │    │ -memory_cache   │              │
│  ├──────────────┤    ├─────────────────┤              │
│  │ +quick_hash()│    │ +get_hash()     │              │
│  │ +full_hash() │    │ +store_hash()   │              │
│  │ +hash_async()│    │ +invalidate()   │              │
│  └──────────────┘    └─────────────────┘              │
│                                                         │
│  ┌──────────────────┐     ┌────────────────────┐      │
│  │ FileComparator   │     │ DuplicateGrouper   │      │
│  ├──────────────────┤     ├────────────────────┤      │
│  │ +compare_by_size │     │ +group_by_hash()   │      │
│  │ +compare_by_name │     │ +group_by_criteria│      │
│  │ +compare_by_hash │     │ +merge_groups()    │      │
│  └──────────────────┘     └────────────────────┘      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Operations Module

```
┌─────────────────────────────────────────────────────────┐
│                 Operations Module                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────────────────────────────────────┐     │
│  │        OperationsManager                      │     │
│  ├───────────────────────────────────────────────┤     │
│  │ -queue: OperationQueue                        │     │
│  │ -workers: ThreadPoolExecutor                  │     │
│  │ -operations: Dict[str, Operation]             │     │
│  ├───────────────────────────────────────────────┤     │
│  │ +add_operation(op) -> str (operation_id)      │     │
│  │ +cancel_operation(operation_id)               │     │
│  │ +pause_operation(operation_id)                │     │
│  │ +resume_operation(operation_id)               │     │
│  │ +get_status(operation_id) -> Status           │     │
│  └───────────────────────────────────────────────┘     │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ CopyOperation│  │ MoveOperation│  │DeleteOp     │  │
│  ├──────────────┤  ├──────────────┤  ├─────────────┤  │
│  │ -source      │  │ -source      │  │ -targets    │  │
│  │ -destination │  │ -destination │  │ -use_bin    │  │
│  │ -verify      │  │ -verify      │  ├─────────────┤  │
│  ├──────────────┤  ├──────────────┤  │ +execute()  │  │
│  │ +execute()   │  │ +execute()   │  │ +rollback() │  │
│  │ +rollback()  │  │ +rollback()  │  └─────────────┘  │
│  │ +verify()    │  │ +verify()    │                    │
│  └──────────────┘  └──────────────┘                    │
│                                                         │
│  ┌─────────────────┐       ┌──────────────────┐       │
│  │ BufferManager   │       │ CRC32Verifier    │       │
│  ├─────────────────┤       ├──────────────────┤       │
│  │ -buffer_size    │       │ +calculate_crc() │       │
│  │ -buffers        │       │ +verify_file()   │       │
│  ├─────────────────┤       └──────────────────┘       │
│  │ +allocate()     │                                    │
│  │ +release()      │                                    │
│  └─────────────────┘                                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### UI Layer

```
┌─────────────────────────────────────────────────────────┐
│                      UI Layer                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────────────────────────────────────┐     │
│  │            MainWindow                         │     │
│  ├───────────────────────────────────────────────┤     │
│  │ -search_view: SearchView                      │     │
│  │ -duplicates_view: DuplicatesView              │     │
│  │ -operations_view: OperationsView              │     │
│  │ -preview_panel: PreviewPanel                  │     │
│  │ -controller: AppController                    │     │
│  ├───────────────────────────────────────────────┤     │
│  │ +show_search_view()                           │     │
│  │ +show_duplicates_view()                       │     │
│  │ +show_settings()                              │     │
│  └───────────────────────────────────────────────┘     │
│                                                         │
│  ┌───────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  SearchView   │  │DuplicatesView│  │OperationsV │  │
│  ├───────────────┤  ├──────────────┤  ├────────────┤  │
│  │ -search_bar   │  │ -scanner     │  │ -queue     │  │
│  │ -filter_panel │  │ -groups_list │  │ -progress  │  │
│  │ -results_list │  │ -actions     │  ├────────────┤  │
│  ├───────────────┤  ├──────────────┤  │ +add_op()  │  │
│  │ +search()     │  │ +scan()      │  │ +pause()   │  │
│  │ +apply_filter│  │ +select_keep │  │ +cancel()  │  │
│  └───────────────┘  └──────────────┘  └────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────┐       │
│  │          Custom Widgets                     │       │
│  ├─────────────────────────────────────────────┤       │
│  │ - SmartSearchBar (autocomplete)             │       │
│  │ - FileListWidget (virtual scrolling)        │       │
│  │ - FilterPanelWidget (dynamic filters)       │       │
│  │ - EnhancedProgressBar (speed, ETA)          │       │
│  │ - ToastNotification (non-blocking alerts)   │       │
│  └─────────────────────────────────────────────┘       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Search Flow

```
User Input
    │
    ▼
┌───────────────┐
│  Search Bar   │
└───────┬───────┘
        │ query
        ▼
┌───────────────┐
│ QueryParser   │ ─────→ parse query, extract filters
└───────┬───────┘
        │ parsed_query
        ▼
┌───────────────┐
│ SearchEngine  │
└───────┬───────┘
        │
        ├─→ [Cache Check] ─→ if cached, return
        │
        ├─→ [Everything SDK] ─→ execute search
        │
        ├─→ [Filter Engine] ─→ apply additional filters
        │
        └─→ [History] ─→ save to search_history
        │
        ▼
┌───────────────┐
│  Results      │
└───────┬───────┘
        │
        ├─→ [UI Update] ─→ display in FileListWidget
        │
        └─→ [EventBus] ─→ emit 'search.completed'
```

### Duplicate Scan Flow

```
User Selects Paths
    │
    ▼
┌───────────────┐
│DuplicateScanner│
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Pass 1: Size  │ ─────→ group files by size
└───────┬───────┘       (skip unique sizes)
        │
        ▼
┌───────────────┐
│Pass 2: Quick  │ ─────→ hash first 8KB + last 8KB
│     Hash      │       (check cache first)
└───────┬───────┘
        │
        ▼
┌───────────────┐
│Pass 3: Full   │ ─────→ hash entire file
│     Hash      │       (only if quick hashes match)
└───────┬───────┘
        │
        ▼
┌───────────────┐
│  Grouper      │ ─────→ create duplicate groups
└───────┬───────┘
        │
        ├─→ [HashCache] ─→ save new hashes
        │
        ├─→ [Database] ─→ save groups
        │
        └─→ [EventBus] ─→ emit 'scan.completed'
        │
        ▼
┌───────────────┐
│Display Groups │
└───────────────┘
```

### File Copy Flow

```
User Initiates Copy
    │
    ▼
┌───────────────┐
│CopyOperation  │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   Validate    │ ─────→ check space, permissions
└───────┬───────┘
        │
        ▼
┌───────────────┐
│OperationQueue │ ─────→ add to queue with priority
└───────┬───────┘
        │
        ▼
┌───────────────┐
│WorkerThread   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│  Copy Loop    │
└───────┬───────┘
        │
        ├─→ [BufferManager] ─→ allocate buffer
        │
        ├─→ [Read/Write] ─→ copy in chunks
        │
        ├─→ [Progress] ─→ emit progress events
        │
        ├─→ [Speed Limit] ─→ throttle if needed
        │
        └─→ [Error Handler] ─→ retry/skip/abort
        │
        ▼
┌───────────────┐
│  Verify       │ ─────→ CRC32 check (optional)
└───────┬───────┘
        │
        ├─→ [Database] ─→ save to operation_history
        │
        └─→ [EventBus] ─→ emit 'operation.completed'
        │
        ▼
┌───────────────┐
│   Complete    │
└───────────────┘
```

### Preview Generation Flow

```
User Selects File
    │
    ▼
┌───────────────┐
│PreviewManager │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Cache Check   │ ─────→ check preview_cache table
└───────┬───────┘
        │
        ├─→ if cached & valid ─→ load from cache
        │
        └─→ if not cached ─────┐
                                │
                                ▼
                        ┌───────────────┐
                        │Detect FileType│
                        └───────┬───────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │  Image   │    │   Text   │    │  Video   │
        │ Preview  │    │ Preview  │    │ Preview  │
        └────┬─────┘    └────┬─────┘    └────┬─────┘
             │               │               │
             │ generate      │ read          │ extract frame
             │ thumbnail     │ first 1000    │ & metadata
             │               │ lines         │
             └───────────────┴───────────────┘
                             │
                             ▼
                     ┌───────────────┐
                     │  Save Cache   │ ─→ save to preview_cache
                     └───────┬───────┘
                             │
                             ▼
                     ┌───────────────┐
                     │Display Preview│
                     └───────────────┘
```

---

## API Contracts

### Search API

```python
class SearchEngine:
    """Main search engine interface."""

    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        max_results: int = 10000
    ) -> SearchResults:
        """
        Synchronous search.

        Args:
            query: Search query string
            filters: Optional filters (size, date, type, etc.)
            max_results: Maximum number of results

        Returns:
            SearchResults object with files and metadata

        Raises:
            SearchError: If search fails
        """
        pass

    async def search_async(
        self,
        query: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> SearchResults:
        """
        Asynchronous search with progress updates.

        Args:
            query: Search query string
            progress_callback: Called with (current, total)

        Returns:
            SearchResults object
        """
        pass

    def cancel_search(self):
        """Cancel ongoing search operation."""
        pass

@dataclass
class SearchResults:
    """Search results container."""
    files: List[FileInfo]
    total_count: int
    execution_time_ms: int
    query: str
    filters: Dict[str, Any]

@dataclass
class FileInfo:
    """File information."""
    path: Path
    name: str
    size: int
    modified: datetime
    created: datetime
    extension: str
    is_directory: bool
    attributes: int
```

### Duplicates API

```python
class DuplicateScanner:
    """Duplicate file scanner interface."""

    def scan(
        self,
        paths: List[Path],
        strategy: str = "full",  # 'quick', 'full', 'content'
        min_size: int = 0,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[DuplicateGroup]:
        """
        Scan for duplicate files.

        Args:
            paths: Directories to scan
            strategy: Detection strategy
            min_size: Minimum file size to consider
            progress_callback: Progress updates

        Returns:
            List of duplicate groups

        Raises:
            ScanError: If scan fails
        """
        pass

    def cancel_scan(self):
        """Cancel ongoing scan."""
        pass

@dataclass
class DuplicateGroup:
    """Group of duplicate files."""
    files: List[FileInfo]
    total_size: int
    hash: str
    hash_type: str
    confidence: float  # 0.0 - 1.0

    def get_wasted_space(self) -> int:
        """Calculate wasted space (total_size - largest_file)."""
        return self.total_size - max(f.size for f in self.files)

    def suggest_keep(self) -> FileInfo:
        """Suggest which file to keep based on heuristics."""
        # Prefer: shortest path > oldest file > first alphabetically
        pass
```

### Operations API

```python
class OperationsManager:
    """File operations manager interface."""

    def copy(
        self,
        sources: List[Path],
        destination: Path,
        overwrite_policy: str = "ask",  # 'ask', 'skip', 'overwrite', 'rename'
        verify: bool = True,
        progress_callback: Optional[Callable[[OperationProgress], None]] = None
    ) -> str:
        """
        Copy files/folders.

        Args:
            sources: Source files/folders
            destination: Destination folder
            overwrite_policy: How to handle existing files
            verify: Verify copied files with CRC32
            progress_callback: Progress updates

        Returns:
            operation_id for tracking

        Raises:
            OperationError: If operation fails
        """
        pass

    def move(
        self,
        sources: List[Path],
        destination: Path
    ) -> str:
        """Move files/folders."""
        pass

    def delete(
        self,
        targets: List[Path],
        use_recycle_bin: bool = True
    ) -> str:
        """Delete files/folders."""
        pass

    def get_status(self, operation_id: str) -> OperationStatus:
        """Get operation status."""
        pass

    def pause(self, operation_id: str):
        """Pause operation."""
        pass

    def resume(self, operation_id: str):
        """Resume paused operation."""
        pass

    def cancel(self, operation_id: str):
        """Cancel operation."""
        pass

@dataclass
class OperationProgress:
    """Operation progress information."""
    operation_id: str
    operation_type: str
    current_file: Path
    files_processed: int
    files_total: int
    bytes_processed: int
    bytes_total: int
    speed_mbps: float
    eta_seconds: int
    status: str  # 'running', 'paused', 'completed', 'failed'
    error_message: Optional[str] = None
```

### Export API

```python
class Exporter:
    """Export results to various formats."""

    def export_to_csv(
        self,
        data: List[FileInfo],
        output_path: Path,
        columns: Optional[List[str]] = None
    ) -> bool:
        """Export to CSV."""
        pass

    def export_to_excel(
        self,
        data: List[FileInfo],
        output_path: Path,
        include_formatting: bool = True
    ) -> bool:
        """Export to Excel with formatting."""
        pass

    def export_to_html(
        self,
        data: List[FileInfo],
        output_path: Path,
        template: str = "default",
        include_thumbnails: bool = False
    ) -> bool:
        """Export to HTML report."""
        pass

    def export_to_json(
        self,
        data: List[FileInfo],
        output_path: Path,
        indent: int = 2
    ) -> bool:
        """Export to JSON."""
        pass
```

---

## Technology Stack

### Core Technologies

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Language** | Python 3.11+ | Fast development, rich ecosystem, async support |
| **UI Framework** | PyQt6 | Native performance, rich widgets, cross-platform |
| **Database** | SQLite 3.x | Zero-config, ACID, excellent for local apps |
| **Search Backend** | Everything SDK | Instant NTFS search, 500MB/s throughput |
| **Async** | asyncio + aiofiles | Non-blocking I/O for responsiveness |
| **Concurrency** | ThreadPoolExecutor | CPU-bound tasks (hashing, copying) |
| **Configuration** | PyYAML | Human-readable, supports comments |
| **Logging** | structlog | Structured logging for debugging |

### Key Dependencies

```txt
# Core
PyQt6>=6.6.0
PyQt6-WebEngine>=6.6.0

# Database
aiosqlite>=0.19.0

# Hashing & Verification
xxhash>=3.4.0
crcmod>=1.7

# File Operations
aiofiles>=23.2.0
send2trash>=1.8.2

# Everything SDK
pywin32>=306
cffi>=1.16.0

# Export
openpyxl>=3.1.0
jinja2>=3.1.0

# Configuration
pyyaml>=6.0
pydantic>=2.5.0

# Logging
structlog>=23.2.0
colorama>=0.4.6

# Utilities
python-magic-bin>=0.4.14
humanize>=4.9.0
watchdog>=3.0.0

# Preview
pillow>=10.1.0
pypdf>=3.17.0
python-docx>=1.1.0

# Dev/Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-qt>=4.2.0
black>=23.12.0
ruff>=0.1.0
```

### System Requirements

- **OS**: Windows 10/11 (64-bit)
- **Python**: 3.11 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 100MB for application, variable for cache
- **Dependencies**: Everything 1.4+ installed (for Everything SDK)

---

## Scaling Considerations

### Performance Optimization

#### 1. Search Performance

```python
# Problem: Slow initial load with 1M+ files
# Solution: Virtual scrolling + lazy loading

class FileListWidget(QListWidget):
    """Virtual scrolling for large result sets."""

    def __init__(self):
        super().__init__()
        self.visible_range = (0, 100)
        self.total_items = 0
        self.item_height = 24

    def load_visible_items(self):
        """Only load items visible in viewport."""
        start, end = self.visible_range
        # Load only items[start:end] from database
```

**Bottleneck**: Loading 10,000+ results into UI
**Solution**: Virtual scrolling, load 100 at a time
**Improvement**: 50ms initial load vs 2000ms full load

#### 2. Hash Caching

```python
# Problem: Re-hashing same files on each scan
# Solution: Multi-level cache with invalidation

class HashCache:
    """Two-level hash cache."""

    def __init__(self):
        self.memory_cache = LRUCache(maxsize=10000)  # Hot cache
        self.db_cache = Database()                    # Persistent cache

    def get_hash(self, file_path: Path, file_size: int, modified_time: int):
        # Check memory cache
        key = (file_path, file_size, modified_time)
        if key in self.memory_cache:
            return self.memory_cache[key]

        # Check database cache
        hash_value = self.db_cache.query(
            "SELECT full_hash FROM hash_cache "
            "WHERE file_path = ? AND file_size = ? AND modified_time = ?",
            (str(file_path), file_size, modified_time)
        )

        if hash_value:
            self.memory_cache[key] = hash_value
            return hash_value

        return None
```

**Bottleneck**: Hashing 10GB file takes 15+ seconds
**Solution**: Cache hash with file metadata (size + mtime)
**Improvement**: 15s -> 0.1ms on cache hit (150,000x faster)

#### 3. Parallel Hashing

```python
# Problem: Sequential hashing is slow
# Solution: Thread pool for parallel hashing

from concurrent.futures import ThreadPoolExecutor
import os

def hash_files_parallel(files: List[Path], max_workers: int = None):
    """Hash multiple files in parallel."""
    if max_workers is None:
        max_workers = os.cpu_count()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(hash_file, f): f for f in files}

        for future in as_completed(futures):
            file_path = futures[future]
            try:
                hash_value = future.result()
                yield file_path, hash_value
            except Exception as e:
                print(f"Error hashing {file_path}: {e}")
```

**Bottleneck**: Hashing 1000 files sequentially takes 500s
**Solution**: Parallel hashing with 8 threads
**Improvement**: 500s -> 70s (7x faster on 8-core CPU)

#### 4. Database Indexing

```sql
-- Problem: Slow queries on large tables
-- Solution: Strategic indexing

-- Query: Find all hashes for duplicate detection
-- Without index: 5000ms for 100K rows
-- With index: 50ms
CREATE INDEX idx_full_hash ON hash_cache(full_hash);

-- Query: Lookup hash by file path
-- Without index: 3000ms
-- With index: 1ms
CREATE INDEX idx_file_path ON hash_cache(file_path);

-- Composite index for common query pattern
CREATE INDEX idx_file_metadata
ON hash_cache(file_path, file_size, modified_time);
```

**Bottleneck**: Search history queries slow with 100K+ records
**Solution**: Indexes on `query`, `created_at`
**Improvement**: 500ms -> 5ms (100x faster)

#### 5. Buffer Management

```python
# Problem: Too many small I/O operations
# Solution: Large buffers with async I/O

import aiofiles

async def copy_file_async(source: Path, dest: Path, buffer_size: int = 1024*1024):
    """Copy file with optimal buffer size."""
    async with aiofiles.open(source, 'rb') as src:
        async with aiofiles.open(dest, 'wb') as dst:
            while chunk := await src.read(buffer_size):
                await dst.write(chunk)
```

**Bottleneck**: Copying with 4KB buffer = 50MB/s
**Solution**: 1MB buffer + async I/O
**Improvement**: 50MB/s -> 400MB/s (8x faster)

### Horizontal Scaling Opportunities

While Smart Search Pro is a desktop application, some operations can be distributed:

#### 1. Cloud Sync for Hash Cache

```python
# Allow multiple machines to share hash cache
# via Supabase or cloud storage

class CloudHashCache:
    def sync_to_cloud(self):
        """Upload local cache to cloud."""
        local_hashes = self.db.query("SELECT * FROM hash_cache WHERE synced = 0")
        # Upload to Supabase

    def sync_from_cloud(self):
        """Download hashes from cloud."""
        # Download from Supabase
        # Merge with local cache
```

#### 2. Distributed Scanning

```python
# For network drives, distribute scan across multiple machines

class DistributedScanner:
    def scan_network_drive(self, drive_path: Path):
        """Distribute scan across available workers."""
        # Divide folders among workers
        # Each worker scans its subset
        # Aggregate results
```

### Memory Management

```python
# Problem: Loading 1M file results uses 2GB RAM
# Solution: Pagination + generator pattern

def search_generator(query: str, page_size: int = 1000):
    """Yield search results in batches."""
    offset = 0
    while True:
        results = search_engine.search(
            query,
            limit=page_size,
            offset=offset
        )
        if not results:
            break

        yield results
        offset += page_size

# Usage
for batch in search_generator("*.mp4"):
    process_batch(batch)  # Process 1000 at a time
```

**Bottleneck**: 1M results = 2GB RAM
**Solution**: Generator with 1000-item batches
**Improvement**: 2GB -> 10MB memory usage

### Caching Strategy

```
┌─────────────────────────────────────────┐
│         Cache Hierarchy                 │
├─────────────────────────────────────────┤
│                                         │
│  Level 1: Memory (LRU)                  │
│  - 10,000 hot items                     │
│  - O(1) access                          │
│  - Evict after 1 hour idle              │
│                                         │
│  Level 2: SQLite                        │
│  - 100,000 items                        │
│  - Indexed queries < 5ms                │
│  - Evict after 30 days                  │
│                                         │
│  Level 3: Disk Cache (thumbnails)       │
│  - 500MB max size                       │
│  - Evict LRU when full                  │
│                                         │
└─────────────────────────────────────────┘
```

---

## Security Considerations

### 1. File Access Permissions

```python
def safe_file_access(file_path: Path, mode: str = 'r'):
    """Safely access files with permission checking."""
    try:
        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check read permission
        if mode == 'r' and not os.access(file_path, os.R_OK):
            raise PermissionError(f"No read permission: {file_path}")

        # Check write permission
        if mode in ('w', 'a') and not os.access(file_path, os.W_OK):
            raise PermissionError(f"No write permission: {file_path}")

        return open(file_path, mode)

    except Exception as e:
        log.error("File access error", path=file_path, error=str(e))
        raise
```

### 2. Path Traversal Prevention

```python
def validate_path(base_dir: Path, target_path: Path) -> Path:
    """Prevent path traversal attacks."""
    # Resolve to absolute path
    absolute_path = target_path.resolve()
    base_absolute = base_dir.resolve()

    # Ensure target is within base directory
    if not str(absolute_path).startswith(str(base_absolute)):
        raise ValueError(f"Path traversal detected: {target_path}")

    return absolute_path
```

### 3. SQL Injection Prevention

```python
# ALWAYS use parameterized queries
def get_search_history(query: str):
    # BAD - SQL injection vulnerable
    # sql = f"SELECT * FROM search_history WHERE query = '{query}'"

    # GOOD - parameterized
    sql = "SELECT * FROM search_history WHERE query = ?"
    return db.query(sql, (query,))
```

### 4. UAC Elevation

```python
import ctypes

def is_admin() -> bool:
    """Check if running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_admin():
    """Request UAC elevation."""
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            " ".join(sys.argv),
            None,
            1  # SW_SHOWNORMAL
        )
        sys.exit()
```

---

## Error Handling

### Exception Hierarchy

```python
class SmartSearchError(Exception):
    """Base exception for Smart Search Pro."""
    pass

class SearchError(SmartSearchError):
    """Search-related errors."""
    pass

class ScanError(SmartSearchError):
    """Duplicate scan errors."""
    pass

class OperationError(SmartSearchError):
    """File operation errors."""
    pass

class ConfigError(SmartSearchError):
    """Configuration errors."""
    pass

class PluginError(SmartSearchError):
    """Plugin-related errors."""
    pass
```

### Error Recovery

```python
class RetryPolicy:
    """Automatic retry with exponential backoff."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def execute(self, func, *args, **kwargs):
        """Execute function with retry policy."""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise

                delay = self.base_delay * (2 ** attempt)
                log.warning(
                    "Retry attempt",
                    attempt=attempt + 1,
                    delay=delay,
                    error=str(e)
                )
                await asyncio.sleep(delay)
```

---

## Testing Strategy

### Unit Tests

```python
# tests/search/test_query_parser.py

import pytest
from search.query_parser import QueryParser

def test_simple_query():
    parser = QueryParser()
    result = parser.parse("*.txt")
    assert result.pattern == "*.txt"
    assert result.type == "wildcard"

def test_size_filter():
    parser = QueryParser()
    result = parser.parse("size:>1mb")
    assert result.filters['size_min'] == 1048576

def test_date_filter():
    parser = QueryParser()
    result = parser.parse("modified:today")
    assert 'modified_after' in result.filters
```

### Integration Tests

```python
# tests/integration/test_search_flow.py

import pytest
from search.engine import SearchEngine
from core.database import Database

@pytest.fixture
def search_engine(tmp_path):
    db = Database(tmp_path / "test.db")
    return SearchEngine(db)

def test_search_and_save_history(search_engine):
    results = search_engine.search("*.py")
    assert len(results.files) > 0

    # Check history saved
    history = search_engine.get_history()
    assert len(history) == 1
    assert history[0].query == "*.py"
```

### Performance Tests

```python
# tests/performance/test_hash_speed.py

import pytest
from duplicates.hasher import FileHasher
from pathlib import Path

def test_hash_performance(tmp_path, benchmark):
    # Create 100MB test file
    test_file = tmp_path / "test.dat"
    test_file.write_bytes(b'0' * 100 * 1024 * 1024)

    hasher = FileHasher()

    # Benchmark hashing
    result = benchmark(hasher.full_hash, test_file)

    assert result is not None
    assert benchmark.stats['mean'] < 1.0  # Less than 1s
```

---

## Deployment

### Build Process

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run tests
pytest tests/

# 3. Build executable with PyInstaller
pyinstaller --name "SmartSearchPro" \
            --windowed \
            --onefile \
            --icon resources/icons/app.ico \
            --add-data "resources;resources" \
            --add-data "plugins;plugins" \
            main.py

# 4. Create installer with Inno Setup
iscc installer.iss
```

### Installation

```
Smart Search Pro Setup
├── Everything SDK check
├── Install to Program Files
├── Create Start Menu shortcuts
├── Register file associations (optional)
├── Add to Windows startup (optional)
└── Create desktop shortcut
```

---

## Future Enhancements

### Phase 2 Features

1. **Cloud Integration**
   - OneDrive, Google Drive, Dropbox search
   - Cloud hash cache synchronization

2. **Advanced Filters**
   - Content search (full-text indexing)
   - Image similarity search (perceptual hashing)
   - Video duration, resolution filters

3. **Automation**
   - Scheduled scans
   - Auto-cleanup rules
   - File organization rules

4. **Collaboration**
   - Share search queries
   - Export reports with links
   - Team duplicate cleanup

5. **AI Features**
   - Smart categorization
   - Duplicate confidence scoring
   - File organization suggestions

---

## Conclusion

Smart Search Pro is designed as a high-performance, extensible file management application with the following strengths:

**Performance**:
- Everything SDK integration for instant search
- Multi-pass hashing with aggressive caching
- Parallel operations with worker pools
- Virtual scrolling for large result sets

**Scalability**:
- Handles millions of files
- Efficient database indexing
- Memory-conscious design
- Plugin architecture for extensions

**User Experience**:
- Modern PyQt6 interface
- Real-time search feedback
- Non-blocking operations
- Toast notifications

**Reliability**:
- ACID database transactions
- Automatic retry policies
- Comprehensive error handling
- CRC32 verification

The modular architecture allows independent development and testing of components while maintaining loose coupling through the EventBus. The plugin system enables third-party extensions without modifying core code.

This architecture balances performance, maintainability, and extensibility for a production-ready application.

---

**Document Version**: 2.0.0
**Last Updated**: 2025-12-12
**Status**: Ready for Implementation
