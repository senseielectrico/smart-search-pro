"""
Enhanced Preview Panel - Advanced file preview with lazy loading and interactive features

Features:
- Syntax highlighting for 40+ languages
- Line numbers and word wrap toggle
- Find in preview (Ctrl+F)
- Image zoom controls and rotation
- EXIF metadata display
- PDF multi-page scrolling
- Markdown rendering
- JSON formatting
- Thumbnail caching
- Lazy loading with animated placeholder
"""

import os
import sys
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QFrame, QGroupBox, QToolBar,
    QSizePolicy, QLineEdit, QSlider, QSpinBox, QTextBrowser,
    QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer, QThread, pyqtSlot
from PyQt6.QtGui import QPixmap, QImage, QFont, QTransform, QTextCursor

# Optional: QWebEngineView for advanced HTML rendering
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preview.manager import PreviewManager
from preview.text_preview import TextPreviewer
from preview.image_preview import ImagePreviewer
from preview.document_preview import DocumentPreviewer


class LoadingPlaceholder(QWidget):
    """Animated loading placeholder"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._animation_frame = 0
        self._timer = QTimer()
        self._timer.timeout.connect(self._animate)
        self._timer.start(100)  # 100ms animation

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label = QLabel("Loading preview...")
        self.label.setStyleSheet("color: #8A8886; font-size: 14px;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.progress = QLabel("▪▪▪")
        self.progress.setStyleSheet("color: #0078D4; font-size: 24px;")
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress)

    def _animate(self):
        dots = ["▪", "▪▪", "▪▪▪", "▪▪▪▪", "▪▪▪"]
        self.progress.setText(dots[self._animation_frame % len(dots)])
        self._animation_frame += 1

    def stop(self):
        self._timer.stop()


class PreviewLoaderThread(QThread):
    """Background thread for loading previews"""

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, preview_manager: PreviewManager, file_path: str):
        super().__init__()
        self.preview_manager = preview_manager
        self.file_path = file_path

    def run(self):
        try:
            preview = self.preview_manager.get_preview(self.file_path)
            self.finished.emit(preview)
        except Exception as e:
            self.error.emit(str(e))


class FindDialog(QWidget):
    """Find in text widget"""

    find_next = pyqtSignal(str, bool)  # text, case_sensitive
    close_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Find in preview...")
        self.search_input.returnPressed.connect(self._on_find_next)
        layout.addWidget(self.search_input, stretch=1)

        find_btn = QPushButton("Next")
        find_btn.clicked.connect(self._on_find_next)
        layout.addWidget(find_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedWidth(30)
        close_btn.clicked.connect(self.close_requested.emit)
        layout.addWidget(close_btn)

        self.setStyleSheet("""
            QWidget {
                background: #F3F2F1;
                border-top: 1px solid #E1DFDD;
            }
            QLineEdit {
                background: white;
                border: 1px solid #8A8886;
                padding: 4px;
                border-radius: 2px;
            }
            QPushButton {
                background: #0078D4;
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background: #106EBE;
            }
        """)

    def _on_find_next(self):
        text = self.search_input.text()
        if text:
            self.find_next.emit(text, False)

    def focus_search(self):
        self.search_input.setFocus()
        self.search_input.selectAll()


class EnhancedPreviewPanel(QWidget):
    """Enhanced preview panel with advanced features"""

    open_requested = pyqtSignal(str)
    open_location_requested = pyqtSignal(str)

    # Preview limits
    MAX_TEXT_SIZE = 1024 * 500  # 500 KB
    MAX_IMAGE_SIZE = 1024 * 1024 * 50  # 50 MB

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_file: Optional[str] = None
        self.current_zoom = 100  # Percentage
        self.current_rotation = 0  # Degrees
        self.original_pixmap: Optional[QPixmap] = None

        # Initialize preview manager with cache
        cache_dir = os.path.join(Path.home(), '.smart_search', 'preview_cache')
        self.preview_manager = PreviewManager(
            cache_dir=cache_dir,
            memory_cache_size=50,
            cache_ttl_hours=48
        )

        self.text_previewer = TextPreviewer()
        self.image_previewer = ImagePreviewer()
        self.doc_previewer = DocumentPreviewer()

        self._loader_thread: Optional[PreviewLoaderThread] = None

        self._init_ui()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Toolbar (hidden by default)
        self.toolbar = self._create_toolbar()
        self.toolbar.setVisible(False)
        layout.addWidget(self.toolbar)

        # Stacked widget for different content types
        self.content_stack = QStackedWidget()
        layout.addWidget(self.content_stack)

        # Loading placeholder
        self.loading_widget = LoadingPlaceholder()
        self.content_stack.addWidget(self.loading_widget)

        # Scroll area for preview content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.content_layout.setSpacing(12)

        self.scroll_area.setWidget(self.content_widget)
        self.content_stack.addWidget(self.scroll_area)

        # Empty state
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label = QLabel("Select a file to preview")
        empty_label.setStyleSheet("color: #8A8886; font-size: 14px;")
        empty_layout.addWidget(empty_label)
        self.content_stack.addWidget(self.empty_widget)

        # Find dialog (hidden)
        self.find_dialog = FindDialog()
        self.find_dialog.find_next.connect(self._on_find_text)
        self.find_dialog.close_requested.connect(self._hide_find)
        self.find_dialog.setVisible(False)
        layout.addWidget(self.find_dialog)

        # Show empty state initially
        self.content_stack.setCurrentWidget(self.empty_widget)

    def _create_header(self) -> QWidget:
        """Create header with file info"""
        header = QFrame()
        header.setFrameShape(QFrame.Shape.StyledPanel)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(8, 8, 8, 8)
        header_layout.setSpacing(6)

        # File name
        self.file_name_label = QLabel("")
        self.file_name_label.setStyleSheet("font-weight: 600; font-size: 12px;")
        self.file_name_label.setWordWrap(True)
        header_layout.addWidget(self.file_name_label)

        # Actions
        actions_row = QHBoxLayout()
        actions_row.setSpacing(4)

        self.open_btn = QPushButton("Open")
        self.open_btn.clicked.connect(self._on_open_clicked)
        actions_row.addWidget(self.open_btn)

        self.open_location_btn = QPushButton("Location")
        self.open_location_btn.clicked.connect(self._on_open_location_clicked)
        actions_row.addWidget(self.open_location_btn)

        actions_row.addStretch()

        header_layout.addLayout(actions_row)

        return header

    def _create_toolbar(self) -> QToolBar:
        """Create toolbar for preview controls"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))

        # Text controls
        self.line_numbers_btn = QPushButton("Line Numbers")
        self.line_numbers_btn.setCheckable(True)
        self.line_numbers_btn.setChecked(True)
        self.line_numbers_btn.clicked.connect(self._toggle_line_numbers)
        toolbar.addWidget(self.line_numbers_btn)

        self.word_wrap_btn = QPushButton("Word Wrap")
        self.word_wrap_btn.setCheckable(True)
        self.word_wrap_btn.clicked.connect(self._toggle_word_wrap)
        toolbar.addWidget(self.word_wrap_btn)

        self.find_btn = QPushButton("Find (Ctrl+F)")
        self.find_btn.clicked.connect(self._show_find)
        toolbar.addWidget(self.find_btn)

        toolbar.addSeparator()

        # Image controls
        self.zoom_label = QLabel("Zoom:")
        toolbar.addWidget(self.zoom_label)

        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(10)
        self.zoom_slider.setMaximum(400)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(100)
        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)
        toolbar.addWidget(self.zoom_slider)

        self.zoom_value = QLabel("100%")
        toolbar.addWidget(self.zoom_value)

        self.fit_btn = QPushButton("Fit")
        self.fit_btn.clicked.connect(self._zoom_fit)
        toolbar.addWidget(self.fit_btn)

        self.rotate_left_btn = QPushButton("↺")
        self.rotate_left_btn.clicked.connect(lambda: self._rotate_image(-90))
        toolbar.addWidget(self.rotate_left_btn)

        self.rotate_right_btn = QPushButton("↻")
        self.rotate_right_btn.clicked.connect(lambda: self._rotate_image(90))
        toolbar.addWidget(self.rotate_right_btn)

        return toolbar

    def set_file(self, file_path: str):
        """Set file to preview with lazy loading"""
        self.current_file = file_path

        if not file_path or not os.path.exists(file_path):
            self.content_stack.setCurrentWidget(self.empty_widget)
            return

        # Update header
        self.file_name_label.setText(Path(file_path).name)

        # Show loading
        self.content_stack.setCurrentWidget(self.loading_widget)

        # Load preview in background
        self._load_preview_async(file_path)

    def _load_preview_async(self, file_path: str):
        """Load preview in background thread"""
        # Cancel previous loading
        if self._loader_thread and self._loader_thread.isRunning():
            self._loader_thread.terminate()
            self._loader_thread.wait()

        # Start new loading
        self._loader_thread = PreviewLoaderThread(self.preview_manager, file_path)
        self._loader_thread.finished.connect(self._on_preview_loaded)
        self._loader_thread.error.connect(self._on_preview_error)
        self._loader_thread.start()

    @pyqtSlot(dict)
    def _on_preview_loaded(self, preview_data: dict):
        """Handle preview loaded"""
        self.loading_widget.stop()

        # Clear previous content
        self._clear_content()

        # Load content based on type
        ext = Path(self.current_file).suffix.lower()

        try:
            # Show appropriate toolbar
            if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
                self._show_image_toolbar()
                self._display_image_preview(self.current_file, preview_data)
            elif ext in self.text_previewer.LANGUAGE_MAP or ext in ['.txt', '.log']:
                self._show_text_toolbar()
                self._display_text_preview(self.current_file, preview_data)
            elif ext == '.pdf':
                self._hide_toolbar()
                self._display_pdf_preview(self.current_file, preview_data)
            elif ext == '.md':
                self._show_text_toolbar()
                self._display_markdown_preview(self.current_file, preview_data)
            elif ext == '.json':
                self._show_text_toolbar()
                self._display_json_preview(self.current_file, preview_data)
            else:
                self._hide_toolbar()
                self._display_metadata(preview_data)

            self.content_stack.setCurrentWidget(self.scroll_area)

        except Exception as e:
            self._display_error(str(e))

    @pyqtSlot(str)
    def _on_preview_error(self, error: str):
        """Handle preview error"""
        self.loading_widget.stop()
        self._clear_content()
        self._display_error(error)
        self.content_stack.setCurrentWidget(self.scroll_area)

    def _display_text_preview(self, file_path: str, preview_data: dict):
        """Display text file preview"""
        group = QGroupBox("Text Preview")
        layout = QVBoxLayout()

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Consolas", 9))

        # Use highlighted HTML if available
        if 'highlighted' in preview_data:
            text_edit.setHtml(preview_data['highlighted'])
        else:
            text_edit.setPlainText(preview_data.get('text', ''))

        text_edit.setMinimumHeight(400)
        self.current_text_edit = text_edit
        layout.addWidget(text_edit)

        # Stats
        stats = QLabel(
            f"Lines: {preview_data.get('lines', 0)} | "
            f"Language: {preview_data.get('language', 'text')} | "
            f"Encoding: {preview_data.get('encoding', 'utf-8')}"
        )
        stats.setStyleSheet("color: #8A8886; font-size: 10px;")
        layout.addWidget(stats)

        if preview_data.get('truncated'):
            truncate_label = QLabel("⚠ File truncated for preview")
            truncate_label.setStyleSheet("color: #D13438;")
            layout.addWidget(truncate_label)

        group.setLayout(layout)
        self.content_layout.addWidget(group)

    def _display_json_preview(self, file_path: str, preview_data: dict):
        """Display formatted JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            formatted = self.text_previewer.format_json(content)

            group = QGroupBox("JSON Preview")
            layout = QVBoxLayout()

            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setFont(QFont("Consolas", 9))
            text_edit.setPlainText(formatted)
            text_edit.setMinimumHeight(400)
            self.current_text_edit = text_edit
            layout.addWidget(text_edit)

            group.setLayout(layout)
            self.content_layout.addWidget(group)

        except Exception as e:
            self._display_error(f"Error formatting JSON: {e}")

    def _display_markdown_preview(self, file_path: str, preview_data: dict):
        """Display rendered Markdown"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            html = self.text_previewer.render_markdown(content)

            if html:
                # Use QTextBrowser for HTML
                browser = QTextBrowser()
                browser.setHtml(html)
                browser.setMinimumHeight(400)
                browser.setOpenExternalLinks(True)
                self.content_layout.addWidget(browser)
            else:
                # Fallback to plain text
                self._display_text_preview(file_path, preview_data)

        except Exception as e:
            self._display_error(f"Error rendering Markdown: {e}")

    def _display_image_preview(self, file_path: str, preview_data: dict):
        """Display image with zoom and rotation"""
        group = QGroupBox("Image Preview")
        layout = QVBoxLayout()

        # Load image
        self.original_pixmap = QPixmap(file_path)
        if not self.original_pixmap.isNull():
            self.image_label = QLabel()
            self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._update_image_display()
            layout.addWidget(self.image_label)

            # Dimensions
            dims = QLabel(
                f"Dimensions: {preview_data.get('width', 0)} × {preview_data.get('height', 0)} | "
                f"Format: {preview_data.get('format', 'Unknown')}"
            )
            dims.setStyleSheet("color: #8A8886;")
            layout.addWidget(dims)

            # EXIF metadata
            exif = self.image_previewer.extract_exif(file_path)
            if exif:
                exif_group = QGroupBox("EXIF Metadata")
                exif_layout = QVBoxLayout()
                for key, value in exif.items():
                    row = QLabel(f"<b>{key}:</b> {value}")
                    row.setTextFormat(Qt.TextFormat.RichText)
                    exif_layout.addWidget(row)
                exif_group.setLayout(exif_layout)
                layout.addWidget(exif_group)

        group.setLayout(layout)
        self.content_layout.addWidget(group)

    def _display_pdf_preview(self, file_path: str, preview_data: dict):
        """Display PDF with multiple pages"""
        group = QGroupBox(f"PDF Preview - {preview_data.get('pages', 0)} pages")
        layout = QVBoxLayout()

        # Page selector
        page_controls = QHBoxLayout()
        page_controls.addWidget(QLabel("Page:"))

        self.pdf_page_spin = QSpinBox()
        self.pdf_page_spin.setMinimum(1)
        self.pdf_page_spin.setMaximum(preview_data.get('pages', 1))
        self.pdf_page_spin.valueChanged.connect(lambda: self._load_pdf_page(file_path))
        page_controls.addWidget(self.pdf_page_spin)

        page_controls.addStretch()
        layout.addLayout(page_controls)

        # PDF display area
        self.pdf_display = QLabel()
        self.pdf_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.pdf_display)

        # Load first page
        self._load_pdf_page(file_path)

        group.setLayout(layout)
        self.content_layout.addWidget(group)

    def _load_pdf_page(self, file_path: str):
        """Load specific PDF page"""
        try:
            page_num = self.pdf_page_spin.value()
            pages = self.doc_previewer.render_pdf_pages(file_path, page_num, page_num)

            if pages and len(pages) > 0:
                # Decode base64 image
                import base64
                img_data = pages[0].split(',')[1]
                img_bytes = base64.b64decode(img_data)

                # Display
                pixmap = QPixmap()
                pixmap.loadFromData(img_bytes)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        600, 800,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.pdf_display.setPixmap(scaled)

        except Exception as e:
            self.pdf_display.setText(f"Error loading page: {e}")

    def _display_metadata(self, preview_data: dict):
        """Display file metadata"""
        group = QGroupBox("File Information")
        layout = QVBoxLayout()

        for key, value in preview_data.items():
            if key != 'error':
                row = QLabel(f"<b>{key}:</b> {value}")
                row.setTextFormat(Qt.TextFormat.RichText)
                row.setWordWrap(True)
                layout.addWidget(row)

        group.setLayout(layout)
        self.content_layout.addWidget(group)

    def _display_error(self, error: str):
        """Display error message"""
        label = QLabel(f"Error: {error}")
        label.setStyleSheet("color: #D13438; padding: 20px;")
        label.setWordWrap(True)
        self.content_layout.addWidget(label)

    def _clear_content(self):
        """Clear content area"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.original_pixmap = None
        self.current_zoom = 100
        self.current_rotation = 0

    def _show_text_toolbar(self):
        """Show text editing toolbar"""
        self.toolbar.setVisible(True)
        self.line_numbers_btn.setVisible(True)
        self.word_wrap_btn.setVisible(True)
        self.find_btn.setVisible(True)
        self.zoom_label.setVisible(False)
        self.zoom_slider.setVisible(False)
        self.zoom_value.setVisible(False)
        self.fit_btn.setVisible(False)
        self.rotate_left_btn.setVisible(False)
        self.rotate_right_btn.setVisible(False)

    def _show_image_toolbar(self):
        """Show image toolbar"""
        self.toolbar.setVisible(True)
        self.line_numbers_btn.setVisible(False)
        self.word_wrap_btn.setVisible(False)
        self.find_btn.setVisible(False)
        self.zoom_label.setVisible(True)
        self.zoom_slider.setVisible(True)
        self.zoom_value.setVisible(True)
        self.fit_btn.setVisible(True)
        self.rotate_left_btn.setVisible(True)
        self.rotate_right_btn.setVisible(True)

    def _hide_toolbar(self):
        """Hide toolbar"""
        self.toolbar.setVisible(False)

    def _toggle_line_numbers(self):
        """Toggle line numbers in text preview"""
        # TODO: Implement line numbers toggle
        pass

    def _toggle_word_wrap(self):
        """Toggle word wrap in text preview"""
        if hasattr(self, 'current_text_edit'):
            if self.word_wrap_btn.isChecked():
                self.current_text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
            else:
                self.current_text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

    def _show_find(self):
        """Show find dialog"""
        self.find_dialog.setVisible(True)
        self.find_dialog.focus_search()

    def _hide_find(self):
        """Hide find dialog"""
        self.find_dialog.setVisible(False)

    def _on_find_text(self, text: str, case_sensitive: bool):
        """Find text in preview"""
        if hasattr(self, 'current_text_edit'):
            flags = QTextCursor.FindFlag(0)
            if case_sensitive:
                flags |= QTextCursor.FindFlag.FindCaseSensitively

            found = self.current_text_edit.find(text, flags)
            if not found:
                # Wrap around
                cursor = self.current_text_edit.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                self.current_text_edit.setTextCursor(cursor)
                self.current_text_edit.find(text, flags)

    def _on_zoom_changed(self, value: int):
        """Handle zoom slider change"""
        self.current_zoom = value
        self.zoom_value.setText(f"{value}%")
        self._update_image_display()

    def _zoom_fit(self):
        """Fit image to view"""
        if self.original_pixmap:
            # Calculate fit zoom
            view_width = self.scroll_area.width() - 50
            img_width = self.original_pixmap.width()
            zoom = int((view_width / img_width) * 100)
            self.zoom_slider.setValue(min(max(zoom, 10), 400))

    def _rotate_image(self, angle: int):
        """Rotate image"""
        self.current_rotation = (self.current_rotation + angle) % 360
        self._update_image_display()

    def _update_image_display(self):
        """Update image display with current zoom and rotation"""
        if not self.original_pixmap or not hasattr(self, 'image_label'):
            return

        # Apply zoom
        width = int(self.original_pixmap.width() * self.current_zoom / 100)
        height = int(self.original_pixmap.height() * self.current_zoom / 100)
        scaled = self.original_pixmap.scaled(
            width, height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Apply rotation
        if self.current_rotation != 0:
            transform = QTransform()
            transform.rotate(self.current_rotation)
            scaled = scaled.transformed(transform, Qt.TransformationMode.SmoothTransformation)

        self.image_label.setPixmap(scaled)

    def _on_open_clicked(self):
        """Handle open button"""
        if self.current_file:
            self.open_requested.emit(self.current_file)

    def _on_open_location_clicked(self):
        """Handle open location button"""
        if self.current_file:
            self.open_location_requested.emit(self.current_file)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_F and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self._show_find()
        else:
            super().keyPressEvent(event)

    def clear(self):
        """Clear preview"""
        self.current_file = None
        self._clear_content()
        self.content_stack.setCurrentWidget(self.empty_widget)
        self._hide_toolbar()
        self.find_dialog.setVisible(False)

    def cleanup(self):
        """Cleanup resources"""
        if self._loader_thread and self._loader_thread.isRunning():
            self._loader_thread.terminate()
            self._loader_thread.wait()
        self.preview_manager.shutdown()
