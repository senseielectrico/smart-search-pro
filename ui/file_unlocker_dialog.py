"""
File Unlocker Dialog - PyQt6 UI for FileUnlocker

Features:
- File/folder selector
- Show locking processes list
- Unlock button with confirmation
- Force unlock checkbox
- Kill process option
- Progress and status log
- Batch unlock multiple files

Security Warning:
This dialog provides access to powerful system operations.
Use with caution and only on files you own.
"""

import os
import sys
from typing import List, Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QCheckBox,
    QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox,
    QProgressBar, QGroupBox, QHeaderView, QListWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor

import logging

# Import the file unlocker
import sys
from pathlib import Path
tools_path = Path(__file__).parent.parent / 'tools'
sys.path.insert(0, str(tools_path))

from file_unlocker import FileUnlocker, LockingProcess

logger = logging.getLogger(__name__)


class UnlockWorker(QThread):
    """Background worker for unlock operations"""

    progress = pyqtSignal(str)  # Status message
    finished = pyqtSignal(dict)  # Result dictionary
    error = pyqtSignal(str)  # Error message

    def __init__(self, file_paths: List[str], kill_process: bool = False,
                 safe_mode: bool = False):
        super().__init__()
        self.file_paths = file_paths
        self.kill_process = kill_process
        self.safe_mode = safe_mode
        self.unlocker = FileUnlocker()

    def run(self):
        """Execute unlock operations"""
        try:
            for file_path in self.file_paths:
                self.progress.emit(f"Processing: {file_path}")

                result = self.unlocker.unlock_file(
                    file_path,
                    kill_process=self.kill_process,
                    safe_mode=self.safe_mode
                )

                self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))


class FileUnlockerDialog(QDialog):
    """
    File Unlocker Dialog

    Provides GUI for unlocking files and managing file locks.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("File Unlocker - Smart Search Pro")
        self.setMinimumSize(900, 700)

        self.unlocker = FileUnlocker()
        self.current_file = None
        self.locking_processes = []

        self._setup_ui()
        self._connect_signals()

        # Check admin status
        if not self.unlocker.is_admin():
            self._show_admin_warning()

    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("File Unlocker")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Admin status
        self.admin_label = QLabel()
        if self.unlocker.is_admin():
            self.admin_label.setText("Running with Administrator privileges")
            self.admin_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.admin_label.setText("⚠ Not running as Administrator - functionality limited")
            self.admin_label.setStyleSheet("color: orange; font-weight: bold;")
        layout.addWidget(self.admin_label)

        # File selection group
        file_group = QGroupBox("File Selection")
        file_layout = QVBoxLayout()

        # File path input
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select file or folder to unlock...")
        path_layout.addWidget(self.path_input)

        self.browse_file_btn = QPushButton("Browse File")
        self.browse_folder_btn = QPushButton("Browse Folder")
        path_layout.addWidget(self.browse_file_btn)
        path_layout.addWidget(self.browse_folder_btn)

        file_layout.addLayout(path_layout)

        # Multi-file list
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(100)
        file_layout.addWidget(QLabel("Selected Files:"))
        file_layout.addWidget(self.file_list)

        list_buttons = QHBoxLayout()
        self.add_file_btn = QPushButton("Add File")
        self.remove_file_btn = QPushButton("Remove Selected")
        self.clear_files_btn = QPushButton("Clear All")
        list_buttons.addWidget(self.add_file_btn)
        list_buttons.addWidget(self.remove_file_btn)
        list_buttons.addWidget(self.clear_files_btn)
        file_layout.addLayout(list_buttons)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Locking processes group
        process_group = QGroupBox("Locking Processes")
        process_layout = QVBoxLayout()

        self.process_table = QTableWidget()
        self.process_table.setColumnCount(3)
        self.process_table.setHorizontalHeaderLabels(["PID", "Process Name", "Handle"])
        self.process_table.horizontalHeader().setStretchLastSection(True)
        self.process_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        process_layout.addWidget(self.process_table)

        process_buttons = QHBoxLayout()
        self.scan_btn = QPushButton("Scan for Locks")
        self.scan_btn.setStyleSheet("background-color: #0078d4; color: white; font-weight: bold;")
        self.close_handle_btn = QPushButton("Close Selected Handle")
        self.kill_process_btn = QPushButton("Kill Selected Process")
        self.kill_process_btn.setStyleSheet("background-color: #d13438; color: white;")

        process_buttons.addWidget(self.scan_btn)
        process_buttons.addWidget(self.close_handle_btn)
        process_buttons.addWidget(self.kill_process_btn)
        process_layout.addLayout(process_buttons)

        process_group.setLayout(process_layout)
        layout.addWidget(process_group)

        # Options group
        options_group = QGroupBox("Unlock Options")
        options_layout = QVBoxLayout()

        self.remove_attrs_check = QCheckBox("Remove read-only/hidden/system attributes")
        self.remove_attrs_check.setChecked(True)

        self.kill_on_unlock_check = QCheckBox("Kill locking processes during unlock")
        self.kill_on_unlock_check.setStyleSheet("color: #d13438;")

        self.safe_mode_check = QCheckBox("Safe mode (don't force unlock, just report)")

        options_layout.addWidget(self.remove_attrs_check)
        options_layout.addWidget(self.kill_on_unlock_check)
        options_layout.addWidget(self.safe_mode_check)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status log
        log_group = QGroupBox("Status Log")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)

        log_buttons = QHBoxLayout()
        self.clear_log_btn = QPushButton("Clear Log")
        log_buttons.addStretch()
        log_buttons.addWidget(self.clear_log_btn)
        log_layout.addLayout(log_buttons)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # Action buttons
        button_layout = QHBoxLayout()

        self.unlock_btn = QPushButton("Unlock File(s)")
        self.unlock_btn.setStyleSheet("background-color: #0078d4; color: white; font-weight: bold; padding: 10px;")
        self.unlock_btn.setMinimumHeight(40)

        self.close_btn = QPushButton("Close")
        self.close_btn.setMinimumHeight(40)

        button_layout.addWidget(self.unlock_btn)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def _connect_signals(self):
        """Connect signals and slots"""
        self.browse_file_btn.clicked.connect(self._browse_file)
        self.browse_folder_btn.clicked.connect(self._browse_folder)
        self.add_file_btn.clicked.connect(self._add_file)
        self.remove_file_btn.clicked.connect(self._remove_selected_files)
        self.clear_files_btn.clicked.connect(self._clear_files)

        self.scan_btn.clicked.connect(self._scan_locks)
        self.close_handle_btn.clicked.connect(self._close_selected_handle)
        self.kill_process_btn.clicked.connect(self._kill_selected_process)

        self.unlock_btn.clicked.connect(self._unlock_files)
        self.clear_log_btn.clicked.connect(self.log_text.clear)
        self.close_btn.clicked.connect(self.accept)

    def _show_admin_warning(self):
        """Show warning about not running as admin"""
        QMessageBox.warning(
            self,
            "Administrator Privileges Required",
            "File Unlocker is not running with administrator privileges.\n\n"
            "Some features will be limited:\n"
            "- Cannot enumerate system handles\n"
            "- Cannot close handles in other processes\n"
            "- Cannot kill processes\n\n"
            "Run as administrator for full functionality."
        )

    def _browse_file(self):
        """Browse for file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Unlock",
            "",
            "All Files (*.*)"
        )

        if file_path:
            self.path_input.setText(file_path)
            self.current_file = file_path
            self._log(f"Selected file: {file_path}")

    def _browse_folder(self):
        """Browse for folder"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Unlock"
        )

        if folder_path:
            self.path_input.setText(folder_path)
            self.current_file = folder_path
            self._log(f"Selected folder: {folder_path}")

    def _add_file(self):
        """Add file to batch list"""
        file_path = self.path_input.text().strip()

        if not file_path:
            QMessageBox.warning(self, "No File", "Please select a file first")
            return

        if not os.path.exists(file_path):
            QMessageBox.warning(self, "File Not Found", f"File not found: {file_path}")
            return

        # Check if already in list
        for i in range(self.file_list.count()):
            if self.file_list.item(i).text() == file_path:
                QMessageBox.information(self, "Duplicate", "File already in list")
                return

        self.file_list.addItem(file_path)
        self._log(f"Added to batch: {file_path}")

    def _remove_selected_files(self):
        """Remove selected files from list"""
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def _clear_files(self):
        """Clear all files from list"""
        self.file_list.clear()
        self._log("Cleared file list")

    def _scan_locks(self):
        """Scan for locking processes"""
        if not self.unlocker.is_admin():
            QMessageBox.warning(
                self,
                "Admin Required",
                "Administrator privileges required to scan for locks"
            )
            return

        file_path = self.path_input.text().strip()
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "No File", "Please select a valid file first")
            return

        self._log(f"Scanning for processes locking: {file_path}")

        try:
            self.locking_processes = self.unlocker.get_locking_processes(file_path)

            # Update table
            self.process_table.setRowCount(len(self.locking_processes))

            for i, process in enumerate(self.locking_processes):
                self.process_table.setItem(i, 0, QTableWidgetItem(str(process.pid)))
                self.process_table.setItem(i, 1, QTableWidgetItem(process.process_name))
                self.process_table.setItem(i, 2, QTableWidgetItem(str(process.handle_value)))

            if self.locking_processes:
                self._log(f"Found {len(self.locking_processes)} locking process(es)")
            else:
                self._log("No locking processes found")

        except Exception as e:
            self._log(f"Error scanning locks: {e}", error=True)
            QMessageBox.critical(self, "Error", f"Error scanning locks:\n{e}")

    def _close_selected_handle(self):
        """Close selected handle"""
        if not self.unlocker.is_admin():
            QMessageBox.warning(self, "Admin Required", "Administrator privileges required")
            return

        selected = self.process_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a process first")
            return

        row = selected[0].row()
        process = self.locking_processes[row]

        reply = QMessageBox.question(
            self,
            "Confirm Close Handle",
            f"Close handle {process.handle_value} in process {process.process_name} (PID: {process.pid})?\n\n"
            "This may cause the application to malfunction.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.unlocker.close_handle(process.pid, process.handle_value):
                    self._log(f"Successfully closed handle {process.handle_value} in PID {process.pid}")
                    self._scan_locks()  # Refresh
                else:
                    self._log(f"Failed to close handle", error=True)

            except Exception as e:
                self._log(f"Error closing handle: {e}", error=True)
                QMessageBox.critical(self, "Error", f"Error closing handle:\n{e}")

    def _kill_selected_process(self):
        """Kill selected process"""
        selected = self.process_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a process first")
            return

        row = selected[0].row()
        process = self.locking_processes[row]

        reply = QMessageBox.critical(
            self,
            "Confirm Kill Process",
            f"KILL process {process.process_name} (PID: {process.pid})?\n\n"
            "⚠ WARNING: This will force-terminate the application.\n"
            "Unsaved work will be lost!\n\n"
            "Are you absolutely sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.unlocker.kill_locking_process(process.pid, force=True):
                    self._log(f"Successfully killed process {process.pid}")
                    self._scan_locks()  # Refresh
                else:
                    self._log(f"Failed to kill process", error=True)

            except Exception as e:
                self._log(f"Error killing process: {e}", error=True)
                QMessageBox.critical(self, "Error", f"Error killing process:\n{e}")

    def _unlock_files(self):
        """Unlock selected files"""
        # Get files to unlock
        files = []

        if self.file_list.count() > 0:
            # Use batch list
            for i in range(self.file_list.count()):
                files.append(self.file_list.item(i).text())
        else:
            # Use single file
            file_path = self.path_input.text().strip()
            if file_path and os.path.exists(file_path):
                files.append(file_path)

        if not files:
            QMessageBox.warning(self, "No Files", "Please select file(s) to unlock")
            return

        # Confirm
        msg = f"Unlock {len(files)} file(s)?"
        if self.kill_on_unlock_check.isChecked():
            msg += "\n\n⚠ WARNING: Locking processes will be KILLED!"

        reply = QMessageBox.question(
            self,
            "Confirm Unlock",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Execute unlock
        self._log(f"Starting unlock operation on {len(files)} file(s)...")

        for file_path in files:
            try:
                result = self.unlocker.unlock_file(
                    file_path,
                    kill_process=self.kill_on_unlock_check.isChecked(),
                    safe_mode=self.safe_mode_check.isChecked()
                )

                if result['success']:
                    self._log(f"✓ Successfully unlocked: {file_path}", success=True)
                    self._log(f"  - Handles closed: {result['handles_closed']}")
                    if result['processes_killed']:
                        self._log(f"  - Processes killed: {result['processes_killed']}")
                else:
                    self._log(f"✗ Failed to unlock: {file_path}", error=True)
                    for error in result.get('errors', []):
                        self._log(f"  - {error}", error=True)

            except Exception as e:
                self._log(f"✗ Error unlocking {file_path}: {e}", error=True)

        self._log("Unlock operation completed")

        QMessageBox.information(
            self,
            "Operation Complete",
            f"Unlock operation completed.\nSee log for details."
        )

    def _log(self, message: str, error: bool = False, success: bool = False):
        """Add message to log"""
        if error:
            color = "red"
        elif success:
            color = "green"
        else:
            color = "black"

        self.log_text.append(f'<span style="color: {color};">{message}</span>')


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = FileUnlockerDialog()
    dialog.show()
    sys.exit(app.exec())
