"""
Batch Rename Integration Example
Shows how to integrate batch rename into existing Smart Search Pro UI
"""

from PyQt6.QtWidgets import QAction, QMenu
from PyQt6.QtGui import QIcon


class ResultsPanelWithBatchRename:
    """
    Example integration into ResultsPanel
    Add this code to your existing results_panel.py
    """

    def _create_context_menu_with_rename(self) -> QMenu:
        """Enhanced context menu with batch rename"""
        menu = QMenu(self)

        # Existing actions
        open_action = menu.addAction("Open")
        open_folder_action = menu.addAction("Open Folder")
        menu.addSeparator()

        # Copy/Move actions
        copy_action = menu.addAction("Copy to...")
        move_action = menu.addAction("Move to...")
        menu.addSeparator()

        # NEW: Batch Rename action
        rename_action = menu.addAction("Batch Rename Selected...")
        rename_action.setShortcut("F2")
        rename_action.triggered.connect(self._batch_rename_selected)

        menu.addSeparator()

        # Delete action
        delete_action = menu.addAction("Delete")

        return menu

    def _batch_rename_selected(self):
        """Open batch rename dialog for selected files"""
        from ui.batch_rename_dialog import BatchRenameDialog
        from PyQt6.QtWidgets import QMessageBox

        # Get selected file paths
        selected_files = self.get_selected_file_paths()

        if not selected_files:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select files to rename"
            )
            return

        # Open batch rename dialog
        dialog = BatchRenameDialog(initial_files=selected_files, parent=self)

        # Connect to refresh signal
        dialog.files_renamed.connect(self._on_batch_rename_complete)

        # Show dialog
        dialog.exec()

    def _on_batch_rename_complete(self, count: int):
        """Handle batch rename completion"""
        # Show success message
        if hasattr(self, 'statusBar'):
            self.statusBar().showMessage(f"✓ Renamed {count} files", 3000)

        # Refresh results to show new names
        if hasattr(self, 'refresh_results'):
            self.refresh_results()


class MainWindowWithBatchRename:
    """
    Example integration into MainWindow
    Add this code to your existing main_window.py
    """

    def _create_toolbar_with_rename(self):
        """Enhanced toolbar with batch rename"""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)

        # Existing actions
        search_action = QAction("Search", self)
        search_action.setShortcut("Ctrl+F")
        toolbar.addAction(search_action)

        toolbar.addSeparator()

        # NEW: Batch Rename action
        rename_action = QAction("Batch Rename", self)
        rename_action.setToolTip("Batch rename files (Ctrl+R)")
        rename_action.setShortcut("Ctrl+R")
        rename_action.triggered.connect(self._open_batch_rename)
        toolbar.addAction(rename_action)

        toolbar.addSeparator()

        return toolbar

    def _create_menu_with_rename(self):
        """Enhanced menu with batch rename"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # ... existing actions ...

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        # NEW: Batch Rename action
        rename_action = QAction("&Batch Rename Files...", self)
        rename_action.setShortcut("Ctrl+R")
        rename_action.triggered.connect(self._open_batch_rename)
        tools_menu.addAction(rename_action)

        # History action
        history_action = QAction("Rename &History...", self)
        history_action.triggered.connect(self._show_rename_history)
        tools_menu.addAction(history_action)

    def _open_batch_rename(self):
        """Open batch rename dialog"""
        from ui.batch_rename_dialog import BatchRenameDialog

        # Open empty dialog - user can add files via drag & drop
        dialog = BatchRenameDialog(parent=self)
        dialog.files_renamed.connect(self._on_files_renamed)
        dialog.exec()

    def _show_rename_history(self):
        """Show rename history"""
        from operations.rename_history import get_rename_history
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton

        history = get_rename_history()
        entries = history.get_history(limit=50)

        if not entries:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Rename History",
                "No rename operations in history"
            )
            return

        # Create history dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Rename History")
        dialog.resize(700, 500)

        layout = QVBoxLayout(dialog)

        # Text display
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        # Format history
        text = "RENAME OPERATION HISTORY\n"
        text += "=" * 60 + "\n\n"

        for entry in entries:
            text += f"Date: {entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            text += f"Pattern: {entry.pattern_used}\n"
            text += f"Files: {entry.success_count} of {entry.total_files} renamed\n"
            text += f"Can Undo: {'Yes' if entry.can_undo else 'No'}\n"
            text += "-" * 60 + "\n\n"

        # Add statistics
        stats = history.get_statistics()
        text += "\nSTATISTICS\n"
        text += "=" * 60 + "\n"
        text += f"Total Operations: {stats['total_operations']}\n"
        text += f"Total Files Renamed: {stats['total_files_renamed']}\n"
        text += f"Success Rate: {stats['success_rate']:.1f}%\n"

        text_edit.setPlainText(text)
        layout.addWidget(text_edit)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def _on_files_renamed(self, count: int):
        """Handle files renamed signal"""
        self.statusBar().showMessage(f"✓ {count} files renamed", 3000)


class OperationsPanelWithBatchRename:
    """
    Example integration into OperationsPanel
    Add this code to your existing operations_panel.py
    """

    def _add_batch_rename_button(self, layout):
        """Add batch rename button to operations panel"""
        from PyQt6.QtWidgets import QPushButton, QGroupBox, QVBoxLayout

        # Create group
        rename_group = QGroupBox("Batch Operations")
        rename_layout = QVBoxLayout(rename_group)

        # Batch rename button
        rename_btn = QPushButton("Batch Rename Files...")
        rename_btn.setToolTip("Rename multiple files with patterns")
        rename_btn.clicked.connect(self._open_batch_rename_dialog)
        rename_layout.addWidget(rename_btn)

        layout.addWidget(rename_group)

    def _open_batch_rename_dialog(self):
        """Open batch rename dialog"""
        from ui.batch_rename_dialog import BatchRenameDialog

        dialog = BatchRenameDialog(parent=self)
        dialog.files_renamed.connect(self._on_batch_rename_complete)
        dialog.exec()

    def _on_batch_rename_complete(self, count: int):
        """Handle batch rename completion"""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "Batch Rename Complete",
            f"Successfully renamed {count} files"
        )


# Example: Adding keyboard shortcut globally
class GlobalShortcutExample:
    """Example of adding F2 shortcut for batch rename"""

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        from PyQt6.QtGui import QShortcut, QKeySequence

        # F2 for batch rename (like Windows Explorer)
        rename_shortcut = QShortcut(QKeySequence("F2"), self)
        rename_shortcut.activated.connect(self._quick_rename_selected)

        # Ctrl+R for batch rename dialog
        batch_rename_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        batch_rename_shortcut.activated.connect(self._open_batch_rename)

    def _quick_rename_selected(self):
        """Quick rename selected file (like F2 in Explorer)"""
        from ui.batch_rename_dialog import BatchRenameDialog

        # Get currently selected file(s)
        selected = self.get_selected_files()

        if selected:
            dialog = BatchRenameDialog(initial_files=selected, parent=self)
            dialog.exec()


# Complete integration example
def integrate_batch_rename_into_smart_search():
    """
    Complete integration guide

    1. Add to results_panel.py:
       - Import: from ui.batch_rename_dialog import BatchRenameDialog
       - Add context menu item (see ResultsPanelWithBatchRename)
       - Add F2 shortcut support

    2. Add to main_window.py:
       - Import: from ui.batch_rename_dialog import BatchRenameDialog
       - Add toolbar action (see MainWindowWithBatchRename)
       - Add menu item under Tools menu
       - Add Ctrl+R shortcut

    3. Add to operations_panel.py:
       - Add batch rename button (see OperationsPanelWithBatchRename)

    4. Test:
       - python ui/test_batch_rename_dialog.py
       - python operations/test_batch_rename.py
    """
    pass


if __name__ == "__main__":
    print(__doc__)
    print("\nSee function docstrings for integration examples:")
    print("  - ResultsPanelWithBatchRename")
    print("  - MainWindowWithBatchRename")
    print("  - OperationsPanelWithBatchRename")
    print("  - GlobalShortcutExample")
