"""
Preview manager with caching and async support.

Coordinates all preview generation, handles caching, and provides
a unified interface for all file types with auto-detected optimal workers.
"""

import os
import sys
import logging
import hashlib
import json
import asyncio
from typing import Optional, Dict, Any, Callable
from pathlib import Path
from datetime import datetime, timedelta
import threading

# Add parent directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.threading import create_mixed_executor, ManagedThreadPoolExecutor

from .text_preview import TextPreviewer
from .image_preview import ImagePreviewer
from .document_preview import DocumentPreviewer
from .media_preview import MediaPreviewer
from .archive_preview import ArchivePreviewer
from .metadata import MetadataExtractor

logger = logging.getLogger(__name__)


class PreviewManager:
    """
    Manages preview generation with caching.

    Features:
    - Automatic format detection
    - In-memory and disk caching
    - Async preview generation
    - Extensible preview system
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        memory_cache_size: int = 100,
        cache_ttl_hours: int = 24,
        max_workers: Optional[int] = None
    ):
        """
        Initialize preview manager with auto-detected optimal workers.

        Args:
            cache_dir: Directory for disk cache (None = no disk cache)
            memory_cache_size: Maximum items in memory cache
            cache_ttl_hours: Cache time-to-live in hours
            max_workers: Maximum worker threads for async operations (None = auto-detect for mixed workload)
        """
        self.cache_dir = cache_dir
        self.memory_cache_size = memory_cache_size
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.max_workers = max_workers

        # Initialize previewers
        self.text_previewer = TextPreviewer()
        self.image_previewer = ImagePreviewer()
        self.document_previewer = DocumentPreviewer()
        self.media_previewer = MediaPreviewer()
        self.archive_previewer = ArchivePreviewer()
        self.metadata_extractor = MetadataExtractor()

        # Memory cache: {file_hash: (preview_data, timestamp)}
        self._memory_cache: Dict[str, tuple[Dict[str, Any], datetime]] = {}
        self._cache_lock = threading.Lock()

        # Thread pool for async operations (mixed I/O and CPU for preview generation)
        self._executor = create_mixed_executor(
            max_workers=max_workers,
            thread_name_prefix="Preview"
        )

        # Create cache directory
        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)

        logger.info(f"PreviewManager initialized with cache_dir={cache_dir}")

    def get_preview(
        self,
        file_path: str,
        include_metadata: bool = True,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get preview for file.

        Args:
            file_path: Path to file
            include_metadata: Include extended metadata
            use_cache: Use cached preview if available

        Returns:
            Dictionary containing preview data
        """
        if not os.path.exists(file_path):
            return {'error': 'File not found'}

        # Generate cache key
        cache_key = self._get_cache_key(file_path)

        # Check cache
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached:
                logger.debug(f"Cache hit for {file_path}")
                return cached

        # Generate preview
        preview = self._generate_preview(file_path)

        # Add metadata if requested
        if include_metadata and 'error' not in preview:
            metadata = self.metadata_extractor.extract(file_path)
            preview['metadata'] = metadata

        # Cache result
        if use_cache and 'error' not in preview:
            self._save_to_cache(cache_key, preview)

        return preview

    async def get_preview_async(
        self,
        file_path: str,
        include_metadata: bool = True,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get preview asynchronously.

        Args:
            file_path: Path to file
            include_metadata: Include extended metadata
            use_cache: Use cached preview if available

        Returns:
            Dictionary containing preview data
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.get_preview,
            file_path,
            include_metadata,
            use_cache
        )

    def _generate_preview(self, file_path: str) -> Dict[str, Any]:
        """
        Generate preview based on file type.

        Args:
            file_path: Path to file

        Returns:
            Preview data dictionary
        """
        ext = Path(file_path).suffix.lower()

        # Detect file type and route to appropriate previewer
        try:
            # Images
            if self.image_previewer.is_supported(file_path):
                return self.image_previewer.generate_preview(file_path)

            # Documents (PDF, Office)
            elif self.document_previewer.is_supported(file_path):
                return self.document_previewer.generate_preview(file_path)

            # Media (audio, video)
            elif self.media_previewer.is_supported(file_path):
                return self.media_previewer.generate_preview(file_path)

            # Archives
            elif self.archive_previewer.is_supported(file_path):
                return self.archive_previewer.generate_preview(file_path)

            # Text files
            elif self.text_previewer.is_text_file(file_path):
                return self.text_previewer.generate_preview(file_path)

            else:
                # Fallback: basic file info
                return {
                    'type': 'unknown',
                    'file_size': os.path.getsize(file_path),
                    'extension': ext,
                }

        except Exception as e:
            logger.error(f"Error generating preview for {file_path}: {e}")
            return {'error': str(e)}

    def _get_cache_key(self, file_path: str) -> str:
        """
        Generate cache key for file.

        Uses file path and modification time to invalidate cache
        when file changes.

        Args:
            file_path: Path to file

        Returns:
            Cache key string
        """
        try:
            mtime = os.path.getmtime(file_path)
            key_data = f"{file_path}:{mtime}"
            return hashlib.md5(key_data.encode()).hexdigest()
        except Exception:
            # Fallback to just path
            return hashlib.md5(file_path.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get preview from cache.

        Args:
            cache_key: Cache key

        Returns:
            Cached preview data or None
        """
        # Check memory cache
        with self._cache_lock:
            if cache_key in self._memory_cache:
                data, timestamp = self._memory_cache[cache_key]

                # Check if expired
                if datetime.now() - timestamp < self.cache_ttl:
                    return data.copy()
                else:
                    # Remove expired entry
                    del self._memory_cache[cache_key]

        # Check disk cache
        if self.cache_dir:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            if os.path.exists(cache_file):
                try:
                    # Check if expired
                    file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
                    if file_age < self.cache_ttl:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        # Add to memory cache
                        with self._cache_lock:
                            self._add_to_memory_cache(cache_key, data)

                        return data
                    else:
                        # Remove expired cache file
                        os.remove(cache_file)
                except Exception as e:
                    logger.debug(f"Error reading cache file: {e}")

        return None

    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """
        Save preview to cache.

        Args:
            cache_key: Cache key
            data: Preview data to cache
        """
        # Save to memory cache
        with self._cache_lock:
            self._add_to_memory_cache(cache_key, data)

        # Save to disk cache
        if self.cache_dir:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            try:
                # Create a serializable copy (remove non-serializable objects)
                serializable_data = self._make_serializable(data)

                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(serializable_data, f, indent=2)
            except Exception as e:
                logger.debug(f"Error saving to disk cache: {e}")

    def _add_to_memory_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """
        Add item to memory cache with LRU eviction.

        Args:
            cache_key: Cache key
            data: Data to cache
        """
        # Remove oldest items if cache is full
        if len(self._memory_cache) >= self.memory_cache_size:
            # Find oldest item
            oldest_key = min(
                self._memory_cache.keys(),
                key=lambda k: self._memory_cache[k][1]
            )
            del self._memory_cache[oldest_key]

        # Add new item
        self._memory_cache[cache_key] = (data.copy(), datetime.now())

    def _make_serializable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make data JSON-serializable by removing problematic types.

        Args:
            data: Data dictionary

        Returns:
            Serializable copy of data
        """
        result = {}
        for key, value in data.items():
            try:
                # Skip non-serializable types
                if isinstance(value, (str, int, float, bool, type(None))):
                    result[key] = value
                elif isinstance(value, dict):
                    result[key] = self._make_serializable(value)
                elif isinstance(value, (list, tuple)):
                    result[key] = [
                        self._make_serializable(item) if isinstance(item, dict) else item
                        for item in value
                    ]
                else:
                    # Convert to string
                    result[key] = str(value)
            except Exception:
                # Skip problematic values
                pass

        return result

    def clear_cache(self, memory_only: bool = False) -> None:
        """
        Clear preview cache.

        Args:
            memory_only: Only clear memory cache, not disk cache
        """
        with self._cache_lock:
            self._memory_cache.clear()

        if not memory_only and self.cache_dir:
            try:
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.json'):
                        file_path = os.path.join(self.cache_dir, filename)
                        os.remove(file_path)
                logger.info("Disk cache cleared")
            except Exception as e:
                logger.error(f"Error clearing disk cache: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self._cache_lock:
            memory_items = len(self._memory_cache)

        disk_items = 0
        disk_size = 0

        if self.cache_dir and os.path.exists(self.cache_dir):
            try:
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.json'):
                        disk_items += 1
                        file_path = os.path.join(self.cache_dir, filename)
                        disk_size += os.path.getsize(file_path)
            except Exception:
                pass

        return {
            'memory_items': memory_items,
            'memory_capacity': self.memory_cache_size,
            'disk_items': disk_items,
            'disk_size_bytes': disk_size,
            'disk_size_mb': round(disk_size / (1024 * 1024), 2),
        }

    def preload_previews(
        self,
        file_paths: list[str],
        callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> None:
        """
        Preload previews for multiple files in background.

        Args:
            file_paths: List of file paths to preload
            callback: Optional callback function(file_path, preview_data)
        """
        def preload_worker(path: str):
            try:
                preview = self.get_preview(path)
                if callback:
                    callback(path, preview)
            except Exception as e:
                logger.error(f"Error preloading preview for {path}: {e}")

        for file_path in file_paths:
            self._executor.submit(preload_worker, file_path)

    def shutdown(self) -> None:
        """Shutdown the preview manager and cleanup resources."""
        self._executor.shutdown(wait=True)
        logger.info("PreviewManager shutdown complete")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
