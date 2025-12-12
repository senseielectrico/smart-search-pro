"""
Verification script for the duplicate finder module.

This script verifies that:
1. All imports work correctly
2. Basic functionality is operational
3. Dependencies are available
"""

import sys
import io
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def verify_imports():
    """Verify all module imports."""
    print("=" * 60)
    print("VERIFICATION: Module Imports")
    print("=" * 60)

    try:
        # Main package import
        from duplicates import (
            # Scanner
            DuplicateScanner,
            ScanProgress,
            ScanStats,

            # Hasher
            FileHasher,
            HashAlgorithm,
            HashResult,

            # Cache
            HashCache,
            CacheStats,

            # Groups
            DuplicateGroup,
            DuplicateGroupManager,
            SelectionStrategy,

            # Actions
            DuplicateAction,
            ActionResult,
            RecycleBinAction,
            MoveToFolderAction,
            PermanentDeleteAction,
            HardLinkAction,
            SymlinkAction,
        )

        print("✓ All imports successful")
        return True

    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def verify_optional_dependencies():
    """Check for optional dependencies."""
    print("\n" + "=" * 60)
    print("VERIFICATION: Optional Dependencies")
    print("=" * 60)

    dependencies = {
        'send2trash': 'Recycle bin support',
        'xxhash': 'xxHash algorithm (fast hashing)',
        'blake3': 'BLAKE3 algorithm (fastest cryptographic hash)',
    }

    results = {}
    for module, description in dependencies.items():
        try:
            __import__(module)
            print(f"✓ {module:15} - Available ({description})")
            results[module] = True
        except ImportError:
            print(f"✗ {module:15} - Not installed ({description})")
            results[module] = False

    return results


def verify_basic_functionality():
    """Test basic functionality."""
    print("\n" + "=" * 60)
    print("VERIFICATION: Basic Functionality")
    print("=" * 60)

    import tempfile
    from duplicates import FileHasher, HashAlgorithm, DuplicateScanner

    try:
        # Test 1: Hash computation
        print("\nTest 1: Hash Computation")
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test content for verification")
            temp_path = Path(f.name)

        try:
            hasher = FileHasher(algorithm=HashAlgorithm.SHA256)
            result = hasher.hash_file(temp_path, quick_hash=True, full_hash=True)

            if result.success and result.quick_hash and result.full_hash:
                print(f"  ✓ Hash computation working")
                print(f"    Quick hash: {result.quick_hash[:16]}...")
                print(f"    Full hash:  {result.full_hash[:16]}...")
            else:
                print(f"  ✗ Hash computation failed")
                return False

        finally:
            temp_path.unlink()

        # Test 2: Scanner initialization
        print("\nTest 2: Scanner Initialization")
        scanner = DuplicateScanner(use_cache=False)
        print(f"  ✓ Scanner created successfully")

        # Test 3: Cache initialization
        print("\nTest 3: Cache Initialization")
        from duplicates import HashCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / 'test_cache.db'
            cache = HashCache(cache_path)
            stats = cache.get_stats()
            print(f"  ✓ Cache initialized (entries: {stats.total_entries})")

        # Test 4: Group management
        print("\nTest 4: Group Management")
        from duplicates import DuplicateGroup, SelectionStrategy

        group = DuplicateGroup(hash_value="test123")

        with tempfile.TemporaryDirectory() as tmpdir:
            import time
            for i in range(3):
                file_path = Path(tmpdir) / f"file{i}.txt"
                file_path.write_text(f"Content {i}")
                group.add_file(file_path, size=100, mtime=time.time() + i)

            print(f"  ✓ Group created with {group.file_count} files")

            group.select_by_strategy(SelectionStrategy.KEEP_OLDEST)
            print(f"  ✓ Selection strategy applied")
            print(f"    Selected {len(group.selected_for_deletion)} for deletion")

        print("\n✓ All basic functionality tests passed")
        return True

    except Exception as e:
        print(f"\n✗ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_algorithm_support():
    """Verify supported hash algorithms."""
    print("\n" + "=" * 60)
    print("VERIFICATION: Hash Algorithm Support")
    print("=" * 60)

    from duplicates import FileHasher, HashAlgorithm
    import tempfile

    # Create test file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Test content")
        temp_path = Path(f.name)

    try:
        algorithms = [
            (HashAlgorithm.MD5, "MD5 (fast, non-cryptographic)"),
            (HashAlgorithm.SHA1, "SHA-1 (deprecated)"),
            (HashAlgorithm.SHA256, "SHA-256 (recommended)"),
        ]

        # Check optional algorithms
        try:
            import xxhash
            algorithms.append((HashAlgorithm.XXHASH, "xxHash (very fast)"))
        except ImportError:
            pass

        try:
            import blake3
            algorithms.append((HashAlgorithm.BLAKE3, "BLAKE3 (fastest cryptographic)"))
        except ImportError:
            pass

        for algo, description in algorithms:
            try:
                hasher = FileHasher(algorithm=algo)
                result = hasher.hash_file(temp_path, full_hash=True)

                if result.success:
                    print(f"✓ {algo.value:12} - Working ({description})")
                else:
                    print(f"✗ {algo.value:12} - Failed ({description})")

            except Exception as e:
                print(f"✗ {algo.value:12} - Error: {e}")

    finally:
        temp_path.unlink()


def create_simple_test():
    """Create and run a simple duplicate detection test."""
    print("\n" + "=" * 60)
    print("VERIFICATION: Simple Duplicate Detection Test")
    print("=" * 60)

    import tempfile
    from duplicates import DuplicateScanner

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create original file
        original = tmpdir / "original.txt"
        content = "This is a test file for duplicate detection" * 100
        original.write_text(content)

        # Create duplicates
        for i in range(3):
            duplicate = tmpdir / f"duplicate_{i}.txt"
            duplicate.write_text(content)

        # Create unique file
        unique = tmpdir / "unique.txt"
        unique.write_text("This is a unique file")

        print(f"\nCreated test files in: {tmpdir}")
        print(f"  - 1 original file")
        print(f"  - 3 duplicate files")
        print(f"  - 1 unique file")

        # Scan for duplicates
        print("\nScanning for duplicates...")
        scanner = DuplicateScanner(use_cache=False)

        progress_updates = []

        def progress_callback(progress):
            if progress.current_file % 2 == 0:  # Report every 2 files
                progress_updates.append(progress.progress_percent)

        groups = scanner.scan([tmpdir], progress_callback=progress_callback)

        print(f"✓ Scan completed")
        print(f"  Found {len(groups.groups)} duplicate group(s)")

        if len(groups.groups) == 1:
            group = groups.groups[0]
            print(f"  Group contains {group.file_count} files")
            print(f"  Wasted space: {group.wasted_space} bytes")

            if group.file_count == 4:  # 1 original + 3 duplicates
                print("✓ Duplicate detection working correctly!")
                return True
            else:
                print(f"✗ Expected 4 files, found {group.file_count}")
                return False
        else:
            print(f"✗ Expected 1 group, found {len(groups.groups)}")
            return False


def main():
    """Run all verification tests."""
    print("\n" + "=" * 60)
    print("SMART SEARCH PRO - DUPLICATE FINDER MODULE VERIFICATION")
    print("=" * 60)

    results = {}

    # Run verification tests
    results['imports'] = verify_imports()
    results['dependencies'] = verify_optional_dependencies()
    results['algorithms'] = verify_algorithm_support()
    results['functionality'] = verify_basic_functionality()
    results['detection'] = create_simple_test()

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    all_passed = all([
        results.get('imports', False),
        results.get('functionality', False),
        results.get('detection', False),
    ])

    if all_passed:
        print("\n✓ ALL VERIFICATION TESTS PASSED")
        print("\nThe duplicate finder module is ready to use!")
        return 0
    else:
        print("\n✗ SOME VERIFICATION TESTS FAILED")
        print("\nPlease review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
