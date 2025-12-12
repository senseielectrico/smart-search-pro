"""
Integration example for saved searches and favorites system.

This file shows how to integrate the saved searches, favorites, and smart collections
into the main Smart Search Pro window.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QPushButton, QToolBar, QStatusBar, QMessageBox,
    QFileDialog
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QKeySequence, QIcon

# Import panels
sys.path.insert(0, str(Path(__file__).parent / 'ui'))
sys.path.insert(0, str(Path(__file__).parent / 'search'))

from ui.saved_searches_panel import SavedSearchesPanel
from ui.favorites_panel import FavoritesPanel
from ui.save_search_dialog import SaveSearchDialog
from ui.collection_editor import CollectionEditor

from search.saved_searches import SavedSearch
from search.favorites_manager import Favorite
from search.smart_collections import SmartCollection


class IntegratedMainWindow(QMainWindow):
    """
    Example main window with saved searches and favorites integrated.

    This demonstrates how to integrate all the new features into
    your existing Smart Search Pro main window.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Search Pro - With Saved Searches & Favorites")
        self.setGeometry(100, 100, 1400, 800)

        # Settings
        self.settings = QSettings("SmartSearchPro", "SavedSearches")

        # Initialize UI
        self._init_ui()
        self._init_toolbar()
        self._init_menu()
        self._init_shortcuts()

        # Restore state
        self._restore_state()

    def _init_ui(self):
        """Initialize UI components."""
        # Central widget with splitter
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Main splitter (3 panels)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Saved searches & collections
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Saved searches panel
        self.saved_searches_panel = SavedSearchesPanel()
        self.saved_searches_panel.search_executed.connect(self.on_execute_saved_search)
        self.saved_searches_panel.search_edited.connect(self.on_edit_saved_search)
        self.saved_searches_panel.search_selected.connect(self.on_saved_search_selected)
        left_layout.addWidget(self.saved_searches_panel)

        splitter.addWidget(left_panel)

        # Center panel: Main search area (placeholder)
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.addWidget(QPushButton("Main Search Panel\n(Your existing search UI goes here)"))
        splitter.addWidget(center_panel)

        # Right panel: Favorites
        self.favorites_panel = FavoritesPanel()
        self.favorites_panel.favorite_opened.connect(self.on_open_favorite)
        self.favorites_panel.favorite_selected.connect(self.on_favorite_selected)
        splitter.addWidget(self.favorites_panel)

        # Set initial sizes (25% - 50% - 25%)
        splitter.setSizes([300, 600, 300])

        layout.addWidget(splitter)

        # Status bar
        self.statusBar().showMessage("Ready")

    def _init_toolbar(self):
        """Initialize toolbar with new actions."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Save search action
        save_search_action = QAction("Save Search", self)
        save_search_action.setShortcut(QKeySequence("Ctrl+S"))
        save_search_action.setStatusTip("Save current search")
        save_search_action.triggered.connect(self.on_save_current_search)
        toolbar.addAction(save_search_action)

        toolbar.addSeparator()

        # Toggle favorites panel
        toggle_favorites_action = QAction("Favorites", self)
        toggle_favorites_action.setCheckable(True)
        toggle_favorites_action.setChecked(True)
        toggle_favorites_action.setStatusTip("Toggle favorites panel")
        toggle_favorites_action.triggered.connect(self.toggle_favorites_panel)
        toolbar.addAction(toggle_favorites_action)

        # Toggle saved searches panel
        toggle_saved_action = QAction("Saved Searches", self)
        toggle_saved_action.setCheckable(True)
        toggle_saved_action.setChecked(True)
        toggle_saved_action.setStatusTip("Toggle saved searches panel")
        toggle_saved_action.triggered.connect(self.toggle_saved_searches_panel)
        toolbar.addAction(toggle_saved_action)

        toolbar.addSeparator()

        # Collections
        collections_action = QAction("Smart Collections", self)
        collections_action.setStatusTip("Manage smart collections")
        collections_action.triggered.connect(self.show_collections_manager)
        toolbar.addAction(collections_action)

        toolbar.addSeparator()

        # Export/Import
        export_action = QAction("Export...", self)
        export_action.setStatusTip("Export saved searches and favorites")
        export_action.triggered.connect(self.export_data)
        toolbar.addAction(export_action)

        import_action = QAction("Import...", self)
        import_action.setStatusTip("Import saved searches and favorites")
        import_action.triggered.connect(self.import_data)
        toolbar.addAction(import_action)

    def _init_menu(self):
        """Initialize menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        save_search_action = file_menu.addAction("Save Search...")
        save_search_action.setShortcut(QKeySequence("Ctrl+S"))
        save_search_action.triggered.connect(self.on_save_current_search)

        file_menu.addSeparator()

        export_action = file_menu.addAction("Export Data...")
        export_action.triggered.connect(self.export_data)

        import_action = file_menu.addAction("Import Data...")
        import_action.triggered.connect(self.import_data)

        # Favorites menu
        favorites_menu = menubar.addMenu("Favorites")

        add_favorite_action = favorites_menu.addAction("Add to Favorites")
        add_favorite_action.setShortcut(QKeySequence("F"))
        add_favorite_action.triggered.connect(self.toggle_current_favorite)

        favorites_menu.addSeparator()

        for i in range(1, 6):
            stars = "★" * i
            action = favorites_menu.addAction(f"Set Rating: {stars}")
            action.triggered.connect(lambda checked, r=i: self.set_current_rating(r))

        # View menu
        view_menu = menubar.addMenu("View")

        toggle_saved = view_menu.addAction("Saved Searches Panel")
        toggle_saved.setCheckable(True)
        toggle_saved.setChecked(True)
        toggle_saved.triggered.connect(self.toggle_saved_searches_panel)

        toggle_favs = view_menu.addAction("Favorites Panel")
        toggle_favs.setCheckable(True)
        toggle_favs.setChecked(True)
        toggle_favs.triggered.connect(self.toggle_favorites_panel)

        # Collections menu
        collections_menu = menubar.addMenu("Collections")

        new_collection_action = collections_menu.addAction("New Collection...")
        new_collection_action.triggered.connect(self.create_new_collection)

        manage_collections_action = collections_menu.addAction("Manage Collections...")
        manage_collections_action.triggered.connect(self.show_collections_manager)

    def _init_shortcuts(self):
        """Initialize keyboard shortcuts."""
        # Saved search shortcuts (Ctrl+1 through Ctrl+9)
        for i in range(1, 10):
            shortcut = QKeySequence(f"Ctrl+{i}")
            action = QAction(self)
            action.setShortcut(shortcut)
            action.triggered.connect(lambda checked, key=i: self.execute_saved_search_by_key(key))
            self.addAction(action)

        # Toggle favorite (F key)
        toggle_fav_action = QAction(self)
        toggle_fav_action.setShortcut(QKeySequence("F"))
        toggle_fav_action.triggered.connect(self.toggle_current_favorite)
        self.addAction(toggle_fav_action)

    # ====================
    # Saved Searches
    # ====================

    def on_save_current_search(self):
        """Save current search configuration."""
        # Get current search parameters
        # (This would come from your actual search panel)
        params = self._get_current_search_params()

        # Show save dialog
        dialog = SaveSearchDialog(parent=self)
        dialog.set_search_params(params)

        if dialog.exec():
            saved_search = dialog.get_search()
            self.saved_searches_panel.refresh()
            self.statusBar().showMessage(f"Saved search '{saved_search.name}'", 3000)

    def on_execute_saved_search(self, search: SavedSearch):
        """Execute a saved search."""
        # Apply search parameters
        self._apply_search_params({
            'query': search.query,
            'file_types': search.file_types,
            'min_size': search.min_size,
            'max_size': search.max_size,
            'date_from': search.date_from,
            'date_to': search.date_to,
            'sort_order': search.sort_order,
            'ascending': search.ascending,
            'search_paths': search.search_paths,
            'view_mode': search.view_mode,
            'show_preview': search.show_preview,
        })

        # Execute search
        # (Your search execution code here)
        result_count = self._perform_search()

        # Update statistics
        self.saved_searches_panel.update_search_results(search.id, result_count)

        self.statusBar().showMessage(
            f"Executed '{search.name}' - {result_count} results",
            3000
        )

    def on_edit_saved_search(self, search: SavedSearch):
        """Edit a saved search."""
        dialog = SaveSearchDialog(search, parent=self)

        if dialog.exec():
            updated_search = dialog.get_search()
            self.saved_searches_panel.refresh()
            self.statusBar().showMessage(f"Updated '{updated_search.name}'", 3000)

    def on_saved_search_selected(self, search: SavedSearch):
        """Handle saved search selection (preview parameters)."""
        # Show search parameters in status bar or preview panel
        self.statusBar().showMessage(
            f"Selected: {search.name} - Query: {search.query}",
            5000
        )

    def execute_saved_search_by_key(self, key: int):
        """Execute saved search by keyboard shortcut."""
        search = self.saved_searches_panel.get_search_by_shortcut(key)
        if search:
            self.on_execute_saved_search(search)
        else:
            self.statusBar().showMessage(f"No search assigned to Ctrl+{key}", 3000)

    # ====================
    # Favorites
    # ====================

    def toggle_current_favorite(self):
        """Toggle favorite status for currently selected file."""
        # Get selected file from results panel
        selected_file = self._get_selected_file()
        if not selected_file:
            self.statusBar().showMessage("No file selected", 3000)
            return

        if self.favorites_panel.is_favorite(selected_file):
            self.favorites_panel.remove_favorite(selected_file)
            self.statusBar().showMessage(f"Removed from favorites", 3000)
        else:
            self.favorites_panel.add_favorite(selected_file, rating=3)
            self.statusBar().showMessage(f"Added to favorites", 3000)

    def set_current_rating(self, rating: int):
        """Set rating for currently selected file."""
        selected_file = self._get_selected_file()
        if not selected_file:
            return

        if not self.favorites_panel.is_favorite(selected_file):
            # Add to favorites first
            self.favorites_panel.add_favorite(selected_file, rating=rating)
        else:
            # Update rating
            favorite = self.favorites_panel.manager.get_by_path(selected_file)
            if favorite:
                self.favorites_panel.manager.update_rating(favorite.id, rating)
                self.favorites_panel.refresh()

        self.statusBar().showMessage(f"Set rating to {rating} stars", 3000)

    def on_open_favorite(self, path: str):
        """Open a favorite file."""
        # Open file with default application
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl

        QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        self.statusBar().showMessage(f"Opened: {Path(path).name}", 3000)

    def on_favorite_selected(self, favorite: Favorite):
        """Handle favorite selection."""
        self.statusBar().showMessage(
            f"Selected: {favorite.name} - Rating: {favorite.rating}/5",
            5000
        )

    # ====================
    # Collections
    # ====================

    def create_new_collection(self):
        """Create a new smart collection."""
        dialog = CollectionEditor(parent=self)

        if dialog.exec():
            collection = dialog.get_collection()
            self.statusBar().showMessage(
                f"Created collection '{collection.name}'",
                3000
            )

    def show_collections_manager(self):
        """Show collections management dialog."""
        # This would show a dialog listing all collections
        # with options to edit, delete, and evaluate them
        QMessageBox.information(
            self,
            "Collections Manager",
            "Collections manager would be shown here.\n"
            "This would list all smart collections with options to:\n"
            "- Edit collection rules\n"
            "- Delete collections\n"
            "- Evaluate collections\n"
            "- View matching files"
        )

    # ====================
    # Import/Export
    # ====================

    def export_data(self):
        """Export saved searches and favorites."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            str(Path.home())
        )

        if not directory:
            return

        try:
            # Export saved searches
            searches_file = Path(directory) / "saved_searches.json"
            self.saved_searches_panel.manager.export_to_json(str(searches_file))

            # Export favorites
            favorites_file = Path(directory) / "favorites.json"
            self.favorites_panel.manager.export_to_json(str(favorites_file))

            # Export collections
            from search.smart_collections import SmartCollectionsManager
            collections_manager = SmartCollectionsManager()
            collections_file = Path(directory) / "collections.json"
            collections_manager.export_to_json(str(collections_file))

            QMessageBox.information(
                self,
                "Export Complete",
                f"Data exported to:\n{directory}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export data: {e}"
            )

    def import_data(self):
        """Import saved searches and favorites."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Import Directory",
            str(Path.home())
        )

        if not directory:
            return

        try:
            imported = []

            # Import saved searches
            searches_file = Path(directory) / "saved_searches.json"
            if searches_file.exists():
                count = self.saved_searches_panel.manager.import_from_json(
                    str(searches_file),
                    merge=True
                )
                imported.append(f"{count} saved searches")
                self.saved_searches_panel.refresh()

            # Import favorites
            favorites_file = Path(directory) / "favorites.json"
            if favorites_file.exists():
                count = self.favorites_panel.manager.import_from_json(
                    str(favorites_file),
                    merge=True
                )
                imported.append(f"{count} favorites")
                self.favorites_panel.refresh()

            # Import collections
            collections_file = Path(directory) / "collections.json"
            if collections_file.exists():
                from search.smart_collections import SmartCollectionsManager
                collections_manager = SmartCollectionsManager()
                count = collections_manager.import_from_json(
                    str(collections_file),
                    merge=True
                )
                imported.append(f"{count} collections")

            if imported:
                QMessageBox.information(
                    self,
                    "Import Complete",
                    f"Imported:\n" + "\n".join(imported)
                )
            else:
                QMessageBox.warning(
                    self,
                    "Nothing to Import",
                    "No data files found in selected directory."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Failed",
                f"Failed to import data: {e}"
            )

    # ====================
    # UI Toggles
    # ====================

    def toggle_favorites_panel(self):
        """Toggle favorites panel visibility."""
        visible = self.favorites_panel.isVisible()
        self.favorites_panel.setVisible(not visible)

    def toggle_saved_searches_panel(self):
        """Toggle saved searches panel visibility."""
        visible = self.saved_searches_panel.isVisible()
        self.saved_searches_panel.setVisible(not visible)

    # ====================
    # State Management
    # ====================

    def _restore_state(self):
        """Restore window state from settings."""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)

    def closeEvent(self, event):
        """Save state on close."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        event.accept()

    # ====================
    # Helper Methods (Placeholder implementations)
    # ====================

    def _get_current_search_params(self) -> Dict[str, Any]:
        """Get current search parameters from UI."""
        # This would extract actual parameters from your search panel
        return {
            'query': '*.py',
            'file_types': ['.py'],
            'min_size': None,
            'max_size': None,
            'date_from': None,
            'date_to': None,
            'sort_order': 'name',
            'ascending': True,
            'search_paths': [],
            'view_mode': 'list',
            'show_preview': True,
        }

    def _apply_search_params(self, params: Dict[str, Any]):
        """Apply search parameters to UI."""
        # This would update your search panel with the parameters
        print(f"Applying search params: {params}")

    def _perform_search(self) -> int:
        """Perform the actual search."""
        # This would execute your search and return result count
        return 42  # Mock result

    def _get_selected_file(self) -> Optional[str]:
        """Get currently selected file path."""
        # This would get the selected file from your results panel
        return None  # Placeholder


def main():
    """Run the integrated example."""
    app = QApplication(sys.argv)

    window = IntegratedMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
