"""
MIME type detection engine using magic bytes (file signatures).

Features:
- Detect file type by magic bytes
- Fast detection (read only first 8KB)
- Fallback to python-magic if available
- Cache detection results
- Handle corrupted files gracefully
- Support 500+ file signatures
"""

import os
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
import threading

from .mime_database import MimeDatabase, get_mime_database


@dataclass
class DetectionResult:
    """MIME detection result."""
    mime_type: str
    confidence: float  # 0.0 to 1.0
    detected_by: str  # "magic", "extension", "python-magic", "content"
    description: str = ""
    extension_mismatch: bool = False


class MimeDetector:
    """
    Fast MIME type detector using magic bytes.

    Features:
    - Magic byte detection (primary)
    - python-magic fallback
    - Extension-based fallback
    - Result caching
    - Thread-safe
    """

    # Read first 8KB for detection
    MAGIC_BYTES_SIZE = 8192

    def __init__(self, use_cache: bool = True):
        """
        Initialize MIME detector.

        Args:
            use_cache: Enable detection result caching
        """
        self.mime_db = get_mime_database()
        self.use_cache = use_cache
        self._cache: Dict[str, DetectionResult] = {}
        self._cache_lock = threading.Lock()

        # Try to import python-magic
        self.python_magic = None
        try:
            import magic
            self.python_magic = magic
        except ImportError:
            pass

    def detect(self, file_path: str, check_extension: bool = True) -> DetectionResult:
        """
        Detect MIME type of a file.

        Args:
            file_path: Path to file
            check_extension: Check for extension mismatch

        Returns:
            DetectionResult with MIME type and metadata
        """
        file_path = str(file_path)

        # Check cache
        if self.use_cache:
            with self._cache_lock:
                if file_path in self._cache:
                    return self._cache[file_path]

        result = self._detect_uncached(file_path, check_extension)

        # Cache result
        if self.use_cache:
            with self._cache_lock:
                self._cache[file_path] = result

        return result

    def _detect_uncached(self, file_path: str, check_extension: bool) -> DetectionResult:
        """Detect MIME type without cache."""
        path = Path(file_path)

        # Check if file exists and is readable
        if not path.exists():
            return DetectionResult(
                mime_type="application/octet-stream",
                confidence=0.0,
                detected_by="error",
                description="File not found"
            )

        if not path.is_file():
            return DetectionResult(
                mime_type="inode/directory",
                confidence=1.0,
                detected_by="filesystem",
                description="Directory"
            )

        # Get extension
        extension = path.suffix.lstrip(".").lower()
        extension_mime = self.mime_db.get_mime_by_extension(extension) if extension else None

        # Try magic bytes detection first
        try:
            magic_result = self._detect_by_magic(file_path)
            if magic_result:
                mime_type, confidence = magic_result

                # Check for extension mismatch
                extension_mismatch = False
                if check_extension and extension_mime:
                    # Allow some flexibility (e.g., jpg/jpeg, htm/html)
                    if not self._mime_types_compatible(mime_type, extension_mime):
                        extension_mismatch = True

                return DetectionResult(
                    mime_type=mime_type,
                    confidence=confidence,
                    detected_by="magic",
                    description=self.mime_db.get_description(mime_type),
                    extension_mismatch=extension_mismatch
                )
        except Exception:
            pass

        # Try python-magic if available
        if self.python_magic:
            try:
                magic_mime = self.python_magic.from_file(file_path, mime=True)
                if magic_mime:
                    return DetectionResult(
                        mime_type=magic_mime,
                        confidence=0.9,
                        detected_by="python-magic",
                        description=self.mime_db.get_description(magic_mime)
                    )
            except Exception:
                pass

        # Fall back to extension
        if extension_mime:
            return DetectionResult(
                mime_type=extension_mime,
                confidence=0.7,
                detected_by="extension",
                description=self.mime_db.get_description(extension_mime)
            )

        # Try content analysis for text files
        try:
            content_result = self._detect_by_content(file_path)
            if content_result:
                return DetectionResult(
                    mime_type=content_result,
                    confidence=0.6,
                    detected_by="content",
                    description=self.mime_db.get_description(content_result)
                )
        except Exception:
            pass

        # Unknown type
        return DetectionResult(
            mime_type="application/octet-stream",
            confidence=0.3,
            detected_by="default",
            description="Unknown binary file"
        )

    def _detect_by_magic(self, file_path: str) -> Optional[Tuple[str, float]]:
        """
        Detect MIME type by magic bytes.

        Returns:
            Tuple of (mime_type, confidence) or None
        """
        try:
            with open(file_path, "rb") as f:
                header = f.read(self.MAGIC_BYTES_SIZE)

            if not header:
                return None

            # Check each signature
            for signature in self.mime_db.get_signatures():
                if self._matches_signature(header, signature):
                    # Higher confidence for longer signatures
                    confidence = min(1.0, 0.85 + (len(signature.signature) / 100))
                    return (signature.mime_type, confidence)

            return None

        except (IOError, OSError):
            return None

    def _matches_signature(self, data: bytes, signature) -> bool:
        """Check if data matches a signature."""
        offset = signature.offset
        sig_bytes = signature.signature

        # Check if we have enough data
        if len(data) < offset + len(sig_bytes):
            return False

        # Extract relevant portion
        data_portion = data[offset:offset + len(sig_bytes)]

        # Apply mask if provided
        if signature.mask:
            data_portion = bytes(
                d & m for d, m in zip(data_portion, signature.mask)
            )
            sig_bytes = bytes(
                s & m for s, m in zip(sig_bytes, signature.mask)
            )

        return data_portion == sig_bytes

    def _detect_by_content(self, file_path: str) -> Optional[str]:
        """
        Detect MIME type by content analysis (for text files).

        Returns:
            MIME type or None
        """
        try:
            with open(file_path, "rb") as f:
                content = f.read(512)

            # Check if it's text
            if self._is_text(content):
                # Try to detect specific text formats
                text_content = content.decode("utf-8", errors="ignore")

                if text_content.strip().startswith("<!DOCTYPE html") or \
                   text_content.strip().startswith("<html"):
                    return "text/html"
                elif text_content.strip().startswith("<?xml"):
                    return "application/xml"
                elif text_content.strip().startswith("{") or \
                     text_content.strip().startswith("["):
                    try:
                        import json
                        json.loads(text_content.strip())
                        return "application/json"
                    except:
                        pass
                elif "#!/usr/bin/env python" in text_content or \
                     "#!/usr/bin/python" in text_content:
                    return "text/x-python"

                # Generic text
                return "text/plain"

            return None

        except Exception:
            return None

    def _is_text(self, data: bytes) -> bool:
        """Check if data appears to be text."""
        if not data:
            return False

        # Check for null bytes (binary indicator)
        if b"\x00" in data:
            return False

        # Try to decode as UTF-8
        try:
            data.decode("utf-8")
            return True
        except UnicodeDecodeError:
            pass

        # Check for common text characters
        text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
        non_text_count = sum(1 for byte in data if byte not in text_chars)

        # If more than 30% non-text characters, probably binary
        return non_text_count / len(data) < 0.3

    def _mime_types_compatible(self, mime1: str, mime2: str) -> bool:
        """Check if two MIME types are compatible."""
        if mime1 == mime2:
            return True

        # Handle wildcards
        if "*" in mime1 or "*" in mime2:
            category1 = mime1.split("/")[0]
            category2 = mime2.split("/")[0]
            return category1 == category2

        # Handle common aliases
        aliases = {
            ("image/jpeg", "image/jpg"),
            ("text/html", "application/xhtml+xml"),
            ("application/javascript", "text/javascript"),
        }

        pair = (mime1, mime2)
        reverse_pair = (mime2, mime1)

        return pair in aliases or reverse_pair in aliases

    def detect_batch(self, file_paths: list, max_workers: int = 4) -> Dict[str, DetectionResult]:
        """
        Detect MIME types for multiple files in parallel.

        Args:
            file_paths: List of file paths
            max_workers: Maximum worker threads

        Returns:
            Dictionary mapping file paths to DetectionResults
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {
                executor.submit(self.detect, path): path
                for path in file_paths
            }

            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    results[path] = future.result()
                except Exception:
                    results[path] = DetectionResult(
                        mime_type="application/octet-stream",
                        confidence=0.0,
                        detected_by="error",
                        description="Detection failed"
                    )

        return results

    def clear_cache(self):
        """Clear detection cache."""
        with self._cache_lock:
            self._cache.clear()

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        with self._cache_lock:
            return {
                "size": len(self._cache),
                "enabled": self.use_cache
            }


# Global instance
_detector = None


def get_mime_detector() -> MimeDetector:
    """Get global MIME detector instance."""
    global _detector
    if _detector is None:
        _detector = MimeDetector()
    return _detector


def detect_mime_type(file_path: str) -> str:
    """
    Convenience function to detect MIME type.

    Args:
        file_path: Path to file

    Returns:
        MIME type string
    """
    detector = get_mime_detector()
    result = detector.detect(file_path)
    return result.mime_type
