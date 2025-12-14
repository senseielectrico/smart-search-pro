"""
Integration Tests - End-to-End Workflow Testing
================================================

Tests that verify the complete workflows and interactions between modules.
"""

import pytest
import os
import time


@pytest.mark.integration
class TestEndToEndWorkflows:
    """End-to-end workflow tests"""

    def test_search_export_workflow(self, temp_dir):
        """Test complete search and export workflow"""
        from search.query_parser import QueryParser
        from export.json_exporter import JSONExporter
        from unittest.mock import MagicMock

        # Parse query
        parser = QueryParser()
        parsed = parser.parse("test document ext:pdf")

        # Mock search results
        mock_results = [
            {
                'filename': 'document.pdf',
                'path': '/test/path',
                'size': 1024,
                'modified': time.time()
            }
        ]

        # Export results
        exporter = JSONExporter()
        output_file = os.path.join(temp_dir, "search_results.json")
        exporter.export(mock_results, output_file)

        assert os.path.exists(output_file)

    def test_duplicate_scan_and_action_workflow(self, duplicate_files, temp_db):
        """Test duplicate detection and handling workflow"""
        from duplicates.scanner import DuplicateScanner
        from duplicates.groups import DuplicateGroupManager

        # Scan for duplicates
        scanner = DuplicateScanner(use_cache=True, cache_path=temp_db, max_workers=2)
        scan_path = os.path.dirname(duplicate_files['original'])
        groups = scanner.scan([scan_path])

        assert groups is not None
        # Verify workflow completed
        assert isinstance(groups, DuplicateGroupManager)

    def test_file_operation_with_progress_workflow(self, sample_files, temp_dir):
        """Test file operations with progress tracking"""
        from operations.copier import FileCopier

        if len(sample_files) > 0:
            copier = FileCopier(max_workers=2)
            copier.start()

            progress_updates = []

            def track_progress(current, total):
                progress_updates.append((current, total))

            source = sample_files[0]
            dest = os.path.join(temp_dir, "workflow_copy.txt")

            try:
                success = copier.copy_file(source, dest, progress_callback=track_progress)
                assert success is True
                assert len(progress_updates) > 0
            finally:
                copier.shutdown()

    def test_search_filter_export_workflow(self, temp_dir):
        """Test search with filtering and export"""
        from search.query_parser import QueryParser, SizeFilter, SizeOperator
        from search.filters import SizeFilterImpl, FilterChain
        from export.csv_exporter import CSVExporter

        # Parse query with filters
        parser = QueryParser()
        parsed = parser.parse("document size:>1mb")

        # Apply filters to mock results
        filter_chain = FilterChain()
        size_filters = [SizeFilter(operator=SizeOperator.GREATER_EQUAL, value=1024*1024, unit="b")]
        filter_chain.add_filter(SizeFilterImpl(size_filters))

        mock_results = [
            {'filename': 'large.pdf', 'size': 2048*1024, 'path': '/test'},
            {'filename': 'small.txt', 'size': 500, 'path': '/test'}
        ]

        # Filter results
        from search.engine import SearchResult
        results = []
        for r in mock_results:
            sr = SearchResult(
                filename=r['filename'],
                path=r['path'],
                full_path=f"{r['path']}/{r['filename']}",
                size=r['size']
            )
            if filter_chain.matches(sr):
                results.append(r)

        # Export filtered results
        exporter = CSVExporter()
        output_file = os.path.join(temp_dir, "filtered_results.csv")
        exporter.export(results, output_file)

        assert os.path.exists(output_file)


@pytest.mark.integration
class TestDatabaseIntegration:
    """Database integration tests"""

    def test_search_history_persistence(self, test_database):
        """Test search history storage and retrieval"""
        # Insert search history
        test_database.insert('search_history', {
            'query': 'test query',
            'query_type': 'keyword',
            'result_count': 10,
            'execution_time': 0.5,
            'timestamp': time.time(),
            'filters': None,
            'metadata': None
        })

        # Retrieve history
        history = test_database.fetchall(
            "SELECT * FROM search_history ORDER BY timestamp DESC LIMIT 10"
        )

        assert len(history) > 0
        assert history[0]['query'] == 'test query'

    def test_operation_history_tracking(self, test_database):
        """Test operation history tracking"""
        # Record operation
        test_database.insert('operation_history', {
            'operation_type': 'copy',
            'operation_data': '{"source": "/test/file.txt", "dest": "/dest/file.txt"}',
            'status': 'completed',
            'error_message': None,
            'duration': 1.5,
            'timestamp': time.time()
        })

        # Query history
        operations = test_database.fetchall(
            "SELECT * FROM operation_history WHERE operation_type = 'copy'"
        )

        assert len(operations) > 0

    def test_hash_cache_integration(self, test_hash_cache, sample_files):
        """Test hash cache with database backend"""
        if len(sample_files) > 0:
            file_path = sample_files[0]
            test_hash = "test_hash_123"

            # Cache hash using correct API
            test_hash_cache.set_hash(file_path, quick_hash=test_hash)

            # Retrieve hash
            cached_data = test_hash_cache.get_hash(file_path)

            assert cached_data is not None
            assert cached_data.get('quick_hash') == test_hash


@pytest.mark.integration
class TestCacheIntegration:
    """Cache integration tests"""

    def test_search_result_caching(self, test_cache):
        """Test caching search results"""
        # Simulate search results
        results = [
            {'filename': 'file1.txt', 'path': '/test'},
            {'filename': 'file2.txt', 'path': '/test'}
        ]

        query_key = "search:test query"
        test_cache.set(query_key, results, ttl=300, cache_type='search')

        # Retrieve cached results
        cached_results = test_cache.get(query_key)

        assert cached_results == results

    def test_preview_cache_integration(self, test_cache, sample_text_file):
        """Test caching preview data"""
        from preview.text_preview import TextPreviewer

        previewer = TextPreviewer()
        preview_data = previewer.generate_preview(sample_text_file)

        # Cache preview
        cache_key = f"preview:{sample_text_file}"
        test_cache.set(cache_key, preview_data, ttl=600, cache_type='preview')

        # Retrieve cached preview
        cached_preview = test_cache.get(cache_key)

        assert cached_preview is not None

    def test_cache_invalidation_workflow(self, test_cache):
        """Test cache invalidation patterns"""
        # Add various cached items
        test_cache.set('search:query1', {'results': []}, cache_type='search')
        test_cache.set('search:query2', {'results': []}, cache_type='search')
        test_cache.set('preview:file1', {'content': ''}, cache_type='preview')

        # Invalidate only search cache
        removed = test_cache.invalidate_by_type('search')

        assert removed == 2
        assert test_cache.get('preview:file1') is not None


@pytest.mark.integration
class TestEventBusIntegration:
    """Event bus integration tests"""

    def test_operation_events(self, test_eventbus, test_database):
        """Test event-driven operation tracking"""
        operation_log = []

        def log_operation(event):
            operation_log.append({
                'type': event.data['operation'],
                'timestamp': event.timestamp,
                'status': event.data.get('status', 'unknown')
            })

        # Subscribe to operation events
        test_eventbus.subscribe('operation:started', log_operation)
        test_eventbus.subscribe('operation:completed', log_operation)

        # Publish events
        test_eventbus.publish('operation:started', {
            'operation': 'copy',
            'source': '/test/file.txt',
            'dest': '/dest/file.txt'
        })

        test_eventbus.publish('operation:completed', {
            'operation': 'copy',
            'status': 'success'
        })

        assert len(operation_log) == 2

    def test_search_events(self, test_eventbus):
        """Test event-driven search notifications"""
        search_events = []

        def handle_search_event(event):
            search_events.append(event.data)

        test_eventbus.subscribe('search:started', handle_search_event)
        test_eventbus.subscribe('search:completed', handle_search_event)

        # Simulate search workflow
        test_eventbus.publish('search:started', {'query': 'test'})
        test_eventbus.publish('search:completed', {'query': 'test', 'results': 10})

        assert len(search_events) == 2


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Performance integration tests"""

    def test_large_file_operations(self, temp_dir, performance_timer):
        """Test operations on large files"""
        from operations.copier import FileCopier

        # Create large test file (10MB)
        large_file = os.path.join(temp_dir, "large_file.bin")
        with open(large_file, 'wb') as f:
            f.write(b'0' * (10 * 1024 * 1024))

        dest_file = os.path.join(temp_dir, "large_file_copy.bin")

        copier = FileCopier(max_workers=2)
        copier.start()

        try:
            performance_timer['start']()
            success = copier.copy_file(large_file, dest_file)
            duration = performance_timer['stop']()

            assert success is True
            assert duration < 10.0  # Should complete within 10 seconds
        finally:
            copier.shutdown()

    def test_concurrent_searches(self, performance_timer):
        """Test concurrent search operations"""
        from search.query_parser import QueryParser
        import concurrent.futures

        parser = QueryParser()
        queries = [f"test query {i}" for i in range(10)]

        def parse_query(query):
            return parser.parse(query)

        performance_timer['start']()

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(parse_query, q) for q in queries]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        duration = performance_timer['stop']()

        assert len(results) == 10
        assert duration < 5.0  # Should complete within 5 seconds

    def test_bulk_export(self, temp_dir, performance_timer):
        """Test exporting large dataset"""
        from export.json_exporter import JSONExporter
        from datetime import datetime

        # Create large dataset (10000 items)
        large_dataset = [
            {
                'id': i,
                'filename': f'file_{i}.txt',
                'path': f'/test/path_{i}',
                'size': i * 1024,
                'modified': datetime.now().isoformat()
            }
            for i in range(10000)
        ]

        exporter = JSONExporter()
        output_file = os.path.join(temp_dir, "bulk_export.json")

        performance_timer['start']()
        exporter.export(large_dataset, output_file)
        duration = performance_timer['stop']()

        assert os.path.exists(output_file)
        assert duration < 5.0  # Should complete within 5 seconds


@pytest.mark.integration
class TestErrorHandling:
    """Error handling integration tests"""

    def test_graceful_failure_in_workflow(self, temp_dir):
        """Test graceful failure handling in complete workflow"""
        from operations.copier import FileCopier

        copier = FileCopier(max_workers=2, retry_attempts=2)
        copier.start()

        try:
            # Try to copy non-existent file
            source = os.path.join(temp_dir, "nonexistent.txt")
            dest = os.path.join(temp_dir, "dest.txt")

            success, error = copier.copy_file_with_retry(source, dest)

            # Should fail gracefully
            assert success is False
            assert error is not None
        finally:
            copier.shutdown()

    def test_cache_failure_recovery(self, test_cache):
        """Test recovery from cache failures"""
        # Try to get non-existent key
        result = test_cache.get('nonexistent_key', default='fallback')

        assert result == 'fallback'

    def test_database_constraint_handling(self, test_database):
        """Test handling of database constraints"""
        from core.exceptions import IntegrityError

        # Insert initial record
        test_database.insert('settings', {
            'key': 'duplicate_test',
            'value': 'value1',
            'value_type': 'string',
            'updated_at': time.time()
        })

        # Try to insert duplicate (should fail due to UNIQUE constraint)
        with pytest.raises(IntegrityError):
            test_database.insert('settings', {
                'key': 'duplicate_test',
                'value': 'value2',
                'value_type': 'string',
                'updated_at': time.time()
            })
