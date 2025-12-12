"""
SQLite Database Viewer
======================

Comprehensive SQLite database viewer with:
- Table browsing with pagination
- Schema inspection
- Custom SQL query execution
- Inline cell editing
- Export capabilities
- Search across tables
- Foreign key visualization
- Recent databases history

Usage:
    viewer = DatabaseViewer()
    viewer.open_database("path/to/database.db")
    viewer.show()
"""

import os
import csv
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QLabel, QPushButton, QLineEdit, QTextEdit,
    QComboBox, QSpinBox, QMessageBox, QFileDialog, QTabWidget, QProgressDialog,
    QHeaderView, QMenu, QDialog, QDialogButtonBox, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QColor, QIcon, QAction
from PyQt6.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel, QSqlQueryModel


class SQLiteConnection:
    """Thread-safe SQLite connection manager"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Open database connection"""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
        return self.connection

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute SELECT query and return results"""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            raise Exception(f"Query error: {str(e)}")
        finally:
            cursor.close()

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE and return affected rows"""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            conn.rollback()
            raise Exception(f"Update error: {str(e)}")
        finally:
            cursor.close()

    def get_tables(self) -> List[str]:
        """Get list of all tables"""
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        rows = self.execute_query(query)
        return [row['name'] for row in rows]

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information"""
        query = f"PRAGMA table_info({table_name})"
        rows = self.execute_query(query)
        return [dict(row) for row in rows]

    def get_table_row_count(self, table_name: str) -> int:
        """Get row count for a table"""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        rows = self.execute_query(query)
        return rows[0]['count'] if rows else 0

    def get_table_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get indexes for a table"""
        query = f"PRAGMA index_list({table_name})"
        rows = self.execute_query(query)
        return [dict(row) for row in rows]

    def get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """Get foreign key relationships"""
        query = f"PRAGMA foreign_key_list({table_name})"
        rows = self.execute_query(query)
        return [dict(row) for row in rows]


class QueryHistoryManager:
    """Manages SQL query history"""

    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.settings = QSettings('SmartSearch', 'DatabaseViewer')
        self.history: List[str] = self._load_history()

    def add_query(self, query: str):
        """Add query to history"""
        query = query.strip()
        if not query:
            return

        # Remove if already exists
        if query in self.history:
            self.history.remove(query)

        # Add to beginning
        self.history.insert(0, query)

        # Trim to max
        self.history = self.history[:self.max_history]

        self._save_history()

    def get_history(self) -> List[str]:
        """Get query history"""
        return self.history.copy()

    def clear_history(self):
        """Clear all history"""
        self.history.clear()
        self._save_history()

    def _load_history(self) -> List[str]:
        """Load history from settings"""
        history_json = self.settings.value('query_history', '[]')
        try:
            return json.loads(history_json)
        except:
            return []

    def _save_history(self):
        """Save history to settings"""
        history_json = json.dumps(self.history)
        self.settings.setValue('query_history', history_json)


class RecentDatabasesManager:
    """Manages recent databases list"""

    def __init__(self, max_recent: int = 10):
        self.max_recent = max_recent
        self.settings = QSettings('SmartSearch', 'DatabaseViewer')
        self.recent: List[str] = self._load_recent()

    def add_database(self, db_path: str):
        """Add database to recent list"""
        db_path = os.path.abspath(db_path)

        # Remove if already exists
        if db_path in self.recent:
            self.recent.remove(db_path)

        # Add to beginning
        self.recent.insert(0, db_path)

        # Trim to max
        self.recent = self.recent[:self.max_recent]

        self._save_recent()

    def get_recent(self) -> List[str]:
        """Get recent databases (filter out non-existent)"""
        return [db for db in self.recent if os.path.exists(db)]

    def clear_recent(self):
        """Clear recent list"""
        self.recent.clear()
        self._save_recent()

    def _load_recent(self) -> List[str]:
        """Load from settings"""
        recent_json = self.settings.value('recent_databases', '[]')
        try:
            return json.loads(recent_json)
        except:
            return []

    def _save_recent(self):
        """Save to settings"""
        recent_json = json.dumps(self.recent)
        self.settings.setValue('recent_databases', recent_json)


class TableDataModel(QSqlQueryModel):
    """Custom model for table data with editing support"""

    def __init__(self, db_connection: SQLiteConnection, parent=None):
        super().__init__(parent)
        self.db_connection = db_connection
        self.table_name = ""
        self.editable_columns = set()

    def load_table(self, table_name: str, offset: int = 0, limit: int = 1000):
        """Load table data with pagination"""
        self.table_name = table_name
        query = f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}"
        self.setQuery(query)

        # Determine editable columns (exclude primary keys)
        schema = self.db_connection.get_table_schema(table_name)
        self.editable_columns = {
            col['name'] for col in schema if col['pk'] == 0
        }

    def flags(self, index):
        """Make cells editable"""
        flags = super().flags(index)
        column_name = self.headerData(index.column(), Qt.Orientation.Horizontal)
        if column_name in self.editable_columns:
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """Handle cell editing"""
        if role != Qt.ItemDataRole.EditRole:
            return False

        # Get column and row info
        column_name = self.headerData(index.column(), Qt.Orientation.Horizontal)
        row_data = {}
        for col in range(self.columnCount()):
            col_name = self.headerData(col, Qt.Orientation.Horizontal)
            row_data[col_name] = self.data(self.index(index.row(), col))

        # Build UPDATE query
        try:
            # Find primary key column
            schema = self.db_connection.get_table_schema(self.table_name)
            pk_cols = [col['name'] for col in schema if col['pk'] > 0]

            if not pk_cols:
                QMessageBox.warning(None, "Edit Error", "Cannot edit table without primary key")
                return False

            # Build WHERE clause
            where_parts = []
            where_values = []
            for pk_col in pk_cols:
                where_parts.append(f"{pk_col} = ?")
                where_values.append(row_data[pk_col])

            where_clause = " AND ".join(where_parts)

            # Execute UPDATE
            query = f"UPDATE {self.table_name} SET {column_name} = ? WHERE {where_clause}"
            params = (value, *where_values)

            self.db_connection.execute_update(query, params)

            # Refresh model
            self.setQuery(self.query().lastQuery())

            return True

        except Exception as e:
            QMessageBox.critical(None, "Update Error", str(e))
            return False


class DatabaseViewer(QWidget):
    """Main database viewer widget"""

    database_opened = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.db_connection: Optional[SQLiteConnection] = None
        self.current_db_path: Optional[str] = None
        self.query_history = QueryHistoryManager()
        self.recent_databases = RecentDatabasesManager()

        self._init_ui()
        self._setup_connections()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Tables tree
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # Right panel: Tabs
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter)

        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("No database loaded")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)

    def _create_toolbar(self) -> QWidget:
        """Create toolbar"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(5, 5, 5, 5)

        # Open database button
        self.open_btn = QPushButton("Open Database")
        self.open_btn.clicked.connect(self.open_database_dialog)
        layout.addWidget(self.open_btn)

        # Recent databases button
        self.recent_btn = QPushButton("Recent")
        recent_menu = QMenu(self.recent_btn)
        self.recent_btn.setMenu(recent_menu)
        layout.addWidget(self.recent_btn)

        # Database info
        self.db_info_label = QLabel("")
        layout.addWidget(self.db_info_label)

        layout.addStretch()

        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_current)
        self.refresh_btn.setEnabled(False)
        layout.addWidget(self.refresh_btn)

        return toolbar

    def _create_left_panel(self) -> QWidget:
        """Create left panel with tables tree"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Search box
        self.table_search = QLineEdit()
        self.table_search.setPlaceholderText("Search tables...")
        self.table_search.textChanged.connect(self._filter_tables)
        layout.addWidget(self.table_search)

        # Tables tree
        self.tables_tree = QTreeWidget()
        self.tables_tree.setHeaderLabel("Tables")
        self.tables_tree.itemClicked.connect(self._on_table_selected)
        self.tables_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tables_tree.customContextMenuRequested.connect(self._show_table_context_menu)
        layout.addWidget(self.tables_tree)

        return panel

    def _create_right_panel(self) -> QWidget:
        """Create right panel with tabs"""
        self.tab_widget = QTabWidget()

        # Data tab
        self.data_tab = self._create_data_tab()
        self.tab_widget.addTab(self.data_tab, "Data")

        # Schema tab
        self.schema_tab = self._create_schema_tab()
        self.tab_widget.addTab(self.schema_tab, "Schema")

        # Query tab
        self.query_tab = self._create_query_tab()
        self.tab_widget.addTab(self.query_tab, "Query")

        # Search tab
        self.search_tab = self._create_search_tab()
        self.tab_widget.addTab(self.search_tab, "Search")

        return self.tab_widget

    def _create_data_tab(self) -> QWidget:
        """Create data browsing tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Pagination controls
        pagination = QHBoxLayout()

        self.page_label = QLabel("Page:")
        pagination.addWidget(self.page_label)

        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.valueChanged.connect(self._load_current_page)
        pagination.addWidget(self.page_spin)

        self.rows_per_page_combo = QComboBox()
        self.rows_per_page_combo.addItems(['100', '500', '1000', '5000'])
        self.rows_per_page_combo.setCurrentText('1000')
        self.rows_per_page_combo.currentTextChanged.connect(self._on_page_size_changed)
        pagination.addWidget(QLabel("Rows per page:"))
        pagination.addWidget(self.rows_per_page_combo)

        self.row_count_label = QLabel("Rows: 0")
        pagination.addWidget(self.row_count_label)

        pagination.addStretch()

        # Export button
        self.export_btn = QPushButton("Export Table")
        self.export_btn.clicked.connect(self._export_current_table)
        pagination.addWidget(self.export_btn)

        layout.addLayout(pagination)

        # Data table
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSortingEnabled(True)
        self.data_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        layout.addWidget(self.data_table)

        return tab

    def _create_schema_tab(self) -> QWidget:
        """Create schema inspection tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Schema table
        self.schema_table = QTableWidget()
        self.schema_table.setColumnCount(6)
        self.schema_table.setHorizontalHeaderLabels([
            'Column', 'Type', 'Not Null', 'Default', 'Primary Key', 'Auto Inc'
        ])
        self.schema_table.horizontalHeader().setStretchLastSection(False)
        self.schema_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.schema_table)

        # Indexes section
        indexes_group = QGroupBox("Indexes")
        indexes_layout = QVBoxLayout(indexes_group)
        self.indexes_list = QTextEdit()
        self.indexes_list.setReadOnly(True)
        self.indexes_list.setMaximumHeight(100)
        indexes_layout.addWidget(self.indexes_list)
        layout.addWidget(indexes_group)

        # Foreign keys section
        fk_group = QGroupBox("Foreign Keys")
        fk_layout = QVBoxLayout(fk_group)
        self.fk_list = QTextEdit()
        self.fk_list.setReadOnly(True)
        self.fk_list.setMaximumHeight(100)
        fk_layout.addWidget(self.fk_list)
        layout.addWidget(fk_group)

        return tab

    def _create_query_tab(self) -> QWidget:
        """Create SQL query tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Query controls
        controls = QHBoxLayout()

        self.execute_btn = QPushButton("Execute (Ctrl+Enter)")
        self.execute_btn.clicked.connect(self._execute_query)
        controls.addWidget(self.execute_btn)

        self.clear_query_btn = QPushButton("Clear")
        self.clear_query_btn.clicked.connect(lambda: self.query_editor.clear())
        controls.addWidget(self.clear_query_btn)

        self.history_combo = QComboBox()
        self.history_combo.setPlaceholderText("Query history...")
        self.history_combo.setMinimumWidth(300)
        self.history_combo.currentTextChanged.connect(self._load_query_from_history)
        controls.addWidget(self.history_combo)

        controls.addStretch()

        self.export_query_btn = QPushButton("Export Results")
        self.export_query_btn.clicked.connect(self._export_query_results)
        controls.addWidget(self.export_query_btn)

        layout.addLayout(controls)

        # Query editor
        self.query_editor = QTextEdit()
        self.query_editor.setPlaceholderText("Enter SQL query here...")
        font = QFont("Courier New", 10)
        self.query_editor.setFont(font)
        self.query_editor.setMaximumHeight(150)
        layout.addWidget(self.query_editor)

        # Results table
        self.query_results = QTableWidget()
        self.query_results.setAlternatingRowColors(True)
        self.query_results.setSortingEnabled(True)
        layout.addWidget(self.query_results)

        return tab

    def _create_search_tab(self) -> QWidget:
        """Create search across tables tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Search controls
        search_controls = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search term...")
        self.search_input.returnPressed.connect(self._search_all_tables)
        search_controls.addWidget(self.search_input)

        self.search_btn = QPushButton("Search All Tables")
        self.search_btn.clicked.connect(self._search_all_tables)
        search_controls.addWidget(self.search_btn)

        self.case_sensitive_cb = QCheckBox("Case sensitive")
        search_controls.addWidget(self.case_sensitive_cb)

        layout.addLayout(search_controls)

        # Search results
        self.search_results = QTableWidget()
        self.search_results.setColumnCount(3)
        self.search_results.setHorizontalHeaderLabels(['Table', 'Column', 'Value'])
        self.search_results.setAlternatingRowColors(True)
        layout.addWidget(self.search_results)

        return tab

    def _setup_connections(self):
        """Setup signal connections"""
        # Update recent menu when clicked
        self.recent_btn.menu().aboutToShow.connect(self._update_recent_menu)

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
            # Close existing connection
            if self.db_connection:
                self.db_connection.close()

            # Open new connection
            self.db_connection = SQLiteConnection(db_path)
            self.current_db_path = db_path

            # Update UI
            self.refresh_btn.setEnabled(True)
            self.db_info_label.setText(f"Database: {os.path.basename(db_path)}")
            self.status_label.setText(f"Loaded: {db_path}")

            # Add to recent
            self.recent_databases.add_database(db_path)

            # Load tables
            self._load_tables()

            # Update history combo
            self._update_history_combo()

            # Emit signal
            self.database_opened.emit(db_path)

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to open database:\n{str(e)}")

    def _load_tables(self):
        """Load tables into tree"""
        if not self.db_connection:
            return

        self.tables_tree.clear()

        try:
            tables = self.db_connection.get_tables()

            for table in tables:
                row_count = self.db_connection.get_table_row_count(table)
                item = QTreeWidgetItem([f"{table} ({row_count} rows)"])
                item.setData(0, Qt.ItemDataRole.UserRole, table)
                self.tables_tree.addTopLevelItem(item)

        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load tables:\n{str(e)}")

    def _filter_tables(self, text: str):
        """Filter tables by search text"""
        for i in range(self.tables_tree.topLevelItemCount()):
            item = self.tables_tree.topLevelItem(i)
            table_name = item.data(0, Qt.ItemDataRole.UserRole)
            item.setHidden(text.lower() not in table_name.lower())

    def _on_table_selected(self, item: QTreeWidgetItem, column: int):
        """Handle table selection"""
        table_name = item.data(0, Qt.ItemDataRole.UserRole)
        if table_name:
            self._load_table_data(table_name)
            self._load_table_schema(table_name)

    def _load_table_data(self, table_name: str):
        """Load table data"""
        if not self.db_connection:
            return

        try:
            # Get page size
            page_size = int(self.rows_per_page_combo.currentText())
            page = self.page_spin.value()
            offset = (page - 1) * page_size

            # Query data
            query = f"SELECT * FROM {table_name} LIMIT {page_size} OFFSET {offset}"
            rows = self.db_connection.execute_query(query)

            # Get row count
            row_count = self.db_connection.get_table_row_count(table_name)
            self.row_count_label.setText(f"Rows: {row_count}")

            # Calculate pages
            total_pages = (row_count + page_size - 1) // page_size
            self.page_spin.setMaximum(max(1, total_pages))

            # Populate table
            self.data_table.clear()

            if rows:
                columns = list(rows[0].keys())
                self.data_table.setColumnCount(len(columns))
                self.data_table.setHorizontalHeaderLabels(columns)
                self.data_table.setRowCount(len(rows))

                for row_idx, row in enumerate(rows):
                    for col_idx, col_name in enumerate(columns):
                        value = row[col_name]
                        item = QTableWidgetItem(str(value) if value is not None else "NULL")
                        if value is None:
                            item.setForeground(QColor(128, 128, 128))
                        self.data_table.setItem(row_idx, col_idx, item)

        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load table data:\n{str(e)}")

    def _load_table_schema(self, table_name: str):
        """Load table schema"""
        if not self.db_connection:
            return

        try:
            # Load schema
            schema = self.db_connection.get_table_schema(table_name)

            self.schema_table.setRowCount(len(schema))

            for row_idx, col_info in enumerate(schema):
                self.schema_table.setItem(row_idx, 0, QTableWidgetItem(col_info['name']))
                self.schema_table.setItem(row_idx, 1, QTableWidgetItem(col_info['type']))
                self.schema_table.setItem(row_idx, 2, QTableWidgetItem('Yes' if col_info['notnull'] else 'No'))
                self.schema_table.setItem(row_idx, 3, QTableWidgetItem(str(col_info['dflt_value']) if col_info['dflt_value'] else ''))
                self.schema_table.setItem(row_idx, 4, QTableWidgetItem('Yes' if col_info['pk'] else 'No'))
                # Auto increment is indicated by INTEGER PRIMARY KEY in SQLite
                is_autoinc = col_info['pk'] and col_info['type'].upper() == 'INTEGER'
                self.schema_table.setItem(row_idx, 5, QTableWidgetItem('Yes' if is_autoinc else 'No'))

            # Load indexes
            indexes = self.db_connection.get_table_indexes(table_name)
            indexes_text = "\n".join([f"{idx['name']} ({'UNIQUE' if idx['unique'] else 'INDEX'})" for idx in indexes])
            self.indexes_list.setText(indexes_text if indexes_text else "No indexes")

            # Load foreign keys
            fks = self.db_connection.get_foreign_keys(table_name)
            fk_text = "\n".join([
                f"{fk['from']} -> {fk['table']}.{fk['to']}"
                for fk in fks
            ])
            self.fk_list.setText(fk_text if fk_text else "No foreign keys")

        except Exception as e:
            QMessageBox.warning(self, "Schema Error", f"Failed to load schema:\n{str(e)}")

    def _load_current_page(self):
        """Reload current page"""
        current_item = self.tables_tree.currentItem()
        if current_item:
            table_name = current_item.data(0, Qt.ItemDataRole.UserRole)
            if table_name:
                self._load_table_data(table_name)

    def _on_page_size_changed(self):
        """Handle page size change"""
        self.page_spin.setValue(1)
        self._load_current_page()

    def _execute_query(self):
        """Execute custom SQL query"""
        if not self.db_connection:
            QMessageBox.warning(self, "No Database", "Please open a database first")
            return

        query = self.query_editor.toPlainText().strip()
        if not query:
            return

        try:
            # Add to history
            self.query_history.add_query(query)
            self._update_history_combo()

            # Execute query
            rows = self.db_connection.execute_query(query)

            # Display results
            self.query_results.clear()

            if rows:
                columns = list(rows[0].keys())
                self.query_results.setColumnCount(len(columns))
                self.query_results.setHorizontalHeaderLabels(columns)
                self.query_results.setRowCount(len(rows))

                for row_idx, row in enumerate(rows):
                    for col_idx, col_name in enumerate(columns):
                        value = row[col_name]
                        item = QTableWidgetItem(str(value) if value is not None else "NULL")
                        if value is None:
                            item.setForeground(QColor(128, 128, 128))
                        self.query_results.setItem(row_idx, col_idx, item)

                self.status_label.setText(f"Query returned {len(rows)} rows")
            else:
                self.status_label.setText("Query executed successfully (no results)")

        except Exception as e:
            QMessageBox.critical(self, "Query Error", f"Failed to execute query:\n{str(e)}")

    def _update_history_combo(self):
        """Update history combo box"""
        self.history_combo.clear()
        self.history_combo.addItems(self.query_history.get_history())

    def _load_query_from_history(self, query: str):
        """Load query from history into editor"""
        if query:
            self.query_editor.setText(query)

    def _search_all_tables(self):
        """Search for term across all tables"""
        if not self.db_connection:
            return

        search_term = self.search_input.text().strip()
        if not search_term:
            return

        self.search_results.setRowCount(0)

        try:
            tables = self.db_connection.get_tables()
            case_sensitive = self.case_sensitive_cb.isChecked()

            results_count = 0

            for table in tables:
                schema = self.db_connection.get_table_schema(table)

                # Build search query for this table
                where_clauses = []
                for col in schema:
                    col_name = col['name']
                    if case_sensitive:
                        where_clauses.append(f"CAST({col_name} AS TEXT) LIKE '%{search_term}%'")
                    else:
                        where_clauses.append(f"CAST({col_name} AS TEXT) LIKE '%{search_term}%' COLLATE NOCASE")

                if where_clauses:
                    query = f"SELECT * FROM {table} WHERE {' OR '.join(where_clauses)}"
                    rows = self.db_connection.execute_query(query)

                    # Add results
                    for row in rows:
                        for col_name in row.keys():
                            value = row[col_name]
                            if value is not None:
                                value_str = str(value)
                                # Check if this column matches
                                if (case_sensitive and search_term in value_str) or \
                                   (not case_sensitive and search_term.lower() in value_str.lower()):
                                    row_idx = self.search_results.rowCount()
                                    self.search_results.insertRow(row_idx)
                                    self.search_results.setItem(row_idx, 0, QTableWidgetItem(table))
                                    self.search_results.setItem(row_idx, 1, QTableWidgetItem(col_name))
                                    self.search_results.setItem(row_idx, 2, QTableWidgetItem(value_str))
                                    results_count += 1

            self.status_label.setText(f"Found {results_count} matches")

        except Exception as e:
            QMessageBox.warning(self, "Search Error", f"Search failed:\n{str(e)}")

    def _export_current_table(self):
        """Export current table to CSV"""
        current_item = self.tables_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Table", "Please select a table first")
            return

        table_name = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not table_name:
            return

        # Get save path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Table",
            f"{table_name}.csv",
            "CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*.*)"
        )

        if not file_path:
            return

        try:
            # Query all data
            query = f"SELECT * FROM {table_name}"
            rows = self.db_connection.execute_query(query)

            if file_path.endswith('.csv'):
                # Export to CSV
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    if rows:
                        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                        writer.writeheader()
                        for row in rows:
                            writer.writerow(dict(row))

            elif file_path.endswith('.xlsx'):
                # Export to Excel (requires openpyxl)
                try:
                    import openpyxl
                    wb = openpyxl.Workbook()
                    ws = wb.active
                    ws.title = table_name[:31]  # Excel sheet name limit

                    if rows:
                        # Write header
                        headers = list(rows[0].keys())
                        ws.append(headers)

                        # Write data
                        for row in rows:
                            ws.append(list(row))

                    wb.save(file_path)
                except ImportError:
                    QMessageBox.warning(self, "Export Error", "Excel export requires openpyxl package")
                    return

            QMessageBox.information(self, "Export Complete", f"Exported {len(rows)} rows to {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Export failed:\n{str(e)}")

    def _export_query_results(self):
        """Export query results to CSV"""
        if self.query_results.rowCount() == 0:
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
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                # Get headers
                headers = [
                    self.query_results.horizontalHeaderItem(i).text()
                    for i in range(self.query_results.columnCount())
                ]

                writer = csv.writer(f)
                writer.writerow(headers)

                # Write rows
                for row in range(self.query_results.rowCount()):
                    row_data = [
                        self.query_results.item(row, col).text()
                        for col in range(self.query_results.columnCount())
                    ]
                    writer.writerow(row_data)

            QMessageBox.information(self, "Export Complete", f"Exported to {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Export failed:\n{str(e)}")

    def _update_recent_menu(self):
        """Update recent databases menu"""
        menu = self.recent_btn.menu()
        menu.clear()

        recent = self.recent_databases.get_recent()

        if recent:
            for db_path in recent:
                action = QAction(os.path.basename(db_path), self)
                action.setToolTip(db_path)
                action.triggered.connect(lambda checked, path=db_path: self.open_database(path))
                menu.addAction(action)

            menu.addSeparator()
            clear_action = QAction("Clear Recent", self)
            clear_action.triggered.connect(self.recent_databases.clear_recent)
            menu.addAction(clear_action)
        else:
            no_recent = QAction("No recent databases", self)
            no_recent.setEnabled(False)
            menu.addAction(no_recent)

    def _show_table_context_menu(self, position):
        """Show context menu for table"""
        item = self.tables_tree.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        export_action = QAction("Export Table...", self)
        export_action.triggered.connect(self._export_current_table)
        menu.addAction(export_action)

        menu.exec(self.tables_tree.viewport().mapToGlobal(position))

    def refresh_current(self):
        """Refresh current view"""
        if self.current_db_path:
            self._load_tables()
            self._load_current_page()
            self.status_label.setText("Refreshed")

    def closeEvent(self, event):
        """Handle close event"""
        if self.db_connection:
            self.db_connection.close()
        super().closeEvent(event)


# Example usage
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    viewer = DatabaseViewer()
    viewer.setWindowTitle("SQLite Database Viewer")
    viewer.resize(1200, 800)
    viewer.show()
    sys.exit(app.exec())
