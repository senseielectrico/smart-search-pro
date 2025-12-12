"""
Tab-based window manager for Smart Search Pro.

Provides tab-based interface as an alternative to multiple windows,
with ability to detach tabs to windows and merge windows into tabs.
"""

from typing import Dict, List, Optional

from PyQt6.QtCore import QMimeData, QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QDrag
from PyQt6.QtWidgets import (
    QTabBar,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QMenu,
    QApplication
)

from core.logger import get_logger

logger = get_logger(__name__)


class DraggableTabBar(QTabBar):
    """
    Custom tab bar with drag-and-drop support.

    Features:
    - Drag tabs to reorder
    - Drag tab out to create window
    - Drop tab from other windows to merge
    """

    # Signals
    tab_detach_requested = pyqtSignal(int, QPoint)  # index, global_pos
    tab_move_requested = pyqtSignal(int, int)  # from_index, to_index

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize draggable tab bar."""
        super().__init__(parent)

        self.setAcceptDrops(True)
        self.setElideMode(Qt.TextElideMode.ElideRight)
        self.setSelectionBehaviorOnRemove(
            QTabBar.SelectionBehavior.SelectLeftTab
        )

        self._drag_start_pos: Optional[QPoint] = None
        self._dragging = False

    def mousePressEvent(self, event):
        """Handle mouse press for drag initiation."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self._dragging = False

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        if self._drag_start_pos is None:
            return

        # Check if drag threshold exceeded
        if not self._dragging:
            distance = (event.pos() - self._drag_start_pos).manhattanLength()
            if distance < QApplication.startDragDistance():
                return

        self._dragging = True

        # Check if dragging outside tab bar (to detach)
        if not self.rect().contains(event.pos()):
            index = self.tabAt(self._drag_start_pos)
            if index >= 0:
                # Emit detach signal with global position
                global_pos = self.mapToGlobal(event.pos())
                self.tab_detach_requested.emit(index, global_pos)
                self._dragging = False
                self._drag_start_pos = None
                return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        self._dragging = False
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)


class SearchTabWidget(QTabWidget):
    """
    Tab widget for search tabs.

    Features:
    - Multiple search tabs in single window
    - Context menu on tabs
    - Close button on tabs
    - New tab button
    - Drag to reorder
    - Drag out to detach
    """

    # Signals
    new_tab_requested = pyqtSignal()
    tab_detached = pyqtSignal(int, QPoint)  # index, position
    close_tab_requested = pyqtSignal(int)  # index

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize search tab widget."""
        super().__init__(parent)

        # Use custom draggable tab bar
        self._tab_bar = DraggableTabBar(self)
        self.setTabBar(self._tab_bar)

        # Configure tab widget
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        self.setElideMode(Qt.TextElideMode.ElideRight)

        # Connect signals
        self.tabCloseRequested.connect(self._on_close_requested)
        self._tab_bar.tab_detach_requested.connect(self._on_detach_requested)

        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _on_close_requested(self, index: int) -> None:
        """Handle tab close request."""
        # Don't close if it's the last tab
        if self.count() <= 1:
            logger.debug("Cannot close last tab")
            return

        self.close_tab_requested.emit(index)

    def _on_detach_requested(self, index: int, global_pos: QPoint) -> None:
        """Handle tab detach request."""
        # Don't detach if it's the only tab
        if self.count() <= 1:
            logger.debug("Cannot detach last tab")
            return

        self.tab_detached.emit(index, global_pos)

    def _show_context_menu(self, pos: QPoint) -> None:
        """Show context menu on tab."""
        # Get tab index at position
        index = self.tabBar().tabAt(pos)
        if index < 0:
            return

        # Create context menu
        menu = QMenu(self)

        # Close tab
        close_action = menu.addAction("Close Tab")
        close_action.setEnabled(self.count() > 1)
        close_action.triggered.connect(lambda: self._on_close_requested(index))

        # Close other tabs
        close_others_action = menu.addAction("Close Other Tabs")
        close_others_action.setEnabled(self.count() > 1)
        close_others_action.triggered.connect(
            lambda: self._close_other_tabs(index)
        )

        # Close tabs to right
        close_right_action = menu.addAction("Close Tabs to Right")
        close_right_action.setEnabled(index < self.count() - 1)
        close_right_action.triggered.connect(
            lambda: self._close_tabs_to_right(index)
        )

        menu.addSeparator()

        # Detach to window
        detach_action = menu.addAction("Detach to New Window")
        detach_action.setEnabled(self.count() > 1)
        detach_action.triggered.connect(
            lambda: self.tab_detached.emit(index, self.mapToGlobal(pos))
        )

        menu.addSeparator()

        # New tab
        new_tab_action = menu.addAction("New Tab")
        new_tab_action.triggered.connect(self.new_tab_requested.emit)

        # Show menu
        menu.exec(self.tabBar().mapToGlobal(pos))

    def _close_other_tabs(self, keep_index: int) -> None:
        """Close all tabs except the specified one."""
        # Close tabs in reverse to maintain indices
        for i in range(self.count() - 1, -1, -1):
            if i != keep_index:
                self.close_tab_requested.emit(i)

    def _close_tabs_to_right(self, index: int) -> None:
        """Close all tabs to the right of specified index."""
        for i in range(self.count() - 1, index, -1):
            self.close_tab_requested.emit(i)


class TabManager:
    """
    Manages search tabs within a window.

    Features:
    - Create new search tabs
    - Close tabs
    - Detach tabs to new windows
    - Merge window tabs
    - Save/restore tab states
    """

    def __init__(self, tab_widget: SearchTabWidget):
        """
        Initialize tab manager.

        Args:
            tab_widget: SearchTabWidget instance
        """
        self._tab_widget = tab_widget
        self._tabs: Dict[int, Dict] = {}  # index -> tab_data

        # Connect signals
        self._tab_widget.new_tab_requested.connect(self.create_tab)
        self._tab_widget.close_tab_requested.connect(self.close_tab)
        self._tab_widget.tab_detached.connect(self._on_tab_detached)

        logger.debug("Tab manager initialized")

    def create_tab(
        self,
        title: str = "New Search",
        widget: Optional[QWidget] = None
    ) -> int:
        """
        Create a new search tab.

        Args:
            title: Tab title
            widget: Widget to add (creates default if None)

        Returns:
            Tab index
        """
        if widget is None:
            # Create default search widget
            widget = self._create_search_widget()

        # Add tab
        index = self._tab_widget.addTab(widget, title)

        # Store tab data
        self._tabs[index] = {
            'title': title,
            'widget': widget,
            'created_at': __import__('time').time()
        }

        # Switch to new tab
        self._tab_widget.setCurrentIndex(index)

        logger.info("Tab created", index=index, title=title)

        return index

    def close_tab(self, index: int) -> bool:
        """
        Close tab at index.

        Args:
            index: Tab index to close

        Returns:
            True if tab was closed
        """
        if index < 0 or index >= self._tab_widget.count():
            return False

        # Don't close last tab
        if self._tab_widget.count() <= 1:
            logger.debug("Cannot close last tab")
            return False

        # Remove tab
        widget = self._tab_widget.widget(index)
        self._tab_widget.removeTab(index)

        # Clean up widget
        if widget:
            widget.deleteLater()

        # Remove from tracking
        if index in self._tabs:
            del self._tabs[index]

        # Reindex remaining tabs
        self._reindex_tabs()

        logger.info("Tab closed", index=index)

        return True

    def detach_tab(self, index: int, position: QPoint) -> Optional[QWidget]:
        """
        Detach tab to create new window.

        Args:
            index: Tab index to detach
            position: Window position

        Returns:
            Detached widget or None
        """
        if index < 0 or index >= self._tab_widget.count():
            return None

        # Don't detach last tab
        if self._tab_widget.count() <= 1:
            logger.debug("Cannot detach last tab")
            return None

        # Get widget
        widget = self._tab_widget.widget(index)
        title = self._tab_widget.tabText(index)

        # Remove from tab widget (but don't delete)
        self._tab_widget.removeTab(index)

        # Remove from tracking
        if index in self._tabs:
            del self._tabs[index]

        # Reindex
        self._reindex_tabs()

        logger.info("Tab detached", index=index, title=title)

        return widget

    def get_tab_count(self) -> int:
        """
        Get number of tabs.

        Returns:
            Tab count
        """
        return self._tab_widget.count()

    def get_current_index(self) -> int:
        """
        Get current tab index.

        Returns:
            Current index
        """
        return self._tab_widget.currentIndex()

    def set_current_index(self, index: int) -> None:
        """
        Set current tab.

        Args:
            index: Tab index to activate
        """
        if 0 <= index < self._tab_widget.count():
            self._tab_widget.setCurrentIndex(index)

    def _create_search_widget(self) -> QWidget:
        """
        Create default search widget for tab.

        Returns:
            QWidget instance
        """
        # Create simple placeholder widget
        # In real implementation, this would create a full search panel
        widget = QWidget()
        layout = QVBoxLayout(widget)

        from PyQt6.QtWidgets import QLabel
        label = QLabel("Search Tab - Not yet implemented")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        return widget

    def _on_tab_detached(self, index: int, position: QPoint) -> None:
        """
        Handle tab detach event.

        Args:
            index: Tab index
            position: Global position for new window
        """
        widget = self.detach_tab(index, position)

        if widget:
            # Create new window with detached widget
            from .window_manager import get_window_manager
            window_manager = get_window_manager()

            # Create new window at position
            new_window = window_manager.create_window()
            if new_window:
                new_window.move(position)

                logger.info("New window created from detached tab")

    def _reindex_tabs(self) -> None:
        """Reindex tabs after removal."""
        old_tabs = self._tabs.copy()
        self._tabs.clear()

        for new_index in range(self._tab_widget.count()):
            # Find corresponding old tab
            widget = self._tab_widget.widget(new_index)
            for old_index, data in old_tabs.items():
                if data['widget'] == widget:
                    self._tabs[new_index] = data
                    break


def create_tab_widget() -> SearchTabWidget:
    """
    Create configured search tab widget.

    Returns:
        SearchTabWidget instance
    """
    tab_widget = SearchTabWidget()

    logger.debug("Search tab widget created")

    return tab_widget
