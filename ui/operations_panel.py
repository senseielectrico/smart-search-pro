"""
Operations Panel - Complete integration with backend file operations manager
Fully functional with drag & drop, real-time progress, pause/resume/cancel
"""

from typing import Dict, List, Optional
from enum import Enum
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QFileDialog, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QDragLeaveEvent, QDragMoveEvent
from .widgets import ProgressCard, EmptyStateWidget, SpeedGraph
from .drag_drop import DragDropHandler, DropZoneWidget

# Import backend operations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from operations.manager import (
    OperationsManager, OperationType, OperationStatus as BackendStatus,
    OperationPriority
)
from operations.conflicts import ConflictAction


class OperationStatus(Enum):
    """UI Operation status (mirrors backend)"""
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OperationsPanel(QWidget, DropZoneWidget):
    """
    Fully functional file operations panel with backend integration.

    Features:
    - Drag & drop files to queue operations
    - Real-time progress tracking with speed graphs
    - Pause/Resume/Cancel operations
    - Copy/Move operations with verification
    - Operation history
    - Multi-file batch operations
    - Context menu on drop (copy/move choice)
    """

    # Signals
    operation_completed = pyqtSignal(str)  # operation ID
    operation_failed = pyqtSignal(str, str)  # operation ID, error
    files_dropped_signal = pyqtSignal(list)  # files dropped
    cancel_requested = pyqtSignal(str)  # operation ID to cancel
    pause_requested = pyqtSignal(str)  # operation ID to pause
    resume_requested = pyqtSignal(str)  # operation ID to resume

    def __init__(self, parent=None, operations_manager: Optional[OperationsManager] = None):
        super().__init__(parent)

        # Backend operations manager
        self.operations_manager = operations_manager
        if not self.operations_manager:
            # Create default manager
            history_file = Path.home() / ".smart_search" / "operations_history.json"
            history_file.parent.mkdir(parents=True, exist_ok=True)
            self.operations_manager = OperationsManager(
                max_concurrent_operations=2,
                history_file=str(history_file),
                auto_save_history=True
            )

        # UI state
        self.operation_widgets: Dict[str, ProgressCard] = {}
        self.selected_files: List[str] = []
        self.destination_folder: str = ""

        # Drag & Drop handler
        self.drag_handler = DragDropHandler(self)
        self.drag_handler.files_dropped.connect(self._on_files_dropped_to_panel)

        # Enable drag & drop with enhanced visual feedback
        self.setAcceptDrops(True)
        self._is_drag_hovering = False

        self._init_ui()
        self._start_update_timer()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header with controls
        header = QHBoxLayout()

        title = QLabel("File Operations")
        title.setProperty("heading", True)
        header.addWidget(title)

        header.addStretch()

        # Action buttons
        self.select_files_btn = QPushButton("Select Files")
        self.select_files_btn.setProperty("secondary", True)
        self.select_files_btn.clicked.connect(self._select_files)
        header.addWidget(self.select_files_btn)

        self.select_dest_btn = QPushButton("Select Destination")
        self.select_dest_btn.setProperty("secondary", True)
        self.select_dest_btn.clicked.connect(self._select_destination)
        header.addWidget(self.select_dest_btn)

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setProperty("primary", True)
        self.copy_btn.clicked.connect(self._queue_copy)
        self.copy_btn.setEnabled(False)
        header.addWidget(self.copy_btn)

        self.move_btn = QPushButton("Move")
        self.move_btn.setProperty("primary", True)
        self.move_btn.clicked.connect(self._queue_move)
        self.move_btn.setEnabled(False)
        header.addWidget(self.move_btn)

        clear_btn = QPushButton("Clear Completed")
        clear_btn.setProperty("secondary", True)
        clear_btn.clicked.connect(self._clear_completed)
        header.addWidget(clear_btn)

        layout.addLayout(header)

        # Selection info bar
        self.info_bar = QLabel("Drag & drop files here or use Select Files button")
        self.info_bar.setStyleSheet("""
            QLabel {
                background-color: #F3F3F3;
                border: 2px dashed #E1DFDD;
                border-radius: 6px;
                padding: 12px;
                color: #605E5C;
            }
        """)
        self.info_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_bar)

        # Speed graph
        self.speed_graph = SpeedGraph(max_points=50)
        self.speed_graph.setFixedHeight(80)
        layout.addWidget(self.speed_graph)

        # Operations scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.operations_widget = QWidget()
        self.operations_layout = QVBoxLayout(self.operations_widget)
        self.operations_layout.setSpacing(8)
        self.operations_layout.addStretch()

        scroll.setWidget(self.operations_widget)
        layout.addWidget(scroll)

        # Empty state
        self.empty_state = EmptyStateWidget(
            "📂",
            "No active operations",
            "Drag files here or click Select Files to start"
        )
        layout.addWidget(self.empty_state)

        self._update_empty_state()

    def _start_update_timer(self):
        """Start timer for real-time progress updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_operations)
        self.update_timer.start(500)  # Update every 500ms

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter - check if files and show visual feedback"""
        if self.drag_handler.handle_drag_enter(event, accept_files=True, accept_folders=True):
            self._is_drag_hovering = True
            self._apply_drag_hover_style()

            # Show operation hint based on modifiers
            modifiers = event.keyboardModifiers()
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                self.info_bar.setText("Drop to COPY files here")
            elif modifiers & Qt.KeyboardModifier.ShiftModifier:
                self.info_bar.setText("Drop to MOVE files here")
            else:
                self.info_bar.setText("Drop to add files (Ctrl=Copy, Shift=Move)")

    def dragMoveEvent(self, event: QDragMoveEvent):
        """Handle drag move - update cursor and hints"""
        if self.drag_handler.handle_drag_move(event):
            # Update hint based on modifiers
            modifiers = event.keyboardModifiers()
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                self.info_bar.setText("Drop to COPY files here")
            elif modifiers & Qt.KeyboardModifier.ShiftModifier:
                self.info_bar.setText("Drop to MOVE files here")
            else:
                self.info_bar.setText("Drop to add files (Ctrl=Copy, Shift=Move)")

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        """Handle drag leave - reset style"""
        self._is_drag_hovering = False
        self._reset_info_bar_style()

    def dropEvent(self, event: QDropEvent):
        """Handle file drop - show context menu or add to selection"""
        self._is_drag_hovering = False
        self._reset_info_bar_style()

        files = self.drag_handler.handle_drop(event, "operations_panel")

        if files:
            # Check if destination is set
            if self.destination_folder:
                # Show context menu to choose operation
                self._show_drop_context_menu(files, event.pos())
            else:
                # No destination - just add to selection
                self.selected_files.extend(files)
                self._update_selection_info()

    def _apply_drag_hover_style(self):
        """Apply hover style when dragging over"""
        self.info_bar.setStyleSheet("""
            QLabel {
                background-color: #E3F2FD;
                border: 2px dashed #0078D4;
                border-radius: 6px;
                padding: 12px;
                color: #0078D4;
                font-weight: 600;
            }
        """)

    def _show_drop_context_menu(self, files: List[str], pos):
        """Show context menu to choose copy or move operation"""
        menu = QMenu(self)

        # Copy action
        copy_action = menu.addAction(f"Copy {len(files)} file(s) to {Path(self.destination_folder).name}")
        copy_action.triggered.connect(lambda: self._quick_copy(files))

        # Move action
        move_action = menu.addAction(f"Move {len(files)} file(s) to {Path(self.destination_folder).name}")
        move_action.triggered.connect(lambda: self._quick_move(files))

        menu.addSeparator()

        # Add to selection action
        add_action = menu.addAction(f"Add {len(files)} file(s) to selection")
        add_action.triggered.connect(lambda: self._add_to_selection(files))

        # Show menu at drop position
        menu.exec(self.mapToGlobal(pos))

    def _quick_copy(self, files: List[str]):
        """Quick copy operation from dropped files"""
        if not self.destination_folder:
            return

        # Build destination paths
        dest_paths = []
        for source in files:
            filename = Path(source).name
            dest_path = str(Path(self.destination_folder) / filename)
            dest_paths.append(dest_path)

        # Queue operation
        operation_id = self.operations_manager.queue_copy(
            source_paths=files,
            dest_paths=dest_paths,
            priority=OperationPriority.NORMAL,
            verify=True,
            preserve_metadata=True,
            conflict_action=ConflictAction.ASK
        )

        # Create UI card
        title = f"Copy {len(files)} file(s) (from drag & drop)"
        self._add_operation_card(operation_id, title, len(files))

    def _quick_move(self, files: List[str]):
        """Quick move operation from dropped files"""
        if not self.destination_folder:
            return

        # Build destination paths
        dest_paths = []
        for source in files:
            filename = Path(source).name
            dest_path = str(Path(self.destination_folder) / filename)
            dest_paths.append(dest_path)

        # Queue operation
        operation_id = self.operations_manager.queue_move(
            source_paths=files,
            dest_paths=dest_paths,
            priority=OperationPriority.NORMAL,
            verify=True,
            preserve_metadata=True
        )

        # Create UI card
        title = f"Move {len(files)} file(s) (from drag & drop)"
        self._add_operation_card(operation_id, title, len(files))

    def _add_to_selection(self, files: List[str]):
        """Add files to selection"""
        self.selected_files.extend(files)
        self._update_selection_info()

    def _on_files_dropped_to_panel(self, files: List[str], zone: str):
        """Handle files dropped signal from drag handler"""
        if zone == "operations_panel":
            self.files_dropped_signal.emit(files)

    def _reset_info_bar_style(self):
        """Reset info bar to default style"""
        self.info_bar.setStyleSheet("""
            QLabel {
                background-color: #F3F3F3;
                border: 2px dashed #E1DFDD;
                border-radius: 6px;
                padding: 12px;
                color: #605E5C;
            }
        """)

    def _select_files(self):
        """Open file dialog to select files"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files to Copy/Move",
            "",
            "All Files (*.*)"
        )
        if files:
            self.selected_files.extend(files)
            self._update_selection_info()

    def _select_destination(self):
        """Open folder dialog to select destination"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Destination Folder"
        )
        if folder:
            self.destination_folder = folder
            self._update_selection_info()

    def _update_selection_info(self):
        """Update info bar with selection details"""
        num_files = len(self.selected_files)
        dest = self.destination_folder

        if num_files > 0 and dest:
            self.info_bar.setText(
                f"Selected {num_files} file(s) → {dest}"
            )
            self.copy_btn.setEnabled(True)
            self.move_btn.setEnabled(True)
        elif num_files > 0:
            self.info_bar.setText(
                f"Selected {num_files} file(s). Select destination to proceed."
            )
            self.copy_btn.setEnabled(False)
            self.move_btn.setEnabled(False)
        elif dest:
            self.info_bar.setText(
                f"Destination: {dest}. Select files to proceed."
            )
            self.copy_btn.setEnabled(False)
            self.move_btn.setEnabled(False)
        else:
            self.info_bar.setText("Drag & drop files here or use Select Files button")
            self.copy_btn.setEnabled(False)
            self.move_btn.setEnabled(False)

    def _queue_copy(self):
        """Queue copy operation"""
        if not self.selected_files or not self.destination_folder:
            return

        # Build destination paths
        dest_paths = []
        for source in self.selected_files:
            filename = Path(source).name
            dest_path = str(Path(self.destination_folder) / filename)
            dest_paths.append(dest_path)

        # Queue operation in backend
        operation_id = self.operations_manager.queue_copy(
            source_paths=self.selected_files,
            dest_paths=dest_paths,
            priority=OperationPriority.NORMAL,
            verify=True,  # Enable hash verification
            preserve_metadata=True,
            conflict_action=ConflictAction.ASK
        )

        # Create UI card
        title = f"Copy {len(self.selected_files)} file(s)"
        self._add_operation_card(operation_id, title, len(self.selected_files))

        # Clear selection
        self.selected_files.clear()
        self._update_selection_info()

    def _queue_move(self):
        """Queue move operation"""
        if not self.selected_files or not self.destination_folder:
            return

        # Build destination paths
        dest_paths = []
        for source in self.selected_files:
            filename = Path(source).name
            dest_path = str(Path(self.destination_folder) / filename)
            dest_paths.append(dest_path)

        # Queue operation in backend
        operation_id = self.operations_manager.queue_move(
            source_paths=self.selected_files,
            dest_paths=dest_paths,
            priority=OperationPriority.NORMAL,
            verify=True,
            preserve_metadata=True
        )

        # Create UI card
        title = f"Move {len(self.selected_files)} file(s)"
        self._add_operation_card(operation_id, title, len(self.selected_files))

        # Clear selection
        self.selected_files.clear()
        self._update_selection_info()

    def _add_operation_card(self, operation_id: str, title: str, total_files: int):
        """Add operation card to UI"""
        if operation_id in self.operation_widgets:
            return

        # Create progress card
        card = ProgressCard(title)
        card.cancel_clicked.connect(lambda: self._cancel_operation(operation_id))
        card.pause_clicked.connect(lambda: self._toggle_pause(operation_id))

        self.operation_widgets[operation_id] = card

        # Add to layout (before stretch)
        self.operations_layout.insertWidget(
            self.operations_layout.count() - 1,
            card
        )

        self._update_empty_state()

    def _update_operations(self):
        """Update all operations from backend (periodic)"""
        # Get all active operations
        active_operations = self.operations_manager.get_all_operations()

        for operation in active_operations:
            operation_id = operation.operation_id

            # Create card if doesn't exist
            if operation_id not in self.operation_widgets:
                op_type = operation.operation_type.value.title()
                title = f"{op_type} {operation.total_files} file(s)"
                self._add_operation_card(operation_id, title, operation.total_files)

            card = self.operation_widgets[operation_id]

            # Get progress from backend
            progress = self.operations_manager.get_progress(operation_id)

            if progress:
                # Update progress bar
                percent = int(progress.progress_percent)
                card.set_progress(percent)

                # Update speed
                speed_text = self._format_speed(progress.current_speed)
                card.set_speed(speed_text)

                # Add to speed graph (only for active operations)
                if operation.status == BackendStatus.IN_PROGRESS:
                    self.speed_graph.add_data_point(progress.current_speed)

                # Update status and details
                eta_text = self._format_time(progress.eta_seconds)
                files_text = f"{progress.completed_files}/{progress.total_files} files"

                if operation.status == BackendStatus.IN_PROGRESS:
                    card.set_status(f"In Progress - ETA: {eta_text}")
                    card.set_details(f"{files_text} - {self._format_size(progress.copied_size)} / {self._format_size(progress.total_size)}")
                elif operation.status == BackendStatus.PAUSED:
                    card.set_status("Paused")
                    card.set_paused(True)
                    card.set_details(f"{files_text} - {self._format_size(progress.copied_size)} / {self._format_size(progress.total_size)}")
                elif operation.status == BackendStatus.COMPLETED:
                    card.set_status("Completed ✓")
                    card.set_progress(100)
                    card.set_details(f"Completed {progress.completed_files} files in {self._format_time(progress.elapsed_time)}")
                    if progress.failed_files > 0:
                        card.set_details(f"Completed with {progress.failed_files} errors")
                elif operation.status == BackendStatus.FAILED:
                    card.set_status("Failed ✗")
                    if operation.error:
                        card.set_details(f"Error: {operation.error}")
                elif operation.status == BackendStatus.CANCELLED:
                    card.set_status("Cancelled")
                    card.set_details("Operation cancelled by user")
                elif operation.status == BackendStatus.QUEUED:
                    card.set_status("Queued...")
                    card.set_details("Waiting to start")

    def _toggle_pause(self, operation_id: str):
        """Toggle pause state for operation"""
        operation = self.operations_manager.get_operation(operation_id)
        if not operation:
            return

        if operation.status == BackendStatus.PAUSED:
            # Resume
            self.operations_manager.resume_operation(operation_id)
            if operation_id in self.operation_widgets:
                self.operation_widgets[operation_id].set_paused(False)
        elif operation.status == BackendStatus.IN_PROGRESS:
            # Pause
            self.operations_manager.pause_operation(operation_id)
            if operation_id in self.operation_widgets:
                self.operation_widgets[operation_id].set_paused(True)

    def _cancel_operation(self, operation_id: str):
        """Cancel operation"""
        # Confirm cancellation
        reply = QMessageBox.question(
            self,
            "Cancel Operation",
            "Are you sure you want to cancel this operation?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.operations_manager.cancel_operation(operation_id)

    def _clear_completed(self):
        """Clear completed operations"""
        # Get completed operation IDs
        to_remove = []
        for operation in self.operations_manager.get_all_operations():
            if operation.status in (
                BackendStatus.COMPLETED,
                BackendStatus.FAILED,
                BackendStatus.CANCELLED
            ):
                to_remove.append(operation.operation_id)

        # Remove from UI
        for op_id in to_remove:
            if op_id in self.operation_widgets:
                card = self.operation_widgets[op_id]
                self.operations_layout.removeWidget(card)
                card.deleteLater()
                del self.operation_widgets[op_id]

        # Clear from backend
        self.operations_manager.clear_completed()

        self._update_empty_state()

    def _update_empty_state(self):
        """Update empty state visibility"""
        has_operations = len(self.operation_widgets) > 0
        self.empty_state.setVisible(not has_operations)

    def _format_speed(self, bytes_per_sec: float) -> str:
        """Format transfer speed"""
        if bytes_per_sec < 1024:
            return f"{bytes_per_sec:.0f} B/s"
        elif bytes_per_sec < 1024 ** 2:
            return f"{bytes_per_sec / 1024:.1f} KB/s"
        elif bytes_per_sec < 1024 ** 3:
            return f"{bytes_per_sec / (1024 ** 2):.1f} MB/s"
        else:
            return f"{bytes_per_sec / (1024 ** 3):.2f} GB/s"

    def _format_size(self, size_bytes: int) -> str:
        """Format byte size"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.1f} MB"
        else:
            return f"{size_bytes / (1024 ** 3):.2f} GB"

    def _format_time(self, seconds: Optional[float]) -> str:
        """Format time duration"""
        if seconds is None or seconds < 0:
            return "Unknown"

        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

    def get_active_operations(self) -> List[str]:
        """Get list of active operation IDs"""
        return [
            op.operation_id for op in self.operations_manager.get_active_operations()
        ]

    def has_active_operations(self) -> bool:
        """Check if there are active operations"""
        return len(self.get_active_operations()) > 0

    def shutdown(self):
        """Shutdown operations manager"""
        if self.update_timer:
            self.update_timer.stop()
        if self.operations_manager:
            self.operations_manager.shutdown()

    def closeEvent(self, event):
        """Handle close event"""
        if self.has_active_operations():
            reply = QMessageBox.question(
                self,
                "Active Operations",
                "There are active operations. Are you sure you want to close?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        self.shutdown()
        event.accept()
