# MIME Detection - Quick Start Guide

## Installation

No installation required! The MIME detection system is built-in with zero dependencies.

### Optional Enhancements

```bash
# Enhanced detection (optional)
pip install python-magic-bin

# Image corruption detection (optional)
pip install Pillow
```

## 5-Minute Tutorial

### 1. Basic Detection

```python
from search.mime_detector import get_mime_detector

# Detect MIME type
detector = get_mime_detector()
result = detector.detect("photo.jpg")

print(f"Type: {result.mime_type}")
print(f"Confidence: {result.detection_confidence:.1%}")
```

**Output:**
```
Type: image/jpeg
Confidence: 95.0%
```

### 2. Search with MIME Filters

```python
from search.engine import SearchEngine

engine = SearchEngine()

# Find all images
results = engine.search("vacation mime:image/*")

# Find PDFs only
results = engine.search("report mime:application/pdf")

# Find safe documents
results = engine.search("downloads type:document safe:true")
```

### 3. Detect Disguised Files

```python
# suspicious.jpg is actually an .exe file
result = detector.detect("suspicious.jpg")

if result.extension_mismatch:
    print(f"WARNING: File is actually {result.mime_type}")
    print(f"Expected: .{result.expected_extensions[0]}")
```

**Output:**
```
WARNING: File is actually application/x-msdownload
Expected: .exe
```

### 4. Comprehensive File Analysis

```python
from tools.file_identifier import FileIdentifier

identifier = FileIdentifier()
report = identifier.identify("unknown_file.dat", deep_scan=True)

# Print detailed report
identifier.print_report(report)
```

**Output:**
```
======================================================================
FILE IDENTIFICATION REPORT
======================================================================
File: unknown_file.dat
Path: C:/Downloads/unknown_file.dat
Size: 1.2 MB

MIME Type Detection:
  Type: application/x-msdownload
  Category: executable
  Description: Windows executable
  Confidence: 95.0%
  Method: magic

Extension Analysis:
  Current: .dat
  Expected: .exe, .dll, .sys
  Status: ✗ Incorrect
  Suggested: .exe

Security Assessment:
  Risk Level: CRITICAL
  Dangerous: Yes
  Suspicious: Yes
  Reasons:
    - Executable file
    - Extension doesn't match detected type
    - Executable disguised as safe file type
======================================================================
```

### 5. UI Integration

```python
from PyQt6.QtWidgets import QApplication
from ui.mime_filter_widget import MimeFilterWidget

app = QApplication([])
widget = MimeFilterWidget()

# Connect to search
widget.filter_changed.connect(lambda criteria: search_with_filter(criteria))

widget.show()
app.exec()
```

## Query Syntax

### MIME Type Patterns

```
mime:image/*              # All images
mime:video/*              # All videos
mime:application/pdf      # PDFs only
```

### Category Shortcuts

```
type:image               # All images
type:video               # All videos
type:audio               # All audio
type:document            # Documents
type:archive             # Archives
```

### Security Filters

```
safe:true                # No dangerous files
verified:true            # No extension mismatches
confidence:0.9           # High confidence only
```

### Combined Queries

```
vacation mime:image/* safe:true
report type:document verified:true
*.mp4 type:video size:>100mb
downloads safe:true confidence:0.8
```

## Common Use Cases

### 1. Find All Images in Downloads

```python
results = engine.search("C:/Downloads mime:image/*")
```

### 2. Find Potentially Dangerous Files

```python
from search.mime_filter import scan_files_mime_types

files = list(Path("C:/Downloads").rglob("*"))
result = scan_files_mime_types([str(f) for f in files])

print(f"Dangerous files: {len(result.dangerous)}")
for file in result.dangerous:
    print(f"  {file}")
```

### 3. Fix Wrong Extensions

```python
identifier = FileIdentifier()

# Dry run (just report)
renames = identifier.fix_extensions("C:/Downloads", recursive=True, dry_run=True)

print(f"Found {len(renames)} files with wrong extensions")
for old, new in renames.items():
    print(f"{old} -> {new}")

# Actually rename
renames = identifier.fix_extensions("C:/Downloads", recursive=True, dry_run=False)
print(f"Renamed {len(renames)} files")
```

### 4. Batch Analysis

```python
# Analyze all files in directory
files = list(Path("C:/Downloads").glob("*"))
reports = identifier.identify_batch([str(f) for f in files], deep_scan=True)

# Show dangerous files
for path, report in reports.items():
    if report.is_dangerous:
        print(f"{Path(path).name}: Risk Level {report.risk_level.upper()}")
```

## Command Line

### File Identifier

```bash
# Identify file
python -m tools.file_identifier myfile.dat

# Deep scan with hash
python -m tools.file_identifier myfile.dat --deep --hash

# Suggest correct filename
python -m tools.file_identifier suspicious.jpg --suggest-rename
```

### Run Tests

```bash
# Run all tests
python test_mime_detection.py

# Run demo
python demo_mime_detection.py
```

## Performance Tips

### 1. Enable Caching

```python
detector = get_mime_detector(use_cache=True)
```

### 2. Batch Processing

```python
# Process multiple files at once
results = detector.detect_batch(file_paths, max_workers=4)
```

### 3. Adjust Workers

```python
# More workers for SSD
results = detector.detect_batch(files, max_workers=8)

# Fewer workers for HDD
results = detector.detect_batch(files, max_workers=2)
```

### 4. Skip Deep Scan for Large Files

```python
# Fast scan only
report = identifier.identify(file_path, deep_scan=False)
```

## Security Best Practices

### 1. Always Check Downloads

```python
# Scan downloads directory
files = list(Path("C:/Downloads").rglob("*"))
result = scan_files_mime_types([str(f) for f in files])

if result.dangerous:
    print(f"WARNING: Found {len(result.dangerous)} dangerous files!")
    for file in result.dangerous:
        print(f"  {file}")
```

### 2. Verify Before Opening

```python
def safe_to_open(file_path):
    """Check if file is safe to open."""
    report = identifier.identify(file_path)

    if report.is_dangerous:
        print(f"DANGER: {report.risk_level.upper()} risk")
        return False

    if report.extension_mismatch:
        print("WARNING: Extension doesn't match content")
        return False

    return True

if safe_to_open("suspicious.pdf"):
    # Open file
    pass
```

### 3. Use Safe Filter in Searches

```python
# Always use safe:true for unknown directories
results = engine.search("C:/Downloads safe:true")
```

## Troubleshooting

### Detection Returns "Unknown"

```python
# Try deep scan
report = identifier.identify(file_path, deep_scan=True)

# Check confidence
if report.detection_confidence < 0.7:
    print("Low confidence detection")
```

### False Positives

```python
# Increase confidence threshold
criteria = MimeFilterCriteria(min_confidence=0.9)
```

### Slow Batch Processing

```python
# Reduce workers
results = detector.detect_batch(files, max_workers=2)

# Or disable deep scan
reports = identifier.identify_batch(files, deep_scan=False)
```

## Examples

### Example 1: Security Audit

```python
from pathlib import Path
from search.mime_filter import scan_files_mime_types

def audit_directory(directory):
    """Perform security audit on directory."""
    files = [str(f) for f in Path(directory).rglob("*") if f.is_file()]

    print(f"Scanning {len(files)} files...")
    result = scan_files_mime_types(files, max_workers=4)

    print(f"\nResults:")
    print(f"  Total scanned: {result.files_scanned}")
    print(f"  Extension mismatches: {len(result.mismatched)}")
    print(f"  Dangerous files: {len(result.dangerous)}")

    if result.dangerous:
        print("\nDangerous files found:")
        for file in result.dangerous:
            print(f"  - {file}")

audit_directory("C:/Downloads")
```

### Example 2: Photo Organizer

```python
from pathlib import Path
from search.mime_detector import get_mime_detector

def organize_photos(source_dir, dest_dir):
    """Organize photos by type."""
    detector = get_mime_detector()

    for file in Path(source_dir).rglob("*"):
        if not file.is_file():
            continue

        result = detector.detect(str(file))

        if result.mime_type.startswith("image/"):
            # Determine subdirectory by format
            subdir = result.mime_type.split("/")[1]  # e.g., "jpeg", "png"
            dest = Path(dest_dir) / subdir / file.name

            dest.parent.mkdir(parents=True, exist_ok=True)
            print(f"Moving {file.name} to {subdir}/")
            # file.rename(dest)

organize_photos("C:/Unsorted", "C:/Photos")
```

### Example 3: Duplicate Finder (by content type)

```python
from collections import defaultdict
from pathlib import Path

def find_duplicates_by_type(directory):
    """Find duplicate files by MIME type and size."""
    detector = get_mime_detector()
    files_by_type_size = defaultdict(list)

    for file in Path(directory).rglob("*"):
        if not file.is_file():
            continue

        result = detector.detect(str(file))
        size = file.stat().st_size

        key = (result.mime_type, size)
        files_by_type_size[key].append(file)

    # Show potential duplicates
    for (mime_type, size), files in files_by_type_size.items():
        if len(files) > 1:
            print(f"\nPotential duplicates ({mime_type}, {size} bytes):")
            for file in files:
                print(f"  {file}")

find_duplicates_by_type("C:/Downloads")
```

## Next Steps

1. **Read full guide**: See `MIME_DETECTION_GUIDE.md` for complete documentation
2. **Run tests**: `python test_mime_detection.py`
3. **Try demos**: `python demo_mime_detection.py`
4. **Explore API**: See `search/MIME_README.md` for technical details

## Support

For issues or questions:
1. Check `MIME_DETECTION_GUIDE.md` for detailed documentation
2. Run `python demo_mime_detection.py` for interactive examples
3. Check test suite: `python test_mime_detection.py`

## Version

MIME Detection System 1.0.0 (2025-12-12)
