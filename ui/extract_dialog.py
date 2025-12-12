"""
Extraction Dialog
Configure extraction options before extracting archives
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QCheckBox, QGroupBox, QFormLayout,
    QComboBox, QTextEdit, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from archive.archive_analyzer import ArchiveAnalyzer


class ExtractDialog(QDialog):
    """
    Extraction configuration dialog:
    - Destination folder selector
    - Extraction options (recursive, flatten, overwrite)
    - Password entry if needed
    - Preview extraction size
    - Conflict handling options
    """

    def __init__(self, archive_path: str, parent=None):
        super().__init__(parent)
        self.archive_path = archive_path
        self.analyzer = ArchiveAnalyzer()

        self.setWindowTitle("Extract Archive")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self._init_ui()
        self._load_archive_info()

    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)

        # Archive info
        info_group = QGroupBox("Archive Information")
        info_layout = QFormLayout(info_group)

        self.archive_name_label = QLabel()
        self.file_count_label = QLabel()
        self.size_label = QLabel()
        self.compressed_label = QLabel()

        info_layout.addRow("Archive:", self.archive_name_label)
        info_layout.addRow("Files:", self.file_count_label)
        info_layout.addRow("Uncompressed Size:", self.size_label)
        info_layout.addRow("Compressed Size:", self.compressed_label)

        layout.addWidget(info_group)

        # Destination
        dest_group = QGroupBox("Destination")
        dest_layout = QVBoxLayout(dest_group)

        dest_input_layout = QHBoxLayout()
        self.dest_input = QLineEdit()
        self.dest_input.setText(self._get_default_destination())
        dest_input_layout.addWidget(self.dest_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_destination)
        dest_input_layout.addWidget(browse_btn)

        dest_layout.addLayout(dest_input_layout)

        # Quick destination options
        quick_layout = QHBoxLayout()

        self.dest_same_btn = QPushButton("Same Folder")
        self.dest_same_btn.clicked.connect(self._set_same_folder)
        quick_layout.addWidget(self.dest_same_btn)

        self.dest_desktop_btn = QPushButton("Desktop")
        self.dest_desktop_btn.clicked.connect(self._set_desktop)
        quick_layout.addWidget(self.dest_desktop_btn)

        self.dest_downloads_btn = QPushButton("Downloads")
        self.dest_downloads_btn.clicked.connect(self._set_downloads)
        quick_layout.addWidget(self.dest_downloads_btn)

        dest_layout.addLayout(quick_layout)

        layout.addWidget(dest_group)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        # Recursive extraction
        self.recursive_check = QCheckBox("Extract nested archives recursively")
        self.recursive_check.setToolTip("Automatically extract any archives found inside this archive")
        options_layout.addWidget(self.recursive_check)

        # Flatten
        self.flatten_check = QCheckBox("Flatten directory structure")
        self.flatten_check.setToolTip("Extract all files to destination root, ignoring folder structure")
        options_layout.addWidget(self.flatten_check)

        # Overwrite options
        overwrite_label = QLabel("If file exists:")
        options_layout.addWidget(overwrite_label)

        self.overwrite_group = QButtonGroup()

        self.overwrite_all_radio = QRadioButton("Overwrite all")
        self.overwrite_all_radio.setChecked(True)
        self.overwrite_group.addButton(self.overwrite_all_radio)
        options_layout.addWidget(self.overwrite_all_radio)

        self.skip_existing_radio = QRadioButton("Skip existing")
        self.overwrite_group.addButton(self.skip_existing_radio)
        options_layout.addWidget(self.skip_existing_radio)

        self.rename_radio = QRadioButton("Auto-rename")
        self.overwrite_group.addButton(self.rename_radio)
        options_layout.addWidget(self.rename_radio)

        layout.addWidget(options_group)

        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(100)
        preview_layout.addWidget(self.preview_text)

        layout.addWidget(preview_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.extract_btn = QPushButton("Extract")
        self.extract_btn.setDefault(True)
        self.extract_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.extract_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        # Update preview when options change
        self.dest_input.textChanged.connect(self._update_preview)
        self.recursive_check.toggled.connect(self._update_preview)
        self.flatten_check.toggled.connect(self._update_preview)

    def _load_archive_info(self):
        """Load and display archive information"""
        try:
            # Get archive name
            self.archive_name_label.setText(os.path.basename(self.archive_path))

            # Analyze archive
            estimate = self.analyzer.estimate_extraction_size(self.archive_path)

            self.file_count_label.setText(f"{estimate['files']} files, {estimate['folders']} folders")
            self.size_label.setText(estimate['formatted_size'])
            self.compressed_label.setText(
                f"{self._format_size(estimate['compressed_size'])} "
                f"({estimate['compression_ratio']:.1f}% compression)"
            )

            # Update preview
            self._update_preview()

        except Exception as e:
            self.file_count_label.setText("Error loading info")
            self.size_label.setText(str(e))

    def _get_default_destination(self) -> str:
        """Get default extraction destination"""
        archive_dir = os.path.dirname(self.archive_path)
        archive_name = Path(self.archive_path).stem
        return os.path.join(archive_dir, archive_name)

    def _browse_destination(self):
        """Browse for destination folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Extraction Destination",
            self.dest_input.text()
        )

        if folder:
            self.dest_input.setText(folder)

    def _set_same_folder(self):
        """Set destination to same folder as archive"""
        self.dest_input.setText(self._get_default_destination())

    def _set_desktop(self):
        """Set destination to Desktop"""
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        archive_name = Path(self.archive_path).stem
        self.dest_input.setText(os.path.join(desktop, archive_name))

    def _set_downloads(self):
        """Set destination to Downloads"""
        downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
        archive_name = Path(self.archive_path).stem
        self.dest_input.setText(os.path.join(downloads, archive_name))

    def _update_preview(self):
        """Update extraction preview"""
        destination = self.dest_input.text()

        preview_lines = [
            f"Archive: {os.path.basename(self.archive_path)}",
            f"Destination: {destination}",
            ""
        ]

        if self.recursive_check.isChecked():
            preview_lines.append("- Will extract nested archives recursively")

        if self.flatten_check.isChecked():
            preview_lines.append("- Will flatten directory structure")

        if self.overwrite_all_radio.isChecked():
            preview_lines.append("- Will overwrite existing files")
        elif self.skip_existing_radio.isChecked():
            preview_lines.append("- Will skip existing files")
        elif self.rename_radio.isChecked():
            preview_lines.append("- Will auto-rename conflicting files")

        # Check if destination exists
        if os.path.exists(destination):
            preview_lines.append("")
            preview_lines.append("Warning: Destination folder already exists")

        self.preview_text.setPlainText('\n'.join(preview_lines))

    def get_options(self) -> dict:
        """
        Get extraction options

        Returns:
            Dictionary with extraction options
        """
        return {
            'destination': self.dest_input.text(),
            'recursive': self.recursive_check.isChecked(),
            'flatten': self.flatten_check.isChecked(),
            'overwrite': self.overwrite_all_radio.isChecked(),
            'skip_existing': self.skip_existing_radio.isChecked(),
            'auto_rename': self.rename_radio.isChecked()
        }

    def _format_size(self, size: int) -> str:
        """Format size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
