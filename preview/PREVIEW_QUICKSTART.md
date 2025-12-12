# Preview System - Quick Start

## What's New

The preview system now supports **40+ programming languages**, image zoom/rotation, EXIF metadata, PDF multi-page viewing, Markdown rendering, and more!

## Quick Install

```bash
# Install optional dependencies for full features
python install_preview_deps.py
```

Or manually:

```bash
pip install pillow pygments markdown pypdf python-docx chardet
```

## Usage

### In Your Code

```python
from ui.preview_panel_enhanced import EnhancedPreviewPanel

# Create enhanced preview panel
preview = EnhancedPreviewPanel()

# Preview a file
preview.set_file("/path/to/file.py")
```

### Test It

```bash
python test_preview_enhancements.py
```

## Features

### Text Files (40+ Languages)

- **Syntax Highlighting**: Python, JS, TS, C++, Java, Go, Rust, and more
- **Line Numbers**: Toggle on/off
- **Word Wrap**: Toggle on/off
- **Find**: Press Ctrl+F to search

**Supported:**
Python, JavaScript, TypeScript, HTML, CSS, JSON, XML, YAML, Markdown, SQL, C/C++, C#, Java, PHP, Ruby, Go, Rust, Swift, Kotlin, Dart, and 20+ more

### Images

- **Zoom**: 10% to 400% with slider
- **Fit to View**: Auto-fit button
- **Rotate**: 90° left/right
- **EXIF Data**: Camera make, model, date, settings

**Formats:** JPG, PNG, GIF, BMP, WEBP, TIFF

### Documents

- **PDF**: Multi-page viewing with page selector
- **Word**: Text extraction from .docx files
- **Excel**: Sheet count
- **PowerPoint**: Slide count

### Special Formats

- **JSON**: Auto-formatted with indentation
- **Markdown**: Rendered HTML with code highlighting

## Keyboard Shortcuts

- **Ctrl+F**: Find in text preview

## Performance

- **Lazy Loading**: Files load in background
- **Cache**: Fast re-loading of previously viewed files
- **Thumbnails**: Cached on disk for instant display
- **Large Files**: Handled gracefully (truncated if too large)

## Architecture

```
preview/
├── manager.py              # Caching and coordination
├── text_preview.py         # 40+ language support
├── image_preview.py        # Zoom, EXIF, rotation
├── document_preview.py     # PDF, Office docs
└── ...

ui/
└── preview_panel_enhanced.py   # Main UI component
```

## Configuration

### Cache Settings

```python
preview = EnhancedPreviewPanel()

# Access manager
manager = preview.preview_manager

# Cache stats
stats = manager.get_cache_stats()
print(f"Memory cache: {stats['memory_items']}/{stats['memory_capacity']}")
print(f"Disk cache: {stats['disk_items']} files, {stats['disk_size_mb']} MB")

# Clear cache
manager.clear_cache()
```

### Limits

```python
# Adjust in preview panel
preview.MAX_TEXT_SIZE = 1024 * 1000  # 1 MB
preview.MAX_IMAGE_SIZE = 1024 * 1024 * 100  # 100 MB
```

## Troubleshooting

### No Syntax Highlighting

```bash
pip install pygments
```

### Markdown Not Rendering

```bash
pip install markdown
```

### PDF Pages Not Loading

1. Install poppler: https://github.com/oschwartz10612/poppler-windows/releases/
2. Add `bin` folder to PATH
3. Install: `pip install pdf2image`

### EXIF Not Showing

```bash
pip install pillow
```

## Examples

### Text with Syntax Highlighting

```python
# Python file with 500 lines
preview.set_file("large_script.py")
# → Loads in background
# → Shows first 500 lines
# → Syntax highlighted
# → Line numbers
# → Press Ctrl+F to search
```

### Image with EXIF

```python
# Photo from camera
preview.set_file("photo.jpg")
# → Shows image
# → Zoom slider (10%-400%)
# → Rotate buttons
# → EXIF data: camera, settings, date
```

### Multi-Page PDF

```python
# PDF document
preview.set_file("document.pdf")
# → Page selector (1-N)
# → Rendered at high quality
# → Scroll through pages
```

### Markdown Rendering

```python
# Markdown file
preview.set_file("README.md")
# → Rendered as HTML
# → Code blocks highlighted
# → Tables formatted
# → Links clickable
```

### JSON Formatting

```python
# Minified JSON
preview.set_file("config.json")
# → Auto-formatted
# → Proper indentation
# → Syntax highlighted
```

## Integration

### Replace Old Preview Panel

```python
# In main_window.py or similar

# Old:
# from ui.preview_panel import PreviewPanel
# self.preview = PreviewPanel()

# New:
from ui.preview_panel_enhanced import EnhancedPreviewPanel
self.preview = EnhancedPreviewPanel()

# Same API, more features!
self.preview.set_file(path)
```

### Connect Signals

```python
# Open file
self.preview.open_requested.connect(self.open_file)

# Open location
self.preview.open_location_requested.connect(self.open_location)

def open_file(self, path):
    import os
    os.startfile(path)

def open_location(self, path):
    import os
    os.startfile(os.path.dirname(path))
```

## Performance Tips

1. **Enable Disk Cache**: Faster subsequent loads
2. **Install All Dependencies**: Best feature support
3. **Adjust Limits**: For your use case
4. **Use Lazy Loading**: Non-blocking UI

## Full Documentation

See `PREVIEW_ENHANCEMENTS.md` for complete documentation.

## Support

Issues? Check:
1. Dependencies installed (`python install_preview_deps.py`)
2. File size within limits
3. File format supported
4. Cache not full

---

**Smart Search Pro - Enhanced Preview**
*Preview 40+ file types with syntax highlighting, zoom, and more*
