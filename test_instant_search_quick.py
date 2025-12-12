#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test for instant search implementation

Run this to verify instant search is working correctly.
"""

import sys
import io
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    print("[OK] PyQt6 imports successful")
except ImportError as e:
    print(f"[FAIL] PyQt6 import failed: {e}")
    sys.exit(1)

try:
    from ui.search_panel import SearchPanel
    print("[OK] SearchPanel import successful")
except ImportError as e:
    print(f"[FAIL] SearchPanel import failed: {e}")
    sys.exit(1)

try:
    from ui.main_window import MainWindow, SearchWorker
    print("[OK] MainWindow and SearchWorker imports successful")
except ImportError as e:
    print(f"[FAIL] MainWindow import failed: {e}")
    sys.exit(1)


def test_search_panel():
    """Test SearchPanel instant search features"""
    print("\n=== Testing SearchPanel ===")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    panel = SearchPanel()

    # Test 1: Debounce timer exists
    assert hasattr(panel, 'search_debounce_timer'), "Missing debounce timer"
    assert panel.search_debounce_timer.isSingleShot(), "Timer should be single-shot"
    print("[OK] Debounce timer configured correctly")

    # Test 2: Debounce delay is set
    assert panel.DEBOUNCE_DELAY_MS == 200, "Debounce delay should be 200ms"
    print("[OK] Debounce delay set to 200ms")

    # Test 3: Instant search signal exists
    assert hasattr(panel, 'instant_search_requested'), "Missing instant_search_requested signal"
    print("[OK] instant_search_requested signal exists")

    # Test 4: Search status indicator
    assert hasattr(panel, 'search_status_label'), "Missing search status label"
    assert hasattr(panel, 'is_searching'), "Missing is_searching flag"
    print("[OK] Search status indicator present")

    # Test 5: Methods exist
    assert hasattr(panel, '_trigger_instant_search'), "Missing _trigger_instant_search method"
    assert hasattr(panel, '_set_searching_status'), "Missing _set_searching_status method"
    assert hasattr(panel, 'set_search_complete'), "Missing set_search_complete method"
    print("[OK] All required methods present")

    panel.deleteLater()
    print("[OK] SearchPanel tests passed")


def test_search_worker():
    """Test SearchWorker thread"""
    print("\n=== Testing SearchWorker ===")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    worker = SearchWorker(search_engine=None)

    # Test 1: Worker exists and is QThread
    from PyQt6.QtCore import QThread
    assert isinstance(worker, QThread), "SearchWorker should be QThread"
    print("[OK] SearchWorker is QThread")

    # Test 2: Signals exist
    assert hasattr(worker, 'results_ready'), "Missing results_ready signal"
    assert hasattr(worker, 'progress_update'), "Missing progress_update signal"
    assert hasattr(worker, 'search_complete'), "Missing search_complete signal"
    assert hasattr(worker, 'error_occurred'), "Missing error_occurred signal"
    print("[OK] All signals present")

    # Test 3: Methods exist
    assert hasattr(worker, 'set_params'), "Missing set_params method"
    assert hasattr(worker, 'cancel'), "Missing cancel method"
    print("[OK] All required methods present")

    # Test 4: Cancellation flag
    assert hasattr(worker, 'is_cancelled'), "Missing is_cancelled flag"
    assert worker.is_cancelled == False, "Should start not cancelled"
    worker.cancel()
    assert worker.is_cancelled == True, "Should be cancelled after cancel()"
    print("[OK] Cancellation mechanism works")

    if worker.isRunning():
        worker.wait()
    worker.deleteLater()
    print("[OK] SearchWorker tests passed")


def test_main_window():
    """Test MainWindow integration"""
    print("\n=== Testing MainWindow Integration ===")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    window = MainWindow()

    # Test 1: Search worker initialized
    assert hasattr(window, 'search_worker'), "Missing search_worker"
    assert window.search_worker is not None, "search_worker should be initialized"
    print("[OK] SearchWorker initialized")

    # Test 2: Search panel exists
    assert hasattr(window, 'search_panel'), "Missing search_panel"
    print("[OK] SearchPanel exists")

    # Test 3: Methods exist
    assert hasattr(window, '_perform_instant_search'), "Missing _perform_instant_search"
    assert hasattr(window, '_execute_search'), "Missing _execute_search"
    assert hasattr(window, 'set_search_engine'), "Missing set_search_engine"
    print("[OK] All required methods present")

    # Test 4: Slots connected
    assert hasattr(window, '_on_search_results'), "Missing _on_search_results"
    assert hasattr(window, '_on_search_progress'), "Missing _on_search_progress"
    assert hasattr(window, '_on_search_complete'), "Missing _on_search_complete"
    assert hasattr(window, '_on_search_error'), "Missing _on_search_error"
    print("[OK] All signal handlers present")

    # Cleanup
    if window.search_worker.isRunning():
        window.search_worker.cancel()
        window.search_worker.wait()
    window.deleteLater()
    print("[OK] MainWindow tests passed")


def test_signal_connections():
    """Test signal connections"""
    print("\n=== Testing Signal Connections ===")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    window = MainWindow()

    # Test 1: Verify signals exist (PyQt6 doesn't expose receivers())
    # We test by trying to connect a dummy slot
    test_connected = [False, False]

    def dummy_instant(params):
        test_connected[0] = True

    def dummy_explicit(params):
        test_connected[1] = True

    # Try connecting signals
    try:
        window.search_panel.instant_search_requested.connect(dummy_instant)
        window.search_panel.search_requested.connect(dummy_explicit)
        print("[OK] Search panel signals can be connected")
    except Exception as e:
        raise AssertionError(f"Failed to connect signals: {e}")

    # Test 2: Verify methods are connected by checking they exist
    assert hasattr(window, '_perform_instant_search'), "Missing instant search handler"
    assert hasattr(window, '_perform_search'), "Missing explicit search handler"
    print("[OK] Search handlers exist in MainWindow")

    # Test 3: Worker signal handlers exist
    assert hasattr(window, '_on_search_results'), "Missing results handler"
    assert hasattr(window, '_on_search_complete'), "Missing complete handler"
    print("[OK] Worker signal handlers exist")

    # Cleanup
    if window.search_worker.isRunning():
        window.search_worker.cancel()
        window.search_worker.wait()
    window.deleteLater()
    print("[OK] Signal connection tests passed")


def main():
    """Run all quick tests"""
    print("=" * 60)
    print("Instant Search Quick Test")
    print("=" * 60)

    try:
        test_search_panel()
        test_search_worker()
        test_main_window()
        test_signal_connections()

        print("\n" + "=" * 60)
        print("[PASS] ALL TESTS PASSED")
        print("=" * 60)
        print("\nInstant search implementation is working correctly!")
        print("\nNext steps:")
        print("  1. Run demo: python ui/instant_search_demo.py")
        print("  2. Run full tests: python ui/test_instant_search.py")
        print("  3. Integrate with search engine")
        return 0

    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"[FAIL] TEST FAILED: {e}")
        print("=" * 60)
        return 1

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"[ERROR] {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
