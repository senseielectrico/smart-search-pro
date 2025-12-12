"""
Quick note dialog for rapid note capture.

Features:
- Global hotkey (Ctrl+Shift+N)
- Minimal interface
- Auto-save on close
- Recent notes dropdown
- Quick tag input
"""

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut, QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QComboBox, QMessageBox
)

try:
    from ..notes.note_manager import NoteManager
    from ..notes.note_model import Note
except ImportError:
    from notes.note_manager import NoteManager
    from notes.note_model import Note


class QuickNoteDialog(QDialog):
    """
    Quick note dialog for rapid note capture.

    Signals:
        note_saved: Emitted when a note is saved (note_id)
    """

    note_saved = pyqtSignal(int)

    def __init__(self, note_manager: NoteManager, parent=None):
        super().__init__(parent)
        self.note_manager = note_manager
        self.current_note: Optional[Note] = None

        self.setWindowTitle("Quick Note")
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.resize(500, 400)

        self._setup_ui()
        self._setup_shortcuts()

        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save)

    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()

        # Recent notes dropdown
        header_layout.addWidget(QLabel("Quick Note:"))
        self.recent_combo = QComboBox()
        self.recent_combo.addItem("New Note", None)
        self.recent_combo.currentIndexChanged.connect(self._load_recent_note)
        header_layout.addWidget(self.recent_combo)

        # Save indicator
        self.save_indicator = QLabel("●")
        self.save_indicator.setStyleSheet("color: #95a5a6; font-size: 14pt;")
        self.save_indicator.setToolTip("Unsaved changes")
        header_layout.addWidget(self.save_indicator)

        layout.addLayout(header_layout)

        # Title
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Note title (optional)...")
        self.title_edit.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.title_edit.textChanged.connect(self._mark_modified)
        layout.addWidget(self.title_edit)

        # Content
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText(
            "Start typing your note...\n\n"
            "Tips:\n"
            "- Press Ctrl+Enter to save and close\n"
            "- Press Escape to close\n"
            "- Auto-saves every 5 seconds"
        )
        self.content_edit.textChanged.connect(self._mark_modified)
        self.content_edit.textChanged.connect(self._start_auto_save)
        layout.addWidget(self.content_edit)

        # Tags
        tag_layout = QHBoxLayout()
        tag_layout.addWidget(QLabel("Tags:"))
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("tag1, tag2, tag3...")
        self.tags_edit.textChanged.connect(self._mark_modified)
        tag_layout.addWidget(self.tags_edit)
        layout.addLayout(tag_layout)

        # Buttons
        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("Save")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self._save_and_close)
        button_layout.addWidget(self.save_btn)

        self.save_new_btn = QPushButton("Save && New")
        self.save_new_btn.clicked.connect(self._save_and_new)
        button_layout.addWidget(self.save_new_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        button_layout.addStretch()

        # Word count
        self.word_count_label = QLabel("Words: 0")
        self.word_count_label.setStyleSheet("color: #7f8c8d; font-size: 9pt;")
        button_layout.addWidget(self.word_count_label)

        layout.addLayout(button_layout)

        # Update word count timer
        self.word_count_timer = QTimer()
        self.word_count_timer.timeout.connect(self._update_word_count)
        self.word_count_timer.start(1000)

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Ctrl+Enter to save and close
        save_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        save_shortcut.activated.connect(self._save_and_close)

        # Ctrl+Shift+N to open (when parent has focus)
        if self.parent():
            open_shortcut = QShortcut(QKeySequence("Ctrl+Shift+N"), self.parent())
            open_shortcut.activated.connect(self.show_and_focus)

        # Escape to close
        close_shortcut = QShortcut(QKeySequence("Escape"), self)
        close_shortcut.activated.connect(self.close)

    def _load_recent_notes(self):
        """Load recent notes into dropdown."""
        self.recent_combo.clear()
        self.recent_combo.addItem("New Note", None)

        # Get last 10 notes
        notes = self.note_manager.get_all_notes(limit=10)
        for note in notes:
            title = note.title[:40]
            if len(note.title) > 40:
                title += "..."
            self.recent_combo.addItem(title, note.id)

    def _load_recent_note(self, index: int):
        """Load a recent note."""
        note_id = self.recent_combo.currentData()
        if note_id is None:
            self._clear_form()
            return

        note = self.note_manager.get_note(note_id)
        if note:
            self.current_note = note
            self.title_edit.setText(note.title)
            self.content_edit.setPlainText(note.content)
            self.tags_edit.setText(', '.join(note.tags))
            self._mark_saved()

    def _clear_form(self):
        """Clear the form for a new note."""
        self.current_note = None
        self.title_edit.clear()
        self.content_edit.clear()
        self.tags_edit.clear()
        self.content_edit.setFocus()
        self._mark_saved()

    def _mark_modified(self):
        """Mark as modified."""
        self.save_indicator.setStyleSheet("color: #e74c3c; font-size: 14pt;")
        self.save_indicator.setToolTip("Unsaved changes")

    def _mark_saved(self):
        """Mark as saved."""
        self.save_indicator.setStyleSheet("color: #27ae60; font-size: 14pt;")
        self.save_indicator.setToolTip("Saved")

    def _start_auto_save(self):
        """Start auto-save timer."""
        self.auto_save_timer.stop()
        self.auto_save_timer.start(5000)  # 5 seconds

    def _auto_save(self):
        """Auto-save the note."""
        content = self.content_edit.toPlainText().strip()
        if not content:
            return

        try:
            self._save_note()
            self._mark_saved()
        except Exception as e:
            print(f"Auto-save error: {e}")

    def _save_note(self) -> int:
        """
        Save the note.

        Returns:
            Note ID
        """
        title = self.title_edit.text().strip()
        content = self.content_edit.toPlainText().strip()

        if not content:
            raise ValueError("Note content is required")

        # Parse tags
        tags_text = self.tags_edit.text()
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]

        # Generate title if empty
        if not title:
            # Use first line or first 50 chars
            first_line = content.split('\n')[0]
            title = first_line[:50]
            if len(first_line) > 50:
                title += "..."

        if self.current_note:
            # Update existing note
            self.current_note.title = title
            self.current_note.content = content
            self.current_note.tags = tags
            self.note_manager.update_note(self.current_note)
            note_id = self.current_note.id
        else:
            # Create new note
            note = Note(title=title, content=content, tags=tags)
            note_id = self.note_manager.create_note(note)
            self.current_note = note
            self.current_note.id = note_id

        self.note_saved.emit(note_id)
        return note_id

    def _save_and_close(self):
        """Save and close dialog."""
        content = self.content_edit.toPlainText().strip()
        if not content:
            self.reject()
            return

        try:
            self._save_note()
            self._mark_saved()
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save note: {e}")

    def _save_and_new(self):
        """Save and create a new note."""
        content = self.content_edit.toPlainText().strip()
        if not content:
            return

        try:
            self._save_note()
            self._clear_form()
            self._load_recent_notes()
            QMessageBox.information(
                self,
                "Saved",
                "Note saved! Ready for a new note.",
                QMessageBox.StandardButton.Ok
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save note: {e}")

    def _update_word_count(self):
        """Update word count display."""
        text = self.content_edit.toPlainText()
        words = len(text.split()) if text else 0
        self.word_count_label.setText(f"Words: {words}")

    def closeEvent(self, event):
        """Handle close event - auto-save if content exists."""
        content = self.content_edit.toPlainText().strip()
        if content and self.save_indicator.toolTip() == "Unsaved changes":
            try:
                self._save_note()
            except Exception as e:
                print(f"Auto-save on close error: {e}")

        self.auto_save_timer.stop()
        self.word_count_timer.stop()
        event.accept()

    # ========================================================================
    # Public API
    # ========================================================================

    def show_and_focus(self):
        """Show dialog and focus content editor."""
        self._load_recent_notes()
        self.show()
        self.raise_()
        self.activateWindow()
        self.content_edit.setFocus()

    def show_for_path(self, path: str):
        """Show dialog to create note for a path."""
        self._clear_form()
        self.title_edit.setText(f"Note for {path}")
        self.show_and_focus()


class QuickNoteButton(QPushButton):
    """
    Quick note button that opens the dialog.

    Can be added to any toolbar.
    """

    def __init__(self, note_manager: NoteManager, parent=None):
        super().__init__("Quick Note", parent)
        self.note_manager = note_manager
        self.dialog: Optional[QuickNoteDialog] = None

        self.setToolTip("Quick Note (Ctrl+Shift+N)")
        self.clicked.connect(self._show_dialog)

        # Setup global shortcut
        if parent:
            shortcut = QShortcut(QKeySequence("Ctrl+Shift+N"), parent)
            shortcut.activated.connect(self._show_dialog)

    def _show_dialog(self):
        """Show quick note dialog."""
        if not self.dialog:
            self.dialog = QuickNoteDialog(self.note_manager, self.parent())

        self.dialog.show_and_focus()
