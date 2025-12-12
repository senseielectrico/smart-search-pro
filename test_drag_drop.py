"""
Test script for drag & drop functionality.
Tests all components without requiring full application.
"""

import sys
from pathlib import Path

# Ensure we can import from parent directory
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QMimeData, QUrl, Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

from ui.drag_drop import (
    DragDropHandler, DragOperation, get_files_from_mime_data,
    is_internal_drag
)


class TestDragDrop:
    """Test suite for drag & drop functionality"""

    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.handler = DragDropHandler()
        self.passed = 0
        self.failed = 0

    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("DRAG & DROP TEST SUITE")
        print("=" * 60)
        print()

        self.test_handler_creation()
        self.test_mime_data_creation()
        self.test_file_extraction()
        self.test_internal_drag_detection()
        self.test_modifier_detection()
        self.test_drag_operation_enum()
        self.test_cursor_selection()

        print()
        print("=" * 60)
        print(f"RESULTS: {self.passed} passed, {self.failed} failed")
        print("=" * 60)

        return self.failed == 0

    def test_handler_creation(self):
        """Test handler can be created"""
        try:
            handler = DragDropHandler()
            assert handler is not None
            assert handler.current_drag_paths == []
            assert handler.drag_operation == DragOperation.COPY
            self._pass("Handler creation")
        except Exception as e:
            self._fail("Handler creation", str(e))

    def test_mime_data_creation(self):
        """Test MIME data creation for drag"""
        try:
            test_paths = [
                str(Path.home() / "test1.txt"),
                str(Path.home() / "test2.txt")
            ]

            # Create MIME data
            mime_data = QMimeData()
            urls = [QUrl.fromLocalFile(path) for path in test_paths]
            mime_data.setUrls(urls)

            # Verify
            assert mime_data.hasUrls()
            assert len(mime_data.urls()) == 2

            self._pass("MIME data creation")
        except Exception as e:
            self._fail("MIME data creation", str(e))

    def test_file_extraction(self):
        """Test extracting file paths from MIME data"""
        try:
            test_paths = [
                str(Path.home() / "test1.txt"),
                str(Path.home() / "test2.txt")
            ]

            # Create MIME data
            mime_data = QMimeData()
            urls = [QUrl.fromLocalFile(path) for path in test_paths]
            mime_data.setUrls(urls)

            # Extract files
            extracted = get_files_from_mime_data(mime_data)

            assert len(extracted) == 2
            assert all(isinstance(p, str) for p in extracted)

            self._pass("File extraction from MIME data")
        except Exception as e:
            self._fail("File extraction from MIME data", str(e))

    def test_internal_drag_detection(self):
        """Test internal vs external drag detection"""
        try:
            # External drag (no custom format)
            mime_data_external = QMimeData()
            mime_data_external.setUrls([QUrl.fromLocalFile(str(Path.home() / "test.txt"))])

            assert not is_internal_drag(mime_data_external)

            # Internal drag (has custom format)
            mime_data_internal = QMimeData()
            mime_data_internal.setUrls([QUrl.fromLocalFile(str(Path.home() / "test.txt"))])
            mime_data_internal.setData('application/x-smart-search-files', b'test.txt')

            assert is_internal_drag(mime_data_internal)

            self._pass("Internal drag detection")
        except Exception as e:
            self._fail("Internal drag detection", str(e))

    def test_modifier_detection(self):
        """Test keyboard modifier to drop action conversion"""
        try:
            handler = DragDropHandler()

            # Test without modifiers (should default to Copy)
            action = handler.get_drop_action_from_modifiers()
            assert action == Qt.DropAction.CopyAction

            self._pass("Modifier detection")
        except Exception as e:
            self._fail("Modifier detection", str(e))

    def test_drag_operation_enum(self):
        """Test DragOperation enum"""
        try:
            assert DragOperation.COPY.value == "copy"
            assert DragOperation.MOVE.value == "move"
            assert DragOperation.LINK.value == "link"

            self._pass("DragOperation enum")
        except Exception as e:
            self._fail("DragOperation enum", str(e))

    def test_cursor_selection(self):
        """Test cursor selection based on modifiers"""
        try:
            handler = DragDropHandler()
            cursor = handler.get_operation_cursor()

            assert cursor is not None
            # Should return a valid cursor (default copy cursor)

            self._pass("Cursor selection")
        except Exception as e:
            self._fail("Cursor selection", str(e))

    def _pass(self, test_name):
        """Mark test as passed"""
        self.passed += 1
        print(f"[PASS] {test_name}")

    def _fail(self, test_name, error):
        """Mark test as failed"""
        self.failed += 1
        print(f"[FAIL] {test_name}: {error}")


def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from ui.results_panel import ResultsPanel, DraggableTableView
        print("  [OK] results_panel imports")

        from ui.operations_panel import OperationsPanel
        print("  [OK] operations_panel imports")

        from ui.directory_tree import DirectoryTree
        print("  [OK] directory_tree imports")

        from ui.drag_drop import DragDropHandler, DragSource, DropZoneWidget
        print("  [OK] drag_drop imports")

        return True
    except Exception as e:
        print(f"  [FAIL] Import failed: {e}")
        return False


def test_component_creation():
    """Test that components can be created"""
    print("\nTesting component creation...")
    app = QApplication.instance() or QApplication(sys.argv)

    try:
        from ui.results_panel import ResultsPanel
        panel1 = ResultsPanel()
        assert panel1.drag_handler is not None
        print("  [OK] ResultsPanel created with drag handler")

        from ui.operations_panel import OperationsPanel
        panel2 = OperationsPanel()
        assert panel2.drag_handler is not None
        print("  [OK] OperationsPanel created with drag handler")

        from ui.directory_tree import DirectoryTree
        tree = DirectoryTree()
        assert tree.drag_handler is not None
        print("  [OK] DirectoryTree created with drag handler")

        return True
    except Exception as e:
        print(f"  [FAIL] Component creation failed: {e}")
        return False


def main():
    """Run all tests"""
    print()
    print("=" * 60)
    print(" " * 10 + "SMART SEARCH PRO - DRAG & DROP TESTS")
    print("=" * 60)
    print()

    # Test imports
    import_ok = test_imports()
    if not import_ok:
        print("\n[X] Import tests failed. Cannot continue.")
        return False

    # Test component creation
    component_ok = test_component_creation()
    if not component_ok:
        print("\n[X] Component creation tests failed.")
        return False

    # Run unit tests
    print()
    tester = TestDragDrop()
    success = tester.run_all_tests()

    if success:
        print()
        print("*** ALL TESTS PASSED! ***")
        print()
        print("Next steps:")
        print("  1. Run the demo: python -m ui.drag_drop_demo")
        print("  2. Test with real files in the full application")
        print("  3. Check DRAG_DROP_GUIDE.md for detailed usage")
        print()
    else:
        print()
        print("*** SOME TESTS FAILED ***")
        print()

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
