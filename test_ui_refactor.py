"""
Test script to validate UI refactoring
Verifies that signals are properly defined and connected
"""

import re
from pathlib import Path


def test_signals_defined():
    """Test that ResultsTableWidget has the required signals"""
    ui_path = Path(__file__).parent / "ui.py"
    content = ui_path.read_text(encoding='utf-8')

    # Find ResultsTableWidget class
    class_match = re.search(r'class ResultsTableWidget\(QTableWidget\):(.+?)(?=\nclass |\Z)', content, re.DOTALL)
    assert class_match, "ResultsTableWidget class not found"

    class_content = class_match.group(1)

    # Verify signals exist
    assert 'open_requested = pyqtSignal(list)' in class_content, "Missing open_requested signal"
    assert 'open_location_requested = pyqtSignal(list)' in class_content, "Missing open_location_requested signal"
    assert 'copy_requested = pyqtSignal(list)' in class_content, "Missing copy_requested signal"
    assert 'move_requested = pyqtSignal(list)' in class_content, "Missing move_requested signal"

    print("[OK] All signals properly defined in ResultsTableWidget")
    return True


def test_methods_exist():
    """Test that SmartSearchWindow has the required handler methods"""
    ui_path = Path(__file__).parent / "ui.py"
    content = ui_path.read_text(encoding='utf-8')

    # Check that handler methods exist
    assert 'def _open_files_from_list(self, files: list):' in content, "Missing _open_files_from_list method"
    assert 'def _open_location_from_list(self, files: list):' in content, "Missing _open_location_from_list method"
    assert 'def _copy_files_from_list(self, files: list):' in content, "Missing _copy_files_from_list method"
    assert 'def _move_files_from_list(self, files: list):' in content, "Missing _move_files_from_list method"
    assert 'def closeEvent(self, event):' in content, "Missing closeEvent method"

    print("[OK] All handler methods properly defined in SmartSearchWindow")
    return True


def test_no_parent_chains():
    """Test that context menu doesn't use parent().parent().parent() pattern"""
    ui_path = Path(__file__).parent / "ui.py"
    content = ui_path.read_text(encoding='utf-8')

    # Find _show_context_menu method
    method_match = re.search(r'def _show_context_menu\(self, position\):(.+?)(?=\n    def |\Z)', content, re.DOTALL)
    assert method_match, "_show_context_menu method not found"

    method_content = method_match.group(1)

    # Check that it doesn't contain the fragile parent chain
    assert 'parent().parent().parent()' not in method_content, "Still using fragile parent() chain"

    # Verify it uses signals instead
    assert 'open_requested.emit' in method_content, "Not using open_requested signal"
    assert 'open_location_requested.emit' in method_content, "Not using open_location_requested signal"
    assert 'copy_requested.emit' in method_content, "Not using copy_requested signal"
    assert 'move_requested.emit' in method_content, "Not using move_requested signal"

    print("[OK] Context menu properly uses signals instead of parent() chain")
    return True


def test_signal_connections():
    """Test that signals are connected in SmartSearchWindow"""
    ui_path = Path(__file__).parent / "ui.py"
    content = ui_path.read_text(encoding='utf-8')

    # Find _create_action_bar method where connections are made
    method_match = re.search(r'def _create_action_bar\(self\)(.+?)(?=\n    def |\Z)', content, re.DOTALL)
    assert method_match, "_create_action_bar method not found"

    method_content = method_match.group(1)

    # Verify signal connections
    assert 'table.open_requested.connect(self._open_files_from_list)' in method_content, "open_requested not connected"
    assert 'table.open_location_requested.connect(self._open_location_from_list)' in method_content, "open_location_requested not connected"
    assert 'table.copy_requested.connect(self._copy_files_from_list)' in method_content, "copy_requested not connected"
    assert 'table.move_requested.connect(self._move_files_from_list)' in method_content, "move_requested not connected"

    print("[OK] All signals properly connected in _create_action_bar")
    return True


def test_thread_timeouts():
    """Test that QThread.wait() calls have timeouts"""
    ui_path = Path(__file__).parent / "ui.py"
    content = ui_path.read_text(encoding='utf-8')

    # Check for wait() calls
    wait_calls = re.findall(r'\.wait\((\d+)\)', content)
    assert len(wait_calls) > 0, "No wait() calls with timeout found"

    print(f"[OK] Found {len(wait_calls)} thread wait() calls with timeouts")

    # Check specific methods
    assert '.wait(5000)' in content, "Missing 5-second timeout in search worker"
    assert '.wait(3000)' in content, "Missing 3-second timeout in closeEvent"

    print("[OK] Thread cleanup includes proper timeouts")
    return True


def test_closeEvent_implementation():
    """Test that closeEvent properly handles thread cleanup"""
    ui_path = Path(__file__).parent / "ui.py"
    content = ui_path.read_text(encoding='utf-8')

    # Find closeEvent method
    method_match = re.search(r'def closeEvent\(self, event\):(.+?)(?=\n    def |\nclass |\Z)', content, re.DOTALL)
    assert method_match, "closeEvent method not found"

    method_content = method_match.group(1)

    # Verify proper cleanup
    assert 'self.search_worker' in method_content, "closeEvent doesn't handle search_worker"
    assert 'self.operation_worker' in method_content, "closeEvent doesn't handle operation_worker"
    assert 'isRunning()' in method_content, "closeEvent doesn't check if threads are running"
    assert 'terminate()' in method_content, "closeEvent doesn't terminate unresponsive threads"
    assert 'event.accept()' in method_content, "closeEvent doesn't accept the event"

    print("[OK] closeEvent properly implements thread cleanup")
    return True


def main():
    """Run all validation tests"""
    print("Testing UI refactoring...")
    print()

    tests = [
        test_signals_defined,
        test_methods_exist,
        test_no_parent_chains,
        test_signal_connections,
        test_thread_timeouts,
        test_closeEvent_implementation,
    ]

    try:
        for test in tests:
            test()

        print()
        print("=" * 60)
        print("ALL TESTS PASSED - Refactoring successful!")
        print("=" * 60)
        print()
        print("Summary of changes:")
        print("  - Added 4 signals to ResultsTableWidget")
        print("  - Replaced fragile parent() chains with signal emission")
        print("  - Created 4 new handler methods accepting list parameters")
        print("  - Connected all signals in _create_action_bar")
        print("  - Added thread timeouts to prevent hangs")
        print("  - Implemented closeEvent for proper cleanup")
        print()
        return 0

    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"TEST FAILED: {e}")
        print("=" * 60)
        return 1
    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
