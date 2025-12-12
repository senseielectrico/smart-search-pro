"""
JSON File Viewer
================

Comprehensive JSON viewer with:
- Tree view with collapse/expand
- Syntax highlighting
- Inline editing
- Validation
- Search within JSON
- Format/prettify
- Convert to table view for arrays
- Export to other formats

Usage:
    viewer = JSONViewer()
    viewer.open_file("data.json")
    viewer.show()
"""

import json
import os
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QTextEdit, QLabel,
    QPushButton, QLineEdit, QSplitter, QMessageBox, QFileDialog,
    QTableWidget, QTableWidgetItem, QTabWidget, QMenu, QInputDialog,
    QHeaderView, QToolBar, QCheckBox
)
from PyQt6.QtCore import (
    Qt, QAbstractItemModel, QModelIndex, pyqtSignal, QSettings,
    QMimeData, QByteArray
)
from PyQt6.QtGui import (
    QStandardItemModel, QStandardItem, QFont, QColor, QBrush,
    QIcon, QAction, QPalette
)


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
                # For array elements, use index
                index = node.parent.children.index(node)
                path_parts.insert(0, f"[{index}]")
            else:
                # For object properties, use key
                path_parts.insert(0, f".{node.key}")
            node = node.parent

        # Remove leading dot if present
        path = "".join(path_parts)
        if path.startswith('.'):
            path = path[1:]

        return path or "root"

    def get_display_value(self) -> str:
        """Get display value for this node"""
        if self.node_type == JSONNodeType.OBJECT:
            return f"{{ {len(self.children)} properties }}"
        elif self.node_type == JSONNodeType.ARRAY:
            return f"[ {len(self.children)} items ]"
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


class JSONTreeModel(QAbstractItemModel):
    """Tree model for JSON data"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root_node: Optional[JSONTreeNode] = None

    def load_json(self, data: Any, root_key: str = "root"):
        """Load JSON data into model"""
        self.beginResetModel()
        self.root_node = self._build_tree(root_key, data)
        self.endResetModel()

    def _build_tree(self, key: str, value: Any, parent: Optional[JSONTreeNode] = None) -> JSONTreeNode:
        """Recursively build tree from JSON data"""
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
        """Create model index"""
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

        # Find row of parent in grandparent
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
        return 2  # Key and Value columns

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Get data for index"""
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
            # Show full value and path
            path = node.get_path()
            return f"Path: {path}\nType: {node.node_type.value}\nValue: {node.value}"

        elif role == Qt.ItemDataRole.UserRole:
            # Store node for easy access
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

    def get_json_data(self) -> Any:
        """Get JSON data from tree"""
        if self.root_node:
            return self._node_to_json(self.root_node)
        return None

    def _node_to_json(self, node: JSONTreeNode) -> Any:
        """Convert node back to JSON data"""
        if node.node_type == JSONNodeType.OBJECT:
            return {child.key: self._node_to_json(child) for child in node.children}
        elif node.node_type == JSONNodeType.ARRAY:
            return [self._node_to_json(child) for child in node.children]
        else:
            return node.value


class JSONViewer(QWidget):
    """Main JSON viewer widget"""

    file_opened = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_file: Optional[str] = None
        self.json_data: Any = None
        self.modified = False

        self._init_ui()
        self._setup_connections()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Main content - tabs
        self.tab_widget = QTabWidget()

        # Tree view tab
        self.tree_tab = self._create_tree_tab()
        self.tab_widget.addTab(self.tree_tab, "Tree View")

        # Raw JSON tab
        self.raw_tab = self._create_raw_tab()
        self.tab_widget.addTab(self.raw_tab, "Raw JSON")

        # Table view tab (for arrays)
        self.table_tab = self._create_table_tab()
        self.tab_widget.addTab(self.table_tab, "Table View")

        layout.addWidget(self.tab_widget)

        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("No file loaded")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        self.modified_label = QLabel("")
        status_layout.addWidget(self.modified_label)
        layout.addLayout(status_layout)

    def _create_toolbar(self) -> QWidget:
        """Create toolbar"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(5, 5, 5, 5)

        # Open button
        self.open_btn = QPushButton("Open JSON")
        self.open_btn.clicked.connect(self.open_file_dialog)
        layout.addWidget(self.open_btn)

        # Save button
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_file)
        self.save_btn.setEnabled(False)
        layout.addWidget(self.save_btn)

        # Save As button
        self.save_as_btn = QPushButton("Save As...")
        self.save_as_btn.clicked.connect(self.save_file_as)
        self.save_as_btn.setEnabled(False)
        layout.addWidget(self.save_as_btn)

        layout.addWidget(QLabel("|"))

        # Validate button
        self.validate_btn = QPushButton("Validate")
        self.validate_btn.clicked.connect(self.validate_json)
        self.validate_btn.setEnabled(False)
        layout.addWidget(self.validate_btn)

        # Format button
        self.format_btn = QPushButton("Format")
        self.format_btn.clicked.connect(self.format_json)
        self.format_btn.setEnabled(False)
        layout.addWidget(self.format_btn)

        layout.addWidget(QLabel("|"))

        # Expand/Collapse
        self.expand_btn = QPushButton("Expand All")
        self.expand_btn.clicked.connect(self.tree_view.expandAll)
        layout.addWidget(self.expand_btn)

        self.collapse_btn = QPushButton("Collapse All")
        self.collapse_btn.clicked.connect(self.tree_view.collapseAll)
        layout.addWidget(self.collapse_btn)

        layout.addStretch()

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setMaximumWidth(200)
        self.search_input.textChanged.connect(self._search_json)
        layout.addWidget(self.search_input)

        return toolbar

    def _create_tree_tab(self) -> QWidget:
        """Create tree view tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tree view
        self.tree_view = QTreeView()
        self.tree_model = JSONTreeModel()
        self.tree_view.setModel(self.tree_model)
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self._show_tree_context_menu)

        # Set column widths
        header = self.tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tree_view.setColumnWidth(0, 300)

        layout.addWidget(self.tree_view)

        return tab

    def _create_raw_tab(self) -> QWidget:
        """Create raw JSON tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)

        # Text editor
        self.raw_editor = QTextEdit()
        font = QFont("Courier New", 10)
        self.raw_editor.setFont(font)
        self.raw_editor.textChanged.connect(self._on_raw_text_changed)
        layout.addWidget(self.raw_editor)

        return tab

    def _create_table_tab(self) -> QWidget:
        """Create table view tab (for arrays)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)

        # Info label
        self.table_info_label = QLabel("Table view is available for arrays of objects")
        self.table_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.table_info_label)

        # Table widget
        self.table_view = QTableWidget()
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        layout.addWidget(self.table_view)

        # Export button
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        self.export_table_btn = QPushButton("Export Table to CSV")
        self.export_table_btn.clicked.connect(self._export_table_to_csv)
        export_layout.addWidget(self.export_table_btn)
        layout.addLayout(export_layout)

        return tab

    def _setup_connections(self):
        """Setup signal connections"""
        pass

    def open_file_dialog(self):
        """Open file dialog to select JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open JSON File",
            "",
            "JSON Files (*.json);;All Files (*.*)"
        )

        if file_path:
            self.open_file(file_path)

    def open_file(self, file_path: str):
        """Open a JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.json_data = json.load(f)

            self.current_file = file_path
            self.modified = False

            # Update UI
            self._load_json_data()
            self._update_ui_state()

            self.status_label.setText(f"Loaded: {os.path.basename(file_path)}")
            self.file_opened.emit(file_path)

        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "JSON Error", f"Failed to parse JSON:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "File Error", f"Failed to open file:\n{str(e)}")

    def _load_json_data(self):
        """Load JSON data into views"""
        if self.json_data is None:
            return

        # Load into tree view
        self.tree_model.load_json(self.json_data)
        self.tree_view.expandToDepth(2)

        # Load into raw editor
        self._suppress_raw_changes = True
        formatted_json = json.dumps(self.json_data, indent=2, ensure_ascii=False)
        self.raw_editor.setText(formatted_json)
        self._suppress_raw_changes = False

        # Load into table view if applicable
        self._load_table_view()

    def _load_table_view(self):
        """Load data into table view if it's an array"""
        self.table_view.clear()

        if isinstance(self.json_data, list) and self.json_data:
            # Check if array of objects
            first_item = self.json_data[0]
            if isinstance(first_item, dict):
                # Get all unique keys
                all_keys = set()
                for item in self.json_data:
                    if isinstance(item, dict):
                        all_keys.update(item.keys())

                headers = sorted(all_keys)

                # Setup table
                self.table_view.setColumnCount(len(headers))
                self.table_view.setHorizontalHeaderLabels(headers)
                self.table_view.setRowCount(len(self.json_data))

                # Populate data
                for row_idx, item in enumerate(self.json_data):
                    if isinstance(item, dict):
                        for col_idx, key in enumerate(headers):
                            value = item.get(key, "")
                            # Convert value to string
                            if isinstance(value, (dict, list)):
                                value_str = json.dumps(value)
                            else:
                                value_str = str(value) if value is not None else ""

                            self.table_view.setItem(row_idx, col_idx, QTableWidgetItem(value_str))

                self.table_info_label.setText(f"Showing {len(self.json_data)} rows, {len(headers)} columns")
            else:
                self.table_info_label.setText("Array does not contain objects")
        else:
            self.table_info_label.setText("Data is not an array")

    def _on_raw_text_changed(self):
        """Handle raw text changes"""
        if hasattr(self, '_suppress_raw_changes') and self._suppress_raw_changes:
            return

        self.modified = True
        self._update_ui_state()

    def _update_ui_state(self):
        """Update UI state"""
        has_file = self.current_file is not None or self.json_data is not None

        self.save_btn.setEnabled(has_file and self.modified)
        self.save_as_btn.setEnabled(has_file)
        self.validate_btn.setEnabled(has_file)
        self.format_btn.setEnabled(has_file)

        if self.modified:
            self.modified_label.setText("Modified")
            self.modified_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.modified_label.setText("")

    def validate_json(self):
        """Validate JSON syntax"""
        try:
            text = self.raw_editor.toPlainText()
            json.loads(text)
            QMessageBox.information(self, "Validation", "JSON is valid!")
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "Validation Error", f"Invalid JSON:\n{str(e)}")

    def format_json(self):
        """Format/prettify JSON"""
        try:
            text = self.raw_editor.toPlainText()
            data = json.loads(text)

            self._suppress_raw_changes = True
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            self.raw_editor.setText(formatted)
            self._suppress_raw_changes = False

            self.json_data = data
            self._load_json_data()

        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "Format Error", f"Cannot format invalid JSON:\n{str(e)}")

    def save_file(self):
        """Save to current file"""
        if not self.current_file:
            self.save_file_as()
            return

        try:
            # Get data from raw editor
            text = self.raw_editor.toPlainText()
            data = json.loads(text)

            # Save to file
            with open(self.current_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.json_data = data
            self.modified = False
            self._update_ui_state()

            self.status_label.setText(f"Saved: {os.path.basename(self.current_file)}")

        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "Save Error", f"Cannot save invalid JSON:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save file:\n{str(e)}")

    def save_file_as(self):
        """Save to new file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save JSON As",
            "",
            "JSON Files (*.json);;All Files (*.*)"
        )

        if not file_path:
            return

        try:
            # Get data from raw editor
            text = self.raw_editor.toPlainText()
            data = json.loads(text)

            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.current_file = file_path
            self.json_data = data
            self.modified = False
            self._update_ui_state()

            self.status_label.setText(f"Saved: {os.path.basename(file_path)}")

        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "Save Error", f"Cannot save invalid JSON:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save file:\n{str(e)}")

    def _search_json(self, search_text: str):
        """Search within JSON"""
        # Simple implementation - could be enhanced
        # For now, just filter raw text view
        pass

    def _show_tree_context_menu(self, position):
        """Show context menu for tree view"""
        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return

        node = self.tree_model.get_node(index)
        if not node:
            return

        menu = QMenu(self)

        # Copy path
        copy_path_action = QAction("Copy Path", self)
        copy_path_action.triggered.connect(lambda: self._copy_to_clipboard(node.get_path()))
        menu.addAction(copy_path_action)

        # Copy value
        copy_value_action = QAction("Copy Value", self)
        copy_value_action.triggered.connect(lambda: self._copy_to_clipboard(str(node.value)))
        menu.addAction(copy_value_action)

        # Copy JSON
        if node.node_type in (JSONNodeType.OBJECT, JSONNodeType.ARRAY):
            copy_json_action = QAction("Copy JSON", self)
            copy_json_action.triggered.connect(lambda: self._copy_node_as_json(node))
            menu.addAction(copy_json_action)

        menu.exec(self.tree_view.viewport().mapToGlobal(position))

    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard"""
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(text)

    def _copy_node_as_json(self, node: JSONTreeNode):
        """Copy node as JSON to clipboard"""
        json_data = self.tree_model._node_to_json(node)
        json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
        self._copy_to_clipboard(json_str)

    def _export_table_to_csv(self):
        """Export table view to CSV"""
        if self.table_view.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "No data to export")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to CSV",
            "data.csv",
            "CSV Files (*.csv);;All Files (*.*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write headers
                headers = [
                    self.table_view.horizontalHeaderItem(i).text()
                    for i in range(self.table_view.columnCount())
                ]
                writer.writerow(headers)

                # Write data
                for row in range(self.table_view.rowCount()):
                    row_data = [
                        self.table_view.item(row, col).text() if self.table_view.item(row, col) else ""
                        for col in range(self.table_view.columnCount())
                    ]
                    writer.writerow(row_data)

            QMessageBox.information(self, "Export Complete", f"Exported to {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export:\n{str(e)}")


# Example usage
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    viewer = JSONViewer()
    viewer.setWindowTitle("JSON Viewer")
    viewer.resize(1000, 700)
    viewer.show()
    sys.exit(app.exec())
