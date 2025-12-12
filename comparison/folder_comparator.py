"""
Folder Comparator - Compare two directories for duplicates, missing, and extra files.

Features:
- Multiple comparison modes (content hash, name only, size+name)
- Recursive directory traversal
- Multi-threaded hashing for performance
- Filtering by extension, size range, date range
- Detailed comparison reports
- Space savings calculation
"""

import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

# Add parent directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.threading import create_io_executor
from duplicates.hasher import FileHasher, HashAlgorithm


class ComparisonMode(Enum):
    """Comparison modes for directory comparison."""
    CONTENT_HASH = "content"     # Compare by file content hash (most accurate)
    NAME_ONLY = "name"            # Compare by filename only
    SIZE_NAME = "size_name"       # Compare by size + filename (fast)


class FileStatus(Enum):
    """Status of a file in comparison."""
    SAME = "same"                 # File exists in both with same content
    DIFFERENT = "different"       # File exists in both but different content
    MISSING_IN_TARGET = "missing_target"  # File in source but not in target
    EXTRA_IN_TARGET = "extra_target"      # File in target but not in source


@dataclass
class FileComparison:
    """Comparison result for a single file."""
    relative_path: str
    status: FileStatus
    source_path: Optional[Path] = None
    target_path: Optional[Path] = None
    source_size: int = 0
    target_size: int = 0
    source_modified: Optional[datetime] = None
    target_modified: Optional[datetime] = None
    source_hash: Optional[str] = None
    target_hash: Optional[str] = None


@dataclass
class ComparisonStats:
    """Statistics from directory comparison."""
    total_files: int = 0
    same_files: int = 0
    different_files: int = 0
    missing_in_target: int = 0
    extra_in_target: int = 0
    total_source_size: int = 0
    total_target_size: int = 0
    missing_size: int = 0      # Size of files missing in target
    extra_size: int = 0        # Size of extra files in target
    duplicate_size: int = 0    # Size of duplicate files (same)

    @property
    def space_wasted_by_duplicates(self) -> int:
        """Calculate space wasted by duplicate files."""
        return self.duplicate_size

    @property
    def space_savings_potential(self) -> int:
        """Calculate potential space savings if extra files are removed."""
        return self.extra_size


@dataclass
class ComparisonResult:
    """Result of directory comparison."""
    source_dir: Path
    target_dir: Path
    mode: ComparisonMode
    comparisons: List[FileComparison] = field(default_factory=list)
    stats: ComparisonStats = field(default_factory=ComparisonStats)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None

    @property
    def duration(self) -> float:
        """Get comparison duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def get_files_by_status(self, status: FileStatus) -> List[FileComparison]:
        """Get all files with a specific status."""
        return [c for c in self.comparisons if c.status == status]

    def get_missing_files(self) -> List[FileComparison]:
        """Get files missing in target."""
        return self.get_files_by_status(FileStatus.MISSING_IN_TARGET)

    def get_extra_files(self) -> List[FileComparison]:
        """Get extra files in target."""
        return self.get_files_by_status(FileStatus.EXTRA_IN_TARGET)

    def get_different_files(self) -> List[FileComparison]:
        """Get files that exist in both but are different."""
        return self.get_files_by_status(FileStatus.DIFFERENT)

    def get_same_files(self) -> List[FileComparison]:
        """Get files that are identical in both."""
        return self.get_files_by_status(FileStatus.SAME)


class FolderComparator:
    """
    Compare two directories to find duplicates, missing, and extra files.

    Features:
    - Multiple comparison modes
    - File filtering (extensions, size, date)
    - Multi-threaded hashing
    - Progress callbacks
    - Recursive comparison

    Example:
        >>> comparator = FolderComparator(mode=ComparisonMode.CONTENT_HASH)
        >>> result = comparator.compare(
        ...     source='/path/to/source',
        ...     target='/path/to/target',
        ...     recursive=True
        ... )
        >>> print(f"Missing: {result.stats.missing_in_target}")
        >>> print(f"Extra: {result.stats.extra_in_target}")
    """

    def __init__(
        self,
        mode: ComparisonMode = ComparisonMode.CONTENT_HASH,
        hash_algorithm: HashAlgorithm = HashAlgorithm.SHA256,
        max_workers: Optional[int] = None,
        extensions: Optional[List[str]] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        modified_after: Optional[datetime] = None,
        modified_before: Optional[datetime] = None
    ):
        """
        Initialize folder comparator.

        Args:
            mode: Comparison mode
            hash_algorithm: Hash algorithm for content comparison
            max_workers: Max worker threads (None = auto-detect)
            extensions: Filter by file extensions (e.g., ['.jpg', '.png'])
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes
            modified_after: Only include files modified after this date
            modified_before: Only include files modified before this date
        """
        self.mode = mode
        self.hash_algorithm = hash_algorithm
        self.max_workers = max_workers
        self.extensions = set(ext.lower() for ext in extensions) if extensions else None
        self.min_size = min_size
        self.max_size = max_size
        self.modified_after = modified_after
        self.modified_before = modified_before

        # Initialize hasher for content comparison
        if self.mode == ComparisonMode.CONTENT_HASH:
            self.hasher = FileHasher(
                algorithm=hash_algorithm,
                max_workers=max_workers
            )

    def _should_include_file(self, file_path: Path) -> bool:
        """Check if file passes filters."""
        # Extension filter
        if self.extensions and file_path.suffix.lower() not in self.extensions:
            return False

        try:
            stat = file_path.stat()

            # Size filter
            if self.min_size is not None and stat.st_size < self.min_size:
                return False
            if self.max_size is not None and stat.st_size > self.max_size:
                return False

            # Date filter
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            if self.modified_after and modified_time < self.modified_after:
                return False
            if self.modified_before and modified_time > self.modified_before:
                return False

            return True

        except (OSError, IOError):
            return False

    def _scan_directory(
        self,
        directory: Path,
        recursive: bool = True
    ) -> Dict[str, Path]:
        """
        Scan directory and return mapping of relative paths to absolute paths.

        Args:
            directory: Directory to scan
            recursive: Scan subdirectories

        Returns:
            Dict mapping relative path to absolute path
        """
        files = {}

        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"

        for file_path in directory.glob(pattern):
            if file_path.is_file() and self._should_include_file(file_path):
                relative_path = str(file_path.relative_to(directory))
                files[relative_path] = file_path

        return files

    def _compute_hashes(
        self,
        files: Dict[str, Path],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, str]:
        """
        Compute hashes for files.

        Args:
            files: Dict of relative_path -> absolute_path
            progress_callback: Optional callback(completed, total)

        Returns:
            Dict mapping relative path to hash
        """
        hashes = {}
        file_list = list(files.items())
        total = len(file_list)
        completed = 0

        with create_io_executor(max_workers=self.max_workers, thread_name_prefix="HashCompare") as executor:
            future_to_rel = {
                executor.submit(self.hasher.hash_file, path, quick_hash=False, full_hash=True): rel_path
                for rel_path, path in file_list
            }

            for future in as_completed(future_to_rel):
                rel_path = future_to_rel[future]
                result = future.result()

                if result.success and result.full_hash:
                    hashes[rel_path] = result.full_hash

                completed += 1
                if progress_callback:
                    progress_callback(completed, total)

        return hashes

    def _compare_by_content(
        self,
        source_files: Dict[str, Path],
        target_files: Dict[str, Path],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[FileComparison]:
        """Compare files by content hash."""
        comparisons = []

        # Progress tracking
        total_operations = len(source_files) + len(target_files)
        completed = 0

        def hash_progress(done, total):
            nonlocal completed
            completed = done
            if progress_callback:
                progress_callback(completed, total_operations)

        # Compute hashes for source files
        source_hashes = self._compute_hashes(source_files, hash_progress)

        # Compute hashes for target files
        completed = len(source_files)
        target_hashes = self._compute_hashes(target_files, hash_progress)

        # Find common files and compare
        all_relative_paths = set(source_files.keys()) | set(target_files.keys())

        for rel_path in sorted(all_relative_paths):
            source_path = source_files.get(rel_path)
            target_path = target_files.get(rel_path)

            comparison = FileComparison(relative_path=rel_path)

            # File in source
            if source_path:
                comparison.source_path = source_path
                comparison.source_size = source_path.stat().st_size
                comparison.source_modified = datetime.fromtimestamp(source_path.stat().st_mtime)
                comparison.source_hash = source_hashes.get(rel_path)

            # File in target
            if target_path:
                comparison.target_path = target_path
                comparison.target_size = target_path.stat().st_size
                comparison.target_modified = datetime.fromtimestamp(target_path.stat().st_mtime)
                comparison.target_hash = target_hashes.get(rel_path)

            # Determine status
            if source_path and target_path:
                # Both exist - compare hashes
                if comparison.source_hash == comparison.target_hash:
                    comparison.status = FileStatus.SAME
                else:
                    comparison.status = FileStatus.DIFFERENT
            elif source_path and not target_path:
                comparison.status = FileStatus.MISSING_IN_TARGET
            else:  # target_path and not source_path
                comparison.status = FileStatus.EXTRA_IN_TARGET

            comparisons.append(comparison)

        return comparisons

    def _compare_by_name(
        self,
        source_files: Dict[str, Path],
        target_files: Dict[str, Path]
    ) -> List[FileComparison]:
        """Compare files by name only."""
        comparisons = []
        all_relative_paths = set(source_files.keys()) | set(target_files.keys())

        for rel_path in sorted(all_relative_paths):
            source_path = source_files.get(rel_path)
            target_path = target_files.get(rel_path)

            comparison = FileComparison(relative_path=rel_path)

            if source_path:
                comparison.source_path = source_path
                try:
                    stat = source_path.stat()
                    comparison.source_size = stat.st_size
                    comparison.source_modified = datetime.fromtimestamp(stat.st_mtime)
                except (OSError, IOError):
                    pass

            if target_path:
                comparison.target_path = target_path
                try:
                    stat = target_path.stat()
                    comparison.target_size = stat.st_size
                    comparison.target_modified = datetime.fromtimestamp(stat.st_mtime)
                except (OSError, IOError):
                    pass

            # Determine status
            if source_path and target_path:
                comparison.status = FileStatus.SAME  # Same name = same for this mode
            elif source_path and not target_path:
                comparison.status = FileStatus.MISSING_IN_TARGET
            else:
                comparison.status = FileStatus.EXTRA_IN_TARGET

            comparisons.append(comparison)

        return comparisons

    def _compare_by_size_name(
        self,
        source_files: Dict[str, Path],
        target_files: Dict[str, Path]
    ) -> List[FileComparison]:
        """Compare files by size and name."""
        comparisons = []
        all_relative_paths = set(source_files.keys()) | set(target_files.keys())

        for rel_path in sorted(all_relative_paths):
            source_path = source_files.get(rel_path)
            target_path = target_files.get(rel_path)

            comparison = FileComparison(relative_path=rel_path)

            if source_path:
                comparison.source_path = source_path
                try:
                    stat = source_path.stat()
                    comparison.source_size = stat.st_size
                    comparison.source_modified = datetime.fromtimestamp(stat.st_mtime)
                except (OSError, IOError):
                    pass

            if target_path:
                comparison.target_path = target_path
                try:
                    stat = target_path.stat()
                    comparison.target_size = stat.st_size
                    comparison.target_modified = datetime.fromtimestamp(stat.st_mtime)
                except (OSError, IOError):
                    pass

            # Determine status
            if source_path and target_path:
                if comparison.source_size == comparison.target_size:
                    comparison.status = FileStatus.SAME
                else:
                    comparison.status = FileStatus.DIFFERENT
            elif source_path and not target_path:
                comparison.status = FileStatus.MISSING_IN_TARGET
            else:
                comparison.status = FileStatus.EXTRA_IN_TARGET

            comparisons.append(comparison)

        return comparisons

    def _calculate_stats(self, comparisons: List[FileComparison]) -> ComparisonStats:
        """Calculate statistics from comparisons."""
        stats = ComparisonStats()

        stats.total_files = len(comparisons)

        for comp in comparisons:
            if comp.status == FileStatus.SAME:
                stats.same_files += 1
                stats.duplicate_size += comp.source_size
            elif comp.status == FileStatus.DIFFERENT:
                stats.different_files += 1
            elif comp.status == FileStatus.MISSING_IN_TARGET:
                stats.missing_in_target += 1
                stats.missing_size += comp.source_size
            elif comp.status == FileStatus.EXTRA_IN_TARGET:
                stats.extra_in_target += 1
                stats.extra_size += comp.target_size

            if comp.source_path:
                stats.total_source_size += comp.source_size
            if comp.target_path:
                stats.total_target_size += comp.target_size

        return stats

    def compare(
        self,
        source: str | Path,
        target: str | Path,
        recursive: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> ComparisonResult:
        """
        Compare two directories.

        Args:
            source: Source directory path
            target: Target directory path
            recursive: Recursively compare subdirectories
            progress_callback: Optional callback(completed, total)

        Returns:
            ComparisonResult with detailed comparison data
        """
        source_dir = Path(source)
        target_dir = Path(target)

        result = ComparisonResult(
            source_dir=source_dir,
            target_dir=target_dir,
            mode=self.mode,
            start_time=datetime.now()
        )

        try:
            # Validate directories
            if not source_dir.exists() or not source_dir.is_dir():
                raise ValueError(f"Source directory not found: {source_dir}")
            if not target_dir.exists() or not target_dir.is_dir():
                raise ValueError(f"Target directory not found: {target_dir}")

            # Scan directories
            source_files = self._scan_directory(source_dir, recursive)
            target_files = self._scan_directory(target_dir, recursive)

            # Perform comparison based on mode
            if self.mode == ComparisonMode.CONTENT_HASH:
                result.comparisons = self._compare_by_content(
                    source_files, target_files, progress_callback
                )
            elif self.mode == ComparisonMode.NAME_ONLY:
                result.comparisons = self._compare_by_name(source_files, target_files)
            elif self.mode == ComparisonMode.SIZE_NAME:
                result.comparisons = self._compare_by_size_name(source_files, target_files)

            # Calculate statistics
            result.stats = self._calculate_stats(result.comparisons)

        except Exception as e:
            result.error = str(e)

        result.end_time = datetime.now()
        return result


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def print_comparison_report(result: ComparisonResult) -> None:
    """Print detailed comparison report to console."""
    print("\n" + "=" * 80)
    print("FOLDER COMPARISON REPORT")
    print("=" * 80)
    print(f"Source:      {result.source_dir}")
    print(f"Target:      {result.target_dir}")
    print(f"Mode:        {result.mode.value}")
    print(f"Duration:    {result.duration:.2f}s")
    print("-" * 80)

    stats = result.stats
    print(f"Total Files:          {stats.total_files}")
    print(f"  Same:               {stats.same_files}")
    print(f"  Different:          {stats.different_files}")
    print(f"  Missing in Target:  {stats.missing_in_target}")
    print(f"  Extra in Target:    {stats.extra_in_target}")
    print("-" * 80)
    print(f"Source Size:          {format_size(stats.total_source_size)}")
    print(f"Target Size:          {format_size(stats.total_target_size)}")
    print(f"Missing Size:         {format_size(stats.missing_size)}")
    print(f"Extra Size:           {format_size(stats.extra_size)}")
    print(f"Duplicate Size:       {format_size(stats.duplicate_size)}")
    print(f"Space Savings:        {format_size(stats.space_savings_potential)}")
    print("=" * 80)
