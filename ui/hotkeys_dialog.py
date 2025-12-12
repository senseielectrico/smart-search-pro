"""
Hotkeys Configuration Dialog for Smart Search Pro.

Allows users to view and customize keyboard shortcuts.
"""

from typing import Dict, Optional, Tuple
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QMessageBox, QHeaderView, QGroupBox,
    QCheckBox, QWidget, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QKeyEvent

from system.hotkeys import HotkeyManager, ModifierKeys, VirtualKeys, parse_hotkey_string


class HotkeyCaptureWidget(QLineEdit):
    """
    Widget for capturing keyboard input for hotkey configuration.
    """

    hotkey_captured = pyqtSignal(str)  # Emits hotkey string like "Ctrl+Shift+F"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Press keys to capture...")
        self.setReadOnly(True)
        self._capturing = False
        self._modifiers = 0
        self._key = 0

    def keyPressEvent(self, event: QKeyEvent):
        """Capture key press events."""
        key = event.key()
        modifiers = event.modifiers()

        # Build hotkey string
        parts = []
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            parts.append("Ctrl")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            parts.append("Shift")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            parts.append("Alt")
        if modifiers & Qt.KeyboardModifier.MetaModifier:
            parts.append("Win")

        # Get key name
        key_name = None
        if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            key_name = chr(key)
        elif Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            key_name = chr(key)
        elif Qt.Key.Key_F1 <= key <= Qt.Key.Key_F12:
            key_name = f"F{key - Qt.Key.Key_F1 + 1}"
        elif key == Qt.Key.Key_Space:
            key_name = "Space"
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            key_name = "Enter"
        elif key == Qt.Key.Key_Escape:
            key_name = "Esc"
        elif key == Qt.Key.Key_Tab:
            key_name = "Tab"
        elif key == Qt.Key.Key_Delete:
            key_name = "Delete"
        elif key == Qt.Key.Key_Backspace:
            key_name = "Backspace"

        # Must have at least one modifier and a valid key
        if key_name and parts:
            parts.append(key_name)
            hotkey_str = "+".join(parts)
            self.setText(hotkey_str)
            self.hotkey_captured.emit(hotkey_str)
        elif key_name and not parts:
            # Special keys without modifiers
            if key in (Qt.Key.Key_Delete, Qt.Key.Key_F5, Qt.Key.Key_Escape,
                      Qt.Key.Key_Enter, Qt.Key.Key_Space):
                self.setText(key_name)
                self.hotkey_captured.emit(key_name)

    def clear_capture(self):
        """Clear captured hotkey."""
        self.clear()


class HotkeysDialog(QDialog):
    """
    Dialog for configuring keyboard shortcuts.
    """

    def __init__(self, hotkey_manager: HotkeyManager, parent=None):
        super().__init__(parent)
        self.hotkey_manager = hotkey_manager
        self.changes_made = False

        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumSize(700, 500)
        self._init_ui()
        self._load_hotkeys()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("<h2>Keyboard Shortcuts</h2>")
        layout.addWidget(header_label)

        info_label = QLabel(
            "Configure keyboard shortcuts for Smart Search Pro. "
            "Click on a shortcut to change it."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Hotkeys table
        table_group = QGroupBox("Application Shortcuts")
        table_layout = QVBoxLayout(table_group)

        self.hotkeys_table = QTableWidget()
        self.hotkeys_table.setColumnCount(4)
        self.hotkeys_table.setHorizontalHeaderLabels([
            "Action", "Shortcut", "Description", "Type"
        ])

        # Configure table
        header = self.hotkeys_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.hotkeys_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.hotkeys_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        table_layout.addWidget(self.hotkeys_table)
        layout.addWidget(table_group)

        # Edit controls
        edit_group = QGroupBox("Edit Shortcut")
        edit_layout = QHBoxLayout(edit_group)

        edit_layout.addWidget(QLabel("New Shortcut:"))

        self.capture_widget = HotkeyCaptureWidget()
        self.capture_widget.hotkey_captured.connect(self._on_hotkey_captured)
        edit_layout.addWidget(self.capture_widget, stretch=1)

        self.clear_capture_btn = QPushButton("Clear")
        self.clear_capture_btn.clicked.connect(self.capture_widget.clear_capture)
        edit_layout.addWidget(self.clear_capture_btn)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._apply_hotkey_change)
        self.apply_btn.setEnabled(False)
        edit_layout.addWidget(self.apply_btn)

        self.reset_btn = QPushButton("Reset to Default")
        self.reset_btn.clicked.connect(self._reset_selected_hotkey)
        edit_layout.addWidget(self.reset_btn)

        layout.addWidget(edit_group)

        # Global hotkey option
        self.global_hotkey_cb = QCheckBox(
            "Enable global hotkey (Ctrl+Shift+F) to show/hide window"
        )
        self.global_hotkey_cb.setChecked(True)
        self.global_hotkey_cb.stateChanged.connect(self._on_global_hotkey_changed)
        layout.addWidget(self.global_hotkey_cb)

        # Hint
        hint_label = QLabel(
            "<i>Note: Global hotkeys work system-wide, even when the application "
            "is minimized or not focused.</i>"
        )
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: gray;")
        layout.addWidget(hint_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.restore_all_btn = QPushButton("Restore All Defaults")
        self.restore_all_btn.clicked.connect(self._restore_all_defaults)
        button_layout.addWidget(self.restore_all_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._save_changes)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def _load_hotkeys(self):
        """Load hotkeys into table."""
        self.hotkeys_table.setRowCount(0)

        # Get all hotkeys
        hotkeys = self.hotkey_manager.get_all_hotkeys()

        for name, key_combo, description in hotkeys:
            row = self.hotkeys_table.rowCount()
            self.hotkeys_table.insertRow(row)

            # Action name
            action_item = QTableWidgetItem(name.replace("_", " ").title())
            action_item.setData(Qt.ItemDataRole.UserRole, name)
            action_item.setFlags(action_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.hotkeys_table.setItem(row, 0, action_item)

            # Shortcut
            shortcut_item = QTableWidgetItem(key_combo)
            shortcut_item.setFlags(shortcut_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.hotkeys_table.setItem(row, 1, shortcut_item)

            # Description
            desc_item = QTableWidgetItem(description)
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.hotkeys_table.setItem(row, 2, desc_item)

            # Type
            hotkey_info = self.hotkey_manager.get_hotkey_info(name)
            type_str = "Global" if (hotkey_info and hotkey_info.is_global) else "Local"
            type_item = QTableWidgetItem(type_str)
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.hotkeys_table.setItem(row, 3, type_item)

    def _on_hotkey_captured(self, hotkey_str: str):
        """Handle hotkey capture."""
        # Check for conflicts
        parsed = parse_hotkey_string(hotkey_str)
        if parsed:
            modifiers, vk_code = parsed
            conflict = self.hotkey_manager.check_conflict(modifiers, vk_code)

            if conflict:
                # Get current selection
                selected = self.hotkeys_table.selectedItems()
                if selected:
                    current_name = selected[0].data(Qt.ItemDataRole.UserRole)
                    if conflict != current_name:
                        QMessageBox.warning(
                            self,
                            "Conflict",
                            f"This shortcut is already used by: {conflict}"
                        )
                        self.capture_widget.clear()
                        self.apply_btn.setEnabled(False)
                        return

        self.apply_btn.setEnabled(True)

    def _apply_hotkey_change(self):
        """Apply hotkey change to selected action."""
        selected = self.hotkeys_table.selectedItems()
        if not selected:
            return

        # Get action name
        action_name = selected[0].data(Qt.ItemDataRole.UserRole)

        # Get new hotkey
        new_hotkey = self.capture_widget.text()
        if not new_hotkey:
            return

        # Parse hotkey string
        parsed = parse_hotkey_string(new_hotkey)
        if not parsed:
            QMessageBox.warning(
                self,
                "Invalid Hotkey",
                f"Could not parse hotkey: {new_hotkey}"
            )
            return

        # Update table
        row = selected[0].row()
        self.hotkeys_table.item(row, 1).setText(new_hotkey)

        self.changes_made = True
        self.capture_widget.clear()
        self.apply_btn.setEnabled(False)

        QMessageBox.information(
            self,
            "Shortcut Updated",
            f"Shortcut for '{action_name}' updated to '{new_hotkey}'.\n"
            "Click Save to apply changes."
        )

    def _reset_selected_hotkey(self):
        """Reset selected hotkey to default."""
        selected = self.hotkeys_table.selectedItems()
        if not selected:
            return

        # This would need default hotkey configuration
        QMessageBox.information(
            self,
            "Reset",
            "Default hotkey restoration not yet implemented."
        )

    def _restore_all_defaults(self):
        """Restore all hotkeys to defaults."""
        reply = QMessageBox.question(
            self,
            "Restore Defaults",
            "Are you sure you want to restore all shortcuts to their defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # This would need default hotkey configuration
            QMessageBox.information(
                self,
                "Restore Defaults",
                "Default restoration not yet implemented."
            )

    def _on_global_hotkey_changed(self, state: int):
        """Handle global hotkey checkbox change."""
        self.changes_made = True

    def _save_changes(self):
        """Save changes and close."""
        if self.changes_made:
            # Save hotkey configuration
            self.hotkey_manager.save_config()

            QMessageBox.information(
                self,
                "Saved",
                "Hotkey configuration saved.\n"
                "Changes will take effect on next restart."
            )

        self.accept()

    def get_global_hotkey_enabled(self) -> bool:
        """Get whether global hotkey is enabled."""
        return self.global_hotkey_cb.isChecked()
