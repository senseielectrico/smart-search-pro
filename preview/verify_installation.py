"""
Verification script for the preview module installation.

Checks:
- All modules can be imported
- Required dependencies available
- Optional dependencies status
- Basic functionality works
"""

import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_imports():
    """Check if all modules can be imported."""
    print("\n=== Checking Imports ===\n")

    modules = [
        ('preview', 'Preview package'),
        ('preview.manager', 'Preview Manager'),
        ('preview.text_preview', 'Text Previewer'),
        ('preview.image_preview', 'Image Previewer'),
        ('preview.document_preview', 'Document Previewer'),
        ('preview.media_preview', 'Media Previewer'),
        ('preview.archive_preview', 'Archive Previewer'),
        ('preview.metadata', 'Metadata Extractor'),
    ]

    all_ok = True

    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"✓ {description:25} - OK")
        except ImportError as e:
            print(f"✗ {description:25} - FAILED: {e}")
            all_ok = False

    return all_ok


def check_dependencies():
    """Check optional dependencies."""
    print("\n=== Checking Dependencies ===\n")

    dependencies = [
        ('PIL', 'Pillow', 'Image preview and thumbnails'),
        ('pypdf', 'pypdf', 'PDF document preview'),
        ('mutagen', 'mutagen', 'Audio/video metadata'),
        ('pygments', 'Pygments', 'Syntax highlighting'),
        ('chardet', 'chardet', 'Encoding detection'),
        ('olefile', 'olefile', 'Office document metadata'),
    ]

    available = []
    missing = []

    for import_name, package_name, description in dependencies:
        try:
            __import__(import_name)
            print(f"✓ {package_name:12} - {description}")
            available.append(package_name)
        except ImportError:
            print(f"⚠ {package_name:12} - NOT INSTALLED ({description})")
            missing.append(package_name)

    print(f"\nAvailable: {len(available)}/{len(dependencies)}")

    if missing:
        print(f"\nTo install missing dependencies:")
        print(f"  pip install {' '.join(missing)}")

    return available, missing


def check_external_tools():
    """Check external tools availability."""
    print("\n=== Checking External Tools ===\n")

    import subprocess

    tools = [
        ('ffmpeg', 'FFmpeg', 'Video thumbnails and media info'),
        ('7z', '7-Zip', '7z archive support'),
        ('unrar', 'UnRAR', 'RAR archive support'),
    ]

    available = []
    missing = []

    for command, name, description in tools:
        try:
            result = subprocess.run(
                [command],
                capture_output=True,
                timeout=5
            )
            print(f"✓ {name:12} - {description}")
            available.append(name)
        except (subprocess.SubprocessError, FileNotFoundError):
            print(f"⚠ {name:12} - NOT AVAILABLE ({description})")
            missing.append(name)

    print(f"\nAvailable: {len(available)}/{len(tools)}")

    return available, missing


def test_basic_functionality():
    """Test basic preview functionality."""
    print("\n=== Testing Basic Functionality ===\n")

    import tempfile
    from preview import PreviewManager

    all_ok = True

    try:
        # Create manager
        manager = PreviewManager()
        print("✓ PreviewManager created")

        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('Hello, World!')\n")
            test_file = f.name

        try:
            # Generate preview
            preview = manager.get_preview(test_file)

            if 'error' in preview:
                print(f"✗ Preview generation failed: {preview['error']}")
                all_ok = False
            else:
                print(f"✓ Preview generated for test file")
                print(f"  - Language: {preview.get('language', 'unknown')}")
                print(f"  - Lines: {preview.get('lines', 0)}")
                print(f"  - Has highlighting: {'highlighted' in preview}")

            # Test cache
            preview2 = manager.get_preview(test_file, use_cache=True)
            if preview == preview2:
                print("✓ Cache working correctly")
            else:
                print("⚠ Cache may not be working")

            # Test stats
            stats = manager.get_cache_stats()
            print(f"✓ Cache stats: {stats['memory_items']} items in memory")

        finally:
            import os
            os.unlink(test_file)

        manager.shutdown()
        print("✓ Manager shutdown successful")

    except Exception as e:
        print(f"✗ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        all_ok = False

    return all_ok


def test_all_previewers():
    """Test individual previewers."""
    print("\n=== Testing Individual Previewers ===\n")

    import tempfile
    import json

    all_ok = True

    # Test Text Previewer
    try:
        from preview.text_preview import TextPreviewer

        previewer = TextPreviewer()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test():\n    pass\n")
            test_file = f.name

        try:
            preview = previewer.generate_preview(test_file)
            if 'error' not in preview:
                print(f"✓ Text Previewer works")
            else:
                print(f"✗ Text Previewer failed")
                all_ok = False
        finally:
            import os
            os.unlink(test_file)

    except Exception as e:
        print(f"✗ Text Previewer test failed: {e}")
        all_ok = False

    # Test Image Previewer
    try:
        from preview.image_preview import ImagePreviewer

        previewer = ImagePreviewer()
        if previewer._pillow_available:
            from PIL import Image

            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                img = Image.new('RGB', (100, 100), 'red')
                img.save(f.name)
                test_file = f.name

            try:
                preview = previewer.generate_preview(test_file)
                if 'error' not in preview:
                    print(f"✓ Image Previewer works")
                else:
                    print(f"✗ Image Previewer failed")
                    all_ok = False
            finally:
                import os
                os.unlink(test_file)
        else:
            print(f"⚠ Image Previewer skipped (Pillow not available)")

    except Exception as e:
        print(f"⚠ Image Previewer test skipped: {e}")

    # Test Archive Previewer
    try:
        from preview.archive_preview import ArchivePreviewer
        import zipfile

        previewer = ArchivePreviewer()

        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            test_file = f.name

        try:
            with zipfile.ZipFile(test_file, 'w') as zf:
                zf.writestr('test.txt', 'content')

            preview = previewer.generate_preview(test_file)
            if 'error' not in preview:
                print(f"✓ Archive Previewer works")
            else:
                print(f"✗ Archive Previewer failed")
                all_ok = False
        finally:
            import os
            os.unlink(test_file)

    except Exception as e:
        print(f"✗ Archive Previewer test failed: {e}")
        all_ok = False

    return all_ok


def generate_report():
    """Generate installation report."""
    print("\n" + "=" * 60)
    print("PREVIEW MODULE VERIFICATION REPORT")
    print("=" * 60)

    results = {}

    # Run checks
    results['imports'] = check_imports()
    results['dependencies'] = check_dependencies()
    results['external_tools'] = check_external_tools()
    results['basic_functionality'] = test_basic_functionality()
    results['previewers'] = test_all_previewers()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = all([
        results['imports'],
        results['basic_functionality'],
        results['previewers']
    ])

    if all_passed:
        print("\n✓ Preview module is fully functional!")
        print("\nCore features: WORKING")
    else:
        print("\n⚠ Some issues detected")
        print("\nPlease review the report above for details.")

    available_deps, missing_deps = results['dependencies']
    if missing_deps:
        print(f"\nOptional features: {len(available_deps)}/6 available")
        print("Some enhanced features may not be available.")
    else:
        print("\nAll optional dependencies: INSTALLED")

    available_tools, missing_tools = results['external_tools']
    if missing_tools:
        print(f"\nExternal tools: {len(available_tools)}/3 available")
        print("Some file types may have limited support.")

    print("\n" + "=" * 60)

    return all_passed


def main():
    """Run verification."""
    try:
        success = generate_report()
        return 0 if success else 1
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
