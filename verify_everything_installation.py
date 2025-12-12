"""
Everything SDK Installation Verifier

Comprehensive verification of Everything SDK installation and functionality.
Checks all components and provides diagnostic information.
"""

import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def print_section(title):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_mark(condition):
    """Return check mark or X."""
    return "✓" if condition else "✗"


def check_everything_exe():
    """Check if Everything.exe is installed."""
    print_section("1. Everything.exe Installation")

    paths = [
        r"C:\Program Files\Everything\Everything.exe",
        r"C:\Program Files (x86)\Everything\Everything.exe",
    ]

    found = False
    for path in paths:
        exists = os.path.exists(path)
        print(f"  {check_mark(exists)} {path}")
        if exists:
            found = True
            try:
                size = os.path.getsize(path)
                print(f"      Size: {size:,} bytes")
            except Exception as e:
                print(f"      Error: {e}")

    return found


def check_everything_dll():
    """Check if Everything DLL is installed."""
    print_section("2. Everything SDK DLL")

    dlls = [
        r"C:\Program Files\Everything\Everything64.dll",
        r"C:\Program Files\Everything\Everything32.dll",
    ]

    found_64 = False
    found_32 = False

    for dll in dlls:
        exists = os.path.exists(dll)
        print(f"  {check_mark(exists)} {dll}")

        if exists:
            if "64" in dll:
                found_64 = True
            else:
                found_32 = True

            try:
                size = os.path.getsize(dll)
                print(f"      Size: {size:,} bytes")
            except Exception as e:
                print(f"      Error: {e}")

    return found_64 or found_32


def check_python_arch():
    """Check Python architecture."""
    print_section("3. Python Architecture")

    import struct
    bits = struct.calcsize("P") * 8

    print(f"  Python version: {sys.version.split()[0]}")
    print(f"  Architecture: {bits}-bit")

    recommended_dll = "Everything64.dll" if bits == 64 else "Everything32.dll"
    dll_path = f"C:\\Program Files\\Everything\\{recommended_dll}"
    dll_exists = os.path.exists(dll_path)

    print(f"\n  Recommended DLL: {recommended_dll}")
    print(f"  {check_mark(dll_exists)} DLL matches Python architecture")

    return dll_exists


def check_everything_running():
    """Check if Everything.exe is running."""
    print_section("4. Everything Service Status")

    try:
        import psutil
        processes = [p for p in psutil.process_iter(['name']) if p.info['name'] == 'Everything.exe']

        if processes:
            print(f"  ✓ Everything.exe is running")
            for p in processes:
                try:
                    print(f"      PID: {p.pid}")
                    print(f"      Memory: {p.memory_info().rss / 1024 / 1024:.1f} MB")
                except Exception:
                    pass
            return True
        else:
            print(f"  ✗ Everything.exe is NOT running")
            return False
    except ImportError:
        print("  ? Cannot check (psutil not installed)")
        return None


def check_sdk_import():
    """Check if SDK can be imported."""
    print_section("5. SDK Import Test")

    try:
        from search.everything_sdk import (
            EverythingSDK,
            EverythingResult,
            EverythingSort,
            get_everything_instance,
        )
        print("  ✓ SDK module imported successfully")
        print(f"      EverythingSDK: {EverythingSDK}")
        print(f"      EverythingResult: {EverythingResult}")
        print(f"      EverythingSort: {EverythingSort}")
        return True
    except Exception as e:
        print(f"  ✗ SDK import failed: {e}")
        return False


def check_sdk_initialization():
    """Check if SDK can be initialized."""
    print_section("6. SDK Initialization")

    try:
        from search.everything_sdk import get_everything_instance

        sdk = get_everything_instance()
        print(f"  ✓ SDK initialized successfully")
        print(f"      Available: {sdk.is_available}")
        print(f"      Using fallback: {sdk.is_using_fallback}")

        return sdk.is_available
    except Exception as e:
        print(f"  ✗ SDK initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_sdk_search():
    """Check if SDK can perform searches."""
    print_section("7. SDK Search Test")

    try:
        from search.everything_sdk import get_everything_instance

        sdk = get_everything_instance()

        # Test search
        import time
        start = time.perf_counter()
        results = sdk.search("*.py", max_results=10)
        elapsed = time.perf_counter() - start

        print(f"  ✓ Search completed successfully")
        print(f"      Query: *.py")
        print(f"      Results: {len(results)}")
        print(f"      Time: {elapsed*1000:.2f}ms")

        if results:
            print(f"\n  Sample result:")
            r = results[0]
            print(f"      Filename: {r.filename}")
            print(f"      Path: {r.path}")
            print(f"      Size: {r.size:,} bytes")
            print(f"      Is folder: {r.is_folder}")

        return len(results) > 0
    except Exception as e:
        print(f"  ✗ Search failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_sdk_features():
    """Check SDK features."""
    print_section("8. SDK Features Test")

    try:
        from search.everything_sdk import get_everything_instance

        sdk = get_everything_instance()

        # Test async search
        print("  Testing async search...")
        results_container = []

        def on_results(results):
            results_container.extend(results)

        thread = sdk.search_async("*.txt", callback=on_results, max_results=5)
        thread.join(timeout=5)

        if results_container:
            print(f"  ✓ Async search: {len(results_container)} results")
        else:
            print(f"  ? Async search: No results")

        # Test caching
        print("  Testing caching...")
        sdk.clear_cache()

        import time
        start1 = time.perf_counter()
        results1 = sdk.search("*.log", max_results=10)
        time1 = time.perf_counter() - start1

        start2 = time.perf_counter()
        results2 = sdk.search("*.log", max_results=10)
        time2 = time.perf_counter() - start2

        speedup = time1 / time2 if time2 > 0 else 0
        print(f"  ✓ Caching: {speedup:.0f}x speedup")

        # Test stats
        print("  Testing stats...")
        stats = sdk.get_stats()
        print(f"  ✓ Stats: {stats}")

        return True
    except Exception as e:
        print(f"  ✗ Features test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_files_exist():
    """Check if all required files exist."""
    print_section("9. Required Files Check")

    files = [
        "search/everything_sdk.py",
        "test_everything.py",
        "examples/everything_integration.py",
        "benchmark_everything.py",
        "install_everything_sdk.ps1",
        "README_EVERYTHING_SDK.md",
        "EVERYTHING_SDK_SETUP.md",
        "IMPLEMENTATION_COMPLETE.md",
        "EVERYTHING_INDEX.md",
    ]

    all_exist = True
    for file in files:
        exists = os.path.exists(file)
        print(f"  {check_mark(exists)} {file}")
        if not exists:
            all_exist = False

    return all_exist


def run_diagnostics():
    """Run all diagnostics."""
    print("\n" + "=" * 70)
    print("  EVERYTHING SDK INSTALLATION VERIFIER")
    print("=" * 70)

    results = {}

    # Run checks
    results['exe'] = check_everything_exe()
    results['dll'] = check_everything_dll()
    results['python'] = check_python_arch()
    results['running'] = check_everything_running()
    results['import'] = check_sdk_import()
    results['init'] = check_sdk_initialization()
    results['search'] = check_sdk_search()
    results['features'] = check_sdk_features()
    results['files'] = check_files_exist()

    # Summary
    print_section("SUMMARY")

    checks = [
        ("Everything.exe installed", results['exe']),
        ("Everything SDK DLL installed", results['dll']),
        ("DLL matches Python architecture", results['python']),
        ("Everything service running", results['running']),
        ("SDK module import", results['import']),
        ("SDK initialization", results['init']),
        ("SDK search functionality", results['search']),
        ("SDK features (async, cache, stats)", results['features']),
        ("All required files present", results['files']),
    ]

    passed = 0
    total = 0

    for name, result in checks:
        if result is not None:
            total += 1
            if result:
                passed += 1
            print(f"  {check_mark(result)} {name}")
        else:
            print(f"  ? {name} (skipped)")

    print(f"\n  PASSED: {passed}/{total} checks")

    # Overall status
    print("\n" + "=" * 70)
    if passed == total:
        print("  STATUS: ✓ EVERYTHING SDK IS FULLY FUNCTIONAL")
        print("=" * 70)
        print("\n  You can now use Everything SDK in your applications!")
        print("\n  Quick start:")
        print("    from search.everything_sdk import get_everything_instance")
        print("    sdk = get_everything_instance()")
        print("    results = sdk.search('*.py', max_results=100)")
        return True
    elif results['init'] and results['search']:
        print("  STATUS: ⚠ EVERYTHING SDK IS WORKING (with warnings)")
        print("=" * 70)
        print("\n  SDK is functional but some checks failed.")
        print("  Check the details above for more information.")
        return True
    else:
        print("  STATUS: ✗ INSTALLATION INCOMPLETE OR FAILED")
        print("=" * 70)
        print("\n  Please fix the issues above.")
        print("\n  Installation help:")
        print("    1. Install Everything from: https://www.voidtools.com/")
        print("    2. Run: powershell -ExecutionPolicy Bypass -File install_everything_sdk.ps1")
        print("    3. Run this script again to verify")
        return False


def main():
    """Main entry point."""
    success = run_diagnostics()

    print("\n" + "=" * 70)
    print("  For more information:")
    print("=" * 70)
    print("  - Main README: README_EVERYTHING_SDK.md")
    print("  - Setup Guide: EVERYTHING_SDK_SETUP.md")
    print("  - File Index: EVERYTHING_INDEX.md")
    print("  - Run tests: python test_everything.py")
    print("  - See examples: python examples/everything_integration.py")
    print("=" * 70)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
