"""
Favorites panel with star ratings and tags.

Provides a panel for managing favorite files with ratings, tags,
categories, and quick preview capabilities.
"""

import os
from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLineEdit, QLabel, QMenu, QMessageBox, QComboBox,
    QGridLayout, QToolButton, QDialog, QTextEdit, QSpinBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QColor, QCursor, QFont

import sys
if 'search' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent / 'search'))

from favorites_manager import Favorite, FavoritesManager


class StarRatingWidget(QWidget):
    """Star rating widget (0-5 stars)."""

    rating_changed = pyqtSignal(int)

    def __init__(self, rating: int = 0, parent=None):
        super().__init__(parent)
        self.rating = rating
        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.star_buttons = []
        for i in range(1, 6):
            btn = QToolButton()
            btn.setFixedSize(20, 20)
            btn.setText("★")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, star=i: self._on_star_clicked(star))
            layout.addWidget(btn)
            self.star_buttons.append(btn)

        self._update_display()

    def _on_star_clicked(self, star: int):
        """Handle star click."""
        self.rating = star
        self._update_display()
        self.rating_changed.emit(self.rating)

    def _update_display(self):
        """Update star display."""
        for i, btn in enumerate(self.star_buttons, 1):
            btn.setChecked(i <= self.rating)
            if i <= self.rating:
                btn.setStyleSheet("color: gold; font-weight: bold;")
            else:
                btn.setStyleSheet("color: gray;")

    def set_rating(self, rating: int):
        """Set rating programmatically."""
        self.rating = max(0, min(5, rating))
        self._update_display()


class FavoriteDetailsDialog(QDialog):
    """Dialog for editing favorite details."""

    def __init__(self, favorite: Favorite, parent=None):
        super().__init__(parent)
        self.favorite = favorite
        self.setWindowTitle(f"Edit Favorite - {favorite.name}")
        self.setMinimumWidth(400)
        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)

        # Rating
        rating_layout = QHBoxLayout()
        rating_layout.addWidget(QLabel("Rating:"))
        self.rating_widget = StarRatingWidget(self.favorite.rating)
        rating_layout.addWidget(self.rating_widget)
        rating_layout.addStretch()
        layout.addLayout(rating_layout)

        # Category
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Category:"))
        self.category_input = QLineEdit(self.favorite.category)
        category_layout.addWidget(self.category_input)
        layout.addLayout(category_layout)

        # Tags
        tags_layout = QHBoxLayout()
        tags_layout.addWidget(QLabel("Tags:"))
        self.tags_input = QLineEdit(", ".join(self.favorite.tags))
        self.tags_input.setPlaceholderText("Comma-separated tags")
        tags_layout.addWidget(self.tags_input)
        layout.addLayout(tags_layout)

        # Notes
        layout.addWidget(QLabel("Notes:"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlainText(self.favorite.notes)
        self.notes_input.setMaximumHeight(100)
        layout.addWidget(self.notes_input)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_favorite(self) -> Favorite:
        """Get updated favorite."""
        self.favorite.rating = self.rating_widget.rating
        self.favorite.category = self.category_input.text().strip() or "Uncategorized"
        tags_text = self.tags_input.text().strip()
        self.favorite.tags = [t.strip() for t in tags_text.split(",") if t.strip()]
        self.favorite.notes = self.notes_input.toPlainText().strip()
        return self.favorite


class FavoriteItem(QListWidgetItem):
    """Custom list item for favorite."""

    def __init__(self, favorite: Favorite):
        super().__init__()
        self.favorite = favorite
        self.update_display()

    def update_display(self):
        """Update display text."""
        # Rating stars
        stars = "★" * self.favorite.rating + "☆" * (5 - self.favorite.rating)

        # Build display text
        text = f"{stars} {self.favorite.name}"

        # Add tags if present
        if self.favorite.tags:
            text += f" [{', '.join(self.favorite.tags[:3])}]"

        self.setText(text)

        # Icon for directory vs file
        if self.favorite.is_directory:
            icon_char = "📁"
        else:
            icon_char = "📄"

        # Tooltip
        tooltip = f"<b>{icon_char} {self.favorite.name}</b><br>"
        tooltip += f"Path: {self.favorite.path}<br>"
        tooltip += f"Rating: {self.favorite.rating}/5<br>"
        if self.favorite.category != "Uncategorized":
            tooltip += f"Category: {self.favorite.category}<br>"
        if self.favorite.tags:
            tooltip += f"Tags: {', '.join(self.favorite.tags)}<br>"
        if self.favorite.notes:
            tooltip += f"<br>{self.favorite.notes}"
        if self.favorite.file_size:
            size_mb = self.favorite.file_size / (1024 * 1024)
            tooltip += f"<br>Size: {size_mb:.2f} MB"

        self.setToolTip(tooltip)


class FavoritesPanel(QWidget):
    """
    Favorites panel.

    Features:
    - Star rating toggle
    - Grid/list view
    - Sort by name, rating, date added, category
    - Filter by tag/category
    - Quick preview on hover
    - Remove from favorites
    """

    # Signals
    favorite_selected = pyqtSignal(Favorite)
    favorite_opened = pyqtSignal(str)  # Path to open
    toggle_favorite = pyqtSignal(str)  # Toggle favorite for path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = FavoritesManager()
        self._init_ui()
        self._load_favorites()

    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Header
        header = QLabel("Favorites")
        header.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(header)

        # Search and filter
        filter_layout = QGridLayout()

        # Search box
        filter_layout.addWidget(QLabel("Search:"), 0, 0)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search favorites...")
        self.search_input.textChanged.connect(self._filter_favorites)
        filter_layout.addWidget(self.search_input, 0, 1)

        # Category filter
        filter_layout.addWidget(QLabel("Category:"), 1, 0)
        self.category_combo = QComboBox()
        self.category_combo.currentIndexChanged.connect(self._filter_favorites)
        filter_layout.addWidget(self.category_combo, 1, 1)

        # Tag filter
        filter_layout.addWidget(QLabel("Tag:"), 2, 0)
        self.tag_combo = QComboBox()
        self.tag_combo.currentIndexChanged.connect(self._filter_favorites)
        filter_layout.addWidget(self.tag_combo, 2, 1)

        # Rating filter
        filter_layout.addWidget(QLabel("Min Rating:"), 3, 0)
        self.rating_spin = QSpinBox()
        self.rating_spin.setRange(0, 5)
        self.rating_spin.setValue(0)
        self.rating_spin.valueChanged.connect(self._filter_favorites)
        filter_layout.addWidget(self.rating_spin, 3, 1)

        layout.addLayout(filter_layout)

        # Sort options
        sort_layout = QHBoxLayout()
        sort_layout.addWidget(QLabel("Sort by:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Name", "Rating", "Date Added", "Last Accessed"])
        self.sort_combo.currentTextChanged.connect(self._filter_favorites)
        sort_layout.addWidget(self.sort_combo)

        self.sort_order_btn = QPushButton("↓")
        self.sort_order_btn.setFixedWidth(30)
        self.sort_order_btn.setCheckable(True)
        self.sort_order_btn.setToolTip("Toggle sort order")
        self.sort_order_btn.clicked.connect(self._filter_favorites)
        sort_layout.addWidget(self.sort_order_btn)

        layout.addLayout(sort_layout)

        # Favorites list
        self.favorites_list = QListWidget()
        self.favorites_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.favorites_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.favorites_list.customContextMenuRequested.connect(self._show_context_menu)
        self.favorites_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.favorites_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.favorites_list)

        # Buttons
        buttons_layout = QHBoxLayout()

        self.open_btn = QPushButton("Open")
        self.open_btn.setToolTip("Open selected favorite")
        self.open_btn.clicked.connect(self._on_open_favorite)
        self.open_btn.setEnabled(False)
        buttons_layout.addWidget(self.open_btn)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setToolTip("Edit favorite details")
        self.edit_btn.clicked.connect(self._on_edit_favorite)
        self.edit_btn.setEnabled(False)
        buttons_layout.addWidget(self.edit_btn)

        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setToolTip("Remove from favorites")
        self.remove_btn.clicked.connect(self._on_remove_favorite)
        self.remove_btn.setEnabled(False)
        buttons_layout.addWidget(self.remove_btn)

        layout.addLayout(buttons_layout)

        # Statistics
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("font-size: 9pt; color: gray;")
        layout.addWidget(self.stats_label)

    def _load_favorites(self):
        """Load favorites from database."""
        # Update filter combos
        self._update_filters()

        # Load favorites
        self._filter_favorites()

        # Update statistics
        stats = self.manager.get_statistics()
        self.stats_label.setText(
            f"{stats['total_favorites']} favorites | "
            f"{stats['files']} files | "
            f"{stats['folders']} folders | "
            f"Avg rating: {stats['average_rating']:.1f}"
        )

    def _update_filters(self):
        """Update filter combo boxes."""
        # Categories
        categories = self.manager.get_categories()
        current_category = self.category_combo.currentText()

        self.category_combo.clear()
        self.category_combo.addItem("All Categories")
        self.category_combo.addItems(categories)

        if current_category:
            index = self.category_combo.findText(current_category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

        # Tags
        tags = sorted(self.manager.get_all_tags())
        current_tag = self.tag_combo.currentText()

        self.tag_combo.clear()
        self.tag_combo.addItem("All Tags")
        self.tag_combo.addItems(tags)

        if current_tag:
            index = self.tag_combo.findText(current_tag)
            if index >= 0:
                self.tag_combo.setCurrentIndex(index)

    def _filter_favorites(self):
        """Filter and sort favorites."""
        # Get filters
        search_text = self.search_input.text().strip()
        category = self.category_combo.currentText()
        if category == "All Categories":
            category = None
        tag = self.tag_combo.currentText()
        if tag == "All Tags":
            tag = None
        min_rating = self.rating_spin.value()

        # Get sort options
        sort_map = {
            "Name": "name",
            "Rating": "rating",
            "Date Added": "created_at",
            "Last Accessed": "accessed_at"
        }
        sort_by = sort_map[self.sort_combo.currentText()]
        ascending = not self.sort_order_btn.isChecked()

        # Update sort button
        self.sort_order_btn.setText("↑" if ascending else "↓")

        # Get favorites
        if search_text:
            favorites = self.manager.search(search_text)
        else:
            favorites = self.manager.get_all(
                category=category,
                min_rating=min_rating,
                tags=[tag] if tag else None,
                sort_by=sort_by,
                ascending=ascending
            )

        # Update list
        self.favorites_list.clear()
        for favorite in favorites:
            # Check if file still exists
            if not Path(favorite.path).exists():
                continue

            item = FavoriteItem(favorite)
            self.favorites_list.addItem(item)

        # Update button states
        self.open_btn.setEnabled(False)
        self.edit_btn.setEnabled(False)
        self.remove_btn.setEnabled(False)

    def _on_item_clicked(self, item: FavoriteItem):
        """Handle item selection."""
        self.open_btn.setEnabled(True)
        self.edit_btn.setEnabled(True)
        self.remove_btn.setEnabled(True)
        self.favorite_selected.emit(item.favorite)

    def _on_item_double_clicked(self, item: FavoriteItem):
        """Handle double-click to open favorite."""
        self._on_open_favorite()

    def _show_context_menu(self, pos):
        """Show context menu."""
        item = self.favorites_list.itemAt(pos)
        if not isinstance(item, FavoriteItem):
            return

        menu = QMenu(self)

        # Open
        open_action = menu.addAction("Open")
        open_action.triggered.connect(self._on_open_favorite)

        # Edit
        edit_action = menu.addAction("Edit Details...")
        edit_action.triggered.connect(self._on_edit_favorite)

        menu.addSeparator()

        # Quick rating
        rating_menu = menu.addMenu("Set Rating")
        for i in range(6):
            stars = "★" * i + "☆" * (5 - i) if i > 0 else "No Rating"
            action = rating_menu.addAction(f"{stars} ({i})")
            action.triggered.connect(lambda checked, r=i: self._set_rating(item, r))

        menu.addSeparator()

        # Remove
        remove_action = menu.addAction("Remove from Favorites")
        remove_action.triggered.connect(self._on_remove_favorite)

        menu.exec(QCursor.pos())

    def _on_open_favorite(self):
        """Open selected favorite."""
        item = self.favorites_list.currentItem()
        if not isinstance(item, FavoriteItem):
            return

        # Update access stats
        self.manager.update_access(item.favorite.id)

        # Emit signal to open
        self.favorite_opened.emit(item.favorite.path)

    def _on_edit_favorite(self):
        """Edit favorite details."""
        item = self.favorites_list.currentItem()
        if not isinstance(item, FavoriteItem):
            return

        dialog = FavoriteDetailsDialog(item.favorite, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated = dialog.get_favorite()
            self.manager.save(updated)
            self._load_favorites()

    def _on_remove_favorite(self):
        """Remove favorite."""
        item = self.favorites_list.currentItem()
        if not isinstance(item, FavoriteItem):
            return

        reply = QMessageBox.question(
            self,
            "Remove Favorite",
            f"Remove '{item.favorite.name}' from favorites?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.manager.delete(item.favorite.id)
            self._load_favorites()

    def _set_rating(self, item: FavoriteItem, rating: int):
        """Set rating for favorite."""
        self.manager.update_rating(item.favorite.id, rating)
        item.favorite.rating = rating
        item.update_display()

    def add_favorite(self, path: str, **kwargs):
        """Add path to favorites."""
        if self.manager.is_favorite(path):
            QMessageBox.information(
                self,
                "Already Favorited",
                f"'{Path(path).name}' is already in favorites."
            )
            return

        self.manager.add(path, **kwargs)
        self._load_favorites()

    def remove_favorite(self, path: str):
        """Remove path from favorites."""
        self.manager.delete_by_path(path)
        self._load_favorites()

    def is_favorite(self, path: str) -> bool:
        """Check if path is favorited."""
        return self.manager.is_favorite(path)

    def refresh(self):
        """Refresh the list."""
        self._load_favorites()
