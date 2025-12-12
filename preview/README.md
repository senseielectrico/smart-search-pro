# Smart Search Pro - Preview Module

Comprehensive file preview system with caching, async support, and extensible architecture.

## Features

### Supported File Types

#### Text Files
- Syntax highlighting for 40+ programming languages
- Line numbers
- Automatic encoding detection
- Large file handling (first 10KB)
- Languages: Python, JavaScript, TypeScript, HTML, CSS, SQL, JSON, YAML, and more

#### Images
- Thumbnail generation with configurable sizes
- EXIF metadata extraction
- Base64 encoding support
- Formats: JPG, PNG, GIF, BMP, WEBP, TIFF, ICO
- Lazy loading for large images
- Animation detection for GIFs

#### Documents
- PDF: First page rendering, text extraction, metadata
- Office: Metadata extraction for Word, Excel, PowerPoint (.doc, .docx, .xls, .xlsx, .ppt, .pptx)
- Page/sheet/slide counting

#### Media Files
- Audio: Duration, bitrate, sample rate, ID3 tags
- Video: Duration, resolution, codec info, thumbnail generation
- Formats: MP3, FLAC, OGG, WAV, MP4, AVI, MKV, MOV, and more
- FFmpeg integration for advanced features

#### Archives
- Content listing without extraction
- Compressed/uncompressed size comparison
- Compression ratio calculation
- Formats: ZIP, 7z, RAR, TAR, GZ, BZ2, XZ

## Architecture

```
preview/
├── __init__.py              # Package exports
├── manager.py               # Main preview orchestrator
├── text_preview.py          # Text file handling
├── image_preview.py         # Image processing
├── document_preview.py      # PDF and Office documents
├── media_preview.py         # Audio and video files
├── archive_preview.py       # Compressed archives
├── metadata.py              # Extended metadata extraction
└── test_preview.py          # Test suite
```

## Usage

### Basic Usage

```python
from preview import PreviewManager

# Initialize manager
manager = PreviewManager(
    cache_dir="./cache",        # Optional disk cache
    memory_cache_size=100,      # LRU memory cache
    cache_ttl_hours=24,         # Cache expiration
    max_workers=4               # Thread pool size
)

# Get preview
preview = manager.get_preview("document.pdf")
print(f"Pages: {preview['pages']}")
print(f"Author: {preview.get('author', 'Unknown')}")

# With metadata
preview = manager.get_preview("image.jpg", include_metadata=True)
print(f"Dimensions: {preview['dimensions']}")
print(f"EXIF data: {preview['metadata'].get('exif', {})}")
```

### Async Preview

```python
import asyncio

async def preview_files(file_paths):
    manager = PreviewManager()

    # Generate previews concurrently
    tasks = [manager.get_preview_async(path) for path in file_paths]
    previews = await asyncio.gather(*tasks)

    return previews

# Run
files = ['file1.txt', 'file2.jpg', 'file3.pdf']
previews = asyncio.run(preview_files(files))
```

### Individual Previewers

```python
from preview.text_preview import TextPreviewer
from preview.image_preview import ImagePreviewer

# Text preview
text_previewer = TextPreviewer()
preview = text_previewer.generate_preview("script.py")
print(preview['highlighted'])  # HTML with syntax highlighting

# Image preview
image_previewer = ImagePreviewer()
preview = image_previewer.generate_preview(
    "photo.jpg",
    thumbnail_size=(256, 256),
    include_base64=True
)
```

### Cache Management

```python
# Get cache statistics
stats = manager.get_cache_stats()
print(f"Memory: {stats['memory_items']}/{stats['memory_capacity']}")
print(f"Disk: {stats['disk_items']} items, {stats['disk_size_mb']} MB")

# Clear cache
manager.clear_cache()  # Clear both memory and disk
manager.clear_cache(memory_only=True)  # Keep disk cache

# Preload previews
def on_preview_ready(file_path, preview):
    print(f"Preview ready for {file_path}")

manager.preload_previews(file_list, callback=on_preview_ready)
```

## Dependencies

### Required
- Standard library only for basic functionality

### Optional (Enhanced Features)
```bash
pip install Pillow           # Image preview and thumbnails
pip install pypdf            # PDF preview
pip install mutagen          # Audio/video metadata
pip install pygments         # Syntax highlighting
pip install chardet          # Better encoding detection
pip install olefile          # Office document metadata
pip install pdf2image        # PDF page rendering
```

### External Tools (Optional)
- **ffmpeg**: Video thumbnails and advanced media info
- **7z**: 7z archive support
- **unrar**: RAR archive support

## Preview Data Structure

### Text Preview
```python
{
    'text': '1 | def main():\n2 |     pass',
    'highlighted': '<div class="source">...</div>',  # HTML
    'encoding': 'utf-8',
    'lines': 42,
    'truncated': False,
    'language': 'python'
}
```

### Image Preview
```python
{
    'dimensions': '1920x1080',
    'width': 1920,
    'height': 1080,
    'format': 'JPEG',
    'mode': 'RGB',
    'file_size': 2048000,
    'has_transparency': False,
    'thumbnail_base64': 'data:image/png;base64,...',
    'metadata': {
        'camera_make': 'Canon',
        'camera_model': 'EOS 5D',
        'exposure': '1/125',
        'iso': '400'
    }
}
```

### PDF Preview
```python
{
    'type': 'pdf',
    'pages': 10,
    'title': 'Document Title',
    'author': 'John Doe',
    'first_page_text': 'Introduction...',
    'first_page_image': 'data:image/png;base64,...',
    'metadata': {...}
}
```

### Audio Preview
```python
{
    'type': 'audio',
    'duration': '03:45',
    'duration_seconds': 225.3,
    'bitrate': '320 kbps',
    'sample_rate': '44100 Hz',
    'channels': 2,
    'title': 'Song Title',
    'artist': 'Artist Name',
    'album': 'Album Name'
}
```

### Archive Preview
```python
{
    'type': 'zip',
    'total_files': 42,
    'compressed_size': 1024000,
    'uncompressed_size': 5120000,
    'compression_ratio': '80.0%',
    'files': [
        {
            'filename': 'file.txt',
            'compressed_size': 512,
            'uncompressed_size': 2048,
            'is_dir': False
        }
    ]
}
```

## Performance

### Caching Strategy
- **Memory Cache**: LRU cache for instant access
- **Disk Cache**: Persistent cache with TTL
- **Cache Invalidation**: Based on file modification time
- **Async Operations**: Non-blocking preview generation

### Optimizations
- Lazy loading for large images
- Partial file reading for text files (10KB limit)
- Thumbnail caching
- Thread pool for concurrent operations
- Metadata extraction on demand

### Benchmarks
- Text file (50KB): ~5ms
- Image thumbnail: ~50ms
- PDF first page: ~100ms
- Archive listing (100 files): ~20ms

## Testing

```bash
# Run test suite
cd C:\Users\ramos\.local\bin\smart_search\preview
python test_preview.py

# Test individual components
python -c "from preview import PreviewManager; print('OK')"
```

## Error Handling

All preview methods return dictionaries. Errors are indicated by an `'error'` key:

```python
preview = manager.get_preview("nonexistent.txt")
if 'error' in preview:
    print(f"Error: {preview['error']}")
else:
    # Process preview
    pass
```

## Extension

### Adding New Preview Types

```python
from preview.manager import PreviewManager

class CustomPreviewer:
    def is_supported(self, file_path: str) -> bool:
        return file_path.endswith('.custom')

    def generate_preview(self, file_path: str) -> dict:
        return {'type': 'custom', 'data': '...'}

# Integrate with manager
manager = PreviewManager()
manager.custom_previewer = CustomPreviewer()
```

## Security Considerations

- No file execution
- Limited file reading (10KB for text)
- Archive content listing without extraction
- Path traversal protection
- Timeout on external commands (ffmpeg, 7z)

## Limitations

- Text files: First 10KB or 500 lines
- Archive listing: First 100 files
- Image thumbnails: Max 512x512 by default
- Cache TTL: 24 hours by default
- Thread pool: 4 workers by default

## License

Part of Smart Search Pro project.

## Authors

Smart Search Pro Development Team
