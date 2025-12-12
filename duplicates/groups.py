"""
Duplicate group management module.

Features:
- Group duplicates by hash
- Calculate wasted space
- Selection strategies (oldest, newest, folder priority)
- Group statistics and analysis
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Optional, Union


class SelectionStrategy(Enum):
    """Strategies for auto-selecting files to keep/delete."""
    KEEP_OLDEST = "keep_oldest"           # Keep file with oldest mtime
    KEEP_NEWEST = "keep_newest"           # Keep file with newest mtime
    KEEP_SHORTEST_PATH = "keep_shortest"  # Keep file with shortest path
    KEEP_FIRST_ALPHABETICAL = "keep_alpha"  # Keep first alphabetically
    FOLDER_PRIORITY = "folder_priority"   # Keep based on folder priority list
    CUSTOM = "custom"                     # Custom selection function


@dataclass
class FileInfo:
    """Information about a file in a duplicate group."""
    path: Path
    size: int
    mtime: float
    selected_for_deletion: bool = False

    @property
    def mtime_datetime(self) -> datetime:
        """Get modification time as datetime."""
        return datetime.fromtimestamp(self.mtime)

    def __repr__(self) -> str:
        status = "DELETE" if self.selected_for_deletion else "KEEP"
        return f"FileInfo({self.path}, {self.size} bytes, {status})"


@dataclass
class DuplicateGroup:
    """
    A group of duplicate files with the same hash.

    Attributes:
        hash_value: The hash identifying this group
        files: List of FileInfo objects
        hash_type: Type of hash ('quick' or 'full')
    """
    hash_value: str
    files: list[FileInfo] = field(default_factory=list)
    hash_type: str = "full"

    @property
    def file_count(self) -> int:
        """Number of files in the group."""
        return len(self.files)

    @property
    def total_size(self) -> int:
        """Total size of all files in the group."""
        return sum(f.size for f in self.files)

    @property
    def wasted_space(self) -> int:
        """
        Wasted space from duplicates.

        This is (n-1) * size, as we only need to keep one copy.
        """
        if not self.files:
            return 0
        return (len(self.files) - 1) * self.files[0].size

    @property
    def selected_for_deletion(self) -> list[FileInfo]:
        """Get files selected for deletion."""
        return [f for f in self.files if f.selected_for_deletion]

    @property
    def selected_for_keeping(self) -> list[FileInfo]:
        """Get files selected for keeping."""
        return [f for f in self.files if not f.selected_for_deletion]

    @property
    def recoverable_space(self) -> int:
        """Space that would be recovered by deleting selected files."""
        return sum(f.size for f in self.selected_for_deletion)

    def add_file(self, file_path: Union[str, Path], size: int, mtime: float) -> None:
        """
        Add a file to the duplicate group.

        Args:
            file_path: Path to the file
            size: File size in bytes
            mtime: Modification time (timestamp)
        """
        file_info = FileInfo(
            path=Path(file_path),
            size=size,
            mtime=mtime
        )
        self.files.append(file_info)

    def clear_selection(self) -> None:
        """Clear all deletion selections."""
        for file in self.files:
            file.selected_for_deletion = False

    def select_by_strategy(
        self,
        strategy: SelectionStrategy,
        folder_priorities: Optional[list[str]] = None,
        custom_selector: Optional[Callable[[list[FileInfo]], list[FileInfo]]] = None
    ) -> None:
        """
        Auto-select files for deletion based on strategy.

        Args:
            strategy: Selection strategy to use
            folder_priorities: List of folder prefixes in priority order (for FOLDER_PRIORITY)
            custom_selector: Custom selection function (for CUSTOM strategy)
        """
        if not self.files or len(self.files) <= 1:
            return

        self.clear_selection()

        if strategy == SelectionStrategy.KEEP_OLDEST:
            self._select_keep_oldest()

        elif strategy == SelectionStrategy.KEEP_NEWEST:
            self._select_keep_newest()

        elif strategy == SelectionStrategy.KEEP_SHORTEST_PATH:
            self._select_keep_shortest_path()

        elif strategy == SelectionStrategy.KEEP_FIRST_ALPHABETICAL:
            self._select_keep_first_alphabetical()

        elif strategy == SelectionStrategy.FOLDER_PRIORITY:
            if folder_priorities:
                self._select_by_folder_priority(folder_priorities)
            else:
                # Fallback to keep oldest
                self._select_keep_oldest()

        elif strategy == SelectionStrategy.CUSTOM:
            if custom_selector:
                to_delete = custom_selector(self.files)
                for file in to_delete:
                    file.selected_for_deletion = True
            else:
                # Fallback to keep oldest
                self._select_keep_oldest()

    def _select_keep_oldest(self) -> None:
        """Mark all files except the oldest for deletion."""
        oldest = min(self.files, key=lambda f: f.mtime)
        for file in self.files:
            if file != oldest:
                file.selected_for_deletion = True

    def _select_keep_newest(self) -> None:
        """Mark all files except the newest for deletion."""
        newest = max(self.files, key=lambda f: f.mtime)
        for file in self.files:
            if file != newest:
                file.selected_for_deletion = True

    def _select_keep_shortest_path(self) -> None:
        """Mark all files except the one with shortest path for deletion."""
        shortest = min(self.files, key=lambda f: len(str(f.path)))
        for file in self.files:
            if file != shortest:
                file.selected_for_deletion = True

    def _select_keep_first_alphabetical(self) -> None:
        """Mark all files except the first alphabetically for deletion."""
        first = min(self.files, key=lambda f: str(f.path).lower())
        for file in self.files:
            if file != first:
                file.selected_for_deletion = True

    def _select_by_folder_priority(self, priorities: list[str]) -> None:
        """
        Mark files for deletion based on folder priority.

        Files in earlier priority folders are kept. If no files match
        priorities, keeps the oldest file.

        Args:
            priorities: List of folder prefixes in priority order
        """
        # Normalize priorities
        norm_priorities = [str(Path(p).resolve()) for p in priorities]

        # Find file with highest priority
        best_file = None
        best_priority = len(norm_priorities)  # Lower is better

        for file in self.files:
            file_path = str(file.path.resolve())

            # Check priority
            priority = len(norm_priorities)  # Default: lowest priority
            for i, prefix in enumerate(norm_priorities):
                if file_path.startswith(prefix):
                    priority = i
                    break

            if priority < best_priority:
                best_priority = priority
                best_file = file

        # If no priority match, keep oldest
        if best_file is None:
            best_file = min(self.files, key=lambda f: f.mtime)

        # Mark others for deletion
        for file in self.files:
            if file != best_file:
                file.selected_for_deletion = True

    def manual_select(self, file_path: Union[str, Path], delete: bool = True) -> bool:
        """
        Manually select/deselect a file for deletion.

        Args:
            file_path: Path to the file
            delete: True to mark for deletion, False to keep

        Returns:
            True if file was found and updated
        """
        path = Path(file_path).resolve()
        for file in self.files:
            if file.path.resolve() == path:
                file.selected_for_deletion = delete
                return True
        return False

    def get_statistics(self) -> dict:
        """Get statistics about this duplicate group."""
        return {
            'hash': self.hash_value[:16] + '...',
            'file_count': self.file_count,
            'total_size': self.total_size,
            'wasted_space': self.wasted_space,
            'selected_for_deletion': len(self.selected_for_deletion),
            'selected_for_keeping': len(self.selected_for_keeping),
            'recoverable_space': self.recoverable_space,
            'oldest_file': min(self.files, key=lambda f: f.mtime).path if self.files else None,
            'newest_file': max(self.files, key=lambda f: f.mtime).path if self.files else None,
        }

    def __repr__(self) -> str:
        return (
            f"DuplicateGroup(hash={self.hash_value[:8]}..., "
            f"files={self.file_count}, wasted={self.wasted_space} bytes)"
        )


class DuplicateGroupManager:
    """
    Manager for organizing and analyzing duplicate groups.

    Features:
    - Create groups from hash results
    - Apply selection strategies to all groups
    - Calculate total statistics
    - Filter and sort groups
    """

    def __init__(self):
        """Initialize duplicate group manager."""
        self.groups: list[DuplicateGroup] = []

    def add_group(self, group: DuplicateGroup) -> None:
        """Add a duplicate group."""
        self.groups.append(group)

    def create_group(self, hash_value: str, hash_type: str = "full") -> DuplicateGroup:
        """
        Create and add a new duplicate group.

        Args:
            hash_value: Hash identifying the group
            hash_type: Type of hash ('quick' or 'full')

        Returns:
            The created group
        """
        group = DuplicateGroup(hash_value=hash_value, hash_type=hash_type)
        self.groups.append(group)
        return group

    def apply_strategy_to_all(
        self,
        strategy: SelectionStrategy,
        folder_priorities: Optional[list[str]] = None,
        custom_selector: Optional[Callable[[list[FileInfo]], list[FileInfo]]] = None
    ) -> None:
        """
        Apply selection strategy to all groups.

        Args:
            strategy: Selection strategy to use
            folder_priorities: Folder priorities (for FOLDER_PRIORITY strategy)
            custom_selector: Custom selector function (for CUSTOM strategy)
        """
        for group in self.groups:
            group.select_by_strategy(strategy, folder_priorities, custom_selector)

    def get_total_statistics(self) -> dict:
        """Get aggregate statistics across all groups."""
        total_files = sum(g.file_count for g in self.groups)
        total_wasted = sum(g.wasted_space for g in self.groups)
        total_recoverable = sum(g.recoverable_space for g in self.groups)

        return {
            'total_groups': len(self.groups),
            'total_duplicate_files': total_files,
            'total_wasted_space': total_wasted,
            'total_recoverable_space': total_recoverable,
            'average_duplicates_per_group': total_files / len(self.groups) if self.groups else 0,
            'largest_group': max(self.groups, key=lambda g: g.file_count) if self.groups else None,
            'most_wasteful_group': max(self.groups, key=lambda g: g.wasted_space) if self.groups else None,
        }

    def filter_by_size(self, min_size: int = 0, max_size: Optional[int] = None) -> list[DuplicateGroup]:
        """
        Filter groups by file size.

        Args:
            min_size: Minimum file size (bytes)
            max_size: Maximum file size (bytes), None for no limit

        Returns:
            Filtered list of groups
        """
        filtered = []
        for group in self.groups:
            if not group.files:
                continue

            file_size = group.files[0].size
            if file_size >= min_size:
                if max_size is None or file_size <= max_size:
                    filtered.append(group)

        return filtered

    def filter_by_count(self, min_count: int = 2) -> list[DuplicateGroup]:
        """
        Filter groups by number of duplicates.

        Args:
            min_count: Minimum number of duplicate files

        Returns:
            Filtered list of groups
        """
        return [g for g in self.groups if g.file_count >= min_count]

    def sort_by_wasted_space(self, reverse: bool = True) -> list[DuplicateGroup]:
        """
        Sort groups by wasted space.

        Args:
            reverse: True for descending order (most wasteful first)

        Returns:
            Sorted list of groups
        """
        return sorted(self.groups, key=lambda g: g.wasted_space, reverse=reverse)

    def sort_by_file_count(self, reverse: bool = True) -> list[DuplicateGroup]:
        """
        Sort groups by number of duplicate files.

        Args:
            reverse: True for descending order (most duplicates first)

        Returns:
            Sorted list of groups
        """
        return sorted(self.groups, key=lambda g: g.file_count, reverse=reverse)

    def clear_all_selections(self) -> None:
        """Clear deletion selections in all groups."""
        for group in self.groups:
            group.clear_selection()

    def get_all_selected_for_deletion(self) -> list[Path]:
        """Get all files selected for deletion across all groups."""
        files = []
        for group in self.groups:
            files.extend(f.path for f in group.selected_for_deletion)
        return files

    def export_report(self, include_files: bool = True) -> dict:
        """
        Export detailed report of all duplicate groups.

        Args:
            include_files: Include individual file listings

        Returns:
            Dict with comprehensive report data
        """
        report = {
            'summary': self.get_total_statistics(),
            'groups': []
        }

        for group in self.groups:
            group_data = {
                'hash': group.hash_value,
                'hash_type': group.hash_type,
                'statistics': group.get_statistics(),
            }

            if include_files:
                group_data['files'] = [
                    {
                        'path': str(f.path),
                        'size': f.size,
                        'mtime': f.mtime,
                        'mtime_readable': f.mtime_datetime.isoformat(),
                        'selected_for_deletion': f.selected_for_deletion,
                    }
                    for f in group.files
                ]

            report['groups'].append(group_data)

        return report
