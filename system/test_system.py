"""
Test suite for system integration module.

Run individual tests or all tests to verify functionality.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_elevation():
    """Test elevation manager."""
    print("\n" + "=" * 60)
    print("Testing Elevation Manager")
    print("=" * 60)

    from system.elevation import ElevationManager

    manager = ElevationManager()

    print(f"Is Admin: {manager.is_admin()}")
    print(f"Is Elevated: {manager.is_elevated()}")
    print(f"Elevation Type: {manager.get_elevation_type()}")

    if not manager.is_elevated():
        response = input("\nRequest elevation? (y/n): ")
        if response.lower() == 'y':
            print("Requesting elevation (will relaunch)...")
            manager.relaunch_elevated()
    else:
        print("Already running elevated!")


def test_hotkeys():
    """Test hotkey manager."""
    print("\n" + "=" * 60)
    print("Testing Hotkey Manager")
    print("=" * 60)

    from system.hotkeys import (
        HotkeyManager,
        ModifierKeys,
        VirtualKeys,
        parse_hotkey_string,
    )

    # Test hotkey parsing
    print("\nTesting hotkey parsing:")
    test_strings = [
        "Ctrl+Shift+F",
        "Win+R",
        "Ctrl+Alt+Delete",
        "F12",
    ]

    for hotkey_str in test_strings:
        result = parse_hotkey_string(hotkey_str)
        if result:
            mods, vk = result
            print(f"  {hotkey_str}: Mods={mods:#04x}, VK={vk:#04x}")
        else:
            print(f"  {hotkey_str}: Invalid")

    # Test hotkey registration
    response = input("\nRegister test hotkeys? (y/n): ")
    if response.lower() != 'y':
        return

    manager = HotkeyManager()

    def on_test1():
        print("Hotkey 1 pressed! (Ctrl+Shift+F)")

    def on_test2():
        print("Hotkey 2 pressed! (Ctrl+Q)")
        manager.cleanup()
        sys.exit(0)

    manager.register(
        "test1",
        ModifierKeys.CTRL | ModifierKeys.SHIFT,
        VirtualKeys.letter('F'),
        on_test1,
        "Test hotkey 1"
    )

    manager.register(
        "test2",
        ModifierKeys.CTRL,
        VirtualKeys.letter('Q'),
        on_test2,
        "Quit test"
    )

    print("\nHotkeys registered:")
    for name, info in manager.list_hotkeys().items():
        print(f"  {name}: {info.description}")

    print("\nPress Ctrl+Shift+F to test, Ctrl+Q to quit")

    try:
        manager.process_messages()
    except KeyboardInterrupt:
        print("\nExiting...")
        manager.cleanup()


def test_single_instance():
    """Test single instance manager."""
    print("\n" + "=" * 60)
    print("Testing Single Instance Manager")
    print("=" * 60)

    from system.single_instance import SingleInstanceManager
    import time

    manager = SingleInstanceManager("SmartSearchPro_Test")

    if not manager.is_first_instance():
        print("Another instance is running!")
        print("Attempting to activate existing instance...")

        if manager.activate_existing_instance():
            print("Activated existing instance")
        else:
            print("Could not activate existing instance")

        manager.cleanup()
        return
    else:
        print("This is the first instance")
        print("Running for 10 seconds...")
        print("Try running this script again in another terminal")

        try:
            time.sleep(10)
        except KeyboardInterrupt:
            print("\nExiting...")

        manager.cleanup()


def test_autostart():
    """Test autostart manager."""
    print("\n" + "=" * 60)
    print("Testing Autostart Manager")
    print("=" * 60)

    from system.autostart import AutostartManager, StartupMethod

    manager = AutostartManager("SmartSearchPro_Test")

    print("\nCurrent autostart status:")
    for method in StartupMethod:
        enabled = manager.is_enabled(method)
        status = "Enabled" if enabled else "Disabled"
        print(f"  {method.value}: {status}")

    print("\nOptions:")
    print("1. Enable (Registry - Current User)")
    print("2. Enable (Task Scheduler)")
    print("3. Disable all")
    print("4. Skip")

    choice = input("\nSelect option (1-4): ")

    if choice == "1":
        exe_path = input("Executable path (or press Enter for test): ")
        if not exe_path:
            exe_path = sys.executable

        if manager.enable(
            exe_path,
            "--test",
            StartupMethod.REGISTRY_CURRENT_USER
        ):
            print("Enabled successfully!")
        else:
            print("Failed to enable")

    elif choice == "2":
        exe_path = input("Executable path (or press Enter for test): ")
        if not exe_path:
            exe_path = sys.executable

        if manager.enable(
            exe_path,
            "--test",
            StartupMethod.TASK_SCHEDULER
        ):
            print("Enabled successfully!")
        else:
            print("Failed to enable")

    elif choice == "3":
        if manager.disable_all():
            print("Disabled all autostart methods")
        else:
            print("Some methods could not be disabled")


def test_shell_integration():
    """Test shell integration (requires admin)."""
    print("\n" + "=" * 60)
    print("Testing Shell Integration")
    print("=" * 60)
    print("Note: Most operations require administrator privileges")

    from system.shell_integration import (
        ShellIntegration,
        ContextMenuItem,
    )
    from system.elevation import ElevationManager

    elevation = ElevationManager()
    if not elevation.is_elevated():
        print("\nWarning: Not running as administrator")
        print("Some operations may fail")

    manager = ShellIntegration()

    print("\nOptions:")
    print("1. Add context menu for .txt files")
    print("2. Remove context menu")
    print("3. Add to Send To menu")
    print("4. Remove from Send To menu")
    print("5. Set App ID")
    print("6. Skip")

    choice = input("\nSelect option (1-6): ")

    app_path = sys.executable

    if choice == "1":
        item = ContextMenuItem(
            name="Test Smart Search",
            command=f'"{app_path}" --test "%1"',
        )
        if manager.add_context_menu(item, file_types=[".txt"]):
            print("Context menu added!")
        else:
            print("Failed to add context menu")

    elif choice == "2":
        if manager.remove_context_menu("Test Smart Search", file_types=[".txt"]):
            print("Context menu removed!")
        else:
            print("Failed to remove context menu")

    elif choice == "3":
        if manager.add_to_send_to("Smart Search Test", app_path):
            print("Added to Send To menu!")
        else:
            print("Failed to add to Send To menu")

    elif choice == "4":
        if manager.remove_from_send_to("Smart Search Test"):
            print("Removed from Send To menu!")
        else:
            print("Failed to remove from Send To menu")

    elif choice == "5":
        if manager.set_app_id("com.smartsearch.test"):
            print("App ID set!")
        else:
            print("Failed to set App ID")


def test_tray():
    """Test system tray (requires PyQt6)."""
    print("\n" + "=" * 60)
    print("Testing System Tray")
    print("=" * 60)

    try:
        from PyQt6.QtWidgets import QApplication
        from system.tray import SystemTrayIcon
    except ImportError:
        print("PyQt6 not installed. Install with: pip install PyQt6")
        return

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray = SystemTrayIcon()

    # Connect signals
    tray.show_main_window.connect(lambda: print("Show main window"))
    tray.hide_main_window.connect(lambda: print("Hide main window"))
    tray.quick_search_requested.connect(
        lambda q: print(f"Quick search: {q}")
    )
    tray.exit_requested.connect(app.quit)

    # Show tray
    tray.show()
    tray.set_tooltip("Smart Search Pro - Test")
    tray.show_notification(
        "Test",
        "System tray test started",
    )

    # Add some test searches
    tray.add_recent_search("test query 1")
    tray.add_recent_search("test query 2")
    tray.add_recent_search("test query 3")

    print("\nSystem tray icon shown")
    print("Try:")
    print("  - Left click: Toggle window")
    print("  - Double click: Quick search")
    print("  - Right click: Context menu")
    print("\nPress Ctrl+C to exit")

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nExiting...")
        tray.cleanup()


def main():
    """Main test menu."""
    print("=" * 60)
    print("Smart Search Pro - System Integration Tests")
    print("=" * 60)

    while True:
        print("\nAvailable tests:")
        print("1. Elevation Manager")
        print("2. Hotkey Manager")
        print("3. Single Instance Manager")
        print("4. Autostart Manager")
        print("5. Shell Integration (requires admin)")
        print("6. System Tray (requires PyQt6)")
        print("7. Run all tests")
        print("0. Exit")

        choice = input("\nSelect test (0-7): ")

        if choice == "0":
            break
        elif choice == "1":
            test_elevation()
        elif choice == "2":
            test_hotkeys()
        elif choice == "3":
            test_single_instance()
        elif choice == "4":
            test_autostart()
        elif choice == "5":
            test_shell_integration()
        elif choice == "6":
            test_tray()
        elif choice == "7":
            # Run non-interactive tests
            test_elevation()
            test_single_instance()
            test_autostart()
            print("\nNon-interactive tests completed")
            print("Run individual tests for interactive features")
        else:
            print("Invalid choice")

    print("\nTests completed")


if __name__ == "__main__":
    main()
