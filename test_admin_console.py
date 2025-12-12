"""
Test script for Admin Console System.

Tests admin console manager, privilege manager, and UI widgets.
"""

import sys
import os
import logging
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

from system.admin_console import AdminConsoleManager, ConsoleConfig, ConsoleType
from system.privilege_manager import PrivilegeManager, PrivilegeContext
from system.elevation import ElevationManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_elevation_manager():
    """Test elevation manager."""
    print("\n" + "="*60)
    print("ELEVATION MANAGER TEST")
    print("="*60)

    manager = ElevationManager()

    print(f"Is Admin: {manager.is_admin()}")
    print(f"Is Elevated: {manager.is_elevated()}")
    print(f"Elevation Type: {manager.get_elevation_type()}")


def test_privilege_manager():
    """Test privilege manager."""
    print("\n" + "="*60)
    print("PRIVILEGE MANAGER TEST")
    print("="*60)

    manager = PrivilegeManager()

    print(f"Running as Admin: {manager.is_admin()}")
    print(f"In Admin Group: {manager.is_in_admin_group()}")
    print(f"Current User: {manager.get_token_user()}")

    print("\nAll Privileges:")
    for name, enabled in manager.get_all_privileges():
        status = "ENABLED" if enabled else "disabled"
        print(f"  {name}: {status}")

    print("\nChecking Specific Privileges:")
    privileges_to_check = [
        "SeBackupPrivilege",
        "SeRestorePrivilege",
        "SeDebugPrivilege",
        "SeShutdownPrivilege"
    ]

    for privilege in privileges_to_check:
        has = manager.has_privilege(privilege)
        enabled = manager.is_privilege_enabled(privilege)
        print(f"  {privilege}: has={has}, enabled={enabled}")

    # Test privilege enable/disable (only if admin)
    if manager.is_admin():
        print("\nTesting Privilege Enable/Disable:")
        if manager.has_privilege("SeBackupPrivilege"):
            print("  Enabling SeBackupPrivilege...")
            if manager.enable_privilege("SeBackupPrivilege"):
                print(f"    Enabled: {manager.is_privilege_enabled('SeBackupPrivilege')}")

                print("  Disabling SeBackupPrivilege...")
                manager.disable_privilege("SeBackupPrivilege")
                print(f"    Enabled: {manager.is_privilege_enabled('SeBackupPrivilege')}")

        # Test context manager
        print("\nTesting Privilege Context:")
        print(f"  Before: {manager.is_privilege_enabled('SeBackupPrivilege')}")

        with PrivilegeContext(["SeBackupPrivilege"]):
            print(f"  Inside: {manager.is_privilege_enabled('SeBackupPrivilege')}")

        print(f"  After: {manager.is_privilege_enabled('SeBackupPrivilege')}")
    else:
        print("\nNot running as admin, skipping privilege manipulation tests")


def test_admin_console_manager():
    """Test admin console manager."""
    print("\n" + "="*60)
    print("ADMIN CONSOLE MANAGER TEST")
    print("="*60)

    manager = AdminConsoleManager()

    print(f"Running as Admin: {manager.is_admin()}")

    print("\nConsole Paths:")
    for console_type in ConsoleType:
        path = manager.get_console_path(console_type)
        status = "FOUND" if path else "NOT FOUND"
        print(f"  {console_type.name}: {status}")
        if path:
            print(f"    Path: {path}")

    # Test batch command execution
    print("\nTesting Batch Command Execution:")
    commands = [
        'echo "Hello from PowerShell"',
        'Get-Date',
        'Get-Location',
        '$PSVersionTable.PSVersion'
    ]

    print("  Executing commands:")
    for cmd in commands:
        print(f"    - {cmd}")

    success, stdout, stderr = manager.execute_batch_commands(
        commands,
        config=ConsoleConfig(
            console_type=ConsoleType.POWERSHELL,
            working_directory=os.getcwd()
        )
    )

    print(f"\n  Success: {success}")
    if stdout:
        print(f"\n  Output:\n{stdout}")
    if stderr:
        print(f"\n  Errors:\n{stderr}")

    # Cleanup
    manager.cleanup()


def test_console_launch():
    """Test interactive console launch."""
    print("\n" + "="*60)
    print("CONSOLE LAUNCH TEST")
    print("="*60)

    manager = AdminConsoleManager()

    response = input("\nLaunch interactive PowerShell console? (y/n): ")
    if response.lower() != 'y':
        print("Skipped.")
        return

    print("Launching PowerShell console...")

    config = ConsoleConfig(
        console_type=ConsoleType.POWERSHELL,
        elevated=False,
        title="Smart Search Pro - Test Console",
        initial_commands=['Write-Host "Welcome to Smart Search Pro Test Console!"']
    )

    session = manager.launch_console(config)

    if session:
        print(f"Console launched successfully!")
        print(f"  Process ID: {session.process_id}")
        print(f"  Console Type: {session.console_type.name}")
        print(f"  Elevated: {session.elevated}")
        print(f"  Working Directory: {session.working_directory}")

        input("\nPress Enter to continue (console will remain open)...")
    else:
        print("Failed to launch console.")


def test_elevated_console():
    """Test elevated console launch."""
    print("\n" + "="*60)
    print("ELEVATED CONSOLE TEST")
    print("="*60)

    manager = AdminConsoleManager()
    elevation_manager = ElevationManager()

    if elevation_manager.is_elevated():
        print("Already running as administrator.")
        print("Skipping elevated launch test (would launch redundant console).")
        return

    response = input("\nLaunch elevated console with UAC prompt? (y/n): ")
    if response.lower() != 'y':
        print("Skipped.")
        return

    print("Launching elevated console...")
    print("You should see a UAC prompt...")

    config = ConsoleConfig(
        console_type=ConsoleType.POWERSHELL,
        elevated=True,
        title="Smart Search Pro - Admin Console (Elevated)"
    )

    session = manager.launch_console(config)

    if session:
        print("Elevated console launched successfully!")
        print("Check for new console window.")
    else:
        print("Failed to launch elevated console (UAC may have been declined).")


def test_ui_widgets():
    """Test UI widgets."""
    print("\n" + "="*60)
    print("UI WIDGETS TEST")
    print("="*60)

    response = input("\nLaunch UI test window? (requires PyQt6) (y/n): ")
    if response.lower() != 'y':
        print("Skipped.")
        return

    try:
        from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
        from ui.admin_console_widget import AdminConsoleWidget
        from ui.elevation_dialog import ElevationDialog, QuickElevationDialog

        print("Launching UI test...")

        app = QApplication(sys.argv)

        # Main window with tabs
        window = QMainWindow()
        window.setWindowTitle("Admin Console System Test")
        window.resize(1000, 700)

        tabs = QTabWidget()

        # Admin console widget
        console_widget = AdminConsoleWidget()
        tabs.addTab(console_widget, "Admin Console")

        window.setCentralWidget(tabs)
        window.show()

        print("UI test window launched!")
        print("Close the window to continue tests...")

        sys.exit(app.exec())

    except ImportError as e:
        print(f"Cannot test UI: {e}")
        print("Make sure PyQt6 is installed: pip install PyQt6")


def main():
    """Run all tests."""
    print("="*60)
    print("SMART SEARCH PRO - ADMIN CONSOLE SYSTEM TEST")
    print("="*60)

    try:
        # Test elevation manager
        test_elevation_manager()

        # Test privilege manager
        test_privilege_manager()

        # Test admin console manager
        test_admin_console_manager()

        # Test console launch
        test_console_launch()

        # Test elevated console
        test_elevated_console()

        # Test UI widgets
        test_ui_widgets()

        print("\n" + "="*60)
        print("ALL TESTS COMPLETED")
        print("="*60)

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
    except Exception as e:
        logger.exception("Error during tests")
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
