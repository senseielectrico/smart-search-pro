# Smart Search Pro - Archive Module

Complete 7-Zip integration for Smart Search Pro with advanced archive management features.

## Features

### 7-Zip Manager (`sevenzip_manager.py`)
Complete wrapper for 7z.exe with full format support:

- **Multi-format support**: 7z, zip, rar, tar, gz, bz2, xz, iso, cab, wim, and 30+ more formats
- **Extract archives** with progress tracking and cancellation
- **Create archives** with custom compression levels (0-9)
- **Password protection** for encrypted archives
- **Split archives** support (multi-volume)
- **List contents** without extracting
- **Test integrity** to verify archive health
- **Extract specific files** or folders
- **Auto-detection** of 7z.exe in Program Files or PATH

### Recursive Extractor (`recursive_extractor.py`)
Handle nested archives automatically:

- **Unlimited depth** extraction (configurable max)
- **Detect archives inside archives** and extract recursively
- **Circular reference protection** prevents infinite loops
- **Preserve directory structure** or flatten output
- **Memory-efficient** streaming for large archives
- **Automatic cleanup** of temporary files
- **Progress tracking** for multi-level extraction

### Archive Analyzer (`archive_analyzer.py`)
Analyze archives without extraction:

- **Calculate total size** (compressed and uncompressed)
- **Count files and folders** in archive
- **Detect nested archives** automatically
- **Identify encrypted files** and entries
- **Compression ratio** calculation
- **File type statistics** (count by extension)
- **Largest files** ranking (top 10)
- **Preview as tree** or text
- **Compare archives** to find differences
- **Find duplicates** in archive by size
- **Estimate extraction size** with overhead

### Password Cracker (`password_cracker.py`)
Recover forgotten passwords (educational purposes only):

- **Dictionary attack** with custom wordlists
- **Brute force** with configurable charset
- **Mask attack** for known patterns (e.g., "password?d?d")
- **Common passwords** database built-in
- **Variations** (case changes, suffixes, leet speak)
- **Multi-threaded** attempts (configurable)
- **Progress reporting** with attempts/sec
- **Resume capability** for long-running cracks
- **Time estimation** for brute force attacks

**WARNING**: Only use on your own archives. Unauthorized password cracking is illegal!

## UI Components

### Archive Panel (`ui/archive_panel.py`)
Full-featured archive manager interface:

- **Tree view** of archive contents
- **Extract all** or selected files
- **Extract here** / extract to folder shortcuts
- **Create archive** wizard with options
- **Compression level** slider (0-9)
- **Password field** for encrypted archives
- **Progress dialog** with percentage and cancel
- **Test archive** integrity button
- **Browse archives** with modern UI
- **Drag and drop** support (planned)

### Extract Dialog (`ui/extract_dialog.py`)
Configure extraction before starting:

- **Destination selector** with quick shortcuts
- **Recursive extraction** toggle
- **Flatten structure** option
- **Conflict handling** (overwrite, skip, rename)
- **Preview** extraction plan
- **Size estimate** before extracting
- **Quick destinations** (Desktop, Downloads, etc.)

## Installation

### Requirements

1. **7-Zip** must be installed:
   - Download from: https://www.7-zip.org/
   - Or install via: `winget install 7zip.7zip`
   - Or via Chocolatey: `choco install 7zip`

2. **Python packages** (already included in Smart Search Pro):
   - PyQt6 (for UI)
   - pathlib, subprocess (built-in)

### Verification

```python
from archive.sevenzip_manager import SevenZipManager

# Check if 7-Zip is detected
manager = SevenZipManager()
print(f"7-Zip found at: {manager.seven_zip_path}")
```

## Usage Examples

### Basic Archive Operations

```python
from archive.sevenzip_manager import SevenZipManager, CompressionLevel, ArchiveFormat

manager = SevenZipManager()

# Create archive
manager.create_archive(
    archive_path='output.7z',
    source_paths=['file1.txt', 'folder/'],
    format=ArchiveFormat.SEVEN_ZIP,
    compression_level=CompressionLevel.MAXIMUM
)

# Extract archive
manager.extract(
    archive_path='archive.zip',
    destination='extracted/',
    overwrite=True
)

# Password-protected archive
manager.create_archive(
    archive_path='secure.7z',
    source_paths=['secrets/'],
    password='mypassword'
)

# Extract with password
manager.extract(
    archive_path='secure.7z',
    destination='decrypted/',
    password='mypassword'
)

# List contents
entries = manager.list_contents('archive.zip')
for entry in entries:
    print(f"{entry['Path']} - {entry['Size']} bytes")

# Test integrity
success, message = manager.test_archive('archive.7z')
print(message)
```

### Archive Analysis

```python
from archive.archive_analyzer import ArchiveAnalyzer

analyzer = ArchiveAnalyzer()

# Analyze archive
stats = analyzer.analyze('large_archive.7z')
print(f"Files: {stats.total_files}")
print(f"Size: {stats.total_size} bytes")
print(f"Compression: {stats.compression_ratio:.1f}%")
print(f"Nested archives: {len(stats.nested_archives)}")

# Get file tree
tree = analyzer.get_file_tree('archive.zip')

# Preview as text
preview = analyzer.preview_as_text('archive.7z', max_items=50)
print(preview)

# Compare archives
comparison = analyzer.compare_archives('v1.zip', 'v2.zip')
print(f"Common files: {comparison['common_files']}")
print(f"Only in v1: {comparison['only_in_archive1']}")

# Estimate extraction size
estimate = analyzer.estimate_extraction_size('huge.7z')
print(f"Will need: {estimate['formatted_size']}")
```

### Recursive Extraction

```python
from archive.recursive_extractor import RecursiveExtractor

extractor = RecursiveExtractor(max_depth=10)

# Extract recursively
stats = extractor.extract_recursive(
    archive_path='nested.7z',
    destination='fully_extracted/',
    flatten=False,  # Preserve structure
    progress_callback=lambda p: print(f"Archive {p.current_archive} - {p.percentage:.1f}%")
)

print(f"Extracted {stats['archives_extracted']} archives")
print(f"Depth: {stats['depth_reached']}")
print(f"Total files: {stats['files_extracted']}")

# Detect nesting without extracting
depth = extractor.detect_nested_depth('archive.7z')
print(f"Maximum nesting: {depth} levels")

# Get nested archive tree
tree = extractor.get_nested_archives_tree('archive.7z')
print(f"Contains {tree['count']} nested archives")
```

### Password Recovery

```python
from archive.password_cracker import PasswordCracker

cracker = PasswordCracker(max_threads=4)

# Dictionary attack
password = cracker.dictionary_attack(
    archive_path='protected.7z',
    wordlist_path='passwords.txt',
    use_common=True,
    use_variations=True,
    progress_callback=lambda p: print(f"Tried {p.attempts} passwords...")
)

if password:
    print(f"Password found: {password}")
else:
    print("Password not found")

# Brute force (use with caution!)
password = cracker.brute_force_attack(
    archive_path='short_password.zip',
    charset='0123456789',  # Only digits
    min_length=4,
    max_length=6
)

# Mask attack (known pattern)
# Pattern: "password" + 2 digits
password = cracker.mask_attack(
    archive_path='protected.7z',
    mask='passworddd'  # d = digit
)

# Estimate brute force time
estimate = cracker.estimate_brute_force_time(
    charset='abcdefghijklmnopqrstuvwxyz',
    min_length=1,
    max_length=8,
    attempts_per_second=100
)
print(f"Estimated time: {estimate['estimated_hours']:.1f} hours")
```

### Progress Tracking

```python
from archive.sevenzip_manager import SevenZipManager, ExtractionProgress

manager = SevenZipManager()

def progress_callback(progress: ExtractionProgress):
    print(f"Progress: {progress.percentage:.1f}%")
    print(f"Current file: {progress.current_file}")
    print(f"Files: {progress.processed_files}/{progress.total_files}")
    print(f"Speed: {progress.speed_mbps:.2f} MB/s")

manager.extract(
    archive_path='large.7z',
    destination='output/',
    progress_callback=progress_callback
)

# Cancel extraction
# In another thread:
# manager.cancel_extraction()
```

## UI Integration

### Add Archive Panel to Main Window

```python
from ui.archive_panel import ArchivePanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Add archive tab
        self.archive_panel = ArchivePanel()
        self.tabs.addTab(self.archive_panel, "Archives")

        # Connect signals
        self.archive_panel.archive_opened.connect(self.on_archive_opened)
        self.archive_panel.extraction_completed.connect(self.on_extraction_done)

    def on_archive_opened(self, path):
        print(f"Opened: {path}")

    def on_extraction_done(self, destination):
        print(f"Extracted to: {destination}")
```

### Extract Dialog Usage

```python
from ui.extract_dialog import ExtractDialog

dialog = ExtractDialog('archive.7z', parent=self)
if dialog.exec() == QDialog.DialogCode.Accepted:
    options = dialog.get_options()

    # Use options for extraction
    extractor.extract_recursive(
        archive_path='archive.7z',
        destination=options['destination'],
        recursive=options['recursive'],
        flatten=options['flatten']
    )
```

## Supported Formats

Full list of supported archive formats:

- **7z** - 7-Zip native format
- **zip** - ZIP archives
- **rar** - WinRAR archives (extract only)
- **tar** - TAR archives
- **gzip** (.gz, .tgz) - GZIP compression
- **bzip2** (.bz2, .tbz2) - BZIP2 compression
- **xz** (.xz, .txz) - XZ compression
- **iso** - ISO disk images
- **cab** - Microsoft Cabinet files
- **wim** - Windows Imaging Format
- **arj** - ARJ archives
- **chm** - CHM help files
- **deb** - Debian packages
- **rpm** - RPM packages
- **dmg** - macOS disk images
- **lzh** - LHA archives
- **msi** - Windows Installer
- **vhd** - Virtual hard disks
- And 15+ more formats...

## Performance Tips

1. **Use appropriate compression levels**:
   - `STORE` (0) for already-compressed files
   - `FAST` (3) for quick compression
   - `NORMAL` (5) for balanced speed/ratio
   - `ULTRA` (9) for maximum compression

2. **Recursive extraction**:
   - Set `max_depth` to prevent excessive nesting
   - Use `flatten=True` for simpler output
   - Monitor progress to detect issues early

3. **Large archives**:
   - Use progress callbacks to avoid UI freezing
   - Run extraction in background thread
   - Enable cancellation for user control

4. **Password cracking**:
   - Try dictionary attack first (much faster)
   - Use mask attack for known patterns
   - Brute force only for short passwords (<8 chars)

## Testing

Run the test suite:

```bash
cd archive
python test_archive_integration.py
```

Tests include:
- 7-Zip detection
- Archive creation (7z, zip, tar)
- Extraction with progress
- Password-protected archives
- Recursive extraction
- Archive analysis
- Password recovery
- Content listing

## Security Considerations

1. **Password Protection**:
   - Use strong passwords (12+ characters)
   - Enable header encryption (`-mhe=on`)
   - Never store passwords in code

2. **Path Traversal**:
   - Always validate extraction paths
   - Check for `..` in archive entries
   - Use `os.path.realpath()` to verify paths

3. **Password Cracker**:
   - Only use on your own archives
   - Respect rate limits
   - Don't use for illegal purposes

4. **Temporary Files**:
   - Always cleanup temp directories
   - Use `tempfile.mkdtemp()` for security
   - Handle cleanup in exception handlers

## Troubleshooting

### 7-Zip not found
```
FileNotFoundError: 7-Zip not found
```
**Solution**: Install 7-Zip from https://www.7-zip.org/ or add 7z.exe to PATH

### Wrong password error
```
ValueError: Wrong password or archive is encrypted
```
**Solution**: Verify password or use password recovery tools

### Extraction fails
```
RuntimeError: Extraction failed
```
**Solution**: Check disk space, permissions, and archive integrity with `test_archive()`

### Circular reference detected
```
Recursive extraction stops early
```
**Solution**: This is normal protection. The same archive won't be extracted twice.

## Future Enhancements

Planned features:
- Drag and drop files into archive panel
- Preview files inside archive (text, images)
- Multi-volume archive support
- Archive repair tools
- Batch operations (extract multiple archives)
- Archive conversion (zip to 7z, etc.)
- Integration with file search results
- Context menu integration

## License

Part of Smart Search Pro - All Rights Reserved

## Credits

- 7-Zip by Igor Pavlov: https://www.7-zip.org/
- Smart Search Pro by [Your Name]
