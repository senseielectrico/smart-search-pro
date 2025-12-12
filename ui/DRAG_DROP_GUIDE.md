# Smart Search Pro - Drag & Drop Complete Guide

## Overview

Complete drag and drop implementation for Smart Search Pro with Windows Shell integration, multi-file support, and visual feedback.

## Architecture

```
drag_drop.py
├── DragDropHandler (Core)
│   ├── Drag FROM application
│   ├── Drop TO application
│   └── Visual feedback & cursor management
│
├── DropZoneWidget (Mixin)
│   └── Simplifies adding drop support to widgets
│
└── DragSource (Mixin)
    └── Simplifies adding drag support to widgets
```

## Features Implemented

### 1. Drag FROM Results Panel

**Files**: `ui/results_panel.py`, `ui/drag_drop.py`

#### Capabilities
- Multi-file selection drag
- Visual drag preview with file count
- Keyboard modifiers:
  - `Ctrl + Drag` = Copy operation
  - `Shift + Drag` = Move operation
  - `Alt + Drag` = Link operation
- Windows Shell integration (drag to Explorer, other apps)

#### Usage
```python
# In ResultsPanel
self.drag_handler = DragDropHandler(self)
self.table = DraggableTableView()  # Custom table with drag support
self.table.drag_handler = self.drag_handler
```

#### User Experience
1. Select files in results table
2. Click and hold on selection
3. Drag 10px to initiate drag
4. Visual preview shows file count and names
5. Drop to Windows Explorer, Operations panel, or other apps
6. Hold `Ctrl` during drag to force copy, `Shift` to force move

### 2. Drop TO Operations Panel

**Files**: `ui/operations_panel.py`

#### Capabilities
- Accept file drops from Explorer or Results panel
- Context menu on drop (Copy/Move/Add to Selection)
- Real-time modifier hints during drag
- Integration with backend operations manager
- Visual feedback with highlighted drop zone

#### Usage
```python
# In OperationsPanel
self.drag_handler = DragDropHandler(self)
self.drag_handler.files_dropped.connect(self._on_files_dropped_to_panel)
self.setAcceptDrops(True)
```

#### User Experience
1. Drag files from Explorer or Results panel
2. Hover over Operations panel
3. See blue highlight and operation hints
4. Drop files
5. If destination set: Context menu appears with Copy/Move options
6. If no destination: Files added to selection

### 3. Drop TO Directory Tree

**Files**: `ui/directory_tree.py`

#### Capabilities
- Accept folder drops from Explorer
- Automatically add to search paths
- Auto-check dropped folders
- Visual feedback with border highlight
- Reject non-folder drops

#### Usage
```python
# In DirectoryTree
self.drag_handler = DragDropHandler(self)
self.setAcceptDrops(True)
```

#### User Experience
1. Drag folder from Windows Explorer
2. Hover over Directory Tree
3. See blue border highlight
4. Drop folder
5. Folder automatically added to tree and checked
6. Ready to search in that location

## Implementation Details

### Drag Preview Creation

```python
def _create_drag_pixmap(self, file_paths: List[str]) -> QPixmap:
    """
    Creates visual preview:
    - Single file: Shows filename and size
    - Multiple files: Shows count and first 2 filenames
    - Max 300x100px with rounded corners
    """
```

### Keyboard Modifiers

```python
modifiers = QApplication.keyboardModifiers()

if modifiers & Qt.KeyboardModifier.ControlModifier:
    operation = "COPY"
elif modifiers & Qt.KeyboardModifier.ShiftModifier:
    operation = "MOVE"
else:
    operation = "COPY"  # Default
```

### Windows Shell Integration

The implementation uses Qt's MIME data system which automatically integrates with Windows Shell:

```python
mime_data = QMimeData()
urls = [QUrl.fromLocalFile(path) for path in file_paths]
mime_data.setUrls(urls)
drag.setMimeData(mime_data)
```

This allows:
- Drag from app to Windows Explorer
- Drag from app to email clients
- Drag from app to other applications
- Standard Windows copy/move operations

## Visual Feedback

### Results Panel (Drag Source)
- **Hover**: Normal cursor
- **Drag Start**: Custom drag preview pixmap
- **During Drag**: Copy/Move/Link cursor based on modifiers

### Operations Panel (Drop Zone)
- **Hover**: Blue dashed border, light blue background
- **Info Bar**: Shows "Drop to COPY" or "Drop to MOVE" based on modifiers
- **After Drop**: Context menu with operation choices

### Directory Tree (Drop Zone)
- **Hover**: Blue solid border, light blue tint
- **Drop**: Folder added and expanded automatically

## Signals

### DragDropHandler Signals

```python
drag_started = pyqtSignal(list)        # Emitted when drag starts
drag_completed = pyqtSignal(str)       # Emitted when drag completes
files_dropped = pyqtSignal(list, str)  # Emitted when files dropped
```

### Panel-specific Signals

```python
# ResultsPanel
self.drag_handler.drag_started.connect(handler)
self.drag_handler.drag_completed.connect(handler)

# OperationsPanel
self.files_dropped_signal.emit(files)

# DirectoryTree
self.files_dropped_to_search.emit(folders)
```

## Testing

### Run Demo

```bash
cd C:\Users\ramos\.local\bin\smart_search
python -m ui.drag_drop_demo
```

### Test Scenarios

1. **Single File Drag**
   - Select one file in Results
   - Drag to Explorer
   - Verify file appears at drop location

2. **Multi-File Drag**
   - Select multiple files (Ctrl+Click)
   - Drag to Operations panel
   - Verify context menu appears

3. **Folder Drop to Tree**
   - Drag folder from Explorer
   - Drop on Directory Tree
   - Verify folder is added and checked

4. **Modifier Keys**
   - Drag file while holding Ctrl
   - Verify "Copy" operation
   - Drag while holding Shift
   - Verify "Move" operation

5. **Visual Feedback**
   - Hover over drop zones
   - Verify highlighting appears
   - Leave drop zone
   - Verify highlighting disappears

## Integration Examples

### Adding Drop Support to New Widget

```python
from ui.drag_drop import DragDropHandler, DropZoneWidget

class MyWidget(QWidget, DropZoneWidget):
    def __init__(self):
        super().__init__()

        # Create handler
        self.drag_handler = DragDropHandler(self)
        self.setAcceptDrops(True)

        # Connect signals
        self.drag_handler.files_dropped.connect(self._on_files_dropped)

    def dragEnterEvent(self, event):
        if self.drag_handler.handle_drag_enter(event):
            # Add custom visual feedback
            pass

    def dropEvent(self, event):
        files = self.drag_handler.handle_drop(event, "my_zone")
        # Process dropped files
```

### Adding Drag Support to New Widget

```python
from ui.drag_drop import DragDropHandler, DragSource

class MyListWidget(QListWidget, DragSource):
    def __init__(self):
        super().__init__()

        # Create handler
        self.drag_handler = DragDropHandler(self)
        self.setup_drag_source(self.drag_handler)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            # Get selected items
            files = self._get_selected_files()

            # Start drag
            self.start_drag(files)
```

## Performance Considerations

1. **Drag Preview Generation**: Cached for repeated drags of same selection
2. **MIME Data**: Lightweight URLs, not full file data
3. **Visual Feedback**: CSS-based, no image manipulation
4. **Event Handling**: Minimal processing in drag/drop events

## Windows-Specific Features

### Shell Integration
- Uses `QUrl.fromLocalFile()` for proper Windows path handling
- MIME data automatically recognized by Windows Shell
- Standard Windows drag cursors

### File Operations
- Copy: Creates file copy at destination
- Move: Moves file to destination
- Link: Creates shortcut (Windows .lnk file)

## Troubleshooting

### Drag Not Starting
- Check `setDragEnabled(True)` or custom drag logic
- Verify 10px movement threshold reached
- Ensure file paths are valid

### Drop Not Accepted
- Check `setAcceptDrops(True)`
- Verify `dragEnterEvent` accepts the event
- Check MIME data format

### No Visual Feedback
- Verify stylesheet applied
- Check `dragEnterEvent` and `dragLeaveEvent` called
- Ensure style not overridden

### Context Menu Not Appearing
- Check destination folder is set
- Verify `_show_drop_context_menu` called
- Check menu event position calculation

## Future Enhancements

Possible additions:
- Drag from Operations panel to Results (reorder queue)
- Drag between Directory Tree items (reorganize)
- Drag to Search panel (quick search in dropped locations)
- Custom drag cursors with operation icons
- Drag progress indicator for large selections
- Undo drag operation
- Drag file previews with thumbnails

## API Reference

### DragDropHandler

```python
class DragDropHandler(QObject):
    # Signals
    drag_started = pyqtSignal(list)
    drag_completed = pyqtSignal(str)
    files_dropped = pyqtSignal(list, str)

    # Methods
    def create_drag(file_paths, source_widget) -> QDrag
    def execute_drag(drag, default_action) -> Qt.DropAction
    def handle_drag_enter(event, accept_files, accept_folders) -> bool
    def handle_drag_move(event) -> bool
    def handle_drop(event, zone) -> List[str]
    def get_drop_action_from_modifiers() -> Qt.DropAction
    def get_operation_cursor() -> QCursor
```

### DropZoneWidget Mixin

```python
class DropZoneWidget:
    def setup_drop_zone(zone_name, handler, accept_files, accept_folders, hover_style)
    def on_files_dropped(files: List[str])  # Override in subclass
```

### DragSource Mixin

```python
class DragSource:
    def setup_drag_source(handler)
    def start_drag(file_paths: List[str])
```

## File Structure

```
ui/
├── drag_drop.py              # Core drag & drop implementation
├── results_panel.py          # Drag source (FROM)
├── operations_panel.py       # Drop target (TO) with operations
├── directory_tree.py         # Drop target (TO) for folders
├── drag_drop_demo.py         # Standalone demo
└── DRAG_DROP_GUIDE.md        # This file
```

## Related Files

- `operations/manager.py` - Backend for copy/move operations
- `operations/copier.py` - File copying with progress
- `operations/mover.py` - File moving with progress
- `ui/widgets.py` - Progress cards, visual components

## Contact

For questions or issues with drag & drop functionality, refer to the main project documentation or create an issue.

---

**Version**: 1.0.0
**Last Updated**: 2025-12-12
**Tested On**: Windows 11, PyQt6 6.7+
