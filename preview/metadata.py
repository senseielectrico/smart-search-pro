"""
Extended metadata extraction for various file types.

Extracts EXIF from images, ID3 tags from audio, video codec info,
and document properties.
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extracts metadata from various file types."""

    def __init__(self):
        """Initialize metadata extractor with optional libraries."""
        self._pillow_available = False
        self._mutagen_available = False
        self._office_available = False

        try:
            from PIL import Image
            from PIL.ExifTags import TAGS, GPSTAGS
            self._pillow_available = True
        except ImportError:
            logger.debug("Pillow not available for EXIF extraction")

        try:
            import mutagen
            self._mutagen_available = True
        except ImportError:
            logger.debug("Mutagen not available for audio metadata")

        try:
            import olefile
            self._office_available = True
        except ImportError:
            logger.debug("olefile not available for Office metadata")

    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from file based on type.

        Args:
            file_path: Path to file

        Returns:
            Dictionary containing metadata
        """
        if not os.path.exists(file_path):
            return {}

        path = Path(file_path)
        ext = path.suffix.lower()

        metadata = {
            'filename': path.name,
            'size': os.path.getsize(file_path),
            'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
            'created': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
        }

        # Image metadata
        if ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}:
            metadata.update(self._extract_image_metadata(file_path))

        # Audio metadata
        elif ext in {'.mp3', '.flac', '.ogg', '.m4a', '.wav', '.wma'}:
            metadata.update(self._extract_audio_metadata(file_path))

        # Video metadata
        elif ext in {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'}:
            metadata.update(self._extract_video_metadata(file_path))

        # Document metadata
        elif ext in {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}:
            metadata.update(self._extract_document_metadata(file_path))

        return metadata

    def _extract_image_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract EXIF and other metadata from images."""
        metadata = {}

        if not self._pillow_available:
            return metadata

        try:
            from PIL import Image
            from PIL.ExifTags import TAGS, GPSTAGS

            with Image.open(file_path) as img:
                metadata['dimensions'] = f"{img.width}x{img.height}"
                metadata['format'] = img.format
                metadata['mode'] = img.mode

                # Extract EXIF data
                exif_data = img.getexif()
                if exif_data:
                    exif = {}
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)

                        # Handle special tags
                        if tag == "GPSInfo":
                            gps_data = {}
                            for gps_tag_id, gps_value in value.items():
                                gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                                gps_data[gps_tag] = str(gps_value)
                            exif[tag] = gps_data
                        elif tag == "DateTime":
                            exif[tag] = str(value)
                        elif isinstance(value, bytes):
                            exif[tag] = value.decode('utf-8', errors='ignore')[:100]
                        elif isinstance(value, (int, float, str)):
                            exif[tag] = str(value)

                    # Extract common useful fields
                    if 'Make' in exif:
                        metadata['camera_make'] = exif['Make']
                    if 'Model' in exif:
                        metadata['camera_model'] = exif['Model']
                    if 'DateTime' in exif:
                        metadata['photo_date'] = exif['DateTime']
                    if 'ExposureTime' in exif:
                        metadata['exposure'] = exif['ExposureTime']
                    if 'FNumber' in exif:
                        metadata['aperture'] = exif['FNumber']
                    if 'ISOSpeedRatings' in exif:
                        metadata['iso'] = exif['ISOSpeedRatings']

                    metadata['exif'] = exif

        except Exception as e:
            logger.debug(f"Error extracting image metadata: {e}")

        return metadata

    def _extract_audio_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract ID3 tags and other metadata from audio files."""
        metadata = {}

        if not self._mutagen_available:
            return metadata

        try:
            import mutagen

            audio = mutagen.File(file_path)
            if audio is not None:
                # Duration
                if hasattr(audio.info, 'length'):
                    metadata['duration'] = self._format_duration(audio.info.length)
                    metadata['duration_seconds'] = audio.info.length

                # Bitrate
                if hasattr(audio.info, 'bitrate'):
                    metadata['bitrate'] = f"{audio.info.bitrate // 1000} kbps"

                # Sample rate
                if hasattr(audio.info, 'sample_rate'):
                    metadata['sample_rate'] = f"{audio.info.sample_rate} Hz"

                # Tags
                if audio.tags:
                    tags = {}
                    for key, value in audio.tags.items():
                        # Convert tag values to strings
                        if isinstance(value, list):
                            tags[key] = ', '.join(str(v) for v in value)
                        else:
                            tags[key] = str(value)

                    # Extract common fields
                    for common_key in ['title', 'artist', 'album', 'date', 'genre']:
                        for tag_key, tag_value in tags.items():
                            if common_key in tag_key.lower():
                                metadata[common_key] = tag_value
                                break

                    metadata['tags'] = tags

        except Exception as e:
            logger.debug(f"Error extracting audio metadata: {e}")

        return metadata

    def _extract_video_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract video codec and metadata."""
        metadata = {}

        # Try with mutagen first
        if self._mutagen_available:
            try:
                import mutagen

                video = mutagen.File(file_path)
                if video is not None:
                    if hasattr(video.info, 'length'):
                        metadata['duration'] = self._format_duration(video.info.length)
                        metadata['duration_seconds'] = video.info.length

                    if hasattr(video.info, 'width'):
                        metadata['width'] = video.info.width
                    if hasattr(video.info, 'height'):
                        metadata['height'] = video.info.height
                    if hasattr(video.info, 'bitrate'):
                        metadata['bitrate'] = f"{video.info.bitrate // 1000} kbps"
            except Exception as e:
                logger.debug(f"Error extracting video metadata with mutagen: {e}")

        # Could add ffprobe support here if available
        return metadata

    def _extract_document_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from documents (PDF, Office)."""
        metadata = {}
        ext = Path(file_path).suffix.lower()

        # PDF metadata
        if ext == '.pdf':
            try:
                import pypdf

                with open(file_path, 'rb') as f:
                    pdf = pypdf.PdfReader(f)
                    metadata['pages'] = len(pdf.pages)

                    if pdf.metadata:
                        doc_meta = {}
                        for key, value in pdf.metadata.items():
                            # Remove leading slash from key
                            clean_key = key.lstrip('/')
                            doc_meta[clean_key] = str(value)

                        # Extract common fields
                        if '/Title' in pdf.metadata:
                            metadata['title'] = str(pdf.metadata['/Title'])
                        if '/Author' in pdf.metadata:
                            metadata['author'] = str(pdf.metadata['/Author'])
                        if '/Subject' in pdf.metadata:
                            metadata['subject'] = str(pdf.metadata['/Subject'])
                        if '/Creator' in pdf.metadata:
                            metadata['creator'] = str(pdf.metadata['/Creator'])

                        metadata['pdf_metadata'] = doc_meta

            except Exception as e:
                logger.debug(f"Error extracting PDF metadata: {e}")

        # Office documents
        elif ext in {'.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'} and self._office_available:
            try:
                import olefile

                if olefile.isOleFile(file_path):
                    ole = olefile.OleFileIO(file_path)
                    meta = ole.get_metadata()

                    if meta.author:
                        metadata['author'] = meta.author
                    if meta.title:
                        metadata['title'] = meta.title
                    if meta.subject:
                        metadata['subject'] = meta.subject
                    if meta.create_time:
                        metadata['created'] = meta.create_time.isoformat()
                    if meta.last_saved_time:
                        metadata['modified'] = meta.last_saved_time.isoformat()

                    ole.close()

            except Exception as e:
                logger.debug(f"Error extracting Office metadata: {e}")

        return metadata

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in seconds to HH:MM:SS or MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
