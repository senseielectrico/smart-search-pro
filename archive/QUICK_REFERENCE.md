# Archive Module - Quick Reference Card

One-page reference for common operations.

## Import Statements

```python
from archive.sevenzip_manager import SevenZipManager, CompressionLevel, ArchiveFormat
from archive.archive_analyzer import ArchiveAnalyzer
from archive.recursive_extractor import RecursiveExtractor
from archive.password_cracker import PasswordCracker
from ui.archive_panel import ArchivePanel
from ui.extract_dialog import ExtractDialog
```

## Common Operations

### Create Archive

```python
manager = SevenZipManager()

# Basic
manager.create_archive('output.7z', ['file1.txt', 'folder/'])

# With options
manager.create_archive(
    archive_path='backup.7z',
    source_paths=['documents/'],
    format=ArchiveFormat.SEVEN_ZIP,
    compression_level=CompressionLevel.MAXIMUM,
    password='secret123'
)
```

### Extract Archive

```python
# Simple extraction
manager.extract('archive.zip', 'output/')

# With password
manager.extract('secure.7z', 'output/', password='secret123')

# With progress
manager.extract(
    'large.7z',
    'output/',
    progress_callback=lambda p: print(f"{p.percentage:.1f}%")
)
```

### List Contents

```python
entries = manager.list_contents('archive.7z')
for entry in entries:
    print(f"{entry['Path']} - {entry['Size']} bytes")
```

### Recursive Extraction

```python
extractor = RecursiveExtractor()
stats = extractor.extract_recursive('nested.7z', 'output/')
print(f"Extracted {stats['archives_extracted']} archives")
```

### Analyze Archive

```python
analyzer = ArchiveAnalyzer()
stats = analyzer.analyze('archive.zip')
print(f"Files: {stats.total_files}, Size: {stats.total_size}")
```

### Password Recovery

```python
cracker = PasswordCracker()
password = cracker.dictionary_attack('protected.7z', use_common=True)
if password:
    print(f"Found: {password}")
```

## Compression Levels

| Level | Name | Speed | Ratio | Use Case |
|-------|------|-------|-------|----------|
| 0 | STORE | Fastest | 0% | Already compressed |
| 1 | FASTEST | Very Fast | 30% | Quick backup |
| 3 | FAST | Fast | 50% | Daily use |
| 5 | NORMAL | Medium | 65% | Balanced |
| 7 | MAXIMUM | Slow | 75% | Storage |
| 9 | ULTRA | Slowest | 80% | Archival |

## Archive Formats

| Format | Extension | Create | Extract | Password | Notes |
|--------|-----------|--------|---------|----------|-------|
| 7-Zip | .7z | ✓ | ✓ | ✓ | Best compression |
| ZIP | .zip | ✓ | ✓ | ✓ | Universal |
| RAR | .rar | ✗ | ✓ | ✓ | Extract only |
| TAR | .tar | ✓ | ✓ | ✗ | No compression |
| GZIP | .gz | ✓ | ✓ | ✗ | Single file |
| BZIP2 | .bz2 | ✓ | ✓ | ✗ | Better ratio |
| XZ | .xz | ✓ | ✓ | ✗ | Best ratio |
| ISO | .iso | ✗ | ✓ | ✗ | Disk images |

## Progress Tracking

```python
def progress_callback(progress):
    print(f"Progress: {progress.percentage:.1f}%")
    print(f"File: {progress.current_file}")
    print(f"Speed: {progress.speed_mbps:.2f} MB/s")

manager.extract('archive.7z', 'output/', progress_callback=progress_callback)
```

## Error Handling

```python
try:
    manager.extract('archive.7z', 'output/')
except ValueError as e:
    print(f"Wrong password: {e}")
except FileNotFoundError:
    print("Archive not found")
except RuntimeError as e:
    print(f"Extraction failed: {e}")
```

## UI Components

### Archive Panel

```python
# Add to main window
archive_panel = ArchivePanel(parent)
tabs.addTab(archive_panel, "Archives")

# Open archive
archive_panel.load_archive('archive.7z')

# Connect signals
archive_panel.archive_opened.connect(on_opened)
archive_panel.extraction_completed.connect(on_completed)
```

### Extract Dialog

```python
dialog = ExtractDialog('archive.7z', parent)
if dialog.exec() == QDialog.DialogCode.Accepted:
    options = dialog.get_options()
    # options['destination']
    # options['recursive']
    # options['flatten']
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+E | Extract selected |
| Ctrl+Shift+A | Create archive |
| Ctrl+T | Test integrity |
| F5 | Reload archive |
| Ctrl+A | Select all |

## Common Patterns

### Batch Create

```python
for folder in folders:
    manager.create_archive(
        f"{folder}.7z",
        [folder],
        compression_level=CompressionLevel.NORMAL
    )
```

### Batch Extract

```python
for archive in archives:
    dest = Path(archive).stem
    manager.extract(archive, dest)
```

### Find and Extract

```python
# Find all archives
archives = [f for f in Path('.').rglob('*') if manager.is_archive(f)]

# Extract all
for archive in archives:
    manager.extract(str(archive), f"extracted/{archive.stem}")
```

### Verify Before Extract

```python
is_valid, msg = manager.test_archive('archive.7z')
if is_valid:
    manager.extract('archive.7z', 'output/')
else:
    print(f"Archive corrupted: {msg}")
```

## Performance Tips

1. **Use STORE (0)** for already-compressed files (videos, images)
2. **Use FAST (3)** for daily backups
3. **Use ULTRA (9)** for long-term storage
4. **Extract to SSD** for faster performance
5. **Enable multi-threading** for large operations
6. **Cancel long operations** to avoid blocking UI

## Security Checklist

- [ ] Use strong passwords (12+ chars)
- [ ] Enable header encryption for 7z
- [ ] Validate extraction paths
- [ ] Test archives after creation
- [ ] Cleanup temp files
- [ ] Don't store passwords in code
- [ ] Use password manager for storage

## Troubleshooting

| Problem | Solution |
|---------|----------|
| 7-Zip not found | Install from 7-zip.org |
| Wrong password | Try password recovery |
| Extraction fails | Check disk space |
| Slow performance | Use faster compression |
| Out of memory | Reduce max_depth |

## File Locations

```
smart_search/
├── archive/
│   ├── sevenzip_manager.py    # Main wrapper
│   ├── recursive_extractor.py # Nested handling
│   ├── archive_analyzer.py    # Analysis
│   ├── password_cracker.py    # Recovery
│   └── test_*.py              # Tests
│
└── ui/
    ├── archive_panel.py       # Main UI
    └── extract_dialog.py      # Options dialog
```

## Documentation

- **README.md** - Complete documentation
- **INTEGRATION_GUIDE.md** - Integration steps
- **QUICKSTART.md** - 5-minute guide
- **example_usage.py** - Code examples
- **This file** - Quick reference

## Support

```bash
# Test installation
python archive/test_archive_integration.py

# Run examples
python archive/example_usage.py

# Check 7-Zip path
python -c "from archive.sevenzip_manager import SevenZipManager; print(SevenZipManager().seven_zip_path)"
```

## API Cheatsheet

```python
# Manager
manager = SevenZipManager()
manager.create_archive(path, files, format, level, password, split_size)
manager.extract(archive, dest, password, files, overwrite, progress_callback)
manager.list_contents(archive, password)
manager.test_archive(archive, password)
manager.is_archive(path)
manager.cancel_extraction()

# Analyzer
analyzer = ArchiveAnalyzer()
analyzer.analyze(archive, password, detect_nested)
analyzer.get_file_tree(archive, password, max_items)
analyzer.preview_as_text(archive, password, max_items)
analyzer.compare_archives(archive1, archive2, password1, password2)
analyzer.estimate_extraction_size(archive, password)

# Extractor
extractor = RecursiveExtractor(max_depth)
extractor.extract_recursive(archive, dest, password, flatten, preserve_structure, progress_callback)
extractor.detect_nested_depth(archive)

# Cracker
cracker = PasswordCracker(max_threads)
cracker.dictionary_attack(archive, wordlist_path, use_common, use_variations, progress_callback)
cracker.brute_force_attack(archive, charset, min_length, max_length, progress_callback)
cracker.mask_attack(archive, mask, progress_callback)
cracker.cancel()
```

---

**Quick Reference v1.0** - Part of Smart Search Pro Archive Module
