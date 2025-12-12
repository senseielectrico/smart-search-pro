"""
MIME filter widget for search UI.

Features:
- Dropdown with MIME categories
- Multi-select MIME types
- Custom MIME type input
- Show detected vs extension mismatch
- Quick filters
- Integration with main search panel
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QListWidget,
    QLineEdit, QPushButton, QLabel, QGroupBox, QCheckBox,
    QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from search.mime_database import MimeCategory, get_mime_database
from search.mime_filter import (
    MimeFilterCriteria, expand_category_shortcut,
    get_category_shortcuts
)


class MimeFilterWidget(QWidget):
    """
    Widget for MIME type filtering.

    Signals:
        filter_changed: Emitted when filter criteria changes
    """

    filter_changed = pyqtSignal(object)  # MimeFilterCriteria or None

    def __init__(self, parent=None):
        """Initialize MIME filter widget."""
        super().__init__(parent)
        self.mime_db = get_mime_database()
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Quick filters section
        quick_group = QGroupBox("Quick Filters")
        quick_layout = QHBoxLayout(quick_group)

        self.quick_buttons = {}
        shortcuts = {
            "All": None,
            "Images": "image/*",
            "Videos": "video/*",
            "Audio": "audio/*",
            "Documents": "documents",
            "Archives": "archives",
        }

        for name, filter_value in shortcuts.items():
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, v=filter_value: self._on_quick_filter(v))
            quick_layout.addWidget(btn)
            self.quick_buttons[name] = btn

        # "All" selected by default
        self.quick_buttons["All"].setChecked(True)

        layout.addWidget(quick_group)

        # Category filter section
        category_group = QGroupBox("Filter by Category")
        category_layout = QVBoxLayout(category_group)

        # Category combo box
        cat_select_layout = QHBoxLayout()
        cat_select_layout.addWidget(QLabel("Category:"))

        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories", None)
        for category in MimeCategory:
            if category != MimeCategory.UNKNOWN:
                self.category_combo.addItem(
                    category.value.title(),
                    category
                )
        cat_select_layout.addWidget(self.category_combo, 1)

        category_layout.addLayout(cat_select_layout)
        layout.addWidget(category_group)

        # MIME type filter section
        mime_group = QGroupBox("Filter by MIME Type")
        mime_layout = QVBoxLayout(mime_group)

        # MIME type list
        mime_layout.addWidget(QLabel("Select MIME types:"))

        self.mime_list = QListWidget()
        self.mime_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.mime_list.setMaximumHeight(150)
        self._populate_mime_list()
        mime_layout.addWidget(self.mime_list)

        # Custom MIME type input
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("Custom:"))

        self.custom_mime_input = QLineEdit()
        self.custom_mime_input.setPlaceholderText("e.g., image/*, application/pdf")
        custom_layout.addWidget(self.custom_mime_input, 1)

        add_custom_btn = QPushButton("Add")
        add_custom_btn.clicked.connect(self._add_custom_mime)
        custom_layout.addWidget(add_custom_btn)

        mime_layout.addLayout(custom_layout)
        layout.addWidget(mime_group)

        # Advanced options section
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QVBoxLayout(advanced_group)

        self.exclude_mismatched_cb = QCheckBox("Exclude files with extension mismatch")
        self.exclude_mismatched_cb.setToolTip(
            "Filter out files where extension doesn't match detected MIME type\n"
            "(e.g., .exe renamed to .jpg)"
        )
        advanced_layout.addWidget(self.exclude_mismatched_cb)

        self.exclude_dangerous_cb = QCheckBox("Exclude potentially dangerous files")
        self.exclude_dangerous_cb.setToolTip(
            "Filter out executables and other potentially dangerous file types"
        )
        advanced_layout.addWidget(self.exclude_dangerous_cb)

        # Confidence threshold
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(QLabel("Min confidence:"))

        self.confidence_combo = QComboBox()
        self.confidence_combo.addItem("Any (0%)", 0.0)
        self.confidence_combo.addItem("Low (50%)", 0.5)
        self.confidence_combo.addItem("Medium (70%)", 0.7)
        self.confidence_combo.addItem("High (85%)", 0.85)
        self.confidence_combo.addItem("Very High (95%)", 0.95)
        conf_layout.addWidget(self.confidence_combo, 1)

        advanced_layout.addLayout(conf_layout)
        layout.addWidget(advanced_group)

        # Action buttons
        button_layout = QHBoxLayout()

        self.apply_btn = QPushButton("Apply Filter")
        self.apply_btn.clicked.connect(self._apply_filter)
        button_layout.addWidget(self.apply_btn)

        self.clear_btn = QPushButton("Clear Filter")
        self.clear_btn.clicked.connect(self._clear_filter)
        button_layout.addWidget(self.clear_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel("No MIME filter applied")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.status_label)

        layout.addStretch()

    def _connect_signals(self):
        """Connect widget signals."""
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        self.mime_list.itemSelectionChanged.connect(self._on_mime_selection_changed)
        self.exclude_mismatched_cb.stateChanged.connect(self._on_option_changed)
        self.exclude_dangerous_cb.stateChanged.connect(self._on_option_changed)
        self.confidence_combo.currentIndexChanged.connect(self._on_option_changed)

    def _populate_mime_list(self, category_filter: MimeCategory = None):
        """Populate MIME type list."""
        self.mime_list.clear()

        if category_filter:
            mime_types = self.mime_db.get_mime_types_by_category(category_filter)
        else:
            mime_types = self.mime_db.get_all_mime_types()

        for mime_type in sorted(mime_types):
            description = self.mime_db.get_description(mime_type)
            item = QListWidgetItem(f"{mime_type} - {description}")
            item.setData(Qt.ItemDataRole.UserRole, mime_type)
            self.mime_list.addItem(item)

    def _on_quick_filter(self, filter_value):
        """Handle quick filter button click."""
        # Uncheck other quick filter buttons
        sender = self.sender()
        for btn in self.quick_buttons.values():
            if btn != sender:
                btn.setChecked(False)

        if filter_value is None:
            # "All" button - clear all filters
            self._clear_filter()
        else:
            # Apply quick filter
            if filter_value in get_category_shortcuts():
                # It's a category shortcut
                patterns = expand_category_shortcut(filter_value)
            else:
                # It's a MIME pattern
                patterns = [filter_value]

            criteria = MimeFilterCriteria(
                mime_patterns=patterns,
                categories=set(),
                exclude_mismatched=False,
                exclude_dangerous=False,
                min_confidence=0.0
            )

            self._update_status(f"Quick filter: {sender.text()}")
            self.filter_changed.emit(criteria)

    def _on_category_changed(self, index):
        """Handle category combo box change."""
        category = self.category_combo.currentData()
        self._populate_mime_list(category)

    def _on_mime_selection_changed(self):
        """Handle MIME type selection change."""
        # Auto-uncheck quick filter buttons
        for btn in self.quick_buttons.values():
            btn.setChecked(False)

    def _on_option_changed(self):
        """Handle advanced option change."""
        # Auto-uncheck quick filter buttons
        for btn in self.quick_buttons.values():
            btn.setChecked(False)

    def _add_custom_mime(self):
        """Add custom MIME type pattern."""
        custom_mime = self.custom_mime_input.text().strip()
        if not custom_mime:
            return

        # Validate pattern
        if not self._is_valid_mime_pattern(custom_mime):
            QMessageBox.warning(
                self,
                "Invalid Pattern",
                f"'{custom_mime}' is not a valid MIME type pattern.\n\n"
                "Examples:\n"
                "- image/png (exact)\n"
                "- image/* (wildcard)\n"
                "- image (category)"
            )
            return

        # Add to list
        item = QListWidgetItem(f"{custom_mime} (custom)")
        item.setData(Qt.ItemDataRole.UserRole, custom_mime)
        item.setBackground(QColor(240, 248, 255))  # Light blue
        self.mime_list.addItem(item)
        item.setSelected(True)

        # Clear input
        self.custom_mime_input.clear()

        # Auto-uncheck quick filters
        for btn in self.quick_buttons.values():
            btn.setChecked(False)

    def _is_valid_mime_pattern(self, pattern: str) -> bool:
        """Validate MIME type pattern."""
        if not pattern:
            return False

        # Allow wildcards
        if pattern in ("*", "*/*"):
            return True

        # Allow category only (e.g., "image")
        if "/" not in pattern and pattern.isalpha():
            return True

        # Allow category/* (e.g., "image/*")
        if pattern.endswith("/*"):
            category = pattern[:-2]
            return category.isalpha()

        # Allow full MIME type (category/subtype)
        if "/" in pattern:
            parts = pattern.split("/")
            if len(parts) == 2:
                return all(part.replace("-", "").replace("+", "").replace(".", "").isalnum()
                          for part in parts)

        return False

    def _apply_filter(self):
        """Apply current filter settings."""
        criteria = self.get_filter_criteria()

        if criteria is None:
            QMessageBox.information(
                self,
                "No Filter",
                "No filter criteria specified.\n\n"
                "Please select categories, MIME types, or enable advanced options."
            )
            return

        # Update status
        status_parts = []
        if criteria.mime_patterns:
            status_parts.append(f"{len(criteria.mime_patterns)} MIME pattern(s)")
        if criteria.categories:
            status_parts.append(f"{len(criteria.categories)} category(s)")
        if criteria.exclude_mismatched:
            status_parts.append("verified only")
        if criteria.exclude_dangerous:
            status_parts.append("safe only")

        status = "Filter: " + ", ".join(status_parts)
        self._update_status(status)

        # Emit signal
        self.filter_changed.emit(criteria)

    def _clear_filter(self):
        """Clear all filter settings."""
        # Clear category
        self.category_combo.setCurrentIndex(0)

        # Clear MIME list selection
        self.mime_list.clearSelection()

        # Clear custom input
        self.custom_mime_input.clear()

        # Clear checkboxes
        self.exclude_mismatched_cb.setChecked(False)
        self.exclude_dangerous_cb.setChecked(False)

        # Reset confidence
        self.confidence_combo.setCurrentIndex(0)

        # Check "All" quick filter
        self.quick_buttons["All"].setChecked(True)
        for name, btn in self.quick_buttons.items():
            if name != "All":
                btn.setChecked(False)

        # Update status
        self._update_status("No MIME filter applied")

        # Emit signal
        self.filter_changed.emit(None)

    def _update_status(self, message: str):
        """Update status label."""
        self.status_label.setText(message)

    def get_filter_criteria(self) -> MimeFilterCriteria:
        """
        Get current filter criteria.

        Returns:
            MimeFilterCriteria or None if no filters active
        """
        mime_patterns = []
        categories = set()

        # Get selected MIME types
        for item in self.mime_list.selectedItems():
            mime_type = item.data(Qt.ItemDataRole.UserRole)
            mime_patterns.append(mime_type)

        # Get selected category
        category = self.category_combo.currentData()
        if category:
            categories.add(category)

        # Get advanced options
        exclude_mismatched = self.exclude_mismatched_cb.isChecked()
        exclude_dangerous = self.exclude_dangerous_cb.isChecked()
        min_confidence = self.confidence_combo.currentData()

        # Return None if no filters
        if not mime_patterns and not categories and not exclude_mismatched and not exclude_dangerous:
            return None

        return MimeFilterCriteria(
            mime_patterns=mime_patterns,
            categories=categories,
            exclude_mismatched=exclude_mismatched,
            exclude_dangerous=exclude_dangerous,
            min_confidence=min_confidence
        )

    def set_filter_criteria(self, criteria: MimeFilterCriteria):
        """
        Set filter criteria programmatically.

        Args:
            criteria: Filter criteria to apply
        """
        if criteria is None:
            self._clear_filter()
            return

        # Clear current selection
        self.mime_list.clearSelection()
        self.quick_buttons["All"].setChecked(False)

        # Set MIME patterns
        if criteria.mime_patterns:
            for i in range(self.mime_list.count()):
                item = self.mime_list.item(i)
                mime_type = item.data(Qt.ItemDataRole.UserRole)
                if mime_type in criteria.mime_patterns:
                    item.setSelected(True)

        # Set categories
        if criteria.categories:
            # Set first category in combo box
            category = next(iter(criteria.categories))
            for i in range(self.category_combo.count()):
                if self.category_combo.itemData(i) == category:
                    self.category_combo.setCurrentIndex(i)
                    break

        # Set advanced options
        self.exclude_mismatched_cb.setChecked(criteria.exclude_mismatched)
        self.exclude_dangerous_cb.setChecked(criteria.exclude_dangerous)

        # Set confidence
        for i in range(self.confidence_combo.count()):
            if self.confidence_combo.itemData(i) == criteria.min_confidence:
                self.confidence_combo.setCurrentIndex(i)
                break


if __name__ == "__main__":
    """Test MIME filter widget."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    widget = MimeFilterWidget()
    widget.setWindowTitle("MIME Filter Test")
    widget.resize(400, 600)

    def on_filter_changed(criteria):
        if criteria:
            print(f"Filter changed:")
            print(f"  MIME patterns: {criteria.mime_patterns}")
            print(f"  Categories: {[c.value for c in criteria.categories]}")
            print(f"  Exclude mismatched: {criteria.exclude_mismatched}")
            print(f"  Exclude dangerous: {criteria.exclude_dangerous}")
            print(f"  Min confidence: {criteria.min_confidence}")
        else:
            print("Filter cleared")

    widget.filter_changed.connect(on_filter_changed)

    widget.show()
    sys.exit(app.exec())
