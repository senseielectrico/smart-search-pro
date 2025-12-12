# Multi-Window Support Guide

## Overview

Smart Search Pro now supports multiple independent search windows with full feature parity, shared resources, and persistent layouts.

## Features

### Window Manager (`ui/window_manager.py`)

**Core Capabilities:**
- Track all open windows
- Create new search windows (Ctrl+N)
- Duplicate existing windows (Ctrl+Shift+N)
- Share data between windows (settings, favorites, history)
- Independent search states per window
- Window positioning and sizing
- Save/restore window layouts
- Close all windows (Ctrl+Shift+W)
- Focus management

**Shared Resources:**
- Search engine (single instance for all windows)
- Database connections (connection pool)
- Cache (shared LRU cache)
- Settings (synchronized across windows)

**Usage:**
```python
from ui.window_manager import get_window_manager

# Get global window manager
manager = get_window_manager()

# Create new window
window = manager.create_window()

# Duplicate window
duplicate = manager.create_duplicate_window(window.window_id)

# Arrange windows
manager.arrange_cascade()
manager.arrange_tile_horizontal()
manager.arrange_tile_vertical()

# Save/restore layout
manager.save_layout()
manager.restore_layout()
```

### Secondary Window (`ui/secondary_window.py`)

**Features:**
- Full search functionality
- Independent search query and results
- Different directory scope from primary
- Shared favorites and history
- Window title shows search context
- Mini mode (compact view)

**Usage:**
```python
from ui.secondary_window import create_secondary_window

# Create secondary window
window = create_secondary_window(
    window_id="custom_id",
    mini_mode=False,
    search_query="*.py",
    directory_path="/home/projects"
)

# Toggle mini mode
window.toggle_mini_mode(True)

# Set custom context
window.set_search_context("Python Files in Projects")
```

**Mini Mode:**
- Hides directory tree and preview panel
- Reduced window size (800x500)
- Perfect for quick searches
- Toggle with View > Mini Mode

### Window Menu (`ui/window_menu.py`)

**Menu Structure:**
```
Window
├── New Window (Ctrl+N)
├── Duplicate Window (Ctrl+Shift+N)
├── ─────────────────
├── Close Window (Ctrl+W)
├── Close All Windows (Ctrl+Shift+W)
├── ─────────────────
├── Arrange ►
│   ├── Cascade
│   ├── Tile Horizontally
│   ├── Tile Vertically
│   ├── ─────────────────
│   ├── Save Layout
│   └── Restore Layout
├── ─────────────────
├── 1. Search: *.py (Ctrl+1)
├── 2. Search: *.txt (Ctrl+2)
└── 3. Smart Search (Ctrl+3)
```

**Features:**
- Dynamic window list (updates automatically)
- First 9 windows get number shortcuts (Ctrl+1-9)
- Active window shown with checkmark
- Save/restore layouts

### Tab Manager (`ui/tab_manager.py`)

**Tab-Based Alternative:**
- Multiple search tabs in single window
- Detach tab to new window (drag out)
- Merge windows into tabs
- Tab context menu
- Close tab button
- New tab button
- Drag tabs to reorder

**Usage:**
```python
from ui.tab_manager import SearchTabWidget, TabManager

# Create tab widget
tab_widget = SearchTabWidget()
tab_manager = TabManager(tab_widget)

# Create new tab
index = tab_manager.create_tab(title="Search 1")

# Close tab
tab_manager.close_tab(index)

# Detach tab to window
widget = tab_manager.detach_tab(index, position)
```

**Tab Context Menu:**
- Close Tab
- Close Other Tabs
- Close Tabs to Right
- Detach to New Window
- New Tab

### Window State Persistence (`core/window_state.py`)

**Saved State:**
- Window positions (x, y)
- Window sizes (width, height)
- Maximized/minimized state
- Search query
- Directory paths
- Filter settings
- Sort options
- Selected tab
- Active window
- Window layout mode

**Storage:**
- Location: `data/window_state.json`
- Format: JSON
- Auto-save on window close
- Auto-restore on app start

**Usage:**
```python
from core.window_state import get_window_state_manager

# Get state manager
manager = get_window_state_manager()

# Save state
manager.save_state()

# Get window state
state = manager.get_window_state(window_id)

# Set layout mode
manager.set_layout('cascade')  # or 'tile_horizontal', 'tile_vertical'
```

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| New Window | Ctrl+N |
| Duplicate Window | Ctrl+Shift+N |
| Close Window | Ctrl+W |
| Close All Windows | Ctrl+Shift+W |
| Switch to Window 1-9 | Ctrl+1 to Ctrl+9 |
| Focus Search | Ctrl+F |
| New Tab | Ctrl+T |

## Window Arrangements

### Cascade
Windows arranged diagonally with offset:
```
┌─────┐
│  1  │
└─────┘
  ┌─────┐
  │  2  │
  └─────┘
    ┌─────┐
    │  3  │
    └─────┘
```

### Tile Horizontal
Windows side by side:
```
┌─────┬─────┬─────┐
│  1  │  2  │  3  │
│     │     │     │
└─────┴─────┴─────┘
```

### Tile Vertical
Windows stacked:
```
┌─────────┐
│    1    │
├─────────┤
│    2    │
├─────────┤
│    3    │
└─────────┘
```

## Integration with Main Application

### Updating main_window.py

The main window must support multiple instances. Add window_id tracking:

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Add window tracking
        self.window_id = None
        self.is_primary = False
        self._created_at = time.time()

        # Rest of initialization...
```

### Updating app.py or main.py

Replace single window creation with window manager:

```python
from ui.window_manager import get_window_manager

def main():
    app = QApplication(sys.argv)

    # Get window manager
    manager = get_window_manager()

    # Set shared resources
    manager.set_shared_resources(
        search_engine=search_engine,
        database=database,
        cache=cache
    )

    # Restore previous layout or create primary window
    saved_windows = manager._state_manager.get_all_windows()
    if saved_windows:
        manager.restore_layout()
    else:
        manager.create_window(is_primary=True)

    sys.exit(app.exec())
```

### Adding Window Menu

Add to main window menu bar:

```python
from ui.window_menu import create_window_menu

class MainWindow(QMainWindow):
    def _create_menus(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        # ... file menu items ...

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        # ... edit menu items ...

        # View menu
        view_menu = menubar.addMenu("&View")
        # ... view menu items ...

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        # ... tools menu items ...

        # Window menu (new!)
        from ui.window_manager import get_window_manager
        manager = get_window_manager()
        window_menu_manager = create_window_menu(manager)
        menubar.addMenu(window_menu_manager.get_menu())

        # Help menu
        help_menu = menubar.addMenu("&Help")
        # ... help menu items ...
```

## Shared Resources

### Database Connections

The database uses connection pooling, so multiple windows can safely share:

```python
from core.database import DatabaseManager

# Single database instance
db = DatabaseManager("data/smart_search.db", pool_size=10)

# Share with all windows
manager.set_shared_resources(database=db)
```

### Cache

The LRU cache is thread-safe:

```python
from core.cache import LRUCache

# Single cache instance
cache = LRUCache(max_size=1000)

# Share with all windows
manager.set_shared_resources(cache=cache)
```

### Settings

Settings are automatically synchronized using QSettings:

```python
from PyQt6.QtCore import QSettings

# Each window uses same organization/application name
settings = QSettings("SmartSearch", "MainWindow")
```

## Best Practices

### 1. Resource Management
- Always use shared resources for database, cache
- Don't create duplicate search engine instances
- Use connection pooling for database access

### 2. Window Lifecycle
- Save state on window close
- Clean up resources properly
- Don't block main thread

### 3. User Experience
- Provide visual feedback for window operations
- Show active window clearly
- Sync settings across windows
- Preserve search state when duplicating

### 4. Performance
- Limit maximum number of windows (recommend 10)
- Use mini mode for quick searches
- Clean up closed windows promptly

### 5. State Persistence
- Save layout on app exit
- Restore on next launch
- Handle missing/corrupted state gracefully

## Troubleshooting

### Windows not appearing
- Check if window is minimized
- Verify window manager is initialized
- Check screen bounds

### Layout not restoring
- Verify `data/window_state.json` exists
- Check file permissions
- Validate JSON format

### Search engine conflicts
- Ensure single shared instance
- Check thread safety
- Verify connection pool size

### Memory issues
- Limit number of windows
- Clean up closed windows
- Monitor cache size

## Testing

Run the test suite:

```bash
python test_multi_window.py
```

This tests:
- Window state persistence
- Window manager operations
- Window arrangements
- Secondary windows
- Tab manager
- Window menu
- Integration

## API Reference

### WindowManager

```python
class WindowManager:
    def create_window(
        window_id: Optional[str] = None,
        geometry: Optional[WindowGeometry] = None,
        search_state: Optional[SearchState] = None,
        is_primary: bool = False
    ) -> MainWindow

    def create_duplicate_window(source_window_id: str) -> Optional[MainWindow]
    def close_window(window_id: str) -> bool
    def close_all_windows() -> None
    def get_window(window_id: str) -> Optional[MainWindow]
    def get_all_windows() -> List[MainWindow]
    def get_window_count() -> int
    def get_active_window() -> Optional[MainWindow]
    def set_active_window(window_id: str) -> None
    def arrange_cascade() -> None
    def arrange_tile_horizontal() -> None
    def arrange_tile_vertical() -> None
    def save_layout() -> None
    def restore_layout() -> None
```

### WindowStateManager

```python
class WindowStateManager:
    def save_state() -> None
    def add_window(window_state: WindowState) -> None
    def remove_window(window_id: str) -> None
    def get_window_state(window_id: str) -> Optional[WindowState]
    def get_all_windows() -> List[WindowState]
    def set_active_window(window_id: str) -> None
    def get_active_window_id() -> Optional[str]
    def set_layout(layout: str) -> None
    def get_layout() -> str
```

### SecondaryWindow

```python
class SecondaryWindow(MainWindow):
    def toggle_mini_mode(enabled: bool = None) -> None
    def get_mini_mode() -> bool
    def set_search_context(context: str) -> None
```

### TabManager

```python
class TabManager:
    def create_tab(title: str = "New Search", widget: Optional[QWidget] = None) -> int
    def close_tab(index: int) -> bool
    def detach_tab(index: int, position: QPoint) -> Optional[QWidget]
    def get_tab_count() -> int
    def get_current_index() -> int
    def set_current_index(index: int) -> None
```

## File Structure

```
smart_search/
├── core/
│   └── window_state.py          # Window state persistence
├── ui/
│   ├── window_manager.py        # Multi-window manager
│   ├── secondary_window.py      # Secondary search window
│   ├── window_menu.py           # Window menu management
│   └── tab_manager.py           # Tab-based interface
├── data/
│   └── window_state.json        # Saved window states
└── test_multi_window.py         # Test suite
```

## Examples

### Example 1: Create Multiple Search Windows

```python
from ui.window_manager import get_window_manager

manager = get_window_manager()

# Create windows for different searches
python_window = manager.create_window()
python_window.search_panel.search_input.setText("*.py")

docs_window = manager.create_window()
docs_window.search_panel.search_input.setText("*.md")

# Arrange side by side
manager.arrange_tile_horizontal()
```

### Example 2: Mini Mode Quick Search

```python
from ui.secondary_window import create_secondary_window

# Create compact search window
quick_search = create_secondary_window(
    mini_mode=True,
    search_query="config",
    directory_path="/etc"
)
```

### Example 3: Save Custom Layout

```python
from ui.window_manager import get_window_manager

manager = get_window_manager()

# Create custom layout
window1 = manager.create_window()
window1.setGeometry(0, 0, 800, 600)

window2 = manager.create_window()
window2.setGeometry(800, 0, 800, 600)

window3 = manager.create_window()
window3.setGeometry(400, 600, 800, 400)

# Save layout
manager.save_layout()
```

### Example 4: Restore Previous Session

```python
from ui.window_manager import get_window_manager

manager = get_window_manager()

# Restore all windows from last session
manager.restore_layout()

# Or create new if no saved layout
if manager.get_window_count() == 0:
    manager.create_window(is_primary=True)
```

## Future Enhancements

- [ ] Window groups/workspaces
- [ ] Session management (named layouts)
- [ ] Cross-monitor support
- [ ] Window thumbnails in menu
- [ ] Drag & drop between windows
- [ ] Synchronized scrolling
- [ ] Broadcast search to all windows
- [ ] Window templates
- [ ] Keyboard navigation between windows
- [ ] Quick switch panel (Alt+Tab style)

## License

Part of Smart Search Pro - All rights reserved.
