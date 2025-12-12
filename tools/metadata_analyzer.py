"""
Metadata Analyzer - Deep Forensic Metadata Analysis
Extracts and analyzes forensic information from file metadata.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime
from collections import defaultdict
import logging

try:
    from .exiftool_wrapper import ExifToolWrapper
except ImportError:
    from exiftool_wrapper import ExifToolWrapper

logger = logging.getLogger(__name__)


class MetadataAnalyzer:
    """
    Advanced metadata analyzer for forensic investigation.
    """

    def __init__(self, exiftool: Optional[ExifToolWrapper] = None):
        """
        Initialize metadata analyzer.

        Args:
            exiftool: ExifToolWrapper instance (creates new if None)
        """
        self.exiftool = exiftool or ExifToolWrapper()

    def analyze_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Perform complete forensic analysis of a file's metadata.

        Args:
            file_path: Path to file

        Returns:
            Dictionary containing forensic analysis results
        """
        file_path = str(file_path)

        # Extract all metadata
        metadata = self.exiftool.extract_metadata(file_path, groups=True)

        if not metadata:
            return {
                'error': 'No metadata found or file not accessible',
                'file_path': file_path
            }

        # Perform forensic analysis
        analysis = {
            'file_path': file_path,
            'file_size': os.path.getsize(file_path),
            'camera_info': self._extract_camera_info(metadata),
            'gps_info': self._extract_gps_info(metadata),
            'datetime_info': self._extract_datetime_info(metadata),
            'software_info': self._extract_software_info(metadata),
            'author_info': self._extract_author_info(metadata),
            'copyright_info': self._extract_copyright_info(metadata),
            'hidden_metadata': self._find_hidden_metadata(metadata),
            'anomalies': self._detect_anomalies(metadata),
            'device_fingerprint': self._create_device_fingerprint(metadata),
            'raw_metadata': metadata
        }

        return analysis

    def _extract_camera_info(self, metadata: Dict) -> Dict[str, Any]:
        """Extract camera/device information."""
        camera_info = {}

        # Common camera fields
        camera_fields = {
            'make': ['EXIF:Make', 'Make'],
            'model': ['EXIF:Model', 'Model'],
            'lens': ['EXIF:LensModel', 'LensModel', 'Lens'],
            'serial': ['EXIF:SerialNumber', 'SerialNumber', 'InternalSerialNumber'],
            'lens_serial': ['EXIF:LensSerialNumber', 'LensSerialNumber']
        }

        for key, fields in camera_fields.items():
            for field in fields:
                if field in metadata:
                    camera_info[key] = metadata[field]
                    break

        # Technical details
        tech_fields = {
            'iso': ['EXIF:ISO', 'ISO'],
            'aperture': ['EXIF:FNumber', 'FNumber', 'Aperture'],
            'shutter_speed': ['EXIF:ExposureTime', 'ExposureTime', 'ShutterSpeed'],
            'focal_length': ['EXIF:FocalLength', 'FocalLength'],
            'flash': ['EXIF:Flash', 'Flash']
        }

        for key, fields in tech_fields.items():
            for field in fields:
                if field in metadata:
                    camera_info[key] = metadata[field]
                    break

        return camera_info

    def _extract_gps_info(self, metadata: Dict) -> Dict[str, Any]:
        """Extract and format GPS information."""
        gps_info = {}

        # GPS fields
        gps_fields = {
            'latitude': ['EXIF:GPSLatitude', 'GPSLatitude'],
            'longitude': ['EXIF:GPSLongitude', 'GPSLongitude'],
            'altitude': ['EXIF:GPSAltitude', 'GPSAltitude'],
            'timestamp': ['EXIF:GPSDateTime', 'GPSDateTime', 'EXIF:GPSTimeStamp'],
            'satellites': ['EXIF:GPSSatellites', 'GPSSatellites'],
            'speed': ['EXIF:GPSSpeed', 'GPSSpeed'],
            'direction': ['EXIF:GPSImgDirection', 'GPSImgDirection']
        }

        for key, fields in gps_fields.items():
            for field in fields:
                if field in metadata:
                    gps_info[key] = metadata[field]
                    break

        # Create formatted coordinates
        if 'latitude' in gps_info and 'longitude' in gps_info:
            lat = gps_info['latitude']
            lon = gps_info['longitude']

            # Format coordinates
            gps_info['coordinates'] = f"{lat}, {lon}"

            # Create Google Maps link
            gps_info['map_link'] = f"https://www.google.com/maps?q={lat},{lon}"

            # Create OpenStreetMap link
            gps_info['osm_link'] = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=15"

        return gps_info

    def _extract_datetime_info(self, metadata: Dict) -> Dict[str, Any]:
        """Extract and normalize date/time information."""
        datetime_info = {}

        # Date fields in priority order
        date_fields = [
            ('creation', ['EXIF:DateTimeOriginal', 'DateTimeOriginal', 'CreateDate']),
            ('modification', ['EXIF:ModifyDate', 'ModifyDate', 'FileModifyDate']),
            ('digitized', ['EXIF:DateTimeDigitized', 'DateTimeDigitized']),
            ('gps', ['EXIF:GPSDateTime', 'GPSDateTime'])
        ]

        for key, fields in date_fields:
            for field in fields:
                if field in metadata:
                    datetime_info[key] = self._normalize_datetime(metadata[field])
                    break

        # Check for date inconsistencies
        if datetime_info:
            dates = list(datetime_info.values())
            if len(set(dates)) > 1:
                datetime_info['warning'] = 'Inconsistent dates detected'

        return datetime_info

    def _normalize_datetime(self, date_str: str) -> str:
        """Normalize datetime string to ISO format."""
        try:
            # Common EXIF format: "2024:12:12 15:30:45"
            if ':' in date_str and ' ' in date_str:
                date_str = date_str.replace(':', '-', 2)

            # Try parsing
            dt = datetime.fromisoformat(date_str.replace(' ', 'T'))
            return dt.isoformat()
        except:
            return date_str

    def _extract_software_info(self, metadata: Dict) -> Dict[str, Any]:
        """Extract software and editing information."""
        software_info = {}

        # Software fields
        software_fields = {
            'software': ['EXIF:Software', 'Software', 'CreatorTool'],
            'processing': ['EXIF:ProcessingSoftware', 'ProcessingSoftware'],
            'firmware': ['EXIF:FirmwareVersion', 'FirmwareVersion'],
            'application': ['XMP:CreatorTool', 'XMP-xmp:CreatorTool'],
            'history': ['XMP:History', 'XMP-photoshop:History']
        }

        for key, fields in software_fields.items():
            for field in fields:
                if field in metadata:
                    software_info[key] = metadata[field]
                    break

        # Detect common editing software
        if 'software' in software_info:
            sw = software_info['software'].lower()
            software_info['editors_detected'] = []

            editors = {
                'photoshop': 'Adobe Photoshop',
                'lightroom': 'Adobe Lightroom',
                'gimp': 'GIMP',
                'paint.net': 'Paint.NET',
                'affinity': 'Affinity Photo',
                'capture one': 'Capture One',
                'darktable': 'Darktable'
            }

            for keyword, name in editors.items():
                if keyword in sw:
                    software_info['editors_detected'].append(name)

        return software_info

    def _extract_author_info(self, metadata: Dict) -> Dict[str, Any]:
        """Extract author and creator information."""
        author_info = {}

        # Author fields
        author_fields = {
            'author': ['EXIF:Artist', 'Artist', 'Creator', 'XMP:Creator'],
            'by_line': ['IPTC:By-line', 'By-line'],
            'owner': ['EXIF:OwnerName', 'OwnerName'],
            'credit': ['IPTC:Credit', 'Credit'],
            'source': ['IPTC:Source', 'Source']
        }

        for key, fields in author_fields.items():
            for field in fields:
                if field in metadata:
                    author_info[key] = metadata[field]
                    break

        return author_info

    def _extract_copyright_info(self, metadata: Dict) -> Dict[str, Any]:
        """Extract copyright information."""
        copyright_info = {}

        # Copyright fields
        copyright_fields = {
            'copyright': ['EXIF:Copyright', 'Copyright', 'XMP:Rights'],
            'rights': ['XMP:UsageTerms', 'UsageTerms'],
            'license': ['XMP:License', 'License']
        }

        for key, fields in copyright_fields.items():
            for field in fields:
                if field in metadata:
                    copyright_info[key] = metadata[field]
                    break

        return copyright_info

    def _find_hidden_metadata(self, metadata: Dict) -> Dict[str, Any]:
        """Find potentially hidden or sensitive metadata."""
        hidden = {}

        # Patterns for sensitive data
        sensitive_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'url': r'https?://[^\s]+',
            'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        }

        # Scan all metadata values
        for key, value in metadata.items():
            if not isinstance(value, str):
                continue

            for pattern_name, pattern in sensitive_patterns.items():
                matches = re.findall(pattern, value)
                if matches:
                    if pattern_name not in hidden:
                        hidden[pattern_name] = []
                    hidden[pattern_name].extend(matches)

        # Remove duplicates
        for key in hidden:
            hidden[key] = list(set(hidden[key]))

        # Check for comments and descriptions
        comment_fields = ['EXIF:UserComment', 'XMP:Description', 'IPTC:Caption-Abstract']
        for field in comment_fields:
            if field in metadata and metadata[field]:
                if 'comments' not in hidden:
                    hidden['comments'] = []
                hidden['comments'].append({
                    'field': field,
                    'content': metadata[field]
                })

        return hidden

    def _detect_anomalies(self, metadata: Dict) -> List[str]:
        """Detect metadata anomalies that might indicate tampering."""
        anomalies = []

        # Check for missing standard fields
        expected_fields = ['FileSize', 'FileType', 'MIMEType']
        missing = [f for f in expected_fields if f not in metadata]
        if missing:
            anomalies.append(f"Missing standard fields: {', '.join(missing)}")

        # Check date consistency
        dates = []
        for key, value in metadata.items():
            if 'date' in key.lower() or 'time' in key.lower():
                try:
                    dt = self._normalize_datetime(str(value))
                    dates.append(dt)
                except:
                    pass

        if len(dates) >= 2:
            unique_dates = set(dates)
            if len(unique_dates) > 1:
                anomalies.append(f"Found {len(unique_dates)} different timestamps")

        # Check for GPS without camera make/model
        has_gps = any('gps' in k.lower() for k in metadata.keys())
        has_camera = 'Make' in metadata or 'Model' in metadata

        if has_gps and not has_camera:
            anomalies.append("GPS data present without camera information")

        # Check for suspiciously edited metadata
        if 'Software' in metadata:
            sw = metadata['Software'].lower()
            if any(editor in sw for editor in ['photoshop', 'gimp', 'edited']):
                anomalies.append("Image shows signs of editing")

        return anomalies

    def _create_device_fingerprint(self, metadata: Dict) -> str:
        """Create a unique fingerprint for the device that created the file."""
        fingerprint_parts = []

        # Key identifying fields
        id_fields = [
            'Make', 'Model', 'SerialNumber', 'InternalSerialNumber',
            'LensModel', 'LensSerialNumber', 'Software', 'FirmwareVersion'
        ]

        for field in id_fields:
            if field in metadata:
                fingerprint_parts.append(f"{field}:{metadata[field]}")

        if not fingerprint_parts:
            return "unknown"

        return " | ".join(fingerprint_parts)

    def compare_metadata(
        self,
        file1: Union[str, Path],
        file2: Union[str, Path]
    ) -> Dict[str, Any]:
        """
        Compare metadata between two files.

        Args:
            file1: First file path
            file2: Second file path

        Returns:
            Comparison results
        """
        meta1 = self.exiftool.extract_metadata(file1, groups=False)
        meta2 = self.exiftool.extract_metadata(file2, groups=False)

        # Find common and unique keys
        keys1 = set(meta1.keys())
        keys2 = set(meta2.keys())

        common_keys = keys1 & keys2
        only_in_file1 = keys1 - keys2
        only_in_file2 = keys2 - keys1

        # Compare common fields
        differences = {}
        similarities = {}

        for key in common_keys:
            if meta1[key] == meta2[key]:
                similarities[key] = meta1[key]
            else:
                differences[key] = {
                    'file1': meta1[key],
                    'file2': meta2[key]
                }

        return {
            'similarities': similarities,
            'differences': differences,
            'only_in_file1': {k: meta1[k] for k in only_in_file1},
            'only_in_file2': {k: meta2[k] for k in only_in_file2},
            'similarity_score': len(similarities) / len(common_keys) if common_keys else 0
        }

    def create_timeline(self, file_paths: List[Union[str, Path]]) -> List[Dict[str, Any]]:
        """
        Create timeline from multiple files based on metadata dates.

        Args:
            file_paths: List of file paths

        Returns:
            Sorted timeline of events
        """
        timeline = []

        for file_path in file_paths:
            file_path = str(file_path)
            metadata = self.exiftool.extract_metadata(file_path, groups=False)

            # Extract all dates
            for key, value in metadata.items():
                if any(term in key.lower() for term in ['date', 'time']):
                    try:
                        normalized_date = self._normalize_datetime(str(value))
                        timeline.append({
                            'file': file_path,
                            'event': key,
                            'timestamp': normalized_date,
                            'value': value
                        })
                    except:
                        pass

        # Sort by timestamp
        timeline.sort(key=lambda x: x['timestamp'])

        return timeline

    def detect_duplicates_by_metadata(
        self,
        file_paths: List[Union[str, Path]],
        tolerance: float = 1.0
    ) -> List[List[str]]:
        """
        Detect potential duplicates based on metadata similarity.

        Args:
            file_paths: List of file paths
            tolerance: Similarity threshold (0-1, higher is more strict)

        Returns:
            List of duplicate groups
        """
        if len(file_paths) < 2:
            return []

        file_paths = [str(p) for p in file_paths]

        # Extract metadata for all files
        all_metadata = {}
        for file_path in file_paths:
            meta = self.exiftool.extract_metadata(file_path, groups=False)
            all_metadata[file_path] = meta

        # Compare each pair
        duplicates = []
        checked = set()

        for i, file1 in enumerate(file_paths):
            for file2 in file_paths[i+1:]:
                pair = tuple(sorted([file1, file2]))
                if pair in checked:
                    continue

                checked.add(pair)

                # Compare
                comparison = self.compare_metadata(file1, file2)
                if comparison['similarity_score'] >= tolerance:
                    # Add to duplicate groups
                    found_group = False
                    for group in duplicates:
                        if file1 in group or file2 in group:
                            group.add(file1)
                            group.add(file2)
                            found_group = True
                            break

                    if not found_group:
                        duplicates.append({file1, file2})

        # Convert sets to lists
        return [list(group) for group in duplicates]
