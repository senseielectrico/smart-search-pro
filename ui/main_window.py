"""
Main Window - Tabbed interface with modern layout
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QMenuBar, QMenu, QToolBar, QStatusBar, QLabel,
    QMessageBox, QFileDialog, QApplication, QDialog
)
from PyQt6.QtCore import Qt, QSettings, QSize, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QCloseEvent

from .search_panel import SearchPanel
from .results_panel import ResultsPanel
from .preview_panel import PreviewPanel
from .directory_tree import DirectoryTree
from .duplicates_panel import DuplicatesPanel
from .operations_panel import OperationsPanel
from .settings_dialog import SettingsDialog
from .export_dialog import ExportDialog
from .themes import ThemeManager, Theme, get_theme_manager
from .hotkeys_dialog import HotkeysDialog
from .result_batcher import AdaptiveBatcher

# Advanced UI components - with safe imports
try:
    from .vault_panel import VaultPanel
    from .vault_unlock_dialog import VaultUnlockDialog
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False

try:
    from .archive_panel import ArchivePanel
    from .extract_dialog import ExtractDialog
    ARCHIVE_AVAILABLE = True
except ImportError:
    ARCHIVE_AVAILABLE = False

try:
    from .notepad_panel import NotepadPanel
    from .quick_note_dialog import QuickNoteDialog
    from notes import NoteManager
    from core.database import Database as NotesDatabase
    NOTES_AVAILABLE = True
except ImportError:
    NOTES_AVAILABLE = False
    NoteManager = None
    NotesDatabase = None

try:
    from .saved_searches_panel import SavedSearchesPanel
    from .favorites_panel import FavoritesPanel
    from .save_search_dialog import SaveSearchDialog
    SAVED_SEARCHES_AVAILABLE = True
except ImportError:
    SAVED_SEARCHES_AVAILABLE = False

try:
    from .iphone_view_panel import iPhoneViewPanel
    IPHONE_VIEW_AVAILABLE = True
except ImportError:
    IPHONE_VIEW_AVAILABLE = False

try:
    from .batch_rename_dialog import BatchRenameDialog
    BATCH_RENAME_AVAILABLE = True
except ImportError:
    BATCH_RENAME_AVAILABLE = False

try:
    from .comparison_panel import ComparisonPanel
    COMPARISON_AVAILABLE = True
except ImportError:
    COMPARISON_AVAILABLE = False

try:
    from .database_panel import DatabasePanel
    DATABASE_PANEL_AVAILABLE = True
except ImportError:
    DATABASE_PANEL_AVAILABLE = False

try:
    from .file_unlocker_dialog import FileUnlockerDialog
    from .permission_dialog import PermissionDialog
    FILE_TOOLS_AVAILABLE = True
except ImportError:
    FILE_TOOLS_AVAILABLE = False

# Import backend modules
try:
    from operations import OperationsManager, FileCopier, FileMover
    OPERATIONS_BACKEND_AVAILABLE = True
except ImportError:
    OPERATIONS_BACKEND_AVAILABLE = False

try:
    from duplicates import DuplicateScanner, FileHasher
    DUPLICATES_BACKEND_AVAILABLE = True
except ImportError:
    DUPLICATES_BACKEND_AVAILABLE = False

try:
    from archive import SevenZipManager
    ARCHIVE_BACKEND_AVAILABLE = True
except ImportError:
    ARCHIVE_BACKEND_AVAILABLE = False

try:
    from vault import SecureVault
    VAULT_BACKEND_AVAILABLE = True
except ImportError:
    VAULT_BACKEND_AVAILABLE = False

try:
    from search.saved_searches import SavedSearchManager
    SAVED_SEARCHES_BACKEND_AVAILABLE = True
except ImportError:
    SAVED_SEARCHES_BACKEND_AVAILABLE = False

# Import hotkey system
import sys
if 'system' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from system.hotkeys import HotkeyManager, ModifierKeys, VirtualKeys


class SearchWorker(QThread):
    """Worker thread for async search operations"""

    # Signals
    results_ready = pyqtSignal(list)  # Search results
    progress_update = pyqtSignal(int, int)  # Current, total
    search_complete = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, search_engine, parent=None):
        super().__init__(parent)
        self.search_engine = search_engine
        self.params = None
        self.is_cancelled = False

    def set_params(self, params: Dict):
        """Set search parameters"""
        self.params = params
        self.is_cancelled = False

    def run(self):
        """Execute search in background thread"""
        if not self.params:
            return

        try:
            query = self.params.get('query', '')
            if not query:
                self.search_complete.emit()
                return

            # Use actual search engine if available
            if self.search_engine:
                try:
                    results = self.search_engine.search(
                        query=query,
                        max_results=self.params.get('max_results', 1000),
                        sort_by=self.params.get('sort_by', 'name'),
                        ascending=self.params.get('ascending', True),
                        progress_callback=self._on_progress
                    )

                    if not self.is_cancelled:
                        self.results_ready.emit(results)

                except Exception as e:
                    if not self.is_cancelled:
                        self.error_occurred.emit(f"Search engine error: {str(e)}")
            else:
                # Mock implementation for testing without search engine
                import time
                mock_results = []
                for i in range(10):
                    if self.is_cancelled:
                        break
                    time.sleep(0.01)
                    self.progress_update.emit(i + 1, 10)

                if not self.is_cancelled:
                    self.results_ready.emit(mock_results)

        except Exception as e:
            if not self.is_cancelled:
                self.error_occurred.emit(str(e))
        finally:
            if not self.is_cancelled:
                self.search_complete.emit()

    def _on_progress(self, current: int, total: int):
        """Handle progress callback from search engine"""
        if not self.is_cancelled:
            self.progress_update.emit(current, total)

    def cancel(self):
        """Cancel search operation"""
        self.is_cancelled = True
        if self.search_engine:
            try:
                self.search_engine.cancel()
            except:
                pass


class MainWindow(QMainWindow):
    """Main application window"""

    # Signals
    search_started = pyqtSignal(dict)
    operation_started = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()

        # Settings
        self.settings = QSettings("SmartSearch", "MainWindow")

        # Theme manager
        self.theme_manager = get_theme_manager()

        # Hotkey manager
        self.hotkey_manager = HotkeyManager()

        # State
        self.current_search_params: Optional[Dict] = None
        self.search_worker = None
        self.search_engine = None  # Will be initialized with actual search engine

        # Initialize search worker
        self.search_worker = SearchWorker(self.search_engine, self)
        self.search_worker.results_ready.connect(self._on_search_results)
        self.search_worker.progress_update.connect(self._on_search_progress)
        self.search_worker.search_complete.connect(self._on_search_complete)
        self.search_worker.error_occurred.connect(self._on_search_error)

        # Initialize result batcher for high-performance UI updates
        # AdaptiveBatcher auto-adjusts batch size to maintain 60fps
        self.result_batcher = AdaptiveBatcher(self)
        self.result_batcher.batch_ready.connect(self._on_batch_ready)
        self.result_batcher.all_flushed.connect(self._on_all_results_flushed)

        # Initialize operations manager for TeraCopy-style operations
        self.operations_manager = None
        if OPERATIONS_BACKEND_AVAILABLE:
            try:
                self.operations_manager = OperationsManager(
                    max_concurrent_operations=2,
                    auto_save_history=True
                )
            except Exception as e:
                import logging
                logging.warning(f"Failed to initialize OperationsManager: {e}")

        self._init_ui()
        self._create_menus()
        self._create_toolbar()
        self._create_statusbar()
        self._setup_shortcuts()
        self._setup_hotkeys()
        self._connect_signals()
        self._apply_theme()
        self._restore_geometry()

    def _init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("Smart Search Pro")
        self.setMinimumSize(1200, 700)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Search panel at top
        self.search_panel = SearchPanel()
        main_layout.addWidget(self.search_panel)

        # Main content area - horizontal splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Directory tree
        self.directory_tree = DirectoryTree()
        main_splitter.addWidget(self.directory_tree)

        # Center panel - Tabbed results
        self.results_tabs = QTabWidget()
        self.results_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.results_tabs.setMovable(True)
        self.results_tabs.setTabsClosable(True)
        self.results_tabs.tabCloseRequested.connect(self._close_result_tab)

        # Create default tabs
        self.results_panel = ResultsPanel()
        self.duplicates_panel = DuplicatesPanel()
        self.operations_panel = OperationsPanel()

        self.results_tabs.addTab(self.results_panel, "🔍 Search Results")
        self.results_tabs.addTab(self.duplicates_panel, "📋 Duplicates")
        self.results_tabs.addTab(self.operations_panel, "⚙ Operations")

        # Add Archive tab if available
        if ARCHIVE_AVAILABLE:
            self.archive_panel = ArchivePanel()
            self.results_tabs.addTab(self.archive_panel, "📦 Archives")
        else:
            self.archive_panel = None

        # Add Notes tab if available
        if NOTES_AVAILABLE:
            try:
                from pathlib import Path
                notes_db_path = Path.home() / ".smart_search" / "notes.db"
                notes_db_path.parent.mkdir(parents=True, exist_ok=True)
                self.notes_db = NotesDatabase(notes_db_path)
                self.note_manager = NoteManager(self.notes_db)
                self.notes_panel = NotepadPanel(self.note_manager)
                self.results_tabs.addTab(self.notes_panel, "📝 Notes")
            except Exception as e:
                import logging
                logging.warning(f"Failed to initialize notes panel: {e}")
                self.notes_panel = None
                self.note_manager = None
                self.notes_db = None
        else:
            self.notes_panel = None
            self.note_manager = None
            self.notes_db = None

        # Add iPhone View tab if available  
        if IPHONE_VIEW_AVAILABLE:
            self.iphone_panel = iPhoneViewPanel()
            self.results_tabs.addTab(self.iphone_panel, "📱 iPhone View")
        else:
            self.iphone_panel = None

        # Add Comparison tab if available
        if COMPARISON_AVAILABLE:
            self.comparison_panel = ComparisonPanel()
            self.results_tabs.addTab(self.comparison_panel, "📊 Comparison")
        else:
            self.comparison_panel = None

        # Add Database tab if available
        if DATABASE_PANEL_AVAILABLE:
            self.database_panel = DatabasePanel()
            self.results_tabs.addTab(self.database_panel, "🗄 Database")
        else:
            self.database_panel = None

        main_splitter.addWidget(self.results_tabs)

        # Right panel - Preview
        self.preview_panel = PreviewPanel()
        self.preview_panel.setMaximumWidth(400)
        main_splitter.addWidget(self.preview_panel)

        # Set splitter proportions
        main_splitter.setStretchFactor(0, 1)  # Tree
        main_splitter.setStretchFactor(1, 3)  # Results
        main_splitter.setStretchFactor(2, 1)  # Preview

        main_layout.addWidget(main_splitter)

    def _create_menus(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_search_action = QAction("&New Search Tab", self)
        new_search_action.setShortcut(QKeySequence("Ctrl+T"))
        new_search_action.triggered.connect(self._new_search_tab)
        file_menu.addAction(new_search_action)

        file_menu.addSeparator()

        # Export submenu
        export_menu = file_menu.addMenu("&Export")

        export_all_action = QAction("Export &All Results...", self)
        export_all_action.setShortcut(QKeySequence("Ctrl+E"))
        export_all_action.triggered.connect(self._export_results)
        export_menu.addAction(export_all_action)

        export_selected_action = QAction("Export &Selected...", self)
        export_selected_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        export_selected_action.triggered.connect(self._export_selected)
        export_menu.addAction(export_selected_action)

        export_menu.addSeparator()

        export_csv_action = QAction("Quick Export to C&SV...", self)
        export_csv_action.triggered.connect(self._quick_export_csv)
        export_menu.addAction(export_csv_action)

        export_clipboard_action = QAction("Copy to &Clipboard", self)
        export_clipboard_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        export_clipboard_action.triggered.connect(self._export_to_clipboard)
        export_menu.addAction(export_clipboard_action)

        file_menu.addSeparator()

        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self._show_settings)
        file_menu.addAction(settings_action)

        hotkeys_action = QAction("&Keyboard Shortcuts...", self)
        hotkeys_action.setShortcut(QKeySequence("Ctrl+K"))
        hotkeys_action.triggered.connect(self._show_hotkeys_dialog)
        file_menu.addAction(hotkeys_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        select_all_action = QAction("Select &All", self)
        select_all_action.setShortcut(QKeySequence("Ctrl+A"))
        select_all_action.triggered.connect(self._select_all_results)
        edit_menu.addAction(select_all_action)

        clear_action = QAction("&Clear Results", self)
        clear_action.setShortcut(QKeySequence("Ctrl+L"))
        clear_action.triggered.connect(self._clear_results)
        edit_menu.addAction(clear_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        self.toggle_tree_action = QAction("Show &Directory Tree", self)
        self.toggle_tree_action.setCheckable(True)
        self.toggle_tree_action.setChecked(True)
        self.toggle_tree_action.triggered.connect(self._toggle_directory_tree)
        view_menu.addAction(self.toggle_tree_action)

        self.toggle_preview_action = QAction("Show &Preview Panel", self)
        self.toggle_preview_action.setCheckable(True)
        self.toggle_preview_action.setChecked(True)
        self.toggle_preview_action.triggered.connect(self._toggle_preview_panel)
        view_menu.addAction(self.toggle_preview_action)

        view_menu.addSeparator()

        # View modes submenu
        view_modes_menu = view_menu.addMenu("View &Mode")

        results_view_action = QAction("🔍 &Results View", self)
        results_view_action.triggered.connect(lambda: self.results_tabs.setCurrentIndex(0))
        view_modes_menu.addAction(results_view_action)

        duplicates_view_action = QAction("📋 &Duplicates View", self)
        duplicates_view_action.triggered.connect(lambda: self.results_tabs.setCurrentIndex(1))
        view_modes_menu.addAction(duplicates_view_action)

        operations_view_action = QAction("⚙ &Operations View", self)
        operations_view_action.triggered.connect(lambda: self.results_tabs.setCurrentIndex(2))
        view_modes_menu.addAction(operations_view_action)

        if IPHONE_VIEW_AVAILABLE:
            iphone_view_action = QAction("📱 &iPhone View", self)
            iphone_view_action.triggered.connect(self._show_iphone_view)
            view_modes_menu.addAction(iphone_view_action)

        if NOTES_AVAILABLE:
            notes_view_action = QAction("📝 &Notes View", self)
            notes_view_action.triggered.connect(self._show_notes_panel)
            view_modes_menu.addAction(notes_view_action)

        view_menu.addSeparator()

        # Saved searches panel toggle
        if SAVED_SEARCHES_AVAILABLE:
            self.toggle_saved_searches_action = QAction("Show &Saved Searches", self)
            self.toggle_saved_searches_action.setCheckable(True)
            self.toggle_saved_searches_action.triggered.connect(self._toggle_saved_searches)
            view_menu.addAction(self.toggle_saved_searches_action)

            self.toggle_favorites_action = QAction("Show &Favorites", self)
            self.toggle_favorites_action.setCheckable(True)
            self.toggle_favorites_action.triggered.connect(self._toggle_favorites)
            view_menu.addAction(self.toggle_favorites_action)

            view_menu.addSeparator()

        dark_mode_action = QAction("&Dark Mode", self)
        dark_mode_action.setCheckable(True)
        dark_mode_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(dark_mode_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        find_duplicates_action = QAction("Find &Duplicates...", self)
        find_duplicates_action.setShortcut(QKeySequence("Ctrl+Shift+D"))
        find_duplicates_action.triggered.connect(self._find_duplicates)
        tools_menu.addAction(find_duplicates_action)

        tools_menu.addSeparator()

        # Batch Rename
        batch_rename_action = QAction("&Batch Rename...", self)
        batch_rename_action.setShortcut(QKeySequence("Ctrl+R"))
        batch_rename_action.setEnabled(BATCH_RENAME_AVAILABLE)
        if BATCH_RENAME_AVAILABLE:
            batch_rename_action.triggered.connect(self._show_batch_rename)
        tools_menu.addAction(batch_rename_action)

        # Folder Comparison
        comparison_action = QAction("Folder &Comparison...", self)
        comparison_action.setEnabled(COMPARISON_AVAILABLE)
        if COMPARISON_AVAILABLE:
            comparison_action.triggered.connect(self._show_comparison)
        tools_menu.addAction(comparison_action)

        tools_menu.addSeparator()

        # Archive submenu
        archive_menu = tools_menu.addMenu("&Archive")
        
        extract_action = QAction("&Extract Archive...", self)
        extract_action.setShortcut(QKeySequence("Ctrl+Shift+X"))
        extract_action.setEnabled(ARCHIVE_AVAILABLE)
        if ARCHIVE_AVAILABLE:
            extract_action.triggered.connect(self._show_extract_dialog)
        archive_menu.addAction(extract_action)

        create_archive_action = QAction("&Create Archive...", self)
        create_archive_action.setEnabled(ARCHIVE_AVAILABLE)
        if ARCHIVE_AVAILABLE:
            create_archive_action.triggered.connect(self._create_archive)
        archive_menu.addAction(create_archive_action)

        tools_menu.addSeparator()

        # File Tools submenu
        file_tools_menu = tools_menu.addMenu("File &Tools")

        unlocker_action = QAction("&File Unlocker...", self)
        unlocker_action.setEnabled(FILE_TOOLS_AVAILABLE)
        if FILE_TOOLS_AVAILABLE:
            unlocker_action.triggered.connect(self._show_file_unlocker)
        file_tools_menu.addAction(unlocker_action)

        permissions_action = QAction("&Fix Permissions...", self)
        permissions_action.setEnabled(FILE_TOOLS_AVAILABLE)
        if FILE_TOOLS_AVAILABLE:
            permissions_action.triggered.connect(self._show_permissions_dialog)
        file_tools_menu.addAction(permissions_action)

        tools_menu.addSeparator()

        # Database Viewer
        db_viewer_action = QAction("&Database Viewer...", self)
        db_viewer_action.setEnabled(DATABASE_PANEL_AVAILABLE)
        if DATABASE_PANEL_AVAILABLE:
            db_viewer_action.triggered.connect(self._show_database_viewer)
        tools_menu.addAction(db_viewer_action)

        # Notes menu
        notes_menu = menubar.addMenu("&Notes")

        new_note_action = QAction("&New Note...", self)
        new_note_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        new_note_action.setEnabled(NOTES_AVAILABLE)
        if NOTES_AVAILABLE:
            new_note_action.triggered.connect(self._new_quick_note)
        notes_menu.addAction(new_note_action)

        view_notes_action = QAction("&View Notes", self)
        view_notes_action.setEnabled(NOTES_AVAILABLE)
        if NOTES_AVAILABLE:
            view_notes_action.triggered.connect(self._show_notes_panel)
        notes_menu.addAction(view_notes_action)

        # Vault menu (hidden - access via Ctrl+Shift+V)
        # The vault is accessed via hotkey, not visible menu

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        help_action = QAction("&Help", self)
        help_action.setShortcut(QKeySequence("F1"))
        help_action.triggered.connect(self._show_help)
        help_menu.addAction(help_action)

    def _create_toolbar(self):
        """Create toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Add common actions
        # Note: In a real implementation, use proper icons
        toolbar.addAction("🔍", self._focus_search)
        toolbar.addSeparator()
        toolbar.addAction("📂", self._open_files)
        toolbar.addAction("📍", self._open_location)
        toolbar.addSeparator()
        toolbar.addAction("📋", self._copy_files)
        toolbar.addAction("✂", self._move_files)
        toolbar.addAction("🗑", self._delete_files)
        toolbar.addSeparator()
        toolbar.addAction("💾", self._export_results)
        toolbar.addAction("📄", self._export_to_clipboard)

    def _create_statusbar(self):
        """Create status bar"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # Status message
        self.status_label = QLabel("Ready")
        self.statusbar.addWidget(self.status_label, stretch=1)

        # File count
        self.file_count_label = QLabel("0 files")
        self.statusbar.addPermanentWidget(self.file_count_label)

        # Selected count
        self.selected_count_label = QLabel("")
        self.statusbar.addPermanentWidget(self.selected_count_label)

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts - legacy method, now handled by _setup_hotkeys"""
        pass

    def _setup_hotkeys(self):
        """Setup comprehensive keyboard shortcuts system."""
        # Register global hotkey for show/hide
        try:
            self.hotkey_manager.register(
                "toggle_window",
                ModifierKeys.CTRL | ModifierKeys.SHIFT,
                VirtualKeys.letter('F'),
                self._toggle_window_visibility,
                "Show/Hide Smart Search window",
                is_global=True
            )
        except Exception as e:
            import logging
            logging.warning(f"Failed to register global hotkey: {e}")

        # Install Qt event filter for hotkey processing
        self.hotkey_manager.install_qt_filter()

        # Register local application hotkeys (non-global, work when app is focused)

        # Ctrl+F: Focus search
        self.hotkey_manager.register(
            "focus_search",
            ModifierKeys.CTRL,
            VirtualKeys.letter('F'),
            self._focus_search,
            "Focus search input",
            is_global=False
        )

        # Ctrl+N: New search (clear)
        self.hotkey_manager.register(
            "new_search",
            ModifierKeys.CTRL,
            VirtualKeys.letter('N'),
            self._new_search,
            "Clear search and start new",
            is_global=False
        )

        # Ctrl+E: Export results
        self.hotkey_manager.register(
            "export_results",
            ModifierKeys.CTRL,
            VirtualKeys.letter('E'),
            self._export_results,
            "Export search results",
            is_global=False
        )

        # Ctrl+D: Toggle duplicates panel
        self.hotkey_manager.register(
            "toggle_duplicates",
            ModifierKeys.CTRL,
            VirtualKeys.letter('D'),
            self._toggle_duplicates_tab,
            "Show/hide duplicates panel",
            is_global=False
        )

        # F5: Refresh results
        self.hotkey_manager.register(
            "refresh_results",
            0,  # No modifiers
            VirtualKeys.VK_F5,
            self._refresh_results,
            "Refresh search results",
            is_global=False
        )

        # Delete: Move to recycle bin
        self.hotkey_manager.register(
            "delete_selected",
            0,  # No modifiers
            0x2E,  # VK_DELETE
            self._delete_files,
            "Move selected files to recycle bin",
            is_global=False
        )

        # Enter: Open selected file
        self.hotkey_manager.register(
            "open_file",
            0,  # No modifiers
            VirtualKeys.VK_RETURN,
            self._open_files,
            "Open selected file(s)",
            is_global=False
        )

        # Space: Toggle preview panel
        self.hotkey_manager.register(
            "toggle_preview",
            ModifierKeys.CTRL,
            VirtualKeys.VK_SPACE,
            self._toggle_preview_panel_hotkey,
            "Toggle preview panel visibility",
            is_global=False
        )

        # Ctrl+A: Select all
        self.hotkey_manager.register(
            "select_all",
            ModifierKeys.CTRL,
            VirtualKeys.letter('A'),
            self._select_all_results,
            "Select all results",
            is_global=False
        )

        # Esc: Clear selection or close dialog
        self.hotkey_manager.register(
            "escape",
            0,  # No modifiers
            VirtualKeys.VK_ESCAPE,
            self._handle_escape,
            "Clear selection or close dialog",
            is_global=False
        )

        # Ctrl+Shift+V: Open secure vault (hidden feature)
        if VAULT_AVAILABLE:
            self.hotkey_manager.register(
                "open_vault",
                ModifierKeys.CTRL | ModifierKeys.SHIFT,
                VirtualKeys.letter('V'),
                self._show_vault,
                "Open secure vault",
                is_global=False
            )

        # Ctrl+1-9: Execute saved searches
        if SAVED_SEARCHES_BACKEND_AVAILABLE:
            for i in range(1, 10):
                self.hotkey_manager.register(
                    f"saved_search_{i}",
                    ModifierKeys.CTRL,
                    VirtualKeys.number(i),  # 0x31 through 0x39
                    lambda idx=i: self._execute_saved_search(idx),
                    f"Execute saved search #{i}",
                    is_global=False
                )

        # Update UI elements with hotkey hints
        self._update_hotkey_tooltips()

    def _update_hotkey_tooltips(self):
        """Update tooltips to show hotkey hints."""
        # This would be called to update button tooltips with their hotkeys
        hotkeys_info = {
            'focus_search': self.search_panel.search_input if hasattr(self, 'search_panel') else None,
            'export_results': None,  # Would update toolbar buttons
            'toggle_duplicates': None,
            'open_file': None,
        }

        # Update tooltips with hotkey hints
        for name, widget in hotkeys_info.items():
            if widget:
                hotkey_info = self.hotkey_manager.get_hotkey_info(name)
                if hotkey_info:
                    key_str = hotkey_info.get_key_string()
                    current_tooltip = widget.toolTip()
                    if current_tooltip:
                        widget.setToolTip(f"{current_tooltip} ({key_str})")
                    else:
                        widget.setToolTip(f"{hotkey_info.description} ({key_str})")

    def _connect_signals(self):
        """Connect signals between components"""
        # Search panel
        self.search_panel.search_requested.connect(self._perform_search)
        self.search_panel.instant_search_requested.connect(self._perform_instant_search)
        self.search_panel.filter_changed.connect(self._on_filter_changed)

        # Results panel
        self.results_panel.file_selected.connect(self.preview_panel.set_file)
        self.results_panel.files_selected.connect(self._on_files_selected)
        self.results_panel.open_requested.connect(self._open_files_from_list)
        self.results_panel.open_location_requested.connect(self._open_location)
        self.results_panel.copy_requested.connect(self._copy_files_from_list)
        self.results_panel.move_requested.connect(self._move_files_from_list)
        self.results_panel.delete_requested.connect(self._delete_files_from_list)
        self.results_panel.export_requested.connect(self._export_results)
        self.results_panel.export_selected_requested.connect(self._export_selected)

        # Directory tree
        self.directory_tree.selection_changed.connect(self._on_directory_selection_changed)

        # Preview panel
        self.preview_panel.open_requested.connect(lambda p: self._open_files_from_list([p]))
        self.preview_panel.open_location_requested.connect(self._open_location)

        # Operations panel
        self.operations_panel.cancel_requested.connect(self._cancel_operation)
        self.operations_panel.pause_requested.connect(self._pause_operation)
        self.operations_panel.resume_requested.connect(self._resume_operation)

    def _apply_theme(self):
        """Apply current theme"""
        theme = self.settings.value("appearance/theme", "Light", type=str)
        theme_enum = Theme.DARK if theme == "Dark" else Theme.LIGHT

        self.theme_manager.set_theme(theme_enum)

        # Apply stylesheet
        stylesheet = self.theme_manager.get_stylesheet()
        self.setStyleSheet(stylesheet)

        # Apply palette
        palette = self.theme_manager.get_palette()
        QApplication.instance().setPalette(palette)

    def _toggle_theme(self, checked: bool):
        """Toggle between light and dark theme"""
        theme = Theme.DARK if checked else Theme.LIGHT
        self.theme_manager.set_theme(theme)
        self._apply_theme()
        self.settings.setValue("appearance/theme", "Dark" if checked else "Light")

    def _restore_geometry(self):
        """Restore window geometry"""
        if self.settings.value("general/remember_window", True, type=bool):
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)

            state = self.settings.value("windowState")
            if state:
                self.restoreState(state)

    def _save_geometry(self):
        """Save window geometry"""
        if self.settings.value("general/remember_window", True, type=bool):
            self.settings.setValue("geometry", self.saveGeometry())
            self.settings.setValue("windowState", self.saveState())

    def _perform_search(self, params: Dict):
        """Perform file search (triggered by Enter or Search button)"""
        self._execute_search(params, instant=False)

    def _perform_instant_search(self, params: Dict):
        """Perform instant search (triggered by typing)"""
        self._execute_search(params, instant=True)

    def _execute_search(self, params: Dict, instant: bool = False):
        """Execute search with worker thread"""
        self.current_search_params = params

        # Get search paths from directory tree
        search_paths = self.directory_tree.get_selected_paths()

        if not search_paths and not instant:
            QMessageBox.warning(
                self,
                "No Directories Selected",
                "Please select at least one directory to search."
            )
            return

        # Cancel previous search if running
        if self.search_worker.isRunning():
            self.search_worker.cancel()
            self.search_worker.wait()

        # Clear previous results only for explicit searches
        if not instant:
            self.results_panel.clear_results()

        # Update status
        self.status_label.setText("Searching...")

        # Add search paths to params
        params['paths'] = search_paths
        params['instant'] = instant

        # Start search in worker thread
        self.search_worker.set_params(params)
        self.search_worker.start()

        # Emit signal for compatibility
        self.search_started.emit(params)

    @pyqtSlot(list)
    def _on_search_results(self, results: list):
        """Handle search results from worker thread using batched UI updates"""
        if not results:
            self.file_count_label.setText("0 files")
            return

        # Reset and start batcher for high-performance UI updates
        self.result_batcher.reset()
        self.result_batcher.start()

        # Clear existing results and prepare for batched updates
        self.results_panel.clear_results()

        # Add all results to batcher (will be processed in batches)
        self.result_batcher.add_results(results)

        # Flush remaining and finalize
        self.result_batcher.flush()

    @pyqtSlot(list)
    def _on_batch_ready(self, batch: list):
        """Handle a batch of results ready for UI update"""
        # Add batch to results panel (VirtualTableModel handles efficiently)
        if hasattr(self.results_panel, 'add_results'):
            self.results_panel.add_results(batch)

        # Update file count progressively
        total = self.result_batcher.total_emitted
        self.file_count_label.setText(f"{total} files...")

    @pyqtSlot(int)
    def _on_all_results_flushed(self, total_count: int):
        """Handle completion of all batched result updates"""
        self.file_count_label.setText(f"{total_count} files")
        self.result_batcher.stop()

    @pyqtSlot(int, int)
    def _on_search_progress(self, current: int, total: int):
        """Handle search progress updates"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.status_label.setText(f"Searching... {percentage}%")

    @pyqtSlot()
    def _on_search_complete(self):
        """Handle search completion"""
        query = self.current_search_params.get('query', '') if self.current_search_params else ''
        self.status_label.setText(f"Search completed: {query}" if query else "Ready")

        # Notify search panel
        self.search_panel.set_search_complete()

    @pyqtSlot(str)
    def _on_search_error(self, error_msg: str):
        """Handle search errors"""
        self.status_label.setText(f"Search error: {error_msg}")
        QMessageBox.warning(self, "Search Error", f"Search failed:\n{error_msg}")

    def _on_filter_changed(self, filters: Dict):
        """Handle filter change"""
        # Reapply filters to current results
        pass

    def _on_files_selected(self, files: List[str]):
        """Handle file selection change"""
        count = len(files)
        if count > 0:
            self.selected_count_label.setText(f"{count} selected")
        else:
            self.selected_count_label.setText("")

    def _on_directory_selection_changed(self, paths: List[str]):
        """Handle directory selection change"""
        # Could update search button state, etc.
        pass

    def _focus_search(self):
        """Focus search input"""
        self.search_panel.search_input.setFocus()
        self.search_panel.search_input.selectAll()

    def _open_files(self):
        """Open selected files"""
        files = self.results_panel.get_selected_files()
        self._open_files_from_list(files)

    def _open_files_from_list(self, files: List[str]):
        """Open files from list"""
        if not files:
            return

        # Limit to prevent opening too many
        if len(files) > 10:
            reply = QMessageBox.question(
                self,
                "Open Many Files",
                f"Do you want to open {len(files)} files?\nOnly the first 10 will be opened.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            files = files[:10]

        # Open files
        for file_path in files:
            try:
                os.startfile(file_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to open {file_path}:\n{e}")

    def _open_location(self, file_path: str):
        """Open file location in explorer"""
        try:
            directory = str(Path(file_path).parent)
            os.startfile(directory)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open location:\n{e}")

    def _copy_files(self):
        """Copy selected files"""
        files = self.results_panel.get_selected_files()
        self._copy_files_from_list(files)

    def _copy_files_from_list(self, files: List[str]):
        """Copy files from list using TeraCopy-style operations."""
        if not files:
            return

        dest = QFileDialog.getExistingDirectory(self, "Select Destination")
        if not dest:
            return

        if self.operations_manager:
            # Use TeraCopy-style operations manager
            dest_paths = [str(Path(dest) / Path(f).name) for f in files]
            try:
                operation_id = self.operations_manager.queue_copy(
                    source_paths=files,
                    dest_paths=dest_paths,
                    verify=True,  # Enable verification
                    preserve_metadata=True
                )
                self.status_label.setText(f"Copy operation queued: {len(files)} files")
                # Switch to operations panel to show progress
                self.results_tabs.setCurrentWidget(self.operations_panel)
                # Notify operations panel
                if hasattr(self.operations_panel, 'add_operation'):
                    self.operations_panel.add_operation(operation_id, "copy", files, dest)
            except Exception as e:
                QMessageBox.critical(self, "Copy Error", f"Failed to start copy operation:\n{e}")
        else:
            # Fallback: simple shutil copy
            import shutil
            copied = 0
            errors = []
            for f in files:
                try:
                    dest_path = Path(dest) / Path(f).name
                    if Path(f).is_dir():
                        shutil.copytree(f, dest_path)
                    else:
                        shutil.copy2(f, dest_path)
                    copied += 1
                except Exception as e:
                    errors.append(f"{Path(f).name}: {e}")

            if errors:
                QMessageBox.warning(self, "Copy Completed with Errors",
                    f"Copied {copied} files. Errors:\n" + "\n".join(errors[:5]))
            else:
                QMessageBox.information(self, "Copy Complete", f"Copied {copied} files to {dest}")

    def _move_files(self):
        """Move selected files"""
        files = self.results_panel.get_selected_files()
        self._move_files_from_list(files)

    def _move_files_from_list(self, files: List[str]):
        """Move files from list using TeraCopy-style operations."""
        if not files:
            return

        dest = QFileDialog.getExistingDirectory(self, "Select Destination")
        if not dest:
            return

        if self.operations_manager:
            # Use TeraCopy-style operations manager
            dest_paths = [str(Path(dest) / Path(f).name) for f in files]
            try:
                operation_id = self.operations_manager.queue_move(
                    source_paths=files,
                    dest_paths=dest_paths,
                    verify=True,  # Enable verification
                    preserve_metadata=True
                )
                self.status_label.setText(f"Move operation queued: {len(files)} files")
                # Switch to operations panel to show progress
                self.results_tabs.setCurrentWidget(self.operations_panel)
                # Notify operations panel
                if hasattr(self.operations_panel, 'add_operation'):
                    self.operations_panel.add_operation(operation_id, "move", files, dest)
            except Exception as e:
                QMessageBox.critical(self, "Move Error", f"Failed to start move operation:\n{e}")
        else:
            # Fallback: simple shutil move
            import shutil
            moved = 0
            errors = []
            for f in files:
                try:
                    dest_path = Path(dest) / Path(f).name
                    shutil.move(f, dest_path)
                    moved += 1
                except Exception as e:
                    errors.append(f"{Path(f).name}: {e}")

            if errors:
                QMessageBox.warning(self, "Move Completed with Errors",
                    f"Moved {moved} files. Errors:\n" + "\n".join(errors[:5]))
            else:
                QMessageBox.information(self, "Move Complete", f"Moved {moved} files to {dest}")

            # Refresh results
            self._refresh_results()

    def _delete_files(self):
        """Delete selected files"""
        files = self.results_panel.get_selected_files()
        self._delete_files_from_list(files)

    def _delete_files_from_list(self, files: List[str]):
        """Delete files from list (to recycle bin for safety)."""
        if not files:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to move {len(files)} file(s) to the Recycle Bin?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        deleted = 0
        errors = []

        # Try to use send2trash for safe deletion to recycle bin
        try:
            from send2trash import send2trash
            for f in files:
                try:
                    send2trash(f)
                    deleted += 1
                except Exception as e:
                    errors.append(f"{Path(f).name}: {e}")
        except ImportError:
            # Fallback: use Windows API for recycle bin
            try:
                import ctypes
                from ctypes import wintypes

                # Shell32 SHFileOperation for recycle bin
                class SHFILEOPSTRUCT(ctypes.Structure):
                    _fields_ = [
                        ("hwnd", wintypes.HWND),
                        ("wFunc", wintypes.UINT),
                        ("pFrom", wintypes.LPCWSTR),
                        ("pTo", wintypes.LPCWSTR),
                        ("fFlags", wintypes.WORD),
                        ("fAnyOperationsAborted", wintypes.BOOL),
                        ("hNameMappings", ctypes.c_void_p),
                        ("lpszProgressTitle", wintypes.LPCWSTR),
                    ]

                FO_DELETE = 0x0003
                FOF_ALLOWUNDO = 0x0040
                FOF_NOCONFIRMATION = 0x0010
                FOF_SILENT = 0x0004

                for f in files:
                    try:
                        # Create null-terminated double-null path
                        file_op = SHFILEOPSTRUCT()
                        file_op.wFunc = FO_DELETE
                        file_op.pFrom = f + '\0\0'
                        file_op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT

                        result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(file_op))
                        if result == 0:
                            deleted += 1
                        else:
                            errors.append(f"{Path(f).name}: Error code {result}")
                    except Exception as e:
                        errors.append(f"{Path(f).name}: {e}")
            except Exception as e:
                # Last resort: permanent deletion with warning
                perm_reply = QMessageBox.warning(
                    self,
                    "Warning",
                    f"Could not use Recycle Bin. Permanently delete {len(files)} files?\n\nThis cannot be undone!",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if perm_reply == QMessageBox.StandardButton.Yes:
                    for f in files:
                        try:
                            if Path(f).is_dir():
                                import shutil
                                shutil.rmtree(f)
                            else:
                                Path(f).unlink()
                            deleted += 1
                        except Exception as e:
                            errors.append(f"{Path(f).name}: {e}")

        if errors:
            QMessageBox.warning(self, "Delete Completed with Errors",
                f"Deleted {deleted} files. Errors:\n" + "\n".join(errors[:5]))
        else:
            self.status_label.setText(f"Moved {deleted} files to Recycle Bin")

        # Refresh results
        self._refresh_results()

    def _select_all_results(self):
        """Select all results"""
        self.results_panel.select_all()

    def _clear_results(self):
        """Clear all results"""
        self.results_panel.clear_results()
        self.preview_panel.clear()

    def _new_search_tab(self):
        """Create new search tab"""
        # TODO: Implement multi-tab search
        QMessageBox.information(self, "New Tab", "Multi-tab search coming soon!")

    def _close_result_tab(self, index: int):
        """Close result tab"""
        # Don't allow closing main tabs
        if index < 3:
            return

        self.results_tabs.removeTab(index)

    def _export_results(self):
        """Export search results"""
        # Get results from current tab
        current_widget = self.results_tabs.currentWidget()

        if current_widget == self.results_panel:
            results = self.results_panel.get_all_files()
        elif current_widget == self.duplicates_panel:
            # TODO: Get duplicates data
            results = []
        else:
            results = []

        if not results:
            QMessageBox.warning(
                self,
                "No Results",
                "No results to export. Please perform a search first."
            )
            return

        # Show export dialog
        dialog = ExportDialog(results, self)
        dialog.exec()

    def _export_selected(self):
        """Export only selected results"""
        # Get selected files from current tab
        current_widget = self.results_tabs.currentWidget()

        if current_widget == self.results_panel:
            selected_paths = self.results_panel.get_selected_files()
            if not selected_paths:
                QMessageBox.warning(
                    self,
                    "No Selection",
                    "No files selected. Please select files to export or use 'Export All'."
                )
                return

            # Convert paths to full result objects
            all_results = self.results_panel.get_all_files()
            results = [r for r in all_results if r.get('path') in selected_paths or
                      r.get('full_path') in selected_paths or
                      r.get('name') in [Path(p).name for p in selected_paths]]
        else:
            QMessageBox.warning(
                self,
                "Not Supported",
                "Export selected is only available in the Search Results tab."
            )
            return

        if not results:
            QMessageBox.warning(self, "No Results", "No results to export.")
            return

        # Show export dialog
        dialog = ExportDialog(results, self)
        dialog.exec()

    def _quick_export_csv(self):
        """Quick export to CSV with minimal dialog"""
        results = self.results_panel.get_all_files()

        if not results:
            QMessageBox.warning(self, "No Results", "No results to export.")
            return

        # Quick file dialog
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"search_results_{timestamp}.csv"
        default_dir = Path.home() / "Documents"

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export to CSV",
            str(default_dir / default_filename),
            "CSV Files (*.csv);;All Files (*.*)"
        )

        if not filename:
            return

        # Quick export with default settings
        try:
            from export.csv_exporter import CSVExporter
            from export.base import ExportConfig

            config = ExportConfig(
                output_path=Path(filename),
                overwrite=True,
                columns=["filename", "path", "size", "date_modified"],
                include_headers=True,
            )

            exporter = CSVExporter(config)
            stats = exporter.export(results)

            QMessageBox.information(
                self,
                "Export Complete",
                f"Successfully exported {stats.exported_records:,} results to CSV!"
            )

            # Open file
            try:
                os.startfile(filename)
            except:
                pass

        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export:\n{e}")

    def _export_to_clipboard(self):
        """Quick export to clipboard"""
        results = self.results_panel.get_all_files()

        if not results:
            QMessageBox.warning(self, "No Results", "No results to export.")
            return

        try:
            from export.clipboard import ClipboardExporter
            from export.base import ExportConfig

            config = ExportConfig(
                columns=["filename", "path", "size", "date_modified"],
                include_headers=True,
                options={"format": "csv"}
            )

            exporter = ClipboardExporter(config)
            stats = exporter.export(results)

            self.statusbar.showMessage(
                f"Copied {stats.exported_records:,} results to clipboard",
                5000
            )

            QMessageBox.information(
                self,
                "Copied to Clipboard",
                f"{stats.exported_records:,} results copied to clipboard!\n\nYou can now paste in Excel, a text editor, or any application."
            )

        except ImportError as e:
            QMessageBox.warning(
                self,
                "Clipboard Not Available",
                "Clipboard functionality requires pyperclip.\n\nInstall with: pip install pyperclip"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to copy to clipboard:\n{e}")

    def _find_duplicates(self):
        """Find duplicate files using DuplicateScanner backend."""
        # Switch to duplicates panel
        self.results_tabs.setCurrentWidget(self.duplicates_panel)

        # Get search paths from directory tree
        search_paths = self.directory_tree.get_selected_paths()

        if not search_paths:
            QMessageBox.warning(
                self,
                "No Directories Selected",
                "Please select at least one directory to scan for duplicates."
            )
            return

        if not DUPLICATES_BACKEND_AVAILABLE:
            QMessageBox.warning(
                self,
                "Backend Not Available",
                "Duplicate scanner backend is not available."
            )
            return

        # Start duplicate scan in background
        self.status_label.setText("Scanning for duplicates...")

        try:
            from duplicates import DuplicateScanner

            scanner = DuplicateScanner()

            # Define progress callback
            def on_progress(progress):
                self.status_label.setText(f"Scanning for duplicates... {progress:.1f}%")
                QApplication.processEvents()  # Keep UI responsive

            # Scan for duplicates
            groups = scanner.scan(search_paths, progress_callback=on_progress)

            if groups:
                # Update duplicates panel with results
                if hasattr(self.duplicates_panel, 'set_groups'):
                    self.duplicates_panel.set_groups(groups)
                elif hasattr(self.duplicates_panel, 'load_results'):
                    self.duplicates_panel.load_results(groups)

                total_files = sum(len(g.files) for g in groups)
                total_wasted = sum(g.wasted_space for g in groups)
                wasted_str = self._format_size(total_wasted)

                self.status_label.setText(
                    f"Found {len(groups)} duplicate groups ({total_files} files, {wasted_str} wasted)"
                )
            else:
                self.status_label.setText("No duplicate files found")
                QMessageBox.information(
                    self,
                    "Scan Complete",
                    "No duplicate files were found in the selected directories."
                )

        except Exception as e:
            self.status_label.setText("Duplicate scan failed")
            QMessageBox.critical(
                self,
                "Scan Error",
                f"Failed to scan for duplicates:\n{e}"
            )

    def _format_size(self, size: int) -> str:
        """Format file size for display."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def _toggle_directory_tree(self, checked: bool):
        """Toggle directory tree visibility"""
        self.directory_tree.setVisible(checked)

    def _toggle_preview_panel(self, checked: bool):
        """Toggle preview panel visibility"""
        self.preview_panel.setVisible(checked)

    def _show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            self._apply_theme()

    def _show_hotkeys_dialog(self):
        """Show hotkeys configuration dialog."""
        dialog = HotkeysDialog(self.hotkey_manager, self)
        dialog.exec()

    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Smart Search Pro",
            "<h3>Smart Search Pro v1.0</h3>"
            "<p>Modern file search tool with advanced features.</p>"
            "<p>Built with PyQt6</p>"
            "<p>Copyright © 2024</p>"
        )

    def _show_help(self):
        """Show help"""
        QMessageBox.information(
            self,
            "Help",
            "<h3>Quick Start</h3>"
            "<ol>"
            "<li>Select directories to search in the left panel</li>"
            "<li>Enter search term or use advanced search</li>"
            "<li>View results in the center panel</li>"
            "<li>Preview files in the right panel</li>"
            "</ol>"
            "<p>Press F1 for detailed help.</p>"
        )

    def _cancel_operation(self, operation_id: str):
        """Cancel operation"""
        # TODO: Implement operation cancellation
        pass

    def _pause_operation(self, operation_id: str):
        """Pause operation"""
        # TODO: Implement operation pause
        pass

    def _resume_operation(self, operation_id: str):
        """Resume operation"""
        # TODO: Implement operation resume
        pass

    def set_search_engine(self, search_engine):
        """Set the search engine instance"""
        self.search_engine = search_engine
        if self.search_worker:
            self.search_worker.search_engine = search_engine

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event"""
        # Cancel any running search
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.cancel()
            self.search_worker.wait(2000)  # Wait max 2 seconds

        # Check for active operations
        if self.operations_panel.has_active_operations():
            reply = QMessageBox.question(
                self,
                "Active Operations",
                "There are active file operations. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

        # Save geometry
        self._save_geometry()

        # Save hotkey configuration
        self.hotkey_manager.save_config()

        # Cleanup hotkeys
        self.hotkey_manager.cleanup()

        event.accept()

    # Hotkey handler methods
    def _toggle_window_visibility(self):
        """Toggle window visibility (global hotkey)."""
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

            # On Windows, use additional methods to bring to front
            if sys.platform == 'win32':
                try:
                    import ctypes
                    hwnd = int(self.winId())
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
                except Exception:
                    pass

    def _new_search(self):
        """Start a new search (clear current)."""
        self._clear_results()
        self._focus_search()

    def _toggle_duplicates_tab(self):
        """Toggle to duplicates tab."""
        # Find duplicates tab
        for i in range(self.results_tabs.count()):
            if self.results_tabs.tabText(i).startswith("📋"):
                self.results_tabs.setCurrentIndex(i)
                break

    def _refresh_results(self):
        """Refresh current search results."""
        if self.current_search_params:
            self._perform_search(self.current_search_params)

    def _toggle_preview_panel_hotkey(self):
        """Toggle preview panel visibility (hotkey version)."""
        current_state = self.preview_panel.isVisible()
        self.preview_panel.setVisible(not current_state)
        self.toggle_preview_action.setChecked(not current_state)

    def _handle_escape(self):
        """Handle Escape key - clear selection or close dialogs."""
        # Get current focused widget
        focused = QApplication.focusWidget()

        # If a dialog is open, close it
        active_window = QApplication.activeWindow()
        if active_window and active_window != self:
            if isinstance(active_window, QDialog):
                active_window.reject()
                return

        # Otherwise, clear selection in results panel
        current_widget = self.results_tabs.currentWidget()
        if current_widget == self.results_panel:
            self.results_panel.clearSelection()

    # ========== NEW HANDLER METHODS ==========

    def _show_batch_rename(self):
        """Show batch rename dialog for selected files."""
        if not BATCH_RENAME_AVAILABLE:
            QMessageBox.warning(self, "Not Available", "Batch rename feature is not available.")
            return

        files = self.results_panel.get_selected_files()
        if not files:
            QMessageBox.warning(self, "No Selection", "Please select files to rename.")
            return

        dialog = BatchRenameDialog(files, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            renamed = dialog.get_renamed_files()
            self.status_label.setText(f"Renamed {len(renamed)} files")
            self._refresh_results()

    def _show_comparison(self):
        """Show folder comparison panel."""
        if not COMPARISON_AVAILABLE:
            QMessageBox.warning(self, "Not Available", "Folder comparison feature is not available.")
            return

        # Switch to comparison tab
        if self.comparison_panel:
            for i in range(self.results_tabs.count()):
                if self.results_tabs.widget(i) == self.comparison_panel:
                    self.results_tabs.setCurrentIndex(i)
                    return

    def _show_extract_dialog(self):
        """Show archive extraction dialog."""
        if not ARCHIVE_AVAILABLE:
            QMessageBox.warning(self, "Not Available", "Archive features require 7-Zip.")
            return

        files = self.results_panel.get_selected_files()
        archive_files = [f for f in files if self._is_archive(f)]

        if not archive_files:
            # Let user select an archive file
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Select Archive to Extract",
                str(Path.home()),
                "Archives (*.zip *.7z *.rar *.tar *.tar.gz *.tgz *.tar.bz2 *.tar.xz);;All Files (*.*)"
            )
            if filename:
                archive_files = [filename]
            else:
                return

        dialog = ExtractDialog(archive_files, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.status_label.setText("Extraction started...")
            # Operations panel will show progress
            self.results_tabs.setCurrentWidget(self.operations_panel)

    def _is_archive(self, file_path: str) -> bool:
        """Check if file is a supported archive."""
        archive_extensions = {'.zip', '.7z', '.rar', '.tar', '.gz', '.tgz', '.bz2', '.xz'}
        return Path(file_path).suffix.lower() in archive_extensions

    def _create_archive(self):
        """Create new archive from selected files."""
        if not ARCHIVE_AVAILABLE:
            QMessageBox.warning(self, "Not Available", "Archive features require 7-Zip.")
            return

        files = self.results_panel.get_selected_files()
        if not files:
            QMessageBox.warning(self, "No Selection", "Please select files to archive.")
            return

        # Get archive destination
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Create Archive",
            str(Path.home() / "Documents" / "archive.7z"),
            "7-Zip Archive (*.7z);;ZIP Archive (*.zip);;All Files (*.*)"
        )

        if filename:
            try:
                if ARCHIVE_BACKEND_AVAILABLE:
                    manager = SevenZipManager()
                    manager.create_archive(filename, files)
                    QMessageBox.information(self, "Archive Created", f"Archive created successfully:\n{filename}")
                else:
                    QMessageBox.warning(self, "Backend Not Available", "Archive backend module not found.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create archive:\n{e}")

    def _show_file_unlocker(self):
        """Show file unlocker dialog."""
        if not FILE_TOOLS_AVAILABLE:
            QMessageBox.warning(self, "Not Available", "File tools feature is not available.")
            return

        files = self.results_panel.get_selected_files()
        dialog = FileUnlockerDialog(files if files else [], self)
        dialog.exec()

    def _show_permissions_dialog(self):
        """Show file permissions dialog."""
        if not FILE_TOOLS_AVAILABLE:
            QMessageBox.warning(self, "Not Available", "File tools feature is not available.")
            return

        files = self.results_panel.get_selected_files()
        if not files:
            QMessageBox.warning(self, "No Selection", "Please select files to modify permissions.")
            return

        dialog = PermissionDialog(files, self)
        dialog.exec()

    def _show_database_viewer(self):
        """Show database viewer panel."""
        if not DATABASE_PANEL_AVAILABLE:
            QMessageBox.warning(self, "Not Available", "Database viewer feature is not available.")
            return

        # Switch to database tab
        if self.database_panel:
            for i in range(self.results_tabs.count()):
                if self.results_tabs.widget(i) == self.database_panel:
                    self.results_tabs.setCurrentIndex(i)
                    return

    def _new_quick_note(self):
        """Create a new quick note."""
        if not NOTES_AVAILABLE:
            QMessageBox.warning(self, "Not Available", "Notes feature is not available.")
            return

        dialog = QuickNoteDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            note_content = dialog.get_note()
            if self.notes_panel and hasattr(self.notes_panel, 'add_note'):
                self.notes_panel.add_note(note_content)
            self.status_label.setText("Note saved")

    def _show_notes_panel(self):
        """Show notes panel."""
        if not NOTES_AVAILABLE:
            QMessageBox.warning(self, "Not Available", "Notes feature is not available.")
            return

        # Switch to notes tab
        if self.notes_panel:
            for i in range(self.results_tabs.count()):
                if self.results_tabs.widget(i) == self.notes_panel:
                    self.results_tabs.setCurrentIndex(i)
                    return

    def _show_iphone_view(self):
        """Show iPhone-style file view."""
        if not IPHONE_VIEW_AVAILABLE:
            QMessageBox.warning(self, "Not Available", "iPhone view feature is not available.")
            return

        # Switch to iPhone view tab
        if self.iphone_panel:
            for i in range(self.results_tabs.count()):
                if self.results_tabs.widget(i) == self.iphone_panel:
                    self.results_tabs.setCurrentIndex(i)
                    return

    def _toggle_saved_searches(self, checked: bool):
        """Toggle saved searches panel visibility."""
        if not SAVED_SEARCHES_AVAILABLE:
            return

        # TODO: Implement saved searches dock panel
        if checked:
            self.status_label.setText("Saved searches panel enabled")
        else:
            self.status_label.setText("Saved searches panel disabled")

    def _toggle_favorites(self, checked: bool):
        """Toggle favorites panel visibility."""
        if not SAVED_SEARCHES_AVAILABLE:
            return

        # TODO: Implement favorites dock panel
        if checked:
            self.status_label.setText("Favorites panel enabled")
        else:
            self.status_label.setText("Favorites panel disabled")

    def _show_vault(self):
        """Show the secure vault (hidden feature - Ctrl+Shift+V)."""
        if not VAULT_AVAILABLE:
            QMessageBox.warning(self, "Not Available", "Vault feature is not available.")
            return

        # First, show unlock dialog
        unlock_dialog = VaultUnlockDialog(self)
        if unlock_dialog.exec() == QDialog.DialogCode.Accepted:
            password = unlock_dialog.get_password()

            try:
                # Create or open vault
                if VAULT_BACKEND_AVAILABLE:
                    vault = SecureVault()
                    if vault.unlock(password):
                        # Show vault panel
                        vault_panel = VaultPanel(vault, self)
                        vault_panel.exec()
                    else:
                        QMessageBox.warning(self, "Access Denied", "Invalid vault password.")
                else:
                    # UI-only vault
                    vault_panel = VaultPanel(None, self)
                    vault_panel.exec()
            except Exception as e:
                QMessageBox.critical(self, "Vault Error", f"Failed to open vault:\n{e}")

    def _execute_saved_search(self, search_index: int):
        """Execute a saved search by index (1-9)."""
        if not SAVED_SEARCHES_BACKEND_AVAILABLE:
            return

        try:
            manager = SavedSearchManager()
            saved_searches = manager.get_all()

            if search_index <= len(saved_searches):
                search = saved_searches[search_index - 1]
                # Set search parameters and execute
                self.search_panel.set_query(search.query)
                if hasattr(search, 'filters'):
                    self.search_panel.set_filters(search.filters)
                self._perform_search({'query': search.query, 'filters': getattr(search, 'filters', {})})
                self.status_label.setText(f"Executing saved search: {search.name}")
        except Exception as e:
            self.status_label.setText(f"Failed to execute saved search: {e}")
