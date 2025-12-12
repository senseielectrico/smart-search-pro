# Preview Module Integration Guide

Guide for integrating the preview module with Smart Search Pro UI.

## Quick Integration

### 1. Import the Preview Manager

```python
from preview import PreviewManager

# Initialize in your main application
preview_manager = PreviewManager(
    cache_dir="./cache/previews",
    memory_cache_size=100,
    cache_ttl_hours=24,
    max_workers=4
)
```

### 2. Generate Previews on File Selection

```python
def on_file_selected(file_path):
    """Called when user selects a file in the UI."""
    # Get preview
    preview = preview_manager.get_preview(file_path, include_metadata=True)

    if 'error' in preview:
        display_error(preview['error'])
        return

    # Update UI based on preview type
    update_preview_panel(preview)
```

### 3. Display Preview in UI

```python
def update_preview_panel(preview):
    """Update the preview panel based on preview data."""

    # Text files
    if 'text' in preview:
        if 'highlighted' in preview:
            # Display syntax-highlighted HTML
            preview_widget.setHtml(preview['highlighted'])
        else:
            # Display plain text with line numbers
            preview_widget.setPlainText(preview['text'])

        # Show file info
        info_label.setText(
            f"{preview['language']} | "
            f"{preview['lines']} lines | "
            f"{preview['encoding']}"
        )

    # Images
    elif 'dimensions' in preview:
        if 'thumbnail_base64' in preview:
            # Display base64 image
            display_base64_image(preview['thumbnail_base64'])

        info_label.setText(
            f"{preview['dimensions']} | "
            f"{preview['format']} | "
            f"{preview.get('file_size', 0) // 1024} KB"
        )

        # Show EXIF if available
        if 'metadata' in preview and 'exif' in preview['metadata']:
            display_exif_data(preview['metadata']['exif'])

    # PDF documents
    elif preview.get('type') == 'pdf':
        if 'first_page_image' in preview:
            display_base64_image(preview['first_page_image'])

        info_label.setText(f"{preview['pages']} pages")

        if 'first_page_text' in preview:
            text_preview.setPlainText(preview['first_page_text'])

    # Audio/Video
    elif preview.get('type') in ('audio', 'video'):
        info_parts = [preview.get('duration', 'Unknown duration')]

        if 'bitrate' in preview:
            info_parts.append(preview['bitrate'])

        if preview.get('type') == 'video' and 'resolution' in preview:
            info_parts.append(preview['resolution'])

        info_label.setText(' | '.join(info_parts))

        # Show metadata
        if 'title' in preview:
            title_label.setText(preview['title'])
        if 'artist' in preview:
            artist_label.setText(preview['artist'])

    # Archives
    elif preview.get('type') in ('zip', '7z', 'rar', 'tar'):
        total_files = preview.get('total_files', 0)
        compression = preview.get('compression_ratio', 'N/A')

        info_label.setText(f"{total_files} files | Compression: {compression}")

        # Display file list
        if 'files' in preview:
            display_archive_contents(preview['files'])
```

## PyQt6 Integration Example

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PyQt6.QtCore import QThread, pyqtSignal
from preview import PreviewManager


class PreviewWorker(QThread):
    """Background worker for preview generation."""

    preview_ready = pyqtSignal(dict)

    def __init__(self, manager, file_path):
        super().__init__()
        self.manager = manager
        self.file_path = file_path

    def run(self):
        preview = self.manager.get_preview(self.file_path, include_metadata=True)
        self.preview_ready.emit(preview)


class PreviewPanel(QWidget):
    """Preview panel widget for Smart Search."""

    def __init__(self):
        super().__init__()
        self.preview_manager = PreviewManager(cache_dir="./cache/previews")
        self.current_worker = None

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Info label
        self.info_label = QLabel("No file selected")
        layout.addWidget(self.info_label)

        # Preview area
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)

        self.setLayout(layout)

    def show_preview(self, file_path):
        """Generate and display preview for file."""
        self.info_label.setText("Loading preview...")

        # Cancel previous worker
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.quit()
            self.current_worker.wait()

        # Start new worker
        self.current_worker = PreviewWorker(self.preview_manager, file_path)
        self.current_worker.preview_ready.connect(self.on_preview_ready)
        self.current_worker.start()

    def on_preview_ready(self, preview):
        """Handle preview result."""
        if 'error' in preview:
            self.info_label.setText(f"Error: {preview['error']}")
            self.preview_text.clear()
            return

        # Display based on type
        if 'highlighted' in preview:
            self.preview_text.setHtml(preview['highlighted'])
        elif 'text' in preview:
            self.preview_text.setPlainText(preview['text'])
        else:
            self.preview_text.setPlainText(str(preview))

        # Update info
        info_parts = []
        if 'language' in preview:
            info_parts.append(preview['language'])
        if 'lines' in preview:
            info_parts.append(f"{preview['lines']} lines")
        if 'encoding' in preview:
            info_parts.append(preview['encoding'])

        self.info_label.setText(' | '.join(info_parts))

    def cleanup(self):
        """Cleanup resources."""
        if self.current_worker:
            self.current_worker.quit()
            self.current_worker.wait()
        self.preview_manager.shutdown()
```

## Async Integration (asyncio)

```python
import asyncio
from preview import PreviewManager


class AsyncPreviewHandler:
    """Handle previews asynchronously."""

    def __init__(self):
        self.manager = PreviewManager()

    async def get_previews_batch(self, file_paths):
        """Get previews for multiple files concurrently."""
        tasks = [
            self.manager.get_preview_async(path)
            for path in file_paths
        ]
        return await asyncio.gather(*tasks)

    async def preload_visible_files(self, file_paths):
        """Preload previews for visible files in background."""
        # Get previews without blocking
        previews = await self.get_previews_batch(file_paths)

        # All previews are now cached
        return previews
```

## Performance Tips

### 1. Preload Previews

```python
def on_search_complete(results):
    """Preload previews for search results."""
    # Get first 20 file paths
    file_paths = [r['path'] for r in results[:20]]

    # Preload in background
    preview_manager.preload_previews(file_paths)
```

### 2. Cache Management

```python
# Monitor cache size
stats = preview_manager.get_cache_stats()
if stats['disk_size_mb'] > 100:  # 100 MB limit
    preview_manager.clear_cache()
```

### 3. Lazy Loading

```python
def on_scroll_changed(visible_items):
    """Load previews only for visible items."""
    for item in visible_items:
        if not has_preview_cached(item.path):
            load_preview_async(item.path)
```

## UI Components Checklist

- [ ] File info panel (name, size, type)
- [ ] Preview area (text/image/document)
- [ ] Metadata panel (EXIF, ID3, etc.)
- [ ] Loading indicator
- [ ] Error display
- [ ] Syntax highlighting toggle
- [ ] Thumbnail size selector
- [ ] Cache clear button

## Example UI Layout

```
┌─────────────────────────────────────────┐
│ File: document.pdf                      │
│ Size: 2.5 MB | 15 pages | PDF          │
├─────────────────────────────────────────┤
│                                         │
│  ┌───────────────────────────────────┐ │
│  │                                   │ │
│  │    [First Page Preview Image]    │ │
│  │                                   │ │
│  └───────────────────────────────────┘ │
│                                         │
│  First Page Text:                       │
│  ┌───────────────────────────────────┐ │
│  │ Introduction                       │ │
│  │ This document describes...         │ │
│  │                                   │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Metadata:                              │
│  • Title: Sample Document               │
│  • Author: John Doe                     │
│  • Created: 2024-01-15                  │
└─────────────────────────────────────────┘
```

## Testing Integration

```python
def test_preview_integration():
    """Test preview integration."""
    from preview import PreviewManager

    manager = PreviewManager()

    # Test with actual file from your system
    test_file = "path/to/test/file.py"

    preview = manager.get_preview(test_file)
    assert 'error' not in preview
    assert 'language' in preview or 'type' in preview

    manager.shutdown()
    print("Integration test passed!")
```

## Error Handling

```python
def safe_get_preview(file_path):
    """Safely get preview with error handling."""
    try:
        preview = preview_manager.get_preview(file_path)

        if 'error' in preview:
            logger.warning(f"Preview error for {file_path}: {preview['error']}")
            return create_fallback_preview(file_path)

        return preview

    except Exception as e:
        logger.error(f"Exception getting preview: {e}")
        return create_fallback_preview(file_path)


def create_fallback_preview(file_path):
    """Create basic fallback preview."""
    import os
    return {
        'type': 'fallback',
        'filename': os.path.basename(file_path),
        'size': os.path.getsize(file_path),
        'text': 'Preview not available'
    }
```

## Cleanup on Exit

```python
def on_application_exit():
    """Cleanup when application closes."""
    # Shutdown preview manager
    preview_manager.shutdown()

    # Optionally clear disk cache
    # preview_manager.clear_cache()
```

## Next Steps

1. Add PreviewPanel widget to main UI
2. Connect file selection signals to preview generation
3. Add preview cache management in settings
4. Implement preview type-specific displays
5. Add user preferences (syntax theme, thumbnail size)
6. Performance profiling with real data

## Support

For issues or questions about the preview module, refer to:
- `README.md` - Module documentation
- `test_preview.py` - Test examples
- `example_usage.py` - Usage examples
