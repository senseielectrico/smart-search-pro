"""
Example usage of Smart Search Pro core module.

Demonstrates all major features and best practices.
"""

import asyncio
import sys
import tempfile
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    Config,
    Database,
    Event,
    EventPriority,
    LRUCache,
    get_cache,
    get_event_bus,
    get_logger,
    initialize,
    publish,
    setup_logging,
    subscribe,
)


def example_logging():
    """Demonstrate logging features."""
    print("\n" + "="*60)
    print("LOGGING EXAMPLE")
    print("="*60)

    # Setup logging
    setup_logging(
        log_dir=None,  # Console only for demo
        level="INFO",
        console=True,
        file=False,
    )

    # Get logger
    logger = get_logger(__name__)

    # Basic logging
    logger.info("Application started")
    logger.debug("This won't show at INFO level")
    logger.warning("This is a warning")

    # Structured logging with context
    logger.set_context(user_id=123, session="abc-123")
    logger.info("User action", action="search", query="test query")
    logger.info("Search completed", results=42, duration=1.5)

    # Clear context
    logger.clear_context()
    logger.info("No context message")


def example_config():
    """Demonstrate configuration features."""
    print("\n" + "="*60)
    print("CONFIGURATION EXAMPLE")
    print("="*60)

    # Create config with defaults
    config = Config()
    print(f"Database pool size: {config.database.pool_size}")
    print(f"Cache max size: {config.cache.max_size}")
    print(f"Search max results: {config.search.max_results}")

    # Modify config
    config.database.pool_size = 10
    config.cache.ttl_seconds = 7200  # 2 hours

    # Validate
    config.validate()
    print("Config validation passed")

    # Save and load
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        config_path = Path(f.name)

    config.save(config_path)
    print(f"Config saved to: {config_path}")

    loaded_config = Config.load(config_path)
    print(f"Loaded pool size: {loaded_config.database.pool_size}")

    # Cleanup
    config_path.unlink()


def example_cache():
    """Demonstrate cache features."""
    print("\n" + "="*60)
    print("CACHE EXAMPLE")
    print("="*60)

    # Create cache with limits
    cache = LRUCache[str, dict](max_size=5, default_ttl=2.0)

    # Add entries
    for i in range(7):
        cache.set(f"key{i}", {"value": i, "data": f"Item {i}"})

    # LRU eviction occurred (max_size=5, added 7)
    print(f"Cache size: {cache.size()}")
    print(f"Key0 exists: {cache.contains('key0')}")  # False (evicted)
    print(f"Key6 exists: {cache.contains('key6')}")  # True

    # Get values
    value = cache.get("key6")
    print(f"Retrieved: {value}")

    # Statistics
    stats = cache.stats()
    print(f"Hit rate: {stats['hit_rate']:.2%}")
    print(f"Total hits: {stats['hits']}, misses: {stats['misses']}")

    # TTL expiration
    cache.set("temp", {"data": "expires soon"}, ttl=0.5)
    print(f"Temp value: {cache.get('temp')}")
    time.sleep(0.6)
    print(f"After expiration: {cache.get('temp', 'EXPIRED')}")

    # Named caches
    user_cache = get_cache("users", max_size=100)
    file_cache = get_cache("files", max_size=500)

    user_cache.set("user123", {"name": "John", "role": "admin"})
    file_cache.set("/path/to/file", {"size": 1024, "hash": "abc123"})

    print(f"User cache: {user_cache.get('user123')}")
    print(f"File cache: {file_cache.get('/path/to/file')}")


def example_eventbus():
    """Demonstrate event bus features."""
    print("\n" + "="*60)
    print("EVENT BUS EXAMPLE")
    print("="*60)

    bus = get_event_bus()
    results = []

    # Basic handler
    def on_search(event: Event):
        results.append(f"Search: {event.data['query']}")

    bus.subscribe("search.executed", on_search)

    # Priority handlers
    def high_priority(event: Event):
        results.append("HIGH priority")

    def low_priority(event: Event):
        results.append("LOW priority")

    bus.subscribe("priority.test", high_priority, priority=EventPriority.HIGH)
    bus.subscribe("priority.test", low_priority, priority=EventPriority.LOW)

    # Filtered handler
    def only_errors(event: Event) -> bool:
        return event.data.get("level") == "error"

    def error_handler(event: Event):
        results.append(f"ERROR: {event.data['message']}")

    bus.subscribe("log", error_handler, filter_func=only_errors)

    # One-time handler
    def init_handler(event: Event):
        results.append("Initialized")

    bus.subscribe("app.init", init_handler, once=True)

    # Publish events
    publish("search.executed", {"query": "test query", "results": 10})
    publish("priority.test")
    publish("log", {"level": "info", "message": "Info message"})
    publish("log", {"level": "error", "message": "Error occurred"})
    publish("app.init")
    publish("app.init")  # Won't trigger (once=True)

    print(f"Results: {results}")

    # Statistics
    stats = bus.get_stats()
    print(f"Total events: {stats['total_events']}")
    print(f"Event counts: {stats['event_counts']}")


def example_database():
    """Demonstrate database features."""
    print("\n" + "="*60)
    print("DATABASE EXAMPLE")
    print("="*60)

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    db = Database(db_path, pool_size=3)
    print(f"Database created: {db_path}")

    # Insert search history
    search_id = db.insert(
        "search_history",
        {
            "query": "example query",
            "query_type": "text",
            "result_count": 42,
            "execution_time": 1.5,
            "timestamp": time.time(),
            "filters": '{"case_sensitive": false}',
            "metadata": '{"source": "ui"}',
        },
    )
    print(f"Inserted search with ID: {search_id}")

    # Query data
    result = db.fetchone(
        "SELECT * FROM search_history WHERE id = ?",
        (search_id,),
    )
    print(f"Retrieved: query={result['query']}, results={result['result_count']}")

    # Insert saved search
    saved_id = db.insert(
        "saved_searches",
        {
            "name": "My Favorite Search",
            "query": "*.py",
            "query_type": "glob",
            "description": "Find all Python files",
            "created_at": time.time(),
            "updated_at": time.time(),
        },
    )
    print(f"Saved search ID: {saved_id}")

    # Update
    db.update(
        "saved_searches",
        {"access_count": 5, "last_accessed": time.time()},
        "id = ?",
        (saved_id,),
    )
    print("Updated access count")

    # Batch insert
    tags = [
        ("/path/file1.py", "python", time.time()),
        ("/path/file2.py", "python", time.time()),
        ("/path/file1.py", "important", time.time()),
    ]

    db.executemany(
        "INSERT INTO file_tags (file_path, tag, created_at) VALUES (?, ?, ?)",
        tags,
    )
    print(f"Inserted {len(tags)} tags")

    # Query with join
    results = db.fetchall(
        """
        SELECT file_path, GROUP_CONCAT(tag) as tags
        FROM file_tags
        GROUP BY file_path
        """
    )
    for row in results:
        print(f"  {row['file_path']}: {row['tags']}")

    # Statistics
    stats = db.get_stats()
    print(f"Database size: {stats['size_bytes']} bytes")
    print(f"Tables: {', '.join(stats['tables'].keys())}")

    # Cleanup
    db.close()
    db_path.unlink()


async def example_async_events():
    """Demonstrate async event handlers."""
    print("\n" + "="*60)
    print("ASYNC EVENT BUS EXAMPLE")
    print("="*60)

    bus = get_event_bus()
    results = []

    # Async handler
    async def async_handler(event: Event):
        await asyncio.sleep(0.1)
        results.append(f"Async: {event.data['value']}")

    # Sync handler
    def sync_handler(event: Event):
        results.append(f"Sync: {event.data['value']}")

    bus.subscribe("async.test", async_handler)
    bus.subscribe("async.test", sync_handler)

    # Publish async
    await bus.publish_async("async.test", {"value": 42})

    # Give async handlers time to complete
    await asyncio.sleep(0.2)

    print(f"Results: {results}")


def example_integration():
    """Demonstrate full integration."""
    print("\n" + "="*60)
    print("FULL INTEGRATION EXAMPLE")
    print("="*60)

    # Create temporary directory for data
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create config
        config_file = tmp_path / "config.yaml"
        config = Config()
        config.data_dir = str(tmp_path / "data")
        config.database.path = "app.db"
        config.logging.level = "INFO"
        config.save(config_file)

        # Initialize all components
        loaded_config, db = initialize(
            config_path=str(config_file),
            log_dir=None,  # Console only
            log_level="INFO",
        )

        logger = get_logger("integration")
        logger.info("Application initialized")

        # Setup event handlers
        def on_search_start(event: Event):
            logger.info(
                "Search started",
                query=event.data["query"],
            )

        def on_search_complete(event: Event):
            logger.info(
                "Search completed",
                query=event.data["query"],
                results=event.data["results"],
                duration=event.data["duration"],
            )

            # Cache results
            cache = get_cache("search_results")
            cache.set(event.data["query"], event.data["results"])

        subscribe("search.start", on_search_start)
        subscribe("search.complete", on_search_complete)

        # Simulate search workflow
        query = "*.py"
        publish("search.start", {"query": query})

        # "Execute" search
        start_time = time.time()
        results = ["file1.py", "file2.py", "file3.py"]

        # Store in database
        search_id = db.insert(
            "search_history",
            {
                "query": query,
                "query_type": "glob",
                "result_count": len(results),
                "execution_time": time.time() - start_time,
                "timestamp": time.time(),
            },
        )

        # Publish completion
        publish(
            "search.complete",
            {
                "query": query,
                "results": results,
                "duration": time.time() - start_time,
                "search_id": search_id,
            },
        )

        # Retrieve from cache
        cache = get_cache("search_results")
        cached_results = cache.get(query)
        print(f"Cached results: {cached_results}")

        # Query database
        history = db.fetchall(
            "SELECT query, result_count FROM search_history ORDER BY timestamp DESC LIMIT 5"
        )
        print("Recent searches:")
        for row in history:
            print(f"  {row['query']}: {row['result_count']} results")

        db.close()


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("SMART SEARCH PRO - CORE MODULE EXAMPLES")
    print("="*60)

    example_logging()
    example_config()
    example_cache()
    example_eventbus()
    example_database()

    # Run async example
    asyncio.run(example_async_events())

    example_integration()

    print("\n" + "="*60)
    print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
