"""
Smart/dynamic collections with rule-based auto-updating.

Provides dynamic collections that automatically update based on defined rules,
similar to smart playlists in media players.
"""

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class ConditionType(Enum):
    """Types of conditions for rules."""

    # File name
    NAME_CONTAINS = "name_contains"
    NAME_STARTS_WITH = "name_starts_with"
    NAME_ENDS_WITH = "name_ends_with"
    NAME_MATCHES = "name_matches"  # Regex

    # File extension
    EXTENSION_IS = "extension_is"
    EXTENSION_IN = "extension_in"

    # File size
    SIZE_GREATER = "size_greater"
    SIZE_LESS = "size_less"
    SIZE_BETWEEN = "size_between"

    # Date/time
    MODIFIED_AFTER = "modified_after"
    MODIFIED_BEFORE = "modified_before"
    MODIFIED_WITHIN = "modified_within"  # Last N days
    CREATED_AFTER = "created_after"
    CREATED_BEFORE = "created_before"
    ACCESSED_AFTER = "accessed_after"

    # Path
    PATH_CONTAINS = "path_contains"
    PATH_IN = "path_in"

    # Type
    IS_DIRECTORY = "is_directory"
    IS_FILE = "is_file"


class LogicOperator(Enum):
    """Logical operators for combining conditions."""

    AND = "AND"
    OR = "OR"


@dataclass
class Condition:
    """Single condition in a rule."""

    type: ConditionType
    value: Union[str, int, float, List[str]]
    operator: LogicOperator = LogicOperator.AND

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'type': self.type.value,
            'value': self.value,
            'operator': self.operator.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Condition':
        """Create from dictionary."""
        return cls(
            type=ConditionType(data['type']),
            value=data['value'],
            operator=LogicOperator(data.get('operator', 'AND'))
        )

    def evaluate(self, file_info: Dict[str, Any]) -> bool:
        """
        Evaluate condition against file info.

        Args:
            file_info: Dictionary with file properties

        Returns:
            True if condition matches
        """
        path = Path(file_info.get('path', ''))
        name = path.name.lower()
        size = file_info.get('size', 0)

        # Name conditions
        if self.type == ConditionType.NAME_CONTAINS:
            return str(self.value).lower() in name

        elif self.type == ConditionType.NAME_STARTS_WITH:
            return name.startswith(str(self.value).lower())

        elif self.type == ConditionType.NAME_ENDS_WITH:
            return name.endswith(str(self.value).lower())

        elif self.type == ConditionType.NAME_MATCHES:
            import re
            return bool(re.search(str(self.value), name, re.IGNORECASE))

        # Extension conditions
        elif self.type == ConditionType.EXTENSION_IS:
            ext = path.suffix.lower().lstrip('.')
            return ext == str(self.value).lower().lstrip('.')

        elif self.type == ConditionType.EXTENSION_IN:
            ext = path.suffix.lower().lstrip('.')
            extensions = [e.lower().lstrip('.') for e in self.value]
            return ext in extensions

        # Size conditions
        elif self.type == ConditionType.SIZE_GREATER:
            return size > int(self.value)

        elif self.type == ConditionType.SIZE_LESS:
            return size < int(self.value)

        elif self.type == ConditionType.SIZE_BETWEEN:
            min_size, max_size = self.value
            return min_size <= size <= max_size

        # Date conditions
        elif self.type == ConditionType.MODIFIED_WITHIN:
            modified = file_info.get('modified')
            if not modified:
                return False
            days_ago = datetime.now() - timedelta(days=int(self.value))
            return datetime.fromisoformat(modified) >= days_ago

        elif self.type == ConditionType.MODIFIED_AFTER:
            modified = file_info.get('modified')
            if not modified:
                return False
            return datetime.fromisoformat(modified) >= datetime.fromisoformat(str(self.value))

        # Path conditions
        elif self.type == ConditionType.PATH_CONTAINS:
            return str(self.value).lower() in str(path).lower()

        elif self.type == ConditionType.PATH_IN:
            parent = str(path.parent).lower()
            for search_path in self.value:
                if parent.startswith(str(search_path).lower()):
                    return True
            return False

        # Type conditions
        elif self.type == ConditionType.IS_DIRECTORY:
            return path.is_dir()

        elif self.type == ConditionType.IS_FILE:
            return path.is_file()

        return False


@dataclass
class SmartCollection:
    """Smart collection with dynamic rules."""

    id: Optional[int] = None
    name: str = ""
    description: str = ""
    icon: str = "folder"
    color: str = "#4A90E2"

    # Rules
    conditions: List[Condition] = field(default_factory=list)
    match_all: bool = True  # AND if True, OR if False

    # Limits
    max_results: int = 1000
    sort_by: str = "name"
    ascending: bool = True

    # Metadata
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    last_updated: Optional[str] = None
    result_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['conditions'] = [c.to_dict() for c in self.conditions]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SmartCollection':
        """Create from dictionary."""
        conditions = [Condition.from_dict(c) for c in data.pop('conditions', [])]
        collection = cls(**data)
        collection.conditions = conditions
        return collection

    def matches(self, file_info: Dict[str, Any]) -> bool:
        """
        Check if file matches collection rules.

        Args:
            file_info: File information dictionary

        Returns:
            True if file matches rules
        """
        if not self.conditions:
            return True

        if self.match_all:
            # AND - all conditions must match
            return all(cond.evaluate(file_info) for cond in self.conditions)
        else:
            # OR - at least one condition must match
            return any(cond.evaluate(file_info) for cond in self.conditions)


class SmartCollectionsManager:
    """
    Manages smart/dynamic collections with SQLite storage.

    Features:
    - Rule-based auto-updating collections
    - Complex conditions with AND/OR logic
    - Nested conditions support
    - Predefined collection templates
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize smart collections manager.

        Args:
            db_path: Path to SQLite database (default: ~/.smart_search_collections.db)
        """
        if db_path is None:
            db_path = str(Path.home() / ".smart_search_collections.db")

        self.db_path = db_path
        self._init_database()
        self._create_default_collections()

    def _init_database(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                icon TEXT DEFAULT 'folder',
                color TEXT DEFAULT '#4A90E2',

                -- Rules (JSON)
                conditions TEXT NOT NULL,
                match_all INTEGER DEFAULT 1,

                -- Limits
                max_results INTEGER DEFAULT 1000,
                sort_by TEXT DEFAULT 'name',
                ascending INTEGER DEFAULT 1,

                -- Metadata
                created_at TEXT NOT NULL,
                modified_at TEXT NOT NULL,
                last_updated TEXT,
                result_count INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()

    def _create_default_collections(self):
        """Create default smart collections if they don't exist."""
        defaults = [
            SmartCollection(
                name="Large Files (>1GB)",
                description="Files larger than 1GB",
                icon="storage",
                color="#E74C3C",
                conditions=[
                    Condition(ConditionType.SIZE_GREATER, 1024 * 1024 * 1024),
                    Condition(ConditionType.IS_FILE, True)
                ],
                match_all=True,
                sort_by="size",
                ascending=False
            ),
            SmartCollection(
                name="Recent Documents",
                description="Documents modified in the last 7 days",
                icon="document",
                color="#3498DB",
                conditions=[
                    Condition(ConditionType.EXTENSION_IN, ['doc', 'docx', 'pdf', 'txt', 'odt']),
                    Condition(ConditionType.MODIFIED_WITHIN, 7)
                ],
                match_all=True,
                sort_by="modified",
                ascending=False
            ),
            SmartCollection(
                name="Images",
                description="All image files",
                icon="image",
                color="#9B59B6",
                conditions=[
                    Condition(ConditionType.EXTENSION_IN, ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'])
                ],
                match_all=True
            ),
            SmartCollection(
                name="Videos",
                description="All video files",
                icon="video",
                color="#E67E22",
                conditions=[
                    Condition(ConditionType.EXTENSION_IN, ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm'])
                ],
                match_all=True
            ),
            SmartCollection(
                name="Today's Files",
                description="Files modified today",
                icon="calendar",
                color="#1ABC9C",
                conditions=[
                    Condition(ConditionType.MODIFIED_WITHIN, 1)
                ],
                match_all=True,
                sort_by="modified",
                ascending=False
            ),
        ]

        for collection in defaults:
            if not self.get_by_name(collection.name):
                self.save(collection)

    def save(self, collection: SmartCollection) -> int:
        """Save or update a collection."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        data = {
            'name': collection.name,
            'description': collection.description,
            'icon': collection.icon,
            'color': collection.color,
            'conditions': json.dumps([c.to_dict() for c in collection.conditions]),
            'match_all': 1 if collection.match_all else 0,
            'max_results': collection.max_results,
            'sort_by': collection.sort_by,
            'ascending': 1 if collection.ascending else 0,
            'modified_at': now,
        }

        if collection.id:
            # Update existing
            cursor.execute("""
                UPDATE collections
                SET name=?, description=?, icon=?, color=?, conditions=?,
                    match_all=?, max_results=?, sort_by=?, ascending=?, modified_at=?
                WHERE id=?
            """, (
                data['name'], data['description'], data['icon'], data['color'],
                data['conditions'], data['match_all'], data['max_results'],
                data['sort_by'], data['ascending'], data['modified_at'], collection.id
            ))
            collection_id = collection.id
        else:
            # Insert new
            data['created_at'] = now
            cursor.execute("""
                INSERT INTO collections (
                    name, description, icon, color, conditions, match_all,
                    max_results, sort_by, ascending, created_at, modified_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['name'], data['description'], data['icon'], data['color'],
                data['conditions'], data['match_all'], data['max_results'],
                data['sort_by'], data['ascending'], data['created_at'], data['modified_at']
            ))
            collection_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return collection_id

    def get(self, collection_id: int) -> Optional[SmartCollection]:
        """Get collection by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM collections WHERE id=?", (collection_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_collection(row)
        return None

    def get_by_name(self, name: str) -> Optional[SmartCollection]:
        """Get collection by name."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM collections WHERE name=?", (name,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_collection(row)
        return None

    def get_all(self) -> List[SmartCollection]:
        """Get all collections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM collections ORDER BY name")
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_collection(row) for row in rows]

    def delete(self, collection_id: int):
        """Delete a collection."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM collections WHERE id=?", (collection_id,))

        conn.commit()
        conn.close()

    def update_result_count(self, collection_id: int, count: int):
        """Update result count after evaluation."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE collections
            SET result_count=?, last_updated=?
            WHERE id=?
        """, (count, datetime.now().isoformat(), collection_id))

        conn.commit()
        conn.close()

    def evaluate(self, collection_id: int, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Evaluate collection rules against file list.

        Args:
            collection_id: Collection ID
            files: List of file info dictionaries

        Returns:
            List of matching files
        """
        collection = self.get(collection_id)
        if not collection:
            return []

        # Filter files by conditions
        matches = [f for f in files if collection.matches(f)]

        # Sort results
        if collection.sort_by == 'name':
            matches.sort(key=lambda x: Path(x['path']).name, reverse=not collection.ascending)
        elif collection.sort_by == 'size':
            matches.sort(key=lambda x: x.get('size', 0), reverse=not collection.ascending)
        elif collection.sort_by == 'modified':
            matches.sort(
                key=lambda x: x.get('modified', ''),
                reverse=not collection.ascending
            )

        # Limit results
        matches = matches[:collection.max_results]

        # Update result count
        self.update_result_count(collection_id, len(matches))

        return matches

    def export_to_json(self, output_file: str):
        """Export collections to JSON file."""
        collections = self.get_all()

        data = {
            'version': '1.0',
            'exported_at': datetime.now().isoformat(),
            'count': len(collections),
            'collections': [c.to_dict() for c in collections]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def import_from_json(self, input_file: str, merge: bool = True) -> int:
        """Import collections from JSON file."""
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not merge:
            # Clear existing
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM collections")
            conn.commit()
            conn.close()

        imported = 0
        for coll_data in data.get('collections', []):
            coll_data.pop('id', None)
            collection = SmartCollection.from_dict(coll_data)

            try:
                self.save(collection)
                imported += 1
            except sqlite3.IntegrityError:
                continue

        return imported

    def _row_to_collection(self, row: sqlite3.Row) -> SmartCollection:
        """Convert database row to SmartCollection object."""
        conditions_data = json.loads(row['conditions'])
        conditions = [Condition.from_dict(c) for c in conditions_data]

        return SmartCollection(
            id=row['id'],
            name=row['name'],
            description=row['description'] or '',
            icon=row['icon'],
            color=row['color'],
            conditions=conditions,
            match_all=bool(row['match_all']),
            max_results=row['max_results'],
            sort_by=row['sort_by'],
            ascending=bool(row['ascending']),
            created_at=row['created_at'],
            modified_at=row['modified_at'],
            last_updated=row['last_updated'],
            result_count=row['result_count'],
        )
