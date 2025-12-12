"""
7-Zip Manager - Complete wrapper for 7z.exe
Handles all archive operations with full format support
"""

import os
import subprocess
import shutil
import re
from pathlib import Path
from typing import Optional, List, Callable, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
import threading


class CompressionLevel(Enum):
    """Compression levels for archive creation"""
    STORE = 0  # No compression
    FASTEST = 1
    FAST = 3
    NORMAL = 5
    MAXIMUM = 7
    ULTRA = 9


class ArchiveFormat(Enum):
    """Supported archive formats"""
    SEVEN_ZIP = '7z'
    ZIP = 'zip'
    TAR = 'tar'
    GZIP = 'gzip'
    BZIP2 = 'bzip2'
    XZ = 'xz'
    WIM = 'wim'
    ISO = 'iso'
    CAB = 'cab'
    RAR = 'rar'


@dataclass
class ExtractionProgress:
    """Progress information for extraction"""
    current_file: str = ""
    total_files: int = 0
    processed_files: int = 0
    total_bytes: int = 0
    processed_bytes: int = 0
    percentage: float = 0.0
    speed_mbps: float = 0.0
    cancelled: bool = False


class SevenZipManager:
    """
    Complete 7-Zip wrapper with all features:
    - Multi-format support (7z, zip, rar, tar, gz, bz2, xz, iso, cab, wim, etc.)
    - Extract archives with progress tracking
    - Create archives with compression levels
    - List contents without extraction
    - Test archive integrity
    - Password-protected archives
    - Split archives support
    - Extract specific files/folders
    """

    # Supported archive extensions
    ARCHIVE_EXTENSIONS = {
        '.7z', '.zip', '.rar', '.tar', '.gz', '.bz2', '.xz', '.iso',
        '.cab', '.wim', '.arj', '.chm', '.deb', '.dmg', '.hfs', '.lzh',
        '.lzma', '.msi', '.nsis', '.rpm', '.udf', '.vhd', '.z', '.001',
        '.tgz', '.tbz2', '.txz', '.tar.gz', '.tar.bz2', '.tar.xz'
    }

    def __init__(self):
        """Initialize 7-Zip manager and detect 7z.exe location"""
        self.seven_zip_path = self._detect_seven_zip()
        if not self.seven_zip_path:
            raise FileNotFoundError(
                "7-Zip not found. Please install 7-Zip or ensure 7z.exe is in PATH"
            )

        self._cancel_flag = threading.Event()
        self._lock = threading.Lock()

    def _detect_seven_zip(self) -> Optional[str]:
        """
        Detect 7z.exe location in common paths

        Returns:
            Path to 7z.exe or None if not found
        """
        # Check common installation paths
        common_paths = [
            r'C:\Program Files\7-Zip\7z.exe',
            r'C:\Program Files (x86)\7-Zip\7z.exe',
        ]

        for path in common_paths:
            if os.path.isfile(path):
                return path

        # Check PATH environment
        seven_zip_in_path = shutil.which('7z')
        if seven_zip_in_path:
            return seven_zip_in_path

        # Check bundled version (if included with application)
        bundled_path = Path(__file__).parent.parent / 'bin' / '7z.exe'
        if bundled_path.is_file():
            return str(bundled_path)

        return None

    def is_archive(self, file_path: str) -> bool:
        """
        Check if file is a supported archive

        Args:
            file_path: Path to file

        Returns:
            True if file is an archive
        """
        path = Path(file_path)

        # Check double extensions like .tar.gz
        if len(path.suffixes) >= 2:
            double_ext = ''.join(path.suffixes[-2:]).lower()
            if double_ext in self.ARCHIVE_EXTENSIONS:
                return True

        # Check single extension
        return path.suffix.lower() in self.ARCHIVE_EXTENSIONS

    def list_contents(
        self,
        archive_path: str,
        password: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """
        List archive contents without extracting

        Args:
            archive_path: Path to archive
            password: Password for encrypted archives

        Returns:
            List of file entries with metadata
        """
        cmd = [self.seven_zip_path, 'l', '-slt', archive_path]

        if password:
            cmd.extend([f'-p{password}'])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            return self._parse_list_output(result.stdout)

        except subprocess.CalledProcessError as e:
            if 'Wrong password' in e.stderr or 'Cannot open encrypted archive' in e.stderr:
                raise ValueError("Wrong password or archive is encrypted")
            raise RuntimeError(f"Failed to list archive: {e.stderr}")

    def _parse_list_output(self, output: str) -> List[Dict[str, any]]:
        """Parse 7z list output into structured data"""
        entries = []
        current_entry = {}

        for line in output.split('\n'):
            line = line.strip()

            if line.startswith('Path = ') and current_entry:
                # New entry starts
                if current_entry.get('Path'):
                    entries.append(current_entry)
                current_entry = {}

            if ' = ' in line:
                key, value = line.split(' = ', 1)
                key = key.strip()
                value = value.strip()

                if key == 'Size':
                    current_entry['Size'] = int(value) if value.isdigit() else 0
                elif key == 'Packed Size':
                    current_entry['PackedSize'] = int(value) if value.isdigit() else 0
                elif key == 'Attributes':
                    current_entry['IsDirectory'] = 'D' in value
                    current_entry['Attributes'] = value
                else:
                    current_entry[key] = value

        # Add last entry
        if current_entry.get('Path'):
            entries.append(current_entry)

        return entries

    def extract(
        self,
        archive_path: str,
        destination: str,
        password: Optional[str] = None,
        files: Optional[List[str]] = None,
        overwrite: bool = True,
        progress_callback: Optional[Callable[[ExtractionProgress], None]] = None
    ) -> bool:
        """
        Extract archive with progress tracking

        Args:
            archive_path: Path to archive
            destination: Extraction destination
            password: Password for encrypted archives
            files: Specific files to extract (None = all)
            overwrite: Overwrite existing files
            progress_callback: Progress callback function

        Returns:
            True if successful
        """
        self._cancel_flag.clear()

        # Ensure destination exists
        os.makedirs(destination, exist_ok=True)

        # Build command
        cmd = [self.seven_zip_path, 'x', archive_path, f'-o{destination}']

        if password:
            cmd.append(f'-p{password}')

        if overwrite:
            cmd.append('-aoa')  # Overwrite all
        else:
            cmd.append('-aos')  # Skip existing

        # Add specific files if requested
        if files:
            cmd.extend(files)

        # Progress tracking
        if progress_callback:
            return self._extract_with_progress(cmd, progress_callback)
        else:
            return self._extract_simple(cmd)

    def _extract_simple(self, cmd: List[str]) -> bool:
        """Simple extraction without progress"""
        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            return True
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Extraction failed: {e.stderr.decode()}")

    def _extract_with_progress(
        self,
        cmd: List[str],
        progress_callback: Callable[[ExtractionProgress], None]
    ) -> bool:
        """Extract with progress tracking"""
        progress = ExtractionProgress()

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            # Parse output for progress
            for line in process.stdout:
                if self._cancel_flag.is_set():
                    process.terminate()
                    progress.cancelled = True
                    progress_callback(progress)
                    return False

                # Parse progress from 7z output
                self._update_progress_from_line(line, progress)
                progress_callback(progress)

            process.wait()

            if process.returncode == 0:
                progress.percentage = 100.0
                progress_callback(progress)
                return True
            else:
                raise RuntimeError(f"Extraction failed with code {process.returncode}")

        except Exception as e:
            raise RuntimeError(f"Extraction error: {str(e)}")

    def _update_progress_from_line(self, line: str, progress: ExtractionProgress):
        """Update progress from 7z output line"""
        line = line.strip()

        # Match: "- filename.txt"
        if line.startswith('- '):
            progress.current_file = line[2:]
            progress.processed_files += 1

        # Match percentage: "50%"
        percent_match = re.search(r'(\d+)%', line)
        if percent_match:
            progress.percentage = float(percent_match.group(1))

    def create_archive(
        self,
        archive_path: str,
        source_paths: List[str],
        format: ArchiveFormat = ArchiveFormat.SEVEN_ZIP,
        compression_level: CompressionLevel = CompressionLevel.NORMAL,
        password: Optional[str] = None,
        split_size: Optional[str] = None,
        progress_callback: Optional[Callable[[ExtractionProgress], None]] = None
    ) -> bool:
        """
        Create archive with compression

        Args:
            archive_path: Output archive path
            source_paths: Files/folders to archive
            format: Archive format
            compression_level: Compression level
            password: Password for encryption
            split_size: Split archive size (e.g., '100m', '1g')
            progress_callback: Progress callback

        Returns:
            True if successful
        """
        cmd = [
            self.seven_zip_path,
            'a',
            f'-t{format.value}',
            f'-mx={compression_level.value}',
            archive_path
        ]

        if password:
            cmd.append(f'-p{password}')
            cmd.append('-mhe=on')  # Encrypt headers

        if split_size:
            cmd.append(f'-v{split_size}')

        cmd.extend(source_paths)

        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            return True
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Archive creation failed: {e.stderr.decode()}")

    def test_archive(
        self,
        archive_path: str,
        password: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Test archive integrity

        Args:
            archive_path: Path to archive
            password: Password for encrypted archives

        Returns:
            (success, message)
        """
        cmd = [self.seven_zip_path, 't', archive_path]

        if password:
            cmd.append(f'-p{password}')

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            if 'Everything is Ok' in result.stdout:
                return True, "Archive is valid"
            else:
                return False, "Archive test failed"

        except subprocess.CalledProcessError as e:
            return False, f"Test failed: {e.stderr}"

    def cancel_extraction(self):
        """Cancel ongoing extraction"""
        self._cancel_flag.set()

    def get_archive_info(self, archive_path: str) -> Dict[str, any]:
        """
        Get archive metadata

        Args:
            archive_path: Path to archive

        Returns:
            Archive information
        """
        entries = self.list_contents(archive_path)

        total_size = sum(e.get('Size', 0) for e in entries)
        packed_size = sum(e.get('PackedSize', 0) for e in entries)
        file_count = sum(1 for e in entries if not e.get('IsDirectory', False))
        folder_count = sum(1 for e in entries if e.get('IsDirectory', False))

        compression_ratio = 0
        if total_size > 0:
            compression_ratio = (1 - (packed_size / total_size)) * 100

        return {
            'total_size': total_size,
            'packed_size': packed_size,
            'file_count': file_count,
            'folder_count': folder_count,
            'compression_ratio': compression_ratio,
            'entries': entries
        }

    def extract_to_temp(
        self,
        archive_path: str,
        password: Optional[str] = None
    ) -> str:
        """
        Extract archive to temporary directory

        Args:
            archive_path: Path to archive
            password: Password for encrypted archives

        Returns:
            Path to temporary extraction directory
        """
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix='smart_search_archive_')

        try:
            self.extract(archive_path, temp_dir, password=password)
            return temp_dir
        except Exception as e:
            # Cleanup on failure
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise e

    @staticmethod
    def cleanup_temp_dir(temp_dir: str):
        """Clean up temporary extraction directory"""
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
