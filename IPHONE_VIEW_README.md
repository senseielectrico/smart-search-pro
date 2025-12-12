# iPhone View - iOS-Style File Browser

## Overview

The iPhone View is a modern, iOS-inspired file categorization and browsing system for Smart Search Pro. It provides an intuitive, visual way to organize and access files by automatically categorizing them into familiar groups.

## Features

### Core Features

- **Automatic File Categorization**: Files are automatically sorted into categories:
  - 📸 Photos (jpg, png, gif, webp, heic, raw)
  - 🎬 Videos (mp4, mov, avi, mkv, wmv)
  - 🎵 Music (mp3, flac, wav, aac, m4a)
  - 📄 Documents (pdf, doc, docx, xls, xlsx, ppt, txt)
  - 💻 Code (py, js, ts, html, css, json)
  - 📦 Archives (zip, rar, 7z, tar)
  - ⚙ Applications (exe, msi, appx)
  - 💾 Data (db, sqlite, json)
  - 📁 Other (uncategorized)

- **iOS-Inspired Design**:
  - Rounded card widgets with shadows
  - Smooth hover animations
  - Color-coded category icons
  - Clean, minimalist interface
  - Dark/Light theme support

- **Smart Detection**:
  - MIME type verification for accuracy
  - Extension-based categorization
  - Intelligent fallback system

- **Performance Optimized**:
  - Background scanning
  - Result caching (5-minute TTL)
  - Incremental updates
  - Thread-safe operations

### UI Features

- **Category Grid View**: Visual cards showing:
  - Category icon with gradient background
  - File count
  - Total size
  - Percentage of total files

- **Category Browser**:
  - List view (table)
  - Grid view (cards)
  - Search within category
  - Sort by: Name, Date, Size, Type
  - Context menu actions
  - Multi-select support

- **Recent Files Section**:
  - Shows last modified files
  - Quick access to frequently used files

- **Statistics Dashboard**:
  - Total file count
  - Total storage used
  - Active categories count

## Architecture

### File Structure

```
smart_search/
├── views/
│   ├── __init__.py
│   ├── iphone_view.py          # Main view component
│   └── category_scanner.py     # Categorization engine
│
└── ui/
    ├── iphone_view_panel.py    # Main panel with category grid
    ├── category_browser.py     # Category file browser
    └── iphone_widgets.py       # iOS-style custom widgets
```

### Components

#### 1. iPhoneFileView (views/iphone_view.py)

Main component providing the complete browsing experience.

```python
from views.iphone_view import iPhoneFileView

view = iPhoneFileView()
view.set_path('/path/to/scan')
view.show()

# Get statistics
stats = view.get_statistics()
print(f"Total files: {stats['total_files']}")

# Search in category
from categories import FileCategory
results = view.search_in_category(FileCategory.IMAGENES, "vacation")

# Get recent files
recent = view.get_recent_files(limit=10)
```

#### 2. CategoryScanner (views/category_scanner.py)

Engine for scanning and categorizing files.

```python
from views.category_scanner import CategoryScanner

scanner = CategoryScanner(cache_enabled=True)

# Scan directory
categories = scanner.scan_directory(
    path='/path/to/scan',
    max_depth=3,
    include_hidden=False
)

# Get breakdown
breakdown = scanner.get_category_breakdown(categories)

# Get recent files
recent = scanner.get_recent_files(categories, limit=20)

# Clear cache
scanner.clear_cache()
```

#### 3. iPhoneViewPanel (ui/iphone_view_panel.py)

Main panel with category cards grid.

```python
from ui.iphone_view_panel import iPhoneViewPanel

panel = iPhoneViewPanel()
panel.set_path('/path/to/scan')

# Connect signals
panel.category_selected.connect(on_category_selected)
panel.refresh_requested.connect(on_refresh)
```

#### 4. CategoryBrowser (ui/category_browser.py)

Browser for viewing files in a category.

```python
from ui.category_browser import CategoryBrowser
from categories import FileCategory

browser = CategoryBrowser(
    category=FileCategory.IMAGENES,
    category_data=category_data
)
browser.exec()
```

#### 5. iOS Widgets (ui/iphone_widgets.py)

Custom iOS-style widgets:

- **CategoryCardWidget**: Category card with icon and stats
- **CategoryIconWidget**: Colored category icon
- **RoundedCardWidget**: Base rounded card with shadow
- **iOSToggleSwitch**: iOS-style toggle switch
- **SmoothScrollArea**: Smooth kinetic scrolling
- **PullToRefreshWidget**: Pull-to-refresh gesture
- **BlurBackgroundWidget**: Translucent blur background

```python
from ui.iphone_widgets import (
    CategoryCardWidget,
    CategoryIconWidget,
    iOSToggleSwitch
)

# Category card
card = CategoryCardWidget("Photos", count=150, size="2.5 GB")
card.clicked.connect(on_card_clicked)

# Icon
icon = CategoryIconWidget("Videos", size=64)

# Toggle switch
toggle = iOSToggleSwitch()
toggle.setChecked(True)
toggle.toggled.connect(on_toggle_changed)
```

## Usage Examples

### Basic Usage

```python
from PyQt6.QtWidgets import QApplication
from views.iphone_view import iPhoneFileView
import sys

app = QApplication(sys.argv)

view = iPhoneFileView()
view.setWindowTitle("File Browser")
view.resize(1200, 800)

# Scan Documents folder
import os
docs_path = os.path.join(os.environ['USERPROFILE'], 'Documents')
view.set_path(docs_path)

view.show()
sys.exit(app.exec())
```

### Integration with Main Window

```python
from PyQt6.QtWidgets import QMainWindow, QTabWidget
from views.iphone_view import iPhoneFileView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create tabs
        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        # Add iPhone view tab
        self.iphone_view = iPhoneFileView()
        tabs.addTab(self.iphone_view, "Browse Files")

        # Connect signals
        self.iphone_view.category_selected.connect(
            self.on_category_selected
        )

    def on_category_selected(self, category):
        print(f"Selected: {category.value}")
```

### Custom Scanning

```python
from views.category_scanner import CategoryScanner, BackgroundScanner
from categories import FileCategory

scanner = CategoryScanner()

# Scan with custom options
categories = scanner.scan_directory(
    path='/path/to/scan',
    max_depth=5,              # Max recursion depth
    include_hidden=False,      # Skip hidden files
    follow_symlinks=False      # Don't follow symlinks
)

# Access specific category
images = categories[FileCategory.IMAGENES]
print(f"Found {images.file_count} images")
print(f"Total size: {images.formatted_size}")

# Iterate files
for file_info in images.files:
    print(f"{file_info['name']} - {file_info['size']} bytes")
```

### Background Scanning

```python
from views.category_scanner import BackgroundScanner

def on_scan_complete(categories):
    print("Scan complete!")
    for cat, data in categories.items():
        print(f"{cat.value}: {data.file_count} files")

# Start background scan
bg_scanner = BackgroundScanner(
    scanner=scanner,
    path='/path/to/scan',
    callback=on_scan_complete
)
bg_scanner.start()

# Stop if needed
bg_scanner.stop()
```

## Customization

### Theme Integration

The iPhone View automatically adapts to the application theme:

```python
from ui.themes import get_theme_manager, Theme

theme_manager = get_theme_manager()

# Switch to dark theme
theme_manager.set_theme(Theme.DARK)
app.setStyleSheet(theme_manager.get_stylesheet())

# Switch to light theme
theme_manager.set_theme(Theme.LIGHT)
app.setStyleSheet(theme_manager.get_stylesheet())
```

### Custom Category Colors

Modify colors in `ui/iphone_widgets.py`:

```python
class CategoryIconWidget(QLabel):
    CATEGORY_COLORS = {
        'Photos': QColor(0, 122, 255),     # Custom blue
        'Videos': QColor(255, 149, 0),      # Custom orange
        # ... add more
    }
```

### Custom Icons

Modify icons in `ui/iphone_widgets.py`:

```python
class CategoryIconWidget(QLabel):
    CATEGORY_ICONS = {
        'Photos': '📸',
        'Videos': '🎥',
        # ... use emoji or unicode
    }
```

## Performance Considerations

### Caching

- Scanner caches results for 5 minutes (configurable)
- Cache is thread-safe
- Per-directory caching

```python
# Configure cache
scanner = CategoryScanner(cache_enabled=True)

# Clear cache manually
scanner.clear_cache()           # Clear all
scanner.clear_cache('/path')    # Clear specific path
```

### Scanning Performance

- Background scanning prevents UI blocking
- Incremental updates for large directories
- Smart depth limiting

```python
# Fast scan (shallow)
categories = scanner.scan_directory(path, max_depth=1)

# Deep scan
categories = scanner.scan_directory(path, max_depth=-1)  # Unlimited
```

### Memory Usage

- Files are stored as lightweight dictionaries
- Recent files limited to 50 per category
- No file content is loaded into memory

## Accessibility

- Keyboard navigation support
- Screen reader compatible labels
- High contrast mode support
- Focus indicators on all interactive elements

## Testing

Run the test suite:

```bash
python test_iphone_view.py
```

Test features:
- Full iPhone View
- Widget Gallery
- Category Browser with sample data

## API Reference

### iPhoneFileView

**Methods:**
- `set_path(path: str)` - Set directory to browse
- `get_current_path() -> str` - Get current path
- `get_category_data(category) -> CategoryData` - Get category data
- `refresh()` - Refresh current view
- `clear_cache()` - Clear scanner cache
- `get_statistics() -> Dict` - Get file statistics
- `search_in_category(category, query) -> List` - Search in category
- `get_recent_files(limit) -> List` - Get recent files

**Signals:**
- `category_selected(FileCategory)` - Category card clicked
- `file_opened(str)` - File opened
- `path_changed(str)` - Browsing path changed

### CategoryScanner

**Methods:**
- `scan_directory(path, max_depth, include_hidden, follow_symlinks)` - Scan directory
- `get_recent_files(categories, limit)` - Get recent files
- `get_category_breakdown(categories)` - Get statistics
- `search_in_category(category, categories, query)` - Search files
- `clear_cache(path)` - Clear cache

### CategoryData

**Properties:**
- `category: FileCategory` - Category enum
- `file_count: int` - Number of files
- `total_size: int` - Total size in bytes
- `files: List[Dict]` - File info list
- `recent_files: List[Dict]` - Recent files (max 50)
- `formatted_size: str` - Human-readable size
- `average_size: int` - Average file size

**Methods:**
- `add_file(file_info: Dict)` - Add file to category

## Troubleshooting

### Slow Scanning

- Reduce max_depth
- Enable caching
- Exclude network drives
- Use background scanner

### Files Not Categorized

- Check MIME type detection
- Verify file extensions
- Check scanner logs
- Update extension mappings in `categories.py`

### UI Not Updating

- Check Qt event loop
- Verify signal connections
- Use background scanner for long operations
- Check for exceptions in callbacks

## Future Enhancements

- [ ] Thumbnail previews for images/videos
- [ ] Smart folders (auto-categorization)
- [ ] File tagging system
- [ ] Cloud storage integration
- [ ] Advanced filtering options
- [ ] Export to various formats
- [ ] Duplicate file detection
- [ ] Storage analysis charts

## License

Part of Smart Search Pro - See main LICENSE file

## Credits

Inspired by iOS Files app design and UX patterns.
