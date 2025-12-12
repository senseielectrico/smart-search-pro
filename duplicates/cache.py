"""
Hash cache module with SQLite persistence and LRU eviction.

Features:
- Persistent storage of file hashes
- Quick hash and full hash caching
- Automatic invalidation on file modification (mtime)
- LRU eviction policy to manage cache size
- Thread-safe operations
- Statistics tracking
"""

import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from .hasher import HashAlgorithm


@dataclass
class CacheStats:
    """Statistics for hash cache operations."""
    total_entries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    invalidations: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0

    def __repr__(self) -> str:
        return (
            f"CacheStats(entries={self.total_entries}, "
            f"hits={self.cache_hits}, misses={self.cache_misses}, "
            f"hit_rate={self.hit_rate:.1f}%, "
            f"invalidations={self.invalidations}, evictions={self.evictions})"
        )


class HashCache:
    """
    SQLite-based hash cache with LRU eviction.

    The cache stores both quick hashes and full hashes for files, indexed by
    file path, size, and modification time. Entries are automatically invalidated
    when files are modified.

    Schema:
        - file_path: Normalized absolute path
        - file_size: File size in bytes
        - mtime: Last modification timestamp
        - quick_hash: Hash of first/last chunks
        - full_hash: Hash of entire file
        - algorithm: Hash algorithm used
        - last_accessed: Timestamp for LRU eviction
        - access_count: Number of times accessed

    Example:
        >>> with HashCache('~/.cache/smart_search/hashes.db') as cache:
        ...     cache.set_hash('/path/to/file.txt', quick_hash='abc123', full_hash='def456')
        ...     result = cache.get_hash('/path/to/file.txt')
        ...     print(f"Quick: {result['quick_hash']}, Full: {result['full_hash']}")
    """

    # Default cache settings
    DEFAULT_MAX_SIZE = 100000  # Maximum number of cached files
    DEFAULT_EVICTION_SIZE = 10000  # Number of entries to evict when full

    def __init__(
        self,
        db_path: Union[str, Path],
        max_size: int = DEFAULT_MAX_SIZE,
        eviction_size: int = DEFAULT_EVICTION_SIZE
    ):
        """
        Initialize hash cache.

        Args:
            db_path: Path to SQLite database file
            max_size: Maximum number of entries before eviction
            eviction_size: Number of LRU entries to evict when full
        """
        self.db_path = Path(db_path)
        self.max_size = max_size
        self.eviction_size = eviction_size
        self._lock = threading.Lock()
        self.stats = CacheStats()

        # Create database directory if needed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup."""
        self.close()
        return False

    def close(self):
        """Close any open database connections."""
        # SQLite connections are created per-operation, so nothing to close
        # But we ensure any pending operations are complete
        pass

    def _init_db(self) -> None:
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hash_cache (
                    file_path TEXT PRIMARY KEY,
                    file_size INTEGER NOT NULL,
                    mtime REAL NOT NULL,
                    quick_hash TEXT,
                    full_hash TEXT,
                    algorithm TEXT NOT NULL,
                    last_accessed REAL NOT NULL,
                    access_count INTEGER DEFAULT 1,
                    created_at REAL NOT NULL
                )
            """)

            # Create indexes for performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_last_accessed
                ON hash_cache(last_accessed)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_size
                ON hash_cache(file_size)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_quick_hash
                ON hash_cache(quick_hash)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_full_hash
                ON hash_cache(full_hash)
            """)

            conn.commit()

        # Update initial stats
        self._update_stats()

    def _normalize_path(self, file_path: Union[str, Path]) -> str:
        """Normalize file path for consistent cache keys."""
        return str(Path(file_path).resolve())

    def _update_stats(self) -> None:
        """Update cache statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM hash_cache")
            self.stats.total_entries = cursor.fetchone()[0]

    def get_hash(
        self,
        file_path: Union[str, Path],
        validate_mtime: bool = True
    ) -> Optional[dict]:
        """
        Get cached hash for a file.

        Args:
            file_path: Path to the file
            validate_mtime: Check if file has been modified

        Returns:
            Dict with hash data, or None if not cached or invalid
        """
        with self._lock:
            try:
                path = Path(file_path)
                normalized_path = self._normalize_path(path)

                # Get file stats
                stat = path.stat()
                current_size = stat.st_size
                current_mtime = stat.st_mtime

                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute(
                        """
                        SELECT * FROM hash_cache
                        WHERE file_path = ?
                        """,
                        (normalized_path,)
                    )
                    row = cursor.fetchone()

                    if not row:
                        self.stats.cache_misses += 1
                        return None

                    # Validate cache entry
                    if validate_mtime:
                        if row['file_size'] != current_size or row['mtime'] != current_mtime:
                            # File has been modified, invalidate cache
                            self._invalidate(normalized_path, conn)
                            self.stats.cache_misses += 1
                            self.stats.invalidations += 1
                            return None

                    # Update access statistics
                    now = datetime.now().timestamp()
                    conn.execute(
                        """
                        UPDATE hash_cache
                        SET last_accessed = ?, access_count = access_count + 1
                        WHERE file_path = ?
                        """,
                        (now, normalized_path)
                    )
                    conn.commit()

                    self.stats.cache_hits += 1

                    return {
                        'file_path': row['file_path'],
                        'file_size': row['file_size'],
                        'mtime': row['mtime'],
                        'quick_hash': row['quick_hash'],
                        'full_hash': row['full_hash'],
                        'algorithm': row['algorithm'],
                    }

            except Exception:
                self.stats.cache_misses += 1
                return None

    def set_hash(
        self,
        file_path: Union[str, Path],
        quick_hash: Optional[str] = None,
        full_hash: Optional[str] = None,
        algorithm: HashAlgorithm = HashAlgorithm.SHA256
    ) -> bool:
        """
        Store hash in cache.

        Args:
            file_path: Path to the file
            quick_hash: Quick hash value
            full_hash: Full hash value
            algorithm: Hash algorithm used

        Returns:
            True if stored successfully
        """
        with self._lock:
            try:
                path = Path(file_path)
                normalized_path = self._normalize_path(path)

                # Get file stats
                stat = path.stat()
                file_size = stat.st_size
                mtime = stat.st_mtime
                now = datetime.now().timestamp()

                # Check if we need to evict entries
                self._check_and_evict()

                with sqlite3.connect(self.db_path) as conn:
                    # Insert or replace cache entry
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO hash_cache
                        (file_path, file_size, mtime, quick_hash, full_hash,
                         algorithm, last_accessed, access_count, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                        """,
                        (
                            normalized_path,
                            file_size,
                            mtime,
                            quick_hash,
                            full_hash,
                            algorithm.value,
                            now,
                            now
                        )
                    )
                    conn.commit()

                self._update_stats()
                return True

            except Exception:
                return False

    def _invalidate(self, file_path: str, conn: sqlite3.Connection) -> None:
        """
        Invalidate a cache entry.

        Args:
            file_path: Normalized file path
            conn: Database connection
        """
        conn.execute("DELETE FROM hash_cache WHERE file_path = ?", (file_path,))
        conn.commit()

    def invalidate(self, file_path: Union[str, Path]) -> bool:
        """
        Manually invalidate a cache entry.

        Args:
            file_path: Path to the file

        Returns:
            True if invalidated
        """
        with self._lock:
            try:
                normalized_path = self._normalize_path(file_path)
                with sqlite3.connect(self.db_path) as conn:
                    self._invalidate(normalized_path, conn)
                self.stats.invalidations += 1
                self._update_stats()
                return True
            except Exception:
                return False

    def _check_and_evict(self) -> None:
        """Check cache size and evict LRU entries if needed."""
        if self.stats.total_entries >= self.max_size:
            self._evict_lru()

    def _evict_lru(self) -> None:
        """Evict least recently used entries."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Delete oldest entries based on last_accessed
                conn.execute(
                    """
                    DELETE FROM hash_cache
                    WHERE file_path IN (
                        SELECT file_path FROM hash_cache
                        ORDER BY last_accessed ASC
                        LIMIT ?
                    )
                    """,
                    (self.eviction_size,)
                )
                evicted = conn.total_changes
                conn.commit()

            self.stats.evictions += evicted
            self._update_stats()

        except Exception:
            pass

    def clear(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if cleared successfully
        """
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM hash_cache")
                    conn.commit()

                self.stats = CacheStats()
                return True

            except Exception:
                return False

    def vacuum(self) -> bool:
        """
        Optimize database by reclaiming unused space.

        Returns:
            True if successful
        """
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("VACUUM")
                    conn.commit()
                return True
            except Exception:
                return False

    def get_duplicates_by_hash(
        self,
        hash_value: str,
        hash_type: str = 'full'
    ) -> list[str]:
        """
        Find all files with the same hash.

        Args:
            hash_value: Hash value to search for
            hash_type: 'quick' or 'full'

        Returns:
            List of file paths with matching hash
        """
        with self._lock:
            try:
                column = 'quick_hash' if hash_type == 'quick' else 'full_hash'

                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        f"SELECT file_path FROM hash_cache WHERE {column} = ?",
                        (hash_value,)
                    )
                    return [row[0] for row in cursor.fetchall()]

            except Exception:
                return []

    def get_stats(self) -> CacheStats:
        """Get current cache statistics."""
        self._update_stats()
        return self.stats

    def optimize(self) -> bool:
        """
        Optimize cache by:
        - Removing entries for non-existent files
        - Vacuuming database
        - Updating statistics

        Returns:
            True if optimization completed successfully
        """
        with self._lock:
            try:
                removed = 0
                with sqlite3.connect(self.db_path) as conn:
                    # Get all file paths
                    cursor = conn.execute("SELECT file_path FROM hash_cache")
                    paths = [row[0] for row in cursor.fetchall()]

                    # Remove entries for non-existent files
                    for path in paths:
                        if not Path(path).exists():
                            conn.execute(
                                "DELETE FROM hash_cache WHERE file_path = ?",
                                (path,)
                            )
                            removed += 1

                    conn.commit()

                # Vacuum database
                self.vacuum()

                self.stats.invalidations += removed
                self._update_stats()

                return True

            except Exception:
                return False
