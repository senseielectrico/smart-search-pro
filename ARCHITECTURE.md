# Smart Search - Architecture Documentation

## Overview

Smart Search is a professional PyQt6-based file search tool for Windows with advanced filtering, categorization, and file management capabilities.

**Total Code**: 906 lines | **Classes**: 7 | **Methods**: 45+ | **Docstrings**: 47

## Architecture Layers

```
┌─────────────────────────────────────────────────┐
│           UI Layer (PyQt6 Widgets)              │
│  SmartSearchWindow, TreeWidget, TableWidget     │
└────────────┬────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────┐
│       Business Logic Layer                      │
│  File categorization, Search logic, Operations  │
└────────────┬────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────┐
│       Threading Layer (QThread)                 │
│  SearchWorker, FileOperationWorker              │
└────────────┬────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────┐
│       System Layer (OS, File I/O)               │
│  os.walk, shutil, os.stat, os.startfile         │
└─────────────────────────────────────────────────┘
```

## Core Components

### 1. SmartSearchWindow (QMainWindow)
**Purpose**: Main application window, orchestrates all components

**Key Methods**:
- `_init_ui()`: Initialize UI layout
- `_create_search_bar()`: Top search controls
- `_create_action_bar()`: Bottom action buttons
- `_start_search()`: Initiate file search
- `_apply_theme()`: Apply dark/light theme
- `_perform_file_operation()`: Execute copy/move

**Responsibilities**:
- Window management
- Component coordination
- User interaction handling
- Theme management

**Layout Structure**:
```
┌────────────────────────────────────────────┐
│  Search Bar (QHBoxLayout)                  │
│  [Input] [Case] [Search] [Stop] [Theme]    │
├───────────┬────────────────────────────────┤
│           │                                │
│  Dir Tree │  Results Tabs (QTabWidget)    │
│  (QTree   │  [Docs][Images][Videos]...     │
│  Widget)  │  QTableWidget (sortable)       │
│           │                                │
├───────────┴────────────────────────────────┤
│  Action Bar (QHBoxLayout)                  │
│  [Open][Location][Copy][Move][Clear]       │
├────────────────────────────────────────────┤
│  Status Bar + Progress Bar                 │
└────────────────────────────────────────────┘
```

### 2. DirectoryTreeWidget (QTreeWidget)
**Purpose**: Hierarchical directory selection with tri-state checkboxes

**Key Methods**:
- `_populate_tree()`: Load common Windows directories
- `_on_item_changed()`: Handle checkbox state changes
- `_update_parent_state()`: Sync parent/child checkboxes
- `get_selected_paths()`: Extract checked directories

**Features**:
- Tri-state checkboxes (checked, unchecked, partial)
- Parent-child synchronization
- Path tooltips
- Lazy subdirectory loading

**Common Paths**:
- C:\ (System Drive)
- User Home
- Desktop, Documents, Downloads
- Pictures, Videos, Music

### 3. ResultsTableWidget (QTableWidget)
**Purpose**: Display search results with sorting and selection

**Columns**:
1. **Name**: Filename
2. **Path**: Full file path
3. **Size**: Human-readable size (B, KB, MB, GB)
4. **Modified**: Last modified date/time
5. **Type**: File extension

**Key Methods**:
- `add_result()`: Add file to table
- `_format_size()`: Convert bytes to readable format
- `get_selected_files()`: Get selected file paths
- `_show_context_menu()`: Right-click menu

**Context Menu**:
- Open
- Open Location
- Copy to...
- Move to...
- Copy Path (to clipboard)

### 4. SearchWorker (QThread)
**Purpose**: Background file search without blocking UI

**Signals**:
- `progress(int, str)`: Progress update (percentage, current file)
- `result(dict)`: File found (file info dict)
- `finished(int)`: Search complete (total files)
- `error(str)`: Error occurred

**Key Methods**:
- `run()`: Execute search (overrides QThread.run)
- `_search_directory()`: Recursive directory traversal
- `_matches_search()`: Check filename match
- `_get_file_info()`: Extract file metadata
- `stop()`: Gracefully stop search

**Search Algorithm**:
```python
for path in search_paths:
    for root, dirs, files in os.walk(path):
        for file in files:
            if matches_search(file):
                emit_result(file_info)
```

### 5. FileOperationWorker (QThread)
**Purpose**: Background file copy/move operations

**Signals**:
- `progress(int, str)`: Progress (percentage, current file)
- `finished(int, int)`: Complete (success count, error count)
- `error(str)`: Error message

**Features**:
- Automatic conflict resolution (append _1, _2, etc.)
- Progress tracking per file
- Error isolation (one failure doesn't stop batch)

### 6. FileType (Enum)
**Purpose**: File categorization system

**Categories**:
- **Documents**: Office files, PDFs, text
- **Images**: Photos, graphics, icons
- **Videos**: Video files
- **Audio**: Music, podcasts, sound
- **Archives**: Compressed files
- **Code**: Source code files
- **Executables**: Programs, scripts
- **Other**: Uncategorized

**Method**: `get_category(filename)` - Maps extension to category

### 7. FileOperation (Enum)
**Purpose**: Operation type enum

**Values**:
- `COPY`: Copy files
- `MOVE`: Move files

## Data Flow

### Search Flow
```
User → [Search Button]
  ↓
SmartSearchWindow._start_search()
  ↓
Create SearchWorker(paths, term, case_sensitive)
  ↓
SearchWorker.run() [Background Thread]
  ↓
os.walk() → Filter matches → Get file info
  ↓
Emit result signal → SmartSearchWindow._on_search_result()
  ↓
Categorize → Add to appropriate ResultsTableWidget
  ↓
Update UI (tab counts, file count label)
```

### File Operation Flow
```
User → [Copy/Move Button]
  ↓
SmartSearchWindow._perform_file_operation()
  ↓
QFileDialog.getExistingDirectory() → Get destination
  ↓
QMessageBox.question() → Confirm operation
  ↓
Create FileOperationWorker(files, dest, operation)
  ↓
FileOperationWorker.run() [Background Thread]
  ↓
For each file: shutil.copy2() or shutil.move()
  ↓
Emit progress → Update progress bar
  ↓
Emit finished → Show completion message
```

## Threading Model

### Main Thread (UI Thread)
- All PyQt6 widget updates
- User interaction handling
- Signal/slot connections
- UI rendering

### Worker Threads (QThread)
- File system operations (search, copy, move)
- Long-running tasks
- CPU/IO intensive operations

**Communication**: Qt signals/slots (thread-safe)

## State Management

### Application State
- `search_worker`: Current SearchWorker instance (or None)
- `operation_worker`: Current FileOperationWorker instance (or None)
- `dark_mode`: Boolean theme flag
- `result_tables`: Dict mapping FileType → ResultsTableWidget

### UI State
- Button enabled/disabled based on selection
- Progress bar visibility based on operation
- Tab labels showing file counts
- Status bar messages

## Performance Optimizations

### 1. Background Threading
- All file I/O in worker threads
- UI remains responsive during operations
- Graceful cancellation support

### 2. Lazy Loading
- Directory tree loads only immediate children
- Results streamed (not batched)
- Minimal memory footprint

### 3. Efficient Updates
- Progress updates throttled (every 10 files)
- Batch UI updates where possible
- Sortable tables use Qt's native sorting

### 4. Smart Categorization
- O(1) category lookup using dict/enum
- Pre-computed extension mappings
- Minimal string operations

## Error Handling

### Levels
1. **Silent**: Permission errors during search (logged, not shown)
2. **Logged**: Individual file operation errors (counted)
3. **User Notification**: Critical errors (QMessageBox)

### Recovery
- Search continues on permission error
- File operations track success/error counts
- Graceful degradation

## Keyboard Shortcuts

| Shortcut | Action | Implementation |
|----------|--------|----------------|
| Ctrl+F | Focus search | QAction + setFocus() |
| Ctrl+O | Open files | QAction + _open_files() |
| Ctrl+Shift+C | Copy files | QAction + _copy_files() |
| Ctrl+M | Move files | QAction + _move_files() |
| Ctrl+L | Clear results | QAction + _clear_results() |
| Enter | Start search | QLineEdit.returnPressed |

## Theming System

### Light Theme
- Default Qt styling
- System colors
- Standard Windows appearance

### Dark Theme
- Custom stylesheet (CSS-like)
- Color palette:
  - Background: #1e1e1e
  - Widget BG: #2d2d30
  - Accent: #0e639c
  - Text: #d4d4d4
  - Border: #3e3e42

**Toggle**: QPushButton.checkable with stylesheet update

## Extensibility Points

### Adding File Categories
1. Add enum value to `FileType`
2. Define extensions list
3. UI automatically creates tab

### Adding Operations
1. Add enum value to `FileOperation`
2. Implement logic in `FileOperationWorker.run()`
3. Add UI button if needed

### Custom Search Filters
Extend `SearchWorker._matches_search()`:
- Size filters
- Date range filters
- Regex patterns
- Content search

### Integration Points
- Replace `os.walk()` with Everything SDK for instant search
- Add database backend for search history
- Export results to CSV/JSON
- Cloud storage integration (OneDrive, Google Drive)

## Testing Strategy

### Unit Tests
- File categorization logic
- Size formatting
- Tri-state checkbox logic
- Path collection

### Integration Tests
- Search worker with mock filesystem
- File operation worker with temp directory
- Signal/slot connections

### UI Tests
- Button state transitions
- Table sorting
- Theme switching
- Keyboard shortcuts

## Dependencies

### Required
- **PyQt6** (>=6.6.0): GUI framework
  - QtWidgets: UI components
  - QtCore: Signals, threads, enums
  - QtGui: Icons, fonts, palettes

### Standard Library
- `os`: File system operations
- `sys`: System configuration
- `pathlib`: Path manipulation
- `datetime`: Timestamp formatting
- `shutil`: File copy/move
- `typing`: Type hints
- `enum`: Enumerations

## File Structure

```
smart_search/
├── ui.py                 # Main application (906 lines)
├── requirements.txt      # Dependencies
├── README.md            # User documentation
├── INSTALL.md           # Installation guide
├── ARCHITECTURE.md      # This file
├── example.py           # Usage examples
├── validate.py          # Code validation script
├── install.bat          # Windows installer
└── run.bat             # Windows launcher
```

## Security Considerations

### File System Access
- Respects OS permissions
- Handles permission errors gracefully
- No privilege escalation

### User Input
- Path validation before operations
- No shell command execution
- SQL injection not applicable (no database)

### Operations
- Confirms destructive operations (move)
- Automatic conflict resolution (no overwrites)
- Limited to 10 simultaneous file opens

## Accessibility

### WCAG 2.1 AA Compliance
- High contrast in dark mode
- Keyboard navigation support
- Focus indicators on all controls
- Tooltips on interactive elements

### Screen Reader Support
- Qt's accessible widgets
- Semantic structure
- Label associations

## Future Enhancements

### Planned Features
1. Regex search patterns
2. Advanced filters (size, date, type)
3. Search history
4. Saved searches
5. Export results (CSV, JSON, HTML)
6. Duplicate file detection
7. Everything SDK integration
8. Search across network drives
9. File preview pane
10. Drag-and-drop support

### Performance Improvements
1. Multi-threaded search (one thread per drive)
2. Result pagination
3. Virtual scrolling for large result sets
4. Caching for repeated searches

### UI Enhancements
1. Custom file type categories
2. Column customization
3. Layout persistence
4. Multiple search tabs
5. Quick filters

## Maintenance

### Code Quality
- Type hints throughout
- Comprehensive docstrings
- Consistent naming (PEP 8)
- Modular design

### Version Control
- Git-friendly structure
- Single-file deployment option
- Semantic versioning

### Documentation
- Inline comments for complex logic
- API documentation in docstrings
- User-facing README
- This architecture document

## Contributing

### Code Style
- PEP 8 compliance
- Type hints required
- Docstrings for all public methods
- Maximum line length: 120

### Pull Request Checklist
- [ ] Passes validation script
- [ ] No new dependencies (or justified)
- [ ] Updated documentation
- [ ] Keyboard shortcuts work
- [ ] Dark/Light themes tested

## License

MIT License - Free to use and modify

## Author

Built with Claude Code
Professional React and Frontend Development Assistant
Anthropic, 2024
