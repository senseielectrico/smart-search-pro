"""
Quick demonstration of TeraCopy-style file operations.
Shows the most important features in action.
"""

import os
import sys
import time
import tempfile
from pathlib import Path

# Set UTF-8 encoding for console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from operations.copier import FileCopier
from operations.mover import FileMover
from operations.verifier import FileVerifier, HashAlgorithm
from operations.manager import OperationsManager, OperationPriority


def create_test_file(path: str, size_mb: int) -> None:
    """Create a test file."""
    with open(path, 'wb') as f:
        f.write(os.urandom(size_mb * 1024 * 1024))


def format_size(bytes_val: int) -> str:
    """Format bytes to human-readable."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"


def format_speed(bps: float) -> str:
    """Format speed to human-readable."""
    for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
        if bps < 1024.0:
            return f"{bps:.2f} {unit}"
        bps /= 1024.0
    return f"{bps:.2f} TB/s"


def demo_adaptive_buffering():
    """Demo 1: Adaptive buffering."""
    print("\n" + "="*60)
    print("DEMO 1: Adaptive Buffering")
    print("="*60)

    sizes = [
        (500 * 1024, "500 KB"),
        (50 * 1024 * 1024, "50 MB"),
        (5 * 1024 * 1024 * 1024, "5 GB"),
    ]

    print("\nAutomatic buffer size selection:")
    for size, label in sizes:
        buffer = FileCopier._get_optimal_buffer_size(size, "C:\\src", "D:\\dst")
        print(f"  {label:>10s} → {format_size(buffer):>10s} buffer")


def demo_copy_with_progress():
    """Demo 2: Copy with progress."""
    print("\n" + "="*60)
    print("DEMO 2: Copy with Progress Tracking")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        source = os.path.join(temp_dir, "test.bin")
        dest = os.path.join(temp_dir, "copy.bin")

        print("\nCreating 20MB test file...")
        create_test_file(source, 20)

        start_time = time.time()

        def progress(copied, total):
            percent = (copied / total) * 100
            elapsed = time.time() - start_time
            speed = copied / elapsed if elapsed > 0 else 0

            bar_width = 40
            filled = int(bar_width * copied / total)
            bar = '█' * filled + '░' * (bar_width - filled)

            print(f"\r  [{bar}] {percent:5.1f}% | {format_speed(speed):>12s}", end='')

        print("Copying...")
        with FileCopier() as copier:
            success = copier.copy_file(source, dest, progress_callback=progress)

        print()
        if success:
            elapsed = time.time() - start_time
            avg_speed = os.path.getsize(dest) / elapsed
            print(f"\n✓ Copy completed in {elapsed:.2f}s")
            print(f"  Average speed: {format_speed(avg_speed)}")


def demo_hash_verification():
    """Demo 3: Hash verification."""
    print("\n" + "="*60)
    print("DEMO 3: Hash Verification")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        original = os.path.join(temp_dir, "original.bin")
        copy = os.path.join(temp_dir, "verified.bin")

        print("\nCreating 10MB test file...")
        create_test_file(original, 10)

        print("\nCopying with SHA256 verification...")
        start = time.time()

        with FileCopier(verify_after_copy=True, verify_algorithm='sha256') as copier:
            success = copier.copy_file(original, copy)

        elapsed = time.time() - start

        if success:
            print(f"✓ Copy and verification completed in {elapsed:.2f}s")
            print("  Files verified to match exactly!")
        else:
            print("✗ Verification failed!")


def demo_batch_operations():
    """Demo 4: Batch operations."""
    print("\n" + "="*60)
    print("DEMO 4: Batch Copy (4 workers)")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        files = []
        print("\nCreating 5 test files...")

        for i in range(5):
            path = os.path.join(temp_dir, f"file_{i}.bin")
            create_test_file(path, (i + 1) * 2)  # 2MB, 4MB, 6MB, 8MB, 10MB
            files.append(path)
            print(f"  file_{i}.bin ({(i+1)*2} MB)")

        # Build pairs
        pairs = [
            (f, os.path.join(temp_dir, "backup", os.path.basename(f)))
            for f in files
        ]

        print("\nCopying in parallel...")
        start = time.time()

        with FileCopier(max_workers=4) as copier:
            results = copier.copy_files_batch(pairs)

        elapsed = time.time() - start
        success_count = sum(1 for s, _ in results.values() if s)

        print(f"\n✓ Copied {success_count}/{len(files)} files in {elapsed:.2f}s")


def demo_queue_management():
    """Demo 5: Queue with priorities."""
    print("\n" + "="*60)
    print("DEMO 5: Queue Management with Priorities")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = OperationsManager(max_concurrent_operations=2)

        # Create test files
        files = []
        for i in range(6):
            path = os.path.join(temp_dir, f"file_{i}.bin")
            create_test_file(path, 2)
            files.append(path)

        # Queue with different priorities
        print("\nQueueing operations...")

        op_high = manager.queue_copy(
            [files[0]],
            [os.path.join(temp_dir, "high", "file_0.bin")],
            priority=OperationPriority.HIGH
        )
        print(f"  HIGH:   {op_high[:8]}...")

        op_normal = manager.queue_copy(
            files[1:4],
            [os.path.join(temp_dir, "normal", f"file_{i}.bin") for i in range(1, 4)],
            priority=OperationPriority.NORMAL
        )
        print(f"  NORMAL: {op_normal[:8]}...")

        op_low = manager.queue_copy(
            files[4:],
            [os.path.join(temp_dir, "low", f"file_{i}.bin") for i in range(4, 6)],
            priority=OperationPriority.LOW
        )
        print(f"  LOW:    {op_low[:8]}...")

        # Monitor
        print("\nProcessing (2 concurrent operations)...")
        all_ops = [op_high, op_normal, op_low]

        while True:
            active = manager.get_active_operations()
            queued = manager.get_queued_operations()

            completed = sum(
                1 for op_id in all_ops
                if manager.get_operation(op_id) and
                manager.get_operation(op_id).status.value == 'completed'
            )

            if completed == len(all_ops):
                break

            print(f"\r  Active: {len(active)} | Queued: {len(queued)} | Done: {completed}/3", end='')
            time.sleep(0.3)

        print("\n\n✓ All operations completed!")
        manager.shutdown()


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("TeraCopy-Style File Operations - Quick Demo")
    print("="*60)

    demos = [
        demo_adaptive_buffering,
        demo_copy_with_progress,
        demo_hash_verification,
        demo_batch_operations,
        demo_queue_management,
    ]

    for demo in demos:
        try:
            demo()
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nDemo interrupted")
            break
        except Exception as e:
            print(f"\n✗ Demo failed: {e}")

    print("\n" + "="*60)
    print("Demo Complete!")
    print("="*60)
    print("\nFor more examples, see:")
    print("  - operations/example_usage.py")
    print("  - operations/test_teracopy_features.py")
    print("  - operations/TERACOPY_FEATURES.md")
    print()


if __name__ == "__main__":
    main()
