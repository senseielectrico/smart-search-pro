"""
Tests for core module: Database, Cache, EventBus, Config
"""

import pytest
import time
import os
from pathlib import Path


# ============================================================================
# DATABASE TESTS
# ============================================================================

class TestDatabase:
    """Tests for Database class"""

    def test_database_initialization(self, test_database):
        """Test database initialization and schema creation"""
        assert test_database is not None
        stats = test_database.get_stats()
        assert 'schema_version' in stats
        assert stats['schema_version'] == 1

    def test_database_insert(self, test_database):
        """Test inserting data into database"""
        row_id = test_database.insert('settings', {
            'key': 'test_key',
            'value': 'test_value',
            'value_type': 'string',
            'updated_at': time.time()
        })
        assert row_id > 0

    def test_database_fetchone(self, test_database):
        """Test fetching single row"""
        test_database.insert('settings', {
            'key': 'fetch_test',
            'value': 'fetch_value',
            'value_type': 'string',
            'updated_at': time.time()
        })

        result = test_database.fetchone(
            "SELECT * FROM settings WHERE key = ?",
            ('fetch_test',)
        )
        assert result is not None
        assert result['key'] == 'fetch_test'
        assert result['value'] == 'fetch_value'

    def test_database_fetchall(self, test_database):
        """Test fetching multiple rows"""
        for i in range(5):
            test_database.insert('settings', {
                'key': f'key_{i}',
                'value': f'value_{i}',
                'value_type': 'string',
                'updated_at': time.time()
            })

        results = test_database.fetchall("SELECT * FROM settings")
        assert len(results) >= 5

    def test_database_update(self, test_database):
        """Test updating data"""
        test_database.insert('settings', {
            'key': 'update_test',
            'value': 'old_value',
            'value_type': 'string',
            'updated_at': time.time()
        })

        updated = test_database.update(
            'settings',
            {'value': 'new_value', 'updated_at': time.time()},
            'key = ?',
            ('update_test',)
        )
        assert updated == 1

        result = test_database.fetchone(
            "SELECT * FROM settings WHERE key = ?",
            ('update_test',)
        )
        assert result['value'] == 'new_value'

    def test_database_delete(self, test_database):
        """Test deleting data"""
        test_database.insert('settings', {
            'key': 'delete_test',
            'value': 'delete_value',
            'value_type': 'string',
            'updated_at': time.time()
        })

        deleted = test_database.delete('settings', 'key = ?', ('delete_test',))
        assert deleted == 1

        result = test_database.fetchone(
            "SELECT * FROM settings WHERE key = ?",
            ('delete_test',)
        )
        assert result is None

    def test_database_transaction_rollback(self, test_database):
        """Test transaction rollback on error"""
        from core.exceptions import IntegrityError

        test_database.insert('settings', {
            'key': 'unique_key',
            'value': 'value1',
            'value_type': 'string',
            'updated_at': time.time()
        })

        with pytest.raises(IntegrityError):
            test_database.insert('settings', {
                'key': 'unique_key',  # Duplicate key
                'value': 'value2',
                'value_type': 'string',
                'updated_at': time.time()
            })

    def test_database_connection_pool(self, test_database):
        """Test connection pooling"""
        # Multiple operations should reuse connections
        for i in range(10):
            test_database.fetchone("SELECT 1", ())

        stats = test_database.get_stats()
        assert stats is not None


# ============================================================================
# CACHE TESTS
# ============================================================================

class TestCache:
    """Tests for LRUCache class"""

    def test_cache_set_get(self, test_cache):
        """Test basic set and get operations"""
        test_cache.set('key1', 'value1')
        assert test_cache.get('key1') == 'value1'

    def test_cache_get_default(self, test_cache):
        """Test get with default value"""
        assert test_cache.get('nonexistent', 'default') == 'default'

    def test_cache_ttl_expiration(self, test_cache):
        """Test TTL expiration"""
        from core.exceptions import CacheExpiredError

        test_cache.set('expire_key', 'expire_value', ttl=0.1)
        time.sleep(0.2)

        with pytest.raises(CacheExpiredError):
            test_cache.get('expire_key')

    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        from core.cache import LRUCache

        cache = LRUCache(max_size=3)
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.set('key3', 'value3')

        # Access key1 to make it recently used
        cache.get('key1')

        # Add new key, should evict key2 (least recently used)
        cache.set('key4', 'value4')

        assert cache.get('key1') == 'value1'
        assert cache.get('key2', None) is None
        assert cache.get('key3') == 'value3'
        assert cache.get('key4') == 'value4'

    def test_cache_size_based_eviction(self):
        """Test size-based eviction"""
        from core.cache import LRUCache

        cache = LRUCache(max_size=100, max_bytes=1000)
        cache.set('key1', 'x' * 400, size=400)
        cache.set('key2', 'y' * 400, size=400)
        # Next set should trigger eviction
        cache.set('key3', 'z' * 400, size=400)

        assert cache.bytes_used() <= 1000

    def test_cache_delete(self, test_cache):
        """Test delete operation"""
        test_cache.set('delete_key', 'delete_value')
        assert test_cache.delete('delete_key') is True
        assert test_cache.get('delete_key', None) is None

    def test_cache_clear(self, test_cache):
        """Test clear operation"""
        test_cache.set('key1', 'value1')
        test_cache.set('key2', 'value2')
        test_cache.clear()
        assert test_cache.size() == 0

    def test_cache_cleanup(self, test_cache):
        """Test cleanup of expired entries"""
        test_cache.set('expire1', 'value1', ttl=0.1)
        test_cache.set('expire2', 'value2', ttl=0.1)
        test_cache.set('keep', 'value3', ttl=10)

        time.sleep(0.2)
        removed = test_cache.cleanup()

        assert removed == 2
        assert test_cache.get('keep') == 'value3'

    def test_cache_contains(self, test_cache):
        """Test contains operation"""
        test_cache.set('exists', 'value')
        assert test_cache.contains('exists') is True
        assert test_cache.contains('nonexistent') is False

    def test_cache_stats(self, test_cache):
        """Test statistics tracking"""
        test_cache.set('key1', 'value1')
        test_cache.get('key1')
        test_cache.get('nonexistent', None)

        stats = test_cache.stats()
        assert stats['hits'] >= 1
        assert stats['misses'] >= 1
        assert stats['size'] >= 1

    def test_cache_invalidate_by_type(self, test_cache):
        """Test type-based invalidation"""
        test_cache.set('key1', 'value1', cache_type='type_a')
        test_cache.set('key2', 'value2', cache_type='type_a')
        test_cache.set('key3', 'value3', cache_type='type_b')

        removed = test_cache.invalidate_by_type('type_a')
        assert removed == 2
        assert test_cache.get('key3') == 'value3'

    def test_cache_prewarm(self, test_cache):
        """Test cache prewarming"""
        data = {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}
        count = test_cache.prewarm(data)

        assert count == 3
        assert test_cache.get('key1') == 'value1'

    def test_cache_persistence(self, temp_dir):
        """Test save and load operations"""
        from core.cache import LRUCache
        cache_file = os.path.join(temp_dir, 'cache.pkl')

        cache = LRUCache(max_size=100)
        cache.set('persist1', 'value1')
        cache.set('persist2', 'value2')
        cache.save(cache_file)

        cache2 = LRUCache(max_size=100)
        cache2.load(cache_file)

        assert cache2.get('persist1') == 'value1'
        assert cache2.get('persist2') == 'value2'


# ============================================================================
# EVENTBUS TESTS
# ============================================================================

class TestEventBus:
    """Tests for EventBus class"""

    def test_eventbus_subscribe_publish(self, test_eventbus):
        """Test basic subscribe and publish"""
        received_events = []

        def handler(event):
            received_events.append(event)

        test_eventbus.subscribe('test_event', handler)
        test_eventbus.publish('test_event', {'data': 'test'})

        assert len(received_events) == 1
        assert received_events[0].name == 'test_event'
        assert received_events[0].data['data'] == 'test'

    def test_eventbus_multiple_handlers(self, test_eventbus):
        """Test multiple handlers for same event"""
        call_count = {'count': 0}

        def handler1(event):
            call_count['count'] += 1

        def handler2(event):
            call_count['count'] += 10

        test_eventbus.subscribe('multi_event', handler1)
        test_eventbus.subscribe('multi_event', handler2)
        test_eventbus.publish('multi_event')

        assert call_count['count'] == 11

    def test_eventbus_handler_priority(self, test_eventbus):
        """Test handler priority order"""
        from core.eventbus import EventPriority
        order = []

        def low_priority(event):
            order.append('low')

        def high_priority(event):
            order.append('high')

        test_eventbus.subscribe('priority_event', low_priority, priority=EventPriority.LOW)
        test_eventbus.subscribe('priority_event', high_priority, priority=EventPriority.HIGH)
        test_eventbus.publish('priority_event')

        assert order == ['high', 'low']

    def test_eventbus_one_time_handler(self, test_eventbus):
        """Test one-time handler removal"""
        call_count = {'count': 0}

        def once_handler(event):
            call_count['count'] += 1

        test_eventbus.subscribe('once_event', once_handler, once=True)
        test_eventbus.publish('once_event')
        test_eventbus.publish('once_event')

        assert call_count['count'] == 1

    def test_eventbus_unsubscribe(self, test_eventbus):
        """Test unsubscribe operation"""
        call_count = {'count': 0}

        def handler(event):
            call_count['count'] += 1

        test_eventbus.subscribe('unsub_event', handler)
        test_eventbus.publish('unsub_event')
        test_eventbus.unsubscribe('unsub_event', handler)
        test_eventbus.publish('unsub_event')

        assert call_count['count'] == 1

    def test_eventbus_stop_propagation(self, test_eventbus):
        """Test event propagation stopping"""
        call_count = {'count': 0}

        def handler1(event):
            call_count['count'] += 1
            event.stop_propagation()

        def handler2(event):
            call_count['count'] += 10

        test_eventbus.subscribe('stop_event', handler1)
        test_eventbus.subscribe('stop_event', handler2)
        test_eventbus.publish('stop_event')

        assert call_count['count'] == 1

    def test_eventbus_filter_func(self, test_eventbus):
        """Test event filtering"""
        received = []

        def handler(event):
            received.append(event.data['value'])

        def filter_func(event):
            return event.data.get('value', 0) > 5

        test_eventbus.subscribe('filter_event', handler, filter_func=filter_func)
        test_eventbus.publish('filter_event', {'value': 3})
        test_eventbus.publish('filter_event', {'value': 7})

        assert received == [7]

    def test_eventbus_has_handlers(self, test_eventbus):
        """Test has_handlers check"""
        def handler(event):
            pass

        assert test_eventbus.has_handlers('test') is False
        test_eventbus.subscribe('test', handler)
        assert test_eventbus.has_handlers('test') is True

    def test_eventbus_get_stats(self, test_eventbus):
        """Test statistics retrieval"""
        def handler(event):
            pass

        test_eventbus.subscribe('event1', handler)
        test_eventbus.subscribe('event2', handler)
        test_eventbus.publish('event1')

        stats = test_eventbus.get_stats()
        assert stats['total_events'] >= 1
        assert stats['total_handlers'] >= 2

    def test_eventbus_clear_handlers(self, test_eventbus):
        """Test clearing handlers"""
        def handler(event):
            pass

        test_eventbus.subscribe('event1', handler)
        test_eventbus.subscribe('event2', handler)

        test_eventbus.clear_handlers('event1')
        assert test_eventbus.has_handlers('event1') is False
        assert test_eventbus.has_handlers('event2') is True


# ============================================================================
# CONFIG TESTS
# ============================================================================

class TestConfig:
    """Tests for Config class"""

    def test_config_initialization(self, test_config):
        """Test config initialization with defaults"""
        assert test_config is not None

    def test_config_get_set(self, test_config):
        """Test get and set operations"""
        test_config.set('test_key', 'test_value')
        assert test_config.get('test_key') == 'test_value'

    def test_config_get_default(self, test_config):
        """Test get with default value"""
        assert test_config.get('nonexistent', 'default') == 'default'

    def test_config_get_nested(self, test_config):
        """Test nested configuration access"""
        test_config.set('nested.level1.level2', 'deep_value')
        assert test_config.get('nested.level1.level2') == 'deep_value'

    def test_config_save_load(self, temp_dir):
        """Test config persistence"""
        from core.config import Config
        config_path = os.path.join(temp_dir, 'config_test.yaml')

        config1 = Config(config_path)
        config1.set('save_test', 'save_value')
        config1.save()

        config2 = Config(config_path)
        config2.load()
        assert config2.get('save_test') == 'save_value'

    def test_config_to_dict(self, test_config):
        """Test config to dictionary conversion"""
        test_config.set('dict_test', 'dict_value')
        config_dict = test_config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict.get('dict_test') == 'dict_value'


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
class TestCoreIntegration:
    """Integration tests for core modules"""

    def test_database_with_cache(self, test_database, test_cache):
        """Test database operations with caching"""
        # Insert to database
        test_database.insert('settings', {
            'key': 'cached_key',
            'value': 'cached_value',
            'value_type': 'string',
            'updated_at': time.time()
        })

        # Cache the result
        result = test_database.fetchone(
            "SELECT * FROM settings WHERE key = ?",
            ('cached_key',)
        )
        test_cache.set('db:cached_key', result)

        # Retrieve from cache
        cached = test_cache.get('db:cached_key')
        assert cached['value'] == 'cached_value'

    def test_eventbus_with_database(self, test_eventbus, test_database):
        """Test event bus triggering database operations"""
        def save_to_db(event):
            test_database.insert('operation_history', {
                'operation_type': event.data['type'],
                'operation_data': str(event.data),
                'status': 'completed',
                'timestamp': time.time()
            })

        test_eventbus.subscribe('db_operation', save_to_db)
        test_eventbus.publish('db_operation', {'type': 'test_op', 'data': 'test'})

        results = test_database.fetchall("SELECT * FROM operation_history")
        assert len(results) > 0
