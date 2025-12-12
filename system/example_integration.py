"""
Complete integration example for Smart Search Pro.

This demonstrates how to use all system integration features together.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SmartSearchSystemIntegration:
    """
    Complete system integration for Smart Search Pro.

    This class demonstrates how to integrate all system features:
    - Single instance enforcement
    - System tray icon
    - Global hotkeys
    - Autostart management
    - Shell integration
    - Administrator elevation
    """

    def __init__(
        self,
        app_name: str = "SmartSearchPro",
        executable_path: Optional[str] = None,
    ):
        """
        Initialize system integration.

        Args:
            app_name: Application name
            executable_path: Path to executable (default: sys.executable)
        """
        self.app_name = app_name
        self.executable_path = executable_path or sys.executable

        # Components
        self.instance_manager = None
        self.tray_icon = None
        self.hotkey_manager = None
        self.autostart_manager = None
        self.shell_integration = None
        self.elevation_manager = None

        # Qt application (if using tray)
        self.qt_app = None
        self.main_window = None

    def initialize(self, use_tray: bool = True) -> bool:
        """
        Initialize all system integration features.

        Args:
            use_tray: Whether to use system tray

        Returns:
            True if initialization successful
        """
        logger.info("Initializing system integration...")

        # 1. Check single instance
        if not self._init_single_instance():
            logger.info("Another instance is running, exiting")
            return False

        # 2. Initialize elevation manager
        self._init_elevation()

        # 3. Initialize Qt application (if needed)
        if use_tray:
            if not self._init_qt_app():
                logger.warning("Failed to initialize Qt application")

        # 4. Initialize system tray
        if use_tray and self.qt_app:
            self._init_tray()

        # 5. Initialize hotkeys
        self._init_hotkeys()

        # 6. Initialize autostart
        self._init_autostart()

        # 7. Initialize shell integration (if admin)
        if self.elevation_manager and self.elevation_manager.is_elevated():
            self._init_shell_integration()

        logger.info("System integration initialized successfully")
        return True

    def _init_single_instance(self) -> bool:
        """Initialize single instance manager."""
        from single_instance import SingleInstanceManager

        self.instance_manager = SingleInstanceManager(self.app_name)

        if not self.instance_manager.is_first_instance():
            logger.info("Another instance detected, activating...")
            self.instance_manager.activate_existing_instance()
            return False

        logger.info("This is the first instance")
        return True

    def _init_elevation(self) -> None:
        """Initialize elevation manager."""
        from elevation import ElevationManager

        self.elevation_manager = ElevationManager()

        elevation_type = self.elevation_manager.get_elevation_type()
        logger.info(f"Elevation type: {elevation_type}")

    def _init_qt_app(self) -> bool:
        """Initialize Qt application."""
        try:
            from PyQt6.QtWidgets import QApplication

            self.qt_app = QApplication.instance()
            if self.qt_app is None:
                self.qt_app = QApplication(sys.argv)
                self.qt_app.setQuitOnLastWindowClosed(False)

            logger.info("Qt application initialized")
            return True

        except ImportError:
            logger.error("PyQt6 not installed")
            return False

    def _init_tray(self) -> None:
        """Initialize system tray icon."""
        try:
            from tray import SystemTrayIcon

            self.tray_icon = SystemTrayIcon()

            # Connect signals
            self.tray_icon.show_main_window.connect(self._on_show_window)
            self.tray_icon.hide_main_window.connect(self._on_hide_window)
            self.tray_icon.toggle_main_window.connect(self._on_toggle_window)
            self.tray_icon.quick_search_requested.connect(self._on_quick_search)
            self.tray_icon.exit_requested.connect(self._on_exit)

            self.tray_icon.show()
            self.tray_icon.set_tooltip(f"{self.app_name} - Running")
            self.tray_icon.show_notification(
                self.app_name,
                "Application started"
            )

            logger.info("System tray icon initialized")

        except Exception as e:
            logger.error(f"Failed to initialize tray icon: {e}")

    def _init_hotkeys(self) -> None:
        """Initialize global hotkeys."""
        try:
            from hotkeys import HotkeyManager, ModifierKeys, VirtualKeys

            self.hotkey_manager = HotkeyManager()

            # Register Ctrl+Shift+F for quick search
            self.hotkey_manager.register(
                "quick_search",
                ModifierKeys.CTRL | ModifierKeys.SHIFT,
                VirtualKeys.letter('F'),
                self._on_quick_search_hotkey,
                "Quick search"
            )

            # Register Ctrl+Shift+S for show window
            self.hotkey_manager.register(
                "show_window",
                ModifierKeys.CTRL | ModifierKeys.SHIFT,
                VirtualKeys.letter('S'),
                self._on_show_window,
                "Show window"
            )

            logger.info("Hotkeys registered")
            logger.info("  Ctrl+Shift+F - Quick search")
            logger.info("  Ctrl+Shift+S - Show window")

        except Exception as e:
            logger.error(f"Failed to initialize hotkeys: {e}")

    def _init_autostart(self) -> None:
        """Initialize autostart manager."""
        from autostart import AutostartManager, StartupMethod

        self.autostart_manager = AutostartManager(self.app_name)

        # Check if autostart is enabled
        is_enabled = self.autostart_manager.is_enabled(
            StartupMethod.REGISTRY_CURRENT_USER
        )

        logger.info(f"Autostart enabled: {is_enabled}")

    def _init_shell_integration(self) -> None:
        """Initialize shell integration (requires admin)."""
        try:
            from shell_integration import (
                ShellIntegration,
                ContextMenuItem,
            )

            self.shell_integration = ShellIntegration()

            # Set App ID for taskbar grouping
            self.shell_integration.set_app_id(f"com.{self.app_name.lower()}")

            logger.info("Shell integration initialized")

        except Exception as e:
            logger.error(f"Failed to initialize shell integration: {e}")

    def enable_autostart(self) -> bool:
        """
        Enable autostart.

        Returns:
            True if enabled successfully
        """
        if not self.autostart_manager:
            logger.error("Autostart manager not initialized")
            return False

        from autostart import StartupMethod

        success = self.autostart_manager.enable(
            self.executable_path,
            "--minimized --tray",
            StartupMethod.REGISTRY_CURRENT_USER,
            minimized=True
        )

        if success:
            logger.info("Autostart enabled")
        else:
            logger.error("Failed to enable autostart")

        return success

    def disable_autostart(self) -> bool:
        """
        Disable autostart.

        Returns:
            True if disabled successfully
        """
        if not self.autostart_manager:
            logger.error("Autostart manager not initialized")
            return False

        success = self.autostart_manager.disable_all()

        if success:
            logger.info("Autostart disabled")
        else:
            logger.error("Failed to disable autostart")

        return success

    def add_context_menu(
        self,
        file_types: list[str],
        name: str = "Search with Smart Search Pro",
    ) -> bool:
        """
        Add context menu for file types.

        Args:
            file_types: List of file extensions
            name: Context menu item name

        Returns:
            True if added successfully
        """
        if not self.shell_integration:
            logger.error("Shell integration not initialized (requires admin)")
            return False

        from shell_integration import ContextMenuItem

        item = ContextMenuItem(
            name=name,
            command=f'"{self.executable_path}" --search "%1"',
        )

        success = self.shell_integration.add_context_menu(
            item,
            file_types=file_types
        )

        if success:
            logger.info(f"Context menu added for: {', '.join(file_types)}")
        else:
            logger.error("Failed to add context menu")

        return success

    def remove_context_menu(
        self,
        file_types: list[str],
        name: str = "Search with Smart Search Pro",
    ) -> bool:
        """
        Remove context menu.

        Args:
            file_types: List of file extensions
            name: Context menu item name

        Returns:
            True if removed successfully
        """
        if not self.shell_integration:
            logger.error("Shell integration not initialized")
            return False

        success = self.shell_integration.remove_context_menu(
            name,
            file_types=file_types
        )

        if success:
            logger.info("Context menu removed")
        else:
            logger.error("Failed to remove context menu")

        return success

    # Signal handlers
    def _on_show_window(self) -> None:
        """Handle show window request."""
        logger.info("Show window requested")
        if self.main_window:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()

    def _on_hide_window(self) -> None:
        """Handle hide window request."""
        logger.info("Hide window requested")
        if self.main_window:
            self.main_window.hide()

    def _on_toggle_window(self) -> None:
        """Handle toggle window request."""
        if self.main_window:
            if self.main_window.isVisible():
                self._on_hide_window()
            else:
                self._on_show_window()

    def _on_quick_search(self, query: str = "") -> None:
        """Handle quick search request."""
        logger.info(f"Quick search requested: {query}")

        if query and self.tray_icon:
            self.tray_icon.add_recent_search(query)

        # Perform search...
        # self.search_engine.search(query)

    def _on_quick_search_hotkey(self) -> None:
        """Handle quick search hotkey."""
        if self.tray_icon:
            self.tray_icon.show_quick_search()

    def _on_exit(self) -> None:
        """Handle exit request."""
        logger.info("Exit requested")
        self.cleanup()
        if self.qt_app:
            self.qt_app.quit()
        sys.exit(0)

    def set_main_window(self, window) -> None:
        """
        Set the main window.

        Args:
            window: QMainWindow instance
        """
        self.main_window = window

        if self.instance_manager:
            # Set window handle for single instance
            try:
                hwnd = window.winId()
                self.instance_manager.set_window_handle(hwnd)
            except Exception as e:
                logger.error(f"Failed to set window handle: {e}")

    def run(self) -> int:
        """
        Run the application event loop.

        Returns:
            Exit code
        """
        if self.qt_app:
            logger.info("Starting Qt event loop")
            return self.qt_app.exec()
        else:
            logger.error("Qt application not initialized")
            return 1

    def cleanup(self) -> None:
        """Cleanup all system integration components."""
        logger.info("Cleaning up system integration...")

        if self.tray_icon:
            self.tray_icon.cleanup()

        if self.hotkey_manager:
            self.hotkey_manager.cleanup()

        if self.instance_manager:
            self.instance_manager.cleanup()

        logger.info("System integration cleaned up")


# Example usage
def main():
    """Example main function."""
    print("Smart Search Pro - System Integration Example")
    print("=" * 60)

    # Create integration
    integration = SmartSearchSystemIntegration(
        app_name="SmartSearchPro",
        executable_path=sys.executable,
    )

    # Initialize
    if not integration.initialize(use_tray=True):
        print("Another instance is running or initialization failed")
        return 1

    # Create a simple main window (if using PyQt6)
    try:
        from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton

        class MainWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("Smart Search Pro")
                self.setGeometry(100, 100, 800, 600)

                # Central widget
                central = QWidget()
                self.setCentralWidget(central)

                # Layout
                layout = QVBoxLayout(central)

                # Label
                label = QLabel("Smart Search Pro\n\nPress Ctrl+Shift+F for quick search")
                label.setStyleSheet("font-size: 16px; padding: 20px;")
                layout.addWidget(label)

                # Autostart button
                autostart_btn = QPushButton("Enable Autostart")
                autostart_btn.clicked.connect(integration.enable_autostart)
                layout.addWidget(autostart_btn)

                # Exit button
                exit_btn = QPushButton("Exit")
                exit_btn.clicked.connect(integration._on_exit)
                layout.addWidget(exit_btn)

        window = MainWindow()
        integration.set_main_window(window)
        window.show()

        print("\nApplication started!")
        print("Try:")
        print("  - Press Ctrl+Shift+F for quick search")
        print("  - Press Ctrl+Shift+S to show/hide window")
        print("  - Click system tray icon")
        print("  - Right-click tray icon for menu")

        return integration.run()

    except ImportError:
        print("PyQt6 not installed. Install with: pip install PyQt6")
        return 1


if __name__ == "__main__":
    sys.exit(main())
