"""
Comparison Panel - PyQt6 UI for folder comparison

Features:
- Dual directory selectors with drag & drop
- Comparison mode selection
- Results table with filtering
- Batch actions (copy, delete, sync)
- Export reports (CSV, HTML)
- Statistics panel
- Progress tracking
"""

import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QProgressDialog, QMenu,
    QLineEdit, QCheckBox, QGroupBox, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QColor, QIcon, QDragEnterEvent, QDropEvent

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from comparison.folder_comparator import (
    FolderComparator,
    ComparisonMode,
    ComparisonResult,
    FileStatus,
    format_size
)
from comparison.sync_engine import (
    SyncEngine,
    ConflictResolution,
    SyncResult,
    format_sync_summary
)
from core.logger import get_logger

logger = get_logger(__name__)


# Status icons and colors
STATUS_ICONS = {
    FileStatus.SAME: "✓",
    FileStatus.DIFFERENT: "⚠",
    FileStatus.MISSING_IN_TARGET: "←",
    FileStatus.EXTRA_IN_TARGET: "→"
}

STATUS_COLORS = {
    FileStatus.SAME: QColor(46, 204, 113),       # Green
    FileStatus.DIFFERENT: QColor(230, 126, 34),  # Orange
    FileStatus.MISSING_IN_TARGET: QColor(231, 76, 60),   # Red
    FileStatus.EXTRA_IN_TARGET: QColor(241, 196, 15)     # Yellow
}


class ComparisonThread(QThread):
    """Background thread for directory comparison."""

    progress_updated = pyqtSignal(int, int)
    comparison_completed = pyqtSignal(object)  # ComparisonResult
    comparison_failed = pyqtSignal(str)

    def __init__(
        self,
        source: Path,
        target: Path,
        mode: ComparisonMode,
        recursive: bool = True
    ):
        super().__init__()
        self.source = source
        self.target = target
        self.mode = mode
        self.recursive = recursive

    def run(self):
        """Execute comparison in background."""
        try:
            comparator = FolderComparator(mode=self.mode)
            result = comparator.compare(
                source=self.source,
                target=self.target,
                recursive=self.recursive,
                progress_callback=self.progress_updated.emit
            )
            self.comparison_completed.emit(result)

        except Exception as e:
            self.comparison_failed.emit(str(e))


class SyncThread(QThread):
    """Background thread for sync operations."""

    progress_updated = pyqtSignal(int, int)
    sync_completed = pyqtSignal(object)  # SyncResult
    sync_failed = pyqtSignal(str)

    def __init__(
        self,
        source: Path,
        target: Path,
        copy_missing: bool,
        delete_extra: bool,
        update_different: bool,
        dry_run: bool = False
    ):
        super().__init__()
        self.source = source
        self.target = target
        self.copy_missing = copy_missing
        self.delete_extra = delete_extra
        self.update_different = update_different
        self.dry_run = dry_run

    def run(self):
        """Execute sync in background."""
        try:
            engine = SyncEngine(conflict_resolution=ConflictResolution.NEWER_WINS)
            result = engine.sync(
                source=self.source,
                target=self.target,
                copy_missing=self.copy_missing,
                delete_extra=self.delete_extra,
                update_different=self.update_different,
                dry_run=self.dry_run,
                progress_callback=self.progress_updated.emit
            )
            self.sync_completed.emit(result)

        except Exception as e:
            self.sync_failed.emit(str(e))


class DirectorySelector(QFrame):
    """Widget for selecting a directory with drag & drop support."""

    directory_changed = pyqtSignal(Path)

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.current_path: Optional[Path] = None

        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            DirectorySelector {
                background-color: #F9F9F9;
                border: 2px dashed #CCCCCC;
                border-radius: 8px;
                padding: 8px;
            }
            DirectorySelector:hover {
                border-color: #0078D4;
                background-color: #F3F3F3;
            }
        """)

        layout = QHBoxLayout(self)

        # Label
        self.label = QLabel(label)
        self.label.setProperty("heading", True)
        layout.addWidget(self.label)

        # Path display
        self.path_label = QLabel("No directory selected")
        self.path_label.setStyleSheet("color: #999999;")
        layout.addWidget(self.path_label, 1)

        # Browse button
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse)
        layout.addWidget(browse_btn)

    def _browse(self):
        """Open directory selection dialog."""
        directory = QFileDialog.getExistingDirectory(
            self,
            f"Select {self.label.text()}",
            str(self.current_path) if self.current_path else ""
        )

        if directory:
            self.set_directory(Path(directory))

    def set_directory(self, path: Path):
        """Set the selected directory."""
        if path and path.is_dir():
            self.current_path = path
            self.path_label.setText(str(path))
            self.path_label.setStyleSheet("color: #000000;")
            self.directory_changed.emit(path)

    def get_directory(self) -> Optional[Path]:
        """Get current directory."""
        return self.current_path

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Handle drop."""
        urls = event.mimeData().urls()
        if urls:
            path = Path(urls[0].toLocalFile())
            if path.is_dir():
                self.set_directory(path)


class ComparisonPanel(QWidget):
    """Main panel for folder comparison."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # State
        self.comparison_result: Optional[ComparisonResult] = None
        self.comparison_thread: Optional[ComparisonThread] = None
        self.sync_thread: Optional[SyncThread] = None

        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header_label = QLabel("Folder Comparison")
        header_label.setProperty("heading", True)
        layout.addWidget(header_label)

        # Directory selectors
        selectors_group = QGroupBox("Directories")
        selectors_layout = QVBoxLayout(selectors_group)

        self.source_selector = DirectorySelector("Source Directory")
        selectors_layout.addWidget(self.source_selector)

        self.target_selector = DirectorySelector("Target Directory")
        selectors_layout.addWidget(self.target_selector)

        # Swap button
        swap_layout = QHBoxLayout()
        swap_layout.addStretch()
        swap_btn = QPushButton("⇅ Swap")
        swap_btn.setToolTip("Swap source and target")
        swap_btn.clicked.connect(self._swap_directories)
        swap_layout.addWidget(swap_btn)
        selectors_layout.addLayout(swap_layout)

        layout.addWidget(selectors_group)

        # Options
        options_group = QGroupBox("Comparison Options")
        options_layout = QHBoxLayout(options_group)

        # Mode selector
        options_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Content Hash (Accurate)", ComparisonMode.CONTENT_HASH)
        self.mode_combo.addItem("Size + Name (Fast)", ComparisonMode.SIZE_NAME)
        self.mode_combo.addItem("Name Only", ComparisonMode.NAME_ONLY)
        options_layout.addWidget(self.mode_combo)

        # Recursive checkbox
        self.recursive_check = QCheckBox("Recursive")
        self.recursive_check.setChecked(True)
        options_layout.addWidget(self.recursive_check)

        options_layout.addStretch()

        # Compare button
        self.compare_btn = QPushButton("Compare Directories")
        self.compare_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        self.compare_btn.clicked.connect(self._start_comparison)
        options_layout.addWidget(self.compare_btn)

        layout.addWidget(options_group)

        # Stats panel
        self.stats_label = QLabel("Ready to compare")
        self.stats_label.setStyleSheet("padding: 8px; background-color: #F3F3F3; border-radius: 4px;")
        layout.addWidget(self.stats_label)

        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Files", None)
        self.filter_combo.addItem("Same", FileStatus.SAME)
        self.filter_combo.addItem("Different", FileStatus.DIFFERENT)
        self.filter_combo.addItem("Missing in Target", FileStatus.MISSING_IN_TARGET)
        self.filter_combo.addItem("Extra in Target", FileStatus.EXTRA_IN_TARGET)
        self.filter_combo.currentIndexChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.filter_combo)

        filter_layout.addStretch()

        # Action buttons
        self.copy_missing_btn = QPushButton("Copy Missing to Target")
        self.copy_missing_btn.clicked.connect(self._copy_missing)
        self.copy_missing_btn.setEnabled(False)
        filter_layout.addWidget(self.copy_missing_btn)

        self.delete_extra_btn = QPushButton("Delete Extra from Target")
        self.delete_extra_btn.clicked.connect(self._delete_extra)
        self.delete_extra_btn.setEnabled(False)
        filter_layout.addWidget(self.delete_extra_btn)

        self.sync_btn = QPushButton("Sync All")
        self.sync_btn.clicked.connect(self._sync_all)
        self.sync_btn.setEnabled(False)
        filter_layout.addWidget(self.sync_btn)

        layout.addLayout(filter_layout)

        # Results table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Status", "File Name", "Source Path", "Target Path", "Size", "Modified"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Configure columns
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table)

        # Export button
        export_layout = QHBoxLayout()
        export_layout.addStretch()

        export_btn = QPushButton("Export Report")
        export_btn.clicked.connect(self._export_report)
        export_layout.addWidget(export_btn)

        layout.addLayout(export_layout)

    def _swap_directories(self):
        """Swap source and target directories."""
        source_path = self.source_selector.get_directory()
        target_path = self.target_selector.get_directory()

        if source_path:
            self.target_selector.set_directory(source_path)
        if target_path:
            self.source_selector.set_directory(target_path)

    def _start_comparison(self):
        """Start directory comparison."""
        source = self.source_selector.get_directory()
        target = self.target_selector.get_directory()

        if not source or not target:
            QMessageBox.warning(
                self,
                "Missing Directories",
                "Please select both source and target directories."
            )
            return

        if source == target:
            QMessageBox.warning(
                self,
                "Same Directory",
                "Source and target cannot be the same directory."
            )
            return

        # Get options
        mode = self.mode_combo.currentData()
        recursive = self.recursive_check.isChecked()

        # Disable UI
        self.compare_btn.setEnabled(False)
        self.stats_label.setText("Comparing directories...")

        # Start comparison thread
        self.comparison_thread = ComparisonThread(source, target, mode, recursive)
        self.comparison_thread.comparison_completed.connect(self._on_comparison_completed)
        self.comparison_thread.comparison_failed.connect(self._on_comparison_failed)
        self.comparison_thread.start()

    def _on_comparison_completed(self, result: ComparisonResult):
        """Handle comparison completion."""
        self.comparison_result = result
        self._populate_table()
        self._update_stats()

        # Enable action buttons
        self.copy_missing_btn.setEnabled(result.stats.missing_in_target > 0)
        self.delete_extra_btn.setEnabled(result.stats.extra_in_target > 0)
        self.sync_btn.setEnabled(True)
        self.compare_btn.setEnabled(True)

    def _on_comparison_failed(self, error: str):
        """Handle comparison failure."""
        self.compare_btn.setEnabled(True)
        self.stats_label.setText("Comparison failed")
        QMessageBox.critical(self, "Comparison Failed", f"Error: {error}")

    def _populate_table(self):
        """Populate results table."""
        if not self.comparison_result:
            return

        self.table.setRowCount(0)

        for comp in self.comparison_result.comparisons:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Status
            status_item = QTableWidgetItem(f"{STATUS_ICONS[comp.status]} {comp.status.value}")
            status_item.setBackground(STATUS_COLORS[comp.status])
            status_item.setData(Qt.ItemDataRole.UserRole, comp.status)
            self.table.setItem(row, 0, status_item)

            # File name
            file_name = Path(comp.relative_path).name
            self.table.setItem(row, 1, QTableWidgetItem(file_name))

            # Source path
            source_text = str(comp.source_path) if comp.source_path else "-"
            self.table.setItem(row, 2, QTableWidgetItem(source_text))

            # Target path
            target_text = str(comp.target_path) if comp.target_path else "-"
            self.table.setItem(row, 3, QTableWidgetItem(target_text))

            # Size
            size_text = format_size(comp.source_size or comp.target_size)
            self.table.setItem(row, 4, QTableWidgetItem(size_text))

            # Modified
            modified = comp.source_modified or comp.target_modified
            modified_text = modified.strftime("%Y-%m-%d %H:%M") if modified else "-"
            self.table.setItem(row, 5, QTableWidgetItem(modified_text))

    def _apply_filter(self):
        """Apply status filter to table."""
        filter_status = self.filter_combo.currentData()

        for row in range(self.table.rowCount()):
            status_item = self.table.item(row, 0)
            if status_item:
                status = status_item.data(Qt.ItemDataRole.UserRole)
                if filter_status is None or status == filter_status:
                    self.table.setRowHidden(row, False)
                else:
                    self.table.setRowHidden(row, True)

    def _update_stats(self):
        """Update statistics display."""
        if not self.comparison_result:
            return

        stats = self.comparison_result.stats
        text = (
            f"Total: {stats.total_files} | "
            f"Same: {stats.same_files} | "
            f"Different: {stats.different_files} | "
            f"Missing: {stats.missing_in_target} | "
            f"Extra: {stats.extra_in_target} | "
            f"Space Savings: {format_size(stats.space_savings_potential)}"
        )
        self.stats_label.setText(text)

    def _copy_missing(self):
        """Copy missing files to target."""
        if not self.comparison_result:
            return

        missing = self.comparison_result.stats.missing_in_target
        reply = QMessageBox.question(
            self,
            "Copy Missing Files",
            f"Copy {missing} missing file(s) to target directory?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._execute_sync(copy_missing=True, delete_extra=False, update_different=False)

    def _delete_extra(self):
        """Delete extra files from target."""
        if not self.comparison_result:
            return

        extra = self.comparison_result.stats.extra_in_target
        reply = QMessageBox.warning(
            self,
            "Delete Extra Files",
            f"Delete {extra} extra file(s) from target directory?\n\nThis cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._execute_sync(copy_missing=False, delete_extra=True, update_different=False)

    def _sync_all(self):
        """Synchronize all files."""
        if not self.comparison_result:
            return

        reply = QMessageBox.question(
            self,
            "Sync All",
            "Synchronize all files? This will:\n"
            "- Copy missing files to target\n"
            "- Update different files (newer wins)\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._execute_sync(copy_missing=True, delete_extra=False, update_different=True)

    def _execute_sync(self, copy_missing: bool, delete_extra: bool, update_different: bool):
        """Execute sync operation."""
        source = self.source_selector.get_directory()
        target = self.target_selector.get_directory()

        if not source or not target:
            return

        # Progress dialog
        progress = QProgressDialog("Synchronizing...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        # Start sync thread
        self.sync_thread = SyncThread(
            source, target, copy_missing, delete_extra, update_different, dry_run=False
        )

        def on_progress(current, total):
            if total > 0:
                progress.setValue(int((current / total) * 100))

        self.sync_thread.progress_updated.connect(on_progress)
        self.sync_thread.sync_completed.connect(
            lambda result: self._on_sync_completed(result, progress)
        )
        self.sync_thread.sync_failed.connect(
            lambda error: self._on_sync_failed(error, progress)
        )
        self.sync_thread.start()

    def _on_sync_completed(self, result: SyncResult, progress: QProgressDialog):
        """Handle sync completion."""
        progress.close()

        summary = format_sync_summary(result)
        QMessageBox.information(self, "Sync Complete", summary)

        # Refresh comparison
        self._start_comparison()

    def _on_sync_failed(self, error: str, progress: QProgressDialog):
        """Handle sync failure."""
        progress.close()
        QMessageBox.critical(self, "Sync Failed", f"Error: {error}")

    def _show_context_menu(self, position):
        """Show context menu for table."""
        menu = QMenu(self)

        # Get selected row
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        # Add actions based on status
        status_item = self.table.item(row, 0)
        if status_item:
            status = status_item.data(Qt.ItemDataRole.UserRole)

            if status == FileStatus.MISSING_IN_TARGET:
                copy_action = menu.addAction("Copy to Target")
                copy_action.triggered.connect(lambda: self._copy_file(row))

            elif status == FileStatus.EXTRA_IN_TARGET:
                delete_action = menu.addAction("Delete from Target")
                delete_action.triggered.connect(lambda: self._delete_file(row))

        menu.exec(self.table.viewport().mapToGlobal(position))

    def _copy_file(self, row: int):
        """Copy single file to target."""
        # Implementation for single file copy
        pass

    def _delete_file(self, row: int):
        """Delete single file from target."""
        # Implementation for single file delete
        pass

    def _export_report(self):
        """Export comparison report."""
        if not self.comparison_result:
            QMessageBox.warning(self, "No Data", "No comparison data to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Report",
            f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv);;HTML Files (*.html)"
        )

        if not file_path:
            return

        try:
            if file_path.endswith('.csv'):
                self._export_csv(file_path)
            elif file_path.endswith('.html'):
                self._export_html(file_path)

            QMessageBox.information(self, "Export Complete", f"Report saved to:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Error: {e}")

    def _export_csv(self, file_path: str):
        """Export to CSV."""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Status', 'Relative Path', 'Source Path', 'Target Path', 'Size', 'Modified'])

            for comp in self.comparison_result.comparisons:
                writer.writerow([
                    comp.status.value,
                    comp.relative_path,
                    str(comp.source_path) if comp.source_path else '',
                    str(comp.target_path) if comp.target_path else '',
                    comp.source_size or comp.target_size,
                    (comp.source_modified or comp.target_modified).isoformat() if (comp.source_modified or comp.target_modified) else ''
                ])

    def _export_html(self, file_path: str):
        """Export to HTML."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Folder Comparison Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #0078D4; color: white; }}
        .same {{ background-color: #d4edda; }}
        .different {{ background-color: #fff3cd; }}
        .missing {{ background-color: #f8d7da; }}
        .extra {{ background-color: #d1ecf1; }}
    </style>
</head>
<body>
    <h1>Folder Comparison Report</h1>
    <p><strong>Source:</strong> {self.comparison_result.source_dir}</p>
    <p><strong>Target:</strong> {self.comparison_result.target_dir}</p>
    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <h2>Statistics</h2>
    <ul>
        <li>Total Files: {self.comparison_result.stats.total_files}</li>
        <li>Same: {self.comparison_result.stats.same_files}</li>
        <li>Different: {self.comparison_result.stats.different_files}</li>
        <li>Missing in Target: {self.comparison_result.stats.missing_in_target}</li>
        <li>Extra in Target: {self.comparison_result.stats.extra_in_target}</li>
    </ul>
    <h2>Files</h2>
    <table>
        <tr>
            <th>Status</th>
            <th>File</th>
            <th>Size</th>
            <th>Modified</th>
        </tr>
"""

        for comp in self.comparison_result.comparisons:
            row_class = {
                FileStatus.SAME: 'same',
                FileStatus.DIFFERENT: 'different',
                FileStatus.MISSING_IN_TARGET: 'missing',
                FileStatus.EXTRA_IN_TARGET: 'extra'
            }[comp.status]

            modified = comp.source_modified or comp.target_modified
            modified_str = modified.strftime('%Y-%m-%d %H:%M') if modified else '-'

            html += f"""
        <tr class="{row_class}">
            <td>{comp.status.value}</td>
            <td>{comp.relative_path}</td>
            <td>{format_size(comp.source_size or comp.target_size)}</td>
            <td>{modified_str}</td>
        </tr>
"""

        html += """
    </table>
</body>
</html>
"""

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html)
