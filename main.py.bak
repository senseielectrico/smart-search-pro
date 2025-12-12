"""
Smart Search - Aplicación de búsqueda avanzada de archivos en Windows
=========================================================================

Integra todos los módulos para proporcionar una herramienta de búsqueda
completa con interfaz gráfica PyQt6 y Windows Search API.

Características:
- Búsqueda en nombre Y contenido de archivos
- Soporte para múltiples palabras con separador *
- Árbol de directorios indexados con estados persistentes
- Clasificación automática por tipo de archivo
- Operaciones de archivos (copiar, mover, abrir)
- Tema claro/oscuro
- Progreso en tiempo real

Uso:
    python main.py

Autor: Smart Search Team
Fecha: 2025-12-11
"""

import sys
import os
import json
import logging
import threading
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime

# Configurar logger
logger = logging.getLogger(__name__)

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, QTabWidget,
    QTableWidget, QTableWidgetItem, QSplitter, QLabel, QComboBox,
    QFileDialog, QProgressBar, QMessageBox, QMenu, QHeaderView,
    QCheckBox, QGroupBox, QFrame, QStatusBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QAction, QKeySequence, QIcon, QPixmap, QPainter, QColor

# Backend imports
from backend import (
    SearchService, SearchQuery, SearchResult,
    FileOperations
)

# Importar categorías del sistema unificado
from categories import FileCategory

# File manager imports
from file_manager import (
    DirectoryTree, CheckState, DirectoryNode,
    WindowsSearchIndexManager, create_tree_from_indexed_directories
)

# Classifier imports
from classifier import (
    classify_file, format_file_size, format_date,
    ResultItem, group_results_by_type, get_category_stats
)


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

APP_NAME = "Smart Search"
APP_VERSION = "1.0.0"
CONFIG_DIR = Path.home() / ".smart_search"
CONFIG_FILE = CONFIG_DIR / "config.json"
TREE_CONFIG_FILE = CONFIG_DIR / "directory_tree.json"


def create_app_icon() -> QIcon:
    """Creates a programmatic icon for the application"""
    # Create a 64x64 pixmap with search icon
    sizes = [16, 32, 48, 64, 128, 256]
    icon = QIcon()

    for size in sizes:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw search magnifying glass
        scale = size / 64.0

        # Background circle (blue)
        painter.setBrush(QColor(14, 99, 156))  # Windows blue
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(4*scale), int(4*scale), int(56*scale), int(56*scale))

        # Magnifying glass circle (white)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(int(12*scale), int(12*scale), int(28*scale), int(28*scale))

        # Inner circle (blue) - creates ring effect
        painter.setBrush(QColor(14, 99, 156))
        painter.drawEllipse(int(18*scale), int(18*scale), int(16*scale), int(16*scale))

        # Magnifying glass handle (white)
        from PyQt6.QtGui import QPen
        pen = QPen(QColor(255, 255, 255))
        pen.setWidth(int(6*scale))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(int(38*scale), int(38*scale), int(50*scale), int(50*scale))

        painter.end()
        icon.addPixmap(pixmap)

    return icon


# ============================================================================
# WORKER THREADS
# ============================================================================

class IntegratedSearchWorker(QThread):
    """Worker thread que usa el backend real de Windows Search API"""

    # Señales
    progress = pyqtSignal(int, str)  # progress, current file
    result = pyqtSignal(SearchResult)  # resultado individual
    finished = pyqtSignal(int)  # total resultados
    error = pyqtSignal(str)  # mensaje de error

    def __init__(
        self,
        search_service: SearchService,
        keywords: List[str],
        search_paths: List[str],
        search_content: bool,
        search_filename: bool
    ):
        super().__init__()
        self.search_service = search_service
        self.keywords = keywords
        self.search_paths = search_paths
        self.search_content = search_content
        self.search_filename = search_filename
        self._cancel_requested = threading.Event()
        self.results_count = 0

    def run(self):
        """Ejecuta la búsqueda usando SearchService"""
        try:
            # Construir query
            query = SearchQuery(
                keywords=self.keywords,
                search_paths=self.search_paths,
                search_content=self.search_content,
                search_filename=self.search_filename,
                max_results=10000
            )

            # Callback para resultados individuales
            def on_result(result: SearchResult):
                if not self._cancel_requested.is_set():
                    self.results_count += 1
                    self.result.emit(result)

                    if self.results_count % 10 == 0:
                        self.progress.emit(0, result.name)

            # Ejecutar búsqueda síncrona (ya estamos en thread)
            results = self.search_service.search_sync(query, callback=on_result)

            # Emitir finalización si no fue cancelada
            if not self._cancel_requested.is_set():
                self.finished.emit(len(results))
            else:
                self.finished.emit(0)

        except Exception as e:
            if not self._cancel_requested.is_set():
                self.error.emit(str(e))
                logger.exception(f"Error in search worker: {e}")

    def stop(self):
        """Detiene la búsqueda"""
        self._cancel_requested.set()
        logger.info("Search cancellation requested")


# ============================================================================
# WIDGETS PERSONALIZADOS
# ============================================================================

class IntegratedDirectoryTreeWidget(QTreeWidget):
    """
    Widget de árbol de directorios integrado con DirectoryTree backend
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("Directories to Search")
        self.setMinimumWidth(300)

        # Backend DirectoryTree
        self.tree_model = DirectoryTree()

        # Configurar widget
        self.itemChanged.connect(self._on_item_changed)
        self._suppress_signals = False

        # Poblar desde directorios indexados
        self._populate_from_indexed()

        # Intentar cargar configuración guardada
        self._load_tree_config()

    def _populate_from_indexed(self):
        """Pobla el árbol desde los directorios indexados de Windows"""
        self.clear()

        # Obtener directorios indexados
        indexed_dirs = WindowsSearchIndexManager.get_indexed_directories()

        # Si no hay indexados, usar directorios comunes
        if not indexed_dirs:
            user_profile = os.environ.get('USERPROFILE', '')
            if user_profile:
                indexed_dirs = [
                    user_profile,
                    os.path.join(user_profile, 'Desktop'),
                    os.path.join(user_profile, 'Documents'),
                    os.path.join(user_profile, 'Downloads'),
                    os.path.join(user_profile, 'Pictures'),
                    os.path.join(user_profile, 'Videos'),
                    os.path.join(user_profile, 'Music'),
                ]

        # Añadir al modelo backend
        for directory in indexed_dirs:
            if os.path.exists(directory):
                self.tree_model.add_directory(directory)

        # Construir UI desde modelo
        self._build_ui_from_model()

    def _build_ui_from_model(self):
        """Construye la UI del árbol desde el modelo backend"""
        self._suppress_signals = True

        def add_node_to_tree(node: DirectoryNode, parent_item: Optional[QTreeWidgetItem] = None):
            # Crear item
            display_name = node.name
            item = QTreeWidgetItem([display_name])

            # Establecer estado checkbox
            qt_state = self._checkstate_to_qt(node.state)
            item.setCheckState(0, qt_state)

            # Guardar referencia al nodo
            item.setData(0, Qt.ItemDataRole.UserRole, node.path)
            item.setToolTip(0, node.path)

            # Añadir a padre o raíz
            if parent_item:
                parent_item.addChild(item)
            else:
                self.addTopLevelItem(item)

            # Recursivamente añadir hijos
            for child_name in sorted(node.children.keys()):
                child_node = node.children[child_name]
                add_node_to_tree(child_node, item)

        # Añadir todos los nodos raíz
        for root_name in sorted(self.tree_model.root_nodes.keys()):
            root_node = self.tree_model.root_nodes[root_name]
            add_node_to_tree(root_node)

        self._suppress_signals = False

    def _checkstate_to_qt(self, state: CheckState) -> Qt.CheckState:
        """Convierte CheckState a Qt.CheckState"""
        mapping = {
            CheckState.UNCHECKED: Qt.CheckState.Unchecked,
            CheckState.PARTIAL: Qt.CheckState.PartiallyChecked,
            CheckState.CHECKED: Qt.CheckState.Checked
        }
        return mapping.get(state, Qt.CheckState.Unchecked)

    def _qt_to_checkstate(self, qt_state: Qt.CheckState) -> CheckState:
        """Convierte Qt.CheckState a CheckState"""
        mapping = {
            Qt.CheckState.Unchecked: CheckState.UNCHECKED,
            Qt.CheckState.PartiallyChecked: CheckState.PARTIAL,
            Qt.CheckState.Checked: CheckState.CHECKED
        }
        return mapping.get(qt_state, CheckState.UNCHECKED)

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """Maneja cambios de checkbox"""
        if self._suppress_signals:
            return

        # Obtener path del item
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path:
            return

        # Actualizar modelo backend
        qt_state = item.checkState(column)
        check_state = self._qt_to_checkstate(qt_state)

        self.tree_model.set_state(path, check_state, propagate=True)

        # Refrescar UI
        self._refresh_ui_from_model()

    def _refresh_ui_from_model(self):
        """Refresca la UI desde el modelo backend"""
        self._suppress_signals = True

        def update_item(item: QTreeWidgetItem):
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path:
                node = self.tree_model._find_node(path)
                if node:
                    qt_state = self._checkstate_to_qt(node.state)
                    item.setCheckState(0, qt_state)

            # Recursivamente actualizar hijos
            for i in range(item.childCount()):
                update_item(item.child(i))

        # Actualizar todos los items
        for i in range(self.topLevelItemCount()):
            update_item(self.topLevelItem(i))

        self._suppress_signals = False

    def get_selected_paths(self) -> List[str]:
        """Obtiene los paths seleccionados"""
        return self.tree_model.get_checked_leaf_directories()

    def _load_tree_config(self):
        """Carga configuración del árbol desde archivo"""
        if TREE_CONFIG_FILE.exists():
            if self.tree_model.load_config(str(TREE_CONFIG_FILE)):
                self._refresh_ui_from_model()

    def save_tree_config(self):
        """Guarda configuración del árbol"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.tree_model.save_config(str(TREE_CONFIG_FILE))


class ClassifiedResultsTableWidget(QTableWidget):
    """
    Tabla de resultados con clasificación automática
    """

    HEADERS = ["Name", "Path", "Size", "Modified", "Category"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(len(self.HEADERS))
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)

        # Configurar header
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.setColumnWidth(0, 250)

        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def add_result(self, result: SearchResult):
        """Añade un resultado de búsqueda"""
        row = self.rowCount()
        self.insertRow(row)

        # Name
        name_item = QTableWidgetItem(result.name)
        name_item.setData(Qt.ItemDataRole.UserRole, result.path)
        self.setItem(row, 0, name_item)

        # Path
        path_item = QTableWidgetItem(result.path)
        self.setItem(row, 1, path_item)

        # Size (formateado)
        size_str = format_file_size(result.size)
        size_item = QTableWidgetItem(size_str)
        size_item.setData(Qt.ItemDataRole.UserRole, result.size)
        self.setItem(row, 2, size_item)

        # Modified
        if result.modified:
            date_str = result.modified.strftime("%Y-%m-%d %H:%M")
            modified_item = QTableWidgetItem(date_str)
            modified_item.setData(Qt.ItemDataRole.UserRole, result.modified)
        else:
            modified_item = QTableWidgetItem("N/A")
        self.setItem(row, 3, modified_item)

        # Category
        category_item = QTableWidgetItem(result.category.value)
        self.setItem(row, 4, category_item)

    def get_selected_files(self) -> List[str]:
        """Obtiene lista de archivos seleccionados"""
        files = []
        for item in self.selectedItems():
            if item.column() == 0:
                path = item.data(Qt.ItemDataRole.UserRole)
                if path:
                    files.append(path)
        return files

    def _show_context_menu(self, position):
        """Muestra menú contextual"""
        if not self.selectedItems():
            return

        menu = QMenu(self)

        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self._open_files())
        menu.addAction(open_action)

        open_location_action = QAction("Open Location", self)
        open_location_action.triggered.connect(lambda: self._open_location())
        menu.addAction(open_location_action)

        menu.addSeparator()

        copy_path_action = QAction("Copy Path", self)
        copy_path_action.triggered.connect(self._copy_path_to_clipboard)
        menu.addAction(copy_path_action)

        menu.exec(self.viewport().mapToGlobal(position))

    def _open_files(self):
        """Abre archivos seleccionados"""
        files = self.get_selected_files()
        for file_path in files[:10]:
            FileOperations.open_file(file_path)

        if len(files) > 10:
            QMessageBox.information(
                self,
                "Too Many Files",
                f"Only opening first 10 of {len(files)} selected files."
            )

    def _open_location(self):
        """Abre ubicación en explorador"""
        files = self.get_selected_files()
        if files:
            FileOperations.open_location(files[0])

    def _copy_path_to_clipboard(self):
        """Copia paths al portapapeles"""
        files = self.get_selected_files()
        if files:
            QApplication.clipboard().setText('\n'.join(files))


# ============================================================================
# VENTANA PRINCIPAL
# ============================================================================

class SmartSearchApp(QMainWindow):
    """
    Aplicación principal que integra todos los módulos
    """

    def __init__(self):
        super().__init__()

        # Backend components
        self.search_service = SearchService(use_windows_search=True)
        self.file_ops = FileOperations()

        # Worker
        self.search_worker: Optional[IntegratedSearchWorker] = None

        # UI state
        self.dark_mode = False

        # Inicializar UI
        self._init_ui()
        self._setup_shortcuts()
        self._apply_theme()

        # Cargar configuración
        self._load_config()

    def _init_ui(self):
        """Inicializa la interfaz de usuario"""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)

        # Set application icon
        app_icon = create_app_icon()
        self.setWindowIcon(app_icon)
        QApplication.instance().setWindowIcon(app_icon)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Top search bar
        search_layout = self._create_search_bar()
        main_layout.addLayout(search_layout)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Directory tree
        self.dir_tree = IntegratedDirectoryTreeWidget()
        splitter.addWidget(self.dir_tree)

        # Right panel: Results tabs
        self.results_tabs = QTabWidget()

        # Crear tabs por categoría
        self.result_tables: Dict[FileCategory, ClassifiedResultsTableWidget] = {}
        for category in FileCategory:
            table = ClassifiedResultsTableWidget()
            self.results_tabs.addTab(table, category.value)
            self.result_tables[category] = table

            # Conectar señales de selección
            table.itemSelectionChanged.connect(self._update_button_states)

        splitter.addWidget(self.results_tabs)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)

        # Bottom action bar
        action_layout = self._create_action_bar()
        main_layout.addLayout(action_layout)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(300)
        self.status_bar.addPermanentWidget(self.progress_bar)

        self.status_bar.showMessage("Ready")

    def _create_search_bar(self) -> QHBoxLayout:
        """Crea la barra de búsqueda"""
        layout = QHBoxLayout()

        # Search input
        search_label = QLabel("Search:")
        layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Enter keywords separated by * (e.g., python * script)"
        )
        self.search_input.returnPressed.connect(self._start_search)
        layout.addWidget(self.search_input, stretch=3)

        # Search options
        self.search_filename_cb = QCheckBox("Filename")
        self.search_filename_cb.setChecked(True)
        layout.addWidget(self.search_filename_cb)

        self.search_content_cb = QCheckBox("Content")
        self.search_content_cb.setChecked(False)
        layout.addWidget(self.search_content_cb)

        # Search button
        self.search_btn = QPushButton("Search")
        self.search_btn.setIcon(
            self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogContentsView)
        )
        self.search_btn.clicked.connect(self._start_search)
        layout.addWidget(self.search_btn)

        # Stop button
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setIcon(
            self.style().standardIcon(self.style().StandardPixmap.SP_BrowserStop)
        )
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_search)
        layout.addWidget(self.stop_btn)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Theme toggle
        self.theme_btn = QPushButton("Dark Mode")
        self.theme_btn.setCheckable(True)
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)

        return layout

    def _create_action_bar(self) -> QHBoxLayout:
        """Crea la barra de acciones"""
        layout = QHBoxLayout()

        # File count
        self.file_count_label = QLabel("Files: 0")
        layout.addWidget(self.file_count_label)

        layout.addStretch()

        # Action buttons
        self.open_btn = QPushButton("Open")
        self.open_btn.setIcon(
            self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon)
        )
        self.open_btn.clicked.connect(self._open_files)
        self.open_btn.setEnabled(False)
        layout.addWidget(self.open_btn)

        self.open_location_btn = QPushButton("Open Location")
        self.open_location_btn.setIcon(
            self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon)
        )
        self.open_location_btn.clicked.connect(self._open_location)
        self.open_location_btn.setEnabled(False)
        layout.addWidget(self.open_location_btn)

        self.copy_btn = QPushButton("Copy To...")
        self.copy_btn.setIcon(
            self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogDetailedView)
        )
        self.copy_btn.clicked.connect(self._copy_files)
        self.copy_btn.setEnabled(False)
        layout.addWidget(self.copy_btn)

        self.move_btn = QPushButton("Move To...")
        self.move_btn.setIcon(
            self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogDetailedView)
        )
        self.move_btn.clicked.connect(self._move_files)
        self.move_btn.setEnabled(False)
        layout.addWidget(self.move_btn)

        self.clear_btn = QPushButton("Clear Results")
        self.clear_btn.setIcon(
            self.style().standardIcon(self.style().StandardPixmap.SP_TrashIcon)
        )
        self.clear_btn.clicked.connect(self._clear_results)
        layout.addWidget(self.clear_btn)

        return layout

    def _setup_shortcuts(self):
        """Configura atajos de teclado"""
        # Search
        search_action = QAction(self)
        search_action.setShortcut(QKeySequence("Ctrl+F"))
        search_action.triggered.connect(lambda: self.search_input.setFocus())
        self.addAction(search_action)

        # Open
        open_action = QAction(self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self._open_files)
        self.addAction(open_action)

        # Clear
        clear_action = QAction(self)
        clear_action.setShortcut(QKeySequence("Ctrl+L"))
        clear_action.triggered.connect(self._clear_results)
        self.addAction(clear_action)

    def _apply_theme(self):
        """Aplica el tema visual"""
        if self.dark_mode:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                }
                QWidget {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                }
                QLineEdit, QComboBox {
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
            self.setStyleSheet("""
                QPushButton {
                    padding: 6px 12px;
                }
                QLineEdit, QComboBox {
                    padding: 5px;
                }
            """)

    def _toggle_theme(self, checked: bool):
        """Alterna el tema"""
        self.dark_mode = checked
        self._apply_theme()
        self.theme_btn.setText("Light Mode" if self.dark_mode else "Dark Mode")

    def _start_search(self):
        """Inicia la búsqueda"""
        # Obtener directorios seleccionados
        search_paths = self.dir_tree.get_selected_paths()
        if not search_paths:
            QMessageBox.warning(
                self,
                "No Directories",
                "Please select at least one directory to search."
            )
            return

        # Obtener términos de búsqueda
        search_text = self.search_input.text().strip()
        if not search_text:
            QMessageBox.warning(
                self,
                "No Search Terms",
                "Please enter at least one search term."
            )
            return

        # Parsear keywords (separadas por *)
        keywords = [kw.strip() for kw in search_text.split('*') if kw.strip()]

        # Obtener opciones
        search_filename = self.search_filename_cb.isChecked()
        search_content = self.search_content_cb.isChecked()

        if not search_filename and not search_content:
            QMessageBox.warning(
                self,
                "No Search Options",
                "Please select at least Filename or Content search."
            )
            return

        # Limpiar resultados anteriores
        self._clear_results()

        # Crear worker
        self.search_worker = IntegratedSearchWorker(
            self.search_service,
            keywords,
            search_paths,
            search_content,
            search_filename
        )

        # Conectar señales
        self.search_worker.progress.connect(self._on_search_progress)
        self.search_worker.result.connect(self._on_search_result)
        self.search_worker.finished.connect(self._on_search_finished)
        self.search_worker.error.connect(self._on_search_error)

        # Actualizar UI
        self.search_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_bar.showMessage("Searching...")

        # Iniciar búsqueda
        self.search_worker.start()

    def _stop_search(self):
        """Detiene la búsqueda"""
        if self.search_worker:
            self.search_worker.stop()
            if not self.search_worker.wait(5000):  # 5 seconds timeout
                self.search_worker.terminate()
                logger.warning("Search worker terminated due to timeout")
            self._on_search_finished(0)

    def _on_search_progress(self, percentage: int, current_file: str):
        """Maneja progreso de búsqueda"""
        self.status_bar.showMessage(f"Searching: {current_file}")

    def _on_search_result(self, result: SearchResult):
        """Maneja un resultado de búsqueda"""
        # Añadir a la tabla correspondiente
        category = result.category
        table = self.result_tables[category]
        table.add_result(result)

        # Actualizar contadores
        total = sum(table.rowCount() for table in self.result_tables.values())
        self.file_count_label.setText(f"Files: {total}")

        # Actualizar etiquetas de tabs
        for cat, tbl in self.result_tables.items():
            count = tbl.rowCount()
            tab_index = list(self.result_tables.keys()).index(cat)
            self.results_tabs.setTabText(tab_index, f"{cat.value} ({count})")

    def _on_search_finished(self, total_files: int):
        """Maneja finalización de búsqueda"""
        self.search_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(
            f"Search complete. Found {total_files} files.",
            5000
        )

    def _on_search_error(self, error_msg: str):
        """Maneja error de búsqueda"""
        QMessageBox.critical(self, "Search Error", error_msg)
        self._on_search_finished(0)

    def _get_current_table(self) -> Optional[ClassifiedResultsTableWidget]:
        """Obtiene la tabla actualmente visible"""
        current_widget = self.results_tabs.currentWidget()
        if isinstance(current_widget, ClassifiedResultsTableWidget):
            return current_widget
        return None

    def _update_button_states(self):
        """Actualiza estado de botones según selección"""
        table = self._get_current_table()
        has_selection = table and len(table.get_selected_files()) > 0

        self.open_btn.setEnabled(has_selection)
        self.open_location_btn.setEnabled(has_selection)
        self.copy_btn.setEnabled(has_selection)
        self.move_btn.setEnabled(has_selection)

    def _open_files(self):
        """Abre archivos seleccionados"""
        table = self._get_current_table()
        if not table:
            return

        files = table.get_selected_files()
        for file_path in files[:10]:
            self.file_ops.open_file(file_path)

        if len(files) > 10:
            QMessageBox.information(
                self,
                "Too Many Files",
                f"Only opening first 10 of {len(files)} selected files."
            )

    def _open_location(self):
        """Abre ubicación en explorador"""
        table = self._get_current_table()
        if not table:
            return

        files = table.get_selected_files()
        if files:
            self.file_ops.open_location(files[0])

    def _copy_files(self):
        """Copia archivos seleccionados"""
        table = self._get_current_table()
        if not table:
            return

        files = table.get_selected_files()
        if not files:
            return

        destination = QFileDialog.getExistingDirectory(
            self,
            "Select Destination for Copy",
            os.path.expanduser("~")
        )

        if not destination:
            return

        # Copiar archivos
        success_count = 0
        error_count = 0

        for file_path in files:
            try:
                self.file_ops.copy(file_path, destination)
                success_count += 1
            except Exception as e:
                error_count += 1

        # Mostrar resultado
        msg = f"Copy complete.\nSuccessful: {success_count}"
        if error_count > 0:
            msg += f"\nErrors: {error_count}"

        QMessageBox.information(self, "Copy Complete", msg)

    def _move_files(self):
        """Mueve archivos seleccionados"""
        table = self._get_current_table()
        if not table:
            return

        files = table.get_selected_files()
        if not files:
            return

        destination = QFileDialog.getExistingDirectory(
            self,
            "Select Destination for Move",
            os.path.expanduser("~")
        )

        if not destination:
            return

        # Confirmar
        reply = QMessageBox.question(
            self,
            "Confirm Move",
            f"Move {len(files)} file(s) to:\n{destination}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Mover archivos
        success_count = 0
        error_count = 0

        for file_path in files:
            try:
                self.file_ops.move(file_path, destination)
                success_count += 1
            except Exception as e:
                error_count += 1

        # Mostrar resultado
        msg = f"Move complete.\nSuccessful: {success_count}"
        if error_count > 0:
            msg += f"\nErrors: {error_count}"

        QMessageBox.information(self, "Move Complete", msg)

    def _clear_results(self):
        """Limpia todos los resultados"""
        for table in self.result_tables.values():
            table.setRowCount(0)

        # Resetear etiquetas
        for cat in self.result_tables.keys():
            tab_index = list(self.result_tables.keys()).index(cat)
            self.results_tabs.setTabText(tab_index, cat.value)

        self.file_count_label.setText("Files: 0")
        self.status_bar.showMessage("Results cleared", 3000)

    def _load_config(self):
        """Carga configuración de la aplicación"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)

                # Restaurar tema
                if config.get('dark_mode', False):
                    self.theme_btn.setChecked(True)
                    self._toggle_theme(True)

            except Exception as e:
                print(f"Error loading config: {e}")

    def _save_config(self):
        """Guarda configuración de la aplicación"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        config = {
            'version': APP_VERSION,
            'dark_mode': self.dark_mode
        }

        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)

            # Guardar configuración del árbol
            self.dir_tree.save_tree_config()

        except Exception as e:
            print(f"Error saving config: {e}")

    def closeEvent(self, event):
        """Maneja el cierre de la aplicación"""
        # Guardar configuración
        self._save_config()

        # Detener búsqueda activa
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.stop()
            if not self.search_worker.wait(3000):  # 3 seconds timeout
                self.search_worker.terminate()
                logger.warning("Search worker terminated on close")

        event.accept()


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

def main():
    """Punto de entrada de la aplicación"""
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("SmartTools")

    # Set app icon early
    app_icon = create_app_icon()
    app.setWindowIcon(app_icon)

    # Configurar fuente
    font = QFont("Segoe UI", 9)
    app.setFont(font)

    # Crear y mostrar ventana principal
    window = SmartSearchApp()
    window.show()

    # Ensure window comes to foreground
    window.raise_()
    window.activateWindow()

    # On Windows, use additional methods to bring to front
    if sys.platform == 'win32':
        try:
            import ctypes
            hwnd = int(window.winId())
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass  # Fallback if ctypes fails

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
