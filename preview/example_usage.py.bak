"""
Example usage of the Preview Module for Smart Search Pro.

Demonstrates:
- Basic preview generation
- Cache management
- Async operations
- Different file types
- Integration patterns
"""

import asyncio
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preview import PreviewManager


def example_basic_usage():
    """Basic preview generation example."""
    print("\n=== Basic Usage ===\n")

    manager = PreviewManager(
        cache_dir="./preview_cache",
        memory_cache_size=50,
        cache_ttl_hours=24
    )

    # Example files (use your own paths)
    test_files = [
        r"C:\Users\ramos\.local\bin\smart_search\main.py",
        r"C:\Users\ramos\.local\bin\smart_search\README.md",
    ]

    for file_path in test_files:
        if not Path(file_path).exists():
            continue

        print(f"Preview for: {file_path}")

        preview = manager.get_preview(file_path, include_metadata=True)

        if 'error' in preview:
            print(f"  Error: {preview['error']}")
            continue

        # Display based on type
        if 'language' in preview:
            # Text file
            print(f"  Type: Text ({preview['language']})")
            print(f"  Lines: {preview.get('lines', 0)}")
            print(f"  Encoding: {preview.get('encoding', 'unknown')}")

        elif preview.get('type') == 'pdf':
            # PDF document
            print(f"  Type: PDF")
            print(f"  Pages: {preview.get('pages', 0)}")
            if 'title' in preview:
                print(f"  Title: {preview['title']}")

        elif 'dimensions' in preview:
            # Image
            print(f"  Type: Image")
            print(f"  Dimensions: {preview['dimensions']}")
            print(f"  Format: {preview.get('format', 'unknown')}")

        elif preview.get('type') == 'audio':
            # Audio file
            print(f"  Type: Audio")
            print(f"  Duration: {preview.get('duration', 'unknown')}")
            if 'artist' in preview:
                print(f"  Artist: {preview['artist']}")

        print()

    # Show cache stats
    stats = manager.get_cache_stats()
    print(f"Cache Statistics:")
    print(f"  Memory: {stats['memory_items']}/{stats['memory_capacity']} items")
    print(f"  Disk: {stats['disk_items']} items ({stats['disk_size_mb']} MB)")

    manager.shutdown()


async def example_async_usage():
    """Async preview generation example."""
    print("\n=== Async Usage ===\n")

    manager = PreviewManager()

    # Example files
    test_files = [
        r"C:\Users\ramos\.local\bin\smart_search\main.py",
        r"C:\Users\ramos\.local\bin\smart_search\config.py",
        r"C:\Users\ramos\.local\bin\smart_search\backend.py",
    ]

    # Filter existing files
    files = [f for f in test_files if Path(f).exists()]

    print(f"Generating {len(files)} previews asynchronously...")

    # Generate all previews concurrently
    tasks = [manager.get_preview_async(f) for f in files]
    previews = await asyncio.gather(*tasks)

    # Display results
    for file_path, preview in zip(files, previews):
        filename = Path(file_path).name
        if 'error' not in preview:
            lines = preview.get('lines', 0)
            lang = preview.get('language', 'unknown')
            print(f"  {filename}: {lines} lines ({lang})")

    manager.shutdown()


def example_cache_management():
    """Cache management example."""
    print("\n=== Cache Management ===\n")

    manager = PreviewManager(
        cache_dir="./temp_cache",
        memory_cache_size=5
    )

    # Generate some previews
    test_file = r"C:\Users\ramos\.local\bin\smart_search\main.py"

    if Path(test_file).exists():
        # First call - generates preview
        print("First call (no cache)...")
        preview1 = manager.get_preview(test_file)
        print(f"  Generated preview with {preview1.get('lines', 0)} lines")

        # Second call - from cache
        print("\nSecond call (from cache)...")
        preview2 = manager.get_preview(test_file, use_cache=True)
        print(f"  Retrieved from cache: {preview1 == preview2}")

        # Third call - bypass cache
        print("\nThird call (bypass cache)...")
        preview3 = manager.get_preview(test_file, use_cache=False)
        print(f"  Fresh preview generated")

        # Cache stats
        stats = manager.get_cache_stats()
        print(f"\nCache contains {stats['memory_items']} items")

        # Clear cache
        manager.clear_cache()
        print("Cache cleared")

        stats_after = manager.get_cache_stats()
        print(f"Cache now contains {stats_after['memory_items']} items")

    manager.shutdown()


def example_preload():
    """Preload preview example."""
    print("\n=== Preload Previews ===\n")

    manager = PreviewManager()

    # Callback for when preview is ready
    def on_preview_ready(file_path, preview):
        filename = Path(file_path).name
        if 'error' not in preview:
            lines = preview.get('lines', 'N/A')
            print(f"  ✓ {filename}: {lines} lines")
        else:
            print(f"  ✗ {filename}: {preview['error']}")

    # Files to preload
    test_files = [
        r"C:\Users\ramos\.local\bin\smart_search\main.py",
        r"C:\Users\ramos\.local\bin\smart_search\backend.py",
        r"C:\Users\ramos\.local\bin\smart_search\ui.py",
    ]

    files = [f for f in test_files if Path(f).exists()]

    print(f"Preloading {len(files)} previews in background...")

    manager.preload_previews(files, callback=on_preview_ready)

    # Wait a moment for preloading to complete
    import time
    time.sleep(2)

    stats = manager.get_cache_stats()
    print(f"\nPreloaded {stats['memory_items']} previews")

    manager.shutdown()


def example_specific_previewers():
    """Using specific previewers directly."""
    print("\n=== Specific Previewers ===\n")

    from preview.text_preview import TextPreviewer
    from preview.image_preview import ImagePreviewer

    # Text previewer
    text_previewer = TextPreviewer()
    test_file = r"C:\Users\ramos\.local\bin\smart_search\main.py"

    if Path(test_file).exists():
        print("Text Preview:")
        preview = text_previewer.generate_preview(test_file)
        print(f"  Language: {preview.get('language')}")
        print(f"  Lines: {preview.get('lines')}")
        print(f"  Has syntax highlighting: {'highlighted' in preview}")

        # First few lines of preview
        text_lines = preview.get('text', '').split('\n')[:5]
        print(f"\n  First lines:")
        for line in text_lines:
            print(f"    {line}")

    # Image previewer
    print("\n\nImage Preview Example:")
    print("  (Would display image info if image file provided)")

    image_previewer = ImagePreviewer()
    print(f"  Image preview available: {image_previewer._pillow_available}")


def main():
    """Run all examples."""
    print("=" * 60)
    print("Smart Search Pro - Preview Module Examples")
    print("=" * 60)

    try:
        # Sync examples
        example_basic_usage()
        example_cache_management()
        example_preload()
        example_specific_previewers()

        # Async example
        asyncio.run(example_async_usage())

        print("\n" + "=" * 60)
        print("All examples completed!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
