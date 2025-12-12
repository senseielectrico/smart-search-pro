"""
Drag and Drop Module - Complete implementation for Smart Search Pro
Supports drag FROM results to external apps and drop TO the application.
Windows-specific implementation with Shell integration.
"""

import os
from pathlib import Path
from typing import List, Optional, Set
from enum import Enum

from PyQt6.QtCore import Qt, QMimeData, QUrl, pyqtSignal, QObject
from PyQt6.QtGui import (
    QDrag, QPixmap, QPainter, QColor, QPen, QCursor,
    QDragEnterEvent, QDragMoveEvent, QDragLeaveEvent, QDropEvent
)
from PyQt6.QtWidgets import QApplication


class DragOperation(Enum):
    """Drag operation types"""
    COPY = "copy"
    MOVE = "move"
    LINK = "link"


class DragState(Enum):
    """Drag state for visual feedback"""
    NONE = "none"
    HOVERING = "hovering"
    VALID_DROP = "valid_drop"
    INVALID_DROP = "invalid_drop"


class DragDropHandler(QObject):
    """
    Centralized drag and drop handler with Windows Shell integration.

    Features:
    - Multi-file drag FROM results panel
    - Drop TO application (search paths, operations)
    - Visual feedback with custom cursors
    - Keyboard modifiers: Ctrl=copy, Shift=move
    - Windows Shell integration for external drops
    """

    # Signals
    files_dropped = pyqtSignal(list, str)  # files, drop_zone
    drag_started = pyqtSignal(list)  # file_paths
    drag_completed = pyqtSignal(str)  # operation type

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_drag_paths: List[str] = []
        self.drag_operation = DragOperation.COPY

    # ==================== DRAG FROM APPLICATION ====================

    def create_drag(self, file_paths: List[str], source_widget) -> Optional[QDrag]:
        """
        Create drag object for dragging files FROM the application.

        Args:
            file_paths: List of file paths to drag
            source_widget: Widget initiating the drag

        Returns:
            QDrag object ready to execute, or None if invalid
        """
        if not file_paths:
            return None

        self.current_drag_paths = file_paths

        # Create drag object
        drag = QDrag(source_widget)

        # Create MIME data with file URLs
        mime_data = QMimeData()

        # Add URLs for file drops
        urls = [QUrl.fromLocalFile(path) for path in file_paths]
        mime_data.setUrls(urls)

        # Add text representation (paths)
        mime_data.setText('\n'.join(file_paths))

        # Add custom format with file list
        file_list = '\n'.join(file_paths).encode('utf-8')
        mime_data.setData('application/x-smart-search-files', file_list)

        drag.setMimeData(mime_data)

        # Create drag preview pixmap
        pixmap = self._create_drag_pixmap(file_paths)
        drag.setPixmap(pixmap)

        # Emit signal
        self.drag_started.emit(file_paths)

        return drag

    def execute_drag(self, drag: QDrag, default_action=Qt.DropAction.CopyAction) -> Qt.DropAction:
        """
        Execute drag operation with keyboard modifier support.

        Keyboard modifiers:
        - Ctrl: Force copy
        - Shift: Force move
        - Alt: Force link
        - None: Use default (copy)

        Returns:
            The drop action that was performed
        """
        if not drag:
            return Qt.DropAction.IgnoreAction

        # Determine allowed actions
        allowed_actions = (
            Qt.DropAction.CopyAction |
            Qt.DropAction.MoveAction |
            Qt.DropAction.LinkAction
        )

        # Check keyboard modifiers
        modifiers = QApplication.keyboardModifiers()

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            default_action = Qt.DropAction.CopyAction
            self.drag_operation = DragOperation.COPY
        elif modifiers & Qt.KeyboardModifier.ShiftModifier:
            default_action = Qt.DropAction.MoveAction
            self.drag_operation = DragOperation.MOVE
        elif modifiers & Qt.KeyboardModifier.AltModifier:
            default_action = Qt.DropAction.LinkAction
            self.drag_operation = DragOperation.LINK
        else:
            self.drag_operation = DragOperation.COPY

        # Execute drag
        result = drag.exec(allowed_actions, default_action)

        # Emit completion signal
        operation_name = self.drag_operation.value
        self.drag_completed.emit(operation_name)

        return result

    def _create_drag_pixmap(self, file_paths: List[str], max_width=300, max_height=100) -> QPixmap:
        """
        Create visual preview for dragged files.

        Shows file count and first few filenames.
        """
        num_files = len(file_paths)

        # Create pixmap
        pixmap = QPixmap(max_width, max_height)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background
        painter.setBrush(QColor(255, 255, 255, 230))
        painter.setPen(QPen(QColor(0, 120, 212), 2))
        painter.drawRoundedRect(2, 2, max_width - 4, max_height - 4, 8, 8)

        # Draw file icon and count
        painter.setPen(QColor(0, 0, 0))

        if num_files == 1:
            # Single file - show name
            filename = Path(file_paths[0]).name
            if len(filename) > 40:
                filename = filename[:37] + "..."

            painter.drawText(10, 30, f"📄 {filename}")
            painter.drawText(10, 50, f"Size: {self._format_file_size(file_paths[0])}")
        else:
            # Multiple files - show count and first few names
            painter.drawText(10, 30, f"📁 {num_files} files")

            # Show first 2 filenames
            y_pos = 50
            for i, path in enumerate(file_paths[:2]):
                if i >= 2:
                    break
                filename = Path(path).name
                if len(filename) > 35:
                    filename = filename[:32] + "..."
                painter.drawText(10, y_pos + (i * 20), f"  • {filename}")

            if num_files > 2:
                painter.drawText(10, y_pos + 40, f"  ... and {num_files - 2} more")

        painter.end()

        return pixmap

    def _format_file_size(self, file_path: str) -> str:
        """Format file size for display"""
        try:
            size = Path(file_path).stat().st_size
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} PB"
        except:
            return "Unknown"

    # ==================== DROP TO APPLICATION ====================

    def handle_drag_enter(self, event: QDragEnterEvent, accept_files=True, accept_folders=True) -> bool:
        """
        Handle drag enter event.

        Args:
            event: Drag enter event
            accept_files: Accept file drops
            accept_folders: Accept folder drops

        Returns:
            True if drag should be accepted
        """
        if not event.mimeData().hasUrls():
            event.ignore()
            return False

        # Check if URLs are valid files/folders
        urls = event.mimeData().urls()
        has_valid = False

        for url in urls:
            if not url.isLocalFile():
                continue

            path = Path(url.toLocalFile())

            if accept_files and path.is_file():
                has_valid = True
                break
            elif accept_folders and path.is_dir():
                has_valid = True
                break

        if has_valid:
            event.acceptProposedAction()
            return True
        else:
            event.ignore()
            return False

    def handle_drag_move(self, event: QDragMoveEvent) -> bool:
        """Handle drag move event (same as enter)"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return True
        event.ignore()
        return False

    def handle_drop(self, event: QDropEvent, zone: str = "default") -> List[str]:
        """
        Handle drop event and extract file paths.

        Args:
            event: Drop event
            zone: Identifier for the drop zone (for signal emission)

        Returns:
            List of dropped file paths
        """
        if not event.mimeData().hasUrls():
            event.ignore()
            return []

        # Extract file paths
        file_paths = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                file_paths.append(url.toLocalFile())

        if file_paths:
            event.acceptProposedAction()

            # Emit signal
            self.files_dropped.emit(file_paths, zone)

            return file_paths

        event.ignore()
        return []

    def get_drop_action_from_modifiers(self) -> Qt.DropAction:
        """
        Get drop action based on keyboard modifiers.

        Returns:
            Drop action matching current modifiers
        """
        modifiers = QApplication.keyboardModifiers()

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            return Qt.DropAction.CopyAction
        elif modifiers & Qt.KeyboardModifier.ShiftModifier:
            return Qt.DropAction.MoveAction
        elif modifiers & Qt.KeyboardModifier.AltModifier:
            return Qt.DropAction.LinkAction
        else:
            return Qt.DropAction.CopyAction

    def get_operation_cursor(self) -> QCursor:
        """
        Get cursor for current drag operation.

        Returns:
            Cursor matching the drag operation
        """
        modifiers = QApplication.keyboardModifiers()

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            # Copy cursor
            return QCursor(Qt.CursorShape.DragCopyCursor)
        elif modifiers & Qt.KeyboardModifier.ShiftModifier:
            # Move cursor
            return QCursor(Qt.CursorShape.DragMoveCursor)
        elif modifiers & Qt.KeyboardModifier.AltModifier:
            # Link cursor
            return QCursor(Qt.CursorShape.DragLinkCursor)
        else:
            # Default cursor
            return QCursor(Qt.CursorShape.DragCopyCursor)


class DropZoneWidget:
    """
    Mixin class for widgets that accept drops.

    Usage:
        class MyWidget(QWidget, DropZoneWidget):
            def __init__(self):
                super().__init__()
                self.setup_drop_zone("my_zone")
    """

    def setup_drop_zone(
        self,
        zone_name: str,
        handler: DragDropHandler,
        accept_files=True,
        accept_folders=True,
        hover_style: Optional[str] = None
    ):
        """
        Setup widget as drop zone.

        Args:
            zone_name: Identifier for this drop zone
            handler: DragDropHandler instance
            accept_files: Accept file drops
            accept_folders: Accept folder drops
            hover_style: CSS style to apply on hover
        """
        self.drop_zone_name = zone_name
        self.drop_handler = handler
        self.accept_files = accept_files
        self.accept_folders = accept_folders
        self.hover_style = hover_style or self._default_hover_style()
        self.original_style = ""

        # Enable drops
        self.setAcceptDrops(True)

        # Connect handler signals
        handler.files_dropped.connect(self._on_files_dropped)

    def _default_hover_style(self) -> str:
        """Default hover style for drop zones"""
        return """
            border: 2px dashed #0078D4;
            background-color: rgba(0, 120, 212, 0.1);
        """

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter"""
        if self.drop_handler.handle_drag_enter(event, self.accept_files, self.accept_folders):
            self._apply_hover_style()

    def dragMoveEvent(self, event: QDragMoveEvent):
        """Handle drag move"""
        self.drop_handler.handle_drag_move(event)

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        """Handle drag leave"""
        self._remove_hover_style()

    def dropEvent(self, event: QDropEvent):
        """Handle drop"""
        self._remove_hover_style()
        self.drop_handler.handle_drop(event, self.drop_zone_name)

    def _apply_hover_style(self):
        """Apply hover visual feedback"""
        if hasattr(self, 'styleSheet'):
            self.original_style = self.styleSheet()
            current = self.original_style or ""
            self.setStyleSheet(current + "\n" + self.hover_style)

    def _remove_hover_style(self):
        """Remove hover visual feedback"""
        if hasattr(self, 'styleSheet') and self.original_style:
            self.setStyleSheet(self.original_style)

    def _on_files_dropped(self, files: List[str], zone: str):
        """Handle files dropped (override in subclass)"""
        if zone == self.drop_zone_name:
            self.on_files_dropped(files)

    def on_files_dropped(self, files: List[str]):
        """Override this method to handle dropped files"""
        pass


class DragSource:
    """
    Mixin class for widgets that initiate drags.

    Usage:
        class MyWidget(QWidget, DragSource):
            def __init__(self):
                super().__init__()
                self.setup_drag_source(handler)
    """

    def setup_drag_source(self, handler: DragDropHandler):
        """
        Setup widget as drag source.

        Args:
            handler: DragDropHandler instance
        """
        self.drag_handler = handler

    def start_drag(self, file_paths: List[str]):
        """
        Initiate drag operation.

        Args:
            file_paths: Files to drag
        """
        if not file_paths:
            return

        # Create drag
        drag = self.drag_handler.create_drag(file_paths, self)

        if drag:
            # Execute drag with modifier support
            result = self.drag_handler.execute_drag(drag)

            # Handle result if needed
            if result == Qt.DropAction.MoveAction:
                # Files were moved - could update UI here
                pass
            elif result == Qt.DropAction.CopyAction:
                # Files were copied
                pass


# ==================== UTILITY FUNCTIONS ====================

def get_files_from_mime_data(mime_data: QMimeData) -> List[str]:
    """
    Extract file paths from MIME data.

    Args:
        mime_data: MIME data from drag/drop

    Returns:
        List of file paths
    """
    if not mime_data.hasUrls():
        return []

    files = []
    for url in mime_data.urls():
        if url.isLocalFile():
            files.append(url.toLocalFile())

    return files


def is_internal_drag(mime_data: QMimeData) -> bool:
    """
    Check if drag originated from within the application.

    Args:
        mime_data: MIME data from drag/drop

    Returns:
        True if internal drag
    """
    return mime_data.hasFormat('application/x-smart-search-files')


def create_file_shortcuts_for_clipboard(file_paths: List[str]):
    """
    Create Windows file shortcuts on clipboard for drag operations.
    This allows proper Windows Shell integration.

    Args:
        file_paths: List of file paths
    """
    try:
        import win32clipboard
        import win32con

        # Create file list in DROPFILES format
        files_str = '\0'.join(file_paths) + '\0\0'

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()

        # Set DROPFILES format
        win32clipboard.SetClipboardData(
            win32con.CF_HDROP,
            files_str.encode('utf-16le')
        )

        win32clipboard.CloseClipboard()
    except ImportError:
        # win32clipboard not available - skip Shell integration
        pass
    except Exception as e:
        # Error setting clipboard - continue without it
        pass
