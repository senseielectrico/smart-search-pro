# Preview Module - Installation & Setup

## Quick Start

### 1. Verify Installation

```bash
cd C:\Users\ramos\.local\bin\smart_search\preview
python verify_installation.py
```

Expected output: "Preview module is fully functional!"

### 2. Test Basic Functionality

```bash
python test_preview.py
```

Expected: All tests should pass.

### 3. Try Examples

```bash
python example_usage.py
```

## Installation Checklist

### Core Components (Required)

- [x] `__init__.py` - Package initialization
- [x] `manager.py` - Preview orchestrator
- [x] `text_preview.py` - Text file handler
- [x] `image_preview.py` - Image handler
- [x] `document_preview.py` - Document handler
- [x] `media_preview.py` - Media handler
- [x] `archive_preview.py` - Archive handler
- [x] `metadata.py` - Metadata extractor

### Documentation (Included)

- [x] `README.md` - Full documentation
- [x] `INTEGRATION_GUIDE.md` - UI integration
- [x] `MODULE_SUMMARY.md` - Complete summary
- [x] `QUICK_REFERENCE.md` - Quick reference
- [x] `INSTALLATION.md` - This file

### Tests & Examples (Included)

- [x] `test_preview.py` - Test suite
- [x] `example_usage.py` - Usage examples
- [x] `verify_installation.py` - Verification script

## Dependencies

### Required (Already Installed)

Standard library modules - no additional installation needed.

### Optional (Enhanced Features)

Install for full functionality:

```bash
pip install Pillow pypdf mutagen pygments chardet olefile
```

Individual packages:

```bash
# Image preview and thumbnails
pip install Pillow

# PDF document preview
pip install pypdf

# Audio/video metadata
pip install mutagen

# Syntax highlighting for code
pip install pygments

# Better encoding detection
pip install chardet

# Office document metadata
pip install olefile

# PDF page rendering (requires poppler)
pip install pdf2image
```

### External Tools (Optional)

#### FFmpeg (Video Thumbnails)

**Windows:**
1. Download from https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to PATH
4. Verify: `ffmpeg -version`

**Alternative:**
```bash
# Using chocolatey
choco install ffmpeg

# Using scoop
scoop install ffmpeg
```

#### 7-Zip (7z Archive Support)

**Windows:**
1. Download from https://www.7-zip.org/
2. Install to default location
3. Add `C:\Program Files\7-Zip` to PATH
4. Verify: `7z`

**Alternative:**
```bash
choco install 7zip
```

#### UnRAR (RAR Archive Support)

**Windows:**
1. Download from https://www.rarlab.com/
2. Extract unrar.exe
3. Add to PATH
4. Verify: `unrar`

## Verification

### Check Installation Status

```bash
python verify_installation.py
```

This checks:
- All module imports work
- Available dependencies
- External tools
- Basic functionality
- Individual previewers

### Expected Results

**Minimum (Core Functionality):**
- All imports: OK
- Basic functionality: WORKING
- Text/Archive previewers: WORKING

**Full Functionality:**
- All imports: OK
- Dependencies: 6/6 available
- External tools: 3/3 available
- All previewers: WORKING

## Feature Matrix

| Feature | Requires | Status |
|---------|----------|--------|
| Text preview | Standard library | ✓ Core |
| Syntax highlighting | pygments | ○ Optional |
| Image preview | Pillow | ○ Optional |
| PDF preview | pypdf | ○ Optional |
| PDF rendering | pdf2image + poppler | ○ Optional |
| Audio metadata | mutagen | ○ Optional |
| Video metadata | mutagen | ○ Optional |
| Video thumbnails | ffmpeg | ○ Optional |
| ZIP archives | Standard library | ✓ Core |
| 7z archives | 7z command | ○ Optional |
| RAR archives | unrar command | ○ Optional |
| Office metadata | olefile | ○ Optional |

✓ Core = Works without additional dependencies
○ Optional = Requires additional dependencies

## Testing Installation

### 1. Import Test

```python
from preview import PreviewManager
print("✓ Preview module installed correctly")
```

### 2. Functionality Test

```python
from preview import PreviewManager
import tempfile

manager = PreviewManager()

# Create test file
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    f.write("print('test')")
    test_file = f.name

# Generate preview
preview = manager.get_preview(test_file)

if 'error' not in preview:
    print("✓ Preview generation works")
    print(f"  Language: {preview.get('language')}")
    print(f"  Lines: {preview.get('lines')}")
else:
    print("✗ Preview generation failed")

# Cleanup
import os
os.unlink(test_file)
manager.shutdown()
```

### 3. Full Test Suite

```bash
python test_preview.py
```

Expected output: "All tests passed!"

## Troubleshooting

### Issue: Import Error

```
ImportError: No module named 'preview'
```

**Solution:**
```python
import sys
sys.path.insert(0, 'C:\\Users\\ramos\\.local\\bin\\smart_search')
from preview import PreviewManager
```

### Issue: Pillow Not Found

```
Image preview not available
```

**Solution:**
```bash
pip install Pillow
```

### Issue: ffmpeg Not Found

```
Video thumbnails not available
```

**Solution:**
1. Install ffmpeg (see External Tools section)
2. Add to PATH
3. Restart terminal
4. Verify: `ffmpeg -version`

### Issue: Cache Permission Error

```
PermissionError: [Errno 13] Permission denied
```

**Solution:**
```python
# Use different cache directory
manager = PreviewManager(cache_dir="./my_cache")

# Or disable disk cache
manager = PreviewManager(cache_dir=None)
```

### Issue: Unicode Errors on Windows

```
UnicodeEncodeError: 'charmap' codec can't encode
```

**Solution:**
```python
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
```

## Performance Tuning

### For Large File Sets

```python
manager = PreviewManager(
    cache_dir="./cache",
    memory_cache_size=200,    # Increase cache
    cache_ttl_hours=48,       # Longer TTL
    max_workers=8             # More workers
)
```

### For Low Memory

```python
manager = PreviewManager(
    cache_dir=None,           # Disable disk cache
    memory_cache_size=20,     # Smaller cache
    max_workers=2             # Fewer workers
)
```

### For Fast Response

```python
# Preload previews
file_list = get_recent_files()
manager.preload_previews(file_list)
```

## Integration Steps

1. **Import module in your application:**
   ```python
   from preview import PreviewManager
   ```

2. **Initialize manager:**
   ```python
   self.preview_manager = PreviewManager(cache_dir="./cache")
   ```

3. **Connect to UI:**
   ```python
   def on_file_selected(self, file_path):
       preview = self.preview_manager.get_preview(file_path)
       self.display_preview(preview)
   ```

4. **Cleanup on exit:**
   ```python
   def closeEvent(self, event):
       self.preview_manager.shutdown()
       event.accept()
   ```

See `INTEGRATION_GUIDE.md` for detailed integration examples.

## Next Steps

1. ✓ Verify installation with `verify_installation.py`
2. ✓ Run test suite with `test_preview.py`
3. ✓ Try examples with `example_usage.py`
4. Read `INTEGRATION_GUIDE.md` for UI integration
5. Read `README.md` for full documentation
6. Use `QUICK_REFERENCE.md` as a cheat sheet

## Support Files

| File | Purpose |
|------|---------|
| `README.md` | Complete documentation |
| `INTEGRATION_GUIDE.md` | UI integration examples |
| `MODULE_SUMMARY.md` | Feature summary |
| `QUICK_REFERENCE.md` | Quick reference card |
| `INSTALLATION.md` | This file |
| `test_preview.py` | Test suite |
| `example_usage.py` | Usage examples |
| `verify_installation.py` | Installation checker |

## Version

- **Version:** 1.0.0
- **Date:** 2025-12-12
- **Status:** Production Ready
- **Location:** `C:\Users\ramos\.local\bin\smart_search\preview\`

## License

Part of Smart Search Pro project.
