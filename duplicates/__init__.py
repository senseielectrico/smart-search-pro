"""
Smart Search Pro - Duplicate File Finder Module

A comprehensive duplicate detection system with multi-pass scanning,
hash caching, and safe deletion actions.

Key Features:
- Multi-pass scanning (size -> quick hash -> full hash)
- Multiple hash algorithms (MD5, SHA-1, SHA-256, xxHash, BLAKE3)
- SQLite-based hash caching with LRU eviction
- Progress reporting and cancellation support
- Safe deletion actions (recycle bin, move, hard link, symlink)
- Audit logging for all operations

Example Usage:
    >>> from duplicates import DuplicateScanner
    >>> scanner = DuplicateScanner()
    >>> groups = scanner.scan(['/path/to/folder'], progress_callback=lambda p: print(f"{p}%"))
    >>> for group in groups:
    ...     print(f"Duplicate group: {len(group.files)} files, {group.wasted_space} bytes wasted")
"""

from .scanner import DuplicateScanner, ScanProgress, ScanStats
from .hasher import FileHasher, HashAlgorithm, HashResult
from .cache import HashCache, CacheStats
from .groups import DuplicateGroup, DuplicateGroupManager, SelectionStrategy
from .actions import (
    DuplicateAction,
    ActionResult,
    RecycleBinAction,
    MoveToFolderAction,
    PermanentDeleteAction,
    HardLinkAction,
    SymlinkAction,
)

__all__ = [
    # Scanner
    'DuplicateScanner',
    'ScanProgress',
    'ScanStats',

    # Hasher
    'FileHasher',
    'HashAlgorithm',
    'HashResult',

    # Cache
    'HashCache',
    'CacheStats',

    # Groups
    'DuplicateGroup',
    'DuplicateGroupManager',
    'SelectionStrategy',

    # Actions
    'DuplicateAction',
    'ActionResult',
    'RecycleBinAction',
    'MoveToFolderAction',
    'PermanentDeleteAction',
    'HardLinkAction',
    'SymlinkAction',
]

__version__ = '1.0.0'
