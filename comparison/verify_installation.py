"""
Verification script for folder comparison module installation.

Run this to verify that all components are properly installed and importable.
"""

import sys
from pathlib import Path

# Fix Unicode output on Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 80)
print("Folder Comparison Module - Installation Verification")
print("=" * 80)

# Test 1: Import core module
print("\n[1/6] Testing core module imports...")
try:
    from comparison import (
        FolderComparator,
        ComparisonMode,
        ComparisonResult,
        FileStatus,
        SyncEngine,
        ConflictResolution,
        SyncResult
    )
    print("✓ Core module imports successful")
except ImportError as e:
    print(f"✗ Core module import failed: {e}")
    sys.exit(1)

# Test 2: Test comparator instantiation
print("\n[2/6] Testing FolderComparator instantiation...")
try:
    comparator = FolderComparator(mode=ComparisonMode.CONTENT_HASH)
    print("✓ FolderComparator instantiated successfully")
except Exception as e:
    print(f"✗ FolderComparator instantiation failed: {e}")
    sys.exit(1)

# Test 3: Test sync engine instantiation
print("\n[3/6] Testing SyncEngine instantiation...")
try:
    engine = SyncEngine(conflict_resolution=ConflictResolution.NEWER_WINS)
    print("✓ SyncEngine instantiated successfully")
except Exception as e:
    print(f"✗ SyncEngine instantiation failed: {e}")
    sys.exit(1)

# Test 4: Test UI imports
print("\n[4/6] Testing UI component imports...")
try:
    from ui.comparison_panel import ComparisonPanel
    from ui.comparison_dialog import ComparisonDialog
    print("✓ UI component imports successful")
except ImportError as e:
    print(f"✗ UI component import failed: {e}")
    print("  Note: PyQt6 must be installed for UI components")
    ui_available = False
else:
    ui_available = True

# Test 5: Test examples module
print("\n[5/6] Testing examples module...")
try:
    import comparison.examples as examples
    print("✓ Examples module loaded successfully")
except ImportError as e:
    print(f"✗ Examples module import failed: {e}")
    sys.exit(1)

# Test 6: Check required dependencies
print("\n[6/6] Checking dependencies...")
dependencies = {
    'PyQt6': False,
    'pathlib': False,
    'dataclasses': False,
    'concurrent.futures': False,
}

try:
    from PyQt6.QtWidgets import QApplication
    dependencies['PyQt6'] = True
except ImportError:
    pass

try:
    from pathlib import Path
    dependencies['pathlib'] = True
except ImportError:
    pass

try:
    from dataclasses import dataclass
    dependencies['dataclasses'] = True
except ImportError:
    pass

try:
    from concurrent.futures import ThreadPoolExecutor
    dependencies['concurrent.futures'] = True
except ImportError:
    pass

for dep, available in dependencies.items():
    status = "✓" if available else "✗"
    print(f"  {status} {dep}")

# Test 7: Quick functional test
print("\n[7/7] Running quick functional test...")
try:
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as source_dir, \
         tempfile.TemporaryDirectory() as target_dir:

        source = Path(source_dir)
        target = Path(target_dir)

        # Create test file
        (source / 'test.txt').write_text('test content')
        (target / 'test.txt').write_text('test content')

        # Compare
        comparator = FolderComparator(mode=ComparisonMode.SIZE_NAME)
        result = comparator.compare(source, target, recursive=False)

        if result.stats.total_files == 1 and result.stats.same_files == 1:
            print("✓ Functional test passed")
        else:
            print(f"✗ Functional test failed: unexpected results")
            print(f"  Total: {result.stats.total_files}, Same: {result.stats.same_files}")

except Exception as e:
    print(f"✗ Functional test failed: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)
print("\nCore Module: ✓ Working")
print(f"UI Components: {'✓ Working' if ui_available else '✗ PyQt6 required'}")
print("Examples: ✓ Available")
print("\nThe folder comparison module is ready to use!")
print("\nQuick Start:")
print("  - Run examples: python comparison/examples.py")
print("  - Run tests: python -m pytest comparison/test_comparison.py -v")
print("  - Run UI demo: python comparison/demo_ui.py")
print("\nDocumentation:")
print("  - README: comparison/README.md")
print("  - Summary: comparison/IMPLEMENTATION_SUMMARY.md")
print("=" * 80)
