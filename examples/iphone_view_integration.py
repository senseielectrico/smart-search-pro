"""
iPhone View Integration Example
Demonstrates how to integrate the iPhone view into Smart Search Pro
"""

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget,
    QVBoxLayout, QPushButton, QLabel, QFileDialog
)
from PyQt6.QtCore import Qt
import sys
import os

# Import iPhone view components
from views.iphone_view import iPhoneFileView
from categories import FileCategory
from ui.themes import get_theme_manager, Theme


class IntegrationExample(QMainWindow):
    """
    Example showing how to integrate iPhone view into your application
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("iPhone View Integration - Smart Search Pro")
        self.resize(1400, 900)

        # Get theme manager
        self.theme_manager = get_theme_manager()

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        """Setup user interface"""
        # Central widget with tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tab 1: iPhone View
        self._create_iphone_view_tab()

        # Tab 2: Control Panel
        self._create_control_panel_tab()

    def _create_iphone_view_tab(self):
        """Create iPhone view tab"""
        self.iphone_view = iPhoneFileView()

        # Set initial path (Documents folder)
        default_path = os.path.join(
            os.environ.get('USERPROFILE', ''),
            'Documents'
        )

        if os.path.exists(default_path):
            self.iphone_view.set_path(default_path)

        # Connect signals
        self.iphone_view.category_selected.connect(self._on_category_selected)
        self.iphone_view.file_opened.connect(self._on_file_opened)
        self.iphone_view.path_changed.connect(self._on_path_changed)

        self.tabs.addTab(self.iphone_view, "📱 Browse Files")

    def _create_control_panel_tab(self):
        """Create control panel tab"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Title
        title = QLabel("Control Panel")
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Path selector
        path_btn = QPushButton("Select Directory to Browse")
        path_btn.clicked.connect(self._select_directory)
        layout.addWidget(path_btn)

        # Current path display
        self.path_label = QLabel("No path selected")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: #8E8E93; padding: 10px;")
        layout.addWidget(self.path_label)

        # Statistics
        stats_label = QLabel("Statistics:")
        font = stats_label.font()
        font.setBold(True)
        stats_label.setFont(font)
        layout.addWidget(stats_label)

        self.stats_display = QLabel("No data")
        self.stats_display.setWordWrap(True)
        self.stats_display.setStyleSheet("padding: 10px; background-color: palette(base);")
        layout.addWidget(self.stats_display)

        # Refresh button
        refresh_btn = QPushButton("Refresh View")
        refresh_btn.clicked.connect(self._refresh_view)
        layout.addWidget(refresh_btn)

        # Theme toggle
        self.theme_btn = QPushButton("Switch to Dark Theme")
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)

        # Clear cache button
        clear_btn = QPushButton("Clear Cache")
        clear_btn.clicked.connect(self._clear_cache)
        layout.addWidget(clear_btn)

        # Get recent files button
        recent_btn = QPushButton("Show Recent Files")
        recent_btn.clicked.connect(self._show_recent_files)
        layout.addWidget(recent_btn)

        layout.addStretch()

        self.tabs.addTab(panel, "⚙ Control Panel")

    def _apply_theme(self):
        """Apply current theme"""
        stylesheet = self.theme_manager.get_stylesheet()
        self.setStyleSheet(stylesheet)

    def _select_directory(self):
        """Select directory to browse"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Browse",
            self.iphone_view.get_current_path() or os.path.expanduser('~')
        )

        if path:
            self.iphone_view.set_path(path)
            self.path_label.setText(f"Current path: {path}")
            self._update_statistics()

    def _refresh_view(self):
        """Refresh current view"""
        self.iphone_view.refresh()
        self._update_statistics()
        print("View refreshed")

    def _toggle_theme(self):
        """Toggle between light and dark theme"""
        current = self.theme_manager.current_theme

        if current == Theme.LIGHT:
            self.theme_manager.set_theme(Theme.DARK)
            self.theme_btn.setText("Switch to Light Theme")
        else:
            self.theme_manager.set_theme(Theme.LIGHT)
            self.theme_btn.setText("Switch to Dark Theme")

        self._apply_theme()

    def _clear_cache(self):
        """Clear scanner cache"""
        self.iphone_view.clear_cache()
        print("Cache cleared")

    def _show_recent_files(self):
        """Show recent files in console"""
        recent = self.iphone_view.get_recent_files(limit=10)

        print("\nRecent Files:")
        print("-" * 80)

        if not recent:
            print("No recent files found")
            return

        from datetime import datetime

        for i, file_info in enumerate(recent, 1):
            dt = datetime.fromtimestamp(file_info['modified'])
            print(f"{i}. {file_info['name']}")
            print(f"   Path: {file_info['path']}")
            print(f"   Modified: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Size: {file_info['size']} bytes")
            print()

    def _update_statistics(self):
        """Update statistics display"""
        stats = self.iphone_view.get_statistics()

        text = f"""
        <b>Total Files:</b> {stats['total_files']}<br>
        <b>Total Size:</b> {stats['formatted_size']}<br>
        <br>
        <b>Category Breakdown:</b><br>
        """

        categories = stats.get('categories', {})
        for cat_name, cat_stats in categories.items():
            text += f"• {cat_name}: {cat_stats['count']} files ({cat_stats['formatted_size']})<br>"

        self.stats_display.setText(text)

    def _on_category_selected(self, category: FileCategory):
        """Handle category selection"""
        print(f"\n=== Category Selected: {category.value} ===")

        data = self.iphone_view.get_category_data(category)
        if data:
            print(f"Files: {data.file_count}")
            print(f"Total Size: {data.formatted_size}")
            print(f"Average Size: {data.average_size} bytes")

    def _on_file_opened(self, path: str):
        """Handle file opened"""
        print(f"\n=== File Opened ===")
        print(f"Path: {path}")

    def _on_path_changed(self, path: str):
        """Handle path changed"""
        print(f"\n=== Path Changed ===")
        print(f"New path: {path}")

        self.path_label.setText(f"Current path: {path}")
        self._update_statistics()


def main():
    """Run integration example"""
    app = QApplication(sys.argv)

    # Set Fusion style for better cross-platform look
    app.setStyle('Fusion')

    # Create and show window
    window = IntegrationExample()
    window.show()

    # Print instructions
    print("=" * 80)
    print("iPhone View Integration Example")
    print("=" * 80)
    print("\nFeatures to try:")
    print("1. Browse categories by clicking category cards")
    print("2. View files in list or grid mode")
    print("3. Search within categories")
    print("4. Sort files by different criteria")
    print("5. Switch between light and dark themes")
    print("6. Select different directories to browse")
    print("7. View recent files")
    print("8. Check statistics in the control panel")
    print("\nSignals are logged to console for demonstration.")
    print("=" * 80)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
