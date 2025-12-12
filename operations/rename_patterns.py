"""
Rename Patterns - Pre-built and custom pattern library for batch renaming
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from .batch_renamer import RenamePattern, CaseMode


@dataclass
class SavedPattern:
    """Saved rename pattern with metadata"""
    name: str
    description: str
    pattern: RenamePattern
    category: str = "Custom"
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        data = {
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'tags': self.tags,
            'pattern': {
                'pattern': self.pattern.pattern,
                'find': self.pattern.find,
                'replace': self.pattern.replace,
                'use_regex': self.pattern.use_regex,
                'case_mode': self.pattern.case_mode.value,
                'prefix': self.pattern.prefix,
                'suffix': self.pattern.suffix,
                'remove_chars': self.pattern.remove_chars,
                'start_number': self.pattern.start_number,
                'number_padding': self.pattern.number_padding,
                'date_format': self.pattern.date_format,
                'trim_whitespace': self.pattern.trim_whitespace,
            }
        }
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'SavedPattern':
        """Create from dictionary"""
        pattern_data = data['pattern']
        pattern = RenamePattern(
            pattern=pattern_data.get('pattern', '{name}'),
            find=pattern_data.get('find', ''),
            replace=pattern_data.get('replace', ''),
            use_regex=pattern_data.get('use_regex', False),
            case_mode=CaseMode(pattern_data.get('case_mode', 'keep')),
            prefix=pattern_data.get('prefix', ''),
            suffix=pattern_data.get('suffix', ''),
            remove_chars=pattern_data.get('remove_chars', ''),
            start_number=pattern_data.get('start_number', 1),
            number_padding=pattern_data.get('number_padding', 3),
            date_format=pattern_data.get('date_format', '%Y%m%d'),
            trim_whitespace=pattern_data.get('trim_whitespace', True),
        )
        return cls(
            name=data['name'],
            description=data['description'],
            pattern=pattern,
            category=data.get('category', 'Custom'),
            tags=data.get('tags', [])
        )


class PatternLibrary:
    """
    Pattern library with pre-built and custom patterns
    """

    # Pre-built pattern definitions
    PREBUILT_PATTERNS = {
        # Photo patterns
        'photo_date_numbered': SavedPattern(
            name="Photo: Date + Number",
            description="Format: 20231215_IMG_001.jpg",
            pattern=RenamePattern(
                pattern="{date}_IMG_{num}",
                date_format="%Y%m%d",
                number_padding=3
            ),
            category="Photos",
            tags=["photos", "date", "numbered"]
        ),
        'photo_exif_date': SavedPattern(
            name="Photo: EXIF Date",
            description="Format: 20231215_143022.jpg (from EXIF data)",
            pattern=RenamePattern(
                pattern="{exif_datetime}",
                date_format="%Y%m%d"
            ),
            category="Photos",
            tags=["photos", "exif", "date"]
        ),
        'photo_folder_date': SavedPattern(
            name="Photo: Folder + Date",
            description="Format: Vacation_20231215_001.jpg",
            pattern=RenamePattern(
                pattern="{parent}_{date}_{num}",
                date_format="%Y%m%d",
                number_padding=3
            ),
            category="Photos",
            tags=["photos", "folder", "date"]
        ),

        # Document patterns
        'doc_folder_name': SavedPattern(
            name="Document: Folder + Name",
            description="Format: ProjectName_document.pdf",
            pattern=RenamePattern(
                pattern="{parent}_{name}"
            ),
            category="Documents",
            tags=["documents", "folder"]
        ),
        'doc_date_name': SavedPattern(
            name="Document: Date + Name",
            description="Format: 2023-12-15_document.pdf",
            pattern=RenamePattern(
                pattern="{date}_{name}",
                date_format="%Y-%m-%d"
            ),
            category="Documents",
            tags=["documents", "date"]
        ),

        # Music patterns
        'music_track_title': SavedPattern(
            name="Music: Track + Title",
            description="Format: 01 - Song Name.mp3",
            pattern=RenamePattern(
                pattern="{num} - {name}",
                number_padding=2
            ),
            category="Music",
            tags=["music", "numbered"]
        ),

        # Sequential patterns
        'sequential_padded': SavedPattern(
            name="Sequential: Padded Numbers",
            description="Format: File_001.ext, File_002.ext",
            pattern=RenamePattern(
                pattern="File_{num}",
                number_padding=3
            ),
            category="Sequential",
            tags=["sequential", "numbers"]
        ),
        'sequential_date': SavedPattern(
            name="Sequential: Date + Number",
            description="Format: 20231215_001.ext",
            pattern=RenamePattern(
                pattern="{date}_{num}",
                date_format="%Y%m%d",
                number_padding=3
            ),
            category="Sequential",
            tags=["sequential", "date", "numbers"]
        ),

        # Clean up patterns
        'cleanup_spaces': SavedPattern(
            name="Clean: Remove Extra Spaces",
            description="Remove multiple spaces and trim",
            pattern=RenamePattern(
                pattern="{name}",
                find=r'\s+',
                replace=' ',
                use_regex=True,
                trim_whitespace=True
            ),
            category="Cleanup",
            tags=["cleanup", "spaces"]
        ),
        'cleanup_special_chars': SavedPattern(
            name="Clean: Remove Special Characters",
            description="Remove !@#$%^&*() characters",
            pattern=RenamePattern(
                pattern="{name}",
                remove_chars="!@#$%^&*()"
            ),
            category="Cleanup",
            tags=["cleanup", "special"]
        ),
        'cleanup_lowercase': SavedPattern(
            name="Clean: Lowercase",
            description="Convert to lowercase",
            pattern=RenamePattern(
                pattern="{name}",
                case_mode=CaseMode.LOWER
            ),
            category="Cleanup",
            tags=["cleanup", "case"]
        ),
        'cleanup_title_case': SavedPattern(
            name="Clean: Title Case",
            description="Convert To Title Case",
            pattern=RenamePattern(
                pattern="{name}",
                case_mode=CaseMode.TITLE
            ),
            category="Cleanup",
            tags=["cleanup", "case"]
        ),

        # Advanced patterns
        'advanced_hash_date': SavedPattern(
            name="Advanced: Hash + Date",
            description="Format: 20231215_a1b2c3d4.ext",
            pattern=RenamePattern(
                pattern="{date}_{hash}",
                date_format="%Y%m%d"
            ),
            category="Advanced",
            tags=["advanced", "hash", "date"]
        ),
    }

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize pattern library

        Args:
            storage_path: Path to JSON file for custom patterns
        """
        if storage_path is None:
            storage_path = Path.home() / ".smart_search" / "rename_patterns.json"

        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self.custom_patterns: Dict[str, SavedPattern] = {}
        self._load_custom_patterns()

    def get_all_patterns(self) -> Dict[str, SavedPattern]:
        """Get all patterns (pre-built + custom)"""
        patterns = dict(self.PREBUILT_PATTERNS)
        patterns.update(self.custom_patterns)
        return patterns

    def get_pattern(self, pattern_id: str) -> Optional[SavedPattern]:
        """Get specific pattern by ID"""
        if pattern_id in self.PREBUILT_PATTERNS:
            return self.PREBUILT_PATTERNS[pattern_id]
        return self.custom_patterns.get(pattern_id)

    def get_patterns_by_category(self, category: str) -> Dict[str, SavedPattern]:
        """Get patterns filtered by category"""
        all_patterns = self.get_all_patterns()
        return {
            pid: pattern for pid, pattern in all_patterns.items()
            if pattern.category == category
        }

    def get_patterns_by_tag(self, tag: str) -> Dict[str, SavedPattern]:
        """Get patterns filtered by tag"""
        all_patterns = self.get_all_patterns()
        return {
            pid: pattern for pid, pattern in all_patterns.items()
            if tag in pattern.tags
        }

    def get_categories(self) -> List[str]:
        """Get list of all categories"""
        categories = set()
        for pattern in self.get_all_patterns().values():
            categories.add(pattern.category)
        return sorted(categories)

    def save_pattern(self, pattern_id: str, pattern: SavedPattern) -> bool:
        """
        Save custom pattern

        Args:
            pattern_id: Unique identifier for pattern
            pattern: SavedPattern to save

        Returns:
            True if saved successfully
        """
        try:
            self.custom_patterns[pattern_id] = pattern
            self._save_custom_patterns()
            return True
        except Exception:
            return False

    def delete_pattern(self, pattern_id: str) -> bool:
        """
        Delete custom pattern

        Args:
            pattern_id: Pattern to delete

        Returns:
            True if deleted successfully
        """
        if pattern_id in self.custom_patterns:
            del self.custom_patterns[pattern_id]
            self._save_custom_patterns()
            return True
        return False

    def import_patterns(self, file_path: str) -> int:
        """
        Import patterns from JSON file

        Returns:
            Number of patterns imported
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            count = 0
            for pattern_id, pattern_data in data.items():
                pattern = SavedPattern.from_dict(pattern_data)
                self.custom_patterns[pattern_id] = pattern
                count += 1

            self._save_custom_patterns()
            return count
        except Exception:
            return 0

    def export_patterns(self, file_path: str, pattern_ids: Optional[List[str]] = None) -> bool:
        """
        Export patterns to JSON file

        Args:
            file_path: Output file path
            pattern_ids: Specific patterns to export (None = all custom patterns)

        Returns:
            True if exported successfully
        """
        try:
            if pattern_ids is None:
                patterns_to_export = self.custom_patterns
            else:
                patterns_to_export = {
                    pid: pattern for pid, pattern in self.custom_patterns.items()
                    if pid in pattern_ids
                }

            data = {
                pid: pattern.to_dict()
                for pid, pattern in patterns_to_export.items()
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception:
            return False

    def _load_custom_patterns(self):
        """Load custom patterns from storage"""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for pattern_id, pattern_data in data.items():
                pattern = SavedPattern.from_dict(pattern_data)
                self.custom_patterns[pattern_id] = pattern
        except Exception:
            pass

    def _save_custom_patterns(self):
        """Save custom patterns to storage"""
        try:
            data = {
                pid: pattern.to_dict()
                for pid, pattern in self.custom_patterns.items()
            }

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass


# Helper function to get default library instance
_default_library = None

def get_pattern_library() -> PatternLibrary:
    """Get default pattern library instance"""
    global _default_library
    if _default_library is None:
        _default_library = PatternLibrary()
    return _default_library
