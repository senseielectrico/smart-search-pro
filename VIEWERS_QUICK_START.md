# Data Viewers - Quick Start Guide

**5-Minute Guide to Using the Database and JSON Viewers**

## Installation Check

The viewers are already included in Smart Search Pro. No additional installation needed!

Optional for full features:
```bash
pip install openpyxl  # For Excel export
pip install PyYAML    # For YAML files
```

## Quick Test (30 seconds)

```bash
cd C:\Users\ramos\.local\bin\smart_search
python test_viewers.py
```

This opens a test app with:
- Sample SQLite database (users, posts, tags)
- Sample JSON file (nested data)
- All viewers ready to explore

## Usage Patterns

### Pattern 1: Open Any Database

```python
from viewers.database_viewer import DatabaseViewer
from PyQt6.QtWidgets import QApplication

app = QApplication([])
viewer = DatabaseViewer()
viewer.open_database("mydata.db")
viewer.show()
app.exec()
```

**What you get:**
- Browse all tables
- View schemas
- Execute SQL queries
- Export to CSV/Excel

### Pattern 2: Open Any JSON File

```python
from viewers.json_viewer import JSONViewer
from PyQt6.QtWidgets import QApplication

app = QApplication([])
viewer = JSONViewer()
viewer.open_file("config.json")
viewer.show()
app.exec()
```

**What you get:**
- Interactive tree view
- Edit and save
- Convert arrays to tables
- Export to CSV

### Pattern 3: Auto-Detect File Type

```python
from viewers.data_viewer_factory import DataViewerFactory

factory = DataViewerFactory()
viewer = factory.create_viewer("unknown_file.???")
if viewer:
    viewer.show()
```

**Supports:**
- .db, .sqlite, .sqlite3 → Database Viewer
- .json → JSON Viewer
- .csv, .tsv → CSV Viewer
- .xml → XML Viewer
- .yaml, .yml → YAML Viewer
- .ini, .conf → INI Viewer

### Pattern 4: Add to Your Qt Application

```python
# In your main window
from ui.database_panel import DatabasePanel

# Add as tab
db_panel = DatabasePanel()
self.tabs.addTab(db_panel, "Database Explorer")

# Open database programmatically
db_panel.open_database("data.db")

# Connect to signals
db_panel.database_opened.connect(self.on_db_opened)
db_panel.table_selected.connect(self.on_table_selected)
```

## Common Tasks

### Task: View Database Schema

1. Open database
2. Click table in left panel
3. Click "Schema" tab
4. See columns, types, indexes, foreign keys

### Task: Execute SQL Query

1. Open database
2. Click "Query" tab
3. Type query (or select from history)
4. Press Ctrl+Enter or click "Execute"
5. View results in table below

### Task: Export Table to CSV

1. Open database
2. Select table
3. Click "Data" tab
4. Click "Export Table"
5. Choose CSV or Excel format
6. Save file

### Task: Edit JSON File

1. Open JSON file
2. Click "Raw JSON" tab
3. Edit the text
4. Click "Format" to prettify
5. Click "Validate" to check syntax
6. Click "Save" to save changes

### Task: Navigate JSON Structure

1. Open JSON file
2. Click "Tree View" tab
3. Expand/collapse nodes
4. Right-click → Copy Path
5. Right-click → Copy Value

### Task: Search Across Database Tables

1. Open database
2. Click "Search" tab
3. Enter search term
4. Check "Case sensitive" if needed
5. Click "Search All Tables"
6. View matches with table/column/value

## Keyboard Shortcuts

### Database Viewer
- `Ctrl+Enter` - Execute query
- `F5` - Refresh

### JSON Viewer
- `Ctrl+S` - Save file
- `Ctrl+Shift+F` - Format JSON

## Integration Examples

### Add to Menu Bar

```python
# In main window
def create_menus(self):
    tools_menu = self.menuBar().addMenu("Tools")

    db_action = QAction("Database Viewer...", self)
    db_action.triggered.connect(self.open_db_viewer)
    tools_menu.addAction(db_action)

def open_db_viewer(self):
    from PyQt6.QtWidgets import QFileDialog
    from viewers.database_viewer import DatabaseViewer

    path, _ = QFileDialog.getOpenFileName(
        self, "Open Database", "",
        "SQLite Database (*.db *.sqlite *.sqlite3);;All Files (*.*)"
    )

    if path:
        viewer = DatabaseViewer()
        viewer.open_database(path)
        viewer.show()
        # Store reference to prevent garbage collection
        if not hasattr(self, '_viewers'):
            self._viewers = []
        self._viewers.append(viewer)
```

### Add to Context Menu

```python
# In results panel
def show_context_menu(self, position):
    menu = QMenu(self)

    # Get selected file
    file_path = self.get_selected_file()

    # Add appropriate viewer action
    if file_path.endswith('.db'):
        action = QAction("View in Database Viewer", self)
        action.triggered.connect(lambda: self.open_db_viewer(file_path))
        menu.addAction(action)

    elif file_path.endswith('.json'):
        action = QAction("View in JSON Viewer", self)
        action.triggered.connect(lambda: self.open_json_viewer(file_path))
        menu.addAction(action)

    menu.exec(self.viewport().mapToGlobal(position))
```

## File Locations

```
C:\Users\ramos\.local\bin\smart_search\
├── viewers/
│   ├── __init__.py
│   ├── database_viewer.py      # SQLite viewer
│   ├── json_viewer.py          # JSON viewer
│   ├── data_viewer_factory.py  # Auto-detect factory
│   └── README.md               # Full documentation
│
├── ui/
│   ├── database_panel.py       # For integration
│   └── json_tree_widget.py     # Reusable widget
│
├── test_viewers.py             # Test application
├── VIEWERS_INTEGRATION_GUIDE.md    # Integration examples
├── VIEWERS_IMPLEMENTATION_SUMMARY.md  # Technical details
└── VIEWERS_QUICK_START.md      # This file
```

## Sample Queries (for test database)

Copy-paste these into the query editor:

**All active users:**
```sql
SELECT * FROM users WHERE active = 1
```

**Posts with author names:**
```sql
SELECT users.username, posts.title, posts.views
FROM posts
JOIN users ON posts.user_id = users.id
ORDER BY posts.views DESC
```

**User statistics:**
```sql
SELECT
    users.username,
    COUNT(posts.id) as post_count,
    SUM(posts.views) as total_views
FROM users
LEFT JOIN posts ON users.id = posts.user_id
GROUP BY users.id
ORDER BY total_views DESC
```

**Published posts only:**
```sql
SELECT title, views FROM posts
WHERE published = 1
ORDER BY created_at DESC
```

## Troubleshooting

**Database won't open**
- Check file exists: `os.path.exists(db_path)`
- Check it's SQLite: Try opening in SQLite browser
- Check permissions: Run as administrator if needed

**JSON parse error**
- Validate syntax at jsonlint.com
- Check for trailing commas
- Ensure UTF-8 encoding

**Viewer closes immediately**
- Keep reference to viewer: `self._viewers.append(viewer)`
- Don't let viewer go out of scope
- Check console for errors

**Slow with large files**
- Use pagination for databases (default: 1000 rows)
- Consider file size limits for JSON (>10MB may be slow)
- Use search instead of browsing entire database

## Next Steps

1. **Test it**: `python test_viewers.py`

2. **Read more**:
   - Full features: `viewers/README.md`
   - Integration: `VIEWERS_INTEGRATION_GUIDE.md`
   - Technical: `VIEWERS_IMPLEMENTATION_SUMMARY.md`

3. **Integrate**:
   - Add to menu bar
   - Add to context menu
   - Add as tab in main window
   - Add to preview panel

4. **Customize**:
   - Add custom viewers
   - Register new file types
   - Modify UI styling
   - Add keyboard shortcuts

## Support

For detailed documentation, see:
- `viewers/README.md` - Complete feature list and API
- `VIEWERS_INTEGRATION_GUIDE.md` - Integration examples
- `test_viewers.py` - Working code examples

Happy viewing!
