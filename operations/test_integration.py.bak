"""
Integration test for operations module
Tests interaction between BatchRenamer, Progress tracking, and file operations
"""

import sys
import os
import tempfile
import time
from pathlib import Path

# Ensure UTF-8 output
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from operations import (
    BatchRenamer, RenamePattern, CaseMode, CollisionMode,
    PatternLibrary, RenameHistory,
    ProgressTracker, FileCopier, FileMover
)


def test_batch_rename_with_progress():
    """Test batch rename with progress tracking"""
    print("\n=== Integration Test 1: Batch Rename + Progress ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create test files
        files = []
        sizes = []
        for i in range(10):
            file = tmppath / f"document_{i}.txt"
            content = f"Document content {i}\n" * 100
            file.write_text(content)
            files.append(str(file))
            sizes.append(file.stat().st_size)

        print(f"Created {len(files)} test files")

        # Setup progress tracker
        tracker = ProgressTracker()
        operation_id = "rename_test_1"
        progress = tracker.start_operation(operation_id, files, sizes)

        # Setup renamer
        renamer = BatchRenamer()
        pattern = RenamePattern(
            pattern="{date}_Doc_{num}",
            date_format="%Y%m%d",
            number_padding=3
        )

        # Preview
        print("\nPreview (first 3 files):")
        previews = renamer.preview_rename(files, pattern)
        for old, new, conflict in previews[:3]:
            print(f"  {old} -> {new}")

        # Execute rename
        print("\nExecuting rename...")
        start_time = time.time()
        result = renamer.batch_rename(files, pattern, CollisionMode.AUTO_NUMBER)
        elapsed = time.time() - start_time

        # Update progress
        for op in result.operations:
            if op.success:
                tracker.complete_file(operation_id, str(op.old_path))

        tracker.complete_operation(operation_id)

        # Show results
        print(f"\nResults:")
        print(f"  Total: {result.total_files}")
        print(f"  Success: {result.success_count}")
        print(f"  Failed: {result.failed_count}")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Progress: {progress.progress_percent:.1f}%")


def test_pattern_library_workflow():
    """Test pattern library workflow"""
    print("\n=== Integration Test 2: Pattern Library Workflow ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create pattern library
        library_file = tmppath / "patterns.json"
        library = PatternLibrary(library_file)

        # Create custom pattern
        custom_pattern = RenamePattern(
            pattern="MyProject_{name}_{num}",
            prefix="",
            suffix="_final",
            number_padding=4,
            case_mode=CaseMode.LOWER
        )

        from operations.rename_patterns import SavedPattern
        saved = SavedPattern(
            name="My Custom Pattern",
            description="Custom pattern for project files",
            pattern=custom_pattern,
            category="Projects",
            tags=["project", "custom"]
        )

        # Save pattern
        pattern_id = "my_custom_1"
        success = library.save_pattern(pattern_id, saved)
        print(f"Pattern saved: {success}")

        # Retrieve pattern
        retrieved = library.get_pattern(pattern_id)
        if retrieved:
            print(f"Retrieved pattern: {retrieved.name}")
            print(f"  Category: {retrieved.category}")
            print(f"  Pattern: {retrieved.pattern.pattern}")

        # List all categories
        print(f"\nTotal categories: {len(library.get_categories())}")
        print(f"Total patterns: {len(library.get_all_patterns())}")

        # Export patterns
        export_file = tmppath / "exported.json"
        success = library.export_patterns(str(export_file))
        print(f"Patterns exported: {success}")

        # Import patterns
        library2 = PatternLibrary(tmppath / "patterns2.json")
        count = library2.import_patterns(str(export_file))
        print(f"Patterns imported: {count}")


def test_rename_with_history():
    """Test rename with history tracking"""
    print("\n=== Integration Test 3: Rename + History ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Setup history
        history_file = tmppath / "history.json"
        history = RenameHistory(history_file)

        # Create files
        files = []
        for i in range(5):
            file = tmppath / f"file_{i}.txt"
            file.write_text(f"Content {i}")
            files.append(str(file))

        # Rename with pattern
        renamer = BatchRenamer()
        pattern = RenamePattern(
            pattern="renamed_{num}",
            number_padding=2
        )

        result = renamer.batch_rename(files, pattern)

        # Add to history
        operations = [op.to_dict() for op in result.operations]
        history.add_entry(
            operation_id="test_op_1",
            operations=operations,
            pattern_used=pattern.pattern,
            total_files=result.total_files,
            success_count=result.success_count,
        )

        # Check history
        entries = history.get_history(limit=5)
        print(f"\nHistory entries: {len(entries)}")
        if entries:
            entry = entries[0]
            print(f"  Latest operation:")
            print(f"    Pattern: {entry.pattern_used}")
            print(f"    Files: {entry.success_count}/{entry.total_files}")
            print(f"    Can undo: {entry.can_undo}")

        # Statistics
        stats = history.get_statistics()
        print(f"\nStatistics:")
        print(f"  Total operations: {stats['total_operations']}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")


def test_file_operations_integration():
    """Test file operations (copy/move) integration"""
    print("\n=== Integration Test 4: File Operations ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create source directory
        source_dir = tmppath / "source"
        source_dir.mkdir()

        dest_dir = tmppath / "destination"
        dest_dir.mkdir()

        # Create test files
        files = []
        for i in range(5):
            file = source_dir / f"file_{i}.txt"
            file.write_text(f"Content {i}\n" * 1000)
            files.append(file)

        print(f"Created {len(files)} test files in source")

        # Test FileCopier
        print("\nTesting FileCopier...")
        with FileCopier(max_workers=2, verify_after_copy=False) as copier:
            copy_pairs = [
                (str(f), str(dest_dir / f.name))
                for f in files
            ]

            results = copier.copy_files_batch(copy_pairs)
            success_count = sum(1 for success, _ in results.values() if success)
            print(f"  Copied: {success_count}/{len(files)}")

        # Verify destination
        dest_files = list(dest_dir.glob("*.txt"))
        print(f"  Files in destination: {len(dest_files)}")

        # Test FileMover
        print("\nTesting FileMover...")
        move_dir = tmppath / "moved"
        move_dir.mkdir()

        mover = FileMover(verify_after_move=False)
        move_pairs = [
            (str(f), str(move_dir / f.name))
            for f in dest_files
        ]

        results = mover.move_files_batch(move_pairs)
        success_count = sum(1 for success, _ in results.values() if success)
        print(f"  Moved: {success_count}/{len(dest_files)}")

        # Verify
        moved_files = list(move_dir.glob("*.txt"))
        print(f"  Files in moved dir: {len(moved_files)}")


def test_complex_workflow():
    """Test complex workflow: copy -> rename -> track"""
    print("\n=== Integration Test 5: Complex Workflow ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Setup
        source_dir = tmppath / "source"
        source_dir.mkdir()
        work_dir = tmppath / "work"
        work_dir.mkdir()

        # Create source files
        print("Creating source files...")
        source_files = []
        for i in range(3):
            file = source_dir / f"photo_{i}.jpg"
            file.write_text(f"Photo data {i}\n" * 500)
            source_files.append(file)

        # Step 1: Copy files to work directory
        print("\nStep 1: Copying files...")
        with FileCopier() as copier:
            copy_pairs = [
                (str(f), str(work_dir / f.name))
                for f in source_files
            ]
            results = copier.copy_files_batch(copy_pairs)
            print(f"  Copied: {sum(1 for s, _ in results.values() if s)}/{len(source_files)}")

        # Step 2: Rename with pattern
        print("\nStep 2: Renaming files...")
        work_files = [str(f) for f in work_dir.glob("*.jpg")]

        library = PatternLibrary()
        photo_pattern = library.get_pattern('photo_date_numbered')

        if photo_pattern:
            renamer = BatchRenamer()
            result = renamer.batch_rename(
                work_files,
                photo_pattern.pattern,
                CollisionMode.AUTO_NUMBER
            )
            print(f"  Renamed: {result.success_count}/{result.total_files}")

            # Show results
            print("\n  Results:")
            for op in result.operations[:3]:
                print(f"    {op.old_path.name} -> {op.new_name}")

        # Step 3: Track with history
        print("\nStep 3: Recording history...")
        history = RenameHistory(tmppath / "history.json")
        history.add_entry(
            operation_id="workflow_test",
            operations=[op.to_dict() for op in result.operations],
            pattern_used="photo_date_numbered",
            total_files=result.total_files,
            success_count=result.success_count
        )

        stats = history.get_statistics()
        print(f"  History recorded: {stats['total_operations']} operations")


def run_all_integration_tests():
    """Run all integration tests"""
    print("=" * 70)
    print("OPERATIONS MODULE - INTEGRATION TEST SUITE")
    print("=" * 70)

    tests = [
        test_batch_rename_with_progress,
        test_pattern_library_workflow,
        test_rename_with_history,
        test_file_operations_integration,
        test_complex_workflow,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
            print(f"\n✓ {test.__name__} PASSED")
        except Exception as e:
            failed += 1
            print(f"\n✗ {test.__name__} FAILED")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 70)
    print(f"Total: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all_integration_tests())
