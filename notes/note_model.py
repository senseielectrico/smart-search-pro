"""
Data models for notes system.

Defines the structure for notes, categories, tags, and version history.
"""

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NoteCategory:
    """Note category model."""

    id: Optional[int] = None
    name: str = ""
    color: str = "#3498db"
    icon: str = "📁"
    description: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'icon': self.icon,
            'description': self.description,
            'created_at': self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'NoteCategory':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class NoteTag:
    """Note tag model."""

    id: Optional[int] = None
    name: str = ""
    color: str = "#95a5a6"
    created_at: float = field(default_factory=time.time)
    usage_count: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'created_at': self.created_at,
            'usage_count': self.usage_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'NoteTag':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class NoteVersion:
    """Note version history model."""

    id: Optional[int] = None
    note_id: int = 0
    version: int = 1
    title: str = ""
    content: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'note_id': self.note_id,
            'version': self.version,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'NoteVersion':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Note:
    """Note model with full metadata."""

    id: Optional[int] = None
    title: str = "Untitled Note"
    content: str = ""
    category_id: Optional[int] = None
    tags: list[str] = field(default_factory=list)
    linked_path: Optional[str] = None
    is_pinned: bool = False
    is_markdown: bool = True
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    word_count: int = 0
    char_count: int = 0

    def __post_init__(self):
        """Calculate word and character counts."""
        self.update_counts()

    def update_counts(self):
        """Update word and character counts."""
        self.char_count = len(self.content)
        self.word_count = len(self.content.split()) if self.content else 0

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category_id': self.category_id,
            'tags': ','.join(self.tags) if self.tags else '',
            'linked_path': self.linked_path,
            'is_pinned': 1 if self.is_pinned else 0,
            'is_markdown': 1 if self.is_markdown else 0,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'accessed_at': self.accessed_at,
            'word_count': self.word_count,
            'char_count': self.char_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Note':
        """Create note from dictionary."""
        # Convert tags from comma-separated string to list
        tags_str = data.pop('tags', '')
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]

        # Convert boolean fields
        is_pinned = bool(data.pop('is_pinned', 0))
        is_markdown = bool(data.pop('is_markdown', 1))

        return cls(
            **data,
            tags=tags,
            is_pinned=is_pinned,
            is_markdown=is_markdown,
        )

    def matches_search(self, query: str) -> bool:
        """Check if note matches search query."""
        query_lower = query.lower()
        return (
            query_lower in self.title.lower() or
            query_lower in self.content.lower() or
            any(query_lower in tag.lower() for tag in self.tags)
        )
