# iPhone View - Quick Start Guide

## 5-Minute Quick Start

### 1. Run the Test Application

```bash
cd C:\Users\ramos\.local\bin\smart_search
python test_iphone_view.py
```

This opens a test window with three tabs:
- **Full View**: Complete iPhone-style file browser
- **Widget Gallery**: All iOS-style widgets
- **Browser Test**: Category browser with sample data

### 2. Run the Integration Example

```bash
python examples\iphone_view_integration.py
```

Features:
- Browse Files tab with full iPhone view
- Control Panel for testing features
- Theme switching
- Statistics display
- Recent files viewer

### 3. Basic Integration

Add iPhone view to your application in 3 simple steps:

```python
from PyQt6.QtWidgets import QApplication, QMainWindow
from views.iphone_view import iPhoneFileView
import sys
import os

# 1. Create application
app = QApplication(sys.argv)

# 2. Create main window with iPhone view
window = QMainWindow()
iphone_view = iPhoneFileView()
window.setCentralWidget(iphone_view)

# 3. Set path and show
docs = os.path.join(os.environ['USERPROFILE'], 'Documents')
iphone_view.set_path(docs)
window.show()

sys.exit(app.exec())
```

## Key Features to Try

### Browse by Category

1. Open the application
2. Click any category card (Photos, Videos, Documents, etc.)
3. Files in that category open in the browser
4. Switch between List and Grid views
5. Search within the category
6. Sort by Name, Date, Size, or Type

### View Recent Files

Recent files appear at the bottom of the main view, showing:
- File name
- Last modified date
- Quick access to frequently used files

### Search Within Categories

1. Open a category browser
2. Type in the search box at the top
3. Results filter in real-time
4. Clear search to see all files again

### Switch Views

- **List View**: Traditional table with columns
- **Grid View**: Visual cards with icons
- Toggle with buttons in the toolbar

### Context Menu Actions

Right-click any file in list view:
- **Open**: Open with default application
- **Open File Location**: Show in Windows Explorer
- **Copy Path**: Copy file path to clipboard
- **Properties**: Show file properties

## File Categories

Files are automatically categorized by type:

| Category | Icon | File Types |
|----------|------|------------|
| Photos | 🖼 | jpg, png, gif, webp, heic, raw, cr2, nef |
| Videos | 🎬 | mp4, mov, avi, mkv, wmv, webm |
| Music | 🎵 | mp3, flac, wav, aac, m4a, ogg |
| Documents | 📄 | pdf, doc, docx, xls, xlsx, ppt, txt |
| Code | 💻 | py, js, ts, html, css, json, xml |
| Archives | 📦 | zip, rar, 7z, tar, gz |
| Applications | ⚙ | exe, msi, appx, dll |
| Data | 💾 | db, sqlite, json |
| Other | 📁 | Everything else |

## Common Tasks

### Browse a Different Folder

```python
# From code
iphone_view.set_path('/path/to/folder')

# From UI
# Use the Location dropdown or browse button
```

### Get Category Statistics

```python
stats = iphone_view.get_statistics()

print(f"Total files: {stats['total_files']}")
print(f"Total size: {stats['formatted_size']}")

for category, data in stats['categories'].items():
    print(f"{category}: {data['count']} files")
```

### Search for Files

```python
from categories import FileCategory

# Search in Photos category
results = iphone_view.search_in_category(
    FileCategory.IMAGENES,
    "vacation"
)

for file_info in results:
    print(file_info['name'])
```

### Get Recent Files

```python
recent = iphone_view.get_recent_files(limit=10)

for file_info in recent:
    print(f"{file_info['name']} - {file_info['modified']}")
```

### Handle Events

```python
# Connect to signals
iphone_view.category_selected.connect(on_category_clicked)
iphone_view.file_opened.connect(on_file_opened)
iphone_view.path_changed.connect(on_path_changed)

def on_category_clicked(category):
    print(f"Category: {category.value}")

def on_file_opened(path):
    print(f"Opened: {path}")

def on_path_changed(path):
    print(f"Now browsing: {path}")
```

## Customization

### Change Theme

```python
from ui.themes import get_theme_manager, Theme

theme_manager = get_theme_manager()

# Dark theme
theme_manager.set_theme(Theme.DARK)
app.setStyleSheet(theme_manager.get_stylesheet())

# Light theme
theme_manager.set_theme(Theme.LIGHT)
app.setStyleSheet(theme_manager.get_stylesheet())
```

### Adjust Scan Depth

```python
scanner = iphone_view.get_scanner()

# Shallow scan (faster)
categories = scanner.scan_directory(path, max_depth=1)

# Deep scan (slower, more complete)
categories = scanner.scan_directory(path, max_depth=-1)
```

### Clear Cache

```python
# Clear all cache
iphone_view.clear_cache()

# Or clear specific path cache
scanner = iphone_view.get_scanner()
scanner.clear_cache('/specific/path')
```

## Performance Tips

### For Large Directories

1. **Limit scan depth**: Use `max_depth=2` or `max_depth=3`
2. **Enable caching**: Scanner caches by default (5 min TTL)
3. **Use background scanning**: Automatic in the UI
4. **Exclude hidden files**: Default behavior

### For Better Responsiveness

1. **Use the main thread for UI**: All file operations are async
2. **Leverage caching**: Don't clear cache unnecessarily
3. **Scan incrementally**: Scan one level at a time for very large directories

### Memory Optimization

- Scanner stores only file metadata, not content
- Recent files limited to 50 per category
- Cache has automatic TTL (5 minutes)
- No thumbnails loaded (future feature)

## Troubleshooting

### Files Not Showing

1. Check path exists: `os.path.exists(path)`
2. Verify permissions: Try as administrator
3. Check file extensions are supported
4. Clear cache and rescan

### Slow Scanning

1. Reduce max_depth parameter
2. Exclude network drives
3. Use background scanner
4. Check for antivirus interference

### UI Not Updating

1. Ensure Qt event loop is running
2. Check signal connections
3. Verify background scanner callback
4. Look for exceptions in console

### Category Not Accurate

1. MIME type detection may differ
2. Update extension mappings in `categories.py`
3. Some files may be miscategorized
4. File without extension goes to "Other"

## Next Steps

1. **Read full documentation**: `IPHONE_VIEW_README.md`
2. **Explore widget customization**: `ui/iphone_widgets.py`
3. **Modify category mappings**: `categories.py`
4. **Add custom features**: Extend `iPhoneFileView` class
5. **Integrate with existing app**: See integration examples

## Support

For issues or questions:
1. Check `IPHONE_VIEW_README.md` for detailed documentation
2. Review code comments in source files
3. Run test applications to verify setup
4. Check existing Smart Search Pro documentation

## Quick Reference

### Main Components

```python
# Main view
from views.iphone_view import iPhoneFileView

# Scanner
from views.category_scanner import CategoryScanner

# Panel
from ui.iphone_view_panel import iPhoneViewPanel

# Browser
from ui.category_browser import CategoryBrowser

# Widgets
from ui.iphone_widgets import (
    CategoryCardWidget,
    CategoryIconWidget,
    iOSToggleSwitch,
    RoundedCardWidget
)
```

### File Locations

```
smart_search/
├── views/iphone_view.py              # Main component
├── views/category_scanner.py         # Scanner engine
├── ui/iphone_view_panel.py           # Main panel
├── ui/category_browser.py            # File browser
├── ui/iphone_widgets.py              # iOS widgets
├── test_iphone_view.py               # Tests
├── examples/iphone_view_integration.py # Example
├── IPHONE_VIEW_README.md             # Full docs
└── IPHONE_VIEW_QUICKSTART.md         # This file
```

Happy browsing! 📱
