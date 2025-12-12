# Admin Console System - Complete Guide

## Overview

The Admin Console System provides comprehensive elevated administrator console support for Smart Search Pro with UAC integration, privilege management, and embedded terminal widgets.

## Components

### 1. system/admin_console.py - Admin Console Manager

Core manager for launching and controlling administrator consoles.

#### Features
- Launch cmd.exe or PowerShell with administrator privileges
- UAC elevation via ShellExecuteEx with 'runas' verb
- Custom working directory and environment variables
- Output capture (redirected mode)
- Batch command execution
- Process monitoring and session management
- Support for multiple console types (CMD, PowerShell, PowerShell Core)

#### Basic Usage

```python
from system.admin_console import AdminConsoleManager, ConsoleConfig, ConsoleType

manager = AdminConsoleManager()

# Launch interactive PowerShell console
config = ConsoleConfig(
    console_type=ConsoleType.POWERSHELL,
    elevated=False,
    title="My Console"
)

session = manager.launch_console(config)
```

#### Batch Command Execution

```python
# Execute commands and capture output
commands = [
    'Get-Process',
    'Get-Service',
    'Get-Date'
]

success, stdout, stderr = manager.execute_batch_commands(commands)

if success:
    print(f"Output: {stdout}")
```

#### Elevated Console Launch

```python
# Launch with UAC elevation
config = ConsoleConfig(
    console_type=ConsoleType.POWERSHELL,
    elevated=True,
    title="Admin Console"
)

session = manager.launch_console(config)
# UAC prompt will be shown to user
```

#### Advanced Configuration

```python
config = ConsoleConfig(
    console_type=ConsoleType.POWERSHELL,
    working_directory="C:\\Projects",
    environment_vars={"CUSTOM_VAR": "value"},
    elevated=True,
    capture_output=True,
    show_window=ShowWindow.SW_SHOWNORMAL,
    initial_commands=['Write-Host "Welcome!"'],
    title="Custom Console"
)
```

---

### 2. system/privilege_manager.py - Privilege Management

Fine-grained Windows privilege management for specific system operations.

#### Features
- Check current process privileges
- Request specific privileges (SeBackupPrivilege, SeRestorePrivilege, etc.)
- Enable/disable privileges dynamically
- Check if user is in Administrators group
- Token manipulation utilities
- Context manager for temporary privilege elevation

#### Basic Usage

```python
from system.privilege_manager import PrivilegeManager

manager = PrivilegeManager()

# Check elevation status
print(f"Running as admin: {manager.is_admin()}")
print(f"In admin group: {manager.is_in_admin_group()}")
print(f"Current user: {manager.get_token_user()}")
```

#### Enable Specific Privileges

```python
# Enable backup privilege
if manager.enable_privilege("SeBackupPrivilege"):
    print("Backup privilege enabled!")
    # Perform backup operations
    manager.disable_privilege("SeBackupPrivilege")

# Enable both backup and restore
if manager.enable_backup_restore_privileges():
    print("Backup/restore privileges enabled!")
```

#### Check Privileges

```python
# Check if privilege exists
has_backup = manager.has_privilege("SeBackupPrivilege")

# Check if privilege is enabled
is_enabled = manager.is_privilege_enabled("SeBackupPrivilege")

# Get all privileges
for name, enabled in manager.get_all_privileges():
    print(f"{name}: {'ENABLED' if enabled else 'disabled'}")
```

#### Privilege Context Manager

```python
from system.privilege_manager import PrivilegeContext

# Temporarily enable privileges
with PrivilegeContext(["SeBackupPrivilege", "SeRestorePrivilege"]):
    # Privileges automatically enabled here
    perform_backup_operation()
    # Privileges automatically disabled on exit
```

#### Common Privileges

| Privilege | Description |
|-----------|-------------|
| `SeBackupPrivilege` | Backup files and directories |
| `SeRestorePrivilege` | Restore files and directories |
| `SeDebugPrivilege` | Debug and adjust memory of other processes |
| `SeShutdownPrivilege` | Shut down the system |
| `SeTakeOwnershipPrivilege` | Take ownership of files/objects |
| `SeSecurityPrivilege` | Manage auditing and security log |
| `SeLoadDriverPrivilege` | Load and unload device drivers |

---

### 3. ui/admin_console_widget.py - PyQt6 Console Widget

Embedded terminal widget with full console functionality in Qt.

#### Features
- Embedded PowerShell/CMD terminal in Qt application
- Command history with up/down arrow navigation
- Auto-complete for common commands
- Run as admin button with UAC shield icon
- Multiple console tabs
- Output syntax highlighting (errors, warnings, success)
- Copy/paste support
- Clear and save output options
- Dark terminal theme

#### Basic Usage

```python
from PyQt6.QtWidgets import QApplication
from ui.admin_console_widget import AdminConsoleWidget

app = QApplication(sys.argv)

widget = AdminConsoleWidget()
widget.show()

app.exec()
```

#### Integration in Main Window

```python
from ui.admin_console_widget import AdminConsoleWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Add console as a dock widget
        console_dock = QDockWidget("Admin Console", self)
        console_widget = AdminConsoleWidget()
        console_dock.setWidget(console_widget)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, console_dock)

        # Or as a tab
        tabs = QTabWidget()
        tabs.addTab(console_widget, "Console")
```

#### Features

**Command History**
- Use Up/Down arrow keys to navigate command history
- History persists for last 100 commands

**Auto-Complete**
- Press Tab to auto-complete commands
- Supports PowerShell cmdlets and common commands

**Multiple Tabs**
- Create multiple console tabs (PowerShell or CMD)
- Each tab maintains independent history and state

**Syntax Highlighting**
- Errors shown in red
- Warnings in yellow
- Success messages in green
- Prompts in blue

---

### 4. ui/elevation_dialog.py - Elevation Request Dialog

UAC-style dialog for requesting administrator privileges.

#### Features
- UAC shield icon (custom painted)
- Operation description with details
- Remember choice option
- Cancel/Elevate buttons
- Windows UAC-inspired styling
- Full and quick dialog variants

#### Full Elevation Dialog

```python
from ui.elevation_dialog import ElevationDialog

dialog = ElevationDialog(
    operation="Modify System Files",
    description="Smart Search Pro needs to access system directories.",
    show_remember=True,
    parent=self
)

if dialog.exec() == QDialog.DialogCode.Accepted:
    # User approved elevation
    if dialog.get_remember_choice():
        # User wants to remember this choice
        pass
```

#### Quick Elevation Dialog

```python
from ui.elevation_dialog import QuickElevationDialog

dialog = QuickElevationDialog(
    operation="Access protected directory",
    parent=self
)

if dialog.exec() == QDialog.DialogCode.Accepted:
    # User approved
    perform_elevated_operation()
```

#### Custom UAC Shield Icon

```python
from ui.elevation_dialog import UACShieldIcon

# Add shield icon to button
shield = UACShieldIcon(size=24)
layout.addWidget(shield)
```

---

## Architecture

### Console Session Management

```
AdminConsoleManager
├── ConsoleSession (tracks active console)
│   ├── process_handle
│   ├── process_id
│   ├── console_type
│   ├── elevated
│   └── working_directory
├── Launch Methods
│   ├── _launch_elevated_console (via ShellExecuteW + runas)
│   ├── _launch_with_createprocess (Win32 API)
│   └── _launch_with_subprocess (fallback)
└── Session Tracking
    ├── active_sessions dict
    ├── is_session_active()
    └── close_session()
```

### Privilege Management

```
PrivilegeManager
├── Token Operations
│   ├── get_process_token()
│   ├── get_token_user()
│   └── get_token_groups()
├── Privilege Checks
│   ├── has_privilege()
│   ├── is_privilege_enabled()
│   └── get_all_privileges()
├── Privilege Control
│   ├── enable_privilege()
│   ├── disable_privilege()
│   └── PrivilegeContext (RAII)
└── Elevation Helpers
    ├── is_admin()
    ├── is_in_admin_group()
    └── elevate_if_needed()
```

### UI Widget Hierarchy

```
AdminConsoleWidget
├── QToolBar (controls)
│   ├── New PowerShell button
│   ├── New CMD button
│   ├── Run as Administrator button
│   ├── Clear button
│   └── Save Output button
└── QTabWidget (console tabs)
    └── AdminConsoleTab (per console)
        ├── ConsoleOutputWidget (QTextEdit)
        │   ├── Syntax highlighting
        │   └── Dark terminal theme
        ├── ConsoleInputWidget (QLineEdit)
        │   ├── Command history
        │   └── Auto-complete
        └── CommandExecutor (QThread)
            └── Batch execution
```

---

## Security Considerations

### Input Sanitization

All command-line arguments are sanitized using `sanitize_cli_argument()` from `core.security`:

```python
from core.security import sanitize_cli_argument

# Arguments are automatically sanitized
safe_arg = sanitize_cli_argument(user_input)
```

### Privilege Least Access

Always request only the minimum required privileges:

```python
# Good: Request specific privilege
with PrivilegeContext(["SeBackupPrivilege"]):
    backup_files()

# Bad: Run entire application elevated
manager.relaunch_elevated()  # Only when necessary
```

### Elevation Prompts

Always inform user about elevated operations:

```python
# Show dialog before elevation
dialog = ElevationDialog(
    operation="Clear description",
    description="Detailed explanation",
    parent=self
)

if dialog.exec() == QDialog.DialogCode.Accepted:
    # Proceed with elevation
    pass
```

---

## Common Use Cases

### 1. Execute Admin Command

```python
from system.admin_console import AdminConsoleManager, ConsoleConfig, ConsoleType

manager = AdminConsoleManager()

# Execute single command
commands = ['Get-Service | Where-Object {$_.Status -eq "Running"}']
success, stdout, stderr = manager.execute_batch_commands(commands)
```

### 2. Access Protected Files

```python
from system.privilege_manager import PrivilegeContext

# Enable backup privilege to read protected files
with PrivilegeContext(["SeBackupPrivilege"]):
    with open(r"C:\Windows\System32\config\SAM", "rb") as f:
        data = f.read()
```

### 3. Launch Elevated Console for User

```python
from ui.elevation_dialog import ElevationDialog
from system.admin_console import AdminConsoleManager, ConsoleConfig, ConsoleType

# Ask user
dialog = ElevationDialog(
    operation="Launch Administrator Console",
    description="Open console with full system access.",
    parent=self
)

if dialog.exec() == QDialog.DialogCode.Accepted:
    # Launch elevated
    manager = AdminConsoleManager()
    config = ConsoleConfig(
        console_type=ConsoleType.POWERSHELL,
        elevated=True,
        title="Admin Console"
    )
    manager.launch_console(config)
```

### 4. Embed Console in Application

```python
from PyQt6.QtWidgets import QMainWindow, QDockWidget
from PyQt6.QtCore import Qt
from ui.admin_console_widget import AdminConsoleWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create console widget
        console = AdminConsoleWidget()

        # Add as docked panel
        dock = QDockWidget("Console", self)
        dock.setWidget(console)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
```

### 5. Check Privileges Before Operation

```python
from system.privilege_manager import PrivilegeManager

manager = PrivilegeManager()

# Check required privileges
required = ["SeBackupPrivilege", "SeRestorePrivilege"]
if not manager.elevate_if_needed(required):
    QMessageBox.critical(
        self,
        "Insufficient Privileges",
        "This operation requires administrator privileges."
    )
    return
```

---

## Testing

Run the comprehensive test suite:

```bash
python test_admin_console.py
```

### Test Coverage

- ✓ Elevation detection
- ✓ Privilege checking and manipulation
- ✓ Console path detection
- ✓ Batch command execution
- ✓ Interactive console launch
- ✓ Elevated console with UAC
- ✓ UI widget functionality
- ✓ Elevation dialogs

---

## Error Handling

### Access Denied

```python
try:
    manager.enable_privilege("SeDebugPrivilege")
except PermissionError:
    # Not running as admin
    QMessageBox.warning(
        self,
        "Permission Denied",
        "Administrator privileges required."
    )
```

### UAC Declined

```python
config = ConsoleConfig(elevated=True)
session = manager.launch_console(config)

if not session:
    # UAC was declined or failed
    QMessageBox.information(
        self,
        "Elevation Declined",
        "Administrator elevation was not granted."
    )
```

### Command Execution Failure

```python
success, stdout, stderr = manager.execute_batch_commands(commands)

if not success:
    logger.error(f"Command failed: {stderr}")
    # Handle error
```

---

## Best Practices

### 1. Minimize Elevation Scope

```python
# Good: Elevate only specific operation
with PrivilegeContext(["SeBackupPrivilege"]):
    perform_backup()

# Bad: Elevate entire application
if not manager.is_admin():
    manager.relaunch_elevated()  # Overkill
```

### 2. Inform Users

```python
# Always show dialog before elevation
dialog = ElevationDialog(
    operation="Clear operation name",
    description="Explain why elevation is needed",
    parent=self
)

if dialog.exec() == QDialog.DialogCode.Accepted:
    # Proceed
    pass
```

### 3. Handle UAC Gracefully

```python
session = manager.launch_console(config)

if not session:
    # Don't fail silently
    QMessageBox.information(
        self,
        "Operation Cancelled",
        "Administrator privileges were not granted. "
        "Operation cancelled."
    )
    return
```

### 4. Clean Up Resources

```python
try:
    session = manager.launch_console(config)
    # Use session
finally:
    manager.cleanup()  # Always cleanup
```

### 5. Use Context Managers

```python
# Privileges automatically cleaned up
with PrivilegeContext(["SeBackupPrivilege"]):
    # Privilege enabled
    perform_operation()
# Privilege automatically disabled
```

---

## Integration with Smart Search Pro

### Add Console to Main Window

```python
# In ui/main_window.py

from ui.admin_console_widget import AdminConsoleWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Add console menu action
        console_action = QAction("Admin Console", self)
        console_action.triggered.connect(self.show_admin_console)
        tools_menu.addAction(console_action)

    def show_admin_console(self):
        """Show admin console dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Administrator Console")
        dialog.resize(900, 600)

        layout = QVBoxLayout(dialog)
        console = AdminConsoleWidget()
        layout.addWidget(console)

        dialog.exec()
```

### Use for File Operations

```python
from system.privilege_manager import PrivilegeContext

def copy_protected_file(src, dst):
    """Copy file with backup privilege."""
    try:
        with PrivilegeContext(["SeBackupPrivilege", "SeRestorePrivilege"]):
            shutil.copy2(src, dst)
        return True
    except Exception as e:
        logger.error(f"Copy failed: {e}")
        return False
```

---

## API Reference

### AdminConsoleManager

#### Methods

- `launch_console(config: ConsoleConfig) -> Optional[ConsoleSession]`
  - Launch console with configuration

- `execute_batch_commands(commands: List[str], config: Optional[ConsoleConfig]) -> Tuple[bool, str, str]`
  - Execute batch commands and return (success, stdout, stderr)

- `is_session_active(session: ConsoleSession) -> bool`
  - Check if session is still running

- `close_session(session: ConsoleSession, force: bool) -> bool`
  - Close console session

- `get_active_sessions() -> List[ConsoleSession]`
  - Get list of active sessions

- `cleanup()`
  - Cleanup all sessions

### PrivilegeManager

#### Methods

- `is_admin() -> bool`
  - Check if running as administrator

- `is_in_admin_group() -> bool`
  - Check if user is in Administrators group

- `has_privilege(name: str) -> bool`
  - Check if privilege exists

- `is_privilege_enabled(name: str) -> bool`
  - Check if privilege is enabled

- `enable_privilege(name: str) -> bool`
  - Enable privilege

- `disable_privilege(name: str) -> bool`
  - Disable privilege

- `get_all_privileges() -> List[Tuple[str, bool]]`
  - Get all privileges with status

- `elevate_if_needed(privileges: List[str]) -> bool`
  - Elevate if privileges not available

### AdminConsoleWidget

#### Signals

- None (internal use)

#### Methods

- No public methods needed (self-contained widget)

### ElevationDialog

#### Methods

- `get_remember_choice() -> bool`
  - Get whether user wants to remember choice

---

## Dependencies

- **pywin32** - Windows API access
- **PyQt6** - UI framework
- **core.security** - Input sanitization
- **system.elevation** - Elevation manager

---

## License

Part of Smart Search Pro system.

---

## Support

For issues or questions:
1. Check test suite: `python test_admin_console.py`
2. Review logs in Smart Search Pro log directory
3. Verify pywin32 is installed: `pip install pywin32`

---

**Last Updated:** 2025-12-12
**Version:** 1.0.0
