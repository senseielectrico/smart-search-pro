#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify Preview Enhancements
Quick verification that all enhancements are working
"""

import sys
import os
from pathlib import Path

# Fix console encoding for Windows
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

# Add to path
sys.path.insert(0, str(Path(__file__).parent))


def verify_imports():
    """Verify all modules can be imported"""
    print("\n=== Verifying Imports ===")

    results = []

    # Core modules
    modules = [
        ('preview.text_preview', 'TextPreviewer'),
        ('preview.image_preview', 'ImagePreviewer'),
        ('preview.document_preview', 'DocumentPreviewer'),
        ('preview.manager', 'PreviewManager'),
        ('ui.preview_panel_enhanced', 'EnhancedPreviewPanel'),
    ]

    for module_name, class_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✓ {module_name}.{class_name}")
            results.append(True)
        except Exception as e:
            print(f"✗ {module_name}.{class_name}: {e}")
            results.append(False)

    return all(results)


def verify_features():
    """Verify feature availability"""
    print("\n=== Verifying Features ===")

    from preview.text_preview import TextPreviewer
    from preview.image_preview import ImagePreviewer
    from preview.document_preview import DocumentPreviewer

    text_prev = TextPreviewer()
    img_prev = ImagePreviewer()
    doc_prev = DocumentPreviewer()

    features = {
        'Text Preview': True,
        'Syntax Highlighting (40+ languages)': text_prev._pygments_available,
        'Markdown Rendering': text_prev._markdown_available,
        'Image Preview': img_prev._pillow_available,
        'EXIF Metadata': img_prev._exif_available,
        'PDF Text Extraction': doc_prev._pypdf_available,
        'PDF Page Rendering': doc_prev._pdf2image_available,
    }

    results = []
    for feature, available in features.items():
        status = "✓" if available else "○"
        print(f"{status} {feature}: {'Available' if available else 'Not available'}")
        results.append(available)

    # Count languages
    lang_count = len(text_prev.LANGUAGE_MAP)
    print(f"\n  Supported languages: {lang_count}")

    return True  # Features are optional


def verify_components():
    """Verify UI components"""
    print("\n=== Verifying UI Components ===")

    try:
        from PyQt6.QtWidgets import QApplication
        from ui.preview_panel_enhanced import EnhancedPreviewPanel

        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)

        # Create panel
        panel = EnhancedPreviewPanel()

        components = {
            'Loading Placeholder': hasattr(panel, 'loading_widget'),
            'Content Stack': hasattr(panel, 'content_stack'),
            'Toolbar': hasattr(panel, 'toolbar'),
            'Find Dialog': hasattr(panel, 'find_dialog'),
            'Preview Manager': hasattr(panel, 'preview_manager'),
            'Text Previewer': hasattr(panel, 'text_previewer'),
            'Image Previewer': hasattr(panel, 'image_previewer'),
            'Document Previewer': hasattr(panel, 'doc_previewer'),
        }

        results = []
        for component, exists in components.items():
            status = "✓" if exists else "✗"
            print(f"{status} {component}")
            results.append(exists)

        # Cleanup
        panel.cleanup()

        return all(results)

    except Exception as e:
        print(f"✗ Component verification failed: {e}")
        return False


def verify_methods():
    """Verify key methods exist"""
    print("\n=== Verifying Methods ===")

    try:
        from preview.text_preview import TextPreviewer
        from preview.image_preview import ImagePreviewer
        from preview.document_preview import DocumentPreviewer

        text_prev = TextPreviewer()
        img_prev = ImagePreviewer()
        doc_prev = DocumentPreviewer()

        methods = [
            (text_prev, 'format_json', 'JSON formatting'),
            (text_prev, 'render_markdown', 'Markdown rendering'),
            (img_prev, 'extract_exif', 'EXIF extraction'),
            (img_prev, 'rotate_image', 'Image rotation'),
            (img_prev, 'create_thumbnail_cache', 'Thumbnail caching'),
            (doc_prev, 'render_pdf_pages', 'PDF multi-page'),
            (doc_prev, 'extract_text_from_docx', 'Word text extraction'),
        ]

        results = []
        for obj, method_name, description in methods:
            has_method = hasattr(obj, method_name) and callable(getattr(obj, method_name))
            status = "✓" if has_method else "✗"
            print(f"{status} {description} ({method_name})")
            results.append(has_method)

        return all(results)

    except Exception as e:
        print(f"✗ Method verification failed: {e}")
        return False


def verify_files():
    """Verify all required files exist"""
    print("\n=== Verifying Files ===")

    base_dir = Path(__file__).parent

    files = [
        'preview/text_preview.py',
        'preview/image_preview.py',
        'preview/document_preview.py',
        'preview/manager.py',
        'ui/preview_panel_enhanced.py',
        'test_preview_enhancements.py',
        'install_preview_deps.py',
        'PREVIEW_ENHANCEMENTS.md',
        'preview/PREVIEW_QUICKSTART.md',
        'preview/USAGE_EXAMPLES.py',
        'PREVIEW_IMPLEMENTATION_SUMMARY.md',
    ]

    results = []
    for file_path in files:
        full_path = base_dir / file_path
        exists = full_path.exists()
        status = "✓" if exists else "✗"
        size = f"({full_path.stat().st_size // 1024} KB)" if exists else ""
        print(f"{status} {file_path} {size}")
        results.append(exists)

    return all(results)


def verify_performance():
    """Quick performance check"""
    print("\n=== Performance Check ===")

    try:
        import time
        from preview.manager import PreviewManager

        # Create manager
        manager = PreviewManager(cache_dir=None)  # Memory only

        # Create test file
        test_file = Path(__file__).parent / "test_perf.txt"
        test_file.write_text("Test content\n" * 100)

        # Cold load
        start = time.time()
        preview1 = manager.get_preview(str(test_file))
        cold_time = (time.time() - start) * 1000

        # Warm load
        start = time.time()
        preview2 = manager.get_preview(str(test_file))
        warm_time = (time.time() - start) * 1000

        speedup = cold_time / warm_time if warm_time > 0 else 0

        print(f"Cold load: {cold_time:.2f}ms")
        print(f"Warm load: {warm_time:.2f}ms")
        print(f"Speedup: {speedup:.1f}x")

        # Cleanup
        test_file.unlink(missing_ok=True)
        manager.shutdown()

        # Check performance
        is_fast = cold_time < 500 and warm_time < 50
        print(f"\n{'✓' if is_fast else '○'} Performance: {'Good' if is_fast else 'Acceptable'}")

        return True

    except Exception as e:
        print(f"✗ Performance check failed: {e}")
        return False


def print_summary(results):
    """Print verification summary"""
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)

    total = len(results)
    passed = sum(1 for r in results if r)

    for name, result in results.items():
        status = "✓" if result else "✗"
        print(f"{status} {name}")

    print()
    print(f"Result: {passed}/{total} checks passed")

    if passed == total:
        print("✓ All verifications passed!")
        print("\nYou can now:")
        print("  1. Install dependencies: python install_preview_deps.py")
        print("  2. Test features: python test_preview_enhancements.py")
        print("  3. See examples: python preview/USAGE_EXAMPLES.py")
        return True
    else:
        print("○ Some checks failed. See above for details.")
        return False


def main():
    """Run all verifications"""
    print("=" * 60)
    print("Preview Enhancements - Verification")
    print("=" * 60)

    results = {
        'Imports': verify_imports(),
        'Features': verify_features(),
        'Components': verify_components(),
        'Methods': verify_methods(),
        'Files': verify_files(),
        'Performance': verify_performance(),
    }

    success = print_summary(results)

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
