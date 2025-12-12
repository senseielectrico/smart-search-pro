# Smart Search Pro - System Integration Module

This module provides Windows system integration features for Smart Search Pro.

## Features

### 1. System Tray Icon (`tray.py`)
- System tray icon with context menu
- Quick search popup
- Recent searches menu
- Show/hide main window
- System notifications

**Requirements:** PyQt6

**Example:**
```python
from PyQt6.QtWidgets import QApplication
from system.tray import SystemTrayIcon

app = QApplication(sys.argv)
tray = SystemTrayIcon()

# Connect signals
tray.quick_search_requested.connect(on_search)
tray.exit_requested.connect(app.quit)

tray.show()
tray.show_notification("Smart Search Pro", "Application started")
```

### 2. Global Hotkeys (`hotkeys.py`)
- Register system-wide hotkeys using Windows API
- Multiple modifier keys (Ctrl, Shift, Alt, Win)
- Enable/disable hotkeys dynamically
- Automatic cleanup

**Example:**
```python
from system.hotkeys import HotkeyManager, ModifierKeys, VirtualKeys

manager = HotkeyManager()

# Register Ctrl+Shift+F
manager.register(
    "search",
    ModifierKeys.CTRL | ModifierKeys.SHIFT,
    VirtualKeys.letter('F'),
    on_search_callback,
    "Quick search"
)

# Process messages
manager.process_messages()  # Blocking
# OR integrate with Qt event loop
```

### 3. Administrator Elevation (`elevation.py`)
- Check if running as administrator
- Request UAC elevation
- Run specific operations elevated
- Relaunch application elevated

**Example:**
```python
from system.elevation import ElevationManager

manager = ElevationManager()

if not manager.is_elevated():
    manager.relaunch_elevated()  # Will relaunch and exit
    sys.exit()

# Continue with elevated operations
```

### 4. Shell Integration (`shell_integration.py`)
- Context menu registration
- File type associations
- Send To menu integration
- App ID for taskbar grouping

**Requirements:** Administrator privileges for most operations

**Example:**
```python
from system.shell_integration import ShellIntegration, ContextMenuItem

manager = ShellIntegration()

# Add context menu
item = ContextMenuItem(
    name="Search with Smart Search",
    command=f'"{app_path}" --search "%1"',
    icon=f"{app_path},0"
)
manager.add_context_menu(item, file_types=[".txt", ".pdf"])

# Register file association
manager.register_file_association(
    ".ssp",
    "SmartSearch.Index",
    "Smart Search Index File",
    app_path,
    icon_path
)
```

### 5. Autostart Management (`autostart.py`)
- Add/remove from Windows startup
- Multiple methods:
  - Registry (Current User)
  - Registry (Local Machine) - requires admin
  - Task Scheduler
  - Startup Folder
- Check current status

**Example:**
```python
from system.autostart import AutostartManager, StartupMethod

manager = AutostartManager("SmartSearchPro")

# Enable autostart
manager.enable(
    executable_path,
    "--minimized --tray",
    StartupMethod.REGISTRY_CURRENT_USER
)

# Check status
is_enabled = manager.is_enabled(StartupMethod.REGISTRY_CURRENT_USER)

# Disable
manager.disable(StartupMethod.REGISTRY_CURRENT_USER)
```

### 6. Single Instance (`single_instance.py`)
- Ensure only one instance runs
- Activate existing instance
- Send messages between instances
- Mutex-based locking

**Example:**
```python
from system.single_instance import SingleInstanceManager

manager = SingleInstanceManager("SmartSearchPro")

if not manager.is_first_instance():
    # Activate existing instance and exit
    manager.activate_existing_instance()
    sys.exit(0)

# Continue with application
manager.set_window_handle(main_window.winId())
```

## Complete Integration Example

```python
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from system import (
    SystemTrayIcon,
    HotkeyManager,
    ElevationManager,
    ShellIntegration,
    AutostartManager,
    SingleInstanceManager,
)

class SmartSearchApp:
    def __init__(self):
        # Check single instance
        self.instance_manager = SingleInstanceManager("SmartSearchPro")
        if not self.instance_manager.is_first_instance():
            self.instance_manager.activate_existing_instance()
            sys.exit(0)

        # Initialize Qt application
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Create main window
        self.window = QMainWindow()
        self.window.setWindowTitle("Smart Search Pro")

        # Set single instance window handle
        self.instance_manager.set_window_handle(self.window.winId())

        # Setup system tray
        self.setup_tray()

        # Setup hotkeys
        self.setup_hotkeys()

        # Setup autostart
        self.setup_autostart()

        # Setup shell integration (if admin)
        self.setup_shell_integration()

    def setup_tray(self):
        """Setup system tray icon."""
        self.tray = SystemTrayIcon()
        self.tray.show_main_window.connect(self.window.show)
        self.tray.hide_main_window.connect(self.window.hide)
        self.tray.quick_search_requested.connect(self.on_search)
        self.tray.exit_requested.connect(self.quit)
        self.tray.show()
        self.tray.set_tooltip("Smart Search Pro")

    def setup_hotkeys(self):
        """Setup global hotkeys."""
        from system.hotkeys import ModifierKeys, VirtualKeys

        self.hotkey_manager = HotkeyManager()

        # Ctrl+Shift+F - Quick search
        self.hotkey_manager.register(
            "quick_search",
            ModifierKeys.CTRL | ModifierKeys.SHIFT,
            VirtualKeys.letter('F'),
            self.show_quick_search,
            "Quick search"
        )

        # Ctrl+Shift+S - Show window
        self.hotkey_manager.register(
            "show_window",
            ModifierKeys.CTRL | ModifierKeys.SHIFT,
            VirtualKeys.letter('S'),
            self.window.show,
            "Show window"
        )

    def setup_autostart(self):
        """Setup autostart if enabled in settings."""
        from system.autostart import StartupMethod

        self.autostart_manager = AutostartManager("SmartSearchPro")

        # Check if autostart is desired (from settings)
        if self.should_autostart():
            if not self.autostart_manager.is_enabled(
                StartupMethod.REGISTRY_CURRENT_USER
            ):
                self.autostart_manager.enable(
                    sys.executable,
                    "--minimized --tray",
                    StartupMethod.REGISTRY_CURRENT_USER
                )

    def setup_shell_integration(self):
        """Setup shell integration if running as admin."""
        elevation = ElevationManager()

        if elevation.is_elevated():
            from system.shell_integration import ContextMenuItem

            self.shell = ShellIntegration()

            # Add context menu for common file types
            item = ContextMenuItem(
                name="Search with Smart Search Pro",
                command=f'"{sys.executable}" --search "%1"',
            )
            self.shell.add_context_menu(
                item,
                file_types=[".txt", ".pdf", ".doc", ".docx"]
            )

            # Set App ID
            self.shell.set_app_id("com.smartsearch.pro")

    def on_search(self, query: str):
        """Handle search request."""
        print(f"Searching for: {query}")
        self.tray.add_recent_search(query)
        # Perform actual search...

    def show_quick_search(self):
        """Show quick search popup."""
        self.tray.show_quick_search()

    def should_autostart(self) -> bool:
        """Check if autostart is enabled in settings."""
        # Load from settings...
        return False

    def quit(self):
        """Quit application."""
        self.hotkey_manager.cleanup()
        self.instance_manager.cleanup()
        self.tray.cleanup()
        self.app.quit()

    def run(self):
        """Run the application."""
        return self.app.exec()

if __name__ == "__main__":
    app = SmartSearchApp()
    sys.exit(app.run())
```

## Testing

Run the test suite:

```bash
python system/test_system.py
```

Individual test functions are available for each module.

## Requirements

- Windows 10 or later
- Python 3.8+
- PyQt6 (for system tray)
- Administrator privileges (for shell integration)

## Installation

```bash
pip install PyQt6
```

## Notes

- Most shell integration features require administrator privileges
- Hotkeys are system-wide and may conflict with other applications
- Single instance uses a mutex with the application name
- Autostart can be configured per-user or system-wide

## License

Part of Smart Search Pro application.
