"""
File verification system using multiple hash algorithms.
Supports parallel verification and checksum file generation with auto-detected optimal workers.
"""

import hashlib
import os
import sys
import zlib
from typing import Optional, Dict, List, Tuple
from pathlib import Path
from concurrent.futures import as_completed
from enum import Enum

# Add parent directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.threading import create_cpu_executor


class HashAlgorithm(Enum):
    """Supported hash algorithms."""
    CRC32 = "crc32"
    MD5 = "md5"
    SHA256 = "sha256"
    SHA512 = "sha512"

    # xxHash support (optional, faster but requires package)
    XXHASH64 = "xxhash64"


class FileVerifier:
    """
    High-performance file verification using hash algorithms.
    Supports parallel verification for multiple files.
    """

    def __init__(
        self,
        algorithm: HashAlgorithm = HashAlgorithm.MD5,
        buffer_size: int = 64 * 1024 * 1024  # 64MB default
    ):
        """
        Initialize file verifier.

        Args:
            algorithm: Hash algorithm to use
            buffer_size: Buffer size for reading files (default 64MB)
        """
        self.algorithm = algorithm
        self.buffer_size = buffer_size
        self._xxhash_available = False

        # Check if xxhash is available
        try:
            import xxhash
            self._xxhash_available = True
            self._xxhash = xxhash
        except ImportError:
            if algorithm == HashAlgorithm.XXHASH64:
                raise ImportError(
                    "xxhash package required for XXHASH64. "
                    "Install with: pip install xxhash"
                )

    def calculate_hash(self, file_path: str) -> str:
        """
        Calculate hash of a file.

        Args:
            file_path: Path to file

        Returns:
            Hash string (hex for most algorithms, integer for CRC32)
        """
        if self.algorithm == HashAlgorithm.CRC32:
            return self._calculate_crc32(file_path)
        elif self.algorithm == HashAlgorithm.XXHASH64 and self._xxhash_available:
            return self._calculate_xxhash64(file_path)
        else:
            return self._calculate_hashlib(file_path)

    def _calculate_crc32(self, file_path: str) -> str:
        """Calculate CRC32 checksum."""
        crc = 0
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(self.buffer_size)
                if not chunk:
                    break
                crc = zlib.crc32(chunk, crc)
        return f"{crc & 0xFFFFFFFF:08x}"

    def _calculate_xxhash64(self, file_path: str) -> str:
        """Calculate xxHash64 (if available)."""
        hasher = self._xxhash.xxh64()
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(self.buffer_size)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()

    def _calculate_hashlib(self, file_path: str) -> str:
        """Calculate hash using hashlib (MD5, SHA256, SHA512)."""
        if self.algorithm == HashAlgorithm.MD5:
            hasher = hashlib.md5()
        elif self.algorithm == HashAlgorithm.SHA256:
            hasher = hashlib.sha256()
        elif self.algorithm == HashAlgorithm.SHA512:
            hasher = hashlib.sha512()
        else:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")

        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(self.buffer_size)
                if not chunk:
                    break
                hasher.update(chunk)

        return hasher.hexdigest()

    def verify_copy(
        self,
        source_path: str,
        dest_path: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify that destination is exact copy of source.

        Args:
            source_path: Source file path
            dest_path: Destination file path

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Quick size check first
            source_size = os.path.getsize(source_path)
            dest_size = os.path.getsize(dest_path)

            if source_size != dest_size:
                return False, f"Size mismatch: {source_size} vs {dest_size}"

            # Calculate hashes
            source_hash = self.calculate_hash(source_path)
            dest_hash = self.calculate_hash(dest_path)

            if source_hash != dest_hash:
                return False, f"Hash mismatch: {source_hash} vs {dest_hash}"

            return True, None

        except Exception as e:
            return False, f"Verification error: {str(e)}"

    def verify_batch(
        self,
        file_pairs: List[Tuple[str, str]],
        max_workers: Optional[int] = None
    ) -> Dict[str, Tuple[bool, Optional[str]]]:
        """
        Verify multiple file copies in parallel with CPU-optimized threading.

        Args:
            file_pairs: List of (source, destination) tuples
            max_workers: Maximum worker threads (None = auto-detect optimal for CPU)

        Returns:
            Dictionary mapping destination paths to (is_valid, error_message)
        """
        results = {}

        # Use CPU-optimized executor (hash verification is CPU-bound)
        with create_cpu_executor(max_workers=max_workers, thread_name_prefix="Verifier") as executor:
            # Submit all verification tasks
            future_to_dest = {
                executor.submit(self.verify_copy, src, dst): dst
                for src, dst in file_pairs
            }

            # Collect results as they complete
            for future in as_completed(future_to_dest):
                dest = future_to_dest[future]
                try:
                    is_valid, error = future.result()
                    results[dest] = (is_valid, error)
                except Exception as e:
                    results[dest] = (False, f"Verification exception: {str(e)}")

        return results

    def generate_checksum_file(
        self,
        file_paths: List[str],
        output_path: str,
        format: str = 'md5sum'
    ) -> None:
        """
        Generate checksum file for multiple files.

        Args:
            file_paths: List of file paths
            output_path: Output checksum file path
            format: Format ('md5sum', 'sha256sum', or 'simple')
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            for file_path in file_paths:
                try:
                    hash_value = self.calculate_hash(file_path)
                    file_name = os.path.basename(file_path)

                    if format in ('md5sum', 'sha256sum'):
                        # Format: hash *filename
                        f.write(f"{hash_value} *{file_name}\n")
                    else:
                        # Simple format: filename: hash
                        f.write(f"{file_name}: {hash_value}\n")

                except Exception as e:
                    # Write error to checksum file
                    f.write(f"# Error processing {file_path}: {str(e)}\n")

    def verify_checksum_file(
        self,
        checksum_file: str,
        base_dir: Optional[str] = None
    ) -> Dict[str, Tuple[bool, Optional[str]]]:
        """
        Verify files against a checksum file.

        Args:
            checksum_file: Path to checksum file
            base_dir: Base directory for relative paths (defaults to checksum file dir)

        Returns:
            Dictionary mapping file paths to (is_valid, error_message)
        """
        if base_dir is None:
            base_dir = os.path.dirname(checksum_file)

        results = {}

        try:
            with open(checksum_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue

                    # Parse line
                    if ' *' in line:
                        # md5sum/sha256sum format
                        expected_hash, file_name = line.split(' *', 1)
                    elif ': ' in line:
                        # Simple format
                        file_name, expected_hash = line.split(': ', 1)
                    else:
                        continue

                    # Get full path
                    file_path = os.path.join(base_dir, file_name)

                    # Verify file
                    if not os.path.exists(file_path):
                        results[file_name] = (False, "File not found")
                        continue

                    try:
                        actual_hash = self.calculate_hash(file_path)
                        if actual_hash == expected_hash.strip():
                            results[file_name] = (True, None)
                        else:
                            results[file_name] = (
                                False,
                                f"Hash mismatch: expected {expected_hash}, got {actual_hash}"
                            )
                    except Exception as e:
                        results[file_name] = (False, f"Error: {str(e)}")

        except Exception as e:
            raise ValueError(f"Error reading checksum file: {str(e)}")

        return results

    def compare_directories(
        self,
        source_dir: str,
        dest_dir: str,
        recursive: bool = True,
        max_workers: Optional[int] = None
    ) -> Dict[str, Tuple[bool, Optional[str]]]:
        """
        Compare all files in two directories.

        Args:
            source_dir: Source directory
            dest_dir: Destination directory
            recursive: Include subdirectories
            max_workers: Maximum worker threads

        Returns:
            Dictionary mapping relative paths to (is_valid, error_message)
        """
        source_path = Path(source_dir)
        dest_path = Path(dest_dir)

        # Find all files
        if recursive:
            source_files = list(source_path.rglob('*'))
        else:
            source_files = list(source_path.glob('*'))

        # Filter to files only
        source_files = [f for f in source_files if f.is_file()]

        # Build file pairs
        file_pairs = []
        for source_file in source_files:
            rel_path = source_file.relative_to(source_path)
            dest_file = dest_path / rel_path

            if dest_file.exists():
                file_pairs.append((str(source_file), str(dest_file)))

        # Verify all pairs
        results = self.verify_batch(file_pairs, max_workers)

        # Convert to relative paths
        relative_results = {}
        for dest_full_path, result in results.items():
            rel_path = str(Path(dest_full_path).relative_to(dest_path))
            relative_results[rel_path] = result

        return relative_results

    def get_file_info(self, file_path: str) -> Dict:
        """
        Get detailed file information including hash.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file information
        """
        info = {
            'path': file_path,
            'exists': os.path.exists(file_path),
        }

        if info['exists']:
            try:
                stat = os.stat(file_path)
                info['size'] = stat.st_size
                info['mtime'] = stat.st_mtime
                info['hash'] = self.calculate_hash(file_path)
                info['algorithm'] = self.algorithm.value
            except Exception as e:
                info['error'] = str(e)

        return info

    @staticmethod
    def get_optimal_buffer_size(file_size: int) -> int:
        """
        Get optimal buffer size based on file size.

        Args:
            file_size: File size in bytes

        Returns:
            Optimal buffer size in bytes
        """
        if file_size < 1024 * 1024:  # < 1MB
            return 4 * 1024  # 4KB
        elif file_size < 100 * 1024 * 1024:  # < 100MB
            return 1024 * 1024  # 1MB
        elif file_size < 1024 * 1024 * 1024:  # < 1GB
            return 8 * 1024 * 1024  # 8MB
        else:  # >= 1GB
            return 64 * 1024 * 1024  # 64MB
