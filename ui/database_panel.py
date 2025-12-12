"""
Database Explorer Panel
=======================

PyQt6 panel for database exploration integrated into Smart Search Pro.
Features:
- Tree view for database structure
- Multiple database tabs
- Query editor with syntax highlighting
- Results table with sorting/filtering
- Schema diagram view
- Query history
- Bookmarked queries
- Export capabilities

Usage:
    panel = DatabasePanel()
    panel.open_database("path/to/db.sqlite")
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit, QPushButton,
    QLabel, QLineEdit, QComboBox, QMessageBox, QMenu, QToolBar, QFileDialog,
    QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QFont, QColor, QAction, QIcon

# Import viewers
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from viewers.database_viewer import SQLiteConnection, QueryHistoryManager


class QueryEditorWidget(QTextEdit):
    """SQL Query editor with basic syntax highlighting"""

    execute_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Setup font
        font = QFont("Courier New", 10)
        self.setFont(font)

        # Setup placeholder
        self.setPlaceholderText("-- Enter SQL query here\n-- Press Ctrl+Enter to execute")

    def keyPressEvent(self, event):
        """Handle key events"""
        # Ctrl+Enter to execute
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.execute_requested.emit()
            return

        super().keyPressEvent(event)


class DatabasePanel(QWidget):
    """Database explorer panel for Smart Search Pro"""

    database_opened = pyqtSignal(str)
    table_selected = pyqtSignal(str)
    query_executed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.databases: Dict[str, SQLiteConnection] = {}
        self.current_db_path: Optional[str] = None
        self.query_history = QueryHistoryManager()
        self.bookmarked_queries: List[str] = self._load_bookmarks()

        self._init_ui()
        self._setup_connections()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Database tabs
        self.db_tabs = QTabWidget()
        self.db_tabs.setTabsClosable(True)
        self.db_tabs.tabCloseRequested.connect(self._close_database_tab)
        self.db_tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.db_tabs)

        # Initial empty state
        self._show_empty_state()

    def _create_toolbar(self) -> QToolBar:
        """Create toolbar"""
        toolbar = QToolBar()
        toolbar.setMovable(False)

        # Open database action
        open_action = QAction("Open Database", self)
        open_action.setToolTip("Open SQLite database file")
        open_action.triggered.connect(self.open_database_dialog)
        toolbar.addAction(open_action)

        toolbar.addSeparator()

        # Refresh action
        self.refresh_action = QAction("Refresh", self)
        self.refresh_action.setToolTip("Refresh current database")
        self.refresh_action.triggered.connect(self.refresh_current)
        self.refresh_action.setEnabled(False)
        toolbar.addAction(self.refresh_action)

        toolbar.addSeparator()

        # Execute query action
        self.execute_action = QAction("Execute Query", self)
        self.execute_action.setToolTip("Execute SQL query (Ctrl+Enter)")
        self.execute_action.triggered.connect(self._execute_current_query)
        self.execute_action.setEnabled(False)
        toolbar.addAction(self.execute_action)

        toolbar.addSeparator()

        # Export action
        self.export_action = QAction("Export Results", self)
        self.export_action.setToolTip("Export query results to CSV")
        self.export_action.triggered.connect(self._export_results)
        self.export_action.setEnabled(False)
        toolbar.addAction(self.export_action)

        return toolbar

    def _show_empty_state(self):
        """Show empty state when no database is open"""
        empty_widget = QWidget()
        layout = QVBoxLayout(empty_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("No database open\n\nClick 'Open Database' to get started")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: gray; font-size: 14pt;")
        layout.addWidget(label)

        self.db_tabs.addTab(empty_widget, "Welcome")

    def _setup_connections(self):
        """Setup signal connections"""
        pass

    def open_database_dialog(self):
        """Open file dialog to select database"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open SQLite Database",
            "",
            "SQLite Database (*.db *.sqlite *.sqlite3 *.db3);;All Files (*.*)"
        )

        if file_path:
            self.open_database(file_path)

    def open_database(self, db_path: str):
        """Open a database file"""
        try:
            # Check if already open
            if db_path in self.databases:
                # Switch to existing tab
                for i in range(self.db_tabs.count()):
                    widget = self.db_tabs.widget(i)
                    if hasattr(widget, 'db_path') and widget.db_path == db_path:
                        self.db_tabs.setCurrentIndex(i)
                        return

            # Create connection
            connection = SQLiteConnection(db_path)
            connection.connect()

            # Create tab widget
            tab_widget = self._create_database_tab(db_path, connection)

            # Add to tabs
            tab_name = os.path.basename(db_path)
            self.db_tabs.addTab(tab_widget, tab_name)

            # Remove empty state if present
            if self.db_tabs.count() > 1 and self.db_tabs.tabText(0) == "Welcome":
                self.db_tabs.removeTab(0)

            # Switch to new tab
            self.db_tabs.setCurrentWidget(tab_widget)

            # Store connection
            self.databases[db_path] = connection
            self.current_db_path = db_path

            # Update UI state
            self.refresh_action.setEnabled(True)
            self.execute_action.setEnabled(True)
            self.export_action.setEnabled(True)

            # Emit signal
            self.database_opened.emit(db_path)

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to open database:\n{str(e)}")

    def _create_database_tab(self, db_path: str, connection: SQLiteConnection) -> QWidget:
        """Create tab widget for a database"""
        tab = QWidget()
        tab.db_path = db_path
        tab.connection = connection

        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Tables tree
        left_panel = self._create_tables_panel(connection)
        tab.tables_tree = left_panel
        splitter.addWidget(left_panel)

        # Right panel: Content tabs
        right_panel = self._create_content_tabs(connection)
        tab.content_tabs = right_panel
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter)

        return tab

    def _create_tables_panel(self, connection: SQLiteConnection) -> QWidget:
        """Create tables tree panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # Search box
        search_box = QLineEdit()
        search_box.setPlaceholderText("Search tables...")
        layout.addWidget(search_box)

        # Tables tree
        tree = QTreeWidget()
        tree.setHeaderLabel("Tables")
        tree.itemClicked.connect(self._on_table_clicked)
        tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tree.customContextMenuRequested.connect(self._show_table_context_menu)
        layout.addWidget(tree)

        # Load tables
        self._load_tables_into_tree(tree, connection)

        # Connect search
        search_box.textChanged.connect(lambda text: self._filter_tree(tree, text))

        return tree

    def _load_tables_into_tree(self, tree: QTreeWidget, connection: SQLiteConnection):
        """Load tables into tree widget"""
        tree.clear()

        try:
            tables = connection.get_tables()

            for table_name in tables:
                try:
                    row_count = connection.get_table_row_count(table_name)
                    item = QTreeWidgetItem([f"{table_name} ({row_count} rows)"])
                    item.setData(0, Qt.ItemDataRole.UserRole, table_name)
                    tree.addTopLevelItem(item)
                except:
                    # If row count fails, just show table name
                    item = QTreeWidgetItem([table_name])
                    item.setData(0, Qt.ItemDataRole.UserRole, table_name)
                    tree.addTopLevelItem(item)

        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load tables:\n{str(e)}")

    def _filter_tree(self, tree: QTreeWidget, text: str):
        """Filter tree items"""
        for i in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(i)
            table_name = item.data(0, Qt.ItemDataRole.UserRole)
            item.setHidden(text.lower() not in table_name.lower() if table_name else True)

    def _create_content_tabs(self, connection: SQLiteConnection) -> QTabWidget:
        """Create content tabs"""
        tabs = QTabWidget()

        # Data tab
        data_tab = self._create_data_tab(connection)
        tabs.addTab(data_tab, "Data")

        # Schema tab
        schema_tab = self._create_schema_tab(connection)
        tabs.addTab(schema_tab, "Schema")

        # Query tab
        query_tab = self._create_query_tab(connection)
        tabs.addTab(query_tab, "Query")

        return tabs

    def _create_data_tab(self, connection: SQLiteConnection) -> QWidget:
        """Create data viewing tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Table
        table = QTableWidget()
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table)

        tab.data_table = table

        return tab

    def _create_schema_tab(self, connection: SQLiteConnection) -> QWidget:
        """Create schema viewing tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Schema table
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(['Column', 'Type', 'Not Null', 'Default', 'PK', 'Auto Inc'])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(table)

        tab.schema_table = table

        return tab

    def _create_query_tab(self, connection: SQLiteConnection) -> QWidget:
        """Create query editing tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Query controls
        controls = QHBoxLayout()

        execute_btn = QPushButton("Execute (Ctrl+Enter)")
        execute_btn.clicked.connect(self._execute_current_query)
        controls.addWidget(execute_btn)

        clear_btn = QPushButton("Clear")
        controls.addWidget(clear_btn)

        # History combo
        history_combo = QComboBox()
        history_combo.setPlaceholderText("Recent queries...")
        history_combo.setMinimumWidth(300)
        controls.addWidget(history_combo)

        # Bookmark button
        bookmark_btn = QPushButton("Bookmark")
        controls.addWidget(bookmark_btn)

        controls.addStretch()

        layout.addLayout(controls)

        # Query editor
        editor = QueryEditorWidget()
        editor.execute_requested.connect(self._execute_current_query)
        editor.setMaximumHeight(150)
        layout.addWidget(editor)

        # Results table
        results = QTableWidget()
        results.setAlternatingRowColors(True)
        results.setSortingEnabled(True)
        layout.addWidget(results)

        # Connect clear button
        clear_btn.clicked.connect(editor.clear)

        # Store references
        tab.query_editor = editor
        tab.query_results = results
        tab.history_combo = history_combo
        tab.bookmark_btn = bookmark_btn

        # Load history
        self._update_query_history(tab)

        # Connect history selection
        history_combo.currentTextChanged.connect(lambda text: editor.setText(text) if text else None)

        # Connect bookmark button
        bookmark_btn.clicked.connect(lambda: self._bookmark_query(editor.toPlainText()))

        return tab

    def _on_table_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle table selection"""
        table_name = item.data(0, Qt.ItemDataRole.UserRole)
        if not table_name:
            return

        # Get current tab
        current_tab = self.db_tabs.currentWidget()
        if not current_tab or not hasattr(current_tab, 'connection'):
            return

        connection = current_tab.connection

        # Load table data
        self._load_table_data(current_tab, connection, table_name)

        # Load schema
        self._load_table_schema(current_tab, connection, table_name)

        # Emit signal
        self.table_selected.emit(table_name)

    def _load_table_data(self, tab: QWidget, connection: SQLiteConnection, table_name: str):
        """Load table data"""
        try:
            # Get data tab
            content_tabs = tab.content_tabs
            data_tab = content_tabs.widget(0)
            table = data_tab.data_table

            # Query data (limit to 1000 rows for performance)
            query = f"SELECT * FROM {table_name} LIMIT 1000"
            rows = connection.execute_query(query)

            # Clear and populate
            table.clear()

            if rows:
                columns = list(rows[0].keys())
                table.setColumnCount(len(columns))
                table.setHorizontalHeaderLabels(columns)
                table.setRowCount(len(rows))

                for row_idx, row in enumerate(rows):
                    for col_idx, col_name in enumerate(columns):
                        value = row[col_name]
                        item = QTableWidgetItem(str(value) if value is not None else "NULL")
                        if value is None:
                            item.setForeground(QColor(128, 128, 128))
                        table.setItem(row_idx, col_idx, item)

        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load table data:\n{str(e)}")

    def _load_table_schema(self, tab: QWidget, connection: SQLiteConnection, table_name: str):
        """Load table schema"""
        try:
            # Get schema tab
            content_tabs = tab.content_tabs
            schema_tab = content_tabs.widget(1)
            table = schema_tab.schema_table

            # Get schema
            schema = connection.get_table_schema(table_name)

            table.setRowCount(len(schema))

            for row_idx, col_info in enumerate(schema):
                table.setItem(row_idx, 0, QTableWidgetItem(col_info['name']))
                table.setItem(row_idx, 1, QTableWidgetItem(col_info['type']))
                table.setItem(row_idx, 2, QTableWidgetItem('Yes' if col_info['notnull'] else 'No'))
                table.setItem(row_idx, 3, QTableWidgetItem(str(col_info['dflt_value']) if col_info['dflt_value'] else ''))
                table.setItem(row_idx, 4, QTableWidgetItem('Yes' if col_info['pk'] else 'No'))
                is_autoinc = col_info['pk'] and col_info['type'].upper() == 'INTEGER'
                table.setItem(row_idx, 5, QTableWidgetItem('Yes' if is_autoinc else 'No'))

        except Exception as e:
            QMessageBox.warning(self, "Schema Error", f"Failed to load schema:\n{str(e)}")

    def _execute_current_query(self):
        """Execute current query"""
        current_tab = self.db_tabs.currentWidget()
        if not current_tab or not hasattr(current_tab, 'connection'):
            return

        # Get query tab
        content_tabs = current_tab.content_tabs
        query_tab = content_tabs.widget(2)

        query = query_tab.query_editor.toPlainText().strip()
        if not query:
            return

        try:
            connection = current_tab.connection

            # Execute query
            rows = connection.execute_query(query)

            # Add to history
            self.query_history.add_query(query)
            self._update_query_history(current_tab)

            # Display results
            results_table = query_tab.query_results
            results_table.clear()

            if rows:
                columns = list(rows[0].keys())
                results_table.setColumnCount(len(columns))
                results_table.setHorizontalHeaderLabels(columns)
                results_table.setRowCount(len(rows))

                for row_idx, row in enumerate(rows):
                    for col_idx, col_name in enumerate(columns):
                        value = row[col_name]
                        item = QTableWidgetItem(str(value) if value is not None else "NULL")
                        if value is None:
                            item.setForeground(QColor(128, 128, 128))
                        results_table.setItem(row_idx, col_idx, item)

            # Emit signal
            self.query_executed.emit(query)

            QMessageBox.information(self, "Query Success", f"Returned {len(rows)} rows")

        except Exception as e:
            QMessageBox.critical(self, "Query Error", f"Failed to execute query:\n{str(e)}")

    def _update_query_history(self, tab: QWidget):
        """Update query history combo"""
        if not hasattr(tab, 'content_tabs'):
            return

        content_tabs = tab.content_tabs
        query_tab = content_tabs.widget(2)

        query_tab.history_combo.clear()
        query_tab.history_combo.addItems(self.query_history.get_history())

    def _bookmark_query(self, query: str):
        """Bookmark a query"""
        query = query.strip()
        if not query:
            return

        if query not in self.bookmarked_queries:
            self.bookmarked_queries.append(query)
            self._save_bookmarks()
            QMessageBox.information(self, "Bookmarked", "Query bookmarked successfully")

    def _load_bookmarks(self) -> List[str]:
        """Load bookmarked queries"""
        settings = QSettings('SmartSearch', 'DatabasePanel')
        bookmarks_json = settings.value('bookmarked_queries', '[]')
        try:
            return json.loads(bookmarks_json)
        except:
            return []

    def _save_bookmarks(self):
        """Save bookmarked queries"""
        settings = QSettings('SmartSearch', 'DatabasePanel')
        bookmarks_json = json.dumps(self.bookmarked_queries)
        settings.setValue('bookmarked_queries', bookmarks_json)

    def _export_results(self):
        """Export query results to CSV"""
        current_tab = self.db_tabs.currentWidget()
        if not current_tab or not hasattr(current_tab, 'content_tabs'):
            return

        content_tabs = current_tab.content_tabs
        query_tab = content_tabs.widget(2)
        results_table = query_tab.query_results

        if results_table.rowCount() == 0:
            QMessageBox.warning(self, "No Results", "Execute a query first")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            "query_results.csv",
            "CSV Files (*.csv);;All Files (*.*)"
        )

        if not file_path:
            return

        try:
            import csv

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write headers
                headers = [
                    results_table.horizontalHeaderItem(i).text()
                    for i in range(results_table.columnCount())
                ]
                writer.writerow(headers)

                # Write data
                for row in range(results_table.rowCount()):
                    row_data = [
                        results_table.item(row, col).text() if results_table.item(row, col) else ""
                        for col in range(results_table.columnCount())
                    ]
                    writer.writerow(row_data)

            QMessageBox.information(self, "Export Complete", f"Exported to {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export:\n{str(e)}")

    def _show_table_context_menu(self, position):
        """Show context menu for table"""
        # Get the tree from the current tab
        current_tab = self.db_tabs.currentWidget()
        if not current_tab or not hasattr(current_tab, 'tables_tree'):
            return

        tree = current_tab.tables_tree
        item = tree.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        view_action = QAction("View Data", self)
        view_action.triggered.connect(lambda: self._on_table_clicked(item, 0))
        menu.addAction(view_action)

        menu.exec(tree.viewport().mapToGlobal(position))

    def _close_database_tab(self, index: int):
        """Close database tab"""
        tab = self.db_tabs.widget(index)
        if hasattr(tab, 'db_path'):
            db_path = tab.db_path

            # Close connection
            if db_path in self.databases:
                self.databases[db_path].close()
                del self.databases[db_path]

        # Remove tab
        self.db_tabs.removeTab(index)

        # Show empty state if no tabs left
        if self.db_tabs.count() == 0:
            self._show_empty_state()
            self.refresh_action.setEnabled(False)
            self.execute_action.setEnabled(False)
            self.export_action.setEnabled(False)

    def _on_tab_changed(self, index: int):
        """Handle tab change"""
        if index >= 0:
            tab = self.db_tabs.widget(index)
            if hasattr(tab, 'db_path'):
                self.current_db_path = tab.db_path

    def refresh_current(self):
        """Refresh current database"""
        current_tab = self.db_tabs.currentWidget()
        if not current_tab or not hasattr(current_tab, 'connection'):
            return

        # Reload tables
        self._load_tables_into_tree(current_tab.tables_tree, current_tab.connection)

    def closeEvent(self, event):
        """Handle close event"""
        # Close all connections
        for connection in self.databases.values():
            connection.close()

        super().closeEvent(event)


# Example usage
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    panel = DatabasePanel()
    panel.setWindowTitle("Database Explorer Panel")
    panel.resize(1200, 800)
    panel.show()
    sys.exit(app.exec())
