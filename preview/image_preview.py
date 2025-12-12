"""
Image preview with thumbnail generation and EXIF metadata.

Supports:
- Thumbnail generation
- EXIF metadata extraction
- Common image formats (JPG, PNG, GIF, BMP, WEBP)
- Lazy loading for large images
"""

import os
import io
import logging
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import base64

logger = logging.getLogger(__name__)


class ImagePreviewer:
    """Generate image previews and thumbnails."""

    # Default thumbnail size
    DEFAULT_THUMBNAIL_SIZE = (256, 256)
    MAX_THUMBNAIL_SIZE = (512, 512)

    # Supported image formats
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif', '.ico'}

    def __init__(self):
        """Initialize image previewer."""
        self._pillow_available = False
        self._exif_available = False

        try:
            from PIL import Image, ExifTags
            self._pillow_available = True
            self._exif_available = True
        except ImportError:
            logger.warning("Pillow not available - image preview disabled")

    def is_supported(self, file_path: str) -> bool:
        """
        Check if file format is supported.

        Args:
            file_path: Path to file

        Returns:
            True if format is supported
        """
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_FORMATS

    def generate_preview(
        self,
        file_path: str,
        thumbnail_size: Optional[Tuple[int, int]] = None,
        include_base64: bool = False
    ) -> Dict[str, Any]:
        """
        Generate image preview with thumbnail and metadata.

        Args:
            file_path: Path to image file
            thumbnail_size: Custom thumbnail size (width, height)
            include_base64: Include base64-encoded thumbnail

        Returns:
            Dictionary containing:
                - dimensions: Original image dimensions
                - format: Image format
                - mode: Color mode
                - file_size: File size in bytes
                - thumbnail_path: Path to cached thumbnail (optional)
                - thumbnail_base64: Base64-encoded thumbnail (optional)
                - has_transparency: Whether image has alpha channel
        """
        if not self._pillow_available:
            return {'error': 'Pillow not available'}

        if not os.path.exists(file_path):
            return {'error': 'File not found'}

        try:
            from PIL import Image

            with Image.open(file_path) as img:
                result = {
                    'dimensions': f"{img.width}x{img.height}",
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'file_size': os.path.getsize(file_path),
                    'has_transparency': img.mode in ('RGBA', 'LA', 'P'),
                }

                # Generate thumbnail
                thumb_size = thumbnail_size or self.DEFAULT_THUMBNAIL_SIZE
                thumbnail = self._generate_thumbnail(img, thumb_size)

                if thumbnail and include_base64:
                    result['thumbnail_base64'] = self._image_to_base64(thumbnail)

                # Get animation info for GIFs
                if img.format == 'GIF':
                    try:
                        n_frames = getattr(img, 'n_frames', 1)
                        result['frames'] = n_frames
                        result['is_animated'] = n_frames > 1
                    except Exception:
                        pass

                return result

        except Exception as e:
            logger.error(f"Error generating image preview: {e}")
            return {'error': str(e)}

    def _generate_thumbnail(
        self,
        image: 'Image.Image',
        size: Tuple[int, int]
    ) -> Optional['Image.Image']:
        """
        Generate thumbnail from image.

        Args:
            image: PIL Image object
            size: Thumbnail size (width, height)

        Returns:
            Thumbnail Image object or None
        """
        try:
            from PIL import Image

            # Create a copy to avoid modifying original
            thumbnail = image.copy()

            # Convert RGBA to RGB for formats that don't support transparency
            if thumbnail.mode == 'RGBA':
                # Create white background
                background = Image.new('RGB', thumbnail.size, (255, 255, 255))
                background.paste(thumbnail, mask=thumbnail.split()[3])  # Use alpha channel as mask
                thumbnail = background
            elif thumbnail.mode not in ('RGB', 'L'):
                thumbnail = thumbnail.convert('RGB')

            # Generate thumbnail maintaining aspect ratio
            thumbnail.thumbnail(size, Image.Resampling.LANCZOS)

            return thumbnail

        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return None

    def _image_to_base64(self, image: 'Image.Image', format: str = 'PNG') -> str:
        """
        Convert PIL Image to base64 string.

        Args:
            image: PIL Image object
            format: Output format (PNG, JPEG)

        Returns:
            Base64-encoded image string
        """
        try:
            buffer = io.BytesIO()
            image.save(buffer, format=format)
            buffer.seek(0)
            img_bytes = buffer.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            return f"data:image/{format.lower()};base64,{img_base64}"
        except Exception as e:
            logger.error(f"Error converting image to base64: {e}")
            return ""

    def save_thumbnail(
        self,
        file_path: str,
        output_path: str,
        size: Optional[Tuple[int, int]] = None
    ) -> bool:
        """
        Generate and save thumbnail to disk.

        Args:
            file_path: Path to source image
            output_path: Path to save thumbnail
            size: Thumbnail size (width, height)

        Returns:
            True if successful
        """
        if not self._pillow_available:
            return False

        try:
            from PIL import Image

            with Image.open(file_path) as img:
                thumb_size = size or self.DEFAULT_THUMBNAIL_SIZE
                thumbnail = self._generate_thumbnail(img, thumb_size)

                if thumbnail:
                    # Ensure output directory exists
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)

                    # Save thumbnail
                    thumbnail.save(output_path, format='PNG', optimize=True)
                    return True

        except Exception as e:
            logger.error(f"Error saving thumbnail: {e}")

        return False

    def get_image_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed image information without generating preview.

        Args:
            file_path: Path to image file

        Returns:
            Dictionary with image information
        """
        if not self._pillow_available:
            return {'error': 'Pillow not available'}

        try:
            from PIL import Image

            with Image.open(file_path) as img:
                info = {
                    'dimensions': f"{img.width}x{img.height}",
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'file_size': os.path.getsize(file_path),
                }

                # Get additional format-specific info
                if hasattr(img, 'info'):
                    pil_info = img.info.copy()

                    # Extract useful fields
                    if 'dpi' in pil_info:
                        info['dpi'] = pil_info['dpi']
                    if 'compression' in pil_info:
                        info['compression'] = pil_info['compression']

                return info

        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            return {'error': str(e)}

    def lazy_load_image(
        self,
        file_path: str,
        max_dimension: int = 1920
    ) -> Optional[bytes]:
        """
        Load and optionally resize large image for display.

        Args:
            file_path: Path to image file
            max_dimension: Maximum width or height

        Returns:
            Image bytes or None
        """
        if not self._pillow_available:
            return None

        try:
            from PIL import Image

            with Image.open(file_path) as img:
                # Check if resizing is needed
                if img.width > max_dimension or img.height > max_dimension:
                    # Calculate new size maintaining aspect ratio
                    ratio = min(max_dimension / img.width, max_dimension / img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))

                    # Resize
                    img = img.resize(new_size, Image.Resampling.LANCZOS)

                # Convert to bytes
                buffer = io.BytesIO()
                img.save(buffer, format=img.format or 'PNG')
                buffer.seek(0)
                return buffer.getvalue()

        except Exception as e:
            logger.error(f"Error lazy loading image: {e}")
            return None

    def extract_exif(self, file_path: str) -> Dict[str, Any]:
        """
        Extract EXIF metadata from image.

        Args:
            file_path: Path to image file

        Returns:
            Dictionary with EXIF data
        """
        if not self._pillow_available or not self._exif_available:
            return {}

        try:
            from PIL import Image, ExifTags

            with Image.open(file_path) as img:
                exif_data = {}

                # Get EXIF data
                exif = img.getexif()
                if not exif:
                    return {}

                # Map tag IDs to names
                for tag_id, value in exif.items():
                    tag_name = ExifTags.TAGS.get(tag_id, tag_id)

                    # Convert bytes to string
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8', errors='ignore')
                        except:
                            value = str(value)

                    # Format specific fields
                    if tag_name in ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']:
                        exif_data[tag_name] = str(value)
                    elif tag_name == 'ExposureTime':
                        if isinstance(value, tuple) and len(value) == 2:
                            exif_data[tag_name] = f"{value[0]}/{value[1]}s"
                        else:
                            exif_data[tag_name] = str(value)
                    elif tag_name == 'FNumber':
                        if isinstance(value, tuple) and len(value) == 2:
                            f_num = value[0] / value[1]
                            exif_data[tag_name] = f"f/{f_num:.1f}"
                        else:
                            exif_data[tag_name] = str(value)
                    elif tag_name == 'ISOSpeedRatings':
                        exif_data[tag_name] = f"ISO {value}"
                    elif tag_name == 'FocalLength':
                        if isinstance(value, tuple) and len(value) == 2:
                            focal = value[0] / value[1]
                            exif_data[tag_name] = f"{focal:.1f}mm"
                        else:
                            exif_data[tag_name] = str(value)
                    elif isinstance(value, (str, int, float)):
                        exif_data[tag_name] = str(value)

                # Get useful fields
                useful_fields = {
                    'Make': 'Camera Make',
                    'Model': 'Camera Model',
                    'DateTime': 'Date Taken',
                    'DateTimeOriginal': 'Original Date',
                    'ExposureTime': 'Shutter Speed',
                    'FNumber': 'Aperture',
                    'ISOSpeedRatings': 'ISO',
                    'FocalLength': 'Focal Length',
                    'Flash': 'Flash',
                    'Orientation': 'Orientation',
                    'Software': 'Software',
                    'Copyright': 'Copyright',
                    'Artist': 'Artist',
                }

                filtered = {}
                for key, label in useful_fields.items():
                    if key in exif_data:
                        filtered[label] = exif_data[key]

                return filtered

        except Exception as e:
            logger.debug(f"Error extracting EXIF: {e}")
            return {}

    def rotate_image(
        self,
        file_path: str,
        angle: int,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Rotate image by angle (90, 180, 270 degrees).

        Args:
            file_path: Path to source image
            angle: Rotation angle (90, 180, 270)
            output_path: Path to save rotated image (None = overwrite)

        Returns:
            Path to rotated image or None
        """
        if not self._pillow_available:
            return None

        if angle not in [90, 180, 270]:
            logger.error(f"Invalid rotation angle: {angle}")
            return None

        try:
            from PIL import Image

            with Image.open(file_path) as img:
                # Rotate
                rotated = img.rotate(-angle, expand=True)

                # Save
                save_path = output_path or file_path
                rotated.save(save_path)

                return save_path

        except Exception as e:
            logger.error(f"Error rotating image: {e}")
            return None

    def create_thumbnail_cache(
        self,
        file_path: str,
        cache_dir: str,
        size: Optional[Tuple[int, int]] = None
    ) -> Optional[str]:
        """
        Create and cache thumbnail on disk.

        Args:
            file_path: Path to source image
            cache_dir: Directory to store thumbnails
            size: Thumbnail size (width, height)

        Returns:
            Path to cached thumbnail or None
        """
        if not self._pillow_available:
            return None

        try:
            import hashlib
            from PIL import Image

            # Generate cache key from file path + mtime
            mtime = os.path.getmtime(file_path)
            cache_key = hashlib.md5(f"{file_path}:{mtime}".encode()).hexdigest()
            cache_file = os.path.join(cache_dir, f"{cache_key}.png")

            # Check if cached thumbnail exists
            if os.path.exists(cache_file):
                return cache_file

            # Create cache directory
            os.makedirs(cache_dir, exist_ok=True)

            # Generate thumbnail
            with Image.open(file_path) as img:
                thumb_size = size or self.DEFAULT_THUMBNAIL_SIZE
                thumbnail = self._generate_thumbnail(img, thumb_size)

                if thumbnail:
                    thumbnail.save(cache_file, format='PNG', optimize=True)
                    return cache_file

        except Exception as e:
            logger.error(f"Error creating thumbnail cache: {e}")

        return None
