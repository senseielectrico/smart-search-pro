# Folder Comparison Module

Complete directory comparison and synchronization system for Smart Search Pro.

## Features

### Comparison Engine (`folder_comparator.py`)
- **Multiple comparison modes**:
  - Content Hash: Compare by file content (most accurate)
  - Size + Name: Fast comparison by size and name
  - Name Only: Compare by filename only
- **File filtering**: Extensions, size range, date range
- **Multi-threaded hashing**: Parallel processing for performance
- **Detailed statistics**: Space savings, duplicates, missing files
- **Progress callbacks**: Real-time progress tracking

### Sync Engine (`sync_engine.py`)
- **Copy operations**: Copy missing files from source to target
- **Delete operations**: Remove extra files from target
- **Bidirectional sync**: Sync in both directions
- **Conflict resolution**: Multiple strategies (newer wins, larger wins, manual)
- **Preview mode**: Dry run to preview changes
- **Operation logging**: Log all operations for undo capability
- **Progress tracking**: Real-time progress callbacks

### UI Components

#### Comparison Panel (`ui/comparison_panel.py`)
- Dual directory selectors with drag & drop
- Comparison mode selection
- Results table with filtering by status
- Batch actions: Copy missing, Delete extra, Sync all
- Export reports (CSV, HTML)
- Statistics panel
- Context menu actions

#### Comparison Dialog (`ui/comparison_dialog.py`)
- Quick comparison dialog
- Recent directories history
- Swap source/target button
- Quick results summary
- Launch full comparison panel

## Installation

The comparison module is included with Smart Search Pro. No additional dependencies required.

```bash
# All dependencies are in requirements.txt
pip install -r requirements.txt
```

## Quick Start

### Basic Comparison

```python
from comparison import FolderComparator, ComparisonMode

# Create comparator
comparator = FolderComparator(mode=ComparisonMode.CONTENT_HASH)

# Compare directories
result = comparator.compare(
    source='/path/to/source',
    target='/path/to/target',
    recursive=True
)

# Check results
print(f"Same files: {result.stats.same_files}")
print(f"Missing in target: {result.stats.missing_in_target}")
print(f"Extra in target: {result.stats.extra_in_target}")
print(f"Different files: {result.stats.different_files}")

# Get specific files
missing_files = result.get_missing_files()
extra_files = result.get_extra_files()
```

### Synchronization

```python
from comparison import SyncEngine, ConflictResolution

# Create sync engine
engine = SyncEngine(conflict_resolution=ConflictResolution.NEWER_WINS)

# Preview sync (dry run)
result = engine.sync(
    source='/path/to/source',
    target='/path/to/target',
    copy_missing=True,
    delete_extra=False,
    update_different=True,
    dry_run=True  # Preview only
)

print(f"Operations to perform: {result.total_operations}")

# Execute sync
result = engine.sync(
    source='/path/to/source',
    target='/path/to/target',
    copy_missing=True,
    delete_extra=False,
    update_different=True,
    dry_run=False  # Execute
)

print(f"Successful: {result.successful_operations}")
print(f"Failed: {result.failed_operations}")
```

### Using UI Components

```python
from PyQt6.QtWidgets import QApplication
from ui.comparison_panel import ComparisonPanel
from ui.comparison_dialog import ComparisonDialog, quick_compare

# Full comparison panel
app = QApplication([])
panel = ComparisonPanel()
panel.show()
app.exec()

# Quick comparison dialog
result = quick_compare(
    source=Path('/path/to/source'),
    target=Path('/path/to/target')
)
```

## Comparison Modes

### Content Hash (Recommended)
- Compares files by SHA-256 hash
- Most accurate - detects any content differences
- Slower for large files
- Best for: Backup verification, duplicate detection

### Size + Name
- Compares files by size and filename
- Fast performance
- May miss content differences in same-size files
- Best for: Quick checks, large directories

### Name Only
- Compares files by filename only
- Fastest performance
- Ignores file content
- Best for: Structure comparison, quick overview

## Filtering

```python
from datetime import datetime, timedelta

comparator = FolderComparator(
    mode=ComparisonMode.CONTENT_HASH,
    extensions=['.jpg', '.png', '.gif'],  # Only images
    min_size=1024,                        # At least 1KB
    max_size=10 * 1024 * 1024,           # Max 10MB
    modified_after=datetime.now() - timedelta(days=30)  # Last 30 days
)
```

## Conflict Resolution Strategies

- **NEWER_WINS**: Use file with newer modification time
- **LARGER_WINS**: Use larger file
- **SOURCE_WINS**: Always prefer source file
- **TARGET_WINS**: Always prefer target file
- **MANUAL**: Require manual resolution
- **SKIP**: Skip conflicting files

## Export Formats

### CSV Export
```csv
Status,Relative Path,Source Path,Target Path,Size,Modified
same,document.txt,/source/document.txt,/target/document.txt,1024,2024-01-15T10:30:00
missing_target,photo.jpg,/source/photo.jpg,,2048576,2024-01-14T15:45:00
```

### HTML Export
- Styled HTML report
- Color-coded status indicators
- Statistics summary
- Sortable table

## Performance Tips

1. **Use appropriate comparison mode**:
   - Content Hash: Accurate but slower
   - Size + Name: Good balance
   - Name Only: Fast overview

2. **Apply filters**: Reduce files to compare

3. **Multi-threading**: Automatic optimization based on CPU cores

4. **Preview first**: Use dry_run=True before executing sync

## Statistics

The comparison result provides detailed statistics:

```python
stats = result.stats

# File counts
stats.total_files
stats.same_files
stats.different_files
stats.missing_in_target
stats.extra_in_target

# Sizes
stats.total_source_size
stats.total_target_size
stats.missing_size
stats.extra_size
stats.duplicate_size

# Calculated
stats.space_wasted_by_duplicates
stats.space_savings_potential
```

## Error Handling

```python
result = comparator.compare(source, target)

if result.error:
    print(f"Comparison failed: {result.error}")
else:
    # Process results
    for comparison in result.comparisons:
        if comparison.status == FileStatus.MISSING_IN_TARGET:
            print(f"Missing: {comparison.relative_path}")
```

## Operation Logging

Sync operations are automatically logged for undo capability:

```python
# Get recent operations
operations = engine.get_undo_operations(limit=10)

for op in operations:
    print(f"{op['timestamp']}: {op['action']} - {op['relative_path']}")
```

## Integration with Smart Search Pro

The comparison module integrates seamlessly with Smart Search Pro:

1. **From main window**: Tools → Compare Folders
2. **From search results**: Right-click → Compare with folder
3. **Keyboard shortcut**: Ctrl+Shift+C

## Examples

See `comparison/examples.py` for complete examples:
- Basic comparison
- Filtered comparison
- Synchronization
- Export reports
- UI integration

## API Reference

### FolderComparator

```python
FolderComparator(
    mode: ComparisonMode = ComparisonMode.CONTENT_HASH,
    hash_algorithm: HashAlgorithm = HashAlgorithm.SHA256,
    max_workers: Optional[int] = None,
    extensions: Optional[List[str]] = None,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    modified_after: Optional[datetime] = None,
    modified_before: Optional[datetime] = None
)
```

### SyncEngine

```python
SyncEngine(
    conflict_resolution: ConflictResolution = ConflictResolution.NEWER_WINS,
    log_file: Optional[Path] = None
)
```

### ComparisonResult

```python
result.comparisons          # List[FileComparison]
result.stats               # ComparisonStats
result.duration            # float (seconds)
result.get_missing_files()
result.get_extra_files()
result.get_different_files()
result.get_same_files()
```

### SyncResult

```python
result.operations          # List[SyncOperation]
result.conflicts          # List[SyncConflict]
result.total_operations
result.successful_operations
result.failed_operations
result.total_bytes_transferred
```

## Troubleshooting

### Comparison is slow
- Use SIZE_NAME mode instead of CONTENT_HASH
- Apply filters to reduce file count
- Check disk I/O performance

### Sync fails
- Check file permissions
- Verify disk space
- Review operation logs

### Memory issues with large directories
- Use filtering to process in batches
- Increase system memory
- Process subdirectories separately

## License

Part of Smart Search Pro. See main LICENSE file.
