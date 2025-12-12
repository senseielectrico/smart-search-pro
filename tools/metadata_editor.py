"""
Metadata Editor - Advanced Metadata Manipulation
Edit, batch process, and manipulate file metadata.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Callable
from datetime import datetime, timedelta
import logging

from .exiftool_wrapper import ExifToolWrapper

logger = logging.getLogger(__name__)


class MetadataEditor:
    """
    Advanced metadata editor with batch operations and templates.
    """

    def __init__(self, exiftool: Optional[ExifToolWrapper] = None):
        """
        Initialize metadata editor.

        Args:
            exiftool: ExifToolWrapper instance (creates new if None)
        """
        self.exiftool = exiftool or ExifToolWrapper()
        self._templates = {}

    def edit_field(
        self,
        file_path: Union[str, Path],
        field_name: str,
        new_value: Any,
        backup: bool = False
    ) -> bool:
        """
        Edit a single metadata field.

        Args:
            file_path: Path to file
            field_name: Metadata field name
            new_value: New value
            backup: Create backup file

        Returns:
            True if successful
        """
        return self.exiftool.set_tag(
            file_path,
            field_name,
            new_value,
            overwrite=not backup
        )

    def edit_multiple_fields(
        self,
        file_path: Union[str, Path],
        fields: Dict[str, Any],
        backup: bool = False
    ) -> bool:
        """
        Edit multiple metadata fields at once.

        Args:
            file_path: Path to file
            fields: Dictionary of field names and values
            backup: Create backup file

        Returns:
            True if successful
        """
        return self.exiftool.set_tags(
            file_path,
            fields,
            overwrite=not backup
        )

    def batch_edit(
        self,
        file_paths: List[Union[str, Path]],
        fields: Dict[str, Any],
        backup: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, bool]:
        """
        Edit metadata for multiple files.

        Args:
            file_paths: List of file paths
            fields: Dictionary of field names and values
            backup: Create backup files
            progress_callback: Callback function(current, total)

        Returns:
            Dictionary mapping file paths to success status
        """
        results = {}
        total = len(file_paths)

        for i, file_path in enumerate(file_paths):
            file_path = str(file_path)

            try:
                success = self.edit_multiple_fields(file_path, fields, backup)
                results[file_path] = success

                if progress_callback:
                    progress_callback(i + 1, total)

            except Exception as e:
                logger.error(f"Error editing {file_path}: {e}")
                results[file_path] = False

        return results

    def apply_pattern(
        self,
        file_paths: List[Union[str, Path]],
        pattern: str,
        target_field: str,
        backup: bool = False
    ) -> Dict[str, bool]:
        """
        Apply a naming pattern to files using their metadata.

        Pattern syntax:
        - {field_name} - Insert metadata field value
        - {date:format} - Insert date with custom format
        - {counter:N} - Insert counter with N digits

        Example: "{Make}_{Model}_{DateTimeOriginal}_{counter:4}"

        Args:
            file_paths: List of file paths
            pattern: Naming pattern
            target_field: Target metadata field (e.g., 'FileName')
            backup: Create backup files

        Returns:
            Dictionary mapping file paths to success status
        """
        results = {}
        counter = 1

        for file_path in file_paths:
            file_path = str(file_path)

            try:
                # Get metadata
                metadata = self.exiftool.extract_metadata(file_path, groups=False)

                # Replace pattern variables
                new_value = pattern

                # Replace metadata fields
                import re
                for match in re.finditer(r'\{([^:}]+)\}', pattern):
                    field = match.group(1)
                    if field in metadata:
                        new_value = new_value.replace(f"{{{field}}}", str(metadata[field]))

                # Replace counter
                for match in re.finditer(r'\{counter:(\d+)\}', pattern):
                    digits = int(match.group(1))
                    new_value = new_value.replace(
                        f"{{counter:{digits}}}",
                        str(counter).zfill(digits)
                    )
                    counter += 1

                # Apply to target field
                success = self.edit_field(file_path, target_field, new_value, backup)
                results[file_path] = success

            except Exception as e:
                logger.error(f"Error applying pattern to {file_path}: {e}")
                results[file_path] = False

        return results

    def anonymize_file(
        self,
        file_path: Union[str, Path],
        backup: bool = False
    ) -> bool:
        """
        Remove all identifying metadata from a file.

        Removes:
        - GPS coordinates
        - Camera serial numbers
        - Author/creator information
        - Copyright
        - Software information

        Args:
            file_path: Path to file
            backup: Create backup file

        Returns:
            True if successful
        """
        # Fields to remove
        fields_to_remove = [
            'GPSLatitude',
            'GPSLongitude',
            'GPSAltitude',
            'GPSPosition',
            'GPS',
            'SerialNumber',
            'InternalSerialNumber',
            'LensSerialNumber',
            'OwnerName',
            'Artist',
            'Creator',
            'Author',
            'Copyright',
            'By-line',
            'Credit',
            'Source',
            'UserComment',
            'XMP:Creator',
            'IPTC:By-line'
        ]

        # Set all fields to empty
        fields = {field: '' for field in fields_to_remove}

        return self.edit_multiple_fields(file_path, fields, backup)

    def anonymize_batch(
        self,
        file_paths: List[Union[str, Path]],
        backup: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, bool]:
        """
        Anonymize multiple files.

        Args:
            file_paths: List of file paths
            backup: Create backup files
            progress_callback: Progress callback function

        Returns:
            Dictionary mapping file paths to success status
        """
        results = {}
        total = len(file_paths)

        for i, file_path in enumerate(file_paths):
            file_path = str(file_path)

            try:
                success = self.anonymize_file(file_path, backup)
                results[file_path] = success

                if progress_callback:
                    progress_callback(i + 1, total)

            except Exception as e:
                logger.error(f"Error anonymizing {file_path}: {e}")
                results[file_path] = False

        return results

    def shift_dates(
        self,
        file_paths: List[Union[str, Path]],
        offset: timedelta,
        backup: bool = False
    ) -> Dict[str, bool]:
        """
        Shift all date/time metadata by a specified offset.

        Useful for correcting timezone issues or camera clock errors.

        Args:
            file_paths: List of file paths
            offset: Time offset to apply
            backup: Create backup files

        Returns:
            Dictionary mapping file paths to success status
        """
        results = {}

        for file_path in file_paths:
            file_path = str(file_path)

            try:
                # Get all metadata
                metadata = self.exiftool.extract_metadata(file_path, groups=False)

                # Find all date fields
                date_fields = {}
                for key, value in metadata.items():
                    if any(term in key.lower() for term in ['date', 'time']):
                        try:
                            # Parse date
                            if isinstance(value, str):
                                # Try EXIF format
                                if ':' in value and ' ' in value:
                                    date_str = value.replace(':', '-', 2)
                                    dt = datetime.fromisoformat(date_str.replace(' ', 'T'))
                                else:
                                    dt = datetime.fromisoformat(value)

                                # Apply offset
                                new_dt = dt + offset

                                # Format back to EXIF format
                                new_value = new_dt.strftime('%Y:%m:%d %H:%M:%S')
                                date_fields[key] = new_value

                        except Exception as e:
                            logger.debug(f"Could not parse date field {key}: {e}")
                            continue

                # Apply changes
                if date_fields:
                    success = self.edit_multiple_fields(file_path, date_fields, backup)
                    results[file_path] = success
                else:
                    results[file_path] = False

            except Exception as e:
                logger.error(f"Error shifting dates for {file_path}: {e}")
                results[file_path] = False

        return results

    def geotag_from_gpx(
        self,
        file_paths: List[Union[str, Path]],
        gpx_file: Union[str, Path],
        backup: bool = False
    ) -> Dict[str, bool]:
        """
        Add GPS coordinates to photos based on GPX track and timestamp.

        Args:
            file_paths: List of image file paths
            gpx_file: GPX track file
            backup: Create backup files

        Returns:
            Dictionary mapping file paths to success status
        """
        try:
            import gpxpy
            import gpxpy.gpx
        except ImportError:
            logger.error("gpxpy library not installed. Install with: pip install gpxpy")
            return {str(f): False for f in file_paths}

        # Parse GPX file
        try:
            with open(str(gpx_file), 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)
        except Exception as e:
            logger.error(f"Error parsing GPX file: {e}")
            return {str(f): False for f in file_paths}

        # Build time-indexed track points
        track_points = []
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    track_points.append({
                        'time': point.time,
                        'lat': point.latitude,
                        'lon': point.longitude,
                        'ele': point.elevation
                    })

        if not track_points:
            logger.error("No track points found in GPX file")
            return {str(f): False for f in file_paths}

        # Sort by time
        track_points.sort(key=lambda p: p['time'])

        results = {}

        for file_path in file_paths:
            file_path = str(file_path)

            try:
                # Get image timestamp
                metadata = self.exiftool.extract_metadata(file_path, groups=False)

                # Find date field
                photo_time = None
                for field in ['DateTimeOriginal', 'CreateDate', 'ModifyDate']:
                    if field in metadata:
                        try:
                            date_str = metadata[field].replace(':', '-', 2)
                            photo_time = datetime.fromisoformat(date_str.replace(' ', 'T'))
                            break
                        except:
                            pass

                if not photo_time:
                    logger.warning(f"No timestamp found for {file_path}")
                    results[file_path] = False
                    continue

                # Find closest track point
                closest_point = min(
                    track_points,
                    key=lambda p: abs((p['time'] - photo_time).total_seconds())
                )

                # Set GPS coordinates
                gps_fields = {
                    'GPSLatitude': closest_point['lat'],
                    'GPSLongitude': closest_point['lon']
                }

                if closest_point['ele']:
                    gps_fields['GPSAltitude'] = closest_point['ele']

                success = self.edit_multiple_fields(file_path, gps_fields, backup)
                results[file_path] = success

            except Exception as e:
                logger.error(f"Error geotagging {file_path}: {e}")
                results[file_path] = False

        return results

    def create_template(self, name: str, fields: Dict[str, Any]):
        """
        Create a reusable metadata template.

        Args:
            name: Template name
            fields: Dictionary of field names and values
        """
        self._templates[name] = fields.copy()

    def apply_template(
        self,
        file_paths: List[Union[str, Path]],
        template_name: str,
        backup: bool = False
    ) -> Dict[str, bool]:
        """
        Apply a metadata template to files.

        Args:
            file_paths: List of file paths
            template_name: Name of template to apply
            backup: Create backup files

        Returns:
            Dictionary mapping file paths to success status
        """
        if template_name not in self._templates:
            raise ValueError(f"Template '{template_name}' not found")

        return self.batch_edit(file_paths, self._templates[template_name], backup)

    def get_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get all available templates."""
        return self._templates.copy()

    def copy_metadata_batch(
        self,
        source_file: Union[str, Path],
        target_files: List[Union[str, Path]],
        backup: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, bool]:
        """
        Copy metadata from one file to multiple target files.

        Args:
            source_file: Source file path
            target_files: List of target file paths
            backup: Create backup files
            progress_callback: Progress callback function

        Returns:
            Dictionary mapping file paths to success status
        """
        results = {}
        total = len(target_files)

        for i, target_file in enumerate(target_files):
            target_file = str(target_file)

            try:
                success = self.exiftool.copy_metadata(
                    source_file,
                    target_file,
                    overwrite=not backup
                )
                results[target_file] = success

                if progress_callback:
                    progress_callback(i + 1, total)

            except Exception as e:
                logger.error(f"Error copying metadata to {target_file}: {e}")
                results[target_file] = False

        return results

    def strip_metadata_batch(
        self,
        file_paths: List[Union[str, Path]],
        backup: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, bool]:
        """
        Remove all metadata from multiple files.

        Args:
            file_paths: List of file paths
            backup: Create backup files
            progress_callback: Progress callback function

        Returns:
            Dictionary mapping file paths to success status
        """
        results = {}
        total = len(file_paths)

        for i, file_path in enumerate(file_paths):
            file_path = str(file_path)

            try:
                success = self.exiftool.remove_all_metadata(
                    file_path,
                    overwrite=not backup
                )
                results[file_path] = success

                if progress_callback:
                    progress_callback(i + 1, total)

            except Exception as e:
                logger.error(f"Error stripping metadata from {file_path}: {e}")
                results[file_path] = False

        return results

    def rename_by_metadata(
        self,
        file_paths: List[Union[str, Path]],
        pattern: str,
        dry_run: bool = False
    ) -> Dict[str, str]:
        """
        Rename files based on their metadata.

        Pattern syntax: same as apply_pattern()

        Args:
            file_paths: List of file paths
            pattern: Naming pattern
            dry_run: Preview changes without applying

        Returns:
            Dictionary mapping old paths to new paths
        """
        renames = {}
        counter = 1

        for file_path in file_paths:
            file_path = str(file_path)

            try:
                # Get metadata
                metadata = self.exiftool.extract_metadata(file_path, groups=False)

                # Get directory and extension
                directory = os.path.dirname(file_path)
                _, ext = os.path.splitext(file_path)

                # Replace pattern variables
                new_name = pattern

                import re
                for match in re.finditer(r'\{([^:}]+)\}', pattern):
                    field = match.group(1)
                    if field in metadata:
                        value = str(metadata[field])
                        # Clean invalid filename characters
                        value = re.sub(r'[<>:"/\\|?*]', '_', value)
                        new_name = new_name.replace(f"{{{field}}}", value)

                # Replace counter
                for match in re.finditer(r'\{counter:(\d+)\}', pattern):
                    digits = int(match.group(1))
                    new_name = new_name.replace(
                        f"{{counter:{digits}}}",
                        str(counter).zfill(digits)
                    )
                    counter += 1

                # Add extension
                new_name += ext
                new_path = os.path.join(directory, new_name)

                renames[file_path] = new_path

                # Perform rename if not dry run
                if not dry_run:
                    os.rename(file_path, new_path)

            except Exception as e:
                logger.error(f"Error renaming {file_path}: {e}")

        return renames
