"""
Window menu management for Smart Search Pro.

Provides comprehensive window management actions including
create, duplicate, close, arrange, and switch operations.
"""

from typing import Optional

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QMenu

from core.logger import get_logger

logger = get_logger(__name__)


class WindowMenuManager(QObject):
    """
    Manages window menu with dynamic updates.

    Features:
    - New Window (Ctrl+N)
    - Duplicate Window (Ctrl+Shift+N)
    - Close Window (Ctrl+W)
    - Close All Windows (Ctrl+Shift+W)
    - Window List submenu
    - Arrange: Cascade, Tile Horizontal, Tile Vertical
    - Switch to Window 1-9 (Ctrl+1-9)
    """

    # Signals
    new_window_requested = pyqtSignal()
    duplicate_window_requested = pyqtSignal()
    close_window_requested = pyqtSignal()
    close_all_requested = pyqtSignal()
    cascade_requested = pyqtSignal()
    tile_horizontal_requested = pyqtSignal()
    tile_vertical_requested = pyqtSignal()
    switch_window_requested = pyqtSignal(str)  # window_id

    def __init__(self, window_manager, parent: Optional[QObject] = None):
        """
        Initialize window menu manager.

        Args:
            window_manager: WindowManager instance
            parent: Parent QObject
        """
        super().__init__(parent)
        self._window_manager = window_manager
        self._menu: Optional[QMenu] = None

        # Connect to window manager signals
        self._window_manager.windows_changed.connect(self._update_menu)

    def create_menu(self) -> QMenu:
        """
        Create window menu.

        Returns:
            QMenu instance
        """
        menu = QMenu("&Window")
        self._menu = menu

        # New window
        new_action = QAction("&New Window", menu)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.setStatusTip("Open a new search window")
        new_action.triggered.connect(self.new_window_requested.emit)
        menu.addAction(new_action)

        # Duplicate window
        duplicate_action = QAction("&Duplicate Window", menu)
        duplicate_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        duplicate_action.setStatusTip("Duplicate current window with same search")
        duplicate_action.triggered.connect(self.duplicate_window_requested.emit)
        menu.addAction(duplicate_action)

        menu.addSeparator()

        # Close window
        close_action = QAction("&Close Window", menu)
        close_action.setShortcut(QKeySequence("Ctrl+W"))
        close_action.setStatusTip("Close current window")
        close_action.triggered.connect(self.close_window_requested.emit)
        menu.addAction(close_action)

        # Close all windows
        close_all_action = QAction("Close &All Windows", menu)
        close_all_action.setShortcut(QKeySequence("Ctrl+Shift+W"))
        close_all_action.setStatusTip("Close all open windows")
        close_all_action.triggered.connect(self.close_all_requested.emit)
        menu.addAction(close_all_action)

        menu.addSeparator()

        # Arrange submenu
        arrange_menu = self._create_arrange_menu()
        menu.addMenu(arrange_menu)

        menu.addSeparator()

        # Window list (will be populated dynamically)
        self._window_list_separator = menu.addSeparator()

        # Initial update
        self._update_menu()

        return menu

    def _create_arrange_menu(self) -> QMenu:
        """
        Create arrange submenu.

        Returns:
            QMenu instance
        """
        menu = QMenu("&Arrange")

        # Cascade
        cascade_action = QAction("&Cascade", menu)
        cascade_action.setStatusTip("Arrange windows in cascade layout")
        cascade_action.triggered.connect(self.cascade_requested.emit)
        menu.addAction(cascade_action)

        # Tile horizontally
        tile_h_action = QAction("Tile &Horizontally", menu)
        tile_h_action.setStatusTip("Arrange windows side by side")
        tile_h_action.triggered.connect(self.tile_horizontal_requested.emit)
        menu.addAction(tile_h_action)

        # Tile vertically
        tile_v_action = QAction("Tile &Vertically", menu)
        tile_v_action.setStatusTip("Arrange windows stacked vertically")
        tile_v_action.triggered.connect(self.tile_vertical_requested.emit)
        menu.addAction(tile_v_action)

        menu.addSeparator()

        # Save layout
        save_action = QAction("&Save Layout", menu)
        save_action.setStatusTip("Save current window positions and sizes")
        save_action.triggered.connect(self._save_layout)
        menu.addAction(save_action)

        # Restore layout
        restore_action = QAction("&Restore Layout", menu)
        restore_action.setStatusTip("Restore saved window layout")
        restore_action.triggered.connect(self._restore_layout)
        menu.addAction(restore_action)

        return menu

    def _update_menu(self) -> None:
        """Update window list in menu."""
        if not self._menu:
            return

        # Remove existing window actions
        actions = self._menu.actions()
        separator_index = actions.index(self._window_list_separator)

        # Remove all actions after separator
        for action in actions[separator_index + 1:]:
            self._menu.removeAction(action)

        # Add window list
        windows = self._window_manager.get_all_windows()
        active_window = self._window_manager.get_active_window()

        for i, window in enumerate(windows, 1):
            window_id = getattr(window, 'window_id', str(i))
            title = self._get_window_title(window, i)

            action = QAction(title, self._menu)

            # Add shortcut for first 9 windows
            if i <= 9:
                action.setShortcut(QKeySequence(f"Ctrl+{i}"))

            # Check if active window
            if window == active_window:
                action.setCheckable(True)
                action.setChecked(True)

            # Connect to switch window
            action.triggered.connect(
                lambda checked, wid=window_id: self._switch_to_window(wid)
            )

            self._menu.addAction(action)

        logger.debug("Window menu updated", window_count=len(windows))

    def _get_window_title(self, window, index: int) -> str:
        """
        Get display title for window.

        Args:
            window: Window instance
            index: Window index

        Returns:
            Display title
        """
        # Try to get search query
        query = ""
        if hasattr(window, 'search_panel'):
            query = window.search_panel.search_input.text()

        if query:
            # Truncate long queries
            if len(query) > 30:
                query = query[:27] + "..."
            return f"&{index}. Search: {query}"
        else:
            return f"&{index}. Smart Search"

    def _switch_to_window(self, window_id: str) -> None:
        """
        Switch to specific window.

        Args:
            window_id: Window ID to switch to
        """
        self._window_manager.set_active_window(window_id)
        self.switch_window_requested.emit(window_id)

    def _save_layout(self) -> None:
        """Save current window layout."""
        self._window_manager.save_layout()

        logger.info("Window layout saved")

        # Show confirmation
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            None,
            "Layout Saved",
            f"Window layout saved successfully.\n"
            f"Windows: {self._window_manager.get_window_count()}"
        )

    def _restore_layout(self) -> None:
        """Restore saved window layout."""
        # Ask for confirmation if windows are open
        if self._window_manager.get_window_count() > 0:
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                None,
                "Restore Layout",
                "This will close all current windows and restore the saved layout.\n"
                "Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            # Close all windows
            self._window_manager.close_all_windows()

        # Restore layout
        self._window_manager.restore_layout()

        logger.info("Window layout restored")

    def get_menu(self) -> Optional[QMenu]:
        """
        Get menu instance.

        Returns:
            QMenu or None if not created
        """
        return self._menu


def create_window_menu(window_manager) -> WindowMenuManager:
    """
    Create window menu manager.

    Args:
        window_manager: WindowManager instance

    Returns:
        WindowMenuManager instance
    """
    menu_manager = WindowMenuManager(window_manager)
    menu_manager.create_menu()

    # Connect signals to window manager
    menu_manager.new_window_requested.connect(
        lambda: window_manager.create_window()
    )
    menu_manager.duplicate_window_requested.connect(
        window_manager._duplicate_current_window
    )
    menu_manager.close_window_requested.connect(
        window_manager._close_current_window
    )
    menu_manager.close_all_requested.connect(
        window_manager.close_all_windows
    )
    menu_manager.cascade_requested.connect(
        window_manager.arrange_cascade
    )
    menu_manager.tile_horizontal_requested.connect(
        window_manager.arrange_tile_horizontal
    )
    menu_manager.tile_vertical_requested.connect(
        window_manager.arrange_tile_vertical
    )

    return menu_manager
