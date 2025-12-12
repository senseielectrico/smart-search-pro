"""
Test and demo for batch rename functionality
"""

import os
import sys
import tempfile
from pathlib import Path

# Ensure UTF-8 output
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from operations.batch_renamer import (
    BatchRenamer, RenamePattern, CaseMode, CollisionMode
)
from operations.rename_patterns import PatternLibrary, SavedPattern
from operations.rename_history import RenameHistory


def test_basic_rename():
    """Test basic renaming functionality"""
    print("\n=== Test 1: Basic Rename ===")

    # Create temp files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create test files
        files = []
        for i in range(5):
            file = tmppath / f"test_file_{i}.txt"
            file.write_text(f"Content {i}")
            files.append(str(file))

        print(f"Created {len(files)} test files in {tmpdir}")

        # Test renaming with pattern
        renamer = BatchRenamer()
        pattern = RenamePattern(
            pattern="renamed_{num}",
            number_padding=2
        )

        # Preview first
        print("\nPreview:")
        previews = renamer.preview_rename(files, pattern)
        for old, new, conflict in previews:
            print(f"  {old} -> {new} {'[CONFLICT]' if conflict else ''}")

        # Apply rename
        print("\nApplying rename...")
        result = renamer.batch_rename(files, pattern, CollisionMode.AUTO_NUMBER)

        print(f"\nResults:")
        print(f"  Total: {result.total_files}")
        print(f"  Success: {result.success_count}")
        print(f"  Failed: {result.failed_count}")
        print(f"  Skipped: {result.skipped_count}")

        # List files after rename
        print("\nFiles after rename:")
        for file in sorted(tmppath.iterdir()):
            print(f"  {file.name}")


def test_pattern_library():
    """Test pattern library"""
    print("\n=== Test 2: Pattern Library ===")

    library = PatternLibrary()

    # Get all categories
    print("\nAvailable categories:")
    for category in library.get_categories():
        patterns = library.get_patterns_by_category(category)
        print(f"\n  {category} ({len(patterns)} patterns):")
        for pattern_id, saved_pattern in list(patterns.items())[:3]:  # Show first 3
            print(f"    - {saved_pattern.name}")
            print(f"      Pattern: {saved_pattern.pattern.pattern}")

    # Get photo patterns
    print("\n\nPhoto patterns:")
    photo_patterns = library.get_patterns_by_tag("photos")
    for pattern_id, saved_pattern in photo_patterns.items():
        print(f"  {saved_pattern.name}: {saved_pattern.pattern.pattern}")


def test_rename_history():
    """Test rename history"""
    print("\n=== Test 3: Rename History ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        history = RenameHistory(history_file)

        # Add some test entries
        print("\nAdding history entries...")
        for i in range(3):
            operations = [
                {
                    'old_path': f'/path/to/file_{i}_{j}.txt',
                    'new_path': f'/path/to/renamed_{j}.txt',
                    'success': True
                }
                for j in range(5)
            ]

            history.add_entry(
                operation_id=f"op_{i}",
                operations=operations,
                pattern_used=f"pattern_{i}",
                total_files=5,
                success_count=5
            )

        # Get history
        print("\nRecent history:")
        for entry in history.get_history(limit=5):
            print(f"  {entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    Pattern: {entry.pattern_used}")
            print(f"    Files: {entry.success_count}/{entry.total_files}")
            print(f"    Can undo: {entry.can_undo}")

        # Statistics
        stats = history.get_statistics()
        print("\nStatistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")


def test_text_operations():
    """Test text operations"""
    print("\n=== Test 4: Text Operations ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create files with various names
        test_names = [
            "File With Spaces.txt",
            "UPPERCASE.TXT",
            "file_with_underscores.dat",
            "Mixed-Case-File.pdf",
            "file!!!special###chars.doc"
        ]

        files = []
        for name in test_names:
            file = tmppath / name
            file.write_text("content")
            files.append(str(file))

        renamer = BatchRenamer()

        # Test 1: Remove special characters
        print("\n1. Remove special characters:")
        pattern = RenamePattern(
            pattern="{name}",
            remove_chars="!@#$%"
        )
        previews = renamer.preview_rename(files, pattern)
        for old, new, _ in previews:
            if old != new:
                print(f"  {old} -> {new}")

        # Test 2: Lowercase
        print("\n2. Convert to lowercase:")
        pattern = RenamePattern(
            pattern="{name}",
            case_mode=CaseMode.LOWER
        )
        previews = renamer.preview_rename(files, pattern)
        for old, new, _ in previews:
            if old != new:
                print(f"  {old} -> {new}")

        # Test 3: Add prefix/suffix
        print("\n3. Add prefix and suffix:")
        pattern = RenamePattern(
            pattern="{name}",
            prefix="PROJECT_",
            suffix="_2023"
        )
        previews = renamer.preview_rename(files, pattern)
        for old, new, _ in previews:
            print(f"  {old} -> {new}")


def test_date_patterns():
    """Test date-based patterns"""
    print("\n=== Test 5: Date Patterns ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create test files
        files = []
        for i in range(3):
            file = tmppath / f"photo_{i}.jpg"
            file.write_text(f"image data {i}")
            files.append(str(file))

        renamer = BatchRenamer()

        # Test different date formats
        date_formats = [
            ("%Y%m%d", "YYYYMMDD"),
            ("%Y-%m-%d", "YYYY-MM-DD"),
            ("%d_%m_%Y", "DD_MM_YYYY"),
        ]

        for fmt, label in date_formats:
            print(f"\n{label} format:")
            pattern = RenamePattern(
                pattern="{date}_{num}",
                date_format=fmt,
                number_padding=2
            )
            previews = renamer.preview_rename(files, pattern)
            for old, new, _ in previews:
                print(f"  {old} -> {new}")


def test_collision_handling():
    """Test collision handling"""
    print("\n=== Test 6: Collision Handling ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create files that will have name collisions
        files = []
        for i in range(5):
            file = tmppath / f"different_name_{i}.txt"
            file.write_text(f"content {i}")
            files.append(str(file))

        renamer = BatchRenamer()

        # Pattern that causes all files to have same name
        pattern = RenamePattern(pattern="samename")

        print("\nPattern that causes collisions: 'samename'")

        # Test AUTO_NUMBER mode
        print("\nAuto-number mode:")
        previews = renamer.preview_rename(files, pattern)
        for old, new, conflict in previews:
            print(f"  {old} -> {new} {'[CONFLICT]' if conflict else ''}")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Batch Rename System - Test Suite")
    print("=" * 60)

    tests = [
        test_basic_rename,
        test_pattern_library,
        test_rename_history,
        test_text_operations,
        test_date_patterns,
        test_collision_handling,
    ]

    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"\n[FAIL] Test failed: {test.__name__}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
