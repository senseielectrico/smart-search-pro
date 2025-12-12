"""
Saved searches manager with SQLite storage.

Provides persistent saved search management with categorization,
quick execution, and import/export capabilities.
"""

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


@dataclass
class SavedSearch:
    """Saved search with all parameters."""

    id: Optional[int] = None
    name: str = ""
    description: str = ""
    query: str = ""
    category: str = "General"
    icon: str = "search"
    color: str = "#4A90E2"

    # Search parameters
    file_types: List[str] = field(default_factory=list)
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    sort_order: str = "name"
    ascending: bool = True
    search_paths: List[str] = field(default_factory=list)

    # View preferences
    view_mode: str = "list"  # list, grid, details
    show_preview: bool = True

    # Metadata
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    last_run: Optional[str] = None
    run_count: int = 0
    last_result_count: int = 0

    # Keyboard shortcut (Ctrl+1 through Ctrl+9)
    shortcut_key: Optional[int] = None  # 1-9

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SavedSearch':
        """Create from dictionary."""
        return cls(**data)


class SavedSearchManager:
    """
    Manages saved searches with SQLite storage.

    Features:
    - Persistent storage in SQLite database
    - Categories and organization
    - Quick execution with keyboard shortcuts
    - Import/export capability
    - Search within saved searches
    - Statistics tracking
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize saved search manager.

        Args:
            db_path: Path to SQLite database (default: ~/.smart_search_saved.db)
        """
        if db_path is None:
            db_path = str(Path.home() / ".smart_search_saved.db")

        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                query TEXT NOT NULL,
                category TEXT DEFAULT 'General',
                icon TEXT DEFAULT 'search',
                color TEXT DEFAULT '#4A90E2',

                -- Search parameters (JSON)
                file_types TEXT,
                min_size INTEGER,
                max_size INTEGER,
                date_from TEXT,
                date_to TEXT,
                sort_order TEXT DEFAULT 'name',
                ascending INTEGER DEFAULT 1,
                search_paths TEXT,

                -- View preferences
                view_mode TEXT DEFAULT 'list',
                show_preview INTEGER DEFAULT 1,

                -- Metadata
                created_at TEXT NOT NULL,
                modified_at TEXT NOT NULL,
                last_run TEXT,
                run_count INTEGER DEFAULT 0,
                last_result_count INTEGER DEFAULT 0,

                -- Keyboard shortcut
                shortcut_key INTEGER,

                UNIQUE(name)
            )
        """)

        # Create index on category for faster filtering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_category
            ON saved_searches(category)
        """)

        # Create index on shortcut_key
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_shortcut
            ON saved_searches(shortcut_key)
        """)

        conn.commit()
        conn.close()

    def save(self, search: SavedSearch) -> int:
        """
        Save or update a search.

        Args:
            search: SavedSearch object

        Returns:
            ID of saved search
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        # Prepare data
        data = {
            'name': search.name,
            'description': search.description,
            'query': search.query,
            'category': search.category,
            'icon': search.icon,
            'color': search.color,
            'file_types': json.dumps(search.file_types),
            'min_size': search.min_size,
            'max_size': search.max_size,
            'date_from': search.date_from,
            'date_to': search.date_to,
            'sort_order': search.sort_order,
            'ascending': 1 if search.ascending else 0,
            'search_paths': json.dumps(search.search_paths),
            'view_mode': search.view_mode,
            'show_preview': 1 if search.show_preview else 0,
            'modified_at': now,
            'shortcut_key': search.shortcut_key,
        }

        if search.id:
            # Update existing
            cursor.execute("""
                UPDATE saved_searches
                SET name=?, description=?, query=?, category=?, icon=?, color=?,
                    file_types=?, min_size=?, max_size=?, date_from=?, date_to=?,
                    sort_order=?, ascending=?, search_paths=?, view_mode=?, show_preview=?,
                    modified_at=?, shortcut_key=?
                WHERE id=?
            """, (
                data['name'], data['description'], data['query'], data['category'],
                data['icon'], data['color'], data['file_types'], data['min_size'],
                data['max_size'], data['date_from'], data['date_to'], data['sort_order'],
                data['ascending'], data['search_paths'], data['view_mode'],
                data['show_preview'], data['modified_at'], data['shortcut_key'],
                search.id
            ))
            search_id = search.id
        else:
            # Insert new
            data['created_at'] = now
            cursor.execute("""
                INSERT INTO saved_searches (
                    name, description, query, category, icon, color,
                    file_types, min_size, max_size, date_from, date_to,
                    sort_order, ascending, search_paths, view_mode, show_preview,
                    created_at, modified_at, shortcut_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['name'], data['description'], data['query'], data['category'],
                data['icon'], data['color'], data['file_types'], data['min_size'],
                data['max_size'], data['date_from'], data['date_to'], data['sort_order'],
                data['ascending'], data['search_paths'], data['view_mode'],
                data['show_preview'], data['created_at'], data['modified_at'],
                data['shortcut_key']
            ))
            search_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return search_id

    def get(self, search_id: int) -> Optional[SavedSearch]:
        """Get search by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM saved_searches WHERE id=?", (search_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_search(row)
        return None

    def get_by_name(self, name: str) -> Optional[SavedSearch]:
        """Get search by name."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM saved_searches WHERE name=?", (name,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_search(row)
        return None

    def get_by_shortcut(self, key: int) -> Optional[SavedSearch]:
        """Get search by keyboard shortcut (1-9)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM saved_searches WHERE shortcut_key=?", (key,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_search(row)
        return None

    def get_all(self, category: Optional[str] = None) -> List[SavedSearch]:
        """
        Get all saved searches.

        Args:
            category: Filter by category (optional)

        Returns:
            List of SavedSearch objects
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if category:
            cursor.execute(
                "SELECT * FROM saved_searches WHERE category=? ORDER BY name",
                (category,)
            )
        else:
            cursor.execute("SELECT * FROM saved_searches ORDER BY category, name")

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_search(row) for row in rows]

    def get_categories(self) -> List[str]:
        """Get list of all categories."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT category FROM saved_searches ORDER BY category")
        categories = [row[0] for row in cursor.fetchall()]

        conn.close()
        return categories

    def search(self, keyword: str) -> List[SavedSearch]:
        """
        Search within saved searches.

        Args:
            keyword: Search keyword

        Returns:
            List of matching SavedSearch objects
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        pattern = f"%{keyword}%"
        cursor.execute("""
            SELECT * FROM saved_searches
            WHERE name LIKE ? OR description LIKE ? OR query LIKE ?
            ORDER BY name
        """, (pattern, pattern, pattern))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_search(row) for row in rows]

    def delete(self, search_id: int):
        """Delete a saved search."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM saved_searches WHERE id=?", (search_id,))

        conn.commit()
        conn.close()

    def duplicate(self, search_id: int, new_name: str) -> int:
        """
        Duplicate a saved search with new name.

        Args:
            search_id: ID of search to duplicate
            new_name: Name for the duplicate

        Returns:
            ID of new search
        """
        search = self.get(search_id)
        if not search:
            raise ValueError(f"Search {search_id} not found")

        # Create copy with new name
        search.id = None
        search.name = new_name
        search.created_at = None
        search.modified_at = None
        search.last_run = None
        search.run_count = 0
        search.shortcut_key = None

        return self.save(search)

    def update_run_stats(self, search_id: int, result_count: int):
        """
        Update run statistics after executing a search.

        Args:
            search_id: ID of search
            result_count: Number of results returned
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE saved_searches
            SET last_run=?, run_count=run_count+1, last_result_count=?
            WHERE id=?
        """, (datetime.now().isoformat(), result_count, search_id))

        conn.commit()
        conn.close()

    def export_to_json(self, output_file: str, search_ids: Optional[List[int]] = None):
        """
        Export saved searches to JSON file.

        Args:
            output_file: Path to output JSON file
            search_ids: List of search IDs to export (None = all)
        """
        if search_ids:
            searches = [self.get(sid) for sid in search_ids if self.get(sid)]
        else:
            searches = self.get_all()

        data = {
            'version': '1.0',
            'exported_at': datetime.now().isoformat(),
            'count': len(searches),
            'searches': [s.to_dict() for s in searches]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def import_from_json(self, input_file: str, merge: bool = True) -> int:
        """
        Import saved searches from JSON file.

        Args:
            input_file: Path to input JSON file
            merge: If True, merge with existing; if False, replace

        Returns:
            Number of searches imported
        """
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not merge:
            # Clear existing searches
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM saved_searches")
            conn.commit()
            conn.close()

        imported = 0
        for search_data in data.get('searches', []):
            # Remove ID to create new entry
            search_data.pop('id', None)

            search = SavedSearch.from_dict(search_data)

            # Check if name already exists
            existing = self.get_by_name(search.name)
            if existing and merge:
                # Skip duplicates when merging
                continue

            try:
                self.save(search)
                imported += 1
            except sqlite3.IntegrityError:
                # Name conflict, skip
                continue

        return imported

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about saved searches."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM saved_searches")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT category) FROM saved_searches")
        categories = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(run_count) FROM saved_searches")
        total_runs = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT name, run_count FROM saved_searches
            ORDER BY run_count DESC LIMIT 5
        """)
        most_used = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT COUNT(*) FROM saved_searches WHERE shortcut_key IS NOT NULL
        """)
        with_shortcuts = cursor.fetchone()[0]

        conn.close()

        return {
            'total_searches': total,
            'categories': categories,
            'total_runs': total_runs,
            'most_used': most_used,
            'with_shortcuts': with_shortcuts,
        }

    def _row_to_search(self, row: sqlite3.Row) -> SavedSearch:
        """Convert database row to SavedSearch object."""
        return SavedSearch(
            id=row['id'],
            name=row['name'],
            description=row['description'] or '',
            query=row['query'],
            category=row['category'],
            icon=row['icon'],
            color=row['color'],
            file_types=json.loads(row['file_types']) if row['file_types'] else [],
            min_size=row['min_size'],
            max_size=row['max_size'],
            date_from=row['date_from'],
            date_to=row['date_to'],
            sort_order=row['sort_order'],
            ascending=bool(row['ascending']),
            search_paths=json.loads(row['search_paths']) if row['search_paths'] else [],
            view_mode=row['view_mode'],
            show_preview=bool(row['show_preview']),
            created_at=row['created_at'],
            modified_at=row['modified_at'],
            last_run=row['last_run'],
            run_count=row['run_count'],
            last_result_count=row['last_result_count'],
            shortcut_key=row['shortcut_key'],
        )
