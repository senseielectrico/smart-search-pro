"""
Test script for TeraCopy-style file operations.
Demonstrates all advanced features including:
- Adaptive buffering
- Hash verification
- Progress tracking with speed and ETA
- Pause/Resume/Cancel
- Queue management
- Large file handling
"""

import os
import sys
import time
import tempfile
from pathlib import Path

# Set UTF-8 encoding for console output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from operations.copier import FileCopier
from operations.mover import FileMover
from operations.manager import OperationsManager, OperationPriority
from operations.verifier import FileVerifier, HashAlgorithm
from operations.progress import ProgressTracker


def create_test_file(path: str, size_mb: int) -> None:
    """Create a test file of specified size."""
    size_bytes = size_mb * 1024 * 1024
    chunk_size = 1024 * 1024  # 1MB chunks

    with open(path, 'wb') as f:
        remaining = size_bytes
        while remaining > 0:
            chunk = min(chunk_size, remaining)
            f.write(os.urandom(chunk))
            remaining -= chunk


def format_size(bytes_val: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"


def format_speed(bytes_per_sec: float) -> str:
    """Format speed to human-readable format."""
    for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
        if bytes_per_sec < 1024.0:
            return f"{bytes_per_sec:.2f} {unit}"
        bytes_per_sec /= 1024.0
    return f"{bytes_per_sec:.2f} TB/s"


def test_adaptive_buffering():
    """Test 1: Adaptive buffer sizing for different file sizes."""
    print("\n" + "="*70)
    print("TEST 1: Adaptive Buffer Sizing")
    print("="*70)

    test_sizes = [
        (500 * 1024, "500 KB"),
        (5 * 1024 * 1024, "5 MB"),
        (50 * 1024 * 1024, "50 MB"),
        (500 * 1024 * 1024, "500 MB"),
        (5 * 1024 * 1024 * 1024, "5 GB"),
        (50 * 1024 * 1024 * 1024, "50 GB"),
    ]

    print("\nBuffer sizes (same drive):")
    for size, label in test_sizes:
        buffer = FileCopier._get_optimal_buffer_size(size, "C:\\test", "C:\\dest")
        print(f"  {label:>10s}: {format_size(buffer):>12s} buffer")

    print("\nBuffer sizes (different drives):")
    for size, label in test_sizes:
        buffer = FileCopier._get_optimal_buffer_size(size, "C:\\test", "D:\\dest")
        print(f"  {label:>10s}: {format_size(buffer):>12s} buffer")


def test_basic_copy_with_progress():
    """Test 2: Basic copy with real-time progress tracking."""
    print("\n" + "="*70)
    print("TEST 2: Copy with Progress Tracking")
    print("="*70)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test file
        source = os.path.join(temp_dir, "test_10mb.bin")
        dest = os.path.join(temp_dir, "copied_10mb.bin")

        print("\nCreating 10MB test file...")
        create_test_file(source, 10)

        # Copy with progress
        print("Copying with progress tracking...")
        start_time = time.time()
        last_update = start_time

        def progress_callback(copied, total):
            nonlocal last_update
            now = time.time()
            if now - last_update >= 0.1:  # Update every 100ms
                percent = (copied / total) * 100
                elapsed = now - start_time
                speed = copied / elapsed if elapsed > 0 else 0

                # Simple progress bar
                bar_width = 30
                filled = int(bar_width * copied / total)
                bar = '█' * filled + '░' * (bar_width - filled)

                print(f"\r  [{bar}] {percent:6.2f}% | "
                      f"{format_speed(speed):>12s} | "
                      f"{format_size(copied)}/{format_size(total)}", end='')
                last_update = now

        with FileCopier(verify_after_copy=False) as copier:
            success = copier.copy_file(source, dest, progress_callback)

        print()  # New line

        if success:
            elapsed = time.time() - start_time
            avg_speed = os.path.getsize(dest) / elapsed
            print(f"\n✓ Copy completed successfully!")
            print(f"  Time: {elapsed:.2f}s")
            print(f"  Average speed: {format_speed(avg_speed)}")
        else:
            print("\n✗ Copy failed!")


def test_hash_verification():
    """Test 3: Copy with hash verification."""
    print("\n" + "="*70)
    print("TEST 3: Hash Verification")
    print("="*70)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test file
        source = os.path.join(temp_dir, "original.bin")
        dest = os.path.join(temp_dir, "verified_copy.bin")

        print("\nCreating 5MB test file...")
        create_test_file(source, 5)

        # Test different hash algorithms
        algorithms = [
            ('crc32', HashAlgorithm.CRC32),
            ('md5', HashAlgorithm.MD5),
            ('sha256', HashAlgorithm.SHA256),
        ]

        for algo_name, algo_enum in algorithms:
            print(f"\nTesting {algo_name.upper()} verification...")

            # Calculate original hash
            verifier = FileVerifier(algorithm=algo_enum)
            original_hash = verifier.calculate_hash(source)
            print(f"  Original hash: {original_hash}")

            # Copy with verification
            start_time = time.time()
            with FileCopier(verify_after_copy=True, verify_algorithm=algo_name) as copier:
                success = copier.copy_file(source, dest)
            elapsed = time.time() - start_time

            if success:
                # Calculate dest hash
                dest_hash = verifier.calculate_hash(dest)
                print(f"  Copy hash:     {dest_hash}")
                print(f"  Match: {'✓' if original_hash == dest_hash else '✗'}")
                print(f"  Time: {elapsed:.2f}s")
            else:
                print(f"  ✗ Copy failed!")

            # Clean up for next test
            if os.path.exists(dest):
                os.remove(dest)


def test_pause_resume_cancel():
    """Test 4: Pause/Resume/Cancel operations."""
    print("\n" + "="*70)
    print("TEST 4: Pause/Resume/Cancel")
    print("="*70)

    with tempfile.TemporaryDirectory() as temp_dir:
        source = os.path.join(temp_dir, "large.bin")
        dest = os.path.join(temp_dir, "copy.bin")

        print("\nCreating 50MB test file...")
        create_test_file(source, 50)

        print("\nTesting pause/resume...")
        copier = FileCopier()
        copier.start()

        paused_at = None
        resumed_at = None

        def progress_callback(copied, total):
            nonlocal paused_at, resumed_at
            percent = (copied / total) * 100

            # Pause at 30%
            if percent >= 30 and paused_at is None:
                paused_at = copied
                print(f"\n  Pausing at {percent:.1f}%...")
                copier.pause()
                time.sleep(1)  # Pause for 1 second
                print("  Resuming...")
                copier.resume()
                resumed_at = copied

            # Simple progress indicator
            if int(percent) % 10 == 0:
                print(f"\r  Progress: {percent:.0f}%", end='')

        success = copier.copy_file(source, dest, progress_callback)
        print()

        if success:
            print(f"✓ Pause/Resume test completed!")
            print(f"  Paused at: {format_size(paused_at)}")
            print(f"  Resumed at: {format_size(resumed_at)}")

        copier.shutdown()


def test_batch_operations():
    """Test 5: Batch file operations with queue."""
    print("\n" + "="*70)
    print("TEST 5: Batch Operations")
    print("="*70)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create multiple test files
        file_pairs = []
        print("\nCreating test files...")

        for i in range(5):
            size_mb = (i + 1) * 2  # 2MB, 4MB, 6MB, 8MB, 10MB
            source = os.path.join(temp_dir, f"file_{i}.bin")
            dest = os.path.join(temp_dir, "backup", f"file_{i}.bin")

            create_test_file(source, size_mb)
            file_pairs.append((source, dest))
            print(f"  Created: file_{i}.bin ({size_mb} MB)")

        # Batch copy
        print("\nCopying files in batch (4 workers)...")
        start_time = time.time()

        with FileCopier(max_workers=4) as copier:
            results = copier.copy_files_batch(file_pairs)

        elapsed = time.time() - start_time

        # Show results
        success_count = sum(1 for success, _ in results.values() if success)
        print(f"\n✓ Batch copy completed!")
        print(f"  Success: {success_count}/{len(file_pairs)} files")
        print(f"  Time: {elapsed:.2f}s")


def test_move_operations():
    """Test 6: Move operations (same/different volumes)."""
    print("\n" + "="*70)
    print("TEST 6: Move Operations")
    print("="*70)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test file
        source = os.path.join(temp_dir, "original.txt")
        dest_same_vol = os.path.join(temp_dir, "subdir", "moved.txt")

        with open(source, 'w') as f:
            f.write("Test content\n" * 10000)

        print("\nTesting same-volume move (instant rename)...")

        with FileMover() as mover:
            strategy = mover.get_move_strategy(source, dest_same_vol)
            print(f"  Strategy: {strategy}")

            start_time = time.time()
            success, error = mover.move_file(source, dest_same_vol)
            elapsed = time.time() - start_time

            if success:
                print(f"  ✓ Move completed in {elapsed:.4f}s")
                print(f"  Source exists: {os.path.exists(source)}")
                print(f"  Dest exists: {os.path.exists(dest_same_vol)}")
            else:
                print(f"  ✗ Move failed: {error}")


def test_operations_manager():
    """Test 7: Operations manager with priorities."""
    print("\n" + "="*70)
    print("TEST 7: Operations Manager with Queue")
    print("="*70)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create manager
        manager = OperationsManager(max_concurrent_operations=2)

        # Create test files
        print("\nCreating test files...")
        files = []
        for i in range(6):
            path = os.path.join(temp_dir, f"file_{i}.bin")
            create_test_file(path, 2)  # 2MB each
            files.append(path)
            print(f"  Created: file_{i}.bin")

        # Queue operations with different priorities
        print("\nQueuing operations...")

        op_high = manager.queue_copy(
            [files[0]],
            [os.path.join(temp_dir, "high", "file_0.bin")],
            priority=OperationPriority.HIGH
        )
        print(f"  HIGH priority:   {op_high[:8]}...")

        op_normal = manager.queue_copy(
            files[1:4],
            [os.path.join(temp_dir, "normal", f"file_{i}.bin") for i in range(1, 4)],
            priority=OperationPriority.NORMAL
        )
        print(f"  NORMAL priority: {op_normal[:8]}...")

        op_low = manager.queue_copy(
            files[4:],
            [os.path.join(temp_dir, "low", f"file_{i}.bin") for i in range(4, 6)],
            priority=OperationPriority.LOW
        )
        print(f"  LOW priority:    {op_low[:8]}...")

        # Monitor progress
        print("\nMonitoring operations...")
        all_ops = [op_high, op_normal, op_low]

        while True:
            time.sleep(0.5)

            active = manager.get_active_operations()
            queued = manager.get_queued_operations()

            # Check if all done
            completed = sum(
                1 for op_id in all_ops
                if manager.get_operation(op_id) and
                manager.get_operation(op_id).status.value == 'completed'
            )

            if completed == len(all_ops):
                break

            print(f"\r  Active: {len(active)} | Queued: {len(queued)} | "
                  f"Completed: {completed}/{len(all_ops)}", end='')

        print("\n\n✓ All operations completed!")

        # Show final stats
        for op_id in all_ops:
            op = manager.get_operation(op_id)
            if op:
                duration = (op.completed_at - op.started_at).total_seconds()
                print(f"  {op_id[:8]}... - {op.processed_files} files in {duration:.2f}s")

        manager.shutdown()


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("TeraCopy-Style File Operations - Test Suite")
    print("="*70)

    tests = [
        ("Adaptive Buffering", test_adaptive_buffering),
        ("Copy with Progress", test_basic_copy_with_progress),
        ("Hash Verification", test_hash_verification),
        ("Pause/Resume/Cancel", test_pause_resume_cancel),
        ("Batch Operations", test_batch_operations),
        ("Move Operations", test_move_operations),
        ("Operations Manager", test_operations_manager),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
            time.sleep(0.5)  # Brief pause between tests
        except KeyboardInterrupt:
            print("\n\nTests interrupted by user")
            break
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {len(tests)}")
    print("="*70 + "\n")


if __name__ == "__main__":
    run_all_tests()
