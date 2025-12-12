# Smart Search Pro UI - Quick Reference Card

## Installation & Testing

```bash
# Test imports
python -c "from smart_search.ui import MainWindow; print('✓ OK')"

# Run demo
python -m smart_search.ui.demo

# Run standalone
python -m smart_search.ui
```

## Basic Usage

```python
from PyQt6.QtWidgets import QApplication
from smart_search.ui import MainWindow

app = QApplication([])
window = MainWindow()
window.show()
app.exec()
```

## Component Quick Access

### Main Components
```python
window.search_panel       # Search interface
window.results_panel      # Results table
window.preview_panel      # File preview
window.directory_tree     # Directory selector
window.duplicates_panel   # Duplicates manager
window.operations_panel   # Operations tracker
```

### Add Search Results
```python
window.results_panel.add_result({
    'name': 'file.txt',
    'path': '/full/path/to/file.txt',
    'size': 1024,  # bytes
    'modified': datetime.now(),
})
```

### Handle Search Request
```python
def on_search(params):
    query = params['query']
    paths = params['paths']
    filters = params.get('filters', {})
    # Your search logic here

window.search_started.connect(on_search)
```

### Track File Operations
```python
# Add operation
op_id = "copy_001"
window.operations_panel.add_operation(op_id, "Copying files", total_files=100)

# Update progress
window.operations_panel.update_operation(
    op_id,
    progress=50,
    current_file="file.txt",
    speed=5242880  # bytes/sec
)

# Complete
from smart_search.ui.operations_panel import OperationStatus
window.operations_panel.set_operation_status(op_id, OperationStatus.COMPLETED)
```

### Show Duplicates
```python
duplicates = [
    [  # Group 1
        {'name': 'file1.txt', 'path': '/path/1', 'size': 1024, 'modified': datetime.now()},
        {'name': 'file2.txt', 'path': '/path/2', 'size': 1024, 'modified': datetime.now()},
    ],
    # More groups...
]
window.duplicates_panel.set_duplicates(duplicates)
```

## Signals Reference

### Search Panel
```python
search_panel.search_requested.connect(callback)  # dict params
search_panel.filter_changed.connect(callback)    # dict filters
```

### Results Panel
```python
results_panel.file_selected.connect(callback)        # str path
results_panel.files_selected.connect(callback)       # list[str] paths
results_panel.open_requested.connect(callback)       # list[str] paths
results_panel.copy_requested.connect(callback)       # list[str] paths
results_panel.move_requested.connect(callback)       # list[str] paths
results_panel.delete_requested.connect(callback)     # list[str] paths
```

### Directory Tree
```python
directory_tree.selection_changed.connect(callback)   # list[str] paths
directory_tree.favorites_changed.connect(callback)   # list[str] paths
```

### Operations Panel
```python
operations_panel.cancel_requested.connect(callback)  # str op_id
operations_panel.pause_requested.connect(callback)   # str op_id
operations_panel.resume_requested.connect(callback)  # str op_id
```

## Theme Management

```python
from smart_search.ui.themes import get_theme_manager, Theme

theme_mgr = get_theme_manager()

# Switch theme
theme_mgr.set_theme(Theme.DARK)
window.setStyleSheet(theme_mgr.get_stylesheet())
app.setPalette(theme_mgr.get_palette())
```

## Custom Widgets

```python
from smart_search.ui.widgets import (
    FilterChip, SpeedGraph, BreadcrumbBar,
    ProgressCard, FileIcon, EmptyStateWidget
)

# Filter chip
chip = FilterChip("Type: PDF", removable=True)
chip.clicked.connect(lambda: print("Clicked"))
chip.removed.connect(lambda: print("Removed"))

# Speed graph
graph = SpeedGraph(max_points=50)
graph.add_data_point(5242880)  # Add speed in bytes/sec

# Progress card
card = ProgressCard("Operation Name")
card.set_progress(50)
card.set_status("Running")
card.set_speed("5.2 MB/s")
card.cancel_clicked.connect(lambda: print("Cancel"))
```

## Settings Access

```python
from PyQt6.QtCore import QSettings

settings = QSettings("SmartSearch", "MainWindow")

# Read
max_results = settings.value("search/max_results", 10000, type=int)
theme = settings.value("appearance/theme", "Light", type=str)

# Write
settings.setValue("search/max_results", 20000)
```

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Focus Search | Ctrl+F |
| New Tab | Ctrl+T |
| Open File | Ctrl+O |
| Copy Files | Ctrl+Shift+C |
| Move Files | Ctrl+M |
| Delete | Delete |
| Select All | Ctrl+A |
| Clear Results | Ctrl+L |
| Settings | Ctrl+, |
| Help | F1 |

## Common Tasks

### Populate Results from Search
```python
from datetime import datetime

def search_and_populate(query, paths):
    window.results_panel.clear_results()

    # Your search logic
    results = your_search_function(query, paths)

    for result in results:
        window.results_panel.add_result({
            'name': result.filename,
            'path': result.full_path,
            'size': result.file_size,
            'modified': datetime.fromtimestamp(result.mtime),
        })
```

### Handle File Copy with Progress
```python
from PyQt6.QtCore import QThread, pyqtSignal

class CopyWorker(QThread):
    progress = pyqtSignal(int, str, float)

    def __init__(self, files, dest):
        super().__init__()
        self.files = files
        self.dest = dest

    def run(self):
        for i, file in enumerate(self.files):
            # Copy logic
            progress_pct = int((i + 1) / len(self.files) * 100)
            self.progress.emit(progress_pct, file, speed)

# Usage
def copy_files(files):
    op_id = f"copy_{len(files)}"
    window.operations_panel.add_operation(op_id, "Copying", len(files))

    worker = CopyWorker(files, destination)
    worker.progress.connect(
        lambda p, f, s: window.operations_panel.update_operation(
            op_id, progress=p, current_file=f, speed=s
        )
    )
    worker.start()

window.results_panel.copy_requested.connect(copy_files)
```

### Update Preview on Selection
```python
def on_file_selected(file_path):
    window.preview_panel.set_file(file_path)

window.results_panel.file_selected.connect(on_file_selected)
```

## File Locations

```
C:\Users\ramos\.local\bin\smart_search\ui\
├── Core Components
│   ├── main_window.py         (Main window)
│   ├── search_panel.py        (Search UI)
│   ├── results_panel.py       (Results table)
│   ├── preview_panel.py       (Preview)
│   ├── directory_tree.py      (Directory tree)
│   ├── duplicates_panel.py    (Duplicates)
│   ├── operations_panel.py    (Operations)
│   └── settings_dialog.py     (Settings)
├── Support
│   ├── themes.py              (Themes)
│   ├── widgets.py             (Custom widgets)
│   ├── __init__.py            (Exports)
│   └── __main__.py            (Entry point)
├── Demo & Docs
│   ├── demo.py                (Interactive demo)
│   ├── README.md              (Full docs)
│   ├── INTEGRATION.md         (Integration guide)
│   ├── SUMMARY.md             (Overview)
│   ├── STRUCTURE.txt          (Visual structure)
│   └── QUICKREF.md            (This file)
```

## Tips & Tricks

### Performance
- Batch result additions for large datasets
- Disable sorting when adding many items: `table.setSortingEnabled(False)`
- Use QTimer.singleShot(0, ...) for deferred UI updates

### Error Handling
```python
try:
    # UI operation
    window.results_panel.add_result(file_info)
except Exception as e:
    from PyQt6.QtWidgets import QMessageBox
    QMessageBox.critical(window, "Error", str(e))
```

### Thread Safety
Always use signals to update UI from worker threads:
```python
# WRONG (crashes)
class Worker(QThread):
    def run(self):
        window.status_label.setText("Working")  # NOT thread-safe!

# RIGHT (safe)
class Worker(QThread):
    status_update = pyqtSignal(str)

    def run(self):
        self.status_update.emit("Working")

worker.status_update.connect(window.status_label.setText)
```

## Troubleshooting

### Import Errors
```bash
# Verify PyQt6 installed
pip install PyQt6

# Check Python path
python -c "import sys; print(sys.path)"
```

### High DPI Issues
```python
# Before QApplication creation
from PyQt6.QtCore import Qt
QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
```

### Theme Not Applied
```python
# Ensure theme applied AFTER widgets created
window = MainWindow()  # Creates widgets
window._apply_theme()   # Then apply theme
```

## Next Steps

1. Read **README.md** for detailed component APIs
2. Check **INTEGRATION.md** for backend integration patterns
3. Run **demo.py** to see all features in action
4. Review **STRUCTURE.txt** for visual layout
5. Examine source code (well-documented)

## Support Resources

| Resource | Purpose |
|----------|---------|
| README.md | Component APIs and features |
| INTEGRATION.md | Backend integration examples |
| SUMMARY.md | Implementation overview |
| STRUCTURE.txt | Visual UI structure |
| demo.py | Working examples |
| Source code | Comprehensive docstrings |

---

**Version**: 1.0.0
**Status**: Production Ready
**Created**: December 12, 2024
