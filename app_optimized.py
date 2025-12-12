#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Search Pro - OPTIMIZED Application Entry Point
====================================================

Performance-optimized launcher with:
- Lazy imports to reduce startup time
- Splash screen for visual feedback
- Performance monitoring
- Memory optimization
- Background initialization

Target: <2 seconds startup, <100ms search latency
"""

import sys
import os
import time
import logging
from pathlib import Path
from typing import Optional

# CRITICAL: Only import absolute essentials before splash screen
_startup_begin = time.perf_counter()

# Add package to path
APP_DIR = Path(__file__).parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# Configure minimal logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SmartSearchPro')


# Initialize performance monitoring EARLY
from core.performance import get_performance_monitor, get_lazy_importer

monitor = get_performance_monitor()
monitor.start_startup_tracking()
lazy = get_lazy_importer()


def check_critical_dependencies() -> bool:
    """Fast check for critical dependencies only"""
    try:
        import PyQt6
        return True
    except ImportError:
        print("\nERROR: PyQt6 is required. Install with: pip install PyQt6>=6.6.0")
        return False


def register_lazy_imports():
    """Register all heavy imports for lazy loading"""

    # Heavy optional imports
    lazy.register('openpyxl', lambda: __import__('openpyxl'))
    lazy.register('PIL', lambda: __import__('PIL'))
    lazy.register('pygments', lambda: __import__('pygments'))
    lazy.register('send2trash', lambda: __import__('send2trash'))
    lazy.register('xxhash', lambda: __import__('xxhash'))

    # System modules (loaded on demand)
    def _load_system_tray():
        from system.tray import SystemTrayIcon
        return SystemTrayIcon

    def _load_hotkeys():
        from system.hotkeys import HotkeyManager, Hotkey, HotkeyModifiers
        return {'HotkeyManager': HotkeyManager, 'Hotkey': Hotkey, 'HotkeyModifiers': HotkeyModifiers}

    def _load_single_instance():
        from system.single_instance import SingleInstanceManager
        return SingleInstanceManager

    lazy.register('system_tray', _load_system_tray)
    lazy.register('hotkeys', _load_hotkeys)
    lazy.register('single_instance', _load_single_instance)

    logger.debug("Lazy imports registered")


def create_app_icon():
    """Create application icon - OPTIMIZED"""
    from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
    from PyQt6.QtCore import Qt

    # Create only essential sizes for faster startup
    icon = QIcon()
    for size in [32, 48]:  # Minimal sizes, others on demand
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        scale = size / 64.0

        # Simple icon for fast rendering
        painter.setBrush(QColor(0, 120, 212))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(2*scale), int(2*scale), int(60*scale), int(60*scale))

        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(int(10*scale), int(10*scale), int(30*scale), int(30*scale))

        painter.end()
        icon.addPixmap(pixmap)

    return icon


class SmartSearchProApp:
    """Optimized main application class"""

    def __init__(self):
        self.app = None
        self.main_window = None
        self.tray_icon = None
        self.single_instance = None
        self.splash = None
        self.search_engine = None

    def ensure_single_instance(self) -> bool:
        """Ensure only one instance is running"""
        try:
            SingleInstance = lazy.get('single_instance')
            self.single_instance = SingleInstance("SmartSearchPro_v2")

            if not self.single_instance.is_first_instance():
                logger.info("Another instance running, activating it...")
                self.single_instance.activate_existing_window()
                return False
            return True
        except Exception as e:
            logger.warning(f"Single instance check failed: {e}")
            return True

    def setup_system_tray(self, main_window):
        """Setup system tray - LAZY LOADED"""
        try:
            SystemTrayIcon = lazy.get('system_tray')
            self.tray_icon = SystemTrayIcon(main_window)
            self.tray_icon.show()
            logger.info("System tray initialized")
        except Exception as e:
            logger.warning(f"System tray setup failed: {e}")

    def setup_global_hotkeys(self, main_window):
        """Setup global hotkeys - LAZY LOADED"""
        try:
            hotkeys = lazy.get('hotkeys')
            HotkeyManager = hotkeys['HotkeyManager']
            Hotkey = hotkeys['Hotkey']
            HotkeyModifiers = hotkeys['HotkeyModifiers']

            self.hotkey_manager = HotkeyManager()

            # Ctrl+Shift+F - Show and focus search
            search_hotkey = Hotkey(
                id=1,
                key=ord('F'),
                modifiers=HotkeyModifiers.CTRL | HotkeyModifiers.SHIFT,
                callback=lambda: self.activate_search(main_window)
            )
            self.hotkey_manager.register(search_hotkey)

            logger.info("Global hotkeys registered")
        except Exception as e:
            logger.warning(f"Hotkey setup failed: {e}")

    def activate_search(self, main_window):
        """Activate main window and focus search"""
        main_window.show()
        main_window.raise_()
        main_window.activateWindow()

        if hasattr(main_window, 'search_panel'):
            main_window.search_panel.focus_search()

    def initialize_search_engine_background(self, main_window):
        """Initialize search engine in background thread"""
        import threading

        def _init_engine():
            try:
                with monitor.track_operation("search_engine_init"):
                    from search.engine import SearchEngine
                    self.search_engine = SearchEngine()
                    main_window.set_search_engine(self.search_engine)
                    logger.info("Search engine initialized in background")
            except Exception as e:
                logger.error(f"Failed to initialize search engine: {e}")

        thread = threading.Thread(target=_init_engine, daemon=True)
        thread.start()

    def run(self) -> int:
        """Run the application - OPTIMIZED"""

        # Critical dependencies check (fast)
        if not check_critical_dependencies():
            return 1

        # Register lazy imports
        register_lazy_imports()

        # Import PyQt6 essentials ONLY
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont

        # Create Qt application
        with monitor.track_operation("qt_app_creation"):
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("Smart Search Pro")
            self.app.setApplicationVersion("2.0.0")
            self.app.setOrganizationName("SmartTools")

        # Show splash screen IMMEDIATELY
        from ui.splash_screen import SplashScreenManager
        splash_mgr = SplashScreenManager()
        splash_mgr.show(total_steps=8)

        # Set app icon (fast version)
        with monitor.track_operation("icon_creation"):
            app_icon = create_app_icon()
            self.app.setWindowIcon(app_icon)
        splash_mgr.update("Loading icon...")

        # Set font
        font = QFont("Segoe UI", 9)
        self.app.setFont(font)
        splash_mgr.update("Configuring UI...")

        # Check single instance
        if not self.ensure_single_instance():
            splash_mgr.close()
            return 0
        splash_mgr.update("Checking instance...")

        # Create main window (deferred heavy loading)
        with monitor.track_operation("main_window_creation"):
            try:
                from ui.main_window import MainWindow
                self.main_window = MainWindow()
            except ImportError:
                logger.info("Using legacy UI")
                from main import SmartSearchApp
                self.main_window = SmartSearchApp()

        self.main_window.setWindowIcon(app_icon)
        splash_mgr.update("Creating main window...")

        # Setup integrations (in background where possible)
        splash_mgr.update("Setting up system tray...")
        self.setup_system_tray(self.main_window)

        splash_mgr.update("Registering hotkeys...")
        self.setup_global_hotkeys(self.main_window)

        # Initialize search engine in background
        splash_mgr.update("Initializing search engine...")
        self.initialize_search_engine_background(self.main_window)

        # Finish splash and show window
        splash_mgr.update("Loading complete!")
        splash_mgr.finish(self.main_window)

        # End startup tracking
        monitor.end_startup_tracking()

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

        # Log startup performance
        monitor.log_summary()

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

        if self.search_engine:
            self.search_engine.shutdown()

        # Export performance report
        try:
            report_path = APP_DIR / "logs" / f"performance_{int(time.time())}.json"
            report_path.parent.mkdir(exist_ok=True)
            monitor.export_report(report_path)
            logger.info(f"Performance report saved: {report_path}")
        except Exception as e:
            logger.warning(f"Failed to save performance report: {e}")


def main():
    """Optimized entry point"""
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
