"""
Archive Analyzer
Scan and analyze archive contents without extraction
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from .sevenzip_manager import SevenZipManager


@dataclass
class ArchiveStats:
    """Statistics for an archive"""
    total_files: int = 0
    total_folders: int = 0
    total_size: int = 0
    packed_size: int = 0
    compression_ratio: float = 0.0
    encrypted_files: int = 0
    nested_archives: List[str] = field(default_factory=list)
    file_types: Dict[str, int] = field(default_factory=dict)
    largest_files: List[Tuple[str, int]] = field(default_factory=list)
    depth: int = 0
    is_encrypted: bool = False


class ArchiveAnalyzer:
    """
    Analyze archive contents without extraction:
    - Calculate total uncompressed size
    - Count files and folders
    - Detect nested archives
    - Identify encrypted entries
    - Get compression ratio
    - Preview file list as tree
    - Generate statistics
    """

    def __init__(self):
        """Initialize archive analyzer"""
        self.seven_zip = SevenZipManager()

    def analyze(
        self,
        archive_path: str,
        password: Optional[str] = None,
        detect_nested: bool = True
    ) -> ArchiveStats:
        """
        Analyze archive and return statistics

        Args:
            archive_path: Path to archive
            password: Password for encrypted archives
            detect_nested: Detect nested archives

        Returns:
            Archive statistics
        """
        stats = ArchiveStats()

        try:
            # Get archive contents
            entries = self.seven_zip.list_contents(archive_path, password=password)

            for entry in entries:
                path = entry.get('Path', '')
                size = entry.get('Size', 0)
                packed = entry.get('PackedSize', 0)
                is_dir = entry.get('IsDirectory', False)
                attrs = entry.get('Attributes', '')

                if is_dir:
                    stats.total_folders += 1
                else:
                    stats.total_files += 1
                    stats.total_size += size
                    stats.packed_size += packed

                    # Check encryption
                    if entry.get('Encrypted', 'no') == 'yes' or '+' in attrs:
                        stats.encrypted_files += 1
                        stats.is_encrypted = True

                    # Track file types
                    ext = Path(path).suffix.lower()
                    if ext:
                        stats.file_types[ext] = stats.file_types.get(ext, 0) + 1
                    else:
                        stats.file_types['[no extension]'] = stats.file_types.get('[no extension]', 0) + 1

                    # Track largest files (top 10)
                    stats.largest_files.append((path, size))

                    # Detect nested archives
                    if detect_nested and self.seven_zip.is_archive(path):
                        stats.nested_archives.append(path)

            # Sort largest files
            stats.largest_files.sort(key=lambda x: x[1], reverse=True)
            stats.largest_files = stats.largest_files[:10]

            # Calculate compression ratio
            if stats.total_size > 0:
                stats.compression_ratio = (1 - (stats.packed_size / stats.total_size)) * 100

            # Calculate depth
            if stats.nested_archives:
                stats.depth = self._calculate_max_depth(entries)

            return stats

        except ValueError as e:
            # Likely wrong password
            stats.is_encrypted = True
            raise e
        except Exception as e:
            raise RuntimeError(f"Analysis failed: {str(e)}")

    def _calculate_max_depth(self, entries: List[Dict]) -> int:
        """Calculate maximum directory depth"""
        max_depth = 0

        for entry in entries:
            path = entry.get('Path', '')
            if path:
                depth = path.count(os.sep) + path.count('/')
                max_depth = max(max_depth, depth)

        return max_depth

    def get_file_tree(
        self,
        archive_path: str,
        password: Optional[str] = None,
        max_items: int = 1000
    ) -> Dict[str, any]:
        """
        Get file tree structure

        Args:
            archive_path: Path to archive
            password: Password
            max_items: Maximum items to include

        Returns:
            Tree structure
        """
        try:
            entries = self.seven_zip.list_contents(archive_path, password=password)

            # Build tree
            tree = {'name': os.path.basename(archive_path), 'children': [], 'type': 'archive'}

            for idx, entry in enumerate(entries):
                if idx >= max_items:
                    tree['children'].append({
                        'name': f'... and {len(entries) - max_items} more items',
                        'type': 'truncated'
                    })
                    break

                path = entry.get('Path', '')
                is_dir = entry.get('IsDirectory', False)
                size = entry.get('Size', 0)

                self._add_to_tree(tree, path, is_dir, size)

            return tree

        except Exception as e:
            return {
                'name': os.path.basename(archive_path),
                'error': str(e),
                'type': 'error'
            }

    def _add_to_tree(self, tree: Dict, path: str, is_dir: bool, size: int):
        """Add path to tree structure"""
        parts = path.replace('\\', '/').split('/')

        current = tree
        for part in parts[:-1]:
            # Find or create folder
            found = False
            for child in current.get('children', []):
                if child.get('name') == part and child.get('type') == 'folder':
                    current = child
                    found = True
                    break

            if not found:
                new_folder = {'name': part, 'children': [], 'type': 'folder'}
                current.setdefault('children', []).append(new_folder)
                current = new_folder

        # Add final item
        if parts:
            item = {
                'name': parts[-1],
                'type': 'folder' if is_dir else 'file',
                'size': size
            }

            if is_dir:
                item['children'] = []

            current.setdefault('children', []).append(item)

    def preview_as_text(
        self,
        archive_path: str,
        password: Optional[str] = None,
        max_items: int = 100
    ) -> str:
        """
        Generate text preview of archive contents

        Args:
            archive_path: Path to archive
            password: Password
            max_items: Maximum items to show

        Returns:
            Formatted text preview
        """
        try:
            entries = self.seven_zip.list_contents(archive_path, password=password)

            lines = [
                f"Archive: {os.path.basename(archive_path)}",
                "=" * 80,
                ""
            ]

            for idx, entry in enumerate(entries[:max_items]):
                path = entry.get('Path', '')
                size = entry.get('Size', 0)
                is_dir = entry.get('IsDirectory', False)

                # Format size
                size_str = self._format_size(size) if not is_dir else '<DIR>'

                # Format line
                line = f"  {size_str:>12}  {path}"
                lines.append(line)

            if len(entries) > max_items:
                lines.append("")
                lines.append(f"... and {len(entries) - max_items} more items")

            return '\n'.join(lines)

        except Exception as e:
            return f"Error previewing archive: {str(e)}"

    def _format_size(self, size: int) -> str:
        """Format size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def compare_archives(
        self,
        archive1: str,
        archive2: str,
        password1: Optional[str] = None,
        password2: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Compare two archives

        Args:
            archive1: First archive
            archive2: Second archive
            password1: Password for first archive
            password2: Password for second archive

        Returns:
            Comparison results
        """
        try:
            stats1 = self.analyze(archive1, password=password1, detect_nested=False)
            stats2 = self.analyze(archive2, password=password2, detect_nested=False)

            entries1 = set(e.get('Path', '') for e in self.seven_zip.list_contents(archive1, password1))
            entries2 = set(e.get('Path', '') for e in self.seven_zip.list_contents(archive2, password2))

            only_in_1 = entries1 - entries2
            only_in_2 = entries2 - entries1
            common = entries1 & entries2

            return {
                'archive1': {
                    'name': os.path.basename(archive1),
                    'files': stats1.total_files,
                    'size': stats1.total_size,
                    'compression_ratio': stats1.compression_ratio
                },
                'archive2': {
                    'name': os.path.basename(archive2),
                    'files': stats2.total_files,
                    'size': stats2.total_size,
                    'compression_ratio': stats2.compression_ratio
                },
                'common_files': len(common),
                'only_in_archive1': len(only_in_1),
                'only_in_archive2': len(only_in_2),
                'unique_to_1': list(only_in_1)[:50],  # Sample
                'unique_to_2': list(only_in_2)[:50]   # Sample
            }

        except Exception as e:
            return {'error': str(e)}

    def find_duplicates_in_archive(
        self,
        archive_path: str,
        password: Optional[str] = None
    ) -> Dict[int, List[str]]:
        """
        Find duplicate files in archive (by size)

        Args:
            archive_path: Path to archive
            password: Password

        Returns:
            Dict mapping size to list of files with that size
        """
        try:
            entries = self.seven_zip.list_contents(archive_path, password=password)

            size_map: Dict[int, List[str]] = {}

            for entry in entries:
                if not entry.get('IsDirectory', False):
                    size = entry.get('Size', 0)
                    path = entry.get('Path', '')

                    if size > 0:
                        size_map.setdefault(size, []).append(path)

            # Filter to only duplicates
            duplicates = {size: paths for size, paths in size_map.items() if len(paths) > 1}

            return duplicates

        except Exception as e:
            raise RuntimeError(f"Failed to find duplicates: {str(e)}")

    def estimate_extraction_size(
        self,
        archive_path: str,
        password: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Estimate disk space needed for extraction

        Args:
            archive_path: Path to archive
            password: Password

        Returns:
            Size estimates
        """
        try:
            stats = self.analyze(archive_path, password=password, detect_nested=False)

            # Add 10% overhead for filesystem metadata
            estimated_size = int(stats.total_size * 1.1)

            return {
                'uncompressed_size': stats.total_size,
                'estimated_with_overhead': estimated_size,
                'compressed_size': stats.packed_size,
                'compression_ratio': stats.compression_ratio,
                'files': stats.total_files,
                'folders': stats.total_folders,
                'formatted_size': self._format_size(estimated_size)
            }

        except Exception as e:
            return {'error': str(e)}
