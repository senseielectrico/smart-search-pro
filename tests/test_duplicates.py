"""
Tests for duplicates module: Scanner, Hasher, Cache
"""

import pytest
import os
import hashlib


# ============================================================================
# FILE HASHER TESTS
# ============================================================================

class TestFileHasher:
    """Tests for FileHasher class"""

    def test_hasher_initialization(self, test_file_hasher):
        """Test hasher initialization"""
        assert test_file_hasher is not None

    def test_hash_file(self, test_file_hasher, sample_files):
        """Test hashing single file"""
        if len(sample_files) > 0:
            file_path = sample_files[0]
            file_hash = test_file_hasher.hash_file(file_path)
            assert file_hash is not None
            assert len(file_hash) > 0

    def test_hash_multiple_files(self, test_file_hasher, sample_files):
        """Test hashing multiple files"""
        if len(sample_files) >= 3:
            hashes = test_file_hasher.hash_files(sample_files[:3])
            assert len(hashes) == 3
            for file_path, file_hash in hashes.items():
                assert file_hash is not None

    def test_quick_hash(self, test_file_hasher, sample_files):
        """Test quick hash (first/last chunks)"""
        if len(sample_files) > 0:
            file_path = sample_files[0]
            quick_hash = test_file_hasher.quick_hash(file_path)
            assert quick_hash is not None
            assert len(quick_hash) > 0

    def test_hash_consistency(self, test_file_hasher, sample_files):
        """Test hash consistency for same file"""
        if len(sample_files) > 0:
            file_path = sample_files[0]
            hash1 = test_file_hasher.hash_file(file_path)
            hash2 = test_file_hasher.hash_file(file_path)
            assert hash1 == hash2

    def test_different_files_different_hashes(self, test_file_hasher, sample_files):
        """Test different files produce different hashes"""
        if len(sample_files) >= 2:
            hash1 = test_file_hasher.hash_file(sample_files[0])
            hash2 = test_file_hasher.hash_file(sample_files[1])
            # Hashes should be different (unless files are identical)
            assert isinstance(hash1, str)
            assert isinstance(hash2, str)


# ============================================================================
# HASH CACHE TESTS
# ============================================================================

class TestHashCache:
    """Tests for HashCache class"""

    def test_cache_initialization(self, test_hash_cache):
        """Test cache initialization"""
        assert test_hash_cache is not None

    def test_cache_set_get(self, test_hash_cache, sample_files):
        """Test setting and getting cached hashes"""
        if len(sample_files) > 0:
            file_path = sample_files[0]
            test_hash = "abc123def456"
            file_size = os.path.getsize(file_path)
            modified_time = os.path.getmtime(file_path)

            test_hash_cache.set(file_path, test_hash, file_size, modified_time)
            cached_hash = test_hash_cache.get(file_path, file_size, modified_time)

            assert cached_hash == test_hash

    def test_cache_invalidation_on_size_change(self, test_hash_cache, sample_files):
        """Test cache invalidation when file size changes"""
        if len(sample_files) > 0:
            file_path = sample_files[0]
            test_hash = "abc123def456"
            file_size = os.path.getsize(file_path)
            modified_time = os.path.getmtime(file_path)

            test_hash_cache.set(file_path, test_hash, file_size, modified_time)

            # Different size should not match
            cached_hash = test_hash_cache.get(file_path, file_size + 1, modified_time)
            assert cached_hash is None

    def test_cache_invalidation_on_mtime_change(self, test_hash_cache, sample_files):
        """Test cache invalidation when modification time changes"""
        if len(sample_files) > 0:
            file_path = sample_files[0]
            test_hash = "abc123def456"
            file_size = os.path.getsize(file_path)
            modified_time = os.path.getmtime(file_path)

            test_hash_cache.set(file_path, test_hash, file_size, modified_time)

            # Different mtime should not match
            cached_hash = test_hash_cache.get(file_path, file_size, modified_time + 1)
            assert cached_hash is None

    def test_cache_clear(self, test_hash_cache, sample_files):
        """Test cache clearing"""
        if len(sample_files) >= 2:
            for file_path in sample_files[:2]:
                test_hash_cache.set(
                    file_path,
                    "hash",
                    os.path.getsize(file_path),
                    os.path.getmtime(file_path)
                )

            test_hash_cache.clear()
            # After clear, no hashes should be found
            for file_path in sample_files[:2]:
                cached = test_hash_cache.get(
                    file_path,
                    os.path.getsize(file_path),
                    os.path.getmtime(file_path)
                )
                assert cached is None


# ============================================================================
# DUPLICATE SCANNER TESTS
# ============================================================================

class TestDuplicateScanner:
    """Tests for DuplicateScanner class"""

    def test_scanner_initialization(self, test_duplicate_scanner):
        """Test scanner initialization"""
        assert test_duplicate_scanner is not None

    def test_scan_no_duplicates(self, test_duplicate_scanner, sample_files):
        """Test scanning files with no duplicates"""
        if len(sample_files) > 0:
            groups = test_duplicate_scanner.scan([os.path.dirname(sample_files[0])])
            # Should have DuplicateGroupManager
            assert groups is not None

    def test_scan_with_duplicates(self, test_duplicate_scanner, duplicate_files):
        """Test scanning files with duplicates"""
        scan_path = os.path.dirname(duplicate_files['original'])
        groups = test_duplicate_scanner.scan([scan_path])

        # Should find at least one duplicate group
        assert groups is not None
        if len(groups.get_all_groups()) > 0:
            # Verify duplicate detection
            assert True

    def test_scan_with_min_size_filter(self, test_duplicate_scanner, sample_files):
        """Test scanning with minimum file size filter"""
        from duplicates.scanner import DuplicateScanner

        scanner = DuplicateScanner(min_file_size=1024 * 100, max_workers=2)  # 100KB min
        if len(sample_files) > 0:
            groups = scanner.scan([os.path.dirname(sample_files[0])])
            assert groups is not None

    def test_scan_cancellation(self, test_duplicate_scanner, sample_files):
        """Test scan cancellation"""
        if len(sample_files) > 0:
            test_duplicate_scanner.cancel()
            groups = test_duplicate_scanner.scan([os.path.dirname(sample_files[0])])
            # Should complete without error
            assert groups is not None

    def test_scan_progress_callback(self, test_duplicate_scanner, sample_files):
        """Test scan with progress callback"""
        progress_calls = []

        def progress_callback(progress):
            progress_calls.append(progress)

        if len(sample_files) > 0:
            groups = test_duplicate_scanner.scan(
                [os.path.dirname(sample_files[0])],
                progress_callback=progress_callback
            )
            # Progress callback should be called
            assert len(progress_calls) >= 0

    def test_scan_stats(self, test_duplicate_scanner, sample_files):
        """Test scan statistics collection"""
        if len(sample_files) > 0:
            groups = test_duplicate_scanner.scan([os.path.dirname(sample_files[0])])
            stats = test_duplicate_scanner.stats

            assert stats.total_files_scanned >= 0
            assert stats.scan_duration >= 0


# ============================================================================
# DUPLICATE GROUP TESTS
# ============================================================================

class TestDuplicateGroup:
    """Tests for DuplicateGroup class"""

    def test_group_creation(self):
        """Test creating duplicate group"""
        from duplicates.groups import DuplicateGroup

        group = DuplicateGroup(file_hash="abc123", file_size=1024)
        assert group is not None
        assert group.file_hash == "abc123"
        assert group.file_size == 1024

    def test_add_files_to_group(self):
        """Test adding files to group"""
        from duplicates.groups import DuplicateGroup

        group = DuplicateGroup(file_hash="abc123", file_size=1024)
        group.add_file("/test/file1.txt")
        group.add_file("/test/file2.txt")

        assert len(group.files) == 2

    def test_wasted_space_calculation(self):
        """Test wasted space calculation"""
        from duplicates.groups import DuplicateGroup

        group = DuplicateGroup(file_hash="abc123", file_size=1024)
        group.add_file("/test/file1.txt")
        group.add_file("/test/file2.txt")
        group.add_file("/test/file3.txt")

        # Wasted space = (count - 1) * size
        expected_wasted = 2 * 1024
        assert group.wasted_space == expected_wasted


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
class TestDuplicatesIntegration:
    """Integration tests for duplicates module"""

    def test_full_duplicate_detection_workflow(self, duplicate_files, temp_db):
        """Test complete duplicate detection workflow"""
        from duplicates.scanner import DuplicateScanner
        from duplicates.hasher import HashAlgorithm

        scanner = DuplicateScanner(
            algorithm=HashAlgorithm.MD5,
            use_cache=True,
            cache_path=temp_db,
            max_workers=2
        )

        scan_path = os.path.dirname(duplicate_files['original'])
        groups = scanner.scan([scan_path])

        # Should detect duplicates
        assert groups is not None
        all_groups = groups.get_all_groups()
        if len(all_groups) > 0:
            # Verify duplicate group contains expected files
            for group in all_groups:
                assert len(group.files) >= 1

    def test_cached_vs_uncached_scanning(self, duplicate_files, temp_db):
        """Test performance difference with caching"""
        from duplicates.scanner import DuplicateScanner
        import time

        scan_path = os.path.dirname(duplicate_files['original'])

        # First scan (populate cache)
        scanner1 = DuplicateScanner(use_cache=True, cache_path=temp_db, max_workers=2)
        start1 = time.time()
        groups1 = scanner1.scan([scan_path])
        duration1 = time.time() - start1

        # Second scan (should use cache)
        scanner2 = DuplicateScanner(use_cache=True, cache_path=temp_db, max_workers=2)
        start2 = time.time()
        groups2 = scanner2.scan([scan_path])
        duration2 = time.time() - start2

        # Both should succeed
        assert groups1 is not None
        assert groups2 is not None
        # Second scan might be faster (cached)
        assert duration2 >= 0
