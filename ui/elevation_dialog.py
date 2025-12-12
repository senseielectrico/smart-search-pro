"""
Elevation Request Dialog for Smart Search Pro.

Provides a UAC-style dialog for requesting administrator privileges.
"""

import sys
import os
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QWidget, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen

try:
    from system.elevation import ElevationManager
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from system.elevation import ElevationManager


class UACSh ieldIcon(QWidget):
    """Custom UAC shield icon widget."""

    def __init__(self, size: int = 32, parent=None):
        super().__init__(parent)
        self.icon_size = size
        self.setFixedSize(QSize(size, size))

    def paintEvent(self, event):
        """Paint the UAC shield icon."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Shield background
        # Draw a shield shape similar to Windows UAC
        shield_color = QColor(41, 128, 185)  # Blue shield
        painter.setBrush(shield_color)
        painter.setPen(QPen(QColor(30, 90, 140), 2))

        # Draw shield polygon
        width = self.icon_size
        height = self.icon_size
        center_x = width // 2
        center_y = height // 2

        # Shield path (simplified)
        from PyQt6.QtGui import QPainterPath

        path = QPainterPath()
        path.moveTo(center_x, 2)  # Top center
        path.lineTo(width - 4, height // 3)  # Top right
        path.lineTo(width - 4, height * 2 // 3)  # Bottom right
        path.lineTo(center_x, height - 2)  # Bottom center
        path.lineTo(4, height * 2 // 3)  # Bottom left
        path.lineTo(4, height // 3)  # Top left
        path.closeSubpath()

        painter.drawPath(path)

        # Draw inner details (simplified Windows logo shape)
        painter.setBrush(QColor(255, 255, 255, 200))
        painter.setPen(Qt.PenStyle.NoPen)

        # Four quadrants representing Windows logo
        quad_size = width // 6
        spacing = 2

        # Top left
        painter.drawRect(
            center_x - quad_size - spacing,
            center_y - quad_size - spacing,
            quad_size,
            quad_size
        )

        # Top right
        painter.drawRect(
            center_x + spacing,
            center_y - quad_size - spacing,
            quad_size,
            quad_size
        )

        # Bottom left
        painter.drawRect(
            center_x - quad_size - spacing,
            center_y + spacing,
            quad_size,
            quad_size
        )

        # Bottom right
        painter.drawRect(
            center_x + spacing,
            center_y + spacing,
            quad_size,
            quad_size
        )


class ElevationDialog(QDialog):
    """
    Elevation request dialog with UAC-style appearance.

    Features:
    - UAC shield icon
    - Operation description
    - Remember choice option
    - Cancel/Elevate buttons
    - Windows UAC-inspired styling
    """

    def __init__(
        self,
        operation: str,
        description: str,
        show_remember: bool = True,
        parent=None
    ):
        """
        Initialize elevation dialog.

        Args:
            operation: Name of operation requiring elevation
            description: Detailed description
            show_remember: Show "Remember my choice" checkbox
            parent: Parent widget
        """
        super().__init__(parent)

        self.operation = operation
        self.description = description
        self.show_remember = show_remember
        self.remember_choice = False

        self.elevation_manager = ElevationManager()

        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        self.setWindowTitle("User Account Control")
        self.setModal(True)
        self.setFixedWidth(500)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header section
        self._create_header(layout)

        # Content section
        self._create_content(layout)

        # Footer section
        self._create_footer(layout)

        # Apply UAC-style styling
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QLabel#header {
                font-size: 14pt;
                font-weight: bold;
                color: #2c3e50;
            }
            QLabel#description {
                font-size: 10pt;
                color: #555555;
            }
            QLabel#warning {
                font-size: 9pt;
                color: #c0392b;
            }
            QPushButton#elevate {
                background-color: #2980b9;
                color: white;
                border: none;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 3px;
            }
            QPushButton#elevate:hover {
                background-color: #3498db;
            }
            QPushButton#elevate:pressed {
                background-color: #1c598a;
            }
            QPushButton#cancel {
                background-color: #e0e0e0;
                color: #333333;
                border: 1px solid #cccccc;
                padding: 8px 20px;
                border-radius: 3px;
            }
            QPushButton#cancel:hover {
                background-color: #d0d0d0;
            }
            QCheckBox {
                font-size: 9pt;
                color: #555555;
            }
            QFrame#separator {
                background-color: #cccccc;
                max-height: 1px;
            }
        """)

    def _create_header(self, layout):
        """Create header section."""
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        # UAC Shield Icon
        shield_icon = UACShieldIcon(48)
        header_layout.addWidget(shield_icon)

        # Header text
        header_label = QLabel("Do you want to allow this app to make changes to your device?")
        header_label.setObjectName("header")
        header_label.setWordWrap(True)
        header_layout.addWidget(header_label, 1)

        layout.addLayout(header_layout)

        # Separator
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(separator)

    def _create_content(self, layout):
        """Create content section."""
        content_layout = QVBoxLayout()
        content_layout.setSpacing(10)

        # Program info
        program_layout = QHBoxLayout()
        program_layout.addWidget(QLabel("Program:"))
        program_label = QLabel("Smart Search Pro")
        program_label.setStyleSheet("font-weight: bold;")
        program_layout.addWidget(program_label, 1)
        content_layout.addLayout(program_layout)

        # Operation
        operation_layout = QHBoxLayout()
        operation_layout.addWidget(QLabel("Operation:"))
        operation_label = QLabel(self.operation)
        operation_label.setObjectName("description")
        operation_label.setWordWrap(True)
        operation_layout.addWidget(operation_label, 1)
        content_layout.addLayout(operation_layout)

        # Description
        if self.description:
            desc_label = QLabel(self.description)
            desc_label.setObjectName("description")
            desc_label.setWordWrap(True)
            content_layout.addWidget(desc_label)

        # Current elevation status
        if self.elevation_manager.is_elevated():
            status_label = QLabel("Current Status: Running as Administrator")
            status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            status_label = QLabel("Current Status: Limited User")
            status_label.setStyleSheet("color: #e67e22; font-weight: bold;")
        content_layout.addWidget(status_label)

        # Warning
        warning_label = QLabel(
            "⚠ Elevated operations can access system files and make system-wide changes. "
            "Only proceed if you trust this operation."
        )
        warning_label.setObjectName("warning")
        warning_label.setWordWrap(True)
        content_layout.addWidget(warning_label)

        layout.addLayout(content_layout)

        # Separator
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(separator)

    def _create_footer(self, layout):
        """Create footer section."""
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(10)

        # Remember choice checkbox
        if self.show_remember:
            self.remember_checkbox = QCheckBox("Remember my choice for this operation")
            self.remember_checkbox.setToolTip(
                "If checked, this choice will be remembered for future requests"
            )
            footer_layout.addWidget(self.remember_checkbox)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("cancel")
        cancel_button.setFixedWidth(100)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        # Elevate button
        elevate_button = QPushButton("Elevate")
        elevate_button.setObjectName("elevate")
        elevate_button.setFixedWidth(100)
        elevate_button.setDefault(True)
        elevate_button.clicked.connect(self._on_elevate)
        button_layout.addWidget(elevate_button)

        footer_layout.addLayout(button_layout)
        layout.addLayout(footer_layout)

    def _on_elevate(self):
        """Handle elevate button click."""
        # Check remember choice
        if self.show_remember and hasattr(self, 'remember_checkbox'):
            self.remember_choice = self.remember_checkbox.isChecked()

        self.accept()

    def get_remember_choice(self) -> bool:
        """Get whether user wants to remember this choice."""
        return self.remember_choice


class QuickElevationDialog(QDialog):
    """Quick elevation confirmation dialog (less verbose)."""

    def __init__(self, operation: str, parent=None):
        super().__init__(parent)
        self.operation = operation
        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        self.setWindowTitle("Administrator Permission Required")
        self.setModal(True)
        self.setFixedWidth(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Icon and message
        content_layout = QHBoxLayout()

        # Shield icon
        shield = UACShieldIcon(32)
        content_layout.addWidget(shield)

        # Message
        message = QLabel(f"This operation requires administrator privileges:\n\n{self.operation}")
        message.setWordWrap(True)
        content_layout.addWidget(message, 1)

        layout.addLayout(content_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        elevate_button = QPushButton("Continue")
        elevate_button.setDefault(True)
        elevate_button.clicked.connect(self.accept)
        elevate_button.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border: none;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        """)
        button_layout.addWidget(elevate_button)

        layout.addLayout(button_layout)


# Example usage
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

    app = QApplication(sys.argv)

    # Test window
    window = QWidget()
    layout = QVBoxLayout(window)

    def show_full_dialog():
        dialog = ElevationDialog(
            operation="Modify System Files",
            description="Smart Search Pro needs to modify system registry entries to enable advanced search features.",
            show_remember=True,
            parent=window
        )

        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            print("Elevation granted!")
            if dialog.get_remember_choice():
                print("User wants to remember this choice")
        else:
            print("Elevation denied")

    def show_quick_dialog():
        dialog = QuickElevationDialog(
            operation="Access protected directory: C:\\Windows\\System32",
            parent=window
        )

        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            print("Quick elevation granted!")
        else:
            print("Quick elevation denied")

    # Test buttons
    full_button = QPushButton("Show Full Elevation Dialog")
    full_button.clicked.connect(show_full_dialog)
    layout.addWidget(full_button)

    quick_button = QPushButton("Show Quick Elevation Dialog")
    quick_button.clicked.connect(show_quick_dialog)
    layout.addWidget(quick_button)

    window.setWindowTitle("Elevation Dialog Test")
    window.resize(400, 200)
    window.show()

    sys.exit(app.exec())
