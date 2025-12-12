"""
MIME-based filtering for search results.

Features:
- Filter by actual MIME type (not extension)
- Query syntax: mime:image/*, type:video
- Category shortcuts
- Detect disguised files
- Flag potentially dangerous files
- Integration with search engine
"""

import re
from typing import List, Optional, Set
from dataclasses import dataclass

from .mime_detector import get_mime_detector, DetectionResult
from .mime_database import get_mime_database, MimeCategory


@dataclass
class MimeFilterCriteria:
    """MIME filter criteria."""
    mime_patterns: List[str]  # e.g., ["image/*", "application/pdf"]
    categories: Set[MimeCategory]
    exclude_mismatched: bool = False
    exclude_dangerous: bool = False
    min_confidence: float = 0.0


class MimeFilter:
    """
    MIME-based filter for search results.

    Features:
    - Filter by MIME type patterns
    - Filter by categories
    - Detect and flag suspicious files
    - Integration with query parser
    """

    # Dangerous MIME types
    DANGEROUS_MIME_TYPES = {
        "application/x-msdownload",  # .exe, .dll
        "application/x-executable",  # Linux executables
        "application/x-bat",  # Batch files
        "application/x-sh",  # Shell scripts
        "application/java-vm",  # Java class files
        "application/x-mach-binary",  # macOS executables
        "application/vnd.android.dex",  # Android DEX
    }

    # Suspicious extension changes
    SUSPICIOUS_DISGUISES = {
        ("application/x-msdownload", "jpg"),
        ("application/x-msdownload", "png"),
        ("application/x-msdownload", "pdf"),
        ("application/x-msdownload", "txt"),
        ("application/x-executable", "jpg"),
        ("application/x-executable", "png"),
    }

    def __init__(self):
        """Initialize MIME filter."""
        self.detector = get_mime_detector()
        self.mime_db = get_mime_database()

    def matches(self, file_path: str, criteria: MimeFilterCriteria) -> bool:
        """
        Check if file matches MIME filter criteria.

        Args:
            file_path: Path to file
            criteria: Filter criteria

        Returns:
            True if file matches criteria
        """
        # Detect MIME type
        detection = self.detector.detect(file_path)

        # Check confidence threshold
        if detection.confidence < criteria.min_confidence:
            return False

        # Check MIME patterns
        if criteria.mime_patterns:
            matches_pattern = False
            for pattern in criteria.mime_patterns:
                if self._matches_mime_pattern(detection.mime_type, pattern):
                    matches_pattern = True
                    break

            if not matches_pattern:
                return False

        # Check categories
        if criteria.categories:
            category = self.mime_db.get_category(detection.mime_type)
            if category not in criteria.categories:
                return False

        # Exclude mismatched extensions
        if criteria.exclude_mismatched and detection.extension_mismatch:
            return False

        # Exclude dangerous files
        if criteria.exclude_dangerous and self._is_dangerous(detection, file_path):
            return False

        return True

    def _matches_mime_pattern(self, mime_type: str, pattern: str) -> bool:
        """
        Check if MIME type matches pattern.

        Supports:
        - Exact match: image/png
        - Wildcard: image/*
        - Prefix: image
        """
        if pattern == "*" or pattern == "*/*":
            return True

        if "/" not in pattern:
            # Category match (e.g., "image")
            return mime_type.startswith(pattern + "/")

        if pattern.endswith("/*"):
            # Wildcard match (e.g., "image/*")
            category = pattern[:-2]
            return mime_type.startswith(category + "/")

        # Exact match
        return mime_type == pattern

    def _is_dangerous(self, detection: DetectionResult, file_path: str) -> bool:
        """Check if file is potentially dangerous."""
        # Check if MIME type is dangerous
        if detection.mime_type in self.DANGEROUS_MIME_TYPES:
            return True

        # Check for suspicious disguises
        if detection.extension_mismatch:
            from pathlib import Path
            ext = Path(file_path).suffix.lstrip(".").lower()
            pair = (detection.mime_type, ext)
            if pair in self.SUSPICIOUS_DISGUISES:
                return True

        return False

    def filter_results(self, file_paths: List[str], criteria: MimeFilterCriteria) -> List[str]:
        """
        Filter list of file paths by MIME criteria.

        Args:
            file_paths: List of file paths
            criteria: Filter criteria

        Returns:
            Filtered list of file paths
        """
        return [
            path for path in file_paths
            if self.matches(path, criteria)
        ]

    def get_file_info(self, file_path: str) -> dict:
        """
        Get detailed MIME information for a file.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with MIME information
        """
        detection = self.detector.detect(file_path)
        category = self.mime_db.get_category(detection.mime_type)

        from pathlib import Path
        path = Path(file_path)
        extension = path.suffix.lstrip(".").lower()
        extension_mime = self.mime_db.get_mime_by_extension(extension) if extension else None

        return {
            "mime_type": detection.mime_type,
            "category": category.value,
            "description": detection.description,
            "confidence": detection.confidence,
            "detected_by": detection.detected_by,
            "extension": extension,
            "extension_mime": extension_mime,
            "extension_mismatch": detection.extension_mismatch,
            "is_dangerous": self._is_dangerous(detection, file_path),
        }


def parse_mime_query(query: str) -> Optional[MimeFilterCriteria]:
    """
    Parse MIME filter from query string.

    Supports:
    - mime:image/*
    - mime:application/pdf
    - type:image
    - type:video,audio
    - safe:true (exclude dangerous)
    - verified:true (exclude mismatched)

    Args:
        query: Query string

    Returns:
        MimeFilterCriteria or None if no MIME filters found
    """
    mime_patterns = []
    categories = set()
    exclude_dangerous = False
    exclude_mismatched = False
    min_confidence = 0.0

    # Extract mime: patterns
    mime_matches = re.findall(r'mime:([^\s]+)', query, re.IGNORECASE)
    mime_patterns.extend(mime_matches)

    # Extract type: categories
    type_matches = re.findall(r'type:([^\s]+)', query, re.IGNORECASE)
    for type_match in type_matches:
        for type_name in type_match.split(","):
            type_name = type_name.strip().upper()
            try:
                category = MimeCategory[type_name]
                categories.add(category)
            except KeyError:
                # Try as MIME category
                mime_patterns.append(type_name.lower() + "/*")

    # Extract safe: flag
    if re.search(r'safe:true', query, re.IGNORECASE):
        exclude_dangerous = True

    # Extract verified: flag
    if re.search(r'verified:true', query, re.IGNORECASE):
        exclude_mismatched = True

    # Extract confidence: threshold
    confidence_match = re.search(r'confidence:(\d+(?:\.\d+)?)', query, re.IGNORECASE)
    if confidence_match:
        min_confidence = float(confidence_match.group(1))

    # Return None if no filters specified
    if not mime_patterns and not categories and not exclude_dangerous and not exclude_mismatched:
        return None

    return MimeFilterCriteria(
        mime_patterns=mime_patterns,
        categories=categories,
        exclude_mismatched=exclude_mismatched,
        exclude_dangerous=exclude_dangerous,
        min_confidence=min_confidence
    )


def get_category_shortcuts() -> dict:
    """Get mapping of category shortcuts to MIME patterns."""
    return {
        "images": "image/*",
        "videos": "video/*",
        "audio": "audio/*",
        "documents": [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.*",
        ],
        "archives": [
            "application/zip",
            "application/x-rar-compressed",
            "application/x-7z-compressed",
        ],
        "executables": "application/x-msdownload",
        "code": [
            "text/x-python",
            "application/javascript",
            "text/html",
            "application/xml",
        ],
    }


def expand_category_shortcut(shortcut: str) -> List[str]:
    """
    Expand category shortcut to MIME patterns.

    Args:
        shortcut: Category shortcut (e.g., "images")

    Returns:
        List of MIME patterns
    """
    shortcuts = get_category_shortcuts()
    patterns = shortcuts.get(shortcut.lower())

    if patterns is None:
        return []

    if isinstance(patterns, str):
        return [patterns]

    return patterns


class MimeScanResult:
    """Result of bulk MIME scanning."""

    def __init__(self):
        """Initialize scan result."""
        self.files_scanned = 0
        self.mime_types = {}  # mime_type -> count
        self.categories = {}  # category -> count
        self.mismatched = []  # files with extension mismatch
        self.dangerous = []  # potentially dangerous files
        self.errors = []  # files that couldn't be scanned


def scan_files_mime_types(file_paths: List[str], max_workers: int = 4) -> MimeScanResult:
    """
    Scan multiple files and collect MIME type statistics.

    Args:
        file_paths: List of file paths
        max_workers: Maximum worker threads

    Returns:
        MimeScanResult with statistics
    """
    detector = get_mime_detector()
    mime_db = get_mime_database()
    mime_filter = MimeFilter()

    result = MimeScanResult()

    # Batch detect
    detections = detector.detect_batch(file_paths, max_workers=max_workers)

    for path, detection in detections.items():
        result.files_scanned += 1

        # Count MIME types
        mime_type = detection.mime_type
        result.mime_types[mime_type] = result.mime_types.get(mime_type, 0) + 1

        # Count categories
        category = mime_db.get_category(mime_type)
        cat_name = category.value
        result.categories[cat_name] = result.categories.get(cat_name, 0) + 1

        # Track mismatches
        if detection.extension_mismatch:
            result.mismatched.append(path)

        # Track dangerous files
        if mime_filter._is_dangerous(detection, path):
            result.dangerous.append(path)

        # Track errors
        if detection.detected_by == "error":
            result.errors.append(path)

    return result
