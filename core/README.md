# Smart Search Pro - Core Module

Production-ready core module providing foundational components for Smart Search Pro.

## Features

- **Configuration System**: YAML-based configuration with validation and defaults
- **Database Manager**: SQLite with connection pooling, migrations, and thread-safety
- **LRU Cache**: Memory-efficient cache with TTL, size limits, and persistence
- **Event Bus**: Pub-sub pattern for loose coupling with async support
- **Structured Logging**: Rich console output with file rotation
- **Exception Hierarchy**: Comprehensive custom exceptions

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from smart_search.core import initialize, get_logger

# Initialize all core components
config, db = initialize("config.yaml", log_dir="logs", log_level="INFO")

# Use structured logging
logger = get_logger(__name__)
logger.info("Application started", version="1.0.0")

# Insert data
search_id = db.insert("search_history", {
    "query": "test",
    "query_type": "text",
    "result_count": 10,
    "execution_time": 0.5,
    "timestamp": time.time()
})

# Use cache
from smart_search.core import get_cache

cache = get_cache("my_cache", max_size=1000)
cache.set("key", "value", ttl=3600)
value = cache.get("key")

# Use event bus
from smart_search.core import subscribe, publish

def on_search(event):
    print(f"Search completed: {event.data}")

subscribe("search.completed", on_search)
publish("search.completed", {"query": "test", "results": 42})

# Clean up
db.close()
```

## Components

### Configuration (`config.py`)

Type-safe configuration with dataclasses and YAML support:

```python
from smart_search.core import Config, load_config

# Load from file
config = load_config("config.yaml")

# Access nested config
print(config.database.pool_size)
print(config.cache.max_size)

# Save changes
config.database.pool_size = 10
config.save("config.yaml")
```

### Database (`database.py`)

Thread-safe SQLite database with connection pooling:

```python
from smart_search.core import Database

db = Database("app.db", pool_size=5)

# Insert
row_id = db.insert("search_history", {
    "query": "test",
    "result_count": 10,
    "timestamp": time.time()
})

# Query
results = db.fetchall("SELECT * FROM search_history WHERE result_count > ?", (5,))

# Update
db.update("settings", {"value": "new_value"}, "key = ?", ("theme",))

# Delete
db.delete("search_history", "timestamp < ?", (old_timestamp,))

# Statistics
stats = db.get_stats()
print(f"Database size: {stats['size_bytes']} bytes")
```

### Cache (`cache.py`)

LRU cache with TTL and size limits:

```python
from smart_search.core import LRUCache, get_cache

# Create cache with limits
cache = LRUCache(max_size=1000, max_bytes=10*1024*1024, default_ttl=3600)

# Set with custom TTL
cache.set("key", "value", ttl=1800)

# Get with default
value = cache.get("key", default="not_found")

# Statistics
stats = cache.stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")

# Persistence
cache.save("cache.pkl")
cache.load("cache.pkl")

# Named caches
user_cache = get_cache("users", max_size=500)
file_cache = get_cache("files", max_size=1000)
```

### Event Bus (`eventbus.py`)

Publish-subscribe pattern for decoupled components:

```python
from smart_search.core import EventBus, Event, EventPriority

bus = EventBus()

# Subscribe with priority
def high_priority_handler(event: Event):
    print(f"High: {event.data}")

bus.subscribe("event", high_priority_handler, priority=EventPriority.HIGH)

# Async handler
async def async_handler(event: Event):
    await asyncio.sleep(0.1)
    print(f"Async: {event.data}")

bus.subscribe("event", async_handler)

# Filter events
def only_errors(event: Event) -> bool:
    return event.data.get("level") == "error"

bus.subscribe("log", error_handler, filter_func=only_errors)

# One-time handler
bus.subscribe("init", init_handler, once=True)

# Publish
bus.publish("event", {"key": "value"})
await bus.publish_async("event", {"key": "value"})

# Statistics
stats = bus.get_stats()
```

### Logger (`logger.py`)

Structured logging with rich console output:

```python
from smart_search.core import setup_logging, get_logger

# Setup
setup_logging(
    log_dir="logs",
    level="INFO",
    console=True,
    file=True,
    max_bytes=10*1024*1024,
    backup_count=5
)

# Get logger
logger = get_logger(__name__)

# Log with context
logger.set_context(user_id=123, session="abc")
logger.info("User action", action="search", query="test")

# Structured data
logger.error("Search failed", query="test", error_code=500, duration=1.5)

# Exception logging
try:
    risky_operation()
except Exception:
    logger.exception("Operation failed", operation="risky")
```

### Exceptions (`exceptions.py`)

Comprehensive exception hierarchy:

```python
from smart_search.core import (
    DatabaseError,
    CacheError,
    SearchError,
    ConfigurationError
)

try:
    db.insert("table", {})
except IntegrityError as e:
    print(f"Constraint violated: {e.message}")
    print(f"Details: {e.details}")
```

## Database Schema

### Tables

- **search_history**: Search query history with metadata
- **saved_searches**: User-saved search queries
- **hash_cache**: File hash cache for duplicate detection
- **file_tags**: User-defined file tags
- **settings**: Application settings
- **operation_history**: Operation audit log
- **preview_cache**: File preview cache

### Indexes

All tables have appropriate indexes for performance:
- Timestamps for time-based queries
- Paths for file lookups
- Hash values for duplicate detection

## Testing

Run the test suite:

```bash
# All tests
pytest test_core.py -v

# With coverage
pytest test_core.py --cov=. --cov-report=html

# Specific test class
pytest test_core.py::TestDatabase -v
```

## Type Checking

```bash
mypy *.py --strict
```

## Code Quality

```bash
ruff check .
ruff format .
```

## Architecture

### Thread Safety

All components are thread-safe:
- Database uses connection pooling with locks
- Cache uses RLock for atomic operations
- Event bus uses RLock for handler management

### Performance

- Connection pooling reduces overhead
- LRU cache minimizes memory usage
- WAL mode for concurrent reads
- Lazy initialization where possible

### Error Handling

- Custom exceptions with context
- Graceful degradation
- Detailed error messages
- Exception chaining preserved

## Configuration Example

```yaml
database:
  path: "smart_search.db"
  pool_size: 5
  timeout: 30.0
  enable_wal: true
  journal_mode: "WAL"
  synchronous: "NORMAL"

cache:
  max_size: 1000
  ttl_seconds: 3600
  cleanup_interval: 300
  enable_persistence: true

search:
  max_results: 1000
  timeout: 30.0
  case_sensitive: false
  fuzzy_threshold: 0.7
  max_file_size_mb: 100
  excluded_extensions:
    - ".exe"
    - ".dll"
    - ".zip"
  excluded_dirs:
    - ".git"
    - "node_modules"
    - "__pycache__"

logging:
  level: "INFO"
  console: true
  file: true
  log_dir: "logs"
  max_bytes: 10485760  # 10MB
  backup_count: 5

ui:
  theme: "dark"
  accent_color: "#00ff00"
  font_family: "Consolas"
  font_size: 10
  auto_save: true

performance:
  max_threads: 8
  chunk_size: 8192
  memory_limit_mb: 1024
  enable_profiling: false
```

## License

Proprietary - Smart Search Pro Team

## Version

1.0.0
