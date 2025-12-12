"""
Test suite for multi-window functionality in Smart Search Pro.

Tests window manager, secondary windows, tab management,
and window state persistence.
"""

import sys
import time
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtTest import QTest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_window_state_persistence():
    """Test window state save/load."""
    print("\n=== Testing Window State Persistence ===")

    from core.window_state import (
        WindowGeometry,
        SearchState,
        WindowState,
        WindowStateManager
    )

    # Create test state
    geometry = WindowGeometry(
        x=100, y=100, width=1200, height=700,
        is_maximized=False, is_minimized=False
    )

    search_state = SearchState(
        query="test query",
        directory_paths=["/home/user/documents"],
        filters={"size": ">1MB"},
        sort_by="modified",
        sort_ascending=False
    )

    window_state = WindowState(
        window_id="test_window_1",
        geometry=geometry,
        search_state=search_state,
        is_primary=True,
        created_at=time.time(),
        last_active=time.time()
    )

    # Create state manager
    import tempfile
    temp_file = Path(tempfile.mktemp(suffix=".json"))

    manager = WindowStateManager(temp_file)

    # Add window state
    manager.add_window(window_state)
    manager.save_state()

    print(f"✓ Window state saved to {temp_file}")

    # Load state
    manager2 = WindowStateManager(temp_file)
    loaded_state = manager2.get_window_state("test_window_1")

    assert loaded_state is not None, "Failed to load window state"
    assert loaded_state.window_id == "test_window_1"
    assert loaded_state.search_state.query == "test query"
    assert loaded_state.geometry.width == 1200

    print("✓ Window state loaded correctly")

    # Clean up
    temp_file.unlink()

    print("✓ Window state persistence tests passed")


def test_window_manager_basic():
    """Test basic window manager operations."""
    print("\n=== Testing Window Manager ===")

    from ui.window_manager import WindowManager

    # Create application
    app = QApplication.instance() or QApplication(sys.argv)

    # Create window manager
    manager = WindowManager()

    # Create first window
    window1 = manager.create_window(window_id="test_1", is_primary=True)
    assert window1 is not None, "Failed to create window"
    assert manager.get_window_count() == 1

    print("✓ Created first window")

    # Create second window
    window2 = manager.create_window(window_id="test_2")
    assert manager.get_window_count() == 2

    print("✓ Created second window")

    # Get window by ID
    retrieved = manager.get_window("test_1")
    assert retrieved == window1

    print("✓ Retrieved window by ID")

    # Set active window
    manager.set_active_window("test_2")
    assert manager.get_active_window() == window2

    print("✓ Set active window")

    # Get all windows
    all_windows = manager.get_all_windows()
    assert len(all_windows) == 2

    print("✓ Retrieved all windows")

    # Close window
    manager.close_window("test_1")
    assert manager.get_window_count() == 1

    print("✓ Closed window")

    # Clean up
    manager.close_all_windows()
    assert manager.get_window_count() == 0

    print("✓ Window manager tests passed")


def test_window_arrangements():
    """Test window arrangement functions."""
    print("\n=== Testing Window Arrangements ===")

    from ui.window_manager import WindowManager

    app = QApplication.instance() or QApplication(sys.argv)

    manager = WindowManager()

    # Create multiple windows
    windows = []
    for i in range(3):
        window = manager.create_window(window_id=f"test_{i}")
        windows.append(window)

    print(f"✓ Created {len(windows)} windows")

    # Test cascade
    manager.arrange_cascade()
    print("✓ Arranged in cascade")

    # Test tile horizontal
    manager.arrange_tile_horizontal()
    print("✓ Arranged horizontally")

    # Test tile vertical
    manager.arrange_tile_vertical()
    print("✓ Arranged vertically")

    # Clean up
    manager.close_all_windows()

    print("✓ Window arrangement tests passed")


def test_secondary_window():
    """Test secondary window functionality."""
    print("\n=== Testing Secondary Window ===")

    from ui.secondary_window import SecondaryWindow, create_secondary_window

    app = QApplication.instance() or QApplication(sys.argv)

    # Create secondary window
    window = create_secondary_window(
        window_id="secondary_test",
        mini_mode=False,
        search_query="test search",
        directory_path="/home/user"
    )

    assert window is not None
    assert window.window_id == "secondary_test"
    assert not window.is_primary

    print("✓ Created secondary window")

    # Test mini mode toggle
    window.toggle_mini_mode(True)
    assert window.get_mini_mode() == True

    print("✓ Toggled mini mode")

    # Test search context
    window.set_search_context("Custom Context")
    assert "Custom Context" in window.windowTitle()

    print("✓ Set search context")

    # Clean up
    window.close()

    print("✓ Secondary window tests passed")


def test_tab_manager():
    """Test tab manager functionality."""
    print("\n=== Testing Tab Manager ===")

    from ui.tab_manager import SearchTabWidget, TabManager

    app = QApplication.instance() or QApplication(sys.argv)

    # Create tab widget
    tab_widget = SearchTabWidget()
    tab_manager = TabManager(tab_widget)

    # Create tabs
    index1 = tab_manager.create_tab(title="Search 1")
    assert index1 >= 0
    assert tab_manager.get_tab_count() == 1

    print("✓ Created first tab")

    index2 = tab_manager.create_tab(title="Search 2")
    assert tab_manager.get_tab_count() == 2

    print("✓ Created second tab")

    # Switch tabs
    tab_manager.set_current_index(0)
    assert tab_manager.get_current_index() == 0

    print("✓ Switched tabs")

    # Close tab
    result = tab_manager.close_tab(1)
    assert result == True
    assert tab_manager.get_tab_count() == 1

    print("✓ Closed tab")

    # Try to close last tab (should fail)
    result = tab_manager.close_tab(0)
    assert result == False
    assert tab_manager.get_tab_count() == 1

    print("✓ Prevented closing last tab")

    # Clean up
    tab_widget.close()

    print("✓ Tab manager tests passed")


def test_window_menu():
    """Test window menu functionality."""
    print("\n=== Testing Window Menu ===")

    from ui.window_manager import WindowManager
    from ui.window_menu import WindowMenuManager

    app = QApplication.instance() or QApplication(sys.argv)

    # Create window manager and menu
    manager = WindowManager()
    menu_manager = WindowMenuManager(manager)
    menu = menu_manager.create_menu()

    assert menu is not None
    assert menu.title() == "&Window"

    print("✓ Created window menu")

    # Create some windows
    manager.create_window(window_id="menu_test_1")
    manager.create_window(window_id="menu_test_2")

    # Menu should update automatically
    actions = menu.actions()
    assert len(actions) > 0

    print("✓ Menu updated with windows")

    # Clean up
    manager.close_all_windows()

    print("✓ Window menu tests passed")


def test_integration():
    """Test integration of all components."""
    print("\n=== Testing Integration ===")

    from ui.window_manager import WindowManager
    from ui.window_menu import create_window_menu
    from core.window_state import get_window_state_manager

    app = QApplication.instance() or QApplication(sys.argv)

    # Create window manager
    manager = WindowManager()

    # Create window menu
    menu_manager = create_window_menu(manager)

    # Create windows
    window1 = manager.create_window(is_primary=True)
    window2 = manager.create_window()

    print("✓ Created windows with menu integration")

    # Save layout
    manager.save_layout()

    print("✓ Saved layout")

    # Close all
    manager.close_all_windows()

    # Restore layout
    manager.restore_layout()

    print("✓ Restored layout")

    # Verify windows restored
    assert manager.get_window_count() == 2

    print("✓ Windows restored from layout")

    # Clean up
    manager.close_all_windows()

    print("✓ Integration tests passed")


def run_visual_test():
    """Run visual test with UI."""
    print("\n=== Running Visual Test ===")
    print("This will open multiple windows. Close them to continue.")

    from ui.window_manager import WindowManager
    from ui.window_menu import create_window_menu

    app = QApplication.instance() or QApplication(sys.argv)

    # Create window manager
    manager = WindowManager()

    # Create primary window
    window1 = manager.create_window(is_primary=True)
    window1.setWindowTitle("Primary Window")

    # Wait a bit
    QTimer.singleShot(500, lambda: create_secondary_windows(manager))

    def create_secondary_windows(mgr):
        # Create secondary windows
        window2 = mgr.create_window()
        window2.setWindowTitle("Secondary Window 1")

        QTimer.singleShot(500, lambda: create_third_window(mgr))

    def create_third_window(mgr):
        window3 = mgr.create_window()
        window3.setWindowTitle("Secondary Window 2")

        # Arrange in cascade
        QTimer.singleShot(500, mgr.arrange_cascade)

    # Run app
    sys.exit(app.exec())


if __name__ == "__main__":
    print("=" * 60)
    print("Smart Search Pro - Multi-Window Test Suite")
    print("=" * 60)

    try:
        # Run tests
        test_window_state_persistence()
        test_window_manager_basic()
        test_window_arrangements()
        test_secondary_window()
        test_tab_manager()
        test_window_menu()
        test_integration()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)

        # Ask if user wants visual test
        response = input("\nRun visual test? (y/n): ")
        if response.lower() == 'y':
            run_visual_test()

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
