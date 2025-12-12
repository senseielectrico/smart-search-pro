# Best Practices for Smart Search UI Development

## Signal-Based Communication

### DO
```python
# Define signals in widget class
class CustomWidget(QWidget):
    action_requested = pyqtSignal(list)  # Always include type hint

    def trigger_action(self):
        data = self.get_data()
        self.action_requested.emit(data)

# Connect in parent
widget.action_requested.connect(self.handle_action)
```

### DON'T
```python
# Avoid parent() chains
widget.triggered.connect(lambda: self.parent().parent()._method())  # FRAGILE!

# Avoid direct parent method calls
self.parent().some_method()  # BREAKS ENCAPSULATION
```

## Thread Management

### DO
```python
# Always use timeouts
if not worker.wait(5000):  # 5 seconds
    logger.warning("Worker timeout")
    worker.terminate()
    worker.wait(1000)  # Final cleanup wait

# Check if running before stopping
if worker and worker.isRunning():
    worker.stop()
```

### DON'T
```python
# No indefinite waits
worker.wait()  # Can hang forever!

# No unchecked termination
worker.terminate()  # Without wait or running check
```

## Resource Cleanup

### DO
```python
def closeEvent(self, event):
    """Cleanup all resources"""
    # Stop workers
    if self.worker and self.worker.isRunning():
        self.worker.stop()
        if not self.worker.wait(3000):
            self.worker.terminate()
            self.worker.wait(1000)

    # Close connections, files, etc.

    event.accept()
```

### DON'T
```python
# No cleanup implementation
# Relying on Python's GC alone
# Ignoring running threads
```

## Error Handling

### DO
```python
def handle_files(self, files: list):
    """Process files with proper validation"""
    if not files:
        return

    # Validate files exist
    valid_files = [f for f in files if os.path.exists(f)]

    if not valid_files:
        QMessageBox.warning(self, "Error", "No valid files")
        return

    # Process with error counting
    errors = 0
    for file in valid_files:
        try:
            process_file(file)
        except Exception as e:
            logger.error(f"Error: {e}")
            errors += 1

    # Report results
    if errors:
        QMessageBox.warning(self, "Errors", f"{errors} files failed")
```

### DON'T
```python
# No validation
def handle_files(self, files):
    for file in files:  # What if files is None?
        process_file(file)  # What if file doesn't exist?
```

## Type Annotations

### DO
```python
def process_files(self, files: List[str]) -> int:
    """Process files and return count"""
    count = 0
    for file_path in files:
        # Process...
        count += 1
    return count

# Signal with type
data_ready = pyqtSignal(list)  # or pyqtSignal(object) for complex types
```

### DON'T
```python
# No type hints
def process_files(self, files):  # What type is files?
    # ...
    return count  # What type is count?
```

## Widget Hierarchy

### DO
```python
# Communicate via signals
class ChildWidget(QWidget):
    request_action = pyqtSignal(str)

    def on_click(self):
        self.request_action.emit("action_data")

class ParentWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.child = ChildWidget()
        self.child.request_action.connect(self.handle_action)
```

### DON'T
```python
# Tight coupling
class ChildWidget(QWidget):
    def on_click(self):
        self.parent().handle_action()  # Assumes parent has this method
```

## Logging

### DO
```python
import logging

logger = logging.getLogger(__name__)

def risky_operation(self):
    try:
        # Operation
        logger.info("Operation successful")
    except Exception as e:
        logger.error(f"Operation failed: {e}", exc_info=True)
```

### DON'T
```python
# Silent failures
try:
    operation()
except:
    pass  # NO! At least log it!

# Print debugging
print(f"Debug: {value}")  # Use logger instead
```

## File Operations

### DO
```python
def copy_files(self, files: List[str], dest: str):
    """Copy files with conflict resolution"""
    for file_path in files:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            continue

        filename = os.path.basename(file_path)
        dest_path = os.path.join(dest, filename)

        # Handle conflicts
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dest_path):
                filename = f"{base}_{counter}{ext}"
                dest_path = os.path.join(dest, filename)
                counter += 1

        shutil.copy2(file_path, dest_path)
```

### DON'T
```python
# No conflict handling
def copy_files(self, files, dest):
    for file in files:
        shutil.copy2(file, dest)  # Overwrites without warning!
```

## Progress Feedback

### DO
```python
class Worker(QThread):
    progress = pyqtSignal(int, str)  # percentage, message

    def run(self):
        total = len(self.items)
        for i, item in enumerate(self.items):
            process(item)
            percentage = int((i + 1) / total * 100)
            self.progress.emit(percentage, f"Processing {item}")
```

### DON'T
```python
# No feedback
class Worker(QThread):
    def run(self):
        for item in self.items:
            process(item)  # User has no idea what's happening
```

## Testing

### DO
```python
# Create testable functions
def validate_files(files: List[str]) -> List[str]:
    """Return only existing files"""
    return [f for f in files if os.path.exists(f)]

# Then use in UI
valid_files = validate_files(selected_files)
```

### DON'T
```python
# Mix logic with UI
def button_clicked(self):
    # Validation logic mixed with UI updates
    # Hard to test independently
```

## Performance

### DO
```python
# Batch updates
self.table.setUpdatesEnabled(False)
for item in items:
    self.table.add_item(item)
self.table.setUpdatesEnabled(True)

# Use threads for I/O
worker = SearchWorker(paths, term)
worker.result.connect(self.handle_result)
worker.start()
```

### DON'T
```python
# Update UI in loop
for item in items:
    self.table.add_item(item)
    QApplication.processEvents()  # Bad practice!

# Block UI with I/O
results = search_files(paths)  # Freezes UI
```

## Configuration

### DO
```python
# Use constants
MAX_OPEN_FILES = 10
SEARCH_TIMEOUT = 5000  # ms
THREAD_CLEANUP_TIMEOUT = 3000  # ms

# Reference in code
for file in files[:MAX_OPEN_FILES]:
    open_file(file)
```

### DON'T
```python
# Magic numbers
for file in files[:10]:  # What does 10 mean?
    open_file(file)
```

## Documentation

### DO
```python
def process_files(self, files: List[str]) -> Dict[str, int]:
    """
    Process files and return statistics.

    Args:
        files: List of absolute file paths

    Returns:
        Dict with 'success' and 'error' counts

    Raises:
        ValueError: If files list is empty
    """
```

### DON'T
```python
def process_files(self, files):
    # Process files
    pass
```

## Code Organization

### DO
```python
# Organize by functionality
class SmartSearchWindow(QMainWindow):
    # 1. Initialization
    def __init__(self):
        pass

    # 2. UI Setup
    def _init_ui(self):
        pass

    # 3. Event Handlers
    def _on_search_clicked(self):
        pass

    # 4. Business Logic
    def _validate_paths(self):
        pass

    # 5. Cleanup
    def closeEvent(self, event):
        pass
```

### DON'T
```python
# Random method order
class MyWindow(QMainWindow):
    def helper3(self):
        pass

    def __init__(self):
        pass

    def helper1(self):
        pass
```

## Signal Naming Conventions

- Use past tense for events that happened: `file_opened`, `search_completed`
- Use present/imperative for requests: `open_requested`, `copy_requested`
- Include data type in comment: `pyqtSignal(list)  # list of file paths`
- Group related signals together in class definition

## Method Naming Conventions

- Private helpers: `_validate_input()`, `_format_size()`
- Event handlers: `_on_search_finished()`, `_on_button_clicked()`
- Public API: `start_search()`, `clear_results()`
- Signal handlers: `_handle_open_request()`, `_process_files_from_list()`

## Common Pitfalls to Avoid

1. **Forgetting to disconnect signals** when removing widgets dynamically
2. **Not checking QThread.isRunning()** before operations
3. **Ignoring return value of wait()** (it returns bool)
4. **Using processEvents()** instead of proper threading
5. **Not validating file existence** before operations
6. **Hardcoding paths** - use os.path.join()
7. **Not handling file name conflicts** in copy/move
8. **Forgetting to update UI** after background operations
9. **Not limiting batch operations** (e.g., max 10 files to open)
10. **Missing error feedback** to user

## Checklist for New Features

- [ ] Type annotations on all parameters and return values
- [ ] Docstrings for public methods
- [ ] Input validation
- [ ] Error handling with logging
- [ ] User feedback (progress, errors, success)
- [ ] Thread safety (if using QThread)
- [ ] Resource cleanup (in closeEvent if needed)
- [ ] Tests for critical paths
- [ ] Performance considerations (batch updates, threading)
- [ ] Consistent naming conventions

## References

- PyQt6 Documentation: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- Qt Signals & Slots: https://doc.qt.io/qt-6/signalsandslots.html
- Python Logging: https://docs.python.org/3/library/logging.html
- Thread Safety: https://doc.qt.io/qt-6/threads-qobject.html
