"""
Preview module for Smart Search Pro.

Provides preview generation and caching for various file types including:
- Text files with syntax highlighting
- Images with thumbnails and EXIF data
- Documents (PDF, Office)
- Media files (audio, video)
- Archives (ZIP, 7z, RAR)
"""

from .manager import PreviewManager
from .metadata import MetadataExtractor

__all__ = ['PreviewManager', 'MetadataExtractor']
