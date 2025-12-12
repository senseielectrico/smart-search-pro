"""
Preview Panel - File preview with syntax highlighting and metadata
"""

import os
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QFrame, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QImage, QFont
from .widgets import FileIcon, EmptyStateWidget


class PreviewPanel(QWidget):
    """Preview panel for file content and metadata"""

    # Signals
    open_requested = pyqtSignal(str)
    open_location_requested = pyqtSignal(str)

    # Preview limits
    MAX_TEXT_SIZE = 1024 * 100  # 100 KB
    MAX_IMAGE_SIZE = 1024 * 1024 * 10  # 10 MB

    # Text file extensions
    TEXT_EXTENSIONS = {
        '.txt', '.log', '.md', '.json', '.xml', '.csv', '.ini', '.cfg',
        '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.php',
        '.html', '.css', '.scss', '.yaml', '.yml', '.toml', '.sh', '.bat',
        '.ps1', '.rb', '.go', '.rs', '.sql', '.r', '.m', '.swift'
    }

    # Image extensions
    IMAGE_EXTENSIONS = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.ico'
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_file: Optional[str] = None

        self._init_ui()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Content area (scrollable)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.content_layout.setSpacing(12)

        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)

        # Empty state
        self.empty_state = EmptyStateWidget(
            "👁",
            "No Preview",
            "Select a file to preview"
        )
        layout.addWidget(self.empty_state)

        # Initially show empty state
        self._show_content(False)

    def _create_header(self) -> QWidget:
        """Create header with file info and actions"""
        header = QFrame()
        header.setFrameShape(QFrame.Shape.StyledPanel)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(8, 8, 8, 8)
        header_layout.setSpacing(6)

        # File name row
        name_row = QHBoxLayout()

        self.file_icon = FileIcon("", size=32)
        name_row.addWidget(self.file_icon)

        self.file_name_label = QLabel("")
        self.file_name_label.setProperty("heading", True)
        self.file_name_label.setWordWrap(True)
        name_row.addWidget(self.file_name_label, stretch=1)

        header_layout.addLayout(name_row)

        # Action buttons row
        actions_row = QHBoxLayout()

        self.open_btn = QPushButton("Open")
        self.open_btn.clicked.connect(self._on_open_clicked)
        actions_row.addWidget(self.open_btn)

        self.open_location_btn = QPushButton("Open Location")
        self.open_location_btn.setProperty("secondary", True)
        self.open_location_btn.clicked.connect(self._on_open_location_clicked)
        actions_row.addWidget(self.open_location_btn)

        actions_row.addStretch()

        header_layout.addLayout(actions_row)

        return header

    def set_file(self, file_path: str):
        """Set file to preview"""
        self.current_file = file_path

        if not file_path or not os.path.exists(file_path):
            self._show_content(False)
            return

        # Update header
        self._update_header(file_path)

        # Clear previous content
        self._clear_content()

        # Show content area
        self._show_content(True)

        # Load preview based on file type
        self._load_preview(file_path)

    def _update_header(self, file_path: str):
        """Update header with file info"""
        name = Path(file_path).name
        self.file_name_label.setText(name)
        self.file_icon = FileIcon(name, size=32)

    def _clear_content(self):
        """Clear content area"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_content(self, show: bool):
        """Show/hide content vs empty state"""
        self.scroll_area.setVisible(show)
        self.empty_state.setVisible(not show)

    def _load_preview(self, file_path: str):
        """Load file preview"""
        ext = Path(file_path).suffix.lower()

        try:
            # Metadata (always shown)
            self._add_metadata_section(file_path)

            # Type-specific preview
            if ext in self.IMAGE_EXTENSIONS:
                self._add_image_preview(file_path)
            elif ext in self.TEXT_EXTENSIONS:
                self._add_text_preview(file_path)
            else:
                self._add_no_preview_message()

        except Exception as e:
            self._add_error_message(str(e))

    def _add_metadata_section(self, file_path: str):
        """Add metadata section"""
        metadata_group = QGroupBox("File Information")
        metadata_layout = QVBoxLayout()

        try:
            stat = os.stat(file_path)

            # Path
            path_label = self._create_info_row("Path:", str(Path(file_path).parent))
            metadata_layout.addWidget(path_label)

            # Size
            size = self._format_size(stat.st_size)
            size_label = self._create_info_row("Size:", size)
            metadata_layout.addWidget(size_label)

            # Type
            ext = Path(file_path).suffix.upper() or "FILE"
            type_label = self._create_info_row("Type:", ext)
            metadata_layout.addWidget(type_label)

            # Modified
            from datetime import datetime
            modified = datetime.fromtimestamp(stat.st_mtime)
            modified_label = self._create_info_row("Modified:", modified.strftime("%Y-%m-%d %H:%M:%S"))
            metadata_layout.addWidget(modified_label)

            # Created
            created = datetime.fromtimestamp(stat.st_ctime)
            created_label = self._create_info_row("Created:", created.strftime("%Y-%m-%d %H:%M:%S"))
            metadata_layout.addWidget(created_label)

        except Exception as e:
            error_label = QLabel(f"Error reading metadata: {e}")
            error_label.setStyleSheet("color: #D13438;")
            metadata_layout.addWidget(error_label)

        metadata_group.setLayout(metadata_layout)
        self.content_layout.addWidget(metadata_group)

    def _create_info_row(self, label: str, value: str) -> QWidget:
        """Create info row widget"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 2, 0, 2)

        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-weight: 600; color: #605E5C;")
        layout.addWidget(label_widget)

        value_widget = QLabel(value)
        value_widget.setWordWrap(True)
        layout.addWidget(value_widget, stretch=1)

        return widget

    def _add_image_preview(self, file_path: str):
        """Add image preview"""
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()

        try:
            # Check file size
            size = os.path.getsize(file_path)
            if size > self.MAX_IMAGE_SIZE:
                msg = QLabel(f"Image too large to preview ({self._format_size(size)})")
                msg.setStyleSheet("color: #8A8886;")
                preview_layout.addWidget(msg)
            else:
                # Load and display image
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    # Scale to fit
                    max_size = QSize(400, 400)
                    scaled_pixmap = pixmap.scaled(
                        max_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )

                    image_label = QLabel()
                    image_label.setPixmap(scaled_pixmap)
                    image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    preview_layout.addWidget(image_label)

                    # Image dimensions
                    dims_label = QLabel(f"Dimensions: {pixmap.width()} × {pixmap.height()}")
                    dims_label.setStyleSheet("color: #8A8886;")
                    dims_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    preview_layout.addWidget(dims_label)
                else:
                    raise Exception("Failed to load image")

        except Exception as e:
            error_label = QLabel(f"Error loading image: {e}")
            error_label.setStyleSheet("color: #D13438;")
            preview_layout.addWidget(error_label)

        preview_group.setLayout(preview_layout)
        self.content_layout.addWidget(preview_group)

    def _add_text_preview(self, file_path: str):
        """Add text file preview with syntax highlighting"""
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()

        try:
            # Check file size
            size = os.path.getsize(file_path)
            if size > self.MAX_TEXT_SIZE:
                msg = QLabel(f"File too large to preview ({self._format_size(size)})")
                msg.setStyleSheet("color: #8A8886;")
                preview_layout.addWidget(msg)
            else:
                # Read file content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Create text edit
                text_edit = QTextEdit()
                text_edit.setReadOnly(True)
                text_edit.setPlainText(content)
                text_edit.setFont(QFont("Consolas", 9))
                text_edit.setMinimumHeight(300)

                # Basic styling
                text_edit.setStyleSheet("""
                    QTextEdit {
                        background-color: #F9F9F9;
                        border: 1px solid #E1DFDD;
                        border-radius: 4px;
                        padding: 8px;
                    }
                """)

                preview_layout.addWidget(text_edit)

                # Line count
                line_count = content.count('\n') + 1
                lines_label = QLabel(f"Lines: {line_count}")
                lines_label.setStyleSheet("color: #8A8886;")
                preview_layout.addWidget(lines_label)

        except Exception as e:
            error_label = QLabel(f"Error loading file: {e}")
            error_label.setStyleSheet("color: #D13438;")
            preview_layout.addWidget(error_label)

        preview_group.setLayout(preview_layout)
        self.content_layout.addWidget(preview_group)

    def _add_no_preview_message(self):
        """Add no preview available message"""
        msg = QLabel("Preview not available for this file type")
        msg.setStyleSheet("color: #8A8886; padding: 20px;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(msg)

    def _add_error_message(self, error: str):
        """Add error message"""
        error_label = QLabel(f"Error: {error}")
        error_label.setStyleSheet("color: #D13438; padding: 20px;")
        error_label.setWordWrap(True)
        self.content_layout.addWidget(error_label)

    def _format_size(self, size: int) -> str:
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def _on_open_clicked(self):
        """Handle open button click"""
        if self.current_file:
            self.open_requested.emit(self.current_file)

    def _on_open_location_clicked(self):
        """Handle open location button click"""
        if self.current_file:
            self.open_location_requested.emit(self.current_file)

    def clear(self):
        """Clear preview"""
        self.current_file = None
        self._clear_content()
        self._show_content(False)
