"""
Single Instance Manager for Smart Search Pro.

Ensures only one instance of the application runs at a time.
"""

import ctypes
import ctypes.wintypes as wintypes
import logging
import sys
from typing import Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

# Windows API constants
HWND_BROADCAST = 0xFFFF
WM_USER = 0x0400
WM_SHOW_WINDOW = WM_USER + 1


class SingleInstanceManager:
    """
    Single instance manager using Windows mutex.

    Features:
    - Ensure single application instance
    - Bring existing window to front
    - Send messages to existing instance
    - Cleanup on exit

    Example:
        manager = SingleInstanceManager("SmartSearchPro")

        if not manager.is_first_instance():
            manager.activate_existing_instance()
            sys.exit(0)

        # Continue with application initialization
        manager.set_window_handle(hwnd)
    """

    def __init__(
        self,
        app_name: str = "SmartSearchPro",
        unique_id: Optional[str] = None,
    ):
        """
        Initialize single instance manager.

        Args:
            app_name: Application name for mutex
            unique_id: Optional unique identifier (default: app_name)
        """
        self.app_name = app_name
        self.unique_id = unique_id or app_name
        self.mutex_name = f"Global\\{self.unique_id}_Mutex"

        # Windows API
        self.kernel32 = ctypes.windll.kernel32
        self.user32 = ctypes.windll.user32

        # Mutex handle
        self.mutex_handle: Optional[int] = None

        # Window handle for activation
        self.window_handle: Optional[int] = None

        # Register custom message for communication
        self.wm_activate = self.user32.RegisterWindowMessageW(
            f"{self.unique_id}_Activate"
        )

        self._create_mutex()

        logger.info(f"Single instance manager initialized: {self.unique_id}")

    def _create_mutex(self) -> None:
        """Create or open the mutex."""
        self.mutex_handle = self.kernel32.CreateMutexW(
            None,
            True,  # Initial owner
            self.mutex_name,
        )

        if not self.mutex_handle:
            logger.error("Failed to create mutex")

    def is_first_instance(self) -> bool:
        """
        Check if this is the first instance.

        Returns:
            True if this is the first instance
        """
        if not self.mutex_handle:
            return True

        # Check if mutex already existed
        error = self.kernel32.GetLastError()

        # ERROR_ALREADY_EXISTS = 183
        if error == 183:
            logger.info("Another instance is already running")
            return False
        else:
            logger.info("This is the first instance")
            return True

    def set_window_handle(self, hwnd: int) -> None:
        """
        Set the main window handle.

        Args:
            hwnd: Window handle (HWND)
        """
        self.window_handle = hwnd
        logger.debug(f"Window handle set: {hwnd}")

    def activate_existing_instance(self, arguments: Optional[str] = None) -> bool:
        """
        Activate the existing instance.

        This will bring the existing window to the front.

        Args:
            arguments: Optional arguments to pass to existing instance

        Returns:
            True if existing instance was activated
        """
        logger.info("Attempting to activate existing instance")

        # Find the existing window
        hwnd = self._find_window()

        if not hwnd:
            logger.warning("Could not find existing window")
            return False

        # Send activation message
        self.user32.PostMessageW(
            hwnd,
            self.wm_activate,
            0,
            0,
        )

        # Bring window to front
        self._show_window(hwnd)

        logger.info("Activated existing instance")
        return True

    def _find_window(self) -> Optional[int]:
        """
        Find the window of the existing instance.

        Returns:
            Window handle or None
        """
        # Try to find by window class or title
        hwnd = self.user32.FindWindowW(None, self.app_name)

        if hwnd:
            return hwnd

        # Alternative: Enumerate all windows and find ours
        return self._enumerate_windows()

    def _enumerate_windows(self) -> Optional[int]:
        """
        Enumerate windows to find our application.

        Returns:
            Window handle or None
        """
        found_hwnd = None

        def enum_callback(hwnd, lParam):
            nonlocal found_hwnd

            # Get window title
            length = self.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(hwnd, buffer, length + 1)
                title = buffer.value

                # Check if this is our window
                if self.app_name in title:
                    found_hwnd = hwnd
                    return False  # Stop enumeration

            return True  # Continue enumeration

        # Define callback type
        WNDENUMPROC = ctypes.WINFUNCTYPE(
            wintypes.BOOL,
            wintypes.HWND,
            wintypes.LPARAM,
        )

        callback = WNDENUMPROC(enum_callback)

        self.user32.EnumWindows(callback, 0)

        return found_hwnd

    def _show_window(self, hwnd: int) -> None:
        """
        Show and activate a window.

        Args:
            hwnd: Window handle
        """
        # Constants
        SW_RESTORE = 9
        SW_SHOW = 5

        # Restore if minimized
        if self.user32.IsIconic(hwnd):
            self.user32.ShowWindow(hwnd, SW_RESTORE)
        else:
            self.user32.ShowWindow(hwnd, SW_SHOW)

        # Bring to foreground
        self.user32.SetForegroundWindow(hwnd)

        # Flash window to get attention
        self._flash_window(hwnd)

    def _flash_window(self, hwnd: int, count: int = 3) -> None:
        """
        Flash window to get user attention.

        Args:
            hwnd: Window handle
            count: Number of flashes
        """
        try:
            # FLASHWINFO structure
            class FLASHWINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.UINT),
                    ("hwnd", wintypes.HWND),
                    ("dwFlags", wintypes.DWORD),
                    ("uCount", wintypes.UINT),
                    ("dwTimeout", wintypes.DWORD),
                ]

            # Flash flags
            FLASHW_ALL = 0x00000003

            flash_info = FLASHWINFO()
            flash_info.cbSize = ctypes.sizeof(FLASHWINFO)
            flash_info.hwnd = hwnd
            flash_info.dwFlags = FLASHW_ALL
            flash_info.uCount = count
            flash_info.dwTimeout = 0

            self.user32.FlashWindowEx(ctypes.byref(flash_info))

        except Exception as e:
            logger.error(f"Error flashing window: {e}")

    def send_message_to_existing(self, message: str) -> bool:
        """
        Send a message to the existing instance.

        Args:
            message: Message to send

        Returns:
            True if message was sent
        """
        hwnd = self._find_window()

        if not hwnd:
            return False

        # Use WM_COPYDATA to send string data
        try:
            COPYDATASTRUCT = type('COPYDATASTRUCT', (ctypes.Structure,), {
                '_fields_': [
                    ('dwData', wintypes.LPARAM),
                    ('cbData', wintypes.DWORD),
                    ('lpData', ctypes.c_void_p),
                ]
            })

            WM_COPYDATA = 0x004A

            # Encode message
            encoded = message.encode('utf-16le')

            cds = COPYDATASTRUCT()
            cds.dwData = 0
            cds.cbData = len(encoded)
            cds.lpData = ctypes.cast(
                ctypes.c_wchar_p(message),
                ctypes.c_void_p
            )

            self.user32.SendMessageW(
                hwnd,
                WM_COPYDATA,
                0,
                ctypes.byref(cds),
            )

            logger.info(f"Sent message to existing instance: {message}")
            return True

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    def cleanup(self) -> None:
        """Cleanup mutex and resources."""
        if self.mutex_handle:
            try:
                self.kernel32.ReleaseMutex(self.mutex_handle)
                self.kernel32.CloseHandle(self.mutex_handle)
                self.mutex_handle = None
                logger.info("Single instance manager cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up mutex: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()

    def __del__(self):
        """Destructor."""
        self.cleanup()


# Example usage
if __name__ == "__main__":
    import time

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("Single Instance Manager Test")
    print("=" * 50)

    manager = SingleInstanceManager("SmartSearchPro_Test")

    if not manager.is_first_instance():
        print("Another instance is running!")
        print("Attempting to activate existing instance...")

        if manager.activate_existing_instance():
            print("Activated existing instance")
        else:
            print("Could not activate existing instance")

        sys.exit(0)
    else:
        print("This is the first instance")
        print("Running for 30 seconds...")
        print("Try running this script again in another terminal")

        try:
            time.sleep(30)
        except KeyboardInterrupt:
            print("\nExiting...")

        manager.cleanup()
