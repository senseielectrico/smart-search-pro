"""
Global Hotkey Manager for Smart Search Pro.

Provides system-wide hotkey registration using Windows API with Qt integration.
Features:
- Global hotkeys via Windows API
- Qt event loop integration
- Conflict detection
- Configurable hotkeys with persistence
- Tooltip hints
"""

import ctypes
import ctypes.wintypes as wintypes
from typing import Dict, Callable, Optional, Tuple, List
import logging
import json
from enum import IntFlag
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QAbstractNativeEventFilter
    from PyQt6.QtWidgets import QApplication
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    QObject = object
    pyqtSignal = None

logger = logging.getLogger(__name__)

# Windows API constants
WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000


class ModifierKeys(IntFlag):
    """Modifier key flags."""
    ALT = MOD_ALT
    CTRL = MOD_CONTROL
    SHIFT = MOD_SHIFT
    WIN = MOD_WIN
    NOREPEAT = MOD_NOREPEAT


# Virtual key codes (common ones)
class VirtualKeys:
    """Virtual key code constants."""
    VK_F1 = 0x70
    VK_F2 = 0x71
    VK_F3 = 0x72
    VK_F4 = 0x73
    VK_F5 = 0x74
    VK_F6 = 0x75
    VK_F7 = 0x76
    VK_F8 = 0x77
    VK_F9 = 0x78
    VK_F10 = 0x79
    VK_F11 = 0x7A
    VK_F12 = 0x7B

    VK_SPACE = 0x20
    VK_RETURN = 0x0D
    VK_ESCAPE = 0x1B
    VK_TAB = 0x09

    # Letters (A-Z)
    @staticmethod
    def letter(char: str) -> int:
        """Get virtual key code for letter."""
        char = char.upper()
        if len(char) == 1 and 'A' <= char <= 'Z':
            return ord(char)
        raise ValueError(f"Invalid letter: {char}")

    # Numbers (0-9)
    @staticmethod
    def number(num: int) -> int:
        """Get virtual key code for number."""
        if 0 <= num <= 9:
            return 0x30 + num
        raise ValueError(f"Invalid number: {num}")


@dataclass
class HotkeyInfo:
    """Information about a registered hotkey."""
    hotkey_id: int
    modifiers: int
    vk_code: int
    description: str
    callback: Callable[[], None]
    enabled: bool = True
    is_global: bool = False

    def to_dict(self) -> Dict:
        """Convert to dict for serialization (without callback)."""
        return {
            'hotkey_id': self.hotkey_id,
            'modifiers': self.modifiers,
            'vk_code': self.vk_code,
            'description': self.description,
            'enabled': self.enabled,
            'is_global': self.is_global
        }

    def get_key_string(self) -> str:
        """Get human-readable key combination."""
        parts = []
        if self.modifiers & MOD_CONTROL:
            parts.append("Ctrl")
        if self.modifiers & MOD_SHIFT:
            parts.append("Shift")
        if self.modifiers & MOD_ALT:
            parts.append("Alt")
        if self.modifiers & MOD_WIN:
            parts.append("Win")

        # Get key name
        key_name = _vk_to_string(self.vk_code)
        parts.append(key_name)

        return "+".join(parts)


def _vk_to_string(vk_code: int) -> str:
    """Convert virtual key code to string."""
    # Function keys
    if 0x70 <= vk_code <= 0x7B:
        return f"F{vk_code - 0x70 + 1}"

    # Letters
    if 0x41 <= vk_code <= 0x5A:
        return chr(vk_code)

    # Numbers
    if 0x30 <= vk_code <= 0x39:
        return chr(vk_code)

    # Special keys
    special_keys = {
        0x20: "Space",
        0x0D: "Enter",
        0x1B: "Esc",
        0x09: "Tab",
        0x2E: "Delete",
        0x08: "Backspace",
    }

    return special_keys.get(vk_code, f"VK_{vk_code:02X}")


class QtHotkeyEventFilter(QAbstractNativeEventFilter):
    """Qt event filter for processing Windows hotkey messages."""

    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def nativeEventFilter(self, eventType, message):
        """Filter native events for WM_HOTKEY."""
        if PYQT_AVAILABLE:
            # Check for WM_HOTKEY message
            try:
                if eventType == b"windows_generic_MSG":
                    import struct
                    # Parse message structure
                    msg = struct.unpack_from('IQQQ', message)
                    if msg[0] == WM_HOTKEY:
                        hotkey_id = msg[1]
                        self.manager._handle_hotkey(hotkey_id)
                        return True, 0
            except Exception as e:
                logger.error(f"Error processing hotkey event: {e}")

        return False, 0


class HotkeyManager(QObject if PYQT_AVAILABLE else object):
    """
    Global hotkey manager using Windows API with Qt integration.

    Features:
    - Register system-wide hotkeys
    - Enable/disable hotkeys
    - Automatic cleanup
    - Callback support
    - Qt event loop integration
    - Conflict detection
    - Configuration persistence

    Example:
        manager = HotkeyManager()
        manager.register(
            "search",
            ModifierKeys.CTRL | ModifierKeys.SHIFT,
            VirtualKeys.letter('F'),
            lambda: print("Search hotkey pressed"),
            is_global=True
        )
        manager.install_qt_filter()
    """

    if PYQT_AVAILABLE:
        hotkey_activated = pyqtSignal(str)  # Signal emitted when hotkey is activated

    def __init__(self, config_file: Optional[Path] = None):
        """Initialize hotkey manager."""
        if PYQT_AVAILABLE:
            super().__init__()

        self.hotkeys: Dict[str, HotkeyInfo] = {}
        self._next_id = 1
        self._listening = False
        self._event_filter: Optional[QtHotkeyEventFilter] = None
        self.config_file = config_file or Path.home() / ".smart_search" / "hotkeys.json"

        # Load Windows API functions
        self.user32 = ctypes.windll.user32
        self.user32.RegisterHotKey.argtypes = [
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_uint,
            ctypes.c_uint,
        ]
        self.user32.RegisterHotKey.restype = wintypes.BOOL

        self.user32.UnregisterHotKey.argtypes = [
            wintypes.HWND,
            ctypes.c_int,
        ]
        self.user32.UnregisterHotKey.restype = wintypes.BOOL

        logger.info("Hotkey manager initialized")

    def register(
        self,
        name: str,
        modifiers: int,
        vk_code: int,
        callback: Callable[[], None],
        description: str = "",
        is_global: bool = False,
    ) -> bool:
        """
        Register a hotkey.

        Args:
            name: Unique name for the hotkey
            modifiers: Modifier keys (use ModifierKeys flags)
            vk_code: Virtual key code
            callback: Function to call when hotkey is pressed
            description: Optional description
            is_global: If True, register as global system-wide hotkey

        Returns:
            True if registered successfully, False if failed or conflict detected

        Example:
            register(
                "quick_search",
                ModifierKeys.CTRL | ModifierKeys.SHIFT,
                VirtualKeys.letter('F'),
                on_quick_search,
                "Quick search hotkey",
                is_global=True
            )
        """
        if name in self.hotkeys:
            logger.warning(f"Hotkey '{name}' already registered")
            return False

        # Check for conflicts
        conflict = self.check_conflict(modifiers, vk_code)
        if conflict:
            logger.warning(
                f"Hotkey conflict detected for '{name}': "
                f"Already used by '{conflict}'"
            )
            return False

        hotkey_id = self._next_id
        self._next_id += 1

        # Only register globally if requested
        if is_global:
            # Add NOREPEAT flag to prevent repeated triggers
            register_mods = modifiers | MOD_NOREPEAT

            # Register with Windows
            result = self.user32.RegisterHotKey(
                None,  # No window handle (global)
                hotkey_id,
                register_mods,
                vk_code,
            )

            if not result:
                error_code = ctypes.get_last_error()
                logger.error(
                    f"Failed to register global hotkey '{name}': "
                    f"Error code {error_code} (may be in use by another application)"
                )
                return False

        # Store hotkey info
        self.hotkeys[name] = HotkeyInfo(
            hotkey_id=hotkey_id,
            modifiers=modifiers,
            vk_code=vk_code,
            description=description or name,
            callback=callback,
            is_global=is_global,
        )

        logger.info(
            f"Registered hotkey '{name}' "
            f"(ID: {hotkey_id}, Mods: {modifiers}, VK: {vk_code}, Global: {is_global})"
        )
        return True

    def check_conflict(self, modifiers: int, vk_code: int) -> Optional[str]:
        """
        Check if a hotkey combination conflicts with existing hotkeys.

        Args:
            modifiers: Modifier keys
            vk_code: Virtual key code

        Returns:
            Name of conflicting hotkey, or None if no conflict
        """
        for name, info in self.hotkeys.items():
            if info.modifiers == modifiers and info.vk_code == vk_code:
                return name
        return None

    def unregister(self, name: str) -> bool:
        """
        Unregister a hotkey.

        Args:
            name: Name of hotkey to unregister

        Returns:
            True if unregistered successfully
        """
        if name not in self.hotkeys:
            logger.warning(f"Hotkey '{name}' not found")
            return False

        hotkey = self.hotkeys[name]

        # Unregister from Windows
        result = self.user32.UnregisterHotKey(None, hotkey.hotkey_id)

        if result:
            del self.hotkeys[name]
            logger.info(f"Unregistered hotkey '{name}'")
            return True
        else:
            logger.error(f"Failed to unregister hotkey '{name}'")
            return False

    def enable(self, name: str) -> bool:
        """
        Enable a hotkey.

        Args:
            name: Name of hotkey to enable

        Returns:
            True if enabled successfully
        """
        if name not in self.hotkeys:
            logger.warning(f"Hotkey '{name}' not found")
            return False

        hotkey = self.hotkeys[name]

        if hotkey.enabled:
            return True

        # Re-register
        result = self.user32.RegisterHotKey(
            None,
            hotkey.hotkey_id,
            hotkey.modifiers,
            hotkey.vk_code,
        )

        if result:
            hotkey.enabled = True
            logger.info(f"Enabled hotkey '{name}'")
            return True
        else:
            logger.error(f"Failed to enable hotkey '{name}'")
            return False

    def disable(self, name: str) -> bool:
        """
        Disable a hotkey.

        Args:
            name: Name of hotkey to disable

        Returns:
            True if disabled successfully
        """
        if name not in self.hotkeys:
            logger.warning(f"Hotkey '{name}' not found")
            return False

        hotkey = self.hotkeys[name]

        if not hotkey.enabled:
            return True

        # Unregister temporarily
        result = self.user32.UnregisterHotKey(None, hotkey.hotkey_id)

        if result:
            hotkey.enabled = False
            logger.info(f"Disabled hotkey '{name}'")
            return True
        else:
            logger.error(f"Failed to disable hotkey '{name}'")
            return False

    def is_registered(self, name: str) -> bool:
        """Check if a hotkey is registered."""
        return name in self.hotkeys

    def is_enabled(self, name: str) -> bool:
        """Check if a hotkey is enabled."""
        return (
            name in self.hotkeys and
            self.hotkeys[name].enabled
        )

    def get_hotkey_info(self, name: str) -> Optional[HotkeyInfo]:
        """Get information about a hotkey."""
        return self.hotkeys.get(name)

    def list_hotkeys(self) -> Dict[str, HotkeyInfo]:
        """List all registered hotkeys."""
        return self.hotkeys.copy()

    def process_messages(self) -> None:
        """
        Process Windows messages (blocking).

        This should be called in a loop or integrated with Qt event loop.
        For Qt integration, use start_listening() instead.
        """
        msg = wintypes.MSG()

        while self.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY:
                self._handle_hotkey(msg.wParam)

            self.user32.TranslateMessage(ctypes.byref(msg))
            self.user32.DispatchMessageW(ctypes.byref(msg))

    def install_qt_filter(self) -> bool:
        """
        Install Qt native event filter for hotkey processing.

        Call this after Qt application is created.

        Returns:
            True if filter installed successfully
        """
        if not PYQT_AVAILABLE:
            logger.warning("PyQt6 not available, cannot install event filter")
            return False

        app = QApplication.instance()
        if not app:
            logger.error("No QApplication instance found")
            return False

        self._event_filter = QtHotkeyEventFilter(self)
        app.installNativeEventFilter(self._event_filter)
        logger.info("Qt native event filter installed for hotkeys")
        return True

    def _handle_hotkey(self, hotkey_id: int) -> None:
        """Handle hotkey activation."""
        for name, hotkey in self.hotkeys.items():
            if hotkey.hotkey_id == hotkey_id and hotkey.enabled:
                try:
                    logger.debug(f"Hotkey '{name}' activated")
                    hotkey.callback()

                    # Emit Qt signal if available
                    if PYQT_AVAILABLE and hasattr(self, 'hotkey_activated'):
                        self.hotkey_activated.emit(name)

                except Exception as e:
                    logger.error(
                        f"Error in hotkey callback '{name}': {e}",
                        exc_info=True
                    )
                break

    def save_config(self) -> bool:
        """
        Save hotkey configuration to file.

        Returns:
            True if saved successfully
        """
        try:
            config_data = {}
            for name, info in self.hotkeys.items():
                config_data[name] = info.to_dict()

            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

            logger.info(f"Hotkey configuration saved to {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save hotkey config: {e}")
            return False

    def load_config(self) -> bool:
        """
        Load hotkey configuration from file.

        Note: This only loads the configuration data. You still need to
        register hotkeys with their callbacks separately.

        Returns:
            True if loaded successfully
        """
        try:
            if not self.config_file.exists():
                logger.info("No hotkey configuration file found")
                return False

            with open(self.config_file, 'r') as f:
                config_data = json.load(f)

            logger.info(f"Loaded hotkey configuration from {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to load hotkey config: {e}")
            return False

    def get_all_hotkeys(self) -> List[Tuple[str, str, str]]:
        """
        Get list of all registered hotkeys.

        Returns:
            List of tuples (name, key_combination, description)
        """
        result = []
        for name, info in self.hotkeys.items():
            key_combo = info.get_key_string()
            result.append((name, key_combo, info.description))
        return result

    def cleanup(self) -> None:
        """Cleanup all registered hotkeys."""
        for name in list(self.hotkeys.keys()):
            self.unregister(name)

        logger.info("Hotkey manager cleaned up")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


def parse_hotkey_string(hotkey_str: str) -> Optional[Tuple[int, int]]:
    """
    Parse a hotkey string to modifiers and virtual key code.

    Args:
        hotkey_str: Hotkey string (e.g., "Ctrl+Shift+F", "Win+R")

    Returns:
        Tuple of (modifiers, vk_code) or None if invalid

    Example:
        mods, vk = parse_hotkey_string("Ctrl+Shift+F")
    """
    parts = [p.strip().upper() for p in hotkey_str.split('+')]

    if len(parts) < 2:
        return None

    modifiers = 0
    key = parts[-1]

    # Parse modifiers
    for part in parts[:-1]:
        if part in ('CTRL', 'CONTROL'):
            modifiers |= ModifierKeys.CTRL
        elif part in ('SHIFT',):
            modifiers |= ModifierKeys.SHIFT
        elif part in ('ALT',):
            modifiers |= ModifierKeys.ALT
        elif part in ('WIN', 'WINDOWS'):
            modifiers |= ModifierKeys.WIN
        else:
            return None

    # Parse key
    try:
        if key.startswith('F') and len(key) > 1 and key[1:].isdigit():
            # Function key
            f_num = int(key[1:])
            if 1 <= f_num <= 12:
                vk_code = 0x70 + (f_num - 1)
            else:
                return None
        elif len(key) == 1 and key.isalpha():
            # Letter
            vk_code = VirtualKeys.letter(key)
        elif len(key) == 1 and key.isdigit():
            # Number
            vk_code = VirtualKeys.number(int(key))
        elif key == 'SPACE':
            vk_code = VirtualKeys.VK_SPACE
        elif key == 'ENTER':
            vk_code = VirtualKeys.VK_RETURN
        elif key == 'ESC':
            vk_code = VirtualKeys.VK_ESCAPE
        elif key == 'TAB':
            vk_code = VirtualKeys.VK_TAB
        else:
            return None

        return (modifiers, vk_code)

    except ValueError:
        return None


# Example usage
if __name__ == "__main__":
    import time

    def on_search():
        print("Search hotkey pressed!")

    def on_quit():
        print("Quit hotkey pressed!")
        manager.cleanup()

    manager = HotkeyManager()

    # Register Ctrl+Shift+F for search
    manager.register(
        "search",
        ModifierKeys.CTRL | ModifierKeys.SHIFT,
        VirtualKeys.letter('F'),
        on_search,
        "Quick search"
    )

    # Register Ctrl+Q for quit
    manager.register(
        "quit",
        ModifierKeys.CTRL,
        VirtualKeys.letter('Q'),
        on_quit,
        "Quit application"
    )

    print("Hotkeys registered. Press Ctrl+Shift+F to search, Ctrl+Q to quit.")

    try:
        manager.process_messages()
    except KeyboardInterrupt:
        print("\nExiting...")
        manager.cleanup()
