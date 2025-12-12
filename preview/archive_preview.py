"""
Archive preview for compressed files.

Supports:
- List contents of ZIP, 7z, RAR, TAR, GZ without extraction
- Show compressed/uncompressed sizes
- Directory structure visualization
"""

import os
import logging
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ArchivePreviewer:
    """Generate previews for archive files."""

    # Maximum number of files to list
    MAX_FILES_TO_LIST = 100

    def __init__(self):
        """Initialize archive previewer."""
        self._zipfile_available = True  # Standard library
        self._tarfile_available = True  # Standard library
        self._7z_available = False
        self._rar_available = False

        # Check if 7z is available
        try:
            result = subprocess.run(
                ['7z'],
                capture_output=True,
                text=True,
                timeout=5
            )
            self._7z_available = True
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.debug("7z not available")

        # Check if unrar is available
        try:
            result = subprocess.run(
                ['unrar'],
                capture_output=True,
                text=True,
                timeout=5
            )
            self._rar_available = True
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.debug("unrar not available")

    def is_supported(self, file_path: str) -> bool:
        """
        Check if file format is supported.

        Args:
            file_path: Path to file

        Returns:
            True if format is supported
        """
        ext = Path(file_path).suffix.lower()
        supported = {'.zip', '.7z', '.rar', '.tar', '.gz', '.bz2', '.xz', '.tgz', '.tbz2'}
        return ext in supported

    def generate_preview(self, file_path: str) -> Dict[str, Any]:
        """
        Generate archive preview.

        Args:
            file_path: Path to archive file

        Returns:
            Dictionary containing archive preview data
        """
        if not os.path.exists(file_path):
            return {'error': 'File not found'}

        ext = Path(file_path).suffix.lower()
        path = Path(file_path)

        # Handle .tar.gz, .tar.bz2, etc.
        if path.suffixes:
            ext_combo = ''.join(path.suffixes[-2:]).lower()
            if ext_combo in {'.tar.gz', '.tar.bz2', '.tar.xz'}:
                ext = ext_combo

        # Route to appropriate handler
        if ext == '.zip':
            return self._preview_zip(file_path)
        elif ext == '.7z':
            return self._preview_7z(file_path)
        elif ext == '.rar':
            return self._preview_rar(file_path)
        elif ext in {'.tar', '.tar.gz', '.tar.bz2', '.tar.xz', '.tgz', '.tbz2'}:
            return self._preview_tar(file_path, ext)
        elif ext in {'.gz', '.bz2', '.xz'}:
            return self._preview_compressed(file_path, ext)
        else:
            return {'error': 'Unsupported archive format'}

    def _preview_zip(self, file_path: str) -> Dict[str, Any]:
        """
        Preview ZIP archive.

        Args:
            file_path: Path to ZIP file

        Returns:
            Archive preview data
        """
        try:
            import zipfile

            result = {
                'type': 'zip',
                'file_size': os.path.getsize(file_path),
                'files': [],
            }

            with zipfile.ZipFile(file_path, 'r') as zf:
                info_list = zf.infolist()
                result['total_files'] = len(info_list)

                total_compressed = 0
                total_uncompressed = 0

                # List files (up to MAX_FILES_TO_LIST)
                for i, info in enumerate(info_list):
                    if i >= self.MAX_FILES_TO_LIST:
                        result['truncated'] = True
                        break

                    file_info = {
                        'filename': info.filename,
                        'compressed_size': info.compress_size,
                        'uncompressed_size': info.file_size,
                        'is_dir': info.is_dir(),
                    }

                    if info.date_time:
                        try:
                            dt = datetime(*info.date_time)
                            file_info['modified'] = dt.isoformat()
                        except Exception:
                            pass

                    result['files'].append(file_info)

                    total_compressed += info.compress_size
                    total_uncompressed += info.file_size

                result['compressed_size'] = total_compressed
                result['uncompressed_size'] = total_uncompressed

                if total_uncompressed > 0:
                    ratio = (1 - total_compressed / total_uncompressed) * 100
                    result['compression_ratio'] = f"{ratio:.1f}%"

            return result

        except Exception as e:
            logger.error(f"Error previewing ZIP: {e}")
            return {'error': str(e)}

    def _preview_7z(self, file_path: str) -> Dict[str, Any]:
        """
        Preview 7z archive using 7z command.

        Args:
            file_path: Path to 7z file

        Returns:
            Archive preview data
        """
        if not self._7z_available:
            return {'error': '7z not available'}

        try:
            result = {
                'type': '7z',
                'file_size': os.path.getsize(file_path),
                'files': [],
            }

            # Run 7z list command
            cmd = ['7z', 'l', '-slt', file_path]
            proc_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if proc_result.returncode == 0:
                # Parse output
                files = self._parse_7z_output(proc_result.stdout)
                result['files'] = files[:self.MAX_FILES_TO_LIST]
                result['total_files'] = len(files)

                if len(files) > self.MAX_FILES_TO_LIST:
                    result['truncated'] = True

                # Calculate totals
                total_compressed = sum(f.get('compressed_size', 0) for f in files)
                total_uncompressed = sum(f.get('uncompressed_size', 0) for f in files)

                result['compressed_size'] = total_compressed
                result['uncompressed_size'] = total_uncompressed

                if total_uncompressed > 0:
                    ratio = (1 - total_compressed / total_uncompressed) * 100
                    result['compression_ratio'] = f"{ratio:.1f}%"

            return result

        except Exception as e:
            logger.error(f"Error previewing 7z: {e}")
            return {'error': str(e)}

    def _preview_rar(self, file_path: str) -> Dict[str, Any]:
        """
        Preview RAR archive using unrar command.

        Args:
            file_path: Path to RAR file

        Returns:
            Archive preview data
        """
        if not self._rar_available:
            return {'error': 'unrar not available'}

        try:
            result = {
                'type': 'rar',
                'file_size': os.path.getsize(file_path),
                'files': [],
            }

            # Run unrar list command
            cmd = ['unrar', 'l', '-v', file_path]
            proc_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if proc_result.returncode == 0:
                # Parse output (simplified)
                files = self._parse_rar_output(proc_result.stdout)
                result['files'] = files[:self.MAX_FILES_TO_LIST]
                result['total_files'] = len(files)

                if len(files) > self.MAX_FILES_TO_LIST:
                    result['truncated'] = True

            return result

        except Exception as e:
            logger.error(f"Error previewing RAR: {e}")
            return {'error': str(e)}

    def _preview_tar(self, file_path: str, ext: str) -> Dict[str, Any]:
        """
        Preview TAR archive.

        Args:
            file_path: Path to TAR file
            ext: File extension

        Returns:
            Archive preview data
        """
        try:
            import tarfile

            result = {
                'type': 'tar',
                'file_size': os.path.getsize(file_path),
                'files': [],
            }

            # Determine compression mode
            if ext in {'.tar.gz', '.tgz'}:
                mode = 'r:gz'
                result['compression'] = 'gzip'
            elif ext in {'.tar.bz2', '.tbz2'}:
                mode = 'r:bz2'
                result['compression'] = 'bzip2'
            elif ext == '.tar.xz':
                mode = 'r:xz'
                result['compression'] = 'xz'
            else:
                mode = 'r'
                result['compression'] = 'none'

            with tarfile.open(file_path, mode) as tf:
                members = tf.getmembers()
                result['total_files'] = len(members)

                total_size = 0

                # List files
                for i, member in enumerate(members):
                    if i >= self.MAX_FILES_TO_LIST:
                        result['truncated'] = True
                        break

                    file_info = {
                        'filename': member.name,
                        'size': member.size,
                        'is_dir': member.isdir(),
                    }

                    if member.mtime:
                        dt = datetime.fromtimestamp(member.mtime)
                        file_info['modified'] = dt.isoformat()

                    result['files'].append(file_info)
                    total_size += member.size

                result['uncompressed_size'] = total_size

            return result

        except Exception as e:
            logger.error(f"Error previewing TAR: {e}")
            return {'error': str(e)}

    def _preview_compressed(self, file_path: str, ext: str) -> Dict[str, Any]:
        """
        Preview single-file compressed archive (gz, bz2, xz).

        Args:
            file_path: Path to compressed file
            ext: File extension

        Returns:
            Archive preview data
        """
        compression_map = {
            '.gz': 'gzip',
            '.bz2': 'bzip2',
            '.xz': 'xz',
        }

        result = {
            'type': 'compressed',
            'compression': compression_map.get(ext, 'unknown'),
            'file_size': os.path.getsize(file_path),
        }

        # Try to get original filename (for .gz files)
        if ext == '.gz':
            try:
                import gzip
                with gzip.open(file_path, 'rb') as f:
                    # Read a small chunk to verify it's valid
                    f.read(1024)
                    result['valid'] = True
            except Exception as e:
                logger.debug(f"Error reading compressed file: {e}")
                result['valid'] = False

        return result

    def _parse_7z_output(self, output: str) -> List[Dict[str, Any]]:
        """
        Parse 7z list output.

        Args:
            output: Command output

        Returns:
            List of file info dictionaries
        """
        files = []
        current_file = {}

        for line in output.splitlines():
            line = line.strip()

            if line.startswith('Path = '):
                if current_file and 'filename' in current_file:
                    files.append(current_file)
                current_file = {'filename': line[7:]}

            elif line.startswith('Size = '):
                try:
                    current_file['uncompressed_size'] = int(line[7:])
                except ValueError:
                    pass

            elif line.startswith('Packed Size = '):
                try:
                    current_file['compressed_size'] = int(line[14:])
                except ValueError:
                    pass

            elif line.startswith('Modified = '):
                current_file['modified'] = line[11:]

            elif line.startswith('Folder = '):
                current_file['is_dir'] = line[9:] == '+'

        # Add last file
        if current_file and 'filename' in current_file:
            files.append(current_file)

        return files

    def _parse_rar_output(self, output: str) -> List[Dict[str, Any]]:
        """
        Parse unrar list output (simplified).

        Args:
            output: Command output

        Returns:
            List of file info dictionaries
        """
        files = []

        # Simple parsing - look for file lines
        in_file_list = False

        for line in output.splitlines():
            line = line.strip()

            if '----------' in line:
                in_file_list = True
                continue

            if in_file_list and line:
                # Try to parse file line (format varies)
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        # Last part is usually filename
                        filename = parts[-1]
                        files.append({'filename': filename})
                    except Exception:
                        pass

        return files
