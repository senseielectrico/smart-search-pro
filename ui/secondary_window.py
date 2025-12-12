"""
Secondary search window for Smart Search Pro.

Provides full search functionality in an independent window
with optional mini/compact mode.
"""

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from .main_window import MainWindow
from core.logger import get_logger

logger = get_logger(__name__)


class SecondaryWindow(MainWindow):
    """
    Secondary search window with independent state.

    Features:
    - Full search functionality
    - Independent search query and results
    - Can have different directory scope
    - Shared favorites and history
    - Window title shows search context
    - Optional mini mode (compact view)
    """

    # Additional signals
    mini_mode_toggled = pyqtSignal(bool)

    def __init__(self, window_id: Optional[str] = None, mini_mode: bool = False):
        """
        Initialize secondary window.

        Args:
            window_id: Unique window identifier
            mini_mode: Start in compact/mini mode
        """
        super().__init__()

        self.window_id = window_id or f"secondary_{id(self)}"
        self._mini_mode = mini_mode
        self.is_primary = False

        if mini_mode:
            self._apply_mini_mode()

        self._setup_secondary_ui()

        logger.info(
            "Secondary window created",
            window_id=self.window_id,
            mini_mode=mini_mode
        )

    def _setup_secondary_ui(self) -> None:
        """Setup UI specific to secondary windows."""
        # Update window title
        self.setWindowTitle(f"Smart Search Pro - {self.window_id}")

        # Add mini mode toggle to view menu
        self._add_mini_mode_toggle()

        # Update status bar
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"Secondary Window - Ready")

    def _add_mini_mode_toggle(self) -> None:
        """Add mini mode toggle to view menu."""
        try:
            # Find view menu
            menubar = self.menuBar()
            for action in menubar.actions():
                if action.text() == "&View":
                    view_menu = action.menu()
                    if view_menu:
                        view_menu.addSeparator()

                        # Add mini mode action
                        from PyQt6.QtGui import QAction
                        mini_action = QAction("&Mini Mode", self)
                        mini_action.setCheckable(True)
                        mini_action.setChecked(self._mini_mode)
                        mini_action.triggered.connect(self.toggle_mini_mode)
                        view_menu.addAction(mini_action)
                        break
        except Exception as e:
            logger.warning("Failed to add mini mode toggle", error=str(e))

    def toggle_mini_mode(self, enabled: bool = None) -> None:
        """
        Toggle mini/compact mode.

        Args:
            enabled: Force enable/disable, or toggle if None
        """
        if enabled is None:
            enabled = not self._mini_mode

        self._mini_mode = enabled

        if enabled:
            self._apply_mini_mode()
        else:
            self._apply_normal_mode()

        self.mini_mode_toggled.emit(enabled)

        logger.info(
            "Mini mode toggled",
            window_id=self.window_id,
            enabled=enabled
        )

    def _apply_mini_mode(self) -> None:
        """Apply mini/compact mode layout."""
        # Hide panels to save space
        if hasattr(self, 'directory_tree'):
            self.directory_tree.hide()
            if hasattr(self, 'toggle_tree_action'):
                self.toggle_tree_action.setChecked(False)

        if hasattr(self, 'preview_panel'):
            self.preview_panel.hide()
            if hasattr(self, 'toggle_preview_action'):
                self.toggle_preview_action.setChecked(False)

        # Reduce window size
        self.resize(800, 500)

        # Update window flags for always-on-top option
        # Note: This is optional, can be made configurable
        # self.setWindowFlags(
        #     self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
        # )

        logger.debug("Mini mode applied", window_id=self.window_id)

    def _apply_normal_mode(self) -> None:
        """Apply normal mode layout."""
        # Show panels
        if hasattr(self, 'directory_tree'):
            self.directory_tree.show()
            if hasattr(self, 'toggle_tree_action'):
                self.toggle_tree_action.setChecked(True)

        if hasattr(self, 'preview_panel'):
            self.preview_panel.show()
            if hasattr(self, 'toggle_preview_action'):
                self.toggle_preview_action.setChecked(True)

        # Restore normal size
        self.resize(1200, 700)

        logger.debug("Normal mode applied", window_id=self.window_id)

    def set_search_context(self, context: str) -> None:
        """
        Set search context displayed in title.

        Args:
            context: Context description (e.g., directory, query)
        """
        self.setWindowTitle(f"Smart Search Pro - {context}")

    def get_mini_mode(self) -> bool:
        """
        Check if window is in mini mode.

        Returns:
            True if in mini mode
        """
        return self._mini_mode

    def closeEvent(self, event):
        """Handle window close event."""
        logger.info("Secondary window closing", window_id=self.window_id)

        # Call parent close event
        super().closeEvent(event)


def create_secondary_window(
    window_id: Optional[str] = None,
    mini_mode: bool = False,
    search_query: Optional[str] = None,
    directory_path: Optional[str] = None
) -> SecondaryWindow:
    """
    Create and configure a secondary search window.

    Args:
        window_id: Unique window identifier
        mini_mode: Start in compact mode
        search_query: Initial search query
        directory_path: Initial directory to search

    Returns:
        SecondaryWindow instance
    """
    window = SecondaryWindow(window_id=window_id, mini_mode=mini_mode)

    # Set initial search query
    if search_query and hasattr(window, 'search_panel'):
        window.search_panel.search_input.setText(search_query)

    # Set initial directory
    if directory_path and hasattr(window, 'directory_tree'):
        if hasattr(window.directory_tree, 'set_selected_paths'):
            window.directory_tree.set_selected_paths([directory_path])

    # Update context in title
    if search_query or directory_path:
        context_parts = []
        if search_query:
            context_parts.append(f"'{search_query}'")
        if directory_path:
            from pathlib import Path
            context_parts.append(f"in {Path(directory_path).name}")
        window.set_search_context(" ".join(context_parts))

    return window
