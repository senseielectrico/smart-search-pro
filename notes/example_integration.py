"""
Complete integration example for the Notes system.

Shows how to integrate the notes system into Smart Search Pro
or use it standalone.
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QToolBar, QMessageBox
)
from PyQt6.QtCore import Qt

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import Database
from notes.note_manager import NoteManager
from notes.note_model import Note, NoteCategory
from ui.notepad_panel import NotepadPanel
from ui.quick_note_dialog import QuickNoteButton


class NotesExampleWindow(QMainWindow):
    """Example application window with notes integration."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Search Pro - Notes Example")
        self.resize(1200, 800)

        # Initialize database and note manager
        db_path = Path.home() / ".smart_search" / "smart_search.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db = Database(db_path)
        self.note_manager = NoteManager(self.db)

        # Create default categories if none exist
        self._create_default_categories()

        self._setup_ui()

    def _create_default_categories(self):
        """Create default categories."""
        categories = self.note_manager.get_all_categories()
        if not categories:
            default_cats = [
                NoteCategory(name="Personal", icon="👤", color="#3498db"),
                NoteCategory(name="Work", icon="💼", color="#e74c3c"),
                NoteCategory(name="Projects", icon="🚀", color="#9b59b6"),
                NoteCategory(name="Ideas", icon="💡", color="#f39c12"),
                NoteCategory(name="Learning", icon="📚", color="#27ae60"),
            ]
            for cat in default_cats:
                self.note_manager.create_category(cat)

    def _setup_ui(self):
        """Setup UI components."""
        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Quick note button
        quick_note_btn = QuickNoteButton(self.note_manager, self)
        quick_note_btn.dialog.note_saved.connect(self._on_note_saved)
        toolbar.addWidget(quick_note_btn)

        toolbar.addSeparator()

        # Example buttons
        example_btn = toolbar.addAction("Create Example Notes")
        example_btn.triggered.connect(self._create_example_notes)

        stats_btn = toolbar.addAction("Show Statistics")
        stats_btn.triggered.connect(self._show_stats)

        # Tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Notes panel
        self.notepad = NotepadPanel(self.note_manager)
        self.notepad.note_linked.connect(self._on_note_linked)
        self.tabs.addTab(self.notepad, "📝 Notes")

        # Status bar
        self.statusBar().showMessage("Ready - Press Ctrl+Shift+N for quick note")

    def _create_example_notes(self):
        """Create example notes."""
        examples = [
            Note(
                title="Welcome to Notes",
                content="""# Welcome to the Notes System!

This is an example note showing **Markdown** support.

## Features

- Rich text formatting
- Tags and categories
- Full-text search
- File linking
- Auto-save
- Version history

## Getting Started

1. Create a new note
2. Add tags and categories
3. Link to files/folders
4. Use Ctrl+Shift+N for quick notes

Happy note-taking! 📝
""",
                tags=["welcome", "tutorial"],
                is_pinned=True,
            ),
            Note(
                title="Python Best Practices",
                content="""# Python Best Practices

## Code Style
- Follow PEP 8
- Use meaningful variable names
- Write docstrings

## Performance
- Use list comprehensions
- Profile before optimizing
- Consider generators for large datasets

## Testing
- Write unit tests
- Use pytest
- Aim for high coverage

```python
def example():
    '''This is a docstring.'''
    return [x**2 for x in range(10)]
```
""",
                tags=["python", "programming", "best-practices"],
            ),
            Note(
                title="Project Ideas",
                content="""# Project Ideas

## Web Apps
- [ ] Personal blog
- [ ] Task manager
- [ ] Recipe organizer

## Desktop Apps
- [x] Smart Search Pro
- [ ] Note-taking app
- [ ] File organizer

## Mobile Apps
- [ ] Habit tracker
- [ ] Expense tracker
""",
                tags=["ideas", "projects"],
            ),
            Note(
                title="Meeting Notes - 2024-12-12",
                content="""# Team Meeting

**Date:** December 12, 2024
**Attendees:** Team A, Team B

## Agenda
1. Project status
2. Timeline review
3. Next steps

## Discussion
- Progress on notes system integration
- Database optimization completed
- UI improvements in progress

## Action Items
- [ ] Complete testing
- [ ] Update documentation
- [ ] Schedule next meeting
""",
                tags=["meeting", "work"],
            ),
            Note(
                title="Learning Resources",
                content="""# Learning Resources

## Python
- Real Python (https://realpython.com)
- Python Docs (https://docs.python.org)
- PyQt6 Tutorial (https://www.pythonguis.com)

## Database
- SQLite Documentation
- SQL Tutorial
- Database Design

## Git
- Pro Git Book
- Git Branching Guide
""",
                tags=["learning", "resources", "reference"],
            ),
        ]

        # Get category IDs
        categories = self.note_manager.get_all_categories()
        cat_map = {cat.name: cat.id for cat in categories}

        # Assign categories
        examples[0].category_id = cat_map.get("Personal")
        examples[1].category_id = cat_map.get("Learning")
        examples[2].category_id = cat_map.get("Ideas")
        examples[3].category_id = cat_map.get("Work")
        examples[4].category_id = cat_map.get("Learning")

        # Create notes
        count = 0
        for note in examples:
            try:
                self.note_manager.create_note(note)
                count += 1
            except Exception as e:
                print(f"Error creating note: {e}")

        # Reload notes panel
        self.notepad._load_notes()

        QMessageBox.information(
            self,
            "Example Notes Created",
            f"Created {count} example notes.\n\n"
            "Try searching, filtering by category/tag, and editing them!"
        )

    def _show_stats(self):
        """Show notes statistics."""
        stats = self.note_manager.get_stats()

        msg = f"""Notes Statistics

Total Notes: {stats['total_notes']}
Pinned Notes: {stats['pinned_notes']}
Total Tags: {stats['total_tags']}

Notes by Category:
"""
        for cat, count in stats['by_category'].items():
            msg += f"  • {cat}: {count}\n"

        msg += "\nTop Tags:\n"
        for tag, count in stats['top_tags'][:5]:
            msg += f"  • {tag}: {count}\n"

        QMessageBox.information(self, "Statistics", msg)

    def _on_note_saved(self, note_id: int):
        """Handle note saved from quick note dialog."""
        note = self.note_manager.get_note(note_id)
        if note:
            self.statusBar().showMessage(f"Saved: {note.title}", 3000)
            self.notepad._load_notes()

    def _on_note_linked(self, note_id: int, path: str):
        """Handle note linked to path."""
        self.statusBar().showMessage(f"Note linked to: {path}", 3000)

    def closeEvent(self, event):
        """Handle close event."""
        self.db.close()
        event.accept()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    # Create and show window
    window = NotesExampleWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
