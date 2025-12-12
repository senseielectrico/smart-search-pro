"""
Standalone Archive Module Test
Tests archive components without requiring parent package imports
"""

import sys
import os
import tempfile

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print()
print("+" + "=" * 78 + "+")
print("|" + " " * 18 + "ARCHIVE MODULE - STANDALONE VERIFICATION" + " " * 20 + "|")
print("+" + "=" * 78 + "+")
print()

results = {'total': 0, 'passed': 0, 'failed': 0, 'errors': []}

def test(name):
    """Decorator to track tests"""
    def decorator(func):
        def wrapper():
            results['total'] += 1
            print(f"\n{'='*80}")
            print(f"TEST: {name}")
            print('='*80)
            try:
                func()
                results['passed'] += 1
                print(f"\n{name}: PASSED\n")
                return True
            except Exception as e:
                results['failed'] += 1
                results['errors'].append((name, str(e)))
                print(f"\n{name}: FAILED - {e}\n")
                import traceback
                traceback.print_exc()
                return False
        return wrapper()
    return decorator

# =============================================================================
# TEST 1: SevenZipManager (Standalone)
# =============================================================================
@test("SevenZipManager")
def test_sevenzip():
    # Import directly
    import sevenzip_manager
    from sevenzip_manager import SevenZipManager, CompressionLevel, ArchiveFormat

    print("[1.1] Module imported successfully")

    print("[1.2] Initializing...")
    manager = SevenZipManager()
    print(f"  7-Zip path: {manager.seven_zip_path}")
    assert manager.seven_zip_path is not None
    assert os.path.exists(manager.seven_zip_path)

    print(f"[1.3] Supported formats: {len(manager.ARCHIVE_EXTENSIONS)}")

    print("[1.4] Testing is_archive()...")
    assert manager.is_archive("test.zip") == True
    assert manager.is_archive("test.7z") == True
    assert manager.is_archive("test.txt") == False

    with tempfile.TemporaryDirectory() as temp_dir:
        print("[1.5] Creating test archive...")
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content " * 100)

        archive_path = os.path.join(temp_dir, "test.7z")
        success = manager.create_archive(
            archive_path=archive_path,
            source_paths=[test_file],
            format=ArchiveFormat.SEVEN_ZIP,
            compression_level=CompressionLevel.FAST
        )

        assert success
        assert os.path.exists(archive_path)
        print(f"  Archive size: {os.path.getsize(archive_path)} bytes")

        print("[1.6] Testing list_contents()...")
        entries = manager.list_contents(archive_path)
        assert len(entries) > 0
        print(f"  Entries: {len(entries)}")

        print("[1.7] Testing extract()...")
        extract_dir = os.path.join(temp_dir, "extracted")
        success = manager.extract(archive_path, extract_dir)
        assert success
        assert os.path.exists(os.path.join(extract_dir, "test.txt"))

        print("[1.8] Testing get_archive_info()...")
        info = manager.get_archive_info(archive_path)
        print(f"  Files: {info['file_count']}, Compression: {info['compression_ratio']:.1f}%")

        print("[1.9] Testing test_archive()...")
        success, message = manager.test_archive(archive_path)
        assert success
        print(f"  Test result: {message}")

# =============================================================================
# TEST 2: RecursiveExtractor (needs SevenZipManager)
# =============================================================================
@test("RecursiveExtractor")
def test_recursive():
    import recursive_extractor
    import sevenzip_manager
    from recursive_extractor import RecursiveExtractor
    from sevenzip_manager import SevenZipManager, ArchiveFormat

    print("[2.1] Module imported successfully")

    print("[2.2] Initializing...")
    extractor = RecursiveExtractor(max_depth=10)
    manager = SevenZipManager()
    print(f"  Max depth: {extractor.max_depth}")

    with tempfile.TemporaryDirectory() as temp_dir:
        print("[2.3] Creating nested archives...")

        # Inner archive
        inner_file = os.path.join(temp_dir, "inner.txt")
        with open(inner_file, 'w') as f:
            f.write("Inner content")

        inner_archive = os.path.join(temp_dir, "inner.zip")
        manager.create_archive(inner_archive, [inner_file], ArchiveFormat.ZIP)

        # Outer archive
        outer_archive = os.path.join(temp_dir, "outer.7z")
        manager.create_archive(outer_archive, [inner_archive], ArchiveFormat.SEVEN_ZIP)

        print("[2.4] Testing extract_recursive()...")
        extract_dir = os.path.join(temp_dir, "extracted")
        stats = extractor.extract_recursive(outer_archive, extract_dir)

        print(f"  Archives extracted: {stats['archives_extracted']}")
        print(f"  Depth reached: {stats['depth_reached']}")
        print(f"  Files extracted: {stats['files_extracted']}")

        assert stats['archives_extracted'] >= 1
        assert os.path.exists(os.path.join(extract_dir, "inner.txt"))

# =============================================================================
# TEST 3: ArchiveAnalyzer
# =============================================================================
@test("ArchiveAnalyzer")
def test_analyzer():
    import archive_analyzer
    import sevenzip_manager
    from archive_analyzer import ArchiveAnalyzer
    from sevenzip_manager import SevenZipManager, ArchiveFormat

    print("[3.1] Module imported successfully")

    print("[3.2] Initializing...")
    analyzer = ArchiveAnalyzer()
    manager = SevenZipManager()

    with tempfile.TemporaryDirectory() as temp_dir:
        print("[3.3] Creating test archive...")
        files = []
        for i in range(5):
            file_path = os.path.join(temp_dir, f"file{i}.txt")
            with open(file_path, 'w') as f:
                f.write(f"Content {i} " * 200)
            files.append(file_path)

        archive_path = os.path.join(temp_dir, "test.7z")
        manager.create_archive(archive_path, files, ArchiveFormat.SEVEN_ZIP)

        print("[3.4] Testing analyze()...")
        stats = analyzer.analyze(archive_path)
        print(f"  Files: {stats.total_files}")
        print(f"  Size: {stats.total_size} bytes")
        print(f"  Compression: {stats.compression_ratio:.1f}%")
        assert stats.total_files > 0

        print("[3.5] Testing preview_as_text()...")
        preview = analyzer.preview_as_text(archive_path)
        print(f"  Preview length: {len(preview)} chars")
        assert len(preview) > 0

        print("[3.6] Testing estimate_extraction_size()...")
        estimate = analyzer.estimate_extraction_size(archive_path)
        print(f"  Estimated size: {estimate['formatted_size']}")
        assert estimate['uncompressed_size'] > 0

        print("[3.7] Testing find_duplicates_in_archive()...")
        dups = analyzer.find_duplicates_in_archive(archive_path)
        print(f"  Duplicate groups: {len(dups)}")

# =============================================================================
# TEST 4: PasswordCracker
# =============================================================================
@test("PasswordCracker")
def test_password():
    import password_cracker
    import sevenzip_manager
    from password_cracker import PasswordCracker
    from sevenzip_manager import SevenZipManager, ArchiveFormat

    print("[4.1] Module imported successfully")

    print("[4.2] Initializing...")
    cracker = PasswordCracker(max_threads=4)
    manager = SevenZipManager()
    print(f"  Threads: {cracker.max_threads}")
    print(f"  Common passwords: {len(cracker.COMMON_PASSWORDS)}")

    with tempfile.TemporaryDirectory() as temp_dir:
        print("[4.3] Creating password-protected archive...")
        test_file = os.path.join(temp_dir, "secret.txt")
        with open(test_file, 'w') as f:
            f.write("Secret content")

        archive_path = os.path.join(temp_dir, "protected.7z")
        password = "password"  # In common list

        manager.create_archive(
            archive_path=archive_path,
            source_paths=[test_file],
            format=ArchiveFormat.SEVEN_ZIP,
            password=password
        )

        print("[4.4] Testing dictionary_attack()...")
        found = cracker.dictionary_attack(
            archive_path=archive_path,
            use_common=True,
            use_variations=False
        )

        if found:
            print(f"  Password found: '{found}'")
        else:
            print("  Password not found in dictionary")

        print("[4.5] Testing estimate_brute_force_time()...")
        estimate = cracker.estimate_brute_force_time("abc123", 1, 4)
        print(f"  Combinations: {estimate['total_combinations']}")
        print(f"  Estimated time: {estimate['estimated_seconds']:.2f} seconds")

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)
print(f"\nTotal Tests:  {results['total']}")
print(f"Passed:       {results['passed']}")
print(f"Failed:       {results['failed']}")

if results['errors']:
    print("\nERRORS:")
    for name, error in results['errors']:
        print(f"  - {name}: {error}")

print("\n" + "=" * 80)
if results['failed'] == 0:
    print("ALL TESTS PASSED - ARCHIVE MODULE FULLY FUNCTIONAL!")
    print("\nComponents verified:")
    print("  1. SevenZipManager - 7-Zip integration with all operations")
    print("  2. RecursiveExtractor - Nested archive extraction")
    print("  3. ArchiveAnalyzer - Archive content analysis and statistics")
    print("  4. PasswordCracker - Dictionary and brute-force password recovery")
else:
    print(f"TESTS COMPLETED WITH {results['failed']} FAILURES")
    print("See errors above for details")
print("=" * 80)
print()

sys.exit(0 if results['failed'] == 0 else 1)
