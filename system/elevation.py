"""
Administrator Elevation Manager for Smart Search Pro.

Provides UAC elevation support for operations requiring administrator privileges.
"""

import ctypes
import ctypes.wintypes as wintypes
import sys
import os
import logging
from typing import Optional, List
from pathlib import Path
from enum import IntEnum

logger = logging.getLogger(__name__)

# Import security functions
try:
    from core.security import sanitize_cli_argument, log_security_event, SecurityEvent
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.security import sanitize_cli_argument, log_security_event, SecurityEvent


class ShowWindow(IntEnum):
    """ShowWindow command constants."""
    SW_HIDE = 0
    SW_SHOWNORMAL = 1
    SW_SHOWMINIMIZED = 2
    SW_SHOWMAXIMIZED = 3
    SW_SHOWNOACTIVATE = 4
    SW_SHOW = 5
    SW_MINIMIZE = 6
    SW_SHOWMINNOACTIVE = 7
    SW_SHOWNA = 8
    SW_RESTORE = 9


class ElevationManager:
    """
    Manager for administrator elevation.

    Features:
    - Check if running as administrator
    - Request elevation via UAC
    - Run specific operations elevated
    - Relaunch application elevated
    """

    def __init__(self):
        """Initialize elevation manager."""
        self.shell32 = ctypes.windll.shell32
        self.advapi32 = ctypes.windll.advapi32

        logger.info("Elevation manager initialized")

    def is_admin(self) -> bool:
        """
        Check if the current process is running as administrator.

        Returns:
            True if running as admin
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            return False

    def is_elevated(self) -> bool:
        """
        Check if the current process has elevated privileges.

        This is more accurate than is_admin() for UAC environments.

        Returns:
            True if process is elevated
        """
        try:
            # Open process token
            TOKEN_QUERY = 0x0008
            token = wintypes.HANDLE()

            if not self.advapi32.OpenProcessToken(
                wintypes.HANDLE(-1),  # Current process
                TOKEN_QUERY,
                ctypes.byref(token)
            ):
                return False

            # Get elevation status
            TOKEN_ELEVATION = 20
            elevation = wintypes.DWORD()
            size = wintypes.DWORD()

            result = self.advapi32.GetTokenInformation(
                token,
                TOKEN_ELEVATION,
                ctypes.byref(elevation),
                ctypes.sizeof(elevation),
                ctypes.byref(size)
            )

            ctypes.windll.kernel32.CloseHandle(token)

            if result:
                return elevation.value != 0
            else:
                return False

        except Exception as e:
            logger.error(f"Error checking elevation: {e}")
            return False

    def request_elevation(
        self,
        executable: Optional[str] = None,
        arguments: Optional[List[str]] = None,
        show_window: int = ShowWindow.SW_SHOWNORMAL,
    ) -> bool:
        """
        Request elevation for an executable.

        Args:
            executable: Path to executable (default: current script)
            arguments: Command line arguments
            show_window: Window show state

        Returns:
            True if elevation was granted (process started)

        Example:
            # Relaunch current script elevated
            if not manager.is_admin():
                if manager.request_elevation():
                    sys.exit()
        """
        if executable is None:
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                executable = sys.executable
            else:
                # Running as Python script
                executable = sys.executable
                if arguments is None:
                    arguments = []
                arguments = [sys.argv[0]] + arguments

        if arguments is None:
            arguments = sys.argv[1:]

        # Validate executable path
        try:
            executable_path = Path(executable).resolve()
            if not executable_path.exists():
                raise FileNotFoundError(f"Executable not found: {executable}")
        except Exception as e:
            logger.error(f"Invalid executable path: {e}")
            return False

        # SANITIZE each argument to prevent command injection
        try:
            sanitized_args = [sanitize_cli_argument(arg) for arg in arguments]
        except ValueError as e:
            log_security_event(
                SecurityEvent.COMMAND_INJECTION_ATTEMPT,
                {'executable': executable, 'arguments': arguments, 'error': str(e)},
                severity="ERROR"
            )
            logger.error(f"Invalid argument detected: {e}")
            return False

        # Build command line with proper quoting
        # Always quote arguments to prevent injection
        params = ' '.join(f'"{arg}"' for arg in sanitized_args)

        logger.info(
            f"Requesting elevation for: {executable} {params}"
        )

        try:
            # Use ShellExecuteW with 'runas' verb
            result = self.shell32.ShellExecuteW(
                None,
                "runas",  # Verb for elevation
                str(executable_path),  # Use validated path
                params,
                None,
                show_window
            )

            # Return value > 32 indicates success
            success = result > 32

            if success:
                logger.info("Elevation request successful")
            else:
                logger.warning(f"Elevation request failed: {result}")

            return success

        except Exception as e:
            logger.error(f"Error requesting elevation: {e}")
            return False

    def run_elevated(
        self,
        command: str,
        arguments: Optional[List[str]] = None,
        wait: bool = False,
    ) -> bool:
        """
        Run a command with elevation.

        Args:
            command: Command or executable to run
            arguments: Command arguments
            wait: Wait for command to complete

        Returns:
            True if command was started
        """
        if arguments is None:
            arguments = []

        params = ' '.join(f'"{arg}"' if ' ' in arg else arg for arg in arguments)

        logger.info(f"Running elevated: {command} {params}")

        try:
            result = self.shell32.ShellExecuteW(
                None,
                "runas",
                command,
                params,
                None,
                ShowWindow.SW_SHOWNORMAL if not wait else ShowWindow.SW_HIDE
            )

            success = result > 32

            if success:
                logger.info("Elevated command started")
            else:
                logger.warning(f"Failed to start elevated command: {result}")

            return success

        except Exception as e:
            logger.error(f"Error running elevated command: {e}")
            return False

    def relaunch_elevated(self) -> None:
        """
        Relaunch the current application with elevation.

        This will exit the current process if successful.
        """
        if self.is_elevated():
            logger.info("Already running elevated")
            return

        logger.info("Relaunching application elevated")

        if self.request_elevation():
            # Elevation request successful, exit current process
            sys.exit(0)
        else:
            logger.error("Failed to elevate application")

    def check_and_elevate(self, required: bool = True) -> bool:
        """
        Check if running elevated, and optionally request elevation.

        Args:
            required: If True, relaunch elevated if not already

        Returns:
            True if running elevated
        """
        if self.is_elevated():
            return True

        if required:
            logger.info("Elevation required, requesting...")
            self.relaunch_elevated()
            # Will exit if successful

        return False

    def get_elevation_type(self) -> str:
        """
        Get detailed elevation type.

        Returns:
            One of: "admin", "elevated", "limited", "unknown"
        """
        try:
            if self.is_elevated():
                return "elevated"
            elif self.is_admin():
                return "admin"
            else:
                return "limited"
        except Exception:
            return "unknown"


def require_admin(func):
    """
    Decorator to require admin privileges for a function.

    Example:
        @require_admin
        def modify_system_file():
            # This will only run if elevated
            pass
    """
    def wrapper(*args, **kwargs):
        manager = ElevationManager()

        if not manager.is_elevated():
            logger.warning(
                f"Function {func.__name__} requires elevation"
            )
            manager.relaunch_elevated()
            # Will exit if successful
            return None

        return func(*args, **kwargs)

    return wrapper


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    manager = ElevationManager()

    print(f"Is Admin: {manager.is_admin()}")
    print(f"Is Elevated: {manager.is_elevated()}")
    print(f"Elevation Type: {manager.get_elevation_type()}")

    # Test elevation
    if not manager.is_elevated():
        response = input("\nRequest elevation? (y/n): ")
        if response.lower() == 'y':
            print("Requesting elevation...")
            manager.relaunch_elevated()
    else:
        print("\nAlready running elevated!")

        # Test running elevated command
        response = input("Run notepad elevated? (y/n): ")
        if response.lower() == 'y':
            manager.run_elevated("notepad.exe")
