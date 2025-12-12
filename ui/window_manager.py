"""
Multi-window manager for Smart Search Pro.

Manages multiple search windows with independent states,
synchronized settings, and proper resource sharing.
"""

import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtCore import QObject, QSettings, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QScreen
from PyQt6.QtWidgets import QApplication, QMenu

from core.logger import get_logger
from core.window_state import (
    WindowGeometry,
    WindowState,
    SearchState,
    get_window_state_manager
)

logger = get_logger(__name__)


class WindowManager(QObject):
    """
    Manages multiple application windows.

    Features:
    - Track all open windows
    - Create new search windows
    - Share data between windows (settings, favorites, history)
    - Independent search states per window
    - Window positioning and sizing
    - Save/restore window layouts
    - Close all windows
    - Focus management
    """

    # Signals
    window_created = pyqtSignal(object)  # New window created
    window_closed = pyqtSignal(str)  # Window closed (window_id)
    active_window_changed = pyqtSignal(str)  # Active window changed
    windows_changed = pyqtSignal()  # Window list changed

    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize window manager.

        Args:
            parent: Parent QObject
        """
        super().__init__(parent)

        self._windows: Dict[str, object] = {}  # window_id -> MainWindow
        self._active_window_id: Optional[str] = None
        self._state_manager = get_window_state_manager()
        self._settings = QSettings("SmartSearch", "WindowManager")

        # Shared resources
        self._shared_search_engine = None
        self._shared_database = None
        self._shared_cache = None

    def set_shared_resources(
        self,
        search_engine=None,
        database=None,
        cache=None
    ) -> None:
        """
        Set shared resources for all windows.

        Args:
            search_engine: Shared search engine instance
            database: Shared database instance
            cache: Shared cache instance
        """
        self._shared_search_engine = search_engine
        self._shared_database = database
        self._shared_cache = cache

        # Update existing windows
        for window in self._windows.values():
            if hasattr(window, 'set_search_engine') and search_engine:
                window.set_search_engine(search_engine)

        logger.debug("Shared resources updated for all windows")

    def create_window(
        self,
        window_id: Optional[str] = None,
        geometry: Optional[WindowGeometry] = None,
        search_state: Optional[SearchState] = None,
        is_primary: bool = False
    ) -> object:
        """
        Create a new search window.

        Args:
            window_id: Unique window ID (auto-generated if None)
            geometry: Initial window geometry
            search_state: Initial search state
            is_primary: Whether this is the primary window

        Returns:
            MainWindow instance
        """
        from .main_window import MainWindow

        # Generate window ID if not provided
        if window_id is None:
            window_id = str(uuid.uuid4())

        # Check if window already exists
        if window_id in self._windows:
            logger.warning("Window already exists", window_id=window_id)
            return self._windows[window_id]

        # Create window
        window = MainWindow()
        window.window_id = window_id
        window.is_primary = is_primary

        # Set shared resources
        if self._shared_search_engine:
            window.set_search_engine(self._shared_search_engine)

        # Apply geometry
        if geometry:
            self._apply_geometry(window, geometry)
        else:
            # Position based on existing windows
            self._position_new_window(window)

        # Apply search state
        if search_state:
            self._apply_search_state(window, search_state)

        # Track window
        self._windows[window_id] = window

        # Set as active if first window
        if len(self._windows) == 1:
            self._active_window_id = window_id

        # Connect signals
        window.destroyed.connect(lambda: self._on_window_closed(window_id))

        # Update window title
        self._update_window_title(window, window_id)

        # Show window
        window.show()

        # Emit signals
        self.window_created.emit(window)
        self.windows_changed.emit()

        logger.info(
            "Window created",
            window_id=window_id,
            total_windows=len(self._windows),
            is_primary=is_primary
        )

        return window

    def create_duplicate_window(self, source_window_id: str) -> Optional[object]:
        """
        Create a duplicate of an existing window.

        Args:
            source_window_id: ID of window to duplicate

        Returns:
            New MainWindow instance or None if source not found
        """
        source_window = self._windows.get(source_window_id)
        if not source_window:
            logger.warning("Source window not found", window_id=source_window_id)
            return None

        # Get current state from source
        geometry = self._get_window_geometry(source_window)
        search_state = self._get_search_state(source_window)

        # Offset position for new window
        geometry.x += 40
        geometry.y += 40

        # Create new window
        new_window = self.create_window(
            geometry=geometry,
            search_state=search_state,
            is_primary=False
        )

        logger.info(
            "Duplicate window created",
            source_id=source_window_id,
            new_id=new_window.window_id
        )

        return new_window

    def close_window(self, window_id: str) -> bool:
        """
        Close a specific window.

        Args:
            window_id: Window ID to close

        Returns:
            True if window was closed
        """
        window = self._windows.get(window_id)
        if not window:
            return False

        # Save state before closing
        self._save_window_state(window, window_id)

        # Close window
        window.close()

        return True

    def close_all_windows(self) -> None:
        """Close all windows."""
        logger.info("Closing all windows", count=len(self._windows))

        # Get window IDs (copy to avoid modification during iteration)
        window_ids = list(self._windows.keys())

        # Close each window
        for window_id in window_ids:
            self.close_window(window_id)

    def get_window(self, window_id: str) -> Optional[object]:
        """
        Get window by ID.

        Args:
            window_id: Window ID

        Returns:
            MainWindow instance or None
        """
        return self._windows.get(window_id)

    def get_all_windows(self) -> List[object]:
        """
        Get all open windows.

        Returns:
            List of MainWindow instances
        """
        return list(self._windows.values())

    def get_window_count(self) -> int:
        """
        Get number of open windows.

        Returns:
            Window count
        """
        return len(self._windows)

    def get_active_window(self) -> Optional[object]:
        """
        Get currently active window.

        Returns:
            Active MainWindow or None
        """
        if self._active_window_id:
            return self._windows.get(self._active_window_id)
        return None

    def set_active_window(self, window_id: str) -> None:
        """
        Set active window.

        Args:
            window_id: Window ID to activate
        """
        if window_id not in self._windows:
            return

        self._active_window_id = window_id
        self._state_manager.set_active_window(window_id)

        # Raise and activate window
        window = self._windows[window_id]
        window.raise_()
        window.activateWindow()

        self.active_window_changed.emit(window_id)

    def arrange_cascade(self) -> None:
        """Arrange windows in cascade layout."""
        logger.info("Arranging windows in cascade")

        self._state_manager.set_layout('cascade')

        for i, (window_id, window) in enumerate(self._windows.items()):
            x, y = self._state_manager.get_next_window_position(i)
            window.move(x, y)

    def arrange_tile_horizontal(self) -> None:
        """Arrange windows side by side."""
        logger.info("Arranging windows horizontally")

        if not self._windows:
            return

        self._state_manager.set_layout('tile_horizontal')

        # Get screen geometry
        screen = QApplication.primaryScreen().geometry()

        count = len(self._windows)
        width = screen.width() // count
        height = screen.height() - 100  # Leave space for taskbar

        for i, window in enumerate(self._windows.values()):
            window.setGeometry(
                i * width,
                50,
                width - 10,
                height
            )

    def arrange_tile_vertical(self) -> None:
        """Arrange windows stacked vertically."""
        logger.info("Arranging windows vertically")

        if not self._windows:
            return

        self._state_manager.set_layout('tile_vertical')

        # Get screen geometry
        screen = QApplication.primaryScreen().geometry()

        count = len(self._windows)
        width = screen.width() - 100
        height = (screen.height() - 100) // count

        for i, window in enumerate(self._windows.values()):
            window.setGeometry(
                50,
                i * height,
                width,
                height - 10
            )

    def save_layout(self) -> None:
        """Save current window layout."""
        logger.info("Saving window layout", window_count=len(self._windows))

        for window_id, window in self._windows.items():
            self._save_window_state(window, window_id)

        self._state_manager.save_state()

    def restore_layout(self) -> None:
        """Restore saved window layout."""
        logger.info("Restoring window layout")

        # Get saved window states
        saved_states = self._state_manager.get_all_windows()

        if not saved_states:
            logger.info("No saved layout found")
            return

        # Create windows from saved states
        for state in saved_states:
            self.create_window(
                window_id=state.window_id,
                geometry=state.geometry,
                search_state=state.search_state,
                is_primary=state.is_primary
            )

        # Restore active window
        active_id = self._state_manager.get_active_window_id()
        if active_id and active_id in self._windows:
            self.set_active_window(active_id)

    def create_window_menu(self) -> QMenu:
        """
        Create window menu for menu bar.

        Returns:
            QMenu with window management actions
        """
        menu = QMenu("&Window")

        # New window
        new_action = QAction("&New Window", menu)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(lambda: self.create_window())
        menu.addAction(new_action)

        # Duplicate window
        duplicate_action = QAction("&Duplicate Window", menu)
        duplicate_action.setShortcut("Ctrl+Shift+N")
        duplicate_action.triggered.connect(self._duplicate_current_window)
        menu.addAction(duplicate_action)

        menu.addSeparator()

        # Close window
        close_action = QAction("&Close Window", menu)
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self._close_current_window)
        menu.addAction(close_action)

        # Close all
        close_all_action = QAction("Close &All Windows", menu)
        close_all_action.setShortcut("Ctrl+Shift+W")
        close_all_action.triggered.connect(self.close_all_windows)
        menu.addAction(close_all_action)

        menu.addSeparator()

        # Arrange submenu
        arrange_menu = menu.addMenu("&Arrange")

        cascade_action = QAction("&Cascade", arrange_menu)
        cascade_action.triggered.connect(self.arrange_cascade)
        arrange_menu.addAction(cascade_action)

        tile_h_action = QAction("Tile &Horizontally", arrange_menu)
        tile_h_action.triggered.connect(self.arrange_tile_horizontal)
        arrange_menu.addAction(tile_h_action)

        tile_v_action = QAction("Tile &Vertically", arrange_menu)
        tile_v_action.triggered.connect(self.arrange_tile_vertical)
        arrange_menu.addAction(tile_v_action)

        menu.addSeparator()

        # Window list
        for i, (window_id, window) in enumerate(self._windows.items(), 1):
            if i <= 9:  # First 9 windows get number shortcuts
                title = f"&{i}. {self._get_window_display_name(window)}"
                action = QAction(title, menu)
                action.setShortcut(f"Ctrl+{i}")
                action.triggered.connect(
                    lambda checked, wid=window_id: self.set_active_window(wid)
                )
                menu.addAction(action)

        return menu

    def _position_new_window(self, window: object) -> None:
        """Position new window based on existing windows."""
        index = len(self._windows)
        x, y = self._state_manager.get_next_window_position(index)
        window.move(x, y)

    def _apply_geometry(self, window: object, geometry: WindowGeometry) -> None:
        """Apply geometry to window."""
        window.setGeometry(geometry.x, geometry.y, geometry.width, geometry.height)

        if geometry.is_maximized:
            window.showMaximized()
        elif geometry.is_minimized:
            window.showMinimized()

    def _apply_search_state(self, window: object, state: SearchState) -> None:
        """Apply search state to window."""
        # Set search query
        if hasattr(window, 'search_panel') and state.query:
            window.search_panel.search_input.setText(state.query)

        # Set directory paths
        if hasattr(window, 'directory_tree') and state.directory_paths:
            window.directory_tree.set_selected_paths(state.directory_paths)

        # Set filters
        if hasattr(window, 'search_panel') and state.filters:
            window.search_panel.set_filters(state.filters)

        # Set tab
        if hasattr(window, 'results_tabs') and state.selected_tab >= 0:
            window.results_tabs.setCurrentIndex(state.selected_tab)

    def _get_window_geometry(self, window: object) -> WindowGeometry:
        """Get current window geometry."""
        return WindowGeometry(
            x=window.x(),
            y=window.y(),
            width=window.width(),
            height=window.height(),
            is_maximized=window.isMaximized(),
            is_minimized=window.isMinimized()
        )

    def _get_search_state(self, window: object) -> SearchState:
        """Get current search state from window."""
        state = SearchState()

        if hasattr(window, 'search_panel'):
            state.query = window.search_panel.search_input.text()
            if hasattr(window.search_panel, 'get_filters'):
                state.filters = window.search_panel.get_filters()

        if hasattr(window, 'directory_tree'):
            if hasattr(window.directory_tree, 'get_selected_paths'):
                state.directory_paths = window.directory_tree.get_selected_paths()

        if hasattr(window, 'results_tabs'):
            state.selected_tab = window.results_tabs.currentIndex()

        return state

    def _save_window_state(self, window: object, window_id: str) -> None:
        """Save window state."""
        state = WindowState(
            window_id=window_id,
            geometry=self._get_window_geometry(window),
            search_state=self._get_search_state(window),
            is_primary=getattr(window, 'is_primary', False),
            created_at=getattr(window, '_created_at', time.time()),
            last_active=time.time()
        )

        self._state_manager.add_window(state)

    def _update_window_title(self, window: object, window_id: str) -> None:
        """Update window title with context."""
        base_title = "Smart Search Pro"

        if len(self._windows) > 1:
            index = list(self._windows.keys()).index(window_id) + 1
            window.setWindowTitle(f"{base_title} - Window {index}")
        else:
            window.setWindowTitle(base_title)

    def _get_window_display_name(self, window: object) -> str:
        """Get display name for window."""
        if hasattr(window, 'search_panel'):
            query = window.search_panel.search_input.text()
            if query:
                return f"Search: {query[:30]}"

        return "Smart Search"

    def _on_window_closed(self, window_id: str) -> None:
        """Handle window closed event."""
        if window_id in self._windows:
            window = self._windows[window_id]

            # Save state
            self._save_window_state(window, window_id)

            # Remove from tracking
            del self._windows[window_id]

            # Update active window
            if self._active_window_id == window_id:
                self._active_window_id = None
                if self._windows:
                    self._active_window_id = list(self._windows.keys())[0]

            # Emit signals
            self.window_closed.emit(window_id)
            self.windows_changed.emit()

            logger.info(
                "Window closed",
                window_id=window_id,
                remaining_windows=len(self._windows)
            )

            # Save state
            if len(self._windows) == 0:
                self._state_manager.save_state()

    def _duplicate_current_window(self) -> None:
        """Duplicate currently active window."""
        if self._active_window_id:
            self.create_duplicate_window(self._active_window_id)

    def _close_current_window(self) -> None:
        """Close currently active window."""
        if self._active_window_id:
            self.close_window(self._active_window_id)


# Global instance
_window_manager: Optional[WindowManager] = None


def get_window_manager() -> WindowManager:
    """
    Get global window manager instance.

    Returns:
        WindowManager instance
    """
    global _window_manager
    if _window_manager is None:
        _window_manager = WindowManager()
    return _window_manager
