"""
iPhone View - Main iOS-style file browser interface
Combines all components into a cohesive browsing experience
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PyQt6.QtCore import Qt, pyqtSignal

from categories import FileCategory
from views.category_scanner import CategoryScanner, CategoryData
from ui.iphone_view_panel import iPhoneViewPanel
from ui.category_browser import CategoryBrowser

from typing import Optional, Dict


class iPhoneFileView(QWidget):
    """
    Main iPhone-style file browser view

    This is the top-level component that provides iOS Files app-like experience:
    - Category-based file organization
    - Visual grid of category cards
    - Smooth animations and modern UI
    - Quick access to recent files
    - Search within categories
    - Multiple view modes (list/grid)

    Usage:
        view = iPhoneFileView()
        view.set_path('/path/to/scan')
        view.show()
    """

    category_selected = pyqtSignal(FileCategory)
    file_opened = pyqtSignal(str)
    path_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scanner = CategoryScanner(cache_enabled=True)
        self.current_path: Optional[str] = None

        self._setup_ui()

    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main view panel
        self.main_panel = iPhoneViewPanel()
        self.main_panel.category_selected.connect(self._on_category_selected)
        self.main_panel.refresh_requested.connect(self._on_refresh_requested)

        layout.addWidget(self.main_panel)

    def set_path(self, path: str):
        """
        Set directory path to browse

        Args:
            path: Directory path to scan and categorize
        """
        self.current_path = path
        self.main_panel.set_path(path)
        self.path_changed.emit(path)

    def get_current_path(self) -> Optional[str]:
        """
        Get current browsing path

        Returns:
            Current directory path or None
        """
        return self.current_path

    def get_category_data(self, category: FileCategory) -> Optional[CategoryData]:
        """
        Get data for a specific category

        Args:
            category: FileCategory to get data for

        Returns:
            CategoryData or None if no data available
        """
        return self.main_panel.get_category_data(category)

    def refresh(self):
        """Refresh current view"""
        self.main_panel._refresh_scan()

    def clear_cache(self):
        """Clear scanner cache"""
        self.scanner.clear_cache()

    def _on_category_selected(self, category: FileCategory):
        """Handle category selection"""
        self.category_selected.emit(category)

    def _on_refresh_requested(self):
        """Handle refresh request"""
        # Additional refresh logic if needed
        pass

    # Public API for integration

    def get_scanner(self) -> CategoryScanner:
        """
        Get the category scanner instance

        Returns:
            CategoryScanner instance
        """
        return self.scanner

    def get_statistics(self) -> Dict:
        """
        Get file statistics for current path

        Returns:
            Dictionary with statistics:
            - total_files: Total number of files
            - total_size: Total size in bytes
            - categories: Category breakdown
        """
        categories = self.main_panel.categories_data
        if not categories:
            return {
                'total_files': 0,
                'total_size': 0,
                'categories': {}
            }

        return self.scanner.get_category_breakdown(categories)

    def search_in_category(self, category: FileCategory, query: str):
        """
        Search for files within a category

        Args:
            category: Category to search in
            query: Search query string

        Returns:
            List of matching file info dictionaries
        """
        categories = self.main_panel.categories_data
        return self.scanner.search_in_category(category, categories, query)

    def get_recent_files(self, limit: int = 20):
        """
        Get recently modified files across all categories

        Args:
            limit: Maximum number of files to return

        Returns:
            List of recent file info dictionaries
        """
        categories = self.main_panel.categories_data
        return self.scanner.get_recent_files(categories, limit)


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys
    import os

    app = QApplication(sys.argv)

    # Create main view
    view = iPhoneFileView()
    view.setWindowTitle("iPhone File View - Smart Search Pro")
    view.resize(1200, 800)

    # Set default path
    default_path = os.path.join(
        os.environ.get('USERPROFILE', ''),
        'Documents'
    )
    view.set_path(default_path)

    # Connect signals for testing
    view.category_selected.connect(
        lambda cat: print(f"Category selected: {cat.value}")
    )
    view.file_opened.connect(
        lambda path: print(f"File opened: {path}")
    )

    view.show()

    sys.exit(app.exec())
