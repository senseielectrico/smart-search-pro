#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Search Pro v3.0 - Full Launch Test
Tests all backend modules and UI initialization
"""

import sys
import os

# Fix console encoding on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def test_backend_modules():
    """Test all backend modules"""
    print("=" * 60)
    print("SMART SEARCH PRO v3.0 - BACKEND MODULE TEST")
    print("=" * 60)
    print()

    modules_loaded = []
    errors = []

    # Test 1: Core module
    print("[1/8] Testing core module...")
    try:
        from core import Config, Database, EventBus, get_logger
        modules_loaded.extend(['Config', 'Database', 'EventBus', 'get_logger'])
        print("      [OK] core module")
    except ImportError as e:
        print(f"      [FAIL] core: {e}")
        errors.append(("core", str(e)))

    # Test 2: Operations module
    print("[2/8] Testing operations module...")
    try:
        from operations import OperationsManager, FileCopier, FileMover
        modules_loaded.extend(['OperationsManager', 'FileCopier', 'FileMover'])
        print("      [OK] operations module")
    except ImportError as e:
        print(f"      [FAIL] operations: {e}")
        errors.append(("operations", str(e)))

    # Test 3: Duplicates module
    print("[3/8] Testing duplicates module...")
    try:
        from duplicates import DuplicateScanner, HashAlgorithm, DuplicateGroup
        modules_loaded.extend(['DuplicateScanner', 'HashAlgorithm', 'DuplicateGroup'])
        print("      [OK] duplicates module")
    except ImportError as e:
        print(f"      [FAIL] duplicates: {e}")
        errors.append(("duplicates", str(e)))

    # Test 4: Archive module
    print("[4/8] Testing archive module...")
    try:
        from archive import SevenZipManager, ArchiveAnalyzer, RecursiveExtractor
        modules_loaded.extend(['SevenZipManager', 'ArchiveAnalyzer', 'RecursiveExtractor'])
        print("      [OK] archive module")
    except ImportError as e:
        print(f"      [FAIL] archive: {e}")
        errors.append(("archive", str(e)))

    # Test 5: Vault module
    print("[5/8] Testing vault module...")
    try:
        from vault import SecureVault
        modules_loaded.append('SecureVault')
        print("      [OK] vault module")
    except ImportError as e:
        print(f"      [FAIL] vault: {e}")
        errors.append(("vault", str(e)))

    # Test 6: Export module
    print("[6/8] Testing export module...")
    try:
        from export import CSVExporter, ExcelExporter, HTMLExporter, JSONExporter
        modules_loaded.extend(['CSVExporter', 'ExcelExporter', 'HTMLExporter', 'JSONExporter'])
        print("      [OK] export module")
    except ImportError as e:
        print(f"      [FAIL] export: {e}")
        errors.append(("export", str(e)))

    # Test 7: Preview module
    print("[7/8] Testing preview module...")
    try:
        from preview import PreviewManager, MetadataExtractor
        modules_loaded.extend(['PreviewManager', 'MetadataExtractor'])
        print("      [OK] preview module")
    except ImportError as e:
        print(f"      [FAIL] preview: {e}")
        errors.append(("preview", str(e)))

    # Test 8: System module
    print("[8/8] Testing system module...")
    try:
        from system import SystemTrayIcon, HotkeyManager, ShellIntegration
        modules_loaded.extend(['SystemTrayIcon', 'HotkeyManager', 'ShellIntegration'])
        print("      [OK] system module")
    except ImportError as e:
        print(f"      [FAIL] system: {e}")
        errors.append(("system", str(e)))

    print()
    print(f"Loaded {len(modules_loaded)} backend components")

    return len(errors) == 0, errors


def test_ui_modules():
    """Test PyQt6 and UI modules"""
    print()
    print("=" * 60)
    print("TESTING UI MODULES")
    print("=" * 60)
    print()

    errors = []

    # Test PyQt6
    print("[1/3] Testing PyQt6...")
    try:
        from PyQt6.QtWidgets import QApplication, QMainWindow
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont
        print("      [OK] PyQt6")
    except ImportError as e:
        print(f"      [FAIL] PyQt6: {e}")
        errors.append(("PyQt6", str(e)))
        return False, errors

    # Test MainWindow import
    print("[2/3] Testing MainWindow import...")
    try:
        from ui.main_window import MainWindow
        print("      [OK] MainWindow")
    except ImportError as e:
        print(f"      [FAIL] MainWindow: {e}")
        errors.append(("MainWindow", str(e)))
        return False, errors

    # Test window creation
    print("[3/3] Testing MainWindow creation...")
    try:
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)

        window = MainWindow()

        # Get info
        tabs = window.results_tabs
        tab_count = tabs.count()
        tab_names = [tabs.tabText(i) for i in range(tab_count)]

        print(f"      Window Title: {window.windowTitle()}")
        print(f"      Window Size: {window.size().width()} x {window.size().height()}")
        print(f"      Tab Count: {tab_count}")
        print(f"      Tabs: {tab_names}")

        # Check menus
        menubar = window.menuBar()
        menus = []
        for action in menubar.actions():
            if action.menu():
                menus.append(action.text().replace('&', ''))
        print(f"      Menus: {menus}")

        # Check operations manager
        if hasattr(window, 'operations_manager') and window.operations_manager:
            print("      OperationsManager: Connected")
        else:
            print("      OperationsManager: Not connected (OK - lazy init)")

        print("      [OK] MainWindow created successfully")

    except Exception as e:
        import traceback
        print(f"      [FAIL] MainWindow creation: {e}")
        traceback.print_exc()
        errors.append(("MainWindow creation", str(e)))
        return False, errors

    return True, errors


if __name__ == "__main__":
    print()
    print("*" * 60)
    print("   SMART SEARCH PRO v3.0 - FULL LAUNCH DIAGNOSTIC")
    print("*" * 60)
    print()

    # Test backend
    backend_ok, backend_errors = test_backend_modules()

    # Test UI
    ui_ok, ui_errors = test_ui_modules()

    # Summary
    print()
    print("=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    print()

    if backend_ok and ui_ok:
        print("[OK] ALL TESTS PASSED")
        print()
        print("Smart Search Pro v3.0 is ready!")
        print()
        print("To start the application:")
        print("  python app.py")
        print("  or run SmartSearchPro.exe")
        sys.exit(0)
    else:
        print("[FAIL] SOME TESTS FAILED")
        print()
        all_errors = backend_errors + ui_errors
        for module, error in all_errors:
            print(f"  - {module}: {error}")
        sys.exit(1)
