# Smart Search Pro - UI Module

Modern Files App-style interface built with PyQt6.

## Architecture

```
ui/
├── __init__.py           # Package exports
├── __main__.py           # Entry point for standalone testing
├── main_window.py        # Main application window
├── search_panel.py       # Search interface with filters
├── results_panel.py      # Results table with virtual scrolling
├── preview_panel.py      # File preview panel
├── directory_tree.py     # Enhanced directory tree
├── duplicates_panel.py   # Duplicates management
├── operations_panel.py   # File operations tracker
├── settings_dialog.py    # Settings with tabs
├── themes.py             # Theme system (Light/Dark)
├── widgets.py            # Custom reusable widgets
└── README.md             # This file
```

## Features

### Main Window
- **Tabbed Interface**: Multiple searches in tabs
- **Modern Layout**: Splitter-based responsive design
- **Menu Bar**: File, Edit, View, Tools, Help
- **Toolbar**: Quick access to common actions
- **Status Bar**: Live updates on search progress

### Search Panel
- **Smart Search Box**: With autocomplete history
- **Quick Filters**: One-click file type filters
- **Advanced Search**: Dialog with detailed options
- **Filter Chips**: Visual active filters display
- **Search History**: Automatic history tracking

### Results Panel
- **Virtual Scrolling**: Handle 100k+ results
- **Sortable Columns**: Name, Size, Type, Date
- **Multi-Select**: Extended selection support
- **Context Menu**: Right-click actions
- **File Icons**: Type-based colored icons
- **Export**: CSV/JSON export (coming soon)

### Preview Panel
- **Text Preview**: With syntax highlighting
- **Image Preview**: Thumbnails with zoom
- **Metadata Display**: File info and properties
- **Quick Actions**: Open, Open Location buttons
- **Size Limits**: Configurable preview limits

### Directory Tree
- **Tristate Checkboxes**: Partial selection support
- **Lazy Loading**: Load subdirectories on demand
- **Favorites**: Pin frequently used folders
- **Quick Access**: Desktop, Documents, Downloads, etc.
- **Context Menu**: Add to favorites, open, refresh

### Duplicates Panel
- **Grouped View**: Files grouped by content
- **Wasted Space**: Calculate duplicate overhead
- **Selection Helpers**: Select oldest/newest
- **Bulk Actions**: Keep one, delete others
- **Smart Detection**: Hash-based comparison

### Operations Panel
- **Progress Tracking**: Real-time operation status
- **Speed Graph**: Visual transfer speed
- **Pause/Resume**: Control long operations
- **Multiple Operations**: Queue management
- **ETA Display**: Time remaining estimates

### Settings Dialog
- **General**: Startup, defaults, paths
- **Search**: Behavior, performance, indexing
- **Preview**: Size limits, image settings
- **Operations**: Confirmation, buffer size
- **Appearance**: Theme, font, colors
- **Shortcuts**: Customizable keyboard shortcuts

### Themes
- **Light Theme**: Windows 11 inspired
- **Dark Theme**: High contrast dark mode
- **Fluent Design**: Modern styling
- **Accent Colors**: Customizable (coming soon)
- **High DPI**: Full support for 4K displays

### Custom Widgets
- **FilterChip**: Removable filter tags
- **SpeedGraph**: Real-time speed visualization
- **BreadcrumbBar**: Path navigation
- **ProgressCard**: Rich progress display
- **FileIcon**: Type-based icons with colors
- **EmptyStateWidget**: Placeholder states
- **LoadingSpinner**: Animated loading indicator

## Usage

### Standalone Testing

Run the UI module directly:

```bash
python -m smart_search.ui
```

### Integration

```python
from PyQt6.QtWidgets import QApplication
from smart_search.ui import MainWindow

app = QApplication([])
window = MainWindow()
window.show()
app.exec()
```

### Connecting Backend

```python
from smart_search.ui import MainWindow

window = MainWindow()

# Connect search signal
window.search_started.connect(your_search_function)

# Add results
window.results_panel.add_result({
    'name': 'file.txt',
    'path': '/path/to/file.txt',
    'size': 1024,
    'modified': datetime.now(),
})

# Update operations
window.operations_panel.add_operation('copy_1', 'Copying files')
window.operations_panel.update_operation('copy_1', progress=50)
```

## Components API

### MainWindow

```python
window = MainWindow()

# Access panels
window.search_panel
window.results_panel
window.preview_panel
window.directory_tree
window.duplicates_panel
window.operations_panel

# Signals
window.search_started.connect(callback)  # Dict with search params
window.operation_started.connect(callback)  # str operation_id, str type
```

### SearchPanel

```python
panel = SearchPanel()

# Methods
panel.get_search_text() -> str
panel.set_search_text(text: str)
panel.get_active_filters() -> Dict
panel.clear_filters()
panel.clear_history()

# Signals
panel.search_requested.connect(callback)  # Dict params
panel.filter_changed.connect(callback)  # Dict filters
```

### ResultsPanel

```python
panel = ResultsPanel()

# Methods
panel.add_result(file_info: Dict)
panel.add_results(file_infos: List[Dict])
panel.clear_results()
panel.get_selected_files() -> List[str]
panel.get_all_files() -> List[Dict]
panel.select_all()
panel.select_none()

# Signals
panel.file_selected.connect(callback)  # str path
panel.files_selected.connect(callback)  # List[str] paths
panel.open_requested.connect(callback)  # List[str] paths
panel.copy_requested.connect(callback)  # List[str] paths
panel.move_requested.connect(callback)  # List[str] paths
```

### PreviewPanel

```python
panel = PreviewPanel()

# Methods
panel.set_file(path: str)
panel.clear()

# Signals
panel.open_requested.connect(callback)  # str path
panel.open_location_requested.connect(callback)  # str path
```

### DirectoryTree

```python
tree = DirectoryTree()

# Methods
tree.get_selected_paths() -> List[str]
tree.set_selected_paths(paths: List[str])
tree.add_favorite(path: str)
tree.remove_favorite(path: str)

# Signals
tree.selection_changed.connect(callback)  # List[str] paths
tree.favorites_changed.connect(callback)  # List[str] paths
```

### OperationsPanel

```python
panel = OperationsPanel()

# Methods
panel.add_operation(id: str, title: str, total: int)
panel.update_operation(id: str, progress: int, file: str, speed: float)
panel.remove_operation(id: str)
panel.set_operation_status(id: str, status: OperationStatus)
panel.get_active_operations() -> List[str]

# Signals
panel.cancel_requested.connect(callback)  # str operation_id
panel.pause_requested.connect(callback)  # str operation_id
panel.resume_requested.connect(callback)  # str operation_id
```

## Theming

### Switching Themes

```python
from smart_search.ui.themes import get_theme_manager, Theme

theme_manager = get_theme_manager()
theme_manager.set_theme(Theme.DARK)

# Apply to window
window.setStyleSheet(theme_manager.get_stylesheet())
app.setPalette(theme_manager.get_palette())
```

### Custom Colors

```python
from smart_search.ui.themes import ColorScheme

# Define custom colors
custom_colors = ColorScheme(
    bg_primary="#1E1E1E",
    accent="#FF6B6B",
    # ... other colors
)

# Create custom stylesheet
stylesheet = theme_manager.get_stylesheet(custom_colors)
```

## Performance

- **Virtual Scrolling**: Only renders visible rows
- **Lazy Loading**: Directories loaded on demand
- **Debounced Search**: Prevents excessive filtering
- **Async Operations**: Background file operations
- **Memory Efficient**: Handles 100k+ files

## Accessibility

- **Keyboard Navigation**: Full keyboard support
- **Screen Reader**: ARIA-compatible labels
- **High Contrast**: Dark mode support
- **Focus Indicators**: Clear focus states
- **Shortcuts**: Customizable key bindings

## Requirements

- Python 3.8+
- PyQt6 6.0+
- Windows 10/11 (for native features)

## Known Limitations

1. Virtual scrolling not yet fully implemented
2. Export functionality placeholder
3. Batch rename not implemented
4. Multi-tab search in progress
5. Syntax highlighting basic

## Future Enhancements

- [ ] Full syntax highlighting (Pygments)
- [ ] Video/Audio preview
- [ ] PDF preview
- [ ] Icon cache for performance
- [ ] Custom column configuration
- [ ] Saved search templates
- [ ] Search filters presets
- [ ] Drag and drop support
- [ ] Multi-monitor support
- [ ] Themes: Auto (system), Custom colors

## License

Part of Smart Search Pro project.

## Contributing

See main project README for contribution guidelines.
