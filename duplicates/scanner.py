"""
Multi-pass duplicate scanner with progress reporting.

Features:
- Pass 1: Group files by size (instant elimination of unique sizes)
- Pass 2: Quick hash (first/last 8KB) for fast filtering
- Pass 3: Full hash (SHA-256) for definitive confirmation
- Support for cancellation and progress callbacks
- Optional hash caching for performance
- Comprehensive statistics and reporting
- Auto-detected optimal worker threads
"""

import os
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Union

from .cache import HashCache
from .groups import DuplicateGroup, DuplicateGroupManager
from .hasher import FileHasher, HashAlgorithm


@dataclass
class ScanProgress:
    """Progress information for duplicate scan."""
    current_pass: int = 1       # Current pass (1, 2, or 3)
    total_passes: int = 3       # Total number of passes
    current_file: int = 0       # Current file being processed
    total_files: int = 0        # Total files to process
    current_phase: str = ""     # Description of current phase
    bytes_processed: int = 0    # Bytes processed so far
    total_bytes: int = 0        # Total bytes to process

    @property
    def progress_percent(self) -> float:
        """Calculate overall progress percentage."""
        if self.total_files == 0:
            return 0.0

        # Weight each pass differently
        # Pass 1 (size): 10%
        # Pass 2 (quick hash): 30%
        # Pass 3 (full hash): 60%
        pass_weights = {1: 0.1, 2: 0.3, 3: 0.6}
        completed_passes = self.current_pass - 1
        current_pass_weight = pass_weights.get(self.current_pass, 0.33)

        # Calculate progress within current pass
        pass_progress = (self.current_file / self.total_files) if self.total_files > 0 else 0

        # Calculate total progress
        total = 0
        for i in range(1, completed_passes + 1):
            total += pass_weights.get(i, 0.33)

        total += current_pass_weight * pass_progress

        return min(total * 100, 100.0)

    def __repr__(self) -> str:
        return (
            f"ScanProgress(pass={self.current_pass}/{self.total_passes}, "
            f"file={self.current_file}/{self.total_files}, "
            f"progress={self.progress_percent:.1f}%, "
            f"phase='{self.current_phase}')"
        )


@dataclass
class ScanStats:
    """Statistics for a duplicate scan operation."""
    total_files_scanned: int = 0
    total_bytes_scanned: int = 0
    unique_files: int = 0
    duplicate_groups: int = 0
    duplicate_files: int = 0
    wasted_space: int = 0
    scan_duration: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0

    def __repr__(self) -> str:
        return (
            f"ScanStats(scanned={self.total_files_scanned} files, "
            f"duplicates={self.duplicate_files} in {self.duplicate_groups} groups, "
            f"wasted={self.wasted_space} bytes, duration={self.scan_duration:.2f}s)"
        )


class DuplicateScanner:
    """
    Multi-pass duplicate file scanner.

    The scanner uses a three-pass approach:
    1. Size grouping: Fast elimination of unique file sizes
    2. Quick hashing: Hash first/last 8KB to eliminate most non-duplicates
    3. Full hashing: Complete file hash for definitive duplicate detection

    Features:
    - Parallel processing with thread pool
    - Progress callbacks for UI integration
    - Cancellation support
    - Optional hash caching
    - Comprehensive statistics

    Example:
        >>> scanner = DuplicateScanner(use_cache=True)
        >>> def progress(prog: ScanProgress):
        ...     print(f"Progress: {prog.progress_percent:.1f}% - {prog.current_phase}")
        >>> groups = scanner.scan(['/path/to/scan'], progress_callback=progress)
        >>> print(f"Found {len(groups)} duplicate groups")
    """

    def __init__(
        self,
        algorithm: HashAlgorithm = HashAlgorithm.SHA256,
        use_cache: bool = True,
        cache_path: Optional[Union[str, Path]] = None,
        max_workers: Optional[int] = None,
        min_file_size: int = 0,
        max_file_size: Optional[int] = None
    ):
        """
        Initialize duplicate scanner.

        Args:
            algorithm: Hash algorithm to use
            use_cache: Enable hash caching
            cache_path: Path to cache database (default: ~/.cache/smart_search/hashes.db)
            max_workers: Maximum number of worker threads (None = auto-detect optimal)
            min_file_size: Minimum file size to scan (bytes)
            max_file_size: Maximum file size to scan (bytes, None for no limit)
        """
        self.algorithm = algorithm
        self.use_cache = use_cache
        self.max_workers = max_workers
        self.min_file_size = min_file_size
        self.max_file_size = max_file_size

        # Initialize hasher with auto-detected workers
        self.hasher = FileHasher(algorithm=algorithm, max_workers=max_workers)

        # Initialize cache
        self.cache: Optional[HashCache] = None
        if use_cache:
            if cache_path is None:
                cache_path = Path.home() / '.cache' / 'smart_search' / 'hashes.db'
            self.cache = HashCache(cache_path)

        # Cancellation flag
        self._cancelled = False

        # Statistics
        self.stats = ScanStats()

    def cancel(self) -> None:
        """Cancel the current scan operation."""
        self._cancelled = True

    def scan(
        self,
        paths: list[Union[str, Path]],
        recursive: bool = True,
        follow_symlinks: bool = False,
        progress_callback: Optional[Callable[[ScanProgress], None]] = None
    ) -> DuplicateGroupManager:
        """
        Scan paths for duplicate files.

        Args:
            paths: List of directories or files to scan
            recursive: Recursively scan subdirectories
            follow_symlinks: Follow symbolic links
            progress_callback: Optional callback for progress updates

        Returns:
            DuplicateGroupManager with found duplicates
        """
        import time
        start_time = time.time()

        self._cancelled = False
        self.stats = ScanStats()

        # Initialize progress
        progress = ScanProgress()

        # Collect all files
        progress.current_phase = "Discovering files..."
        if progress_callback:
            progress_callback(progress)

        files = self._collect_files(paths, recursive, follow_symlinks)

        if self._cancelled:
            return DuplicateGroupManager()

        # Pass 1: Group by size
        progress.current_pass = 1
        progress.total_files = len(files)
        progress.current_phase = "Grouping by file size..."
        if progress_callback:
            progress_callback(progress)

        size_groups = self._group_by_size(files, progress, progress_callback)

        if self._cancelled:
            return DuplicateGroupManager()

        # Pass 2: Quick hash
        progress.current_pass = 2
        progress.current_file = 0
        progress.current_phase = "Computing quick hashes..."
        if progress_callback:
            progress_callback(progress)

        quick_hash_groups = self._quick_hash_pass(size_groups, progress, progress_callback)

        if self._cancelled:
            return DuplicateGroupManager()

        # Pass 3: Full hash
        progress.current_pass = 3
        progress.current_file = 0
        progress.current_phase = "Computing full hashes..."
        if progress_callback:
            progress_callback(progress)

        duplicate_groups = self._full_hash_pass(quick_hash_groups, progress, progress_callback)

        # Finalize statistics
        self.stats.scan_duration = time.time() - start_time
        self.stats.total_files_scanned = len(files)
        self.stats.duplicate_groups = len(duplicate_groups.groups)
        self.stats.duplicate_files = sum(g.file_count for g in duplicate_groups.groups)
        self.stats.wasted_space = sum(g.wasted_space for g in duplicate_groups.groups)
        self.stats.unique_files = len(files) - self.stats.duplicate_files

        if self.cache:
            cache_stats = self.cache.get_stats()
            self.stats.cache_hits = cache_stats.cache_hits
            self.stats.cache_misses = cache_stats.cache_misses

        # Final progress update
        progress.current_file = progress.total_files
        progress.current_phase = "Scan complete"
        if progress_callback:
            progress_callback(progress)

        return duplicate_groups

    def _collect_files(
        self,
        paths: list[Union[str, Path]],
        recursive: bool,
        follow_symlinks: bool
    ) -> list[Path]:
        """Collect all files from the given paths."""
        files = []

        for path_str in paths:
            path = Path(path_str)

            if not path.exists():
                continue

            if path.is_file():
                if self._should_include_file(path):
                    files.append(path)

            elif path.is_dir():
                if recursive:
                    for root, dirs, filenames in os.walk(path, followlinks=follow_symlinks):
                        for filename in filenames:
                            file_path = Path(root) / filename

                            if self._cancelled:
                                return files

                            if self._should_include_file(file_path):
                                files.append(file_path)
                else:
                    for item in path.iterdir():
                        if item.is_file() and self._should_include_file(item):
                            files.append(item)

        return files

    def _should_include_file(self, path: Path) -> bool:
        """Check if file should be included in scan."""
        try:
            stat = path.stat()

            # Check if it's a regular file
            if not path.is_file():
                return False

            # Check size constraints
            if stat.st_size < self.min_file_size:
                return False

            if self.max_file_size is not None and stat.st_size > self.max_file_size:
                return False

            return True

        except (OSError, IOError):
            return False

    def _group_by_size(
        self,
        files: list[Path],
        progress: ScanProgress,
        progress_callback: Optional[Callable[[ScanProgress], None]]
    ) -> dict[int, list[Path]]:
        """Group files by size (Pass 1)."""
        size_groups = defaultdict(list)

        for i, file_path in enumerate(files):
            if self._cancelled:
                break

            try:
                size = file_path.stat().st_size
                size_groups[size].append(file_path)

                progress.current_file = i + 1
                if progress_callback and i % 100 == 0:
                    progress_callback(progress)

            except (OSError, IOError):
                continue

        # Filter out unique sizes (no duplicates possible)
        return {size: paths for size, paths in size_groups.items() if len(paths) > 1}

    def _quick_hash_pass(
        self,
        size_groups: dict[int, list[Path]],
        progress: ScanProgress,
        progress_callback: Optional[Callable[[ScanProgress], None]]
    ) -> dict[str, list[tuple[Path, int, float]]]:
        """Compute quick hashes for files (Pass 2)."""
        quick_hash_groups = defaultdict(list)
        total_files = sum(len(paths) for paths in size_groups.values())
        progress.total_files = total_files
        processed = 0

        for size, paths in size_groups.items():
            if self._cancelled:
                break

            for path in paths:
                if self._cancelled:
                    break

                # Check cache first
                quick_hash = None
                if self.cache:
                    cached = self.cache.get_hash(path, validate_mtime=True)
                    if cached and cached['quick_hash']:
                        quick_hash = cached['quick_hash']

                # Compute if not cached
                if quick_hash is None:
                    quick_hash = self.hasher.compute_quick_hash(path)
                    if quick_hash and self.cache:
                        self.cache.set_hash(
                            path,
                            quick_hash=quick_hash,
                            algorithm=self.algorithm
                        )

                if quick_hash:
                    stat = path.stat()
                    quick_hash_groups[quick_hash].append((path, size, stat.st_mtime))

                processed += 1
                progress.current_file = processed
                if progress_callback and processed % 50 == 0:
                    progress_callback(progress)

        # Filter out unique quick hashes
        return {hash_val: paths for hash_val, paths in quick_hash_groups.items() if len(paths) > 1}

    def _full_hash_pass(
        self,
        quick_hash_groups: dict[str, list[tuple[Path, int, float]]],
        progress: ScanProgress,
        progress_callback: Optional[Callable[[ScanProgress], None]]
    ) -> DuplicateGroupManager:
        """Compute full hashes for potential duplicates (Pass 3)."""
        manager = DuplicateGroupManager()
        full_hash_groups = defaultdict(list)
        total_files = sum(len(paths) for paths in quick_hash_groups.values())
        progress.total_files = total_files
        processed = 0

        for quick_hash, file_infos in quick_hash_groups.items():
            if self._cancelled:
                break

            for path, size, mtime in file_infos:
                if self._cancelled:
                    break

                # Check cache first
                full_hash = None
                if self.cache:
                    cached = self.cache.get_hash(path, validate_mtime=True)
                    if cached and cached['full_hash']:
                        full_hash = cached['full_hash']

                # Compute if not cached
                if full_hash is None:
                    full_hash = self.hasher.compute_full_hash(path)
                    if full_hash and self.cache:
                        # Update cache with full hash
                        self.cache.set_hash(
                            path,
                            full_hash=full_hash,
                            algorithm=self.algorithm
                        )

                if full_hash:
                    full_hash_groups[full_hash].append((path, size, mtime))
                    self.stats.total_bytes_scanned += size

                processed += 1
                progress.current_file = processed
                if progress_callback and processed % 25 == 0:
                    progress_callback(progress)

        # Create duplicate groups
        for full_hash, file_infos in full_hash_groups.items():
            if len(file_infos) > 1:
                group = manager.create_group(full_hash, hash_type="full")
                for path, size, mtime in file_infos:
                    group.add_file(path, size, mtime)

        return manager

    def get_stats(self) -> ScanStats:
        """Get statistics from the last scan."""
        return self.stats

    def optimize_cache(self) -> bool:
        """
        Optimize the hash cache.

        Removes entries for non-existent files and vacuums the database.

        Returns:
            True if optimization succeeded
        """
        if self.cache:
            return self.cache.optimize()
        return False

    def clear_cache(self) -> bool:
        """
        Clear all cached hashes.

        Returns:
            True if cache was cleared
        """
        if self.cache:
            return self.cache.clear()
        return False
