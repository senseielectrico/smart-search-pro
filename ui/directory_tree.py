"""
Enhanced Directory Tree with tristate checkboxes, lazy loading, and drag & drop support
"""

import os
from pathlib import Path
from typing import List, Set, Optional, Dict
from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox,
    QInputDialog, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QAction, QDragEnterEvent, QDropEvent, QDragLeaveEvent
from .drag_drop import DragDropHandler


class DirectoryTree(QTreeWidget):
    """Enhanced directory tree with favorites, lazy loading, and drag & drop support"""

    # Signals
    selection_changed = pyqtSignal(list)  # List of selected paths
    favorites_changed = pyqtSignal(list)  # List of favorite paths
    files_dropped_to_search = pyqtSignal(list)  # Files/folders dropped to add to search

    # Quick access paths
    QUICK_ACCESS = [
        ("Desktop", "Desktop"),
        ("Documents", "Documents"),
        ("Downloads", "Downloads"),
        ("Pictures", "Pictures"),
        ("Videos", "Videos"),
        ("Music", "Music"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)

        # State
        self.favorites: Set[str] = set()
        self.expanded_paths: Set[str] = set()
        self._loading_items: Set[QTreeWidgetItem] = set()

        # Drag & Drop handler
        self.drag_handler = DragDropHandler(self)
        self.drag_handler.files_dropped.connect(self._on_files_dropped)

        # Enable drops
        self.setAcceptDrops(True)

        self._setup_ui()
        self._load_initial_items()
        self._setup_connections()

    def _setup_ui(self):
        """Setup UI components"""
        self.setHeaderLabel("Directories")
        self.setColumnCount(1)
        self.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Enable features
        self.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setAnimated(True)
        self.setIndentation(20)

        # Styling
        self.setMinimumWidth(250)
        self.setStyleSheet("""
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:hover {
                background-color: #F3F3F3;
            }
        """)

    def _setup_connections(self):
        """Setup signal connections"""
        self.itemChanged.connect(self._on_item_changed)
        self.itemExpanded.connect(self._on_item_expanded)
        self.itemCollapsed.connect(self._on_item_collapsed)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _load_initial_items(self):
        """Load initial directory structure"""
        # Favorites section
        favorites_root = QTreeWidgetItem(["⭐ Favorites"])
        favorites_root.setData(0, Qt.ItemDataRole.UserRole, "FAVORITES_ROOT")
        favorites_root.setExpanded(True)
        favorites_root.setFlags(favorites_root.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
        self.addTopLevelItem(favorites_root)

        # Quick Access section
        quick_root = QTreeWidgetItem(["⚡ Quick Access"])
        quick_root.setData(0, Qt.ItemDataRole.UserRole, "QUICK_ACCESS_ROOT")
        quick_root.setExpanded(True)
        quick_root.setFlags(quick_root.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
        self.addTopLevelItem(quick_root)

        # Add quick access items
        user_home = Path.home()
        for display_name, folder_name in self.QUICK_ACCESS:
            path = user_home / folder_name
            if path.exists():
                item = self._create_directory_item(str(path), f"📁 {display_name}")
                quick_root.addChild(item)
                self._add_placeholder_child(item)

        # This PC section
        this_pc_root = QTreeWidgetItem(["💻 This PC"])
        this_pc_root.setData(0, Qt.ItemDataRole.UserRole, "THIS_PC_ROOT")
        this_pc_root.setExpanded(True)
        this_pc_root.setFlags(this_pc_root.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
        self.addTopLevelItem(this_pc_root)

        # Add drives
        self._load_drives(this_pc_root)

    def _load_drives(self, parent_item: QTreeWidgetItem):
        """Load system drives"""
        if os.name == 'nt':  # Windows
            import string
            from ctypes import windll

            drives = []
            bitmask = windll.kernel32.GetLogicalDrives()
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    drive = f"{letter}:\\"
                    if os.path.exists(drive):
                        drives.append(drive)
                bitmask >>= 1

            for drive in drives:
                item = self._create_directory_item(drive, f"💾 {drive}")
                parent_item.addChild(item)
                self._add_placeholder_child(item)
        else:  # Unix-like
            root_item = self._create_directory_item("/", "💾 /")
            parent_item.addChild(root_item)
            self._add_placeholder_child(root_item)

    def _create_directory_item(self, path: str, display_name: str = None) -> QTreeWidgetItem:
        """Create directory tree item"""
        if display_name is None:
            display_name = f"📁 {Path(path).name or path}"

        item = QTreeWidgetItem([display_name])
        item.setData(0, Qt.ItemDataRole.UserRole, path)
        item.setCheckState(0, Qt.CheckState.Unchecked)
        item.setToolTip(0, path)

        # Check if it's a favorite
        if path in self.favorites:
            item.setIcon(0, QIcon("⭐"))

        return item

    def _add_placeholder_child(self, item: QTreeWidgetItem):
        """Add placeholder child to enable expansion"""
        placeholder = QTreeWidgetItem(["Loading..."])
        placeholder.setData(0, Qt.ItemDataRole.UserRole, "PLACEHOLDER")
        placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
        item.addChild(placeholder)

    def _on_item_expanded(self, item: QTreeWidgetItem):
        """Handle item expansion - lazy load children"""
        path = item.data(0, Qt.ItemDataRole.UserRole)

        # Skip special items
        if not path or path in ["FAVORITES_ROOT", "QUICK_ACCESS_ROOT", "THIS_PC_ROOT", "PLACEHOLDER"]:
            return

        # Check if already loaded
        if path in self.expanded_paths:
            return

        # Remove placeholder
        for i in range(item.childCount()):
            child = item.child(i)
            if child.data(0, Qt.ItemDataRole.UserRole) == "PLACEHOLDER":
                item.removeChild(child)
                break

        # Load subdirectories
        self._load_subdirectories(item, path)
        self.expanded_paths.add(path)

    def _on_item_collapsed(self, item: QTreeWidgetItem):
        """Handle item collapse"""
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path in self.expanded_paths:
            self.expanded_paths.remove(path)

    def _load_subdirectories(self, parent_item: QTreeWidgetItem, path: str):
        """Load subdirectories for path"""
        try:
            path_obj = Path(path)
            subdirs = []

            # Get subdirectories
            for item in path_obj.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    subdirs.append(item)

            # Sort subdirectories
            subdirs.sort(key=lambda p: p.name.lower())

            # Add items
            for subdir in subdirs:
                try:
                    item = self._create_directory_item(str(subdir))
                    parent_item.addChild(item)

                    # Check if has subdirectories
                    if self._has_subdirectories(subdir):
                        self._add_placeholder_child(item)

                except (PermissionError, OSError):
                    continue

        except (PermissionError, OSError) as e:
            # Show error item
            error_item = QTreeWidgetItem([f"⚠ Access Denied"])
            error_item.setFlags(Qt.ItemFlag.NoItemFlags)
            parent_item.addChild(error_item)

    def _has_subdirectories(self, path: Path) -> bool:
        """Check if directory has subdirectories"""
        try:
            for item in path.iterdir():
                if item.is_dir():
                    return True
            return False
        except (PermissionError, OSError):
            return False

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle checkbox state changes (tristate)"""
        path = item.data(0, Qt.ItemDataRole.UserRole)

        # Skip special items
        if not path or path in ["FAVORITES_ROOT", "QUICK_ACCESS_ROOT", "THIS_PC_ROOT", "PLACEHOLDER"]:
            return

        # Prevent recursion
        if item in self._loading_items:
            return

        self._loading_items.add(item)

        try:
            state = item.checkState(column)

            # Block signals during bulk update to prevent recursion
            self.blockSignals(True)
            try:
                # Update children
                if state != Qt.CheckState.PartiallyChecked:
                    self._update_children_state(item, state)

                # Update parent
                self._update_parent_state(item)
            finally:
                self.blockSignals(False)

            # Emit selection changed (after signals unblocked)
            self.selection_changed.emit(self.get_selected_paths())

        finally:
            self._loading_items.discard(item)

    def _update_children_state(self, item: QTreeWidgetItem, state: Qt.CheckState):
        """Recursively update children state"""
        for i in range(item.childCount()):
            child = item.child(i)
            if child.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                child.setCheckState(0, state)
                self._update_children_state(child, state)

    def _update_parent_state(self, item: QTreeWidgetItem):
        """Update parent checkbox based on children states"""
        parent = item.parent()
        if not parent or parent in self._loading_items:
            return

        self._loading_items.add(parent)

        try:
            checked_count = 0
            partial_count = 0
            total_count = parent.childCount()

            for i in range(total_count):
                child = parent.child(i)
                if child.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                    state = child.checkState(0)
                    if state == Qt.CheckState.Checked:
                        checked_count += 1
                    elif state == Qt.CheckState.PartiallyChecked:
                        partial_count += 1

            # Set parent state
            if partial_count > 0 or (checked_count > 0 and checked_count < total_count):
                parent.setCheckState(0, Qt.CheckState.PartiallyChecked)
            elif checked_count == total_count and total_count > 0:
                parent.setCheckState(0, Qt.CheckState.Checked)
            else:
                parent.setCheckState(0, Qt.CheckState.Unchecked)

            # Recurse to grandparent
            self._update_parent_state(parent)

        finally:
            self._loading_items.discard(parent)

    def get_selected_paths(self) -> List[str]:
        """Get all checked directory paths"""
        paths = []

        def collect_checked(item: QTreeWidgetItem):
            path = item.data(0, Qt.ItemDataRole.UserRole)

            if path and path not in ["FAVORITES_ROOT", "QUICK_ACCESS_ROOT", "THIS_PC_ROOT", "PLACEHOLDER"]:
                if item.checkState(0) == Qt.CheckState.Checked:
                    paths.append(path)
                    return  # Don't check children if parent is fully checked

            # Check children
            for i in range(item.childCount()):
                collect_checked(item.child(i))

        for i in range(self.topLevelItemCount()):
            collect_checked(self.topLevelItem(i))

        return paths

    def set_selected_paths(self, paths: List[str]):
        """Set checked paths"""
        # First uncheck all
        self._uncheck_all()

        # Then check specified paths
        for path in paths:
            self._check_path(path)

    def _uncheck_all(self):
        """Uncheck all items"""
        def uncheck_recursive(item: QTreeWidgetItem):
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(0, Qt.CheckState.Unchecked)

            for i in range(item.childCount()):
                uncheck_recursive(item.child(i))

        for i in range(self.topLevelItemCount()):
            uncheck_recursive(self.topLevelItem(i))

    def _check_path(self, path: str):
        """Check specific path"""
        # TODO: Implement path finding and checking
        pass

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter - accept folders"""
        if self.drag_handler.handle_drag_enter(event, accept_files=False, accept_folders=True):
            # Apply visual feedback
            self.setStyleSheet(self.styleSheet() + """
                QTreeWidget {
                    border: 2px solid #0078D4;
                    background-color: rgba(0, 120, 212, 0.05);
                }
            """)

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        """Handle drag leave - reset style"""
        self.setStyleSheet("""
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:hover {
                background-color: #F3F3F3;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        """Handle drop - add folders to search paths"""
        # Reset style
        self.dragLeaveEvent(None)

        files = self.drag_handler.handle_drop(event, "directory_tree")

        if files:
            # Filter to only directories
            folders = [f for f in files if Path(f).is_dir()]

            if folders:
                # Add to tree and check them
                for folder in folders:
                    self._add_and_check_path(folder)

                # Emit signal
                self.files_dropped_to_search.emit(folders)

    def _add_and_check_path(self, path: str):
        """Add path to tree and check it"""
        path_obj = Path(path)

        # Find appropriate parent (Quick Access or This PC)
        parent_item = None
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data == "THIS_PC_ROOT":
                parent_item = item
                break

        if not parent_item:
            return

        # Check if already exists
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            child_path = child.data(0, Qt.ItemDataRole.UserRole)
            if child_path == path:
                # Already exists - just check it
                child.setCheckState(0, Qt.CheckState.Checked)
                return

        # Add new item
        new_item = self._create_directory_item(path)
        parent_item.addChild(new_item)

        # Check if has subdirectories
        if self._has_subdirectories(path_obj):
            self._add_placeholder_child(new_item)

        # Check the item
        new_item.setCheckState(0, Qt.CheckState.Checked)

        # Expand parent to show it
        parent_item.setExpanded(True)

    def _on_files_dropped(self, files: List[str], zone: str):
        """Handle files dropped signal"""
        if zone == "directory_tree":
            # Already handled in dropEvent
            pass

    def add_favorite(self, path: str):
        """Add path to favorites"""
        if path not in self.favorites:
            self.favorites.add(path)
            self._update_favorites_section()
            self.favorites_changed.emit(list(self.favorites))

    def remove_favorite(self, path: str):
        """Remove path from favorites"""
        if path in self.favorites:
            self.favorites.discard(path)
            self._update_favorites_section()
            self.favorites_changed.emit(list(self.favorites))

    def _update_favorites_section(self):
        """Update favorites section"""
        # Find favorites root
        favorites_root = self.topLevelItem(0)
        if favorites_root.data(0, Qt.ItemDataRole.UserRole) != "FAVORITES_ROOT":
            return

        # Clear existing favorites
        while favorites_root.childCount() > 0:
            favorites_root.removeChild(favorites_root.child(0))

        # Add current favorites
        for path in sorted(self.favorites):
            if os.path.exists(path):
                name = Path(path).name or path
                item = self._create_directory_item(path, f"⭐ {name}")
                favorites_root.addChild(item)
                if self._has_subdirectories(Path(path)):
                    self._add_placeholder_child(item)

    def _show_context_menu(self, position):
        """Show context menu"""
        item = self.itemAt(position)
        if not item:
            return

        path = item.data(0, Qt.ItemDataRole.UserRole)

        # Skip special items
        if not path or path in ["FAVORITES_ROOT", "QUICK_ACCESS_ROOT", "THIS_PC_ROOT", "PLACEHOLDER"]:
            return

        menu = QMenu(self)

        # Add to favorites
        if path not in self.favorites:
            fav_action = QAction("⭐ Add to Favorites", self)
            fav_action.triggered.connect(lambda: self.add_favorite(path))
            menu.addAction(fav_action)
        else:
            unfav_action = QAction("Remove from Favorites", self)
            unfav_action.triggered.connect(lambda: self.remove_favorite(path))
            menu.addAction(unfav_action)

        menu.addSeparator()

        # Open in Explorer
        open_action = QAction("📂 Open in Explorer", self)
        open_action.triggered.connect(lambda: self._open_in_explorer(path))
        menu.addAction(open_action)

        # Copy path
        copy_action = QAction("📋 Copy Path", self)
        copy_action.triggered.connect(lambda: self._copy_path(path))
        menu.addAction(copy_action)

        menu.addSeparator()

        # Refresh
        refresh_action = QAction("🔄 Refresh", self)
        refresh_action.triggered.connect(lambda: self._refresh_item(item))
        menu.addAction(refresh_action)

        menu.exec(self.viewport().mapToGlobal(position))

    def _open_in_explorer(self, path: str):
        """Open path in file explorer"""
        try:
            if os.path.exists(path):
                os.startfile(path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open path:\n{e}")

    def _copy_path(self, path: str):
        """Copy path to clipboard"""
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(path)

    def _refresh_item(self, item: QTreeWidgetItem):
        """Refresh directory item"""
        path = item.data(0, Qt.ItemDataRole.UserRole)

        if path in self.expanded_paths:
            self.expanded_paths.remove(path)

        # Remove all children
        while item.childCount() > 0:
            item.removeChild(item.child(0))

        # Add placeholder
        self._add_placeholder_child(item)

        # Re-expand if it was expanded
        if item.isExpanded():
            self._on_item_expanded(item)
