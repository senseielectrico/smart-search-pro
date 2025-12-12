"""
Tests for folder comparison module

Run with: python -m pytest comparison/test_comparison.py -v
"""

import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from comparison import (
    FolderComparator,
    ComparisonMode,
    FileStatus,
    SyncEngine,
    ConflictResolution,
    SyncAction
)


@pytest.fixture
def temp_dirs():
    """Create temporary source and target directories."""
    with tempfile.TemporaryDirectory() as source_dir, \
         tempfile.TemporaryDirectory() as target_dir:

        source = Path(source_dir)
        target = Path(target_dir)

        # Create test files in source
        (source / 'same.txt').write_text('same content')
        (source / 'different.txt').write_text('source version')
        (source / 'missing.txt').write_text('only in source')

        # Create subdirectory
        subdir = source / 'subdir'
        subdir.mkdir()
        (subdir / 'nested.txt').write_text('nested file')

        # Create test files in target
        (target / 'same.txt').write_text('same content')
        (target / 'different.txt').write_text('target version')
        (target / 'extra.txt').write_text('only in target')

        yield source, target


class TestFolderComparator:
    """Test FolderComparator class."""

    def test_basic_comparison(self, temp_dirs):
        """Test basic directory comparison."""
        source, target = temp_dirs

        comparator = FolderComparator(mode=ComparisonMode.CONTENT_HASH)
        result = comparator.compare(source, target, recursive=False)

        # Check statistics
        assert result.stats.total_files == 4  # same, different, missing, extra
        assert result.stats.same_files == 1  # same.txt
        assert result.stats.different_files == 1  # different.txt
        assert result.stats.missing_in_target == 1  # missing.txt
        assert result.stats.extra_in_target == 1  # extra.txt

    def test_recursive_comparison(self, temp_dirs):
        """Test recursive directory comparison."""
        source, target = temp_dirs

        comparator = FolderComparator(mode=ComparisonMode.CONTENT_HASH)
        result = comparator.compare(source, target, recursive=True)

        # Should find nested file
        assert result.stats.total_files >= 5  # Including nested.txt

        # Check nested file is missing
        nested_missing = any(
            'nested.txt' in comp.relative_path and
            comp.status == FileStatus.MISSING_IN_TARGET
            for comp in result.comparisons
        )
        assert nested_missing

    def test_size_name_mode(self, temp_dirs):
        """Test size+name comparison mode."""
        source, target = temp_dirs

        comparator = FolderComparator(mode=ComparisonMode.SIZE_NAME)
        result = comparator.compare(source, target, recursive=False)

        # Should detect same file by size
        assert result.stats.same_files >= 1

    def test_name_only_mode(self, temp_dirs):
        """Test name-only comparison mode."""
        source, target = temp_dirs

        comparator = FolderComparator(mode=ComparisonMode.NAME_ONLY)
        result = comparator.compare(source, target, recursive=False)

        # Both same.txt and different.txt exist in both
        assert result.stats.same_files >= 2

    def test_extension_filter(self, temp_dirs):
        """Test extension filtering."""
        source, target = temp_dirs

        # Only .txt files
        comparator = FolderComparator(
            mode=ComparisonMode.CONTENT_HASH,
            extensions=['.txt']
        )
        result = comparator.compare(source, target, recursive=False)

        # All files should be .txt
        for comp in result.comparisons:
            assert comp.relative_path.endswith('.txt')

    def test_size_filter(self, temp_dirs):
        """Test size filtering."""
        source, target = temp_dirs

        # Only files >= 10 bytes
        comparator = FolderComparator(
            mode=ComparisonMode.CONTENT_HASH,
            min_size=10
        )
        result = comparator.compare(source, target, recursive=False)

        # All files should be >= 10 bytes
        for comp in result.comparisons:
            size = comp.source_size or comp.target_size
            assert size >= 10

    def test_get_missing_files(self, temp_dirs):
        """Test getting missing files."""
        source, target = temp_dirs

        comparator = FolderComparator(mode=ComparisonMode.CONTENT_HASH)
        result = comparator.compare(source, target, recursive=False)

        missing = result.get_missing_files()

        # Should find missing.txt
        assert len(missing) == 1
        assert missing[0].relative_path == 'missing.txt'

    def test_get_extra_files(self, temp_dirs):
        """Test getting extra files."""
        source, target = temp_dirs

        comparator = FolderComparator(mode=ComparisonMode.CONTENT_HASH)
        result = comparator.compare(source, target, recursive=False)

        extra = result.get_extra_files()

        # Should find extra.txt
        assert len(extra) == 1
        assert extra[0].relative_path == 'extra.txt'

    def test_get_different_files(self, temp_dirs):
        """Test getting different files."""
        source, target = temp_dirs

        comparator = FolderComparator(mode=ComparisonMode.CONTENT_HASH)
        result = comparator.compare(source, target, recursive=False)

        different = result.get_different_files()

        # Should find different.txt
        assert len(different) == 1
        assert different[0].relative_path == 'different.txt'

    def test_duration_tracking(self, temp_dirs):
        """Test duration tracking."""
        source, target = temp_dirs

        comparator = FolderComparator(mode=ComparisonMode.CONTENT_HASH)
        result = comparator.compare(source, target, recursive=False)

        # Should have positive duration
        assert result.duration > 0


class TestSyncEngine:
    """Test SyncEngine class."""

    def test_sync_preview(self, temp_dirs):
        """Test sync preview (dry run)."""
        source, target = temp_dirs

        engine = SyncEngine()
        result = engine.sync(
            source=source,
            target=target,
            copy_missing=True,
            delete_extra=False,
            update_different=False,
            dry_run=True
        )

        # Should have operations
        assert result.total_operations > 0

        # But nothing should be executed
        assert result.successful_operations == 0

        # Files should still be missing
        assert not (target / 'missing.txt').exists()

    def test_copy_missing(self, temp_dirs):
        """Test copying missing files."""
        source, target = temp_dirs

        engine = SyncEngine()
        result = engine.sync(
            source=source,
            target=target,
            copy_missing=True,
            delete_extra=False,
            update_different=False,
            dry_run=False
        )

        # Should have copied missing.txt
        assert (target / 'missing.txt').exists()
        assert (target / 'missing.txt').read_text() == 'only in source'

        # Should have successful operations
        assert result.successful_operations > 0

    def test_delete_extra(self, temp_dirs):
        """Test deleting extra files."""
        source, target = temp_dirs

        engine = SyncEngine()
        result = engine.sync(
            source=source,
            target=target,
            copy_missing=False,
            delete_extra=True,
            update_different=False,
            dry_run=False
        )

        # Should have deleted extra.txt
        assert not (target / 'extra.txt').exists()

    def test_conflict_resolution_newer_wins(self, temp_dirs):
        """Test newer wins conflict resolution."""
        source, target = temp_dirs

        # Make source file newer
        (source / 'different.txt').write_text('newer source')

        engine = SyncEngine(conflict_resolution=ConflictResolution.NEWER_WINS)
        result = engine.sync(
            source=source,
            target=target,
            update_different=True,
            dry_run=True
        )

        # Should have update operation
        update_ops = [
            op for op in result.operations
            if op.action == SyncAction.UPDATE_TARGET
        ]
        assert len(update_ops) > 0

    def test_conflict_resolution_source_wins(self, temp_dirs):
        """Test source wins conflict resolution."""
        source, target = temp_dirs

        engine = SyncEngine(conflict_resolution=ConflictResolution.SOURCE_WINS)
        result = engine.sync(
            source=source,
            target=target,
            update_different=True,
            dry_run=True
        )

        # Should always prefer source
        update_ops = [
            op for op in result.operations
            if op.action == SyncAction.UPDATE_TARGET
        ]
        # Should have operation to update different.txt
        assert any('different.txt' in op.relative_path for op in update_ops)

    def test_operation_logging(self, temp_dirs):
        """Test operation logging."""
        source, target = temp_dirs

        engine = SyncEngine()
        result = engine.sync(
            source=source,
            target=target,
            copy_missing=True,
            dry_run=False
        )

        # Get logged operations
        operations = engine.get_undo_operations(limit=10)

        # Should have logged operations
        assert len(operations) > 0

        # Check operation structure
        op = operations[0]
        assert 'timestamp' in op
        assert 'action' in op
        assert 'relative_path' in op

    def test_bytes_transferred(self, temp_dirs):
        """Test bytes transferred tracking."""
        source, target = temp_dirs

        engine = SyncEngine()
        result = engine.sync(
            source=source,
            target=target,
            copy_missing=True,
            dry_run=False
        )

        # Should have transferred bytes
        assert result.total_bytes_transferred > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_directories(self):
        """Test comparison of empty directories."""
        with tempfile.TemporaryDirectory() as source_dir, \
             tempfile.TemporaryDirectory() as target_dir:

            source = Path(source_dir)
            target = Path(target_dir)

            comparator = FolderComparator(mode=ComparisonMode.CONTENT_HASH)
            result = comparator.compare(source, target)

            # Should have no files
            assert result.stats.total_files == 0

    def test_nonexistent_source(self):
        """Test error handling for nonexistent source."""
        with tempfile.TemporaryDirectory() as target_dir:
            target = Path(target_dir)
            source = Path('/nonexistent/path')

            comparator = FolderComparator(mode=ComparisonMode.CONTENT_HASH)
            result = comparator.compare(source, target)

            # Should have error
            assert result.error is not None

    def test_same_directory(self):
        """Test comparing directory with itself."""
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / 'file.txt').write_text('content')

            comparator = FolderComparator(mode=ComparisonMode.CONTENT_HASH)
            result = comparator.compare(directory, directory)

            # All files should be same
            assert result.stats.same_files == result.stats.total_files


def test_integration():
    """Test complete workflow."""
    with tempfile.TemporaryDirectory() as source_dir, \
         tempfile.TemporaryDirectory() as target_dir:

        source = Path(source_dir)
        target = Path(target_dir)

        # Create test files
        (source / 'file1.txt').write_text('content 1')
        (source / 'file2.txt').write_text('content 2')
        (target / 'file1.txt').write_text('content 1')

        # 1. Compare
        comparator = FolderComparator(mode=ComparisonMode.CONTENT_HASH)
        comparison_result = comparator.compare(source, target)

        assert comparison_result.stats.same_files == 1
        assert comparison_result.stats.missing_in_target == 1

        # 2. Preview sync
        engine = SyncEngine()
        sync_preview = engine.sync(
            source=source,
            target=target,
            copy_missing=True,
            dry_run=True
        )

        assert sync_preview.total_operations == 1

        # 3. Execute sync
        sync_result = engine.sync(
            source=source,
            target=target,
            copy_missing=True,
            dry_run=False
        )

        assert sync_result.successful_operations == 1
        assert (target / 'file2.txt').exists()

        # 4. Verify sync
        verify_result = comparator.compare(source, target)
        assert verify_result.stats.missing_in_target == 0
        assert verify_result.stats.same_files == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
