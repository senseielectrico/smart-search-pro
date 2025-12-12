"""
Recursive Archive Extractor
Handles nested archives with unlimited depth and circular reference protection
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import Optional, Set, Callable, Dict, List
from dataclasses import dataclass
import threading

from .sevenzip_manager import SevenZipManager, ExtractionProgress


@dataclass
class RecursiveProgress:
    """Progress for recursive extraction"""
    current_archive: str = ""
    current_depth: int = 0
    total_archives: int = 0
    processed_archives: int = 0
    total_files_extracted: int = 0
    current_file: str = ""
    percentage: float = 0.0


class RecursiveExtractor:
    """
    Recursively extract nested archives with features:
    - Unlimited depth (configurable max)
    - Detect archives inside archives
    - Handle circular references
    - Memory-efficient streaming
    - Preserve directory structure
    - Option to flatten output
    - Automatic cleanup of temporary files
    """

    def __init__(self, max_depth: int = 10):
        """
        Initialize recursive extractor

        Args:
            max_depth: Maximum recursion depth (default: 10)
        """
        self.max_depth = max_depth
        self.seven_zip = SevenZipManager()
        self._processed_hashes: Set[str] = set()
        self._temp_dirs: List[str] = []
        self._lock = threading.Lock()

    def extract_recursive(
        self,
        archive_path: str,
        destination: str,
        password: Optional[str] = None,
        flatten: bool = False,
        preserve_structure: bool = True,
        progress_callback: Optional[Callable[[RecursiveProgress], None]] = None
    ) -> Dict[str, any]:
        """
        Recursively extract archive and all nested archives

        Args:
            archive_path: Path to archive
            destination: Final extraction destination
            password: Password for encrypted archives
            flatten: Flatten all files into destination
            preserve_structure: Preserve directory structure
            progress_callback: Progress callback

        Returns:
            Extraction statistics
        """
        # Reset state
        self._processed_hashes.clear()
        self._temp_dirs.clear()

        progress = RecursiveProgress()
        progress.current_archive = os.path.basename(archive_path)

        # Ensure destination exists
        os.makedirs(destination, exist_ok=True)

        try:
            stats = self._extract_recursive_internal(
                archive_path=archive_path,
                destination=destination,
                password=password,
                flatten=flatten,
                preserve_structure=preserve_structure,
                current_depth=0,
                progress=progress,
                progress_callback=progress_callback
            )

            # Final cleanup
            self._cleanup_temp_dirs()

            return stats

        except Exception as e:
            # Cleanup on error
            self._cleanup_temp_dirs()
            raise e

    def _extract_recursive_internal(
        self,
        archive_path: str,
        destination: str,
        password: Optional[str],
        flatten: bool,
        preserve_structure: bool,
        current_depth: int,
        progress: RecursiveProgress,
        progress_callback: Optional[Callable[[RecursiveProgress], None]]
    ) -> Dict[str, any]:
        """Internal recursive extraction logic"""

        # Check depth limit
        if current_depth >= self.max_depth:
            return {
                'archives_extracted': 0,
                'files_extracted': 0,
                'depth_reached': current_depth,
                'skipped_depth_limit': True
            }

        # Check for circular reference
        archive_hash = self._compute_file_hash(archive_path)
        if archive_hash in self._processed_hashes:
            return {
                'archives_extracted': 0,
                'files_extracted': 0,
                'depth_reached': current_depth,
                'circular_reference': True
            }

        self._processed_hashes.add(archive_hash)

        # Update progress
        progress.current_depth = current_depth
        progress.total_archives += 1

        # Extract this archive
        temp_extract_dir = self._create_temp_dir()

        try:
            # Extract current archive
            def extract_progress(ep: ExtractionProgress):
                progress.current_file = ep.current_file
                if progress_callback:
                    progress_callback(progress)

            self.seven_zip.extract(
                archive_path=archive_path,
                destination=temp_extract_dir,
                password=password,
                progress_callback=extract_progress
            )

            progress.processed_archives += 1
            if progress_callback:
                progress_callback(progress)

            # Find nested archives
            nested_archives = self._find_archives(temp_extract_dir)

            # Statistics
            stats = {
                'archives_extracted': 1,
                'files_extracted': 0,
                'nested_archives': len(nested_archives),
                'depth_reached': current_depth,
                'total_size': 0
            }

            # Recursively extract nested archives
            for nested_archive in nested_archives:
                nested_stats = self._extract_recursive_internal(
                    archive_path=nested_archive,
                    destination=temp_extract_dir if not flatten else destination,
                    password=password,
                    flatten=flatten,
                    preserve_structure=preserve_structure,
                    current_depth=current_depth + 1,
                    progress=progress,
                    progress_callback=progress_callback
                )

                # Aggregate stats
                stats['archives_extracted'] += nested_stats.get('archives_extracted', 0)
                stats['files_extracted'] += nested_stats.get('files_extracted', 0)
                stats['depth_reached'] = max(
                    stats['depth_reached'],
                    nested_stats.get('depth_reached', current_depth)
                )

                # Remove nested archive after extraction
                try:
                    os.remove(nested_archive)
                except:
                    pass

            # Move/copy files to final destination
            if current_depth == 0:  # Only for top-level
                self._move_to_destination(
                    temp_extract_dir,
                    destination,
                    flatten,
                    preserve_structure
                )

                # Count files
                file_count = sum(1 for _ in Path(destination).rglob('*') if _.is_file())
                stats['files_extracted'] = file_count

                # Calculate total size
                total_size = sum(
                    f.stat().st_size for f in Path(destination).rglob('*') if f.is_file()
                )
                stats['total_size'] = total_size

            return stats

        except Exception as e:
            raise RuntimeError(f"Recursive extraction failed at depth {current_depth}: {str(e)}")

    def _find_archives(self, directory: str) -> List[str]:
        """Find all archives in directory (non-recursive)"""
        archives = []

        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if self.seven_zip.is_archive(file_path):
                    archives.append(file_path)

        return archives

    def _move_to_destination(
        self,
        source_dir: str,
        destination: str,
        flatten: bool,
        preserve_structure: bool
    ):
        """Move extracted files to final destination"""

        if flatten:
            # Flatten: move all files to destination root
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    src = os.path.join(root, file)
                    dst = os.path.join(destination, file)

                    # Handle name conflicts
                    counter = 1
                    base, ext = os.path.splitext(file)
                    while os.path.exists(dst):
                        dst = os.path.join(destination, f"{base}_{counter}{ext}")
                        counter += 1

                    shutil.move(src, dst)

        elif preserve_structure:
            # Preserve structure: move entire directory tree
            for item in os.listdir(source_dir):
                src = os.path.join(source_dir, item)
                dst = os.path.join(destination, item)

                if os.path.exists(dst):
                    if os.path.isdir(dst) and os.path.isdir(src):
                        # Merge directories
                        self._merge_directories(src, dst)
                    else:
                        # Handle file conflict
                        base, ext = os.path.splitext(item)
                        counter = 1
                        while os.path.exists(dst):
                            new_name = f"{base}_{counter}{ext}" if ext else f"{item}_{counter}"
                            dst = os.path.join(destination, new_name)
                            counter += 1
                        shutil.move(src, dst)
                else:
                    shutil.move(src, dst)

    def _merge_directories(self, src: str, dst: str):
        """Recursively merge two directories"""
        for item in os.listdir(src):
            src_item = os.path.join(src, item)
            dst_item = os.path.join(dst, item)

            if os.path.isdir(src_item):
                if os.path.exists(dst_item):
                    self._merge_directories(src_item, dst_item)
                else:
                    shutil.move(src_item, dst_item)
            else:
                if os.path.exists(dst_item):
                    # Handle conflict
                    base, ext = os.path.splitext(item)
                    counter = 1
                    while os.path.exists(dst_item):
                        new_name = f"{base}_{counter}{ext}" if ext else f"{item}_{counter}"
                        dst_item = os.path.join(dst, new_name)
                        counter += 1

                shutil.move(src_item, dst_item)

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of file for circular reference detection"""
        hasher = hashlib.sha256()

        try:
            with open(file_path, 'rb') as f:
                # Read in chunks for large files
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)

            return hasher.hexdigest()
        except Exception:
            # If can't hash, use path + size as fallback
            size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            return f"{file_path}_{size}"

    def _create_temp_dir(self) -> str:
        """Create temporary directory and track it"""
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix='smart_search_recursive_')

        with self._lock:
            self._temp_dirs.append(temp_dir)

        return temp_dir

    def _cleanup_temp_dirs(self):
        """Clean up all temporary directories"""
        with self._lock:
            for temp_dir in self._temp_dirs:
                if os.path.exists(temp_dir):
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception:
                        pass  # Best effort cleanup

            self._temp_dirs.clear()

    def detect_nested_depth(self, archive_path: str) -> int:
        """
        Detect maximum nesting depth without extracting

        Args:
            archive_path: Path to archive

        Returns:
            Maximum nesting depth
        """
        try:
            # List contents
            entries = self.seven_zip.list_contents(archive_path)

            # Check if any entries are archives
            max_depth = 0
            for entry in entries:
                path = entry.get('Path', '')
                if self.seven_zip.is_archive(path):
                    # Found nested archive
                    max_depth = 1

            return max_depth

        except Exception:
            return 0

    def get_nested_archives_tree(self, archive_path: str) -> Dict[str, any]:
        """
        Get tree of nested archives (without extracting)

        Args:
            archive_path: Path to archive

        Returns:
            Tree structure of nested archives
        """
        try:
            entries = self.seven_zip.list_contents(archive_path)

            nested = []
            for entry in entries:
                path = entry.get('Path', '')
                if self.seven_zip.is_archive(path):
                    nested.append({
                        'name': path,
                        'size': entry.get('Size', 0),
                        'packed_size': entry.get('PackedSize', 0)
                    })

            return {
                'archive': os.path.basename(archive_path),
                'nested_archives': nested,
                'count': len(nested)
            }

        except Exception as e:
            return {
                'archive': os.path.basename(archive_path),
                'error': str(e)
            }
