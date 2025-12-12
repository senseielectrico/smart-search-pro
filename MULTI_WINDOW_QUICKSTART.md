# Multi-Window Quick Start Guide

## Installation

All multi-window files are already in place:

```
✓ core/window_state.py          - State persistence
✓ ui/window_manager.py          - Window management
✓ ui/secondary_window.py        - Secondary windows
✓ ui/window_menu.py             - Window menu
✓ ui/tab_manager.py             - Tab management
```

No additional dependencies required - uses existing PyQt6.

## Quick Setup (3 Steps)

### Step 1: Update main_window.py

Add window tracking to MainWindow class:

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Add these lines at the start
        self.window_id = None
        self.is_primary = False
        self._created_at = time.time()

        # Rest of your existing code...
```

### Step 2: Update main app entry point

Replace single window creation with window manager:

**Before:**
```python
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

**After:**
```python
from ui.window_manager import get_window_manager

def main():
    app = QApplication(sys.argv)

    # Create window manager
    manager = get_window_manager()

    # Create or restore windows
    saved_windows = manager._state_manager.get_all_windows()
    if saved_windows:
        manager.restore_layout()
    else:
        manager.create_window(is_primary=True)

    sys.exit(app.exec())
```

### Step 3: Add Window menu to MainWindow

In `_create_menus()` method:

```python
def _create_menus(self):
    menubar = self.menuBar()

    # ... existing menus (File, Edit, View, Tools) ...

    # Add Window menu (NEW!)
    from ui.window_manager import get_window_manager
    from ui.window_menu import create_window_menu

    manager = get_window_manager()
    window_menu_manager = create_window_menu(manager)
    menubar.addMenu(window_menu_manager.get_menu())

    # ... Help menu ...
```

## That's It!

Now you have:
- ✓ Multiple independent windows (Ctrl+N)
- ✓ Duplicate windows (Ctrl+Shift+N)
- ✓ Window arrangements (Cascade, Tile)
- ✓ Persistent layouts
- ✓ Window switching (Ctrl+1-9)

## Basic Usage

### Create New Window
```
Menu: Window > New Window
Shortcut: Ctrl+N
```

### Duplicate Current Window
```
Menu: Window > Duplicate Window
Shortcut: Ctrl+Shift+N
```

### Close Window
```
Menu: Window > Close Window
Shortcut: Ctrl+W
```

### Arrange Windows
```
Menu: Window > Arrange > Cascade
Menu: Window > Arrange > Tile Horizontally
Menu: Window > Arrange > Tile Vertically
```

### Switch Between Windows
```
Shortcut: Ctrl+1 (first window)
Shortcut: Ctrl+2 (second window)
...
Shortcut: Ctrl+9 (ninth window)
```

### Save Layout
```
Menu: Window > Arrange > Save Layout
```

### Restore Layout
```
Menu: Window > Arrange > Restore Layout
(Automatically restores on app start)
```

## Advanced Features

### Mini Mode Windows

Create compact search window:

```python
from ui.secondary_window import create_secondary_window

window = create_secondary_window(mini_mode=True)
```

### Programmatic Window Creation

```python
from ui.window_manager import get_window_manager

manager = get_window_manager()

# Create window with specific search
window = manager.create_window()
window.search_panel.search_input.setText("*.py")
```

### Tab-Based Interface (Alternative)

If you prefer tabs instead of windows:

```python
from ui.tab_manager import SearchTabWidget, TabManager

# Replace main results area with tab widget
tab_widget = SearchTabWidget()
tab_manager = TabManager(tab_widget)

# Create tabs
tab_manager.create_tab("Search 1")
tab_manager.create_tab("Search 2")

# Users can drag tabs out to create windows
```

## Shared Resources (Optional but Recommended)

Share search engine, database, and cache across windows:

```python
from ui.window_manager import get_window_manager

manager = get_window_manager()

# Set shared resources (prevents duplication)
manager.set_shared_resources(
    search_engine=your_search_engine,
    database=your_database,
    cache=your_cache
)
```

This ensures:
- Single database connection pool
- Shared search index
- Unified cache
- Better memory usage

## Testing

Run the test suite to verify everything works:

```bash
python test_multi_window.py
```

Expected output:
```
=== Testing Window State Persistence ===
✓ Window state saved
✓ Window state loaded correctly
✓ Window state persistence tests passed

=== Testing Window Manager ===
✓ Created first window
✓ Created second window
...
✓ ALL TESTS PASSED
```

## Troubleshooting

### Q: Windows appear in wrong position
**A:** Delete `data/window_state.json` to reset layout

### Q: Ctrl+N not working
**A:** Make sure Window menu is added to menubar

### Q: Layout not restoring on startup
**A:** Check if `data/window_state.json` exists and is readable

### Q: Memory issues with many windows
**A:** Limit to 5-10 windows, use mini mode for quick searches

## Example Workflows

### Workflow 1: Compare Search Results

1. Create window (Ctrl+N)
2. Search for "*.py" in first window
3. Duplicate window (Ctrl+Shift+N)
4. Search for "*.txt" in second window
5. Arrange side by side (Window > Arrange > Tile Horizontally)

### Workflow 2: Different Directory Scopes

1. Create primary window for /home/projects
2. Create secondary window (Ctrl+N)
3. Set second window to /etc
4. Keep both open for quick switching

### Workflow 3: Save Common Layouts

1. Arrange windows as needed
2. Window > Arrange > Save Layout
3. Layout restored on next app launch

## Next Steps

- Read full guide: `MULTI_WINDOW_GUIDE.md`
- Explore tab manager: `ui/tab_manager.py`
- Customize layouts: `core/window_state.py`
- Add shortcuts: `ui/window_menu.py`

## Support

For issues or questions:
1. Check test suite: `python test_multi_window.py`
2. Review logs in `logs/` directory
3. Check window state: `data/window_state.json`

---

**That's it! You now have full multi-window support in Smart Search Pro.**

Keyboard shortcuts are your friend:
- Ctrl+N: New window
- Ctrl+Shift+N: Duplicate
- Ctrl+W: Close
- Ctrl+1-9: Switch windows
