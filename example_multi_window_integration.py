"""
Example integration of multi-window support into Smart Search Pro.

This file demonstrates how to integrate the multi-window system
into your existing application.
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def integrate_step_by_step():
    """
    Step-by-step integration example.
    Shows what to change in your existing code.
    """

    print("=" * 70)
    print("MULTI-WINDOW INTEGRATION EXAMPLE")
    print("=" * 70)

    # ===== STEP 1: Import window manager =====
    print("\nSTEP 1: Import window manager")
    print("-" * 70)

    from ui.window_manager import get_window_manager

    print("✓ Imported: get_window_manager")

    # ===== STEP 2: Create QApplication =====
    print("\nSTEP 2: Create QApplication")
    print("-" * 70)

    app = QApplication.instance() or QApplication(sys.argv)
    print("✓ QApplication created")

    # ===== STEP 3: Get window manager instance =====
    print("\nSTEP 3: Get window manager instance")
    print("-" * 70)

    manager = get_window_manager()
    print(f"✓ Window manager created: {manager}")

    # ===== STEP 4: Set up shared resources (OPTIONAL) =====
    print("\nSTEP 4: Set up shared resources (optional)")
    print("-" * 70)

    # Example: Create shared search engine
    # In real app, you would pass your actual search engine
    print("  Note: You can set shared resources like:")
    print("  manager.set_shared_resources(")
    print("      search_engine=your_search_engine,")
    print("      database=your_database,")
    print("      cache=your_cache")
    print("  )")
    print("✓ Shared resources can be configured")

    # ===== STEP 5: Restore or create windows =====
    print("\nSTEP 5: Restore saved layout or create new window")
    print("-" * 70)

    # Check if there are saved windows
    saved_windows = manager._state_manager.get_all_windows()

    if saved_windows:
        print(f"  Found {len(saved_windows)} saved windows")
        print("  Restoring layout...")
        manager.restore_layout()
    else:
        print("  No saved layout found")
        print("  Creating primary window...")
        window = manager.create_window(is_primary=True)
        print(f"  ✓ Primary window created: {window.window_id}")

    print(f"✓ Total windows: {manager.get_window_count()}")

    # ===== STEP 6: Show usage examples =====
    print("\nSTEP 6: Usage examples")
    print("-" * 70)

    print("\nAvailable operations:")
    print("  • manager.create_window() - Create new window")
    print("  • manager.create_duplicate_window(id) - Duplicate window")
    print("  • manager.close_window(id) - Close specific window")
    print("  • manager.close_all_windows() - Close all windows")
    print("  • manager.arrange_cascade() - Cascade layout")
    print("  • manager.arrange_tile_horizontal() - Horizontal layout")
    print("  • manager.arrange_tile_vertical() - Vertical layout")
    print("  • manager.save_layout() - Save current layout")

    # ===== STEP 7: Add Window menu =====
    print("\nSTEP 7: Add Window menu to main window")
    print("-" * 70)

    from ui.window_menu import create_window_menu

    # Get first window
    windows = manager.get_all_windows()
    if windows:
        main_window = windows[0]

        # Create window menu
        menu_manager = create_window_menu(manager)
        window_menu = menu_manager.get_menu()

        # Add to menu bar
        main_window.menuBar().addMenu(window_menu)

        print("✓ Window menu added to main window")
        print("\nWindow menu includes:")
        print("  • New Window (Ctrl+N)")
        print("  • Duplicate Window (Ctrl+Shift+N)")
        print("  • Close Window (Ctrl+W)")
        print("  • Close All Windows (Ctrl+Shift+W)")
        print("  • Arrange submenu")
        print("  • Window list (Ctrl+1-9)")

    # ===== STEP 8: Final summary =====
    print("\n" + "=" * 70)
    print("INTEGRATION COMPLETE!")
    print("=" * 70)

    print(f"\nCurrent state:")
    print(f"  • Windows open: {manager.get_window_count()}")
    print(f"  • Active window: {manager.get_active_window_id()}")
    print(f"  • Layout mode: {manager._state_manager.get_layout()}")

    print("\nNext steps:")
    print("  1. Run the application")
    print("  2. Test window creation (Ctrl+N)")
    print("  3. Try different layouts")
    print("  4. Save your layout")
    print("  5. Restart app to test restore")

    return manager


def example_complete_application():
    """
    Complete example of an application with multi-window support.
    """

    print("\n" + "=" * 70)
    print("COMPLETE APPLICATION EXAMPLE")
    print("=" * 70)

    # Create application
    app = QApplication.instance() or QApplication(sys.argv)

    # Import managers
    from ui.window_manager import get_window_manager
    from ui.window_menu import create_window_menu

    # Get window manager
    manager = get_window_manager()

    # Optional: Set up shared resources
    # manager.set_shared_resources(
    #     search_engine=search_engine,
    #     database=database,
    #     cache=cache
    # )

    # Restore or create windows
    saved_windows = manager._state_manager.get_all_windows()

    if saved_windows:
        print(f"\nRestoring {len(saved_windows)} windows from saved layout...")
        manager.restore_layout()
    else:
        print("\nCreating new primary window...")
        window = manager.create_window(is_primary=True)

        # Add window menu to first window
        menu_manager = create_window_menu(manager)
        window.menuBar().addMenu(menu_manager.get_menu())

    print(f"✓ Application started with {manager.get_window_count()} window(s)")

    # Show all windows
    for window in manager.get_all_windows():
        window.show()

    print("\nApplication ready!")
    print("Try these keyboard shortcuts:")
    print("  • Ctrl+N: New window")
    print("  • Ctrl+Shift+N: Duplicate current window")
    print("  • Ctrl+W: Close current window")
    print("  • Ctrl+1-9: Switch between windows")

    # Note: Uncomment to actually run the application
    # sys.exit(app.exec())


def example_advanced_usage():
    """
    Advanced usage examples.
    """

    print("\n" + "=" * 70)
    print("ADVANCED USAGE EXAMPLES")
    print("=" * 70)

    from ui.window_manager import get_window_manager
    from ui.secondary_window import create_secondary_window
    from core.window_state import WindowGeometry, SearchState

    app = QApplication.instance() or QApplication(sys.argv)
    manager = get_window_manager()

    # Example 1: Create window with specific search
    print("\nExample 1: Create window with predefined search")
    print("-" * 70)

    window1 = manager.create_window()
    if hasattr(window1, 'search_panel'):
        window1.search_panel.search_input.setText("*.py")
        print("✓ Created window searching for Python files")

    # Example 2: Create mini mode window
    print("\nExample 2: Create compact mini-mode window")
    print("-" * 70)

    mini_window = create_secondary_window(
        mini_mode=True,
        search_query="config",
        directory_path="/etc"
    )
    print("✓ Created mini window for config files")

    # Example 3: Custom window layout
    print("\nExample 3: Create custom 3-window layout")
    print("-" * 70)

    # Create 3 windows
    w1 = manager.create_window()
    w1.setGeometry(0, 0, 600, 800)

    w2 = manager.create_window()
    w2.setGeometry(600, 0, 600, 800)

    w3 = manager.create_window()
    w3.setGeometry(1200, 0, 600, 800)

    print("✓ Created 3-column layout")

    # Example 4: Save custom layout
    print("\nExample 4: Save custom layout")
    print("-" * 70)

    manager.save_layout()
    print("✓ Layout saved (will restore on next launch)")

    # Example 5: Programmatic window control
    print("\nExample 5: Programmatic window control")
    print("-" * 70)

    all_windows = manager.get_all_windows()
    print(f"  Total windows: {len(all_windows)}")

    for i, window in enumerate(all_windows, 1):
        window_id = getattr(window, 'window_id', f'unknown_{i}')
        print(f"  Window {i}: {window_id}")

    # Switch to second window
    if len(all_windows) >= 2:
        second_window_id = getattr(all_windows[1], 'window_id', None)
        if second_window_id:
            manager.set_active_window(second_window_id)
            print(f"✓ Switched to window: {second_window_id}")

    print("\n" + "=" * 70)


def example_error_handling():
    """
    Example of proper error handling.
    """

    print("\n" + "=" * 70)
    print("ERROR HANDLING EXAMPLE")
    print("=" * 70)

    from ui.window_manager import get_window_manager

    try:
        app = QApplication.instance() or QApplication(sys.argv)
        manager = get_window_manager()

        # Try to restore layout
        try:
            saved_windows = manager._state_manager.get_all_windows()
            if saved_windows:
                print(f"Attempting to restore {len(saved_windows)} windows...")
                manager.restore_layout()
                print("✓ Layout restored successfully")
        except Exception as e:
            print(f"⚠ Failed to restore layout: {e}")
            print("  Creating new window instead...")
            manager.create_window(is_primary=True)

        # Ensure at least one window exists
        if manager.get_window_count() == 0:
            print("No windows open, creating primary window...")
            manager.create_window(is_primary=True)

        print(f"✓ Application running with {manager.get_window_count()} window(s)")

    except Exception as e:
        print(f"✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 70)


if __name__ == "__main__":
    print("\n\n")
    print("#" * 70)
    print("# SMART SEARCH PRO - MULTI-WINDOW INTEGRATION EXAMPLES")
    print("#" * 70)

    # Run integration example
    integrate_step_by_step()

    # Show complete application example
    example_complete_application()

    # Show advanced usage
    example_advanced_usage()

    # Show error handling
    example_error_handling()

    print("\n\n")
    print("#" * 70)
    print("# INTEGRATION EXAMPLES COMPLETE")
    print("#" * 70)

    print("\n\nTo integrate into your app:")
    print("  1. Copy relevant code from integrate_step_by_step()")
    print("  2. Update your main() function")
    print("  3. Add window menu to MainWindow")
    print("  4. Test with: python test_multi_window.py")
    print("\nSee MULTI_WINDOW_QUICKSTART.md for detailed instructions.")
