"""
ExifTool Wrapper - Complete ExifTool Integration
Provides Python interface to ExifTool for metadata extraction and manipulation.

Supports 400+ file formats including:
- Images: JPEG, PNG, TIFF, RAW (CR2, NEF, ARW, etc.)
- Video: MP4, MOV, AVI, MKV
- Audio: MP3, FLAC, WAV
- Documents: PDF, DOCX, XLSX
- And many more...
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ExifToolWrapper:
    """
    Wrapper for ExifTool with automatic path detection and fallback support.
    """

    # Default ExifTool paths to check
    DEFAULT_PATHS = [
        r"D:\MAIN_DATA_CENTER\Dev_Tools\ExifTool\ExifTool.exe",
        r"C:\Program Files\ExifTool\exiftool.exe",
        r"C:\Program Files (x86)\ExifTool\exiftool.exe",
        "exiftool",  # Check PATH
        "exiftool.exe"
    ]

    def __init__(self, exiftool_path: Optional[str] = None):
        """
        Initialize ExifTool wrapper.

        Args:
            exiftool_path: Custom path to ExifTool executable. If None, auto-detect.
        """
        self.exiftool_path = exiftool_path or self._find_exiftool()
        self._verify_installation()
        self._cache = {}  # Simple result cache

    def _find_exiftool(self) -> Optional[str]:
        """
        Automatically find ExifTool executable.

        Returns:
            Path to ExifTool or None if not found
        """
        # Check each default path
        for path in self.DEFAULT_PATHS:
            try:
                # Try to expand environment variables
                expanded_path = os.path.expandvars(path)

                # Check if file exists
                if os.path.isfile(expanded_path):
                    return expanded_path

                # Try using shutil.which for executables in PATH
                if shutil.which(path):
                    return shutil.which(path)

            except Exception as e:
                logger.debug(f"Error checking path {path}: {e}")
                continue

        return None

    def _verify_installation(self):
        """
        Verify ExifTool is properly installed and accessible.

        Raises:
            RuntimeError: If ExifTool is not found or not working
        """
        if not self.exiftool_path:
            raise RuntimeError(
                "ExifTool not found. Please install ExifTool or set the path manually.\n"
                "Download from: https://exiftool.org/\n"
                f"Checked paths: {', '.join(self.DEFAULT_PATHS)}"
            )

        try:
            # Test ExifTool with version command
            result = subprocess.run(
                [self.exiftool_path, '-ver'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"ExifTool version {version} found at: {self.exiftool_path}")
            else:
                raise RuntimeError(f"ExifTool execution failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            raise RuntimeError("ExifTool execution timed out")
        except Exception as e:
            raise RuntimeError(f"Failed to verify ExifTool: {e}")

    def get_version(self) -> str:
        """Get ExifTool version."""
        result = subprocess.run(
            [self.exiftool_path, '-ver'],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

    def is_available(self) -> bool:
        """Check if ExifTool is available and working."""
        try:
            self._verify_installation()
            return True
        except:
            return False

    def extract_metadata(
        self,
        file_path: Union[str, Path],
        groups: bool = True,
        binary: bool = False
    ) -> Dict[str, Any]:
        """
        Extract all metadata from a file.

        Args:
            file_path: Path to file
            groups: Include group names in output
            binary: Include binary data fields

        Returns:
            Dictionary containing all metadata
        """
        file_path = str(file_path)

        # Check cache
        cache_key = f"{file_path}_{groups}_{binary}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Build command
        cmd = [self.exiftool_path, '-json', '-charset', 'UTF8']

        if groups:
            cmd.append('-G')

        if binary:
            cmd.append('-b')
        else:
            cmd.append('-n')  # Numeric output for GPS coordinates

        cmd.append(file_path)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"ExifTool error: {result.stderr}")
                return {}

            # Parse JSON output
            data = json.loads(result.stdout)
            metadata = data[0] if data else {}

            # Cache result
            self._cache[cache_key] = metadata

            return metadata

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout reading metadata from {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ExifTool JSON output: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}

    def extract_metadata_batch(
        self,
        file_paths: List[Union[str, Path]],
        groups: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract metadata from multiple files in one call (more efficient).

        Args:
            file_paths: List of file paths
            groups: Include group names

        Returns:
            Dictionary mapping file paths to their metadata
        """
        if not file_paths:
            return {}

        # Convert to strings
        file_paths = [str(p) for p in file_paths]

        # Filter existing files
        existing_files = [f for f in file_paths if os.path.isfile(f)]

        if not existing_files:
            return {}

        # Build command
        cmd = [self.exiftool_path, '-json', '-charset', 'UTF8', '-n']

        if groups:
            cmd.append('-G')

        cmd.extend(existing_files)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                logger.error(f"ExifTool batch error: {result.stderr}")
                return {}

            # Parse JSON output
            data = json.loads(result.stdout)

            # Map by SourceFile
            metadata_map = {}
            for item in data:
                source_file = item.get('SourceFile', '')
                if source_file:
                    metadata_map[source_file] = item

            return metadata_map

        except Exception as e:
            logger.error(f"Error in batch extraction: {e}")
            return {}

    def get_tag(
        self,
        file_path: Union[str, Path],
        tag_name: str
    ) -> Optional[Any]:
        """
        Get a specific metadata tag value.

        Args:
            file_path: Path to file
            tag_name: Tag name (e.g., 'DateTimeOriginal', 'GPSLatitude')

        Returns:
            Tag value or None if not found
        """
        metadata = self.extract_metadata(file_path, groups=False)
        return metadata.get(tag_name)

    def set_tag(
        self,
        file_path: Union[str, Path],
        tag_name: str,
        value: Any,
        overwrite: bool = True
    ) -> bool:
        """
        Set a metadata tag value.

        Args:
            file_path: Path to file
            tag_name: Tag name
            value: New value
            overwrite: Overwrite original file (creates backup with _original)

        Returns:
            True if successful
        """
        file_path = str(file_path)

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Build command
        cmd = [self.exiftool_path]

        if overwrite:
            cmd.append('-overwrite_original')

        cmd.append(f'-{tag_name}={value}')
        cmd.append(file_path)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Clear cache for this file
            self._clear_file_cache(file_path)

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Error setting tag: {e}")
            return False

    def set_tags(
        self,
        file_path: Union[str, Path],
        tags: Dict[str, Any],
        overwrite: bool = True
    ) -> bool:
        """
        Set multiple metadata tags at once.

        Args:
            file_path: Path to file
            tags: Dictionary of tag names and values
            overwrite: Overwrite original file

        Returns:
            True if successful
        """
        file_path = str(file_path)

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not tags:
            return False

        # Build command
        cmd = [self.exiftool_path]

        if overwrite:
            cmd.append('-overwrite_original')

        for tag_name, value in tags.items():
            cmd.append(f'-{tag_name}={value}')

        cmd.append(file_path)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Clear cache
            self._clear_file_cache(file_path)

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Error setting tags: {e}")
            return False

    def remove_all_metadata(
        self,
        file_path: Union[str, Path],
        overwrite: bool = True
    ) -> bool:
        """
        Remove all metadata from a file (strip).

        Args:
            file_path: Path to file
            overwrite: Overwrite original file

        Returns:
            True if successful
        """
        file_path = str(file_path)

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Build command
        cmd = [self.exiftool_path, '-all=']

        if overwrite:
            cmd.append('-overwrite_original')

        cmd.append(file_path)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Clear cache
            self._clear_file_cache(file_path)

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Error removing metadata: {e}")
            return False

    def copy_metadata(
        self,
        source_file: Union[str, Path],
        target_file: Union[str, Path],
        overwrite: bool = True
    ) -> bool:
        """
        Copy all metadata from source to target file.

        Args:
            source_file: Source file path
            target_file: Target file path
            overwrite: Overwrite original target file

        Returns:
            True if successful
        """
        source_file = str(source_file)
        target_file = str(target_file)

        if not os.path.isfile(source_file):
            raise FileNotFoundError(f"Source file not found: {source_file}")

        if not os.path.isfile(target_file):
            raise FileNotFoundError(f"Target file not found: {target_file}")

        # Build command
        cmd = [self.exiftool_path, '-TagsFromFile', source_file]

        if overwrite:
            cmd.append('-overwrite_original')

        cmd.append(target_file)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Clear cache
            self._clear_file_cache(target_file)

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Error copying metadata: {e}")
            return False

    def extract_thumbnail(
        self,
        file_path: Union[str, Path],
        output_path: Union[str, Path]
    ) -> bool:
        """
        Extract embedded thumbnail from file.

        Args:
            file_path: Source file path
            output_path: Output thumbnail path

        Returns:
            True if successful
        """
        file_path = str(file_path)
        output_path = str(output_path)

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Build command
        cmd = [
            self.exiftool_path,
            '-b',
            '-ThumbnailImage',
            file_path
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout:
                # Write thumbnail data
                with open(output_path, 'wb') as f:
                    f.write(result.stdout)
                return True

            return False

        except Exception as e:
            logger.error(f"Error extracting thumbnail: {e}")
            return False

    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported file formats.

        Returns:
            List of supported file extensions
        """
        try:
            result = subprocess.run(
                [self.exiftool_path, '-listf'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # Parse format list
                formats = []
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('--') and not line.startswith('ExifTool'):
                        formats.append(line)
                return formats

            return []

        except Exception as e:
            logger.error(f"Error getting supported formats: {e}")
            return []

    def _clear_file_cache(self, file_path: str):
        """Clear cache entries for a specific file."""
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(file_path)]
        for key in keys_to_remove:
            del self._cache[key]

    def clear_cache(self):
        """Clear the entire metadata cache."""
        self._cache.clear()

    def execute_command(
        self,
        args: List[str],
        timeout: int = 30
    ) -> subprocess.CompletedProcess:
        """
        Execute custom ExifTool command.

        Args:
            args: List of ExifTool arguments (without exiftool executable)
            timeout: Command timeout in seconds

        Returns:
            subprocess.CompletedProcess result
        """
        cmd = [self.exiftool_path] + args

        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
