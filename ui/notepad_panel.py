"""
Main notepad panel for Smart Search Pro.

Provides full note management interface with:
- Note list sidebar with search
- Rich text editor
- Tag and category management
- Pin/unpin notes
- Split view for multiple notes
- Link to files/folders
"""

import time
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget,
    QListWidgetItem, QPushButton, QLineEdit, QLabel, QComboBox,
    QMessageBox, QFileDialog, QMenu, QDialog, QDialogButtonBox,
    QTextEdit, QCheckBox, QGroupBox, QFormLayout, QColorDialog,
    QInputDialog, QToolBar
)

try:
    from ..notes.note_manager import NoteManager
    from ..notes.note_model import Note, NoteCategory, NoteTag
    from .note_editor_widget import NoteEditorWidget
except ImportError:
    from notes.note_manager import NoteManager
    from notes.note_model import Note, NoteCategory, NoteTag
    from ui.note_editor_widget import NoteEditorWidget


class CategoryDialog(QDialog):
    """Dialog for creating/editing categories."""

    def __init__(self, category: Optional[NoteCategory] = None, parent=None):
        super().__init__(parent)
        self.category = category or NoteCategory()
        self.setWindowTitle("Category" if category else "New Category")
        self._setup_ui()

    def _setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # Name
        self.name_edit = QLineEdit(self.category.name)
        form.addRow("Name:", self.name_edit)

        # Icon
        icon_layout = QHBoxLayout()
        self.icon_edit = QLineEdit(self.category.icon)
        self.icon_edit.setMaxLength(2)
        icon_layout.addWidget(self.icon_edit)
        icon_layout.addWidget(QLabel("(emoji)"))
        form.addRow("Icon:", icon_layout)

        # Color
        color_layout = QHBoxLayout()
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(50, 25)
        self.color_btn.setStyleSheet(f"background-color: {self.category.color}")
        self.color_btn.clicked.connect(self._choose_color)
        color_layout.addWidget(self.color_btn)
        self.color_label = QLabel(self.category.color)
        color_layout.addWidget(self.color_label)
        color_layout.addStretch()
        form.addRow("Color:", color_layout)

        # Description
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlainText(self.category.description)
        self.desc_edit.setMaximumHeight(80)
        form.addRow("Description:", self.desc_edit)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _choose_color(self):
        """Choose color."""
        color = QColorDialog.getColor(QColor(self.category.color), self)
        if color.isValid():
            self.category.color = color.name()
            self.color_btn.setStyleSheet(f"background-color: {self.category.color}")
            self.color_label.setText(self.category.color)

    def get_category(self) -> NoteCategory:
        """Get category with updated values."""
        self.category.name = self.name_edit.text()
        self.category.icon = self.icon_edit.text() or "📁"
        self.category.description = self.desc_edit.toPlainText()
        return self.category


class NoteListItem(QListWidgetItem):
    """Custom list item for notes."""

    def __init__(self, note: Note):
        super().__init__()
        self.note = note
        self.update_display()

    def update_display(self):
        """Update item display."""
        # Pin indicator
        pin_icon = "📌 " if self.note.is_pinned else ""

        # Title
        title = self.note.title[:50]

        # Preview
        preview = self.note.content[:100].replace('\n', ' ')
        if len(self.note.content) > 100:
            preview += "..."

        # Tags
        tags = f" [{', '.join(self.note.tags[:3])}]" if self.note.tags else ""

        self.setText(f"{pin_icon}{title}\n{preview}{tags}")

        # Style
        if self.note.is_pinned:
            self.setBackground(QColor("#fff3cd"))


class NotepadPanel(QWidget):
    """
    Main notepad panel widget.

    Signals:
        note_linked: Emitted when a note is linked to a path
    """

    note_linked = pyqtSignal(int, str)  # note_id, path

    def __init__(self, note_manager: NoteManager, parent=None):
        super().__init__(parent)
        self.note_manager = note_manager
        self.current_note: Optional[Note] = None
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save)
        self.auto_save_timer.start(30000)  # Auto-save every 30 seconds

        self._setup_ui()
        self._load_notes()
        self._load_categories()

    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left sidebar
        sidebar = self._create_sidebar()
        splitter.addWidget(sidebar)

        # Right editor
        editor_widget = self._create_editor()
        splitter.addWidget(editor_widget)

        splitter.setSizes([300, 700])
        layout.addWidget(splitter)

        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 9pt;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)

    def _create_toolbar(self) -> QToolBar:
        """Create toolbar."""
        toolbar = QToolBar()
        toolbar.setMovable(False)

        # New note
        new_btn = QPushButton("New Note")
        new_btn.setIcon(QIcon.fromTheme("document-new"))
        new_btn.clicked.connect(self._new_note)
        toolbar.addWidget(new_btn)

        # Save
        save_btn = QPushButton("Save")
        save_btn.setIcon(QIcon.fromTheme("document-save"))
        save_btn.clicked.connect(self._save_note)
        toolbar.addWidget(save_btn)

        # Delete
        delete_btn = QPushButton("Delete")
        delete_btn.setIcon(QIcon.fromTheme("edit-delete"))
        delete_btn.clicked.connect(self._delete_note)
        toolbar.addWidget(delete_btn)

        toolbar.addSeparator()

        # Pin/Unpin
        self.pin_btn = QPushButton("Pin")
        self.pin_btn.setCheckable(True)
        self.pin_btn.clicked.connect(self._toggle_pin)
        toolbar.addWidget(self.pin_btn)

        toolbar.addSeparator()

        # Link to file
        link_btn = QPushButton("Link File")
        link_btn.setToolTip("Link note to a file or folder")
        link_btn.clicked.connect(self._link_to_file)
        toolbar.addWidget(link_btn)

        toolbar.addSeparator()

        # Export
        export_btn = QPushButton("Export")
        export_btn.setToolTip("Export note")
        export_btn.clicked.connect(self._export_note)
        toolbar.addWidget(export_btn)

        # Import
        import_btn = QPushButton("Import")
        import_btn.setToolTip("Import notes")
        import_btn.clicked.connect(self._import_notes)
        toolbar.addWidget(import_btn)

        toolbar.addSeparator()

        # Categories
        category_btn = QPushButton("Categories")
        category_btn.clicked.connect(self._manage_categories)
        toolbar.addWidget(category_btn)

        return toolbar

    def _create_sidebar(self) -> QWidget:
        """Create sidebar with note list."""
        sidebar = QWidget()
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(5, 5, 5, 5)

        # Search
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search notes...")
        self.search_edit.textChanged.connect(self._search_notes)
        search_layout.addWidget(self.search_edit)

        clear_btn = QPushButton("×")
        clear_btn.setFixedSize(25, 25)
        clear_btn.clicked.connect(lambda: self.search_edit.clear())
        search_layout.addWidget(clear_btn)
        layout.addLayout(search_layout)

        # Category filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.currentIndexChanged.connect(self._filter_by_category)
        filter_layout.addWidget(self.category_combo)
        layout.addLayout(filter_layout)

        # Tag filter
        tag_layout = QHBoxLayout()
        tag_layout.addWidget(QLabel("Tag:"))
        self.tag_combo = QComboBox()
        self.tag_combo.currentIndexChanged.connect(self._filter_by_tag)
        tag_layout.addWidget(self.tag_combo)
        layout.addLayout(tag_layout)

        # Note list
        self.note_list = QListWidget()
        self.note_list.itemClicked.connect(self._load_note)
        self.note_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.note_list.customContextMenuRequested.connect(self._show_note_context_menu)
        layout.addWidget(self.note_list)

        # Stats
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #7f8c8d; font-size: 9pt;")
        layout.addWidget(self.stats_label)

        return sidebar

    def _create_editor(self) -> QWidget:
        """Create editor area."""
        editor_widget = QWidget()
        layout = QVBoxLayout(editor_widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Note title...")
        self.title_edit.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.title_edit.textChanged.connect(self._mark_modified)
        layout.addWidget(self.title_edit)

        # Metadata row
        meta_layout = QHBoxLayout()

        # Category
        meta_layout.addWidget(QLabel("Category:"))
        self.note_category_combo = QComboBox()
        self.note_category_combo.currentIndexChanged.connect(self._mark_modified)
        meta_layout.addWidget(self.note_category_combo)

        # Tags
        meta_layout.addWidget(QLabel("Tags:"))
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("tag1, tag2, tag3...")
        self.tags_edit.textChanged.connect(self._mark_modified)
        meta_layout.addWidget(self.tags_edit)

        meta_layout.addStretch()
        layout.addLayout(meta_layout)

        # Linked path
        link_layout = QHBoxLayout()
        link_layout.addWidget(QLabel("Linked:"))
        self.linked_path_label = QLabel("None")
        self.linked_path_label.setStyleSheet("color: #3498db;")
        link_layout.addWidget(self.linked_path_label)
        link_layout.addStretch()
        layout.addLayout(link_layout)

        # Editor
        self.editor = NoteEditorWidget()
        self.editor.content_changed.connect(self._mark_modified)
        layout.addWidget(self.editor)

        return editor_widget

    def _load_notes(self):
        """Load all notes into list."""
        self.note_list.clear()
        notes = self.note_manager.get_all_notes()

        for note in notes:
            item = NoteListItem(note)
            self.note_list.addItem(item)

        self._update_stats()

    def _load_categories(self):
        """Load categories into combos."""
        categories = self.note_manager.get_all_categories()

        # Category filter
        self.category_combo.clear()
        self.category_combo.addItem("All Categories", None)
        for cat in categories:
            self.category_combo.addItem(f"{cat.icon} {cat.name}", cat.id)

        # Note category combo
        self.note_category_combo.clear()
        self.note_category_combo.addItem("No Category", None)
        for cat in categories:
            self.note_category_combo.addItem(f"{cat.icon} {cat.name}", cat.id)

        # Tag filter
        tags = self.note_manager.get_all_tags()
        self.tag_combo.clear()
        self.tag_combo.addItem("All Tags", None)
        for tag in tags:
            self.tag_combo.addItem(tag.name, tag.id)

    def _search_notes(self, query: str):
        """Search notes by query."""
        if not query:
            self._load_notes()
            return

        self.note_list.clear()
        notes = self.note_manager.search_notes(query)

        for note in notes:
            item = NoteListItem(note)
            self.note_list.addItem(item)

        self._update_stats()

    def _filter_by_category(self, index: int):
        """Filter notes by category."""
        category_id = self.category_combo.currentData()
        self.note_list.clear()

        notes = self.note_manager.get_all_notes(category_id=category_id)
        for note in notes:
            item = NoteListItem(note)
            self.note_list.addItem(item)

        self._update_stats()

    def _filter_by_tag(self, index: int):
        """Filter notes by tag."""
        tag_name = self.tag_combo.currentText()
        if tag_name == "All Tags":
            self._load_notes()
            return

        self.note_list.clear()
        notes = self.note_manager.get_notes_by_tag(tag_name)
        for note in notes:
            item = NoteListItem(note)
            self.note_list.addItem(item)

        self._update_stats()

    def _load_note(self, item: QListWidgetItem):
        """Load note into editor."""
        if isinstance(item, NoteListItem):
            # Save current note first
            if self.current_note:
                self._save_note(silent=True)

            note = item.note
            self.current_note = note

            self.title_edit.setText(note.title)
            self.editor.set_content(note.content)
            self.tags_edit.setText(', '.join(note.tags))

            # Set category
            for i in range(self.note_category_combo.count()):
                if self.note_category_combo.itemData(i) == note.category_id:
                    self.note_category_combo.setCurrentIndex(i)
                    break

            # Set linked path
            if note.linked_path:
                self.linked_path_label.setText(note.linked_path)
            else:
                self.linked_path_label.setText("None")

            # Set pin button
            self.pin_btn.setChecked(note.is_pinned)

            self.status_label.setText(f"Loaded: {note.title}")

    def _new_note(self):
        """Create new note."""
        # Save current note first
        if self.current_note:
            self._save_note(silent=True)

        note = Note(title="Untitled Note")
        note_id = self.note_manager.create_note(note)
        note.id = note_id

        self.current_note = note
        self._load_notes()

        # Find and select the new note
        for i in range(self.note_list.count()):
            item = self.note_list.item(i)
            if isinstance(item, NoteListItem) and item.note.id == note_id:
                self.note_list.setCurrentItem(item)
                break

        self.title_edit.setFocus()
        self.title_edit.selectAll()
        self.status_label.setText("New note created")

    def _save_note(self, silent: bool = False):
        """Save current note."""
        if not self.current_note:
            return

        self.current_note.title = self.title_edit.text() or "Untitled Note"
        self.current_note.content = self.editor.get_content()

        # Parse tags
        tags_text = self.tags_edit.text()
        self.current_note.tags = [
            tag.strip() for tag in tags_text.split(',') if tag.strip()
        ]

        # Get category
        self.current_note.category_id = self.note_category_combo.currentData()

        # Update
        self.note_manager.update_note(self.current_note)

        # Update list item
        current_item = self.note_list.currentItem()
        if isinstance(current_item, NoteListItem):
            current_item.note = self.current_note
            current_item.update_display()

        if not silent:
            self.status_label.setText(f"Saved: {self.current_note.title}")

    def _auto_save(self):
        """Auto-save current note."""
        if self.current_note:
            self._save_note(silent=True)

    def _delete_note(self):
        """Delete current note."""
        if not self.current_note:
            return

        reply = QMessageBox.question(
            self,
            "Delete Note",
            f"Are you sure you want to delete '{self.current_note.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.note_manager.delete_note(self.current_note.id)
            self.current_note = None

            self.title_edit.clear()
            self.editor.clear()
            self.tags_edit.clear()
            self.linked_path_label.setText("None")

            self._load_notes()
            self.status_label.setText("Note deleted")

    def _toggle_pin(self, checked: bool):
        """Toggle note pin status."""
        if not self.current_note:
            return

        self.current_note.is_pinned = checked
        self.note_manager.update_note(self.current_note, save_version=False)

        # Update list item
        current_item = self.note_list.currentItem()
        if isinstance(current_item, NoteListItem):
            current_item.note = self.current_note
            current_item.update_display()

        self._load_notes()  # Reload to re-sort by pinned status

    def _link_to_file(self):
        """Link note to a file or folder."""
        if not self.current_note:
            return

        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Select File")

        if path:
            self.current_note.linked_path = path
            self.linked_path_label.setText(path)
            self._save_note(silent=True)
            self.note_linked.emit(self.current_note.id, path)
            self.status_label.setText(f"Linked to: {path}")

    def _export_note(self):
        """Export current note."""
        if not self.current_note:
            return

        file_types = "Markdown (*.md);;Text (*.txt);;HTML (*.html);;JSON (*.json)"
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Export Note", f"{self.current_note.title}.md", file_types
        )

        if file_path:
            file_path = Path(file_path)
            if "Markdown" in selected_filter or file_path.suffix == ".md":
                content = self.note_manager.export_note_to_markdown(self.current_note.id)
                file_path.write_text(content, encoding='utf-8')
            elif "Text" in selected_filter or file_path.suffix == ".txt":
                self.editor.export_to_text(file_path)
            elif "HTML" in selected_filter or file_path.suffix == ".html":
                self.editor.export_to_html(file_path)
            elif "JSON" in selected_filter or file_path.suffix == ".json":
                content = self.note_manager.export_note_to_json(self.current_note.id)
                file_path.write_text(content, encoding='utf-8')

            self.status_label.setText(f"Exported to: {file_path}")

    def _import_notes(self):
        """Import notes."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Note", "", "JSON (*.json);;Markdown (*.md);;Text (*.txt)"
        )

        if file_path:
            file_path = Path(file_path)
            if file_path.suffix == ".json":
                content = file_path.read_text(encoding='utf-8')
                try:
                    self.note_manager.import_note_from_json(content)
                    self._load_notes()
                    self.status_label.setText(f"Imported: {file_path.name}")
                except Exception as e:
                    QMessageBox.warning(self, "Import Error", f"Failed to import: {e}")
            else:
                # Import as new note
                note = Note(
                    title=file_path.stem,
                    content=file_path.read_text(encoding='utf-8')
                )
                self.note_manager.create_note(note)
                self._load_notes()
                self.status_label.setText(f"Imported: {file_path.name}")

    def _manage_categories(self):
        """Manage categories."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Manage Categories")
        layout = QVBoxLayout(dialog)

        # List
        list_widget = QListWidget()
        categories = self.note_manager.get_all_categories()
        for cat in categories:
            list_widget.addItem(f"{cat.icon} {cat.name}")
        layout.addWidget(list_widget)

        # Buttons
        btn_layout = QHBoxLayout()
        new_btn = QPushButton("New")
        edit_btn = QPushButton("Edit")
        delete_btn = QPushButton("Delete")
        btn_layout.addWidget(new_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        layout.addLayout(btn_layout)

        def new_category():
            cat_dialog = CategoryDialog(parent=dialog)
            if cat_dialog.exec() == QDialog.DialogCode.Accepted:
                cat = cat_dialog.get_category()
                self.note_manager.create_category(cat)
                dialog.close()
                self._load_categories()

        def edit_category():
            current = list_widget.currentRow()
            if current >= 0:
                cat = categories[current]
                cat_dialog = CategoryDialog(cat, parent=dialog)
                if cat_dialog.exec() == QDialog.DialogCode.Accepted:
                    cat = cat_dialog.get_category()
                    self.note_manager.update_category(cat)
                    dialog.close()
                    self._load_categories()

        def delete_category():
            current = list_widget.currentRow()
            if current >= 0:
                cat = categories[current]
                reply = QMessageBox.question(
                    dialog, "Delete Category",
                    f"Delete category '{cat.name}'? Notes will not be deleted."
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.note_manager.delete_category(cat.id)
                    dialog.close()
                    self._load_categories()

        new_btn.clicked.connect(new_category)
        edit_btn.clicked.connect(edit_category)
        delete_btn.clicked.connect(delete_category)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.exec()

    def _show_note_context_menu(self, pos):
        """Show context menu for note list."""
        item = self.note_list.itemAt(pos)
        if not isinstance(item, NoteListItem):
            return

        menu = QMenu()
        open_action = menu.addAction("Open")
        pin_action = menu.addAction("Unpin" if item.note.is_pinned else "Pin")
        menu.addSeparator()
        export_action = menu.addAction("Export...")
        duplicate_action = menu.addAction("Duplicate")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")

        action = menu.exec(self.note_list.mapToGlobal(pos))

        if action == open_action:
            self._load_note(item)
        elif action == pin_action:
            item.note.is_pinned = not item.note.is_pinned
            self.note_manager.update_note(item.note, save_version=False)
            self._load_notes()
        elif action == delete_action:
            reply = QMessageBox.question(
                self, "Delete Note",
                f"Delete '{item.note.title}'?"
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.note_manager.delete_note(item.note.id)
                self._load_notes()

    def _mark_modified(self):
        """Mark note as modified."""
        if self.current_note:
            self.status_label.setText("Modified (auto-save in 30s)")

    def _update_stats(self):
        """Update statistics display."""
        stats = self.note_manager.get_stats()
        self.stats_label.setText(
            f"Notes: {stats['total_notes']} | Pinned: {stats['pinned_notes']}"
        )

    # ========================================================================
    # Public API
    # ========================================================================

    def create_note_for_path(self, path: str):
        """Create a new note linked to a path."""
        note = Note(
            title=f"Note for {Path(path).name}",
            linked_path=path
        )
        note_id = self.note_manager.create_note(note)
        self._load_notes()

        # Find and select the new note
        for i in range(self.note_list.count()):
            item = self.note_list.item(i)
            if isinstance(item, NoteListItem) and item.note.id == note_id:
                self.note_list.setCurrentItem(item)
                self._load_note(item)
                break

        return note_id

    def get_notes_for_path(self, path: str) -> list[Note]:
        """Get all notes linked to a path."""
        return self.note_manager.get_notes_by_linked_path(path)
