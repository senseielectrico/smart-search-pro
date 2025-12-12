"""
Permission Dialog - PyQt6 UI for PermissionFixer

Features:
- Current permissions display
- Take ownership button
- Reset permissions button
- Custom permission editor
- Recursive option for folders
- Backup/restore permissions

Security Warning:
This dialog modifies file system permissions.
Incorrect changes can make files inaccessible.
"""

import os
import sys
from typing import Dict, Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QCheckBox,
    QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox,
    QGroupBox, QHeaderView, QComboBox, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor

import logging

# Import the permission fixer
import sys
from pathlib import Path
tools_path = Path(__file__).parent.parent / 'tools'
sys.path.insert(0, str(tools_path))

from permission_fixer import PermissionFixer

logger = logging.getLogger(__name__)


class PermissionWorker(QThread):
    """Background worker for permission operations"""

    progress = pyqtSignal(str)  # Status message
    finished = pyqtSignal(dict)  # Result dictionary
    error = pyqtSignal(str)  # Error message

    def __init__(self, operation: str, path: str, **kwargs):
        super().__init__()
        self.operation = operation
        self.path = path
        self.kwargs = kwargs
        self.fixer = PermissionFixer()

    def run(self):
        """Execute permission operations"""
        try:
            if self.operation == 'take_ownership':
                result = self.fixer.take_ownership(self.path, **self.kwargs)
                self.finished.emit(result)

            elif self.operation == 'grant_full':
                result = self.fixer.grant_full_control(self.path, **self.kwargs)
                self.finished.emit(result)

            elif self.operation == 'remove_deny':
                result = self.fixer.remove_deny_aces(self.path, **self.kwargs)
                self.finished.emit(result)

            elif self.operation == 'reset':
                result = self.fixer.reset_to_defaults(self.path, **self.kwargs)
                self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))


class PermissionDialog(QDialog):
    """
    Permission Fixer Dialog

    Provides GUI for viewing and modifying file permissions.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Permission Fixer - Smart Search Pro")
        self.setMinimumSize(1000, 750)

        self.fixer = PermissionFixer()
        self.current_path = None
        self.current_permissions = None

        self._setup_ui()
        self._connect_signals()

        # Check admin status
        if not self.fixer._is_admin:
            self._show_admin_warning()

    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Permission Fixer")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Admin status
        self.admin_label = QLabel()
        if self.fixer._is_admin:
            self.admin_label.setText("✓ Running with Administrator privileges")
            self.admin_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.admin_label.setText("⚠ Not running as Administrator - operations will fail")
            self.admin_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.admin_label)

        # File selection
        file_group = QGroupBox("File/Folder Selection")
        file_layout = QVBoxLayout()

        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select file or folder...")
        path_layout.addWidget(self.path_input)

        self.browse_file_btn = QPushButton("Browse File")
        self.browse_folder_btn = QPushButton("Browse Folder")
        path_layout.addWidget(self.browse_file_btn)
        path_layout.addWidget(self.browse_folder_btn)

        file_layout.addLayout(path_layout)

        # Load permissions button
        self.load_perms_btn = QPushButton("Load Permissions")
        self.load_perms_btn.setStyleSheet("background-color: #0078d4; color: white; font-weight: bold;")
        file_layout.addWidget(self.load_perms_btn)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Current permissions display
        perms_group = QGroupBox("Current Permissions")
        perms_layout = QVBoxLayout()

        # Owner/Group info
        info_grid = QGridLayout()
        info_grid.addWidget(QLabel("Owner:"), 0, 0)
        self.owner_label = QLabel("-")
        self.owner_label.setFont(QFont("Segoe UI", 10))
        info_grid.addWidget(self.owner_label, 0, 1)

        info_grid.addWidget(QLabel("Group:"), 1, 0)
        self.group_label = QLabel("-")
        self.group_label.setFont(QFont("Segoe UI", 10))
        info_grid.addWidget(self.group_label, 1, 1)

        info_grid.addWidget(QLabel("DACL Protected:"), 2, 0)
        self.protected_label = QLabel("-")
        info_grid.addWidget(self.protected_label, 2, 1)

        perms_layout.addLayout(info_grid)

        # ACE table
        self.ace_table = QTableWidget()
        self.ace_table.setColumnCount(3)
        self.ace_table.setHorizontalHeaderLabels(["Type", "Account", "Permissions"])
        self.ace_table.horizontalHeader().setStretchLastSection(True)
        self.ace_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        perms_layout.addWidget(self.ace_table)

        perms_group.setLayout(perms_layout)
        layout.addWidget(perms_group)

        # Actions group
        actions_group = QGroupBox("Permission Actions")
        actions_layout = QVBoxLayout()

        # Recursive option
        self.recursive_check = QCheckBox("Apply recursively to all subfolders and files")
        self.recursive_check.setStyleSheet("font-weight: bold; color: #d13438;")
        actions_layout.addWidget(self.recursive_check)

        # Action buttons grid
        button_grid = QGridLayout()

        self.take_ownership_btn = QPushButton("Take Ownership")
        self.take_ownership_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 8px;")
        self.take_ownership_btn.setMinimumHeight(35)
        button_grid.addWidget(self.take_ownership_btn, 0, 0)

        self.grant_full_btn = QPushButton("Grant Full Control")
        self.grant_full_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 8px;")
        self.grant_full_btn.setMinimumHeight(35)
        button_grid.addWidget(self.grant_full_btn, 0, 1)

        self.remove_deny_btn = QPushButton("Remove Deny ACEs")
        self.remove_deny_btn.setStyleSheet("background-color: #107c10; color: white; padding: 8px;")
        self.remove_deny_btn.setMinimumHeight(35)
        button_grid.addWidget(self.remove_deny_btn, 1, 0)

        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.setStyleSheet("background-color: #d13438; color: white; padding: 8px;")
        self.reset_btn.setMinimumHeight(35)
        button_grid.addWidget(self.reset_btn, 1, 1)

        actions_layout.addLayout(button_grid)

        # Backup/Restore
        backup_layout = QHBoxLayout()
        self.backup_btn = QPushButton("Backup Permissions")
        self.restore_btn = QPushButton("Restore Permissions")
        backup_layout.addWidget(self.backup_btn)
        backup_layout.addWidget(self.restore_btn)
        actions_layout.addLayout(backup_layout)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

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

        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.close_btn = QPushButton("Close")
        self.close_btn.setMinimumWidth(120)
        self.close_btn.setMinimumHeight(35)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def _connect_signals(self):
        """Connect signals and slots"""
        self.browse_file_btn.clicked.connect(self._browse_file)
        self.browse_folder_btn.clicked.connect(self._browse_folder)
        self.load_perms_btn.clicked.connect(self._load_permissions)

        self.take_ownership_btn.clicked.connect(self._take_ownership)
        self.grant_full_btn.clicked.connect(self._grant_full_control)
        self.remove_deny_btn.clicked.connect(self._remove_deny_aces)
        self.reset_btn.clicked.connect(self._reset_permissions)

        self.backup_btn.clicked.connect(self._backup_permissions)
        self.restore_btn.clicked.connect(self._restore_permissions)

        self.clear_log_btn.clicked.connect(self.log_text.clear)
        self.close_btn.clicked.connect(self.accept)

    def _show_admin_warning(self):
        """Show warning about not running as admin"""
        QMessageBox.critical(
            self,
            "Administrator Privileges Required",
            "Permission Fixer MUST be run with administrator privileges.\n\n"
            "All permission modification operations will fail without admin rights.\n\n"
            "Please restart as administrator."
        )

    def _browse_file(self):
        """Browse for file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*.*)"
        )

        if file_path:
            self.path_input.setText(file_path)
            self.current_path = file_path
            self._log(f"Selected file: {file_path}")

    def _browse_folder(self):
        """Browse for folder"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder"
        )

        if folder_path:
            self.path_input.setText(folder_path)
            self.current_path = folder_path
            self._log(f"Selected folder: {folder_path}")

    def _load_permissions(self):
        """Load and display current permissions"""
        path = self.path_input.text().strip()

        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Invalid Path", "Please select a valid file or folder")
            return

        self.current_path = path
        self._log(f"Loading permissions for: {path}")

        try:
            perms = self.fixer.get_current_permissions(path)

            if 'error' in perms:
                self._log(f"Error loading permissions: {perms['error']}", error=True)
                QMessageBox.critical(self, "Error", f"Error loading permissions:\n{perms['error']}")
                return

            self.current_permissions = perms

            # Update owner/group
            self.owner_label.setText(perms.get('owner', 'Unknown'))
            self.group_label.setText(perms.get('group', 'Unknown'))
            self.protected_label.setText("Yes" if perms.get('dacl_protected') else "No")

            # Update ACE table
            aces = perms.get('aces', [])
            self.ace_table.setRowCount(len(aces))

            for i, ace in enumerate(aces):
                # Type
                type_item = QTableWidgetItem(ace['type'])
                if ace['type'] == 'Deny':
                    type_item.setForeground(QColor('red'))
                self.ace_table.setItem(i, 0, type_item)

                # Account
                self.ace_table.setItem(i, 1, QTableWidgetItem(ace['account']))

                # Permissions
                perms_text = ', '.join(ace['permissions'])
                self.ace_table.setItem(i, 2, QTableWidgetItem(perms_text))

            self._log(f"Loaded {len(aces)} ACE(s)")

        except Exception as e:
            self._log(f"Error loading permissions: {e}", error=True)
            QMessageBox.critical(self, "Error", f"Error loading permissions:\n{e}")

    def _take_ownership(self):
        """Take ownership of file/folder"""
        if not self._confirm_action("Take Ownership"):
            return

        if not self.current_path:
            QMessageBox.warning(self, "No Path", "Please select a file/folder first")
            return

        recursive = self.recursive_check.isChecked()

        self._log(f"Taking ownership of: {self.current_path}")
        if recursive:
            self._log("Recursive mode enabled")

        try:
            result = self.fixer.take_ownership(self.current_path, recursive=recursive)

            if result['success']:
                self._log(f"✓ Successfully took ownership", success=True)
                self._log(f"  Files processed: {result['files_processed']}")

                if result.get('errors'):
                    self._log(f"  Errors: {len(result['errors'])}", error=True)

                QMessageBox.information(
                    self,
                    "Success",
                    f"Successfully took ownership of {result['files_processed']} file(s)"
                )

                self._load_permissions()  # Refresh

            else:
                self._log(f"✗ Failed to take ownership", error=True)
                for error in result.get('errors', []):
                    self._log(f"  - {error}", error=True)

                QMessageBox.critical(self, "Error", "Failed to take ownership. See log for details.")

        except Exception as e:
            self._log(f"Error: {e}", error=True)
            QMessageBox.critical(self, "Error", f"Error taking ownership:\n{e}")

    def _grant_full_control(self):
        """Grant full control to current user"""
        if not self._confirm_action("Grant Full Control"):
            return

        if not self.current_path:
            QMessageBox.warning(self, "No Path", "Please select a file/folder first")
            return

        recursive = self.recursive_check.isChecked()

        self._log(f"Granting full control: {self.current_path}")
        if recursive:
            self._log("Recursive mode enabled")

        try:
            result = self.fixer.grant_full_control(self.current_path, recursive=recursive)

            if result['success']:
                self._log(f"✓ Successfully granted full control", success=True)
                self._log(f"  Files processed: {result['files_processed']}")

                if result.get('errors'):
                    self._log(f"  Errors: {len(result['errors'])}", error=True)

                QMessageBox.information(
                    self,
                    "Success",
                    f"Successfully granted full control to {result['files_processed']} file(s)"
                )

                self._load_permissions()  # Refresh

            else:
                self._log(f"✗ Failed to grant full control", error=True)
                for error in result.get('errors', []):
                    self._log(f"  - {error}", error=True)

                QMessageBox.critical(self, "Error", "Failed to grant full control. See log for details.")

        except Exception as e:
            self._log(f"Error: {e}", error=True)
            QMessageBox.critical(self, "Error", f"Error granting full control:\n{e}")

    def _remove_deny_aces(self):
        """Remove all deny ACEs"""
        if not self._confirm_action("Remove Deny ACEs"):
            return

        if not self.current_path:
            QMessageBox.warning(self, "No Path", "Please select a file/folder first")
            return

        recursive = self.recursive_check.isChecked()

        self._log(f"Removing deny ACEs from: {self.current_path}")
        if recursive:
            self._log("Recursive mode enabled")

        try:
            result = self.fixer.remove_deny_aces(self.current_path, recursive=recursive)

            if result['success']:
                self._log(f"✓ Successfully removed deny ACEs", success=True)
                self._log(f"  Files processed: {result['files_processed']}")
                self._log(f"  ACEs removed: {result['aces_removed']}")

                QMessageBox.information(
                    self,
                    "Success",
                    f"Removed {result['aces_removed']} deny ACE(s) from {result['files_processed']} file(s)"
                )

                self._load_permissions()  # Refresh

            else:
                self._log(f"✗ Failed to remove deny ACEs", error=True)

                QMessageBox.critical(self, "Error", "Failed to remove deny ACEs. See log for details.")

        except Exception as e:
            self._log(f"Error: {e}", error=True)
            QMessageBox.critical(self, "Error", f"Error removing deny ACEs:\n{e}")

    def _reset_permissions(self):
        """Reset permissions to defaults"""
        reply = QMessageBox.critical(
            self,
            "Confirm Reset",
            "⚠ WARNING: Reset permissions to Windows defaults?\n\n"
            "This will:\n"
            "- Take ownership\n"
            "- Remove custom ACEs\n"
            "- Set default permissions\n\n"
            "This operation cannot be easily undone!\n"
            "Consider backing up permissions first.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        if not self.current_path:
            QMessageBox.warning(self, "No Path", "Please select a file/folder first")
            return

        recursive = self.recursive_check.isChecked()

        self._log(f"Resetting permissions: {self.current_path}")
        if recursive:
            self._log("Recursive mode enabled - THIS MAY TAKE A WHILE!")

        try:
            result = self.fixer.reset_to_defaults(self.current_path, recursive=recursive)

            if result['success']:
                self._log(f"✓ Successfully reset permissions", success=True)
                self._log(f"  Files processed: {result['files_processed']}")

                QMessageBox.information(
                    self,
                    "Success",
                    f"Reset permissions on {result['files_processed']} file(s)"
                )

                self._load_permissions()  # Refresh

            else:
                self._log(f"✗ Failed to reset permissions", error=True)

                QMessageBox.critical(self, "Error", "Failed to reset permissions. See log for details.")

        except Exception as e:
            self._log(f"Error: {e}", error=True)
            QMessageBox.critical(self, "Error", f"Error resetting permissions:\n{e}")

    def _backup_permissions(self):
        """Backup current permissions"""
        if not self.current_path:
            QMessageBox.warning(self, "No Path", "Please select a file/folder first")
            return

        self._log(f"Backing up permissions for: {self.current_path}")

        try:
            if self.fixer.backup_permissions(self.current_path):
                self._log("✓ Permissions backed up successfully", success=True)
                QMessageBox.information(self, "Success", "Permissions backed up successfully")
            else:
                self._log("✗ Failed to backup permissions", error=True)
                QMessageBox.critical(self, "Error", "Failed to backup permissions")

        except Exception as e:
            self._log(f"Error: {e}", error=True)
            QMessageBox.critical(self, "Error", f"Error backing up permissions:\n{e}")

    def _restore_permissions(self):
        """Restore permissions from backup"""
        if not self.current_path:
            QMessageBox.warning(self, "No Path", "Please select a file/folder first")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Restore",
            f"Restore permissions from backup for:\n{self.current_path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self._log(f"Restoring permissions for: {self.current_path}")

        try:
            if self.fixer.restore_permissions(self.current_path):
                self._log("✓ Permissions restored successfully", success=True)
                QMessageBox.information(self, "Success", "Permissions restored successfully")
                self._load_permissions()  # Refresh
            else:
                self._log("✗ Failed to restore permissions (no backup found?)", error=True)
                QMessageBox.critical(self, "Error", "Failed to restore permissions. No backup found?")

        except Exception as e:
            self._log(f"Error: {e}", error=True)
            QMessageBox.critical(self, "Error", f"Error restoring permissions:\n{e}")

    def _confirm_action(self, action: str) -> bool:
        """Confirm permission action"""
        if not self.fixer._is_admin:
            QMessageBox.critical(
                self,
                "Admin Required",
                "Administrator privileges required for this operation"
            )
            return False

        recursive = self.recursive_check.isChecked()

        msg = f"{action}?\n\nPath: {self.current_path}"
        if recursive:
            msg += "\n\n⚠ RECURSIVE MODE - will apply to all subfolders and files!"

        reply = QMessageBox.question(
            self,
            f"Confirm {action}",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        return reply == QMessageBox.StandardButton.Yes

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
    dialog = PermissionDialog()
    dialog.show()
    sys.exit(app.exec())
