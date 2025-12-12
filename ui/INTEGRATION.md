# UI Integration Guide

How to integrate the UI module with Smart Search Pro backend.

## Quick Start

### 1. Basic Setup

```python
from PyQt6.QtWidgets import QApplication
from smart_search.ui import MainWindow
from smart_search.search import SearchEngine  # Your backend

app = QApplication([])
window = MainWindow()

# Create backend
search_engine = SearchEngine()

# Connect signals
window.search_started.connect(search_engine.search)
```

### 2. Handle Search Results

```python
def on_search_started(params: dict):
    """Handle search request from UI"""
    query = params.get('query', '')
    paths = params.get('paths', [])
    filters = params.get('filters', {})

    # Clear previous results
    window.results_panel.clear_results()

    # Perform search
    results = search_engine.search(query, paths, filters)

    # Add results to UI
    for result in results:
        window.results_panel.add_result({
            'name': result.name,
            'path': result.path,
            'size': result.size,
            'modified': result.modified_time,
        })

window.search_started.connect(on_search_started)
```

## Backend Integration Patterns

### Pattern 1: Direct Backend Connection

```python
class SearchController:
    """Controller connecting UI and backend"""

    def __init__(self, window: MainWindow, backend):
        self.window = window
        self.backend = backend
        self._connect_signals()

    def _connect_signals(self):
        # Search
        self.window.search_started.connect(self.handle_search)

        # File operations
        self.window.results_panel.copy_requested.connect(self.handle_copy)
        self.window.results_panel.move_requested.connect(self.handle_move)
        self.window.results_panel.delete_requested.connect(self.handle_delete)

    def handle_search(self, params: dict):
        # Start background search
        worker = SearchWorker(self.backend, params)
        worker.result_ready.connect(self.window.results_panel.add_result)
        worker.finished.connect(self.on_search_finished)
        worker.start()

    def handle_copy(self, files: list):
        # Get destination
        from PyQt6.QtWidgets import QFileDialog
        dest = QFileDialog.getExistingDirectory(self.window, "Destination")

        if dest:
            # Start copy operation
            op_id = f"copy_{len(files)}"
            self.window.operations_panel.add_operation(op_id, "Copying files", len(files))

            copier = FileCopier(files, dest)
            copier.progress.connect(
                lambda p: self.window.operations_panel.update_operation(op_id, progress=p)
            )
            copier.start()
```

### Pattern 2: Signal Proxy

```python
from PyQt6.QtCore import QObject, pyqtSignal

class UIBridge(QObject):
    """Bridge between UI and backend with type-safe signals"""

    # Outgoing (UI -> Backend)
    search_requested = pyqtSignal(str, list, dict)  # query, paths, filters
    copy_requested = pyqtSignal(list, str)  # files, destination
    move_requested = pyqtSignal(list, str)  # files, destination

    # Incoming (Backend -> UI)
    result_found = pyqtSignal(dict)  # file_info
    search_completed = pyqtSignal(int)  # total_count
    operation_progress = pyqtSignal(str, int, str)  # op_id, progress, status

    def __init__(self, window: MainWindow):
        super().__init__()
        self.window = window
        self._connect()

    def _connect(self):
        # UI -> Bridge
        self.window.search_started.connect(self._on_search_started)
        self.window.results_panel.copy_requested.connect(self._on_copy_requested)

        # Bridge -> UI
        self.result_found.connect(self.window.results_panel.add_result)
        self.operation_progress.connect(self._update_operation)

    def _on_search_started(self, params: dict):
        self.search_requested.emit(
            params.get('query', ''),
            params.get('paths', []),
            params.get('filters', {})
        )

    def _on_copy_requested(self, files: list):
        # Show dialog and emit
        pass

    def _update_operation(self, op_id: str, progress: int, status: str):
        self.window.operations_panel.update_operation(op_id, progress=progress)
```

### Pattern 3: Async with QThread

```python
from PyQt6.QtCore import QThread, pyqtSignal

class SearchThread(QThread):
    """Background search thread"""
    result_ready = pyqtSignal(dict)
    progress = pyqtSignal(int, str)
    finished_signal = pyqtSignal(int)

    def __init__(self, backend, query, paths):
        super().__init__()
        self.backend = backend
        self.query = query
        self.paths = paths

    def run(self):
        results = self.backend.search(self.query, self.paths)

        for i, result in enumerate(results):
            # Emit result
            self.result_ready.emit({
                'name': result.name,
                'path': result.path,
                'size': result.size,
                'modified': result.modified,
            })

            # Emit progress
            if i % 100 == 0:
                self.progress.emit(i, result.path)

        self.finished_signal.emit(len(results))

# Usage
thread = SearchThread(backend, query, paths)
thread.result_ready.connect(window.results_panel.add_result)
thread.progress.connect(lambda i, p: window.status_label.setText(f"Found {i} files..."))
thread.start()
```

## File Operations Integration

### Copy Operation

```python
from PyQt6.QtCore import QThread, pyqtSignal
import shutil

class CopyWorker(QThread):
    progress = pyqtSignal(int, str, float)  # progress, file, speed
    finished_signal = pyqtSignal(int, int)  # success, errors
    error = pyqtSignal(str)

    def __init__(self, files: list, destination: str):
        super().__init__()
        self.files = files
        self.destination = destination
        self.success_count = 0
        self.error_count = 0

    def run(self):
        import time
        total = len(self.files)

        for i, src_path in enumerate(self.files):
            try:
                start_time = time.time()

                # Copy file
                dest_path = os.path.join(self.destination, os.path.basename(src_path))
                shutil.copy2(src_path, dest_path)

                # Calculate speed
                elapsed = time.time() - start_time
                size = os.path.getsize(src_path)
                speed = size / elapsed if elapsed > 0 else 0

                self.success_count += 1
                progress = int((i + 1) / total * 100)

                self.progress.emit(progress, os.path.basename(src_path), speed)

            except Exception as e:
                self.error_count += 1
                self.error.emit(f"Error copying {src_path}: {e}")

        self.finished_signal.emit(self.success_count, self.error_count)

# Usage
def handle_copy(files: list):
    dest = QFileDialog.getExistingDirectory(window, "Destination")
    if not dest:
        return

    # Create operation in UI
    op_id = f"copy_{int(time.time())}"
    window.operations_panel.add_operation(op_id, "Copying files", len(files))

    # Start worker
    worker = CopyWorker(files, dest)
    worker.progress.connect(
        lambda p, f, s: window.operations_panel.update_operation(
            op_id, progress=p, current_file=f, speed=s
        )
    )
    worker.finished_signal.connect(
        lambda s, e: window.operations_panel.set_operation_status(
            op_id,
            OperationStatus.COMPLETED if e == 0 else OperationStatus.FAILED
        )
    )
    worker.start()

window.results_panel.copy_requested.connect(handle_copy)
```

## Duplicate Detection Integration

```python
from smart_search.duplicates import DuplicateFinder  # Your backend

def find_duplicates():
    """Find and display duplicates"""

    # Get search paths
    paths = window.directory_tree.get_selected_paths()

    if not paths:
        QMessageBox.warning(window, "No Paths", "Select directories to scan")
        return

    # Update UI
    window.results_tabs.setCurrentWidget(window.duplicates_panel)
    window.status_label.setText("Scanning for duplicates...")

    # Create worker
    class DuplicateWorker(QThread):
        duplicates_found = pyqtSignal(list)  # List of duplicate groups
        progress = pyqtSignal(int, str)

        def __init__(self, paths):
            super().__init__()
            self.paths = paths

        def run(self):
            finder = DuplicateFinder()

            for path in self.paths:
                finder.scan_directory(path)
                self.progress.emit(0, f"Scanning {path}")

            groups = finder.get_duplicate_groups()
            self.duplicates_found.emit(groups)

    worker = DuplicateWorker(paths)
    worker.duplicates_found.connect(window.duplicates_panel.set_duplicates)
    worker.progress.connect(lambda _, p: window.status_label.setText(p))
    worker.start()

# Connect to menu action
window.find_duplicates_action.triggered.connect(find_duplicates)
```

## Settings Integration

```python
def load_backend_settings():
    """Load settings from UI into backend"""
    settings = window.settings_dialog.settings

    # Search settings
    backend.set_max_results(settings.value("search/max_results", 10000, type=int))
    backend.set_thread_count(settings.value("search/thread_count", 4, type=int))
    backend.set_follow_symlinks(settings.value("search/follow_symlinks", True, type=bool))

    # Operation settings
    backend.set_buffer_size(settings.value("operations/buffer_size", 256*1024, type=int))
    backend.set_verify_copy(settings.value("operations/verify_copy", False, type=bool))

# Call after settings dialog closes
window.settings_dialog.accepted.connect(load_backend_settings)
```

## Example: Full Integration

```python
# main_app.py
from PyQt6.QtWidgets import QApplication
from smart_search.ui import MainWindow
from smart_search.backend import SmartSearchBackend
from smart_search.controller import SearchController

def main():
    app = QApplication([])

    # Create components
    window = MainWindow()
    backend = SmartSearchBackend()
    controller = SearchController(window, backend)

    # Show window
    window.show()

    # Run
    app.exec()

if __name__ == "__main__":
    main()
```

## Testing Integration

```python
# test_integration.py
import pytest
from PyQt6.QtWidgets import QApplication
from smart_search.ui import MainWindow

@pytest.fixture
def app():
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def window(app):
    return MainWindow()

def test_search_integration(window):
    """Test search signal emission"""
    received = []

    def capture(params):
        received.append(params)

    window.search_started.connect(capture)

    # Simulate search
    window.search_panel.search_input.setText("test.txt")
    window.search_panel._perform_search()

    assert len(received) == 1
    assert received[0]['query'] == "test.txt"

def test_results_display(window):
    """Test adding results"""
    window.results_panel.add_result({
        'name': 'test.txt',
        'path': '/path/to/test.txt',
        'size': 1024,
        'modified': datetime.now(),
    })

    assert window.results_panel.table.rowCount() == 1
```

## Performance Tips

1. **Batch Results**: Add results in batches (100-1000) instead of one-by-one
2. **Use Signals**: Don't call UI methods directly from threads
3. **Defer Updates**: Use QTimer.singleShot(0, ...) for non-critical updates
4. **Disable Sorting**: Temporarily disable table sorting when adding many items
5. **Virtual Scrolling**: Implement for 10k+ results

## Error Handling

```python
def safe_operation(operation_func):
    """Decorator for safe UI operations"""
    def wrapper(*args, **kwargs):
        try:
            return operation_func(*args, **kwargs)
        except Exception as e:
            QMessageBox.critical(
                window,
                "Error",
                f"Operation failed: {e}"
            )
            import traceback
            traceback.print_exc()

    return wrapper

@safe_operation
def handle_search(params):
    # Search logic
    pass
```

## Advanced: Custom Workers

See `smart_search/ui/demo.py` for examples of:
- Progressive result loading
- Simulated operations
- Speed graph updates
- Status bar updates

## Next Steps

1. Implement your backend classes
2. Create worker threads for long operations
3. Connect signals as shown above
4. Test with real data
5. Add error handling
6. Optimize for performance

## Support

For issues or questions:
- Check the main README
- See example code in `ui/demo.py`
- Review `ui/__main__.py` for standalone testing
