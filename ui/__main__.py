"""
UI Module Entry Point - Demo/Testing
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from .main_window import MainWindow


def main():
    """Main entry point for UI module"""
    # Enable high DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Smart Search Pro")
    app.setOrganizationName("SmartSearch")
    app.setApplicationVersion("1.0.0")

    # Set default font
    font = QFont("Segoe UI", 9)
    app.setFont(font)

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
