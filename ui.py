"""
Smart Search UI - PyQt6 Interface
Modern Windows file search tool with advanced filtering and directory management

Usage:
    from ui import SmartSearchWindow
    app = QApplication(sys.argv)
    window = SmartSearchWindow()
    window.show()
    sys.exit(app.exec())
"""

import sys
import os
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Optional
from enum import Enum

# Configurar logger
logger = logging.getLogger(__name__)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, QTabWidget,
    QTableWidget, QTableWidgetItem, QSplitter, QLabel, QComboBox,
    QFileDialog, QProgressBar, QMessageBox, QMenu, QHeaderView,
    QCheckBox, QGroupBox, QSpinBox, QDateEdit, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QDate, QTimer
from PyQt6.QtGui import QIcon, QAction, QKeySequence, QFont, QPalette, QColor


class FileOperation(Enum):
    """File operation types"""
    COPY = "copy"
    MOVE = "move"


# Importar utilidades compartidas
from utils import format_file_size

# Importar validación de seguridad para apertura de archivos
from core.security import validate_safe_file_type

# Importar sistema unificado de categorías
try:
    from categories import FileCategory as FileType, classify_by_extension

    # Wrapper para compatibilidad con código existente
    def _get_category_wrapper(filename: str) -> FileType:
        """Get file category based on extension"""
        ext = Path(filename).suffix.lower()
        return classify_by_extension(ext)

    # Asignar como método estático
    FileType.get_category = staticmethod(_get_category_wrapper)

except ImportError:
    # Fallback si categories.py no está disponible
    class FileType(Enum):
        """File type categories for tab organization"""
        DOCUMENTOS = ("Documents", [".pdf", ".doc", ".docx", ".txt", ".odt", ".rtf", ".xls", ".xlsx", ".ppt", ".pptx"])
        IMAGENES = ("Images", [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico", ".webp", ".tiff"])
        VIDEOS = ("Videos", [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"])
        AUDIO = ("Audio", [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"])
        COMPRIMIDOS = ("Archives", [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"])
        CODIGO = ("Code", [".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".cs", ".php", ".go", ".rs", ".html", ".css"])
        EJECUTABLES = ("Executables", [".exe", ".msi", ".bat", ".cmd", ".ps1", ".sh"])
        OTROS = ("Other", [])

        def __init__(self, display_name: str, extensions: List[str]):
            self.display_name = display_name
            self.extensions = extensions

        @classmethod
        def get_category(cls, filename: str) -> 'FileType':
            """Get file category based on extension"""
            ext = Path(filename).suffix.lower()
            for file_type in cls:
                if ext in file_type.extensions:
                    return file_type
            return cls.OTROS


class SearchWorker(QThread):
    """Background worker for file search operations"""
    progress = pyqtSignal(int, str)  # progress percentage, current file
    result = pyqtSignal(dict)  # file info dict
    finished = pyqtSignal(int)  # total files found
    error = pyqtSignal(str)  # error message

    def __init__(self, search_paths: List[str], search_term: str, case_sensitive: bool = False):
        super().__init__()
        self.search_paths = search_paths
        self.search_term = search_term
        self.case_sensitive = case_sensitive
        self._cancel_requested = threading.Event()
        self.files_found = 0

    def run(self):
        """Execute search in background"""
        try:
            for search_path in self.search_paths:
                if self._cancel_requested.is_set():
                    break
                self._search_directory(search_path)

            if not self._cancel_requested.is_set():
                self.finished.emit(self.files_found)
            else:
                self.finished.emit(0)
        except Exception as e:
            if not self._cancel_requested.is_set():
                self.error.emit(str(e))
                logger.exception(f"Error in search worker: {e}")

    def _search_directory(self, path: str):
        """Recursively search directory"""
        try:
            for root, dirs, files in os.walk(path):
                if self._cancel_requested.is_set():
                    break

                for filename in files:
                    if self._cancel_requested.is_set():
                        break

                    # Check if filename matches search term
                    if self._matches_search(filename):
                        file_path = os.path.join(root, filename)
                        try:
                            file_info = self._get_file_info(file_path)
                            self.result.emit(file_info)
                            self.files_found += 1

                            if self.files_found % 10 == 0:
                                self.progress.emit(0, file_path)
                        except (PermissionError, FileNotFoundError) as e:
                            logger.debug(f"Permission/File error: {e}")
                            continue
        except PermissionError as e:
            logger.debug(f"Permission denied for directory: {path}")
            pass

    def _matches_search(self, filename: str) -> bool:
        """Check if filename matches search criteria"""
        if not self.search_term:
            return True

        search = self.search_term if self.case_sensitive else self.search_term.lower()
        name = filename if self.case_sensitive else filename.lower()
        return search in name

    def _get_file_info(self, file_path: str) -> Dict:
        """Extract file information"""
        stat = os.stat(file_path)
        return {
            'name': os.path.basename(file_path),
            'path': file_path,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'category': FileType.get_category(file_path)
        }

    def stop(self):
        """Stop the search"""
        self._cancel_requested.set()
        logger.info("Search cancellation requested")


class FileOperationWorker(QThread):
    """Background worker for file copy/move operations"""
    progress = pyqtSignal(int, str)  # progress percentage, current file
    finished = pyqtSignal(int, int)  # success count, error count
    error = pyqtSignal(str)

    def __init__(self, files: List[str], destination: str, operation: FileOperation):
        super().__init__()
        self.files = files
        self.destination = destination
        self.operation = operation
        self._cancel_requested = threading.Event()
        self.success_count = 0
        self.error_count = 0

    def run(self):
        """Execute file operations"""
        import shutil

        total = len(self.files)
        for i, file_path in enumerate(self.files):
            # Check for cancellation
            if self._cancel_requested.is_set():
                logger.info("File operation cancelled by user")
                break

            try:
                filename = os.path.basename(file_path)
                dest_path = os.path.join(self.destination, filename)

                # Handle name conflicts
                if os.path.exists(dest_path):
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(dest_path):
                        filename = f"{base}_{counter}{ext}"
                        dest_path = os.path.join(self.destination, filename)
                        counter += 1

                if self.operation == FileOperation.COPY:
                    shutil.copy2(file_path, dest_path)
                else:  # MOVE
                    shutil.move(file_path, dest_path)

                self.success_count += 1
                progress = int((i + 1) / total * 100)
                self.progress.emit(progress, filename)
            except Exception as e:
                self.error_count += 1
                error_msg = f"Error processing {file_path}: {str(e)}"
                self.error.emit(error_msg)
                logger.error(error_msg)

        self.finished.emit(self.success_count, self.error_count)

    def stop(self):
        """Stop file operations"""
        self._cancel_requested.set()
        logger.info("File operation cancellation requested")


class DirectoryTreeWidget(QTreeWidget):
    """Tree widget for directory selection with checkboxes"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("Directories to Search")
        self.setMinimumWidth(250)
        self.itemChanged.connect(self._on_item_changed)
        self._populate_tree()

    def _populate_tree(self):
        """Populate tree with common Windows directories"""
        common_paths = [
            ("C:\\", "System Drive"),
            (os.path.expanduser("~"), "User Home"),
            (os.path.join(os.path.expanduser("~"), "Desktop"), "Desktop"),
            (os.path.join(os.path.expanduser("~"), "Documents"), "Documents"),
            (os.path.join(os.path.expanduser("~"), "Downloads"), "Downloads"),
            (os.path.join(os.path.expanduser("~"), "Pictures"), "Pictures"),
            (os.path.join(os.path.expanduser("~"), "Videos"), "Videos"),
            (os.path.join(os.path.expanduser("~"), "Music"), "Music"),
        ]

        for path, label in common_paths:
            if os.path.exists(path):
                item = QTreeWidgetItem([label])
                item.setCheckState(0, Qt.CheckState.Unchecked)
                item.setData(0, Qt.ItemDataRole.UserRole, path)
                item.setToolTip(0, path)
                self.addTopLevelItem(item)

                # Add immediate subdirectories
                try:
                    for subdir in sorted(os.listdir(path)):
                        subpath = os.path.join(path, subdir)
                        if os.path.isdir(subpath) and not subdir.startswith('.'):
                            child = QTreeWidgetItem([subdir])
                            child.setCheckState(0, Qt.CheckState.Unchecked)
                            child.setData(0, Qt.ItemDataRole.UserRole, subpath)
                            child.setToolTip(0, subpath)
                            item.addChild(child)
                except (PermissionError, FileNotFoundError):
                    pass

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle checkbox state changes (tristate)"""
        if item.checkState(column) != Qt.CheckState.PartiallyChecked:
            # Update children
            for i in range(item.childCount()):
                child = item.child(i)
                child.setCheckState(column, item.checkState(column))

        # Update parent
        self._update_parent_state(item)

    def _update_parent_state(self, item: QTreeWidgetItem):
        """Update parent checkbox based on children states"""
        parent = item.parent()
        if not parent:
            return

        checked_count = 0
        total_count = parent.childCount()

        for i in range(total_count):
            child = parent.child(i)
            if child.checkState(0) == Qt.CheckState.Checked:
                checked_count += 1
            elif child.checkState(0) == Qt.CheckState.PartiallyChecked:
                parent.setCheckState(0, Qt.CheckState.PartiallyChecked)
                return

        if checked_count == 0:
            parent.setCheckState(0, Qt.CheckState.Unchecked)
        elif checked_count == total_count:
            parent.setCheckState(0, Qt.CheckState.Checked)
        else:
            parent.setCheckState(0, Qt.CheckState.PartiallyChecked)

    def get_selected_paths(self) -> List[str]:
        """Get all checked directory paths"""
        paths = []

        def collect_checked(item: QTreeWidgetItem):
            if item.checkState(0) == Qt.CheckState.Checked:
                path = item.data(0, Qt.ItemDataRole.UserRole)
                if path:
                    paths.append(path)
            else:
                # Check children even if parent is unchecked/partial
                for i in range(item.childCount()):
                    collect_checked(item.child(i))

        for i in range(self.topLevelItemCount()):
            collect_checked(self.topLevelItem(i))

        return paths


class ResultsTableWidget(QTableWidget):
    """Table widget for displaying search results"""

    HEADERS = ["Name", "Path", "Size", "Modified", "Type"]

    # Signals for communication with main window
    open_requested = pyqtSignal(list)  # list of file paths
    open_location_requested = pyqtSignal(list)
    copy_requested = pyqtSignal(list)
    move_requested = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(len(self.HEADERS))
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)

        # Configure header
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Path
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Size
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Modified
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Type

        self.setColumnWidth(0, 200)

        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def add_result(self, file_info: Dict):
        """Add a file result to the table"""
        row = self.rowCount()
        self.insertRow(row)

        # Name
        name_item = QTableWidgetItem(file_info['name'])
        name_item.setData(Qt.ItemDataRole.UserRole, file_info['path'])
        self.setItem(row, 0, name_item)

        # Path
        path_item = QTableWidgetItem(file_info['path'])
        self.setItem(row, 1, path_item)

        # Size
        size_item = QTableWidgetItem(format_file_size(file_info['size']))
        size_item.setData(Qt.ItemDataRole.UserRole, file_info['size'])
        self.setItem(row, 2, size_item)

        # Modified
        modified_item = QTableWidgetItem(file_info['modified'].strftime("%Y-%m-%d %H:%M"))
        modified_item.setData(Qt.ItemDataRole.UserRole, file_info['modified'])
        self.setItem(row, 3, modified_item)

        # Type
        type_item = QTableWidgetItem(Path(file_info['name']).suffix.upper() or "FILE")
        self.setItem(row, 4, type_item)


    def get_selected_files(self) -> List[str]:
        """Get list of selected file paths"""
        files = []
        for item in self.selectedItems():
            if item.column() == 0:  # Only process name column
                path = item.data(Qt.ItemDataRole.UserRole)
                if path:
                    files.append(path)
        return files

    def _show_context_menu(self, position):
        """Show context menu for selected files"""
        if not self.selectedItems():
            return

        menu = QMenu(self)

        # Get selected files for all actions
        selected_files = self.get_selected_files()

        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self.open_requested.emit(selected_files))
        menu.addAction(open_action)

        open_location_action = QAction("Open Location", self)
        open_location_action.triggered.connect(lambda: self.open_location_requested.emit(selected_files))
        menu.addAction(open_location_action)

        menu.addSeparator()

        copy_action = QAction("Copy to...", self)
        copy_action.triggered.connect(lambda: self.copy_requested.emit(selected_files))
        menu.addAction(copy_action)

        move_action = QAction("Move to...", self)
        move_action.triggered.connect(lambda: self.move_requested.emit(selected_files))
        menu.addAction(move_action)

        menu.addSeparator()

        copy_path_action = QAction("Copy Path", self)
        copy_path_action.triggered.connect(self._copy_path_to_clipboard)
        menu.addAction(copy_path_action)

        menu.exec(self.viewport().mapToGlobal(position))

    def _copy_path_to_clipboard(self):
        """Copy selected file path to clipboard"""
        files = self.get_selected_files()
        if files:
            QApplication.clipboard().setText('\n'.join(files))


class SmartSearchWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.search_worker = None
        self.operation_worker = None
        self.dark_mode = False

        self._init_ui()
        self._setup_shortcuts()
        self._apply_theme()

    def _init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("Smart Search - Windows File Search Tool")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Top search bar
        search_layout = self._create_search_bar()
        main_layout.addLayout(search_layout)

        # Main splitter (left: directories, right: results)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Directory tree
        self.dir_tree = DirectoryTreeWidget()
        splitter.addWidget(self.dir_tree)

        # Right panel: Results tabs
        self.results_tabs = QTabWidget()
        self.results_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.results_tabs.setMovable(False)

        # Create tab for each file type
        self.result_tables: Dict[FileType, ResultsTableWidget] = {}
        for file_type in FileType:
            table = ResultsTableWidget()
            self.results_tabs.addTab(table, file_type.display_name)
            self.result_tables[file_type] = table

        splitter.addWidget(self.results_tabs)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)

        # Bottom action bar
        action_layout = self._create_action_bar()
        main_layout.addLayout(action_layout)

        # Status bar
        self.status_bar = self.statusBar()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(300)
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.status_bar.showMessage("Ready")

    def _create_search_bar(self) -> QHBoxLayout:
        """Create top search bar with controls and accessibility features."""
        layout = QHBoxLayout()

        # Search input with accessibility
        search_label = QLabel("Search:")
        search_label.setAccessibleName("Search label")
        layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter filename or pattern (use * as wildcard)...")
        self.search_input.setAccessibleName("Search input")
        self.search_input.setAccessibleDescription(
            "Enter search terms. Use asterisk for wildcards. Press Enter to search."
        )
        self.search_input.setToolTip(
            "Enter filename or pattern to search.\n"
            "Use * as wildcard (e.g., *.txt, report*)\n"
            "Press Enter or click Search button"
        )
        self.search_input.returnPressed.connect(self._start_search)
        # Associate label with input for accessibility
        search_label.setBuddy(self.search_input)
        layout.addWidget(self.search_input, stretch=3)

        # Case sensitive checkbox with accessibility
        self.case_sensitive_cb = QCheckBox("Case Sensitive")
        self.case_sensitive_cb.setAccessibleName("Case sensitive search toggle")
        self.case_sensitive_cb.setAccessibleDescription(
            "When checked, search will match exact letter case"
        )
        self.case_sensitive_cb.setToolTip("Enable case-sensitive search matching")
        layout.addWidget(self.case_sensitive_cb)

        # Search button with accessibility
        self.search_btn = QPushButton("Search")
        self.search_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogContentsView))
        self.search_btn.setAccessibleName("Start search")
        self.search_btn.setAccessibleDescription("Click to begin searching for files")
        self.search_btn.setToolTip("Start searching (Enter)")
        self.search_btn.setShortcut(QKeySequence("Ctrl+Return"))
        self.search_btn.clicked.connect(self._start_search)
        layout.addWidget(self.search_btn)

        # Stop button with accessibility
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_BrowserStop))
        self.stop_btn.setEnabled(False)
        self.stop_btn.setAccessibleName("Stop search")
        self.stop_btn.setAccessibleDescription("Click to cancel the current search operation")
        self.stop_btn.setToolTip("Stop current search (Escape)")
        self.stop_btn.setShortcut(QKeySequence("Escape"))
        self.stop_btn.clicked.connect(self._stop_search)
        layout.addWidget(self.stop_btn)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Operation selector with accessibility
        op_label = QLabel("Operation:")
        layout.addWidget(op_label)

        self.operation_combo = QComboBox()
        self.operation_combo.addItems(["Copy", "Move"])
        self.operation_combo.setAccessibleName("File operation selector")
        self.operation_combo.setAccessibleDescription(
            "Select whether to copy or move files to destination"
        )
        self.operation_combo.setToolTip("Select file operation type for selected files")
        op_label.setBuddy(self.operation_combo)
        layout.addWidget(self.operation_combo)

        # Theme toggle with accessibility
        self.theme_btn = QPushButton("Dark Mode")
        self.theme_btn.setCheckable(True)
        self.theme_btn.setAccessibleName("Toggle dark mode")
        self.theme_btn.setAccessibleDescription("Switch between light and dark color theme")
        self.theme_btn.setToolTip("Toggle between light and dark theme (Ctrl+D)")
        self.theme_btn.setShortcut(QKeySequence("Ctrl+D"))
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)

        return layout

    def _create_action_bar(self) -> QHBoxLayout:
        """Create bottom action bar"""
        layout = QHBoxLayout()

        # File count label
        self.file_count_label = QLabel("Files: 0")
        layout.addWidget(self.file_count_label)

        layout.addStretch()

        # Action buttons
        self.open_btn = QPushButton("Open")
        self.open_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
        self.open_btn.clicked.connect(self._open_files)
        self.open_btn.setEnabled(False)
        layout.addWidget(self.open_btn)

        self.open_location_btn = QPushButton("Open Location")
        self.open_location_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon))
        self.open_location_btn.clicked.connect(self._open_location)
        self.open_location_btn.setEnabled(False)
        layout.addWidget(self.open_location_btn)

        self.copy_btn = QPushButton("Copy To...")
        self.copy_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogDetailedView))
        self.copy_btn.clicked.connect(self._copy_files)
        self.copy_btn.setEnabled(False)
        layout.addWidget(self.copy_btn)

        self.move_btn = QPushButton("Move To...")
        self.move_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogDetailedView))
        self.move_btn.clicked.connect(self._move_files)
        self.move_btn.setEnabled(False)
        layout.addWidget(self.move_btn)

        self.clear_btn = QPushButton("Clear Results")
        self.clear_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_TrashIcon))
        self.clear_btn.clicked.connect(self._clear_results)
        layout.addWidget(self.clear_btn)

        # Connect selection changed to enable/disable buttons
        for table in self.result_tables.values():
            table.itemSelectionChanged.connect(self._update_button_states)
            # Connect table signals to handler methods
            table.open_requested.connect(self._open_files_from_list)
            table.open_location_requested.connect(self._open_location_from_list)
            table.copy_requested.connect(self._copy_files_from_list)
            table.move_requested.connect(self._move_files_from_list)

        return layout

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Search: Ctrl+F
        search_shortcut = QKeySequence("Ctrl+F")
        search_action = QAction(self)
        search_action.setShortcut(search_shortcut)
        search_action.triggered.connect(lambda: self.search_input.setFocus())
        self.addAction(search_action)

        # Open: Ctrl+O
        open_shortcut = QKeySequence("Ctrl+O")
        open_action = QAction(self)
        open_action.setShortcut(open_shortcut)
        open_action.triggered.connect(self._open_files)
        self.addAction(open_action)

        # Copy: Ctrl+C
        copy_shortcut = QKeySequence("Ctrl+Shift+C")
        copy_action = QAction(self)
        copy_action.setShortcut(copy_shortcut)
        copy_action.triggered.connect(self._copy_files)
        self.addAction(copy_action)

        # Move: Ctrl+M
        move_shortcut = QKeySequence("Ctrl+M")
        move_action = QAction(self)
        move_action.setShortcut(move_shortcut)
        move_action.triggered.connect(self._move_files)
        self.addAction(move_action)

        # Clear: Ctrl+L
        clear_shortcut = QKeySequence("Ctrl+L")
        clear_action = QAction(self)
        clear_action.setShortcut(clear_shortcut)
        clear_action.triggered.connect(self._clear_results)
        self.addAction(clear_action)

    def _apply_theme(self):
        """Apply color theme"""
        if self.dark_mode:
            # Dark theme
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                }
                QWidget {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                }
                QLineEdit, QComboBox, QSpinBox {
                    background-color: #2d2d30;
                    border: 1px solid #3e3e42;
                    padding: 5px;
                    color: #d4d4d4;
                }
                QPushButton {
                    background-color: #0e639c;
                    border: 1px solid #0e639c;
                    padding: 6px 12px;
                    color: white;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #1177bb;
                }
                QPushButton:disabled {
                    background-color: #3e3e42;
                    color: #858585;
                }
                QTreeWidget, QTableWidget {
                    background-color: #252526;
                    border: 1px solid #3e3e42;
                    color: #d4d4d4;
                }
                QTreeWidget::item:selected, QTableWidget::item:selected {
                    background-color: #094771;
                }
                QHeaderView::section {
                    background-color: #2d2d30;
                    color: #d4d4d4;
                    padding: 5px;
                    border: 1px solid #3e3e42;
                }
                QTabWidget::pane {
                    border: 1px solid #3e3e42;
                }
                QTabBar::tab {
                    background-color: #2d2d30;
                    color: #d4d4d4;
                    padding: 8px 16px;
                    border: 1px solid #3e3e42;
                }
                QTabBar::tab:selected {
                    background-color: #0e639c;
                }
                QProgressBar {
                    border: 1px solid #3e3e42;
                    background-color: #2d2d30;
                    text-align: center;
                    color: #d4d4d4;
                }
                QProgressBar::chunk {
                    background-color: #0e639c;
                }
                QStatusBar {
                    background-color: #007acc;
                    color: white;
                }
            """)
        else:
            # Light theme (default)
            self.setStyleSheet("""
                QPushButton {
                    padding: 6px 12px;
                }
                QLineEdit, QComboBox {
                    padding: 5px;
                }
            """)

    def _toggle_theme(self, checked: bool):
        """Toggle between light and dark theme"""
        self.dark_mode = checked
        self._apply_theme()
        self.theme_btn.setText("Light Mode" if self.dark_mode else "Dark Mode")

    def _start_search(self):
        """Start file search"""
        # Get selected directories
        search_paths = self.dir_tree.get_selected_paths()
        if not search_paths:
            QMessageBox.warning(self, "No Directories", "Please select at least one directory to search.")
            return

        # Validar que los directorios existan
        valid_paths = []
        invalid_paths = []

        for path in search_paths:
            if os.path.exists(path) and os.path.isdir(path):
                valid_paths.append(path)
            else:
                invalid_paths.append(path)

        if invalid_paths:
            msg = "The following directories do not exist or are not accessible:\n\n"
            msg += "\n".join(invalid_paths[:5])
            if len(invalid_paths) > 5:
                msg += f"\n... and {len(invalid_paths) - 5} more"
            QMessageBox.warning(self, "Invalid Directories", msg)

        if not valid_paths:
            QMessageBox.warning(self, "No Valid Directories", "No valid directories to search.")
            return

        # Clear previous results
        self._clear_results()

        # Get search term
        search_term = self.search_input.text().strip()
        case_sensitive = self.case_sensitive_cb.isChecked()

        # Create and start worker with validated paths
        self.search_worker = SearchWorker(valid_paths, search_term, case_sensitive)
        self.search_worker.progress.connect(self._on_search_progress)
        self.search_worker.result.connect(self._on_search_result)
        self.search_worker.finished.connect(self._on_search_finished)
        self.search_worker.error.connect(self._on_search_error)

        # Update UI
        self.search_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_bar.showMessage("Searching...")

        self.search_worker.start()

    def _stop_search(self):
        """Stop ongoing search"""
        if self.search_worker:
            self.search_worker.stop()
            if not self.search_worker.wait(5000):  # 5 second timeout
                logger.warning("Search worker did not stop within timeout")
                self.search_worker.terminate()
            self._on_search_finished(0)

    def _on_search_progress(self, percentage: int, current_file: str):
        """Handle search progress update"""
        self.status_bar.showMessage(f"Searching: {current_file}")

    def _on_search_result(self, file_info: Dict):
        """Handle search result"""
        category = file_info['category']
        table = self.result_tables[category]
        table.add_result(file_info)

        # Update file count
        total = sum(table.rowCount() for table in self.result_tables.values())
        self.file_count_label.setText(f"Files: {total}")

        # Update tab labels with counts
        for file_type, table in self.result_tables.items():
            count = table.rowCount()
            tab_index = list(self.result_tables.keys()).index(file_type)
            self.results_tabs.setTabText(tab_index, f"{file_type.display_name} ({count})")

    def _on_search_finished(self, total_files: int):
        """Handle search completion"""
        self.search_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"Search complete. Found {total_files} files.", 5000)

    def _on_search_error(self, error_msg: str):
        """Handle search error with user-friendly feedback."""
        # Reset UI state
        self.search_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        # Provide contextual error message
        if "permission" in error_msg.lower():
            detailed_msg = (
                f"Search encountered a permission error:\n\n{error_msg}\n\n"
                "Some directories may be protected. Try selecting different folders."
            )
        elif "connection" in error_msg.lower() or "windows search" in error_msg.lower():
            detailed_msg = (
                f"Windows Search service error:\n\n{error_msg}\n\n"
                "Please ensure the Windows Search service is running:\n"
                "1. Press Win+R, type 'services.msc'\n"
                "2. Find 'Windows Search' and ensure it's running"
            )
        elif "timeout" in error_msg.lower():
            detailed_msg = (
                f"Search timed out:\n\n{error_msg}\n\n"
                "Try narrowing your search with more specific terms or fewer directories."
            )
        else:
            detailed_msg = f"An error occurred during search:\n\n{error_msg}"

        QMessageBox.critical(
            self, "Search Error", detailed_msg,
            QMessageBox.StandardButton.Ok
        )
        self.status_bar.showMessage("Search failed. Ready.", 5000)

    def _get_current_table(self) -> Optional[ResultsTableWidget]:
        """Get currently active results table"""
        current_widget = self.results_tabs.currentWidget()
        if isinstance(current_widget, ResultsTableWidget):
            return current_widget
        return None

    def _update_button_states(self):
        """Update action button states based on selection"""
        table = self._get_current_table()
        has_selection = table and len(table.get_selected_files()) > 0

        self.open_btn.setEnabled(has_selection)
        self.open_location_btn.setEnabled(has_selection)
        self.copy_btn.setEnabled(has_selection)
        self.move_btn.setEnabled(has_selection)

    def _open_files(self):
        """Open selected files from current table"""
        table = self._get_current_table()
        if not table:
            return

        files = table.get_selected_files()
        self._open_files_from_list(files)

    def _open_files_from_list(self, files: list):
        """
        Open files from provided list (can be called from signals).

        SECURITY: Uses validate_safe_file_type to prevent opening
        potentially dangerous executable files.
        """
        if not files:
            return

        # Validate files exist
        valid_files = []
        for file_path in files:
            if os.path.exists(file_path):
                valid_files.append(file_path)

        if not valid_files:
            QMessageBox.warning(self, "No Valid Files", "Selected files no longer exist.")
            return

        # Open files with security validation and error handling
        opened_count = 0
        error_count = 0
        blocked_files = []

        for file_path in valid_files[:10]:  # Limit to 10 files
            try:
                # SECURITY: Validate file type before opening
                validate_safe_file_type(file_path)
                os.startfile(file_path)
                opened_count += 1
            except PermissionError as e:
                # File type blocked by security validation
                blocked_files.append(os.path.basename(file_path))
                logger.warning(f"Blocked opening file for security: {file_path}")
            except FileNotFoundError:
                error_count += 1
                logger.warning(f"File not found: {file_path}")
            except Exception as e:
                error_count += 1
                logger.error(f"Error opening {file_path}: {e}")

        # Show feedback to user
        if len(valid_files) > 10:
            QMessageBox.information(
                self, "Too Many Files",
                f"Only opening first 10 of {len(valid_files)} selected files."
            )

        if blocked_files:
            blocked_list = "\n".join(blocked_files[:5])
            if len(blocked_files) > 5:
                blocked_list += f"\n... and {len(blocked_files) - 5} more"
            QMessageBox.warning(
                self, "Security: Files Blocked",
                f"The following files were blocked for security reasons "
                f"(executable/script files cannot be opened directly):\n\n"
                f"{blocked_list}\n\n"
                f"Use 'Open Location' to navigate to these files instead."
            )

        if error_count > 0 and opened_count > 0:
            QMessageBox.warning(
                self, "Some Errors",
                f"Opened {opened_count} files, {error_count} failed to open."
            )

    def _open_location(self):
        """Open file location in Explorer from current table"""
        table = self._get_current_table()
        if not table:
            return

        files = table.get_selected_files()
        self._open_location_from_list(files)

    def _open_location_from_list(self, files: list):
        """Open file location from provided list (can be called from signals)"""
        if not files:
            return

        # Validar que el archivo existe
        file_path = files[0]
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "File Not Found", f"File no longer exists:\n{file_path}")
            return

        try:
            # Open file's directory
            directory = os.path.dirname(file_path)
            if os.path.exists(directory):
                os.startfile(directory)
            else:
                QMessageBox.warning(self, "Directory Not Found", f"Directory no longer exists:\n{directory}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open location:\n{str(e)}")

    def _copy_files(self):
        """Copy selected files to destination from current table"""
        table = self._get_current_table()
        if not table:
            return

        files = table.get_selected_files()
        self._copy_files_from_list(files)

    def _copy_files_from_list(self, files: list):
        """Copy files from provided list (can be called from signals)"""
        if not files:
            return
        self._perform_file_operation_from_list(files, FileOperation.COPY)

    def _move_files(self):
        """Move selected files to destination from current table"""
        table = self._get_current_table()
        if not table:
            return

        files = table.get_selected_files()
        self._move_files_from_list(files)

    def _move_files_from_list(self, files: list):
        """Move files from provided list (can be called from signals)"""
        if not files:
            return
        self._perform_file_operation_from_list(files, FileOperation.MOVE)

    def _perform_file_operation(self, operation: FileOperation):
        """Execute file copy/move operation from current table"""
        table = self._get_current_table()
        if not table:
            return

        files = table.get_selected_files()
        self._perform_file_operation_from_list(files, operation)

    def _perform_file_operation_from_list(self, files: list, operation: FileOperation):
        """Execute file copy/move operation from provided list"""
        if not files:
            return

        # Select destination directory
        destination = QFileDialog.getExistingDirectory(
            self,
            f"Select Destination for {operation.value.title()}",
            os.path.expanduser("~")
        )

        if not destination:
            return

        # Confirm operation
        msg = f"{operation.value.title()} {len(files)} file(s) to:\n{destination}"
        reply = QMessageBox.question(self, f"Confirm {operation.value.title()}", msg,
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Create and start worker
        self.operation_worker = FileOperationWorker(files, destination, operation)
        self.operation_worker.progress.connect(self._on_operation_progress)
        self.operation_worker.finished.connect(self._on_operation_finished)
        self.operation_worker.error.connect(self._on_operation_error)

        # Update UI
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.status_bar.showMessage(f"{operation.value.title()}ing files...")

        self.operation_worker.start()

    def _on_operation_progress(self, percentage: int, current_file: str):
        """Handle file operation progress"""
        self.progress_bar.setValue(percentage)
        self.status_bar.showMessage(f"Processing: {current_file}")

    def _on_operation_finished(self, success_count: int, error_count: int):
        """Handle file operation completion"""
        self.progress_bar.setVisible(False)

        msg = f"Operation complete.\nSuccessful: {success_count}"
        if error_count > 0:
            msg += f"\nErrors: {error_count}"

        QMessageBox.information(self, "Operation Complete", msg)
        self.status_bar.showMessage(f"Operation complete. {success_count} files processed.", 5000)

    def _on_operation_error(self, error_msg: str):
        """Handle file operation error"""
        # Log error (could display in a separate error list)
        print(f"Error: {error_msg}")

    def _clear_results(self):
        """Clear all search results"""
        for table in self.result_tables.values():
            table.setRowCount(0)

        # Reset tab labels
        for file_type, table in self.result_tables.items():
            tab_index = list(self.result_tables.keys()).index(file_type)
            self.results_tabs.setTabText(tab_index, file_type.display_name)

        self.file_count_label.setText("Files: 0")
        self.status_bar.showMessage("Results cleared", 3000)

    def closeEvent(self, event):
        """Handle application close - cleanup threads"""
        # Stop and cleanup search worker
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.stop()
            if not self.search_worker.wait(3000):  # 3 second timeout
                logger.warning("Search worker forced termination on close")
                self.search_worker.terminate()
                self.search_worker.wait(1000)

        # Cleanup operation worker
        if self.operation_worker and self.operation_worker.isRunning():
            if not self.operation_worker.wait(3000):  # 3 second timeout
                logger.warning("Operation worker forced termination on close")
                self.operation_worker.terminate()
                self.operation_worker.wait(1000)

        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Smart Search")
    app.setOrganizationName("SmartTools")

    # Set application font
    font = QFont("Segoe UI", 9)
    app.setFont(font)

    window = SmartSearchWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
