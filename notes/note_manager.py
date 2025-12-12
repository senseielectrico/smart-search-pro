"""
Note manager for CRUD operations and database interactions.

Handles all note operations including creation, reading, updating,
deletion, search, and version history management.
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Optional

# Handle both relative and absolute imports
try:
    from ..core.database import Database
    from ..core.exceptions import QueryError, IntegrityError
    from ..core.logger import get_logger
    from .note_model import Note, NoteCategory, NoteTag, NoteVersion
except ImportError:
    from core.database import Database
    from core.exceptions import QueryError, IntegrityError
    from core.logger import get_logger
    from notes.note_model import Note, NoteCategory, NoteTag, NoteVersion

logger = get_logger(__name__)


class NoteManager:
    """
    Manager for note operations with database integration.

    Features:
    - Full CRUD operations
    - Tag and category management
    - Full-text search
    - Version history (keep last 10 versions)
    - Auto-save support
    - Import/export
    """

    MAX_VERSIONS = 10

    def __init__(self, database: Database):
        """
        Initialize note manager.

        Args:
            database: Database instance
        """
        self.db = database
        self._ensure_tables()

    def _ensure_tables(self):
        """Ensure note tables exist in database."""
        with self.db._pool.get_connection() as conn:
            cursor = conn.cursor()

            # Notes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category_id INTEGER,
                    tags TEXT,
                    linked_path TEXT,
                    is_pinned INTEGER DEFAULT 0,
                    is_markdown INTEGER DEFAULT 1,
                    created_at REAL NOT NULL,
                    modified_at REAL NOT NULL,
                    accessed_at REAL NOT NULL,
                    word_count INTEGER DEFAULT 0,
                    char_count INTEGER DEFAULT 0,
                    FOREIGN KEY (category_id) REFERENCES note_categories(id) ON DELETE SET NULL
                )
            """)

            # Create full-text search index
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
                    title, content, tags,
                    content=notes,
                    content_rowid=id
                )
            """)

            # Triggers to keep FTS in sync
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
                    INSERT INTO notes_fts(rowid, title, content, tags)
                    VALUES (new.id, new.title, new.content, new.tags);
                END
            """)

            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
                    DELETE FROM notes_fts WHERE rowid = old.id;
                END
            """)

            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
                    UPDATE notes_fts SET title = new.title, content = new.content, tags = new.tags
                    WHERE rowid = new.id;
                END
            """)

            # Categories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS note_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    color TEXT DEFAULT '#3498db',
                    icon TEXT DEFAULT '📁',
                    description TEXT,
                    created_at REAL NOT NULL
                )
            """)

            # Tags table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS note_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    color TEXT DEFAULT '#95a5a6',
                    created_at REAL NOT NULL,
                    usage_count INTEGER DEFAULT 0
                )
            """)

            # Version history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS note_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_id INTEGER NOT NULL,
                    version INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
                    UNIQUE(note_id, version)
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_category ON notes(category_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_pinned ON notes(is_pinned)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_linked_path ON notes(linked_path)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_modified ON notes(modified_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_note_versions_note_id ON note_versions(note_id)")

            conn.commit()

        logger.info("Note tables initialized")

    # ========================================================================
    # Note CRUD Operations
    # ========================================================================

    def create_note(self, note: Note) -> int:
        """
        Create a new note.

        Args:
            note: Note to create

        Returns:
            ID of created note
        """
        note.update_counts()
        note.created_at = time.time()
        note.modified_at = note.created_at
        note.accessed_at = note.created_at

        # Update tag usage counts
        for tag in note.tags:
            self._increment_tag_usage(tag)

        note_id = self.db.insert('notes', note.to_dict())
        note.id = note_id

        logger.info("Note created", note_id=note_id, title=note.title)
        return note_id

    def get_note(self, note_id: int) -> Optional[Note]:
        """
        Get note by ID.

        Args:
            note_id: Note ID

        Returns:
            Note or None if not found
        """
        data = self.db.fetchone("SELECT * FROM notes WHERE id = ?", (note_id,))
        if data:
            # Update accessed time
            self.db.execute(
                "UPDATE notes SET accessed_at = ? WHERE id = ?",
                (time.time(), note_id)
            )
            return Note.from_dict(data)
        return None

    def update_note(self, note: Note, save_version: bool = True) -> bool:
        """
        Update existing note.

        Args:
            note: Note to update
            save_version: Whether to save version history

        Returns:
            True if updated successfully
        """
        if not note.id:
            raise ValueError("Note must have an ID to update")

        # Save version history
        if save_version:
            self._save_version(note.id)

        note.update_counts()
        note.modified_at = time.time()

        # Update tag usage counts
        old_note = self.get_note(note.id)
        if old_note:
            # Decrement old tags
            for tag in old_note.tags:
                if tag not in note.tags:
                    self._decrement_tag_usage(tag)
            # Increment new tags
            for tag in note.tags:
                if tag not in old_note.tags:
                    self._increment_tag_usage(tag)

        rows = self.db.update(
            'notes',
            note.to_dict(),
            'id = ?',
            (note.id,)
        )

        logger.info("Note updated", note_id=note.id, title=note.title)
        return rows > 0

    def delete_note(self, note_id: int) -> bool:
        """
        Delete note by ID.

        Args:
            note_id: Note ID

        Returns:
            True if deleted successfully
        """
        # Get note to update tag counts
        note = self.get_note(note_id)
        if note:
            for tag in note.tags:
                self._decrement_tag_usage(tag)

        rows = self.db.delete('notes', 'id = ?', (note_id,))
        logger.info("Note deleted", note_id=note_id)
        return rows > 0

    def get_all_notes(
        self,
        category_id: Optional[int] = None,
        pinned_only: bool = False,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> list[Note]:
        """
        Get all notes with optional filtering.

        Args:
            category_id: Filter by category
            pinned_only: Only return pinned notes
            limit: Maximum number of notes
            offset: Offset for pagination

        Returns:
            List of notes
        """
        query = "SELECT * FROM notes WHERE 1=1"
        params = []

        if category_id is not None:
            query += " AND category_id = ?"
            params.append(category_id)

        if pinned_only:
            query += " AND is_pinned = 1"

        query += " ORDER BY is_pinned DESC, modified_at DESC"

        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        rows = self.db.fetchall(query, tuple(params))
        return [Note.from_dict(row) for row in rows]

    def search_notes(self, query: str, limit: int = 50) -> list[Note]:
        """
        Full-text search in notes.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching notes
        """
        sql = """
            SELECT n.* FROM notes n
            JOIN notes_fts fts ON n.id = fts.rowid
            WHERE notes_fts MATCH ?
            ORDER BY rank, n.modified_at DESC
            LIMIT ?
        """
        rows = self.db.fetchall(sql, (query, limit))
        return [Note.from_dict(row) for row in rows]

    def get_notes_by_tag(self, tag: str) -> list[Note]:
        """
        Get all notes with a specific tag.

        Args:
            tag: Tag name

        Returns:
            List of notes
        """
        sql = "SELECT * FROM notes WHERE tags LIKE ? ORDER BY modified_at DESC"
        # Use LIKE to match tag in comma-separated list
        rows = self.db.fetchall(sql, (f'%{tag}%',))
        notes = [Note.from_dict(row) for row in rows]
        # Filter to exact tag matches
        return [n for n in notes if tag in n.tags]

    def get_notes_by_linked_path(self, path: str) -> list[Note]:
        """
        Get notes linked to a file/folder path.

        Args:
            path: File or folder path

        Returns:
            List of linked notes
        """
        rows = self.db.fetchall(
            "SELECT * FROM notes WHERE linked_path = ? ORDER BY modified_at DESC",
            (path,)
        )
        return [Note.from_dict(row) for row in rows]

    # ========================================================================
    # Category Operations
    # ========================================================================

    def create_category(self, category: NoteCategory) -> int:
        """Create a new category."""
        category.created_at = time.time()
        category_id = self.db.insert('note_categories', category.to_dict())
        logger.info("Category created", category_id=category_id, name=category.name)
        return category_id

    def get_all_categories(self) -> list[NoteCategory]:
        """Get all categories."""
        rows = self.db.fetchall("SELECT * FROM note_categories ORDER BY name")
        return [NoteCategory.from_dict(row) for row in rows]

    def get_category(self, category_id: int) -> Optional[NoteCategory]:
        """Get category by ID."""
        data = self.db.fetchone(
            "SELECT * FROM note_categories WHERE id = ?",
            (category_id,)
        )
        return NoteCategory.from_dict(data) if data else None

    def update_category(self, category: NoteCategory) -> bool:
        """Update category."""
        if not category.id:
            raise ValueError("Category must have an ID to update")
        rows = self.db.update(
            'note_categories',
            category.to_dict(),
            'id = ?',
            (category.id,)
        )
        return rows > 0

    def delete_category(self, category_id: int) -> bool:
        """Delete category (notes will have category_id set to NULL)."""
        rows = self.db.delete('note_categories', 'id = ?', (category_id,))
        logger.info("Category deleted", category_id=category_id)
        return rows > 0

    # ========================================================================
    # Tag Operations
    # ========================================================================

    def get_all_tags(self) -> list[NoteTag]:
        """Get all tags sorted by usage."""
        rows = self.db.fetchall(
            "SELECT * FROM note_tags ORDER BY usage_count DESC, name"
        )
        return [NoteTag.from_dict(row) for row in rows]

    def get_or_create_tag(self, tag_name: str) -> NoteTag:
        """Get existing tag or create new one."""
        data = self.db.fetchone(
            "SELECT * FROM note_tags WHERE name = ?",
            (tag_name,)
        )
        if data:
            return NoteTag.from_dict(data)

        # Create new tag
        tag = NoteTag(name=tag_name)
        tag_id = self.db.insert('note_tags', tag.to_dict())
        tag.id = tag_id
        return tag

    def _increment_tag_usage(self, tag_name: str):
        """Increment tag usage count."""
        tag = self.get_or_create_tag(tag_name)
        self.db.execute(
            "UPDATE note_tags SET usage_count = usage_count + 1 WHERE id = ?",
            (tag.id,)
        )

    def _decrement_tag_usage(self, tag_name: str):
        """Decrement tag usage count."""
        data = self.db.fetchone(
            "SELECT id FROM note_tags WHERE name = ?",
            (tag_name,)
        )
        if data:
            self.db.execute(
                "UPDATE note_tags SET usage_count = MAX(0, usage_count - 1) WHERE id = ?",
                (data['id'],)
            )

    # ========================================================================
    # Version History
    # ========================================================================

    def _save_version(self, note_id: int):
        """Save current note state as version."""
        note = self.get_note(note_id)
        if not note:
            return

        # Get next version number
        result = self.db.fetchone(
            "SELECT MAX(version) as max_v FROM note_versions WHERE note_id = ?",
            (note_id,)
        )
        next_version = (result['max_v'] or 0) + 1

        # Save version
        version = NoteVersion(
            note_id=note_id,
            version=next_version,
            title=note.title,
            content=note.content,
        )
        self.db.insert('note_versions', version.to_dict())

        # Clean old versions (keep last MAX_VERSIONS)
        self.db.execute(
            """
            DELETE FROM note_versions
            WHERE note_id = ? AND version <= (
                SELECT MAX(version) - ? FROM note_versions WHERE note_id = ?
            )
            """,
            (note_id, self.MAX_VERSIONS, note_id)
        )

    def get_note_versions(self, note_id: int) -> list[NoteVersion]:
        """Get all versions of a note."""
        rows = self.db.fetchall(
            "SELECT * FROM note_versions WHERE note_id = ? ORDER BY version DESC",
            (note_id,)
        )
        return [NoteVersion.from_dict(row) for row in rows]

    def restore_version(self, note_id: int, version: int) -> bool:
        """Restore note to a specific version."""
        version_data = self.db.fetchone(
            "SELECT * FROM note_versions WHERE note_id = ? AND version = ?",
            (note_id, version)
        )
        if not version_data:
            return False

        # Save current state as version before restoring
        self._save_version(note_id)

        # Restore
        self.db.update(
            'notes',
            {
                'title': version_data['title'],
                'content': version_data['content'],
                'modified_at': time.time(),
            },
            'id = ?',
            (note_id,)
        )

        logger.info("Note restored to version", note_id=note_id, version=version)
        return True

    # ========================================================================
    # Import/Export
    # ========================================================================

    def export_note_to_json(self, note_id: int) -> str:
        """Export note to JSON string."""
        note = self.get_note(note_id)
        if not note:
            raise ValueError(f"Note {note_id} not found")

        return json.dumps(note.to_dict(), indent=2)

    def export_note_to_markdown(self, note_id: int) -> str:
        """Export note to Markdown format."""
        note = self.get_note(note_id)
        if not note:
            raise ValueError(f"Note {note_id} not found")

        md = f"# {note.title}\n\n"
        if note.tags:
            md += f"**Tags:** {', '.join(note.tags)}\n\n"
        if note.linked_path:
            md += f"**Linked to:** `{note.linked_path}`\n\n"
        md += "---\n\n"
        md += note.content
        return md

    def import_note_from_json(self, json_str: str) -> int:
        """Import note from JSON string."""
        data = json.loads(json_str)
        data.pop('id', None)  # Remove ID to create new note
        note = Note.from_dict(data)
        return self.create_note(note)

    def export_all_notes(self, output_path: Path):
        """Export all notes to a directory."""
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        notes = self.get_all_notes()
        for note in notes:
            filename = f"{note.id}_{note.title[:50]}.md"
            # Sanitize filename
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
            file_path = output_path / filename

            content = self.export_note_to_markdown(note.id)
            file_path.write_text(content, encoding='utf-8')

        logger.info("Exported all notes", count=len(notes), path=str(output_path))

    # ========================================================================
    # Statistics
    # ========================================================================

    def get_stats(self) -> dict:
        """Get notes statistics."""
        stats = {}

        # Total notes
        result = self.db.fetchone("SELECT COUNT(*) as count FROM notes")
        stats['total_notes'] = result['count'] if result else 0

        # Pinned notes
        result = self.db.fetchone("SELECT COUNT(*) as count FROM notes WHERE is_pinned = 1")
        stats['pinned_notes'] = result['count'] if result else 0

        # Notes by category
        rows = self.db.fetchall("""
            SELECT c.name, COUNT(n.id) as count
            FROM note_categories c
            LEFT JOIN notes n ON n.category_id = c.id
            GROUP BY c.id, c.name
        """)
        stats['by_category'] = {row['name']: row['count'] for row in rows}

        # Total tags
        result = self.db.fetchone("SELECT COUNT(*) as count FROM note_tags")
        stats['total_tags'] = result['count'] if result else 0

        # Most used tags
        rows = self.db.fetchall(
            "SELECT name, usage_count FROM note_tags ORDER BY usage_count DESC LIMIT 10"
        )
        stats['top_tags'] = [(row['name'], row['usage_count']) for row in rows]

        return stats
