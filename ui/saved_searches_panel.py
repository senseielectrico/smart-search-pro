"""
Saved searches sidebar panel.

Provides a sidebar for managing and executing saved searches with
drag-to-reorder, context menus, and quick run capabilities.
"""

from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLineEdit, QLabel, QMenu, QMessageBox, QInputDialog,
    QComboBox, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QIcon, QColor, QDrag, QCursor

import sys
if 'search' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent / 'search'))

from saved_searches import SavedSearch, SavedSearchManager


class SavedSearchItem(QListWidgetItem):
    """Custom list item for saved search."""

    def __init__(self, search: SavedSearch):
        super().__init__()
        self.search = search
        self.update_display()

    def update_display(self):
        """Update display text and icon."""
        # Display format: [Icon] Name (Category)
        text = self.search.name
        if self.search.shortcut_key:
            text = f"[Ctrl+{self.search.shortcut_key}] {text}"

        if self.search.run_count > 0:
            text += f" ({self.search.run_count} runs)"

        self.setText(text)

        # Set color
        color = QColor(self.search.color)
        self.setForeground(color)

        # Set tooltip with details
        tooltip = f"<b>{self.search.name}</b><br>"
        if self.search.description:
            tooltip += f"{self.search.description}<br>"
        tooltip += f"<br>Query: {self.search.query}"
        if self.search.category != "General":
            tooltip += f"<br>Category: {self.search.category}"
        if self.search.last_run:
            tooltip += f"<br>Last run: {self.search.last_run[:19]}"
            tooltip += f"<br>Results: {self.search.last_result_count}"
        self.setToolTip(tooltip)


class SavedSearchesPanel(QWidget):
    """
    Saved searches sidebar panel.

    Features:
    - List of saved searches with icons
    - Drag to reorder
    - Right-click context menu
    - Search within saved searches
    - Category filtering
    - Quick run on double-click
    """

    # Signals
    search_selected = pyqtSignal(SavedSearch)  # User selected a search
    search_executed = pyqtSignal(SavedSearch)  # User wants to run search
    search_edited = pyqtSignal(SavedSearch)    # User wants to edit search

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = SavedSearchManager()
        self._init_ui()
        self._load_searches()

    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Header
        header = QLabel("Saved Searches")
        header.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(header)

        # Search box
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search saved searches...")
        self.search_input.textChanged.connect(self._filter_searches)
        search_layout.addWidget(self.search_input)

        # Clear search button
        clear_btn = QPushButton("×")
        clear_btn.setFixedWidth(30)
        clear_btn.setToolTip("Clear search")
        clear_btn.clicked.connect(lambda: self.search_input.clear())
        search_layout.addWidget(clear_btn)

        layout.addLayout(search_layout)

        # Category filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories", None)
        self.category_combo.currentIndexChanged.connect(self._filter_searches)
        filter_layout.addWidget(self.category_combo)
        layout.addLayout(filter_layout)

        # Searches list
        self.searches_list = QListWidget()
        self.searches_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.searches_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.searches_list.customContextMenuRequested.connect(self._show_context_menu)
        self.searches_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.searches_list.itemClicked.connect(self._on_item_clicked)
        self.searches_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        layout.addWidget(self.searches_list)

        # Buttons
        buttons_layout = QHBoxLayout()

        self.new_btn = QPushButton("New")
        self.new_btn.setToolTip("Create new saved search")
        self.new_btn.clicked.connect(self._on_new_search)
        buttons_layout.addWidget(self.new_btn)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setToolTip("Edit selected search")
        self.edit_btn.clicked.connect(self._on_edit_search)
        self.edit_btn.setEnabled(False)
        buttons_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setToolTip("Delete selected search")
        self.delete_btn.clicked.connect(self._on_delete_search)
        self.delete_btn.setEnabled(False)
        buttons_layout.addWidget(self.delete_btn)

        layout.addLayout(buttons_layout)

        # Statistics
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("font-size: 9pt; color: gray;")
        layout.addWidget(self.stats_label)

    def _load_searches(self):
        """Load searches from database."""
        # Update categories combo
        categories = self.manager.get_categories()
        current_category = self.category_combo.currentData()

        self.category_combo.clear()
        self.category_combo.addItem("All Categories", None)
        for category in categories:
            self.category_combo.addItem(category, category)

        # Restore previous selection
        if current_category:
            index = self.category_combo.findData(current_category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

        # Load searches
        self._filter_searches()

        # Update statistics
        stats = self.manager.get_statistics()
        self.stats_label.setText(
            f"{stats['total_searches']} searches | "
            f"{stats['total_runs']} total runs | "
            f"{stats['with_shortcuts']} with shortcuts"
        )

    def _filter_searches(self):
        """Filter searches based on search text and category."""
        search_text = self.search_input.text().strip().lower()
        category = self.category_combo.currentData()

        self.searches_list.clear()

        # Get searches
        if search_text:
            searches = self.manager.search(search_text)
        else:
            searches = self.manager.get_all(category)

        # Add to list
        for search in searches:
            item = SavedSearchItem(search)
            self.searches_list.addItem(item)

        # Update button states
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def _on_item_clicked(self, item: SavedSearchItem):
        """Handle item selection."""
        self.edit_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.search_selected.emit(item.search)

    def _on_item_double_clicked(self, item: SavedSearchItem):
        """Handle double-click to execute search."""
        self.search_executed.emit(item.search)

        # Update run statistics
        # Note: Result count will be updated after search completes
        self.manager.update_run_stats(item.search.id, 0)

    def _show_context_menu(self, pos):
        """Show context menu for list item."""
        item = self.searches_list.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)

        # Run
        run_action = menu.addAction("Run Search")
        run_action.triggered.connect(lambda: self._on_item_double_clicked(item))

        # Edit
        edit_action = menu.addAction("Edit...")
        edit_action.triggered.connect(self._on_edit_search)

        # Duplicate
        duplicate_action = menu.addAction("Duplicate...")
        duplicate_action.triggered.connect(lambda: self._on_duplicate_search(item))

        menu.addSeparator()

        # Assign shortcut
        shortcut_action = menu.addAction("Assign Keyboard Shortcut...")
        shortcut_action.triggered.connect(lambda: self._on_assign_shortcut(item))

        menu.addSeparator()

        # Delete
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(self._on_delete_search)

        menu.exec(QCursor.pos())

    def _on_new_search(self):
        """Create new saved search."""
        # Emit signal to show save search dialog
        # This will be handled by main window
        new_search = SavedSearch(name="New Search")
        self.search_edited.emit(new_search)

    def _on_edit_search(self):
        """Edit selected search."""
        item = self.searches_list.currentItem()
        if isinstance(item, SavedSearchItem):
            self.search_edited.emit(item.search)

    def _on_delete_search(self):
        """Delete selected search."""
        item = self.searches_list.currentItem()
        if not isinstance(item, SavedSearchItem):
            return

        reply = QMessageBox.question(
            self,
            "Delete Search",
            f"Are you sure you want to delete '{item.search.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.manager.delete(item.search.id)
            self._load_searches()

    def _on_duplicate_search(self, item: SavedSearchItem):
        """Duplicate a search."""
        new_name, ok = QInputDialog.getText(
            self,
            "Duplicate Search",
            "Enter name for duplicate:",
            text=f"{item.search.name} (Copy)"
        )

        if ok and new_name:
            try:
                new_id = self.manager.duplicate(item.search.id, new_name)
                self._load_searches()
                QMessageBox.information(
                    self,
                    "Success",
                    f"Search duplicated successfully!"
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to duplicate search: {e}"
                )

    def _on_assign_shortcut(self, item: SavedSearchItem):
        """Assign keyboard shortcut to search."""
        keys = ["None"] + [str(i) for i in range(1, 10)]
        current = str(item.search.shortcut_key) if item.search.shortcut_key else "None"

        key, ok = QInputDialog.getItem(
            self,
            "Assign Shortcut",
            "Select shortcut key (Ctrl+):",
            keys,
            keys.index(current),
            False
        )

        if ok:
            # Update shortcut
            search = item.search
            search.shortcut_key = int(key) if key != "None" else None

            # Check if shortcut already assigned
            if search.shortcut_key:
                existing = self.manager.get_by_shortcut(search.shortcut_key)
                if existing and existing.id != search.id:
                    QMessageBox.warning(
                        self,
                        "Shortcut In Use",
                        f"Ctrl+{key} is already assigned to '{existing.name}'.\n"
                        "Please choose a different key."
                    )
                    return

            self.manager.save(search)
            self._load_searches()

    def refresh(self):
        """Refresh the list."""
        self._load_searches()

    def get_search_by_shortcut(self, key: int) -> Optional[SavedSearch]:
        """Get saved search by keyboard shortcut (1-9)."""
        return self.manager.get_by_shortcut(key)

    def execute_search(self, search_id: int):
        """Execute a saved search by ID."""
        search = self.manager.get(search_id)
        if search:
            self.search_executed.emit(search)

    def update_search_results(self, search_id: int, result_count: int):
        """Update search with result count after execution."""
        self.manager.update_run_stats(search_id, result_count)
        self.refresh()
