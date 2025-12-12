# MIME Detection System

## Quick Start

### Detect MIME Type

```python
from search.mime_detector import get_mime_detector

detector = get_mime_detector()
result = detector.detect("myfile.jpg")

print(f"MIME: {result.mime_type}")
print(f"Confidence: {result.detection_confidence:.1%}")
```

### Filter Files by MIME Type

```python
from search.mime_filter import MimeFilter, MimeFilterCriteria
from search.mime_database import MimeCategory

mime_filter = MimeFilter()

# Filter for images only
criteria = MimeFilterCriteria(
    mime_patterns=["image/*"],
    categories=set()
)

matching_files = mime_filter.filter_results(file_paths, criteria)
```

### Search with MIME Filters

```
# Search query syntax
vacation mime:image/*           # Images only
reports type:document           # Documents only
downloads safe:true            # No dangerous files
photos verified:true           # No extension mismatches
```

### Identify Files

```bash
# Command line
python -m tools.file_identifier suspicious.exe --deep

# Programmatic
from tools.file_identifier import FileIdentifier

identifier = FileIdentifier()
report = identifier.identify("file.dat", deep_scan=True)
identifier.print_report(report)
```

## Architecture

### Components

```
search/
├── mime_database.py      # 500+ file signatures
├── mime_detector.py      # Detection engine
├── mime_filter.py        # Filtering logic
└── MIME_README.md        # This file

ui/
└── mime_filter_widget.py # Qt widget

tools/
└── file_identifier.py    # Comprehensive identification
```

### Data Flow

```
File Path
    ↓
[MIME Detector]
    ├─→ Read magic bytes (first 8KB)
    ├─→ Check against signature database
    ├─→ Fallback to python-magic
    ├─→ Fallback to extension
    └─→ Fallback to content analysis
    ↓
Detection Result
    ├─→ MIME type
    ├─→ Confidence score
    ├─→ Extension mismatch flag
    └─→ Detection method
    ↓
[MIME Filter] (optional)
    ├─→ Pattern matching
    ├─→ Category filtering
    ├─→ Security filtering
    └─→ Confidence filtering
    ↓
Filtered Results
```

## File Signatures

### How Signatures Work

Files are identified by "magic bytes" - specific byte sequences at the beginning of files:

```python
# JPEG signature
b"\xFF\xD8\xFF\xE0"  # JFIF format

# PNG signature
b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"

# PDF signature
b"%PDF"

# Windows EXE signature
b"\x4D\x5A"  # "MZ"
```

### Signature Database

The system includes 500+ signatures covering:

- **Images**: JPEG, PNG, GIF, BMP, TIFF, WebP, HEIC, SVG, PSD
- **Videos**: MP4, AVI, MKV, FLV, MOV, WMV
- **Audio**: MP3, WAV, FLAC, OGG, M4A, WMA
- **Documents**: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, RTF, ODT
- **Archives**: ZIP, RAR, 7Z, GZIP, TAR, BZIP2, CAB
- **Executables**: EXE, DLL, ELF, Mach-O, Java Class, DEX
- **Code**: Python, JavaScript, HTML, XML, JSON
- **Fonts**: TTF, OTF, WOFF, WOFF2
- **3D Models**: STL
- **Databases**: SQLite, Access

## Detection Methods

### 1. Magic Bytes (Primary)

Fast and accurate - reads only first 8KB:

```python
detector.detect("file.jpg")
# Returns: mime_type="image/jpeg", confidence=0.95, detected_by="magic"
```

### 2. python-magic (Fallback)

Uses libmagic if available:

```python
# Requires: pip install python-magic-bin (Windows)
detector.detect("file.dat")
# Returns: mime_type="application/octet-stream", confidence=0.9, detected_by="python-magic"
```

### 3. Extension (Fallback)

Based on file extension:

```python
detector.detect("file.jpg")
# Returns: mime_type="image/jpeg", confidence=0.7, detected_by="extension"
```

### 4. Content Analysis (Fallback)

Analyzes file content for text files:

```python
detector.detect("README.txt")
# Returns: mime_type="text/plain", confidence=0.6, detected_by="content"
```

## Filter Criteria

### MIME Patterns

```python
# Exact match
MimeFilterCriteria(mime_patterns=["image/jpeg"])

# Wildcard
MimeFilterCriteria(mime_patterns=["image/*"])

# Multiple patterns
MimeFilterCriteria(mime_patterns=["image/*", "video/*"])
```

### Categories

```python
from search.mime_database import MimeCategory

# Single category
MimeFilterCriteria(categories={MimeCategory.IMAGE})

# Multiple categories
MimeFilterCriteria(categories={MimeCategory.IMAGE, MimeCategory.VIDEO})
```

### Security Options

```python
# Exclude dangerous files
MimeFilterCriteria(exclude_dangerous=True)

# Exclude extension mismatches
MimeFilterCriteria(exclude_mismatched=True)

# Minimum confidence
MimeFilterCriteria(min_confidence=0.8)

# Combined
MimeFilterCriteria(
    mime_patterns=["image/*"],
    exclude_dangerous=True,
    exclude_mismatched=True,
    min_confidence=0.9
)
```

## Security Features

### Disguised File Detection

Detects executables disguised as safe files:

```python
# photo.jpg is actually an .exe
result = detector.detect("photo.jpg")

if result.extension_mismatch:
    print("WARNING: Extension doesn't match content!")
    print(f"Real type: {result.mime_type}")
```

### Risk Assessment

Files are assigned risk levels:

```python
identifier = FileIdentifier()
report = identifier.identify("suspicious.pdf")

print(f"Risk Level: {report.risk_level}")  # low, medium, high, critical
print(f"Dangerous: {report.is_dangerous}")
print(f"Reasons: {report.risk_reasons}")
```

### Dangerous MIME Types

Automatically flagged:
- Windows executables (.exe, .dll)
- Linux executables (ELF)
- Batch/shell scripts
- Java class files
- macOS executables

## Performance

### Speed

```
Operation               Time        Notes
-----------------      -------     ---------------------
Single detection       0.1 ms      Reads 8KB
Batch (100 files)      50 ms       4 workers
Batch (1000 files)     400 ms      4 workers
Cache hit              0.01 ms     In-memory lookup
```

### Memory

```
Component              Size
------------------    --------
Signature database    ~500 KB
Detection cache       ~100 bytes per file
Total overhead        <5 MB typical
```

### Optimization Tips

1. **Use batch detection** for multiple files
2. **Enable caching** for repeated searches
3. **Adjust workers** based on CPU cores
4. **Disable deep scan** for large files

```python
# Optimized batch detection
detector = get_mime_detector(use_cache=True)
results = detector.detect_batch(files, max_workers=8)
```

## Integration Examples

### With Search Engine

```python
from search.engine import SearchEngine

engine = SearchEngine()

# Search with MIME filter
results = engine.search("vacation mime:image/* safe:true")
```

### With UI

```python
from ui.mime_filter_widget import MimeFilterWidget

# Create widget
mime_widget = MimeFilterWidget()

# Connect to search
mime_widget.filter_changed.connect(on_filter_changed)

# Add to layout
layout.addWidget(mime_widget)
```

### Bulk Operations

```python
from search.mime_filter import scan_files_mime_types

# Scan directory
result = scan_files_mime_types(file_paths, max_workers=4)

print(f"Total files: {result.files_scanned}")
print(f"MIME types: {result.mime_types}")
print(f"Mismatched: {len(result.mismatched)}")
print(f"Dangerous: {len(result.dangerous)}")
```

## Custom Signatures

### Add Custom Type

```python
from search.mime_database import get_mime_database, MimeSignature

mime_db = get_mime_database()

# Add custom signature
custom = MimeSignature(
    mime_type="application/x-myformat",
    signature=b"\x4D\x59\x46\x4D\x54",
    offset=0,
    description="My custom format",
    extensions=["mcf", "myf"]
)

mime_db.add_signature(custom)
```

### Custom Detection Logic

```python
from search.mime_detector import MimeDetector

class CustomDetector(MimeDetector):
    def _detect_uncached(self, file_path, check_extension):
        # Custom logic here
        result = super()._detect_uncached(file_path, check_extension)

        # Post-process
        if result.mime_type == "application/octet-stream":
            # Try custom detection
            pass

        return result
```

## Troubleshooting

### Issue: Low Detection Confidence

**Cause**: File type not in database or corrupted file

**Solution**:
```python
# Use deep scan
report = identifier.identify(file_path, deep_scan=True)

# Or add custom signature
mime_db.add_signature(custom_sig)
```

### Issue: False Extension Mismatch

**Cause**: File formats share signatures (e.g., DOCX is ZIP)

**Solution**:
```python
# Adjust confidence threshold
criteria = MimeFilterCriteria(min_confidence=0.9)

# Or exclude mismatch filter
criteria = MimeFilterCriteria(exclude_mismatched=False)
```

### Issue: Slow Batch Detection

**Cause**: Too many workers or disk I/O bottleneck

**Solution**:
```python
# Reduce workers for HDD
results = detector.detect_batch(files, max_workers=2)

# Or enable caching
detector = get_mime_detector(use_cache=True)
```

## API Reference

### MimeDetector

```python
class MimeDetector:
    def detect(file_path: str, check_extension: bool = True) -> DetectionResult
    def detect_batch(file_paths: list, max_workers: int = 4) -> dict
    def clear_cache() -> None
    def get_cache_stats() -> dict
```

### MimeDatabase

```python
class MimeDatabase:
    def get_mime_by_extension(extension: str) -> Optional[str]
    def get_description(mime_type: str) -> str
    def get_category(mime_type: str) -> MimeCategory
    def add_signature(signature: MimeSignature) -> None
    def get_all_extensions() -> List[str]
    def get_all_mime_types() -> List[str]
```

### MimeFilter

```python
class MimeFilter:
    def matches(file_path: str, criteria: MimeFilterCriteria) -> bool
    def filter_results(file_paths: list, criteria: MimeFilterCriteria) -> list
    def get_file_info(file_path: str) -> dict
```

### FileIdentifier

```python
class FileIdentifier:
    def identify(file_path: str, deep_scan: bool = False) -> FileIdentificationReport
    def identify_batch(file_paths: list, deep_scan: bool = False) -> dict
    def suggest_rename(file_path: str) -> Optional[str]
    def fix_extensions(directory: str, recursive: bool = False, dry_run: bool = True) -> dict
    def print_report(report: FileIdentificationReport) -> None
```

## Testing

### Run Tests

```bash
# Run all MIME tests
python test_mime_detection.py

# Run interactive demo
python demo_mime_detection.py

# Run specific demo
python demo_mime_detection.py 1
```

### Test Coverage

- Basic MIME detection
- Extension mismatch detection
- Batch processing
- Pattern matching
- Category filtering
- Security filtering
- Query parsing
- File identification
- Rename suggestions

## Version History

### 1.0.0 (2025-12-12)
- Initial release
- 500+ file signatures
- Multi-method detection
- Security filtering
- UI widget
- File identifier tool

## License

Part of Smart Search Pro - All rights reserved
