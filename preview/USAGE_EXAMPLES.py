"""
Preview System - Usage Examples

Demonstrates how to use the enhanced preview features
"""

import os
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preview.text_preview import TextPreviewer
from preview.image_preview import ImagePreviewer
from preview.document_preview import DocumentPreviewer
from preview.manager import PreviewManager


def example_text_preview():
    """Example: Text file preview with syntax highlighting"""
    print("\n=== Text Preview Example ===\n")

    previewer = TextPreviewer()

    # Create sample file
    sample_file = Path(__file__).parent.parent / "sample_code.py"
    sample_file.write_text('''
import os
import sys
from typing import List, Dict, Optional

class DataProcessor:
    """Process data with validation"""

    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.results = []

    def process(self, items: List[str]) -> Optional[List[str]]:
        """Process items and return results"""
        if not items:
            return None

        for item in items:
            result = self._process_item(item)
            if result:
                self.results.append(result)

        return self.results

    def _process_item(self, item: str) -> Optional[str]:
        """Process single item"""
        # Validation
        if not item or len(item) < 3:
            return None

        # Processing
        processed = item.strip().upper()
        return processed

# Usage
processor = DataProcessor({"mode": "strict"})
data = ["apple", "banana", "cherry"]
results = processor.process(data)
print(f"Processed {len(results)} items")
''', encoding='utf-8')

    # Generate preview
    preview = previewer.generate_preview(str(sample_file))

    print(f"Language detected: {preview.get('language')}")
    print(f"Lines: {preview.get('lines')}")
    print(f"Encoding: {preview.get('encoding')}")
    print(f"Syntax highlighting: {'Yes' if 'highlighted' in preview else 'No'}")

    # Show first few lines
    if 'text' in preview:
        lines = preview['text'].split('\n')[:10]
        print("\nPreview (first 10 lines):")
        print('\n'.join(lines))

    # JSON formatting
    print("\n--- JSON Formatting ---")
    json_file = Path(__file__).parent.parent / "sample.json"
    json_file.write_text('{"name":"test","values":[1,2,3],"nested":{"key":"value"}}')

    with open(json_file, 'r') as f:
        json_content = f.read()

    formatted = previewer.format_json(json_content)
    print("Formatted JSON:")
    print(formatted)


def example_image_preview():
    """Example: Image preview with EXIF and zoom"""
    print("\n=== Image Preview Example ===\n")

    previewer = ImagePreviewer()

    # Find a sample image (use any image in project or create placeholder)
    # For demo, we'll just show capabilities
    print("Image Preview Capabilities:")
    print(f"- Pillow available: {previewer._pillow_available}")
    print(f"- EXIF support: {previewer._exif_available}")
    print(f"- Supported formats: {previewer.SUPPORTED_FORMATS}")

    # If you have an image, uncomment and use:
    # preview = previewer.generate_preview("path/to/image.jpg")
    # print(f"Dimensions: {preview.get('dimensions')}")
    # print(f"Format: {preview.get('format')}")
    # print(f"Has transparency: {preview.get('has_transparency')}")
    #
    # exif = previewer.extract_exif("path/to/image.jpg")
    # if exif:
    #     print("\nEXIF Data:")
    #     for key, value in exif.items():
    #         print(f"  {key}: {value}")

    print("\nFeatures:")
    print("- Zoom: 10% to 400%")
    print("- Rotation: 90°, 180°, 270°")
    print("- EXIF: Camera make, model, date, settings")
    print("- Thumbnail caching: Fast reload")


def example_document_preview():
    """Example: Document preview (PDF, Office)"""
    print("\n=== Document Preview Example ===\n")

    previewer = DocumentPreviewer()

    print("Document Preview Capabilities:")
    print(f"- PDF text extraction: {previewer._pypdf_available}")
    print(f"- PDF rendering: {previewer._pdf2image_available}")
    print(f"- Office metadata: {previewer._office_available}")

    # If you have a PDF, uncomment and use:
    # preview = previewer.generate_preview("path/to/document.pdf")
    # print(f"Pages: {preview.get('pages')}")
    # print(f"Title: {preview.get('title')}")
    # print(f"Author: {preview.get('author')}")
    #
    # text = previewer.extract_text("path/to/document.pdf", max_length=500)
    # print(f"\nExtracted text (first 500 chars):")
    # print(text[:500])

    print("\nFeatures:")
    print("- PDF: Multi-page viewing")
    print("- Word: Text extraction from .docx")
    print("- Excel: Sheet count")
    print("- PowerPoint: Slide count")
    print("- Metadata: Title, author, dates")


def example_preview_manager():
    """Example: Preview manager with caching"""
    print("\n=== Preview Manager Example ===\n")

    # Create manager with cache
    cache_dir = Path.home() / '.smart_search_test' / 'preview_cache'
    manager = PreviewManager(
        cache_dir=str(cache_dir),
        memory_cache_size=50,
        cache_ttl_hours=24
    )

    print(f"Cache directory: {cache_dir}")

    # Create sample file
    sample_file = Path(__file__).parent.parent / "test_file.txt"
    sample_file.write_text("Hello, World!\nThis is a test file.\n" * 50)

    # First load (cold)
    import time
    start = time.time()
    preview1 = manager.get_preview(str(sample_file))
    cold_time = (time.time() - start) * 1000

    # Second load (cached)
    start = time.time()
    preview2 = manager.get_preview(str(sample_file))
    cached_time = (time.time() - start) * 1000

    print(f"Cold load: {cold_time:.2f}ms")
    print(f"Cached load: {cached_time:.2f}ms")
    print(f"Speedup: {cold_time / cached_time:.1f}x")

    # Cache stats
    stats = manager.get_cache_stats()
    print("\nCache Statistics:")
    print(f"  Memory cache: {stats['memory_items']}/{stats['memory_capacity']}")
    print(f"  Disk cache: {stats['disk_items']} files")
    print(f"  Disk size: {stats['disk_size_mb']} MB")

    # Preload multiple files
    print("\n--- Preload Example ---")
    files = [str(sample_file)] * 5  # Same file 5 times

    def on_loaded(path, preview):
        print(f"  Loaded: {Path(path).name}")

    manager.preload_previews(files, callback=on_loaded)
    time.sleep(0.5)  # Wait for background loading

    # Cleanup
    manager.shutdown()
    print("\nManager shutdown complete")


def example_lazy_loading():
    """Example: Lazy loading pattern"""
    print("\n=== Lazy Loading Example ===\n")

    print("Lazy loading simulates background preview generation:")
    print("1. Show loading placeholder")
    print("2. Load preview in background thread")
    print("3. Update UI when ready")
    print()
    print("Benefits:")
    print("- Non-blocking UI")
    print("- Responsive even with large files")
    print("- Can cancel if user switches files")
    print()
    print("See EnhancedPreviewPanel._load_preview_async() for implementation")


def example_find_in_preview():
    """Example: Find functionality"""
    print("\n=== Find in Preview Example ===\n")

    print("Find in Preview Features:")
    print("- Keyboard shortcut: Ctrl+F")
    print("- Search box with 'Next' button")
    print("- Highlights matches in text")
    print("- Wraps around when reaching end")
    print()
    print("Usage:")
    print("1. Open text file in preview")
    print("2. Press Ctrl+F")
    print("3. Type search term")
    print("4. Press Enter or click 'Next'")


def example_integration():
    """Example: Integration into main window"""
    print("\n=== Integration Example ===\n")

    print("To integrate enhanced preview into Smart Search Pro:")
    print()
    print("1. Import:")
    print("   from ui.preview_panel_enhanced import EnhancedPreviewPanel")
    print()
    print("2. Create in __init__:")
    print("   self.preview_panel = EnhancedPreviewPanel()")
    print("   layout.addWidget(self.preview_panel)")
    print()
    print("3. Connect signals:")
    print("   self.preview_panel.open_requested.connect(self.open_file)")
    print("   self.preview_panel.open_location_requested.connect(self.open_location)")
    print()
    print("4. Use:")
    print("   self.preview_panel.set_file(selected_file_path)")
    print()
    print("5. Cleanup:")
    print("   def closeEvent(self, event):")
    print("       self.preview_panel.cleanup()")
    print("       event.accept()")


def main():
    """Run all examples"""
    print("=" * 70)
    print("Enhanced Preview System - Usage Examples")
    print("=" * 70)

    try:
        example_text_preview()
        example_image_preview()
        example_document_preview()
        example_preview_manager()
        example_lazy_loading()
        example_find_in_preview()
        example_integration()
    except Exception as e:
        print(f"\nError in examples: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 70)
    print("Examples complete!")
    print()
    print("To see it in action:")
    print("  python test_preview_enhancements.py")
    print()


if __name__ == '__main__':
    main()
