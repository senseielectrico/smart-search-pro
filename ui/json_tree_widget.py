"""
JSON Tree Widget
================

Reusable JSON tree widget for Smart Search Pro UI.
Features:
- QTreeView with custom model for JSON
- Icons for different types
- Value preview in tooltips
- Copy path to node
- Copy value
- Expand/collapse controls

Usage:
    tree = JSONTreeWidget()
    tree.load_json({"key": "value", "array": [1, 2, 3]})
"""

import json
from typing import Any, Optional, List
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QPushButton,
    QLineEdit, QLabel, QMenu, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QAbstractItemModel, QModelIndex, pyqtSignal
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor, QBrush, QIcon, QAction


class JSONNodeType(Enum):
    """JSON node types"""
    OBJECT = "object"
    ARRAY = "array"
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    NULL = "null"


class JSONTreeNode:
    """Node in JSON tree"""

    def __init__(self, key: str, value: Any, parent: Optional['JSONTreeNode'] = None):
        self.key = key
        self.value = value
        self.parent = parent
        self.children: List['JSONTreeNode'] = []
        self.node_type = self._determine_type(value)

    def _determine_type(self, value: Any) -> JSONNodeType:
        """Determine node type"""
        if value is None:
            return JSONNodeType.NULL
        elif isinstance(value, bool):
            return JSONNodeType.BOOLEAN
        elif isinstance(value, (int, float)):
            return JSONNodeType.NUMBER
        elif isinstance(value, str):
            return JSONNodeType.STRING
        elif isinstance(value, dict):
            return JSONNodeType.OBJECT
        elif isinstance(value, list):
            return JSONNodeType.ARRAY
        else:
            return JSONNodeType.STRING

    def add_child(self, child: 'JSONTreeNode'):
        """Add child node"""
        self.children.append(child)
        child.parent = self

    def get_path(self) -> str:
        """Get JSON path to this node"""
        path_parts = []
        node = self
        while node.parent:
            if node.parent.node_type == JSONNodeType.ARRAY:
                index = node.parent.children.index(node)
                path_parts.insert(0, f"[{index}]")
            else:
                path_parts.insert(0, f".{node.key}")
            node = node.parent

        path = "".join(path_parts)
        if path.startswith('.'):
            path = path[1:]

        return path or "root"

    def get_display_value(self) -> str:
        """Get display value"""
        if self.node_type == JSONNodeType.OBJECT:
            return f"{{ {len(self.children)} }}"
        elif self.node_type == JSONNodeType.ARRAY:
            return f"[ {len(self.children)} ]"
        elif self.node_type == JSONNodeType.STRING:
            value_str = str(self.value)
            if len(value_str) > 50:
                return f'"{value_str[:50]}..."'
            return f'"{value_str}"'
        elif self.node_type == JSONNodeType.NULL:
            return "null"
        elif self.node_type == JSONNodeType.BOOLEAN:
            return "true" if self.value else "false"
        else:
            return str(self.value)

    def get_icon_name(self) -> str:
        """Get icon name for this node type"""
        icons = {
            JSONNodeType.OBJECT: "folder",
            JSONNodeType.ARRAY: "list",
            JSONNodeType.STRING: "text",
            JSONNodeType.NUMBER: "number",
            JSONNodeType.BOOLEAN: "check",
            JSONNodeType.NULL: "null",
        }
        return icons.get(self.node_type, "default")


class JSONTreeModel(QAbstractItemModel):
    """Tree model for JSON data"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root_node: Optional[JSONTreeNode] = None

    def load_json(self, data: Any, root_key: str = "root"):
        """Load JSON data"""
        self.beginResetModel()
        self.root_node = self._build_tree(root_key, data)
        self.endResetModel()

    def _build_tree(self, key: str, value: Any, parent: Optional[JSONTreeNode] = None) -> JSONTreeNode:
        """Build tree recursively"""
        node = JSONTreeNode(key, value, parent)

        if isinstance(value, dict):
            for k, v in value.items():
                child = self._build_tree(k, v, node)
                node.add_child(child)
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                child = self._build_tree(f"[{idx}]", item, node)
                node.add_child(child)

        return node

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        """Create index"""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_node = self.root_node
        else:
            parent_node = parent.internalPointer()

        if parent_node and row < len(parent_node.children):
            child_node = parent_node.children[row]
            return self.createIndex(row, column, child_node)

        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        """Get parent index"""
        if not index.isValid():
            return QModelIndex()

        child_node = index.internalPointer()
        if not child_node:
            return QModelIndex()

        parent_node = child_node.parent

        if parent_node == self.root_node or parent_node is None:
            return QModelIndex()

        grandparent = parent_node.parent
        if grandparent:
            row = grandparent.children.index(parent_node)
            return self.createIndex(row, 0, parent_node)

        return QModelIndex()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get row count"""
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parent_node = self.root_node
        else:
            parent_node = parent.internalPointer()

        if parent_node:
            return len(parent_node.children)

        return 0

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get column count"""
        return 2

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Get data"""
        if not index.isValid():
            return None

        node = index.internalPointer()
        if not node:
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return node.key
            elif index.column() == 1:
                return node.get_display_value()

        elif role == Qt.ItemDataRole.ForegroundRole:
            # Color code by type
            colors = {
                JSONNodeType.STRING: QColor(206, 145, 120),
                JSONNodeType.NUMBER: QColor(181, 206, 168),
                JSONNodeType.BOOLEAN: QColor(86, 156, 214),
                JSONNodeType.NULL: QColor(128, 128, 128),
                JSONNodeType.OBJECT: QColor(78, 201, 176),
                JSONNodeType.ARRAY: QColor(220, 220, 170),
            }
            return QBrush(colors.get(node.node_type, QColor(212, 212, 212)))

        elif role == Qt.ItemDataRole.ToolTipRole:
            path = node.get_path()
            value_preview = str(node.value)
            if len(value_preview) > 100:
                value_preview = value_preview[:100] + "..."
            return f"Path: {path}\nType: {node.node_type.value}\nValue: {value_preview}"

        elif role == Qt.ItemDataRole.UserRole:
            return node

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Get header data"""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return ["Key", "Value"][section]
        return None

    def get_node(self, index: QModelIndex) -> Optional[JSONTreeNode]:
        """Get node from index"""
        if index.isValid():
            return index.internalPointer()
        return self.root_node


class JSONTreeWidget(QWidget):
    """JSON tree widget with controls"""

    node_selected = pyqtSignal(object)  # Emits JSONTreeNode
    path_copied = pyqtSignal(str)
    value_copied = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.model = JSONTreeModel()

        self._init_ui()
        self._setup_connections()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = QHBoxLayout()

        # Expand/collapse buttons
        expand_btn = QPushButton("Expand All")
        expand_btn.clicked.connect(self._expand_all)
        toolbar.addWidget(expand_btn)

        collapse_btn = QPushButton("Collapse All")
        collapse_btn.clicked.connect(self._collapse_all)
        toolbar.addWidget(collapse_btn)

        toolbar.addStretch()

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setMaximumWidth(200)
        toolbar.addWidget(self.search_input)

        layout.addLayout(toolbar)

        # Tree view
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self._show_context_menu)

        # Set column widths
        from PyQt6.QtWidgets import QHeaderView
        header = self.tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tree_view.setColumnWidth(0, 300)

        layout.addWidget(self.tree_view)

        # Info label
        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.info_label)

    def _setup_connections(self):
        """Setup connections"""
        self.tree_view.selectionModel().currentChanged.connect(self._on_selection_changed)
        self.search_input.textChanged.connect(self._search)

    def load_json(self, data: Any):
        """Load JSON data"""
        self.model.load_json(data)
        self.tree_view.expandToDepth(2)

        # Update info
        node_count = self._count_nodes(self.model.root_node)
        self.info_label.setText(f"Nodes: {node_count}")

    def _count_nodes(self, node: Optional[JSONTreeNode]) -> int:
        """Count total nodes"""
        if not node:
            return 0

        count = 1
        for child in node.children:
            count += self._count_nodes(child)

        return count

    def load_json_file(self, file_path: str):
        """Load JSON from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.load_json(data)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load JSON:\n{str(e)}")

    def load_json_string(self, json_str: str):
        """Load JSON from string"""
        try:
            data = json.loads(json_str)
            self.load_json(data)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Parse Error", f"Invalid JSON:\n{str(e)}")

    def get_selected_node(self) -> Optional[JSONTreeNode]:
        """Get currently selected node"""
        index = self.tree_view.currentIndex()
        return self.model.get_node(index)

    def _expand_all(self):
        """Expand all nodes"""
        self.tree_view.expandAll()

    def _collapse_all(self):
        """Collapse all nodes"""
        self.tree_view.collapseAll()

    def _on_selection_changed(self, current: QModelIndex, previous: QModelIndex):
        """Handle selection change"""
        node = self.model.get_node(current)
        if node:
            self.node_selected.emit(node)

    def _search(self, text: str):
        """Search in tree"""
        # Simple implementation - could be enhanced
        # For now, just highlight matching text
        # TODO: Implement proper search with result navigation
        pass

    def _show_context_menu(self, position):
        """Show context menu"""
        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return

        node = self.model.get_node(index)
        if not node:
            return

        menu = QMenu(self)

        # Copy path action
        copy_path_action = QAction(f"Copy Path: {node.get_path()}", self)
        copy_path_action.triggered.connect(lambda: self._copy_path(node))
        menu.addAction(copy_path_action)

        # Copy value action
        copy_value_action = QAction("Copy Value", self)
        copy_value_action.triggered.connect(lambda: self._copy_value(node))
        menu.addAction(copy_value_action)

        # Copy JSON action (for objects/arrays)
        if node.node_type in (JSONNodeType.OBJECT, JSONNodeType.ARRAY):
            copy_json_action = QAction("Copy as JSON", self)
            copy_json_action.triggered.connect(lambda: self._copy_as_json(node))
            menu.addAction(copy_json_action)

        menu.addSeparator()

        # Expand/Collapse
        if node.children:
            if self.tree_view.isExpanded(index):
                collapse_action = QAction("Collapse", self)
                collapse_action.triggered.connect(lambda: self.tree_view.collapse(index))
                menu.addAction(collapse_action)
            else:
                expand_action = QAction("Expand", self)
                expand_action.triggered.connect(lambda: self.tree_view.expand(index))
                menu.addAction(expand_action)

        menu.exec(self.tree_view.viewport().mapToGlobal(position))

    def _copy_path(self, node: JSONTreeNode):
        """Copy path to clipboard"""
        path = node.get_path()
        QApplication.clipboard().setText(path)
        self.path_copied.emit(path)

    def _copy_value(self, node: JSONTreeNode):
        """Copy value to clipboard"""
        value_str = str(node.value)
        QApplication.clipboard().setText(value_str)
        self.value_copied.emit(value_str)

    def _copy_as_json(self, node: JSONTreeNode):
        """Copy node as JSON to clipboard"""
        json_data = self._node_to_json(node)
        json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
        QApplication.clipboard().setText(json_str)
        self.value_copied.emit(json_str)

    def _node_to_json(self, node: JSONTreeNode) -> Any:
        """Convert node back to JSON"""
        if node.node_type == JSONNodeType.OBJECT:
            return {child.key: self._node_to_json(child) for child in node.children}
        elif node.node_type == JSONNodeType.ARRAY:
            return [self._node_to_json(child) for child in node.children]
        else:
            return node.value


# Example usage
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Create widget
    widget = JSONTreeWidget()
    widget.setWindowTitle("JSON Tree Widget")
    widget.resize(800, 600)

    # Load sample data
    sample_data = {
        "name": "Smart Search Pro",
        "version": "1.0.0",
        "features": [
            "Database viewer",
            "JSON viewer",
            "File search"
        ],
        "config": {
            "theme": "dark",
            "max_results": 1000,
            "enabled": True
        },
        "stats": {
            "files_indexed": 15234,
            "total_size": 5368709120,
            "last_scan": None
        }
    }

    widget.load_json(sample_data)

    # Connect signals
    widget.node_selected.connect(lambda node: print(f"Selected: {node.get_path()}"))
    widget.path_copied.connect(lambda path: print(f"Copied path: {path}"))

    widget.show()
    sys.exit(app.exec())
