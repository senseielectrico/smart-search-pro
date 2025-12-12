# Smart Search Pro - Keyboard Shortcuts Guide

## Overview

Smart Search Pro includes a comprehensive keyboard shortcuts system with:
- Global hotkeys (work system-wide)
- Local application hotkeys
- Configurable shortcuts
- Conflict detection
- Persistent configuration

## Global Hotkeys

### Show/Hide Window
- **Shortcut**: `Ctrl+Shift+F`
- **Description**: Toggle Smart Search window visibility from anywhere in Windows
- **Type**: Global (works even when app is minimized or not focused)

## Application Hotkeys

These shortcuts work when Smart Search Pro is focused:

### Search Operations

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+F` | Focus Search | Jump to search input field |
| `Ctrl+N` | New Search | Clear current search and start fresh |
| `F5` | Refresh Results | Re-run the current search |
| `Esc` | Clear/Cancel | Clear selection or close dialogs |

### Results Management

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+A` | Select All | Select all results in current view |
| `Enter` | Open File | Open selected file(s) with default application |
| `Delete` | Move to Recycle Bin | Send selected files to recycle bin |

### Export & Views

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+E` | Export Results | Open export dialog for current results |
| `Ctrl+D` | Toggle Duplicates | Switch to duplicates panel |
| `Ctrl+Space` | Toggle Preview | Show/hide preview panel |

### Application

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+,` | Settings | Open settings dialog |
| `Ctrl+K` | Keyboard Shortcuts | Configure keyboard shortcuts |
| `Ctrl+Q` | Exit | Quit application |
| `F1` | Help | Show help dialog |

## Configuration

### Accessing Hotkey Configuration
1. Go to **File → Keyboard Shortcuts** (or press `Ctrl+K`)
2. The Hotkeys dialog shows all available shortcuts
3. Click on a shortcut to change it
4. Press the desired key combination
5. Click "Apply" to set the new shortcut
6. Click "Save" to persist changes

### Customizing Shortcuts
1. Select the action you want to customize
2. Click in the "New Shortcut" field
3. Press your desired key combination
4. The system will detect conflicts automatically
5. Apply and save your changes

### Conflict Detection
The system automatically detects when:
- A shortcut is already used by another action
- A shortcut conflicts with system shortcuts (warning shown)
- Invalid key combinations are used

### Restoring Defaults
- Click "Reset to Default" for a single shortcut
- Click "Restore All Defaults" to reset everything

## Technical Details

### Global Hotkey Implementation
- Uses Windows API `RegisterHotKey`
- Integrates with Qt event loop via `QAbstractNativeEventFilter`
- Automatically handles cleanup on app exit
- NOREPEAT flag prevents repeated triggers

### Local Hotkeys
- Registered as non-global hotkeys
- Work only when application has focus
- No conflict with other applications
- Standard Qt keyboard event handling

### Configuration Persistence
- Hotkey settings saved to: `~/.smart_search/hotkeys.json`
- Automatically loaded on startup
- Changes apply immediately or on restart (depending on hotkey type)

## Tips

1. **Global Hotkey Conflicts**: If `Ctrl+Shift+F` is already used by another application, the registration will fail. Choose a different combination in settings.

2. **Quick Access**: Pin Smart Search Pro to taskbar and use `Ctrl+Shift+F` for instant access from anywhere.

3. **Tooltips**: Hover over buttons to see their keyboard shortcuts.

4. **Context-Aware**: Some shortcuts work differently depending on context (e.g., Esc in dialog vs. in results).

5. **Productivity**: Learn the shortcuts gradually - start with `Ctrl+F`, `Enter`, and `Ctrl+E` for basic workflow.

## Architecture

### Components

```
system/
  hotkeys.py              # Core hotkey manager with Windows API integration

ui/
  hotkeys_dialog.py       # Configuration dialog
  main_window.py          # Hotkey integration and handlers
```

### Key Classes

- **HotkeyManager**: Central manager for all hotkeys (global and local)
- **QtHotkeyEventFilter**: Qt native event filter for Windows messages
- **HotkeysDialog**: User interface for configuration
- **HotkeyCaptureWidget**: Widget for capturing key combinations

### Registration Flow

1. Application starts
2. HotkeyManager initialized
3. Global hotkeys registered with Windows API
4. Local hotkeys registered with manager
5. Qt event filter installed
6. User presses hotkey
7. Windows sends WM_HOTKEY message
8. Event filter catches message
9. HotkeyManager dispatches to callback
10. Action executed

## Troubleshooting

### Global Hotkey Not Working
- Check if another application is using the same shortcut
- Verify Windows Search service is running
- Run application as Administrator (if needed)
- Check Event Viewer for errors

### Local Hotkey Not Working
- Ensure application has focus
- Check for conflicting shortcuts in other Qt widgets
- Verify hotkey is enabled in configuration

### Configuration Not Saving
- Check file permissions for `~/.smart_search/` directory
- Verify disk space available
- Check application logs for errors

## Examples

### Custom Workflow Setup

**Power User**:
- `Ctrl+Shift+F`: Quick access
- `Ctrl+F`: Start typing immediately
- `Enter`: Open file
- `Ctrl+E`: Export if needed

**Batch Operations**:
- `Ctrl+A`: Select all results
- `Delete`: Move to recycle bin
- Or `Ctrl+C`: Copy files

**Research Mode**:
- `Ctrl+Space`: Toggle preview on
- Arrow keys: Navigate results
- `Ctrl+D`: Check duplicates

## Future Enhancements

Planned features:
- [ ] Mouse gesture support
- [ ] Macro recording
- [ ] Profile-based hotkey sets
- [ ] Hotkey suggestions based on usage
- [ ] Import/export hotkey configurations
- [ ] Voice command integration

## Support

For issues with keyboard shortcuts:
1. Check this guide
2. Review application logs in `~/.smart_search/logs/`
3. Open an issue with details about your system and the problem

## Version History

- **v1.0.0**: Initial hotkey system
  - Global hotkey support
  - 11 application hotkeys
  - Configuration dialog
  - Conflict detection
  - Persistent configuration
