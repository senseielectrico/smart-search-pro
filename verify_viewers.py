#!/usr/bin/env python
"""
Verify Data Viewers Installation
=================================

Quick verification script to check all viewer components are properly installed.

Usage:
    python verify_viewers.py
"""

import sys
import os
from pathlib import Path

# Set UTF-8 output for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')


def check_import(module_name, class_name=None):
    """Check if a module/class can be imported"""
    try:
        module = __import__(module_name, fromlist=[class_name] if class_name else [])
        if class_name:
            cls = getattr(module, class_name)
            return True, f"[OK] {module_name}.{class_name}"
        return True, f"[OK] {module_name}"
    except ImportError as e:
        return False, f"[FAIL] {module_name}{('.' + class_name) if class_name else ''}: {e}"
    except Exception as e:
        return False, f"[FAIL] {module_name}{('.' + class_name) if class_name else ''}: {e}"


def check_file(file_path):
    """Check if a file exists"""
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        return True, f"[OK] {os.path.basename(file_path)} ({size:,} bytes)"
    return False, f"[FAIL] {os.path.basename(file_path)} not found"


def main():
    """Run verification checks"""
    print("=" * 70)
    print("Data Viewers Installation Verification")
    print("=" * 70)
    print()

    all_passed = True

    # Check PyQt6
    print("1. Checking PyQt6 dependency...")
    success, msg = check_import('PyQt6.QtWidgets', 'QApplication')
    print(f"   {msg}")
    if not success:
        all_passed = False
        print("   → Install PyQt6: pip install PyQt6")
    print()

    # Check viewer files
    print("2. Checking viewer module files...")
    base_path = Path(__file__).parent / "viewers"

    files_to_check = [
        "__init__.py",
        "database_viewer.py",
        "json_viewer.py",
        "data_viewer_factory.py",
        "README.md"
    ]

    for file_name in files_to_check:
        file_path = base_path / file_name
        success, msg = check_file(str(file_path))
        print(f"   {msg}")
        if not success:
            all_passed = False
    print()

    # Check UI integration files
    print("3. Checking UI integration files...")
    ui_path = Path(__file__).parent / "ui"

    ui_files = [
        "database_panel.py",
        "json_tree_widget.py"
    ]

    for file_name in ui_files:
        file_path = ui_path / file_name
        success, msg = check_file(str(file_path))
        print(f"   {msg}")
        if not success:
            all_passed = False
    print()

    # Check viewer imports
    print("4. Checking viewer module imports...")

    viewer_imports = [
        ('viewers.database_viewer', 'DatabaseViewer'),
        ('viewers.database_viewer', 'SQLiteConnection'),
        ('viewers.json_viewer', 'JSONViewer'),
        ('viewers.json_viewer', 'JSONTreeModel'),
        ('viewers.data_viewer_factory', 'DataViewerFactory'),
        ('viewers.data_viewer_factory', 'ViewerType'),
    ]

    for module, class_name in viewer_imports:
        success, msg = check_import(module, class_name)
        print(f"   {msg}")
        if not success:
            all_passed = False
    print()

    # Check UI integration imports
    print("5. Checking UI integration imports...")

    ui_imports = [
        ('ui.database_panel', 'DatabasePanel'),
        ('ui.json_tree_widget', 'JSONTreeWidget'),
    ]

    for module, class_name in ui_imports:
        success, msg = check_import(module, class_name)
        print(f"   {msg}")
        if not success:
            all_passed = False
    print()

    # Check test file
    print("6. Checking test file...")
    test_file = Path(__file__).parent / "test_viewers.py"
    success, msg = check_file(str(test_file))
    print(f"   {msg}")
    if not success:
        all_passed = False
    print()

    # Check documentation
    print("7. Checking documentation files...")

    doc_files = [
        "VIEWERS_QUICK_START.md",
        "VIEWERS_INTEGRATION_GUIDE.md",
        "VIEWERS_IMPLEMENTATION_SUMMARY.md"
    ]

    for file_name in doc_files:
        file_path = Path(__file__).parent / file_name
        success, msg = check_file(str(file_path))
        print(f"   {msg}")
        if not success:
            all_passed = False
    print()

    # Optional dependencies
    print("8. Checking optional dependencies...")

    optional_imports = [
        ('openpyxl', None, 'For Excel export from database viewer'),
        ('yaml', None, 'For YAML file viewing'),
    ]

    for module, class_name, purpose in optional_imports:
        success, msg = check_import(module, class_name)
        status = "[OK]" if success else "[OPTIONAL]"
        print(f"   {status} {module} - {purpose}")
        if not success:
            print(f"      Install with: pip install {module if module != 'yaml' else 'PyYAML'}")
    print()

    # Summary
    print("=" * 70)
    if all_passed:
        print("[SUCCESS] ALL CHECKS PASSED!")
        print()
        print("The viewers are correctly installed and ready to use.")
        print()
        print("Next steps:")
        print("  1. Run test suite: python test_viewers.py")
        print("  2. Read quick start: VIEWERS_QUICK_START.md")
        print("  3. Integrate into your app: VIEWERS_INTEGRATION_GUIDE.md")
    else:
        print("[FAILED] SOME CHECKS FAILED")
        print()
        print("Please fix the issues above before using the viewers.")
        print("See error messages for specific problems.")
    print("=" * 70)
    print()

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
