"""
Save search dialog for creating/editing saved searches.

Provides a dialog for creating and editing saved searches with
all parameters, keyboard shortcuts, and visual customization.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QTextEdit, QComboBox, QPushButton, QDialogButtonBox, QLabel,
    QSpinBox, QCheckBox, QListWidget, QGroupBox, QColorDialog,
    QWidget, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette

import sys
if 'search' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent / 'search'))

from saved_searches import SavedSearch, SavedSearchManager


class ColorButton(QPushButton):
    """Button for selecting color."""

    def __init__(self, color: str = "#4A90E2", parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.setFixedSize(60, 30)
        self.clicked.connect(self._choose_color)
        self._update_color()

    def _choose_color(self):
        """Open color picker."""
        color = QColorDialog.getColor(self.color, self, "Choose Color")
        if color.isValid():
            self.color = color
            self._update_color()

    def _update_color(self):
        """Update button color."""
        self.setStyleSheet(
            f"background-color: {self.color.name()}; "
            f"border: 1px solid #ccc;"
        )

    def get_color(self) -> str:
        """Get color as hex string."""
        return self.color.name()


class SaveSearchDialog(QDialog):
    """
    Dialog for saving/editing searches.

    Features:
    - Name and description
    - Category selector
    - Icon/color picker
    - Keyboard shortcut assignment
    - Search parameters preview
    """

    def __init__(self, search: Optional[SavedSearch] = None, parent=None):
        super().__init__(parent)
        self.search = search or SavedSearch()
        self.manager = SavedSearchManager()

        # Search parameters (to be filled from current search state)
        self.search_params = {}

        self.setWindowTitle("Save Search" if not search else f"Edit Search - {search.name}")
        self.setMinimumWidth(500)
        self._init_ui()
        self._load_search()

    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)

        # Basic information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter search name...")
        basic_layout.addRow("Name:", self.name_input)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Optional description...")
        self.description_input.setMaximumHeight(60)
        basic_layout.addRow("Description:", self.description_input)

        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.addItem("General")
        # Load existing categories
        categories = self.manager.get_categories()
        for cat in categories:
            if cat != "General":
                self.category_input.addItem(cat)
        basic_layout.addRow("Category:", self.category_input)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Visual customization
        visual_group = QGroupBox("Visual Customization")
        visual_layout = QFormLayout()

        self.icon_input = QComboBox()
        self.icon_input.addItems([
            "search", "folder", "star", "document", "image",
            "video", "music", "code", "archive", "settings"
        ])
        visual_layout.addRow("Icon:", self.icon_input)

        self.color_button = ColorButton()
        visual_layout.addRow("Color:", self.color_button)

        visual_group.setLayout(visual_layout)
        layout.addWidget(visual_group)

        # Keyboard shortcut
        shortcut_group = QGroupBox("Keyboard Shortcut")
        shortcut_layout = QHBoxLayout()

        shortcut_layout.addWidget(QLabel("Ctrl +"))
        self.shortcut_combo = QComboBox()
        self.shortcut_combo.addItem("None", None)
        for i in range(1, 10):
            self.shortcut_combo.addItem(str(i), i)
        shortcut_layout.addWidget(self.shortcut_combo)
        shortcut_layout.addStretch()

        shortcut_group.setLayout(shortcut_layout)
        layout.addWidget(shortcut_group)

        # Search parameters preview
        params_group = QGroupBox("Search Parameters")
        params_layout = QVBoxLayout()

        self.params_preview = QTextEdit()
        self.params_preview.setReadOnly(True)
        self.params_preview.setMaximumHeight(100)
        self.params_preview.setStyleSheet("background-color: #f5f5f5;")
        params_layout.addWidget(self.params_preview)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_search(self):
        """Load search data into form."""
        if not self.search:
            return

        self.name_input.setText(self.search.name)
        self.description_input.setPlainText(self.search.description)

        # Set category
        index = self.category_input.findText(self.search.category)
        if index >= 0:
            self.category_input.setCurrentIndex(index)
        else:
            self.category_input.setEditText(self.search.category)

        # Set icon
        index = self.icon_input.findText(self.search.icon)
        if index >= 0:
            self.icon_input.setCurrentIndex(index)

        # Set color
        self.color_button.color = QColor(self.search.color)
        self.color_button._update_color()

        # Set shortcut
        if self.search.shortcut_key:
            index = self.shortcut_combo.findData(self.search.shortcut_key)
            if index >= 0:
                self.shortcut_combo.setCurrentIndex(index)

        # Update preview
        self._update_params_preview()

    def set_search_params(self, params: Dict[str, Any]):
        """
        Set search parameters to save.

        Args:
            params: Dictionary with search parameters
        """
        self.search_params = params

        # Update search object
        self.search.query = params.get('query', '')
        self.search.file_types = params.get('file_types', [])
        self.search.min_size = params.get('min_size')
        self.search.max_size = params.get('max_size')
        self.search.date_from = params.get('date_from')
        self.search.date_to = params.get('date_to')
        self.search.sort_order = params.get('sort_order', 'name')
        self.search.ascending = params.get('ascending', True)
        self.search.search_paths = params.get('search_paths', [])
        self.search.view_mode = params.get('view_mode', 'list')
        self.search.show_preview = params.get('show_preview', True)

        self._update_params_preview()

    def _update_params_preview(self):
        """Update parameters preview."""
        preview_lines = []

        if self.search.query:
            preview_lines.append(f"Query: {self.search.query}")

        if self.search.file_types:
            preview_lines.append(f"File Types: {', '.join(self.search.file_types)}")

        if self.search.min_size or self.search.max_size:
            size_str = "Size: "
            if self.search.min_size:
                size_mb = self.search.min_size / (1024 * 1024)
                size_str += f"≥ {size_mb:.1f} MB"
            if self.search.max_size:
                if self.search.min_size:
                    size_str += " and "
                size_mb = self.search.max_size / (1024 * 1024)
                size_str += f"≤ {size_mb:.1f} MB"
            preview_lines.append(size_str)

        if self.search.date_from or self.search.date_to:
            date_str = "Date: "
            if self.search.date_from:
                date_str += f"from {self.search.date_from[:10]}"
            if self.search.date_to:
                if self.search.date_from:
                    date_str += " "
                date_str += f"to {self.search.date_to[:10]}"
            preview_lines.append(date_str)

        if self.search.search_paths:
            preview_lines.append(f"Search Paths: {len(self.search.search_paths)} path(s)")

        preview_lines.append(
            f"Sort: {self.search.sort_order} "
            f"({'ascending' if self.search.ascending else 'descending'})"
        )

        preview_lines.append(
            f"View: {self.search.view_mode}, "
            f"Preview: {'on' if self.search.show_preview else 'off'}"
        )

        self.params_preview.setPlainText("\n".join(preview_lines))

    def _on_save(self):
        """Validate and save search."""
        # Validate name
        name = self.name_input.text().strip()
        if not name:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Invalid Name",
                "Please enter a search name."
            )
            return

        # Validate query
        if not self.search.query:
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "No Query",
                "The search query is empty. Continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # Check if name exists (for new searches)
        if not self.search.id:
            existing = self.manager.get_by_name(name)
            if existing:
                from PyQt6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self,
                    "Name Exists",
                    f"A search named '{name}' already exists. Overwrite it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.search.id = existing.id
                else:
                    return

        # Update search object
        self.search.name = name
        self.search.description = self.description_input.toPlainText().strip()
        self.search.category = self.category_input.currentText().strip() or "General"
        self.search.icon = self.icon_input.currentText()
        self.search.color = self.color_button.get_color()
        self.search.shortcut_key = self.shortcut_combo.currentData()

        # Check if shortcut is already used
        if self.search.shortcut_key:
            existing = self.manager.get_by_shortcut(self.search.shortcut_key)
            if existing and existing.id != self.search.id:
                from PyQt6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self,
                    "Shortcut In Use",
                    f"Ctrl+{self.search.shortcut_key} is already assigned to '{existing.name}'.\n"
                    "Reassign to this search?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
                else:
                    # Remove shortcut from other search
                    existing.shortcut_key = None
                    self.manager.save(existing)

        # Save to database
        try:
            search_id = self.manager.save(self.search)
            self.search.id = search_id
            self.accept()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save search: {e}"
            )

    def get_search(self) -> SavedSearch:
        """Get the saved search."""
        return self.search
