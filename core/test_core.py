"""
Comprehensive tests for Smart Search Pro core module.

Run with: pytest test_core.py -v
"""

import asyncio
import tempfile
import time
from pathlib import Path

import pytest

from . import (
    CacheExpiredError,
    Config,
    Database,
    Event,
    EventBus,
    IntegrityError,
    LRUCache,
    get_cache,
    get_config,
    get_event_bus,
    get_logger,
    initialize,
    setup_logging,
)


class TestExceptions:
    """Test custom exception hierarchy."""

    def test_base_exception(self):
        from .exceptions import SmartSearchError

        exc = SmartSearchError("Test error", {"key": "value"})
        assert str(exc) == "Test error (key=value)"
        assert exc.message == "Test error"
        assert exc.details == {"key": "value"}

    def test_exception_without_details(self):
        from .exceptions import SearchError

        exc = SearchError("No details")
        assert str(exc) == "No details"
        assert exc.details == {}


class TestLogger:
    """Test logging functionality."""

    def test_get_logger(self):
        logger = get_logger(__name__)
        assert logger is not None
        assert logger.name == __name__

    def test_structured_logging(self):
        logger = get_logger("test")
        logger.set_context(user="test_user", session="123")

        # Should not raise
        logger.info("Test message", extra_data="value")
        logger.debug("Debug message")
        logger.warning("Warning message")
        logger.error("Error message")

        logger.clear_context()

    def test_setup_logging(self, tmp_path):
        log_dir = tmp_path / "logs"
        setup_logging(log_dir=log_dir, level="DEBUG", console=False, file=True)

        logger = get_logger("test_setup")
        logger.info("Test log message")

        # Check log file was created
        log_files = list(log_dir.glob("*.log"))
        assert len(log_files) > 0


class TestConfig:
    """Test configuration system."""

    def test_default_config(self):
        config = Config()
        config.validate()

        assert config.database.pool_size == 5
        assert config.cache.max_size == 1000
        assert config.search.max_results == 1000

    def test_config_to_dict(self):
        config = Config()
        data = config.to_dict()

        assert "database" in data
        assert "cache" in data
        assert "search" in data

    def test_config_from_dict(self):
        data = {
            "database": {"pool_size": 10},
            "cache": {"max_size": 500},
            "version": "2.0.0",
        }

        config = Config.from_dict(data)
        assert config.database.pool_size == 10
        assert config.cache.max_size == 500
        assert config.version == "2.0.0"

    def test_config_save_load(self, tmp_path):
        config_file = tmp_path / "config.yaml"

        # Create and save config
        config = Config()
        config.database.pool_size = 20
        config.save(config_file)

        assert config_file.exists()

        # Load config
        loaded = Config.load(config_file)
        assert loaded.database.pool_size == 20

    def test_invalid_config(self):
        from .exceptions import InvalidConfigError

        config = Config()
        config.database.pool_size = -1

        with pytest.raises(InvalidConfigError):
            config.validate()


class TestCache:
    """Test LRU cache functionality."""

    def test_basic_operations(self):
        cache = LRUCache[str, int](max_size=3)

        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)

        assert cache.get("a") == 1
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    def test_lru_eviction(self):
        cache = LRUCache[str, int](max_size=3)

        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # Should evict "a"

        assert cache.get("a") is None
        assert cache.get("d") == 4

    def test_ttl_expiration(self):
        cache = LRUCache[str, int](default_ttl=0.1)  # 100ms TTL

        cache.set("key", 100)
        assert cache.get("key") == 100

        time.sleep(0.2)  # Wait for expiration

        with pytest.raises(CacheExpiredError):
            cache.get("key")

    def test_cleanup(self):
        cache = LRUCache[str, int](default_ttl=0.1)

        cache.set("a", 1)
        cache.set("b", 2)

        time.sleep(0.2)
        cleaned = cache.cleanup()

        assert cleaned == 2
        assert cache.size() == 0

    def test_statistics(self):
        cache = LRUCache[str, int]()

        cache.set("a", 1)
        cache.get("a")  # Hit
        cache.get("b")  # Miss

        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1

    def test_persistence(self, tmp_path):
        cache_file = tmp_path / "cache.pkl"

        # Create and populate cache
        cache = LRUCache[str, int]()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.save(cache_file)

        # Load into new cache
        new_cache = LRUCache[str, int]()
        new_cache.load(cache_file)

        assert new_cache.get("a") == 1
        assert new_cache.get("b") == 2

    def test_get_cache_manager(self):
        cache1 = get_cache("test1", max_size=100)
        cache2 = get_cache("test1")  # Should return same instance

        assert cache1 is cache2

    def test_dict_interface(self):
        cache = LRUCache[str, int]()

        cache["a"] = 1
        cache["b"] = 2

        assert cache["a"] == 1
        assert "a" in cache
        assert len(cache) == 2

        del cache["a"]
        assert "a" not in cache


class TestEventBus:
    """Test event bus functionality."""

    def test_subscribe_publish(self):
        bus = EventBus()
        results = []

        def handler(event: Event):
            results.append(event.data["value"])

        bus.subscribe("test.event", handler)
        bus.publish("test.event", {"value": 42})

        assert results == [42]

    def test_priority_ordering(self):
        bus = EventBus()
        results = []

        def high_priority(event: Event):
            results.append("high")

        def low_priority(event: Event):
            results.append("low")

        bus.subscribe("test", low_priority, priority=10)
        bus.subscribe("test", high_priority, priority=100)

        bus.publish("test")

        assert results == ["high", "low"]

    def test_event_filtering(self):
        bus = EventBus()
        results = []

        def handler(event: Event):
            results.append(event.data["value"])

        def only_even(event: Event) -> bool:
            return event.data["value"] % 2 == 0

        bus.subscribe("test", handler, filter_func=only_even)

        bus.publish("test", {"value": 1})
        bus.publish("test", {"value": 2})
        bus.publish("test", {"value": 3})

        assert results == [2]

    def test_one_time_handler(self):
        bus = EventBus()
        count = [0]

        def handler(event: Event):
            count[0] += 1

        bus.subscribe("test", handler, once=True)

        bus.publish("test")
        bus.publish("test")

        assert count[0] == 1

    def test_stop_propagation(self):
        bus = EventBus()
        results = []

        def handler1(event: Event):
            results.append(1)
            event.stop_propagation()

        def handler2(event: Event):
            results.append(2)

        bus.subscribe("test", handler1, priority=100)
        bus.subscribe("test", handler2, priority=50)

        bus.publish("test")

        assert results == [1]

    @pytest.mark.asyncio
    async def test_async_handler(self):
        bus = EventBus()
        results = []

        async def async_handler(event: Event):
            await asyncio.sleep(0.01)
            results.append("async")

        bus.subscribe("test", async_handler)
        await bus.publish_async("test")

        # Give async handler time to complete
        await asyncio.sleep(0.05)

        assert results == ["async"]

    def test_statistics(self):
        bus = EventBus()

        def handler(event: Event):
            pass

        bus.subscribe("event1", handler)
        bus.subscribe("event2", handler)
        bus.publish("event1")
        bus.publish("event1")

        stats = bus.get_stats()
        assert stats["total_handlers"] == 2
        assert stats["total_events"] == 2
        assert stats["event_counts"]["event1"] == 2

    def test_global_bus(self):
        from .eventbus import get_event_bus, publish, subscribe

        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2

        results = []

        def handler(event: Event):
            results.append(event.data["value"])

        subscribe("global.test", handler)
        publish("global.test", {"value": 123})

        assert results == [123]


class TestDatabase:
    """Test database functionality."""

    def test_database_creation(self, tmp_path):
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        assert db_path.exists()

        stats = db.get_stats()
        assert stats["schema_version"] == 1
        assert "search_history" in stats["tables"]

        db.close()

    def test_insert_query(self, tmp_path):
        db = Database(tmp_path / "test.db")

        # Insert into search_history
        row_id = db.insert(
            "search_history",
            {
                "query": "test query",
                "query_type": "text",
                "result_count": 10,
                "execution_time": 0.5,
                "timestamp": time.time(),
            },
        )

        assert row_id > 0

        # Query back
        result = db.fetchone(
            "SELECT * FROM search_history WHERE id = ?",
            (row_id,),
        )

        assert result is not None
        assert result["query"] == "test query"
        assert result["result_count"] == 10

        db.close()

    def test_update_delete(self, tmp_path):
        db = Database(tmp_path / "test.db")

        # Insert
        row_id = db.insert(
            "settings",
            {
                "key": "theme",
                "value": "dark",
                "value_type": "string",
                "updated_at": time.time(),
            },
        )

        # Update
        updated = db.update(
            "settings",
            {"value": "light"},
            "key = ?",
            ("theme",),
        )

        assert updated == 1

        result = db.fetchone("SELECT value FROM settings WHERE key = ?", ("theme",))
        assert result["value"] == "light"

        # Delete
        deleted = db.delete("settings", "key = ?", ("theme",))
        assert deleted == 1

        result = db.fetchone("SELECT * FROM settings WHERE key = ?", ("theme",))
        assert result is None

        db.close()

    def test_integrity_error(self, tmp_path):
        db = Database(tmp_path / "test.db")

        # Insert first time
        db.insert(
            "settings",
            {
                "key": "unique_key",
                "value": "value1",
                "value_type": "string",
                "updated_at": time.time(),
            },
        )

        # Try to insert duplicate (should fail due to PRIMARY KEY)
        with pytest.raises(IntegrityError):
            db.insert(
                "settings",
                {
                    "key": "unique_key",
                    "value": "value2",
                    "value_type": "string",
                    "updated_at": time.time(),
                },
            )

        db.close()

    def test_connection_pool(self, tmp_path):
        db = Database(tmp_path / "test.db", pool_size=3)

        # Execute multiple queries
        for i in range(10):
            db.insert(
                "search_history",
                {
                    "query": f"query {i}",
                    "query_type": "text",
                    "result_count": i,
                    "execution_time": 0.1,
                    "timestamp": time.time(),
                },
            )

        results = db.fetchall("SELECT COUNT(*) as count FROM search_history")
        assert results[0]["count"] == 10

        db.close()

    def test_vacuum(self, tmp_path):
        db = Database(tmp_path / "test.db")

        # Should not raise
        db.vacuum()

        db.close()


class TestIntegration:
    """Test integration of core components."""

    def test_initialize_function(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        log_dir = tmp_path / "logs"

        # Create config
        config = Config()
        config.data_dir = str(tmp_path / "data")
        config.save(config_file)

        # Initialize
        loaded_config, db = initialize(
            config_path=str(config_file),
            log_dir=str(log_dir),
            log_level="DEBUG",
        )

        assert loaded_config is not None
        assert db is not None

        # Verify logging
        logger = get_logger("integration_test")
        logger.info("Test message")

        log_files = list(log_dir.glob("*.log"))
        assert len(log_files) > 0

        db.close()

    def test_full_workflow(self, tmp_path):
        """Test complete workflow with all components."""
        # Setup
        config_file = tmp_path / "config.yaml"
        config = Config()
        config.data_dir = str(tmp_path / "data")
        config.database.path = "workflow.db"
        config.save(config_file)

        config, db = initialize(str(config_file))

        # Cache
        cache = get_cache("workflow", max_size=100)
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"

        # Event bus
        bus = get_event_bus()
        events_received = []

        def on_search(event: Event):
            events_received.append(event)

        bus.subscribe("search.completed", on_search)

        # Database
        search_id = db.insert(
            "search_history",
            {
                "query": "integration test",
                "query_type": "text",
                "result_count": 42,
                "execution_time": 1.5,
                "timestamp": time.time(),
            },
        )

        # Publish event
        bus.publish("search.completed", {"search_id": search_id})

        assert len(events_received) == 1
        assert events_received[0].data["search_id"] == search_id

        # Cleanup
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
