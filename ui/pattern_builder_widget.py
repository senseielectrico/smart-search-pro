"""
Pattern Builder Widget - Visual pattern builder with drag & drop elements
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QGroupBox, QGridLayout, QToolButton,
    QComboBox, QSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from operations.batch_renamer import RenamePattern, CaseMode


class PatternBuilderWidget(QWidget):
    """
    Visual pattern builder for file renaming

    Features:
    - Placeholder buttons that insert into pattern
    - Live pattern editing
    - Format preview
    - Pattern validation
    """

    pattern_changed = pyqtSignal(RenamePattern)

    # Placeholder definitions with tooltips
    PLACEHOLDERS = {
        'Basic': [
            ('{name}', 'Original filename without extension'),
            ('{ext}', 'File extension (without dot)'),
            ('{parent}', 'Parent folder name'),
        ],
        'Numbers': [
            ('{num}', 'Sequential number (001, 002, ...)'),
        ],
        'Dates': [
            ('{date}', 'File modification date'),
            ('{created}', 'File creation date'),
            ('{exif_date}', 'EXIF date from photos'),
        ],
        'File Info': [
            ('{size}', 'File size in bytes'),
            ('{sizekb}', 'File size in KB'),
            ('{sizemb}', 'File size in MB'),
            ('{hash}', 'Short file hash (8 chars)'),
            ('{hash16}', 'Medium file hash (16 chars)'),
        ],
        'Image': [
            ('{width}', 'Image width in pixels'),
            ('{height}', 'Image height in pixels'),
            ('{exif_datetime}', 'EXIF date and time'),
        ],
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pattern = RenamePattern()
        self._init_ui()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Pattern input
        pattern_group = QGroupBox("Rename Pattern")
        pattern_layout = QVBoxLayout(pattern_group)

        # Pattern edit with toolbar
        edit_layout = QHBoxLayout()

        self.pattern_edit = QLineEdit()
        self.pattern_edit.setPlaceholderText("Enter pattern or use buttons below")
        self.pattern_edit.setText("{name}")
        self.pattern_edit.textChanged.connect(self._on_pattern_text_changed)
        edit_layout.addWidget(self.pattern_edit)

        # Clear button
        clear_btn = QToolButton()
        clear_btn.setText("×")
        clear_btn.setToolTip("Clear pattern")
        clear_btn.clicked.connect(lambda: self.pattern_edit.clear())
        edit_layout.addWidget(clear_btn)

        pattern_layout.addLayout(edit_layout)

        # Placeholder buttons
        placeholders_label = QLabel("Insert Placeholder:")
        placeholders_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        pattern_layout.addWidget(placeholders_label)

        # Create button grid for placeholders
        for category, placeholders in self.PLACEHOLDERS.items():
            category_label = QLabel(category + ":")
            category_label.setStyleSheet("color: #666; font-size: 9pt;")
            pattern_layout.addWidget(category_label)

            buttons_layout = QHBoxLayout()
            buttons_layout.setSpacing(4)

            for placeholder, tooltip in placeholders:
                btn = QPushButton(placeholder)
                btn.setToolTip(tooltip)
                btn.setMaximumWidth(120)
                btn.clicked.connect(lambda checked, p=placeholder: self._insert_placeholder(p))
                buttons_layout.addWidget(btn)

            buttons_layout.addStretch()
            pattern_layout.addLayout(buttons_layout)

        layout.addWidget(pattern_group)

        # Additional options
        options_group = QGroupBox("Options")
        options_layout = QGridLayout(options_group)
        row = 0

        # Date format
        options_layout.addWidget(QLabel("Date Format:"), row, 0)
        self.date_format_combo = QComboBox()
        self.date_format_combo.addItem("YYYYMMDD", "%Y%m%d")
        self.date_format_combo.addItem("YYYY-MM-DD", "%Y-%m-%d")
        self.date_format_combo.addItem("YYYY_MM_DD", "%Y_%m_%d")
        self.date_format_combo.addItem("DD-MM-YYYY", "%d-%m-%Y")
        self.date_format_combo.addItem("MM-DD-YYYY", "%m-%d-%Y")
        self.date_format_combo.currentIndexChanged.connect(self._on_options_changed)
        options_layout.addWidget(self.date_format_combo, row, 1)
        row += 1

        # Number padding
        options_layout.addWidget(QLabel("Number Padding:"), row, 0)
        self.padding_spin = QSpinBox()
        self.padding_spin.setMinimum(1)
        self.padding_spin.setMaximum(10)
        self.padding_spin.setValue(3)
        self.padding_spin.setToolTip("Number of digits for {num} (e.g., 001, 002)")
        self.padding_spin.valueChanged.connect(self._on_options_changed)
        options_layout.addWidget(self.padding_spin, row, 1)
        row += 1

        # Start number
        options_layout.addWidget(QLabel("Start Number:"), row, 0)
        self.start_number_spin = QSpinBox()
        self.start_number_spin.setMinimum(0)
        self.start_number_spin.setMaximum(99999)
        self.start_number_spin.setValue(1)
        self.start_number_spin.valueChanged.connect(self._on_options_changed)
        options_layout.addWidget(self.start_number_spin, row, 1)
        row += 1

        layout.addWidget(options_group)

        # Pattern examples
        examples_group = QGroupBox("Pattern Examples")
        examples_layout = QVBoxLayout(examples_group)

        examples_text = QTextEdit()
        examples_text.setReadOnly(True)
        examples_text.setMaximumHeight(120)
        examples_text.setStyleSheet("background: #f5f5f5; font-family: monospace;")

        examples = """
{name}                  → Keep original name
{date}_{name}          → 20231215_photo
IMG_{num}              → IMG_001, IMG_002, IMG_003
{parent}_{name}_{num}  → FolderName_file_001
{date}_{hash}          → 20231215_a1b2c3d4
{exif_date}_{num}      → 20231215_001 (from photo metadata)
        """.strip()

        examples_text.setPlainText(examples)
        examples_layout.addWidget(examples_text)

        layout.addWidget(examples_group)

        # Regex helper
        regex_group = QGroupBox("Regular Expression (Advanced)")
        regex_layout = QVBoxLayout(regex_group)

        regex_help = QLabel(
            "Use regex in Find & Replace tab.\n"
            "Capture groups: Use $1, $2, etc. in pattern.\n"
            "Example: Find '(\\d+)_(\\w+)' → Pattern '{$2}_{$1}'"
        )
        regex_help.setWordWrap(True)
        regex_help.setStyleSheet("color: #666; font-size: 9pt;")
        regex_layout.addWidget(regex_help)

        layout.addWidget(regex_group)

        layout.addStretch()

    def _insert_placeholder(self, placeholder: str):
        """Insert placeholder at cursor position"""
        current_text = self.pattern_edit.text()
        cursor_pos = self.pattern_edit.cursorPosition()

        new_text = current_text[:cursor_pos] + placeholder + current_text[cursor_pos:]
        self.pattern_edit.setText(new_text)
        self.pattern_edit.setCursorPosition(cursor_pos + len(placeholder))
        self.pattern_edit.setFocus()

    def _on_pattern_text_changed(self):
        """Handle pattern text change"""
        self._update_pattern()

    def _on_options_changed(self):
        """Handle option changes"""
        self._update_pattern()

    def _update_pattern(self):
        """Update current pattern and emit signal"""
        self.current_pattern.pattern = self.pattern_edit.text()
        self.current_pattern.date_format = self.date_format_combo.currentData()
        self.current_pattern.number_padding = self.padding_spin.value()
        self.current_pattern.start_number = self.start_number_spin.value()

        self.pattern_changed.emit(self.current_pattern)

    def set_pattern(self, pattern: RenamePattern):
        """Set pattern programmatically"""
        self.current_pattern = pattern

        # Block signals to prevent loops
        self.pattern_edit.blockSignals(True)
        self.date_format_combo.blockSignals(True)
        self.padding_spin.blockSignals(True)
        self.start_number_spin.blockSignals(True)

        self.pattern_edit.setText(pattern.pattern)

        # Set date format
        index = self.date_format_combo.findData(pattern.date_format)
        if index >= 0:
            self.date_format_combo.setCurrentIndex(index)

        self.padding_spin.setValue(pattern.number_padding)
        self.start_number_spin.setValue(pattern.start_number)

        # Unblock signals
        self.pattern_edit.blockSignals(False)
        self.date_format_combo.blockSignals(False)
        self.padding_spin.blockSignals(False)
        self.start_number_spin.blockSignals(False)

    def get_pattern(self) -> RenamePattern:
        """Get current pattern"""
        return self.current_pattern

    def validate_pattern(self) -> tuple[bool, str]:
        """
        Validate current pattern

        Returns:
            (is_valid, error_message)
        """
        pattern = self.pattern_edit.text()

        if not pattern:
            return False, "Pattern cannot be empty"

        # Check for balanced braces
        if pattern.count('{') != pattern.count('}'):
            return False, "Unbalanced braces in pattern"

        # Check for unknown placeholders
        import re
        placeholders = re.findall(r'\{(\w+)\}', pattern)
        all_valid_placeholders = set()
        for category_placeholders in self.PLACEHOLDERS.values():
            for ph, _ in category_placeholders:
                placeholder_name = ph[1:-1]  # Remove {}
                all_valid_placeholders.add(placeholder_name)

        for ph in placeholders:
            if ph not in all_valid_placeholders:
                return False, f"Unknown placeholder: {{{ph}}}"

        return True, ""
