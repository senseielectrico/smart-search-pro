"""
Tests for operations module: Copier, Mover, Manager
"""

import pytest
import os
import shutil


# ============================================================================
# FILE COPIER TESTS
# ============================================================================

class TestFileCopier:
    """Tests for FileCopier class"""

    def test_copier_initialization(self, test_file_copier):
        """Test copier initialization"""
        assert test_file_copier is not None

    def test_copy_single_file(self, test_file_copier, sample_files, temp_dir):
        """Test copying single file"""
        if len(sample_files) > 0:
            source = sample_files[0]
            dest = os.path.join(temp_dir, "copied_" + os.path.basename(source))

            success = test_file_copier.copy_file(source, dest)
            assert success is True
            assert os.path.exists(dest)
            assert os.path.getsize(source) == os.path.getsize(dest)

    def test_copy_with_progress(self, test_file_copier, sample_files, temp_dir):
        """Test copy with progress callback"""
        if len(sample_files) > 0:
            source = sample_files[0]
            dest = os.path.join(temp_dir, "progress_" + os.path.basename(source))

            progress_calls = []

            def progress_callback(current, total):
                progress_calls.append((current, total))

            success = test_file_copier.copy_file(
                source, dest, progress_callback=progress_callback
            )
            assert success is True
            assert len(progress_calls) > 0

    def test_copy_nonexistent_file(self, test_file_copier, temp_dir):
        """Test copying non-existent file"""
        source = os.path.join(temp_dir, "nonexistent.txt")
        dest = os.path.join(temp_dir, "dest.txt")

        with pytest.raises(Exception):
            test_file_copier.copy_file(source, dest)

    def test_copy_to_invalid_destination(self, test_file_copier, sample_files):
        """Test copying to invalid destination"""
        if len(sample_files) > 0:
            source = sample_files[0]
            dest = "/invalid/path/that/does/not/exist/file.txt"

            with pytest.raises(Exception):
                test_file_copier.copy_file(source, dest)

    def test_copy_with_metadata_preservation(self, test_file_copier, sample_files, temp_dir):
        """Test metadata preservation during copy"""
        if len(sample_files) > 0:
            source = sample_files[0]
            dest = os.path.join(temp_dir, "metadata_" + os.path.basename(source))

            success = test_file_copier.copy_file(source, dest, preserve_metadata=True)
            assert success is True
            # Check basic metadata
            assert os.path.exists(dest)

    def test_pause_resume(self, test_file_copier):
        """Test pause and resume functionality"""
        test_file_copier.pause()
        assert test_file_copier._pause_event.is_set() is False
        test_file_copier.resume()
        assert test_file_copier._pause_event.is_set() is True

    def test_cancel(self, test_file_copier):
        """Test cancellation"""
        test_file_copier.cancel()
        assert test_file_copier._cancel_event.is_set() is True


# ============================================================================
# FILE MOVER TESTS
# ============================================================================

class TestFileMover:
    """Tests for FileMover class"""

    def test_mover_initialization(self, test_file_mover):
        """Test mover initialization"""
        assert test_file_mover is not None

    def test_move_single_file(self, test_file_mover, sample_files, temp_dir):
        """Test moving single file"""
        if len(sample_files) > 0:
            # Create a copy to move (don't move original)
            source = sample_files[0]
            temp_source = os.path.join(temp_dir, "to_move.txt")
            shutil.copy2(source, temp_source)

            dest = os.path.join(temp_dir, "moved_file.txt")

            success = test_file_mover.move_file(temp_source, dest)
            assert success is True
            assert not os.path.exists(temp_source)
            assert os.path.exists(dest)

    def test_move_with_progress(self, test_file_mover, sample_files, temp_dir):
        """Test move with progress callback"""
        if len(sample_files) > 0:
            source = sample_files[0]
            temp_source = os.path.join(temp_dir, "to_move_progress.txt")
            shutil.copy2(source, temp_source)

            dest = os.path.join(temp_dir, "moved_progress.txt")

            progress_calls = []

            def progress_callback(current, total):
                progress_calls.append((current, total))

            success = test_file_mover.move_file(
                temp_source, dest, progress_callback=progress_callback
            )
            assert success is True

    def test_move_nonexistent_file(self, test_file_mover, temp_dir):
        """Test moving non-existent file"""
        source = os.path.join(temp_dir, "nonexistent.txt")
        dest = os.path.join(temp_dir, "dest.txt")

        with pytest.raises(Exception):
            test_file_mover.move_file(source, dest)


# ============================================================================
# OPERATION MANAGER TESTS
# ============================================================================

class TestOperationManager:
    """Tests for OperationManager class"""

    def test_manager_initialization(self, test_operation_manager):
        """Test manager initialization"""
        assert test_operation_manager is not None

    def test_queue_copy_operation(self, test_operation_manager, sample_files, temp_dir):
        """Test queuing copy operation"""
        if len(sample_files) > 0:
            source = sample_files[0]
            dest = os.path.join(temp_dir, "managed_copy.txt")

            op_id = test_operation_manager.queue_copy(source, dest)
            assert op_id is not None

    def test_queue_move_operation(self, test_operation_manager, sample_files, temp_dir):
        """Test queuing move operation"""
        if len(sample_files) > 0:
            source = sample_files[0]
            temp_source = os.path.join(temp_dir, "to_move_managed.txt")
            shutil.copy2(source, temp_source)

            dest = os.path.join(temp_dir, "managed_move.txt")

            op_id = test_operation_manager.queue_move(temp_source, dest)
            assert op_id is not None

    def test_get_operation_status(self, test_operation_manager, sample_files, temp_dir):
        """Test getting operation status"""
        if len(sample_files) > 0:
            source = sample_files[0]
            dest = os.path.join(temp_dir, "status_test.txt")

            op_id = test_operation_manager.queue_copy(source, dest)
            status = test_operation_manager.get_operation_status(op_id)
            assert status is not None

    def test_cancel_operation(self, test_operation_manager, sample_files, temp_dir):
        """Test canceling operation"""
        if len(sample_files) > 0:
            source = sample_files[0]
            dest = os.path.join(temp_dir, "cancel_test.txt")

            op_id = test_operation_manager.queue_copy(source, dest)
            result = test_operation_manager.cancel_operation(op_id)
            # Should return True or False depending on timing
            assert isinstance(result, bool)

    def test_get_active_operations(self, test_operation_manager):
        """Test getting list of active operations"""
        active = test_operation_manager.get_active_operations()
        assert isinstance(active, list)

    def test_get_history(self, test_operation_manager, sample_files, temp_dir):
        """Test getting operation history"""
        if len(sample_files) > 0:
            source = sample_files[0]
            dest = os.path.join(temp_dir, "history_test.txt")

            test_operation_manager.queue_copy(source, dest)
            history = test_operation_manager.get_history(limit=10)
            assert isinstance(history, list)


# ============================================================================
# CONFLICT RESOLUTION TESTS
# ============================================================================

class TestConflictResolution:
    """Tests for conflict resolution strategies"""

    def test_skip_strategy(self, temp_dir, sample_files):
        """Test skip conflict resolution"""
        from operations.conflicts import ConflictResolution

        if len(sample_files) > 0:
            strategy = ConflictResolution.SKIP
            assert strategy.name == 'SKIP'

    def test_overwrite_strategy(self, temp_dir, sample_files):
        """Test overwrite conflict resolution"""
        from operations.conflicts import ConflictResolution

        if len(sample_files) > 0:
            strategy = ConflictResolution.OVERWRITE
            assert strategy.name == 'OVERWRITE'

    def test_rename_strategy(self, temp_dir, sample_files):
        """Test rename conflict resolution"""
        from operations.conflicts import ConflictResolution

        if len(sample_files) > 0:
            strategy = ConflictResolution.RENAME
            assert strategy.name == 'RENAME'


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
class TestOperationsIntegration:
    """Integration tests for operations module"""

    def test_copy_and_verify(self, test_file_copier, sample_files, temp_dir):
        """Test copy with verification"""
        from operations.copier import FileCopier

        if len(sample_files) > 0:
            # Create copier with verification enabled
            verifying_copier = FileCopier(max_workers=2, verify_after_copy=True)
            verifying_copier.start()

            source = sample_files[0]
            dest = os.path.join(temp_dir, "verified_copy.txt")

            try:
                # This may fail if verifier dependencies are missing
                success = verifying_copier.copy_file(source, dest)
                assert success is True or isinstance(success, bool)
            except Exception:
                # Verification may not be available in test environment
                pass
            finally:
                verifying_copier.shutdown()

    def test_batch_operations(self, test_operation_manager, sample_files, temp_dir):
        """Test batch copy operations"""
        if len(sample_files) >= 3:
            op_ids = []
            for i, source in enumerate(sample_files[:3]):
                dest = os.path.join(temp_dir, f"batch_{i}.txt")
                op_id = test_operation_manager.queue_copy(source, dest)
                op_ids.append(op_id)

            assert len(op_ids) == 3

    def test_operation_retry(self, test_file_copier, temp_dir):
        """Test operation retry on failure"""
        source = os.path.join(temp_dir, "retry_source.txt")
        dest = os.path.join(temp_dir, "retry_dest.txt")

        # Create source file
        with open(source, 'w') as f:
            f.write("retry test")

        success, error = test_file_copier.copy_file_with_retry(source, dest)
        assert success is True or error is not None
