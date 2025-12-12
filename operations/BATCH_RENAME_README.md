# Batch Rename System - Complete Documentation

## Overview

Comprehensive batch file renaming system with pattern-based renaming, live preview, undo capability, and extensive text operations.

## Features

### 🎯 Core Features
- **Pattern-based renaming** with 15+ placeholders
- **Find & Replace** with regex support
- **Text operations**: prefix, suffix, remove characters, trim
- **Case conversion**: UPPER, lower, Title, Sentence
- **Sequential numbering** with configurable padding
- **Live preview** with conflict detection
- **Undo capability** with full history
- **Preset patterns** library
- **Drag & drop** support

### 📝 Supported Placeholders

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{name}` | Original filename (no extension) | document |
| `{ext}` | File extension (no dot) | pdf |
| `{num}` | Sequential number (padded) | 001, 002, 003 |
| `{date}` | File modification date | 20231215 |
| `{created}` | File creation date | 20231215 |
| `{parent}` | Parent folder name | Photos |
| `{size}` | File size in bytes | 1024 |
| `{sizekb}` | File size in KB | 1 |
| `{sizemb}` | File size in MB | 1 |
| `{hash}` | Short file hash (8 chars) | a1b2c3d4 |
| `{hash16}` | Medium file hash (16 chars) | a1b2c3d4e5f6g7h8 |
| `{exif_date}` | EXIF date from photos | 20231215 |
| `{exif_datetime}` | EXIF date and time | 20231215_143022 |
| `{width}` | Image width | 1920 |
| `{height}` | Image height | 1080 |

### 🎨 Preset Patterns

#### Photos
- **Photo: Date + Number** - `{date}_IMG_{num}` → `20231215_IMG_001.jpg`
- **Photo: EXIF Date** - `{exif_datetime}` → `20231215_143022.jpg`
- **Photo: Folder + Date** - `{parent}_{date}_{num}` → `Vacation_20231215_001.jpg`

#### Documents
- **Document: Folder + Name** - `{parent}_{name}` → `ProjectName_document.pdf`
- **Document: Date + Name** - `{date}_{name}` → `2023-12-15_document.pdf`

#### Sequential
- **Sequential: Padded Numbers** - `File_{num}` → `File_001.ext`
- **Sequential: Date + Number** - `{date}_{num}` → `20231215_001.ext`

#### Cleanup
- **Clean: Remove Extra Spaces** - Normalize whitespace
- **Clean: Remove Special Characters** - Remove `!@#$%^&*()`
- **Clean: Lowercase** - Convert to lowercase
- **Clean: Title Case** - Convert To Title Case

## Architecture

### Backend Components

#### 1. `batch_renamer.py` - Core Renaming Engine

```python
from operations.batch_renamer import (
    BatchRenamer, RenamePattern, CaseMode, CollisionMode
)

# Create renamer
renamer = BatchRenamer()

# Create pattern
pattern = RenamePattern(
    pattern="{date}_{num}",
    date_format="%Y%m%d",
    number_padding=3,
    start_number=1
)

# Preview changes
files = ["photo1.jpg", "photo2.jpg", "photo3.jpg"]
previews = renamer.preview_rename(files, pattern)

# Preview format: [(old_name, new_name, has_conflict), ...]
for old, new, conflict in previews:
    print(f"{old} → {new}" + (" [CONFLICT]" if conflict else ""))

# Apply rename
result = renamer.batch_rename(
    files,
    pattern,
    CollisionMode.AUTO_NUMBER
)

print(f"Success: {result.success_count}/{result.total_files}")
```

**Classes:**
- `BatchRenamer` - Main renaming engine
- `RenamePattern` - Pattern configuration
- `RenameOperation` - Single rename operation result
- `RenameResult` - Batch operation results
- `TextOperations` - Text manipulation utilities

**Enums:**
- `CaseMode` - UPPER, LOWER, TITLE, SENTENCE, KEEP
- `CollisionMode` - AUTO_NUMBER, SKIP, OVERWRITE, ASK

#### 2. `rename_patterns.py` - Pattern Library

```python
from operations.rename_patterns import PatternLibrary, SavedPattern

# Get library
library = PatternLibrary()

# Browse patterns
all_patterns = library.get_all_patterns()
photo_patterns = library.get_patterns_by_category("Photos")
date_patterns = library.get_patterns_by_tag("date")

# Get specific pattern
pattern_data = library.get_pattern("photo_date_numbered")
pattern = pattern_data.pattern

# Save custom pattern
custom_pattern = SavedPattern(
    name="My Custom Pattern",
    description="Custom naming scheme",
    pattern=RenamePattern(pattern="{parent}_{name}_{num}"),
    category="Custom",
    tags=["custom", "numbered"]
)
library.save_pattern("my_pattern", custom_pattern)

# Export/Import
library.export_patterns("my_patterns.json", ["my_pattern"])
library.import_patterns("shared_patterns.json")
```

#### 3. `rename_history.py` - History & Undo

```python
from operations.rename_history import RenameHistory

# Get history
history = RenameHistory()

# Add entry (done automatically by BatchRenameDialog)
history.add_entry(
    operation_id="unique_id",
    operations=[...],  # List of rename operations
    pattern_used="{date}_{num}",
    total_files=10,
    success_count=10
)

# Get recent history
recent = history.get_history(limit=10)

# Undo operation
success, message, count = history.undo_operation("unique_id")

# Statistics
stats = history.get_statistics()
print(f"Total operations: {stats['total_operations']}")
print(f"Total files renamed: {stats['total_files_renamed']}")
print(f"Success rate: {stats['success_rate']:.1f}%")

# Search history
results = history.search_history(
    pattern="IMG",
    start_date=datetime(2023, 12, 1)
)

# Export history
history.export_history("rename_log.json", limit=100)
```

### UI Components

#### 1. `batch_rename_dialog.py` - Main Dialog

```python
from ui.batch_rename_dialog import BatchRenameDialog

# Open with files
files = ["file1.txt", "file2.txt", "file3.txt"]
dialog = BatchRenameDialog(initial_files=files, parent=main_window)
dialog.files_renamed.connect(on_files_renamed)

if dialog.exec():
    print("Rename completed")
```

**Features:**
- Multi-tab interface (Pattern, Find & Replace, Add/Remove, Case, Numbering)
- File list with drag & drop
- Live preview table
- Preset selection
- Save custom presets
- Undo last rename
- View history

#### 2. `pattern_builder_widget.py` - Pattern Builder

Visual pattern builder with:
- Placeholder buttons with tooltips
- Live pattern editing
- Format options (date format, number padding)
- Pattern examples
- Regex helper

#### 3. `rename_preview_table.py` - Preview Table

Preview table showing:
- Original filename
- New filename (with highlighting)
- Status (✓ Will rename, ⚠ Conflict, - No change)
- Color coding (green=change, red=conflict, gray=no change)
- Statistics
- Filter by status
- Export to CSV

## Usage Examples

### Example 1: Rename Photos by Date

```python
from operations.batch_renamer import BatchRenamer, RenamePattern

renamer = BatchRenamer()
pattern = RenamePattern(
    pattern="{exif_date}_{num}",
    date_format="%Y%m%d",
    number_padding=4,
    start_number=1
)

files = [
    "DSC00123.jpg",
    "DSC00124.jpg",
    "DSC00125.jpg"
]

# Preview
for old, new, conflict in renamer.preview_rename(files, pattern):
    print(f"{old} → {new}")

# Output:
# DSC00123.jpg → 20231215_0001.jpg
# DSC00124.jpg → 20231215_0002.jpg
# DSC00125.jpg → 20231215_0003.jpg
```

### Example 2: Clean Up File Names

```python
pattern = RenamePattern(
    pattern="{name}",
    remove_chars="!@#$%^&*()",
    case_mode=CaseMode.LOWER,
    trim_whitespace=True
)

files = [
    "File With Spaces!!!.txt",
    "UPPERCASE FILE.TXT",
    "Mixed-Case@File#123.doc"
]

# Results:
# File With Spaces!!!.txt → file with spaces.txt
# UPPERCASE FILE.TXT → uppercase file.txt
# Mixed-Case@File#123.doc → mixed-casefile123.doc
```

### Example 3: Sequential Numbering

```python
pattern = RenamePattern(
    pattern="Project_{parent}_{num}",
    number_padding=3,
    start_number=1
)

# If files are in folder "Website":
# file1.txt → Project_Website_001.txt
# file2.txt → Project_Website_002.txt
```

### Example 4: Find & Replace with Regex

```python
pattern = RenamePattern(
    pattern="{name}",
    find=r"(\d{4})-(\d{2})-(\d{2})",
    replace=r"\1\2\3",
    use_regex=True
)

# 2023-12-15_photo.jpg → 20231215_photo.jpg
```

### Example 5: Date Format Conversion

```python
pattern = RenamePattern(
    pattern="{date}_{name}",
    date_format="%Y-%m-%d"  # ISO format
)

# photo.jpg → 2023-12-15_photo.jpg
```

## Integration with Main UI

### Add to Results Panel Context Menu

```python
# In results_panel.py
def _create_context_menu(self):
    menu = QMenu(self)

    # ... existing actions ...

    # Add batch rename action
    rename_action = menu.addAction("Batch Rename...")
    rename_action.triggered.connect(self._batch_rename_selected)

    return menu

def _batch_rename_selected(self):
    """Open batch rename dialog for selected files"""
    from ui.batch_rename_dialog import BatchRenameDialog

    selected_files = self.get_selected_file_paths()
    if not selected_files:
        QMessageBox.warning(self, "No Selection", "Please select files to rename")
        return

    dialog = BatchRenameDialog(initial_files=selected_files, parent=self)
    dialog.files_renamed.connect(self._on_files_renamed)
    dialog.exec()

def _on_files_renamed(self, count: int):
    """Handle files renamed"""
    self.statusBar().showMessage(f"Renamed {count} files", 3000)
    self.refresh_results()  # Refresh file list
```

### Add to Main Window Toolbar

```python
# In main_window.py
def _create_toolbar(self):
    toolbar = self.addToolBar("Main")

    # ... existing actions ...

    # Batch rename action
    rename_action = QAction("Batch Rename", self)
    rename_action.setIcon(QIcon("icons/rename.png"))
    rename_action.setShortcut("Ctrl+R")
    rename_action.triggered.connect(self._open_batch_rename)
    toolbar.addAction(rename_action)

def _open_batch_rename(self):
    """Open batch rename dialog"""
    from ui.batch_rename_dialog import BatchRenameDialog

    dialog = BatchRenameDialog(parent=self)
    dialog.exec()
```

### Add to Operations Panel

```python
# In operations_panel.py
def _init_ui(self):
    # ... existing UI ...

    # Add batch rename button
    rename_btn = QPushButton("Batch Rename Files...")
    rename_btn.clicked.connect(self._open_batch_rename)
    layout.addWidget(rename_btn)

def _open_batch_rename(self):
    """Open batch rename dialog"""
    from ui.batch_rename_dialog import BatchRenameDialog

    dialog = BatchRenameDialog(parent=self)
    dialog.files_renamed.connect(self._on_files_renamed)
    dialog.exec()
```

## Testing

### Backend Tests

```bash
# Run backend tests
python operations/test_batch_rename.py
```

Tests cover:
- Basic renaming
- Pattern library
- Rename history
- Text operations
- Date patterns
- Collision handling

### UI Tests

```bash
# Run UI tests
python ui/test_batch_rename_dialog.py
```

Opens test window with sample files to test all dialog features.

## File Locations

### Backend
- `C:\Users\ramos\.local\bin\smart_search\operations\batch_renamer.py`
- `C:\Users\ramos\.local\bin\smart_search\operations\rename_patterns.py`
- `C:\Users\ramos\.local\bin\smart_search\operations\rename_history.py`

### UI
- `C:\Users\ramos\.local\bin\smart_search\ui\batch_rename_dialog.py`
- `C:\Users\ramos\.local\bin\smart_search\ui\pattern_builder_widget.py`
- `C:\Users\ramos\.local\bin\smart_search\ui\rename_preview_table.py`

### Data Files (Created Automatically)
- `~/.smart_search/rename_patterns.json` - Custom patterns
- `~/.smart_search/rename_history.json` - Rename history

## Performance

- **Preview**: Instant for 1000+ files (dry run mode)
- **Metadata caching**: File hash and EXIF data cached
- **Unicode support**: Full Unicode filename support
- **Large files**: Hash calculated in chunks (8KB)
- **Memory efficient**: Streaming operations

## Safety Features

1. **Preview before apply** - Always see what will change
2. **Collision detection** - Warns about name conflicts
3. **Undo capability** - Can undo recent operations
4. **Dry run mode** - Test without applying changes
5. **Error handling** - Graceful failure handling
6. **History logging** - Full audit trail

## Future Enhancements

- [ ] Multi-step patterns (apply multiple patterns)
- [ ] Conditional renaming (if/then rules)
- [ ] Music metadata support (MP3 tags)
- [ ] Video metadata support
- [ ] Batch undo (undo multiple operations)
- [ ] Pattern testing sandbox
- [ ] Import patterns from file
- [ ] Schedule rename operations

## Version

Current version: 1.1.0

Last updated: 2023-12-12
