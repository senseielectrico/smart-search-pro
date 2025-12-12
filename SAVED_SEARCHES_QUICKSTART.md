# Saved Searches & Favorites - Quick Start Guide

Get up and running with saved searches, favorites, and smart collections in 5 minutes.

## Quick Test

Run the test suite to verify everything works:

```bash
python test_saved_searches_favorites.py
```

Expected output: `SUCCESS: ALL TESTS PASSED!`

## Basic Usage

### 1. Saved Searches - Save Your Complex Searches

```python
from search.saved_searches import SavedSearch, SavedSearchManager

# Create manager
manager = SavedSearchManager()

# Save a search
search = SavedSearch(
    name="Large Python Files",
    query="*.py",
    category="Development",
    file_types=['.py'],
    min_size=1024 * 1024,  # 1MB
    sort_order="size",
    ascending=False,
    shortcut_key=1  # Assign Ctrl+1
)

search_id = manager.save(search)

# Execute later
search = manager.get_by_shortcut(1)  # Get by Ctrl+1
# Apply search.query, search.filters, etc.
```

### 2. Favorites - Star Your Important Files

```python
from search.favorites_manager import FavoritesManager

# Create manager
manager = FavoritesManager()

# Add to favorites
manager.add(
    path="/path/to/important/file.txt",
    rating=5,  # 5 stars
    tags=['important', 'work'],
    category='Projects',
    notes='Critical project file'
)

# Check if favorited
if manager.is_favorite("/path/to/file.txt"):
    print("File is favorited!")

# Get top-rated files
top_files = manager.get_top_rated(limit=10, min_rating=4)
```

### 3. Smart Collections - Auto-Updating File Groups

```python
from search.smart_collections import (
    SmartCollection, SmartCollectionsManager,
    Condition, ConditionType
)

# Create manager
manager = SmartCollectionsManager()

# Create collection
collection = SmartCollection(
    name="Recent Large Files",
    conditions=[
        Condition(ConditionType.SIZE_GREATER, 100 * 1024 * 1024),  # >100MB
        Condition(ConditionType.MODIFIED_WITHIN, 7)  # Last 7 days
    ],
    match_all=True  # AND logic
)

manager.save(collection)

# Evaluate against files
files = [
    {'path': '/file1.zip', 'size': 200*1024*1024, 'modified': '2024-01-10T00:00:00'},
    {'path': '/file2.txt', 'size': 1024, 'modified': '2024-01-10T00:00:00'}
]

matches = manager.evaluate(collection.id, files)
# Returns: [first file only]
```

## UI Integration

### Add to Main Window

```python
from ui.saved_searches_panel import SavedSearchesPanel
from ui.favorites_panel import FavoritesPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Add panels to splitter
        splitter = QSplitter()
        splitter.addWidget(SavedSearchesPanel())  # Left
        splitter.addWidget(your_search_panel)     # Center
        splitter.addWidget(FavoritesPanel())      # Right

        # Connect signals
        self.saved_searches.search_executed.connect(self.run_search)
        self.favorites.favorite_opened.connect(self.open_file)
```

### Keyboard Shortcuts

```python
# In your main window __init__:

# Saved searches (Ctrl+1 through Ctrl+9)
for i in range(1, 10):
    QShortcut(QKeySequence(f"Ctrl+{i}"), self).activated.connect(
        lambda key=i: self.execute_saved_search(key)
    )

# Toggle favorite (F key)
QShortcut(QKeySequence("F"), self).activated.connect(
    self.toggle_favorite
)

# Save search (Ctrl+S)
QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(
    self.save_current_search
)
```

## File Structure

```
smart_search/
├── search/
│   ├── saved_searches.py        # Saved searches manager
│   ├── favorites_manager.py     # Favorites manager
│   └── smart_collections.py     # Smart collections manager
│
├── ui/
│   ├── saved_searches_panel.py  # Saved searches sidebar
│   ├── favorites_panel.py       # Favorites panel
│   ├── save_search_dialog.py    # Save search dialog
│   └── collection_editor.py     # Collection editor dialog
│
├── test_saved_searches_favorites.py    # Test suite
├── integration_example_saved_favorites.py  # Full example
└── SAVED_SEARCHES_FAVORITES_GUIDE.md   # Complete documentation
```

## Database Files

Three SQLite databases are created automatically:

- `~/.smart_search_saved.db` - Saved searches
- `~/.smart_search_favorites.db` - Favorites
- `~/.smart_search_collections.db` - Smart collections

## Common Patterns

### Pattern 1: Save Current Search

```python
def save_current_search(self):
    from ui.save_search_dialog import SaveSearchDialog

    params = {
        'query': self.search_input.text(),
        'file_types': self.get_selected_file_types(),
        'min_size': self.min_size_spin.value(),
        # ... other parameters
    }

    dialog = SaveSearchDialog()
    dialog.set_search_params(params)

    if dialog.exec():
        self.saved_searches_panel.refresh()
```

### Pattern 2: Execute Saved Search

```python
def execute_saved_search(self, search):
    # Apply search parameters to UI
    self.search_input.setText(search.query)
    self.file_types_combo.setCurrentText(search.file_types)

    # Run search
    results = self.perform_search()

    # Update statistics
    self.saved_searches_panel.update_search_results(
        search.id, len(results)
    )
```

### Pattern 3: Toggle Favorite

```python
def toggle_favorite(self):
    file_path = self.get_selected_file()

    if self.favorites_panel.is_favorite(file_path):
        self.favorites_panel.remove_favorite(file_path)
    else:
        self.favorites_panel.add_favorite(file_path, rating=3)
```

### Pattern 4: Smart Collection with Preview

```python
def show_collection_preview(self, collection):
    # Get all files from current search results
    files = self.get_all_search_results()

    # Evaluate collection
    matches = self.collections_manager.evaluate(collection.id, files)

    # Display matches
    self.preview_panel.show_results(matches)
```

## Example: Complete Integration

See `integration_example_saved_favorites.py` for a complete working example with:
- All panels integrated
- Full keyboard shortcuts
- Context menus
- Import/export functionality
- State persistence

Run it:

```bash
python integration_example_saved_favorites.py
```

## Troubleshooting

### Issue: Database locked

**Solution**: Close all database connections properly

```python
import gc
gc.collect()  # Force garbage collection
```

### Issue: Can't find modules

**Solution**: Add to Python path

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'search'))
sys.path.insert(0, str(Path(__file__).parent / 'ui'))
```

### Issue: Tests fail

**Solution**: Run with full output

```bash
python test_saved_searches_favorites.py -v
```

Check database files in `%TEMP%` directory.

## Next Steps

1. **Read full documentation**: `SAVED_SEARCHES_FAVORITES_GUIDE.md`
2. **Run integration example**: `integration_example_saved_favorites.py`
3. **Customize for your needs**: Modify UI panels, add custom icons, etc.
4. **Import/Export**: Backup your data regularly

## Support

For issues or questions:
1. Check test suite passes
2. Review full documentation
3. Examine integration example
4. Check database files with SQLite browser

## Performance Tips

- Use categories to organize searches (faster filtering)
- Set reasonable `max_results` for collections
- Periodically clean old favorites (removed files)
- Export data for backup before major changes

## Advanced Features

### Custom Collection Rules

```python
# Complex AND/OR logic
collection = SmartCollection(
    name="Important Documents",
    conditions=[
        Condition(ConditionType.EXTENSION_IN, ['doc', 'pdf']),
        Condition(ConditionType.SIZE_GREATER, 1024*1024, LogicOperator.AND),
        Condition(ConditionType.MODIFIED_WITHIN, 30, LogicOperator.AND),
        Condition(ConditionType.PATH_CONTAINS, 'important', LogicOperator.OR)
    ],
    match_all=False  # OR between main conditions
)
```

### Batch Operations

```python
# Add multiple files to favorites
for file in file_list:
    manager.add(file, rating=3, category='Batch Import')

# Export multiple saved searches
manager.export_to_json('backup.json', search_ids=[1, 2, 3])
```

### Statistics and Analytics

```python
# Saved searches statistics
stats = saved_manager.get_statistics()
print(f"Most used: {stats['most_used'][0]['name']}")

# Favorites statistics
fav_stats = favorites_manager.get_statistics()
print(f"Average rating: {fav_stats['average_rating']}")
```

## License

Part of Smart Search Pro. Same license applies.
