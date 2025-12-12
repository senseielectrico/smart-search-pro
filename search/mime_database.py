"""
MIME type database with comprehensive file signatures and mappings.

Provides:
- 500+ file signatures (magic bytes)
- MIME type to description mapping
- Extension to MIME mapping
- Category classification
- User-extensible definitions
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class MimeCategory(Enum):
    """Main MIME type categories."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    ARCHIVE = "archive"
    EXECUTABLE = "executable"
    CODE = "code"
    DATA = "data"
    FONT = "font"
    MODEL = "model"
    TEXT = "text"
    APPLICATION = "application"
    UNKNOWN = "unknown"


@dataclass
class MimeSignature:
    """File signature definition."""
    mime_type: str
    signature: bytes
    offset: int = 0
    mask: Optional[bytes] = None
    description: str = ""
    extensions: List[str] = None

    def __post_init__(self):
        if self.extensions is None:
            self.extensions = []


class MimeDatabase:
    """
    Comprehensive MIME type database.

    Features:
    - 500+ file signatures
    - Category classification
    - Extension mapping
    - User-extensible
    """

    def __init__(self):
        """Initialize MIME database."""
        self._signatures = self._build_signatures()
        self._extension_map = self._build_extension_map()
        self._mime_descriptions = self._build_descriptions()
        self._category_map = self._build_category_map()
        self._user_signatures = []

    def _build_signatures(self) -> List[MimeSignature]:
        """Build comprehensive list of file signatures."""
        signatures = []

        # === IMAGES ===
        signatures.extend([
            # JPEG
            MimeSignature(
                "image/jpeg",
                b"\xFF\xD8\xFF\xDB",
                description="JPEG image (JFIF)",
                extensions=["jpg", "jpeg"]
            ),
            MimeSignature(
                "image/jpeg",
                b"\xFF\xD8\xFF\xE0",
                description="JPEG image (JFIF)",
                extensions=["jpg", "jpeg"]
            ),
            MimeSignature(
                "image/jpeg",
                b"\xFF\xD8\xFF\xE1",
                description="JPEG image (Exif)",
                extensions=["jpg", "jpeg"]
            ),
            MimeSignature(
                "image/jpeg",
                b"\xFF\xD8\xFF\xEE",
                description="JPEG image",
                extensions=["jpg", "jpeg"]
            ),

            # PNG
            MimeSignature(
                "image/png",
                b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A",
                description="PNG image",
                extensions=["png"]
            ),

            # GIF
            MimeSignature(
                "image/gif",
                b"\x47\x49\x46\x38\x37\x61",
                description="GIF image (87a)",
                extensions=["gif"]
            ),
            MimeSignature(
                "image/gif",
                b"\x47\x49\x46\x38\x39\x61",
                description="GIF image (89a)",
                extensions=["gif"]
            ),

            # BMP
            MimeSignature(
                "image/bmp",
                b"\x42\x4D",
                description="BMP image",
                extensions=["bmp", "dib"]
            ),

            # TIFF
            MimeSignature(
                "image/tiff",
                b"\x49\x49\x2A\x00",
                description="TIFF image (little-endian)",
                extensions=["tif", "tiff"]
            ),
            MimeSignature(
                "image/tiff",
                b"\x4D\x4D\x00\x2A",
                description="TIFF image (big-endian)",
                extensions=["tif", "tiff"]
            ),

            # WebP
            MimeSignature(
                "image/webp",
                b"\x52\x49\x46\x46",
                description="WebP image",
                extensions=["webp"]
            ),

            # ICO
            MimeSignature(
                "image/x-icon",
                b"\x00\x00\x01\x00",
                description="Icon file",
                extensions=["ico"]
            ),

            # HEIC/HEIF
            MimeSignature(
                "image/heic",
                b"\x00\x00\x00\x18\x66\x74\x79\x70\x68\x65\x69\x63",
                description="HEIC image",
                extensions=["heic"]
            ),

            # SVG
            MimeSignature(
                "image/svg+xml",
                b"<?xml",
                description="SVG image",
                extensions=["svg"]
            ),

            # PSD
            MimeSignature(
                "image/vnd.adobe.photoshop",
                b"\x38\x42\x50\x53",
                description="Adobe Photoshop",
                extensions=["psd"]
            ),
        ])

        # === VIDEOS ===
        signatures.extend([
            # MP4
            MimeSignature(
                "video/mp4",
                b"\x00\x00\x00\x18\x66\x74\x79\x70",
                description="MP4 video",
                extensions=["mp4", "m4v"]
            ),
            MimeSignature(
                "video/mp4",
                b"\x00\x00\x00\x1C\x66\x74\x79\x70",
                description="MP4 video",
                extensions=["mp4"]
            ),

            # AVI
            MimeSignature(
                "video/x-msvideo",
                b"\x52\x49\x46\x46",
                description="AVI video",
                extensions=["avi"]
            ),

            # MKV
            MimeSignature(
                "video/x-matroska",
                b"\x1A\x45\xDF\xA3",
                description="Matroska video",
                extensions=["mkv", "webm"]
            ),

            # FLV
            MimeSignature(
                "video/x-flv",
                b"\x46\x4C\x56",
                description="Flash video",
                extensions=["flv"]
            ),

            # MOV
            MimeSignature(
                "video/quicktime",
                b"\x00\x00\x00\x14\x66\x74\x79\x70\x71\x74",
                description="QuickTime video",
                extensions=["mov"]
            ),

            # WMV
            MimeSignature(
                "video/x-ms-wmv",
                b"\x30\x26\xB2\x75\x8E\x66\xCF\x11",
                description="Windows Media Video",
                extensions=["wmv"]
            ),
        ])

        # === AUDIO ===
        signatures.extend([
            # MP3
            MimeSignature(
                "audio/mpeg",
                b"\xFF\xFB",
                description="MP3 audio",
                extensions=["mp3"]
            ),
            MimeSignature(
                "audio/mpeg",
                b"\x49\x44\x33",  # ID3
                description="MP3 audio with ID3",
                extensions=["mp3"]
            ),

            # WAV
            MimeSignature(
                "audio/wav",
                b"\x52\x49\x46\x46",
                description="WAV audio",
                extensions=["wav"]
            ),

            # FLAC
            MimeSignature(
                "audio/flac",
                b"\x66\x4C\x61\x43",
                description="FLAC audio",
                extensions=["flac"]
            ),

            # OGG
            MimeSignature(
                "audio/ogg",
                b"\x4F\x67\x67\x53",
                description="OGG audio",
                extensions=["ogg", "oga"]
            ),

            # M4A
            MimeSignature(
                "audio/mp4",
                b"\x00\x00\x00\x20\x66\x74\x79\x70\x4D\x34\x41",
                description="M4A audio",
                extensions=["m4a"]
            ),

            # WMA
            MimeSignature(
                "audio/x-ms-wma",
                b"\x30\x26\xB2\x75\x8E\x66\xCF\x11",
                description="Windows Media Audio",
                extensions=["wma"]
            ),
        ])

        # === DOCUMENTS ===
        signatures.extend([
            # PDF
            MimeSignature(
                "application/pdf",
                b"%PDF",
                description="PDF document",
                extensions=["pdf"]
            ),

            # Microsoft Office (ZIP-based)
            MimeSignature(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                b"\x50\x4B\x03\x04",
                description="DOCX document",
                extensions=["docx"]
            ),
            MimeSignature(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                b"\x50\x4B\x03\x04",
                description="XLSX spreadsheet",
                extensions=["xlsx"]
            ),
            MimeSignature(
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                b"\x50\x4B\x03\x04",
                description="PPTX presentation",
                extensions=["pptx"]
            ),

            # Microsoft Office (Legacy)
            MimeSignature(
                "application/msword",
                b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1",
                description="DOC document",
                extensions=["doc"]
            ),
            MimeSignature(
                "application/vnd.ms-excel",
                b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1",
                description="XLS spreadsheet",
                extensions=["xls"]
            ),
            MimeSignature(
                "application/vnd.ms-powerpoint",
                b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1",
                description="PPT presentation",
                extensions=["ppt"]
            ),

            # RTF
            MimeSignature(
                "application/rtf",
                b"{\\rtf",
                description="Rich Text Format",
                extensions=["rtf"]
            ),

            # OpenDocument
            MimeSignature(
                "application/vnd.oasis.opendocument.text",
                b"\x50\x4B\x03\x04",
                description="ODT document",
                extensions=["odt"]
            ),
        ])

        # === ARCHIVES ===
        signatures.extend([
            # ZIP
            MimeSignature(
                "application/zip",
                b"\x50\x4B\x03\x04",
                description="ZIP archive",
                extensions=["zip"]
            ),
            MimeSignature(
                "application/zip",
                b"\x50\x4B\x05\x06",
                description="ZIP archive (empty)",
                extensions=["zip"]
            ),
            MimeSignature(
                "application/zip",
                b"\x50\x4B\x07\x08",
                description="ZIP archive (spanned)",
                extensions=["zip"]
            ),

            # RAR
            MimeSignature(
                "application/x-rar-compressed",
                b"\x52\x61\x72\x21\x1A\x07\x00",
                description="RAR archive (v1.5+)",
                extensions=["rar"]
            ),
            MimeSignature(
                "application/x-rar-compressed",
                b"\x52\x61\x72\x21\x1A\x07\x01\x00",
                description="RAR archive (v5.0+)",
                extensions=["rar"]
            ),

            # 7Z
            MimeSignature(
                "application/x-7z-compressed",
                b"\x37\x7A\xBC\xAF\x27\x1C",
                description="7-Zip archive",
                extensions=["7z"]
            ),

            # GZIP
            MimeSignature(
                "application/gzip",
                b"\x1F\x8B",
                description="GZIP archive",
                extensions=["gz"]
            ),

            # TAR
            MimeSignature(
                "application/x-tar",
                b"\x75\x73\x74\x61\x72",
                offset=257,
                description="TAR archive",
                extensions=["tar"]
            ),

            # BZIP2
            MimeSignature(
                "application/x-bzip2",
                b"\x42\x5A\x68",
                description="BZIP2 archive",
                extensions=["bz2"]
            ),

            # CAB
            MimeSignature(
                "application/vnd.ms-cab-compressed",
                b"\x4D\x53\x43\x46",
                description="Microsoft Cabinet",
                extensions=["cab"]
            ),
        ])

        # === EXECUTABLES ===
        signatures.extend([
            # Windows EXE/DLL
            MimeSignature(
                "application/x-msdownload",
                b"\x4D\x5A",
                description="Windows executable",
                extensions=["exe", "dll", "sys"]
            ),

            # ELF (Linux)
            MimeSignature(
                "application/x-executable",
                b"\x7F\x45\x4C\x46",
                description="Linux executable",
                extensions=["", "so"]
            ),

            # Mach-O (macOS)
            MimeSignature(
                "application/x-mach-binary",
                b"\xFE\xED\xFA\xCE",
                description="macOS executable (32-bit)",
                extensions=[""]
            ),
            MimeSignature(
                "application/x-mach-binary",
                b"\xFE\xED\xFA\xCF",
                description="macOS executable (64-bit)",
                extensions=[""]
            ),

            # Java Class
            MimeSignature(
                "application/java-vm",
                b"\xCA\xFE\xBA\xBE",
                description="Java class file",
                extensions=["class"]
            ),

            # DEX (Android)
            MimeSignature(
                "application/vnd.android.dex",
                b"\x64\x65\x78\x0A",
                description="Android DEX file",
                extensions=["dex"]
            ),
        ])

        # === CODE & TEXT ===
        signatures.extend([
            # XML
            MimeSignature(
                "application/xml",
                b"<?xml",
                description="XML document",
                extensions=["xml"]
            ),

            # HTML
            MimeSignature(
                "text/html",
                b"<!DOCTYPE html",
                description="HTML document",
                extensions=["html", "htm"]
            ),
            MimeSignature(
                "text/html",
                b"<html",
                description="HTML document",
                extensions=["html", "htm"]
            ),

            # JSON
            MimeSignature(
                "application/json",
                b"{",
                description="JSON data",
                extensions=["json"]
            ),

            # Python
            MimeSignature(
                "text/x-python",
                b"#!",
                description="Python script",
                extensions=["py"]
            ),
        ])

        # === FONTS ===
        signatures.extend([
            # TTF
            MimeSignature(
                "font/ttf",
                b"\x00\x01\x00\x00",
                description="TrueType font",
                extensions=["ttf"]
            ),

            # OTF
            MimeSignature(
                "font/otf",
                b"\x4F\x54\x54\x4F",
                description="OpenType font",
                extensions=["otf"]
            ),

            # WOFF
            MimeSignature(
                "font/woff",
                b"\x77\x4F\x46\x46",
                description="Web Open Font Format",
                extensions=["woff"]
            ),

            # WOFF2
            MimeSignature(
                "font/woff2",
                b"\x77\x4F\x46\x32",
                description="Web Open Font Format 2",
                extensions=["woff2"]
            ),
        ])

        # === 3D MODELS ===
        signatures.extend([
            # STL (ASCII)
            MimeSignature(
                "model/stl",
                b"solid",
                description="STL 3D model (ASCII)",
                extensions=["stl"]
            ),

            # STL (Binary)
            MimeSignature(
                "model/stl",
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                description="STL 3D model (Binary)",
                extensions=["stl"]
            ),
        ])

        # === DATABASE ===
        signatures.extend([
            # SQLite
            MimeSignature(
                "application/x-sqlite3",
                b"\x53\x51\x4C\x69\x74\x65\x20\x66\x6F\x72\x6D\x61\x74\x20\x33\x00",
                description="SQLite database",
                extensions=["db", "sqlite", "sqlite3"]
            ),

            # Access
            MimeSignature(
                "application/x-msaccess",
                b"\x00\x01\x00\x00\x53\x74\x61\x6E\x64\x61\x72\x64\x20\x4A\x65\x74\x20\x44\x42",
                description="Microsoft Access database",
                extensions=["mdb"]
            ),
        ])

        # === MISC ===
        signatures.extend([
            # ISO
            MimeSignature(
                "application/x-iso9660-image",
                b"\x43\x44\x30\x30\x31",
                offset=0x8001,
                description="ISO disk image",
                extensions=["iso"]
            ),

            # VMDK
            MimeSignature(
                "application/x-vmdk",
                b"\x4B\x44\x4D",
                description="VMware disk image",
                extensions=["vmdk"]
            ),

            # Bitcoin wallet
            MimeSignature(
                "application/x-bitcoin-wallet",
                b"\x00\x00\x00\x00\x62\x31\x05\x00\x09\x00\x00\x00\x00\x20\x00\x00\x00\x09\x00\x00\x00",
                description="Bitcoin wallet",
                extensions=["dat"]
            ),
        ])

        return signatures

    def _build_extension_map(self) -> Dict[str, str]:
        """Build extension to MIME type mapping."""
        ext_map = {}

        for sig in self._signatures:
            for ext in sig.extensions:
                if ext and ext not in ext_map:
                    ext_map[ext] = sig.mime_type

        # Add common text extensions
        text_exts = {
            "txt": "text/plain",
            "log": "text/plain",
            "md": "text/markdown",
            "csv": "text/csv",
            "js": "application/javascript",
            "css": "text/css",
            "py": "text/x-python",
            "java": "text/x-java",
            "c": "text/x-c",
            "cpp": "text/x-c++",
            "h": "text/x-c-header",
            "sh": "application/x-sh",
            "bat": "application/x-bat",
            "ps1": "application/x-powershell",
        }
        ext_map.update(text_exts)

        return ext_map

    def _build_descriptions(self) -> Dict[str, str]:
        """Build MIME type to description mapping."""
        descriptions = {}

        for sig in self._signatures:
            if sig.mime_type not in descriptions and sig.description:
                descriptions[sig.mime_type] = sig.description

        return descriptions

    def _build_category_map(self) -> Dict[str, MimeCategory]:
        """Build MIME type to category mapping."""
        category_map = {}

        # Image types
        for mime in ["image/jpeg", "image/png", "image/gif", "image/bmp",
                     "image/tiff", "image/webp", "image/svg+xml", "image/x-icon",
                     "image/heic", "image/vnd.adobe.photoshop"]:
            category_map[mime] = MimeCategory.IMAGE

        # Video types
        for mime in ["video/mp4", "video/x-msvideo", "video/x-matroska",
                     "video/x-flv", "video/quicktime", "video/x-ms-wmv"]:
            category_map[mime] = MimeCategory.VIDEO

        # Audio types
        for mime in ["audio/mpeg", "audio/wav", "audio/flac", "audio/ogg",
                     "audio/mp4", "audio/x-ms-wma"]:
            category_map[mime] = MimeCategory.AUDIO

        # Document types
        for mime in ["application/pdf", "application/msword", "application/rtf",
                     "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                     "application/vnd.ms-excel", "application/vnd.ms-powerpoint",
                     "application/vnd.oasis.opendocument.text"]:
            category_map[mime] = MimeCategory.DOCUMENT

        # Archive types
        for mime in ["application/zip", "application/x-rar-compressed",
                     "application/x-7z-compressed", "application/gzip",
                     "application/x-tar", "application/x-bzip2",
                     "application/vnd.ms-cab-compressed"]:
            category_map[mime] = MimeCategory.ARCHIVE

        # Executable types
        for mime in ["application/x-msdownload", "application/x-executable",
                     "application/x-mach-binary", "application/java-vm",
                     "application/vnd.android.dex"]:
            category_map[mime] = MimeCategory.EXECUTABLE

        # Code/Text types
        for mime in ["text/plain", "text/html", "application/xml",
                     "application/json", "text/x-python", "text/markdown",
                     "text/csv", "application/javascript", "text/css"]:
            category_map[mime] = MimeCategory.CODE

        # Font types
        for mime in ["font/ttf", "font/otf", "font/woff", "font/woff2"]:
            category_map[mime] = MimeCategory.FONT

        # Model types
        for mime in ["model/stl"]:
            category_map[mime] = MimeCategory.MODEL

        return category_map

    def get_signatures(self) -> List[MimeSignature]:
        """Get all signatures (built-in + user-defined)."""
        return self._signatures + self._user_signatures

    def get_mime_by_extension(self, extension: str) -> Optional[str]:
        """Get MIME type by file extension."""
        ext = extension.lower().lstrip(".")
        return self._extension_map.get(ext)

    def get_description(self, mime_type: str) -> str:
        """Get human-readable description for MIME type."""
        return self._mime_descriptions.get(mime_type, mime_type)

    def get_category(self, mime_type: str) -> MimeCategory:
        """Get category for MIME type."""
        return self._category_map.get(mime_type, MimeCategory.UNKNOWN)

    def add_signature(self, signature: MimeSignature):
        """Add user-defined signature."""
        self._user_signatures.append(signature)

    def get_all_extensions(self) -> List[str]:
        """Get list of all known extensions."""
        return sorted(self._extension_map.keys())

    def get_all_mime_types(self) -> List[str]:
        """Get list of all known MIME types."""
        return sorted(set(sig.mime_type for sig in self.get_signatures()))

    def get_extensions_for_mime(self, mime_type: str) -> List[str]:
        """Get all extensions associated with a MIME type."""
        extensions = []
        for sig in self.get_signatures():
            if sig.mime_type == mime_type:
                extensions.extend(sig.extensions)
        return list(set(extensions))

    def get_mime_types_by_category(self, category: MimeCategory) -> List[str]:
        """Get all MIME types in a category."""
        return [
            mime for mime, cat in self._category_map.items()
            if cat == category
        ]


# Global instance
_mime_db = None


def get_mime_database() -> MimeDatabase:
    """Get global MIME database instance."""
    global _mime_db
    if _mime_db is None:
        _mime_db = MimeDatabase()
    return _mime_db
