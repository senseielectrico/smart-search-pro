"""
Folder/Directory Comparison Module

Compare directories, find duplicates across folders, missing files,
extra files, and synchronization capabilities.
"""

from .folder_comparator import (
    FolderComparator,
    ComparisonMode,
    ComparisonResult,
    ComparisonStats,
    FileComparison,
    FileStatus,
    format_size
)

from .sync_engine import (
    SyncEngine,
    SyncAction,
    SyncConflict,
    ConflictResolution,
    SyncOperation,
    SyncResult,
    format_sync_summary
)

__all__ = [
    # Comparator
    "FolderComparator",
    "ComparisonMode",
    "ComparisonResult",
    "ComparisonStats",
    "FileComparison",
    "FileStatus",
    "format_size",

    # Sync Engine
    "SyncEngine",
    "SyncAction",
    "SyncConflict",
    "ConflictResolution",
    "SyncOperation",
    "SyncResult",
    "format_sync_summary"
]
