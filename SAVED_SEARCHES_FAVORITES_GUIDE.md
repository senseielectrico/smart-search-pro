# Saved Searches & Favorites System

Complete guide to the saved searches, favorites, and smart collections system in Smart Search Pro.

## Overview

This system provides three powerful features:

1. **Saved Searches** - Save and quickly re-execute complex searches
2. **Favorites** - Star-rate and organize your most important files
3. **Smart Collections** - Dynamic, rule-based collections that auto-update

## Features

### Saved Searches

- Save search queries with all parameters (filters, sort, paths)
- Categorize searches for organization
- Assign keyboard shortcuts (Ctrl+1 through Ctrl+9)
- Quick execute from sidebar
- Track usage statistics (run count, last results)
- Import/export saved searches
- Search within saved searches

### Favorites

- Star rating system (0-5 stars)
- Custom tags for organization
- Categories/collections
- Quick access list
- Recent favorites tracking
- Search and filter favorites
- Notes and metadata
- Import/export favorites

### Smart Collections

- Auto-updating collections based on rules
- Multiple condition types (name, size, date, extension, etc.)
- AND/OR logic for complex rules
- Predefined collections (Large Files, Recent Documents, etc.)
- Visual rule builder
- Live preview of matching files

## Installation

The system is integrated into Smart Search Pro. No additional installation required.

### Database Files

Three SQLite databases are created in your home directory:

```
~/.smart_search_saved.db         # Saved searches
~/.smart_search_favorites.db     # Favorites
~/.smart_search_collections.db   # Smart collections
```

## Usage

### Saved Searches

#### Creating a Saved Search

1. Perform a search with desired filters
2. Click "Save Search" button or press Ctrl+S
3. Enter name and optional description
4. Choose category and visual settings
5. Optionally assign keyboard shortcut
6. Click Save

#### Executing a Saved Search

- Double-click in saved searches panel
- Press assigned keyboard shortcut (Ctrl+1-9)
- Right-click and select "Run Search"

#### Managing Saved Searches

- **Edit**: Right-click → Edit
- **Duplicate**: Right-click → Duplicate
- **Delete**: Right-click → Delete
- **Assign Shortcut**: Right-click → Assign Keyboard Shortcut

### Favorites

#### Adding to Favorites

1. Right-click file in results
2. Select "Add to Favorites" or press F
3. Set rating, tags, and category
4. Add optional notes

#### Quick Star Rating

- Right-click → Set Rating → Select stars
- Or use favorites panel for full editing

#### Managing Favorites

The favorites panel provides:

- **Search**: Filter by name, path, or notes
- **Filter**: By category, tag, or minimum rating
- **Sort**: By name, rating, date added, or last accessed
- **Edit**: Click Edit button for full details
- **Remove**: Remove from favorites (file not deleted)

### Smart Collections

#### Using Predefined Collections

Default collections are created automatically:

- **Large Files (>1GB)**: Files over 1GB
- **Recent Documents**: Documents modified in last 7 days
- **Images**: All image files
- **Videos**: All video files
- **Today's Files**: Files modified today

#### Creating Custom Collections

1. Click "New Collection" in collections panel
2. Enter name and description
3. Add conditions:
   - Click "Add Condition"
   - Select condition type
   - Enter value
   - Choose AND/OR operator
4. Set match mode (All/Any conditions)
5. Configure sort and limit options
6. Click Save

#### Condition Types

**Name/Path**:
- Name Contains
- Name Starts With
- Name Ends With
- Name Matches (regex)
- Path Contains
- Path In (specific directories)

**File Type**:
- Extension Is (single)
- Extension In (multiple)
- Is Directory
- Is File

**Size**:
- Size Greater Than
- Size Less Than
- Size Between

**Date**:
- Modified After
- Modified Before
- Modified Within (last N days)
- Created After/Before
- Accessed After

## Integration with Main UI

### Toolbar Integration

Add these buttons to the main toolbar:

```python
# Save current search
save_search_btn = QPushButton("Save Search")
save_search_btn.setIcon(QIcon.fromTheme("document-save"))
save_search_btn.clicked.connect(self.on_save_search)

# Toggle favorites panel
favorites_btn = QPushButton("Favorites")
favorites_btn.setCheckable(True)
favorites_btn.clicked.connect(self.toggle_favorites_panel)

# Collections
collections_btn = QPushButton("Collections")
collections_btn.clicked.connect(self.show_collections)
```

### Keyboard Shortcuts

```python
# Saved search shortcuts (Ctrl+1 through Ctrl+9)
for i in range(1, 10):
    shortcut = QShortcut(QKeySequence(f"Ctrl+{i}"), self)
    shortcut.activated.connect(lambda key=i: self.execute_saved_search(key))

# Toggle favorite (F key)
QShortcut(QKeySequence("F"), self).activated.connect(self.toggle_favorite)

# Save search (Ctrl+S)
QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.save_current_search)
```

### Context Menu Integration

Add to results panel context menu:

```python
# Add to favorites
if not favorites_manager.is_favorite(file_path):
    add_fav_action = menu.addAction("Add to Favorites")
    add_fav_action.triggered.connect(lambda: self.add_to_favorites(file_path))
else:
    remove_fav_action = menu.addAction("Remove from Favorites")
    remove_fav_action.triggered.connect(lambda: self.remove_from_favorites(file_path))

# Quick rating
rating_menu = menu.addMenu("Set Rating")
for i in range(6):
    stars = "★" * i if i > 0 else "No Rating"
    action = rating_menu.addAction(f"{stars}")
    action.triggered.connect(lambda checked, r=i: self.set_rating(file_path, r))
```

## API Reference

### SavedSearchManager

```python
from search.saved_searches import SavedSearch, SavedSearchManager

manager = SavedSearchManager()

# Create search
search = SavedSearch(
    name="My Search",
    query="*.py",
    category="Development",
    shortcut_key=1
)

# Save
search_id = manager.save(search)

# Retrieve
search = manager.get(search_id)
search = manager.get_by_name("My Search")
search = manager.get_by_shortcut(1)

# List
all_searches = manager.get_all()
searches = manager.get_all(category="Development")

# Search
results = manager.search("python")

# Update stats
manager.update_run_stats(search_id, result_count=42)

# Export/Import
manager.export_to_json("searches.json")
manager.import_from_json("searches.json", merge=True)

# Delete
manager.delete(search_id)
```

### FavoritesManager

```python
from search.favorites_manager import Favorite, FavoritesManager

manager = FavoritesManager()

# Add favorite
fav_id = manager.add(
    path="/path/to/file",
    rating=5,
    tags=['important', 'work'],
    category='Projects',
    notes='Important project file'
)

# Check if favorite
is_fav = manager.is_favorite("/path/to/file")

# Get favorite
favorite = manager.get(fav_id)
favorite = manager.get_by_path("/path/to/file")

# Update rating
manager.update_rating(fav_id, 4)

# Manage tags
manager.add_tag(fav_id, 'urgent')
manager.remove_tag(fav_id, 'work')

# Filter and sort
favorites = manager.get_all(
    category="Projects",
    min_rating=4,
    tags=['important'],
    sort_by='rating',
    ascending=False
)

# Get recent/top-rated
recent = manager.get_recent(limit=10)
top_rated = manager.get_top_rated(limit=10, min_rating=4)

# Search
results = manager.search('project')

# Update access
manager.update_access(fav_id)

# Delete
manager.delete(fav_id)
```

### SmartCollectionsManager

```python
from search.smart_collections import (
    SmartCollection, SmartCollectionsManager,
    Condition, ConditionType
)

manager = SmartCollectionsManager()

# Create collection
collection = SmartCollection(
    name="Large Python Files",
    description="Python files over 10MB",
    conditions=[
        Condition(ConditionType.EXTENSION_IS, 'py'),
        Condition(ConditionType.SIZE_GREATER, 10 * 1024 * 1024)
    ],
    match_all=True,
    sort_by='size',
    ascending=False
)

# Save
coll_id = manager.save(collection)

# Retrieve
collection = manager.get(coll_id)
collection = manager.get_by_name("Large Python Files")

# Evaluate against files
file_info = {
    'path': '/code/large.py',
    'size': 15 * 1024 * 1024,
    'modified': '2024-01-01T00:00:00'
}

matches = collection.matches(file_info)

# Evaluate collection against list
files = [file_info, ...]
results = manager.evaluate(coll_id, files)

# Delete
manager.delete(coll_id)
```

## Example: Full Integration

```python
from PyQt6.QtWidgets import QMainWindow, QSplitter
from ui.saved_searches_panel import SavedSearchesPanel
from ui.favorites_panel import FavoritesPanel
from ui.save_search_dialog import SaveSearchDialog
from ui.collection_editor import CollectionEditor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create panels
        self.saved_searches_panel = SavedSearchesPanel()
        self.favorites_panel = FavoritesPanel()

        # Connect signals
        self.saved_searches_panel.search_executed.connect(self.execute_saved_search)
        self.saved_searches_panel.search_edited.connect(self.edit_saved_search)
        self.favorites_panel.favorite_opened.connect(self.open_file)

        # Add to layout
        splitter = QSplitter()
        splitter.addWidget(self.saved_searches_panel)
        splitter.addWidget(self.search_panel)
        splitter.addWidget(self.favorites_panel)

    def on_save_search(self):
        """Save current search."""
        dialog = SaveSearchDialog(parent=self)

        # Get current search parameters
        params = {
            'query': self.search_input.text(),
            'file_types': self.get_selected_file_types(),
            'min_size': self.get_min_size(),
            'max_size': self.get_max_size(),
            'sort_order': self.get_sort_order(),
            # ... other parameters
        }

        dialog.set_search_params(params)

        if dialog.exec():
            saved_search = dialog.get_search()
            self.saved_searches_panel.refresh()

    def execute_saved_search(self, search: SavedSearch):
        """Execute a saved search."""
        # Apply search parameters
        self.search_input.setText(search.query)
        self.apply_filters(search)

        # Execute search
        results = self.perform_search()

        # Update stats
        self.saved_searches_panel.update_search_results(
            search.id,
            len(results)
        )

    def toggle_favorite(self):
        """Toggle favorite for selected file."""
        selected_file = self.get_selected_file()
        if not selected_file:
            return

        if self.favorites_panel.is_favorite(selected_file):
            self.favorites_panel.remove_favorite(selected_file)
        else:
            self.favorites_panel.add_favorite(selected_file, rating=3)
```

## Performance Considerations

### Database Optimization

All three databases use SQLite with proper indexing:

- Saved searches: Indexed on category, shortcut_key
- Favorites: Indexed on rating, category, created_at, accessed_at
- Collections: Indexed on name

### Best Practices

1. **Limit result counts**: Set reasonable max_results for collections
2. **Archive old searches**: Export and delete unused saved searches
3. **Clean favorites**: Periodically remove favorites for deleted files
4. **Use categories**: Organize with categories for faster filtering

## Troubleshooting

### Database Issues

If database corruption occurs:

```python
# Backup databases
import shutil
shutil.copy('~/.smart_search_saved.db', '~/.smart_search_saved.db.bak')

# Re-initialize
from search.saved_searches import SavedSearchManager
manager = SavedSearchManager()
manager._init_database()
```

### Migration

To migrate to new system:

```python
# Export from old system
old_manager.export_to_json('export.json')

# Import to new system
new_manager.import_from_json('export.json', merge=True)
```

## Future Enhancements

Potential future features:

- [ ] Sync across devices (cloud storage)
- [ ] Shared searches between users
- [ ] Scheduled smart collection updates
- [ ] Advanced regex patterns
- [ ] Custom collection icons
- [ ] Favorites sync with Windows Quick Access
- [ ] Search history integration
- [ ] Auto-categorization with AI
- [ ] Backup/restore functionality
- [ ] Performance analytics

## Support

For issues or questions:

1. Check test suite: `python test_saved_searches_favorites.py`
2. Review database with SQLite browser
3. Check logs in `~/.smart_search/logs/`
4. Report issues with full error trace

## License

Part of Smart Search Pro. Same license applies.
