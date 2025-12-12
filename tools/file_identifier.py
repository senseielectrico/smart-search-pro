"""
Comprehensive file identification tool.

Features:
- Combine multiple detection methods
- Magic bytes analysis
- Extension analysis
- Content analysis
- Confidence score
- Detailed file type report
- Suggest correct extension
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import hashlib

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from search.mime_detector import get_mime_detector, DetectionResult
from search.mime_database import get_mime_database, MimeCategory
from search.mime_filter import MimeFilter


@dataclass
class FileIdentificationReport:
    """Comprehensive file identification report."""

    # Basic info
    file_path: str
    file_name: str
    file_size: int

    # MIME detection
    detected_mime: str
    detected_category: str
    detected_description: str
    detection_confidence: float
    detection_method: str

    # Extension info
    current_extension: str
    expected_extensions: List[str]
    extension_correct: bool
    suggested_extension: str = ""

    # Security
    is_dangerous: bool = False
    is_suspicious: bool = False
    risk_level: str = "low"  # low, medium, high, critical
    risk_reasons: List[str] = None

    # File integrity
    file_hash: str = ""
    is_corrupted: bool = False

    # Additional metadata
    is_text: bool = False
    encoding: str = ""
    line_count: int = 0

    def __post_init__(self):
        if self.risk_reasons is None:
            self.risk_reasons = []


class FileIdentifier:
    """
    Comprehensive file identification tool.

    Combines:
    - Magic bytes detection
    - Extension analysis
    - Content analysis
    - Security assessment
    - File integrity check
    """

    def __init__(self):
        """Initialize file identifier."""
        self.detector = get_mime_detector()
        self.mime_db = get_mime_database()
        self.mime_filter = MimeFilter()

    def identify(self, file_path: str, deep_scan: bool = False) -> FileIdentificationReport:
        """
        Identify file and generate comprehensive report.

        Args:
            file_path: Path to file
            deep_scan: Perform deep content analysis

        Returns:
            FileIdentificationReport
        """
        path = Path(file_path)

        # Basic file info
        if not path.exists():
            return self._error_report(file_path, "File not found")

        if not path.is_file():
            return self._error_report(file_path, "Not a file")

        file_size = path.stat().st_size
        file_name = path.name
        current_ext = path.suffix.lstrip(".").lower()

        # MIME detection
        detection = self.detector.detect(file_path)
        category = self.mime_db.get_category(detection.mime_type)

        # Expected extensions
        expected_exts = self.mime_db.get_extensions_for_mime(detection.mime_type)
        extension_correct = current_ext in expected_exts if current_ext else True

        # Suggest correct extension
        suggested_ext = ""
        if not extension_correct and expected_exts:
            suggested_ext = expected_exts[0]  # First one is usually most common

        # Security assessment
        is_dangerous, is_suspicious, risk_level, risk_reasons = self._assess_security(
            file_path, detection
        )

        # File hash (optional, for integrity)
        file_hash = ""
        if deep_scan and file_size < 100 * 1024 * 1024:  # Only for files < 100MB
            file_hash = self._calculate_hash(file_path)

        # Content analysis
        is_text = False
        encoding = ""
        line_count = 0
        is_corrupted = False

        if deep_scan:
            is_text, encoding, line_count = self._analyze_text_content(file_path)
            is_corrupted = self._check_corruption(file_path, detection.mime_type)

        return FileIdentificationReport(
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            detected_mime=detection.mime_type,
            detected_category=category.value,
            detected_description=detection.description,
            detection_confidence=detection.confidence,
            detection_method=detection.detected_by,
            current_extension=current_ext,
            expected_extensions=expected_exts,
            extension_correct=extension_correct,
            suggested_extension=suggested_ext,
            is_dangerous=is_dangerous,
            is_suspicious=is_suspicious,
            risk_level=risk_level,
            risk_reasons=risk_reasons,
            file_hash=file_hash,
            is_corrupted=is_corrupted,
            is_text=is_text,
            encoding=encoding,
            line_count=line_count
        )

    def identify_batch(
        self,
        file_paths: List[str],
        deep_scan: bool = False,
        max_workers: int = 4
    ) -> Dict[str, FileIdentificationReport]:
        """
        Identify multiple files in parallel.

        Args:
            file_paths: List of file paths
            deep_scan: Perform deep content analysis
            max_workers: Maximum worker threads

        Returns:
            Dictionary mapping file paths to reports
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        reports = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {
                executor.submit(self.identify, path, deep_scan): path
                for path in file_paths
            }

            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    reports[path] = future.result()
                except Exception as e:
                    reports[path] = self._error_report(path, str(e))

        return reports

    def suggest_rename(self, file_path: str) -> Optional[str]:
        """
        Suggest correct filename based on detected MIME type.

        Args:
            file_path: Path to file

        Returns:
            Suggested new filename or None
        """
        report = self.identify(file_path)

        if report.extension_correct or not report.suggested_extension:
            return None

        path = Path(file_path)
        base_name = path.stem
        new_name = f"{base_name}.{report.suggested_extension}"

        return str(path.parent / new_name)

    def fix_extensions(
        self,
        directory: str,
        recursive: bool = False,
        dry_run: bool = True
    ) -> Dict[str, str]:
        """
        Fix file extensions in directory based on detected MIME types.

        Args:
            directory: Directory to scan
            recursive: Scan subdirectories
            dry_run: Don't actually rename, just report

        Returns:
            Dictionary mapping old paths to new paths
        """
        renames = {}
        path = Path(directory)

        # Get all files
        if recursive:
            files = list(path.rglob("*"))
        else:
            files = list(path.glob("*"))

        files = [f for f in files if f.is_file()]

        # Identify each file
        for file_path in files:
            new_path = self.suggest_rename(str(file_path))
            if new_path:
                renames[str(file_path)] = new_path

                # Actually rename if not dry run
                if not dry_run:
                    try:
                        os.rename(str(file_path), new_path)
                    except OSError:
                        pass  # Skip if rename fails

        return renames

    def _assess_security(
        self,
        file_path: str,
        detection: DetectionResult
    ) -> Tuple[bool, bool, str, List[str]]:
        """
        Assess security risk of file.

        Returns:
            Tuple of (is_dangerous, is_suspicious, risk_level, reasons)
        """
        reasons = []
        is_dangerous = False
        is_suspicious = False
        risk_level = "low"

        # Check if MIME type is dangerous
        dangerous_types = {
            "application/x-msdownload": "Executable file",
            "application/x-executable": "Linux executable",
            "application/x-bat": "Batch script",
            "application/x-sh": "Shell script",
            "application/java-vm": "Java class file",
            "application/x-mach-binary": "macOS executable",
        }

        if detection.mime_type in dangerous_types:
            is_dangerous = True
            risk_level = "high"
            reasons.append(dangerous_types[detection.mime_type])

        # Check for extension mismatch
        if detection.extension_mismatch:
            is_suspicious = True
            if risk_level == "low":
                risk_level = "medium"
            reasons.append("Extension doesn't match detected type")

        # Check for disguised executables
        path = Path(file_path)
        ext = path.suffix.lstrip(".").lower()

        if detection.mime_type in dangerous_types and ext in ["jpg", "png", "pdf", "txt"]:
            is_suspicious = True
            risk_level = "critical"
            reasons.append("Executable disguised as safe file type")

        # Check for double extensions
        if ext and "." in path.stem:
            is_suspicious = True
            if risk_level == "low":
                risk_level = "medium"
            reasons.append("Suspicious double extension")

        # Check for hidden extension
        if path.name.count(".") > 1:
            parts = path.name.split(".")
            if len(parts) > 2 and parts[-2] in ["exe", "bat", "cmd", "scr"]:
                is_suspicious = True
                risk_level = "critical"
                reasons.append("Hidden executable extension")

        return is_dangerous, is_suspicious, risk_level, reasons

    def _calculate_hash(self, file_path: str, algorithm: str = "sha256") -> str:
        """Calculate file hash."""
        try:
            hash_obj = hashlib.new(algorithm)

            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_obj.update(chunk)

            return hash_obj.hexdigest()
        except Exception:
            return ""

    def _analyze_text_content(self, file_path: str) -> Tuple[bool, str, int]:
        """
        Analyze text content.

        Returns:
            Tuple of (is_text, encoding, line_count)
        """
        encodings = ["utf-8", "latin-1", "cp1252", "ascii"]

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    lines = f.readlines()
                    return True, encoding, len(lines)
            except (UnicodeDecodeError, UnicodeError):
                continue

        return False, "", 0

    def _check_corruption(self, file_path: str, mime_type: str) -> bool:
        """Check if file appears to be corrupted."""
        try:
            # Check if file is readable
            with open(file_path, "rb") as f:
                header = f.read(512)

            if not header:
                return True

            # For images, try to verify with PIL
            if mime_type.startswith("image/"):
                try:
                    from PIL import Image
                    img = Image.open(file_path)
                    img.verify()
                    return False
                except Exception:
                    return True

            # For PDFs, check for valid header
            if mime_type == "application/pdf":
                if not header.startswith(b"%PDF"):
                    return True

            # For ZIP-based formats, check ZIP signature
            if mime_type.startswith("application/zip") or \
               "openxmlformats" in mime_type:
                if not header.startswith(b"PK\x03\x04"):
                    return True

            return False

        except Exception:
            return True

    def _error_report(self, file_path: str, error: str) -> FileIdentificationReport:
        """Create error report."""
        return FileIdentificationReport(
            file_path=file_path,
            file_name=Path(file_path).name if file_path else "unknown",
            file_size=0,
            detected_mime="application/octet-stream",
            detected_category="unknown",
            detected_description=f"Error: {error}",
            detection_confidence=0.0,
            detection_method="error",
            current_extension="",
            expected_extensions=[],
            extension_correct=False,
            is_dangerous=False,
            is_suspicious=False,
            risk_level="unknown",
            risk_reasons=[error]
        )

    def print_report(self, report: FileIdentificationReport):
        """Print human-readable report."""
        print("=" * 70)
        print(f"FILE IDENTIFICATION REPORT")
        print("=" * 70)
        print(f"File: {report.file_name}")
        print(f"Path: {report.file_path}")
        print(f"Size: {self._format_size(report.file_size)}")
        print()

        print("MIME Type Detection:")
        print(f"  Type: {report.detected_mime}")
        print(f"  Category: {report.detected_category}")
        print(f"  Description: {report.detected_description}")
        print(f"  Confidence: {report.detection_confidence:.1%}")
        print(f"  Method: {report.detection_method}")
        print()

        print("Extension Analysis:")
        print(f"  Current: .{report.current_extension}" if report.current_extension else "  Current: (none)")
        print(f"  Expected: {', '.join('.' + e for e in report.expected_extensions)}")
        print(f"  Status: {'✓ Correct' if report.extension_correct else '✗ Incorrect'}")
        if report.suggested_extension:
            print(f"  Suggested: .{report.suggested_extension}")
        print()

        print("Security Assessment:")
        print(f"  Risk Level: {report.risk_level.upper()}")
        print(f"  Dangerous: {'Yes' if report.is_dangerous else 'No'}")
        print(f"  Suspicious: {'Yes' if report.is_suspicious else 'No'}")
        if report.risk_reasons:
            print("  Reasons:")
            for reason in report.risk_reasons:
                print(f"    - {reason}")
        print()

        if report.file_hash:
            print(f"File Hash (SHA-256):")
            print(f"  {report.file_hash}")
            print()

        if report.is_text:
            print("Text Content:")
            print(f"  Encoding: {report.encoding}")
            print(f"  Lines: {report.line_count:,}")
            print()

        if report.is_corrupted:
            print("WARNING: File may be corrupted!")
            print()

        print("=" * 70)

    def _format_size(self, size: int) -> str:
        """Format file size."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"


def main():
    """Command-line interface for file identifier."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Comprehensive file identification tool"
    )
    parser.add_argument(
        "file",
        help="File to identify"
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help="Perform deep content analysis"
    )
    parser.add_argument(
        "--suggest-rename",
        action="store_true",
        help="Suggest correct filename"
    )
    parser.add_argument(
        "--hash",
        action="store_true",
        help="Calculate file hash"
    )

    args = parser.parse_args()

    identifier = FileIdentifier()

    if args.suggest_rename:
        new_name = identifier.suggest_rename(args.file)
        if new_name:
            print(f"Suggested rename: {new_name}")
        else:
            print("Extension is correct, no rename needed")
    else:
        report = identifier.identify(args.file, deep_scan=args.deep or args.hash)
        identifier.print_report(report)


if __name__ == "__main__":
    main()
