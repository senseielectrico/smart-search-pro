"""
Comprehensive test suite for file operations module.
"""

import os
import sys
import tempfile
import shutil
import time
from pathlib import Path

# Set UTF-8 encoding for console output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from operations.manager import OperationsManager, OperationPriority, OperationType
from operations.copier import FileCopier
from operations.mover import FileMover
from operations.verifier import FileVerifier, HashAlgorithm
from operations.conflicts import ConflictResolver, ConflictAction
from operations.progress import ProgressTracker


class TestOperations:
    """Test suite for file operations."""

    @staticmethod
    def create_test_file(path: str, size: int = 1024) -> str:
        """Create a test file with random content."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(os.urandom(size))
        return path

    @staticmethod
    def test_copier_basic():
        """Test basic file copying."""
        print("\nTest: FileCopier - Basic Copy")

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            source = os.path.join(temp_dir, "source.txt")
            dest = os.path.join(temp_dir, "dest.txt")
            TestOperations.create_test_file(source, 1024 * 1024)  # 1MB

            # Copy file
            copier = FileCopier()
            copier.start()

            success, error = copier.copy_file_with_retry(source, dest)

            assert success, f"Copy failed: {error}"
            assert os.path.exists(dest), "Destination file not created"
            assert os.path.getsize(source) == os.path.getsize(dest), "Size mismatch"

            copier.shutdown()
            print("✓ Basic copy successful")

    @staticmethod
    def test_copier_batch():
        """Test batch file copying."""
        print("\nTest: FileCopier - Batch Copy")

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple test files
            file_pairs = []
            for i in range(10):
                source = os.path.join(temp_dir, f"source_{i}.txt")
                dest = os.path.join(temp_dir, f"dest_{i}.txt")
                TestOperations.create_test_file(source, 100 * 1024)  # 100KB
                file_pairs.append((source, dest))

            # Copy all files
            with FileCopier(max_workers=4) as copier:
                results = copier.copy_files_batch(file_pairs)

                # Verify all succeeded
                for dest, (success, error) in results.items():
                    assert success, f"Copy failed for {dest}: {error}"
                    assert os.path.exists(dest), f"Destination not created: {dest}"

            print(f"✓ Batch copy successful ({len(file_pairs)} files)")

    @staticmethod
    def test_copier_progress():
        """Test copy progress tracking."""
        print("\nTest: FileCopier - Progress Tracking")

        with tempfile.TemporaryDirectory() as temp_dir:
            source = os.path.join(temp_dir, "large.bin")
            dest = os.path.join(temp_dir, "large_copy.bin")
            TestOperations.create_test_file(source, 10 * 1024 * 1024)  # 10MB

            progress_updates = []

            def progress_callback(copied, total):
                progress_updates.append((copied, total))

            copier = FileCopier()
            copier.start()
            success, error = copier.copy_file_with_retry(
                source,
                dest,
                progress_callback=progress_callback
            )

            assert success, f"Copy failed: {error}"
            assert len(progress_updates) > 0, "No progress updates"
            assert progress_updates[-1][0] == progress_updates[-1][1], "Final progress mismatch"

            copier.shutdown()
            print(f"✓ Progress tracking successful ({len(progress_updates)} updates)")

    @staticmethod
    def test_mover_same_volume():
        """Test moving files on same volume."""
        print("\nTest: FileMover - Same Volume Move")

        with tempfile.TemporaryDirectory() as temp_dir:
            source = os.path.join(temp_dir, "source.txt")
            dest = os.path.join(temp_dir, "moved.txt")
            TestOperations.create_test_file(source, 1024)

            mover = FileMover()
            success, error = mover.move_file(source, dest)

            assert success, f"Move failed: {error}"
            assert os.path.exists(dest), "Destination not created"
            assert not os.path.exists(source), "Source not deleted"

            print("✓ Same volume move successful")

    @staticmethod
    def test_verifier_hash():
        """Test file hash verification."""
        print("\nTest: FileVerifier - Hash Calculation")

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test.bin")
            TestOperations.create_test_file(test_file, 1024 * 1024)  # 1MB

            # Test different algorithms
            algorithms = [
                HashAlgorithm.CRC32,
                HashAlgorithm.MD5,
                HashAlgorithm.SHA256,
            ]

            for algo in algorithms:
                verifier = FileVerifier(algorithm=algo)
                hash1 = verifier.calculate_hash(test_file)
                hash2 = verifier.calculate_hash(test_file)

                assert hash1 == hash2, f"{algo.value} hash mismatch"
                assert len(hash1) > 0, f"{algo.value} hash empty"

                print(f"  ✓ {algo.value}: {hash1}")

    @staticmethod
    def test_verifier_copy():
        """Test copy verification."""
        print("\nTest: FileVerifier - Copy Verification")

        with tempfile.TemporaryDirectory() as temp_dir:
            source = os.path.join(temp_dir, "source.bin")
            dest = os.path.join(temp_dir, "dest.bin")
            TestOperations.create_test_file(source, 1024 * 1024)

            # Copy file
            shutil.copy2(source, dest)

            # Verify
            verifier = FileVerifier()
            is_valid, error = verifier.verify_copy(source, dest)

            assert is_valid, f"Verification failed: {error}"
            print("✓ Copy verification successful")

    @staticmethod
    def test_conflict_resolver():
        """Test conflict resolution."""
        print("\nTest: ConflictResolver")

        with tempfile.TemporaryDirectory() as temp_dir:
            existing_file = os.path.join(temp_dir, "file.txt")
            TestOperations.create_test_file(existing_file, 1024)

            resolver = ConflictResolver(default_action=ConflictAction.RENAME)

            # Test rename
            resolution = resolver.resolve("source.txt", existing_file)
            assert resolution.action == ConflictAction.RENAME
            assert resolution.new_path != existing_file
            assert not os.path.exists(resolution.new_path)

            print(f"✓ Conflict resolution: {existing_file} -> {resolution.new_path}")

    @staticmethod
    def test_progress_tracker():
        """Test progress tracking system."""
        print("\nTest: ProgressTracker")

        tracker = ProgressTracker()

        # Start operation
        files = ["file1.txt", "file2.txt", "file3.txt"]
        sizes = [1024, 2048, 4096]

        progress = tracker.start_operation("test-op", files, sizes)

        # Update progress
        tracker.update_file("test-op", "file1.txt", 512)
        tracker.update_file("test-op", "file2.txt", 1024)

        # Get progress
        current = tracker.get_progress("test-op")
        assert current is not None
        assert current.copied_size == 512 + 1024
        assert current.progress_percent > 0

        # Complete files
        tracker.complete_file("test-op", "file1.txt")
        tracker.complete_file("test-op", "file2.txt")
        tracker.complete_file("test-op", "file3.txt", error="Test error")

        current = tracker.get_progress("test-op")
        assert current.completed_files == 3
        assert current.failed_files == 1

        print(f"✓ Progress tracking: {current.progress_percent:.1f}% complete")

    @staticmethod
    def test_operations_manager():
        """Test operations manager."""
        print("\nTest: OperationsManager")

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = OperationsManager(max_concurrent_operations=2)

            # Create test files
            sources = []
            dests = []
            for i in range(5):
                source = os.path.join(temp_dir, f"src_{i}.txt")
                dest = os.path.join(temp_dir, f"dst_{i}.txt")
                TestOperations.create_test_file(source, 10 * 1024)  # 10KB
                sources.append(source)
                dests.append(dest)

            # Queue copy operation
            op_id = manager.queue_copy(
                sources,
                dests,
                priority=OperationPriority.HIGH
            )

            # Wait for completion
            max_wait = 10  # seconds
            start_time = time.time()
            while time.time() - start_time < max_wait:
                operation = manager.get_operation(op_id)
                if operation and operation.status.value in ['completed', 'failed']:
                    break
                time.sleep(0.1)

            # Check results
            operation = manager.get_operation(op_id)
            assert operation is not None
            assert operation.status.value == 'completed', f"Operation failed: {operation.error}"

            # Verify all files copied
            for dest in dests:
                assert os.path.exists(dest), f"File not copied: {dest}"

            manager.shutdown()
            print(f"✓ Operations manager: {operation.processed_files}/{operation.total_files} files copied")

    @staticmethod
    def test_operations_manager_priority():
        """Test operation priority handling."""
        print("\nTest: OperationsManager - Priority Queue")

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = OperationsManager(max_concurrent_operations=1)

            # Queue operations with different priorities
            operations = []

            for priority in [OperationPriority.LOW, OperationPriority.CRITICAL, OperationPriority.NORMAL]:
                source = os.path.join(temp_dir, f"src_{priority.name}.txt")
                dest = os.path.join(temp_dir, f"dst_{priority.name}.txt")
                TestOperations.create_test_file(source, 1024)

                op_id = manager.queue_copy([source], [dest], priority=priority)
                operations.append((op_id, priority))

            # Wait briefly for processing
            time.sleep(2)

            # Check that critical priority was processed first
            for op_id, priority in operations:
                operation = manager.get_operation(op_id)
                print(f"  {priority.name}: {operation.status.value}")

            manager.shutdown()
            print("✓ Priority queue handling")

    @staticmethod
    def run_all_tests():
        """Run all tests."""
        print("=" * 60)
        print("File Operations Module - Test Suite")
        print("=" * 60)

        tests = [
            TestOperations.test_copier_basic,
            TestOperations.test_copier_batch,
            TestOperations.test_copier_progress,
            TestOperations.test_mover_same_volume,
            TestOperations.test_verifier_hash,
            TestOperations.test_verifier_copy,
            TestOperations.test_conflict_resolver,
            TestOperations.test_progress_tracker,
            TestOperations.test_operations_manager,
            TestOperations.test_operations_manager_priority,
        ]

        passed = 0
        failed = 0

        for test in tests:
            try:
                test()
                passed += 1
            except AssertionError as e:
                print(f"✗ Test failed: {e}")
                failed += 1
            except Exception as e:
                print(f"✗ Test error: {e}")
                failed += 1

        print("\n" + "=" * 60)
        print(f"Results: {passed} passed, {failed} failed")
        print("=" * 60)

        return failed == 0


if __name__ == "__main__":
    success = TestOperations.run_all_tests()
    exit(0 if success else 1)
