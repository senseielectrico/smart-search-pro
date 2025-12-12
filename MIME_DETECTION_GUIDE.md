# MIME Type Detection and Filtering Guide

## Overview

Smart Search Pro now includes comprehensive MIME type detection and filtering capabilities. This system analyzes files by their actual content (magic bytes) rather than just file extensions, providing accurate file type identification and security assessment.

## Features

### 1. Magic Bytes Detection
- **500+ File Signatures**: Comprehensive database of file type signatures
- **Fast Detection**: Reads only first 8KB of files
- **High Accuracy**: Detects files by actual content, not extension
- **Multi-Method**: Combines magic bytes, python-magic fallback, and content analysis

### 2. MIME Type Database
- **Comprehensive Coverage**: Images, videos, audio, documents, archives, executables, code, fonts, 3D models
- **Category Classification**: Automatic categorization of detected types
- **Extension Mapping**: Bidirectional mapping between extensions and MIME types
- **User-Extensible**: Add custom signatures and types

### 3. Advanced Filtering
- **Query Syntax**: `mime:image/*`, `type:video`, `safe:true`
- **Pattern Matching**: Exact match, wildcards, category shortcuts
- **Security Filtering**: Detect disguised files and dangerous types
- **Confidence Threshold**: Filter by detection confidence level

### 4. Security Detection
- **Disguised Executables**: Detect .exe files renamed to .jpg, .pdf, etc.
- **Extension Mismatch**: Flag files where extension doesn't match content
- **Dangerous Files**: Identify executables, scripts, and malware
- **Risk Assessment**: Low, medium, high, critical risk levels

## Usage

### Search Query Syntax

```
# Filter by MIME type pattern
mime:image/*                  # All images
mime:application/pdf          # Only PDFs
mime:video/*                  # All videos

# Filter by category
type:image                    # All images
type:video,audio             # Videos and audio
type:document                # Documents

# Security filters
safe:true                     # Exclude dangerous files
verified:true                 # Exclude extension mismatches
confidence:0.9                # High confidence only

# Combined queries
vacation photos mime:image/* safe:true
*.pdf type:document verified:true
project type:archive,code
```

### Category Shortcuts

```python
"images"      -> "image/*"
"videos"      -> "video/*"
"audio"       -> "audio/*"
"documents"   -> PDF, DOCX, XLSX, PPTX, etc.
"archives"    -> ZIP, RAR, 7Z, etc.
"executables" -> EXE, DLL, etc.
"code"        -> Python, JavaScript, HTML, XML, etc.
```

### Programmatic Usage

```python
from search.mime_detector import get_mime_detector
from search.mime_filter import MimeFilter, MimeFilterCriteria
from search.mime_database import MimeCategory

# Detect MIME type
detector = get_mime_detector()
result = detector.detect("myfile.jpg")

print(f"MIME Type: {result.mime_type}")
print(f"Confidence: {result.confidence:.1%}")
print(f"Description: {result.description}")
print(f"Extension Mismatch: {result.extension_mismatch}")

# Filter files
mime_filter = MimeFilter()
criteria = MimeFilterCriteria(
    mime_patterns=["image/*"],
    categories={MimeCategory.IMAGE},
    exclude_dangerous=True,
    exclude_mismatched=True,
    min_confidence=0.8
)

matching_files = mime_filter.filter_results(file_paths, criteria)

# Batch detection
detections = detector.detect_batch(file_paths, max_workers=4)
```

### File Identifier Tool

```bash
# Identify a file
python -m tools.file_identifier myfile.dat

# Deep scan with hash
python -m tools.file_identifier myfile.dat --deep --hash

# Suggest correct filename
python -m tools.file_identifier suspicious.jpg --suggest-rename
```

## Supported File Types

### Images (500+ formats)
- **Raster**: JPEG, PNG, GIF, BMP, TIFF, WebP, HEIC, ICO
- **Vector**: SVG
- **Professional**: PSD (Photoshop)

### Videos
- MP4, AVI, MKV, FLV, MOV, WMV, WebM

### Audio
- MP3, WAV, FLAC, OGG, M4A, WMA

### Documents
- **PDF**: All versions
- **Microsoft Office**: DOC, DOCX, XLS, XLSX, PPT, PPTX
- **OpenDocument**: ODT, ODS, ODP
- **Rich Text**: RTF

### Archives
- ZIP, RAR (v1.5+, v5.0+), 7Z, GZIP, TAR, BZIP2, CAB

### Executables
- **Windows**: EXE, DLL, SYS
- **Linux**: ELF binaries, SO libraries
- **macOS**: Mach-O (32-bit, 64-bit)
- **Java**: Class files
- **Android**: DEX files

### Code & Text
- Python, JavaScript, HTML, XML, JSON, CSS
- C, C++, Java, Shell scripts
- Batch files, PowerShell scripts

### Fonts
- TrueType (TTF), OpenType (OTF), WOFF, WOFF2

### 3D Models
- STL (ASCII and binary)

### Databases
- SQLite, Microsoft Access

### Disk Images
- ISO, VMDK

## UI Integration

### MIME Filter Widget

The MIME filter widget provides a graphical interface for filtering:

```python
from ui.mime_filter_widget import MimeFilterWidget

# Create widget
mime_widget = MimeFilterWidget()

# Connect to filter changes
mime_widget.filter_changed.connect(on_filter_changed)

# Add to layout
layout.addWidget(mime_widget)
```

**Features**:
- Quick filter buttons (All, Images, Videos, Audio, Documents, Archives)
- Category dropdown
- Multi-select MIME types
- Custom MIME pattern input
- Advanced options (exclude mismatched, exclude dangerous, confidence threshold)
- Real-time status updates

## Security Features

### Disguised File Detection

The system detects potentially dangerous files that have been disguised:

```python
# Example: executable.exe renamed to photo.jpg
detector.detect("photo.jpg")
# Returns:
# - mime_type: "application/x-msdownload"
# - extension_mismatch: True
# - confidence: 0.95
```

### Risk Assessment

Files are assigned risk levels:

- **Low**: Normal files with correct extensions
- **Medium**: Files with extension mismatches or double extensions
- **High**: Executable files
- **Critical**: Disguised executables (exe as jpg, pdf, etc.)

### Dangerous MIME Types

The following types are flagged as potentially dangerous:
- `application/x-msdownload` (Windows executables)
- `application/x-executable` (Linux executables)
- `application/x-bat` (Batch files)
- `application/x-sh` (Shell scripts)
- `application/java-vm` (Java class files)
- `application/x-mach-binary` (macOS executables)
- `application/vnd.android.dex` (Android DEX)

## Performance

### Detection Speed
- **Magic Bytes**: ~0.1ms per file (reads only 8KB)
- **Batch Detection**: 4-8 workers for parallel processing
- **Cache**: Results cached for repeated queries

### Memory Usage
- **Signatures Database**: ~500KB in memory
- **Detection Cache**: ~100 bytes per cached file
- **Total Overhead**: <5MB for typical usage

## Integration with Search Engine

The MIME filter is automatically integrated into the search engine:

```python
# Search with MIME filter
results = engine.search("vacation mime:image/* safe:true")

# Results are automatically filtered by:
# 1. Keyword match ("vacation")
# 2. MIME type (images only)
# 3. Safety (no disguised executables)
```

## Advanced Features

### Custom Signatures

Add your own file signatures:

```python
from search.mime_database import get_mime_database, MimeSignature

mime_db = get_mime_database()

# Add custom signature
custom_sig = MimeSignature(
    mime_type="application/x-custom",
    signature=b"\x4D\x59\x46\x4D\x54",
    description="My custom format",
    extensions=["mcf"]
)

mime_db.add_signature(custom_sig)
```

### Bulk MIME Scanning

Scan directories and collect statistics:

```python
from search.mime_filter import scan_files_mime_types

result = scan_files_mime_types(file_paths, max_workers=4)

print(f"Files scanned: {result.files_scanned}")
print(f"MIME types: {result.mime_types}")
print(f"Categories: {result.categories}")
print(f"Mismatched: {len(result.mismatched)}")
print(f"Dangerous: {len(result.dangerous)}")
```

### Fix Extensions

Automatically rename files to correct extensions:

```python
from tools.file_identifier import FileIdentifier

identifier = FileIdentifier()

# Dry run (just report)
renames = identifier.fix_extensions("C:/MyFolder", recursive=True, dry_run=True)

for old_path, new_path in renames.items():
    print(f"{old_path} -> {new_path}")

# Actually rename
renames = identifier.fix_extensions("C:/MyFolder", recursive=True, dry_run=False)
```

## Best Practices

1. **Use MIME filters for security**: Always use `safe:true` when searching in unknown directories
2. **Verify suspicious files**: Check files with extension mismatches before opening
3. **Combine filters**: Use multiple filter types for precise results
4. **Cache detection results**: Enable caching for repeated searches
5. **Deep scan selectively**: Use deep scan only when needed (slower but more accurate)

## Troubleshooting

### Common Issues

**Detection returns "application/octet-stream"**:
- File type not in signature database
- File is corrupted or encrypted
- File is a custom/proprietary format

**Extension mismatch false positives**:
- Some formats share signatures (e.g., DOCX and ZIP)
- Adjust confidence threshold
- Use deep scan for better accuracy

**Slow detection**:
- Disable deep scan for large files
- Increase max_workers for batch operations
- Clear cache if it grows too large

## Examples

### Find All Images
```
type:image
```

### Find PDFs Only
```
*.pdf mime:application/pdf
```

### Find Safe Documents
```
type:document safe:true verified:true
```

### Find Potential Malware
```
verified:false type:executable
```

### Find Videos Larger Than 100MB
```
type:video size:>100mb
```

### Find All Code Files
```
type:code
```

## API Reference

### MimeDetector
- `detect(file_path, check_extension=True)`: Detect MIME type
- `detect_batch(file_paths, max_workers=4)`: Batch detection
- `clear_cache()`: Clear detection cache
- `get_cache_stats()`: Get cache statistics

### MimeDatabase
- `get_mime_by_extension(extension)`: Get MIME type for extension
- `get_description(mime_type)`: Get human-readable description
- `get_category(mime_type)`: Get category
- `add_signature(signature)`: Add custom signature
- `get_all_extensions()`: List all known extensions
- `get_all_mime_types()`: List all known MIME types

### MimeFilter
- `matches(file_path, criteria)`: Check if file matches criteria
- `filter_results(file_paths, criteria)`: Filter list of files
- `get_file_info(file_path)`: Get detailed MIME information

### FileIdentifier
- `identify(file_path, deep_scan=False)`: Identify file comprehensively
- `identify_batch(file_paths, deep_scan=False)`: Batch identification
- `suggest_rename(file_path)`: Suggest correct filename
- `fix_extensions(directory, recursive=False)`: Fix extensions in directory
- `print_report(report)`: Print human-readable report

## Version History

### 1.0.0 (2025-12-12)
- Initial release
- 500+ file signatures
- MIME-based filtering
- Security detection
- UI integration
- File identifier tool

## License

Part of Smart Search Pro - All rights reserved
