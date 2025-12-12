"""
Duplicates Panel - Fully functional duplicate file finder and manager

Features:
- Real-time scanning with progress
- Multiple selection strategies
- Safe deletion options
- Group visualization
- Space metrics
"""

from typing import List, Dict, Set, Optional
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QHeaderView, QMenu, QFileDialog, QMessageBox,
    QComboBox, QSpinBox, QCheckBox, QProgressDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QAction

from .widgets import EmptyStateWidget, ProgressCard
from duplicates.scanner import DuplicateScanner, ScanProgress
from duplicates.groups import DuplicateGroupManager, SelectionStrategy
from duplicates.actions import (
    RecycleBinAction, MoveToFolderAction, PermanentDeleteAction,
    AuditLogger, execute_batch_action, get_action_summary,
    HAS_SEND2TRASH
)


class ScannerThread(QThread):
    """Background thread for duplicate scanning"""

    progress_updated = pyqtSignal(object)  # ScanProgress
    scan_completed = pyqtSignal(object)    # DuplicateGroupManager
    scan_failed = pyqtSignal(str)          # Error message

    def __init__(self, scanner: DuplicateScanner, paths: List[str], recursive: bool = True):
        super().__init__()
        self.scanner = scanner
        self.paths = paths
        self.recursive = recursive

    def run(self):
        """Execute scan in background"""
        try:
            def progress_callback(progress: ScanProgress):
                self.progress_updated.emit(progress)

            result = self.scanner.scan(
                self.paths,
                recursive=self.recursive,
                follow_symlinks=False,
                progress_callback=progress_callback
            )

            self.scan_completed.emit(result)

        except Exception as e:
            self.scan_failed.emit(str(e))


class DuplicatesPanel(QWidget):
    """Panel for managing duplicate files"""

    # Signals
    delete_requested = pyqtSignal(list)
    keep_requested = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize backend
        self.scanner = DuplicateScanner(use_cache=True, max_workers=4)
        self.group_manager: Optional[DuplicateGroupManager] = None
        self.audit_logger = AuditLogger(
            Path.home() / '.cache' / 'smart_search' / 'duplicates_audit.json'
        )

        # Scanning state
        self.scan_thread: Optional[ScannerThread] = None
        self.is_scanning = False

        self._init_ui()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addLayout(toolbar)

        # Progress card (hidden by default)
        self.progress_card = ProgressCard("Scanning for duplicates")
        self.progress_card.cancel_clicked.connect(self._cancel_scan)
        self.progress_card.hide()
        layout.addWidget(self.progress_card)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["File", "Size", "Path", "Modified"])
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)

        # Configure columns
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.tree)

        # Empty state
        self.empty_state = EmptyStateWidget(
            "🔍",
            "No duplicates found",
            "Click 'Scan' to search for duplicate files"
        )
        self.empty_state.show()
        self.tree.hide()
        layout.addWidget(self.empty_state)

    def _create_toolbar(self) -> QHBoxLayout:
        """Create toolbar with scan and action controls"""
        toolbar = QHBoxLayout()

        # Stats label
        self.stats_label = QLabel("Ready to scan")
        self.stats_label.setProperty("subheading", True)
        toolbar.addWidget(self.stats_label)

        toolbar.addStretch()

        # Scan button
        self.scan_btn = QPushButton("Scan for Duplicates")
        self.scan_btn.clicked.connect(self._start_scan)
        toolbar.addWidget(self.scan_btn)

        # Strategy selector
        strategy_label = QLabel("Auto-select:")
        toolbar.addWidget(strategy_label)

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItem("Keep Oldest", SelectionStrategy.KEEP_OLDEST)
        self.strategy_combo.addItem("Keep Newest", SelectionStrategy.KEEP_NEWEST)
        self.strategy_combo.addItem("Keep Shortest Path", SelectionStrategy.KEEP_SHORTEST_PATH)
        self.strategy_combo.addItem("Keep First Alphabetical", SelectionStrategy.KEEP_FIRST_ALPHABETICAL)
        self.strategy_combo.currentIndexChanged.connect(self._apply_strategy)
        toolbar.addWidget(self.strategy_combo)

        # Delete button
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._delete_selected)
        toolbar.addWidget(self.delete_btn)

        # Move button
        self.move_btn = QPushButton("Move Selected")
        self.move_btn.setProperty("secondary", True)
        self.move_btn.setEnabled(False)
        self.move_btn.clicked.connect(self._move_selected)
        toolbar.addWidget(self.move_btn)

        return toolbar

    def _start_scan(self):
        """Start duplicate scan"""
        # Get scan directory
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Scan",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )

        if not directory:
            return

        # Reset state
        self.tree.clear()
        self.group_manager = None
        self.is_scanning = True

        # Update UI
        self.scan_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.move_btn.setEnabled(False)
        self.progress_card.show()
        self.empty_state.hide()
        self.tree.hide()

        # Start scan in background
        self.scan_thread = ScannerThread(self.scanner, [directory], recursive=True)
        self.scan_thread.progress_updated.connect(self._update_progress)
        self.scan_thread.scan_completed.connect(self._scan_completed)
        self.scan_thread.scan_failed.connect(self._scan_failed)
        self.scan_thread.start()

    def _cancel_scan(self):
        """Cancel ongoing scan"""
        if self.scan_thread and self.scan_thread.isRunning():
            self.scanner.cancel()
            self.scan_thread.wait()

        self.is_scanning = False
        self.scan_btn.setEnabled(True)
        self.progress_card.hide()
        self.empty_state.show()

    def _update_progress(self, progress: ScanProgress):
        """Update progress display"""
        # Update progress bar
        self.progress_card.set_progress(int(progress.progress_percent))

        # Update status
        self.progress_card.set_status(progress.current_phase)

        # Update details
        details = f"Pass {progress.current_pass}/3 - File {progress.current_file}/{progress.total_files}"
        self.progress_card.set_details(details)

    def _scan_completed(self, manager: DuplicateGroupManager):
        """Handle scan completion"""
        self.is_scanning = False
        self.group_manager = manager

        # Update UI
        self.scan_btn.setEnabled(True)
        self.progress_card.hide()

        # Show results
        if manager.groups:
            self._display_results()
            self.tree.show()
            self.empty_state.hide()
            self.delete_btn.setEnabled(True)
            self.move_btn.setEnabled(True)
        else:
            self.tree.hide()
            self.empty_state.show()
            self.stats_label.setText("No duplicates found")

    def _scan_failed(self, error: str):
        """Handle scan failure"""
        self.is_scanning = False
        self.scan_btn.setEnabled(True)
        self.progress_card.hide()
        self.empty_state.show()

        QMessageBox.critical(
            self,
            "Scan Failed",
            f"Failed to scan for duplicates:\n{error}"
        )

    def _display_results(self):
        """Display scan results in tree"""
        if not self.group_manager:
            return

        self.tree.clear()

        # Sort groups by wasted space
        sorted_groups = self.group_manager.sort_by_wasted_space(reverse=True)

        total_wasted = 0
        total_files = 0

        for group in sorted_groups:
            if group.file_count < 2:
                continue

            total_wasted += group.wasted_space
            total_files += group.file_count

            # Create group item
            group_item = QTreeWidgetItem([
                f"{group.file_count} duplicates",
                self._format_size(group.files[0].size),
                f"Wasted: {self._format_size(group.wasted_space)}",
                f"Hash: {group.hash_value[:16]}..."
            ])
            group_item.setExpanded(True)

            # Store group reference
            group_item.setData(0, Qt.ItemDataRole.UserRole, group)

            self.tree.addTopLevelItem(group_item)

            # Add files in group
            for file_info in sorted(group.files, key=lambda x: x.mtime, reverse=True):
                file_item = QTreeWidgetItem([
                    file_info.path.name,
                    self._format_size(file_info.size),
                    str(file_info.path.parent),
                    file_info.mtime_datetime.strftime("%Y-%m-%d %H:%M:%S")
                ])
                file_item.setCheckState(0, Qt.CheckState.Checked if file_info.selected_for_deletion else Qt.CheckState.Unchecked)
                file_item.setData(0, Qt.ItemDataRole.UserRole, file_info)
                group_item.addChild(file_item)

        # Update stats
        self.stats_label.setText(
            f"{len(sorted_groups)} groups, {total_files} duplicates, "
            f"{self._format_size(total_wasted)} wasted"
        )

    def _apply_strategy(self):
        """Apply selected strategy to all groups"""
        if not self.group_manager:
            return

        strategy = self.strategy_combo.currentData()
        if not strategy:
            return

        # Apply strategy
        self.group_manager.apply_strategy_to_all(strategy)

        # Update display
        self._refresh_checkboxes()

    def _refresh_checkboxes(self):
        """Refresh checkbox states from group manager"""
        for i in range(self.tree.topLevelItemCount()):
            group_item = self.tree.topLevelItem(i)

            for j in range(group_item.childCount()):
                file_item = group_item.child(j)
                file_info = file_item.data(0, Qt.ItemDataRole.UserRole)

                if file_info:
                    file_item.setCheckState(
                        0,
                        Qt.CheckState.Checked if file_info.selected_for_deletion else Qt.CheckState.Unchecked
                    )

    def _delete_selected(self):
        """Delete selected files"""
        if not self.group_manager:
            return

        # Collect checked files
        files_to_delete = []

        for i in range(self.tree.topLevelItemCount()):
            group_item = self.tree.topLevelItem(i)

            for j in range(group_item.childCount()):
                file_item = group_item.child(j)
                if file_item.checkState(0) == Qt.CheckState.Checked:
                    file_info = file_item.data(0, Qt.ItemDataRole.UserRole)
                    if file_info:
                        files_to_delete.append(file_info.path)

        if not files_to_delete:
            QMessageBox.information(self, "No Selection", "No files selected for deletion")
            return

        # Calculate space to recover
        total_size = sum(f.stat().st_size for f in files_to_delete if f.exists())

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete {len(files_to_delete)} files?\n"
            f"Space to recover: {self._format_size(total_size)}\n\n"
            f"{'Files will be moved to Recycle Bin.' if HAS_SEND2TRASH else 'WARNING: Permanent deletion (Recycle Bin not available)'}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Execute deletion
        self._execute_deletion(files_to_delete)

    def _execute_deletion(self, file_paths: List[Path]):
        """Execute batch deletion with progress"""
        # Choose action based on availability
        if HAS_SEND2TRASH:
            action = RecycleBinAction(audit_logger=self.audit_logger)
            action_name = "Moving to Recycle Bin"
        else:
            action = PermanentDeleteAction(
                audit_logger=self.audit_logger,
                require_confirmation=False
            )
            action_name = "Deleting"

        # Create progress dialog
        progress = QProgressDialog(
            f"{action_name}...",
            "Cancel",
            0,
            len(file_paths),
            self
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)

        results = []

        for i, file_path in enumerate(file_paths):
            if progress.wasCanceled():
                break

            progress.setValue(i)
            progress.setLabelText(f"{action_name} {file_path.name}...")

            result = action.execute(file_path, confirmed=True)
            results.append(result)

        progress.setValue(len(file_paths))

        # Show summary
        summary = get_action_summary(results)

        QMessageBox.information(
            self,
            "Deletion Complete",
            f"Deleted: {summary['successful']}/{summary['total']} files\n"
            f"Space recovered: {self._format_size(summary['total_bytes_freed'])}\n"
            f"Failed: {summary['failed']}"
        )

        # Refresh display
        self._rescan_quick()

    def _move_selected(self):
        """Move selected files to a folder"""
        if not self.group_manager:
            return

        # Collect checked files
        files_to_move = []

        for i in range(self.tree.topLevelItemCount()):
            group_item = self.tree.topLevelItem(i)

            for j in range(group_item.childCount()):
                file_item = group_item.child(j)
                if file_item.checkState(0) == Qt.CheckState.Checked:
                    file_info = file_item.data(0, Qt.ItemDataRole.UserRole)
                    if file_info:
                        files_to_move.append(file_info.path)

        if not files_to_move:
            QMessageBox.information(self, "No Selection", "No files selected to move")
            return

        # Select destination
        destination = QFileDialog.getExistingDirectory(
            self,
            "Select Destination Folder",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )

        if not destination:
            return

        # Execute move
        action = MoveToFolderAction(audit_logger=self.audit_logger)

        progress = QProgressDialog(
            "Moving files...",
            "Cancel",
            0,
            len(files_to_move),
            self
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)

        results = []

        for i, file_path in enumerate(files_to_move):
            if progress.wasCanceled():
                break

            progress.setValue(i)
            progress.setLabelText(f"Moving {file_path.name}...")

            result = action.execute(file_path, destination)
            results.append(result)

        progress.setValue(len(files_to_move))

        # Show summary
        summary = get_action_summary(results)

        QMessageBox.information(
            self,
            "Move Complete",
            f"Moved: {summary['successful']}/{summary['total']} files\n"
            f"Failed: {summary['failed']}"
        )

        # Refresh display
        self._rescan_quick()

    def _rescan_quick(self):
        """Quick rescan to update display after deletions"""
        # Simply refresh the tree by removing groups where files no longer exist
        for i in range(self.tree.topLevelItemCount() - 1, -1, -1):
            group_item = self.tree.topLevelItem(i)

            # Remove file items that no longer exist
            for j in range(group_item.childCount() - 1, -1, -1):
                file_item = group_item.child(j)
                file_info = file_item.data(0, Qt.ItemDataRole.UserRole)

                if file_info and not file_info.path.exists():
                    group_item.removeChild(file_item)

            # Remove group if it has less than 2 files
            if group_item.childCount() < 2:
                self.tree.takeTopLevelItem(i)

        # Update stats
        if self.tree.topLevelItemCount() == 0:
            self.tree.hide()
            self.empty_state.show()
            self.stats_label.setText("No duplicates found")
        else:
            self._recalculate_stats()

    def _recalculate_stats(self):
        """Recalculate and update stats"""
        total_groups = self.tree.topLevelItemCount()
        total_files = 0
        total_wasted = 0

        for i in range(total_groups):
            group_item = self.tree.topLevelItem(i)
            file_count = group_item.childCount()

            if file_count > 0:
                total_files += file_count

                # Get file size from first child
                first_child = group_item.child(0)
                file_info = first_child.data(0, Qt.ItemDataRole.UserRole)
                if file_info:
                    total_wasted += file_info.size * (file_count - 1)

        self.stats_label.setText(
            f"{total_groups} groups, {total_files} duplicates, "
            f"{self._format_size(total_wasted)} wasted"
        )

    def _show_context_menu(self, position):
        """Show context menu for file items"""
        item = self.tree.itemAt(position)
        if not item or not item.parent():  # Skip group items
            return

        menu = QMenu(self)

        # Keep this file
        keep_action = QAction("Keep This, Delete Others", self)
        keep_action.triggered.connect(lambda: self._keep_file_only(item))
        menu.addAction(keep_action)

        menu.addSeparator()

        # Open location
        open_action = QAction("Open File Location", self)
        open_action.triggered.connect(lambda: self._open_file_location(item))
        menu.addAction(open_action)

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def _keep_file_only(self, item: QTreeWidgetItem):
        """Mark to keep this file and delete all others in group"""
        parent = item.parent()
        if not parent:
            return

        # Uncheck this item, check all others
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child == item:
                child.setCheckState(0, Qt.CheckState.Unchecked)
            else:
                child.setCheckState(0, Qt.CheckState.Checked)

    def _open_file_location(self, item: QTreeWidgetItem):
        """Open file location in system file manager"""
        file_info = item.data(0, Qt.ItemDataRole.UserRole)
        if not file_info:
            return

        import subprocess
        import sys

        path = file_info.path

        if sys.platform == 'win32':
            subprocess.run(['explorer', '/select,', str(path)])
        elif sys.platform == 'darwin':
            subprocess.run(['open', '-R', str(path)])
        else:
            subprocess.run(['xdg-open', str(path.parent)])

    def _format_size(self, size: int) -> str:
        """Format file size for display"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
