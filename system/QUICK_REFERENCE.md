# System Integration - Quick Reference

## Installation

```bash
pip install PyQt6
```

## Module Overview

| Module | Purpose | Admin Required |
|--------|---------|----------------|
| `tray.py` | System tray icon and notifications | No |
| `hotkeys.py` | Global hotkey registration | No |
| `elevation.py` | Administrator privilege management | No |
| `shell_integration.py` | Context menus, file associations | Yes |
| `autostart.py` | Windows startup management | No* |
| `single_instance.py` | Single instance enforcement | No |

*Some autostart methods require admin

## Quick Start

### 1. Single Instance Check

```python
from system.single_instance import SingleInstanceManager

manager = SingleInstanceManager("MyApp")
if not manager.is_first_instance():
    manager.activate_existing_instance()
    sys.exit(0)
```

### 2. System Tray Icon

```python
from PyQt6.QtWidgets import QApplication
from system.tray import SystemTrayIcon

app = QApplication(sys.argv)
tray = SystemTrayIcon()
tray.quick_search_requested.connect(lambda q: print(f"Search: {q}"))
tray.show()
```

### 3. Global Hotkeys

```python
from system.hotkeys import HotkeyManager, ModifierKeys, VirtualKeys

manager = HotkeyManager()
manager.register(
    "search",
    ModifierKeys.CTRL | ModifierKeys.SHIFT,
    VirtualKeys.letter('F'),
    on_search_callback
)
```

### 4. Autostart

```python
from system.autostart import AutostartManager, StartupMethod

manager = AutostartManager("MyApp")
manager.enable(
    r"C:\MyApp\app.exe",
    "--minimized",
    StartupMethod.REGISTRY_CURRENT_USER
)
```

### 5. Check Elevation

```python
from system.elevation import ElevationManager

manager = ElevationManager()
if not manager.is_elevated():
    manager.relaunch_elevated()
    sys.exit()
```

### 6. Context Menu

```python
from system.shell_integration import ShellIntegration, ContextMenuItem

manager = ShellIntegration()
item = ContextMenuItem(
    name="Open with MyApp",
    command='"C:\\MyApp\\app.exe" "%1"'
)
manager.add_context_menu(item, file_types=[".txt"])
```

## Common Patterns

### Application Initialization

```python
# 1. Check single instance
instance_manager = SingleInstanceManager("MyApp")
if not instance_manager.is_first_instance():
    instance_manager.activate_existing_instance()
    sys.exit(0)

# 2. Initialize Qt
app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

# 3. Setup tray
tray = SystemTrayIcon()
tray.show()

# 4. Setup hotkeys
hotkey_manager = HotkeyManager()
hotkey_manager.register(...)

# 5. Run
sys.exit(app.exec())
```

### Cleanup

```python
def cleanup():
    tray.cleanup()
    hotkey_manager.cleanup()
    instance_manager.cleanup()
    app.quit()
```

## Common Hotkey Combinations

```python
# Ctrl+Shift+F
ModifierKeys.CTRL | ModifierKeys.SHIFT, VirtualKeys.letter('F')

# Win+S
ModifierKeys.WIN, VirtualKeys.letter('S')

# Ctrl+Alt+Delete
ModifierKeys.CTRL | ModifierKeys.ALT, VirtualKeys.letter('Delete')

# F12
0, VirtualKeys.VK_F12
```

## Virtual Key Codes

```python
# Letters
VirtualKeys.letter('A')  # through 'Z'

# Numbers
VirtualKeys.number(5)  # 0-9

# Function keys
VirtualKeys.VK_F1  # through VK_F12

# Special keys
VirtualKeys.VK_SPACE
VirtualKeys.VK_RETURN
VirtualKeys.VK_ESCAPE
VirtualKeys.VK_TAB
```

## Autostart Methods

| Method | Scope | Admin | Pros | Cons |
|--------|-------|-------|------|------|
| `REGISTRY_CURRENT_USER` | User | No | Simple, reliable | Registry only |
| `REGISTRY_LOCAL_MACHINE` | System | Yes | All users | Requires admin |
| `TASK_SCHEDULER` | User/System | No* | Flexible, delayed start | Complex |
| `STARTUP_FOLDER` | User | No | User-visible | Easy to disable |

## Error Handling

```python
# Hotkey already registered
try:
    manager.register(...)
except Exception as e:
    if "already registered" in str(e):
        manager.unregister(name)
        manager.register(...)

# Elevation failed
if not elevation.request_elevation():
    print("User cancelled elevation")
    # Fallback to non-admin mode

# Single instance activation failed
if not instance.activate_existing_instance():
    # Could not find window, continue anyway
    pass
```

## Testing

```bash
# Run all tests
python system/test_system.py

# Run specific test
python system/test_system.py
# Then select from menu

# Test individual modules
python system/tray.py
python system/hotkeys.py
python system/single_instance.py
```

## Troubleshooting

### Hotkeys Not Working
- Check if another app uses same hotkey
- Try different modifier combination
- Verify `process_messages()` is called

### Tray Icon Not Showing
- Install PyQt6: `pip install PyQt6`
- Check system tray settings in Windows
- Verify app isn't hidden in overflow

### Autostart Not Working
- Check Windows Startup settings
- Verify executable path is correct
- Use absolute paths, not relative
- Check Task Scheduler for task-based startup

### Context Menu Not Appearing
- Requires administrator privileges
- Run as admin or use `elevation.py`
- Refresh Windows Explorer (F5)
- Check registry for entries

### Single Instance Not Working
- Check if mutex name is unique
- Verify window title matches
- Check if first instance exited cleanly

## Platform Requirements

- **OS**: Windows 10 or later
- **Python**: 3.8+
- **Dependencies**: PyQt6 (for tray icon)
- **Admin**: Required for shell integration only

## Security Notes

1. **Hotkeys**: System-wide, can conflict with other apps
2. **Elevation**: Always validate user intent before requesting
3. **Registry**: Modifications are permanent, provide uninstall
4. **Shell Integration**: Context menus visible to all users (if HKLM)
5. **Single Instance**: Mutex name should be unique per app

## Performance Tips

1. Initialize hotkeys after UI to prevent blocking
2. Use Task Scheduler for delayed startup
3. Register only needed context menu items
4. Cleanup resources on exit
5. Handle elevation requests asynchronously

## See Also

- `README.md` - Detailed documentation
- `test_system.py` - Test suite
- `example_integration.py` - Complete example
- Individual module docstrings for API details
