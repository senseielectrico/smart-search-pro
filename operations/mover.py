"""
File move operations with optimizations for same-volume and cross-volume moves.
"""

import os
import shutil
from typing import Optional, Callable, List
from pathlib import Path
import platform

from .copier import FileCopier


class FileMover:
    """
    High-performance file mover.
    Uses instant rename for same-volume moves,
    copy+delete for cross-volume moves.
    """

    def __init__(
        self,
        verify_after_move: bool = False,
        delete_after_verify: bool = True,
        preserve_metadata: bool = True
    ):
        """
        Initialize file mover.

        Args:
            verify_after_move: Verify files after cross-volume move
            delete_after_verify: Only delete source after verification (cross-volume)
            preserve_metadata: Preserve file metadata
        """
        self.verify_after_move = verify_after_move
        self.delete_after_verify = delete_after_verify
        self.preserve_metadata = preserve_metadata
        self._copier: Optional[FileCopier] = None

    def move_file(
        self,
        source: str,
        destination: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Move a file with automatic optimization.

        Args:
            source: Source file path
            destination: Destination file path
            progress_callback: Callback function(bytes_copied, total_bytes)

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Create destination directory if needed
            os.makedirs(os.path.dirname(destination), exist_ok=True)

            # Check if same volume
            if self._is_same_volume(source, destination):
                # Same volume - use fast rename
                return self._move_same_volume(source, destination)
            else:
                # Cross-volume - copy then delete
                return self._move_cross_volume(
                    source,
                    destination,
                    progress_callback
                )

        except Exception as e:
            return False, str(e)

    def move_files_batch(
        self,
        file_pairs: List[tuple[str, str]],
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> dict[str, tuple[bool, Optional[str]]]:
        """
        Move multiple files.

        Args:
            file_pairs: List of (source, destination) tuples
            progress_callback: Callback function(file_path, bytes_copied, total_bytes)

        Returns:
            Dictionary mapping destination paths to (success, error_message)
        """
        results = {}

        # Separate same-volume and cross-volume moves
        same_volume_pairs = []
        cross_volume_pairs = []

        for source, dest in file_pairs:
            if self._is_same_volume(source, dest):
                same_volume_pairs.append((source, dest))
            else:
                cross_volume_pairs.append((source, dest))

        # Process same-volume moves (fast)
        for source, dest in same_volume_pairs:
            success, error = self._move_same_volume(source, dest)
            results[dest] = (success, error)

        # Process cross-volume moves (with copy)
        if cross_volume_pairs:
            if not self._copier:
                self._copier = FileCopier(
                    verify_after_copy=self.verify_after_move,
                    max_workers=4
                )

            # Copy all files
            copy_results = self._copier.copy_files_batch(
                cross_volume_pairs,
                progress_callback,
                self.preserve_metadata
            )

            # Delete source files if copy succeeded
            for dest, (success, error) in copy_results.items():
                if success:
                    # Find corresponding source
                    source = next(
                        src for src, dst in cross_volume_pairs if dst == dest
                    )

                    # Delete source file
                    try:
                        os.remove(source)
                        results[dest] = (True, None)
                    except Exception as e:
                        results[dest] = (False, f"Copy succeeded but delete failed: {str(e)}")
                else:
                    results[dest] = (success, error)

        return results

    def move_directory(
        self,
        source_dir: str,
        dest_dir: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> dict[str, tuple[bool, Optional[str]]]:
        """
        Move entire directory tree.

        Args:
            source_dir: Source directory path
            dest_dir: Destination directory path
            progress_callback: Progress callback function

        Returns:
            Dictionary mapping destination paths to (success, error_message)
        """
        source_path = Path(source_dir)
        dest_path = Path(dest_dir)

        # Check if same volume - can use fast directory rename
        if self._is_same_volume(source_dir, dest_dir):
            try:
                # Ensure parent directory exists
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                # Fast rename
                os.rename(source_dir, dest_dir)
                return {dest_dir: (True, None)}

            except Exception as e:
                # Fall back to file-by-file move
                pass

        # File-by-file move
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

        # Move all files
        results = self.move_files_batch(file_pairs, progress_callback)

        # Remove empty source directories
        try:
            for dirpath, dirnames, filenames in os.walk(source_dir, topdown=False):
                if not filenames and not dirnames:
                    os.rmdir(dirpath)
        except:
            pass

        return results

    def _move_same_volume(
        self,
        source: str,
        destination: str
    ) -> tuple[bool, Optional[str]]:
        """
        Move file on same volume using rename (instant).

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            Tuple of (success, error_message)
        """
        try:
            os.rename(source, destination)
            return True, None
        except Exception as e:
            return False, str(e)

    def _move_cross_volume(
        self,
        source: str,
        destination: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Move file across volumes using copy+delete.

        Args:
            source: Source file path
            destination: Destination file path
            progress_callback: Progress callback function

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Initialize copier if needed
            if not self._copier:
                self._copier = FileCopier(
                    verify_after_copy=self.verify_after_move
                )

            # Copy file
            success = self._copier.copy_file(
                source,
                destination,
                progress_callback,
                self.preserve_metadata
            )

            if not success:
                return False, "Copy failed"

            # Verify if requested
            if self.verify_after_move and self.delete_after_verify:
                if not self._copier._verify_copy(source, destination):
                    # Clean up destination
                    try:
                        os.remove(destination)
                    except:
                        pass
                    return False, "Verification failed"

            # Delete source
            os.remove(source)
            return True, None

        except Exception as e:
            # Clean up destination on error
            if os.path.exists(destination):
                try:
                    os.remove(destination)
                except:
                    pass
            return False, str(e)

    @staticmethod
    def _is_same_volume(path1: str, path2: str) -> bool:
        """
        Check if two paths are on the same volume.

        Args:
            path1: First path
            path2: Second path

        Returns:
            True if same volume
        """
        if platform.system() == 'Windows':
            # Compare drive letters
            drive1 = os.path.splitdrive(os.path.abspath(path1))[0]
            drive2 = os.path.splitdrive(os.path.abspath(path2))[0]
            return drive1.upper() == drive2.upper()
        else:
            # Compare device numbers (Unix-like)
            try:
                stat1 = os.stat(path1) if os.path.exists(path1) else os.stat(os.path.dirname(path1))
                stat2 = os.stat(path2) if os.path.exists(path2) else os.stat(os.path.dirname(path2))
                return stat1.st_dev == stat2.st_dev
            except:
                return False

    def pause(self) -> None:
        """Pause move operations."""
        if self._copier:
            self._copier.pause()

    def resume(self) -> None:
        """Resume move operations."""
        if self._copier:
            self._copier.resume()

    def cancel(self) -> None:
        """Cancel move operations."""
        if self._copier:
            self._copier.cancel()

    def reset_cancel(self) -> None:
        """Reset cancel flag."""
        if self._copier:
            self._copier.reset_cancel()

    def cleanup(self) -> None:
        """Cleanup resources."""
        if self._copier:
            self._copier.shutdown()
            self._copier = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()

    def calculate_total_size(self, paths: List[str]) -> int:
        """
        Calculate total size of files to move.

        Args:
            paths: List of file paths

        Returns:
            Total size in bytes
        """
        total = 0
        for path in paths:
            if os.path.isfile(path):
                total += os.path.getsize(path)
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            total += os.path.getsize(file_path)
                        except:
                            pass
        return total

    def get_move_strategy(
        self,
        source: str,
        destination: str
    ) -> str:
        """
        Determine the move strategy that will be used.

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            Strategy name: 'rename' or 'copy_delete'
        """
        if self._is_same_volume(source, destination):
            return 'rename'
        else:
            return 'copy_delete'

    def estimate_move_time(
        self,
        source: str,
        destination: str,
        average_speed: float = 100 * 1024 * 1024  # 100 MB/s default
    ) -> Optional[float]:
        """
        Estimate time required to move file.

        Args:
            source: Source file path
            destination: Destination file path
            average_speed: Average transfer speed (bytes/sec)

        Returns:
            Estimated seconds, or None for same-volume moves
        """
        if self._is_same_volume(source, destination):
            return None  # Instant rename

        try:
            file_size = os.path.getsize(source)
            return file_size / average_speed
        except:
            return None
