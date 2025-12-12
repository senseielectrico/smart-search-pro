"""
Batch Rename Dialog - Complete wizard for batch file renaming
"""

import uuid
from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QLineEdit, QSpinBox, QCheckBox,
    QComboBox, QFileDialog, QMessageBox, QGroupBox, QSplitter,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from operations.batch_renamer import (
    BatchRenamer, RenamePattern, CaseMode, CollisionMode
)
from operations.rename_patterns import (
    PatternLibrary, SavedPattern, get_pattern_library
)
from operations.rename_history import get_rename_history

from .pattern_builder_widget import PatternBuilderWidget
from .rename_preview_table import RenamePreviewTable
from .drag_drop import DragDropHandler


class BatchRenameDialog(QDialog):
    """
    Batch rename wizard dialog

    Features:
    - Multiple rename methods (pattern, find/replace, case, etc.)
    - Live preview with conflict detection
    - Pattern library with presets
    - Drag & drop support
    - Undo capability
    """

    files_renamed = pyqtSignal(int)  # Number of files renamed

    def __init__(self, initial_files: Optional[List[str]] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Rename Files")
        self.resize(1000, 700)

        # Backend
        self.renamer = BatchRenamer()
        self.pattern_library = get_pattern_library()
        self.history = get_rename_history()

        # State
        self.files: List[Path] = []
        self.current_pattern = RenamePattern()
        self.last_operation_id: Optional[str] = None

        # Drag & drop
        self.drag_handler = DragDropHandler(self)
        self.drag_handler.files_dropped.connect(self._on_files_dropped)
        self.setAcceptDrops(True)

        self._init_ui()

        # Load initial files
        if initial_files:
            self.add_files(initial_files)

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Batch Rename Files")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        # File count badge
        self.file_count_label = QLabel("0 files")
        self.file_count_label.setStyleSheet("""
            QLabel {
                background: #2196F3;
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-weight: bold;
            }
        """)
        header.addWidget(self.file_count_label)

        layout.addLayout(header)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top: File management and pattern builder
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # File list section
        file_group = QGroupBox("Files to Rename")
        file_layout = QVBoxLayout(file_group)

        # File list with drag & drop zone
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.file_list.setMinimumHeight(120)
        file_layout.addWidget(self.file_list)

        # File buttons
        file_buttons = QHBoxLayout()

        add_btn = QPushButton("Add Files...")
        add_btn.clicked.connect(self._add_files_dialog)
        file_buttons.addWidget(add_btn)

        add_folder_btn = QPushButton("Add Folder...")
        add_folder_btn.clicked.connect(self._add_folder_dialog)
        file_buttons.addWidget(add_folder_btn)

        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_selected_files)
        file_buttons.addWidget(remove_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear_files)
        file_buttons.addWidget(clear_btn)

        file_buttons.addStretch()
        file_layout.addLayout(file_buttons)

        top_layout.addWidget(file_group)

        # Tabs for rename methods
        self.tabs = QTabWidget()

        # Pattern tab
        pattern_tab = self._create_pattern_tab()
        self.tabs.addTab(pattern_tab, "Pattern Rename")

        # Find & Replace tab
        find_replace_tab = self._create_find_replace_tab()
        self.tabs.addTab(find_replace_tab, "Find && Replace")

        # Add/Remove text tab
        text_tab = self._create_text_operations_tab()
        self.tabs.addTab(text_tab, "Add/Remove Text")

        # Case change tab
        case_tab = self._create_case_tab()
        self.tabs.addTab(case_tab, "Case Change")

        # Numbering tab
        number_tab = self._create_numbering_tab()
        self.tabs.addTab(number_tab, "Numbering")

        top_layout.addWidget(self.tabs)
        splitter.addWidget(top_widget)

        # Bottom: Preview table
        self.preview_table = RenamePreviewTable()
        splitter.addWidget(self.preview_table)

        splitter.setSizes([350, 350])
        layout.addWidget(splitter)

        # Bottom buttons
        button_layout = QHBoxLayout()

        # History button
        history_btn = QPushButton("History...")
        history_btn.clicked.connect(self._show_history)
        button_layout.addWidget(history_btn)

        # Undo button
        self.undo_btn = QPushButton("Undo Last Rename")
        self.undo_btn.clicked.connect(self._undo_last)
        self.undo_btn.setEnabled(False)
        button_layout.addWidget(self.undo_btn)

        button_layout.addStretch()

        # Save preset button
        save_preset_btn = QPushButton("Save Preset...")
        save_preset_btn.clicked.connect(self._save_preset)
        button_layout.addWidget(save_preset_btn)

        # Action buttons
        preview_btn = QPushButton("Refresh Preview")
        preview_btn.clicked.connect(self._update_preview)
        button_layout.addWidget(preview_btn)

        apply_btn = QPushButton("Apply Rename")
        apply_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        apply_btn.clicked.connect(self._apply_rename)
        button_layout.addWidget(apply_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        # Connect tab changes to update preview
        self.tabs.currentChanged.connect(self._update_preview)

    def _create_pattern_tab(self) -> QWidget:
        """Create pattern rename tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Pattern builder
        self.pattern_builder = PatternBuilderWidget()
        self.pattern_builder.pattern_changed.connect(self._on_pattern_changed)
        layout.addWidget(self.pattern_builder)

        # Preset patterns
        preset_group = QGroupBox("Preset Patterns")
        preset_layout = QVBoxLayout(preset_group)

        self.preset_combo = QComboBox()
        self._load_presets()
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        preset_layout.addWidget(self.preset_combo)

        layout.addWidget(preset_group)

        return widget

    def _create_find_replace_tab(self) -> QWidget:
        """Create find & replace tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Find field
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("Find:"))
        self.find_edit = QLineEdit()
        self.find_edit.textChanged.connect(self._update_preview)
        find_layout.addWidget(self.find_edit)
        layout.addLayout(find_layout)

        # Replace field
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("Replace:"))
        self.replace_edit = QLineEdit()
        self.replace_edit.textChanged.connect(self._update_preview)
        replace_layout.addWidget(self.replace_edit)
        layout.addLayout(replace_layout)

        # Regex checkbox
        self.regex_check = QCheckBox("Use Regular Expressions")
        self.regex_check.stateChanged.connect(self._update_preview)
        layout.addWidget(self.regex_check)

        layout.addStretch()
        return widget

    def _create_text_operations_tab(self) -> QWidget:
        """Create text operations tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Prefix
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("Add Prefix:"))
        self.prefix_edit = QLineEdit()
        self.prefix_edit.textChanged.connect(self._update_preview)
        prefix_layout.addWidget(self.prefix_edit)
        layout.addLayout(prefix_layout)

        # Suffix
        suffix_layout = QHBoxLayout()
        suffix_layout.addWidget(QLabel("Add Suffix:"))
        self.suffix_edit = QLineEdit()
        self.suffix_edit.textChanged.connect(self._update_preview)
        suffix_layout.addWidget(self.suffix_edit)
        layout.addLayout(suffix_layout)

        # Remove characters
        remove_layout = QHBoxLayout()
        remove_layout.addWidget(QLabel("Remove Characters:"))
        self.remove_edit = QLineEdit()
        self.remove_edit.setPlaceholderText("e.g., !@#$%")
        self.remove_edit.textChanged.connect(self._update_preview)
        remove_layout.addWidget(self.remove_edit)
        layout.addLayout(remove_layout)

        # Trim whitespace
        self.trim_check = QCheckBox("Trim Whitespace")
        self.trim_check.setChecked(True)
        self.trim_check.stateChanged.connect(self._update_preview)
        layout.addWidget(self.trim_check)

        layout.addStretch()
        return widget

    def _create_case_tab(self) -> QWidget:
        """Create case change tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Convert file names to:"))

        self.case_combo = QComboBox()
        self.case_combo.addItem("Keep Original", CaseMode.KEEP)
        self.case_combo.addItem("UPPERCASE", CaseMode.UPPER)
        self.case_combo.addItem("lowercase", CaseMode.LOWER)
        self.case_combo.addItem("Title Case", CaseMode.TITLE)
        self.case_combo.addItem("Sentence case", CaseMode.SENTENCE)
        self.case_combo.currentIndexChanged.connect(self._update_preview)
        layout.addWidget(self.case_combo)

        layout.addStretch()
        return widget

    def _create_numbering_tab(self) -> QWidget:
        """Create numbering tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Start number
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start Number:"))
        self.start_number_spin = QSpinBox()
        self.start_number_spin.setMinimum(0)
        self.start_number_spin.setMaximum(99999)
        self.start_number_spin.setValue(1)
        self.start_number_spin.valueChanged.connect(self._update_preview)
        start_layout.addWidget(self.start_number_spin)
        start_layout.addStretch()
        layout.addLayout(start_layout)

        # Padding
        padding_layout = QHBoxLayout()
        padding_layout.addWidget(QLabel("Number Padding:"))
        self.padding_spin = QSpinBox()
        self.padding_spin.setMinimum(1)
        self.padding_spin.setMaximum(10)
        self.padding_spin.setValue(3)
        self.padding_spin.valueChanged.connect(self._update_preview)
        padding_layout.addWidget(self.padding_spin)
        padding_layout.addWidget(QLabel("(e.g., 001, 002, 003)"))
        padding_layout.addStretch()
        layout.addLayout(padding_layout)

        layout.addStretch()
        return widget

    def add_files(self, file_paths: List[str]):
        """Add files to rename list"""
        for path in file_paths:
            p = Path(path)
            if p.exists() and p.is_file():
                if p not in self.files:
                    self.files.append(p)
                    item = QListWidgetItem(str(p))
                    self.file_list.addItem(item)

        self._update_file_count()
        self._update_preview()

    def _add_files_dialog(self):
        """Show file selection dialog"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files to Rename",
            str(Path.home()),
            "All Files (*.*)"
        )
        if files:
            self.add_files(files)

    def _add_folder_dialog(self):
        """Add all files from a folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            str(Path.home())
        )
        if folder:
            folder_path = Path(folder)
            files = [str(f) for f in folder_path.iterdir() if f.is_file()]
            self.add_files(files)

    def _remove_selected_files(self):
        """Remove selected files from list"""
        for item in self.file_list.selectedItems():
            row = self.file_list.row(item)
            self.file_list.takeItem(row)
            if row < len(self.files):
                del self.files[row]

        self._update_file_count()
        self._update_preview()

    def _clear_files(self):
        """Clear all files"""
        self.files.clear()
        self.file_list.clear()
        self._update_file_count()
        self.preview_table.clear()

    def _update_file_count(self):
        """Update file count label"""
        count = len(self.files)
        self.file_count_label.setText(f"{count} file{'s' if count != 1 else ''}")

    def _load_presets(self):
        """Load preset patterns into combo box"""
        self.preset_combo.clear()
        self.preset_combo.addItem("-- Select Preset --", None)

        all_patterns = self.pattern_library.get_all_patterns()
        for pattern_id, saved_pattern in all_patterns.items():
            label = f"[{saved_pattern.category}] {saved_pattern.name}"
            self.preset_combo.addItem(label, (pattern_id, saved_pattern))

    def _on_preset_selected(self, index: int):
        """Handle preset selection"""
        data = self.preset_combo.itemData(index)
        if data:
            pattern_id, saved_pattern = data
            self.current_pattern = saved_pattern.pattern
            self.pattern_builder.set_pattern(self.current_pattern)
            self._update_preview()

    def _on_pattern_changed(self, pattern: RenamePattern):
        """Handle pattern change from builder"""
        self.current_pattern = pattern
        self._update_preview()

    def _build_current_pattern(self) -> RenamePattern:
        """Build pattern from current tab"""
        current_tab = self.tabs.currentIndex()

        if current_tab == 0:  # Pattern tab
            return self.current_pattern
        elif current_tab == 1:  # Find & Replace
            return RenamePattern(
                pattern="{name}",
                find=self.find_edit.text(),
                replace=self.replace_edit.text(),
                use_regex=self.regex_check.isChecked()
            )
        elif current_tab == 2:  # Add/Remove text
            return RenamePattern(
                pattern="{name}",
                prefix=self.prefix_edit.text(),
                suffix=self.suffix_edit.text(),
                remove_chars=self.remove_edit.text(),
                trim_whitespace=self.trim_check.isChecked()
            )
        elif current_tab == 3:  # Case
            return RenamePattern(
                pattern="{name}",
                case_mode=self.case_combo.currentData()
            )
        elif current_tab == 4:  # Numbering
            return RenamePattern(
                pattern="{name}_{num}",
                start_number=self.start_number_spin.value(),
                number_padding=self.padding_spin.value()
            )

        return RenamePattern()

    def _update_preview(self):
        """Update preview table"""
        if not self.files:
            self.preview_table.clear()
            return

        pattern = self._build_current_pattern()
        previews = self.renamer.preview_rename([str(f) for f in self.files], pattern)
        self.preview_table.set_previews(previews)

    def _apply_rename(self):
        """Apply the rename operation"""
        if not self.files:
            QMessageBox.warning(self, "No Files", "Please add files to rename first.")
            return

        # Check for conflicts
        if self.preview_table.has_conflicts():
            reply = QMessageBox.question(
                self,
                "Conflicts Detected",
                "Some file names will conflict. Auto-number collisions?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # Confirm
        reply = QMessageBox.question(
            self,
            "Confirm Rename",
            f"Rename {len(self.files)} files?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        # Execute rename
        pattern = self._build_current_pattern()
        result = self.renamer.batch_rename(
            [str(f) for f in self.files],
            pattern,
            CollisionMode.AUTO_NUMBER
        )

        # Save to history
        operation_id = str(uuid.uuid4())
        operations = [op.to_dict() for op in result.operations]
        self.history.add_entry(
            operation_id,
            operations,
            pattern.pattern,
            result.total_files,
            result.success_count
        )
        self.last_operation_id = operation_id
        self.undo_btn.setEnabled(True)

        # Show result
        if result.success_count > 0:
            msg = f"Successfully renamed {result.success_count} of {result.total_files} files"
            if result.failed_count > 0:
                msg += f"\n{result.failed_count} files failed"
            QMessageBox.information(self, "Rename Complete", msg)
            self.files_renamed.emit(result.success_count)
            self.accept()
        else:
            QMessageBox.warning(self, "Rename Failed", "No files were renamed.")

    def _undo_last(self):
        """Undo last rename operation"""
        if not self.last_operation_id:
            return

        success, message, count = self.history.undo_operation(self.last_operation_id)

        if success:
            QMessageBox.information(self, "Undo Complete", message)
            self.undo_btn.setEnabled(False)
        else:
            QMessageBox.warning(self, "Undo Failed", message)

    def _save_preset(self):
        """Save current pattern as preset"""
        from PyQt6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(
            self,
            "Save Preset",
            "Preset Name:"
        )

        if ok and name:
            pattern = self._build_current_pattern()
            saved_pattern = SavedPattern(
                name=name,
                description="Custom pattern",
                pattern=pattern,
                category="Custom"
            )

            pattern_id = name.lower().replace(' ', '_')
            if self.pattern_library.save_pattern(pattern_id, saved_pattern):
                QMessageBox.information(self, "Success", "Preset saved successfully")
                self._load_presets()
            else:
                QMessageBox.warning(self, "Error", "Failed to save preset")

    def _show_history(self):
        """Show rename history dialog"""
        # Simple history display
        history = self.history.get_history(limit=20)
        if not history:
            QMessageBox.information(self, "History", "No rename history available")
            return

        text = "Recent Rename Operations:\n\n"
        for entry in history:
            text += f"{entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            text += f"  Pattern: {entry.pattern_used}\n"
            text += f"  Files: {entry.success_count}/{entry.total_files}\n"
            text += f"  Can Undo: {'Yes' if entry.can_undo else 'No'}\n\n"

        from PyQt6.QtWidgets import QTextEdit
        dialog = QDialog(self)
        dialog.setWindowTitle("Rename History")
        dialog.resize(600, 400)
        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(text)
        layout.addWidget(text_edit)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec()

    def _on_files_dropped(self, urls: List[QUrl]):
        """Handle dropped files"""
        files = [url.toLocalFile() for url in urls]
        self.add_files(files)

    # Drag & drop events
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        self.drag_handler.handleDrop(event)
