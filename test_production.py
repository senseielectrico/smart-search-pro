#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Search - Production Environment Test

Quick tests to verify the application is ready for production.

Usage:
    python test_production.py
"""

import sys
import os
from pathlib import Path


def test_python_version():
    """Test Python version is 3.8+"""
    print("[TEST] Python Version...")
    version_info = sys.version_info

    if version_info.major >= 3 and version_info.minor >= 8:
        print(f"  PASS: Python {version_info.major}.{version_info.minor}.{version_info.micro}\n")
        return True
    else:
        print(f"  FAIL: Python {version_info.major}.{version_info.minor} (need 3.8+)\n")
        return False


def test_platform():
    """Test Windows platform"""
    print("[TEST] Windows Platform...")

    if sys.platform == "win32":
        print(f"  PASS: Windows detected\n")
        return True
    else:
        print(f"  FAIL: Not Windows (detected: {sys.platform})\n")
        return False


def test_imports():
    """Test core module imports"""
    print("[TEST] Core Module Imports...")

    modules_to_test = [
        ("PyQt6", "PyQt6"),
        ("win32com", "win32com.client"),
        ("comtypes", "comtypes"),
        ("main", "main"),
        ("backend", "backend"),
        ("ui", "ui"),
        ("categories", "categories"),
        ("classifier", "classifier"),
        ("file_manager", "file_manager"),
        ("utils", "utils"),
    ]

    all_ok = True

    for module_name, import_name in modules_to_test:
        try:
            __import__(import_name)
            print(f"  PASS: {module_name}")
        except ImportError as e:
            print(f"  FAIL: {module_name} - {str(e)[:50]}")
            all_ok = False
        except Exception as e:
            print(f"  WARN: {module_name} - {str(e)[:50]}")

    print()
    return all_ok


def test_files_exist():
    """Test all required files exist"""
    print("[TEST] Required Files...")

    script_dir = Path(__file__).parent
    required_files = [
        "smart_search.pyw",
        "main.py",
        "backend.py",
        "ui.py",
        "categories.py",
        "classifier.py",
        "file_manager.py",
        "utils.py",
        "config.py",
        "start.bat",
        "run.bat",
        "install.bat",
        "verify_setup.py",
        "requirements.txt",
    ]

    all_ok = True

    for filename in required_files:
        filepath = script_dir / filename
        if filepath.exists():
            print(f"  PASS: {filename}")
        else:
            print(f"  FAIL: {filename} not found")
            all_ok = False

    print()
    return all_ok


def test_pyw_syntax():
    """Test smart_search.pyw syntax"""
    print("[TEST] smart_search.pyw Syntax...")

    try:
        import py_compile
        script_dir = Path(__file__).parent
        pyw_file = script_dir / "smart_search.pyw"

        py_compile.compile(str(pyw_file), doraise=True)
        print("  PASS: Syntax is valid\n")
        return True
    except py_compile.PyCompileError as e:
        print(f"  FAIL: {str(e)[:100]}\n")
        return False


def test_config_dir():
    """Test config directory creation"""
    print("[TEST] Config Directory...")

    try:
        config_dir = Path.home() / ".smart_search"
        config_dir.mkdir(parents=True, exist_ok=True)

        if config_dir.exists():
            print(f"  PASS: Config directory ready: {config_dir}\n")
            return True
        else:
            print(f"  FAIL: Could not create config directory\n")
            return False
    except Exception as e:
        print(f"  FAIL: {str(e)}\n")
        return False


def test_pyqt_basic():
    """Test PyQt6 can initialize"""
    print("[TEST] PyQt6 Initialization...")

    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont

        # Don't create a full application, just verify imports
        print("  PASS: PyQt6 imports successful\n")
        return True
    except Exception as e:
        print(f"  FAIL: {str(e)[:100]}\n")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("SMART SEARCH - PRODUCTION ENVIRONMENT TEST")
    print("=" * 70 + "\n")

    tests = [
        ("Python Version", test_python_version),
        ("Windows Platform", test_platform),
        ("Core Modules", test_imports),
        ("Required Files", test_files_exist),
        ("PYW Syntax", test_pyw_syntax),
        ("Config Directory", test_config_dir),
        ("PyQt6 Initialization", test_pyqt_basic),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[ERROR] {test_name}: {str(e)}\n")
            results.append((test_name, False))

    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70 + "\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "[OK]" if result else "[XX]"
        print(f"{symbol} {test_name:<30} {status}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\nStatus: READY FOR PRODUCTION")
        print("\nNext steps:")
        print("  1. Run: start.bat")
        print("  2. Perform manual tests")
        print("  3. Deploy to production")
        return 0
    else:
        print("\nStatus: ISSUES DETECTED")
        print("\nFix the failures above before deploying.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    print("\n" + "=" * 70 + "\n")
    sys.exit(exit_code)
