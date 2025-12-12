# Folder Comparison - Quick Start Guide

## Installation

Already installed! The folder comparison module is included with Smart Search Pro.

## Verify Installation

```bash
cd C:\Users\ramos\.local\bin\smart_search
python comparison/verify_installation.py
```

## Quick Examples

### 1. Compare Two Folders (Python)

```python
from pathlib import Path
from comparison import FolderComparator, ComparisonMode

# Create comparator
comparator = FolderComparator(mode=ComparisonMode.CONTENT_HASH)

# Compare directories
result = comparator.compare(
    source=Path('C:/Users/YourName/Documents'),
    target=Path('D:/Backup/Documents'),
    recursive=True
)

# Display results
print(f"Total files: {result.stats.total_files}")
print(f"Same: {result.stats.same_files}")
print(f"Different: {result.stats.different_files}")
print(f"Missing in target: {result.stats.missing_in_target}")
print(f"Extra in target: {result.stats.extra_in_target}")

# Get specific files
missing_files = result.get_missing_files()
for file in missing_files[:10]:  # First 10
    print(f"Missing: {file.relative_path}")
```

### 2. Synchronize Folders (Python)

```python
from pathlib import Path
from comparison import SyncEngine, ConflictResolution

# Create sync engine
engine = SyncEngine(conflict_resolution=ConflictResolution.NEWER_WINS)

# Preview changes first (dry run)
preview = engine.sync(
    source=Path('C:/Users/YourName/Documents'),
    target=Path('D:/Backup/Documents'),
    copy_missing=True,
    delete_extra=False,
    update_different=True,
    dry_run=True  # Preview only
)

print(f"Operations to perform: {preview.total_operations}")

# Execute sync
result = engine.sync(
    source=Path('C:/Users/YourName/Documents'),
    target=Path('D:/Backup/Documents'),
    copy_missing=True,
    delete_extra=False,
    update_different=True,
    dry_run=False  # Execute
)

print(f"Successful: {result.successful_operations}")
print(f"Failed: {result.failed_operations}")
```

### 3. Use GUI (Python)

```python
import sys
from PyQt6.QtWidgets import QApplication
from ui.comparison_panel import ComparisonPanel

app = QApplication(sys.argv)
panel = ComparisonPanel()
panel.show()
sys.exit(app.exec())
```

### 4. Quick Comparison Dialog

```python
from PyQt6.QtWidgets import QApplication
from ui.comparison_dialog import quick_compare
from pathlib import Path

app = QApplication([])

result = quick_compare(
    source=Path('C:/Users/YourName/Documents'),
    target=Path('D:/Backup/Documents')
)

if result:
    print(f"Comparison complete: {result.stats.total_files} files")
```

## Run Demos

### UI Demo (Full Application)

```bash
cd C:\Users\ramos\.local\bin\smart_search
python comparison/demo_ui.py
```

This shows:
- Full comparison panel with all features
- Quick comparison dialog
- Drag & drop support
- Export capabilities

### Examples Script

```bash
cd C:\Users\ramos\.local\bin\smart_search
python comparison/examples.py
```

Contains 10 examples:
1. Basic comparison
2. Filtered comparison
3. Progress tracking
4. Sync preview
5. Execute sync
6. Bidirectional sync
7. Mode comparison
8. Export reports
9. Operation logs
10. Conflict resolution

## Comparison Modes

| Mode | Speed | Accuracy | Use Case |
|------|-------|----------|----------|
| CONTENT_HASH | Slow | Highest | Backup verification |
| SIZE_NAME | Fast | Good | Quick checks |
| NAME_ONLY | Fastest | Low | Structure comparison |

## Common Tasks

### Find Files Missing in Backup

```python
from pathlib import Path
from comparison import FolderComparator, ComparisonMode

comparator = FolderComparator(mode=ComparisonMode.CONTENT_HASH)
result = comparator.compare(
    source=Path('C:/Important/Data'),
    target=Path('D:/Backup/Data')
)

missing = result.get_missing_files()
print(f"{len(missing)} files not backed up:")
for file in missing:
    print(f"  - {file.relative_path}")
```

### Find Duplicate Images

```python
from pathlib import Path
from comparison import FolderComparator, ComparisonMode

comparator = FolderComparator(
    mode=ComparisonMode.CONTENT_HASH,
    extensions=['.jpg', '.jpeg', '.png', '.gif']
)

result = comparator.compare(
    source=Path('C:/Photos/2024'),
    target=Path('D:/Photos/Archive')
)

duplicates = result.get_same_files()
print(f"Found {len(duplicates)} duplicate images")
```

### Calculate Space Savings

```python
from pathlib import Path
from comparison import FolderComparator, format_size

comparator = FolderComparator(mode=ComparisonMode.CONTENT_HASH)
result = comparator.compare(source_dir, target_dir)

print(f"Duplicate files: {format_size(result.stats.duplicate_size)}")
print(f"Extra files: {format_size(result.stats.extra_size)}")
print(f"Space savings potential: {format_size(result.stats.space_savings_potential)}")
```

### Backup Only Recent Files

```python
from pathlib import Path
from datetime import datetime, timedelta
from comparison import FolderComparator, SyncEngine

# Only files modified in last 7 days
comparator = FolderComparator(
    mode=ComparisonMode.SIZE_NAME,
    modified_after=datetime.now() - timedelta(days=7)
)

# First compare to see what's new
result = comparator.compare(source, target)
print(f"New files in last 7 days: {result.stats.missing_in_target}")

# Then sync
engine = SyncEngine()
sync_result = engine.sync(
    source=source,
    target=target,
    copy_missing=True,
    dry_run=False
)
```

## Run Tests

```bash
cd C:\Users\ramos\.local\bin\smart_search
python -m pytest comparison/test_comparison.py -v
```

## File Structure

```
comparison/
├── __init__.py                  # Module interface
├── folder_comparator.py         # Comparison engine
├── sync_engine.py               # Sync operations
├── examples.py                  # Usage examples
├── test_comparison.py           # Test suite
├── demo_ui.py                   # UI demo
├── verify_installation.py       # Verification script
├── README.md                    # Full documentation
├── QUICK_START.md              # This file
└── IMPLEMENTATION_SUMMARY.md   # Technical details

ui/
├── comparison_panel.py          # Full comparison UI
└── comparison_dialog.py         # Quick dialog
```

## Keyboard Shortcuts (in UI)

- `Ctrl+O`: Open source directory
- `Ctrl+Shift+O`: Open target directory
- `Ctrl+R`: Run comparison
- `Ctrl+S`: Save/export report
- `Ctrl+W`: Close

## Troubleshooting

### "Module not found"
```bash
# Make sure you're in the right directory
cd C:\Users\ramos\.local\bin\smart_search
python -c "from comparison import FolderComparator; print('OK')"
```

### "PyQt6 not found"
```bash
# Install PyQt6
pip install PyQt6
```

### Slow comparison
- Use `SIZE_NAME` mode instead of `CONTENT_HASH`
- Apply filters to reduce file count
- Process smaller directories

### High memory usage
- Apply filters to process in batches
- Use non-recursive mode for large directories
- Process subdirectories separately

## Next Steps

1. **Read the full README**: `comparison/README.md`
2. **Run examples**: `python comparison/examples.py`
3. **Try the UI**: `python comparison/demo_ui.py`
4. **Run tests**: `python -m pytest comparison/test_comparison.py -v`
5. **Check implementation details**: `comparison/IMPLEMENTATION_SUMMARY.md`

## Support

For issues or questions:
1. Check `comparison/README.md` for detailed documentation
2. Review `comparison/examples.py` for code samples
3. Run `python comparison/verify_installation.py` to check setup
4. Review test cases in `comparison/test_comparison.py`

## Integration with Smart Search Pro

The comparison module integrates with Smart Search Pro's main window:

1. **Menu**: Tools → Compare Folders
2. **Toolbar**: Comparison button (optional)
3. **Shortcut**: `Ctrl+Shift+C`
4. **Context Menu**: Right-click in search results → Compare with folder

Enjoy using the Folder Comparison module!
