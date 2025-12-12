"""
Data Viewer Factory
===================

Auto-detect file type and open appropriate viewer.
Supports:
- SQLite (.db, .sqlite, .sqlite3)
- JSON (.json)
- XML (.xml)
- CSV (.csv)
- YAML (.yaml, .yml)
- INI (.ini, .conf)

Plugin architecture for extensibility.

Usage:
    factory = DataViewerFactory()
    viewer = factory.create_viewer("data.json")
    if viewer:
        viewer.show()
"""

import os
import json
import csv
import configparser
from pathlib import Path
from typing import Optional, Dict, Callable, Any
from enum import Enum

from PyQt6.QtWidgets import QWidget, QMessageBox

from .database_viewer import DatabaseViewer
from .json_viewer import JSONViewer


class ViewerType(Enum):
    """Supported viewer types"""
    DATABASE = "database"
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    YAML = "yaml"
    INI = "ini"
    UNKNOWN = "unknown"


class CSVViewer(QWidget):
    """Simple CSV viewer"""

    def __init__(self, parent=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel
        from PyQt6.QtCore import Qt

        layout = QVBoxLayout(self)

        self.info_label = QLabel()
        layout.addWidget(self.info_label)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

    def open_file(self, file_path: str):
        """Open CSV file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Detect dialect
                sample = f.read(4096)
                f.seek(0)
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)

                reader = csv.reader(f, dialect)
                rows = list(reader)

            if not rows:
                self.info_label.setText("Empty CSV file")
                return

            # First row as headers
            headers = rows[0]
            data_rows = rows[1:]

            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)
            self.table.setRowCount(len(data_rows))

            for row_idx, row in enumerate(data_rows):
                for col_idx, value in enumerate(row):
                    from PyQt6.QtWidgets import QTableWidgetItem
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(value))

            self.info_label.setText(f"CSV: {len(data_rows)} rows, {len(headers)} columns")

        except Exception as e:
            QMessageBox.critical(self, "CSV Error", f"Failed to load CSV:\n{str(e)}")


class XMLViewer(QWidget):
    """Simple XML viewer"""

    def __init__(self, parent=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QVBoxLayout, QTextEdit, QLabel
        from PyQt6.QtGui import QFont

        layout = QVBoxLayout(self)

        self.info_label = QLabel()
        layout.addWidget(self.info_label)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        font = QFont("Courier New", 10)
        self.text_edit.setFont(font)
        layout.addWidget(self.text_edit)

    def open_file(self, file_path: str):
        """Open XML file"""
        try:
            import xml.dom.minidom

            with open(file_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()

            # Pretty print
            dom = xml.dom.minidom.parseString(xml_content)
            pretty_xml = dom.toprettyxml(indent="  ")

            self.text_edit.setText(pretty_xml)
            self.info_label.setText(f"XML: {os.path.basename(file_path)}")

        except Exception as e:
            QMessageBox.critical(self, "XML Error", f"Failed to load XML:\n{str(e)}")


class YAMLViewer(QWidget):
    """Simple YAML viewer"""

    def __init__(self, parent=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QVBoxLayout, QTextEdit, QLabel
        from PyQt6.QtGui import QFont

        layout = QVBoxLayout(self)

        self.info_label = QLabel()
        layout.addWidget(self.info_label)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        font = QFont("Courier New", 10)
        self.text_edit.setFont(font)
        layout.addWidget(self.text_edit)

    def open_file(self, file_path: str):
        """Open YAML file"""
        try:
            # Try to import yaml
            try:
                import yaml
                has_yaml = True
            except ImportError:
                has_yaml = False

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if has_yaml:
                # Parse and re-dump for formatting
                data = yaml.safe_load(content)
                formatted = yaml.dump(data, default_flow_style=False, sort_keys=False)
                self.text_edit.setText(formatted)
            else:
                # Just show raw content
                self.text_edit.setText(content)
                self.info_label.setText("YAML (install PyYAML for better formatting)")

            self.info_label.setText(f"YAML: {os.path.basename(file_path)}")

        except Exception as e:
            QMessageBox.critical(self, "YAML Error", f"Failed to load YAML:\n{str(e)}")


class INIViewer(QWidget):
    """Simple INI/config file viewer"""

    def __init__(self, parent=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel
        from PyQt6.QtCore import Qt

        layout = QVBoxLayout(self)

        self.info_label = QLabel()
        layout.addWidget(self.info_label)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Key", "Value"])
        self.tree.setAlternatingRowColors(True)
        layout.addWidget(self.tree)

    def open_file(self, file_path: str):
        """Open INI file"""
        try:
            config = configparser.ConfigParser()
            config.read(file_path, encoding='utf-8')

            self.tree.clear()

            for section in config.sections():
                from PyQt6.QtWidgets import QTreeWidgetItem
                section_item = QTreeWidgetItem([section, ""])
                section_item.setExpanded(True)

                for key, value in config.items(section):
                    key_item = QTreeWidgetItem([key, value])
                    section_item.addChild(key_item)

                self.tree.addTopLevelItem(section_item)

            self.info_label.setText(f"INI: {len(config.sections())} sections")

        except Exception as e:
            QMessageBox.critical(self, "INI Error", f"Failed to load INI:\n{str(e)}")


class DataViewerFactory:
    """Factory for creating appropriate data viewers"""

    def __init__(self):
        self._viewers: Dict[ViewerType, Callable[[], QWidget]] = {
            ViewerType.DATABASE: lambda: DatabaseViewer(),
            ViewerType.JSON: lambda: JSONViewer(),
            ViewerType.CSV: lambda: CSVViewer(),
            ViewerType.XML: lambda: XMLViewer(),
            ViewerType.YAML: lambda: YAMLViewer(),
            ViewerType.INI: lambda: INIViewer(),
        }

        self._extensions: Dict[str, ViewerType] = {
            # Database
            '.db': ViewerType.DATABASE,
            '.sqlite': ViewerType.DATABASE,
            '.sqlite3': ViewerType.DATABASE,
            '.db3': ViewerType.DATABASE,

            # JSON
            '.json': ViewerType.JSON,

            # XML
            '.xml': ViewerType.XML,

            # CSV
            '.csv': ViewerType.CSV,
            '.tsv': ViewerType.CSV,

            # YAML
            '.yaml': ViewerType.YAML,
            '.yml': ViewerType.YAML,

            # INI
            '.ini': ViewerType.INI,
            '.conf': ViewerType.INI,
            '.cfg': ViewerType.INI,
        }

    def detect_type(self, file_path: str) -> ViewerType:
        """Detect viewer type from file path"""
        ext = os.path.splitext(file_path)[1].lower()
        return self._extensions.get(ext, ViewerType.UNKNOWN)

    def create_viewer(self, file_path: str) -> Optional[QWidget]:
        """Create appropriate viewer for file"""
        if not os.path.exists(file_path):
            QMessageBox.critical(None, "File Not Found", f"File does not exist:\n{file_path}")
            return None

        viewer_type = self.detect_type(file_path)

        if viewer_type == ViewerType.UNKNOWN:
            QMessageBox.warning(
                None,
                "Unsupported Format",
                f"No viewer available for:\n{file_path}\n\nSupported formats:\n" +
                "\n".join(sorted(set(self._extensions.keys())))
            )
            return None

        # Create viewer
        viewer_factory = self._viewers.get(viewer_type)
        if not viewer_factory:
            return None

        viewer = viewer_factory()

        # Open file
        try:
            viewer.open_file(file_path)
            viewer.setWindowTitle(f"{viewer_type.value.title()} Viewer - {os.path.basename(file_path)}")
            return viewer
        except Exception as e:
            QMessageBox.critical(None, "Open Error", f"Failed to open file:\n{str(e)}")
            return None

    def register_viewer(self, viewer_type: ViewerType, factory: Callable[[], QWidget]):
        """Register a custom viewer"""
        self._viewers[viewer_type] = factory

    def register_extension(self, extension: str, viewer_type: ViewerType):
        """Register a file extension"""
        if not extension.startswith('.'):
            extension = '.' + extension
        self._extensions[extension.lower()] = viewer_type

    def get_supported_extensions(self) -> list[str]:
        """Get list of supported extensions"""
        return sorted(self._extensions.keys())

    def get_filter_string(self) -> str:
        """Get file filter string for dialogs"""
        filters = []

        # Group by viewer type
        type_extensions: Dict[ViewerType, list[str]] = {}
        for ext, vtype in self._extensions.items():
            if vtype not in type_extensions:
                type_extensions[vtype] = []
            type_extensions[vtype].append(f"*{ext}")

        # Create filter strings
        for vtype, exts in type_extensions.items():
            filter_str = f"{vtype.value.title()} Files ({' '.join(exts)})"
            filters.append(filter_str)

        # Add all supported
        all_exts = [f"*{ext}" for ext in self._extensions.keys()]
        filters.insert(0, f"All Supported ({' '.join(all_exts)})")

        # Add all files
        filters.append("All Files (*.*)")

        return ";;".join(filters)


# Standalone viewer application
class DataViewerApp(QWidget):
    """Standalone data viewer application"""

    def __init__(self, parent=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QLabel, QFileDialog

        self.factory = DataViewerFactory()
        self.current_viewer: Optional[QWidget] = None

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Data Viewer")
        title.setStyleSheet("font-size: 18pt; font-weight: bold;")
        layout.addWidget(title)

        # Open button
        open_btn = QPushButton("Open File...")
        open_btn.clicked.connect(self.open_file)
        layout.addWidget(open_btn)

        # Info
        info = QLabel(
            "Supported formats:\n" +
            "• SQLite databases (.db, .sqlite, .sqlite3)\n" +
            "• JSON files (.json)\n" +
            "• CSV files (.csv)\n" +
            "• XML files (.xml)\n" +
            "• YAML files (.yaml, .yml)\n" +
            "• INI/Config files (.ini, .conf)"
        )
        layout.addWidget(info)

        layout.addStretch()

        self.setWindowTitle("Data Viewer")
        self.resize(600, 400)

    def open_file(self):
        """Open file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Data File",
            "",
            self.factory.get_filter_string()
        )

        if file_path:
            self.open_data_file(file_path)

    def open_data_file(self, file_path: str):
        """Open data file in appropriate viewer"""
        viewer = self.factory.create_viewer(file_path)
        if viewer:
            # Close previous viewer if exists
            if self.current_viewer:
                self.current_viewer.close()

            self.current_viewer = viewer
            viewer.resize(1200, 800)
            viewer.show()


# Example usage
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Create factory
    factory = DataViewerFactory()

    # If file path provided as argument, open it
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        viewer = factory.create_viewer(file_path)
        if viewer:
            viewer.resize(1200, 800)
            viewer.show()
    else:
        # Show app selector
        app_viewer = DataViewerApp()
        app_viewer.show()

    sys.exit(app.exec())
