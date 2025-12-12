"""
Favorites manager with star ratings and tags.

Provides persistent favorites management with categorization,
ratings, tags, and quick access functionality.
"""

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set


@dataclass
class Favorite:
    """Favorite file or folder."""

    id: Optional[int] = None
    path: str = ""
    name: str = ""
    is_directory: bool = False

    # Rating and organization
    rating: int = 0  # 0-5 stars
    tags: List[str] = field(default_factory=list)
    category: str = "Uncategorized"
    notes: str = ""

    # File metadata (cached)
    file_size: Optional[int] = None
    file_type: str = ""
    modified_date: Optional[str] = None

    # Metadata
    created_at: Optional[str] = None
    accessed_at: Optional[str] = None
    access_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Favorite':
        """Create from dictionary."""
        return cls(**data)


class FavoritesManager:
    """
    Manages favorite files and folders with SQLite storage.

    Features:
    - Star ratings (1-5)
    - Custom tags
    - Categories/collections
    - Quick access list
    - Recent favorites
    - Search and filter
    - Import/export
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize favorites manager.

        Args:
            db_path: Path to SQLite database (default: ~/.smart_search_favorites.db)
        """
        if db_path is None:
            db_path = str(Path.home() / ".smart_search_favorites.db")

        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                is_directory INTEGER DEFAULT 0,

                -- Rating and organization
                rating INTEGER DEFAULT 0,
                tags TEXT,  -- JSON array
                category TEXT DEFAULT 'Uncategorized',
                notes TEXT,

                -- File metadata (cached)
                file_size INTEGER,
                file_type TEXT,
                modified_date TEXT,

                -- Metadata
                created_at TEXT NOT NULL,
                accessed_at TEXT,
                access_count INTEGER DEFAULT 0
            )
        """)

        # Create indices
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rating
            ON favorites(rating)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_category
            ON favorites(category)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created
            ON favorites(created_at DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_accessed
            ON favorites(accessed_at DESC)
        """)

        conn.commit()
        conn.close()

    def add(self, path: str, **kwargs) -> int:
        """
        Add file or folder to favorites.

        Args:
            path: File or folder path
            **kwargs: Optional fields (rating, tags, category, notes)

        Returns:
            ID of favorite
        """
        path_obj = Path(path)

        # Get file metadata
        favorite = Favorite(
            path=str(path_obj.absolute()),
            name=path_obj.name,
            is_directory=path_obj.is_dir(),
            rating=kwargs.get('rating', 0),
            tags=kwargs.get('tags', []),
            category=kwargs.get('category', 'Uncategorized'),
            notes=kwargs.get('notes', ''),
            created_at=datetime.now().isoformat(),
        )

        # Cache file metadata
        if path_obj.exists():
            if path_obj.is_file():
                favorite.file_size = path_obj.stat().st_size
                favorite.file_type = path_obj.suffix.lower()
                favorite.modified_date = datetime.fromtimestamp(
                    path_obj.stat().st_mtime
                ).isoformat()

        return self.save(favorite)

    def save(self, favorite: Favorite) -> int:
        """
        Save or update a favorite.

        Args:
            favorite: Favorite object

        Returns:
            ID of favorite
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        data = {
            'path': favorite.path,
            'name': favorite.name,
            'is_directory': 1 if favorite.is_directory else 0,
            'rating': favorite.rating,
            'tags': json.dumps(favorite.tags),
            'category': favorite.category,
            'notes': favorite.notes,
            'file_size': favorite.file_size,
            'file_type': favorite.file_type,
            'modified_date': favorite.modified_date,
        }

        if favorite.id:
            # Update existing
            cursor.execute("""
                UPDATE favorites
                SET name=?, is_directory=?, rating=?, tags=?, category=?, notes=?,
                    file_size=?, file_type=?, modified_date=?
                WHERE id=?
            """, (
                data['name'], data['is_directory'], data['rating'], data['tags'],
                data['category'], data['notes'], data['file_size'], data['file_type'],
                data['modified_date'], favorite.id
            ))
            favorite_id = favorite.id
        else:
            # Insert new
            data['created_at'] = favorite.created_at or now

            try:
                cursor.execute("""
                    INSERT INTO favorites (
                        path, name, is_directory, rating, tags, category, notes,
                        file_size, file_type, modified_date, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data['path'], data['name'], data['is_directory'], data['rating'],
                    data['tags'], data['category'], data['notes'], data['file_size'],
                    data['file_type'], data['modified_date'], data['created_at']
                ))
                favorite_id = cursor.lastrowid
            except sqlite3.IntegrityError:
                # Path already exists, update instead
                cursor.execute("SELECT id FROM favorites WHERE path=?", (data['path'],))
                row = cursor.fetchone()
                if row:
                    favorite.id = row[0]
                    conn.close()
                    return self.save(favorite)
                raise

        conn.commit()
        conn.close()

        return favorite_id

    def get(self, favorite_id: int) -> Optional[Favorite]:
        """Get favorite by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM favorites WHERE id=?", (favorite_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_favorite(row)
        return None

    def get_by_path(self, path: str) -> Optional[Favorite]:
        """Get favorite by path."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM favorites WHERE path=?", (str(Path(path).absolute()),))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_favorite(row)
        return None

    def is_favorite(self, path: str) -> bool:
        """Check if path is favorited."""
        return self.get_by_path(path) is not None

    def get_all(
        self,
        category: Optional[str] = None,
        min_rating: int = 0,
        tags: Optional[List[str]] = None,
        sort_by: str = 'name',
        ascending: bool = True
    ) -> List[Favorite]:
        """
        Get all favorites with optional filtering and sorting.

        Args:
            category: Filter by category
            min_rating: Minimum rating (0-5)
            tags: Filter by tags (any match)
            sort_by: Sort field (name, rating, created_at, accessed_at)
            ascending: Sort order

        Returns:
            List of Favorite objects
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query
        query = "SELECT * FROM favorites WHERE rating >= ?"
        params = [min_rating]

        if category:
            query += " AND category = ?"
            params.append(category)

        # Sort
        order = "ASC" if ascending else "DESC"
        valid_sort = {'name', 'rating', 'created_at', 'accessed_at'}
        sort_field = sort_by if sort_by in valid_sort else 'name'
        query += f" ORDER BY {sort_field} {order}"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        favorites = [self._row_to_favorite(row) for row in rows]

        # Filter by tags if specified
        if tags:
            tag_set = set(t.lower() for t in tags)
            favorites = [
                f for f in favorites
                if tag_set.intersection(set(t.lower() for t in f.tags))
            ]

        return favorites

    def get_recent(self, limit: int = 10) -> List[Favorite]:
        """Get recently accessed favorites."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM favorites
            WHERE accessed_at IS NOT NULL
            ORDER BY accessed_at DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_favorite(row) for row in rows]

    def get_top_rated(self, limit: int = 10, min_rating: int = 4) -> List[Favorite]:
        """Get top-rated favorites."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM favorites
            WHERE rating >= ?
            ORDER BY rating DESC, name ASC
            LIMIT ?
        """, (min_rating, limit))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_favorite(row) for row in rows]

    def get_categories(self) -> List[str]:
        """Get list of all categories."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT category FROM favorites ORDER BY category
        """)
        categories = [row[0] for row in cursor.fetchall()]

        conn.close()
        return categories

    def get_all_tags(self) -> Set[str]:
        """Get set of all tags used."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT tags FROM favorites WHERE tags IS NOT NULL")
        rows = cursor.fetchall()
        conn.close()

        all_tags = set()
        for row in rows:
            if row[0]:
                tags = json.loads(row[0])
                all_tags.update(tags)

        return all_tags

    def search(self, keyword: str) -> List[Favorite]:
        """Search favorites by name, path, or notes."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        pattern = f"%{keyword}%"
        cursor.execute("""
            SELECT * FROM favorites
            WHERE name LIKE ? OR path LIKE ? OR notes LIKE ?
            ORDER BY rating DESC, name ASC
        """, (pattern, pattern, pattern))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_favorite(row) for row in rows]

    def update_rating(self, favorite_id: int, rating: int):
        """Update favorite rating (0-5)."""
        rating = max(0, min(5, rating))

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE favorites SET rating=? WHERE id=?
        """, (rating, favorite_id))

        conn.commit()
        conn.close()

    def add_tag(self, favorite_id: int, tag: str):
        """Add tag to favorite."""
        favorite = self.get(favorite_id)
        if not favorite:
            return

        if tag not in favorite.tags:
            favorite.tags.append(tag)
            self.save(favorite)

    def remove_tag(self, favorite_id: int, tag: str):
        """Remove tag from favorite."""
        favorite = self.get(favorite_id)
        if not favorite:
            return

        if tag in favorite.tags:
            favorite.tags.remove(tag)
            self.save(favorite)

    def update_access(self, favorite_id: int):
        """Update access timestamp and count."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE favorites
            SET accessed_at=?, access_count=access_count+1
            WHERE id=?
        """, (datetime.now().isoformat(), favorite_id))

        conn.commit()
        conn.close()

    def delete(self, favorite_id: int):
        """Remove from favorites."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM favorites WHERE id=?", (favorite_id,))

        conn.commit()
        conn.close()

    def delete_by_path(self, path: str):
        """Remove from favorites by path."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM favorites WHERE path=?", (str(Path(path).absolute()),))

        conn.commit()
        conn.close()

    def export_to_json(self, output_file: str):
        """Export favorites to JSON file."""
        favorites = self.get_all()

        data = {
            'version': '1.0',
            'exported_at': datetime.now().isoformat(),
            'count': len(favorites),
            'favorites': [f.to_dict() for f in favorites]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def import_from_json(self, input_file: str, merge: bool = True) -> int:
        """
        Import favorites from JSON file.

        Args:
            input_file: Path to input JSON file
            merge: If True, merge with existing; if False, replace

        Returns:
            Number of favorites imported
        """
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not merge:
            # Clear existing favorites
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM favorites")
            conn.commit()
            conn.close()

        imported = 0
        for fav_data in data.get('favorites', []):
            # Remove ID to create new entry
            fav_data.pop('id', None)

            favorite = Favorite.from_dict(fav_data)

            try:
                self.save(favorite)
                imported += 1
            except Exception:
                # Skip on error
                continue

        return imported

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about favorites."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM favorites")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM favorites WHERE is_directory=1")
        folders = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM favorites WHERE is_directory=0")
        files = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT category) FROM favorites")
        categories = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(rating) FROM favorites WHERE rating > 0")
        avg_rating = cursor.fetchone()[0] or 0.0

        cursor.execute("""
            SELECT rating, COUNT(*) FROM favorites GROUP BY rating ORDER BY rating DESC
        """)
        rating_dist = dict(cursor.fetchall())

        conn.close()

        return {
            'total_favorites': total,
            'files': files,
            'folders': folders,
            'categories': categories,
            'average_rating': round(avg_rating, 2),
            'rating_distribution': rating_dist,
            'total_tags': len(self.get_all_tags()),
        }

    def _row_to_favorite(self, row: sqlite3.Row) -> Favorite:
        """Convert database row to Favorite object."""
        return Favorite(
            id=row['id'],
            path=row['path'],
            name=row['name'],
            is_directory=bool(row['is_directory']),
            rating=row['rating'],
            tags=json.loads(row['tags']) if row['tags'] else [],
            category=row['category'],
            notes=row['notes'] or '',
            file_size=row['file_size'],
            file_type=row['file_type'] or '',
            modified_date=row['modified_date'],
            created_at=row['created_at'],
            accessed_at=row['accessed_at'],
            access_count=row['access_count'],
        )
