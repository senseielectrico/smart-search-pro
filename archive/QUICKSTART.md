# Archive Module - Quick Start Guide

Get started with 7-Zip integration in 5 minutes!

## Installation

### Step 1: Install 7-Zip

**Option A: Download installer**
- Visit: https://www.7-zip.org/
- Download and install

**Option B: Package manager (Windows)**
```bash
# Using winget
winget install 7zip.7zip

# Using Chocolatey
choco install 7zip

# Using Scoop
scoop install 7zip
```

### Step 2: Verify Installation

Run this test:

```python
python -c "from archive.sevenzip_manager import SevenZipManager; print(SevenZipManager().seven_zip_path)"
```

Should output: `C:\Program Files\7-Zip\7z.exe` (or similar)

## Basic Usage

### Create an Archive

```python
from archive.sevenzip_manager import SevenZipManager, CompressionLevel, ArchiveFormat

manager = SevenZipManager()

# Create 7z archive
manager.create_archive(
    archive_path='my_files.7z',
    source_paths=['file1.txt', 'folder/'],
    format=ArchiveFormat.SEVEN_ZIP,
    compression_level=CompressionLevel.NORMAL
)
```

### Extract an Archive

```python
# Extract to folder
manager.extract(
    archive_path='archive.zip',
    destination='extracted_files/'
)
```

### List Contents

```python
# See what's inside without extracting
entries = manager.list_contents('archive.7z')

for entry in entries:
    print(f"{entry['Path']} - {entry['Size']} bytes")
```

### Password Protection

```python
# Create encrypted archive
manager.create_archive(
    archive_path='secret.7z',
    source_paths=['confidential/'],
    password='MySecurePassword123!'
)

# Extract with password
manager.extract(
    archive_path='secret.7z',
    destination='decrypted/',
    password='MySecurePassword123!'
)
```

## Common Tasks

### Task 1: Archive a folder

```python
from archive.sevenzip_manager import *

manager = SevenZipManager()

manager.create_archive(
    archive_path='backup.7z',
    source_paths=['C:/Users/YourName/Documents'],
    format=ArchiveFormat.SEVEN_ZIP,
    compression_level=CompressionLevel.MAXIMUM
)

print("Backup created!")
```

### Task 2: Extract with progress

```python
def show_progress(progress):
    print(f"{progress.percentage:.1f}% - {progress.current_file}")

manager.extract(
    archive_path='large_archive.7z',
    destination='output/',
    progress_callback=show_progress
)
```

### Task 3: Analyze archive

```python
from archive.archive_analyzer import ArchiveAnalyzer

analyzer = ArchiveAnalyzer()
stats = analyzer.analyze('archive.zip')

print(f"Files: {stats.total_files}")
print(f"Size: {stats.total_size:,} bytes")
print(f"Compression: {stats.compression_ratio:.1f}%")
```

### Task 4: Recursive extraction

```python
from archive.recursive_extractor import RecursiveExtractor

extractor = RecursiveExtractor()

stats = extractor.extract_recursive(
    archive_path='nested.7z',
    destination='fully_extracted/'
)

print(f"Extracted {stats['archives_extracted']} archives")
```

### Task 5: Password recovery

```python
from archive.password_cracker import PasswordCracker

cracker = PasswordCracker()

password = cracker.dictionary_attack(
    archive_path='forgot_password.7z',
    use_common=True
)

if password:
    print(f"Password found: {password}")
```

## UI Usage

### Open Archive Manager

1. Launch Smart Search Pro
2. Click "Archives" tab
3. Click "Open Archive"
4. Select an archive file
5. Browse contents in tree view

### Extract Files

1. Open archive in Archive Manager
2. Select files to extract (or leave empty for all)
3. Click "Extract Selected" or "Extract All"
4. Choose destination
5. Configure options (recursive, flatten, etc.)
6. Click "Extract"

### Create Archive

1. Click "Create Archive" in Archive Manager
2. Select files to add
3. Choose format (7z, zip, tar)
4. Set compression level (slider)
5. Optional: Add password
6. Click "Create"

## Integration with Search

### Search and Extract

1. Search for files in main search
2. Right-click on archive in results
3. Choose:
   - "Open in Archive Manager" - browse contents
   - "Extract Here" - extract to same folder
   - "Extract To..." - choose destination

### Preview Archives

1. Select archive in search results
2. Preview panel shows:
   - File count
   - Total size
   - Compression ratio
   - Contents list

## Tips & Tricks

### Fastest compression
Use `CompressionLevel.STORE` (0) for already-compressed files (images, videos)

### Best compression
Use `CompressionLevel.ULTRA` (9) for text files, source code

### Balanced
Use `CompressionLevel.NORMAL` (5) for general use

### Password security
- Use 12+ characters
- Mix letters, numbers, symbols
- Enable header encryption for 7z format

### Batch operations
Use wildcards in paths:
```python
manager.create_archive(
    archive_path='all_logs.7z',
    source_paths=['C:/logs/*.log']
)
```

### Test before trusting
Always test archives after creation:
```python
is_valid, msg = manager.test_archive('important.7z')
```

### Cleanup temp files
Recursive extractor auto-cleans, but you can force:
```python
extractor._cleanup_temp_dirs()
```

## Keyboard Shortcuts

When archive is open in Archive Manager:

- `Ctrl+E` - Extract selected
- `Ctrl+A` - Select all
- `Delete` - Remove from archive (if supported)
- `F5` - Reload archive
- `Ctrl+T` - Test integrity

## Troubleshooting

### "7-Zip not found"
Install 7-Zip or add to PATH

### "Wrong password"
Verify password, try password recovery

### "Extraction failed"
Check disk space and permissions

### Slow extraction
Use faster compression or extract to SSD

### Out of memory
Increase max_depth limit or extract in batches

## Examples

All examples in one place:

```bash
# Run all examples
python archive/example_usage.py

# Run tests
python archive/test_archive_integration.py

# Test UI
python ui/test_archive_panel.py
```

## Next Steps

1. Read full documentation: `archive/README.md`
2. Review integration guide: `archive/INTEGRATION_GUIDE.md`
3. Explore advanced features: password cracking, recursive extraction
4. Customize settings in Settings dialog
5. Add keyboard shortcuts for your workflow

## Support

- Documentation: `archive/README.md`
- Examples: `archive/example_usage.py`
- Tests: `archive/test_archive_integration.py`
- 7-Zip docs: https://www.7-zip.org/

## Quick Reference

```python
# Create
manager.create_archive(path, files, format, level, password)

# Extract
manager.extract(archive, dest, password, progress_callback)

# List
entries = manager.list_contents(archive, password)

# Test
is_valid, msg = manager.test_archive(archive, password)

# Analyze
stats = analyzer.analyze(archive)

# Recursive
stats = extractor.extract_recursive(archive, dest)

# Crack
password = cracker.dictionary_attack(archive)
```

Happy archiving!
