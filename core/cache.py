"""
LRU cache implementation with TTL and size limits.

Provides efficient caching with automatic eviction, time-to-live,
optional persistence, hit rate statistics, and prewarming.
"""

import pickle
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Generic, TypeVar, Dict, List

from .exceptions import CacheError, CacheExpiredError, CacheFullError
from .logger import get_logger

logger = get_logger(__name__)

K = TypeVar("K")  # Key type
V = TypeVar("V")  # Value type


@dataclass
class CacheEntry(Generic[V]):
    """Cache entry with metadata."""

    value: V
    timestamp: float
    ttl: float | None
    size: int
    access_count: int = 0
    last_access: float | None = None
    cache_type: str = "default"  # Cache type for selective invalidation

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl

    def touch(self) -> None:
        """Update access metadata."""
        self.access_count += 1
        self.last_access = time.time()


@dataclass
class CacheStats:
    """Extended cache statistics."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    sets: int = 0
    deletes: int = 0
    size: int = 0
    bytes_used: int = 0
    max_size: int = 0
    max_bytes: int | None = None

    @property
    def total_requests(self) -> int:
        """Total cache requests."""
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        """Cache hit rate (0.0 to 1.0)."""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    @property
    def miss_rate(self) -> float:
        """Cache miss rate (0.0 to 1.0)."""
        return 1.0 - self.hit_rate

    @property
    def fill_rate(self) -> float:
        """Cache fill rate (0.0 to 1.0)."""
        if self.max_size == 0:
            return 0.0
        return self.size / self.max_size

    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "expirations": self.expirations,
            "sets": self.sets,
            "deletes": self.deletes,
            "size": self.size,
            "bytes_used": self.bytes_used,
            "max_size": self.max_size,
            "max_bytes": self.max_bytes,
            "total_requests": self.total_requests,
            "hit_rate": self.hit_rate,
            "miss_rate": self.miss_rate,
            "fill_rate": self.fill_rate,
        }


class LRUCache(Generic[K, V]):
    """
    Thread-safe LRU cache with TTL and size limits.

    Features:
    - LRU eviction policy
    - Time-to-live (TTL) per entry
    - Size-based eviction
    - Thread-safe operations
    - Optional persistence
    - Cache statistics
    """

    def __init__(
        self,
        max_size: int = 1000,
        max_bytes: int | None = None,
        default_ttl: float | None = None,
        on_evict: Callable[[K, V], None] | None = None,
        ttl_by_type: Dict[str, float] | None = None,
        enable_stats: bool = True,
    ) -> None:
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of entries
            max_bytes: Maximum total size in bytes (None = unlimited)
            default_ttl: Default time-to-live in seconds (None = no expiration)
            on_evict: Callback when entry is evicted
            ttl_by_type: TTL override by cache type (e.g., {"search": 300, "thumbnail": 3600})
            enable_stats: Enable detailed statistics tracking
        """
        self._max_size = max_size
        self._max_bytes = max_bytes
        self._default_ttl = default_ttl
        self._on_evict = on_evict
        self._ttl_by_type = ttl_by_type or {}
        self._enable_stats = enable_stats

        self._cache: OrderedDict[K, CacheEntry[V]] = OrderedDict()
        self._lock = threading.RLock()
        self._current_bytes = 0

        # Enhanced statistics
        self._stats = CacheStats(max_size=max_size, max_bytes=max_bytes)

        # Legacy counters (for backward compatibility)
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0

    def get(self, key: K, default: V | None = None) -> V | None:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default

        Raises:
            CacheExpiredError: If entry is expired (when default is None)
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                if self._enable_stats:
                    self._stats.misses += 1
                return default

            if entry.is_expired():
                self._expirations += 1
                if self._enable_stats:
                    self._stats.expirations += 1
                self._remove(key)
                if default is None:
                    raise CacheExpiredError(
                        f"Cache entry expired: {key}",
                        {"key": str(key)},
                    )
                return default

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.touch()
            self._hits += 1
            if self._enable_stats:
                self._stats.hits += 1

            return entry.value

    def set(
        self,
        key: K,
        value: V,
        ttl: float | None = None,
        size: int | None = None,
        cache_type: str = "default",
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default or type-specific)
            size: Size in bytes (None = auto-calculate)
            cache_type: Cache type for selective invalidation and TTL

        Raises:
            CacheFullError: If cache is full and cannot evict
        """
        # Determine TTL: explicit > type-specific > default
        if ttl is None:
            ttl = self._ttl_by_type.get(cache_type, self._default_ttl)

        if size is None:
            try:
                size = len(pickle.dumps(value))
            except Exception:
                size = 0

        with self._lock:
            # Remove old entry if exists
            if key in self._cache:
                old_entry = self._cache[key]
                self._current_bytes -= old_entry.size

            # Check if we need to evict
            while self._needs_eviction(size):
                if not self._evict_lru():
                    raise CacheFullError(
                        "Cache is full and cannot evict entries",
                        {
                            "max_size": self._max_size,
                            "max_bytes": self._max_bytes,
                            "current_size": len(self._cache),
                            "current_bytes": self._current_bytes,
                        },
                    )

            # Add new entry
            entry = CacheEntry(
                value=value,
                timestamp=time.time(),
                ttl=ttl,
                size=size,
                cache_type=cache_type,
            )
            self._cache[key] = entry
            self._cache.move_to_end(key)
            self._current_bytes += size

            if self._enable_stats:
                self._stats.sets += 1
                self._stats.size = len(self._cache)
                self._stats.bytes_used = self._current_bytes

    def delete(self, key: K) -> bool:
        """
        Delete entry from cache.

        Args:
            key: Cache key

        Returns:
            True if entry was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                self._remove(key)
                if self._enable_stats:
                    self._stats.deletes += 1
                    self._stats.size = len(self._cache)
                    self._stats.bytes_used = self._current_bytes
                return True
            return False

    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            self._cache.clear()
            self._current_bytes = 0
            logger.info("Cache cleared")

    def cleanup(self) -> int:
        """
        Remove expired entries.

        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]

            for key in expired_keys:
                self._remove(key)
                self._expirations += 1

            if expired_keys:
                logger.debug(
                    "Cleaned up expired entries",
                    count=len(expired_keys),
                )

            return len(expired_keys)

    def _needs_eviction(self, new_size: int) -> bool:
        """Check if eviction is needed."""
        if len(self._cache) >= self._max_size:
            return True

        if self._max_bytes is not None:
            if self._current_bytes + new_size > self._max_bytes:
                return True

        return False

    def _evict_lru(self) -> bool:
        """
        Evict least recently used entry.

        Returns:
            True if entry was evicted, False if cache is empty
        """
        if not self._cache:
            return False

        # Get least recently used (first item)
        key = next(iter(self._cache))
        self._remove(key)
        self._evictions += 1

        if self._enable_stats:
            self._stats.evictions += 1

        return True

    def _remove(self, key: K) -> None:
        """Remove entry and update statistics."""
        entry = self._cache.pop(key)
        self._current_bytes -= entry.size

        if self._on_evict:
            try:
                self._on_evict(key, entry.value)
            except Exception as e:
                logger.error(
                    "Error in eviction callback",
                    key=str(key),
                    error=str(e),
                )

    def contains(self, key: K) -> bool:
        """
        Check if key exists and is not expired.

        Args:
            key: Cache key

        Returns:
            True if key exists and is valid
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            if entry.is_expired():
                self._remove(key)
                return False
            return True

    def size(self) -> int:
        """Get number of entries in cache."""
        with self._lock:
            return len(self._cache)

    def bytes_used(self) -> int:
        """Get total bytes used by cache."""
        with self._lock:
            return self._current_bytes

    def invalidate_by_type(self, cache_type: str) -> int:
        """
        Invalidate all entries of a specific type.

        Args:
            cache_type: Cache type to invalidate

        Returns:
            Number of entries removed
        """
        with self._lock:
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if entry.cache_type == cache_type
            ]

            for key in keys_to_remove:
                self._remove(key)

            logger.debug(
                f"Invalidated cache type '{cache_type}'",
                count=len(keys_to_remove),
            )

            return len(keys_to_remove)

    def invalidate_by_pattern(self, pattern_func: Callable[[K], bool]) -> int:
        """
        Invalidate entries matching a pattern function.

        Args:
            pattern_func: Function that returns True for keys to invalidate

        Returns:
            Number of entries removed
        """
        with self._lock:
            keys_to_remove = [
                key for key in self._cache.keys()
                if pattern_func(key)
            ]

            for key in keys_to_remove:
                self._remove(key)

            logger.debug(
                "Invalidated by pattern",
                count=len(keys_to_remove),
            )

            return len(keys_to_remove)

    def prewarm(
        self,
        data: Dict[K, V],
        cache_type: str = "default",
        ttl: float | None = None,
    ) -> int:
        """
        Prewarm cache with multiple entries.

        Useful for loading frequently-used data at startup.

        Args:
            data: Dictionary of key-value pairs to cache
            cache_type: Cache type for all entries
            ttl: TTL for all entries (None = use default)

        Returns:
            Number of entries added
        """
        count = 0
        for key, value in data.items():
            try:
                self.set(key, value, ttl=ttl, cache_type=cache_type)
                count += 1
            except Exception as e:
                logger.warning(
                    f"Failed to prewarm cache entry: {key}",
                    error=str(e),
                )

        logger.info(
            f"Prewarmed cache with {count}/{len(data)} entries",
            cache_type=cache_type,
        )

        return count

    def get_detailed_stats(self) -> CacheStats:
        """
        Get detailed cache statistics.

        Returns:
            CacheStats object with comprehensive metrics
        """
        with self._lock:
            # Update current state
            self._stats.size = len(self._cache)
            self._stats.bytes_used = self._current_bytes

            return self._stats

    def stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with statistics (legacy compatibility)
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            stats_dict = {
                "size": len(self._cache),
                "max_size": self._max_size,
                "bytes_used": self._current_bytes,
                "max_bytes": self._max_bytes,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "evictions": self._evictions,
                "expirations": self._expirations,
            }

            # Add detailed stats if enabled
            if self._enable_stats:
                stats_dict.update(self._stats.to_dict())

            return stats_dict

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            self._expirations = 0

            if self._enable_stats:
                self._stats = CacheStats(
                    max_size=self._max_size,
                    max_bytes=self._max_bytes,
                    size=len(self._cache),
                    bytes_used=self._current_bytes,
                )

    def save(self, path: Path | str) -> None:
        """
        Save cache to disk.

        Args:
            path: Path to save file

        Raises:
            CacheError: If save fails
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with self._lock:
                # Clean up expired entries first
                self.cleanup()

                data = {
                    "cache": dict(self._cache),
                    "current_bytes": self._current_bytes,
                    "stats": {
                        "hits": self._hits,
                        "misses": self._misses,
                        "evictions": self._evictions,
                        "expirations": self._expirations,
                    },
                }

                with open(path, "wb") as f:
                    pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

                logger.info("Cache saved", path=str(path), size=len(self._cache))

        except Exception as e:
            raise CacheError(
                f"Failed to save cache: {e}",
                {"path": str(path)},
            ) from e

    def load(self, path: Path | str) -> None:
        """
        Load cache from disk.

        Args:
            path: Path to load file

        Raises:
            CacheError: If load fails
        """
        path = Path(path)

        if not path.exists():
            logger.warning("Cache file not found", path=str(path))
            return

        try:
            with open(path, "rb") as f:
                data = pickle.load(f)

            with self._lock:
                self._cache = OrderedDict(data["cache"])
                self._current_bytes = data["current_bytes"]

                stats = data.get("stats", {})
                self._hits = stats.get("hits", 0)
                self._misses = stats.get("misses", 0)
                self._evictions = stats.get("evictions", 0)
                self._expirations = stats.get("expirations", 0)

                # Clean up any expired entries
                self.cleanup()

                logger.info("Cache loaded", path=str(path), size=len(self._cache))

        except Exception as e:
            raise CacheError(
                f"Failed to load cache: {e}",
                {"path": str(path)},
            ) from e

    def __len__(self) -> int:
        """Get number of entries."""
        return self.size()

    def __contains__(self, key: K) -> bool:
        """Check if key exists."""
        return self.contains(key)

    def __getitem__(self, key: K) -> V:
        """Get item by key."""
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key: K, value: V) -> None:
        """Set item by key."""
        self.set(key, value)

    def __delitem__(self, key: K) -> None:
        """Delete item by key."""
        if not self.delete(key):
            raise KeyError(key)


class CacheManager:
    """
    Manager for multiple named caches.

    Provides centralized cache management with automatic cleanup.
    """

    def __init__(self) -> None:
        """Initialize cache manager."""
        self._caches: dict[str, LRUCache[Any, Any]] = {}
        self._lock = threading.Lock()
        self._cleanup_thread: threading.Thread | None = None
        self._cleanup_interval = 300  # 5 minutes
        self._running = False

    def get_cache(
        self,
        name: str,
        max_size: int = 1000,
        max_bytes: int | None = None,
        default_ttl: float | None = None,
    ) -> LRUCache[Any, Any]:
        """
        Get or create a named cache.

        Args:
            name: Cache name
            max_size: Maximum number of entries
            max_bytes: Maximum total size in bytes
            default_ttl: Default time-to-live in seconds

        Returns:
            LRUCache instance
        """
        with self._lock:
            if name not in self._caches:
                self._caches[name] = LRUCache(
                    max_size=max_size,
                    max_bytes=max_bytes,
                    default_ttl=default_ttl,
                )
                logger.debug("Created cache", name=name)

            return self._caches[name]

    def remove_cache(self, name: str) -> None:
        """
        Remove a named cache.

        Args:
            name: Cache name
        """
        with self._lock:
            if name in self._caches:
                del self._caches[name]
                logger.debug("Removed cache", name=name)

    def clear_all(self) -> None:
        """Clear all caches."""
        with self._lock:
            for cache in self._caches.values():
                cache.clear()
            logger.info("All caches cleared")

    def cleanup_all(self) -> None:
        """Run cleanup on all caches."""
        with self._lock:
            total_cleaned = 0
            for name, cache in self._caches.items():
                cleaned = cache.cleanup()
                if cleaned > 0:
                    logger.debug(
                        "Cleaned cache",
                        name=name,
                        count=cleaned,
                    )
                total_cleaned += cleaned

            if total_cleaned > 0:
                logger.info("Cleanup completed", total=total_cleaned)

    def stats_all(self) -> dict[str, dict[str, Any]]:
        """
        Get statistics for all caches.

        Returns:
            Dictionary mapping cache names to statistics
        """
        with self._lock:
            return {name: cache.stats() for name, cache in self._caches.items()}

    def start_cleanup_thread(self, interval: int = 300) -> None:
        """
        Start automatic cleanup thread.

        Args:
            interval: Cleanup interval in seconds
        """
        if self._running:
            logger.warning("Cleanup thread already running")
            return

        self._cleanup_interval = interval
        self._running = True
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="CacheCleanup",
        )
        self._cleanup_thread.start()
        logger.info("Cache cleanup thread started", interval=interval)

    def stop_cleanup_thread(self) -> None:
        """Stop automatic cleanup thread."""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
            self._cleanup_thread = None
            logger.info("Cache cleanup thread stopped")

    def _cleanup_loop(self) -> None:
        """Cleanup loop for background thread."""
        while self._running:
            time.sleep(self._cleanup_interval)
            if self._running:
                try:
                    self.cleanup_all()
                except Exception as e:
                    logger.error("Error in cleanup loop", error=str(e))


# Global cache manager instance
_cache_manager = CacheManager()


def get_cache(
    name: str,
    max_size: int = 1000,
    max_bytes: int | None = None,
    default_ttl: float | None = None,
) -> LRUCache[Any, Any]:
    """
    Get or create a named cache (convenience function).

    Args:
        name: Cache name
        max_size: Maximum number of entries
        max_bytes: Maximum total size in bytes
        default_ttl: Default time-to-live in seconds

    Returns:
        LRUCache instance
    """
    return _cache_manager.get_cache(name, max_size, max_bytes, default_ttl)
