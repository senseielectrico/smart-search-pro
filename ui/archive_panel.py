"""
Archive Manager Panel
Browse, extract, and create archives with a modern interface
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QLineEdit, QSlider, QProgressBar, QFileDialog,
    QMessageBox, QSplitter, QGroupBox, QFormLayout, QComboBox, QSpinBox,
    QCheckBox, QDialog, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QIcon
import os
from pathlib import Path
from typing import Optional, List

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from archive.sevenzip_manager import (
    SevenZipManager, CompressionLevel, ArchiveFormat, ExtractionProgress
)
from archive.archive_analyzer import ArchiveAnalyzer, ArchiveStats
from archive.recursive_extractor import RecursiveExtractor, RecursiveProgress


class ExtractionThread(QThread):
    """Background thread for extraction"""
    progress_updated = pyqtSignal(object)
    finished = pyqtSignal(bool, str)

    def __init__(self, manager, archive_path, destination, password, recursive, flatten):
        super().__init__()
        self.manager = manager
        self.archive_path = archive_path
        self.destination = destination
        self.password = password
        self.recursive = recursive
        self.flatten = flatten

    def run(self):
        try:
            if self.recursive:
                extractor = RecursiveExtractor()
                result = extractor.extract_recursive(
                    archive_path=self.archive_path,
                    destination=self.destination,
                    password=self.password,
                    flatten=self.flatten,
                    progress_callback=self.progress_updated.emit
                )
                message = f"Extracted {result.get('files_extracted', 0)} files from {result.get('archives_extracted', 0)} archives"
                self.finished.emit(True, message)
            else:
                self.manager.extract(
                    archive_path=self.archive_path,
                    destination=self.destination,
                    password=self.password,
                    progress_callback=self.progress_updated.emit
                )
                self.finished.emit(True, "Extraction completed successfully")

        except Exception as e:
            self.finished.emit(False, str(e))


class ArchivePanel(QWidget):
    """
    Archive manager with full 7-Zip integration:
    - Browse archive contents in tree view
    - Extract selected files or all
    - Extract here / extract to folder
    - Create archive wizard
    - Compression level slider
    - Password protection
    - Progress dialog with cancel
    - Preview file tree
    """

    archive_opened = pyqtSignal(str)
    extraction_completed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.seven_zip = SevenZipManager()
        self.analyzer = ArchiveAnalyzer()
        self.current_archive = None
        self.current_password = None
        self.extraction_thread = None

        self._init_ui()

    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Top toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Splitter for tree and info
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Archive tree view
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['Name', 'Size', 'Packed Size', 'Type'])
        self.tree.setAlternatingRowColors(True)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        splitter.addWidget(self.tree)

        # Info panel
        info_panel = self._create_info_panel()
        splitter.addWidget(info_panel)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        # Bottom action bar
        action_bar = self._create_action_bar()
        layout.addWidget(action_bar)

    def _create_toolbar(self) -> QWidget:
        """Create top toolbar"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)

        # Open archive button
        self.open_btn = QPushButton("Open Archive")
        self.open_btn.clicked.connect(self.open_archive)
        layout.addWidget(self.open_btn)

        # Archive path label
        self.archive_label = QLabel("No archive opened")
        self.archive_label.setStyleSheet("color: #888;")
        layout.addWidget(self.archive_label, 1)

        # Password field
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Optional")
        self.password_input.setMaximumWidth(150)
        self.password_input.textChanged.connect(self._on_password_changed)
        layout.addWidget(self.password_input)

        # Reload button
        self.reload_btn = QPushButton("Reload")
        self.reload_btn.clicked.connect(self.reload_archive)
        self.reload_btn.setEnabled(False)
        layout.addWidget(self.reload_btn)

        return toolbar

    def _create_info_panel(self) -> QWidget:
        """Create info panel"""
        group = QGroupBox("Archive Information")
        layout = QFormLayout(group)

        self.info_files = QLabel("0")
        self.info_folders = QLabel("0")
        self.info_size = QLabel("0 B")
        self.info_packed = QLabel("0 B")
        self.info_ratio = QLabel("0%")
        self.info_encrypted = QLabel("No")

        layout.addRow("Files:", self.info_files)
        layout.addRow("Folders:", self.info_folders)
        layout.addRow("Uncompressed:", self.info_size)
        layout.addRow("Compressed:", self.info_packed)
        layout.addRow("Ratio:", self.info_ratio)
        layout.addRow("Encrypted:", self.info_encrypted)

        return group

    def _create_action_bar(self) -> QWidget:
        """Create bottom action bar"""
        action_bar = QWidget()
        layout = QHBoxLayout(action_bar)

        # Extract buttons
        self.extract_all_btn = QPushButton("Extract All")
        self.extract_all_btn.clicked.connect(self.extract_all)
        self.extract_all_btn.setEnabled(False)
        layout.addWidget(self.extract_all_btn)

        self.extract_selected_btn = QPushButton("Extract Selected")
        self.extract_selected_btn.clicked.connect(self.extract_selected)
        self.extract_selected_btn.setEnabled(False)
        layout.addWidget(self.extract_selected_btn)

        self.extract_here_btn = QPushButton("Extract Here")
        self.extract_here_btn.clicked.connect(self.extract_here)
        self.extract_here_btn.setEnabled(False)
        layout.addWidget(self.extract_here_btn)

        layout.addStretch()

        # Create archive button
        self.create_btn = QPushButton("Create Archive")
        self.create_btn.clicked.connect(self.create_archive)
        layout.addWidget(self.create_btn)

        # Test archive button
        self.test_btn = QPushButton("Test Archive")
        self.test_btn.clicked.connect(self.test_archive)
        self.test_btn.setEnabled(False)
        layout.addWidget(self.test_btn)

        return action_bar

    def open_archive(self):
        """Open and display archive contents"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Archive",
            "",
            "All Archives (*.7z *.zip *.rar *.tar *.gz *.bz2 *.xz *.iso);;7-Zip (*.7z);;ZIP (*.zip);;RAR (*.rar);;All Files (*.*)"
        )

        if file_path:
            self.load_archive(file_path)

    def load_archive(self, archive_path: str):
        """Load archive and display contents"""
        try:
            self.current_archive = archive_path
            self.archive_label.setText(os.path.basename(archive_path))
            self.archive_label.setStyleSheet("")

            # Analyze archive
            stats = self.analyzer.analyze(
                archive_path,
                password=self.current_password,
                detect_nested=True
            )

            # Update info
            self._update_info(stats)

            # Load tree
            self._load_tree(archive_path)

            # Enable buttons
            self.extract_all_btn.setEnabled(True)
            self.extract_selected_btn.setEnabled(True)
            self.extract_here_btn.setEnabled(True)
            self.test_btn.setEnabled(True)
            self.reload_btn.setEnabled(True)

            self.archive_opened.emit(archive_path)

        except ValueError as e:
            QMessageBox.warning(
                self,
                "Wrong Password",
                "The archive is encrypted. Please enter the correct password."
            )
            self.password_input.setFocus()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open archive:\n{str(e)}"
            )

    def _update_info(self, stats: ArchiveStats):
        """Update info panel with stats"""
        self.info_files.setText(str(stats.total_files))
        self.info_folders.setText(str(stats.total_folders))
        self.info_size.setText(self._format_size(stats.total_size))
        self.info_packed.setText(self._format_size(stats.packed_size))
        self.info_ratio.setText(f"{stats.compression_ratio:.1f}%")
        self.info_encrypted.setText("Yes" if stats.is_encrypted else "No")

    def _load_tree(self, archive_path: str):
        """Load archive contents into tree"""
        self.tree.clear()

        try:
            entries = self.seven_zip.list_contents(
                archive_path,
                password=self.current_password
            )

            # Build tree structure
            root_items = {}

            for entry in entries:
                path = entry.get('Path', '')
                size = entry.get('Size', 0)
                packed = entry.get('PackedSize', 0)
                is_dir = entry.get('IsDirectory', False)

                parts = path.replace('\\', '/').split('/')

                # Find or create parent
                parent = None
                current_path = ""

                for part in parts[:-1]:
                    current_path = f"{current_path}/{part}" if current_path else part

                    if current_path not in root_items:
                        item = QTreeWidgetItem([part, '', '', 'Folder'])
                        if parent:
                            parent.addChild(item)
                        else:
                            self.tree.addTopLevelItem(item)
                        root_items[current_path] = item
                        parent = item
                    else:
                        parent = root_items[current_path]

                # Add final item
                if parts:
                    item_type = 'Folder' if is_dir else 'File'
                    item = QTreeWidgetItem([
                        parts[-1],
                        self._format_size(size) if not is_dir else '',
                        self._format_size(packed) if not is_dir else '',
                        item_type
                    ])

                    if parent:
                        parent.addChild(item)
                    else:
                        self.tree.addTopLevelItem(item)

            # Resize columns
            for i in range(4):
                self.tree.resizeColumnToContents(i)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load archive contents:\n{str(e)}"
            )

    def extract_all(self):
        """Extract all files"""
        if not self.current_archive:
            return

        from .extract_dialog import ExtractDialog

        dialog = ExtractDialog(self.current_archive, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            options = dialog.get_options()
            self._perform_extraction(
                destination=options['destination'],
                recursive=options['recursive'],
                flatten=options['flatten']
            )

    def extract_selected(self):
        """Extract selected files"""
        selected_items = self.tree.selectedItems()

        if not selected_items:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select files or folders to extract."
            )
            return

        # Get selected paths
        paths = []
        for item in selected_items:
            path = self._get_item_path(item)
            if path:
                paths.append(path)

        # Choose destination
        destination = QFileDialog.getExistingDirectory(
            self,
            "Select Extraction Destination"
        )

        if destination:
            self._perform_extraction(destination, files=paths)

    def extract_here(self):
        """Extract to same directory as archive"""
        if not self.current_archive:
            return

        archive_dir = os.path.dirname(self.current_archive)
        archive_name = Path(self.current_archive).stem

        destination = os.path.join(archive_dir, archive_name)

        self._perform_extraction(destination)

    def _perform_extraction(
        self,
        destination: str,
        files: Optional[List[str]] = None,
        recursive: bool = False,
        flatten: bool = False
    ):
        """Perform extraction with progress dialog"""
        # Create progress dialog
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle("Extracting Archive")
        progress_dialog.setModal(True)
        progress_dialog.setMinimumWidth(400)

        layout = QVBoxLayout(progress_dialog)

        status_label = QLabel("Preparing extraction...")
        layout.addWidget(status_label)

        progress_bar = QProgressBar()
        layout.addWidget(progress_bar)

        file_label = QLabel("")
        file_label.setStyleSheet("color: #666;")
        layout.addWidget(file_label)

        cancel_btn = QPushButton("Cancel")
        layout.addWidget(cancel_btn)

        # Start extraction thread
        self.extraction_thread = ExtractionThread(
            self.seven_zip,
            self.current_archive,
            destination,
            self.current_password,
            recursive,
            flatten
        )

        def update_progress(progress):
            if hasattr(progress, 'percentage'):
                progress_bar.setValue(int(progress.percentage))
                file_label.setText(progress.current_file)
            elif hasattr(progress, 'processed_archives'):
                status_label.setText(
                    f"Extracted {progress.processed_archives} of {progress.total_archives} archives"
                )
                file_label.setText(progress.current_file)

        def on_finished(success, message):
            progress_dialog.close()
            if success:
                QMessageBox.information(
                    self,
                    "Extraction Complete",
                    message
                )
                self.extraction_completed.emit(destination)
            else:
                QMessageBox.critical(
                    self,
                    "Extraction Failed",
                    message
                )

        def on_cancel():
            if self.extraction_thread:
                self.seven_zip.cancel_extraction()
            progress_dialog.close()

        self.extraction_thread.progress_updated.connect(update_progress)
        self.extraction_thread.finished.connect(on_finished)
        cancel_btn.clicked.connect(on_cancel)

        self.extraction_thread.start()
        progress_dialog.exec()

    def create_archive(self):
        """Show create archive wizard"""
        # Select files to archive
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files to Archive"
        )

        if not files:
            return

        # Show options dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Archive")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        # Archive name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Archive Name:"))
        name_input = QLineEdit()
        name_input.setText("archive.7z")
        name_layout.addWidget(name_input)
        layout.addLayout(name_layout)

        # Format
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        format_combo = QComboBox()
        format_combo.addItems(['7z', 'zip', 'tar'])
        format_layout.addWidget(format_combo)
        layout.addLayout(format_layout)

        # Compression level
        comp_layout = QVBoxLayout()
        comp_layout.addWidget(QLabel("Compression Level:"))
        comp_slider = QSlider(Qt.Orientation.Horizontal)
        comp_slider.setMinimum(0)
        comp_slider.setMaximum(9)
        comp_slider.setValue(5)
        comp_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        comp_layout.addWidget(comp_slider)
        comp_label = QLabel("Normal (5)")
        comp_layout.addWidget(comp_label)
        layout.addLayout(comp_layout)

        def update_comp_label(value):
            levels = ['Store', 'Fastest', '', 'Fast', '', 'Normal', '', 'Maximum', '', 'Ultra']
            comp_label.setText(f"{levels[value]} ({value})")

        comp_slider.valueChanged.connect(update_comp_label)

        # Password
        pwd_check = QCheckBox("Password Protection")
        layout.addWidget(pwd_check)

        pwd_input = QLineEdit()
        pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        pwd_input.setEnabled(False)
        layout.addWidget(pwd_input)

        pwd_check.toggled.connect(pwd_input.setEnabled)

        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        create_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get destination
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Archive As",
                name_input.text()
            )

            if save_path:
                try:
                    format_map = {
                        '7z': ArchiveFormat.SEVEN_ZIP,
                        'zip': ArchiveFormat.ZIP,
                        'tar': ArchiveFormat.TAR
                    }

                    self.seven_zip.create_archive(
                        archive_path=save_path,
                        source_paths=files,
                        format=format_map[format_combo.currentText()],
                        compression_level=CompressionLevel(comp_slider.value()),
                        password=pwd_input.text() if pwd_check.isChecked() else None
                    )

                    QMessageBox.information(
                        self,
                        "Success",
                        "Archive created successfully!"
                    )

                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to create archive:\n{str(e)}"
                    )

    def test_archive(self):
        """Test archive integrity"""
        if not self.current_archive:
            return

        try:
            success, message = self.seven_zip.test_archive(
                self.current_archive,
                password=self.current_password
            )

            if success:
                QMessageBox.information(
                    self,
                    "Test Result",
                    "Archive is valid - no errors found."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Test Result",
                    f"Archive test failed:\n{message}"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to test archive:\n{str(e)}"
            )

    def reload_archive(self):
        """Reload current archive"""
        if self.current_archive:
            self.load_archive(self.current_archive)

    def _on_password_changed(self, password: str):
        """Handle password change"""
        self.current_password = password if password else None

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item double-click"""
        # Could add preview functionality here
        pass

    def _get_item_path(self, item: QTreeWidgetItem) -> str:
        """Get full path of tree item"""
        parts = []
        current = item

        while current:
            parts.insert(0, current.text(0))
            current = current.parent()

        return '/'.join(parts)

    def _format_size(self, size: int) -> str:
        """Format size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
