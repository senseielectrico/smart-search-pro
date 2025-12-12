"""
Test Archive Integration
Comprehensive tests for 7-Zip integration
"""

import os
import tempfile
import shutil
from pathlib import Path

from sevenzip_manager import SevenZipManager, CompressionLevel, ArchiveFormat
from archive_analyzer import ArchiveAnalyzer
from recursive_extractor import RecursiveExtractor
from password_cracker import PasswordCracker


def test_sevenzip_detection():
    """Test 7-Zip detection"""
    print("Testing 7-Zip detection...")

    manager = SevenZipManager()
    print(f"  7-Zip found at: {manager.seven_zip_path}")

    assert manager.seven_zip_path is not None
    assert os.path.exists(manager.seven_zip_path)

    print("  PASS\n")


def test_archive_creation():
    """Test archive creation"""
    print("Testing archive creation...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        test_file1 = os.path.join(temp_dir, "test1.txt")
        test_file2 = os.path.join(temp_dir, "test2.txt")

        with open(test_file1, 'w') as f:
            f.write("Test content 1" * 1000)

        with open(test_file2, 'w') as f:
            f.write("Test content 2" * 1000)

        # Create archive
        archive_path = os.path.join(temp_dir, "test.7z")

        manager = SevenZipManager()
        success = manager.create_archive(
            archive_path=archive_path,
            source_paths=[test_file1, test_file2],
            format=ArchiveFormat.SEVEN_ZIP,
            compression_level=CompressionLevel.NORMAL
        )

        assert success
        assert os.path.exists(archive_path)

        print(f"  Archive created: {archive_path}")
        print(f"  Size: {os.path.getsize(archive_path)} bytes")
        print("  PASS\n")


def test_archive_extraction():
    """Test archive extraction"""
    print("Testing archive extraction...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test archive
        test_file = os.path.join(temp_dir, "source.txt")
        with open(test_file, 'w') as f:
            f.write("Test content" * 100)

        archive_path = os.path.join(temp_dir, "test.zip")
        extract_dir = os.path.join(temp_dir, "extracted")

        manager = SevenZipManager()

        # Create archive
        manager.create_archive(
            archive_path=archive_path,
            source_paths=[test_file],
            format=ArchiveFormat.ZIP,
            compression_level=CompressionLevel.FAST
        )

        # Extract
        success = manager.extract(
            archive_path=archive_path,
            destination=extract_dir
        )

        assert success
        assert os.path.exists(os.path.join(extract_dir, "source.txt"))

        print(f"  Extraction successful")
        print(f"  Files extracted: {len(os.listdir(extract_dir))}")
        print("  PASS\n")


def test_password_protected():
    """Test password-protected archives"""
    print("Testing password-protected archives...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test file
        test_file = os.path.join(temp_dir, "secret.txt")
        with open(test_file, 'w') as f:
            f.write("Secret content")

        archive_path = os.path.join(temp_dir, "encrypted.7z")
        password = "test123"

        manager = SevenZipManager()

        # Create encrypted archive
        success = manager.create_archive(
            archive_path=archive_path,
            source_paths=[test_file],
            format=ArchiveFormat.SEVEN_ZIP,
            compression_level=CompressionLevel.NORMAL,
            password=password
        )

        assert success

        # Try to extract without password (should fail)
        extract_dir1 = os.path.join(temp_dir, "fail")
        try:
            manager.extract(archive_path, extract_dir1)
            assert False, "Should have failed without password"
        except:
            print("  Correctly rejected wrong/missing password")

        # Extract with correct password
        extract_dir2 = os.path.join(temp_dir, "success")
        success = manager.extract(
            archive_path=archive_path,
            destination=extract_dir2,
            password=password
        )

        assert success
        assert os.path.exists(os.path.join(extract_dir2, "secret.txt"))

        print("  Password protection working")
        print("  PASS\n")


def test_archive_analysis():
    """Test archive analysis"""
    print("Testing archive analysis...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        files = []
        for i in range(5):
            file_path = os.path.join(temp_dir, f"file{i}.txt")
            with open(file_path, 'w') as f:
                f.write(f"Content {i}" * 100)
            files.append(file_path)

        # Create archive
        archive_path = os.path.join(temp_dir, "test.7z")
        manager = SevenZipManager()
        manager.create_archive(
            archive_path=archive_path,
            source_paths=files,
            format=ArchiveFormat.SEVEN_ZIP,
            compression_level=CompressionLevel.NORMAL
        )

        # Analyze
        analyzer = ArchiveAnalyzer()
        stats = analyzer.analyze(archive_path)

        print(f"  Files: {stats.total_files}")
        print(f"  Total size: {stats.total_size} bytes")
        print(f"  Compressed: {stats.packed_size} bytes")
        print(f"  Ratio: {stats.compression_ratio:.1f}%")

        assert stats.total_files == 5
        assert stats.total_size > 0
        assert stats.compression_ratio > 0

        print("  PASS\n")


def test_recursive_extraction():
    """Test recursive extraction of nested archives"""
    print("Testing recursive extraction...")

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = SevenZipManager()

        # Create inner archive
        inner_file = os.path.join(temp_dir, "inner.txt")
        with open(inner_file, 'w') as f:
            f.write("Inner content")

        inner_archive = os.path.join(temp_dir, "inner.zip")
        manager.create_archive(
            archive_path=inner_archive,
            source_paths=[inner_file],
            format=ArchiveFormat.ZIP
        )

        # Create outer archive containing inner archive
        outer_archive = os.path.join(temp_dir, "outer.7z")
        manager.create_archive(
            archive_path=outer_archive,
            source_paths=[inner_archive],
            format=ArchiveFormat.SEVEN_ZIP
        )

        # Recursively extract
        extract_dir = os.path.join(temp_dir, "extracted")
        extractor = RecursiveExtractor()

        stats = extractor.extract_recursive(
            archive_path=outer_archive,
            destination=extract_dir
        )

        print(f"  Archives extracted: {stats['archives_extracted']}")
        print(f"  Depth reached: {stats['depth_reached']}")
        print(f"  Files extracted: {stats['files_extracted']}")

        # Verify inner.txt was extracted
        assert os.path.exists(os.path.join(extract_dir, "inner.txt"))

        print("  PASS\n")


def test_password_recovery():
    """Test password recovery (dictionary attack)"""
    print("Testing password recovery...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create password-protected archive
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content")

        archive_path = os.path.join(temp_dir, "protected.7z")
        password = "password123"  # Common password

        manager = SevenZipManager()
        manager.create_archive(
            archive_path=archive_path,
            source_paths=[test_file],
            format=ArchiveFormat.SEVEN_ZIP,
            password=password
        )

        # Try to crack it
        cracker = PasswordCracker()

        def progress_callback(progress):
            if progress.attempts % 10 == 0:
                print(f"  Attempts: {progress.attempts}, Testing: {progress.current_password}")

        found_password = cracker.dictionary_attack(
            archive_path=archive_path,
            use_common=True,
            use_variations=True,
            progress_callback=progress_callback
        )

        assert found_password == password
        print(f"  Password found: {found_password}")
        print("  PASS\n")


def test_list_contents():
    """Test listing archive contents"""
    print("Testing archive contents listing...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create folder structure
        folder = os.path.join(temp_dir, "test_folder")
        os.makedirs(folder)

        for i in range(3):
            with open(os.path.join(folder, f"file{i}.txt"), 'w') as f:
                f.write(f"Content {i}")

        # Create archive
        archive_path = os.path.join(temp_dir, "test.7z")
        manager = SevenZipManager()
        manager.create_archive(
            archive_path=archive_path,
            source_paths=[folder],
            format=ArchiveFormat.SEVEN_ZIP
        )

        # List contents
        entries = manager.list_contents(archive_path)

        print(f"  Total entries: {len(entries)}")
        for entry in entries[:5]:  # Show first 5
            print(f"    - {entry.get('Path', 'Unknown')} ({entry.get('Size', 0)} bytes)")

        assert len(entries) > 0

        print("  PASS\n")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("7-Zip Integration Test Suite")
    print("=" * 60)
    print()

    tests = [
        test_sevenzip_detection,
        test_archive_creation,
        test_archive_extraction,
        test_password_protected,
        test_archive_analysis,
        test_recursive_extraction,
        test_list_contents,
        test_password_recovery,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  FAILED: {str(e)}\n")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
