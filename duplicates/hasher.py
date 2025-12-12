"""
Hash computation module with multiple algorithms and optimization.

Supports:
- Multiple hash algorithms (MD5, SHA-1, SHA-256, xxHash, BLAKE3)
- Quick hashing (first/last chunks) for fast comparison
- Chunked reading for large files
- Multi-threaded hashing with auto-detected optimal workers
- Progress callbacks
"""

import hashlib
import os
import sys
from concurrent.futures import as_completed
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional, Union

# Add parent directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.threading import create_cpu_executor

try:
    import xxhash
    HAS_XXHASH = True
except ImportError:
    HAS_XXHASH = False

try:
    import blake3
    HAS_BLAKE3 = True
except ImportError:
    HAS_BLAKE3 = False


class HashAlgorithm(Enum):
    """Supported hash algorithms."""
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    XXHASH = "xxhash64"
    BLAKE3 = "blake3"


@dataclass
class HashResult:
    """Result of a hash computation."""
    file_path: Path
    quick_hash: Optional[str] = None  # Hash of first/last chunks
    full_hash: Optional[str] = None   # Hash of entire file
    algorithm: HashAlgorithm = HashAlgorithm.SHA256
    file_size: int = 0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        """Check if hashing was successful."""
        return self.error is None

    def __repr__(self) -> str:
        if self.error:
            return f"HashResult(path={self.file_path}, error={self.error})"
        return f"HashResult(path={self.file_path}, quick={self.quick_hash[:8]}..., full={self.full_hash[:8] if self.full_hash else 'None'}...)"


class FileHasher:
    """
    High-performance file hasher with multiple algorithms and optimization.

    Features:
    - Quick hash: Hash first/last 8KB for fast filtering
    - Full hash: Hash entire file for definitive comparison
    - Chunked reading: Memory-efficient for large files
    - Multi-threaded: Process multiple files concurrently
    - Progress callbacks: Report progress during operations

    Example:
        >>> hasher = FileHasher(algorithm=HashAlgorithm.SHA256, chunk_size=8192)
        >>> result = hasher.hash_file('/path/to/file.txt', full_hash=True)
        >>> print(f"Quick: {result.quick_hash}, Full: {result.full_hash}")
    """

    # Default chunk sizes
    QUICK_HASH_CHUNK_SIZE = 8192  # 8KB for quick hash
    DEFAULT_CHUNK_SIZE = 65536     # 64KB for full hash

    def __init__(
        self,
        algorithm: HashAlgorithm = HashAlgorithm.SHA256,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        max_workers: Optional[int] = None
    ):
        """
        Initialize the file hasher.

        Args:
            algorithm: Hash algorithm to use
            chunk_size: Size of chunks for reading files (bytes)
            max_workers: Maximum number of worker threads (None = auto-detect optimal)
        """
        self.algorithm = algorithm
        self.chunk_size = chunk_size
        self.max_workers = max_workers  # None = auto-detect in batch operations
        self._validate_algorithm()

    def _validate_algorithm(self) -> None:
        """Validate that the selected algorithm is available."""
        if self.algorithm == HashAlgorithm.XXHASH and not HAS_XXHASH:
            raise ImportError("xxhash not available. Install with: pip install xxhash")

        if self.algorithm == HashAlgorithm.BLAKE3 and not HAS_BLAKE3:
            raise ImportError("blake3 not available. Install with: pip install blake3")

    def _create_hasher(self):
        """Create a new hasher instance based on the algorithm."""
        if self.algorithm == HashAlgorithm.MD5:
            return hashlib.md5()
        elif self.algorithm == HashAlgorithm.SHA1:
            return hashlib.sha1()
        elif self.algorithm == HashAlgorithm.SHA256:
            return hashlib.sha256()
        elif self.algorithm == HashAlgorithm.XXHASH:
            return xxhash.xxh64()
        elif self.algorithm == HashAlgorithm.BLAKE3:
            return blake3.blake3()
        else:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")

    def compute_quick_hash(self, file_path: Union[str, Path]) -> Optional[str]:
        """
        Compute quick hash of first and last chunks.

        This is much faster than full hash and eliminates most non-duplicates.

        Args:
            file_path: Path to the file

        Returns:
            Hex digest of the quick hash, or None on error
        """
        try:
            path = Path(file_path)
            size = path.stat().st_size

            # For small files, use full content
            if size <= self.QUICK_HASH_CHUNK_SIZE * 2:
                with open(path, 'rb') as f:
                    data = f.read()
                hasher = self._create_hasher()
                hasher.update(data)
                return hasher.hexdigest()

            # For larger files, hash first and last chunks
            hasher = self._create_hasher()

            with open(path, 'rb') as f:
                # First chunk
                first_chunk = f.read(self.QUICK_HASH_CHUNK_SIZE)
                hasher.update(first_chunk)

                # Last chunk
                f.seek(-self.QUICK_HASH_CHUNK_SIZE, os.SEEK_END)
                last_chunk = f.read(self.QUICK_HASH_CHUNK_SIZE)
                hasher.update(last_chunk)

            return hasher.hexdigest()

        except (OSError, IOError) as e:
            return None

    def compute_full_hash(
        self,
        file_path: Union[str, Path],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Optional[str]:
        """
        Compute full hash of entire file.

        Uses chunked reading for memory efficiency.

        Args:
            file_path: Path to the file
            progress_callback: Optional callback(bytes_read, total_bytes)

        Returns:
            Hex digest of the full hash, or None on error
        """
        try:
            path = Path(file_path)
            size = path.stat().st_size
            hasher = self._create_hasher()
            bytes_read = 0

            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break

                    hasher.update(chunk)
                    bytes_read += len(chunk)

                    if progress_callback:
                        progress_callback(bytes_read, size)

            return hasher.hexdigest()

        except (OSError, IOError) as e:
            return None

    def hash_file(
        self,
        file_path: Union[str, Path],
        quick_hash: bool = True,
        full_hash: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> HashResult:
        """
        Hash a file with optional quick and/or full hash.

        Args:
            file_path: Path to the file
            quick_hash: Compute quick hash (first/last chunks)
            full_hash: Compute full hash (entire file)
            progress_callback: Optional callback(bytes_read, total_bytes)

        Returns:
            HashResult with computed hashes
        """
        path = Path(file_path)
        result = HashResult(
            file_path=path,
            algorithm=self.algorithm
        )

        try:
            result.file_size = path.stat().st_size

            if quick_hash:
                result.quick_hash = self.compute_quick_hash(path)

            if full_hash:
                result.full_hash = self.compute_full_hash(path, progress_callback)

        except Exception as e:
            result.error = str(e)

        return result

    def hash_files_batch(
        self,
        file_paths: list[Union[str, Path]],
        quick_hash: bool = True,
        full_hash: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> list[HashResult]:
        """
        Hash multiple files concurrently using optimized thread pool.

        Args:
            file_paths: List of file paths to hash
            quick_hash: Compute quick hash for each file
            full_hash: Compute full hash for each file
            progress_callback: Optional callback(completed, total)

        Returns:
            List of HashResult objects
        """
        results = []
        total = len(file_paths)
        completed = 0

        # Use CPU-optimized executor (hashing is CPU-bound)
        with create_cpu_executor(max_workers=self.max_workers, thread_name_prefix="Hasher") as executor:
            # Submit all tasks
            future_to_path = {
                executor.submit(self.hash_file, path, quick_hash, full_hash): path
                for path in file_paths
            }

            # Collect results as they complete
            for future in as_completed(future_to_path):
                result = future.result()
                results.append(result)
                completed += 1

                if progress_callback:
                    progress_callback(completed, total)

        return results

    @staticmethod
    def compare_files_bytewise(
        file1: Union[str, Path],
        file2: Union[str, Path],
        chunk_size: int = DEFAULT_CHUNK_SIZE
    ) -> bool:
        """
        Compare two files byte-by-byte.

        This is the ultimate verification method but slower than hash comparison.
        Use this only when absolute certainty is required.

        Args:
            file1: First file path
            file2: Second file path
            chunk_size: Size of chunks for comparison

        Returns:
            True if files are identical, False otherwise
        """
        try:
            path1 = Path(file1)
            path2 = Path(file2)

            # Quick size check
            if path1.stat().st_size != path2.stat().st_size:
                return False

            # Byte-by-byte comparison
            with open(path1, 'rb') as f1, open(path2, 'rb') as f2:
                while True:
                    chunk1 = f1.read(chunk_size)
                    chunk2 = f2.read(chunk_size)

                    if chunk1 != chunk2:
                        return False

                    if not chunk1:  # End of file
                        break

            return True

        except (OSError, IOError):
            return False


def hash_file_simple(
    file_path: Union[str, Path],
    algorithm: HashAlgorithm = HashAlgorithm.SHA256
) -> Optional[str]:
    """
    Convenience function to quickly hash a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use

    Returns:
        Hex digest of the file hash, or None on error
    """
    hasher = FileHasher(algorithm=algorithm)
    result = hasher.hash_file(file_path, quick_hash=False, full_hash=True)
    return result.full_hash if result.success else None
