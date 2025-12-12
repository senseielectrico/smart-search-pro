# ExifTool Integration - Quick Start Guide

## Installation (5 minutes)

### Step 1: Install ExifTool

**Recommended Method:**
1. Download Windows Executable from: https://exiftool.org/
2. Extract `exiftool(-k).exe` from the zip file
3. Rename it to `exiftool.exe`
4. Place in: `D:\MAIN_DATA_CENTER\Dev_Tools\ExifTool\exiftool.exe`

**Alternative: System PATH**
1. Extract ExifTool anywhere
2. Add folder to Windows PATH
3. Restart terminal/application

### Step 2: Verify Installation

Run test:
```bash
python test_exiftool_integration.py
```

Or in Smart Search Pro:
1. Open Tools > ExifTool Operations
2. Check "Configuration" tab
3. Green status = Ready!

## Quick Usage Examples

### Extract Metadata

```python
from tools.exiftool_wrapper import ExifToolWrapper

exiftool = ExifToolWrapper()
metadata = exiftool.extract_metadata("photo.jpg")

# Get specific field
camera = metadata.get("Make")
gps_lat = metadata.get("GPSLatitude")
date = metadata.get("DateTimeOriginal")
```

### Forensic Analysis

```python
from tools.metadata_analyzer import MetadataAnalyzer

analyzer = MetadataAnalyzer()
analysis = analyzer.analyze_file("photo.jpg")

# Check results
print(f"Camera: {analysis['camera_info']}")
print(f"GPS: {analysis['gps_info']}")
print(f"Anomalies: {analysis['anomalies']}")
```

### Generate Report

```python
from tools.forensic_report import ForensicReportGenerator

report_gen = ForensicReportGenerator()
html_report = report_gen.generate_file_report("photo.jpg", 'html')
report_gen.save_report(html_report, "report.html")
```

### Edit Metadata

```python
from tools.metadata_editor import MetadataEditor

editor = MetadataEditor()

# Edit single field
editor.edit_field("photo.jpg", "Artist", "John Doe")

# Anonymize (remove identifying info)
editor.anonymize_file("photo.jpg", backup=True)

# Rename by metadata
editor.rename_by_metadata(
    ["photo1.jpg", "photo2.jpg"],
    pattern="{DateTimeOriginal}_{Make}"
)
```

## UI Features

### 1. Metadata Panel

**Access:** View > Metadata Panel (or integrate in main window)

**Tabs:**
- **Metadata**: Browse/search all fields, edit values
- **Forensic Analysis**: Run analysis, view anomalies
- **Comparison**: Compare two files side-by-side

**Quick Actions:**
- Search metadata: Type in search box
- Export: JSON or CSV
- Generate Report: Full forensic report
- Edit Field: Select and edit
- Strip All: Remove all metadata

### 2. ExifTool Dialog

**Access:** Tools > ExifTool Operations

**Tabs:**
- **Configuration**: Test installation, set path
- **Strip Metadata**: Remove metadata wizard
- **Batch Rename**: Rename files using metadata patterns
- **Custom Command**: Execute custom ExifTool commands

## Common Tasks

### Task 1: View Photo GPS Location

```python
analyzer = MetadataAnalyzer()
analysis = analyzer.analyze_file("photo.jpg")

gps = analysis.get('gps_info', {})
if gps.get('map_link'):
    print(f"Location: {gps['coordinates']}")
    print(f"View on map: {gps['map_link']}")
```

**In UI:**
1. Open Metadata Panel
2. Load photo
3. Go to Forensic Analysis tab
4. GPS info shows with map link

### Task 2: Remove Personal Info

```python
editor = MetadataEditor()
editor.anonymize_file("photo.jpg", backup=True)
```

**In UI:**
1. Open ExifTool Dialog
2. Go to Strip Metadata tab
3. Add files
4. Check "Create backup files"
5. Click Strip Metadata

### Task 3: Organize Photos by Date/Camera

```python
editor = MetadataEditor()
editor.rename_by_metadata(
    photo_list,
    pattern="{DateTimeOriginal}_{Make}_{Model}"
)
```

**In UI:**
1. Open ExifTool Dialog
2. Go to Batch Rename tab
3. Add photos
4. Enter pattern: `{DateTimeOriginal}_{Make}_{Model}`
5. Preview, then Rename

### Task 4: Investigate Suspicious File

```python
analyzer = MetadataAnalyzer()
analysis = analyzer.analyze_file("suspect.jpg")

# Check anomalies
if analysis['anomalies']:
    print("⚠ Anomalies detected:")
    for anomaly in analysis['anomalies']:
        print(f"  - {anomaly}")

# Check for editing
software = analysis.get('software_info', {})
if 'editors_detected' in software:
    print(f"Edited with: {software['editors_detected']}")

# Generate full report
report_gen = ForensicReportGenerator()
report = report_gen.generate_file_report("suspect.jpg", 'html')
report_gen.save_report(report, "investigation.html")
```

**In UI:**
1. Open Metadata Panel
2. Load file
3. Go to Forensic Analysis tab
4. Click "Run Forensic Analysis"
5. Review anomalies and findings
6. Click "Generate Report" for full documentation

### Task 5: Create Photo Timeline

```python
analyzer = MetadataAnalyzer()
timeline = analyzer.create_timeline([
    "photo1.jpg",
    "photo2.jpg",
    "photo3.jpg"
])

# Generate timeline report
report_gen = ForensicReportGenerator()
report = report_gen.generate_timeline_report(timeline, 'html')
```

## Naming Patterns

Use these patterns for batch renaming:

- `{DateTimeOriginal}` - Date/time photo taken
- `{Make}` - Camera manufacturer
- `{Model}` - Camera model
- `{SerialNumber}` - Camera serial number
- `{GPSLatitude}` - GPS latitude
- `{GPSLongitude}` - GPS longitude
- `{Artist}` - Photo author
- `{counter:4}` - 4-digit counter (0001, 0002, etc.)

**Examples:**
- `{DateTimeOriginal}_{counter:3}` → `2024-12-12_001.jpg`
- `{Make}_{Model}` → `Canon_EOS5D.jpg`
- `{DateTimeOriginal}_{GPSLatitude}_{GPSLongitude}` → `2024-12-12_40.7128_-74.0060.jpg`

## Supported Formats

ExifTool supports 400+ formats. Most common:

**Images**: JPG, PNG, TIFF, GIF, BMP, WebP, RAW (CR2, NEF, ARW, DNG, etc.)

**Video**: MP4, MOV, AVI, MKV, FLV, WMV

**Audio**: MP3, FLAC, WAV, M4A, OGG

**Documents**: PDF, DOCX, XLSX, PPTX

**Others**: PSD, AI, EPS, SVG, and many more

Check supported formats in UI:
1. Open ExifTool Dialog
2. Go to Configuration tab
3. Click "Show All Supported Formats"

## Troubleshooting

### "ExifTool not found"

**Solution:**
1. Download from https://exiftool.org/
2. Extract to `D:\MAIN_DATA_CENTER\Dev_Tools\ExifTool\`
3. Or set custom path in ExifTool Dialog
4. Test installation

### "No metadata found"

**Causes:**
- File has no metadata (stripped or never had any)
- File format not supported (rare)
- File is corrupted

**Solution:**
- Try with different file
- Check file format
- Verify file is not damaged

### Slow performance

**Solutions:**
- Use batch operations instead of individual calls
- Clear cache: `exiftool.clear_cache()`
- Check disk I/O
- Reduce timeout if getting stuck

## Best Practices

### 1. Always Backup Before Editing

```python
# Good
editor.edit_field("photo.jpg", "Artist", "John", backup=True)

# Creates photo.jpg_original as backup
```

### 2. Use Batch Operations

```python
# Efficient
metadata_map = exiftool.extract_metadata_batch(file_list)

# Less efficient (many subprocess calls)
for file in file_list:
    metadata = exiftool.extract_metadata(file)
```

### 3. Preview Before Renaming

```python
# Preview first
renames = editor.rename_by_metadata(files, pattern, dry_run=True)
for old, new in renames.items():
    print(f"{old} → {new}")

# Then apply
renames = editor.rename_by_metadata(files, pattern, dry_run=False)
```

### 4. Handle Errors

```python
try:
    metadata = exiftool.extract_metadata("photo.jpg")
except FileNotFoundError:
    print("File not found")
except RuntimeError:
    print("ExifTool error")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Next Steps

1. Read full documentation: `EXIFTOOL_INTEGRATION.md`
2. Run test suite: `python test_exiftool_integration.py`
3. Explore UI components
4. Check API reference in documentation

## Support

For issues or questions:
1. Check `EXIFTOOL_INTEGRATION.md` for detailed docs
2. Review error messages in UI
3. Test with sample files
4. Verify ExifTool installation

## Quick Command Reference

```python
# Initialize
from tools.exiftool_wrapper import ExifToolWrapper
exiftool = ExifToolWrapper()

# Extract
metadata = exiftool.extract_metadata("file.jpg")

# Analyze
from tools.metadata_analyzer import MetadataAnalyzer
analyzer = MetadataAnalyzer()
analysis = analyzer.analyze_file("file.jpg")

# Edit
from tools.metadata_editor import MetadataEditor
editor = MetadataEditor()
editor.edit_field("file.jpg", "Artist", "Name")

# Report
from tools.forensic_report import ForensicReportGenerator
report_gen = ForensicReportGenerator()
report = report_gen.generate_file_report("file.jpg", 'html')
report_gen.save_report(report, "report.html")
```

## Version

ExifTool Integration v1.0.0
Last Updated: 2024-12-12
