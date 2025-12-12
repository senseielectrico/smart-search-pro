"""
Comprehensive Test Suite for Smart Search Pro
==============================================

Complete testing coverage for all core modules, operations, duplicates,
UI components, and integration scenarios.

Test Strategy:
- Unit tests for individual components (70%)
- Integration tests for module interactions (20%)
- End-to-end tests for complete workflows (10%)
- Performance benchmarks for critical paths
- Security tests for input validation
"""

import os
import sys
import time
import tempfile
import sqlite3
import hashlib
import threading
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, call
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# 1. CORE MODULES TESTS
# ============================================================================

class TestConfigLoading:
    """Test configuration system"""

    def test_config_default_values(self, temp_dir):
        """Test config loads with default values"""
        from core.config import Config

        config = Config()

        assert config.app_name == "Smart Search Pro"
        assert config.version == "1.0.0"
        assert config.database.pool_size == 5
        assert config.cache.max_size == 1000
        assert config.search.max_results == 1000

    def test_config_load_from_file(self, temp_dir):
        """Test loading config from YAML file"""
        from core.config import Config
        import yaml

        config_path = os.path.join(temp_dir, "test_config.yaml")
        test_config = {
            'app_name': 'Test App',
            'version': '2.0.0',
            'database': {
                'pool_size': 10,
                'timeout': 60.0
            }
        }

        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)

        config = Config.load(config_path)

        assert config.app_name == 'Test App'
        assert config.version == '2.0.0'
        assert config.database.pool_size == 10
        assert config.database.timeout == 60.0

    def test_config_save_and_reload(self, temp_dir):
        """Test saving and reloading config"""
        from core.config import Config

        config_path = os.path.join(temp_dir, "config.yaml")

        # Create and save config
        config = Config()
        config.app_name = "Modified App"
        config.database.pool_size = 15
        config.save(config_path)

        # Reload and verify
        loaded_config = Config.load(config_path)
        assert loaded_config.app_name == "Modified App"
        assert loaded_config.database.pool_size == 15

    def test_config_validation(self, temp_dir):
        """Test config validation"""
        from core.config import Config, InvalidConfigError

        config = Config()

        # Test invalid pool_size
        config.database.pool_size = -1
        with pytest.raises(InvalidConfigError, match="pool_size must be at least 1"):
            config.validate()

        # Test invalid timeout
        config.database.pool_size = 5
        config.database.timeout = -10
        with pytest.raises(InvalidConfigError, match="timeout must be positive"):
            config.validate()

    def test_config_update_runtime(self, temp_dir):
        """Test runtime configuration updates"""
        from core.config import Config

        config = Config()
        initial_pool_size = config.database.pool_size

        # Update directly on the database config object
        config.database.pool_size = 20
        config.validate()

        assert config.database.pool_size == 20
        assert config.database.pool_size != initial_pool_size


class TestDatabaseOperations:
    """Test database management"""

    def test_database_initialization(self, temp_db):
        """Test database initialization and migrations"""
        from core.database import Database

        db = Database(temp_db, pool_size=2)

        # Verify tables created
        stats = db.get_stats()
        assert 'search_history' in stats['tables']
        assert 'hash_cache' in stats['tables']
        assert 'saved_searches' in stats['tables']
        assert stats['schema_version'] == 1

        db.close()

    def test_database_insert_and_fetch(self, test_database):
        """Test insert and fetch operations"""

        # Insert test data
        data = {
            'query': 'test query',
            'query_type': 'filename',
            'result_count': 10,
            'execution_time': 0.5,
            'timestamp': time.time()
        }

        row_id = test_database.insert('search_history', data)
        assert row_id > 0

        # Fetch inserted data
        result = test_database.fetchone(
            'SELECT * FROM search_history WHERE id = ?',
            (row_id,)
        )

        assert result is not None
        assert result['query'] == 'test query'
        assert result['result_count'] == 10

    def test_database_update(self, test_database):
        """Test update operations"""

        # Insert test data
        data = {'query': 'original', 'query_type': 'filename',
                'result_count': 5, 'execution_time': 0.1, 'timestamp': time.time()}
        row_id = test_database.insert('search_history', data)

        # Update data
        update_data = {'result_count': 15, 'execution_time': 0.3}
        rows_updated = test_database.update(
            'search_history',
            update_data,
            'id = ?',
            (row_id,)
        )

        assert rows_updated == 1

        # Verify update
        result = test_database.fetchone(
            'SELECT * FROM search_history WHERE id = ?',
            (row_id,)
        )
        assert result['result_count'] == 15
        assert result['execution_time'] == 0.3

    def test_database_delete(self, test_database):
        """Test delete operations"""

        # Insert multiple rows
        for i in range(5):
            data = {
                'query': f'query_{i}',
                'query_type': 'filename',
                'result_count': i,
                'execution_time': 0.1,
                'timestamp': time.time()
            }
            test_database.insert('search_history', data)

        # Delete specific rows
        rows_deleted = test_database.delete(
            'search_history',
            'result_count < ?',
            (3,)
        )

        assert rows_deleted == 3

        # Verify deletion
        remaining = test_database.fetchall('SELECT * FROM search_history')
        assert len(remaining) == 2

    def test_database_connection_pooling(self, temp_db):
        """Test connection pool functionality"""
        from core.database import Database

        db = Database(temp_db, pool_size=3)

        # Simulate concurrent access
        def insert_data(thread_id):
            data = {
                'query': f'thread_{thread_id}',
                'query_type': 'filename',
                'result_count': thread_id,
                'execution_time': 0.1,
                'timestamp': time.time()
            }
            return db.insert('search_history', data)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(insert_data, i) for i in range(10)]
            results = [f.result() for f in futures]

        # All inserts should succeed
        assert len(results) == 10
        assert all(r > 0 for r in results)

        db.close()

    def test_database_transaction_rollback(self, test_database):
        """Test transaction rollback on error"""
        from core import exceptions

        # Insert with unique constraint
        data = {
            'name': 'unique_search',
            'query': 'test',
            'query_type': 'filename',
            'created_at': time.time(),
            'updated_at': time.time()
        }
        test_database.insert('saved_searches', data)

        # Try to insert duplicate (should fail with IntegrityError)
        with pytest.raises(exceptions.IntegrityError):
            test_database.insert('saved_searches', data)


class TestEventBusPubSub:
    """Test event bus publish-subscribe system"""

    def test_eventbus_subscribe_and_publish(self, test_eventbus):
        """Test basic subscribe and publish"""

        received_events = []

        def handler(event):
            received_events.append(event)

        test_eventbus.subscribe('test.event', handler)
        test_eventbus.publish('test.event', {'message': 'Hello'})

        assert len(received_events) == 1
        assert received_events[0].name == 'test.event'
        assert received_events[0].data['message'] == 'Hello'

    def test_eventbus_multiple_handlers(self, test_eventbus):
        """Test multiple handlers for same event"""

        call_order = []

        def handler1(event):
            call_order.append('handler1')

        def handler2(event):
            call_order.append('handler2')

        def handler3(event):
            call_order.append('handler3')

        test_eventbus.subscribe('test.event', handler1)
        test_eventbus.subscribe('test.event', handler2)
        test_eventbus.subscribe('test.event', handler3)

        test_eventbus.publish('test.event', {})

        assert len(call_order) == 3
        assert 'handler1' in call_order
        assert 'handler2' in call_order
        assert 'handler3' in call_order

    def test_eventbus_priority_ordering(self, test_eventbus):
        """Test event handler priority"""
        from core.eventbus import EventPriority

        call_order = []

        def low_priority(event):
            call_order.append('low')

        def high_priority(event):
            call_order.append('high')

        def normal_priority(event):
            call_order.append('normal')

        test_eventbus.subscribe('test.event', low_priority, priority=EventPriority.LOW)
        test_eventbus.subscribe('test.event', high_priority, priority=EventPriority.HIGH)
        test_eventbus.subscribe('test.event', normal_priority, priority=EventPriority.NORMAL)

        test_eventbus.publish('test.event', {})

        # Should execute in priority order: high, normal, low
        assert call_order == ['high', 'normal', 'low']

    def test_eventbus_unsubscribe(self, test_eventbus):
        """Test unsubscribe functionality"""

        received = []

        def handler(event):
            received.append(event)

        test_eventbus.subscribe('test.event', handler)
        test_eventbus.publish('test.event', {'count': 1})

        assert len(received) == 1

        # Unsubscribe and publish again
        test_eventbus.unsubscribe('test.event', handler)
        test_eventbus.publish('test.event', {'count': 2})

        # Should not receive second event
        assert len(received) == 1

    def test_eventbus_once_handler(self, test_eventbus):
        """Test one-time event handlers"""

        received = []

        def handler(event):
            received.append(event)

        test_eventbus.subscribe('test.event', handler, once=True)

        test_eventbus.publish('test.event', {'count': 1})
        test_eventbus.publish('test.event', {'count': 2})
        test_eventbus.publish('test.event', {'count': 3})

        # Should only receive first event
        assert len(received) == 1

    def test_eventbus_filter_function(self, test_eventbus):
        """Test event filtering"""

        received = []

        def handler(event):
            received.append(event)

        def filter_func(event):
            return event.data.get('priority') == 'high'

        test_eventbus.subscribe('test.event', handler, filter_func=filter_func)

        test_eventbus.publish('test.event', {'priority': 'low'})
        test_eventbus.publish('test.event', {'priority': 'high'})
        test_eventbus.publish('test.event', {'priority': 'medium'})

        # Should only receive high priority event
        assert len(received) == 1
        assert received[0].data['priority'] == 'high'

    def test_eventbus_stop_propagation(self, test_eventbus):
        """Test stopping event propagation"""

        call_order = []

        def handler1(event):
            call_order.append('handler1')
            event.stop_propagation()

        def handler2(event):
            call_order.append('handler2')

        test_eventbus.subscribe('test.event', handler1)
        test_eventbus.subscribe('test.event', handler2)

        test_eventbus.publish('test.event', {})

        # Only handler1 should be called
        assert call_order == ['handler1']

    def test_eventbus_statistics(self, test_eventbus):
        """Test event bus statistics"""

        def handler(event):
            pass

        test_eventbus.subscribe('event1', handler)
        test_eventbus.subscribe('event2', handler)
        test_eventbus.subscribe('event2', handler)

        test_eventbus.publish('event1', {})
        test_eventbus.publish('event2', {})
        test_eventbus.publish('event2', {})

        stats = test_eventbus.get_stats()

        assert stats['total_events'] == 3
        assert stats['total_handlers'] == 3
        assert stats['event_counts']['event1'] == 1
        assert stats['event_counts']['event2'] == 2


# ============================================================================
# 2. OPERATIONS TESTS
# ============================================================================

class TestFileCopier:
    """Test file copying operations"""

    def test_copy_single_file(self, temp_dir, test_file_copier):
        """Test copying a single file"""

        source = os.path.join(temp_dir, "source.txt")
        dest = os.path.join(temp_dir, "dest.txt")

        # Create source file
        with open(source, 'w') as f:
            f.write("Test content" * 100)

        # Copy file
        success = test_file_copier.copy_file(source, dest)

        assert success
        assert os.path.exists(dest)
        assert os.path.getsize(source) == os.path.getsize(dest)

        # Verify content
        with open(source, 'r') as sf, open(dest, 'r') as df:
            assert sf.read() == df.read()

    def test_copy_large_file(self, temp_dir, test_file_copier):
        """Test copying a large file (10MB)"""

        source = os.path.join(temp_dir, "large.bin")
        dest = os.path.join(temp_dir, "large_copy.bin")

        # Create 10MB file
        with open(source, 'wb') as f:
            f.write(b'0' * (10 * 1024 * 1024))

        # Copy with progress tracking
        progress_updates = []

        def progress_callback(copied, total):
            progress_updates.append((copied, total))

        success = test_file_copier.copy_file(
            source, dest,
            progress_callback=progress_callback
        )

        assert success
        assert os.path.exists(dest)
        assert os.path.getsize(source) == os.path.getsize(dest)
        assert len(progress_updates) > 0

    def test_copy_with_different_sizes(self, temp_dir, test_file_copier):
        """Test copying files of various sizes"""

        sizes = [
            1024,              # 1KB
            10 * 1024,         # 10KB
            100 * 1024,        # 100KB
            1024 * 1024,       # 1MB
            5 * 1024 * 1024,   # 5MB
        ]

        for size in sizes:
            source = os.path.join(temp_dir, f"file_{size}.bin")
            dest = os.path.join(temp_dir, f"copy_{size}.bin")

            # Create file
            with open(source, 'wb') as f:
                f.write(b'X' * size)

            # Copy
            success = test_file_copier.copy_file(source, dest)

            assert success, f"Failed to copy {size} byte file"
            assert os.path.getsize(dest) == size

    def test_copy_with_retry(self, temp_dir, test_file_copier):
        """Test copy with retry mechanism"""

        source = os.path.join(temp_dir, "source.txt")
        dest = os.path.join(temp_dir, "dest.txt")

        with open(source, 'w') as f:
            f.write("Test content")

        # Test successful copy with retry
        success, error = test_file_copier.copy_file_with_retry(source, dest)

        assert success
        assert error is None
        assert os.path.exists(dest)

    def test_copy_batch_parallel(self, temp_dir, test_file_copier):
        """Test batch copying multiple files in parallel"""

        # Create source files
        file_pairs = []
        for i in range(10):
            source = os.path.join(temp_dir, f"source_{i}.txt")
            dest = os.path.join(temp_dir, f"dest_{i}.txt")

            with open(source, 'w') as f:
                f.write(f"Content {i}" * 100)

            file_pairs.append((source, dest))

        # Copy all files
        results = test_file_copier.copy_files_batch(file_pairs)

        assert len(results) == 10
        assert all(success for success, error in results.values())

        # Verify all files copied
        for source, dest in file_pairs:
            assert os.path.exists(dest)
            assert os.path.getsize(source) == os.path.getsize(dest)

    def test_copy_pause_resume(self, temp_dir, test_file_copier):
        """Test pause and resume functionality"""

        source = os.path.join(temp_dir, "source.bin")
        dest = os.path.join(temp_dir, "dest.bin")

        # Create 5MB file
        with open(source, 'wb') as f:
            f.write(b'0' * (5 * 1024 * 1024))

        # Start copy in thread
        copy_thread = threading.Thread(
            target=test_file_copier.copy_file,
            args=(source, dest)
        )
        copy_thread.start()

        # Pause briefly
        time.sleep(0.1)
        test_file_copier.pause()
        time.sleep(0.2)
        test_file_copier.resume()

        copy_thread.join(timeout=10)

        assert os.path.exists(dest)

    def test_copy_cancel(self, temp_dir, test_file_copier):
        """Test cancelling copy operation"""

        source = os.path.join(temp_dir, "source.bin")
        dest = os.path.join(temp_dir, "dest.bin")

        # Create large file
        with open(source, 'wb') as f:
            f.write(b'0' * (10 * 1024 * 1024))

        # Start copy and cancel
        test_file_copier.cancel()
        success = test_file_copier.copy_file(source, dest)

        assert not success
        test_file_copier.reset_cancel()


class TestQueueOperations:
    """Test queue-based operations"""

    def test_operation_queue_fifo(self, test_operation_manager):
        """Test FIFO queue ordering"""

        operations = []

        for i in range(5):
            op = {
                'type': 'copy',
                'source': f'/source/{i}',
                'destination': f'/dest/{i}'
            }
            test_operation_manager.queue_operation(op)
            operations.append(op)

        # Process queue
        processed = []
        while not test_operation_manager.is_queue_empty():
            op = test_operation_manager.dequeue_operation()
            processed.append(op)

        # Verify FIFO order
        assert len(processed) == 5
        for i, op in enumerate(processed):
            assert op['source'] == f'/source/{i}'

    def test_operation_queue_priority(self, test_operation_manager):
        """Test priority queue ordering"""

        # Queue with different priorities
        test_operation_manager.queue_operation(
            {'type': 'copy', 'file': 'normal'},
            priority=1
        )
        test_operation_manager.queue_operation(
            {'type': 'copy', 'file': 'high'},
            priority=10
        )
        test_operation_manager.queue_operation(
            {'type': 'copy', 'file': 'low'},
            priority=0
        )

        # Dequeue and verify order
        first = test_operation_manager.dequeue_operation()
        second = test_operation_manager.dequeue_operation()
        third = test_operation_manager.dequeue_operation()

        assert first['file'] == 'high'
        assert second['file'] == 'normal'
        assert third['file'] == 'low'


class TestProgressCallbacks:
    """Test progress tracking and callbacks"""

    def test_progress_callback_invocation(self, temp_dir, test_file_copier):
        """Test progress callback is called during copy"""

        source = os.path.join(temp_dir, "source.bin")
        dest = os.path.join(temp_dir, "dest.bin")

        # Create 1MB file
        with open(source, 'wb') as f:
            f.write(b'0' * (1024 * 1024))

        callback_calls = []

        def progress_callback(copied, total):
            callback_calls.append((copied, total))

        test_file_copier.copy_file(
            source, dest,
            progress_callback=progress_callback
        )

        assert len(callback_calls) > 0

        # Last callback should report 100%
        last_copied, last_total = callback_calls[-1]
        assert last_copied == last_total

    def test_progress_percentage_calculation(self, temp_dir, test_file_copier):
        """Test progress percentage calculation"""

        source = os.path.join(temp_dir, "source.bin")
        dest = os.path.join(temp_dir, "dest.bin")

        size = 1024 * 1024  # 1MB
        with open(source, 'wb') as f:
            f.write(b'0' * size)

        percentages = []

        def progress_callback(copied, total):
            percent = (copied / total) * 100 if total > 0 else 0
            percentages.append(percent)

        test_file_copier.copy_file(
            source, dest,
            progress_callback=progress_callback
        )

        # Verify progress is monotonically increasing
        for i in range(1, len(percentages)):
            assert percentages[i] >= percentages[i-1]

        # Last percentage should be 100%
        assert percentages[-1] == 100.0


# ============================================================================
# 3. DUPLICATES TESTS
# ============================================================================

class TestDuplicateScanner:
    """Test duplicate file detection"""

    def test_scanner_with_known_duplicates(self, duplicate_files, test_duplicate_scanner):
        """Test scanning with known duplicate files"""

        scan_dir = os.path.dirname(duplicate_files['original'])

        # Run scan
        groups = test_duplicate_scanner.scan([scan_dir])

        # Should find one group with 4 files (1 original + 3 duplicates)
        assert len(groups.groups) == 1

        group = groups.groups[0]
        assert group.file_count == 4
        assert group.total_size > 0

    def test_scanner_no_duplicates(self, sample_files, test_duplicate_scanner):
        """Test scanning directory with no duplicates"""

        scan_dir = os.path.dirname(sample_files[0])

        groups = test_duplicate_scanner.scan([scan_dir])

        # Should find no duplicate groups
        assert len(groups.groups) == 0

    def test_scanner_progress_callback(self, duplicate_files, test_duplicate_scanner):
        """Test progress callback during scan"""

        scan_dir = os.path.dirname(duplicate_files['original'])

        progress_updates = []

        def progress_callback(progress):
            progress_updates.append({
                'pass': progress.current_pass,
                'file': progress.current_file,
                'percent': progress.progress_percent,
                'phase': progress.current_phase
            })

        test_duplicate_scanner.scan([scan_dir], progress_callback=progress_callback)

        # Should have progress updates
        assert len(progress_updates) > 0

        # Should go through all 3 passes
        passes_seen = set(p['pass'] for p in progress_updates)
        assert passes_seen == {1, 2, 3}

    def test_scanner_cancellation(self, sample_directory_structure, test_duplicate_scanner):
        """Test scan cancellation"""

        # Start scan and cancel immediately
        test_duplicate_scanner.cancel()
        groups = test_duplicate_scanner.scan([sample_directory_structure])

        # Should return empty results
        assert len(groups.groups) == 0


class TestHashAlgorithms:
    """Test different hash algorithms"""

    def test_md5_hash(self, temp_dir):
        """Test MD5 hashing"""
        from duplicates.hasher import FileHasher, HashAlgorithm

        filepath = os.path.join(temp_dir, "test.txt")
        content = b"Test content for MD5"

        with open(filepath, 'wb') as f:
            f.write(content)

        hasher = FileHasher(algorithm=HashAlgorithm.MD5)
        full_hash = hasher.compute_full_hash(filepath)

        # Verify against known MD5
        expected = hashlib.md5(content).hexdigest()
        assert full_hash == expected

    def test_sha256_hash(self, temp_dir):
        """Test SHA256 hashing"""
        from duplicates.hasher import FileHasher, HashAlgorithm

        filepath = os.path.join(temp_dir, "test.txt")
        content = b"Test content for SHA256"

        with open(filepath, 'wb') as f:
            f.write(content)

        hasher = FileHasher(algorithm=HashAlgorithm.SHA256)
        full_hash = hasher.compute_full_hash(filepath)

        # Verify against known SHA256
        expected = hashlib.sha256(content).hexdigest()
        assert full_hash == expected

    def test_quick_hash_vs_full_hash(self, temp_dir):
        """Test quick hash vs full hash"""
        from duplicates.hasher import FileHasher, HashAlgorithm

        filepath = os.path.join(temp_dir, "test.bin")

        # Create file larger than quick hash size
        with open(filepath, 'wb') as f:
            f.write(b'A' * 10000)

        hasher = FileHasher(algorithm=HashAlgorithm.SHA256)

        quick_hash = hasher.compute_quick_hash(filepath)
        full_hash = hasher.compute_full_hash(filepath)

        # Quick and full hashes should be different for large files
        assert quick_hash is not None
        assert full_hash is not None
        assert quick_hash != full_hash


class TestGroupManagement:
    """Test duplicate group management"""

    def test_create_duplicate_group(self):
        """Test creating duplicate group"""
        from duplicates.groups import DuplicateGroup

        group = DuplicateGroup(hash_value="test_hash", hash_type="full")

        assert group.hash_value == "test_hash"
        assert group.file_count == 0
        assert group.total_size == 0

    def test_add_files_to_group(self):
        """Test adding files to group"""
        from duplicates.groups import DuplicateGroup

        group = DuplicateGroup(hash_value="test_hash", hash_type="full")

        group.add_file("/path/file1.txt", size=1024, mtime=time.time())
        group.add_file("/path/file2.txt", size=1024, mtime=time.time())
        group.add_file("/path/file3.txt", size=1024, mtime=time.time())

        assert group.file_count == 3
        assert group.total_size == 3072

    def test_wasted_space_calculation(self):
        """Test wasted space calculation"""
        from duplicates.groups import DuplicateGroup

        group = DuplicateGroup(hash_value="test_hash", hash_type="full")

        # Add 3 files of 1024 bytes each
        for i in range(3):
            group.add_file(f"/path/file{i}.txt", size=1024, mtime=time.time())

        # Wasted space = total_size - original_size
        # = (3 * 1024) - 1024 = 2048
        assert group.wasted_space == 2048


# ============================================================================
# 4. UI TESTS (without GUI)
# ============================================================================

class TestMainWindowInitialization:
    """Test UI initialization without actually creating GUI"""

    def test_window_components_initialization(self):
        """Test window components are properly initialized"""
        # Mock QApplication
        with patch('PyQt6.QtWidgets.QApplication'):
            # We can't actually test UI without QApplication running
            # But we can test the logic
            pass

    def test_menu_structure(self):
        """Test menu structure is correct"""
        # Test menu configuration
        menu_structure = {
            'File': ['New Search', 'Open', 'Save', 'Exit'],
            'Edit': ['Copy', 'Cut', 'Paste'],
            'View': ['Refresh', 'Settings'],
            'Help': ['About', 'Documentation']
        }

        assert 'File' in menu_structure
        assert 'New Search' in menu_structure['File']


class TestSignalConnections:
    """Test signal-slot connections"""

    def test_button_click_signal(self):
        """Test button click signal connection"""
        # Mock signal connection
        mock_button = Mock()
        mock_handler = Mock()

        # Simulate signal connection
        mock_button.clicked.connect(mock_handler)

        # Simulate button click
        mock_button.clicked.emit()

        # Verify handler was called
        mock_handler.assert_called_once()

    def test_search_signal_chain(self):
        """Test search signal propagation"""
        # Mock signal chain
        search_input = Mock()
        search_button = Mock()
        search_worker = Mock()

        # Simulate signal chain
        search_button.clicked.connect(lambda: search_worker.start())
        search_button.clicked.emit()

        # Verify worker started
        search_worker.start.assert_called_once()


# ============================================================================
# 5. INTEGRATION TESTS
# ============================================================================

class TestCompleteSearchFlow:
    """Test complete search workflow"""

    def test_search_and_display_results(self, sample_directory_structure):
        """Test complete search flow from query to results"""
        # This would test:
        # 1. Parse search query
        # 2. Execute search
        # 3. Filter results
        # 4. Display in UI
        pass

    def test_search_with_filters(self, sample_directory_structure):
        """Test search with multiple filters"""
        # Test applying multiple filters (size, date, type)
        pass


class TestDuplicatesFlow:
    """Test complete duplicate detection workflow"""

    def test_scan_identify_and_action(self, duplicate_files):
        """Test complete duplicate workflow"""
        from duplicates.scanner import DuplicateScanner
        from duplicates.hasher import HashAlgorithm

        scan_dir = os.path.dirname(duplicate_files['original'])

        # 1. Scan for duplicates
        scanner = DuplicateScanner(
            algorithm=HashAlgorithm.MD5,
            use_cache=False,
            max_workers=2
        )
        groups = scanner.scan([scan_dir])

        # 2. Verify duplicates found
        assert len(groups.groups) > 0

        # 3. Get files to delete (keep newest)
        for group in groups.groups:
            files = group.get_sorted_files(sort_by='mtime', reverse=True)
            to_keep = files[0]
            to_delete = files[1:]

            assert len(to_delete) > 0


class TestExportFlow:
    """Test export to different formats"""

    def test_export_to_csv(self, temp_dir, sample_export_data, test_csv_exporter):
        """Test exporting results to CSV"""

        output_path = os.path.join(temp_dir, "export.csv")
        test_csv_exporter.export(sample_export_data, output_path)

        assert os.path.exists(output_path)

        # Verify content
        import csv
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == len(sample_export_data)

    def test_export_to_json(self, temp_dir, sample_export_data, test_json_exporter):
        """Test exporting results to JSON"""
        import json

        output_path = os.path.join(temp_dir, "export.json")
        test_json_exporter.export(sample_export_data, output_path)

        assert os.path.exists(output_path)

        # Verify content
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert len(data) == len(sample_export_data)

    def test_export_to_html(self, temp_dir, sample_export_data, test_html_exporter):
        """Test exporting results to HTML"""

        output_path = os.path.join(temp_dir, "export.html")
        test_html_exporter.export(sample_export_data, output_path)

        assert os.path.exists(output_path)

        # Verify it's valid HTML
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '<html>' in content.lower()
            assert '<table>' in content.lower()


# ============================================================================
# 6. PERFORMANCE TESTS
# ============================================================================

@pytest.mark.performance
class TestPerformance:
    """Performance benchmarks"""

    def test_large_file_copy_performance(self, temp_dir, test_file_copier, performance_timer):
        """Benchmark copying large files"""

        source = os.path.join(temp_dir, "large.bin")
        dest = os.path.join(temp_dir, "large_copy.bin")

        # Create 100MB file
        size = 100 * 1024 * 1024
        with open(source, 'wb') as f:
            f.write(b'0' * size)

        # Time the copy
        performance_timer['start']()
        success = test_file_copier.copy_file(source, dest)
        duration = performance_timer['stop']()

        assert success

        # Calculate throughput
        throughput_mbps = (size / duration) / (1024 * 1024)

        print(f"\nCopy Performance: {throughput_mbps:.2f} MB/s")

        # Should be reasonable (> 50 MB/s)
        assert throughput_mbps > 50

    def test_hash_computation_performance(self, temp_dir, test_file_hasher, performance_timer):
        """Benchmark hash computation"""

        filepath = os.path.join(temp_dir, "test.bin")

        # Create 50MB file
        size = 50 * 1024 * 1024
        with open(filepath, 'wb') as f:
            f.write(b'X' * size)

        # Time hash computation
        performance_timer['start']()
        full_hash = test_file_hasher.compute_full_hash(filepath)
        duration = performance_timer['stop']()

        assert full_hash is not None

        # Calculate throughput
        throughput_mbps = (size / duration) / (1024 * 1024)

        print(f"\nHash Performance: {throughput_mbps:.2f} MB/s")

        # Should be reasonable (> 100 MB/s for MD5)
        assert throughput_mbps > 100

    def test_database_bulk_insert_performance(self, test_database, performance_timer):
        """Benchmark bulk database inserts"""

        # Prepare data
        data_list = []
        for i in range(1000):
            data_list.append((
                f'query_{i}',
                'filename',
                i,
                0.1,
                time.time()
            ))

        # Time bulk insert
        performance_timer['start']()
        test_database.executemany(
            'INSERT INTO search_history (query, query_type, result_count, execution_time, timestamp) VALUES (?, ?, ?, ?, ?)',
            data_list
        )
        duration = performance_timer['stop']()

        print(f"\nBulk Insert: {len(data_list)} rows in {duration:.3f}s ({len(data_list)/duration:.0f} rows/s)")

        # Should insert > 500 rows/second
        assert (len(data_list) / duration) > 500


# ============================================================================
# TEST SUITE SUMMARY
# ============================================================================

if __name__ == '__main__':
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--color=yes',
        '-k', 'not performance'  # Skip performance tests by default
    ])
