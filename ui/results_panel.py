"""
Results Panel - Virtual scrolling table view with sorting and selection
Optimized for 1M+ results with true virtual scrolling
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Set, Any
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView,
    QMenu, QLabel, QPushButton, QComboBox, QAbstractItemView, QProgressBar
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QTimer, QAbstractTableModel, QModelIndex,
    QSortFilterProxyModel, QVariant, QSize, QPoint
)
from PyQt6.QtGui import QIcon, QAction, QColor, QMouseEvent
from .widgets import FileIcon, EmptyStateWidget, LoadingSpinner
from .drag_drop import DragDropHandler, DragSource


class VirtualTableModel(QAbstractTableModel):
    """
    High-performance virtual table model with:
    - Lazy loading (fetchMore pattern)
    - Row caching for visible items
    - Efficient sorting
    - Memory-efficient storage
    """

    COLUMNS = ["Name", "Path", "Size", "Type", "Modified"]
    BATCH_SIZE = 500  # Load 500 rows at a time
    CACHE_SIZE = 2000  # Keep 2000 rows in cache

    def __init__(self, parent=None):
        super().__init__(parent)

        # Data storage
        self._all_data: List[Dict] = []  # Full dataset
        self._cached_rows: Dict[int, Dict] = {}  # Row cache: {row_index: data}
        self._loaded_count = 0  # Number of rows currently loaded

        # Sorting
        self._sort_column = 0
        self._sort_order = Qt.SortOrder.AscendingOrder

    def rowCount(self, parent=QModelIndex()) -> int:
        """Return total number of rows"""
        if parent.isValid():
            return 0
        return len(self._all_data)

    def columnCount(self, parent=QModelIndex()) -> int:
        """Return number of columns"""
        if parent.isValid():
            return 0
        return len(self.COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return header data"""
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.COLUMNS[section]
        return QVariant()

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return data for cell"""
        if not index.isValid():
            return QVariant()

        row = index.row()
        col = index.column()

        # Load data if not cached
        if row not in self._cached_rows:
            self._load_row(row)

        if row not in self._cached_rows:
            return QVariant()

        file_info = self._cached_rows[row]

        # Display role
        if role == Qt.ItemDataRole.DisplayRole:
            return self._get_display_data(file_info, col)

        # User role - store full path
        elif role == Qt.ItemDataRole.UserRole:
            return file_info.get('path', '')

        # Background color for alternating rows
        elif role == Qt.ItemDataRole.BackgroundRole:
            if row % 2 == 0:
                return QColor(250, 250, 250)

        # Text alignment
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in [2]:  # Size column - right align
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        return QVariant()

    def _get_display_data(self, file_info: Dict, column: int) -> str:
        """Get display text for column"""
        if column == 0:  # Name
            return file_info.get('name', Path(file_info.get('path', '')).name)
        elif column == 1:  # Path
            return str(Path(file_info.get('path', '')).parent)
        elif column == 2:  # Size
            size = file_info.get('size', 0)
            return self._format_size(size)
        elif column == 3:  # Type
            path = file_info.get('path', '')
            ext = Path(path).suffix.upper()[1:] if Path(path).suffix else "FILE"
            return ext
        elif column == 4:  # Modified
            modified = file_info.get('modified', datetime.now())
            if isinstance(modified, datetime):
                return modified.strftime("%Y-%m-%d %H:%M")
            return str(modified)
        return ""

    def _format_size(self, size: int) -> str:
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def _load_row(self, row: int):
        """Load a single row into cache"""
        if 0 <= row < len(self._all_data):
            self._cached_rows[row] = self._all_data[row]

            # Prune cache if too large
            if len(self._cached_rows) > self.CACHE_SIZE:
                self._prune_cache(row)

    def _prune_cache(self, current_row: int):
        """Prune cache keeping rows near current_row"""
        # Keep rows within CACHE_SIZE/2 distance
        half_cache = self.CACHE_SIZE // 2
        min_row = max(0, current_row - half_cache)
        max_row = min(len(self._all_data), current_row + half_cache)

        # Remove rows outside range
        rows_to_remove = [r for r in self._cached_rows.keys()
                         if r < min_row or r > max_row]
        for r in rows_to_remove:
            del self._cached_rows[r]

    def canFetchMore(self, parent=QModelIndex()) -> bool:
        """Check if more data can be loaded"""
        if parent.isValid():
            return False
        return self._loaded_count < len(self._all_data)

    def fetchMore(self, parent=QModelIndex()):
        """Load more data (lazy loading)"""
        if parent.isValid():
            return

        remainder = len(self._all_data) - self._loaded_count
        items_to_fetch = min(self.BATCH_SIZE, remainder)

        if items_to_fetch <= 0:
            return

        self.beginInsertRows(QModelIndex(), self._loaded_count,
                            self._loaded_count + items_to_fetch - 1)
        self._loaded_count += items_to_fetch
        self.endInsertRows()

    def set_data(self, data: List[Dict]):
        """Set all data (replaces existing)"""
        self.beginResetModel()
        self._all_data = data.copy()
        self._cached_rows.clear()
        self._loaded_count = min(self.BATCH_SIZE, len(self._all_data))
        self.endResetModel()

    def add_data(self, data: List[Dict]):
        """Add data (append to existing)"""
        if not data:
            return

        start_row = len(self._all_data)
        self.beginInsertRows(QModelIndex(), start_row, start_row + len(data) - 1)
        self._all_data.extend(data)
        self._loaded_count = min(self._loaded_count + len(data), len(self._all_data))
        self.endInsertRows()

    def clear_data(self):
        """Clear all data"""
        self.beginResetModel()
        self._all_data.clear()
        self._cached_rows.clear()
        self._loaded_count = 0
        self.endResetModel()

    def get_row_data(self, row: int) -> Optional[Dict]:
        """Get data for specific row"""
        if 0 <= row < len(self._all_data):
            return self._all_data[row]
        return None

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder):
        """Sort data by column"""
        self._sort_column = column
        self._sort_order = order

        self.layoutAboutToBeChanged.emit()

        # Define sort key function
        def sort_key(item: Dict) -> Any:
            if column == 0:  # Name
                return item.get('name', '').lower()
            elif column == 1:  # Path
                return str(Path(item.get('path', '')).parent).lower()
            elif column == 2:  # Size
                return item.get('size', 0)
            elif column == 3:  # Type
                return Path(item.get('path', '')).suffix.lower()
            elif column == 4:  # Modified
                return item.get('modified', datetime.min)
            return ''

        # Sort data
        reverse = (order == Qt.SortOrder.DescendingOrder)
        try:
            self._all_data.sort(key=sort_key, reverse=reverse)
        except Exception as e:
            print(f"Sort error: {e}")

        # Clear cache after sort
        self._cached_rows.clear()

        self.layoutChanged.emit()


class DraggableTableView(QTableView, DragSource):
    """
    TableView with drag support for multi-file selection.
    Supports Ctrl+Drag (copy) and Shift+Drag (move).
    """

    drag_started = pyqtSignal(list)  # Emitted when drag starts

    def __init__(self, parent=None):
        super().__init__(parent)
        self.drag_start_pos = QPoint()
        self.drag_handler = None

    def mousePressEvent(self, event: QMouseEvent):
        """Track mouse press for drag detection"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Detect drag and initiate if threshold exceeded"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            super().mouseMoveEvent(event)
            return

        # Check if we've moved enough to start a drag
        if (event.pos() - self.drag_start_pos).manhattanLength() < 10:
            super().mouseMoveEvent(event)
            return

        # Get selected files
        selected_paths = self._get_selected_paths()

        if not selected_paths or not self.drag_handler:
            super().mouseMoveEvent(event)
            return

        # Emit signal
        self.drag_started.emit(selected_paths)

        # Start drag
        self.start_drag(selected_paths)

    def _get_selected_paths(self) -> List[str]:
        """Get paths of selected rows"""
        paths = []
        for index in self.selectionModel().selectedRows():
            path = self.model().data(index, Qt.ItemDataRole.UserRole)
            if path:
                paths.append(path)
        return paths


class ResultsPanel(QWidget):
    """Results panel with virtual scrolling, multi-select, and drag & drop support"""

    # Signals
    file_selected = pyqtSignal(str)  # Single file path
    files_selected = pyqtSignal(list)  # Multiple file paths
    open_requested = pyqtSignal(list)
    open_location_requested = pyqtSignal(str)
    copy_requested = pyqtSignal(list)
    move_requested = pyqtSignal(list)
    delete_requested = pyqtSignal(list)
    export_requested = pyqtSignal()  # Export all
    export_selected_requested = pyqtSignal()  # Export selected only

    def __init__(self, parent=None):
        super().__init__(parent)

        # State
        self.selected_paths: Set[str] = set()

        # Loading state
        self._loading = False
        self._load_timer = QTimer()
        self._load_timer.timeout.connect(self._on_load_progress)

        # Drag & Drop handler
        self.drag_handler = DragDropHandler(self)
        self.drag_handler.drag_started.connect(self._on_drag_started)
        self.drag_handler.drag_completed.connect(self._on_drag_completed)

        self._init_ui()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addLayout(toolbar)

        # Loading indicator
        self.loading_widget = QWidget()
        loading_layout = QHBoxLayout(self.loading_widget)
        loading_layout.setContentsMargins(8, 8, 8, 8)

        self.loading_spinner = LoadingSpinner(size=24)
        loading_layout.addWidget(self.loading_spinner)

        self.loading_label = QLabel("Loading results...")
        loading_layout.addWidget(self.loading_label)

        self.loading_progress = QProgressBar()
        self.loading_progress.setMaximum(100)
        self.loading_progress.setTextVisible(True)
        loading_layout.addWidget(self.loading_progress)

        loading_layout.addStretch()

        self.loading_widget.hide()
        layout.addWidget(self.loading_widget)

        # Create model and view
        self.model = VirtualTableModel(self)

        # Table view with drag support
        self.table = DraggableTableView()
        self.table.setModel(self.model)

        # Setup drag handler for table
        self.table.drag_handler = self.drag_handler
        self.table.drag_started.connect(self._on_table_drag_started)

        # Configure table
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Performance optimizations
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        # Configure columns
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Path
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Size
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Type
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # Modified

        self.table.setColumnWidth(0, 300)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 150)

        # Enable sorting
        header.setSortIndicatorShown(True)
        header.sortIndicatorChanged.connect(self._on_header_sort)

        # Connect signals
        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.table.doubleClicked.connect(self._on_item_double_clicked)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.table)

        # Empty state (hidden initially)
        self.empty_state = EmptyStateWidget(
            "🔍",
            "No results yet",
            "Start a search to find files"
        )
        self.empty_state.hide()
        layout.addWidget(self.empty_state)

    def _create_toolbar(self) -> QHBoxLayout:
        """Create results toolbar"""
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        # Results count
        self.count_label = QLabel("0 files")
        self.count_label.setStyleSheet("font-weight: 600;")
        toolbar.addWidget(self.count_label)

        toolbar.addStretch()

        # View mode selector
        view_label = QLabel("View:")
        toolbar.addWidget(view_label)

        self.view_combo = QComboBox()
        self.view_combo.addItems(["Details", "List", "Tiles"])
        self.view_combo.setProperty("secondary", True)
        toolbar.addWidget(self.view_combo)

        # Sort selector
        sort_label = QLabel("Sort:")
        toolbar.addWidget(sort_label)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Name", "Path", "Size", "Type", "Date Modified"])
        self.sort_combo.setProperty("secondary", True)
        self.sort_combo.currentTextChanged.connect(self._on_sort_changed)
        toolbar.addWidget(self.sort_combo)

        # Sort order button
        self.sort_order_btn = QPushButton("↓")
        self.sort_order_btn.setFixedSize(32, 32)
        self.sort_order_btn.setProperty("secondary", True)
        self.sort_order_btn.setCheckable(True)
        self.sort_order_btn.clicked.connect(self._toggle_sort_order)
        toolbar.addWidget(self.sort_order_btn)

        # Select all button
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setProperty("secondary", True)
        self.select_all_btn.clicked.connect(self.select_all)
        toolbar.addWidget(self.select_all_btn)

        return toolbar

    def add_result(self, file_info: Dict):
        """Add single result"""
        self.model.add_data([file_info])
        self._update_display()

    def add_results(self, file_infos: List[Dict]):
        """Add multiple results with loading indication"""
        if not file_infos:
            return

        # For large datasets, show loading indicator
        if len(file_infos) > 1000:
            self._start_loading(len(file_infos))

        self.model.add_data(file_infos)
        self._update_display()

        if len(file_infos) > 1000:
            self._stop_loading()

    def set_results(self, file_infos: List[Dict]):
        """Set results (replaces existing)"""
        if not file_infos:
            self.clear_results()
            return

        # For large datasets, show loading indicator
        if len(file_infos) > 1000:
            self._start_loading(len(file_infos))

        self.model.set_data(file_infos)
        self._update_display()

        if len(file_infos) > 1000:
            self._stop_loading()

    def clear_results(self):
        """Clear all results"""
        self.model.clear_data()
        self.selected_paths.clear()
        self._update_count()
        self._show_empty_state(True)

    def _update_display(self):
        """Update table display"""
        # Update count
        self._update_count()

        # Show/hide empty state
        has_data = self.model.rowCount() > 0
        self._show_empty_state(not has_data)

    def _update_count(self):
        """Update results count label"""
        total = self.model.rowCount()
        selected = len(self.selected_paths)

        if selected > 0:
            self.count_label.setText(f"{selected} of {total} files selected")
        else:
            self.count_label.setText(f"{total:,} files")

    def _show_empty_state(self, show: bool):
        """Show/hide empty state"""
        self.table.setVisible(not show)
        self.empty_state.setVisible(show)

    def _on_selection_changed(self):
        """Handle selection change"""
        self.selected_paths.clear()

        # Get selected rows
        selected_indexes = self.table.selectionModel().selectedRows()

        for index in selected_indexes:
            path = self.model.data(index, Qt.ItemDataRole.UserRole)
            if path:
                self.selected_paths.add(path)

        self._update_count()

        # Emit signals
        paths = list(self.selected_paths)
        self.files_selected.emit(paths)

        if len(paths) == 1:
            self.file_selected.emit(paths[0])

    def _on_item_double_clicked(self, index: QModelIndex):
        """Handle double click - open file"""
        path = self.model.data(index, Qt.ItemDataRole.UserRole)
        if path:
            self.open_requested.emit([path])

    def _on_sort_changed(self, sort_by: str):
        """Handle sort change"""
        column_map = {
            "Name": 0,
            "Path": 1,
            "Size": 2,
            "Type": 3,
            "Date Modified": 4,
        }

        column = column_map.get(sort_by, 0)
        order = Qt.SortOrder.DescendingOrder if self.sort_order_btn.isChecked() else Qt.SortOrder.AscendingOrder
        self.model.sort(column, order)

    def _on_header_sort(self, column: int, order: Qt.SortOrder):
        """Handle header click sorting"""
        self.model.sort(column, order)

        # Update combo box
        column_names = ["Name", "Path", "Size", "Type", "Date Modified"]
        if 0 <= column < len(column_names):
            self.sort_combo.blockSignals(True)
            self.sort_combo.setCurrentText(column_names[column])
            self.sort_combo.blockSignals(False)

        # Update sort order button
        self.sort_order_btn.blockSignals(True)
        self.sort_order_btn.setChecked(order == Qt.SortOrder.DescendingOrder)
        self.sort_order_btn.setText("↑" if order == Qt.SortOrder.DescendingOrder else "↓")
        self.sort_order_btn.blockSignals(False)

    def _toggle_sort_order(self):
        """Toggle sort order"""
        if self.sort_order_btn.isChecked():
            self.sort_order_btn.setText("↑")
        else:
            self.sort_order_btn.setText("↓")

        self._on_sort_changed(self.sort_combo.currentText())

    def _show_context_menu(self, position):
        """Show context menu"""
        if not self.selected_paths:
            return

        menu = QMenu(self)
        paths = list(self.selected_paths)

        # Open
        open_action = QAction("📂 Open", self)
        open_action.triggered.connect(lambda: self.open_requested.emit(paths))
        menu.addAction(open_action)

        # Open location
        if len(paths) == 1:
            open_loc_action = QAction("📍 Open Location", self)
            open_loc_action.triggered.connect(lambda: self.open_location_requested.emit(paths[0]))
            menu.addAction(open_loc_action)

        menu.addSeparator()

        # Copy
        copy_action = QAction("📋 Copy to...", self)
        copy_action.triggered.connect(lambda: self.copy_requested.emit(paths))
        menu.addAction(copy_action)

        # Move
        move_action = QAction("✂ Move to...", self)
        move_action.triggered.connect(lambda: self.move_requested.emit(paths))
        menu.addAction(move_action)

        menu.addSeparator()

        # Copy path
        copy_path_action = QAction("📄 Copy Path", self)
        copy_path_action.triggered.connect(self._copy_paths_to_clipboard)
        menu.addAction(copy_path_action)

        menu.addSeparator()

        # Export
        export_selected_action = QAction("💾 Export Selected...", self)
        export_selected_action.triggered.connect(self.export_selected_requested.emit)
        menu.addAction(export_selected_action)

        export_all_action = QAction("💾 Export All Results...", self)
        export_all_action.triggered.connect(self.export_requested.emit)
        menu.addAction(export_all_action)

        menu.addSeparator()

        # Delete
        delete_action = QAction("🗑 Delete", self)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(paths))
        menu.addAction(delete_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def _copy_paths_to_clipboard(self):
        """Copy selected paths to clipboard"""
        from PyQt6.QtWidgets import QApplication
        paths_text = '\n'.join(sorted(self.selected_paths))
        QApplication.clipboard().setText(paths_text)

    def _start_loading(self, total: int):
        """Start loading indication"""
        self._loading = True
        self.loading_widget.show()
        self.loading_spinner.start()
        self.loading_progress.setMaximum(total)
        self.loading_progress.setValue(0)

    def _stop_loading(self):
        """Stop loading indication"""
        self._loading = False
        self.loading_widget.hide()
        self.loading_spinner.stop()

    def _on_load_progress(self):
        """Update loading progress"""
        if self._loading:
            current = self.model.rowCount()
            self.loading_progress.setValue(current)
            self.loading_label.setText(f"Loading results... {current:,}")

    def select_all(self):
        """Select all items"""
        self.table.selectAll()

    def select_none(self):
        """Deselect all items"""
        self.table.clearSelection()

    def get_selected_files(self) -> List[str]:
        """Get selected file paths"""
        return list(self.selected_paths)

    def get_all_files(self) -> List[Dict]:
        """Get all file results"""
        return self.model._all_data.copy()

    def filter_results(self, predicate) -> List[Dict]:
        """Filter results by predicate function"""
        return [r for r in self.model._all_data if predicate(r)]

    def export_results(self, format: str = 'csv') -> str:
        """Export results to format"""
        # TODO: Implement export functionality
        pass

    def _on_drag_started(self, file_paths: List[str]):
        """Handle drag start"""
        # Update status or show feedback
        pass

    def _on_drag_completed(self, operation: str):
        """Handle drag completion"""
        # If move operation, could remove from results
        if operation == "move":
            # Files were moved - optionally update UI
            pass

    def _on_table_drag_started(self, file_paths: List[str]):
        """Handle table drag start (forwarding)"""
        # Can add additional handling here
        pass
