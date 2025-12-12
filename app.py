#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Search Pro - Advanced File Search and Management Application
===================================================================

Main application entry point that integrates all modules:
- Advanced search with Everything SDK integration
- Duplicate file finder with multi-pass hashing
- TeraCopy-style file operations
- File preview system
- Export functionality
- System tray and global hotkeys

Version: 2.0.0
Author: Smart Search Team
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional

# Add package to path
APP_DIR = Path(__file__).parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SmartSearchPro')


def check_dependencies():
    """Check and report missing dependencies"""
    missing = []
    optional_missing = []

    # Required
    try:
        import PyQt6
    except ImportError:
        missing.append(('PyQt6', 'pip install PyQt6>=6.6.0'))

    try:
        import win32com.client
    except ImportError:
        missing.append(('pywin32', 'pip install pywin32'))

    # Optional but recommended
    try:
        import openpyxl
    except ImportError:
        optional_missing.append('openpyxl (Excel export)')

    try:
        import send2trash
    except ImportError:
        optional_missing.append('send2trash (Safe delete)')

    try:
        import xxhash
    except ImportError:
        optional_missing.append('xxhash (Fast hashing)')

    try:
        from PIL import Image
    except ImportError:
        optional_missing.append('Pillow (Image preview)')

    try:
        import pygments
    except ImportError:
        optional_missing.append('Pygments (Syntax highlighting)')

    if missing:
        print("\n" + "="*60)
        print("MISSING REQUIRED DEPENDENCIES")
        print("="*60)
        for pkg, cmd in missing:
            print(f"\n  {pkg}")
            print(f"  Install: {cmd}")
        print("\n" + "="*60)
        return False

    if optional_missing:
        logger.info(f"Optional packages not installed: {', '.join(optional_missing)}")

    return True


def create_app_icon():
    """Create application icon programmatically"""
    from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush
    from PyQt6.QtCore import Qt

    sizes = [16, 24, 32, 48, 64, 128, 256]
    icon = QIcon()

    for size in sizes:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        scale = size / 64.0

        # Background gradient circle (blue)
        painter.setBrush(QColor(0, 120, 212))  # Windows blue
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(2*scale), int(2*scale), int(60*scale), int(60*scale))

        # Magnifying glass lens (white)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(int(10*scale), int(10*scale), int(30*scale), int(30*scale))

        # Inner lens (gradient blue)
        painter.setBrush(QColor(0, 120, 212))
        painter.drawEllipse(int(16*scale), int(16*scale), int(18*scale), int(18*scale))

        # Handle
        pen = QPen(QColor(255, 255, 255))
        pen.setWidth(int(7*scale))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(int(36*scale), int(36*scale), int(52*scale), int(52*scale))

        painter.end()
        icon.addPixmap(pixmap)

    return icon


class SmartSearchProApp:
    """Main application class that integrates all components"""

    def __init__(self):
        self.app = None
        self.main_window = None
        self.tray_icon = None
        self.single_instance = None

    def ensure_single_instance(self) -> bool:
        """Ensure only one instance is running"""
        try:
            from system.single_instance import SingleInstanceManager
            self.single_instance = SingleInstanceManager("SmartSearchPro_v2")

            if not self.single_instance.is_first_instance():
                logger.info("Another instance is already running, activating it...")
                self.single_instance.activate_existing_instance()
                return False
            return True
        except ImportError:
            logger.warning("Single instance module not available")
            return True
        except Exception as e:
            logger.warning(f"Single instance check failed: {e}")
            return True

    def setup_system_tray(self, main_window):
        """Setup system tray icon"""
        try:
            from system.tray import SystemTrayIcon
            self.tray_icon = SystemTrayIcon(main_window)
            self.tray_icon.show()
            logger.info("System tray icon initialized")
        except ImportError:
            logger.info("System tray module not available")
        except Exception as e:
            logger.warning(f"System tray setup failed: {e}")

    def setup_global_hotkeys(self, main_window):
        """Setup global hotkeys"""
        try:
            from system.hotkeys import HotkeyManager, Hotkey, HotkeyModifiers
            self.hotkey_manager = HotkeyManager()

            # Ctrl+Shift+F - Show and focus search
            search_hotkey = Hotkey(
                id=1,
                key=ord('F'),
                modifiers=HotkeyModifiers.CTRL | HotkeyModifiers.SHIFT,
                callback=lambda: self.activate_search(main_window)
            )
            self.hotkey_manager.register(search_hotkey)

            logger.info("Global hotkeys registered (Ctrl+Shift+F)")
        except ImportError:
            logger.info("Hotkey module not available")
        except Exception as e:
            logger.warning(f"Hotkey setup failed: {e}")

    def activate_search(self, main_window):
        """Activate main window and focus search"""
        main_window.show()
        main_window.raise_()
        main_window.activateWindow()

        # Focus search box
        if hasattr(main_window, 'search_panel'):
            main_window.search_panel.focus_search()

    def run(self) -> int:
        """Run the application"""
        # Check dependencies
        if not check_dependencies():
            return 1

        # Import PyQt6
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont

        # Create application
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Smart Search Pro")
        self.app.setApplicationVersion("2.0.0")
        self.app.setOrganizationName("SmartTools")

        # Set app icon
        app_icon = create_app_icon()
        self.app.setWindowIcon(app_icon)

        # Set font
        font = QFont("Segoe UI", 9)
        self.app.setFont(font)

        # Check single instance
        if not self.ensure_single_instance():
            return 0

        # Create main window
        try:
            from ui.main_window import MainWindow
            self.main_window = MainWindow()
        except ImportError:
            # Fallback to original main if new UI not available
            logger.info("Using legacy UI")
            from main import SmartSearchApp
            self.main_window = SmartSearchApp()

        self.main_window.setWindowIcon(app_icon)

        # Setup system integrations
        self.setup_system_tray(self.main_window)
        self.setup_global_hotkeys(self.main_window)

        # Show window
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

        # Bring to front on Windows
        if sys.platform == 'win32':
            try:
                import ctypes
                hwnd = int(self.main_window.winId())
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass

        logger.info("Smart Search Pro started successfully")

        # Run event loop
        return self.app.exec()

    def cleanup(self):
        """Cleanup resources"""
        if self.tray_icon:
            self.tray_icon.hide()

        if hasattr(self, 'hotkey_manager'):
            self.hotkey_manager.unregister_all()

        if self.single_instance:
            self.single_instance.release()


def main():
    """Main entry point"""
    app = SmartSearchProApp()

    try:
        exit_code = app.run()
    except KeyboardInterrupt:
        exit_code = 0
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        exit_code = 1
    finally:
        app.cleanup()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
