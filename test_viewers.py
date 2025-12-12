#!/usr/bin/env python
"""
Test Data Viewers
=================

Test script for database and JSON viewers.
Creates sample data and demonstrates all viewer functionality.

Usage:
    python test_viewers.py
"""

import os
import sys
import json
import sqlite3
import tempfile
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt


def create_sample_database(db_path: str):
    """Create a sample SQLite database for testing"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL,
            age INTEGER,
            active BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create posts table with foreign key
    cursor.execute('''
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            views INTEGER DEFAULT 0,
            published BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create index on posts
    cursor.execute('CREATE INDEX idx_posts_user_id ON posts(user_id)')
    cursor.execute('CREATE INDEX idx_posts_published ON posts(published)')

    # Insert sample users
    users = [
        ('alice', 'alice@example.com', 28, 1),
        ('bob', 'bob@example.com', 35, 1),
        ('charlie', 'charlie@example.com', 22, 0),
        ('diana', 'diana@example.com', 31, 1),
        ('eve', 'eve@example.com', 29, 1),
    ]

    cursor.executemany(
        'INSERT INTO users (username, email, age, active) VALUES (?, ?, ?, ?)',
        users
    )

    # Insert sample posts
    posts = [
        (1, 'First Post', 'This is Alice\'s first post', 150, 1),
        (1, 'Second Post', 'Another post by Alice', 89, 1),
        (2, 'Bob\'s Thoughts', 'What I think about databases', 245, 1),
        (2, 'Draft Post', 'Work in progress', 0, 0),
        (3, 'Charlie Here', 'Hello world!', 12, 1),
        (4, 'Diana\'s Guide', 'Complete guide to JSON', 1024, 1),
        (4, 'Data Structures', 'Understanding trees and graphs', 567, 1),
        (5, 'Eve\'s Tutorial', 'How to build viewers', 789, 1),
    ]

    cursor.executemany(
        'INSERT INTO posts (user_id, title, content, views, published) VALUES (?, ?, ?, ?, ?)',
        posts
    )

    # Create a tags table
    cursor.execute('''
        CREATE TABLE tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT
        )
    ''')

    tags = [
        ('python', '#3776ab'),
        ('database', '#336791'),
        ('tutorial', '#ff6b6b'),
        ('guide', '#4ecdc4'),
    ]

    cursor.executemany('INSERT INTO tags (name, color) VALUES (?, ?)', tags)

    conn.commit()
    conn.close()

    return db_path


def create_sample_json(json_path: str):
    """Create a sample JSON file for testing"""
    data = {
        "application": {
            "name": "Smart Search Pro",
            "version": "1.0.0",
            "author": "Smart Search Team",
            "license": "MIT"
        },
        "features": [
            {
                "name": "Database Viewer",
                "enabled": True,
                "priority": 1,
                "formats": ["sqlite", "db", "sqlite3"]
            },
            {
                "name": "JSON Viewer",
                "enabled": True,
                "priority": 2,
                "formats": ["json"]
            },
            {
                "name": "File Search",
                "enabled": True,
                "priority": 3,
                "formats": ["*"]
            }
        ],
        "configuration": {
            "theme": "dark",
            "language": "en",
            "max_results": 1000,
            "cache_enabled": True,
            "cache_size_mb": 100,
            "auto_update": False
        },
        "statistics": {
            "files_indexed": 152340,
            "total_size_bytes": 5368709120,
            "databases_opened": 47,
            "json_files_viewed": 231,
            "last_scan": "2025-12-12T10:30:00Z",
            "uptime_hours": 1247.5
        },
        "users": [
            {
                "id": 1,
                "name": "Alice Admin",
                "role": "administrator",
                "permissions": ["read", "write", "delete", "admin"],
                "last_login": "2025-12-12T09:15:00Z"
            },
            {
                "id": 2,
                "name": "Bob User",
                "role": "user",
                "permissions": ["read", "write"],
                "last_login": "2025-12-11T18:45:00Z"
            },
            {
                "id": 3,
                "name": "Charlie Guest",
                "role": "guest",
                "permissions": ["read"],
                "last_login": None
            }
        ],
        "metadata": {
            "created": "2025-01-01T00:00:00Z",
            "modified": "2025-12-12T10:30:00Z",
            "format_version": "2.1",
            "checksum": "a1b2c3d4e5f6",
            "encrypted": False,
            "compression": None
        }
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return json_path


def create_sample_csv(csv_path: str):
    """Create a sample CSV file for testing"""
    import csv

    data = [
        ['Name', 'Age', 'City', 'Salary', 'Department'],
        ['Alice Johnson', '28', 'New York', '75000', 'Engineering'],
        ['Bob Smith', '35', 'San Francisco', '95000', 'Engineering'],
        ['Charlie Brown', '22', 'Austin', '55000', 'Marketing'],
        ['Diana Prince', '31', 'Seattle', '85000', 'Product'],
        ['Eve Anderson', '29', 'Boston', '72000', 'Design'],
    ]

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(data)

    return csv_path


class ViewerTestApp(QMainWindow):
    """Test application for viewers"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Data Viewers Test Suite")
        self.resize(1400, 900)

        # Create temp directory for sample files
        self.temp_dir = tempfile.mkdtemp(prefix="viewer_test_")

        # Create sample files
        self.db_path = create_sample_database(os.path.join(self.temp_dir, "sample.db"))
        self.json_path = create_sample_json(os.path.join(self.temp_dir, "sample.json"))
        self.csv_path = create_sample_csv(os.path.join(self.temp_dir, "sample.csv"))

        self._init_ui()

    def _init_ui(self):
        """Initialize UI"""
        # Central widget with tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Welcome tab
        welcome_tab = self._create_welcome_tab()
        self.tabs.addTab(welcome_tab, "Welcome")

        # Database viewer tab
        try:
            from viewers.database_viewer import DatabaseViewer
            self.db_viewer = DatabaseViewer()
            self.db_viewer.open_database(self.db_path)
            self.tabs.addTab(self.db_viewer, "Database Viewer")
        except Exception as e:
            print(f"Failed to load database viewer: {e}")

        # JSON viewer tab
        try:
            from viewers.json_viewer import JSONViewer
            self.json_viewer = JSONViewer()
            self.json_viewer.open_file(self.json_path)
            self.tabs.addTab(self.json_viewer, "JSON Viewer")
        except Exception as e:
            print(f"Failed to load JSON viewer: {e}")

        # Database panel tab (UI integration)
        try:
            from ui.database_panel import DatabasePanel
            self.db_panel = DatabasePanel()
            self.db_panel.open_database(self.db_path)
            self.tabs.addTab(self.db_panel, "Database Panel")
        except Exception as e:
            print(f"Failed to load database panel: {e}")

        # JSON tree widget tab
        try:
            from ui.json_tree_widget import JSONTreeWidget
            self.json_tree = JSONTreeWidget()
            self.json_tree.load_json_file(self.json_path)
            self.tabs.addTab(self.json_tree, "JSON Tree Widget")
        except Exception as e:
            print(f"Failed to load JSON tree widget: {e}")

        # Factory demo tab
        factory_tab = self._create_factory_tab()
        self.tabs.addTab(factory_tab, "Factory Demo")

        # Status bar
        self.statusBar().showMessage(f"Sample files created in: {self.temp_dir}")

    def _create_welcome_tab(self) -> QWidget:
        """Create welcome tab"""
        from PyQt6.QtWidgets import QLabel, QTextEdit

        tab = QWidget()
        layout = QVBoxLayout(tab)

        title = QLabel("Data Viewers Test Suite")
        title.setStyleSheet("font-size: 18pt; font-weight: bold;")
        layout.addWidget(title)

        info = QTextEdit()
        info.setReadOnly(True)
        info.setMaximumHeight(300)
        info.setMarkdown(f"""
# Welcome to Data Viewers Test Suite

This test application demonstrates all viewer functionality.

## Sample Files Created

- **Database**: `{os.path.basename(self.db_path)}`
  - Tables: users, posts, tags
  - Relationships: posts -> users (foreign key)
  - Indexes: on user_id and published

- **JSON**: `{os.path.basename(self.json_path)}`
  - Nested objects and arrays
  - Multiple data types
  - User configuration example

- **CSV**: `{os.path.basename(self.csv_path)}`
  - Employee data
  - 5 rows, 5 columns

## Test Features

### Database Viewer Tab
1. Browse tables (users, posts, tags)
2. View table schemas with indexes and foreign keys
3. Execute custom SQL queries (try: `SELECT * FROM users WHERE active = 1`)
4. Export tables to CSV
5. Search across all tables

### JSON Viewer Tab
1. Navigate tree structure
2. Edit values in raw JSON tab
3. View table representation (for arrays)
4. Copy paths and values
5. Format and validate JSON

### Database Panel Tab
- Integrated version for main window
- Multiple database support (tabs)
- Query history and bookmarks

### JSON Tree Widget Tab
- Reusable widget component
- Context menu operations
- Color-coded types

### Factory Demo Tab
- Auto-detect file types
- Open any supported format
- Extension registration

## Sample Queries to Try

**Users Table:**
```sql
SELECT * FROM users WHERE age > 25
```

**Posts with User Info:**
```sql
SELECT users.username, posts.title, posts.views
FROM posts
JOIN users ON posts.user_id = users.id
WHERE posts.published = 1
ORDER BY posts.views DESC
```

**Statistics:**
```sql
SELECT
    users.username,
    COUNT(posts.id) as post_count,
    SUM(posts.views) as total_views
FROM users
LEFT JOIN posts ON users.id = posts.user_id
GROUP BY users.id
```

Enjoy testing!
""")
        layout.addWidget(info)

        return tab

    def _create_factory_tab(self) -> QWidget:
        """Create factory demo tab"""
        from PyQt6.QtWidgets import QFileDialog

        tab = QWidget()
        layout = QVBoxLayout(tab)

        title = QLabel("Data Viewer Factory Demo")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title)

        info = QLabel(
            "Click the button below to open any supported file type.\n"
            "The factory will auto-detect the format and open the appropriate viewer."
        )
        layout.addWidget(info)

        btn = QPushButton("Open File with Factory...")
        btn.clicked.connect(self._open_with_factory)
        layout.addWidget(btn)

        layout.addStretch()

        # Show supported formats
        try:
            from viewers.data_viewer_factory import DataViewerFactory
            factory = DataViewerFactory()

            formats_label = QLabel("Supported Formats:")
            formats_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
            layout.addWidget(formats_label)

            from PyQt6.QtWidgets import QTextEdit
            formats_text = QTextEdit()
            formats_text.setReadOnly(True)
            formats_text.setMaximumHeight(150)
            formats_text.setText("\n".join(factory.get_supported_extensions()))
            layout.addWidget(formats_text)

        except Exception as e:
            print(f"Failed to load factory: {e}")

        return tab

    def _open_with_factory(self):
        """Open file with factory"""
        try:
            from viewers.data_viewer_factory import DataViewerFactory
            from PyQt6.QtWidgets import QFileDialog

            factory = DataViewerFactory()

            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Open Data File",
                self.temp_dir,
                factory.get_filter_string()
            )

            if file_path:
                viewer = factory.create_viewer(file_path)
                if viewer:
                    viewer.resize(1200, 800)
                    viewer.show()
                    self.statusBar().showMessage(f"Opened: {os.path.basename(file_path)}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file:\n{str(e)}")

    def closeEvent(self, event):
        """Clean up on close"""
        # Clean up temp files
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
            print(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            print(f"Failed to clean up temp directory: {e}")

        super().closeEvent(event)


def main():
    """Main entry point"""
    app = QApplication(sys.argv)

    # Set app style
    app.setStyle('Fusion')

    # Create and show test app
    window = ViewerTestApp()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
