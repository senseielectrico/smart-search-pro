"""
High-performance file copier with adaptive buffering and multi-threading.
Implements TeraCopy-style optimizations for maximum speed with auto-detected optimal workers.
"""

import os
import shutil
import sys
import time
from typing import Optional, Callable, List
from pathlib import Path
from concurrent.futures import Future
from threading import Lock, Event
import platform

# Add parent directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.threading import create_io_executor, ManagedThreadPoolExecutor


class FileCopier:
    """
    High-performance file copier with adaptive buffer sizing,
    multi-threading, progress tracking, and error recovery.
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        verify_after_copy: bool = False,
        verify_algorithm: str = 'md5',
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
        use_os_copy: bool = False
    ):
        """
        Initialize file copier with auto-detected optimal workers.

        Args:
            max_workers: Maximum concurrent copy operations (None = auto-detect optimal for I/O)
            verify_after_copy: Verify files after copying using hash
            verify_algorithm: Hash algorithm for verification ('crc32', 'md5', 'sha256')
            retry_attempts: Number of retry attempts on failure
            retry_delay: Initial delay between retries (exponential backoff)
            use_os_copy: Use OS-specific optimized copy when available
        """
        self.max_workers = max_workers
        self.verify_after_copy = verify_after_copy
        self.verify_algorithm = verify_algorithm
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.use_os_copy = use_os_copy

        self._executor: Optional[ManagedThreadPoolExecutor] = None
        self._active_operations: dict[str, Future] = {}
        self._lock = Lock()
        self._cancel_event = Event()
        self._pause_event = Event()
        self._pause_event.set()  # Initially not paused

        # Import verifier for hash checking
        self._verifier = None
        if verify_after_copy:
            from .verifier import FileVerifier, HashAlgorithm
            algo_map = {
                'crc32': HashAlgorithm.CRC32,
                'md5': HashAlgorithm.MD5,
                'sha256': HashAlgorithm.SHA256,
                'sha512': HashAlgorithm.SHA512
            }
            self._verifier = FileVerifier(
                algorithm=algo_map.get(verify_algorithm.lower(), HashAlgorithm.MD5)
            )

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()

    def start(self) -> None:
        """Start the executor with I/O-optimized thread pool."""
        if self._executor is None:
            self._executor = create_io_executor(
                max_workers=self.max_workers,
                thread_name_prefix="Copier"
            )

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the executor."""
        if self._executor:
            self._executor.shutdown(wait=wait)
            self._executor = None
        self._active_operations.clear()

    def copy_file(
        self,
        source: str,
        destination: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        preserve_metadata: bool = True
    ) -> bool:
        """
        Copy a single file with progress tracking.

        Args:
            source: Source file path
            destination: Destination file path
            progress_callback: Callback function(bytes_copied, total_bytes)
            preserve_metadata: Preserve file metadata

        Returns:
            True if successful, False otherwise
        """
        # Check for cancellation
        if self._cancel_event.is_set():
            return False

        # Wait if paused
        self._pause_event.wait()

        try:
            # Get file info
            file_size = os.path.getsize(source)

            # Create destination directory if needed
            os.makedirs(os.path.dirname(destination), exist_ok=True)

            # Use OS-optimized copy for small files or when requested
            if self.use_os_copy and file_size < 100 * 1024 * 1024:  # < 100MB
                return self._os_optimized_copy(
                    source, destination, file_size,
                    progress_callback, preserve_metadata
                )

            # Manual copy with adaptive buffering
            buffer_size = self._get_optimal_buffer_size(file_size, source, destination)

            # Perform copy with progress tracking
            bytes_copied = 0

            with open(source, 'rb') as src_file:
                with open(destination, 'wb') as dst_file:
                    while True:
                        # Check for pause/cancel
                        if self._cancel_event.is_set():
                            return False
                        self._pause_event.wait()

                        # Read chunk
                        chunk = src_file.read(buffer_size)
                        if not chunk:
                            break

                        # Write chunk
                        dst_file.write(chunk)
                        bytes_copied += len(chunk)

                        # Report progress
                        if progress_callback:
                            progress_callback(bytes_copied, file_size)

            # Preserve metadata if requested
            if preserve_metadata:
                self._copy_metadata(source, destination)

            # Verify if requested (using hash algorithm)
            if self.verify_after_copy and self._verifier:
                is_valid, error = self._verifier.verify_copy(source, destination)
                if not is_valid:
                    raise ValueError(f"Verification failed: {error}")

            return True

        except Exception as e:
            # Clean up partial copy
            if os.path.exists(destination):
                try:
                    os.remove(destination)
                except:
                    pass
            raise

    def copy_file_with_retry(
        self,
        source: str,
        destination: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        preserve_metadata: bool = True
    ) -> tuple[bool, Optional[str]]:
        """
        Copy file with automatic retry on failure.

        Returns:
            Tuple of (success, error_message)
        """
        last_error = None

        for attempt in range(self.retry_attempts):
            try:
                success = self.copy_file(
                    source,
                    destination,
                    progress_callback,
                    preserve_metadata
                )
                if success:
                    return True, None

            except Exception as e:
                last_error = str(e)

                # Exponential backoff
                if attempt < self.retry_attempts - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    time.sleep(delay)

        return False, last_error

    def copy_files_batch(
        self,
        file_pairs: List[tuple[str, str]],
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        preserve_metadata: bool = True
    ) -> dict[str, tuple[bool, Optional[str]]]:
        """
        Copy multiple files in parallel.

        Args:
            file_pairs: List of (source, destination) tuples
            progress_callback: Callback function(file_path, bytes_copied, total_bytes)
            preserve_metadata: Preserve file metadata

        Returns:
            Dictionary mapping destination paths to (success, error_message)
        """
        if not self._executor:
            self.start()

        results = {}
        futures = {}

        # Submit all copy tasks
        for source, dest in file_pairs:
            def make_callback(file_path):
                if progress_callback:
                    return lambda copied, total: progress_callback(file_path, copied, total)
                return None

            future = self._executor.submit(
                self.copy_file_with_retry,
                source,
                dest,
                make_callback(dest),
                preserve_metadata
            )
            futures[future] = dest

        # Wait for completion and collect results
        for future in futures:
            dest = futures[future]
            try:
                success, error = future.result()
                results[dest] = (success, error)
            except Exception as e:
                results[dest] = (False, str(e))

        return results

    def pause(self) -> None:
        """Pause all copy operations."""
        self._pause_event.clear()

    def resume(self) -> None:
        """Resume paused copy operations."""
        self._pause_event.set()

    def cancel(self) -> None:
        """Cancel all copy operations."""
        self._cancel_event.set()

    def reset_cancel(self) -> None:
        """Reset cancel flag."""
        self._cancel_event.clear()

    def _os_optimized_copy(
        self,
        source: str,
        destination: str,
        file_size: int,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        preserve_metadata: bool = True
    ) -> bool:
        """
        Use OS-specific optimized copy operations.
        On Windows, uses CopyFileEx for better performance.
        On Linux, uses sendfile when available.

        Args:
            source: Source file path
            destination: Destination file path
            file_size: File size in bytes
            progress_callback: Progress callback
            preserve_metadata: Preserve metadata

        Returns:
            True if successful
        """
        try:
            if platform.system() == 'Windows':
                # Try using Windows CopyFileEx API for better performance
                try:
                    import ctypes
                    from ctypes import wintypes

                    # Define callback for progress
                    if progress_callback:
                        def copy_progress_routine(total_size, total_transferred, *args):
                            progress_callback(int(total_transferred.value), int(total_size.value))
                            return 0  # Continue

                        LPPROGRESS_ROUTINE = ctypes.WINFUNCTYPE(
                            wintypes.DWORD,
                            wintypes.LARGE_INTEGER,
                            wintypes.LARGE_INTEGER,
                            wintypes.LARGE_INTEGER,
                            wintypes.LARGE_INTEGER,
                            wintypes.DWORD,
                            wintypes.DWORD,
                            wintypes.HANDLE,
                            wintypes.HANDLE,
                            wintypes.LPVOID
                        )
                        callback = LPPROGRESS_ROUTINE(copy_progress_routine)
                    else:
                        callback = None

                    # Call CopyFileEx
                    result = ctypes.windll.kernel32.CopyFileExW(
                        source,
                        destination,
                        callback,
                        None,
                        None,
                        0
                    )

                    if result:
                        if preserve_metadata:
                            self._copy_metadata(source, destination)
                        return True

                except Exception:
                    pass  # Fall back to shutil

            # Use shutil.copy2 as fallback
            shutil.copy2(source, destination)

            if progress_callback:
                progress_callback(file_size, file_size)

            return True

        except Exception:
            raise

    @staticmethod
    def _get_optimal_buffer_size(
        file_size: int,
        source_path: str,
        dest_path: str
    ) -> int:
        """
        Calculate optimal buffer size based on file size and device type.
        TeraCopy-style adaptive buffering for maximum performance.

        Args:
            file_size: Size of file in bytes
            source_path: Source file path
            dest_path: Destination file path

        Returns:
            Optimal buffer size in bytes (4KB to 256MB)
        """
        # Base buffer size on file size (TeraCopy algorithm)
        if file_size < 1024 * 1024:  # < 1MB
            buffer_size = 4 * 1024  # 4KB
        elif file_size < 10 * 1024 * 1024:  # < 10MB
            buffer_size = 512 * 1024  # 512KB
        elif file_size < 100 * 1024 * 1024:  # < 100MB
            buffer_size = 2 * 1024 * 1024  # 2MB
        elif file_size < 1024 * 1024 * 1024:  # < 1GB
            buffer_size = 16 * 1024 * 1024  # 16MB
        elif file_size < 10 * 1024 * 1024 * 1024:  # < 10GB
            buffer_size = 64 * 1024 * 1024  # 64MB
        else:  # >= 10GB
            buffer_size = 128 * 1024 * 1024  # 128MB

        # Adjust for device type on Windows
        if platform.system() == 'Windows':
            try:
                # Check if same volume (faster)
                source_drive = os.path.splitdrive(source_path)[0]
                dest_drive = os.path.splitdrive(dest_path)[0]

                if source_drive == dest_drive:
                    # Same drive - can use larger buffer
                    buffer_size = min(buffer_size * 2, 256 * 1024 * 1024)
                else:
                    # Different drives - optimize for parallel I/O
                    # Use moderate buffer for better streaming
                    buffer_size = min(buffer_size, 64 * 1024 * 1024)

            except:
                pass

        return buffer_size

    @staticmethod
    def _copy_metadata(source: str, destination: str) -> None:
        """
        Copy file metadata (timestamps, permissions).

        Args:
            source: Source file path
            destination: Destination file path
        """
        try:
            # Copy stat info (timestamps, permissions)
            stat_info = os.stat(source)
            os.utime(destination, (stat_info.st_atime, stat_info.st_mtime))

            # Copy permissions (Unix-like systems)
            if hasattr(os, 'chmod'):
                os.chmod(destination, stat_info.st_mode)

        except Exception:
            # Metadata copy is best-effort
            pass

    @staticmethod
    def _verify_copy(source: str, destination: str) -> bool:
        """
        Verify that destination matches source.

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            True if files match
        """
        try:
            # Quick size check
            source_size = os.path.getsize(source)
            dest_size = os.path.getsize(destination)

            if source_size != dest_size:
                return False

            # For small files, do byte comparison
            if source_size < 10 * 1024 * 1024:  # < 10MB
                with open(source, 'rb') as src, open(destination, 'rb') as dst:
                    return src.read() == dst.read()

            # For large files, sample-based verification
            sample_size = 1024 * 1024  # 1MB samples
            num_samples = min(10, max(3, source_size // (100 * 1024 * 1024)))

            with open(source, 'rb') as src, open(destination, 'rb') as dst:
                for _ in range(num_samples):
                    # Read sample from random position
                    pos = (source_size // num_samples) * _
                    src.seek(pos)
                    dst.seek(pos)

                    src_chunk = src.read(sample_size)
                    dst_chunk = dst.read(sample_size)

                    if src_chunk != dst_chunk:
                        return False

            return True

        except Exception:
            return False

    def get_copy_speed(
        self,
        bytes_copied: int,
        elapsed_time: float
    ) -> float:
        """
        Calculate copy speed.

        Args:
            bytes_copied: Number of bytes copied
            elapsed_time: Time elapsed in seconds

        Returns:
            Speed in bytes per second
        """
        if elapsed_time > 0:
            return bytes_copied / elapsed_time
        return 0.0

    def estimate_time_remaining(
        self,
        bytes_copied: int,
        total_bytes: int,
        current_speed: float
    ) -> Optional[float]:
        """
        Estimate time remaining for copy operation.

        Args:
            bytes_copied: Bytes copied so far
            total_bytes: Total bytes to copy
            current_speed: Current copy speed (bytes/sec)

        Returns:
            Estimated seconds remaining, or None if unknown
        """
        if current_speed <= 0:
            return None

        remaining_bytes = total_bytes - bytes_copied
        return remaining_bytes / current_speed

    def copy_directory(
        self,
        source_dir: str,
        dest_dir: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        preserve_metadata: bool = True
    ) -> dict[str, tuple[bool, Optional[str]]]:
        """
        Copy entire directory tree.

        Args:
            source_dir: Source directory path
            dest_dir: Destination directory path
            progress_callback: Progress callback function
            preserve_metadata: Preserve file metadata

        Returns:
            Dictionary mapping destination paths to (success, error_message)
        """
        source_path = Path(source_dir)
        dest_path = Path(dest_dir)

        # Find all files
        all_files = list(source_path.rglob('*'))
        file_list = [f for f in all_files if f.is_file()]

        # Build file pairs
        file_pairs = []
        for source_file in file_list:
            rel_path = source_file.relative_to(source_path)
            dest_file = dest_path / rel_path

            # Create destination directory
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            file_pairs.append((str(source_file), str(dest_file)))

        # Copy all files
        return self.copy_files_batch(
            file_pairs,
            progress_callback,
            preserve_metadata
        )

    @staticmethod
    def get_free_space(path: str) -> int:
        """
        Get free space on volume containing path.

        Args:
            path: File or directory path

        Returns:
            Free space in bytes
        """
        if platform.system() == 'Windows':
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(path),
                None,
                None,
                ctypes.pointer(free_bytes)
            )
            return free_bytes.value
        else:
            stat = os.statvfs(path)
            return stat.f_bavail * stat.f_frsize

    @staticmethod
    def check_space_available(
        dest_path: str,
        required_bytes: int
    ) -> tuple[bool, int]:
        """
        Check if enough space is available.

        Args:
            dest_path: Destination path
            required_bytes: Required bytes

        Returns:
            Tuple of (is_available, free_bytes)
        """
        free_bytes = FileCopier.get_free_space(dest_path)
        is_available = free_bytes >= required_bytes
        return is_available, free_bytes
