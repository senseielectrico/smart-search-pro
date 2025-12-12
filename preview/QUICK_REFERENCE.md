# Preview Module - Quick Reference

## Installation

```bash
# Navigate to preview module
cd C:\Users\ramos\.local\bin\smart_search\preview

# Run verification
python verify_installation.py

# Install optional dependencies
pip install Pillow pypdf mutagen pygments chardet olefile
```

## Basic Usage

```python
from preview import PreviewManager

# Create manager
manager = PreviewManager(cache_dir="./cache")

# Get preview
preview = manager.get_preview("file.pdf")

# Check result
if 'error' not in preview:
    print(preview)

# Cleanup
manager.shutdown()
```

## Preview Types

### Text Files
```python
preview = manager.get_preview("script.py")
# Returns: {language, lines, text, highlighted, encoding}
```

### Images
```python
preview = manager.get_preview("photo.jpg")
# Returns: {dimensions, format, mode, thumbnail_base64, metadata}
```

### PDFs
```python
preview = manager.get_preview("document.pdf")
# Returns: {pages, title, author, first_page_text, first_page_image}
```

### Audio/Video
```python
preview = manager.get_preview("song.mp3")
# Returns: {duration, bitrate, artist, album, title}
```

### Archives
```python
preview = manager.get_preview("archive.zip")
# Returns: {total_files, files[], compression_ratio}
```

## Common Patterns

### Check File Type
```python
if 'language' in preview:
    # Text file
    display_code(preview)
elif 'dimensions' in preview:
    # Image
    display_image(preview)
elif preview.get('type') == 'pdf':
    # PDF document
    display_pdf(preview)
```

### Async Preview
```python
import asyncio

async def get_previews(files):
    manager = PreviewManager()
    tasks = [manager.get_preview_async(f) for f in files]
    return await asyncio.gather(*tasks)

previews = asyncio.run(get_previews(file_list))
```

### Cache Management
```python
# Get stats
stats = manager.get_cache_stats()
print(f"Cached: {stats['memory_items']} items")

# Clear cache
manager.clear_cache()
```

### Preload Previews
```python
def on_ready(file_path, preview):
    print(f"Ready: {file_path}")

manager.preload_previews(file_list, callback=on_ready)
```

## Configuration

```python
manager = PreviewManager(
    cache_dir="./cache",      # Disk cache location
    memory_cache_size=100,    # LRU memory cache size
    cache_ttl_hours=24,       # Cache expiration
    max_workers=4             # Thread pool size
)
```

## Error Handling

```python
preview = manager.get_preview(file_path)

if 'error' in preview:
    logger.error(f"Preview failed: {preview['error']}")
    return fallback_preview
else:
    return preview
```

## File Format Support

### Text (25+)
.py .js .ts .html .css .json .yaml .xml .sql .md

### Images (8)
.jpg .png .gif .bmp .webp .tiff .ico

### Documents (6)
.pdf .doc .docx .xls .xlsx .ppt .pptx

### Media (10+)
.mp3 .flac .ogg .wav .mp4 .avi .mkv .mov

### Archives (8+)
.zip .7z .rar .tar .gz .bz2 .xz

## Testing

```bash
# Run all tests
python test_preview.py

# Run examples
python example_usage.py

# Verify installation
python verify_installation.py
```

## Documentation

- `README.md` - Full documentation
- `INTEGRATION_GUIDE.md` - UI integration guide
- `MODULE_SUMMARY.md` - Complete summary
- `QUICK_REFERENCE.md` - This file

## Location

```
C:\Users\ramos\.local\bin\smart_search\preview\
```

## Performance

- Text preview: ~5ms
- Image thumbnail: ~50ms
- PDF render: ~100ms
- Cache hit: <1ms

## Common Issues

### Missing Dependencies
```bash
pip install Pillow pypdf pygments
```

### ffmpeg Not Found
- Install ffmpeg and add to PATH
- Or skip video thumbnails

### Cache Too Large
```python
# Clear old cache
manager.clear_cache()

# Reduce cache size
manager = PreviewManager(memory_cache_size=50)
```

## Examples

See `example_usage.py` for complete examples:
- Basic usage
- Async operations
- Cache management
- Preloading
- Specific previewers

## Support

For issues or questions:
1. Check `README.md` for detailed docs
2. Run `verify_installation.py` to check setup
3. Review `test_preview.py` for usage patterns
4. See `INTEGRATION_GUIDE.md` for UI integration
