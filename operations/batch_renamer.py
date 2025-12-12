"""
Batch Renamer - Advanced pattern-based file renaming engine
Supports placeholders, regex, metadata extraction, and preview capabilities
"""

import re
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import json

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    EXIF_AVAILABLE = True
except ImportError:
    EXIF_AVAILABLE = False


class CaseMode(Enum):
    """Text case transformation modes"""
    UPPER = "upper"
    LOWER = "lower"
    TITLE = "title"
    SENTENCE = "sentence"
    KEEP = "keep"


class CollisionMode(Enum):
    """File name collision handling modes"""
    AUTO_NUMBER = "auto_number"
    SKIP = "skip"
    OVERWRITE = "overwrite"
    ASK = "ask"


@dataclass
class RenameOperation:
    """Single rename operation"""
    old_path: Path
    new_name: str
    success: bool = False
    error: Optional[str] = None
    skipped: bool = False
    collision: bool = False

    @property
    def new_path(self) -> Path:
        """Get full new path"""
        return self.old_path.parent / self.new_name

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'old_path': str(self.old_path),
            'old_name': self.old_path.name,
            'new_name': self.new_name,
            'success': self.success,
            'error': self.error,
            'skipped': self.skipped,
            'collision': self.collision
        }


@dataclass
class RenamePattern:
    """Rename pattern configuration"""
    pattern: str = "{name}"
    find: str = ""
    replace: str = ""
    use_regex: bool = False
    case_mode: CaseMode = CaseMode.KEEP
    prefix: str = ""
    suffix: str = ""
    remove_chars: str = ""
    start_number: int = 1
    number_padding: int = 3
    date_format: str = "%Y%m%d"
    trim_whitespace: bool = True


@dataclass
class RenameResult:
    """Result of batch rename operation"""
    operations: List[RenameOperation] = field(default_factory=list)
    total_files: int = 0
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    collision_count: int = 0

    def add_operation(self, operation: RenameOperation):
        """Add an operation to results"""
        self.operations.append(operation)
        self.total_files += 1
        if operation.success:
            self.success_count += 1
        elif operation.skipped:
            self.skipped_count += 1
        elif operation.collision:
            self.collision_count += 1
        else:
            self.failed_count += 1

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'operations': [op.to_dict() for op in self.operations],
            'total_files': self.total_files,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'skipped_count': self.skipped_count,
            'collision_count': self.collision_count
        }


class BatchRenamer:
    """
    Advanced batch file renaming engine

    Supported placeholders:
    - {name} - original name without extension
    - {ext} - extension (without dot)
    - {num} - sequential number with padding
    - {date} - file modification date
    - {created} - file creation date
    - {parent} - parent folder name
    - {size} - file size in bytes
    - {sizekb} - file size in KB
    - {sizemb} - file size in MB
    - {hash} - short file hash (first 8 chars)
    - {hash16} - medium file hash (first 16 chars)
    - {exif_date} - EXIF date from images (if available)
    - {width} - image width (if available)
    - {height} - image height (if available)

    Regex capture groups: $1, $2, etc.
    """

    def __init__(self):
        self.collision_mode = CollisionMode.AUTO_NUMBER
        self.dry_run = False
        self.metadata_cache: Dict[str, Dict] = {}

    def preview_rename(
        self,
        files: List[str],
        pattern: RenamePattern
    ) -> List[Tuple[str, str, bool]]:
        """
        Preview rename operation without applying

        Returns:
            List of (old_name, new_name, has_collision) tuples
        """
        old_dry_run = self.dry_run
        self.dry_run = True

        file_paths = [Path(f) for f in files]
        result = self._apply_pattern(file_paths, pattern)

        self.dry_run = old_dry_run

        # Return preview info
        previews = []
        seen_names = set()

        for op in result.operations:
            has_collision = op.new_name in seen_names or op.collision
            seen_names.add(op.new_name)
            previews.append((op.old_path.name, op.new_name, has_collision))

        return previews

    def batch_rename(
        self,
        files: List[str],
        pattern: RenamePattern,
        collision_mode: CollisionMode = CollisionMode.AUTO_NUMBER
    ) -> RenameResult:
        """
        Execute batch rename operation

        Args:
            files: List of file paths to rename
            pattern: Rename pattern configuration
            collision_mode: How to handle name collisions

        Returns:
            RenameResult with operation details
        """
        self.collision_mode = collision_mode
        file_paths = [Path(f) for f in files]

        return self._apply_pattern(file_paths, pattern)

    def _apply_pattern(
        self,
        files: List[Path],
        pattern: RenamePattern
    ) -> RenameResult:
        """Apply rename pattern to files"""
        result = RenameResult()

        # Track used names for collision detection
        used_names: Dict[str, int] = {}

        for index, file_path in enumerate(files, start=1):
            try:
                if not file_path.exists():
                    op = RenameOperation(file_path, file_path.name, error="File not found")
                    result.add_operation(op)
                    continue

                # Generate new name
                new_name = self._generate_name(
                    file_path,
                    pattern,
                    index,
                    pattern.start_number + index - 1
                )

                # Handle collision
                final_name = new_name
                collision = False

                if new_name in used_names or (file_path.parent / new_name).exists():
                    collision = True
                    if self.collision_mode == CollisionMode.AUTO_NUMBER:
                        final_name = self._auto_number_name(file_path.parent, new_name, used_names)
                    elif self.collision_mode == CollisionMode.SKIP:
                        op = RenameOperation(file_path, new_name, skipped=True, collision=True)
                        result.add_operation(op)
                        continue
                    elif self.collision_mode == CollisionMode.OVERWRITE:
                        pass  # Will overwrite

                # Track name usage
                used_names[final_name] = used_names.get(final_name, 0) + 1

                # Execute or simulate rename
                if not self.dry_run:
                    try:
                        new_path = file_path.parent / final_name
                        file_path.rename(new_path)
                        op = RenameOperation(file_path, final_name, success=True, collision=collision)
                    except Exception as e:
                        op = RenameOperation(file_path, final_name, error=str(e))
                else:
                    # Dry run - just record what would happen
                    op = RenameOperation(file_path, final_name, success=True, collision=collision)

                result.add_operation(op)

            except Exception as e:
                op = RenameOperation(file_path, file_path.name, error=str(e))
                result.add_operation(op)

        return result

    def _generate_name(
        self,
        file_path: Path,
        pattern: RenamePattern,
        index: int,
        number: int
    ) -> str:
        """Generate new filename based on pattern"""
        # Get base components
        name_no_ext = file_path.stem
        ext = file_path.suffix[1:] if file_path.suffix else ""

        # Apply find/replace first
        if pattern.find:
            if pattern.use_regex:
                name_no_ext = re.sub(pattern.find, pattern.replace, name_no_ext)
            else:
                name_no_ext = name_no_ext.replace(pattern.find, pattern.replace)

        # Remove characters
        if pattern.remove_chars:
            for char in pattern.remove_chars:
                name_no_ext = name_no_ext.replace(char, "")

        # Build placeholder values
        placeholders = {
            'name': name_no_ext,
            'ext': ext,
            'num': str(number).zfill(pattern.number_padding),
            'parent': file_path.parent.name,
        }

        # File stats
        try:
            stat = file_path.stat()
            placeholders['size'] = str(stat.st_size)
            placeholders['sizekb'] = str(stat.st_size // 1024)
            placeholders['sizemb'] = str(stat.st_size // (1024 * 1024))
            placeholders['date'] = datetime.fromtimestamp(stat.st_mtime).strftime(pattern.date_format)
            placeholders['created'] = datetime.fromtimestamp(stat.st_ctime).strftime(pattern.date_format)
        except:
            placeholders['size'] = '0'
            placeholders['sizekb'] = '0'
            placeholders['sizemb'] = '0'
            placeholders['date'] = ''
            placeholders['created'] = ''

        # File hash
        try:
            file_hash = self._get_file_hash(file_path)
            placeholders['hash'] = file_hash[:8]
            placeholders['hash16'] = file_hash[:16]
        except:
            placeholders['hash'] = ''
            placeholders['hash16'] = ''

        # Metadata (EXIF, etc.)
        metadata = self._get_metadata(file_path)
        placeholders.update(metadata)

        # Apply pattern
        new_name = pattern.pattern
        for key, value in placeholders.items():
            new_name = new_name.replace(f'{{{key}}}', value)

        # Handle regex capture groups if pattern has them
        if pattern.use_regex and pattern.find:
            match = re.search(pattern.find, file_path.stem)
            if match:
                for i, group in enumerate(match.groups(), start=1):
                    new_name = new_name.replace(f'${i}', group or '')

        # Add prefix/suffix
        if pattern.prefix:
            new_name = pattern.prefix + new_name
        if pattern.suffix:
            # Add suffix before extension
            if ext:
                new_name = new_name + pattern.suffix

        # Trim whitespace
        if pattern.trim_whitespace:
            new_name = new_name.strip()

        # Apply case transformation
        new_name = self._apply_case(new_name, pattern.case_mode)

        # Add extension back
        if ext:
            new_name = f"{new_name}.{ext}"

        return new_name

    def _get_file_hash(self, file_path: Path, algorithm: str = 'md5') -> str:
        """Calculate file hash (cached)"""
        cache_key = str(file_path)
        if cache_key in self.metadata_cache and 'hash' in self.metadata_cache[cache_key]:
            return self.metadata_cache[cache_key]['hash']

        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                # Read in chunks for large files
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)
            file_hash = hasher.hexdigest()

            if cache_key not in self.metadata_cache:
                self.metadata_cache[cache_key] = {}
            self.metadata_cache[cache_key]['hash'] = file_hash

            return file_hash
        except:
            return ''

    def _get_metadata(self, file_path: Path) -> Dict[str, str]:
        """Extract file metadata (EXIF, etc.)"""
        cache_key = str(file_path)
        if cache_key in self.metadata_cache:
            return {k: v for k, v in self.metadata_cache[cache_key].items() if k != 'hash'}

        metadata = {}

        # Try to extract EXIF from images
        if EXIF_AVAILABLE and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            try:
                image = Image.open(file_path)

                # Image dimensions
                metadata['width'] = str(image.width)
                metadata['height'] = str(image.height)

                # EXIF data
                exif = image._getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag == 'DateTime':
                            try:
                                dt = datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S')
                                metadata['exif_date'] = dt.strftime('%Y%m%d')
                                metadata['exif_datetime'] = dt.strftime('%Y%m%d_%H%M%S')
                            except:
                                pass

                image.close()
            except:
                pass

        # Cache metadata
        self.metadata_cache[cache_key] = metadata
        return metadata

    def _apply_case(self, text: str, case_mode: CaseMode) -> str:
        """Apply case transformation"""
        if case_mode == CaseMode.UPPER:
            return text.upper()
        elif case_mode == CaseMode.LOWER:
            return text.lower()
        elif case_mode == CaseMode.TITLE:
            return text.title()
        elif case_mode == CaseMode.SENTENCE:
            return text[0].upper() + text[1:].lower() if text else text
        else:
            return text

    def _auto_number_name(
        self,
        parent: Path,
        base_name: str,
        used_names: Dict[str, int]
    ) -> str:
        """Generate auto-numbered name to avoid collision"""
        # Split name and extension
        path = Path(base_name)
        name = path.stem
        ext = path.suffix

        counter = 1
        while True:
            new_name = f"{name} ({counter}){ext}"
            if new_name not in used_names and not (parent / new_name).exists():
                return new_name
            counter += 1

    def clear_cache(self):
        """Clear metadata cache"""
        self.metadata_cache.clear()


class TextOperations:
    """Text manipulation operations for batch renaming"""

    @staticmethod
    def find_replace(text: str, find: str, replace: str, use_regex: bool = False) -> str:
        """Find and replace in text"""
        if use_regex:
            return re.sub(find, replace, text)
        else:
            return text.replace(find, replace)

    @staticmethod
    def remove_characters(text: str, chars: str) -> str:
        """Remove specific characters"""
        for char in chars:
            text = text.replace(char, '')
        return text

    @staticmethod
    def trim_whitespace(text: str) -> str:
        """Trim leading/trailing whitespace"""
        return text.strip()

    @staticmethod
    def insert_text(text: str, position: int, insert: str) -> str:
        """Insert text at position"""
        return text[:position] + insert + text[position:]

    @staticmethod
    def remove_range(text: str, start: int, end: int) -> str:
        """Remove text range"""
        return text[:start] + text[end:]

    @staticmethod
    def normalize_spaces(text: str) -> str:
        """Normalize multiple spaces to single space"""
        return re.sub(r'\s+', ' ', text).strip()
