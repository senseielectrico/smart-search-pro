"""
Example of integrating file operations with the UI panel.
Shows how to connect the operations backend with the Qt UI.
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog
from PyQt6.QtCore import QThread, pyqtSignal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from operations.manager import OperationsManager, OperationPriority
from operations.progress import OperationProgress
from ui.operations_panel import OperationsPanel


class OperationsWorker(QThread):
    """Worker thread to monitor operations progress."""

    progress_updated = pyqtSignal(str, int, str, float)  # op_id, progress, file, speed
    operation_completed = pyqtSignal(str)  # op_id

    def __init__(self, manager: OperationsManager):
        super().__init__()
        self.manager = manager
        self.running = True

    def run(self):
        """Monitor operations and emit progress updates."""
        while self.running:
            # Get all active operations
            active_ops = self.manager.get_active_operations()

            for operation in active_ops:
                # Get progress
                progress = self.manager.get_progress(operation.operation_id)

                if progress:
                    # Calculate overall progress
                    overall_percent = int(progress.progress_percent)

                    # Get current file
                    current_file = ""
                    for file_path, file_progress in progress.files.items():
                        if file_progress.end_time is None:
                            current_file = Path(file_path).name
                            break

                    # Emit progress update
                    self.progress_updated.emit(
                        operation.operation_id,
                        overall_percent,
                        current_file,
                        progress.current_speed
                    )

                # Check if completed
                if operation.status.value in ['completed', 'failed', 'cancelled']:
                    self.operation_completed.emit(operation.operation_id)

            # Sleep briefly
            self.msleep(100)

    def stop(self):
        """Stop the worker thread."""
        self.running = False


class MainWindow(QMainWindow):
    """Main window demonstrating operations integration."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Operations - Integration Example")
        self.setGeometry(100, 100, 800, 600)

        # Create operations manager
        self.manager = OperationsManager(
            max_concurrent_operations=2,
            history_file="operations_history.json"
        )

        # Create UI
        self._init_ui()

        # Start worker thread
        self.worker = OperationsWorker(self.manager)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.operation_completed.connect(self._on_operation_completed)
        self.worker.start()

    def _init_ui(self):
        """Initialize UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Add operations panel
        self.operations_panel = OperationsPanel()
        layout.addWidget(self.operations_panel)

        # Connect signals
        self.operations_panel.cancel_requested.connect(self._on_cancel_requested)
        self.operations_panel.pause_requested.connect(self._on_pause_requested)
        self.operations_panel.resume_requested.connect(self._on_resume_requested)

        # Add control buttons
        btn_layout = QVBoxLayout()

        # Copy files button
        btn_copy = QPushButton("Copy Files...")
        btn_copy.clicked.connect(self._on_copy_files)
        btn_layout.addWidget(btn_copy)

        # Move files button
        btn_move = QPushButton("Move Files...")
        btn_move.clicked.connect(self._on_move_files)
        btn_layout.addWidget(btn_move)

        layout.addLayout(btn_layout)

    def _on_copy_files(self):
        """Handle copy files button."""
        # Select source files
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select files to copy",
            "",
            "All Files (*.*)"
        )

        if not files:
            return

        # Select destination directory
        dest_dir = QFileDialog.getExistingDirectory(
            self,
            "Select destination directory"
        )

        if not dest_dir:
            return

        # Build file pairs
        dest_paths = [
            str(Path(dest_dir) / Path(src).name)
            for src in files
        ]

        # Queue copy operation
        op_id = self.manager.queue_copy(
            source_paths=files,
            dest_paths=dest_paths,
            priority=OperationPriority.NORMAL,
            verify=True
        )

        # Add to UI
        self.operations_panel.add_operation(
            operation_id=op_id,
            title=f"Copying {len(files)} file(s)",
            total_files=len(files)
        )

    def _on_move_files(self):
        """Handle move files button."""
        # Select source files
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select files to move",
            "",
            "All Files (*.*)"
        )

        if not files:
            return

        # Select destination directory
        dest_dir = QFileDialog.getExistingDirectory(
            self,
            "Select destination directory"
        )

        if not dest_dir:
            return

        # Build file pairs
        dest_paths = [
            str(Path(dest_dir) / Path(src).name)
            for src in files
        ]

        # Queue move operation
        op_id = self.manager.queue_move(
            source_paths=files,
            dest_paths=dest_paths,
            priority=OperationPriority.NORMAL,
            verify=True
        )

        # Add to UI
        self.operations_panel.add_operation(
            operation_id=op_id,
            title=f"Moving {len(files)} file(s)",
            total_files=len(files)
        )

    def _on_progress_updated(self, op_id: str, progress: int, current_file: str, speed: float):
        """Handle progress update from worker."""
        self.operations_panel.update_operation(
            operation_id=op_id,
            progress=progress,
            current_file=current_file,
            speed=speed
        )

    def _on_operation_completed(self, op_id: str):
        """Handle operation completion."""
        operation = self.manager.get_operation(op_id)
        if operation:
            self.operations_panel.set_operation_status(
                operation_id=op_id,
                status=operation.status
            )

    def _on_cancel_requested(self, op_id: str):
        """Handle cancel request from UI."""
        self.manager.cancel_operation(op_id)

    def _on_pause_requested(self, op_id: str):
        """Handle pause request from UI."""
        self.manager.pause_operation(op_id)

    def _on_resume_requested(self, op_id: str):
        """Handle resume request from UI."""
        self.manager.resume_operation(op_id)

    def closeEvent(self, event):
        """Handle window close."""
        # Stop worker
        self.worker.stop()
        self.worker.wait()

        # Shutdown manager
        self.manager.shutdown()

        event.accept()


def main():
    """Run the example application."""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
