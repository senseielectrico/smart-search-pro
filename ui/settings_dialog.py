"""
Settings Dialog - Application settings with tabs
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QCheckBox, QSpinBox, QComboBox, QLineEdit,
    QPushButton, QDialogButtonBox, QFormLayout, QGroupBox,
    QFileDialog, QKeySequenceEdit
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QKeySequence


class SettingsDialog(QDialog):
    """Settings dialog with multiple tabs"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 500)

        self.settings = QSettings("SmartSearch", "Settings")

        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Tab widget
        self.tabs = QTabWidget()

        self.tabs.addTab(self._create_general_tab(), "General")
        self.tabs.addTab(self._create_search_tab(), "Search")
        self.tabs.addTab(self._create_preview_tab(), "Preview")
        self.tabs.addTab(self._create_operations_tab(), "Operations")
        self.tabs.addTab(self._create_appearance_tab(), "Appearance")
        self.tabs.addTab(self._create_shortcuts_tab(), "Shortcuts")

        layout.addWidget(self.tabs)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply_settings)

        layout.addWidget(button_box)

    def _create_general_tab(self) -> QWidget:
        """Create general settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Startup group
        startup_group = QGroupBox("Startup")
        startup_layout = QFormLayout()

        self.remember_window_cb = QCheckBox("Remember window size and position")
        self.remember_window_cb.setChecked(True)
        startup_layout.addRow(self.remember_window_cb)

        self.restore_session_cb = QCheckBox("Restore last session")
        startup_layout.addRow(self.restore_session_cb)

        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)

        # Default paths group
        paths_group = QGroupBox("Default Paths")
        paths_layout = QFormLayout()

        self.default_search_path_edit = QLineEdit()
        browse_btn = QPushButton("Browse...")
        browse_btn.setProperty("secondary", True)
        browse_btn.clicked.connect(self._browse_default_path)

        path_row = QHBoxLayout()
        path_row.addWidget(self.default_search_path_edit)
        path_row.addWidget(browse_btn)

        paths_layout.addRow("Default search path:", path_row)

        paths_group.setLayout(paths_layout)
        layout.addWidget(paths_group)

        layout.addStretch()
        return widget

    def _create_search_tab(self) -> QWidget:
        """Create search settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Search behavior group
        behavior_group = QGroupBox("Search Behavior")
        behavior_layout = QFormLayout()

        self.case_sensitive_cb = QCheckBox("Case sensitive by default")
        behavior_layout.addRow(self.case_sensitive_cb)

        self.regex_cb = QCheckBox("Enable regex by default")
        behavior_layout.addRow(self.regex_cb)

        self.follow_symlinks_cb = QCheckBox("Follow symbolic links")
        self.follow_symlinks_cb.setChecked(True)
        behavior_layout.addRow(self.follow_symlinks_cb)

        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)

        # Performance group
        perf_group = QGroupBox("Performance")
        perf_layout = QFormLayout()

        self.thread_count_spin = QSpinBox()
        self.thread_count_spin.setRange(1, 16)
        self.thread_count_spin.setValue(4)
        perf_layout.addRow("Search threads:", self.thread_count_spin)

        self.max_results_spin = QSpinBox()
        self.max_results_spin.setRange(100, 100000)
        self.max_results_spin.setSingleStep(100)
        self.max_results_spin.setValue(10000)
        perf_layout.addRow("Max results:", self.max_results_spin)

        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)

        # Indexing group
        index_group = QGroupBox("Indexing")
        index_layout = QFormLayout()

        self.enable_index_cb = QCheckBox("Enable file indexing")
        index_layout.addRow(self.enable_index_cb)

        self.index_hidden_cb = QCheckBox("Index hidden files")
        index_layout.addRow(self.index_hidden_cb)

        index_group.setLayout(index_layout)
        layout.addWidget(index_group)

        layout.addStretch()
        return widget

    def _create_preview_tab(self) -> QWidget:
        """Create preview settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Preview group
        preview_group = QGroupBox("Preview")
        preview_layout = QFormLayout()

        self.enable_preview_cb = QCheckBox("Enable file preview")
        self.enable_preview_cb.setChecked(True)
        preview_layout.addRow(self.enable_preview_cb)

        self.max_preview_size_spin = QSpinBox()
        self.max_preview_size_spin.setRange(1, 100)
        self.max_preview_size_spin.setValue(10)
        self.max_preview_size_spin.setSuffix(" MB")
        preview_layout.addRow("Max preview size:", self.max_preview_size_spin)

        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # Image preview group
        image_group = QGroupBox("Image Preview")
        image_layout = QFormLayout()

        self.max_image_size_spin = QSpinBox()
        self.max_image_size_spin.setRange(1, 50)
        self.max_image_size_spin.setValue(10)
        self.max_image_size_spin.setSuffix(" MB")
        image_layout.addRow("Max image size:", self.max_image_size_spin)

        self.thumbnail_size_spin = QSpinBox()
        self.thumbnail_size_spin.setRange(100, 800)
        self.thumbnail_size_spin.setSingleStep(50)
        self.thumbnail_size_spin.setValue(400)
        self.thumbnail_size_spin.setSuffix(" px")
        image_layout.addRow("Thumbnail size:", self.thumbnail_size_spin)

        image_group.setLayout(image_layout)
        layout.addWidget(image_group)

        layout.addStretch()
        return widget

    def _create_operations_tab(self) -> QWidget:
        """Create operations settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # File operations group
        ops_group = QGroupBox("File Operations")
        ops_layout = QFormLayout()

        self.confirm_delete_cb = QCheckBox("Confirm before deleting")
        self.confirm_delete_cb.setChecked(True)
        ops_layout.addRow(self.confirm_delete_cb)

        self.use_recycle_bin_cb = QCheckBox("Use Recycle Bin")
        self.use_recycle_bin_cb.setChecked(True)
        ops_layout.addRow(self.use_recycle_bin_cb)

        self.verify_copy_cb = QCheckBox("Verify file copies")
        ops_layout.addRow(self.verify_copy_cb)

        ops_group.setLayout(ops_layout)
        layout.addWidget(ops_group)

        # Buffer size group
        buffer_group = QGroupBox("Performance")
        buffer_layout = QFormLayout()

        self.buffer_size_combo = QComboBox()
        self.buffer_size_combo.addItems(["64 KB", "128 KB", "256 KB", "512 KB", "1 MB"])
        self.buffer_size_combo.setCurrentIndex(2)
        buffer_layout.addRow("Copy buffer size:", self.buffer_size_combo)

        buffer_group.setLayout(buffer_layout)
        layout.addWidget(buffer_group)

        layout.addStretch()
        return widget

    def _create_appearance_tab(self) -> QWidget:
        """Create appearance settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Theme group
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout()

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System"])
        theme_layout.addRow("Theme:", self.theme_combo)

        self.accent_combo = QComboBox()
        self.accent_combo.addItems(["Blue", "Green", "Purple", "Red", "Orange"])
        theme_layout.addRow("Accent color:", self.accent_combo)

        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)

        # Font group
        font_group = QGroupBox("Font")
        font_layout = QFormLayout()

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setValue(9)
        font_layout.addRow("Font size:", self.font_size_spin)

        font_group.setLayout(font_layout)
        layout.addWidget(font_group)

        layout.addStretch()
        return widget

    def _create_shortcuts_tab(self) -> QWidget:
        """Create keyboard shortcuts tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        shortcuts_group = QGroupBox("Keyboard Shortcuts")
        shortcuts_layout = QFormLayout()

        # Define shortcuts
        self.shortcuts = {
            'search': QKeySequenceEdit(QKeySequence("Ctrl+F")),
            'advanced_search': QKeySequenceEdit(QKeySequence("Ctrl+Shift+F")),
            'open': QKeySequenceEdit(QKeySequence("Ctrl+O")),
            'copy': QKeySequenceEdit(QKeySequence("Ctrl+Shift+C")),
            'move': QKeySequenceEdit(QKeySequence("Ctrl+M")),
            'delete': QKeySequenceEdit(QKeySequence("Delete")),
            'select_all': QKeySequenceEdit(QKeySequence("Ctrl+A")),
            'clear': QKeySequenceEdit(QKeySequence("Ctrl+L")),
        }

        shortcuts_layout.addRow("Search:", self.shortcuts['search'])
        shortcuts_layout.addRow("Advanced Search:", self.shortcuts['advanced_search'])
        shortcuts_layout.addRow("Open File:", self.shortcuts['open'])
        shortcuts_layout.addRow("Copy Files:", self.shortcuts['copy'])
        shortcuts_layout.addRow("Move Files:", self.shortcuts['move'])
        shortcuts_layout.addRow("Delete Files:", self.shortcuts['delete'])
        shortcuts_layout.addRow("Select All:", self.shortcuts['select_all'])
        shortcuts_layout.addRow("Clear Results:", self.shortcuts['clear'])

        shortcuts_group.setLayout(shortcuts_layout)
        layout.addWidget(shortcuts_group)

        # Reset button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setProperty("secondary", True)
        reset_btn.clicked.connect(self._reset_shortcuts)
        layout.addWidget(reset_btn)

        layout.addStretch()
        return widget

    def _browse_default_path(self):
        """Browse for default search path"""
        path = QFileDialog.getExistingDirectory(self, "Select Default Search Path")
        if path:
            self.default_search_path_edit.setText(path)

    def _reset_shortcuts(self):
        """Reset shortcuts to defaults"""
        defaults = {
            'search': "Ctrl+F",
            'advanced_search': "Ctrl+Shift+F",
            'open': "Ctrl+O",
            'copy': "Ctrl+Shift+C",
            'move': "Ctrl+M",
            'delete': "Delete",
            'select_all': "Ctrl+A",
            'clear': "Ctrl+L",
        }

        for key, default in defaults.items():
            self.shortcuts[key].setKeySequence(QKeySequence(default))

    def _load_settings(self):
        """Load settings from QSettings"""
        # General
        self.remember_window_cb.setChecked(self.settings.value("general/remember_window", True, type=bool))
        self.restore_session_cb.setChecked(self.settings.value("general/restore_session", False, type=bool))
        self.default_search_path_edit.setText(self.settings.value("general/default_path", "", type=str))

        # Search
        self.case_sensitive_cb.setChecked(self.settings.value("search/case_sensitive", False, type=bool))
        self.regex_cb.setChecked(self.settings.value("search/regex", False, type=bool))
        self.follow_symlinks_cb.setChecked(self.settings.value("search/follow_symlinks", True, type=bool))
        self.thread_count_spin.setValue(self.settings.value("search/thread_count", 4, type=int))
        self.max_results_spin.setValue(self.settings.value("search/max_results", 10000, type=int))
        self.enable_index_cb.setChecked(self.settings.value("search/enable_index", False, type=bool))
        self.index_hidden_cb.setChecked(self.settings.value("search/index_hidden", False, type=bool))

        # Preview
        self.enable_preview_cb.setChecked(self.settings.value("preview/enabled", True, type=bool))
        self.max_preview_size_spin.setValue(self.settings.value("preview/max_size", 10, type=int))
        self.max_image_size_spin.setValue(self.settings.value("preview/max_image_size", 10, type=int))
        self.thumbnail_size_spin.setValue(self.settings.value("preview/thumbnail_size", 400, type=int))

        # Operations
        self.confirm_delete_cb.setChecked(self.settings.value("operations/confirm_delete", True, type=bool))
        self.use_recycle_bin_cb.setChecked(self.settings.value("operations/use_recycle_bin", True, type=bool))
        self.verify_copy_cb.setChecked(self.settings.value("operations/verify_copy", False, type=bool))

        # Appearance
        theme = self.settings.value("appearance/theme", "Light", type=str)
        self.theme_combo.setCurrentText(theme)
        self.font_size_spin.setValue(self.settings.value("appearance/font_size", 9, type=int))

    def _apply_settings(self):
        """Apply settings"""
        # General
        self.settings.setValue("general/remember_window", self.remember_window_cb.isChecked())
        self.settings.setValue("general/restore_session", self.restore_session_cb.isChecked())
        self.settings.setValue("general/default_path", self.default_search_path_edit.text())

        # Search
        self.settings.setValue("search/case_sensitive", self.case_sensitive_cb.isChecked())
        self.settings.setValue("search/regex", self.regex_cb.isChecked())
        self.settings.setValue("search/follow_symlinks", self.follow_symlinks_cb.isChecked())
        self.settings.setValue("search/thread_count", self.thread_count_spin.value())
        self.settings.setValue("search/max_results", self.max_results_spin.value())
        self.settings.setValue("search/enable_index", self.enable_index_cb.isChecked())
        self.settings.setValue("search/index_hidden", self.index_hidden_cb.isChecked())

        # Preview
        self.settings.setValue("preview/enabled", self.enable_preview_cb.isChecked())
        self.settings.setValue("preview/max_size", self.max_preview_size_spin.value())
        self.settings.setValue("preview/max_image_size", self.max_image_size_spin.value())
        self.settings.setValue("preview/thumbnail_size", self.thumbnail_size_spin.value())

        # Operations
        self.settings.setValue("operations/confirm_delete", self.confirm_delete_cb.isChecked())
        self.settings.setValue("operations/use_recycle_bin", self.use_recycle_bin_cb.isChecked())
        self.settings.setValue("operations/verify_copy", self.verify_copy_cb.isChecked())

        # Appearance
        self.settings.setValue("appearance/theme", self.theme_combo.currentText())
        self.settings.setValue("appearance/font_size", self.font_size_spin.value())

        # Shortcuts
        for key, widget in self.shortcuts.items():
            self.settings.setValue(f"shortcuts/{key}", widget.keySequence().toString())

    def accept(self):
        """Accept and apply settings"""
        self._apply_settings()
        super().accept()
