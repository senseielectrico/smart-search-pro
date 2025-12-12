# ExifTool Integration - Complete Guide

## Overview

Smart Search Pro now includes complete ExifTool integration for forensic metadata analysis. This powerful feature enables extraction, analysis, editing, and reporting of metadata from 400+ file formats.

## Features

### 1. ExifTool Wrapper (`tools/exiftool_wrapper.py`)

Core wrapper for ExifTool with automatic path detection.

**Key Features:**
- Automatic ExifTool detection (PATH, Program Files, custom locations)
- Fallback paths for common installations
- Extract metadata from any supported file
- Write/modify metadata fields
- Remove all metadata (strip)
- Copy metadata between files
- Batch processing
- JSON output parsing
- GPS coordinate extraction
- Date/time normalization
- Thumbnail extraction
- Support for 400+ file formats

**Usage:**
```python
from tools.exiftool_wrapper import ExifToolWrapper

# Initialize (auto-detects ExifTool)
exiftool = ExifToolWrapper()

# Or specify custom path
exiftool = ExifToolWrapper(r"D:\Tools\ExifTool\exiftool.exe")

# Extract metadata
metadata = exiftool.extract_metadata("photo.jpg")

# Get specific tag
camera = exiftool.get_tag("photo.jpg", "Make")

# Set metadata
exiftool.set_tag("photo.jpg", "Artist", "John Doe")

# Remove all metadata
exiftool.remove_all_metadata("photo.jpg")

# Copy metadata
exiftool.copy_metadata("source.jpg", "target.jpg")

# Extract thumbnail
exiftool.extract_thumbnail("photo.jpg", "thumb.jpg")

# Batch processing
metadata_map = exiftool.extract_metadata_batch([
    "photo1.jpg",
    "photo2.jpg",
    "photo3.jpg"
])
```

### 2. Metadata Analyzer (`tools/metadata_analyzer.py`)

Deep forensic analysis of file metadata.

**Features:**
- Camera/device identification
- GPS coordinate extraction with map links
- Date/time analysis with consistency checks
- Software fingerprinting
- Author/creator information extraction
- Copyright data extraction
- Hidden metadata detection (emails, URLs, IP addresses)
- Anomaly detection (tampering indicators)
- Device fingerprinting
- Metadata comparison between files
- Timeline reconstruction
- Duplicate detection by metadata similarity

**Usage:**
```python
from tools.metadata_analyzer import MetadataAnalyzer

analyzer = MetadataAnalyzer()

# Analyze single file
analysis = analyzer.analyze_file("photo.jpg")

# Access results
camera_info = analysis['camera_info']
gps_info = analysis['gps_info']
datetime_info = analysis['datetime_info']
anomalies = analysis['anomalies']
fingerprint = analysis['device_fingerprint']

# Compare two files
comparison = analyzer.compare_metadata("file1.jpg", "file2.jpg")
similarity_score = comparison['similarity_score']

# Create timeline
timeline = analyzer.create_timeline([
    "photo1.jpg",
    "photo2.jpg",
    "photo3.jpg"
])

# Detect duplicates
duplicates = analyzer.detect_duplicates_by_metadata(
    file_list,
    tolerance=0.9
)
```

### 3. Metadata Editor (`tools/metadata_editor.py`)

Advanced metadata manipulation and batch operations.

**Features:**
- Edit single or multiple fields
- Batch editing across files
- Pattern-based editing with templates
- File anonymization (remove identifying info)
- Date shifting (correct timezone/clock errors)
- Geotagging from GPX tracks
- Template system for reusable metadata sets
- Batch metadata copying
- Bulk metadata stripping
- Smart file renaming based on metadata

**Usage:**
```python
from tools.metadata_editor import MetadataEditor

editor = MetadataEditor()

# Edit single field
editor.edit_field("photo.jpg", "Artist", "John Doe")

# Edit multiple fields
editor.edit_multiple_fields("photo.jpg", {
    "Artist": "John Doe",
    "Copyright": "2024 John Doe",
    "Description": "Beautiful sunset"
})

# Batch edit
editor.batch_edit(
    ["photo1.jpg", "photo2.jpg"],
    {"Artist": "John Doe"}
)

# Anonymize file (remove identifying info)
editor.anonymize_file("photo.jpg")

# Shift dates by 1 hour
from datetime import timedelta
editor.shift_dates(
    ["photo1.jpg", "photo2.jpg"],
    offset=timedelta(hours=1)
)

# Geotag from GPX track
editor.geotag_from_gpx(
    ["photo1.jpg", "photo2.jpg"],
    "track.gpx"
)

# Create and apply template
editor.create_template('vacation', {
    "Artist": "John Doe",
    "Copyright": "2024",
    "Keywords": "vacation, travel"
})

editor.apply_template(file_list, 'vacation')

# Rename by metadata
renames = editor.rename_by_metadata(
    file_list,
    pattern="{Make}_{Model}_{DateTimeOriginal}"
)
```

### 4. Forensic Report Generator (`tools/forensic_report.py`)

Generate comprehensive forensic reports.

**Features:**
- Single file reports
- Batch file reports
- Timeline reports (chronological activity)
- Device identification reports
- GPS location reports with maps
- Multiple output formats (HTML, Text, JSON)
- Professional formatting
- Interactive HTML reports with maps
- Export capabilities

**Usage:**
```python
from tools.forensic_report import ForensicReportGenerator

report_gen = ForensicReportGenerator()

# Generate single file report
html_report = report_gen.generate_file_report(
    "photo.jpg",
    output_format='html'
)

# Generate batch report
batch_report = report_gen.generate_batch_report(
    ["photo1.jpg", "photo2.jpg", "photo3.jpg"],
    output_format='html'
)

# Timeline report
timeline_report = report_gen.generate_timeline_report(
    file_list,
    output_format='html'
)

# Device identification report
device_report = report_gen.generate_device_report(
    file_list,
    output_format='html'
)

# GPS location report
gps_report = report_gen.generate_gps_report(
    file_list,
    output_format='html'
)

# Save report
report_gen.save_report(html_report, "forensic_report.html")
```

### 5. Metadata Panel UI (`ui/metadata_panel.py`)

Comprehensive metadata viewer and editor UI.

**Features:**
- Tree view of all metadata categories
- Search within metadata
- Export to JSON/CSV
- Side-by-side comparison view
- GPS map preview with links
- Edit mode with save/cancel
- Forensic analysis tab
- Batch operations toolbar
- Report generation

**Tabs:**
1. **Metadata** - Browse and edit all metadata fields
2. **Forensic Analysis** - Run forensic analysis and view results
3. **Comparison** - Compare metadata between two files

### 6. ExifTool Dialog (`ui/exiftool_dialog.py`)

ExifTool operations and configuration dialog.

**Features:**
- Configure ExifTool path
- Test ExifTool installation
- View supported formats
- Strip metadata wizard
- Batch rename by metadata
- Custom command builder
- Progress tracking

**Tabs:**
1. **Configuration** - Set up ExifTool path and test
2. **Strip Metadata** - Remove metadata from files
3. **Batch Rename** - Rename files using metadata patterns
4. **Custom Command** - Execute custom ExifTool commands

## Installation

### 1. Install ExifTool

**Option A: Default Location (Recommended)**
```
1. Download ExifTool from: https://exiftool.org/
2. Extract to: D:\MAIN_DATA_CENTER\Dev_Tools\ExifTool\
3. Ensure ExifTool.exe is in that directory
```

**Option B: Add to PATH**
```
1. Download and extract ExifTool
2. Add the directory to your system PATH
3. Restart Smart Search Pro
```

**Option C: Custom Location**
```
1. Download and extract ExifTool anywhere
2. In Smart Search Pro, use ExifTool Dialog to set custom path
3. Test the installation
```

### 2. Verify Installation

Run the test suite:
```bash
python test_exiftool_integration.py
```

Or in Smart Search Pro:
1. Open ExifTool Dialog (Tools menu)
2. Go to Configuration tab
3. Click "Test ExifTool"

## Supported File Formats

ExifTool supports 400+ formats including:

**Images:**
- JPEG, PNG, TIFF, GIF, BMP, WebP, SVG
- RAW formats: CR2, NEF, ARW, DNG, RAF, ORF, RW2, etc.
- PSD, AI, EPS, PDF (images)

**Video:**
- MP4, MOV, AVI, MKV, FLV, WMV, M4V
- 3GP, WebM, OGV

**Audio:**
- MP3, FLAC, WAV, M4A, OGG, WMA
- AAC, AIFF, APE

**Documents:**
- PDF, DOCX, XLSX, PPTX
- ODT, ODS, ODP

**And many more!**

## Common Use Cases

### 1. Forensic Investigation

```python
# Analyze suspicious image
analyzer = MetadataAnalyzer()
analysis = analyzer.analyze_file("suspect_image.jpg")

# Check for anomalies
if analysis['anomalies']:
    print("Anomalies detected:")
    for anomaly in analysis['anomalies']:
        print(f"  - {anomaly}")

# Generate forensic report
report_gen = ForensicReportGenerator()
report = report_gen.generate_file_report(
    "suspect_image.jpg",
    output_format='html'
)
report_gen.save_report(report, "investigation_report.html")
```

### 2. Privacy Protection

```python
# Remove all identifying metadata
editor = MetadataEditor()

# Anonymize single file
editor.anonymize_file("photo.jpg", backup=True)

# Anonymize batch
editor.anonymize_batch([
    "photo1.jpg",
    "photo2.jpg",
    "photo3.jpg"
], backup=True)
```

### 3. Photo Organization

```python
# Rename photos by date and camera
editor = MetadataEditor()

renames = editor.rename_by_metadata(
    photo_list,
    pattern="{DateTimeOriginal}_{Make}_{Model}"
)

# Results in: 2024-12-12_Canon_EOS5D.jpg
```

### 4. GPS Tracking

```python
# Extract GPS data from photos
analyzer = MetadataAnalyzer()

locations = []
for photo in photo_list:
    analysis = analyzer.analyze_file(photo)
    gps = analysis.get('gps_info', {})
    if gps.get('coordinates'):
        locations.append({
            'file': photo,
            'coords': gps['coordinates'],
            'map_link': gps['map_link']
        })

# Generate GPS report
report_gen = ForensicReportGenerator()
report = report_gen.generate_gps_report(photo_list, 'html')
```

### 5. Camera Inventory

```python
# Identify all cameras used
analyzer = MetadataAnalyzer()

cameras = {}
for photo in photo_list:
    analysis = analyzer.analyze_file(photo)
    camera_info = analysis.get('camera_info', {})

    if camera_info.get('make'):
        key = f"{camera_info['make']} {camera_info['model']}"
        cameras[key] = cameras.get(key, 0) + 1

print("Cameras used:")
for camera, count in cameras.items():
    print(f"  {camera}: {count} photos")
```

### 6. Timeline Reconstruction

```python
# Create timeline of photo activity
analyzer = MetadataAnalyzer()
timeline = analyzer.create_timeline(photo_list)

# Generate timeline report
report_gen = ForensicReportGenerator()
report = report_gen.generate_timeline_report(
    photo_list,
    output_format='html'
)
```

## UI Integration

### Open Metadata Panel

```python
from ui.metadata_panel import MetadataPanel

# Create panel
metadata_panel = MetadataPanel()

# Load file
metadata_panel.load_file("photo.jpg")

# Show panel
metadata_panel.show()
```

### Open ExifTool Dialog

```python
from ui.exiftool_dialog import ExifToolDialog

# Create dialog
dialog = ExifToolDialog()

# Show dialog
dialog.exec()
```

## Error Handling

All components include comprehensive error handling:

```python
try:
    exiftool = ExifToolWrapper()
except RuntimeError as e:
    print(f"ExifTool not found: {e}")
    print("Please install ExifTool")

try:
    metadata = exiftool.extract_metadata("photo.jpg")
except FileNotFoundError:
    print("File not found")
except Exception as e:
    print(f"Error extracting metadata: {e}")
```

## Performance Considerations

- **Caching**: ExifToolWrapper caches metadata results
- **Batch Operations**: Use batch methods for multiple files (more efficient)
- **Timeout**: Default 30s timeout for operations (configurable)
- **Large Files**: Handles files up to system limits

### Performance Tips

```python
# Good: Batch extraction
metadata_map = exiftool.extract_metadata_batch(file_list)

# Less efficient: Individual extraction
for file in file_list:
    metadata = exiftool.extract_metadata(file)

# Clear cache when needed
exiftool.clear_cache()
```

## Security Considerations

- Backup files before editing (use `backup=True`)
- Verify anonymization results
- Be cautious with custom commands
- Validate file paths to prevent path traversal
- Handle sensitive metadata appropriately

## Troubleshooting

### ExifTool Not Found

**Problem:** RuntimeError: ExifTool not found

**Solution:**
1. Download from https://exiftool.org/
2. Extract to default location or add to PATH
3. Restart application
4. Use ExifTool Dialog to set custom path

### No Metadata Found

**Problem:** Empty metadata dictionary returned

**Solution:**
- Check if file actually contains metadata
- Verify file format is supported
- Check file permissions
- Try with different file

### Slow Performance

**Problem:** Metadata extraction is slow

**Solution:**
- Use batch operations for multiple files
- Check ExifTool timeout settings
- Verify file is not corrupted
- Check disk I/O performance

## API Reference

### ExifToolWrapper

```python
ExifToolWrapper(exiftool_path: Optional[str] = None)
get_version() -> str
is_available() -> bool
extract_metadata(file_path, groups=True, binary=False) -> Dict
extract_metadata_batch(file_paths, groups=True) -> Dict
get_tag(file_path, tag_name) -> Any
set_tag(file_path, tag_name, value, overwrite=True) -> bool
set_tags(file_path, tags: Dict, overwrite=True) -> bool
remove_all_metadata(file_path, overwrite=True) -> bool
copy_metadata(source_file, target_file, overwrite=True) -> bool
extract_thumbnail(file_path, output_path) -> bool
get_supported_formats() -> List[str]
execute_command(args: List[str], timeout=30) -> CompletedProcess
```

### MetadataAnalyzer

```python
MetadataAnalyzer(exiftool: Optional[ExifToolWrapper] = None)
analyze_file(file_path) -> Dict
compare_metadata(file1, file2) -> Dict
create_timeline(file_paths) -> List[Dict]
detect_duplicates_by_metadata(file_paths, tolerance=1.0) -> List[List[str]]
```

### MetadataEditor

```python
MetadataEditor(exiftool: Optional[ExifToolWrapper] = None)
edit_field(file_path, field_name, new_value, backup=False) -> bool
edit_multiple_fields(file_path, fields: Dict, backup=False) -> bool
batch_edit(file_paths, fields: Dict, backup=False) -> Dict
anonymize_file(file_path, backup=False) -> bool
anonymize_batch(file_paths, backup=False) -> Dict
shift_dates(file_paths, offset: timedelta, backup=False) -> Dict
geotag_from_gpx(file_paths, gpx_file, backup=False) -> Dict
create_template(name, fields: Dict)
apply_template(file_paths, template_name, backup=False) -> Dict
rename_by_metadata(file_paths, pattern, dry_run=False) -> Dict
```

### ForensicReportGenerator

```python
ForensicReportGenerator(exiftool=None, analyzer=None)
generate_file_report(file_path, output_format='html') -> str
generate_batch_report(file_paths, output_format='html') -> str
generate_timeline_report(file_paths, output_format='html') -> str
generate_device_report(file_paths, output_format='html') -> str
generate_gps_report(file_paths, output_format='html') -> str
save_report(report_content, output_path, format_hint=None)
```

## Examples

See `test_exiftool_integration.py` for comprehensive examples of all functionality.

## License

Part of Smart Search Pro. See main LICENSE file.

## Credits

- ExifTool by Phil Harvey (https://exiftool.org/)
- Integration by Smart Search Pro Development Team

## Version

ExifTool Integration v1.0.0
Smart Search Pro v1.1.0
