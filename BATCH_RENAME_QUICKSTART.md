# Batch Rename - Quick Start Guide

## For End Users

### Opening Batch Rename Dialog

**From Context Menu:**
1. Right-click selected files
2. Select "Batch Rename..."

**From Keyboard:**
- Press `F2` for quick rename
- Press `Ctrl+R` for batch rename dialog

**From Menu:**
- Tools → Batch Rename Files

### Using the Dialog

#### 1. Add Files
- Click "Add Files..." button
- Click "Add Folder..." button
- Drag & drop files directly into dialog

#### 2. Choose Rename Method (Tabs)

**Pattern Rename** - Use placeholders:
- `{name}` - Original filename
- `{num}` - Sequential number
- `{date}` - File date
- `{parent}` - Folder name
- And 10+ more...

**Find & Replace:**
- Find text to replace
- Enter replacement text
- Check "Use Regular Expressions" for advanced

**Add/Remove Text:**
- Add prefix before filename
- Add suffix after filename
- Remove specific characters

**Case Change:**
- UPPERCASE
- lowercase
- Title Case
- Sentence case

**Numbering:**
- Set start number
- Set padding (001, 002, etc.)

#### 3. Preview Changes
- Green = Will rename
- Red = Name conflict
- Gray = No change

#### 4. Apply or Cancel
- Click "Apply Rename" to execute
- Click "Cancel" to abort
- Click "Undo Last Rename" if needed

### Common Patterns

**Rename photos by date:**
```
Pattern: {date}_IMG_{num}
Result: 20231215_IMG_001.jpg
```

**Add project name:**
```
Pattern: {parent}_{name}
Result: ProjectName_document.pdf
```

**Sequential numbering:**
```
Pattern: File_{num}
Result: File_001.txt, File_002.txt
```

**Clean filenames:**
```
Method: Case Change → lowercase
Remove Characters: !@#$%
```

---

## For Developers

### Quick Integration

**1. Import:**
```python
from ui.batch_rename_dialog import BatchRenameDialog
```

**2. Open Dialog:**
```python
# With selected files
dialog = BatchRenameDialog(initial_files=file_list, parent=self)
dialog.files_renamed.connect(self._on_files_renamed)
dialog.exec()

# Empty (user adds files)
dialog = BatchRenameDialog(parent=self)
dialog.exec()
```

**3. Handle Result:**
```python
def _on_files_renamed(self, count: int):
    print(f"Renamed {count} files")
    self.refresh_results()  # Update UI
```

### Backend Usage

```python
from operations.batch_renamer import BatchRenamer, RenamePattern

renamer = BatchRenamer()

# Create pattern
pattern = RenamePattern(
    pattern="{date}_{num}",
    number_padding=3,
    date_format="%Y%m%d"
)

# Preview
files = ["photo1.jpg", "photo2.jpg"]
for old, new, conflict in renamer.preview_rename(files, pattern):
    print(f"{old} -> {new}")

# Apply
result = renamer.batch_rename(files, pattern)
print(f"Success: {result.success_count}")
```

### Pattern Library

```python
from operations.rename_patterns import get_pattern_library

library = get_pattern_library()

# Get pre-built pattern
pattern_data = library.get_pattern("photo_date_numbered")
pattern = pattern_data.pattern

# Browse by category
photo_patterns = library.get_patterns_by_category("Photos")

# Save custom pattern
from operations.rename_patterns import SavedPattern

custom = SavedPattern(
    name="My Pattern",
    description="Custom naming",
    pattern=RenamePattern(pattern="{parent}_{num}"),
    category="Custom"
)
library.save_pattern("my_pattern", custom)
```

### History & Undo

```python
from operations.rename_history import get_rename_history

history = get_rename_history()

# Get recent operations
recent = history.get_history(limit=10)

# Undo operation
success, message, count = history.undo_operation(operation_id)

# Statistics
stats = history.get_statistics()
```

---

## File Locations

**Source Code:**
```
operations/
├── batch_renamer.py       - Core engine
├── rename_patterns.py     - Pattern library
└── rename_history.py      - History & undo

ui/
├── batch_rename_dialog.py       - Main dialog
├── pattern_builder_widget.py    - Pattern builder
└── rename_preview_table.py      - Preview table
```

**User Data:**
```
~/.smart_search/
├── rename_patterns.json    - Custom patterns
└── rename_history.json     - Rename history
```

---

## Available Placeholders

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{name}` | Original name | document |
| `{ext}` | Extension | pdf |
| `{num}` | Number | 001 |
| `{date}` | Mod date | 20231215 |
| `{created}` | Create date | 20231215 |
| `{parent}` | Folder | Photos |
| `{size}` | Size (bytes) | 1024 |
| `{sizekb}` | Size (KB) | 1 |
| `{sizemb}` | Size (MB) | 1 |
| `{hash}` | Short hash | a1b2c3d4 |
| `{hash16}` | Med hash | a1b2c3d4e5f6g7h8 |
| `{exif_date}` | EXIF date | 20231215 |
| `{width}` | Image width | 1920 |
| `{height}` | Image height | 1080 |

---

## Testing

**Backend:**
```bash
python operations/test_batch_rename.py
```

**UI:**
```bash
python ui/test_batch_rename_dialog.py
```

---

## Support

**Documentation:** `operations/BATCH_RENAME_README.md`
**Examples:** `operations/batch_rename_integration_example.py`
**Version:** 1.1.0
