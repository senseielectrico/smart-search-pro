"""
ExifTool Dialog - ExifTool Operations and Configuration
Configure ExifTool path and access common operations.
"""

import os
from pathlib import Path
from typing import Optional, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox, QRadioButton, QCheckBox, QTextEdit,
    QFileDialog, QMessageBox, QListWidget, QProgressDialog,
    QTabWidget, QWidget, QSpinBox, QComboBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.exiftool_wrapper import ExifToolWrapper
from tools.metadata_editor import MetadataEditor


class ExifToolDialog(QDialog):
    """
    Dialog for ExifTool operations and configuration.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("ExifTool Operations")
        self.resize(800, 600)

        # Try to initialize ExifTool
        try:
            self.exiftool = ExifToolWrapper()
            self.editor = MetadataEditor(self.exiftool)
            self.exiftool_available = True
        except RuntimeError as e:
            self.exiftool = None
            self.editor = None
            self.exiftool_available = False
            self.error_message = str(e)

        self._init_ui()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Create tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Configuration tab
        self._create_config_tab()

        # Strip metadata tab
        self._create_strip_tab()

        # Batch rename tab
        self._create_rename_tab()

        # Custom command tab
        self._create_command_tab()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _create_config_tab(self):
        """Create configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # ExifTool path configuration
        path_group = QGroupBox("ExifTool Path")
        path_layout = QVBoxLayout()

        # Current status
        if self.exiftool_available:
            version = self.exiftool.get_version()
            status_label = QLabel(
                f"<b>Status:</b> <span style='color: green;'>ExifTool found</span><br>"
                f"<b>Version:</b> {version}<br>"
                f"<b>Path:</b> {self.exiftool.exiftool_path}"
            )
        else:
            status_label = QLabel(
                f"<b>Status:</b> <span style='color: red;'>ExifTool not found</span><br>"
                f"<b>Error:</b> {self.error_message}"
            )

        status_label.setWordWrap(True)
        path_layout.addWidget(status_label)

        # Custom path input
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("Custom Path:"))

        self.custom_path_edit = QLineEdit()
        if self.exiftool_available:
            self.custom_path_edit.setText(self.exiftool.exiftool_path)
        custom_layout.addWidget(self.custom_path_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_exiftool_path)
        custom_layout.addWidget(browse_btn)

        path_layout.addLayout(custom_layout)

        # Test button
        test_btn = QPushButton("Test ExifTool")
        test_btn.clicked.connect(self._test_exiftool)
        path_layout.addWidget(test_btn)

        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        # Supported formats
        formats_group = QGroupBox("Supported Formats")
        formats_layout = QVBoxLayout()

        formats_label = QLabel(
            "ExifTool supports 400+ file formats including:<br>"
            "<ul>"
            "<li><b>Images:</b> JPEG, PNG, TIFF, RAW (CR2, NEF, ARW, DNG, etc.)</li>"
            "<li><b>Video:</b> MP4, MOV, AVI, MKV, FLV</li>"
            "<li><b>Audio:</b> MP3, FLAC, WAV, M4A</li>"
            "<li><b>Documents:</b> PDF, DOCX, XLSX, PPTX</li>"
            "<li><b>And many more...</b></li>"
            "</ul>"
        )
        formats_label.setWordWrap(True)
        formats_layout.addWidget(formats_label)

        if self.exiftool_available:
            show_all_btn = QPushButton("Show All Supported Formats")
            show_all_btn.clicked.connect(self._show_all_formats)
            formats_layout.addWidget(show_all_btn)

        formats_group.setLayout(formats_layout)
        layout.addWidget(formats_group)

        layout.addStretch()

        self.tabs.addTab(tab, "Configuration")

    def _create_strip_tab(self):
        """Create strip metadata tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Description
        desc_label = QLabel(
            "<h3>Strip Metadata Wizard</h3>"
            "<p>Remove all metadata from files. This is useful for:</p>"
            "<ul>"
            "<li>Privacy protection</li>"
            "<li>Removing identifying information</li>"
            "<li>Reducing file size</li>"
            "</ul>"
            "<p><b>Warning:</b> This operation cannot be undone!</p>"
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # File list
        layout.addWidget(QLabel("Files to process:"))

        self.strip_files_list = QListWidget()
        layout.addWidget(self.strip_files_list)

        # Add/remove buttons
        btn_layout = QHBoxLayout()

        add_files_btn = QPushButton("Add Files...")
        add_files_btn.clicked.connect(self._add_files_to_strip)
        btn_layout.addWidget(add_files_btn)

        remove_files_btn = QPushButton("Remove Selected")
        remove_files_btn.clicked.connect(
            lambda: self.strip_files_list.takeItem(self.strip_files_list.currentRow())
        )
        btn_layout.addWidget(remove_files_btn)

        clear_files_btn = QPushButton("Clear All")
        clear_files_btn.clicked.connect(self.strip_files_list.clear)
        btn_layout.addWidget(clear_files_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Options
        self.strip_backup_check = QCheckBox("Create backup files")
        self.strip_backup_check.setChecked(True)
        layout.addWidget(self.strip_backup_check)

        # Strip button
        strip_btn = QPushButton("Strip Metadata")
        strip_btn.clicked.connect(self._strip_metadata)
        strip_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; padding: 10px; }")
        layout.addWidget(strip_btn)

        self.tabs.addTab(tab, "Strip Metadata")

    def _create_rename_tab(self):
        """Create batch rename tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Description
        desc_label = QLabel(
            "<h3>Batch Rename by Metadata</h3>"
            "<p>Rename files using their metadata. Use patterns like:</p>"
            "<ul>"
            "<li><b>{Make}</b> - Camera make</li>"
            "<li><b>{Model}</b> - Camera model</li>"
            "<li><b>{DateTimeOriginal}</b> - Original date/time</li>"
            "<li><b>{counter:4}</b> - Counter with 4 digits</li>"
            "</ul>"
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Pattern input
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("Naming Pattern:"))

        self.rename_pattern_edit = QLineEdit()
        self.rename_pattern_edit.setPlaceholderText("{Make}_{Model}_{DateTimeOriginal}")
        pattern_layout.addWidget(self.rename_pattern_edit)

        layout.addLayout(pattern_layout)

        # File list
        layout.addWidget(QLabel("Files to rename:"))

        self.rename_files_list = QListWidget()
        layout.addWidget(self.rename_files_list)

        # Add/remove buttons
        btn_layout = QHBoxLayout()

        add_files_btn = QPushButton("Add Files...")
        add_files_btn.clicked.connect(self._add_files_to_rename)
        btn_layout.addWidget(add_files_btn)

        remove_files_btn = QPushButton("Remove Selected")
        remove_files_btn.clicked.connect(
            lambda: self.rename_files_list.takeItem(self.rename_files_list.currentRow())
        )
        btn_layout.addWidget(remove_files_btn)

        clear_files_btn = QPushButton("Clear All")
        clear_files_btn.clicked.connect(self.rename_files_list.clear)
        btn_layout.addWidget(clear_files_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Buttons
        action_layout = QHBoxLayout()

        preview_btn = QPushButton("Preview")
        preview_btn.clicked.connect(self._preview_rename)
        action_layout.addWidget(preview_btn)

        rename_btn = QPushButton("Rename Files")
        rename_btn.clicked.connect(self._batch_rename)
        rename_btn.setStyleSheet("QPushButton { background-color: #28a745; color: white; padding: 10px; }")
        action_layout.addWidget(rename_btn)

        action_layout.addStretch()
        layout.addLayout(action_layout)

        self.tabs.addTab(tab, "Batch Rename")

    def _create_command_tab(self):
        """Create custom command tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Description
        desc_label = QLabel(
            "<h3>Custom ExifTool Command</h3>"
            "<p>Execute custom ExifTool commands. See "
            "<a href='https://exiftool.org/'>ExifTool documentation</a> for available options.</p>"
        )
        desc_label.setWordWrap(True)
        desc_label.setOpenExternalLinks(True)
        layout.addWidget(desc_label)

        # Command input
        layout.addWidget(QLabel("ExifTool Arguments (without 'exiftool'):"))

        self.command_edit = QTextEdit()
        self.command_edit.setPlaceholderText(
            "Example:\n"
            "-json -G file.jpg\n"
            "-Make=\"Canon\" -Model=\"EOS 5D\" file.jpg\n"
            "-all= -overwrite_original file.jpg"
        )
        self.command_edit.setMaximumHeight(100)
        layout.addWidget(self.command_edit)

        # Execute button
        execute_btn = QPushButton("Execute Command")
        execute_btn.clicked.connect(self._execute_custom_command)
        layout.addWidget(execute_btn)

        # Output
        layout.addWidget(QLabel("Output:"))

        self.command_output = QTextEdit()
        self.command_output.setReadOnly(True)
        self.command_output.setFont(QFont("Consolas", 9))
        layout.addWidget(self.command_output)

        self.tabs.addTab(tab, "Custom Command")

    def _browse_exiftool_path(self):
        """Browse for ExifTool executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select ExifTool Executable",
            "",
            "Executable Files (*.exe);;All Files (*.*)"
        )

        if file_path:
            self.custom_path_edit.setText(file_path)

    def _test_exiftool(self):
        """Test ExifTool installation"""
        path = self.custom_path_edit.text().strip()

        if not path:
            QMessageBox.warning(self, "Warning", "Please enter ExifTool path")
            return

        try:
            # Create temporary ExifTool instance
            test_exiftool = ExifToolWrapper(path)

            version = test_exiftool.get_version()

            QMessageBox.information(
                self,
                "Success",
                f"ExifTool is working!\n\nVersion: {version}\nPath: {path}"
            )

            # Update main instance
            self.exiftool = test_exiftool
            self.editor = MetadataEditor(self.exiftool)
            self.exiftool_available = True

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"ExifTool test failed:\n{str(e)}"
            )

    def _show_all_formats(self):
        """Show all supported formats"""
        if not self.exiftool_available:
            return

        formats = self.exiftool.get_supported_formats()

        dialog = QDialog(self)
        dialog.setWindowTitle("Supported Formats")
        dialog.resize(600, 400)

        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText("\n".join(formats))
        layout.addWidget(text_edit)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def _add_files_to_strip(self):
        """Add files to strip list"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            "",
            "All Files (*.*)"
        )

        for file_path in file_paths:
            self.strip_files_list.addItem(file_path)

    def _strip_metadata(self):
        """Strip metadata from selected files"""
        if not self.exiftool_available:
            QMessageBox.critical(self, "Error", "ExifTool not available")
            return

        # Get files
        files = []
        for i in range(self.strip_files_list.count()):
            files.append(self.strip_files_list.item(i).text())

        if not files:
            QMessageBox.information(self, "Info", "No files selected")
            return

        # Confirm
        reply = QMessageBox.question(
            self,
            "Confirm",
            f"Strip metadata from {len(files)} file(s)?\n\nThis cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Process
        backup = not self.strip_backup_check.isChecked()

        progress = QProgressDialog("Stripping metadata...", "Cancel", 0, len(files), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)

        def progress_callback(current, total):
            progress.setValue(current)
            QApplication.processEvents()
            if progress.wasCanceled():
                return

        results = self.editor.strip_metadata_batch(files, backup, progress_callback)

        progress.close()

        # Show results
        success_count = sum(1 for v in results.values() if v)
        fail_count = len(results) - success_count

        QMessageBox.information(
            self,
            "Complete",
            f"Metadata stripped from {success_count} file(s)\n"
            f"Failed: {fail_count}"
        )

        # Clear list
        self.strip_files_list.clear()

    def _add_files_to_rename(self):
        """Add files to rename list"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            "",
            "All Files (*.*)"
        )

        for file_path in file_paths:
            self.rename_files_list.addItem(file_path)

    def _preview_rename(self):
        """Preview batch rename"""
        if not self.exiftool_available:
            QMessageBox.critical(self, "Error", "ExifTool not available")
            return

        pattern = self.rename_pattern_edit.text().strip()
        if not pattern:
            QMessageBox.warning(self, "Warning", "Please enter a naming pattern")
            return

        # Get files
        files = []
        for i in range(self.rename_files_list.count()):
            files.append(self.rename_files_list.item(i).text())

        if not files:
            QMessageBox.information(self, "Info", "No files selected")
            return

        # Preview
        try:
            renames = self.editor.rename_by_metadata(files, pattern, dry_run=True)

            # Show preview
            dialog = QDialog(self)
            dialog.setWindowTitle("Rename Preview")
            dialog.resize(700, 400)

            layout = QVBoxLayout(dialog)

            text_edit = QTextEdit()
            text_edit.setReadOnly(True)

            preview_text = []
            for old_path, new_path in renames.items():
                preview_text.append(f"OLD: {os.path.basename(old_path)}")
                preview_text.append(f"NEW: {os.path.basename(new_path)}")
                preview_text.append("")

            text_edit.setPlainText("\n".join(preview_text))
            layout.addWidget(text_edit)

            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Preview failed:\n{str(e)}")

    def _batch_rename(self):
        """Batch rename files"""
        if not self.exiftool_available:
            QMessageBox.critical(self, "Error", "ExifTool not available")
            return

        pattern = self.rename_pattern_edit.text().strip()
        if not pattern:
            QMessageBox.warning(self, "Warning", "Please enter a naming pattern")
            return

        # Get files
        files = []
        for i in range(self.rename_files_list.count()):
            files.append(self.rename_files_list.item(i).text())

        if not files:
            QMessageBox.information(self, "Info", "No files selected")
            return

        # Confirm
        reply = QMessageBox.question(
            self,
            "Confirm",
            f"Rename {len(files)} file(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Rename
        try:
            renames = self.editor.rename_by_metadata(files, pattern, dry_run=False)

            QMessageBox.information(
                self,
                "Success",
                f"Renamed {len(renames)} file(s)"
            )

            # Clear list
            self.rename_files_list.clear()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Rename failed:\n{str(e)}")

    def _execute_custom_command(self):
        """Execute custom ExifTool command"""
        if not self.exiftool_available:
            QMessageBox.critical(self, "Error", "ExifTool not available")
            return

        command_text = self.command_edit.toPlainText().strip()
        if not command_text:
            QMessageBox.warning(self, "Warning", "Please enter a command")
            return

        # Parse arguments
        args = command_text.split()

        try:
            # Execute
            result = self.exiftool.execute_command(args, timeout=60)

            # Show output
            output = []
            output.append("=== STDOUT ===")
            output.append(result.stdout if result.stdout else "(empty)")
            output.append("")
            output.append("=== STDERR ===")
            output.append(result.stderr if result.stderr else "(empty)")
            output.append("")
            output.append(f"=== Return Code: {result.returncode} ===")

            self.command_output.setPlainText("\n".join(output))

        except Exception as e:
            self.command_output.setPlainText(f"ERROR: {str(e)}")
