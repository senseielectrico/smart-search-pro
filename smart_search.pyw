#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Search - Windows Advanced File Search Application
========================================================

Production executable (.pyw) for Smart Search application.
No console window (hides stderr/stdout).

Features:
- Advanced file search with Windows Search API
- PyQt6 graphical interface
- Directory tree selection with persistent state
- File classification and filtering
- Splash screen during startup
- Friendly error messages for missing dependencies
- Dark/Light theme support

Usage:
    python smart_search.pyw
    (or double-click smart_search.pyw)

Author: Smart Search Team
Date: 2025-12-11
Version: 1.0.0
"""

import sys
import os
import traceback
import threading
import time
from pathlib import Path

# ============================================================================
# SPLASH SCREEN - Show before loading heavy dependencies
# ============================================================================

def show_splash_screen():
    """Shows a simple splash screen while app loads"""
    try:
        from PyQt6.QtWidgets import QSplashScreen, QApplication
        from PyQt6.QtGui import QPixmap, QColor, QFont
        from PyQt6.QtCore import Qt, QSize

        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)

        # Create a simple pixmap-based splash screen
        splash_pixmap = QPixmap(400, 300)
        splash_pixmap.fill(QColor(30, 30, 30))  # Dark background

        # Draw text on splash screen
        from PyQt6.QtGui import QPainter, QFont
        painter = QPainter(splash_pixmap)

        # Set font
        font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        painter.setFont(font)

        # Draw title
        painter.setPen(QColor(0, 200, 255))
        painter.drawText(
            splash_pixmap.rect(),
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
            "Smart Search\n\nLoading application..."
        )
        painter.end()

        # Show splash
        splash = QSplashScreen(splash_pixmap, Qt.WindowType.SplashScreen)
        splash.show()
        app.processEvents()

        return splash, app
    except Exception as e:
        return None, None


# ============================================================================
# DEPENDENCY CHECKER
# ============================================================================

class DependencyError(Exception):
    """Raised when required dependencies are missing"""
    pass


def check_dependencies():
    """
    Checks if all required dependencies are installed.

    Raises:
        DependencyError: If critical dependencies are missing
    """
    missing = []

    # Check PyQt6
    try:
        import PyQt6
        from PyQt6 import QtWidgets, QtCore, QtGui
    except ImportError as e:
        missing.append(("PyQt6", "pip install PyQt6>=6.6.0"))

    # Check pywin32 (for Windows Search API)
    try:
        import win32com.client
        import pythoncom
    except ImportError:
        missing.append((
            "pywin32",
            "pip install pywin32\n"
            "Then run: python -m pip install --upgrade pywin32\n"
            "And: python Scripts/pywin32_postinstall.py -install"
        ))

    # Check comtypes (alternative COM library)
    try:
        import comtypes
    except ImportError:
        missing.append(("comtypes", "pip install comtypes"))

    if missing:
        error_msg = "Missing required dependencies:\n\n"
        for pkg, install_cmd in missing:
            error_msg += f"- {pkg}\n  Install: {install_cmd}\n\n"
        raise DependencyError(error_msg)


# ============================================================================
# ERROR DIALOG
# ============================================================================

def show_error_dialog(title: str, message: str, exception: Exception = None):
    """
    Shows a user-friendly error dialog.

    Args:
        title: Dialog title
        message: Error message
        exception: Optional exception for detailed logging
    """
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        from PyQt6.QtCore import Qt

        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)

        # Build detailed message
        full_message = message
        if exception:
            full_message += f"\n\nDetails:\n{str(exception)}"

        # Show message box
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(full_message)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        msg_box.exec()

    except Exception as e:
        # Fallback: Write to error file
        error_file = Path.home() / ".smart_search" / "error.log"
        error_file.parent.mkdir(parents=True, exist_ok=True)
        with open(error_file, 'a') as f:
            f.write(f"\n[ERROR] {title}\n{message}\n")
            if exception:
                f.write(f"{traceback.format_exc()}\n")


# ============================================================================
# APPLICATION LAUNCHER
# ============================================================================

def launch_application():
    """
    Launches the Smart Search application.

    Handles:
    - Dependency checking
    - Splash screen display
    - Module imports
    - Application initialization
    - Error handling
    """
    splash = None
    app = None

    try:
        # ====================================================================
        # Step 1: Check dependencies
        # ====================================================================
        try:
            check_dependencies()
        except DependencyError as e:
            show_error_dialog(
                "Missing Dependencies",
                str(e) + "\n\nPlease install missing packages and try again.",
                e
            )
            sys.exit(1)

        # ====================================================================
        # Step 2: Show splash screen
        # ====================================================================
        splash, app = show_splash_screen()
        if splash:
            splash.showMessage("Initializing application...", alignment=4)

        # Small delay to ensure splash is visible
        time.sleep(0.5)

        # ====================================================================
        # Step 3: Import main module
        # ====================================================================
        if splash:
            splash.showMessage("Loading modules...", alignment=4)

        from main import SmartSearchApp
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QFont

        # ====================================================================
        # Step 4: Create application
        # ====================================================================
        if not app:
            app = QApplication(sys.argv)

        app.setApplicationName("Smart Search")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("SmartTools")

        # Set default font
        font = QFont("Segoe UI", 9)
        app.setFont(font)

        if splash:
            splash.showMessage("Creating main window...", alignment=4)

        # ====================================================================
        # Step 5: Create and show main window
        # ====================================================================
        window = SmartSearchApp()

        # Hide splash before showing main window
        if splash:
            splash.finish(window)
            splash = None

        window.show()

        # ====================================================================
        # Step 6: Run application
        # ====================================================================
        exit_code = app.exec()
        sys.exit(exit_code)

    except ImportError as e:
        show_error_dialog(
            "Import Error",
            f"Failed to import required module:\n{e}",
            e
        )
        sys.exit(1)

    except Exception as e:
        # Catch-all for unexpected errors
        error_type = type(e).__name__
        error_msg = (
            f"An unexpected error occurred:\n\n"
            f"{error_type}: {str(e)}\n\n"
            f"Please check the error log for more details."
        )
        show_error_dialog(
            "Application Error",
            error_msg,
            e
        )
        sys.exit(1)

    finally:
        # Cleanup
        if splash:
            try:
                splash.close()
            except:
                pass


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Suppress stdout/stderr on Windows for .pyw files
    if sys.platform == "win32":
        # Keep stderr for error logging but suppress normal output
        import warnings
        warnings.filterwarnings("ignore")

    # Launch the application
    launch_application()
