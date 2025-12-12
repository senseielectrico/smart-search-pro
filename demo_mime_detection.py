"""
MIME Detection Demo - Interactive demonstration of MIME detection features.

Usage:
    python demo_mime_detection.py
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from search.mime_detector import get_mime_detector
from search.mime_database import get_mime_database
from search.mime_filter import MimeFilter, MimeFilterCriteria, scan_files_mime_types
from tools.file_identifier import FileIdentifier


def print_header(title):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def demo_basic_detection():
    """Demonstrate basic MIME detection."""
    print_header("Demo 1: Basic MIME Detection")

    detector = get_mime_detector()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create sample files
        files = {
            "photo.jpg": b"\xFF\xD8\xFF\xE0" + b"\x00" * 100,  # JPEG
            "document.pdf": b"%PDF-1.4\n" + b"\x00" * 100,  # PDF
            "archive.zip": b"\x50\x4B\x03\x04" + b"\x00" * 100,  # ZIP
            "music.mp3": b"\xFF\xFB" + b"\x00" * 100,  # MP3
            "image.png": b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A" + b"\x00" * 100,  # PNG
        }

        print("Creating test files and detecting MIME types...\n")

        for filename, content in files.items():
            file_path = tmpdir / filename
            file_path.write_bytes(content)

            result = detector.detect(str(file_path))

            print(f"File: {filename}")
            print(f"  MIME Type: {result.mime_type}")
            print(f"  Description: {result.description}")
            print(f"  Confidence: {result.detection_confidence:.1%}")
            print(f"  Method: {result.detected_by}")
            print()


def demo_disguised_files():
    """Demonstrate detection of disguised files."""
    print_header("Demo 2: Disguised File Detection")

    detector = get_mime_detector()
    mime_filter = MimeFilter()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        print("Creating disguised executable (exe renamed to .jpg)...\n")

        # Create disguised executable
        disguised = tmpdir / "vacation_photo.jpg"
        disguised.write_bytes(b"\x4D\x5A" + b"\x00" * 100)  # Windows EXE header

        result = detector.detect(str(disguised))
        file_info = mime_filter.get_file_info(str(disguised))

        print(f"File: {disguised.name}")
        print(f"  Detected MIME: {result.mime_type}")
        print(f"  Expected Extension: .exe")
        print(f"  Current Extension: .jpg")
        print(f"  Extension Mismatch: {result.extension_mismatch}")
        print(f"  Is Dangerous: {file_info['is_dangerous']}")
        print(f"  Category: {file_info['category']}")
        print()

        print("WARNING: This file is a Windows executable disguised as an image!")
        print("This is a common malware technique.\n")


def demo_batch_scanning():
    """Demonstrate batch MIME scanning."""
    print_header("Demo 3: Batch MIME Scanning")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        print("Creating 20 mixed files...\n")

        # Create mixed files
        file_types = [
            ("jpg", b"\xFF\xD8\xFF\xE0"),
            ("png", b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"),
            ("pdf", b"%PDF-1.4\n"),
            ("zip", b"\x50\x4B\x03\x04"),
            ("mp3", b"\xFF\xFB"),
        ]

        files = []
        for i in range(20):
            ext, header = file_types[i % len(file_types)]
            file_path = tmpdir / f"file_{i:02d}.{ext}"
            file_path.write_bytes(header + b"\x00" * 100)
            files.append(str(file_path))

        # Scan files
        result = scan_files_mime_types(files, max_workers=4)

        print(f"Scanned {result.files_scanned} files\n")

        print("MIME Type Distribution:")
        for mime_type, count in sorted(result.mime_types.items()):
            print(f"  {mime_type}: {count} files")

        print("\nCategory Distribution:")
        for category, count in sorted(result.categories.items()):
            print(f"  {category}: {count} files")


def demo_filter_criteria():
    """Demonstrate filter criteria."""
    print_header("Demo 4: MIME Filter Criteria")

    mime_filter = MimeFilter()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create various files
        files = []

        # Images
        for i in range(5):
            f = tmpdir / f"photo_{i}.jpg"
            f.write_bytes(b"\xFF\xD8\xFF\xE0" + b"\x00" * 100)
            files.append(str(f))

        # Documents
        for i in range(3):
            f = tmpdir / f"document_{i}.pdf"
            f.write_bytes(b"%PDF-1.4\n" + b"\x00" * 100)
            files.append(str(f))

        # Disguised executable
        f = tmpdir / "setup.pdf"
        f.write_bytes(b"\x4D\x5A" + b"\x00" * 100)  # EXE
        files.append(str(f))

        print("Created 9 files (5 images, 3 PDFs, 1 disguised exe)\n")

        # Test different filters
        filters = [
            ("All images", MimeFilterCriteria(mime_patterns=["image/*"], categories=set())),
            ("All documents", MimeFilterCriteria(mime_patterns=["application/pdf"], categories=set())),
            ("Safe files only", MimeFilterCriteria(mime_patterns=[], categories=set(), exclude_dangerous=True)),
            ("Verified only", MimeFilterCriteria(mime_patterns=[], categories=set(), exclude_mismatched=True)),
        ]

        for name, criteria in filters:
            matching = mime_filter.filter_results(files, criteria)
            print(f"{name}: {len(matching)} files")


def demo_file_identifier():
    """Demonstrate comprehensive file identification."""
    print_header("Demo 5: Comprehensive File Identification")

    identifier = FileIdentifier()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        print("Creating suspicious file...\n")

        # Create suspicious file
        suspicious = tmpdir / "important_document.docx"
        suspicious.write_bytes(b"\x4D\x5A" + b"\x00" * 500)  # EXE disguised as DOCX

        report = identifier.identify(str(suspicious), deep_scan=False)

        identifier.print_report(report)


def demo_mime_database():
    """Demonstrate MIME database."""
    print_header("Demo 6: MIME Database")

    mime_db = get_mime_database()

    print("MIME Database Statistics:\n")

    print(f"Total known extensions: {len(mime_db.get_all_extensions())}")
    print(f"Total known MIME types: {len(mime_db.get_all_mime_types())}")
    print()

    print("Sample extensions and their MIME types:\n")

    sample_exts = ["jpg", "png", "pdf", "zip", "mp3", "mp4", "docx", "exe"]
    for ext in sample_exts:
        mime_type = mime_db.get_mime_by_extension(ext)
        description = mime_db.get_description(mime_type) if mime_type else "Unknown"
        print(f"  .{ext:8s} -> {mime_type or 'unknown':35s} ({description})")


def demo_query_syntax():
    """Demonstrate query syntax."""
    print_header("Demo 7: Search Query Syntax")

    print("MIME filter query examples:\n")

    queries = [
        "vacation mime:image/*",
        "reports type:document",
        "*.exe safe:true",
        "photos mime:image/* verified:true",
        "type:video size:>100mb",
        "downloads mime:application/* safe:true",
    ]

    for query in queries:
        print(f"  {query}")
        print(f"    Filters by: ", end="")

        if "mime:" in query:
            print("MIME type pattern, ", end="")
        if "type:" in query:
            print("category, ", end="")
        if "safe:" in query:
            print("exclude dangerous, ", end="")
        if "verified:" in query:
            print("exclude mismatched, ", end="")
        if "size:" in query:
            print("file size, ", end="")

        print()
        print()


def interactive_demo():
    """Interactive demo menu."""
    while True:
        print("\n" + "=" * 70)
        print("MIME DETECTION - Interactive Demo")
        print("=" * 70)
        print("\nChoose a demo:")
        print("  1. Basic MIME Detection")
        print("  2. Disguised File Detection")
        print("  3. Batch MIME Scanning")
        print("  4. Filter Criteria")
        print("  5. Comprehensive File Identification")
        print("  6. MIME Database")
        print("  7. Search Query Syntax")
        print("  8. Run All Demos")
        print("  0. Exit")
        print()

        choice = input("Enter choice (0-8): ").strip()

        if choice == "0":
            print("\nGoodbye!")
            break
        elif choice == "1":
            demo_basic_detection()
        elif choice == "2":
            demo_disguised_files()
        elif choice == "3":
            demo_batch_scanning()
        elif choice == "4":
            demo_filter_criteria()
        elif choice == "5":
            demo_file_identifier()
        elif choice == "6":
            demo_mime_database()
        elif choice == "7":
            demo_query_syntax()
        elif choice == "8":
            demo_basic_detection()
            demo_disguised_files()
            demo_batch_scanning()
            demo_filter_criteria()
            demo_file_identifier()
            demo_mime_database()
            demo_query_syntax()
        else:
            print("\nInvalid choice. Please try again.")

        input("\nPress Enter to continue...")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Run specific demo
        demo_num = sys.argv[1]
        demos = {
            "1": demo_basic_detection,
            "2": demo_disguised_files,
            "3": demo_batch_scanning,
            "4": demo_filter_criteria,
            "5": demo_file_identifier,
            "6": demo_mime_database,
            "7": demo_query_syntax,
        }

        if demo_num in demos:
            demos[demo_num]()
        else:
            print(f"Unknown demo: {demo_num}")
            print("Valid demos: 1-7")
    else:
        # Interactive mode
        interactive_demo()


if __name__ == "__main__":
    main()
