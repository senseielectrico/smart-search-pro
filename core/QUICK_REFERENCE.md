# Smart Search Pro Core - Quick Reference

## Installation

```bash
cd C:\Users\ramos\.local\bin\smart_search\core
pip install -r requirements.txt
```

## One-Line Initialization

```python
from smart_search.core import initialize

config, db = initialize("config.yaml", log_dir="logs", log_level="INFO")
```

## Common Operations

### Logging

```python
from smart_search.core import get_logger

logger = get_logger(__name__)
logger.info("Message", key1="value1", key2="value2")
logger.set_context(user_id=123)
logger.error("Error occurred", error_code=500)
```

### Configuration

```python
from smart_search.core import get_config, load_config

# Get default config
config = get_config()

# Load from file
config = load_config("config.yaml")

# Access values
print(config.database.pool_size)
print(config.cache.max_size)

# Modify and save
config.database.pool_size = 10
config.save("config.yaml")
```

### Database

```python
from smart_search.core import Database

db = Database("app.db")

# Insert
row_id = db.insert("search_history", {
    "query": "test",
    "result_count": 10,
    "timestamp": time.time()
})

# Query
results = db.fetchall("SELECT * FROM search_history WHERE result_count > ?", (5,))
result = db.fetchone("SELECT * FROM search_history WHERE id = ?", (row_id,))

# Update
db.update("settings", {"value": "new"}, "key = ?", ("theme",))

# Delete
db.delete("search_history", "timestamp < ?", (old_time,))

# Close
db.close()
```

### Cache

```python
from smart_search.core import get_cache

cache = get_cache("my_cache", max_size=1000)

# Set with TTL
cache.set("key", "value", ttl=3600)

# Get with default
value = cache.get("key", default="not_found")

# Check existence
if "key" in cache:
    print("Found")

# Statistics
stats = cache.stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")

# Save/load
cache.save("cache.pkl")
cache.load("cache.pkl")
```

### Events

```python
from smart_search.core import subscribe, publish

# Subscribe
def handler(event):
    print(f"Got event: {event.data}")

subscribe("my.event", handler)

# Publish
publish("my.event", {"key": "value"})

# With priority
from smart_search.core import EventPriority

subscribe("event", high_handler, priority=EventPriority.HIGH)

# Async handler
async def async_handler(event):
    await do_something()

subscribe("event", async_handler)

# Publish async
await publish_async("event", {"data": "value"})
```

## Database Tables

### search_history
```python
db.insert("search_history", {
    "query": "*.py",
    "query_type": "glob",
    "result_count": 42,
    "execution_time": 1.5,
    "timestamp": time.time(),
    "filters": '{"case_sensitive": false}',
    "metadata": '{}'
})
```

### saved_searches
```python
db.insert("saved_searches", {
    "name": "My Search",
    "query": "pattern",
    "query_type": "text",
    "description": "Description",
    "created_at": time.time(),
    "updated_at": time.time()
})
```

### hash_cache
```python
db.insert("hash_cache", {
    "file_path": "/path/to/file",
    "file_hash": "abc123...",
    "file_size": 1024,
    "modified_time": time.time(),
    "created_at": time.time()
})
```

### file_tags
```python
db.insert("file_tags", {
    "file_path": "/path/to/file",
    "tag": "important",
    "created_at": time.time()
})
```

### settings
```python
db.insert("settings", {
    "key": "theme",
    "value": "dark",
    "value_type": "string",
    "updated_at": time.time()
})
```

### operation_history
```python
db.insert("operation_history", {
    "operation_type": "search",
    "operation_data": '{"query": "test"}',
    "status": "success",
    "duration": 1.5,
    "timestamp": time.time()
})
```

### preview_cache
```python
db.insert("preview_cache", {
    "file_path": "/path/to/file",
    "preview_data": "...",
    "preview_type": "text",
    "file_size": 1024,
    "modified_time": time.time(),
    "created_at": time.time()
})
```

## Exception Handling

```python
from smart_search.core import (
    DatabaseError,
    CacheError,
    SearchError,
    ConfigurationError
)

try:
    db.insert("table", data)
except IntegrityError as e:
    print(f"Error: {e.message}")
    print(f"Details: {e.details}")
```

## Configuration Template

```yaml
database:
  path: "smart_search.db"
  pool_size: 5

cache:
  max_size: 1000
  ttl_seconds: 3600

search:
  max_results: 1000
  excluded_extensions: [".exe", ".dll"]
  excluded_dirs: [".git", "node_modules"]

logging:
  level: "INFO"
  log_dir: "logs"
```

## Common Patterns

### Search Workflow
```python
# Start event
publish("search.start", {"query": query})

# Execute search
results = search_engine.search(query)

# Store in database
search_id = db.insert("search_history", {
    "query": query,
    "result_count": len(results),
    "execution_time": duration,
    "timestamp": time.time()
})

# Cache results
cache = get_cache("search_results")
cache.set(query, results, ttl=3600)

# Complete event
publish("search.complete", {
    "query": query,
    "results": results,
    "search_id": search_id
})
```

### Event-Driven Architecture
```python
# Register handlers
subscribe("file.opened", on_file_opened)
subscribe("file.saved", on_file_saved)
subscribe("search.complete", on_search_complete)

# Publish events throughout app
publish("file.opened", {"path": path})
publish("file.saved", {"path": path, "size": size})
publish("search.complete", {"results": results})
```

### Configuration Override
```python
config = load_config("config.yaml")
config.database.pool_size = 10
config.cache.max_size = 2000
config.validate()
config.save("config.yaml")
```

## Performance Tips

1. **Use connection pooling**: Database class handles this automatically
2. **Cache frequently accessed data**: Use LRU cache with appropriate TTL
3. **Batch database operations**: Use `executemany()` for bulk inserts
4. **Enable WAL mode**: Already enabled by default for better concurrency
5. **Use named caches**: Separate caches for different data types
6. **Set appropriate TTLs**: Match TTL to data volatility

## Debugging

```python
# Enable debug logging
from smart_search.core import set_log_level
set_log_level("DEBUG")

# Get statistics
db_stats = db.get_stats()
cache_stats = cache.stats()
event_stats = get_event_bus().get_stats()

# Check cache hit rate
print(f"Cache hit rate: {cache_stats['hit_rate']:.2%}")

# Monitor events
print(f"Total events: {event_stats['total_events']}")
```

## Testing

```bash
# Run all tests
pytest test_core.py -v

# Run with coverage
pytest test_core.py --cov=. --cov-report=html

# Run specific test
pytest test_core.py::TestDatabase::test_insert_query -v

# Run import test
python test_imports.py

# Run examples
python example_usage.py
```

## Import Shortcuts

```python
# Everything in one import
from smart_search.core import (
    # Initialization
    initialize,

    # Logging
    get_logger,

    # Config
    get_config,
    load_config,

    # Database
    Database,

    # Cache
    get_cache,
    LRUCache,

    # Events
    subscribe,
    publish,
    get_event_bus,

    # Exceptions
    DatabaseError,
    CacheError,
    SearchError,
)
```

## File Locations

```
C:\Users\ramos\.local\bin\smart_search\core\
├── __init__.py           - Package exports
├── exceptions.py         - Custom exceptions
├── logger.py            - Logging system
├── config.py            - Configuration
├── cache.py             - LRU cache
├── eventbus.py          - Event system
├── database.py          - Database manager
└── requirements.txt     - Dependencies
```

## Version

1.0.0 (2025-12-12)
