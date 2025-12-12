# Admin Console System - Quick Reference

## Quick Start

### 1. Launch Interactive Console

```python
from system.admin_console import AdminConsoleManager, ConsoleConfig, ConsoleType

manager = AdminConsoleManager()
config = ConsoleConfig(console_type=ConsoleType.POWERSHELL)
session = manager.launch_console(config)
```

### 2. Execute Commands

```python
commands = ['Get-Process', 'Get-Date']
success, stdout, stderr = manager.execute_batch_commands(commands)
print(stdout)
```

### 3. Enable Privilege

```python
from system.privilege_manager import PrivilegeContext

with PrivilegeContext(["SeBackupPrivilege"]):
    # Perform privileged operation
    pass
```

### 4. Show Elevation Dialog

```python
from ui.elevation_dialog import ElevationDialog

dialog = ElevationDialog(
    operation="System Operation",
    description="Requires admin access",
    parent=self
)

if dialog.exec() == QDialog.DialogCode.Accepted:
    # User approved
    pass
```

### 5. Embed Console Widget

```python
from ui.admin_console_widget import AdminConsoleWidget

console = AdminConsoleWidget()
layout.addWidget(console)
```

---

## Console Types

| Type | Enum Value | Path |
|------|------------|------|
| CMD | `ConsoleType.CMD` | C:\Windows\System32\cmd.exe |
| PowerShell | `ConsoleType.POWERSHELL` | C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe |
| PowerShell Core | `ConsoleType.POWERSHELL_CORE` | pwsh.exe (from PATH) |

---

## Common Privileges

| Privilege Name | Use Case |
|----------------|----------|
| `SeBackupPrivilege` | Read protected files |
| `SeRestorePrivilege` | Write protected files |
| `SeDebugPrivilege` | Debug processes |
| `SeShutdownPrivilege` | Shutdown system |
| `SeTakeOwnershipPrivilege` | Take file ownership |

---

## Console Configuration Options

```python
ConsoleConfig(
    console_type=ConsoleType.POWERSHELL,  # CMD, POWERSHELL, POWERSHELL_CORE
    working_directory="C:\\Projects",      # Starting directory
    environment_vars={"VAR": "value"},     # Additional env vars
    elevated=True,                         # Launch with UAC
    capture_output=True,                   # Redirect stdout/stderr
    show_window=ShowWindow.SW_SHOWNORMAL,  # Window visibility
    initial_commands=['echo "Hi"'],        # Run on start
    title="My Console"                     # Window title
)
```

---

## Error Handling Patterns

### UAC Declined

```python
session = manager.launch_console(config)
if not session:
    QMessageBox.warning(self, "Error", "Elevation declined")
```

### Privilege Not Available

```python
if not manager.has_privilege("SeBackupPrivilege"):
    QMessageBox.critical(self, "Error", "Missing privilege")
```

### Command Execution Failed

```python
success, stdout, stderr = manager.execute_batch_commands(commands)
if not success:
    logger.error(f"Command failed: {stderr}")
```

---

## Widget Features

### AdminConsoleWidget

- **Multiple Tabs**: PowerShell and CMD tabs
- **Command History**: Up/Down arrows
- **Auto-Complete**: Tab key
- **Syntax Highlighting**: Colored output
- **Run as Admin**: UAC elevation button
- **Save Output**: Export to text file

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Up Arrow | Previous command |
| Down Arrow | Next command |
| Tab | Auto-complete |
| Enter | Execute command |
| Ctrl+C | Copy |
| Ctrl+V | Paste |

---

## Best Practices

### ✅ DO

- Use `PrivilegeContext` for temporary elevation
- Show `ElevationDialog` before elevation
- Handle UAC decline gracefully
- Sanitize all user input
- Clean up with `manager.cleanup()`

### ❌ DON'T

- Don't elevate entire application unnecessarily
- Don't enable privileges without cleanup
- Don't ignore UAC failures
- Don't run unsanitized commands
- Don't forget error handling

---

## Common Patterns

### Pattern 1: Safe Privileged Operation

```python
from system.privilege_manager import PrivilegeContext

try:
    with PrivilegeContext(["SeBackupPrivilege"]):
        perform_backup()
except Exception as e:
    logger.error(f"Backup failed: {e}")
```

### Pattern 2: User-Approved Elevation

```python
from ui.elevation_dialog import ElevationDialog

dialog = ElevationDialog(
    operation="Delete System File",
    description="This will permanently delete protected files.",
    parent=self
)

if dialog.exec() == QDialog.DialogCode.Accepted:
    with PrivilegeContext(["SeRestorePrivilege"]):
        os.remove(protected_file)
```

### Pattern 3: Execute with Feedback

```python
from PyQt6.QtWidgets import QProgressDialog

progress = QProgressDialog("Executing commands...", "Cancel", 0, 0, self)
progress.show()

success, stdout, stderr = manager.execute_batch_commands(commands)

progress.close()

if success:
    QMessageBox.information(self, "Success", stdout)
else:
    QMessageBox.critical(self, "Error", stderr)
```

### Pattern 4: Console in Dialog

```python
def show_console_dialog(self):
    dialog = QDialog(self)
    dialog.setWindowTitle("Admin Console")
    dialog.resize(900, 600)

    layout = QVBoxLayout(dialog)
    console = AdminConsoleWidget()
    layout.addWidget(console)

    dialog.exec()
```

---

## Testing

```bash
# Run full test suite
python test_admin_console.py

# Run specific tests interactively
# Will prompt for user input at each step
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "pywin32 not available" | `pip install pywin32` |
| UAC always fails | Run application as admin |
| Privilege enable fails | Need admin rights first |
| Console not found | Check console paths exist |
| Output not captured | Set `capture_output=True` |

---

## Integration Example

```python
# Add to main window menu
def _create_menu(self):
    tools_menu = self.menuBar().addMenu("Tools")

    # Admin console action
    console_action = QAction("Admin Console", self)
    console_action.setShortcut("Ctrl+Alt+C")
    console_action.triggered.connect(self.show_admin_console)
    tools_menu.addAction(console_action)

def show_admin_console(self):
    dialog = QDialog(self)
    dialog.setWindowTitle("Administrator Console")
    dialog.resize(900, 600)

    layout = QVBoxLayout(dialog)
    console = AdminConsoleWidget()
    layout.addWidget(console)

    dialog.exec()
```

---

## API Cheat Sheet

### AdminConsoleManager

```python
manager = AdminConsoleManager()

# Launch
session = manager.launch_console(config)

# Execute
success, out, err = manager.execute_batch_commands(cmds)

# Check
active = manager.is_session_active(session)

# Close
manager.close_session(session)
manager.cleanup()
```

### PrivilegeManager

```python
mgr = PrivilegeManager()

# Check
is_admin = mgr.is_admin()
has = mgr.has_privilege("SeBackupPrivilege")
enabled = mgr.is_privilege_enabled("SeBackupPrivilege")

# Control
mgr.enable_privilege("SeBackupPrivilege")
mgr.disable_privilege("SeBackupPrivilege")

# Context
with PrivilegeContext(["SeBackupPrivilege"]):
    # Auto-enabled and auto-disabled
    pass
```

### ElevationManager

```python
from system.elevation import ElevationManager

mgr = ElevationManager()

# Check
is_elevated = mgr.is_elevated()
is_admin = mgr.is_admin()

# Elevate
mgr.relaunch_elevated()  # Exits current process

# Run elevated
mgr.run_elevated("notepad.exe", ["file.txt"])
```

---

**Quick Links:**
- Full Guide: [ADMIN_CONSOLE_GUIDE.md](ADMIN_CONSOLE_GUIDE.md)
- Tests: [test_admin_console.py](test_admin_console.py)
- Example: [system_admin_console_example.py](system_admin_console_example.py)
