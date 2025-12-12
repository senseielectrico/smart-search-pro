"""
Smart Search UI Enhancements - Advanced UX Components
Modern widgets and features for improved user experience

Features:
- Search history with autocomplete
- Quick filter chips
- File preview panel
- Enhanced directory tree with favorites
- Grid view for results
- Export to CSV
- Search presets
- Accessibility improvements
"""

import os
import sys
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Optional, Callable
from dataclasses import dataclass, asdict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLabel, QScrollArea, QFrame,
    QFileDialog, QMessageBox, QDialog, QDialogButtonBox, QListWidget,
    QCompleter, QMenu, QToolButton, QTextEdit, QGridLayout, QSizePolicy,
    QButtonGroup, QRadioButton, QSlider, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QStringListModel, QTimer, QRect
from PyQt6.QtGui import (
    QIcon, QPixmap, QImage, QPainter, QColor, QFont, QAction,
    QKeySequence, QCursor, QPalette, QFontMetrics
)


# ========================================
# DATA MODELS
# ========================================

@dataclass
class SearchPreset:
    """Search preset configuration"""
    name: str
    search_term: str
    paths: List[str]
    case_sensitive: bool = False
    file_types: List[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'SearchPreset':
        return cls(**data)


@dataclass
class SearchHistory:
    """Search history entry"""
    term: str
    timestamp: datetime
    paths: List[str]
    results_count: int

    def to_dict(self) -> dict:
        return {
            'term': self.term,
            'timestamp': self.timestamp.isoformat(),
            'paths': self.paths,
            'results_count': self.results_count
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SearchHistory':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


# ========================================
# SEARCH ENHANCEMENTS
# ========================================

class SearchHistoryWidget(QWidget):
    """Widget for managing search history with autocomplete"""

    search_selected = pyqtSignal(str, list)  # term, paths

    def __init__(self, parent=None):
        super().__init__(parent)
        self.history: List[SearchHistory] = []
        self.max_history = 50
        self._init_ui()
        self._load_history()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QHBoxLayout()
        title = QLabel("Recent Searches")
        title.setStyleSheet("font-weight: bold;")
        header.addWidget(title)

        clear_btn = QPushButton("Clear")
        clear_btn.setMaximumWidth(60)
        clear_btn.clicked.connect(self.clear_history)
        header.addWidget(clear_btn)

        layout.addLayout(header)

        # History list
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self._on_item_selected)
        layout.addWidget(self.history_list)

    def add_search(self, term: str, paths: List[str], results_count: int):
        """Add search to history"""
        entry = SearchHistory(
            term=term,
            timestamp=datetime.now(),
            paths=paths,
            results_count=results_count
        )

        # Remove duplicates
        self.history = [h for h in self.history if h.term != term]

        # Add to front
        self.history.insert(0, entry)

        # Limit size
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]

        self._update_list()
        self._save_history()

    def _update_list(self):
        """Update history list display"""
        self.history_list.clear()

        for entry in self.history[:20]:  # Show last 20
            time_str = entry.timestamp.strftime("%Y-%m-%d %H:%M")
            text = f"{entry.term} ({entry.results_count} results) - {time_str}"
            self.history_list.addItem(text)

    def _on_item_selected(self, item):
        """Handle history item selection"""
        index = self.history_list.row(item)
        if 0 <= index < len(self.history):
            entry = self.history[index]
            self.search_selected.emit(entry.term, entry.paths)

    def get_terms(self) -> List[str]:
        """Get list of search terms for autocomplete"""
        return [h.term for h in self.history]

    def clear_history(self):
        """Clear all history"""
        reply = QMessageBox.question(
            self, "Clear History",
            "Are you sure you want to clear search history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self._update_list()
            self._save_history()

    def _save_history(self):
        """Save history to file"""
        try:
            history_file = Path.home() / '.smart_search_history.json'
            data = [h.to_dict() for h in self.history]
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def _load_history(self):
        """Load history from file"""
        try:
            history_file = Path.home() / '.smart_search_history.json'
            if history_file.exists():
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.history = [SearchHistory.from_dict(h) for h in data]
                    self._update_list()
        except Exception as e:
            print(f"Error loading history: {e}")


class QuickFilterChips(QWidget):
    """Quick filter chips for common file types"""

    filter_changed = pyqtSignal(list)  # list of selected extensions

    FILTERS = [
        ("All Files", []),
        ("Images", [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"]),
        ("Documents", [".pdf", ".doc", ".docx", ".txt", ".odt"]),
        ("Videos", [".mp4", ".avi", ".mkv", ".mov", ".wmv"]),
        ("Audio", [".mp3", ".wav", ".flac", ".aac", ".ogg"]),
        ("Code", [".py", ".js", ".ts", ".java", ".cpp", ".html", ".css"]),
        ("Archives", [".zip", ".rar", ".7z", ".tar", ".gz"]),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_filter = []
        self._init_ui()

    def _init_ui(self):
        """Initialize UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        label = QLabel("Quick Filters:")
        layout.addWidget(label)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        for i, (name, extensions) in enumerate(self.FILTERS):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setProperty("extensions", extensions)
            btn.clicked.connect(self._on_filter_clicked)

            if i == 0:  # Select "All Files" by default
                btn.setChecked(True)

            self.button_group.addButton(btn, i)
            layout.addWidget(btn)

        layout.addStretch()

    def _on_filter_clicked(self):
        """Handle filter button click"""
        sender = self.sender()
        if sender:
            self.selected_filter = sender.property("extensions") or []
            self.filter_changed.emit(self.selected_filter)

    def get_selected_filter(self) -> List[str]:
        """Get currently selected filter extensions"""
        return self.selected_filter


# ========================================
# ENHANCED DIRECTORY TREE
# ========================================

class EnhancedDirectoryTree(QTreeWidget):
    """Enhanced directory tree with favorites and search"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.favorites: Set[str] = set()
        self._init_ui()
        self._load_favorites()

    def _init_ui(self):
        """Initialize UI"""
        self.setHeaderLabel("Directories to Search")
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # Add toolbar
        self.setHeaderLabels(["Directory", "Size", "Status"])

    def add_favorite(self, path: str):
        """Add directory to favorites"""
        self.favorites.add(path)
        self._save_favorites()
        self._update_item_style(path)

    def remove_favorite(self, path: str):
        """Remove directory from favorites"""
        self.favorites.discard(path)
        self._save_favorites()
        self._update_item_style(path)

    def _update_item_style(self, path: str):
        """Update visual style for favorite items"""
        # Find and update item
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            self._update_item_recursive(item, path)

    def _update_item_recursive(self, item: QTreeWidgetItem, path: str):
        """Recursively update item style"""
        item_path = item.data(0, Qt.ItemDataRole.UserRole)

        if item_path == path:
            if path in self.favorites:
                font = item.font(0)
                font.setBold(True)
                item.setFont(0, font)
                item.setForeground(0, QColor("#FFD700"))  # Gold color
                item.setText(0, f"★ {item.text(0).replace('★ ', '')}")
            else:
                font = item.font(0)
                font.setBold(False)
                item.setFont(0, font)
                item.setForeground(0, QColor())
                item.setText(0, item.text(0).replace('★ ', ''))

        for i in range(item.childCount()):
            self._update_item_recursive(item.child(i), path)

    def _show_context_menu(self, position):
        """Show context menu"""
        item = self.itemAt(position)
        if not item:
            return

        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path:
            return

        menu = QMenu(self)

        # Favorite action
        if path in self.favorites:
            action = QAction("Remove from Favorites", self)
            action.triggered.connect(lambda: self.remove_favorite(path))
        else:
            action = QAction("Add to Favorites", self)
            action.triggered.connect(lambda: self.add_favorite(path))
        menu.addAction(action)

        menu.addSeparator()

        # Expand/collapse
        expand_action = QAction("Expand All", self)
        expand_action.triggered.connect(lambda: self._expand_all(item))
        menu.addAction(expand_action)

        collapse_action = QAction("Collapse All", self)
        collapse_action.triggered.connect(lambda: self._collapse_all(item))
        menu.addAction(collapse_action)

        menu.addSeparator()

        # Open in Explorer
        open_action = QAction("Open in Explorer", self)
        open_action.triggered.connect(lambda: os.startfile(path))
        menu.addAction(open_action)

        # Show properties
        props_action = QAction("Properties", self)
        props_action.triggered.connect(lambda: self._show_properties(path))
        menu.addAction(props_action)

        menu.exec(self.viewport().mapToGlobal(position))

    def _expand_all(self, item: QTreeWidgetItem):
        """Recursively expand item and children"""
        item.setExpanded(True)
        for i in range(item.childCount()):
            self._expand_all(item.child(i))

    def _collapse_all(self, item: QTreeWidgetItem):
        """Recursively collapse item and children"""
        item.setExpanded(False)
        for i in range(item.childCount()):
            self._collapse_all(item.child(i))

    def _show_properties(self, path: str):
        """Show directory properties"""
        try:
            size = self._calculate_directory_size(path)
            file_count = sum(1 for _ in Path(path).rglob('*') if _.is_file())

            msg = f"Path: {path}\n\n"
            msg += f"Total Size: {self._format_size(size)}\n"
            msg += f"File Count: {file_count}\n"
            msg += f"Favorite: {'Yes' if path in self.favorites else 'No'}"

            QMessageBox.information(self, "Directory Properties", msg)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not read properties: {e}")

    def _calculate_directory_size(self, path: str) -> int:
        """Calculate total directory size"""
        total = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += self._calculate_directory_size(entry.path)
        except PermissionError:
            pass
        return total

    def _format_size(self, size: int) -> str:
        """Format size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def _save_favorites(self):
        """Save favorites to file"""
        try:
            favorites_file = Path.home() / '.smart_search_favorites.json'
            with open(favorites_file, 'w') as f:
                json.dump(list(self.favorites), f, indent=2)
        except Exception as e:
            print(f"Error saving favorites: {e}")

    def _load_favorites(self):
        """Load favorites from file"""
        try:
            favorites_file = Path.home() / '.smart_search_favorites.json'
            if favorites_file.exists():
                with open(favorites_file, 'r') as f:
                    self.favorites = set(json.load(f))
        except Exception as e:
            print(f"Error loading favorites: {e}")


# ========================================
# FILE PREVIEW PANEL
# ========================================

class FilePreviewPanel(QWidget):
    """Panel for previewing selected files"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self._init_ui()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Header
        self.title_label = QLabel("Preview")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(self.title_label)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)

        # Image preview
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(200, 200)
        self.image_label.setScaledContents(False)
        self.content_layout.addWidget(self.image_label)

        # Text preview
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setMaximumHeight(300)
        self.content_layout.addWidget(self.text_preview)

        # File info
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.content_layout.addWidget(self.info_label)

        self.content_layout.addStretch()

        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)

        # Initially hide all
        self._hide_all()

    def preview_file(self, file_path: str):
        """Preview file"""
        self.current_file = file_path
        self._hide_all()

        if not os.path.exists(file_path):
            self.info_label.setText("File not found")
            self.info_label.setVisible(True)
            return

        # Update title
        self.title_label.setText(f"Preview: {os.path.basename(file_path)}")

        # Get file info
        stat = os.stat(file_path)
        info_text = f"<b>Path:</b> {file_path}<br>"
        info_text += f"<b>Size:</b> {self._format_size(stat.st_size)}<br>"
        info_text += f"<b>Modified:</b> {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}<br>"
        info_text += f"<b>Type:</b> {Path(file_path).suffix.upper() or 'FILE'}"

        self.info_label.setText(info_text)
        self.info_label.setVisible(True)

        # Preview based on file type
        ext = Path(file_path).suffix.lower()

        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.webp']:
            self._preview_image(file_path)
        elif ext in ['.txt', '.log', '.md', '.json', '.xml', '.csv', '.py', '.js', '.html', '.css']:
            self._preview_text(file_path)
        else:
            self.text_preview.setPlainText("Preview not available for this file type")
            self.text_preview.setVisible(True)

    def _preview_image(self, file_path: str):
        """Preview image file"""
        try:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # Scale to fit while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    400, 400,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                self.image_label.setVisible(True)
        except Exception as e:
            self.text_preview.setPlainText(f"Error loading image: {e}")
            self.text_preview.setVisible(True)

    def _preview_text(self, file_path: str):
        """Preview text file"""
        try:
            # Read first 10KB
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(10240)

            self.text_preview.setPlainText(content)
            self.text_preview.setVisible(True)

            if len(content) >= 10240:
                self.text_preview.append("\n\n... (truncated)")
        except Exception as e:
            self.text_preview.setPlainText(f"Error reading file: {e}")
            self.text_preview.setVisible(True)

    def _hide_all(self):
        """Hide all preview elements"""
        self.image_label.setVisible(False)
        self.image_label.clear()
        self.text_preview.setVisible(False)
        self.text_preview.clear()
        self.info_label.setVisible(False)
        self.info_label.clear()

    def _format_size(self, size: int) -> str:
        """Format size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def clear(self):
        """Clear preview"""
        self.current_file = None
        self.title_label.setText("Preview")
        self._hide_all()


# ========================================
# GRID VIEW FOR RESULTS
# ========================================

class GridViewWidget(QWidget):
    """Grid view for file results with large icons"""

    item_selected = pyqtSignal(str)  # file path
    item_double_clicked = pyqtSignal(str)  # file path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items: List[Dict] = []
        self.selected_index = -1
        self._init_ui()

    def _init_ui(self):
        """Initialize UI"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Grid container
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(10)

        scroll.setWidget(self.grid_widget)
        self.main_layout.addWidget(scroll)

    def add_item(self, file_info: Dict):
        """Add item to grid"""
        self.items.append(file_info)
        self._refresh_grid()

    def clear(self):
        """Clear all items"""
        self.items.clear()
        self._refresh_grid()

    def _refresh_grid(self):
        """Refresh grid layout"""
        # Clear existing items
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add items in grid
        columns = 5
        for i, file_info in enumerate(self.items):
            row = i // columns
            col = i % columns

            item_widget = self._create_item_widget(file_info, i)
            self.grid_layout.addWidget(item_widget, row, col)

    def _create_item_widget(self, file_info: Dict, index: int) -> QWidget:
        """Create widget for grid item"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        widget.setLineWidth(1)
        widget.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        widget.setProperty("index", index)
        widget.setFixedSize(120, 140)

        # Install event filter for clicks
        widget.mousePressEvent = lambda event: self._on_item_clicked(index)
        widget.mouseDoubleClickEvent = lambda event: self._on_item_double_clicked(index)

        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon
        icon_label = QLabel()
        icon_label.setFixedSize(80, 80)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Try to load thumbnail for images
        path = file_info['path']
        ext = Path(path).suffix.lower()

        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            try:
                pixmap = QPixmap(path).scaled(
                    80, 80,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                icon_label.setPixmap(pixmap)
            except:
                icon_label.setText(ext.upper())
        else:
            icon_label.setText(ext.upper() or "FILE")
            icon_label.setStyleSheet("font-size: 14pt; font-weight: bold;")

        layout.addWidget(icon_label)

        # Name
        name_label = QLabel(file_info['name'])
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_metrics = QFontMetrics(name_label.font())
        elided_text = font_metrics.elidedText(
            file_info['name'], Qt.TextElideMode.ElideMiddle, 110
        )
        name_label.setText(elided_text)
        name_label.setToolTip(file_info['name'])
        layout.addWidget(name_label)

        return widget

    def _on_item_clicked(self, index: int):
        """Handle item click"""
        self.selected_index = index
        if 0 <= index < len(self.items):
            self.item_selected.emit(self.items[index]['path'])

    def _on_item_double_clicked(self, index: int):
        """Handle item double click"""
        if 0 <= index < len(self.items):
            self.item_double_clicked.emit(self.items[index]['path'])


# ========================================
# SEARCH PRESETS
# ========================================

class SearchPresetsDialog(QDialog):
    """Dialog for managing search presets"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.presets: List[SearchPreset] = []
        self.selected_preset: Optional[SearchPreset] = None
        self._init_ui()
        self._load_presets()

    def _init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Search Presets")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)

        # Preset list
        self.preset_list = QListWidget()
        self.preset_list.itemDoubleClicked.connect(self._on_preset_selected)
        layout.addWidget(self.preset_list)

        # Buttons
        button_layout = QHBoxLayout()

        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self._load_selected)
        button_layout.addWidget(load_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_selected)
        button_layout.addWidget(delete_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def add_preset(self, preset: SearchPreset):
        """Add new preset"""
        self.presets.append(preset)
        self._save_presets()
        self._update_list()

    def _update_list(self):
        """Update preset list"""
        self.preset_list.clear()
        for preset in self.presets:
            self.preset_list.addItem(f"{preset.name} - '{preset.search_term}'")

    def _on_preset_selected(self, item):
        """Handle preset selection"""
        self._load_selected()
        self.accept()

    def _load_selected(self):
        """Load selected preset"""
        index = self.preset_list.currentRow()
        if 0 <= index < len(self.presets):
            self.selected_preset = self.presets[index]

    def _delete_selected(self):
        """Delete selected preset"""
        index = self.preset_list.currentRow()
        if 0 <= index < len(self.presets):
            reply = QMessageBox.question(
                self, "Delete Preset",
                f"Delete preset '{self.presets[index].name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                del self.presets[index]
                self._save_presets()
                self._update_list()

    def _save_presets(self):
        """Save presets to file"""
        try:
            presets_file = Path.home() / '.smart_search_presets.json'
            data = [p.to_dict() for p in self.presets]
            with open(presets_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving presets: {e}")

    def _load_presets(self):
        """Load presets from file"""
        try:
            presets_file = Path.home() / '.smart_search_presets.json'
            if presets_file.exists():
                with open(presets_file, 'r') as f:
                    data = json.load(f)
                    self.presets = [SearchPreset.from_dict(p) for p in data]
                    self._update_list()
        except Exception as e:
            print(f"Error loading presets: {e}")


# ========================================
# EXPORT UTILITIES
# ========================================

class ExportDialog(QDialog):
    """Dialog for exporting search results"""

    def __init__(self, results: List[Dict], parent=None):
        super().__init__(parent)
        self.results = results
        self._init_ui()

    def _init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Export Results")
        self.setMinimumSize(400, 200)

        layout = QVBoxLayout(self)

        # Info
        info = QLabel(f"Export {len(self.results)} file(s) to CSV")
        layout.addWidget(info)

        # Options
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout()

        self.include_path_cb = QCheckBox("Include full path")
        self.include_path_cb.setChecked(True)
        options_layout.addWidget(self.include_path_cb)

        self.include_size_cb = QCheckBox("Include file size")
        self.include_size_cb.setChecked(True)
        options_layout.addWidget(self.include_size_cb)

        self.include_date_cb = QCheckBox("Include modification date")
        self.include_date_cb.setChecked(True)
        options_layout.addWidget(self.include_date_cb)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._export)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _export(self):
        """Export to CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            str(Path.home() / "search_results.csv"),
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                # Determine columns
                columns = ['Name']
                if self.include_path_cb.isChecked():
                    columns.append('Path')
                if self.include_size_cb.isChecked():
                    columns.append('Size')
                if self.include_date_cb.isChecked():
                    columns.append('Modified')

                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()

                for result in self.results:
                    row = {'Name': result['name']}

                    if self.include_path_cb.isChecked():
                        row['Path'] = result['path']

                    if self.include_size_cb.isChecked():
                        row['Size'] = result['size']

                    if self.include_date_cb.isChecked():
                        row['Modified'] = result['modified'].strftime('%Y-%m-%d %H:%M:%S')

                    writer.writerow(row)

            QMessageBox.information(self, "Export Complete", f"Results exported to:\n{file_path}")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting results:\n{str(e)}")


# ========================================
# ACCESSIBILITY FEATURES
# ========================================

class AccessibleTooltip:
    """Enhanced tooltip with better accessibility"""

    @staticmethod
    def set_tooltip(widget: QWidget, text: str, shortcut: str = None):
        """Set accessible tooltip with optional keyboard shortcut"""
        tooltip = text
        if shortcut:
            tooltip += f" ({shortcut})"

        widget.setToolTip(tooltip)
        widget.setStatusTip(text)


class KeyboardShortcutsDialog(QDialog):
    """Dialog showing all keyboard shortcuts"""

    SHORTCUTS = [
        ("Search", "Ctrl+F", "Focus search input"),
        ("Search", "Enter", "Start search"),
        ("Search", "Esc", "Stop search"),
        ("Files", "Ctrl+O", "Open selected files"),
        ("Files", "Ctrl+Shift+C", "Copy files to..."),
        ("Files", "Ctrl+M", "Move files to..."),
        ("Files", "Delete", "Delete selected files"),
        ("View", "Ctrl+L", "Clear results"),
        ("View", "Ctrl+1-8", "Switch to tab"),
        ("View", "Ctrl+E", "Export results"),
        ("Navigation", "Tab", "Move between elements"),
        ("Navigation", "Arrow Keys", "Navigate list/tree"),
        ("Navigation", "Space", "Toggle checkbox"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Keyboard Shortcuts")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title)

        # Shortcuts list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        shortcuts_widget = QWidget()
        shortcuts_layout = QVBoxLayout(shortcuts_widget)

        current_category = None
        for category, shortcut, description in self.SHORTCUTS:
            if category != current_category:
                current_category = category

                # Category header
                header = QLabel(category)
                header.setStyleSheet("font-weight: bold; font-size: 11pt; margin-top: 10px;")
                shortcuts_layout.addWidget(header)

            # Shortcut row
            row_layout = QHBoxLayout()

            shortcut_label = QLabel(shortcut)
            shortcut_label.setStyleSheet("font-family: monospace; background-color: #f0f0f0; padding: 3px 8px; border-radius: 3px;")
            shortcut_label.setMinimumWidth(150)
            row_layout.addWidget(shortcut_label)

            desc_label = QLabel(description)
            row_layout.addWidget(desc_label)
            row_layout.addStretch()

            shortcuts_layout.addLayout(row_layout)

        shortcuts_layout.addStretch()
        scroll.setWidget(shortcuts_widget)
        layout.addWidget(scroll)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


# ========================================
# NOTIFICATION SYSTEM
# ========================================

class NotificationWidget(QWidget):
    """Toast-style notification widget"""

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._init_ui(message)

        # Auto-hide timer
        QTimer.singleShot(3000, self.hide)

    def _init_ui(self, message: str):
        """Initialize UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)

        self.setStyleSheet("""
            QWidget {
                background-color: #323232;
                border-radius: 5px;
                color: white;
            }
        """)

        label = QLabel(message)
        label.setStyleSheet("color: white; font-size: 10pt;")
        layout.addWidget(label)

        self.adjustSize()


def show_notification(parent: QWidget, message: str):
    """Show notification toast"""
    notification = NotificationWidget(message, parent)

    # Position at bottom-right of parent
    if parent:
        parent_rect = parent.geometry()
        x = parent_rect.right() - notification.width() - 20
        y = parent_rect.bottom() - notification.height() - 20
        notification.move(x, y)

    notification.show()

    return notification
