"""
File Categorization Engine - iOS-style file categorization
Scans directories and categorizes files efficiently
"""

import os
import mimetypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime
import threading
from collections import defaultdict

from categories import FileCategory, classify_by_extension
from utils import format_file_size


@dataclass
class CategoryData:
    """Data for a file category"""
    category: FileCategory
    file_count: int = 0
    total_size: int = 0
    files: List[Dict] = field(default_factory=list)
    recent_files: List[Dict] = field(default_factory=list)

    def add_file(self, file_info: Dict):
        """Add file to category"""
        self.file_count += 1
        self.total_size += file_info.get('size', 0)
        self.files.append(file_info)

        # Keep recent files sorted by modification time
        self.recent_files.append(file_info)
        self.recent_files.sort(key=lambda x: x.get('modified', 0), reverse=True)
        self.recent_files = self.recent_files[:50]  # Keep top 50

    @property
    def formatted_size(self) -> str:
        """Get formatted total size"""
        return format_file_size(self.total_size)

    @property
    def average_size(self) -> int:
        """Get average file size"""
        return self.total_size // self.file_count if self.file_count > 0 else 0


class CategoryScanner:
    """
    iOS-style file categorization engine
    Scans directories and categorizes files by type
    """

    # iOS-inspired category mapping
    IOS_CATEGORIES = {
        'photos': FileCategory.IMAGENES,
        'videos': FileCategory.VIDEOS,
        'music': FileCategory.AUDIO,
        'documents': FileCategory.DOCUMENTOS,
        'archives': FileCategory.COMPRIMIDOS,
        'applications': FileCategory.EJECUTABLES,
        'code': FileCategory.CODIGO,
        'data': FileCategory.DATOS,
        'other': FileCategory.OTROS,
    }

    def __init__(self, cache_enabled: bool = True):
        """
        Initialize category scanner

        Args:
            cache_enabled: Enable result caching
        """
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, Dict[FileCategory, CategoryData]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._lock = threading.Lock()

        # Initialize MIME types
        mimetypes.init()

    def scan_directory(self, path: str,
                      max_depth: int = -1,
                      include_hidden: bool = False,
                      follow_symlinks: bool = False) -> Dict[FileCategory, CategoryData]:
        """
        Scan directory and categorize files

        Args:
            path: Directory path to scan
            max_depth: Maximum recursion depth (-1 for unlimited)
            include_hidden: Include hidden files
            follow_symlinks: Follow symbolic links

        Returns:
            Dictionary mapping FileCategory to CategoryData
        """
        path = os.path.abspath(path)

        # Check cache
        if self.cache_enabled and path in self._cache:
            cache_time = self._cache_timestamps.get(path, 0)
            if (datetime.now().timestamp() - cache_time) < 300:  # 5 min cache
                return self._cache[path]

        # Initialize categories
        categories: Dict[FileCategory, CategoryData] = {
            cat: CategoryData(category=cat) for cat in FileCategory
        }

        # Scan directory
        self._scan_recursive(
            path, categories, 0, max_depth,
            include_hidden, follow_symlinks
        )

        # Update cache
        if self.cache_enabled:
            with self._lock:
                self._cache[path] = categories
                self._cache_timestamps[path] = datetime.now().timestamp()

        return categories

    def _scan_recursive(self, path: str,
                       categories: Dict[FileCategory, CategoryData],
                       current_depth: int,
                       max_depth: int,
                       include_hidden: bool,
                       follow_symlinks: bool):
        """Recursively scan directory"""
        if max_depth >= 0 and current_depth > max_depth:
            return

        try:
            entries = os.scandir(path)
        except (PermissionError, OSError):
            return

        for entry in entries:
            try:
                # Skip hidden files if needed
                if not include_hidden and entry.name.startswith('.'):
                    continue

                # Handle symlinks
                if entry.is_symlink() and not follow_symlinks:
                    continue

                # Process files
                if entry.is_file():
                    self._process_file(entry, categories)

                # Recurse into directories
                elif entry.is_dir():
                    self._scan_recursive(
                        entry.path, categories,
                        current_depth + 1, max_depth,
                        include_hidden, follow_symlinks
                    )

            except (PermissionError, OSError):
                continue

    def _process_file(self, entry: os.DirEntry,
                     categories: Dict[FileCategory, CategoryData]):
        """Process a single file"""
        try:
            stat = entry.stat()
            ext = Path(entry.name).suffix

            # Classify by extension first
            category = classify_by_extension(ext)

            # Verify with MIME type for accuracy
            mime_type, _ = mimetypes.guess_type(entry.path)
            if mime_type:
                category = self._refine_category_by_mime(category, mime_type)

            # Create file info
            file_info = {
                'name': entry.name,
                'path': entry.path,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'accessed': stat.st_atime,
                'created': stat.st_ctime,
                'extension': ext,
                'mime_type': mime_type,
            }

            # Add to category
            categories[category].add_file(file_info)

        except (PermissionError, OSError):
            pass

    def _refine_category_by_mime(self,
                                 category: FileCategory,
                                 mime_type: str) -> FileCategory:
        """
        Refine category using MIME type
        Provides more accurate categorization than extension alone
        """
        mime_main = mime_type.split('/')[0].lower()

        # Override if MIME type is more specific
        if mime_main == 'image':
            return FileCategory.IMAGENES
        elif mime_main == 'video':
            return FileCategory.VIDEOS
        elif mime_main == 'audio':
            return FileCategory.AUDIO
        elif mime_main == 'text':
            # Text files could be documents or code
            if 'html' in mime_type or 'xml' in mime_type:
                return FileCategory.CODIGO
            return FileCategory.DOCUMENTOS
        elif 'application/pdf' in mime_type:
            return FileCategory.DOCUMENTOS
        elif 'application/zip' in mime_type or 'compressed' in mime_type:
            return FileCategory.COMPRIMIDOS
        elif 'application/x-executable' in mime_type:
            return FileCategory.EJECUTABLES

        return category

    def get_recent_files(self,
                        categories: Dict[FileCategory, CategoryData],
                        limit: int = 20) -> List[Dict]:
        """
        Get most recently modified files across all categories

        Args:
            categories: Category data dictionary
            limit: Maximum number of files to return

        Returns:
            List of recent file info dictionaries
        """
        all_files = []
        for category_data in categories.values():
            all_files.extend(category_data.files)

        # Sort by modification time
        all_files.sort(key=lambda x: x.get('modified', 0), reverse=True)

        return all_files[:limit]

    def get_favorites(self,
                     favorites_paths: Set[str],
                     categories: Dict[FileCategory, CategoryData]) -> List[Dict]:
        """
        Get favorite files from categories

        Args:
            favorites_paths: Set of favorite file paths
            categories: Category data dictionary

        Returns:
            List of favorite file info dictionaries
        """
        favorites = []
        for category_data in categories.values():
            for file_info in category_data.files:
                if file_info['path'] in favorites_paths:
                    favorites.append(file_info)

        return favorites

    def search_in_category(self,
                          category: FileCategory,
                          categories: Dict[FileCategory, CategoryData],
                          query: str) -> List[Dict]:
        """
        Search for files within a category

        Args:
            category: Category to search in
            categories: Category data dictionary
            query: Search query

        Returns:
            List of matching file info dictionaries
        """
        query_lower = query.lower()
        category_data = categories.get(category)

        if not category_data:
            return []

        results = []
        for file_info in category_data.files:
            if query_lower in file_info['name'].lower():
                results.append(file_info)

        return results

    def get_category_breakdown(self,
                              categories: Dict[FileCategory, CategoryData]) -> Dict:
        """
        Get statistical breakdown of categories

        Args:
            categories: Category data dictionary

        Returns:
            Dictionary with statistics
        """
        total_files = sum(c.file_count for c in categories.values())
        total_size = sum(c.total_size for c in categories.values())

        breakdown = {
            'total_files': total_files,
            'total_size': total_size,
            'formatted_size': format_file_size(total_size),
            'categories': {}
        }

        for category, data in categories.items():
            if data.file_count > 0:
                breakdown['categories'][category.value] = {
                    'count': data.file_count,
                    'size': data.total_size,
                    'formatted_size': data.formatted_size,
                    'percentage': (data.file_count / total_files * 100) if total_files > 0 else 0,
                    'average_size': data.average_size,
                }

        return breakdown

    def clear_cache(self, path: Optional[str] = None):
        """
        Clear cache for a path or all paths

        Args:
            path: Path to clear (None for all)
        """
        with self._lock:
            if path:
                self._cache.pop(path, None)
                self._cache_timestamps.pop(path, None)
            else:
                self._cache.clear()
                self._cache_timestamps.clear()

    def get_downloads_category(self, user_profile: Optional[str] = None) -> CategoryData:
        """
        Get special Downloads category

        Args:
            user_profile: User profile path (defaults to current user)

        Returns:
            CategoryData for downloads folder
        """
        if user_profile is None:
            user_profile = os.environ.get('USERPROFILE', os.path.expanduser('~'))

        downloads_path = os.path.join(user_profile, 'Downloads')

        if not os.path.exists(downloads_path):
            return CategoryData(category=FileCategory.OTROS)

        # Scan downloads directory (non-recursive for speed)
        categories = self.scan_directory(downloads_path, max_depth=0)

        # Combine all categories into one
        combined = CategoryData(category=FileCategory.OTROS)
        for category_data in categories.values():
            combined.file_count += category_data.file_count
            combined.total_size += category_data.total_size
            combined.files.extend(category_data.files)

        return combined


# Background scanner for non-blocking operations
class BackgroundScanner(threading.Thread):
    """Background thread for scanning directories"""

    def __init__(self, scanner: CategoryScanner, path: str, callback):
        """
        Initialize background scanner

        Args:
            scanner: CategoryScanner instance
            path: Path to scan
            callback: Callback function(categories: Dict[FileCategory, CategoryData])
        """
        super().__init__(daemon=True)
        self.scanner = scanner
        self.path = path
        self.callback = callback
        self._stop_event = threading.Event()

    def run(self):
        """Run scan in background"""
        try:
            categories = self.scanner.scan_directory(self.path)
            if not self._stop_event.is_set():
                self.callback(categories)
        except Exception as e:
            print(f"Background scan error: {e}")

    def stop(self):
        """Stop background scan"""
        self._stop_event.set()


if __name__ == '__main__':
    # Test the scanner
    import sys

    print("=== iOS-style Category Scanner ===\n")

    scanner = CategoryScanner()

    # Scan current user's Documents folder
    user_profile = os.environ.get('USERPROFILE', os.path.expanduser('~'))
    test_path = os.path.join(user_profile, 'Documents')

    if os.path.exists(test_path):
        print(f"Scanning: {test_path}\n")

        categories = scanner.scan_directory(test_path, max_depth=2)

        # Show breakdown
        breakdown = scanner.get_category_breakdown(categories)

        print(f"Total Files: {breakdown['total_files']}")
        print(f"Total Size: {breakdown['formatted_size']}\n")

        print("Category Breakdown:")
        for cat_name, stats in breakdown['categories'].items():
            print(f"  {cat_name:15} {stats['count']:6} files  "
                  f"{stats['formatted_size']:>10}  ({stats['percentage']:.1f}%)")

        # Show recent files
        print("\nRecent Files:")
        recent = scanner.get_recent_files(categories, limit=5)
        for file_info in recent:
            dt = datetime.fromtimestamp(file_info['modified'])
            print(f"  {file_info['name'][:40]:40} {dt.strftime('%Y-%m-%d %H:%M')}")

    else:
        print(f"Path not found: {test_path}")
