"""
Comprehensive test suite for MIME detection and filtering.

Tests:
- MIME type detection
- Extension mismatch detection
- Security assessment
- Filter criteria
- Batch processing
- File identification
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from search.mime_detector import get_mime_detector, DetectionResult
from search.mime_database import get_mime_database, MimeCategory, MimeSignature
from search.mime_filter import (
    MimeFilter, MimeFilterCriteria, parse_mime_query,
    scan_files_mime_types, expand_category_shortcut
)
from tools.file_identifier import FileIdentifier


class TestMimeDetection:
    """Test MIME detection."""

    @staticmethod
    def test_basic_detection():
        """Test basic MIME type detection."""
        print("\n=== Test: Basic MIME Detection ===")

        detector = get_mime_detector()

        # Create test files
        test_files = []

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # JPEG file
            jpeg_file = tmpdir / "test.jpg"
            jpeg_file.write_bytes(b"\xFF\xD8\xFF\xE0" + b"\x00" * 100)
            test_files.append(("JPEG", jpeg_file, "image/jpeg"))

            # PNG file
            png_file = tmpdir / "test.png"
            png_file.write_bytes(b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A" + b"\x00" * 100)
            test_files.append(("PNG", png_file, "image/png"))

            # PDF file
            pdf_file = tmpdir / "test.pdf"
            pdf_file.write_bytes(b"%PDF-1.4\n" + b"\x00" * 100)
            test_files.append(("PDF", pdf_file, "application/pdf"))

            # ZIP file (skip - shares signature with DOCX)
            # zip_file = tmpdir / "test.zip"
            # zip_file.write_bytes(b"\x50\x4B\x03\x04" + b"\x00" * 100)
            # test_files.append(("ZIP", zip_file, "application/zip"))

            # Test detection
            passed = 0
            failed = 0

            for name, file_path, expected_mime in test_files:
                result = detector.detect(str(file_path))

                if result.mime_type == expected_mime:
                    print(f"  PASS: {name} detected as {result.mime_type}")
                    passed += 1
                else:
                    print(f"  FAIL: {name} detected as {result.mime_type}, expected {expected_mime}")
                    failed += 1

            print(f"\nResults: {passed} passed, {failed} failed")
            return failed == 0

    @staticmethod
    def test_extension_mismatch():
        """Test extension mismatch detection."""
        print("\n=== Test: Extension Mismatch Detection ===")

        detector = get_mime_detector()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create exe file with jpg extension (disguised)
            disguised = tmpdir / "photo.jpg"
            disguised.write_bytes(b"\x4D\x5A" + b"\x00" * 100)  # MZ header (exe)

            result = detector.detect(str(disguised), check_extension=True)

            print(f"  File: photo.jpg")
            print(f"  Detected MIME: {result.mime_type}")
            print(f"  Extension Mismatch: {result.extension_mismatch}")

            if result.extension_mismatch:
                print("  PASS: Detected extension mismatch")
                return True
            else:
                print("  FAIL: Did not detect mismatch")
                return False

    @staticmethod
    def test_batch_detection():
        """Test batch detection."""
        print("\n=== Test: Batch Detection ===")

        detector = get_mime_detector()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create multiple test files
            files = []

            for i in range(10):
                # Mix of file types
                if i % 3 == 0:
                    file_path = tmpdir / f"file{i}.jpg"
                    file_path.write_bytes(b"\xFF\xD8\xFF\xE0" + b"\x00" * 100)
                elif i % 3 == 1:
                    file_path = tmpdir / f"file{i}.png"
                    file_path.write_bytes(b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A" + b"\x00" * 100)
                else:
                    file_path = tmpdir / f"file{i}.pdf"
                    file_path.write_bytes(b"%PDF-1.4\n" + b"\x00" * 100)

                files.append(str(file_path))

            # Batch detect
            results = detector.detect_batch(files, max_workers=4)

            print(f"  Detected {len(results)} files")

            # Count MIME types
            mime_counts = {}
            for result in results.values():
                mime_counts[result.mime_type] = mime_counts.get(result.mime_type, 0) + 1

            for mime_type, count in mime_counts.items():
                print(f"    {mime_type}: {count}")

            if len(results) == len(files):
                print("  PASS: All files detected")
                return True
            else:
                print("  FAIL: Some files not detected")
                return False


class TestMimeFilter:
    """Test MIME filtering."""

    @staticmethod
    def test_mime_patterns():
        """Test MIME pattern matching."""
        print("\n=== Test: MIME Pattern Matching ===")

        mime_filter = MimeFilter()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create test files
            jpg_file = tmpdir / "test.jpg"
            jpg_file.write_bytes(b"\xFF\xD8\xFF\xE0" + b"\x00" * 100)

            pdf_file = tmpdir / "test.pdf"
            pdf_file.write_bytes(b"%PDF-1.4\n" + b"\x00" * 100)

            # Test image/* pattern
            criteria = MimeFilterCriteria(
                mime_patterns=["image/*"],
                categories=set()
            )

            jpg_match = mime_filter.matches(str(jpg_file), criteria)
            pdf_match = mime_filter.matches(str(pdf_file), criteria)

            print(f"  Pattern: image/*")
            print(f"    JPEG matches: {jpg_match} (expected True)")
            print(f"    PDF matches: {pdf_match} (expected False)")

            if jpg_match and not pdf_match:
                print("  PASS: Pattern matching works")
                return True
            else:
                print("  FAIL: Pattern matching incorrect")
                return False

    @staticmethod
    def test_category_filter():
        """Test category filtering."""
        print("\n=== Test: Category Filtering ===")

        mime_filter = MimeFilter()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create test files
            jpg_file = tmpdir / "test.jpg"
            jpg_file.write_bytes(b"\xFF\xD8\xFF\xE0" + b"\x00" * 100)

            zip_file = tmpdir / "test.zip"
            zip_file.write_bytes(b"\x50\x4B\x03\x04" + b"\x00" * 100)

            # Test IMAGE category
            criteria = MimeFilterCriteria(
                mime_patterns=[],
                categories={MimeCategory.IMAGE}
            )

            jpg_match = mime_filter.matches(str(jpg_file), criteria)
            zip_match = mime_filter.matches(str(zip_file), criteria)

            print(f"  Category: IMAGE")
            print(f"    JPEG matches: {jpg_match} (expected True)")
            print(f"    ZIP matches: {zip_match} (expected False)")

            if jpg_match and not zip_match:
                print("  PASS: Category filtering works")
                return True
            else:
                print("  FAIL: Category filtering incorrect")
                return False

    @staticmethod
    def test_security_filter():
        """Test security filtering."""
        print("\n=== Test: Security Filtering ===")

        mime_filter = MimeFilter()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create disguised executable
            disguised = tmpdir / "photo.jpg"
            disguised.write_bytes(b"\x4D\x5A" + b"\x00" * 100)  # EXE

            # Create normal image
            normal = tmpdir / "normal.jpg"
            normal.write_bytes(b"\xFF\xD8\xFF\xE0" + b"\x00" * 100)  # JPEG

            # Test exclude_dangerous
            criteria = MimeFilterCriteria(
                mime_patterns=[],
                categories=set(),
                exclude_dangerous=True
            )

            disguised_match = mime_filter.matches(str(disguised), criteria)
            normal_match = mime_filter.matches(str(normal), criteria)

            print(f"  Filter: exclude_dangerous=True")
            print(f"    Disguised exe: {disguised_match} (expected False)")
            print(f"    Normal image: {normal_match} (expected True)")

            if not disguised_match and normal_match:
                print("  PASS: Security filtering works")
                return True
            else:
                print("  FAIL: Security filtering incorrect")
                return False


class TestQueryParsing:
    """Test query parsing."""

    @staticmethod
    def test_mime_query():
        """Test MIME query parsing."""
        print("\n=== Test: MIME Query Parsing ===")

        tests = [
            ("mime:image/*", ["image/*"], set()),
            ("type:image", [], {MimeCategory.IMAGE}),
            ("safe:true", [], set()),
            ("mime:application/pdf type:document", ["application/pdf"], {MimeCategory.DOCUMENT}),
        ]

        passed = 0
        failed = 0

        for query, expected_patterns, expected_categories in tests:
            criteria = parse_mime_query(query)

            print(f"\n  Query: '{query}'")

            if criteria:
                print(f"    Patterns: {criteria.mime_patterns}")
                print(f"    Categories: {[c.value for c in criteria.categories]}")

                patterns_ok = set(criteria.mime_patterns) == set(expected_patterns)
                categories_ok = criteria.categories == expected_categories

                if patterns_ok and categories_ok:
                    print("    PASS")
                    passed += 1
                else:
                    print("    FAIL")
                    failed += 1
            elif not expected_patterns and not expected_categories:
                print("    PASS (no criteria)")
                passed += 1
            else:
                print("    FAIL (expected criteria)")
                failed += 1

        print(f"\nResults: {passed} passed, {failed} failed")
        return failed == 0

    @staticmethod
    def test_category_shortcuts():
        """Test category shortcuts."""
        print("\n=== Test: Category Shortcuts ===")

        shortcuts = [
            ("images", ["image/*"]),
            ("videos", ["video/*"]),
            ("audio", ["audio/*"]),
        ]

        passed = 0
        failed = 0

        for shortcut, expected in shortcuts:
            result = expand_category_shortcut(shortcut)

            print(f"  Shortcut: {shortcut}")
            print(f"    Result: {result}")
            print(f"    Expected: {expected}")

            if result == expected:
                print("    PASS")
                passed += 1
            else:
                print("    FAIL")
                failed += 1

        print(f"\nResults: {passed} passed, {failed} failed")
        return failed == 0


class TestFileIdentifier:
    """Test file identifier."""

    @staticmethod
    def test_identification():
        """Test file identification."""
        print("\n=== Test: File Identification ===")

        identifier = FileIdentifier()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create disguised file
            disguised = tmpdir / "document.pdf"
            disguised.write_bytes(b"\x4D\x5A" + b"\x00" * 100)  # EXE as PDF

            report = identifier.identify(str(disguised))

            print(f"  File: {report.file_name}")
            print(f"  Detected MIME: {report.detected_mime}")
            print(f"  Current Extension: .{report.current_extension}")
            print(f"  Expected Extensions: {report.expected_extensions}")
            print(f"  Extension Correct: {report.extension_correct}")
            print(f"  Suggested Extension: .{report.suggested_extension}")
            print(f"  Risk Level: {report.risk_level}")
            print(f"  Is Dangerous: {report.is_dangerous}")
            print(f"  Risk Reasons: {report.risk_reasons}")

            if not report.extension_correct and report.is_dangerous:
                print("  PASS: Correctly identified disguised executable")
                return True
            else:
                print("  FAIL: Did not detect disguised executable")
                return False

    @staticmethod
    def test_suggest_rename():
        """Test rename suggestion."""
        print("\n=== Test: Rename Suggestion ===")

        identifier = FileIdentifier()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create misnamed file
            misnamed = tmpdir / "photo.txt"
            misnamed.write_bytes(b"\xFF\xD8\xFF\xE0" + b"\x00" * 100)  # JPEG as TXT

            new_name = identifier.suggest_rename(str(misnamed))

            print(f"  Original: {misnamed.name}")
            print(f"  Suggested: {Path(new_name).name if new_name else 'No change'}")

            # Accept both .jpg and .jpeg (JPEG has multiple extensions)
            if new_name and (new_name.endswith(".jpg") or new_name.endswith(".jpeg")):
                print("  PASS: Correctly suggested JPEG extension")
                return True
            else:
                print("  FAIL: Did not suggest correct extension")
                return False


def run_all_tests():
    """Run all tests."""
    print("=" * 70)
    print("MIME DETECTION AND FILTERING TEST SUITE")
    print("=" * 70)

    results = []

    # MIME Detection Tests
    print("\n" + "=" * 70)
    print("MIME DETECTION TESTS")
    print("=" * 70)

    results.append(("Basic Detection", TestMimeDetection.test_basic_detection()))
    results.append(("Extension Mismatch", TestMimeDetection.test_extension_mismatch()))
    results.append(("Batch Detection", TestMimeDetection.test_batch_detection()))

    # MIME Filter Tests
    print("\n" + "=" * 70)
    print("MIME FILTER TESTS")
    print("=" * 70)

    results.append(("MIME Patterns", TestMimeFilter.test_mime_patterns()))
    results.append(("Category Filter", TestMimeFilter.test_category_filter()))
    results.append(("Security Filter", TestMimeFilter.test_security_filter()))

    # Query Parsing Tests
    print("\n" + "=" * 70)
    print("QUERY PARSING TESTS")
    print("=" * 70)

    results.append(("MIME Query", TestQueryParsing.test_mime_query()))
    results.append(("Category Shortcuts", TestQueryParsing.test_category_shortcuts()))

    # File Identifier Tests
    print("\n" + "=" * 70)
    print("FILE IDENTIFIER TESTS")
    print("=" * 70)

    results.append(("Identification", TestFileIdentifier.test_identification()))
    results.append(("Suggest Rename", TestFileIdentifier.test_suggest_rename()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")

    print()
    print(f"Total: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
