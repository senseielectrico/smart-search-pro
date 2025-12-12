"""
Quick verification script for the duplicate finder module.
"""

import sys
import io
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def main():
    print("=" * 60)
    print("DUPLICATE FINDER MODULE - QUICK VERIFICATION")
    print("=" * 60)

    # Test 1: Imports
    print("\n1. Testing imports...")
    try:
        from duplicates import (
            DuplicateScanner,
            FileHasher,
            HashAlgorithm,
            DuplicateGroupManager,
            SelectionStrategy,
            RecycleBinAction,
        )
        print("   ✓ All imports successful")
    except ImportError as e:
        print(f"   ✗ Import failed: {e}")
        return 1

    # Test 2: Hash computation
    print("\n2. Testing hash computation...")
    import tempfile
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test content")
            temp_path = Path(f.name)

        hasher = FileHasher(algorithm=HashAlgorithm.SHA256)
        result = hasher.hash_file(temp_path, quick_hash=True, full_hash=True)

        temp_path.unlink()

        if result.success and result.quick_hash and result.full_hash:
            print(f"   ✓ Hash computation working")
            print(f"     Quick: {result.quick_hash[:16]}...")
            print(f"     Full:  {result.full_hash[:16]}...")
        else:
            print("   ✗ Hash computation failed")
            return 1

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return 1

    # Test 3: Duplicate detection
    print("\n3. Testing duplicate detection...")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create duplicates
            content = "Duplicate test content"
            for i in range(3):
                (tmpdir / f"file{i}.txt").write_text(content)

            # Create unique file
            (tmpdir / "unique.txt").write_text("Unique content")

            # Scan
            scanner = DuplicateScanner(use_cache=False)
            groups = scanner.scan([tmpdir], recursive=False)

            if len(groups.groups) == 1 and groups.groups[0].file_count == 3:
                print(f"   ✓ Duplicate detection working")
                print(f"     Found {groups.groups[0].file_count} duplicates")
                print(f"     Wasted: {groups.groups[0].wasted_space} bytes")
            else:
                print(f"   ✗ Unexpected result: {len(groups.groups)} groups")
                return 1

    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Test 4: Selection strategies
    print("\n4. Testing selection strategies...")
    try:
        group = groups.groups[0]
        group.select_by_strategy(SelectionStrategy.KEEP_OLDEST)

        if len(group.selected_for_deletion) == 2:  # Should select 2 out of 3
            print(f"   ✓ Selection strategy working")
            print(f"     Selected {len(group.selected_for_deletion)} for deletion")
        else:
            print(f"   ✗ Unexpected selection count")
            return 1

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return 1

    # Test 5: Check optional dependencies
    print("\n5. Checking optional dependencies...")
    optional = {
        'send2trash': 'Recycle bin support',
        'xxhash': 'Fast hashing',
        'blake3': 'Fastest cryptographic hash',
    }

    for module, desc in optional.items():
        try:
            __import__(module)
            print(f"   ✓ {module:12} ({desc})")
        except ImportError:
            print(f"   - {module:12} (not installed - {desc})")

    print("\n" + "=" * 60)
    print("✓ ALL VERIFICATION TESTS PASSED")
    print("=" * 60)
    print("\nThe duplicate finder module is ready to use!")
    print("\nNext steps:")
    print("  - Run full test suite: pytest test_duplicates.py -v")
    print("  - Check examples: python example.py")
    print("  - Read README.md for usage documentation")

    return 0


if __name__ == '__main__':
    sys.exit(main())
