"""
System Tray Icon implementation for Smart Search Pro.

Provides system tray functionality with context menu, notifications,
and quick access to search features.
"""

from typing import Optional, Callable, List, Dict, Any
import logging
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QSystemTrayIcon,
        QMenu,
        QWidget,
        QLineEdit,
        QVBoxLayout,
        QApplication,
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont
except ImportError:
    raise ImportError("PyQt6 is required. Install with: pip install PyQt6")

logger = logging.getLogger(__name__)


class QuickSearchPopup(QWidget):
    """Quick search popup window from system tray."""

    search_requested = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 50)

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Quick search... (Press Enter)")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #0078D4;
                border-radius: 5px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #005A9E;
            }
        """)
        self.search_input.returnPressed.connect(self._on_search)
        layout.addWidget(self.search_input)

    def _on_search(self) -> None:
        """Handle search request."""
        query = self.search_input.text().strip()
        if query:
            self.search_requested.emit(query)
            self.search_input.clear()
            self.hide()

    def showEvent(self, event) -> None:
        """Show event handler - position and focus."""
        super().showEvent(event)

        # Position at cursor or center of screen
        cursor_pos = QApplication.instance().desktop().cursor().pos()
        self.move(cursor_pos.x() - self.width() // 2, cursor_pos.y() - 50)

        self.search_input.setFocus()
        self.activateWindow()

    def hideEvent(self, event) -> None:
        """Hide event handler - clear input."""
        super().hideEvent(event)
        self.search_input.clear()


class SystemTrayIcon(QSystemTrayIcon):
    """
    System tray icon for Smart Search Pro.

    Features:
    - Context menu with quick actions
    - Recent searches submenu
    - Quick search popup
    - Show/hide main window
    - Notifications
    """

    # Signals
    show_main_window = pyqtSignal()
    hide_main_window = pyqtSignal()
    toggle_main_window = pyqtSignal()
    quick_search_requested = pyqtSignal(str)
    exit_requested = pyqtSignal()

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        icon_path: Optional[Path] = None,
    ):
        """
        Initialize system tray icon.

        Args:
            parent: Parent widget
            icon_path: Path to custom icon file
        """
        # Create or load icon
        if icon_path and icon_path.exists():
            icon = QIcon(str(icon_path))
        else:
            icon = self._create_default_icon()

        super().__init__(icon, parent)

        self.recent_searches: List[str] = []
        self.max_recent = 10
        self.quick_search_popup = QuickSearchPopup()
        self.quick_search_popup.search_requested.connect(
            self.quick_search_requested.emit
        )

        self._init_menu()
        self._setup_connections()

        logger.info("System tray icon initialized")

    def _create_default_icon(self) -> QIcon:
        """Create a default icon if none provided."""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw a search icon
        painter.setBrush(QColor("#0078D4"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(10, 10, 35, 35)

        painter.setBrush(QColor("white"))
        painter.drawEllipse(15, 15, 25, 25)

        painter.setBrush(QColor("#0078D4"))
        painter.drawRect(38, 38, 20, 8)

        painter.end()

        return QIcon(pixmap)

    def _init_menu(self) -> None:
        """Initialize the context menu."""
        self.menu = QMenu()

        # Quick Search action
        self.quick_search_action = QAction("Quick Search...", self)
        self.quick_search_action.triggered.connect(self.show_quick_search)
        self.menu.addAction(self.quick_search_action)

        self.menu.addSeparator()

        # Show/Hide main window
        self.show_action = QAction("Show Window", self)
        self.show_action.triggered.connect(self.show_main_window.emit)
        self.menu.addAction(self.show_action)

        self.hide_action = QAction("Hide Window", self)
        self.hide_action.triggered.connect(self.hide_main_window.emit)
        self.menu.addAction(self.hide_action)

        self.menu.addSeparator()

        # Recent searches submenu
        self.recent_menu = QMenu("Recent Searches", self.menu)
        self.menu.addMenu(self.recent_menu)
        self._update_recent_menu()

        self.menu.addSeparator()

        # Exit action
        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.exit_requested.emit)
        self.menu.addAction(self.exit_action)

        self.setContextMenu(self.menu)

    def _setup_connections(self) -> None:
        """Setup signal connections."""
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Left click - toggle main window
            self.toggle_main_window.emit()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # Double click - show quick search
            self.show_quick_search()
        elif reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            # Middle click - show quick search
            self.show_quick_search()

    def show_quick_search(self) -> None:
        """Show the quick search popup."""
        if self.quick_search_popup.isVisible():
            self.quick_search_popup.hide()
        else:
            self.quick_search_popup.show()
            self.quick_search_popup.raise_()
            self.quick_search_popup.activateWindow()

    def add_recent_search(self, query: str) -> None:
        """
        Add a search to recent searches.

        Args:
            query: Search query to add
        """
        # Remove if already exists
        if query in self.recent_searches:
            self.recent_searches.remove(query)

        # Add to front
        self.recent_searches.insert(0, query)

        # Trim to max
        if len(self.recent_searches) > self.max_recent:
            self.recent_searches = self.recent_searches[:self.max_recent]

        self._update_recent_menu()

    def _update_recent_menu(self) -> None:
        """Update the recent searches menu."""
        self.recent_menu.clear()

        if not self.recent_searches:
            action = QAction("No recent searches", self.recent_menu)
            action.setEnabled(False)
            self.recent_menu.addAction(action)
        else:
            for query in self.recent_searches:
                action = QAction(query, self.recent_menu)
                action.triggered.connect(
                    lambda checked, q=query: self.quick_search_requested.emit(q)
                )
                self.recent_menu.addAction(action)

            self.recent_menu.addSeparator()

            clear_action = QAction("Clear Recent", self.recent_menu)
            clear_action.triggered.connect(self.clear_recent_searches)
            self.recent_menu.addAction(clear_action)

    def clear_recent_searches(self) -> None:
        """Clear recent searches."""
        self.recent_searches.clear()
        self._update_recent_menu()

    def show_notification(
        self,
        title: str,
        message: str,
        icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
        duration: int = 3000,
    ) -> None:
        """
        Show a system notification.

        Args:
            title: Notification title
            message: Notification message
            icon: Icon type
            duration: Duration in milliseconds
        """
        self.showMessage(title, message, icon, duration)

    def set_tooltip(self, text: str) -> None:
        """
        Set the tray icon tooltip.

        Args:
            text: Tooltip text
        """
        self.setToolTip(text)

    def update_icon(self, icon_path: Path) -> None:
        """
        Update the tray icon.

        Args:
            icon_path: Path to new icon file
        """
        if icon_path.exists():
            self.setIcon(QIcon(str(icon_path)))
        else:
            logger.warning(f"Icon file not found: {icon_path}")

    def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            self.quick_search_popup.close()
            self.hide()
            logger.info("System tray icon cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up tray icon: {e}")


# Example usage
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray = SystemTrayIcon()
    tray.show()

    tray.show_main_window.connect(lambda: print("Show main window"))
    tray.hide_main_window.connect(lambda: print("Hide main window"))
    tray.quick_search_requested.connect(lambda q: print(f"Search: {q}"))
    tray.exit_requested.connect(app.quit)

    tray.add_recent_search("test query 1")
    tray.add_recent_search("test query 2")

    tray.show_notification("Smart Search Pro", "Application started")

    sys.exit(app.exec())
