# Data Viewers Module

Comprehensive database and data file viewers for Smart Search Pro.

## Features

### Database Viewer (SQLite)
- **Open any SQLite database** (.db, .sqlite, .sqlite3)
- **Browse tables** with pagination (configurable rows per page)
- **View table schemas** with column details, indexes, and foreign keys
- **Execute SQL queries** with syntax highlighting and history
- **Edit cells inline** with confirmation (respects primary keys)
- **Export tables** to CSV or Excel
- **Search across all tables** with case-sensitive option
- **Recent databases** dropdown for quick access
- **Query history** with bookmarking capability

### JSON Viewer
- **Parse and display JSON** with interactive tree view
- **Syntax highlighting** with color-coded types
- **Collapse/expand nodes** for easy navigation
- **Search within JSON** structure
- **Edit values inline** with validation
- **Format/prettify JSON** automatically
- **Table view** for arrays of objects
- **Export to CSV** from table view
- **Copy path** to any node
- **Copy values** and JSON snippets

### Data Viewer Factory
Auto-detect file type and open appropriate viewer:
- **SQLite** (.db, .sqlite, .sqlite3, .db3)
- **JSON** (.json)
- **XML** (.xml)
- **CSV** (.csv, .tsv)
- **YAML** (.yaml, .yml)
- **INI** (.ini, .conf, .cfg)
- **Plugin architecture** for adding new formats

## Installation

The viewers are part of Smart Search Pro and require:

```bash
pip install PyQt6
```

Optional dependencies for full functionality:
```bash
pip install openpyxl  # For Excel export
pip install PyYAML    # For YAML support
```

## Usage

### Database Viewer

```python
from viewers.database_viewer import DatabaseViewer

viewer = DatabaseViewer()
viewer.open_database("path/to/database.db")
viewer.show()
```

### JSON Viewer

```python
from viewers.json_viewer import JSONViewer

viewer = JSONViewer()
viewer.open_file("data.json")
viewer.show()
```

### Data Viewer Factory (Recommended)

```python
from viewers.data_viewer_factory import DataViewerFactory

factory = DataViewerFactory()

# Auto-detect and open
viewer = factory.create_viewer("unknown_file.db")
if viewer:
    viewer.show()

# Get file filter for dialogs
filter_string = factory.get_filter_string()
# Returns: "All Supported (*.db *.json *.csv);;Database Files (*.db);;..."
```

### UI Integration

#### Database Panel (for main window integration)

```python
from ui.database_panel import DatabasePanel

panel = DatabasePanel()
panel.open_database("database.db")

# Connect signals
panel.database_opened.connect(lambda path: print(f"Opened: {path}"))
panel.table_selected.connect(lambda table: print(f"Selected: {table}"))
panel.query_executed.connect(lambda query: print(f"Executed: {query}"))
```

#### JSON Tree Widget

```python
from ui.json_tree_widget import JSONTreeWidget

tree = JSONTreeWidget()

# Load from data
data = {"key": "value", "array": [1, 2, 3]}
tree.load_json(data)

# Or from file
tree.load_json_file("data.json")

# Or from string
tree.load_json_string('{"test": true}')

# Connect signals
tree.node_selected.connect(lambda node: print(node.get_path()))
tree.path_copied.connect(lambda path: print(f"Copied: {path}"))
```

## Architecture

### Database Viewer Components

```
DatabaseViewer (QWidget)
├── SQLiteConnection (thread-safe connection manager)
├── QueryHistoryManager (persistent query history)
├── RecentDatabasesManager (recent databases list)
└── TableDataModel (editable table model)
```

### JSON Viewer Components

```
JSONViewer (QWidget)
├── JSONTreeModel (QAbstractItemModel)
│   └── JSONTreeNode (tree node with type info)
├── Tree View Tab (interactive navigation)
├── Raw JSON Tab (editable text)
└── Table View Tab (for arrays)
```

### Factory Pattern

```
DataViewerFactory
├── ViewerType (enum of supported types)
├── Extension mapping (.db -> DATABASE)
├── Viewer factories (type -> widget constructor)
└── Plugin system (register custom viewers)
```

## File Structure

```
smart_search/
├── viewers/
│   ├── __init__.py              # Module exports
│   ├── database_viewer.py       # SQLite database viewer
│   ├── json_viewer.py           # JSON file viewer
│   ├── data_viewer_factory.py   # Auto-detection factory
│   └── README.md                # This file
│
└── ui/
    ├── database_panel.py        # Database explorer panel
    └── json_tree_widget.py      # Reusable JSON tree widget
```

## Key Features

### Database Viewer

**Table Browsing**
- Pagination with configurable page size (100, 500, 1000, 5000 rows)
- Sort by any column
- NULL values displayed in gray
- Row count displayed for each table

**Schema Inspection**
- Column name, type, nullable, default value
- Primary key and auto-increment indicators
- Indexes list with unique/non-unique
- Foreign key relationships

**Query Editor**
- Ctrl+Enter to execute
- Query history dropdown
- Bookmark frequently used queries
- Results displayed in sortable table

**Search**
- Search across all tables
- Case-sensitive option
- Shows table, column, and matching value

**Export**
- Export tables to CSV or Excel
- Export query results to CSV
- Preserves column headers

### JSON Viewer

**Tree View**
- Color-coded by type (string, number, boolean, null, object, array)
- Tooltips show full path and value
- Expand/collapse all or individual nodes
- Icons for different types

**Editing**
- Edit in raw JSON tab
- Automatic validation
- Format/prettify on demand
- Saves back to file

**Table View**
- Converts arrays of objects to table
- Sortable columns
- Export to CSV
- Handles nested objects

**Context Menu**
- Copy path (e.g., "data.users[0].name")
- Copy value
- Copy as JSON (for objects/arrays)

## Integration with Smart Search Pro

The viewers integrate seamlessly with Smart Search Pro:

1. **File Context Menu**: Right-click database or JSON files in search results
2. **Preview Panel**: Quick preview of file contents
3. **Direct Open**: Double-click to open in full viewer
4. **Recent Files**: Access recently opened databases
5. **Export Integration**: Export search results to database or JSON

## Error Handling

All viewers include comprehensive error handling:

- **Invalid files**: Clear error messages with details
- **Corrupted data**: Graceful degradation
- **Missing dependencies**: Fallback behavior
- **Large files**: Pagination and lazy loading
- **Encoding issues**: UTF-8 with fallback

## Performance Considerations

- **Lazy Loading**: Only load visible data
- **Pagination**: Database tables paginated by default
- **Indexing**: Use database indexes for queries
- **Caching**: Recent databases and queries cached
- **Threading**: Database operations on background threads

## Keyboard Shortcuts

### Database Viewer
- `Ctrl+Enter` - Execute query
- `F5` - Refresh current view

### JSON Viewer
- `Ctrl+F` - Focus search
- `Ctrl+S` - Save file
- `Ctrl+Shift+F` - Format JSON

## Extending the Viewers

### Adding a New Viewer Type

```python
from viewers.data_viewer_factory import DataViewerFactory, ViewerType
from enum import Enum

# Define new type
class CustomViewerType(Enum):
    CUSTOM = "custom"

# Create viewer class
class CustomViewer(QWidget):
    def open_file(self, file_path: str):
        # Implementation
        pass

# Register with factory
factory = DataViewerFactory()
factory.register_viewer(CustomViewerType.CUSTOM, lambda: CustomViewer())
factory.register_extension('.custom', CustomViewerType.CUSTOM)
```

## Examples

### Example 1: Open Database and Execute Query

```python
from viewers.database_viewer import DatabaseViewer
from PyQt6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
viewer = DatabaseViewer()
viewer.open_database("example.db")
viewer.resize(1200, 800)
viewer.show()
sys.exit(app.exec())
```

### Example 2: Load and Edit JSON

```python
from viewers.json_viewer import JSONViewer
from PyQt6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
viewer = JSONViewer()
viewer.open_file("config.json")
viewer.resize(1000, 700)
viewer.show()
sys.exit(app.exec())
```

### Example 3: Auto-detect File Type

```python
from viewers.data_viewer_factory import DataViewerFactory
from PyQt6.QtWidgets import QApplication, QFileDialog
import sys

app = QApplication(sys.argv)
factory = DataViewerFactory()

# Open file dialog
file_path, _ = QFileDialog.getOpenFileName(
    None,
    "Open Data File",
    "",
    factory.get_filter_string()
)

if file_path:
    viewer = factory.create_viewer(file_path)
    if viewer:
        viewer.resize(1200, 800)
        viewer.show()

sys.exit(app.exec())
```

### Example 4: Integrate into Main Window

```python
from ui.database_panel import DatabasePanel
from PyQt6.QtWidgets import QMainWindow, QTabWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Add database panel
        self.db_panel = DatabasePanel()
        self.tabs.addTab(self.db_panel, "Database Explorer")

        # Connect signals
        self.db_panel.database_opened.connect(self.on_db_opened)

    def on_db_opened(self, path):
        self.statusBar().showMessage(f"Opened: {path}")
```

## Troubleshooting

### Database won't open
- Verify file is a valid SQLite database
- Check file permissions
- Ensure file is not locked by another process

### JSON parse error
- Validate JSON syntax at jsonlint.com
- Check for trailing commas
- Ensure proper encoding (UTF-8)

### Export fails
- Check write permissions on destination folder
- Install optional dependencies (openpyxl for Excel)
- Ensure enough disk space

### Slow performance
- Reduce page size for large tables
- Use indexed columns in queries
- Close unused database tabs
- Use pagination for large JSON files

## License

Part of Smart Search Pro - see main project LICENSE file.

## Contributing

See main project CONTRIBUTING.md for guidelines.

## Changelog

### Version 1.0.0 (2025-12-12)
- Initial release
- Database viewer with full SQLite support
- JSON viewer with tree and table views
- Data viewer factory with auto-detection
- UI integration components
- Comprehensive error handling
