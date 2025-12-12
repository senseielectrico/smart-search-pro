"""
Archive Module - Complete Usage Examples
Demonstrates all features of the archive module
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from archive.sevenzip_manager import (
    SevenZipManager, CompressionLevel, ArchiveFormat, ExtractionProgress
)
from archive.archive_analyzer import ArchiveAnalyzer
from archive.recursive_extractor import RecursiveExtractor, RecursiveProgress
from archive.password_cracker import PasswordCracker


def example_basic_operations():
    """Example 1: Basic archive operations"""
    print("=" * 60)
    print("Example 1: Basic Archive Operations")
    print("=" * 60)

    manager = SevenZipManager()

    # Check 7-Zip installation
    print(f"\n7-Zip found at: {manager.seven_zip_path}")

    # Create a test archive
    print("\nCreating archive...")

    test_files = [
        "example.py",
        "README.md"
    ]

    archive_path = "test_archive.7z"

    try:
        success = manager.create_archive(
            archive_path=archive_path,
            source_paths=test_files,
            format=ArchiveFormat.SEVEN_ZIP,
            compression_level=CompressionLevel.NORMAL
        )

        if success:
            print(f"Archive created: {archive_path}")
            print(f"Size: {os.path.getsize(archive_path)} bytes")

            # List contents
            print("\nArchive contents:")
            entries = manager.list_contents(archive_path)

            for entry in entries:
                path = entry.get('Path', '')
                size = entry.get('Size', 0)
                print(f"  - {path} ({size} bytes)")

            # Test integrity
            print("\nTesting archive integrity...")
            is_valid, message = manager.test_archive(archive_path)
            print(f"  {message}")

            # Cleanup
            os.remove(archive_path)
            print("\nCleaned up test archive")

    except Exception as e:
        print(f"Error: {str(e)}")

    print()


def example_password_protection():
    """Example 2: Password-protected archives"""
    print("=" * 60)
    print("Example 2: Password Protection")
    print("=" * 60)

    manager = SevenZipManager()

    # Create encrypted archive
    password = "SecurePassword123!"
    archive_path = "encrypted.7z"

    print(f"\nCreating encrypted archive with password: {password}")

    try:
        success = manager.create_archive(
            archive_path=archive_path,
            source_paths=["example_usage.py"],
            format=ArchiveFormat.SEVEN_ZIP,
            compression_level=CompressionLevel.MAXIMUM,
            password=password
        )

        if success:
            print(f"Encrypted archive created: {archive_path}")

            # Try without password (should fail)
            print("\nTrying to list contents without password...")
            try:
                manager.list_contents(archive_path)
                print("  ERROR: Should have failed!")
            except ValueError:
                print("  Correctly rejected - password required")

            # List with correct password
            print("\nListing contents with password...")
            entries = manager.list_contents(archive_path, password=password)
            print(f"  Found {len(entries)} entries")

            # Cleanup
            os.remove(archive_path)
            print("\nCleaned up test archive")

    except Exception as e:
        print(f"Error: {str(e)}")

    print()


def example_archive_analysis():
    """Example 3: Archive analysis"""
    print("=" * 60)
    print("Example 3: Archive Analysis")
    print("=" * 60)

    manager = SevenZipManager()
    analyzer = ArchiveAnalyzer()

    # Create test archive
    archive_path = "analysis_test.zip"

    print("\nCreating test archive...")

    try:
        manager.create_archive(
            archive_path=archive_path,
            source_paths=[".", "*.py"],  # Current directory Python files
            format=ArchiveFormat.ZIP,
            compression_level=CompressionLevel.FAST
        )

        print(f"Archive created: {archive_path}")

        # Analyze
        print("\nAnalyzing archive...")
        stats = analyzer.analyze(archive_path, detect_nested=True)

        print(f"\nStatistics:")
        print(f"  Files: {stats.total_files}")
        print(f"  Folders: {stats.total_folders}")
        print(f"  Total size: {stats.total_size:,} bytes")
        print(f"  Compressed: {stats.packed_size:,} bytes")
        print(f"  Compression ratio: {stats.compression_ratio:.1f}%")

        if stats.file_types:
            print(f"\nFile types:")
            for ext, count in sorted(stats.file_types.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {ext}: {count} files")

        if stats.largest_files:
            print(f"\nLargest files:")
            for path, size in stats.largest_files[:5]:
                print(f"  {path}: {size:,} bytes")

        # Estimate extraction
        print("\nEstimating extraction size...")
        estimate = analyzer.estimate_extraction_size(archive_path)
        print(f"  Uncompressed: {estimate['formatted_size']}")
        print(f"  With overhead: {estimate['estimated_with_overhead']:,} bytes")

        # Cleanup
        os.remove(archive_path)
        print("\nCleaned up test archive")

    except Exception as e:
        print(f"Error: {str(e)}")

    print()


def example_progress_tracking():
    """Example 4: Progress tracking"""
    print("=" * 60)
    print("Example 4: Progress Tracking")
    print("=" * 60)

    manager = SevenZipManager()

    # Create test archive
    archive_path = "progress_test.7z"

    print("\nCreating test archive...")

    try:
        manager.create_archive(
            archive_path=archive_path,
            source_paths=["*.py", "*.md"],
            format=ArchiveFormat.SEVEN_ZIP,
            compression_level=CompressionLevel.NORMAL
        )

        print(f"Archive created: {archive_path}")

        # Extract with progress
        extract_dir = "extracted_progress"

        print("\nExtracting with progress tracking...")

        def progress_callback(progress: ExtractionProgress):
            print(f"  Progress: {progress.percentage:.1f}% - {progress.current_file}")

        success = manager.extract(
            archive_path=archive_path,
            destination=extract_dir,
            progress_callback=progress_callback
        )

        if success:
            print(f"\nExtraction complete!")
            file_count = len([f for f in Path(extract_dir).rglob('*') if f.is_file()])
            print(f"Extracted {file_count} files to {extract_dir}")

        # Cleanup
        import shutil
        shutil.rmtree(extract_dir, ignore_errors=True)
        os.remove(archive_path)
        print("\nCleaned up test files")

    except Exception as e:
        print(f"Error: {str(e)}")

    print()


def example_recursive_extraction():
    """Example 5: Recursive extraction"""
    print("=" * 60)
    print("Example 5: Recursive Extraction")
    print("=" * 60)

    manager = SevenZipManager()

    print("\nCreating nested archives...")

    try:
        # Create inner archive
        inner_archive = "inner.zip"
        manager.create_archive(
            archive_path=inner_archive,
            source_paths=["example_usage.py"],
            format=ArchiveFormat.ZIP
        )
        print(f"  Created: {inner_archive}")

        # Create middle archive containing inner
        middle_archive = "middle.7z"
        manager.create_archive(
            archive_path=middle_archive,
            source_paths=[inner_archive],
            format=ArchiveFormat.SEVEN_ZIP
        )
        print(f"  Created: {middle_archive}")

        # Create outer archive
        outer_archive = "outer.zip"
        manager.create_archive(
            archive_path=outer_archive,
            source_paths=[middle_archive],
            format=ArchiveFormat.ZIP
        )
        print(f"  Created: {outer_archive}")

        # Recursively extract
        print("\nRecursively extracting...")

        extractor = RecursiveExtractor(max_depth=10)
        extract_dir = "fully_extracted"

        def progress_callback(progress: RecursiveProgress):
            print(f"  Depth {progress.current_depth}: {progress.current_archive}")

        stats = extractor.extract_recursive(
            archive_path=outer_archive,
            destination=extract_dir,
            progress_callback=progress_callback
        )

        print(f"\nExtraction complete!")
        print(f"  Archives extracted: {stats['archives_extracted']}")
        print(f"  Maximum depth: {stats['depth_reached']}")
        print(f"  Files extracted: {stats['files_extracted']}")

        # Cleanup
        import shutil
        shutil.rmtree(extract_dir, ignore_errors=True)
        for archive in [inner_archive, middle_archive, outer_archive]:
            if os.path.exists(archive):
                os.remove(archive)
        print("\nCleaned up test files")

    except Exception as e:
        print(f"Error: {str(e)}")

    print()


def example_password_recovery():
    """Example 6: Password recovery (EDUCATIONAL ONLY!)"""
    print("=" * 60)
    print("Example 6: Password Recovery (Educational)")
    print("=" * 60)
    print("\nWARNING: Only use on your own archives!")
    print()

    manager = SevenZipManager()
    cracker = PasswordCracker()

    # Create test archive with common password
    archive_path = "crackme.7z"
    password = "password123"  # Intentionally weak

    print(f"Creating archive with password: {password}")

    try:
        manager.create_archive(
            archive_path=archive_path,
            source_paths=["example_usage.py"],
            format=ArchiveFormat.SEVEN_ZIP,
            password=password
        )

        print(f"Archive created: {archive_path}")

        # Attempt recovery
        print("\nAttempting dictionary attack...")

        attempts = 0

        def progress_callback(progress):
            nonlocal attempts
            attempts = progress.attempts
            if progress.attempts % 10 == 0:
                print(f"  Attempts: {progress.attempts}, Current: {progress.current_password}")

        found = cracker.dictionary_attack(
            archive_path=archive_path,
            use_common=True,
            use_variations=True,
            progress_callback=progress_callback
        )

        if found:
            print(f"\nPassword found: '{found}'")
            print(f"Total attempts: {attempts}")
        else:
            print("\nPassword not found in dictionary")

        # Cleanup
        os.remove(archive_path)
        print("\nCleaned up test archive")

    except Exception as e:
        print(f"Error: {str(e)}")

    print()


def example_split_archives():
    """Example 7: Split/multi-volume archives"""
    print("=" * 60)
    print("Example 7: Split Archives")
    print("=" * 60)

    manager = SevenZipManager()

    print("\nCreating split archive (100KB volumes)...")

    archive_path = "split.7z"

    try:
        # Create split archive
        manager.create_archive(
            archive_path=archive_path,
            source_paths=["*.py", "*.md"],
            format=ArchiveFormat.SEVEN_ZIP,
            compression_level=CompressionLevel.NORMAL,
            split_size='100k'  # 100KB volumes
        )

        # List split files
        print("\nSplit archive volumes:")
        split_files = [
            f for f in os.listdir('.')
            if f.startswith('split.7z')
        ]

        total_size = 0
        for split_file in sorted(split_files):
            size = os.path.getsize(split_file)
            total_size += size
            print(f"  {split_file}: {size:,} bytes")

        print(f"\nTotal size: {total_size:,} bytes")

        # Extract (7-Zip handles multi-volume automatically)
        print("\nExtracting split archive...")
        extract_dir = "extracted_split"

        manager.extract(
            archive_path=archive_path,
            destination=extract_dir
        )

        print(f"Extraction complete to {extract_dir}")

        # Cleanup
        import shutil
        shutil.rmtree(extract_dir, ignore_errors=True)
        for split_file in split_files:
            os.remove(split_file)
        print("\nCleaned up test files")

    except Exception as e:
        print(f"Error: {str(e)}")

    print()


def example_file_tree():
    """Example 8: File tree preview"""
    print("=" * 60)
    print("Example 8: File Tree Preview")
    print("=" * 60)

    manager = SevenZipManager()
    analyzer = ArchiveAnalyzer()

    archive_path = "tree_test.zip"

    print("\nCreating test archive...")

    try:
        manager.create_archive(
            archive_path=archive_path,
            source_paths=["."],
            format=ArchiveFormat.ZIP
        )

        # Get text preview
        print("\nArchive contents (text preview):")
        preview = analyzer.preview_as_text(archive_path, max_items=20)
        print(preview)

        # Cleanup
        os.remove(archive_path)
        print("\nCleaned up test archive")

    except Exception as e:
        print(f"Error: {str(e)}")

    print()


def run_all_examples():
    """Run all examples"""
    print("\n")
    print("=" * 60)
    print("Smart Search Pro - Archive Module Examples")
    print("=" * 60)
    print("\n")

    examples = [
        example_basic_operations,
        example_password_protection,
        example_archive_analysis,
        example_progress_tracking,
        example_recursive_extraction,
        example_password_recovery,
        example_split_archives,
        example_file_tree,
    ]

    for i, example in enumerate(examples, 1):
        try:
            example()
            print()
        except Exception as e:
            print(f"Example {i} failed: {str(e)}\n")

    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_examples()
