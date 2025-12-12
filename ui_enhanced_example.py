"""
Smart Search UI - Enhanced Version Example
Demonstrates integration of all UX enhancements

This is a reference implementation showing how to integrate
ui_enhancements.py components into the main UI.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QSplitter, QLabel, QTabWidget,
    QMessageBox, QDialog, QInputDialog, QMenuBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QFont

# Import original components
from ui import (
    SmartSearchWindow, SearchWorker, FileOperationWorker,
    ResultsTableWidget, FileType
)

# Import enhancements
from ui_enhancements import (
    SearchHistoryWidget, QuickFilterChips, EnhancedDirectoryTree,
    FilePreviewPanel, GridViewWidget, SearchPresetsDialog,
    SearchPreset, ExportDialog, AccessibleTooltip,
    KeyboardShortcutsDialog, show_notification
)


class EnhancedSmartSearchWindow(SmartSearchWindow):
    """
    Enhanced version of SmartSearchWindow with UX improvements
    Inherits from original and adds enhanced features
    """

    def __init__(self):
        # Initialize parent but override _init_ui
        QMainWindow.__init__(self)
        self.search_worker = None
        self.operation_worker = None
        self.dark_mode = False
        self.view_mode = "list"
        self.current_filter = []

        # Initialize presets dialog
        self.presets_dialog = SearchPresetsDialog(self)

        # Initialize enhanced UI
        self._init_enhanced_ui()
        self._setup_enhanced_shortcuts()
        self._apply_theme()

    def _init_enhanced_ui(self):
        """Initialize enhanced UI with all improvements"""
        self.setWindowTitle("Smart Search - Enhanced Edition")
        self.setMinimumSize(1400, 800)
        self.resize(1600, 900)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Menu bar
        self._create_menu_bar()

        # Top search bar with filters
        search_container = self._create_enhanced_search_bar()
        main_layout.addWidget(search_container)

        # Main 3-panel splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # === LEFT PANEL: Directory Tree + History ===
        left_panel = QWidget()
        left_panel.setMinimumWidth(280)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Enhanced directory tree with favorites
        self.dir_tree = EnhancedDirectoryTree()
        self._populate_directory_tree()
        left_layout.addWidget(self.dir_tree, stretch=2)

        # Search history
        history_label = QLabel("Search History")
        history_label.setStyleSheet("font-weight: bold; padding: 5px;")
        left_layout.addWidget(history_label)

        self.search_history = SearchHistoryWidget()
        self.search_history.search_selected.connect(self._load_search_from_history)
        left_layout.addWidget(self.search_history, stretch=1)

        main_splitter.addWidget(left_panel)

        # === CENTER PANEL: Results ===
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)

        # View mode toggle
        view_toolbar = QHBoxLayout()
        view_label = QLabel("View:")
        view_toolbar.addWidget(view_label)

        self.list_view_btn = QPushButton("List")
        self.list_view_btn.setCheckable(True)
        self.list_view_btn.setChecked(True)
        self.list_view_btn.clicked.connect(lambda: self._set_view_mode("list"))
        AccessibleTooltip.set_tooltip(self.list_view_btn, "List view", "Ctrl+1")

        self.grid_view_btn = QPushButton("Grid")
        self.grid_view_btn.setCheckable(True)
        self.grid_view_btn.clicked.connect(lambda: self._set_view_mode("grid"))
        AccessibleTooltip.set_tooltip(self.grid_view_btn, "Grid view with thumbnails", "Ctrl+2")

        view_toolbar.addWidget(self.list_view_btn)
        view_toolbar.addWidget(self.grid_view_btn)
        view_toolbar.addStretch()

        center_layout.addLayout(view_toolbar)

        # Results tabs (list view)
        self.results_tabs = QTabWidget()
        self.results_tabs.setTabPosition(QTabWidget.TabPosition.North)

        self.result_tables: Dict[FileType, ResultsTableWidget] = {}
        for file_type in FileType:
            table = ResultsTableWidget()
            table.itemSelectionChanged.connect(self._on_selection_changed)
            self.results_tabs.addTab(table, file_type.display_name)
            self.result_tables[file_type] = table

        center_layout.addWidget(self.results_tabs)

        # Grid view (hidden by default)
        self.grid_view = GridViewWidget()
        self.grid_view.item_selected.connect(self._on_grid_item_selected)
        self.grid_view.item_double_clicked.connect(self._open_file_from_path)
        self.grid_view.setVisible(False)
        center_layout.addWidget(self.grid_view)

        main_splitter.addWidget(center_panel)

        # === RIGHT PANEL: File Preview ===
        self.preview_panel = FilePreviewPanel()
        self.preview_panel.setMinimumWidth(250)
        self.preview_panel.setMaximumWidth(400)
        main_splitter.addWidget(self.preview_panel)

        # Set splitter proportions
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 4)
        main_splitter.setStretchFactor(2, 1)

        main_layout.addWidget(main_splitter)

        # Bottom action bar
        action_layout = self._create_enhanced_action_bar()
        main_layout.addLayout(action_layout)

        # Status bar with progress
        from PyQt6.QtWidgets import QProgressBar
        self.status_bar = self.statusBar()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(300)
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.status_bar.showMessage("Ready - Press F1 for keyboard shortcuts")

    def _create_menu_bar(self):
        """Create menu bar with actions"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        export_action = QAction("&Export Results...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._export_results)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Search menu
        search_menu = menubar.addMenu("&Search")

        new_search_action = QAction("&New Search", self)
        new_search_action.setShortcut("Ctrl+N")
        new_search_action.triggered.connect(lambda: self.search_input.setFocus())
        search_menu.addAction(new_search_action)

        save_preset_action = QAction("&Save as Preset...", self)
        save_preset_action.setShortcut("Ctrl+S")
        save_preset_action.triggered.connect(self._save_current_as_preset)
        search_menu.addAction(save_preset_action)

        load_preset_action = QAction("&Load Preset...", self)
        load_preset_action.setShortcut("Ctrl+P")
        load_preset_action.triggered.connect(self._show_presets_dialog)
        search_menu.addAction(load_preset_action)

        search_menu.addSeparator()

        clear_history_action = QAction("Clear &History", self)
        clear_history_action.triggered.connect(self.search_history.clear_history)
        search_menu.addAction(clear_history_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        list_view_action = QAction("&List View", self)
        list_view_action.setShortcut("Ctrl+1")
        list_view_action.triggered.connect(lambda: self._set_view_mode("list"))
        view_menu.addAction(list_view_action)

        grid_view_action = QAction("&Grid View", self)
        grid_view_action.setShortcut("Ctrl+2")
        grid_view_action.triggered.connect(lambda: self._set_view_mode("grid"))
        view_menu.addAction(grid_view_action)

        view_menu.addSeparator()

        toggle_preview_action = QAction("Toggle &Preview Panel", self)
        toggle_preview_action.setShortcut("Ctrl+T")
        toggle_preview_action.triggered.connect(self._toggle_preview_panel)
        view_menu.addAction(toggle_preview_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.setShortcut("F1")
        shortcuts_action.triggered.connect(self._show_shortcuts_help)
        help_menu.addAction(shortcuts_action)

        help_menu.addSeparator()

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_enhanced_search_bar(self) -> QWidget:
        """Create search bar with quick filters"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # First row: Search controls
        search_row = QHBoxLayout()

        search_label = QLabel("Search:")
        search_row.addWidget(search_label)

        # Search input with autocomplete
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter filename, pattern, or leave empty for all files...")
        self.search_input.returnPressed.connect(self._start_search)

        # Setup autocomplete from history
        from PyQt6.QtWidgets import QCompleter
        self.search_completer = QCompleter()
        self.search_input.setCompleter(self.search_completer)
        search_row.addWidget(self.search_input, stretch=3)

        # Case sensitive checkbox
        from PyQt6.QtWidgets import QCheckBox
        self.case_sensitive_cb = QCheckBox("Case Sensitive")
        search_row.addWidget(self.case_sensitive_cb)

        # Search button
        self.search_btn = QPushButton("Search")
        self.search_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogContentsView))
        self.search_btn.clicked.connect(self._start_search)
        AccessibleTooltip.set_tooltip(self.search_btn, "Start file search", "Enter")
        search_row.addWidget(self.search_btn)

        # Stop button
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_BrowserStop))
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_search)
        AccessibleTooltip.set_tooltip(self.stop_btn, "Stop current search", "Esc")
        search_row.addWidget(self.stop_btn)

        # Theme toggle
        self.theme_btn = QPushButton("Dark Mode")
        self.theme_btn.setCheckable(True)
        self.theme_btn.clicked.connect(self._toggle_theme)
        search_row.addWidget(self.theme_btn)

        layout.addLayout(search_row)

        # Second row: Quick filter chips
        self.filter_chips = QuickFilterChips()
        self.filter_chips.filter_changed.connect(self._on_filter_changed)
        layout.addWidget(self.filter_chips)

        return container

    def _create_enhanced_action_bar(self) -> QHBoxLayout:
        """Create action bar with enhanced buttons"""
        layout = QHBoxLayout()

        # File count label
        self.file_count_label = QLabel("Files: 0")
        self.file_count_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.file_count_label)

        layout.addStretch()

        # Action buttons
        self.open_btn = QPushButton("Open")
        self.open_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
        self.open_btn.clicked.connect(self._open_files)
        self.open_btn.setEnabled(False)
        AccessibleTooltip.set_tooltip(self.open_btn, "Open selected files", "Ctrl+O")
        layout.addWidget(self.open_btn)

        self.open_location_btn = QPushButton("Open Location")
        self.open_location_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon))
        self.open_location_btn.clicked.connect(self._open_location)
        self.open_location_btn.setEnabled(False)
        AccessibleTooltip.set_tooltip(self.open_location_btn, "Open file location in Explorer")
        layout.addWidget(self.open_location_btn)

        self.copy_btn = QPushButton("Copy To...")
        self.copy_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogDetailedView))
        self.copy_btn.clicked.connect(self._copy_files)
        self.copy_btn.setEnabled(False)
        AccessibleTooltip.set_tooltip(self.copy_btn, "Copy files to directory", "Ctrl+Shift+C")
        layout.addWidget(self.copy_btn)

        self.move_btn = QPushButton("Move To...")
        self.move_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogDetailedView))
        self.move_btn.clicked.connect(self._move_files)
        self.move_btn.setEnabled(False)
        AccessibleTooltip.set_tooltip(self.move_btn, "Move files to directory", "Ctrl+M")
        layout.addWidget(self.move_btn)

        # NEW: Export button
        self.export_btn = QPushButton("Export CSV")
        self.export_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogSaveButton))
        self.export_btn.clicked.connect(self._export_results)
        AccessibleTooltip.set_tooltip(self.export_btn, "Export results to CSV file", "Ctrl+E")
        layout.addWidget(self.export_btn)

        # NEW: Presets button
        self.presets_btn = QPushButton("Presets")
        self.presets_btn.clicked.connect(self._show_presets_dialog)
        AccessibleTooltip.set_tooltip(self.presets_btn, "Manage search presets", "Ctrl+P")
        layout.addWidget(self.presets_btn)

        self.clear_btn = QPushButton("Clear Results")
        self.clear_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_TrashIcon))
        self.clear_btn.clicked.connect(self._clear_results)
        AccessibleTooltip.set_tooltip(self.clear_btn, "Clear all results", "Ctrl+L")
        layout.addWidget(self.clear_btn)

        return layout

    def _setup_enhanced_shortcuts(self):
        """Setup enhanced keyboard shortcuts"""
        # Call parent shortcuts
        super()._setup_shortcuts()

        # Export: Ctrl+E (already in menu)
        # Help: F1 (already in menu)
        # View toggle: Ctrl+1, Ctrl+2 (already in menu)

        # Stop search: Esc
        stop_shortcut = QKeySequence("Esc")
        stop_action = QAction(self)
        stop_action.setShortcut(stop_shortcut)
        stop_action.triggered.connect(self._stop_search)
        self.addAction(stop_action)

    def _populate_directory_tree(self):
        """Populate directory tree with common locations"""
        common_paths = [
            ("C:\\", "System Drive"),
            (os.path.expanduser("~"), "User Home"),
            (os.path.join(os.path.expanduser("~"), "Desktop"), "Desktop"),
            (os.path.join(os.path.expanduser("~"), "Documents"), "Documents"),
            (os.path.join(os.path.expanduser("~"), "Downloads"), "Downloads"),
            (os.path.join(os.path.expanduser("~"), "Pictures"), "Pictures"),
            (os.path.join(os.path.expanduser("~"), "Videos"), "Videos"),
            (os.path.join(os.path.expanduser("~"), "Music"), "Music"),
        ]

        from PyQt6.QtWidgets import QTreeWidgetItem

        for path, label in common_paths:
            if os.path.exists(path):
                item = QTreeWidgetItem([label])
                item.setCheckState(0, Qt.CheckState.Unchecked)
                item.setData(0, Qt.ItemDataRole.UserRole, path)
                item.setToolTip(0, path)
                self.dir_tree.addTopLevelItem(item)

                # Add immediate subdirectories
                try:
                    for subdir in sorted(os.listdir(path))[:10]:  # Limit to first 10
                        subpath = os.path.join(path, subdir)
                        if os.path.isdir(subpath) and not subdir.startswith('.'):
                            child = QTreeWidgetItem([subdir])
                            child.setCheckState(0, Qt.CheckState.Unchecked)
                            child.setData(0, Qt.ItemDataRole.UserRole, subpath)
                            child.setToolTip(0, subpath)
                            item.addChild(child)
                except (PermissionError, FileNotFoundError):
                    pass

    # ========================================
    # ENHANCED FUNCTIONALITY
    # ========================================

    def _on_filter_changed(self, extensions: List[str]):
        """Handle quick filter change"""
        self.current_filter = extensions
        # Would need to re-filter results or restart search
        show_notification(self, f"Filter applied: {len(extensions)} extensions" if extensions else "All files")

    def _load_search_from_history(self, term: str, paths: List[str]):
        """Load search from history"""
        self.search_input.setText(term)
        # TODO: Set directory tree selection based on paths
        show_notification(self, f"Loaded: {term}")

    def _set_view_mode(self, mode: str):
        """Toggle between list and grid view"""
        self.view_mode = mode

        if mode == "list":
            self.results_tabs.setVisible(True)
            self.grid_view.setVisible(False)
            self.list_view_btn.setChecked(True)
            self.grid_view_btn.setChecked(False)
        else:
            self.results_tabs.setVisible(False)
            self.grid_view.setVisible(True)
            self.list_view_btn.setChecked(False)
            self.grid_view_btn.setChecked(True)
            # Sync grid view with current results
            self._sync_grid_view()

    def _sync_grid_view(self):
        """Sync grid view with table results"""
        self.grid_view.clear()
        # Add all results from all tabs
        for table in self.result_tables.values():
            for row in range(table.rowCount()):
                file_info = {
                    'name': table.item(row, 0).text(),
                    'path': table.item(row, 0).data(Qt.ItemDataRole.UserRole),
                    'size': table.item(row, 2).data(Qt.ItemDataRole.UserRole),
                    'modified': table.item(row, 3).data(Qt.ItemDataRole.UserRole),
                }
                self.grid_view.add_item(file_info)

    def _on_selection_changed(self):
        """Handle selection change in table"""
        # Update button states
        super()._update_button_states()

        # Update preview panel
        table = self._get_current_table()
        if table:
            files = table.get_selected_files()
            if files:
                self.preview_panel.preview_file(files[0])
            else:
                self.preview_panel.clear()

    def _on_grid_item_selected(self, path: str):
        """Handle grid item selection"""
        self.preview_panel.preview_file(path)

    def _open_file_from_path(self, path: str):
        """Open file from path"""
        try:
            os.startfile(path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open file:\n{str(e)}")

    def _export_results(self):
        """Export results to CSV"""
        results = []

        # Collect all results from all tabs
        for table in self.result_tables.values():
            for row in range(table.rowCount()):
                results.append({
                    'name': table.item(row, 0).text(),
                    'path': table.item(row, 1).text(),
                    'size': table.item(row, 2).data(Qt.ItemDataRole.UserRole),
                    'modified': table.item(row, 3).data(Qt.ItemDataRole.UserRole),
                })

        if results:
            dialog = ExportDialog(results, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                show_notification(self, "Results exported successfully")
        else:
            QMessageBox.warning(self, "No Results", "No results to export")

    def _save_current_as_preset(self):
        """Save current search configuration as preset"""
        name, ok = QInputDialog.getText(
            self, "Save Preset",
            "Enter preset name:"
        )

        if ok and name:
            preset = SearchPreset(
                name=name,
                search_term=self.search_input.text(),
                paths=self.dir_tree.get_selected_paths(),
                case_sensitive=self.case_sensitive_cb.isChecked(),
                file_types=self.current_filter
            )
            self.presets_dialog.add_preset(preset)
            show_notification(self, f"Preset '{name}' saved")

    def _show_presets_dialog(self):
        """Show presets management dialog"""
        if self.presets_dialog.exec() == QDialog.DialogCode.Accepted:
            if self.presets_dialog.selected_preset:
                self._load_preset(self.presets_dialog.selected_preset)

    def _load_preset(self, preset: SearchPreset):
        """Load a search preset"""
        self.search_input.setText(preset.search_term)
        self.case_sensitive_cb.setChecked(preset.case_sensitive)
        # TODO: Set directory tree paths
        # TODO: Set file type filter

        show_notification(self, f"Loaded preset: {preset.name}")

    def _toggle_preview_panel(self):
        """Toggle preview panel visibility"""
        self.preview_panel.setVisible(not self.preview_panel.isVisible())

    def _show_shortcuts_help(self):
        """Show keyboard shortcuts dialog"""
        KeyboardShortcutsDialog(self).exec()

    def _show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>Smart Search - Enhanced Edition</h2>
        <p>Version 2.0</p>
        <p>Modern Windows file search tool with advanced filtering and UX improvements.</p>
        <br>
        <p><b>Features:</b></p>
        <ul>
            <li>Fast multi-threaded search</li>
            <li>Smart categorization by file type</li>
            <li>Search history and presets</li>
            <li>File preview with thumbnails</li>
            <li>Grid and list views</li>
            <li>Export to CSV</li>
            <li>Full keyboard navigation</li>
        </ul>
        <br>
        <p>Press F1 for keyboard shortcuts</p>
        """
        QMessageBox.about(self, "About Smart Search", about_text)

    # Override search finished to add to history
    def _on_search_finished(self, total_files: int):
        """Handle search completion with notification"""
        super()._on_search_finished(total_files)

        # Add to history
        search_term = self.search_input.text().strip()
        paths = self.dir_tree.get_selected_paths()
        self.search_history.add_search(search_term, paths, total_files)

        # Update autocomplete
        from PyQt6.QtCore import QStringListModel
        model = QStringListModel(self.search_history.get_terms())
        self.search_completer.setModel(model)

        # Show notification
        show_notification(self, f"Search complete: {total_files} files found")


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Smart Search Enhanced")
    app.setOrganizationName("SmartTools")

    # Set application font
    font = QFont("Segoe UI", 9)
    app.setFont(font)

    window = EnhancedSmartSearchWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
