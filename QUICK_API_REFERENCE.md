# Smart Search Pro - Quick API Reference

Quick reference for core and system modules with corrected API usage.

---

## Core Modules

### Database (core.database)

```python
from core.database import Database

# Create database connection
db = Database("smart_search.db")

# Execute SQL
db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
db.execute("INSERT INTO test (value) VALUES (?)", ("test",))

# Fetch results (Note: fetchall, not fetch_all)
rows = db.fetchall("SELECT * FROM test")
row = db.fetchone("SELECT * FROM test WHERE id = ?", (1,))

# CRUD operations
db.insert("test", {"value": "test"})
db.update("test", {"value": "updated"}, "id = ?", (1,))
db.delete("test", "id = ?", (1,))

# Connection stats
stats = db.get_stats()

# Cleanup
db.close()
```

### Cache (core.cache)

```python
from core.cache import LRUCache, CacheManager

# Simple LRU cache
cache = LRUCache(max_size=1000)
cache.set("key", "value", ttl=3600)
value = cache.get("key")

# Cache statistics
stats = cache.stats
print(f"Hit rate: {stats.hit_rate:.2%}")

# Clear cache
cache.clear()

# Cache manager (multi-tier)
manager = CacheManager()
manager.set_cache_config("search_results", max_size=500, ttl=1800)
```

### Config (core.config)

```python
from core.config import Config

# Load default config
config = Config()

# Validate configuration
config.validate()

# Access nested settings
db_path = config.database.path
cache_size = config.cache.max_size
theme = config.ui.theme

# Convert to dict
config_dict = config.to_dict()

# Load from dict
config = Config.from_dict(config_dict)

# Save to YAML
import yaml
from pathlib import Path

Path("config.yaml").write_text(yaml.dump(config.to_dict()))
```

### Security (core.security)

```python
from core.security import (
    sanitize_sql_input,
    validate_table_name,
    sanitize_cli_argument,
    PROTECTED_PATHS,
    ALLOWED_TABLES
)

# Sanitize SQL input
safe_input = sanitize_sql_input("user'input", max_length=1000)

# Validate table name (whitelist)
if validate_table_name("search_history"):
    # Safe to use
    pass

# Sanitize CLI arguments
safe_arg = sanitize_cli_argument("user input")

# Check protected paths
if any(path.startswith(p) for p in PROTECTED_PATHS):
    print("Protected system path")

# Allowed database tables
print(f"Allowed tables: {ALLOWED_TABLES}")
```

### Logger (core.logger)

```python
from core.logger import get_logger, setup_logging

# Setup logging system
setup_logging(
    level="INFO",
    log_file="app.log",
    console=True,
    json_format=False
)

# Get logger instance
logger = get_logger(__name__)

# Log messages
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")

# Structured logging
logger.info("User action", extra={
    "user_id": 123,
    "action": "search",
    "query": "test"
})
```

### Event Bus (core.eventbus)

```python
from core.eventbus import EventBus, Event

# Get event bus instance
bus = EventBus()

# Subscribe to events
def on_search(event: Event):
    print(f"Search: {event.data}")

bus.subscribe("search.started", on_search)

# Publish events
bus.publish(Event(
    name="search.started",
    data={"query": "test", "filters": []}
))

# Unsubscribe
bus.unsubscribe("search.started", on_search)
```

### Threading (core.threading)

```python
from core.threading import (
    create_cpu_executor,
    create_io_executor,
    create_mixed_executor
)

# CPU-bound tasks
cpu_executor = create_cpu_executor(max_workers=4)
future = cpu_executor.submit(heavy_computation, data)
result = future.result()

# I/O-bound tasks
io_executor = create_io_executor(max_workers=20)
futures = [io_executor.submit(fetch_url, url) for url in urls]
results = [f.result() for f in futures]

# Mixed workload
mixed_executor = create_mixed_executor()
```

### Performance (core.performance)

```python
from core.performance import PerformanceMonitor

# Create monitor
monitor = PerformanceMonitor()

# Time operations
with monitor.timer("search_operation"):
    perform_search()

# Get statistics
stats = monitor.get_stats("search_operation")
print(f"Average time: {stats['mean']:.3f}s")
print(f"95th percentile: {stats['p95']:.3f}s")

# Memory snapshot
memory_mb = monitor.get_memory_usage()
print(f"Memory usage: {memory_mb:.1f} MB")
```

### Window State (core.window_state)

```python
from core.window_state import WindowStateManager

# Create manager
state_manager = WindowStateManager()

# Save window state
state_manager.save_state("main_window", {
    "x": 100,
    "y": 100,
    "width": 800,
    "height": 600,
    "maximized": False
})

# Load window state
state = state_manager.load_state("main_window")
if state:
    window.setGeometry(state["x"], state["y"], state["width"], state["height"])
```

---

## System Modules

### Admin Console (system.admin_console)

```python
from system.admin_console import (
    AdminConsoleManager,
    ConsoleType,
    ConsoleConfig
)

# Create manager
manager = AdminConsoleManager()

# Launch elevated PowerShell
config = ConsoleConfig(
    console_type=ConsoleType.POWERSHELL,
    elevated=True,
    working_directory=r"C:\Projects",
    title="Admin PowerShell"
)

session = manager.launch_console(config)

# Execute command
result = manager.execute_command("Get-Process", elevated=True)
```

### Elevation (system.elevation)

```python
from system.elevation import ElevationManager, ShowWindow

# Create manager
elevation = ElevationManager()

# Check if running as admin
if not elevation.is_admin():
    # Request elevation
    elevation.request_elevation(
        script_path=__file__,
        arguments=sys.argv[1:],
        show=ShowWindow.SW_SHOWNORMAL
    )
    sys.exit(0)

# Continue with admin privileges
print("Running as administrator")

# Run elevated command
result = elevation.run_elevated(
    r"C:\Windows\System32\cmd.exe",
    "/c echo test"
)
```

### Hotkeys (system.hotkeys)

```python
from system.hotkeys import HotkeyManager, ModifierKeys, VirtualKeys

# Create manager
hotkey_manager = HotkeyManager()

# Register global hotkey (Ctrl+Shift+F)
def on_search_hotkey():
    print("Search hotkey pressed")

hotkey_manager.register(
    modifiers=ModifierKeys.CTRL | ModifierKeys.SHIFT,
    vk_code=VirtualKeys.letter('F'),
    callback=on_search_hotkey,
    description="Global search"
)

# Unregister hotkey
hotkey_manager.unregister(hotkey_id)

# Cleanup
hotkey_manager.cleanup()
```

### Single Instance (system.single_instance)

```python
from system.single_instance import SingleInstanceManager

# Create manager
instance_manager = SingleInstanceManager("SmartSearchPro")

# Check if first instance
if not instance_manager.is_first_instance():
    # Activate existing instance
    instance_manager.activate_existing_instance()
    sys.exit(0)

# Continue with first instance
print("First instance running")

# Set window handle for activation
instance_manager.set_window_handle(main_window.winId())
```

### Autostart (system.autostart)

```python
from system.autostart import AutostartManager

# Create manager
autostart = AutostartManager(
    app_name="SmartSearchPro",
    executable_path=r"C:\Program Files\SmartSearch\smartsearch.exe"
)

# Enable autostart
autostart.enable()

# Disable autostart
autostart.disable()

# Check if enabled
if autostart.is_enabled():
    print("Autostart is enabled")
```

### Shell Integration (system.shell_integration)

```python
from system.shell_integration import ShellIntegration

# Create integration
shell = ShellIntegration(
    app_name="SmartSearchPro",
    executable_path=r"C:\Program Files\SmartSearch\smartsearch.exe"
)

# Add context menu
shell.install_context_menu(
    menu_text="Search with SmartSearch",
    icon_path=r"C:\Program Files\SmartSearch\icon.ico"
)

# Remove context menu
shell.uninstall_context_menu()
```

### Tray Icon (system.tray)

```python
from system.tray import SystemTrayIcon
from PyQt6.QtWidgets import QApplication

# Create application
app = QApplication(sys.argv)

# Create tray icon
tray = SystemTrayIcon(parent=main_window)

# Set icon and tooltip
tray.setIcon(QIcon("icon.png"))
tray.setToolTip("SmartSearch Pro")

# Add menu actions
menu = tray.contextMenu()
menu.addAction("Show", main_window.show)
menu.addAction("Exit", app.quit)

# Show tray icon
tray.show()
```

### Privilege Manager (system.privilege_manager)

```python
from system.privilege_manager import PrivilegeManager

# Create manager
privileges = PrivilegeManager()

# Enable specific privilege
privileges.enable_privilege("SeBackupPrivilege")
privileges.enable_privilege("SeRestorePrivilege")

# Check if privilege enabled
if privileges.has_privilege("SeDebugPrivilege"):
    print("Debug privilege enabled")

# Disable privilege
privileges.disable_privilege("SeBackupPrivilege")
```

---

## Common Patterns

### Database + Cache Pattern

```python
from core.database import Database
from core.cache import LRUCache

# Setup
db = Database("app.db")
cache = LRUCache(max_size=1000, ttl=3600)

def get_search_results(query: str):
    # Check cache first
    cached = cache.get(f"search:{query}")
    if cached is not None:
        return cached

    # Query database
    results = db.fetchall(
        "SELECT * FROM search_history WHERE query LIKE ?",
        (f"%{query}%",)
    )

    # Cache results
    cache.set(f"search:{query}", results)
    return results
```

### Configuration + Security Pattern

```python
from core.config import Config
from core.security import validate_table_name, sanitize_sql_input

config = Config()

def safe_query(table: str, where_clause: str, params: tuple):
    # Validate table name
    if not validate_table_name(table):
        raise ValueError(f"Invalid table: {table}")

    # Sanitize where clause
    safe_where = sanitize_sql_input(where_clause)

    # Execute query
    db = Database(config.database.path)
    return db.fetchall(f"SELECT * FROM {table} WHERE {safe_where}", params)
```

### Event Bus + Performance Pattern

```python
from core.eventbus import EventBus, Event
from core.performance import PerformanceMonitor

bus = EventBus()
monitor = PerformanceMonitor()

def perform_search(query: str):
    # Publish start event
    bus.publish(Event("search.started", {"query": query}))

    # Time operation
    with monitor.timer("search"):
        results = execute_search(query)

    # Publish complete event
    bus.publish(Event("search.completed", {
        "query": query,
        "count": len(results),
        "duration": monitor.get_last_duration("search")
    }))

    return results
```

---

## Error Handling

```python
from core.exceptions import (
    DatabaseError,
    CacheError,
    ConfigError,
    SecurityError
)

try:
    db.execute("INVALID SQL")
except DatabaseError as e:
    logger.error(f"Database error: {e}")

try:
    cache.set("key", "value")
except CacheError as e:
    logger.error(f"Cache error: {e}")

try:
    config = Config.from_file("invalid.yaml")
except ConfigError as e:
    logger.error(f"Config error: {e}")

try:
    sanitize_sql_input(dangerous_input)
except SecurityError as e:
    logger.error(f"Security error: {e}")
```

---

## Best Practices

1. **Always use parameterized queries**
   ```python
   # Good
   db.execute("SELECT * FROM users WHERE id = ?", (user_id,))

   # Bad
   db.execute(f"SELECT * FROM users WHERE id = {user_id}")
   ```

2. **Validate input before use**
   ```python
   safe_query = sanitize_sql_input(user_query)
   if validate_table_name(table_name):
       db.fetchall(f"SELECT * FROM {table_name} WHERE query = ?", (safe_query,))
   ```

3. **Use caching appropriately**
   ```python
   # Cache expensive operations
   cache.set(key, expensive_operation(), ttl=3600)

   # Don't cache rapidly changing data
   # (or use short TTL)
   ```

4. **Handle cleanup properly**
   ```python
   try:
       db = Database("app.db")
       # Use database
   finally:
       db.close()
   ```

5. **Log errors with context**
   ```python
   logger.error("Operation failed", extra={
       "operation": "search",
       "query": query,
       "error": str(e)
   })
   ```

---

**Last Updated:** 2025-12-12
**Version:** 1.0
