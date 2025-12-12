"""
Example usage of the file operations module.
Demonstrates all major features.
"""

import os
import time
import tempfile
from pathlib import Path

from operations.manager import OperationsManager, OperationPriority, OperationType
from operations.copier import FileCopier
from operations.mover import FileMover
from operations.verifier import FileVerifier, HashAlgorithm
from operations.conflicts import ConflictResolver, ConflictAction
from operations.progress import ProgressTracker


def example_1_basic_copy():
    """Example 1: Basic file copy with progress."""
    print("\n" + "="*60)
    print("Example 1: Basic File Copy")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        source = os.path.join(temp_dir, "source.bin")
        dest = os.path.join(temp_dir, "destination.bin")

        print(f"Creating test file: {source}")
        with open(source, 'wb') as f:
            f.write(os.urandom(5 * 1024 * 1024))  # 5MB

        # Progress callback
        def show_progress(copied, total):
            percent = (copied / total) * 100
            print(f"\rProgress: {percent:6.2f}% ({copied:,}/{total:,} bytes)", end='')

        # Copy with progress
        print("Copying file...")
        with FileCopier() as copier:
            success, error = copier.copy_file_with_retry(
                source,
                dest,
                progress_callback=show_progress
            )

        print()  # New line after progress
        if success:
            print(f"✓ Copy successful!")
            print(f"  Source: {os.path.getsize(source):,} bytes")
            print(f"  Dest:   {os.path.getsize(dest):,} bytes")
        else:
            print(f"✗ Copy failed: {error}")


def example_2_batch_operations():
    """Example 2: Batch copy operations."""
    print("\n" + "="*60)
    print("Example 2: Batch Copy Operations")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create multiple test files
        file_pairs = []
        total_size = 0

        print("Creating test files...")
        for i in range(10):
            source = os.path.join(temp_dir, f"file_{i}.bin")
            dest = os.path.join(temp_dir, "backup", f"file_{i}.bin")

            # Create file with random size
            size = (i + 1) * 100 * 1024  # 100KB to 1MB
            with open(source, 'wb') as f:
                f.write(os.urandom(size))

            file_pairs.append((source, dest))
            total_size += size
            print(f"  Created: file_{i}.bin ({size:,} bytes)")

        print(f"\nTotal size: {total_size:,} bytes")

        # Batch copy
        print("\nCopying files in batch...")
        with FileCopier(max_workers=4) as copier:
            results = copier.copy_files_batch(file_pairs)

        # Show results
        success_count = sum(1 for success, _ in results.values() if success)
        print(f"\n✓ Successfully copied: {success_count}/{len(file_pairs)} files")

        for dest, (success, error) in results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {os.path.basename(dest)}")


def example_3_move_operations():
    """Example 3: File move operations."""
    print("\n" + "="*60)
    print("Example 3: File Move Operations")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test file
        source = os.path.join(temp_dir, "original.txt")
        dest = os.path.join(temp_dir, "subdir", "moved.txt")

        with open(source, 'w') as f:
            f.write("Test content for move operation\n" * 1000)

        print(f"Source: {source}")
        print(f"Dest:   {dest}")

        # Move file
        with FileMover() as mover:
            strategy = mover.get_move_strategy(source, dest)
            print(f"Move strategy: {strategy}")

            success, error = mover.move_file(source, dest)

        if success:
            print("✓ Move successful!")
            print(f"  Source exists: {os.path.exists(source)}")
            print(f"  Dest exists:   {os.path.exists(dest)}")
        else:
            print(f"✗ Move failed: {error}")


def example_4_verification():
    """Example 4: File verification."""
    print("\n" + "="*60)
    print("Example 4: File Verification")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test file
        original = os.path.join(temp_dir, "original.bin")
        with open(original, 'wb') as f:
            f.write(os.urandom(1024 * 1024))  # 1MB

        # Test different hash algorithms
        algorithms = [
            HashAlgorithm.CRC32,
            HashAlgorithm.MD5,
            HashAlgorithm.SHA256,
        ]

        print("Calculating hashes...")
        for algo in algorithms:
            verifier = FileVerifier(algorithm=algo)
            hash_value = verifier.calculate_hash(original)
            print(f"  {algo.value:10s}: {hash_value}")

        # Verify copy
        copy = os.path.join(temp_dir, "copy.bin")
        import shutil
        shutil.copy2(original, copy)

        print("\nVerifying copy...")
        verifier = FileVerifier(algorithm=HashAlgorithm.MD5)
        is_valid, error = verifier.verify_copy(original, copy)

        if is_valid:
            print("✓ Verification successful - files match!")
        else:
            print(f"✗ Verification failed: {error}")


def example_5_conflict_resolution():
    """Example 5: Conflict resolution."""
    print("\n" + "="*60)
    print("Example 5: Conflict Resolution")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create existing file
        existing = os.path.join(temp_dir, "document.txt")
        with open(existing, 'w') as f:
            f.write("Existing content")

        print(f"Existing file: {existing}")

        # Test different resolution strategies
        strategies = [
            (ConflictAction.RENAME, "Rename to unique name"),
            (ConflictAction.OVERWRITE, "Overwrite existing"),
            (ConflictAction.SKIP, "Skip conflicting file"),
        ]

        for action, description in strategies:
            print(f"\n{description}:")
            resolver = ConflictResolver(default_action=action)

            resolution = resolver.resolve("source.txt", existing)
            print(f"  Action: {resolution.action.value}")
            if resolution.new_path:
                print(f"  New path: {resolution.new_path}")

        # Show rename preview
        print("\nRename preview:")
        resolver = ConflictResolver()
        suggestions = resolver.get_rename_preview(existing, max_suggestions=5)
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {os.path.basename(suggestion)}")


def example_6_progress_tracking():
    """Example 6: Advanced progress tracking."""
    print("\n" + "="*60)
    print("Example 6: Progress Tracking")
    print("="*60)

    tracker = ProgressTracker()

    # Simulate operation
    files = ["video.mp4", "document.pdf", "archive.zip"]
    sizes = [100*1024*1024, 5*1024*1024, 50*1024*1024]  # 100MB, 5MB, 50MB

    print("Starting operation...")
    progress = tracker.start_operation("demo-op", files, sizes)

    print(f"Total files: {progress.total_files}")
    print(f"Total size:  {tracker.format_size(progress.total_size)}")

    # Simulate progress updates
    print("\nSimulating copy progress...")
    import random

    for file_path, file_size in zip(files, sizes):
        print(f"\nCopying {file_path}...")

        # Simulate chunks
        copied = 0
        while copied < file_size:
            chunk = min(1024*1024, file_size - copied)  # 1MB chunks
            copied += chunk

            tracker.update_file("demo-op", file_path, copied)

            # Show progress
            current = tracker.get_progress("demo-op")
            print(f"\r  Progress: {current.progress_percent:6.2f}% | "
                  f"Speed: {tracker.format_speed(current.current_speed):>12s} | "
                  f"ETA: {tracker.format_time(current.eta_seconds):>8s}",
                  end='')

            time.sleep(0.01)  # Simulate work

        tracker.complete_file("demo-op", file_path)
        print()  # New line

    # Final stats
    final = tracker.get_progress("demo-op")
    tracker.complete_operation("demo-op")

    print(f"\n✓ Operation complete!")
    print(f"  Files:   {final.completed_files}/{final.total_files}")
    print(f"  Size:    {tracker.format_size(final.copied_size)}")
    print(f"  Time:    {tracker.format_time(final.elapsed_time)}")
    print(f"  Avg speed: {tracker.format_speed(final.average_speed)}")


def example_7_operations_manager():
    """Example 7: Operations manager with queue."""
    print("\n" + "="*60)
    print("Example 7: Operations Manager")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create manager
        history_file = os.path.join(temp_dir, "history.json")
        manager = OperationsManager(
            max_concurrent_operations=2,
            history_file=history_file
        )

        # Create test files
        print("Creating test files...")
        sources = []
        dests = []

        for i in range(5):
            source = os.path.join(temp_dir, f"source_{i}.bin")
            dest = os.path.join(temp_dir, "backup", f"dest_{i}.bin")

            with open(source, 'wb') as f:
                f.write(os.urandom(100 * 1024))  # 100KB

            sources.append(source)
            dests.append(dest)

        # Queue operations with different priorities
        print("\nQueuing operations...")

        # High priority
        op1 = manager.queue_copy(
            [sources[0]],
            [dests[0]],
            priority=OperationPriority.HIGH
        )
        print(f"  High priority:   {op1}")

        # Normal priority
        op2 = manager.queue_copy(
            sources[1:3],
            dests[1:3],
            priority=OperationPriority.NORMAL
        )
        print(f"  Normal priority: {op2}")

        # Low priority
        op3 = manager.queue_copy(
            sources[3:],
            dests[3:],
            priority=OperationPriority.LOW
        )
        print(f"  Low priority:    {op3}")

        # Monitor progress
        print("\nMonitoring operations...")
        completed = 0
        while completed < 3:
            time.sleep(0.5)

            active = manager.get_active_operations()
            queued = manager.get_queued_operations()

            print(f"\r  Active: {len(active)} | Queued: {len(queued)}", end='')

            # Check completions
            for op_id in [op1, op2, op3]:
                operation = manager.get_operation(op_id)
                if operation and operation.status.value in ['completed', 'failed']:
                    completed += 1

        print("\n\n✓ All operations complete!")

        # Show results
        for op_id in [op1, op2, op3]:
            operation = manager.get_operation(op_id)
            print(f"\n  Operation {op_id[:8]}...")
            print(f"    Status:   {operation.status.value}")
            print(f"    Files:    {operation.processed_files}/{operation.total_files}")
            print(f"    Duration: {(operation.completed_at - operation.started_at).total_seconds():.2f}s")

        # Save and load history
        print("\nSaving history...")
        manager.save_history()
        print(f"  Saved to: {history_file}")

        manager.shutdown()


def main():
    """Run all examples."""
    print("\n")
    print("="*60)
    print("File Operations Module - Example Usage")
    print("="*60)

    examples = [
        example_1_basic_copy,
        example_2_batch_operations,
        example_3_move_operations,
        example_4_verification,
        example_5_conflict_resolution,
        example_6_progress_tracking,
        example_7_operations_manager,
    ]

    for example in examples:
        try:
            example()
            time.sleep(1)  # Pause between examples
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            break
        except Exception as e:
            print(f"\n✗ Example failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
