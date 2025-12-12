"""
Vault Panel - Encrypted Vault Interface
Main interface for secure vault management

Features:
- Hidden access (special key combination)
- File browser inside vault
- Drag & drop to add files
- Quick hide (panic button)
- Vault statistics
- Password management
- Export/backup
- Emergency wipe
"""

import sys
import os
from pathlib import Path
from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QToolBar, QMenu, QMessageBox, QFileDialog,
    QInputDialog, QProgressDialog, QSplitter, QTextEdit, QLineEdit,
    QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QMimeData, QUrl
from PyQt6.QtGui import QFont, QIcon, QAction, QDrag, QKeySequence, QShortcut


class VaultPanel(QWidget):
    """
    Secure vault panel with encrypted file storage

    Hidden access via Ctrl+Shift+V
    """

    vault_locked = pyqtSignal()
    vault_unlocked = pyqtSignal()
    panic_triggered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.vault = None
        self.vfs = None
        self.is_unlocked = False
        self.current_path = '/'
        self.auto_lock_timer = QTimer()

        self._setup_ui()
        self._setup_shortcuts()
        self._setup_auto_lock()

        # Start hidden
        self.hide()

    def _setup_ui(self):
        """Setup vault panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Status bar
        status_layout = QHBoxLayout()

        self.status_label = QLabel("Vault Locked")
        self.status_label.setStyleSheet("color: #d32f2f; font-weight: bold; padding: 5px;")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("padding: 5px;")
        status_layout.addWidget(self.stats_label)

        layout.addLayout(status_layout)

        # Main content
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # File tree
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(['Name', 'Size', 'Modified'])
        self.file_tree.setColumnWidth(0, 250)
        self.file_tree.setColumnWidth(1, 100)
        self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self._show_context_menu)
        self.file_tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.file_tree.setDragEnabled(True)
        self.file_tree.setAcceptDrops(True)
        self.file_tree.setDropIndicatorShown(True)
        splitter.addWidget(self.file_tree)

        # Preview/Info panel
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)

        info_label = QLabel("File Information")
        info_label.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
        info_layout.addWidget(info_label)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)

        splitter.addWidget(info_widget)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

        # Drag & drop support
        self.setAcceptDrops(True)

        # Styling
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QTreeWidget {
                background-color: #252525;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #0078d4;
            }
            QTreeWidget::item:hover {
                background-color: #2d2d2d;
            }
            QTextEdit {
                background-color: #252525;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QToolBar {
                background-color: #2d2d2d;
                border-bottom: 1px solid #3d3d3d;
                spacing: 5px;
                padding: 5px;
            }
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #1084d8;
            }
            QPushButton:pressed {
                background-color: #006cbd;
            }
        """)

    def _create_toolbar(self) -> QToolBar:
        """Create vault toolbar"""
        toolbar = QToolBar()

        # Unlock/Lock
        self.unlock_action = QAction("Unlock Vault", self)
        self.unlock_action.triggered.connect(self._unlock_vault)
        toolbar.addAction(self.unlock_action)

        self.lock_action = QAction("Lock Vault", self)
        self.lock_action.triggered.connect(self._lock_vault)
        self.lock_action.setEnabled(False)
        toolbar.addAction(self.lock_action)

        toolbar.addSeparator()

        # Add files
        self.add_file_action = QAction("Add File", self)
        self.add_file_action.triggered.connect(self._add_file)
        self.add_file_action.setEnabled(False)
        toolbar.addAction(self.add_file_action)

        self.add_folder_action = QAction("Add Folder", self)
        self.add_folder_action.triggered.connect(self._add_folder)
        self.add_folder_action.setEnabled(False)
        toolbar.addAction(self.add_folder_action)

        # Extract
        self.extract_action = QAction("Extract", self)
        self.extract_action.triggered.connect(self._extract_selected)
        self.extract_action.setEnabled(False)
        toolbar.addAction(self.extract_action)

        toolbar.addSeparator()

        # Settings
        self.settings_action = QAction("Settings", self)
        self.settings_action.triggered.connect(self._show_settings)
        toolbar.addAction(self.settings_action)

        # Panic button (emergency hide)
        self.panic_action = QAction("PANIC", self)
        self.panic_action.triggered.connect(self._panic_hide)
        self.panic_action.setShortcut(QKeySequence("Ctrl+Shift+H"))
        toolbar.addAction(self.panic_action)

        return toolbar

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Ctrl+Shift+V to show/hide vault
        toggle_shortcut = QShortcut(QKeySequence("Ctrl+Shift+V"), self.parent() or self)
        toggle_shortcut.activated.connect(self._toggle_visibility)

        # ESC to hide
        hide_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        hide_shortcut.activated.connect(self.hide)

    def _setup_auto_lock(self):
        """Setup auto-lock timer"""
        self.auto_lock_timer.timeout.connect(self._check_auto_lock)
        self.auto_lock_timer.setInterval(10000)  # Check every 10 seconds

    def _toggle_visibility(self):
        """Toggle vault panel visibility"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def _unlock_vault(self):
        """Unlock vault with password"""
        from .vault_unlock_dialog import VaultUnlockDialog
        from ..vault.secure_vault import SecureVault, VaultConfig
        from ..vault.virtual_fs import VirtualFileSystem

        try:
            # Show unlock dialog
            password, is_duress, accepted = VaultUnlockDialog.get_unlock_password(
                max_attempts=5,
                lockout_duration=300,
                parent=self
            )

            if not accepted:
                return

            # Create or load vault
            config = VaultConfig()
            config.container_path = str(Path.home() / ".vault_container.dll")

            self.vault = SecureVault(config)

            # Create new vault if doesn't exist
            if not os.path.exists(config.container_path):
                reply = QMessageBox.question(
                    self,
                    "Create Vault",
                    "Vault container not found. Create new vault?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    # Create vault
                    decoy_password = None
                    if config.use_decoy:
                        decoy_password, ok = QInputDialog.getText(
                            self,
                            "Decoy Password",
                            "Enter decoy password (optional):",
                            QLineEdit.EchoMode.Password
                        )
                        if not ok:
                            decoy_password = None

                    if not self.vault.create_vault(password, decoy_password):
                        raise Exception("Failed to create vault")

            # Unlock vault
            is_main = self.vault.unlock_vault(password)

            if is_duress or not is_main:
                QMessageBox.warning(
                    self,
                    "Decoy Vault",
                    "Decoy vault unlocked. Limited functionality."
                )

            # Mount virtual filesystem
            self.vfs = VirtualFileSystem()
            self.vfs.mount(self.vault)

            # Update UI
            self.is_unlocked = True
            self.status_label.setText("Vault Unlocked")
            self.status_label.setStyleSheet("color: #4caf50; font-weight: bold; padding: 5px;")

            self.unlock_action.setEnabled(False)
            self.lock_action.setEnabled(True)
            self.add_file_action.setEnabled(True)
            self.add_folder_action.setEnabled(True)
            self.extract_action.setEnabled(True)

            # Load file tree
            self._refresh_file_tree()

            # Update stats
            self._update_stats()

            # Start auto-lock timer
            self.auto_lock_timer.start()

            self.vault_unlocked.emit()

        except Exception as e:
            QMessageBox.critical(self, "Unlock Failed", f"Failed to unlock vault:\n{str(e)}")

    def _lock_vault(self):
        """Lock vault and clear memory"""
        if self.vault:
            # Unmount filesystem
            if self.vfs:
                self.vfs.unmount()
                self.vfs = None

            # Lock vault
            self.vault.lock_vault()
            self.vault = None

        # Update UI
        self.is_unlocked = False
        self.status_label.setText("Vault Locked")
        self.status_label.setStyleSheet("color: #d32f2f; font-weight: bold; padding: 5px;")

        self.unlock_action.setEnabled(True)
        self.lock_action.setEnabled(False)
        self.add_file_action.setEnabled(False)
        self.add_folder_action.setEnabled(False)
        self.extract_action.setEnabled(False)

        # Clear tree
        self.file_tree.clear()
        self.info_text.clear()
        self.stats_label.clear()

        # Stop auto-lock timer
        self.auto_lock_timer.stop()

        self.vault_locked.emit()

    def _refresh_file_tree(self):
        """Refresh file tree from virtual filesystem"""
        if not self.vfs or not self.is_unlocked:
            return

        self.file_tree.clear()

        try:
            # List files in current directory
            files = self.vfs.list_dir(self.current_path)

            for file_info in files:
                item = QTreeWidgetItem()
                item.setText(0, os.path.basename(file_info.path) or '/')

                if file_info.is_dir:
                    item.setText(1, '<DIR>')
                else:
                    item.setText(1, self._format_size(file_info.size))

                from datetime import datetime
                modified = datetime.fromtimestamp(file_info.modified)
                item.setText(2, modified.strftime('%Y-%m-%d %H:%M'))

                item.setData(0, Qt.ItemDataRole.UserRole, file_info.path)

                self.file_tree.addTopLevelItem(item)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load files:\n{str(e)}")

    def _format_size(self, size: int) -> str:
        """Format file size for display"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _add_file(self):
        """Add file to vault"""
        if not self.is_unlocked:
            return

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Add Files to Vault",
            str(Path.home()),
            "All Files (*.*)"
        )

        if not files:
            return

        progress = QProgressDialog("Adding files to vault...", "Cancel", 0, len(files), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)

        try:
            for i, file_path in enumerate(files):
                if progress.wasCanceled():
                    break

                progress.setValue(i)
                progress.setLabelText(f"Adding: {os.path.basename(file_path)}")

                # Read file
                with open(file_path, 'rb') as f:
                    content = f.read()

                # Add to virtual filesystem
                vpath = f"/{os.path.basename(file_path)}"
                self.vfs.write_file(vpath, content)

            progress.setValue(len(files))

            # Refresh tree
            self._refresh_file_tree()
            self._update_stats()

            QMessageBox.information(self, "Success", f"Added {len(files)} file(s) to vault")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add files:\n{str(e)}")

    def _add_folder(self):
        """Add folder to vault"""
        if not self.is_unlocked:
            return

        folder = QFileDialog.getExistingDirectory(
            self,
            "Add Folder to Vault",
            str(Path.home())
        )

        if not folder:
            return

        try:
            # Import folder tree
            self.vfs.import_tree(folder, '/')

            # Refresh tree
            self._refresh_file_tree()
            self._update_stats()

            QMessageBox.information(self, "Success", "Folder added to vault")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add folder:\n{str(e)}")

    def _extract_selected(self):
        """Extract selected file(s)"""
        if not self.is_unlocked:
            return

        selected = self.file_tree.selectedItems()
        if not selected:
            QMessageBox.information(self, "No Selection", "Please select file(s) to extract")
            return

        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Extract to Folder",
            str(Path.home())
        )

        if not output_dir:
            return

        try:
            for item in selected:
                vpath = item.data(0, Qt.ItemDataRole.UserRole)
                file_info = self.vfs.get_info(vpath)

                if file_info and not file_info.is_dir:
                    # Extract file
                    content = self.vfs.read_file(vpath)
                    if content:
                        output_path = os.path.join(output_dir, os.path.basename(vpath))
                        with open(output_path, 'wb') as f:
                            f.write(content)

            QMessageBox.information(self, "Success", "File(s) extracted successfully")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to extract:\n{str(e)}")

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item double-click"""
        if not self.is_unlocked:
            return

        vpath = item.data(0, Qt.ItemDataRole.UserRole)
        file_info = self.vfs.get_info(vpath)

        if file_info and file_info.is_dir:
            # Navigate into directory
            self.current_path = vpath
            self._refresh_file_tree()
        else:
            # Show file info
            self._show_file_info(vpath)

    def _show_file_info(self, vpath: str):
        """Show file information"""
        file_info = self.vfs.get_info(vpath)

        if not file_info:
            return

        from datetime import datetime

        info_text = f"""
File: {os.path.basename(file_info.path)}
Path: {file_info.path}
Size: {self._format_size(file_info.size)}
Created: {datetime.fromtimestamp(file_info.created).strftime('%Y-%m-%d %H:%M:%S')}
Modified: {datetime.fromtimestamp(file_info.modified).strftime('%Y-%m-%d %H:%M:%S')}
Type: {'Directory' if file_info.is_dir else 'File'}
Permissions: {oct(file_info.permissions)}
        """

        self.info_text.setPlainText(info_text.strip())

    def _show_context_menu(self, position):
        """Show context menu for file tree"""
        if not self.is_unlocked:
            return

        item = self.file_tree.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        extract_action = menu.addAction("Extract")
        extract_action.triggered.connect(self._extract_selected)

        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(self._delete_selected)

        menu.addSeparator()

        info_action = menu.addAction("Properties")
        info_action.triggered.connect(lambda: self._show_file_info(item.data(0, Qt.ItemDataRole.UserRole)))

        menu.exec(self.file_tree.mapToGlobal(position))

    def _delete_selected(self):
        """Delete selected file(s)"""
        if not self.is_unlocked:
            return

        selected = self.file_tree.selectedItems()
        if not selected:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete {len(selected)} item(s) from vault?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            for item in selected:
                vpath = item.data(0, Qt.ItemDataRole.UserRole)
                self.vfs.delete(vpath, recursive=True)

            self._refresh_file_tree()
            self._update_stats()

            QMessageBox.information(self, "Success", "Item(s) deleted")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete:\n{str(e)}")

    def _update_stats(self):
        """Update vault statistics"""
        if not self.vault or not self.is_unlocked:
            return

        try:
            stats = self.vault.get_vault_stats()
            total_size = self.vfs.get_tree_size() if self.vfs else 0

            self.stats_label.setText(
                f"Files: {stats['file_count']} | "
                f"Size: {self._format_size(total_size)}"
            )

        except Exception:
            pass

    def _check_auto_lock(self):
        """Check if vault should auto-lock"""
        if self.vault and self.is_unlocked:
            if self.vault.check_auto_lock():
                self._lock_vault()
                QMessageBox.information(self, "Auto-Lock", "Vault auto-locked due to inactivity")

    def _panic_hide(self):
        """Emergency hide (panic button)"""
        self.hide()
        self.panic_triggered.emit()

        # Optional: Lock vault on panic
        if self.is_unlocked:
            self._lock_vault()

    def _show_settings(self):
        """Show vault settings dialog"""
        # TODO: Implement settings dialog
        QMessageBox.information(self, "Settings", "Vault settings (coming soon)")

    def dragEnterEvent(self, event):
        """Handle drag enter"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle file drop"""
        if not self.is_unlocked:
            QMessageBox.warning(self, "Vault Locked", "Please unlock vault first")
            return

        urls = event.mimeData().urls()
        if not urls:
            return

        files = [url.toLocalFile() for url in urls if url.isLocalFile()]

        if not files:
            return

        try:
            for file_path in files:
                if os.path.isfile(file_path):
                    # Add file
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    vpath = f"/{os.path.basename(file_path)}"
                    self.vfs.write_file(vpath, content)

                elif os.path.isdir(file_path):
                    # Add folder
                    self.vfs.import_tree(file_path, '/')

            self._refresh_file_tree()
            self._update_stats()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add files:\n{str(e)}")


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    window = QMainWindow()
    vault_panel = VaultPanel()
    window.setCentralWidget(vault_panel)
    window.setWindowTitle("Secure Vault")
    window.resize(800, 600)
    window.show()

    # Show vault with Ctrl+Shift+V
    vault_panel.show()

    sys.exit(app.exec())
