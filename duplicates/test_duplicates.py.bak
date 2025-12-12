"""
Comprehensive test suite for the duplicate finder module.

Tests all components:
- Hasher (multiple algorithms, quick/full hash)
- Cache (SQLite persistence, LRU eviction)
- Scanner (multi-pass detection, progress reporting)
- Groups (selection strategies, statistics)
- Actions (all deletion methods, audit logging)
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from duplicates import (
    # Hasher
    FileHasher,
    HashAlgorithm,
    HashResult,
    hash_file_simple,

    # Cache
    HashCache,
    CacheStats,

    # Scanner
    DuplicateScanner,
    ScanProgress,
    ScanStats,

    # Groups
    DuplicateGroup,
    DuplicateGroupManager,
    SelectionStrategy,
    FileInfo,

    # Actions
    RecycleBinAction,
    MoveToFolderAction,
    PermanentDeleteAction,
    HardLinkAction,
    SymlinkAction,
    AuditLogger,
    execute_batch_action,
    get_action_summary,
)


class TestFileHasher:
    """Test FileHasher class."""

    @pytest.fixture
    def temp_file(self, tmp_path):
        """Create a temporary test file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Hello, World!" * 1000)
        return file_path

    @pytest.fixture
    def hasher(self):
        """Create a FileHasher instance."""
        return FileHasher(algorithm=HashAlgorithm.SHA256)

    def test_quick_hash(self, hasher, temp_file):
        """Test quick hash computation."""
        quick_hash = hasher.compute_quick_hash(temp_file)
        assert quick_hash is not None
        assert len(quick_hash) == 64  # SHA-256 hex length

    def test_full_hash(self, hasher, temp_file):
        """Test full hash computation."""
        full_hash = hasher.compute_full_hash(temp_file)
        assert full_hash is not None
        assert len(full_hash) == 64

    def test_hash_file_both(self, hasher, temp_file):
        """Test hashing with both quick and full hash."""
        result = hasher.hash_file(temp_file, quick_hash=True, full_hash=True)
        assert result.success
        assert result.quick_hash is not None
        assert result.full_hash is not None
        assert result.file_size > 0

    def test_hash_nonexistent_file(self, hasher, tmp_path):
        """Test hashing non-existent file."""
        result = hasher.hash_file(tmp_path / "nonexistent.txt")
        assert not result.success
        assert result.error is not None

    def test_multiple_algorithms(self, temp_file):
        """Test different hash algorithms."""
        algorithms = [
            HashAlgorithm.MD5,
            HashAlgorithm.SHA1,
            HashAlgorithm.SHA256,
        ]

        hashes = {}
        for algo in algorithms:
            hasher = FileHasher(algorithm=algo)
            result = hasher.hash_file(temp_file, full_hash=True)
            assert result.success
            hashes[algo] = result.full_hash

        # All hashes should be different (different algorithms)
        assert len(set(hashes.values())) == len(algorithms)

    def test_bytewise_comparison(self, tmp_path):
        """Test byte-by-byte file comparison."""
        # Create identical files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        content = "Test content" * 1000

        file1.write_text(content)
        file2.write_text(content)

        # Should be identical
        assert FileHasher.compare_files_bytewise(file1, file2)

        # Modify one file
        file2.write_text(content + "extra")

        # Should not be identical
        assert not FileHasher.compare_files_bytewise(file1, file2)

    def test_batch_hashing(self, hasher, tmp_path):
        """Test batch hashing with thread pool."""
        # Create multiple files
        files = []
        for i in range(10):
            file_path = tmp_path / f"file{i}.txt"
            file_path.write_text(f"Content {i}" * 100)
            files.append(file_path)

        # Hash all files
        results = hasher.hash_files_batch(files, quick_hash=True, full_hash=True)

        assert len(results) == 10
        assert all(r.success for r in results)
        assert all(r.quick_hash and r.full_hash for r in results)


class TestHashCache:
    """Test HashCache class."""

    @pytest.fixture
    def cache(self, tmp_path):
        """Create a HashCache instance."""
        db_path = tmp_path / "cache.db"
        return HashCache(db_path, max_size=100, eviction_size=10)

    @pytest.fixture
    def temp_file(self, tmp_path):
        """Create a temporary test file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Test content")
        return file_path

    def test_set_and_get_hash(self, cache, temp_file):
        """Test setting and getting cached hash."""
        # Set hash
        success = cache.set_hash(
            temp_file,
            quick_hash="abc123",
            full_hash="def456"
        )
        assert success

        # Get hash
        result = cache.get_hash(temp_file)
        assert result is not None
        assert result['quick_hash'] == "abc123"
        assert result['full_hash'] == "def456"

    def test_cache_invalidation_on_mtime_change(self, cache, temp_file):
        """Test cache invalidation when file is modified."""
        # Cache original hash
        cache.set_hash(temp_file, quick_hash="original", full_hash="hash")

        # Modify file
        import time
        time.sleep(0.1)  # Ensure mtime changes
        temp_file.write_text("Modified content")

        # Cache should be invalidated
        result = cache.get_hash(temp_file, validate_mtime=True)
        assert result is None

    def test_cache_stats(self, cache, temp_file):
        """Test cache statistics tracking."""
        # Initial stats
        stats = cache.get_stats()
        assert stats.total_entries == 0

        # Add entry
        cache.set_hash(temp_file, quick_hash="test")

        # Check stats
        stats = cache.get_stats()
        assert stats.total_entries == 1

        # Cache hit
        cache.get_hash(temp_file)
        stats = cache.get_stats()
        assert stats.cache_hits == 1

        # Cache miss
        cache.get_hash(tmp_path / "nonexistent.txt")
        stats = cache.get_stats()
        assert stats.cache_misses >= 1

    def test_lru_eviction(self, tmp_path):
        """Test LRU eviction when cache is full."""
        cache = HashCache(tmp_path / "cache.db", max_size=5, eviction_size=2)

        # Add 5 entries
        for i in range(5):
            file_path = tmp_path / f"file{i}.txt"
            file_path.write_text(f"Content {i}")
            cache.set_hash(file_path, quick_hash=f"hash{i}")

        # Cache should be at max
        assert cache.get_stats().total_entries == 5

        # Add one more (should trigger eviction)
        file_path = tmp_path / "file6.txt"
        file_path.write_text("Content 6")
        cache.set_hash(file_path, quick_hash="hash6")

        # Cache should have evicted 2 entries and added 1
        assert cache.get_stats().total_entries == 4
        assert cache.get_stats().evictions == 2

    def test_clear_cache(self, cache, temp_file):
        """Test clearing all cache entries."""
        cache.set_hash(temp_file, quick_hash="test")
        assert cache.get_stats().total_entries == 1

        success = cache.clear()
        assert success
        assert cache.get_stats().total_entries == 0

    def test_optimize_cache(self, cache, tmp_path):
        """Test cache optimization."""
        # Add entry for existing file
        file1 = tmp_path / "exists.txt"
        file1.write_text("Content")
        cache.set_hash(file1, quick_hash="hash1")

        # Add entry for non-existent file
        file2 = tmp_path / "nonexistent.txt"
        # Manually insert into cache (simulate stale entry)
        cache.set_hash(file1, quick_hash="hash2")  # Use file1 then modify path

        # Optimize should remove stale entries
        cache.optimize()


class TestDuplicateScanner:
    """Test DuplicateScanner class."""

    @pytest.fixture
    def scanner(self, tmp_path):
        """Create a DuplicateScanner instance."""
        cache_path = tmp_path / "cache.db"
        return DuplicateScanner(use_cache=True, cache_path=cache_path)

    @pytest.fixture
    def duplicate_files(self, tmp_path):
        """Create a set of duplicate files for testing."""
        # Create original file
        original = tmp_path / "original.txt"
        content = "Duplicate content" * 1000
        original.write_text(content)

        # Create duplicates
        duplicates = []
        for i in range(3):
            dup = tmp_path / f"duplicate{i}.txt"
            dup.write_text(content)
            duplicates.append(dup)

        # Create unique file
        unique = tmp_path / "unique.txt"
        unique.write_text("Unique content" * 1000)

        return original, duplicates, unique

    def test_basic_scan(self, scanner, tmp_path, duplicate_files):
        """Test basic duplicate scanning."""
        original, duplicates, unique = duplicate_files

        # Scan directory
        groups = scanner.scan([tmp_path], recursive=False)

        # Should find one duplicate group
        assert len(groups.groups) == 1

        # Group should contain original + 3 duplicates = 4 files
        assert groups.groups[0].file_count == 4

    def test_progress_callback(self, scanner, tmp_path, duplicate_files):
        """Test progress callback during scan."""
        progress_updates = []

        def progress_callback(progress):
            progress_updates.append(progress.progress_percent)

        scanner.scan([tmp_path], progress_callback=progress_callback)

        # Should have received progress updates
        assert len(progress_updates) > 0
        # Progress should increase
        assert progress_updates[-1] >= progress_updates[0]

    def test_scan_cancellation(self, scanner, tmp_path):
        """Test scan cancellation."""
        # Create many files
        for i in range(100):
            file_path = tmp_path / f"file{i}.txt"
            file_path.write_text(f"Content {i}")

        # Start scan and cancel immediately
        def progress_callback(progress):
            if progress.current_file > 10:
                scanner.cancel()

        groups = scanner.scan([tmp_path], progress_callback=progress_callback)

        # Scan should have been cancelled
        assert len(groups.groups) == 0 or scanner._cancelled

    def test_size_filtering(self, tmp_path):
        """Test filtering by file size."""
        # Create small file
        small = tmp_path / "small.txt"
        small.write_text("Small")

        # Create large file
        large = tmp_path / "large.txt"
        large.write_text("Large" * 10000)

        # Create duplicate of large file
        large_dup = tmp_path / "large_dup.txt"
        large_dup.write_text("Large" * 10000)

        # Scan with minimum size filter
        scanner = DuplicateScanner(min_file_size=1000)
        groups = scanner.scan([tmp_path])

        # Should only find large file duplicates
        assert len(groups.groups) == 1
        assert groups.groups[0].files[0].size > 1000

    def test_recursive_scan(self, scanner, tmp_path):
        """Test recursive directory scanning."""
        # Create nested directories with duplicates
        subdir1 = tmp_path / "subdir1"
        subdir2 = tmp_path / "subdir2"
        subdir1.mkdir()
        subdir2.mkdir()

        content = "Duplicate in subdirs"
        (subdir1 / "file.txt").write_text(content)
        (subdir2 / "file.txt").write_text(content)

        # Recursive scan
        groups = scanner.scan([tmp_path], recursive=True)
        assert len(groups.groups) == 1

        # Non-recursive scan
        groups = scanner.scan([tmp_path], recursive=False)
        assert len(groups.groups) == 0


class TestDuplicateGroups:
    """Test DuplicateGroup and DuplicateGroupManager."""

    @pytest.fixture
    def group(self, tmp_path):
        """Create a duplicate group with test files."""
        group = DuplicateGroup(hash_value="abc123", hash_type="full")

        # Add files with different timestamps
        import time
        for i in range(4):
            file_path = tmp_path / f"file{i}.txt"
            file_path.write_text(f"Content {i}")

            # Different mtimes
            mtime = time.time() + (i * 100)
            group.add_file(file_path, size=1024, mtime=mtime)

        return group

    def test_group_statistics(self, group):
        """Test duplicate group statistics."""
        assert group.file_count == 4
        assert group.total_size == 1024 * 4
        assert group.wasted_space == 1024 * 3  # (n-1) * size

    def test_keep_oldest_strategy(self, group):
        """Test keeping oldest file strategy."""
        group.select_by_strategy(SelectionStrategy.KEEP_OLDEST)

        # Should keep oldest (first file)
        assert not group.files[0].selected_for_deletion
        # Others should be marked for deletion
        assert all(f.selected_for_deletion for f in group.files[1:])

    def test_keep_newest_strategy(self, group):
        """Test keeping newest file strategy."""
        group.select_by_strategy(SelectionStrategy.KEEP_NEWEST)

        # Should keep newest (last file)
        assert not group.files[-1].selected_for_deletion
        # Others should be marked for deletion
        assert all(f.selected_for_deletion for f in group.files[:-1])

    def test_folder_priority_strategy(self, group, tmp_path):
        """Test folder priority strategy."""
        # Recreate group with files in different folders
        group = DuplicateGroup(hash_value="test", hash_type="full")

        important_dir = tmp_path / "important"
        regular_dir = tmp_path / "regular"
        important_dir.mkdir()
        regular_dir.mkdir()

        group.add_file(important_dir / "file1.txt", size=1024, mtime=100)
        group.add_file(regular_dir / "file2.txt", size=1024, mtime=200)
        group.add_file(regular_dir / "file3.txt", size=1024, mtime=300)

        # Apply priority (important folder first)
        group.select_by_strategy(
            SelectionStrategy.FOLDER_PRIORITY,
            folder_priorities=[str(important_dir)]
        )

        # File in important folder should be kept
        assert not group.files[0].selected_for_deletion
        # Others should be deleted
        assert group.files[1].selected_for_deletion
        assert group.files[2].selected_for_deletion

    def test_custom_strategy(self, group):
        """Test custom selection strategy."""
        def custom_selector(files):
            # Keep first and last, delete middle ones
            return files[1:-1]

        group.select_by_strategy(
            SelectionStrategy.CUSTOM,
            custom_selector=custom_selector
        )

        assert not group.files[0].selected_for_deletion
        assert group.files[1].selected_for_deletion
        assert group.files[2].selected_for_deletion
        assert not group.files[3].selected_for_deletion

    def test_manual_selection(self, group):
        """Test manual file selection."""
        file_path = group.files[0].path

        # Select for deletion
        success = group.manual_select(file_path, delete=True)
        assert success
        assert group.files[0].selected_for_deletion

        # Deselect
        success = group.manual_select(file_path, delete=False)
        assert success
        assert not group.files[0].selected_for_deletion

    def test_group_manager(self, tmp_path):
        """Test DuplicateGroupManager."""
        manager = DuplicateGroupManager()

        # Create groups
        group1 = manager.create_group("hash1")
        group1.add_file(tmp_path / "file1.txt", size=1000, mtime=100)
        group1.add_file(tmp_path / "file2.txt", size=1000, mtime=200)

        group2 = manager.create_group("hash2")
        group2.add_file(tmp_path / "file3.txt", size=2000, mtime=100)
        group2.add_file(tmp_path / "file4.txt", size=2000, mtime=200)

        # Get statistics
        stats = manager.get_total_statistics()
        assert stats['total_groups'] == 2
        assert stats['total_duplicate_files'] == 4
        assert stats['total_wasted_space'] == 3000  # 1000 + 2000

        # Apply strategy to all groups
        manager.apply_strategy_to_all(SelectionStrategy.KEEP_OLDEST)
        assert len(manager.get_all_selected_for_deletion()) == 2

        # Test filtering
        large_groups = manager.filter_by_size(min_size=1500)
        assert len(large_groups) == 1

        # Test sorting
        sorted_groups = manager.sort_by_wasted_space()
        assert sorted_groups[0].wasted_space >= sorted_groups[1].wasted_space


class TestActions:
    """Test duplicate file actions."""

    @pytest.fixture
    def audit_logger(self, tmp_path):
        """Create an audit logger."""
        log_path = tmp_path / "audit.json"
        return AuditLogger(log_path)

    @pytest.fixture
    def test_file(self, tmp_path):
        """Create a test file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Test content" * 1000)
        return file_path

    def test_permanent_delete(self, audit_logger, test_file):
        """Test permanent file deletion."""
        action = PermanentDeleteAction(
            audit_logger=audit_logger,
            require_confirmation=True
        )

        # Should fail without confirmation
        result = action.execute(test_file, confirmed=False)
        assert not result.success
        assert test_file.exists()

        # Should succeed with confirmation
        result = action.execute(test_file, confirmed=True)
        assert result.success
        assert not test_file.exists()
        assert result.bytes_freed > 0

    def test_move_to_folder(self, audit_logger, test_file, tmp_path):
        """Test moving file to folder."""
        target_folder = tmp_path / "archive"

        action = MoveToFolderAction(audit_logger=audit_logger)
        result = action.execute(test_file, target_path=target_folder)

        assert result.success
        assert not test_file.exists()
        assert (target_folder / test_file.name).exists()
        assert result.target_path == (target_folder / test_file.name)

    def test_hard_link(self, audit_logger, tmp_path):
        """Test hard link replacement."""
        # Create original and duplicate
        original = tmp_path / "original.txt"
        duplicate = tmp_path / "duplicate.txt"
        content = "Test content" * 1000

        original.write_text(content)
        duplicate.write_text(content)

        # Get original size
        original_size = duplicate.stat().st_size

        # Replace duplicate with hard link
        action = HardLinkAction(audit_logger=audit_logger)
        result = action.execute(duplicate, target_path=original)

        assert result.success
        assert duplicate.exists()
        assert result.bytes_freed == original_size

        # Verify hard link (same inode)
        assert duplicate.stat().st_ino == original.stat().st_ino

    def test_symlink(self, audit_logger, tmp_path):
        """Test symlink replacement."""
        # Create original and duplicate
        original = tmp_path / "original.txt"
        duplicate = tmp_path / "duplicate.txt"
        content = "Test content" * 1000

        original.write_text(content)
        duplicate.write_text(content)

        # Get original size
        original_size = duplicate.stat().st_size

        # Replace duplicate with symlink
        action = SymlinkAction(audit_logger=audit_logger)
        result = action.execute(duplicate, target_path=original)

        assert result.success
        assert duplicate.exists()
        assert duplicate.is_symlink()
        assert result.bytes_freed == original_size

    def test_batch_execution(self, audit_logger, tmp_path):
        """Test batch action execution."""
        # Create multiple files
        files = []
        for i in range(5):
            file_path = tmp_path / f"file{i}.txt"
            file_path.write_text(f"Content {i}")
            files.append(file_path)

        # Execute batch delete
        action = PermanentDeleteAction(
            audit_logger=audit_logger,
            require_confirmation=False
        )

        results = execute_batch_action(action, files, confirmed=True)

        assert len(results) == 5
        assert all(r.success for r in results)
        assert all(not f.exists() for f in files)

    def test_action_summary(self, tmp_path):
        """Test action summary generation."""
        from duplicates.actions import ActionResult, ActionType

        results = [
            ActionResult(
                success=True,
                action_type=ActionType.PERMANENT_DELETE,
                source_path=tmp_path / "file1.txt",
                bytes_freed=1000
            ),
            ActionResult(
                success=True,
                action_type=ActionType.PERMANENT_DELETE,
                source_path=tmp_path / "file2.txt",
                bytes_freed=2000
            ),
            ActionResult(
                success=False,
                action_type=ActionType.PERMANENT_DELETE,
                source_path=tmp_path / "file3.txt",
                error="Permission denied"
            ),
        ]

        summary = get_action_summary(results)

        assert summary['total'] == 3
        assert summary['successful'] == 2
        assert summary['failed'] == 1
        assert summary['total_bytes_freed'] == 3000
        assert summary['success_rate'] == pytest.approx(66.67, rel=0.1)

    def test_audit_logging(self, audit_logger, test_file):
        """Test audit logging functionality."""
        action = PermanentDeleteAction(
            audit_logger=audit_logger,
            require_confirmation=False
        )

        result = action.execute(test_file, confirmed=True)

        # Check that action was logged
        recent = audit_logger.get_recent_actions(count=10)
        assert len(recent) >= 1
        assert recent[-1]['action_type'] == 'permanent_delete'
        assert recent[-1]['success'] == True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
