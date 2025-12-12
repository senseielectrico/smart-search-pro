"""
Smart collection editor with visual rule builder.

Provides a visual interface for creating and editing smart collections
with drag-and-drop rule building and live preview.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QTextEdit, QComboBox, QPushButton, QDialogButtonBox, QLabel,
    QSpinBox, QCheckBox, QListWidget, QGroupBox, QWidget,
    QScrollArea, QFrame, QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

import sys
if 'search' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent / 'search'))

from smart_collections import (
    SmartCollection, SmartCollectionsManager,
    Condition, ConditionType, LogicOperator
)


class ConditionWidget(QWidget):
    """Widget for editing a single condition."""

    remove_requested = pyqtSignal(object)  # Self

    def __init__(self, condition: Optional[Condition] = None, parent=None):
        super().__init__(parent)
        self.condition = condition or Condition(
            type=ConditionType.NAME_CONTAINS,
            value=""
        )
        self._init_ui()
        self._load_condition()

    def _init_ui(self):
        """Initialize UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Frame for visual grouping
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        frame_layout = QHBoxLayout(frame)

        # Logic operator (AND/OR)
        self.operator_combo = QComboBox()
        self.operator_combo.addItems(["AND", "OR"])
        frame_layout.addWidget(self.operator_combo)

        # Condition type
        self.type_combo = QComboBox()
        for cond_type in ConditionType:
            display_name = cond_type.value.replace("_", " ").title()
            self.type_combo.addItem(display_name, cond_type)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        frame_layout.addWidget(self.type_combo)

        # Value input (changes based on condition type)
        self.value_widget = QWidget()
        self.value_layout = QHBoxLayout(self.value_widget)
        self.value_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.addWidget(self.value_widget)

        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(25, 25)
        remove_btn.setToolTip("Remove condition")
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        frame_layout.addWidget(remove_btn)

        layout.addWidget(frame)

    def _load_condition(self):
        """Load condition into widgets."""
        # Set operator
        idx = self.operator_combo.findText(self.condition.operator.value)
        if idx >= 0:
            self.operator_combo.setCurrentIndex(idx)

        # Set type
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == self.condition.type:
                self.type_combo.setCurrentIndex(i)
                break

        # Set value
        self._on_type_changed()

    def _on_type_changed(self):
        """Handle condition type change."""
        # Clear existing value widgets
        while self.value_layout.count():
            child = self.value_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        cond_type = self.type_combo.currentData()

        # Create appropriate input widget based on condition type
        if cond_type in [
            ConditionType.NAME_CONTAINS, ConditionType.NAME_STARTS_WITH,
            ConditionType.NAME_ENDS_WITH, ConditionType.NAME_MATCHES,
            ConditionType.PATH_CONTAINS, ConditionType.EXTENSION_IS
        ]:
            # Single text input
            self.value_input = QLineEdit()
            self.value_input.setPlaceholderText("Enter value...")
            if isinstance(self.condition.value, str):
                self.value_input.setText(self.condition.value)
            self.value_layout.addWidget(self.value_input)

        elif cond_type == ConditionType.EXTENSION_IN:
            # Multiple extensions
            self.value_input = QLineEdit()
            self.value_input.setPlaceholderText("Comma-separated extensions (e.g., jpg, png, gif)")
            if isinstance(self.condition.value, list):
                self.value_input.setText(", ".join(self.condition.value))
            self.value_layout.addWidget(self.value_input)

        elif cond_type in [ConditionType.SIZE_GREATER, ConditionType.SIZE_LESS]:
            # Size in MB
            self.value_input = QSpinBox()
            self.value_input.setRange(0, 1000000)
            self.value_input.setSuffix(" MB")
            if isinstance(self.condition.value, (int, float)):
                self.value_input.setValue(int(self.condition.value / (1024 * 1024)))
            self.value_layout.addWidget(self.value_input)

        elif cond_type == ConditionType.SIZE_BETWEEN:
            # Size range
            self.value_input = QWidget()
            range_layout = QHBoxLayout(self.value_input)
            range_layout.setContentsMargins(0, 0, 0, 0)

            self.min_size = QSpinBox()
            self.min_size.setRange(0, 1000000)
            self.min_size.setSuffix(" MB")
            range_layout.addWidget(self.min_size)

            range_layout.addWidget(QLabel("to"))

            self.max_size = QSpinBox()
            self.max_size.setRange(0, 1000000)
            self.max_size.setSuffix(" MB")
            range_layout.addWidget(self.max_size)

            if isinstance(self.condition.value, list) and len(self.condition.value) == 2:
                self.min_size.setValue(int(self.condition.value[0] / (1024 * 1024)))
                self.max_size.setValue(int(self.condition.value[1] / (1024 * 1024)))

            self.value_layout.addWidget(self.value_input)

        elif cond_type == ConditionType.MODIFIED_WITHIN:
            # Days
            self.value_input = QSpinBox()
            self.value_input.setRange(1, 365)
            self.value_input.setSuffix(" days")
            if isinstance(self.condition.value, (int, float)):
                self.value_input.setValue(int(self.condition.value))
            self.value_layout.addWidget(self.value_input)

        elif cond_type in [ConditionType.IS_DIRECTORY, ConditionType.IS_FILE]:
            # Boolean (no value needed)
            label = QLabel("(No value required)")
            label.setStyleSheet("color: gray; font-style: italic;")
            self.value_layout.addWidget(label)

        else:
            # Default text input
            self.value_input = QLineEdit()
            self.value_layout.addWidget(self.value_input)

    def get_condition(self) -> Condition:
        """Get condition from widget."""
        cond_type = self.type_combo.currentData()
        operator = LogicOperator(self.operator_combo.currentText())

        # Get value based on type
        value = None

        if cond_type in [
            ConditionType.NAME_CONTAINS, ConditionType.NAME_STARTS_WITH,
            ConditionType.NAME_ENDS_WITH, ConditionType.NAME_MATCHES,
            ConditionType.PATH_CONTAINS, ConditionType.EXTENSION_IS
        ]:
            value = self.value_input.text().strip()

        elif cond_type == ConditionType.EXTENSION_IN:
            text = self.value_input.text().strip()
            value = [ext.strip() for ext in text.split(",") if ext.strip()]

        elif cond_type in [ConditionType.SIZE_GREATER, ConditionType.SIZE_LESS]:
            value = self.value_input.value() * 1024 * 1024  # Convert MB to bytes

        elif cond_type == ConditionType.SIZE_BETWEEN:
            value = [
                self.min_size.value() * 1024 * 1024,
                self.max_size.value() * 1024 * 1024
            ]

        elif cond_type == ConditionType.MODIFIED_WITHIN:
            value = self.value_input.value()

        elif cond_type in [ConditionType.IS_DIRECTORY, ConditionType.IS_FILE]:
            value = True

        return Condition(type=cond_type, value=value, operator=operator)


class CollectionEditor(QDialog):
    """
    Smart collection editor dialog.

    Features:
    - Visual rule builder
    - Add/remove conditions
    - AND/OR logic
    - Preview matching files (when integrated with search)
    """

    def __init__(self, collection: Optional[SmartCollection] = None, parent=None):
        super().__init__(parent)
        self.collection = collection or SmartCollection()
        self.manager = SmartCollectionsManager()
        self.condition_widgets: List[ConditionWidget] = []

        self.setWindowTitle(
            "New Collection" if not collection else f"Edit Collection - {collection.name}"
        )
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self._init_ui()
        self._load_collection()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)

        # Basic info
        basic_group = QGroupBox("Collection Information")
        basic_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter collection name...")
        basic_layout.addRow("Name:", self.name_input)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Optional description...")
        self.description_input.setMaximumHeight(60)
        basic_layout.addRow("Description:", self.description_input)

        # Icon and color (simplified)
        visual_layout = QHBoxLayout()
        self.icon_input = QComboBox()
        self.icon_input.addItems([
            "folder", "star", "document", "image", "video",
            "music", "code", "archive", "calendar", "storage"
        ])
        visual_layout.addWidget(QLabel("Icon:"))
        visual_layout.addWidget(self.icon_input)
        visual_layout.addStretch()

        basic_layout.addRow("Visual:", visual_layout)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Rules
        rules_group = QGroupBox("Rules")
        rules_layout = QVBoxLayout()

        # Match mode
        match_layout = QHBoxLayout()
        match_layout.addWidget(QLabel("Match:"))
        self.match_mode = QComboBox()
        self.match_mode.addItems(["All conditions (AND)", "Any condition (OR)"])
        match_layout.addWidget(self.match_mode)
        match_layout.addStretch()
        rules_layout.addLayout(match_layout)

        # Conditions list (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(200)

        self.conditions_container = QWidget()
        self.conditions_layout = QVBoxLayout(self.conditions_container)
        self.conditions_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.conditions_container)
        rules_layout.addWidget(scroll)

        # Add condition button
        add_btn = QPushButton("+ Add Condition")
        add_btn.clicked.connect(self._add_condition)
        rules_layout.addWidget(add_btn)

        rules_group.setLayout(rules_layout)
        layout.addWidget(rules_group)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QFormLayout()

        self.max_results = QSpinBox()
        self.max_results.setRange(10, 10000)
        self.max_results.setValue(1000)
        self.max_results.setSingleStep(100)
        options_layout.addRow("Max Results:", self.max_results)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["name", "size", "modified", "created"])
        options_layout.addRow("Sort By:", self.sort_combo)

        self.ascending_check = QCheckBox("Ascending order")
        self.ascending_check.setChecked(True)
        options_layout.addRow("", self.ascending_check)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_collection(self):
        """Load collection into form."""
        if not self.collection:
            return

        self.name_input.setText(self.collection.name)
        self.description_input.setPlainText(self.collection.description)

        # Icon
        idx = self.icon_input.findText(self.collection.icon)
        if idx >= 0:
            self.icon_input.setCurrentIndex(idx)

        # Match mode
        self.match_mode.setCurrentIndex(0 if self.collection.match_all else 1)

        # Load conditions
        for condition in self.collection.conditions:
            self._add_condition(condition)

        # Options
        self.max_results.setValue(self.collection.max_results)

        idx = self.sort_combo.findText(self.collection.sort_by)
        if idx >= 0:
            self.sort_combo.setCurrentIndex(idx)

        self.ascending_check.setChecked(self.collection.ascending)

    def _add_condition(self, condition: Optional[Condition] = None):
        """Add a condition widget."""
        widget = ConditionWidget(condition, self)
        widget.remove_requested.connect(self._remove_condition)

        # Hide operator for first condition
        if len(self.condition_widgets) == 0:
            widget.operator_combo.setVisible(False)

        self.condition_widgets.append(widget)
        self.conditions_layout.addWidget(widget)

    def _remove_condition(self, widget: ConditionWidget):
        """Remove a condition widget."""
        if widget in self.condition_widgets:
            self.condition_widgets.remove(widget)
            self.conditions_layout.removeWidget(widget)
            widget.deleteLater()

            # Show/hide operator for first condition
            if self.condition_widgets:
                self.condition_widgets[0].operator_combo.setVisible(False)

    def _on_save(self):
        """Validate and save collection."""
        # Validate name
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                "Invalid Name",
                "Please enter a collection name."
            )
            return

        # Get conditions
        conditions = []
        for widget in self.condition_widgets:
            try:
                cond = widget.get_condition()
                conditions.append(cond)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Invalid Condition",
                    f"Invalid condition: {e}"
                )
                return

        if not conditions:
            reply = QMessageBox.question(
                self,
                "No Conditions",
                "Collection has no conditions. It will match all files. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # Check if name exists (for new collections)
        if not self.collection.id:
            existing = self.manager.get_by_name(name)
            if existing:
                reply = QMessageBox.question(
                    self,
                    "Name Exists",
                    f"A collection named '{name}' already exists. Overwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.collection.id = existing.id
                else:
                    return

        # Update collection
        self.collection.name = name
        self.collection.description = self.description_input.toPlainText().strip()
        self.collection.icon = self.icon_input.currentText()
        self.collection.conditions = conditions
        self.collection.match_all = (self.match_mode.currentIndex() == 0)
        self.collection.max_results = self.max_results.value()
        self.collection.sort_by = self.sort_combo.currentText()
        self.collection.ascending = self.ascending_check.isChecked()

        # Save
        try:
            collection_id = self.manager.save(self.collection)
            self.collection.id = collection_id
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save collection: {e}"
            )

    def get_collection(self) -> SmartCollection:
        """Get the collection."""
        return self.collection
