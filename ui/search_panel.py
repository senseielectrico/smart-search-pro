"""
Search Panel - Advanced search with filters and history
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QSpinBox, QDateEdit, QCheckBox, QGroupBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QSettings, QTimer
from PyQt6.QtGui import QIcon
from .widgets import FilterChip, SearchHistoryPopup
from .filter_integration import FilterIntegration


class AdvancedSearchDialog(QDialog):
    """Advanced search options dialog"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Search")
        self.setMinimumWidth(500)

        self._init_ui()
        self._load_defaults()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Scroll area for options
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # File Name group
        name_group = QGroupBox("File Name")
        name_layout = QFormLayout()

        self.pattern_edit = QLineEdit()
        self.pattern_edit.setPlaceholderText("*.txt, photo*, etc.")
        name_layout.addRow("Pattern:", self.pattern_edit)

        self.regex_check = QCheckBox("Use Regular Expression")
        name_layout.addRow(self.regex_check)

        self.case_sensitive_check = QCheckBox("Case Sensitive")
        name_layout.addRow(self.case_sensitive_check)

        name_group.setLayout(name_layout)
        scroll_layout.addWidget(name_group)

        # File Type group
        type_group = QGroupBox("File Type")
        type_layout = QFormLayout()

        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "All Files",
            "Documents",
            "Images",
            "Videos",
            "Audio",
            "Archives",
            "Code Files",
            "Executables"
        ])
        type_layout.addRow("Type:", self.type_combo)

        self.extension_edit = QLineEdit()
        self.extension_edit.setPlaceholderText(".txt, .pdf, .jpg")
        type_layout.addRow("Extensions:", self.extension_edit)

        type_group.setLayout(type_layout)
        scroll_layout.addWidget(type_group)

        # File Size group
        size_group = QGroupBox("File Size")
        size_layout = QFormLayout()

        self.size_mode_combo = QComboBox()
        self.size_mode_combo.addItems(["Any Size", "Exact", "Range", "At Least", "At Most"])
        self.size_mode_combo.currentTextChanged.connect(self._update_size_controls)
        size_layout.addRow("Mode:", self.size_mode_combo)

        # Size controls
        size_row1 = QHBoxLayout()
        self.min_size_spin = QSpinBox()
        self.min_size_spin.setRange(0, 999999)
        self.min_size_spin.setSuffix(" KB")
        size_row1.addWidget(self.min_size_spin)

        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(0, 999999)
        self.max_size_spin.setSuffix(" KB")
        size_row1.addWidget(QLabel("to"))
        size_row1.addWidget(self.max_size_spin)

        self.size_unit_combo = QComboBox()
        self.size_unit_combo.addItems(["KB", "MB", "GB"])
        size_row1.addWidget(self.size_unit_combo)

        size_layout.addRow("Size:", size_row1)

        size_group.setLayout(size_layout)
        scroll_layout.addWidget(size_group)

        # Date Modified group
        date_group = QGroupBox("Date Modified")
        date_layout = QFormLayout()

        self.date_mode_combo = QComboBox()
        self.date_mode_combo.addItems([
            "Any Date",
            "Today",
            "Yesterday",
            "This Week",
            "This Month",
            "This Year",
            "Custom Range"
        ])
        self.date_mode_combo.currentTextChanged.connect(self._update_date_controls)
        date_layout.addRow("Mode:", self.date_mode_combo)

        # Date range
        date_row = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        date_row.addWidget(self.start_date)

        date_row.addWidget(QLabel("to"))

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        date_row.addWidget(self.end_date)

        date_layout.addRow("Range:", date_row)

        date_group.setLayout(date_layout)
        scroll_layout.addWidget(date_group)

        # Content group
        content_group = QGroupBox("Content")
        content_layout = QFormLayout()

        self.content_search_edit = QLineEdit()
        self.content_search_edit.setPlaceholderText("Search inside files...")
        content_layout.addRow("Contains:", self.content_search_edit)

        self.content_regex_check = QCheckBox("Use Regular Expression")
        content_layout.addRow(self.content_regex_check)

        content_group.setLayout(content_layout)
        scroll_layout.addWidget(content_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Reset
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self._reset)

        layout.addWidget(button_box)

    def _update_size_controls(self, mode: str):
        """Update size control visibility"""
        if mode == "Any Size":
            self.min_size_spin.setEnabled(False)
            self.max_size_spin.setEnabled(False)
            self.size_unit_combo.setEnabled(False)
        elif mode == "Range":
            self.min_size_spin.setEnabled(True)
            self.max_size_spin.setEnabled(True)
            self.size_unit_combo.setEnabled(True)
        else:  # Exact, At Least, At Most
            self.min_size_spin.setEnabled(True)
            self.max_size_spin.setEnabled(False)
            self.size_unit_combo.setEnabled(True)

    def _update_date_controls(self, mode: str):
        """Update date control visibility"""
        enabled = mode == "Custom Range"
        self.start_date.setEnabled(enabled)
        self.end_date.setEnabled(enabled)

    def _load_defaults(self):
        """Load default values"""
        self._update_size_controls("Any Size")
        self._update_date_controls("Any Date")

    def _reset(self):
        """Reset to defaults"""
        self.pattern_edit.clear()
        self.regex_check.setChecked(False)
        self.case_sensitive_check.setChecked(False)
        self.type_combo.setCurrentIndex(0)
        self.extension_edit.clear()
        self.size_mode_combo.setCurrentIndex(0)
        self.date_mode_combo.setCurrentIndex(0)
        self.content_search_edit.clear()
        self.content_regex_check.setChecked(False)

    def get_search_params(self) -> Dict:
        """Get search parameters"""
        params = {
            'pattern': self.pattern_edit.text(),
            'regex': self.regex_check.isChecked(),
            'case_sensitive': self.case_sensitive_check.isChecked(),
            'file_type': self.type_combo.currentText(),
            'extensions': [ext.strip() for ext in self.extension_edit.text().split(',') if ext.strip()],
            'size_mode': self.size_mode_combo.currentText(),
            'min_size': self.min_size_spin.value() if self.min_size_spin.isEnabled() else None,
            'max_size': self.max_size_spin.value() if self.max_size_spin.isEnabled() else None,
            'size_unit': self.size_unit_combo.currentText(),
            'date_mode': self.date_mode_combo.currentText(),
            'start_date': self.start_date.date().toPyDate() if self.start_date.isEnabled() else None,
            'end_date': self.end_date.date().toPyDate() if self.end_date.isEnabled() else None,
            'content_search': self.content_search_edit.text(),
            'content_regex': self.content_regex_check.isChecked(),
        }
        return params


class SearchPanel(QWidget):
    """Main search panel with filters and history"""

    # Signals
    search_requested = pyqtSignal(dict)  # Search parameters
    filter_changed = pyqtSignal(dict)  # Active filters
    instant_search_requested = pyqtSignal(dict)  # Instant search (as-you-type)

    MAX_HISTORY = 50
    DEBOUNCE_DELAY_MS = 200  # 200ms debounce for instant search

    def __init__(self, parent=None):
        super().__init__(parent)

        # State
        self.active_filters: Dict = {}
        self.search_history: List[str] = []
        self.settings = QSettings("SmartSearch", "SearchPanel")
        self.is_searching = False

        # Debounce timer for instant search
        self.search_debounce_timer = QTimer(self)
        self.search_debounce_timer.setSingleShot(True)
        self.search_debounce_timer.timeout.connect(self._trigger_instant_search)

        self._init_ui()
        self._load_history()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Search box row
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        # Search input with icon
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search files...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.returnPressed.connect(self._perform_search)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        search_row.addWidget(self.search_input, stretch=1)

        # Search status indicator
        self.search_status_label = QLabel()
        self.search_status_label.setStyleSheet("color: #666; font-style: italic;")
        self.search_status_label.setVisible(False)
        search_row.addWidget(self.search_status_label)

        # Search button
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self._perform_search)
        search_row.addWidget(self.search_btn)

        layout.addLayout(search_row)

        # Filter chips row
        filter_chips_row = QHBoxLayout()
        filter_chips_row.setSpacing(4)

        # Size filters
        size_label = QLabel("Size:")
        size_label.setStyleSheet("color: #605E5C; font-weight: bold; padding: 4px;")
        filter_chips_row.addWidget(size_label)

        self.size_filter_chips = {}
        size_filters = [
            (">1KB", ">1kb"),
            (">1MB", ">1mb"),
            (">100MB", ">100mb"),
            (">1GB", ">1gb"),
        ]
        for label, value in size_filters:
            chip = FilterChip(label, removable=False)
            chip.clicked.connect(lambda v=value, c=chip: self._toggle_size_filter(v, c))
            self.size_filter_chips[value] = chip
            filter_chips_row.addWidget(chip)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setFrameShadow(QFrame.Shadow.Sunken)
        sep1.setStyleSheet("color: #E1DFDD;")
        filter_chips_row.addWidget(sep1)

        # Date filters
        date_label = QLabel("Date:")
        date_label.setStyleSheet("color: #605E5C; font-weight: bold; padding: 4px;")
        filter_chips_row.addWidget(date_label)

        self.date_filter_chips = {}
        date_filters = [
            ("Today", "today"),
            ("Week", "thisweek"),
            ("Month", "thismonth"),
            ("Year", "thisyear"),
        ]
        for label, value in date_filters:
            chip = FilterChip(label, removable=False)
            chip.clicked.connect(lambda v=value, c=chip: self._toggle_date_filter(v, c))
            self.date_filter_chips[value] = chip
            filter_chips_row.addWidget(chip)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setFrameShadow(QFrame.Shadow.Sunken)
        sep2.setStyleSheet("color: #E1DFDD;")
        filter_chips_row.addWidget(sep2)

        # Type filters
        type_label = QLabel("Type:")
        type_label.setStyleSheet("color: #605E5C; font-weight: bold; padding: 4px;")
        filter_chips_row.addWidget(type_label)

        self.type_filter_chips = {}
        type_filters = [
            ("📄 Docs", "document"),
            ("🖼 Images", "image"),
            ("🎬 Videos", "video"),
            ("🎵 Audio", "audio"),
            ("📦 Archives", "archive"),
            ("💻 Code", "code"),
        ]
        for label, value in type_filters:
            chip = FilterChip(label, removable=False)
            chip.clicked.connect(lambda v=value, c=chip: self._toggle_type_filter(v, c))
            self.type_filter_chips[value] = chip
            filter_chips_row.addWidget(chip)

        filter_chips_row.addStretch()

        # Clear all filters button
        self.clear_filters_btn = QPushButton("Clear All")
        self.clear_filters_btn.setProperty("secondary", True)
        self.clear_filters_btn.clicked.connect(self._clear_all_filters)
        self.clear_filters_btn.setVisible(False)
        filter_chips_row.addWidget(self.clear_filters_btn)

        # Advanced filters toggle
        self.advanced_toggle_btn = QPushButton("▼ More Filters")
        self.advanced_toggle_btn.setProperty("secondary", True)
        self.advanced_toggle_btn.setCheckable(True)
        self.advanced_toggle_btn.clicked.connect(self._toggle_advanced_filters)
        filter_chips_row.addWidget(self.advanced_toggle_btn)

        layout.addLayout(filter_chips_row)

        # Advanced filters panel (collapsible)
        self.advanced_panel = QFrame()
        self.advanced_panel.setFrameShape(QFrame.Shape.StyledPanel)
        self.advanced_panel.setStyleSheet("""
            QFrame {
                background-color: #F9F9F9;
                border: 1px solid #E1DFDD;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        self.advanced_panel.setVisible(False)

        advanced_layout = QVBoxLayout(self.advanced_panel)
        advanced_layout.setSpacing(8)

        # Extension filter row
        ext_row = QHBoxLayout()
        ext_label = QLabel("Extensions:")
        ext_label.setStyleSheet("color: #605E5C; font-weight: bold;")
        ext_row.addWidget(ext_label)

        self.extension_input = QLineEdit()
        self.extension_input.setPlaceholderText("pdf, doc, jpg (comma separated)")
        self.extension_input.textChanged.connect(self._on_extension_changed)
        ext_row.addWidget(self.extension_input)

        advanced_layout.addLayout(ext_row)

        # Custom size row
        size_row = QHBoxLayout()
        size_row_label = QLabel("Custom Size:")
        size_row_label.setStyleSheet("color: #605E5C; font-weight: bold;")
        size_row.addWidget(size_row_label)

        self.size_operator_combo = QComboBox()
        self.size_operator_combo.addItems([">", "<", ">=", "<=", "="])
        size_row.addWidget(self.size_operator_combo)

        self.size_value_spin = QSpinBox()
        self.size_value_spin.setRange(0, 999999)
        self.size_value_spin.setValue(100)
        size_row.addWidget(self.size_value_spin)

        self.size_unit_combo = QComboBox()
        self.size_unit_combo.addItems(["KB", "MB", "GB"])
        self.size_unit_combo.setCurrentText("MB")
        size_row.addWidget(self.size_unit_combo)

        self.apply_custom_size_btn = QPushButton("Apply")
        self.apply_custom_size_btn.setProperty("secondary", True)
        self.apply_custom_size_btn.clicked.connect(self._apply_custom_size)
        size_row.addWidget(self.apply_custom_size_btn)

        size_row.addStretch()
        advanced_layout.addLayout(size_row)

        # Custom date row
        date_row = QHBoxLayout()
        date_row_label = QLabel("Custom Date:")
        date_row_label.setStyleSheet("color: #605E5C; font-weight: bold;")
        date_row.addWidget(date_row_label)

        self.date_field_combo = QComboBox()
        self.date_field_combo.addItems(["Modified", "Created", "Accessed"])
        date_row.addWidget(self.date_field_combo)

        self.date_operator_combo = QComboBox()
        self.date_operator_combo.addItems([">", "<", ">=", "<=", "="])
        date_row.addWidget(self.date_operator_combo)

        self.custom_date_edit = QDateEdit()
        self.custom_date_edit.setCalendarPopup(True)
        self.custom_date_edit.setDate(QDate.currentDate())
        date_row.addWidget(self.custom_date_edit)

        self.apply_custom_date_btn = QPushButton("Apply")
        self.apply_custom_date_btn.setProperty("secondary", True)
        self.apply_custom_date_btn.clicked.connect(self._apply_custom_date)
        date_row.addWidget(self.apply_custom_date_btn)

        date_row.addStretch()
        advanced_layout.addLayout(date_row)

        layout.addWidget(self.advanced_panel)

        # Active filters display (chips for active filters)
        self.active_filters_row = QHBoxLayout()
        self.active_filters_row.setSpacing(4)

        active_label = QLabel("Active:")
        active_label.setStyleSheet("color: #0078D4; font-weight: bold; padding: 4px;")
        self.active_filters_row.addWidget(active_label)

        self.active_filters_container = QHBoxLayout()
        self.active_filters_container.setSpacing(4)
        self.active_filters_row.addLayout(self.active_filters_container)

        self.active_filters_row.addStretch()

        self.active_filters_widget = QWidget()
        self.active_filters_widget.setLayout(self.active_filters_row)
        self.active_filters_widget.setVisible(False)
        layout.addWidget(self.active_filters_widget)

        # History popup (hidden initially)
        self.history_popup = SearchHistoryPopup(self)
        self.history_popup.item_clicked.connect(self._on_history_selected)
        self.history_popup.hide()

    def _on_search_text_changed(self, text: str):
        """Handle search text change with instant search debouncing"""
        # Hide history popup when typing
        if text:
            self.history_popup.hide()

            # Stop previous debounce timer
            self.search_debounce_timer.stop()

            # Show searching indicator
            self._set_searching_status(True)

            # Start new debounce timer
            self.search_debounce_timer.start(self.DEBOUNCE_DELAY_MS)
        else:
            # Empty text - stop searching
            self.search_debounce_timer.stop()
            self._set_searching_status(False)

            # Show history popup if input has focus
            if self.search_input.hasFocus() and self.search_history:
                pos = self.search_input.mapToGlobal(self.search_input.rect().bottomLeft())
                self.history_popup.move(pos)
                self.history_popup.set_history(self.search_history)
                self.history_popup.show()

    def _trigger_instant_search(self):
        """Trigger instant search after debounce delay"""
        search_text = self.search_input.text().strip()

        if not search_text:
            self._set_searching_status(False)
            return

        # Convert UI filters to query string
        full_query = FilterIntegration.ui_filters_to_query(search_text, self.active_filters)

        # Build search params
        params = {
            'query': full_query,
            'original_query': search_text,
            'instant': True,  # Mark as instant search
            'filters': self.active_filters.copy(),
        }

        # Emit instant search signal
        self.instant_search_requested.emit(params)

    def _set_searching_status(self, searching: bool):
        """Update searching status indicator"""
        self.is_searching = searching
        if searching:
            self.search_status_label.setText("⏳ Searching...")
            self.search_status_label.setVisible(True)
        else:
            self.search_status_label.setVisible(False)

    def set_search_complete(self):
        """Called when search is complete"""
        self._set_searching_status(False)

    def _on_history_selected(self, text: str):
        """Handle history item selection"""
        self.search_input.setText(text)
        self.history_popup.hide()
        self._perform_search()

    def _toggle_size_filter(self, value: str, chip: FilterChip):
        """Toggle size filter chip"""
        # Deactivate all other size chips
        for v, c in self.size_filter_chips.items():
            if v != value:
                c.setActive(False)

        # Toggle current chip
        is_active = not chip.isActive()
        chip.setActive(is_active)

        # Update active filters
        if is_active:
            self.active_filters['size'] = value
        else:
            self.active_filters.pop('size', None)

        self._update_active_filters_display()
        self.filter_changed.emit(self.active_filters)

    def _toggle_date_filter(self, value: str, chip: FilterChip):
        """Toggle date filter chip"""
        # Deactivate all other date chips
        for v, c in self.date_filter_chips.items():
            if v != value:
                c.setActive(False)

        # Toggle current chip
        is_active = not chip.isActive()
        chip.setActive(is_active)

        # Update active filters
        if is_active:
            self.active_filters['modified'] = value
        else:
            self.active_filters.pop('modified', None)

        self._update_active_filters_display()
        self.filter_changed.emit(self.active_filters)

    def _toggle_type_filter(self, value: str, chip: FilterChip):
        """Toggle type filter chip"""
        # Deactivate all other type chips
        for v, c in self.type_filter_chips.items():
            if v != value:
                c.setActive(False)

        # Toggle current chip
        is_active = not chip.isActive()
        chip.setActive(is_active)

        # Update active filters
        if is_active:
            self.active_filters['type'] = value
        else:
            self.active_filters.pop('type', None)

        self._update_active_filters_display()
        self.filter_changed.emit(self.active_filters)

    def _on_extension_changed(self, text: str):
        """Handle extension input change"""
        if text.strip():
            extensions = [ext.strip().lstrip('.') for ext in text.split(',') if ext.strip()]
            if extensions:
                self.active_filters['extensions'] = extensions
            else:
                self.active_filters.pop('extensions', None)
        else:
            self.active_filters.pop('extensions', None)

        self._update_active_filters_display()

    def _apply_custom_size(self):
        """Apply custom size filter"""
        operator = self.size_operator_combo.currentText()
        value = self.size_value_spin.value()
        unit = self.size_unit_combo.currentText().lower()

        size_filter = f"{operator}{value}{unit}"
        self.active_filters['size'] = size_filter

        # Deactivate preset size chips
        for chip in self.size_filter_chips.values():
            chip.setActive(False)

        self._update_active_filters_display()
        self.filter_changed.emit(self.active_filters)

    def _apply_custom_date(self):
        """Apply custom date filter"""
        field = self.date_field_combo.currentText().lower()
        operator = self.date_operator_combo.currentText()
        date = self.custom_date_edit.date().toPyDate()
        date_str = date.strftime("%Y-%m-%d")

        date_filter = f"{operator}{date_str}"
        self.active_filters[field] = date_filter

        # Deactivate preset date chips
        for chip in self.date_filter_chips.values():
            chip.setActive(False)

        self._update_active_filters_display()
        self.filter_changed.emit(self.active_filters)

    def _toggle_advanced_filters(self, checked: bool):
        """Toggle advanced filters panel"""
        self.advanced_panel.setVisible(checked)
        self.advanced_toggle_btn.setText("▲ Less Filters" if checked else "▼ More Filters")

    def _clear_all_filters(self):
        """Clear all active filters"""
        self.active_filters.clear()

        # Deactivate all chips
        for chip in self.size_filter_chips.values():
            chip.setActive(False)
        for chip in self.date_filter_chips.values():
            chip.setActive(False)
        for chip in self.type_filter_chips.values():
            chip.setActive(False)

        # Clear extension input
        self.extension_input.clear()

        self._update_active_filters_display()
        self.filter_changed.emit(self.active_filters)

    def _update_active_filters_display(self):
        """Update the active filters display row"""
        # Clear existing chips
        while self.active_filters_container.count():
            item = self.active_filters_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Show/hide clear button and active filters widget
        has_filters = bool(self.active_filters)
        self.clear_filters_btn.setVisible(has_filters)
        self.active_filters_widget.setVisible(has_filters)

        if not has_filters:
            return

        # Add chips for active filters
        for key, value in self.active_filters.items():
            if isinstance(value, list):
                # Extensions
                chip_text = f"{key}: {', '.join(value)}"
            else:
                chip_text = f"{key}: {value}"

            chip = FilterChip(chip_text, removable=True)
            chip.removed.connect(lambda k=key: self._remove_active_filter(k))
            self.active_filters_container.addWidget(chip)

    def _remove_active_filter(self, key: str):
        """Remove a specific active filter"""
        self.active_filters.pop(key, None)

        # Deactivate corresponding chip if it exists
        if key == 'size':
            for chip in self.size_filter_chips.values():
                chip.setActive(False)
        elif key in ['modified', 'created', 'accessed']:
            for chip in self.date_filter_chips.values():
                chip.setActive(False)
        elif key == 'type':
            for chip in self.type_filter_chips.values():
                chip.setActive(False)
        elif key == 'extensions':
            self.extension_input.clear()

        self._update_active_filters_display()
        self.filter_changed.emit(self.active_filters)

    def _show_advanced_search(self):
        """Show advanced search dialog (legacy - kept for compatibility)"""
        dialog = AdvancedSearchDialog(self)

        # Pre-fill with current filters
        # TODO: Populate dialog from active_filters

        if dialog.exec() == QDialog.DialogCode.Accepted:
            params = dialog.get_search_params()
            self._apply_advanced_filters(params)

    def _apply_advanced_filters(self, params: Dict):
        """Apply advanced search filters"""
        # Update active filters
        self.active_filters.update(params)

        # Update UI
        self._update_active_filters_display()

        # Emit filter changed
        self.filter_changed.emit(self.active_filters)

        # Perform search
        self._perform_search()

    def _perform_search(self):
        """Perform search"""
        search_text = self.search_input.text().strip()

        if not search_text and not self.active_filters:
            return

        # Add to history
        if search_text and search_text not in self.search_history:
            self.search_history.insert(0, search_text)
            if len(self.search_history) > self.MAX_HISTORY:
                self.search_history = self.search_history[:self.MAX_HISTORY]
            self._save_history()

        # Validate filters
        is_valid, error_msg = FilterIntegration.validate_filters(self.active_filters)
        if not is_valid:
            print(f"Filter validation error: {error_msg}")
            # Could show error dialog here
            return

        # Convert UI filters to query string
        full_query = FilterIntegration.ui_filters_to_query(search_text, self.active_filters)

        # Build search params
        params = {
            'query': full_query,
            'original_query': search_text,
            'filters': self.active_filters.copy(),
            'filter_summary': FilterIntegration.get_filter_summary(self.active_filters)
        }

        # Emit search signal
        self.search_requested.emit(params)

    def _load_history(self):
        """Load search history from settings"""
        history_str = self.settings.value("search_history", "")
        if history_str:
            try:
                self.search_history = json.loads(history_str)
            except:
                self.search_history = []

    def _save_history(self):
        """Save search history to settings"""
        self.settings.setValue("search_history", json.dumps(self.search_history))

    def clear_history(self):
        """Clear search history"""
        self.search_history.clear()
        self._save_history()

    def get_search_text(self) -> str:
        """Get current search text"""
        return self.search_input.text()

    def set_search_text(self, text: str):
        """Set search text"""
        self.search_input.setText(text)

    def get_active_filters(self) -> Dict:
        """Get active filters"""
        return self.active_filters.copy()

    def clear_filters(self):
        """Clear all filters"""
        self._clear_all_filters()
