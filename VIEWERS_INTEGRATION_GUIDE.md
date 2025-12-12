# Data Viewers Integration Guide

Guide for integrating database and JSON viewers into Smart Search Pro.

## Quick Start

### 1. Test the Viewers

Run the test suite to see all viewers in action:

```bash
cd C:\Users\ramos\.local\bin\smart_search
python test_viewers.py
```

This will:
- Create sample SQLite database with users, posts, and tags tables
- Create sample JSON file with nested data
- Open all viewers in a tabbed interface
- Demonstrate all features

### 2. Standalone Usage

#### Open a Database

```bash
python -m viewers.database_viewer path/to/database.db
```

#### Open a JSON File

```bash
python -m viewers.json_viewer path/to/data.json
```

#### Auto-detect and Open

```bash
python -m viewers.data_viewer_factory path/to/file
```

## Integration into Main Window

### Option 1: Add as Menu Items

Add to `ui/main_window.py`:

```python
def _create_menus(self):
    # ... existing menu code ...

    # Tools menu
    tools_menu = self.menuBar().addMenu("Tools")

    # Database viewer action
    db_viewer_action = QAction("Database Viewer...", self)
    db_viewer_action.triggered.connect(self.open_database_viewer)
    tools_menu.addAction(db_viewer_action)

    # JSON viewer action
    json_viewer_action = QAction("JSON Viewer...", self)
    json_viewer_action.triggered.connect(self.open_json_viewer)
    tools_menu.addAction(json_viewer_action)

def open_database_viewer(self):
    """Open database viewer dialog"""
    from PyQt6.QtWidgets import QFileDialog
    from viewers.database_viewer import DatabaseViewer

    file_path, _ = QFileDialog.getOpenFileName(
        self,
        "Open SQLite Database",
        "",
        "SQLite Database (*.db *.sqlite *.sqlite3);;All Files (*.*)"
    )

    if file_path:
        viewer = DatabaseViewer()
        viewer.open_database(file_path)
        viewer.resize(1200, 800)
        viewer.show()
        # Keep reference to prevent garbage collection
        if not hasattr(self, '_viewers'):
            self._viewers = []
        self._viewers.append(viewer)

def open_json_viewer(self):
    """Open JSON viewer dialog"""
    from PyQt6.QtWidgets import QFileDialog
    from viewers.json_viewer import JSONViewer

    file_path, _ = QFileDialog.getOpenFileName(
        self,
        "Open JSON File",
        "",
        "JSON Files (*.json);;All Files (*.*)"
    )

    if file_path:
        viewer = JSONViewer()
        viewer.open_file(file_path)
        viewer.resize(1000, 700)
        viewer.show()
        # Keep reference
        if not hasattr(self, '_viewers'):
            self._viewers = []
        self._viewers.append(viewer)
```

### Option 2: Add as Tabs

Add to `ui/main_window.py` tabs:

```python
def _init_ui(self):
    # ... existing UI code ...

    # Add database panel tab
    from ui.database_panel import DatabasePanel
    self.db_panel = DatabasePanel()
    self.main_tabs.addTab(self.db_panel, "Database Explorer")

    # Connect signals
    self.db_panel.database_opened.connect(self._on_database_opened)
    self.db_panel.table_selected.connect(self._on_table_selected)

def _on_database_opened(self, db_path: str):
    """Handle database opened"""
    self.statusBar().showMessage(f"Database opened: {db_path}", 3000)

def _on_table_selected(self, table_name: str):
    """Handle table selected"""
    self.statusBar().showMessage(f"Table: {table_name}", 3000)
```

### Option 3: Context Menu Integration

Add to `ui/results_panel.py` context menu:

```python
def _create_context_menu(self, position):
    """Create context menu for results"""
    # ... existing code ...

    menu = QMenu(self)

    # Get selected file
    selected = self.get_selected_files()
    if not selected:
        return

    file_path = selected[0]
    ext = os.path.splitext(file_path)[1].lower()

    # Add viewer actions based on file type
    if ext in ['.db', '.sqlite', '.sqlite3']:
        view_db_action = QAction("View in Database Viewer", self)
        view_db_action.triggered.connect(lambda: self._open_in_db_viewer(file_path))
        menu.addAction(view_db_action)

    elif ext == '.json':
        view_json_action = QAction("View in JSON Viewer", self)
        view_json_action.triggered.connect(lambda: self._open_in_json_viewer(file_path))
        menu.addAction(view_json_action)

    # ... rest of menu ...

    menu.exec(self.viewport().mapToGlobal(position))

def _open_in_db_viewer(self, file_path: str):
    """Open file in database viewer"""
    from viewers.database_viewer import DatabaseViewer

    viewer = DatabaseViewer()
    viewer.open_database(file_path)
    viewer.resize(1200, 800)
    viewer.show()

    # Store reference in main window
    main_window = self.window()
    if not hasattr(main_window, '_viewers'):
        main_window._viewers = []
    main_window._viewers.append(viewer)

def _open_in_json_viewer(self, file_path: str):
    """Open file in JSON viewer"""
    from viewers.json_viewer import JSONViewer

    viewer = JSONViewer()
    viewer.open_file(file_path)
    viewer.resize(1000, 700)
    viewer.show()

    # Store reference
    main_window = self.window()
    if not hasattr(main_window, '_viewers'):
        main_window._viewers = []
    main_window._viewers.append(viewer)
```

### Option 4: Preview Panel Integration

Add to `ui/preview_panel.py` for quick preview:

```python
def _preview_database(self, file_path: str):
    """Preview database file"""
    from viewers.database_viewer import SQLiteConnection

    try:
        connection = SQLiteConnection(file_path)
        tables = connection.get_tables()

        # Show table list
        preview_text = f"Database: {os.path.basename(file_path)}\n\n"
        preview_text += "Tables:\n"

        for table in tables:
            row_count = connection.get_table_row_count(table)
            preview_text += f"  • {table} ({row_count} rows)\n"

        self.preview_text.setText(preview_text)

        # Add button to open full viewer
        btn = QPushButton("Open in Database Viewer")
        btn.clicked.connect(lambda: self._open_full_db_viewer(file_path))
        self.preview_layout.addWidget(btn)

        connection.close()

    except Exception as e:
        self.preview_text.setText(f"Error previewing database: {e}")

def _preview_json(self, file_path: str):
    """Preview JSON file"""
    from ui.json_tree_widget import JSONTreeWidget

    try:
        # Use JSON tree widget for preview
        tree = JSONTreeWidget()
        tree.load_json_file(file_path)

        # Add to preview area
        self.preview_layout.addWidget(tree)

        # Add button to open full viewer
        btn = QPushButton("Open in JSON Viewer")
        btn.clicked.connect(lambda: self._open_full_json_viewer(file_path))
        self.preview_layout.addWidget(btn)

    except Exception as e:
        self.preview_text.setText(f"Error previewing JSON: {e}")
```

## Advanced Integration

### Export Search Results to Database

```python
def export_results_to_database(self, results: List[SearchResult], db_path: str):
    """Export search results to SQLite database"""
    import sqlite3

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            path TEXT,
            size INTEGER,
            modified TEXT,
            category TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Insert results
    for result in results:
        cursor.execute('''
            INSERT INTO search_results (name, path, size, modified, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            result.name,
            result.path,
            result.size,
            result.modified.isoformat() if result.modified else None,
            result.category.value
        ))

    conn.commit()
    conn.close()

    # Open in viewer
    from viewers.database_viewer import DatabaseViewer
    viewer = DatabaseViewer()
    viewer.open_database(db_path)
    viewer.show()
```

### Export Search Results to JSON

```python
def export_results_to_json(self, results: List[SearchResult], json_path: str):
    """Export search results to JSON"""
    import json

    data = {
        "export_info": {
            "timestamp": datetime.now().isoformat(),
            "total_results": len(results),
            "version": "1.0.0"
        },
        "results": [
            {
                "name": r.name,
                "path": r.path,
                "size": r.size,
                "modified": r.modified.isoformat() if r.modified else None,
                "category": r.category.value
            }
            for r in results
        ]
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Open in viewer
    from viewers.json_viewer import JSONViewer
    viewer = JSONViewer()
    viewer.open_file(json_path)
    viewer.show()
```

### Auto-Open from Search Results

```python
def handle_file_double_click(self, file_path: str):
    """Handle double-click on search result"""
    from viewers.data_viewer_factory import DataViewerFactory

    # Check if file can be viewed
    factory = DataViewerFactory()
    viewer_type = factory.detect_type(file_path)

    if viewer_type != ViewerType.UNKNOWN:
        # Open in appropriate viewer
        viewer = factory.create_viewer(file_path)
        if viewer:
            viewer.resize(1200, 800)
            viewer.show()

            # Store reference
            if not hasattr(self, '_viewers'):
                self._viewers = []
            self._viewers.append(viewer)
    else:
        # Open with default application
        from backend import FileOperations
        FileOperations.open_file(file_path)
```

## Configuration

Add to `config.py`:

```python
class ViewerConfig:
    """Configuration for data viewers"""

    # Database viewer
    DB_DEFAULT_PAGE_SIZE = 1000
    DB_MAX_QUERY_HISTORY = 50
    DB_MAX_RECENT_DATABASES = 10
    DB_AUTO_REFRESH = True

    # JSON viewer
    JSON_DEFAULT_INDENT = 2
    JSON_MAX_PREVIEW_LENGTH = 50
    JSON_AUTO_FORMAT = True
    JSON_VALIDATE_ON_EDIT = True

    # Factory
    VIEWER_AUTO_DETECT = True
    VIEWER_REMEMBER_SIZE = True
    VIEWER_REMEMBER_POSITION = True

    @classmethod
    def save(cls):
        """Save configuration to file"""
        config = {
            'db_page_size': cls.DB_DEFAULT_PAGE_SIZE,
            'db_max_history': cls.DB_MAX_QUERY_HISTORY,
            'json_indent': cls.JSON_DEFAULT_INDENT,
            'auto_detect': cls.VIEWER_AUTO_DETECT,
        }

        import json
        with open('viewer_config.json', 'w') as f:
            json.dump(config, f, indent=2)

    @classmethod
    def load(cls):
        """Load configuration from file"""
        try:
            import json
            with open('viewer_config.json', 'r') as f:
                config = json.load(f)

            cls.DB_DEFAULT_PAGE_SIZE = config.get('db_page_size', 1000)
            cls.DB_MAX_QUERY_HISTORY = config.get('db_max_history', 50)
            cls.JSON_DEFAULT_INDENT = config.get('json_indent', 2)
            cls.VIEWER_AUTO_DETECT = config.get('auto_detect', True)
        except FileNotFoundError:
            pass
```

## Keyboard Shortcuts

Add to hotkey manager:

```python
# In system/hotkeys.py or similar

# Database viewer shortcuts
self.register_hotkey(
    VirtualKeys.F4,
    ModifierKeys.CTRL,
    lambda: self.main_window.open_database_viewer()
)

# JSON viewer shortcuts
self.register_hotkey(
    VirtualKeys.J,
    ModifierKeys.CTRL | ModifierKeys.SHIFT,
    lambda: self.main_window.open_json_viewer()
)

# Quick preview (if file selected)
self.register_hotkey(
    VirtualKeys.SPACE,
    ModifierKeys.NONE,
    lambda: self.main_window.preview_selected_file()
)
```

## Testing Integration

Create test file `test_viewers_integration.py`:

```python
import pytest
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

@pytest.fixture
def app():
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def main_window(app):
    window = MainWindow()
    return window

def test_database_viewer_menu(main_window):
    """Test database viewer menu integration"""
    # Find menu action
    actions = main_window.menuBar().actions()
    tools_menu = None
    for action in actions:
        if action.text() == "Tools":
            tools_menu = action.menu()
            break

    assert tools_menu is not None

    # Find database viewer action
    db_action = None
    for action in tools_menu.actions():
        if "Database" in action.text():
            db_action = action
            break

    assert db_action is not None

def test_open_database_viewer(main_window, tmp_path):
    """Test opening database viewer"""
    import sqlite3

    # Create temp database
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
    conn.close()

    # Open in viewer
    from viewers.database_viewer import DatabaseViewer
    viewer = DatabaseViewer()
    viewer.open_database(str(db_path))

    assert viewer.current_db_path == str(db_path)
    assert viewer.db_connection is not None

def test_json_tree_widget(main_window):
    """Test JSON tree widget"""
    from ui.json_tree_widget import JSONTreeWidget

    tree = JSONTreeWidget()
    data = {"test": "value", "array": [1, 2, 3]}
    tree.load_json(data)

    assert tree.model.root_node is not None
    assert len(tree.model.root_node.children) == 2
```

## Performance Tips

1. **Lazy Loading**: Load only visible data
   ```python
   # In database viewer
   INITIAL_ROW_LIMIT = 100
   MAX_ROW_LIMIT = 10000
   ```

2. **Caching**: Cache frequently accessed data
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=10)
   def get_table_schema(table_name: str):
       # ...
   ```

3. **Background Loading**: Use threads for large operations
   ```python
   from PyQt6.QtCore import QThread

   class LoadDataThread(QThread):
       # ...
   ```

4. **Progressive Rendering**: Show results as they arrive
   ```python
   def on_result(result):
       self.table.add_row(result)
       QApplication.processEvents()  # Keep UI responsive
   ```

## Troubleshooting

### Viewers not appearing in menu
- Check import paths
- Ensure viewers module is in Python path
- Verify PyQt6 is installed

### Database won't open
- Check SQLite version compatibility
- Verify file permissions
- Ensure file is not locked

### JSON parse errors
- Validate JSON syntax
- Check file encoding (should be UTF-8)
- Handle large files with streaming parser

### Memory issues with large files
- Implement pagination
- Use lazy loading
- Consider file size limits

## Best Practices

1. **Always store viewer references** to prevent garbage collection
2. **Use factory pattern** for auto-detection
3. **Implement error handling** for all file operations
4. **Provide user feedback** during long operations
5. **Clean up resources** on window close
6. **Test with various file sizes** and formats
7. **Document integration points** clearly

## Next Steps

1. Test the viewers with `python test_viewers.py`
2. Choose integration option (menu, tabs, context menu, or all)
3. Add to main window following examples above
4. Test with real data
5. Gather user feedback
6. Iterate and improve

## Support

For issues or questions:
- Check `viewers/README.md` for detailed documentation
- Review `test_viewers.py` for examples
- See individual viewer files for API reference

Happy integrating!
