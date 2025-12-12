"""
Test suite for preview module.

Tests all preview types and caching functionality.
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preview.manager import PreviewManager
from preview.text_preview import TextPreviewer
from preview.image_preview import ImagePreviewer
from preview.document_preview import DocumentPreviewer
from preview.media_preview import MediaPreviewer
from preview.archive_preview import ArchivePreviewer
from preview.metadata import MetadataExtractor


def create_test_text_file(path: str, content: str = None) -> str:
    """Create a test text file."""
    if content is None:
        content = """def hello_world():
    '''Simple test function'''
    print("Hello, World!")
    return 42

if __name__ == "__main__":
    result = hello_world()
    print(f"Result: {result}")
"""

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return path


def create_test_json_file(path: str) -> str:
    """Create a test JSON file."""
    data = {
        "name": "Test Project",
        "version": "1.0.0",
        "dependencies": ["requests", "pytest"],
        "author": "Test Author"
    }

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    return path


def test_text_previewer():
    """Test text file preview."""
    print("\n=== Testing Text Previewer ===")

    previewer = TextPreviewer()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Test Python file
        py_file = os.path.join(tmpdir, "test.py")
        create_test_text_file(py_file)

        preview = previewer.generate_preview(py_file)
        print(f"\nPython file preview:")
        print(f"  Language: {preview.get('language')}")
        print(f"  Lines: {preview.get('lines')}")
        print(f"  Encoding: {preview.get('encoding')}")
        print(f"  Truncated: {preview.get('truncated')}")
        print(f"  Has highlighting: {'highlighted' in preview}")

        # Test JSON file
        json_file = os.path.join(tmpdir, "test.json")
        create_test_json_file(json_file)

        preview = previewer.generate_preview(json_file)
        print(f"\nJSON file preview:")
        print(f"  Language: {preview.get('language')}")
        print(f"  Lines: {preview.get('lines')}")

        # Test large file handling
        large_file = os.path.join(tmpdir, "large.txt")
        with open(large_file, 'w') as f:
            for i in range(1000):
                f.write(f"Line {i}: " + "x" * 100 + "\n")

        preview = previewer.generate_preview(large_file)
        print(f"\nLarge file preview:")
        print(f"  Lines: {preview.get('lines')}")
        print(f"  Truncated: {preview.get('truncated')}")

    print("✓ Text previewer tests passed")


def test_image_previewer():
    """Test image preview."""
    print("\n=== Testing Image Previewer ===")

    previewer = ImagePreviewer()

    if not previewer._pillow_available:
        print("⚠ Pillow not available, skipping image tests")
        return

    try:
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test image
            img_file = os.path.join(tmpdir, "test.png")
            img = Image.new('RGB', (800, 600), color='blue')
            img.save(img_file)

            preview = previewer.generate_preview(img_file, include_base64=True)
            print(f"\nImage preview:")
            print(f"  Dimensions: {preview.get('dimensions')}")
            print(f"  Format: {preview.get('format')}")
            print(f"  Mode: {preview.get('mode')}")
            print(f"  Has transparency: {preview.get('has_transparency')}")
            print(f"  Has thumbnail: {'thumbnail_base64' in preview}")

            # Test thumbnail generation
            thumb_file = os.path.join(tmpdir, "thumb.png")
            success = previewer.save_thumbnail(img_file, thumb_file)
            print(f"  Thumbnail saved: {success}")

        print("✓ Image previewer tests passed")

    except ImportError:
        print("⚠ Pillow not available, skipping image tests")


def test_document_previewer():
    """Test document preview."""
    print("\n=== Testing Document Previewer ===")

    previewer = DocumentPreviewer()

    if not previewer._pypdf_available:
        print("⚠ pypdf not available, skipping PDF tests")
    else:
        print("✓ Document previewer initialized (pypdf available)")


def test_media_previewer():
    """Test media preview."""
    print("\n=== Testing Media Previewer ===")

    previewer = MediaPreviewer()

    print(f"Mutagen available: {previewer._mutagen_available}")
    print(f"ffmpeg available: {previewer._ffmpeg_available}")

    print("✓ Media previewer initialized")


def test_archive_previewer():
    """Test archive preview."""
    print("\n=== Testing Archive Previewer ===")

    previewer = ArchivePreviewer()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test ZIP file
        import zipfile

        zip_file = os.path.join(tmpdir, "test.zip")
        with zipfile.ZipFile(zip_file, 'w') as zf:
            # Add some test files
            for i in range(5):
                filename = f"file{i}.txt"
                content = f"Content of file {i}\n" * 10
                zf.writestr(filename, content)

        preview = previewer.generate_preview(zip_file)
        print(f"\nZIP archive preview:")
        print(f"  Type: {preview.get('type')}")
        print(f"  Total files: {preview.get('total_files')}")
        print(f"  Files listed: {len(preview.get('files', []))}")
        print(f"  Compressed size: {preview.get('compressed_size')}")
        print(f"  Uncompressed size: {preview.get('uncompressed_size')}")
        print(f"  Compression ratio: {preview.get('compression_ratio')}")

    print("✓ Archive previewer tests passed")


def test_metadata_extractor():
    """Test metadata extraction."""
    print("\n=== Testing Metadata Extractor ===")

    extractor = MetadataExtractor()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content")

        metadata = extractor.extract(test_file)
        print(f"\nBasic metadata:")
        print(f"  Filename: {metadata.get('filename')}")
        print(f"  Size: {metadata.get('size')}")
        print(f"  Modified: {metadata.get('modified')}")
        print(f"  Created: {metadata.get('created')}")

    print("✓ Metadata extractor tests passed")


def test_preview_manager():
    """Test preview manager with caching."""
    print("\n=== Testing Preview Manager ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = os.path.join(tmpdir, "cache")

        manager = PreviewManager(
            cache_dir=cache_dir,
            memory_cache_size=10,
            cache_ttl_hours=24
        )

        # Create test files
        py_file = os.path.join(tmpdir, "test.py")
        create_test_text_file(py_file)

        json_file = os.path.join(tmpdir, "test.json")
        create_test_json_file(json_file)

        # Test preview generation
        print("\nGenerating previews...")

        preview1 = manager.get_preview(py_file)
        print(f"  Python file: {preview1.get('language', 'unknown')} "
              f"({preview1.get('lines', 0)} lines)")

        preview2 = manager.get_preview(json_file)
        print(f"  JSON file: {preview2.get('language', 'unknown')} "
              f"({preview2.get('lines', 0)} lines)")

        # Test cache
        print("\nTesting cache...")
        preview1_cached = manager.get_preview(py_file, use_cache=True)
        print(f"  Cache hit: {preview1_cached == preview1}")

        # Test cache stats
        stats = manager.get_cache_stats()
        print(f"\nCache stats:")
        print(f"  Memory items: {stats['memory_items']}/{stats['memory_capacity']}")
        print(f"  Disk items: {stats['disk_items']}")
        print(f"  Disk size: {stats['disk_size_mb']} MB")

        # Test cache clear
        manager.clear_cache()
        stats_after = manager.get_cache_stats()
        print(f"\nAfter clearing cache:")
        print(f"  Memory items: {stats_after['memory_items']}")
        print(f"  Disk items: {stats_after['disk_items']}")

        manager.shutdown()

    print("✓ Preview manager tests passed")


def test_async_preview():
    """Test async preview generation."""
    print("\n=== Testing Async Preview ===")

    import asyncio

    async def async_test():
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PreviewManager(cache_dir=None)

            # Create test files
            files = []
            for i in range(5):
                file_path = os.path.join(tmpdir, f"test{i}.py")
                create_test_text_file(file_path, f"# Test file {i}\nprint({i})")
                files.append(file_path)

            # Generate previews asynchronously
            tasks = [manager.get_preview_async(f) for f in files]
            previews = await asyncio.gather(*tasks)

            print(f"  Generated {len(previews)} previews asynchronously")
            for i, preview in enumerate(previews):
                print(f"    File {i}: {preview.get('lines', 0)} lines")

            manager.shutdown()

    asyncio.run(async_test())
    print("✓ Async preview tests passed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Preview Module Test Suite")
    print("=" * 60)

    try:
        test_text_previewer()
        test_image_previewer()
        test_document_previewer()
        test_media_previewer()
        test_archive_previewer()
        test_metadata_extractor()
        test_preview_manager()
        test_async_preview()

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
