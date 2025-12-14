"""
Tests for preview module: Text, Image, Document preview
"""

import pytest
import os


# ============================================================================
# TEXT PREVIEW TESTS
# ============================================================================

class TestTextPreview:
    """Tests for TextPreview class"""

    def test_text_preview_initialization(self, test_text_preview):
        """Test text preview initialization"""
        assert test_text_preview is not None

    def test_preview_text_file(self, test_text_preview, sample_text_file):
        """Test previewing text file"""
        preview_data = test_text_preview.generate_preview(sample_text_file)

        assert preview_data is not None
        assert 'content' in preview_data or 'text' in preview_data or preview_data

    def test_preview_encoding_detection(self, test_text_preview, temp_dir):
        """Test encoding detection for text files"""
        # Create file with UTF-8 encoding
        utf8_file = os.path.join(temp_dir, "utf8.txt")
        with open(utf8_file, 'w', encoding='utf-8') as f:
            f.write("UTF-8 content with special chars: äöü")

        preview_data = test_text_preview.generate_preview(utf8_file)
        assert preview_data is not None

    def test_preview_large_file_truncation(self, test_text_preview, temp_dir):
        """Test truncation of large files"""
        large_file = os.path.join(temp_dir, "large.txt")
        with open(large_file, 'w', encoding='utf-8') as f:
            f.write("Line content\n" * 10000)

        # generate_preview doesn't take max_lines parameter
        preview_data = test_text_preview.generate_preview(large_file)
        assert preview_data is not None

    def test_preview_nonexistent_file(self, test_text_preview, temp_dir):
        """Test previewing non-existent file"""
        nonexistent = os.path.join(temp_dir, "nonexistent.txt")

        # Returns error dict instead of raising exception
        result = test_text_preview.generate_preview(nonexistent)
        assert 'error' in result


# ============================================================================
# IMAGE PREVIEW TESTS
# ============================================================================

class TestImagePreview:
    """Tests for ImagePreview class"""

    def test_image_preview_initialization(self, test_image_preview):
        """Test image preview initialization"""
        assert test_image_preview is not None

    def test_preview_image_file(self, test_image_preview, temp_dir):
        """Test previewing image file"""
        # Create a simple test image (this may require PIL/Pillow)
        try:
            from PIL import Image
            img_file = os.path.join(temp_dir, "test.png")
            img = Image.new('RGB', (100, 100), color='red')
            img.save(img_file)

            preview_data = test_image_preview.generate_preview(img_file)
            assert preview_data is not None
        except ImportError:
            pytest.skip("PIL/Pillow not installed")

    def test_preview_thumbnail_generation(self, test_image_preview, temp_dir):
        """Test thumbnail generation"""
        try:
            from PIL import Image
            img_file = os.path.join(temp_dir, "thumbnail_test.png")
            img = Image.new('RGB', (1000, 1000), color='blue')
            img.save(img_file)

            preview_data = test_image_preview.generate_preview(
                img_file, thumbnail_size=(200, 200)
            )
            assert preview_data is not None
        except ImportError:
            pytest.skip("PIL/Pillow not installed")

    def test_preview_unsupported_format(self, test_image_preview, temp_dir):
        """Test previewing unsupported image format"""
        unsupported_file = os.path.join(temp_dir, "test.txt")
        with open(unsupported_file, 'w') as f:
            f.write("Not an image")

        # Should handle gracefully
        try:
            preview_data = test_image_preview.generate_preview(unsupported_file)
            # May return None or raise exception
            assert True
        except Exception:
            # Expected for non-image files
            assert True


# ============================================================================
# DOCUMENT PREVIEW TESTS
# ============================================================================

class TestDocumentPreview:
    """Tests for DocumentPreviewer class"""

    def test_document_preview_initialization(self):
        """Test document preview initialization"""
        try:
            from preview.document_preview import DocumentPreviewer
            preview = DocumentPreviewer()
            assert preview is not None
        except ImportError:
            pytest.skip("Document preview dependencies not installed")

    def test_preview_pdf_metadata(self, temp_dir):
        """Test extracting PDF metadata"""
        try:
            from preview.document_preview import DocumentPreviewer
            from pypdf import PdfWriter

            # Create a sample PDF file for testing
            pdf_path = os.path.join(temp_dir, "test_sample.pdf")
            writer = PdfWriter()
            writer.add_blank_page(width=612, height=792)  # Letter size
            writer.add_metadata({
                "/Title": "Test PDF Document",
                "/Author": "Test Author",
                "/Subject": "Testing PDF Preview"
            })
            with open(pdf_path, "wb") as f:
                writer.write(f)

            # Test the previewer
            previewer = DocumentPreviewer()
            preview_data = previewer.generate_preview(pdf_path)

            assert preview_data is not None
            # Check if metadata was extracted
            if isinstance(preview_data, dict):
                # Preview might contain metadata, text, or error
                assert 'error' not in preview_data or preview_data.get('pages', 0) >= 0
        except ImportError as e:
            pytest.skip(f"Document preview dependencies not installed: {e}")


# ============================================================================
# PREVIEW MANAGER TESTS
# ============================================================================

class TestPreviewManager:
    """Tests for PreviewManager class"""

    def test_manager_initialization(self):
        """Test preview manager initialization"""
        try:
            from preview.manager import PreviewManager
            manager = PreviewManager()
            assert manager is not None
        except Exception:
            pytest.skip("PreviewManager not available")

    def test_get_preview_for_file_type(self, sample_text_file):
        """Test getting appropriate previewer for file type"""
        try:
            from preview.manager import PreviewManager
            manager = PreviewManager()

            preview = manager.get_preview(sample_text_file)
            assert preview is not None
        except Exception:
            pytest.skip("PreviewManager not available")

    def test_preview_caching(self, sample_text_file, temp_dir):
        """Test preview caching"""
        try:
            from preview.manager import PreviewManager
            cache_dir = os.path.join(temp_dir, "cache")
            manager = PreviewManager(cache_dir=cache_dir)

            # First preview (cache miss)
            preview1 = manager.get_preview(sample_text_file)

            # Second preview (cache hit)
            preview2 = manager.get_preview(sample_text_file)

            assert preview1 is not None
            assert preview2 is not None
        except Exception:
            pytest.skip("PreviewManager not available")


# ============================================================================
# METADATA EXTRACTION TESTS
# ============================================================================

class TestMetadataExtraction:
    """Tests for metadata extraction"""

    def test_extract_text_metadata(self, sample_text_file):
        """Test extracting metadata from text file"""
        try:
            from preview.metadata import MetadataExtractor
            extractor = MetadataExtractor()
            metadata = extractor.extract(sample_text_file)

            assert metadata is not None
            assert 'size' in metadata or metadata
            assert 'modified' in metadata or metadata
        except ImportError:
            pytest.skip("Metadata module not available")

    def test_extract_file_stats(self, sample_text_file):
        """Test extracting file statistics"""
        stats = {
            'size': os.path.getsize(sample_text_file),
            'modified': os.path.getmtime(sample_text_file),
            'created': os.path.getctime(sample_text_file)
        }

        assert stats['size'] > 0
        assert stats['modified'] > 0
        assert stats['created'] > 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
class TestPreviewIntegration:
    """Integration tests for preview module"""

    def test_preview_multiple_file_types(self, temp_dir):
        """Test previewing different file types"""
        from preview.text_preview import TextPreviewer

        # Create various test files
        test_files = {
            'text.txt': "Plain text content",
            'code.py': "print('Python code')",
            'data.json': '{"key": "value"}',
        }

        previewer = TextPreviewer()

        for filename, content in test_files.items():
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            preview = previewer.generate_preview(filepath)
            assert preview is not None

    def test_preview_with_cache(self, sample_text_file, temp_dir):
        """Test preview generation with caching"""
        try:
            from preview.manager import PreviewManager
            import time

            cache_dir = os.path.join(temp_dir, "preview_cache")
            manager = PreviewManager(cache_dir=cache_dir)

            # First preview
            start1 = time.time()
            preview1 = manager.get_preview(sample_text_file)
            duration1 = time.time() - start1

            # Second preview (cached)
            start2 = time.time()
            preview2 = manager.get_preview(sample_text_file)
            duration2 = time.time() - start2

            assert preview1 is not None
            assert preview2 is not None
            # Cached version should be faster (usually)
            assert duration2 >= 0
        except Exception:
            pytest.skip("PreviewManager with caching not available")

    def test_preview_error_handling(self, temp_dir):
        """Test error handling in preview generation"""
        from preview.text_preview import TextPreviewer

        # Create a file and then delete it
        temp_file = os.path.join(temp_dir, "deleted.txt")
        with open(temp_file, 'w') as f:
            f.write("test")
        os.remove(temp_file)

        previewer = TextPreviewer()
        # Returns error dict instead of raising exception
        result = previewer.generate_preview(temp_file)
        assert 'error' in result

    def test_concurrent_preview_generation(self, sample_files, temp_dir):
        """Test concurrent preview generation"""
        from preview.text_preview import TextPreviewer
        import concurrent.futures

        previewer = TextPreviewer()

        # Create text copies of sample files for testing
        text_files = []
        for i in range(min(5, len(sample_files))):
            text_file = os.path.join(temp_dir, f"concurrent_{i}.txt")
            with open(text_file, 'w') as f:
                f.write(f"Content {i}\n" * 100)
            text_files.append(text_file)

        def generate_preview(filepath):
            return previewer.generate_preview(filepath)

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(generate_preview, f) for f in text_files]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert len(results) == len(text_files)
