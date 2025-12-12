"""
Category Browser - Browse files within a category
Shows files in list/grid view with preview, sort, and filter options
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox,
    QListWidget, QListWidgetItem, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMenu, QFileDialog, QMessageBox, QFrame,
    QButtonGroup, QToolButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QIcon, QPixmap, QFont, QCursor, QAction

from typing import List, Dict, Optional
from pathlib import Path
import os
import subprocess
from datetime import datetime

from categories import FileCategory
from views.category_scanner import CategoryData
from ui.iphone_widgets import RoundedCardWidget
from utils import format_file_size


class CategoryBrowser(QDialog):
    """
    Browse and manage files within a category
    iOS-inspired design with list/grid views
    """

    file_opened = pyqtSignal(str)

    def __init__(self, category: FileCategory,
                 category_data: CategoryData,
                 parent=None):
        super().__init__(parent)

        self.category = category
        self.category_data = category_data
        self.current_files = category_data.files.copy()
        self.view_mode = 'list'  # 'list' or 'grid'

        self.setWindowTitle(f"{category.value} - {category_data.file_count} files")
        self.setMinimumSize(900, 600)

        self._setup_ui()
        self._populate_files()

    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self._create_header(layout)

        # Toolbar
        self._create_toolbar(layout)

        # Content area
        self._create_content_area(layout)

        # Footer
        self._create_footer(layout)

    def _create_header(self, parent_layout: QVBoxLayout):
        """Create header with title and stats"""
        header = QWidget()
        header.setMinimumHeight(70)
        header.setStyleSheet("background-color: palette(base);")

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 15, 20, 15)
        header_layout.setSpacing(12)

        # Category icon and title
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(12)

        # Import category icon
        from ui.iphone_widgets import CategoryIconWidget
        icon = CategoryIconWidget(self.category.value, size=48)
        title_layout.addWidget(icon)

        # Title and subtitle
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        title = QLabel(self.category.value)
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        text_layout.addWidget(title)

        subtitle = QLabel(
            f"{self.category_data.file_count} files • "
            f"{self.category_data.formatted_size}"
        )
        subtitle.setStyleSheet("color: #8E8E93;")
        text_layout.addWidget(subtitle)

        title_layout.addWidget(text_widget)

        header_layout.addWidget(title_widget)
        header_layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)

        parent_layout.addWidget(header)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Plain)
        parent_layout.addWidget(separator)

    def _create_toolbar(self, parent_layout: QVBoxLayout):
        """Create toolbar with search, sort, and view options"""
        toolbar = QWidget()
        toolbar.setMinimumHeight(50)

        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(20, 8, 20, 8)
        toolbar_layout.setSpacing(12)

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search in category...")
        self.search_box.setMinimumWidth(250)
        self.search_box.textChanged.connect(self._on_search_changed)
        toolbar_layout.addWidget(self.search_box)

        toolbar_layout.addStretch()

        # Sort options
        toolbar_layout.addWidget(QLabel("Sort by:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Name", "Date Modified", "Size", "Type"])
        self.sort_combo.currentTextChanged.connect(self._on_sort_changed)
        toolbar_layout.addWidget(self.sort_combo)

        # View mode buttons
        view_group = QButtonGroup(self)

        self.list_view_btn = QToolButton()
        self.list_view_btn.setText("≡")
        self.list_view_btn.setToolTip("List View")
        self.list_view_btn.setCheckable(True)
        self.list_view_btn.setChecked(True)
        self.list_view_btn.clicked.connect(lambda: self._set_view_mode('list'))
        view_group.addButton(self.list_view_btn)
        toolbar_layout.addWidget(self.list_view_btn)

        self.grid_view_btn = QToolButton()
        self.grid_view_btn.setText("▦")
        self.grid_view_btn.setToolTip("Grid View")
        self.grid_view_btn.setCheckable(True)
        self.grid_view_btn.clicked.connect(lambda: self._set_view_mode('grid'))
        view_group.addButton(self.grid_view_btn)
        toolbar_layout.addWidget(self.grid_view_btn)

        parent_layout.addWidget(toolbar)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Plain)
        parent_layout.addWidget(separator)

    def _create_content_area(self, parent_layout: QVBoxLayout):
        """Create content area for file list/grid"""
        # Container for both views
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        # List view (table)
        self.list_view = QTableWidget()
        self.list_view.setColumnCount(4)
        self.list_view.setHorizontalHeaderLabels(
            ["Name", "Date Modified", "Size", "Path"]
        )
        self.list_view.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.list_view.setSelectionMode(
            QTableWidget.SelectionMode.ExtendedSelection
        )
        self.list_view.setAlternatingRowColors(True)
        self.list_view.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.list_view.customContextMenuRequested.connect(
            self._show_context_menu
        )
        self.list_view.itemDoubleClicked.connect(self._on_item_double_clicked)

        # Configure headers
        header = self.list_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.content_layout.addWidget(self.list_view)

        # Grid view (widget grid)
        self.grid_view = QWidget()
        self.grid_layout = QGridLayout(self.grid_view)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(20, 20, 20, 20)
        self.grid_view.hide()

        self.content_layout.addWidget(self.grid_view)

        parent_layout.addWidget(self.content_container, stretch=1)

    def _create_footer(self, parent_layout: QVBoxLayout):
        """Create footer with selection info"""
        footer = QWidget()
        footer.setMinimumHeight(40)

        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 8, 20, 8)

        self.selection_label = QLabel("No files selected")
        self.selection_label.setStyleSheet("color: #8E8E93;")
        footer_layout.addWidget(self.selection_label)

        footer_layout.addStretch()

        parent_layout.addWidget(footer)

    def _populate_files(self):
        """Populate file list/grid"""
        if self.view_mode == 'list':
            self._populate_list_view()
        else:
            self._populate_grid_view()

    def _populate_list_view(self):
        """Populate list (table) view"""
        self.list_view.setRowCount(0)
        self.list_view.setRowCount(len(self.current_files))

        for i, file_info in enumerate(self.current_files):
            # Name
            name_item = QTableWidgetItem(file_info['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, file_info)
            self.list_view.setItem(i, 0, name_item)

            # Date modified
            dt = datetime.fromtimestamp(file_info['modified'])
            date_item = QTableWidgetItem(dt.strftime('%Y-%m-%d %H:%M:%S'))
            self.list_view.setItem(i, 1, date_item)

            # Size
            size_item = QTableWidgetItem(format_file_size(file_info['size']))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.list_view.setItem(i, 2, size_item)

            # Path
            path_item = QTableWidgetItem(os.path.dirname(file_info['path']))
            self.list_view.setItem(i, 3, path_item)

    def _populate_grid_view(self):
        """Populate grid view with cards"""
        # Clear existing grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add file cards
        cols = 4
        for i, file_info in enumerate(self.current_files):
            card = self._create_file_card(file_info)
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(card, row, col)

        # Add stretch at the end
        self.grid_layout.setRowStretch(
            self.grid_layout.rowCount(),
            1
        )

    def _create_file_card(self, file_info: Dict) -> QWidget:
        """Create file card for grid view"""
        card = RoundedCardWidget()
        card.setMinimumSize(150, 140)
        card.setMaximumSize(200, 160)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # File icon/extension
        ext = Path(file_info['name']).suffix
        ext_label = QLabel(ext.upper() if ext else "FILE")
        ext_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = ext_label.font()
        font.setPointSize(16)
        font.setBold(True)
        ext_label.setFont(font)
        ext_label.setStyleSheet("color: #007AFF;")
        layout.addWidget(ext_label)

        # File name
        name = file_info['name']
        if len(name) > 20:
            name = name[:17] + "..."

        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        # File size
        size_label = QLabel(format_file_size(file_info['size']))
        size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        size_label.setStyleSheet("color: #8E8E93; font-size: 9pt;")
        layout.addWidget(size_label)

        # Store file info
        card.file_info = file_info
        card.clicked.connect(lambda: self._open_file(file_info['path']))

        return card

    def _set_view_mode(self, mode: str):
        """Set view mode (list or grid)"""
        self.view_mode = mode

        if mode == 'list':
            self.list_view.show()
            self.grid_view.hide()
            self.list_view_btn.setChecked(True)
        else:
            self.list_view.hide()
            self.grid_view.show()
            self.grid_view_btn.setChecked(True)
            self._populate_grid_view()

    def _on_search_changed(self, text: str):
        """Handle search text change"""
        text_lower = text.lower()

        if not text:
            self.current_files = self.category_data.files.copy()
        else:
            self.current_files = [
                f for f in self.category_data.files
                if text_lower in f['name'].lower()
            ]

        self._populate_files()

    def _on_sort_changed(self, sort_by: str):
        """Handle sort option change"""
        if sort_by == "Name":
            self.current_files.sort(key=lambda x: x['name'].lower())
        elif sort_by == "Date Modified":
            self.current_files.sort(key=lambda x: x['modified'], reverse=True)
        elif sort_by == "Size":
            self.current_files.sort(key=lambda x: x['size'], reverse=True)
        elif sort_by == "Type":
            self.current_files.sort(key=lambda x: x['extension'].lower())

        self._populate_files()

    def _on_item_double_clicked(self, item: QTableWidgetItem):
        """Handle item double click"""
        file_info = self.list_view.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
        if file_info:
            self._open_file(file_info['path'])

    def _open_file(self, path: str):
        """Open file with default application"""
        try:
            os.startfile(path)
            self.file_opened.emit(path)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Could not open file:\n{str(e)}"
            )

    def _show_context_menu(self, pos: QPoint):
        """Show context menu for selected files"""
        selected_rows = set(item.row() for item in self.list_view.selectedItems())

        if not selected_rows:
            return

        menu = QMenu(self)

        # Open action
        open_action = menu.addAction("Open")
        open_action.triggered.connect(self._context_open)

        # Open location action
        location_action = menu.addAction("Open File Location")
        location_action.triggered.connect(self._context_open_location)

        menu.addSeparator()

        # Copy path action
        copy_action = menu.addAction("Copy Path")
        copy_action.triggered.connect(self._context_copy_path)

        menu.addSeparator()

        # Properties action
        props_action = menu.addAction("Properties")
        props_action.triggered.connect(self._context_properties)

        menu.exec(self.list_view.viewport().mapToGlobal(pos))

    def _context_open(self):
        """Open selected files"""
        for row in self._get_selected_rows():
            file_info = self.list_view.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if file_info:
                self._open_file(file_info['path'])

    def _context_open_location(self):
        """Open file location in explorer"""
        selected_rows = self._get_selected_rows()
        if selected_rows:
            file_info = self.list_view.item(
                selected_rows[0], 0
            ).data(Qt.ItemDataRole.UserRole)
            if file_info:
                subprocess.Popen(f'explorer /select,"{file_info["path"]}"')

    def _context_copy_path(self):
        """Copy file paths to clipboard"""
        from PyQt6.QtWidgets import QApplication

        paths = []
        for row in self._get_selected_rows():
            file_info = self.list_view.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if file_info:
                paths.append(file_info['path'])

        if paths:
            QApplication.clipboard().setText('\n'.join(paths))

    def _context_properties(self):
        """Show file properties"""
        selected_rows = self._get_selected_rows()
        if selected_rows:
            file_info = self.list_view.item(
                selected_rows[0], 0
            ).data(Qt.ItemDataRole.UserRole)
            if file_info:
                # Show Windows properties dialog
                os.system(f'explorer /e,/select,"{file_info["path"]}"')

    def _get_selected_rows(self) -> List[int]:
        """Get selected row numbers"""
        return sorted(set(item.row() for item in self.list_view.selectedItems()))


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Test data
    from categories import FileCategory

    test_data = CategoryData(category=FileCategory.IMAGENES)

    # Add some test files
    for i in range(20):
        test_data.add_file({
            'name': f'test_image_{i}.jpg',
            'path': f'C:/test/test_image_{i}.jpg',
            'size': 1024 * (i + 1) * 100,
            'modified': 1700000000 + i * 3600,
            'accessed': 1700000000 + i * 3600,
            'created': 1700000000,
            'extension': '.jpg',
            'mime_type': 'image/jpeg',
        })

    # Show browser
    browser = CategoryBrowser(FileCategory.IMAGENES, test_data)
    browser.exec()
