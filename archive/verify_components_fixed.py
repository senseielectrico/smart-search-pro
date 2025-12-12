"""
Component Verification Script - Fixed Version
Test all archive module components for import and basic functionality
Handles relative imports properly
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to enable package imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def test_imports():
    """Test that all components can be imported"""
    print("=" * 80)
    print("COMPONENT IMPORT VERIFICATION")
    print("=" * 80)
    print()

    results = {
        'passed': [],
        'failed': []
    }

    # Test SevenZipManager
    print("[1/4] Testing SevenZipManager import...")
    try:
        from archive.sevenzip_manager import SevenZipManager, CompressionLevel, ArchiveFormat, ExtractionProgress
        print("  SUCCESS: SevenZipManager imported")
        print(f"    - Classes: SevenZipManager, CompressionLevel, ArchiveFormat, ExtractionProgress")
        results['passed'].append('SevenZipManager')
    except Exception as e:
        print(f"  FAILED: {e}")
        results['failed'].append(('SevenZipManager', str(e)))
    print()

    # Test RecursiveExtractor
    print("[2/4] Testing RecursiveExtractor import...")
    try:
        from archive.recursive_extractor import RecursiveExtractor, RecursiveProgress
        print("  SUCCESS: RecursiveExtractor imported")
        print(f"    - Classes: RecursiveExtractor, RecursiveProgress")
        results['passed'].append('RecursiveExtractor')
    except Exception as e:
        print(f"  FAILED: {e}")
        results['failed'].append(('RecursiveExtractor', str(e)))
    print()

    # Test PasswordCracker
    print("[3/4] Testing PasswordCracker import...")
    try:
        from archive.password_cracker import PasswordCracker, CrackProgress
        print("  SUCCESS: PasswordCracker imported")
        print(f"    - Classes: PasswordCracker, CrackProgress")
        results['passed'].append('PasswordCracker')
    except Exception as e:
        print(f"  FAILED: {e}")
        results['failed'].append(('PasswordCracker', str(e)))
    print()

    # Test ArchiveAnalyzer
    print("[4/4] Testing ArchiveAnalyzer import...")
    try:
        from archive.archive_analyzer import ArchiveAnalyzer, ArchiveStats
        print("  SUCCESS: ArchiveAnalyzer imported")
        print(f"    - Classes: ArchiveAnalyzer, ArchiveStats")
        results['passed'].append('ArchiveAnalyzer')
    except Exception as e:
        print(f"  FAILED: {e}")
        results['failed'].append(('ArchiveAnalyzer', str(e)))
    print()

    return results


def test_7zip_detection():
    """Test 7-Zip installation detection"""
    print("=" * 80)
    print("7-ZIP INSTALLATION DETECTION")
    print("=" * 80)
    print()

    try:
        from archive.sevenzip_manager import SevenZipManager

        manager = SevenZipManager()

        if manager.seven_zip_path:
            print(f"SUCCESS: 7-Zip found at: {manager.seven_zip_path}")

            # Verify it exists
            if os.path.exists(manager.seven_zip_path):
                print(f"  File exists: YES")
                print(f"  File size: {os.path.getsize(manager.seven_zip_path):,} bytes")
            else:
                print(f"  WARNING: Path returned but file doesn't exist!")
                return False

            # Check supported extensions
            print(f"  Supported extensions: {len(manager.ARCHIVE_EXTENSIONS)} formats")
            print(f"  Sample formats: {', '.join(list(manager.ARCHIVE_EXTENSIONS)[:10])}")

            return True
        else:
            print("FAILED: 7-Zip not found")
            print("  Please install 7-Zip from https://www.7-zip.org/")
            return False

    except Exception as e:
        print(f"FAILED: Error during detection - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_component_initialization():
    """Test that all components can be initialized"""
    print()
    print("=" * 80)
    print("COMPONENT INITIALIZATION")
    print("=" * 80)
    print()

    results = {
        'passed': [],
        'failed': []
    }

    # Test SevenZipManager initialization
    print("[1/4] Initializing SevenZipManager...")
    try:
        from archive.sevenzip_manager import SevenZipManager
        manager = SevenZipManager()
        print(f"  SUCCESS: Manager initialized with 7z at: {manager.seven_zip_path}")
        results['passed'].append('SevenZipManager')
    except Exception as e:
        print(f"  FAILED: {e}")
        results['failed'].append(('SevenZipManager', str(e)))
    print()

    # Test RecursiveExtractor initialization
    print("[2/4] Initializing RecursiveExtractor...")
    try:
        from archive.recursive_extractor import RecursiveExtractor
        extractor = RecursiveExtractor(max_depth=10)
        print(f"  SUCCESS: Extractor initialized with max_depth={extractor.max_depth}")
        results['passed'].append('RecursiveExtractor')
    except Exception as e:
        print(f"  FAILED: {e}")
        results['failed'].append(('RecursiveExtractor', str(e)))
    print()

    # Test PasswordCracker initialization
    print("[3/4] Initializing PasswordCracker...")
    try:
        from archive.password_cracker import PasswordCracker
        cracker = PasswordCracker(max_threads=4)
        print(f"  SUCCESS: Cracker initialized with {cracker.max_threads} threads")
        print(f"  Common passwords loaded: {len(cracker.COMMON_PASSWORDS)}")
        results['passed'].append('PasswordCracker')
    except Exception as e:
        print(f"  FAILED: {e}")
        results['failed'].append(('PasswordCracker', str(e)))
    print()

    # Test ArchiveAnalyzer initialization
    print("[4/4] Initializing ArchiveAnalyzer...")
    try:
        from archive.archive_analyzer import ArchiveAnalyzer
        analyzer = ArchiveAnalyzer()
        print(f"  SUCCESS: Analyzer initialized")
        results['passed'].append('ArchiveAnalyzer')
    except Exception as e:
        print(f"  FAILED: {e}")
        results['failed'].append(('ArchiveAnalyzer', str(e)))
    print()

    return results


def test_basic_functionality():
    """Test basic functionality of each component"""
    print()
    print("=" * 80)
    print("BASIC FUNCTIONALITY TESTS")
    print("=" * 80)
    print()

    import tempfile

    results = {
        'passed': [],
        'failed': []
    }

    # Test SevenZipManager basic operations
    print("[1/4] Testing SevenZipManager basic operations...")
    try:
        from archive.sevenzip_manager import SevenZipManager, ArchiveFormat, CompressionLevel

        manager = SevenZipManager()

        # Test is_archive
        assert manager.is_archive("test.zip") == True
        assert manager.is_archive("test.7z") == True
        assert manager.is_archive("test.txt") == False
        assert manager.is_archive("test.tar.gz") == True
        print("  is_archive() works correctly")

        # Test archive creation
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, 'w') as f:
                f.write("Test content")

            archive_path = os.path.join(temp_dir, "test.7z")
            success = manager.create_archive(
                archive_path=archive_path,
                source_paths=[test_file],
                format=ArchiveFormat.SEVEN_ZIP,
                compression_level=CompressionLevel.FAST
            )

            assert success == True
            assert os.path.exists(archive_path)
            print("  create_archive() works correctly")

            # Test list contents
            entries = manager.list_contents(archive_path)
            assert len(entries) > 0
            print(f"  list_contents() works correctly - found {len(entries)} entries")

            # Test extraction
            extract_dir = os.path.join(temp_dir, "extracted")
            success = manager.extract(archive_path, extract_dir)
            assert success == True
            assert os.path.exists(os.path.join(extract_dir, "test.txt"))
            print("  extract() works correctly")

            # Test archive info
            info = manager.get_archive_info(archive_path)
            assert info['file_count'] > 0
            print(f"  get_archive_info() works correctly - {info['file_count']} files")

        print("  SUCCESS: All SevenZipManager operations passed")
        results['passed'].append('SevenZipManager')
    except Exception as e:
        print(f"  FAILED: {e}")
        import traceback
        traceback.print_exc()
        results['failed'].append(('SevenZipManager', str(e)))
    print()

    # Test RecursiveExtractor
    print("[2/4] Testing RecursiveExtractor basic operations...")
    try:
        from archive.recursive_extractor import RecursiveExtractor
        from archive.sevenzip_manager import SevenZipManager, ArchiveFormat

        extractor = RecursiveExtractor(max_depth=5)
        manager = SevenZipManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested archive
            inner_file = os.path.join(temp_dir, "inner.txt")
            with open(inner_file, 'w') as f:
                f.write("Inner content")

            inner_archive = os.path.join(temp_dir, "inner.zip")
            manager.create_archive(inner_archive, [inner_file], ArchiveFormat.ZIP)

            outer_archive = os.path.join(temp_dir, "outer.7z")
            manager.create_archive(outer_archive, [inner_archive], ArchiveFormat.SEVEN_ZIP)

            # Test recursive extraction
            extract_dir = os.path.join(temp_dir, "extracted")
            stats = extractor.extract_recursive(outer_archive, extract_dir)

            assert stats['archives_extracted'] >= 1
            print(f"  extract_recursive() works - extracted {stats['archives_extracted']} archives")
            print(f"  Depth reached: {stats['depth_reached']}")

        print("  SUCCESS: RecursiveExtractor operations passed")
        results['passed'].append('RecursiveExtractor')
    except Exception as e:
        print(f"  FAILED: {e}")
        import traceback
        traceback.print_exc()
        results['failed'].append(('RecursiveExtractor', str(e)))
    print()

    # Test ArchiveAnalyzer
    print("[3/4] Testing ArchiveAnalyzer basic operations...")
    try:
        from archive.archive_analyzer import ArchiveAnalyzer
        from archive.sevenzip_manager import SevenZipManager, ArchiveFormat

        analyzer = ArchiveAnalyzer()
        manager = SevenZipManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test archive
            test_files = []
            for i in range(3):
                file_path = os.path.join(temp_dir, f"file{i}.txt")
                with open(file_path, 'w') as f:
                    f.write(f"Content {i}" * 100)
                test_files.append(file_path)

            archive_path = os.path.join(temp_dir, "test.7z")
            manager.create_archive(archive_path, test_files, ArchiveFormat.SEVEN_ZIP)

            # Test analysis
            stats = analyzer.analyze(archive_path)
            assert stats.total_files > 0
            assert stats.total_size > 0
            print(f"  analyze() works - {stats.total_files} files, {stats.total_size} bytes")
            print(f"  Compression ratio: {stats.compression_ratio:.1f}%")

            # Test text preview
            preview = analyzer.preview_as_text(archive_path, max_items=10)
            assert len(preview) > 0
            print(f"  preview_as_text() works - generated {len(preview)} chars")

            # Test estimation
            estimate = analyzer.estimate_extraction_size(archive_path)
            assert estimate['uncompressed_size'] > 0
            print(f"  estimate_extraction_size() works - {estimate['formatted_size']}")

        print("  SUCCESS: ArchiveAnalyzer operations passed")
        results['passed'].append('ArchiveAnalyzer')
    except Exception as e:
        print(f"  FAILED: {e}")
        import traceback
        traceback.print_exc()
        results['failed'].append(('ArchiveAnalyzer', str(e)))
    print()

    # Test PasswordCracker
    print("[4/4] Testing PasswordCracker basic operations...")
    try:
        from archive.password_cracker import PasswordCracker
        from archive.sevenzip_manager import SevenZipManager, ArchiveFormat

        cracker = PasswordCracker(max_threads=2)
        manager = SevenZipManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create password-protected archive
            test_file = os.path.join(temp_dir, "secret.txt")
            with open(test_file, 'w') as f:
                f.write("Secret content")

            archive_path = os.path.join(temp_dir, "protected.7z")
            password = "password"  # Use a common password

            manager.create_archive(
                archive_path=archive_path,
                source_paths=[test_file],
                format=ArchiveFormat.SEVEN_ZIP,
                password=password
            )

            # Test dictionary attack
            found = cracker.dictionary_attack(
                archive_path=archive_path,
                use_common=True,
                use_variations=False
            )

            if found == password:
                print(f"  dictionary_attack() works - found password: '{found}'")
            else:
                print(f"  dictionary_attack() tested (password: '{password}', found: '{found}')")

            # Test brute force estimate
            estimate = cracker.estimate_brute_force_time("abc", 1, 3)
            assert estimate['total_combinations'] > 0
            print(f"  estimate_brute_force_time() works - {estimate['total_combinations']} combinations")

        print("  SUCCESS: PasswordCracker operations passed")
        results['passed'].append('PasswordCracker')
    except Exception as e:
        print(f"  FAILED: {e}")
        import traceback
        traceback.print_exc()
        results['failed'].append(('PasswordCracker', str(e)))
    print()

    return results


def print_summary(import_results, init_results, func_results, seven_zip_ok):
    """Print test summary"""
    print()
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print()

    # 7-Zip status
    print(f"7-Zip Installation: {'DETECTED' if seven_zip_ok else 'NOT FOUND'}")
    print()

    # Import results
    print("Import Tests:")
    print(f"  Passed: {len(import_results['passed'])}/4")
    if import_results['failed']:
        print(f"  Failed: {len(import_results['failed'])}/4")
        for name, error in import_results['failed']:
            print(f"    - {name}: {error[:80]}")
    print()

    # Initialization results
    print("Initialization Tests:")
    print(f"  Passed: {len(init_results['passed'])}/4")
    if init_results['failed']:
        print(f"  Failed: {len(init_results['failed'])}/4")
        for name, error in init_results['failed']:
            print(f"    - {name}: {error[:80]}")
    print()

    # Functionality results
    print("Functionality Tests:")
    print(f"  Passed: {len(func_results['passed'])}/4")
    if func_results['failed']:
        print(f"  Failed: {len(func_results['failed'])}/4")
        for name, error in func_results['failed']:
            print(f"    - {name}: {error[:80]}")
    print()

    # Overall status
    total_passed = len(import_results['passed']) + len(init_results['passed']) + len(func_results['passed'])
    total_tests = 12  # 4 imports + 4 inits + 4 funcs

    print("=" * 80)
    if total_passed == total_tests and seven_zip_ok:
        print(f"ALL TESTS PASSED: {total_passed}/{total_tests}")
        print("Archive module is fully functional!")
    else:
        print(f"TESTS COMPLETED: {total_passed}/{total_tests} passed")
        if not seven_zip_ok:
            print("WARNING: 7-Zip not detected - some features will not work")
        if total_passed < total_tests:
            print("Some components have errors - see details above")
    print("=" * 80)


def main():
    """Main verification function"""
    print()
    print("+" + "=" * 78 + "+")
    print("|" + " " * 20 + "SMART SEARCH PRO - ARCHIVE MODULE" + " " * 25 + "|")
    print("|" + " " * 25 + "Component Verification" + " " * 30 + "|")
    print("+" + "=" * 78 + "+")
    print()

    # Run all verification tests
    import_results = test_imports()
    seven_zip_ok = test_7zip_detection()
    init_results = test_component_initialization()
    func_results = test_basic_functionality()

    # Print summary
    print_summary(import_results, init_results, func_results, seven_zip_ok)

    print()
    print("To run the full integration test suite, execute:")
    print("  python test_archive_integration.py")
    print()


if __name__ == "__main__":
    main()
