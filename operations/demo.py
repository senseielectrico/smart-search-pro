"""
Operations Module - Feature Demonstration
Shows all major features in action
"""

import sys
import os
import tempfile
from pathlib import Path

# Ensure UTF-8 output
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from operations import (
    BatchRenamer, RenamePattern, CaseMode, CollisionMode,
    PatternLibrary, RenameHistory, ProgressTracker
)


def demo_basic_rename():
    """Demo 1: Basic batch renaming"""
    print("\n" + "=" * 70)
    print("DEMO 1: Basic Batch Rename")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create sample files
        print("\nCreating sample files...")
        files = []
        for i in range(5):
            file = tmppath / f"vacation_photo_{i}.jpg"
            file.write_text(f"Photo {i}")
            files.append(str(file))
            print(f"  Created: {file.name}")

        # Setup renamer
        renamer = BatchRenamer()
        pattern = RenamePattern(
            pattern="{date}_Vacation_{num}",
            date_format="%Y%m%d",
            number_padding=3
        )

        # Show preview
        print("\nPreview of rename operation:")
        previews = renamer.preview_rename(files, pattern)
        for old, new, collision in previews:
            print(f"  {old} -> {new}")

        # Execute rename
        print("\nExecuting rename...")
        result = renamer.batch_rename(files, pattern, CollisionMode.AUTO_NUMBER)

        print(f"\nResults:")
        print(f"  Total files: {result.total_files}")
        print(f"  Successful: {result.success_count}")
        print(f"  Failed: {result.failed_count}")

        # Show renamed files
        print("\nRenamed files:")
        for file in sorted(tmppath.iterdir()):
            print(f"  {file.name}")


def demo_pattern_library():
    """Demo 2: Using pattern library"""
    print("\n" + "=" * 70)
    print("DEMO 2: Pattern Library")
    print("=" * 70)

    library = PatternLibrary()

    # Show available categories
    print("\nAvailable pattern categories:")
    for category in library.get_categories():
        patterns = library.get_patterns_by_category(category)
        print(f"\n  {category} ({len(patterns)} patterns)")
        for pid, pattern in list(patterns.items())[:2]:
            print(f"    - {pattern.name}")
            print(f"      Pattern: {pattern.pattern.pattern}")
            print(f"      Description: {pattern.description}")

    # Use a pre-built pattern
    print("\n\nUsing pre-built photo pattern:")
    photo_pattern = library.get_pattern('photo_date_numbered')
    if photo_pattern:
        print(f"  Name: {photo_pattern.name}")
        print(f"  Pattern: {photo_pattern.pattern.pattern}")
        print(f"  Example output: 20251212_IMG_001.jpg")


def demo_text_operations():
    """Demo 3: Text manipulation"""
    print("\n" + "=" * 70)
    print("DEMO 3: Text Operations")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create files with various names
        test_files = [
            "UPPERCASE FILE.TXT",
            "file with   spaces.doc",
            "File!!!With###Special$$$Chars.pdf",
            "Mixed-Case-Document.docx"
        ]

        files = []
        for name in test_files:
            file = tmppath / name
            file.write_text("content")
            files.append(str(file))

        renamer = BatchRenamer()

        # Demo 1: Lowercase conversion
        print("\n1. Convert to lowercase:")
        pattern = RenamePattern(pattern="{name}", case_mode=CaseMode.LOWER)
        previews = renamer.preview_rename(files, pattern)
        for old, new, _ in previews:
            print(f"  {old} -> {new}")

        # Demo 2: Remove special characters
        print("\n2. Remove special characters:")
        pattern = RenamePattern(
            pattern="{name}",
            remove_chars="!@#$%^&*()"
        )
        previews = renamer.preview_rename(files, pattern)
        for old, new, _ in previews:
            if old != new:
                print(f"  {old} -> {new}")

        # Demo 3: Add prefix and suffix
        print("\n3. Add prefix and suffix:")
        pattern = RenamePattern(
            pattern="{name}",
            prefix="PROJ_",
            suffix="_final"
        )
        previews = renamer.preview_rename(files, pattern)
        for old, new, _ in previews:
            print(f"  {old} -> {new}")


def demo_collision_handling():
    """Demo 4: Collision handling"""
    print("\n" + "=" * 70)
    print("DEMO 4: Collision Handling")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create files
        files = []
        for i in range(5):
            file = tmppath / f"different_{i}.txt"
            file.write_text(f"Content {i}")
            files.append(str(file))

        renamer = BatchRenamer()

        # Pattern that causes collisions
        pattern = RenamePattern(pattern="document")

        print("\nRenaming all files to 'document':")
        print("(Auto-number mode will add (1), (2), etc.)")

        previews = renamer.preview_rename(files, pattern)
        for old, new, collision in previews:
            status = "[COLLISION]" if collision else ""
            print(f"  {old} -> {new} {status}")


def demo_date_formats():
    """Demo 5: Date formatting options"""
    print("\n" + "=" * 70)
    print("DEMO 5: Date Format Options")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create test file
        file = tmppath / "photo.jpg"
        file.write_text("photo data")
        files = [str(file)]

        renamer = BatchRenamer()

        formats = [
            ("%Y%m%d", "Compact (YYYYMMDD)"),
            ("%Y-%m-%d", "ISO format (YYYY-MM-DD)"),
            ("%d_%m_%Y", "European (DD_MM_YYYY)"),
            ("%Y%m%d_%H%M%S", "With time (YYYYMMDD_HHMMSS)"),
            ("%B_%d_%Y", "Long month (Month_DD_YYYY)")
        ]

        print("\nSame file with different date formats:")
        for fmt, description in formats:
            pattern = RenamePattern(
                pattern="{date}_photo",
                date_format=fmt
            )
            previews = renamer.preview_rename(files, pattern)
            for _, new, _ in previews:
                print(f"  {description:30} -> {new}")


def demo_placeholders():
    """Demo 6: Available placeholders"""
    print("\n" + "=" * 70)
    print("DEMO 6: Placeholder Reference")
    print("=" * 70)

    print("\nAvailable placeholders for pattern building:")
    print()
    print("FILE INFORMATION:")
    print("  {name}       - Original name without extension")
    print("  {ext}        - File extension (without dot)")
    print("  {parent}     - Parent folder name")
    print()
    print("NUMBERING:")
    print("  {num}        - Sequential number with padding")
    print()
    print("DATES:")
    print("  {date}       - File modification date")
    print("  {created}    - File creation date")
    print("  {exif_date}  - EXIF date from images (if available)")
    print()
    print("FILE SIZE:")
    print("  {size}       - Size in bytes")
    print("  {sizekb}     - Size in kilobytes")
    print("  {sizemb}     - Size in megabytes")
    print()
    print("HASH:")
    print("  {hash}       - Short hash (8 chars)")
    print("  {hash16}     - Medium hash (16 chars)")
    print()
    print("IMAGE METADATA:")
    print("  {width}      - Image width (if image)")
    print("  {height}     - Image height (if image)")
    print()
    print("EXAMPLES:")
    print("  {date}_{name}_{num}        -> 20251212_vacation_001.jpg")
    print("  {parent}_{num}             -> Photos_001.jpg")
    print("  IMG_{date}_{hash}          -> IMG_20251212_a1b2c3d4.jpg")


def demo_regex_mode():
    """Demo 7: Regex find and replace"""
    print("\n" + "=" * 70)
    print("DEMO 7: Regex Mode")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create files with patterns
        test_files = [
            "IMG_2023_001.jpg",
            "IMG_2023_002.jpg",
            "IMG_2024_003.jpg"
        ]

        files = []
        for name in test_files:
            file = tmppath / name
            file.write_text("content")
            files.append(str(file))

        renamer = BatchRenamer()

        print("\nOriginal files:")
        for f in test_files:
            print(f"  {f}")

        # Use regex to extract year and number
        print("\nUsing regex to reformat (capture groups):")
        pattern = RenamePattern(
            pattern="Photo_$1_No$2",  # $1 = year, $2 = number
            find=r"IMG_(\d{4})_(\d+)",
            replace="",
            use_regex=True
        )

        previews = renamer.preview_rename(files, pattern)
        for old, new, _ in previews:
            print(f"  {old} -> {new}")


def demo_history():
    """Demo 8: History tracking"""
    print("\n" + "=" * 70)
    print("DEMO 8: History Tracking and Undo")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        history_file = tmppath / "history.json"
        history = RenameHistory(history_file)

        # Simulate multiple operations
        print("\nSimulating rename operations...")
        for i in range(3):
            operations = [
                {
                    'old_path': f'/path/to/file_{i}_{j}.txt',
                    'new_path': f'/path/to/renamed_{j}.txt',
                    'success': True
                }
                for j in range(3)
            ]

            history.add_entry(
                operation_id=f"op_{i}",
                operations=operations,
                pattern_used=f"pattern_{i}",
                total_files=3,
                success_count=3
            )
            print(f"  Operation {i+1}: Renamed 3 files")

        # Show history
        print("\nRecent history:")
        entries = history.get_history(limit=3)
        for i, entry in enumerate(entries, 1):
            print(f"\n  {i}. {entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"     Operation ID: {entry.operation_id}")
            print(f"     Pattern: {entry.pattern_used}")
            print(f"     Files: {entry.success_count}/{entry.total_files}")
            print(f"     Can undo: {entry.can_undo}")

        # Statistics
        stats = history.get_statistics()
        print("\nStatistics:")
        print(f"  Total operations: {stats['total_operations']}")
        print(f"  Total files renamed: {stats['total_files_renamed']}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")


def run_all_demos():
    """Run all demonstrations"""
    print("=" * 70)
    print("OPERATIONS MODULE - FEATURE DEMONSTRATION")
    print("=" * 70)
    print()
    print("This demo showcases all major features of the operations module.")
    print()

    demos = [
        demo_basic_rename,
        demo_pattern_library,
        demo_text_operations,
        demo_collision_handling,
        demo_date_formats,
        demo_placeholders,
        demo_regex_mode,
        demo_history,
    ]

    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"\n[ERROR] Demo failed: {demo.__name__}")
            print(f"  {str(e)}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("DEMO COMPLETED")
    print("=" * 70)
    print()
    print("For more information:")
    print("  - Import tests: python operations/test_imports.py")
    print("  - Functional tests: python operations/test_batch_rename.py")
    print("  - Integration tests: python operations/test_integration.py")
    print("  - Full report: operations/VERIFICATION_REPORT.md")
    print()


if __name__ == "__main__":
    run_all_demos()
