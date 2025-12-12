"""
Notes module for Smart Search Pro.

Provides integrated notepad functionality with:
- Note management (create, read, update, delete)
- Tags and categories
- Full-text search
- Markdown support
- File/folder linking
- Version history
"""

from .note_model import Note, NoteCategory, NoteTag, NoteVersion
from .note_manager import NoteManager

__all__ = [
    'Note',
    'NoteCategory',
    'NoteTag',
    'NoteVersion',
    'NoteManager',
]
