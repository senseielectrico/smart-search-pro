"""
Reusable note editor widget with rich text editing capabilities.

Features:
- Rich text formatting (bold, italic, underline)
- Markdown support with preview
- Code highlighting
- Image embedding
- Tables
- Checkbox lists
- Find and replace
- Word count
- Export to multiple formats
"""

import re
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import (
    QTextCharFormat, QFont, QColor, QTextCursor, QSyntaxHighlighter,
    QTextDocument, QTextBlockFormat, QTextListFormat, QImage, QTextImageFormat
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QToolBar,
    QPushButton, QLabel, QDialog, QLineEdit, QDialogButtonBox,
    QFileDialog, QMessageBox, QSplitter, QTextBrowser, QComboBox,
    QCheckBox
)

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.formatters import HtmlFormatter
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False


class MarkdownHighlighter(QSyntaxHighlighter):
    """Simple Markdown syntax highlighter."""

    def __init__(self, document):
        super().__init__(document)
        self._setup_formats()

    def _setup_formats(self):
        """Setup text formats for different Markdown elements."""
        # Headers
        self.header_format = QTextCharFormat()
        self.header_format.setFontWeight(QFont.Weight.Bold)
        self.header_format.setForeground(QColor("#2c3e50"))

        # Bold
        self.bold_format = QTextCharFormat()
        self.bold_format.setFontWeight(QFont.Weight.Bold)

        # Italic
        self.italic_format = QTextCharFormat()
        self.italic_format.setFontItalic(True)

        # Code
        self.code_format = QTextCharFormat()
        self.code_format.setFontFamily("Consolas")
        self.code_format.setBackground(QColor("#f5f5f5"))

        # Link
        self.link_format = QTextCharFormat()
        self.link_format.setForeground(QColor("#3498db"))
        self.link_format.setFontUnderline(True)

    def highlightBlock(self, text):
        """Highlight a block of text."""
        # Headers
        if text.startswith('#'):
            self.setFormat(0, len(text), self.header_format)
            return

        # Bold **text**
        for match in re.finditer(r'\*\*(.+?)\*\*', text):
            self.setFormat(match.start(), match.end() - match.start(), self.bold_format)

        # Italic *text*
        for match in re.finditer(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', text):
            self.setFormat(match.start(), match.end() - match.start(), self.italic_format)

        # Inline code `code`
        for match in re.finditer(r'`(.+?)`', text):
            self.setFormat(match.start(), match.end() - match.start(), self.code_format)

        # Links [text](url)
        for match in re.finditer(r'\[(.+?)\]\((.+?)\)', text):
            self.setFormat(match.start(), match.end() - match.start(), self.link_format)


class FindReplaceDialog(QDialog):
    """Find and replace dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Find and Replace")
        self.setModal(False)
        self._setup_ui()

    def _setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)

        # Find
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("Find:"))
        self.find_edit = QLineEdit()
        find_layout.addWidget(self.find_edit)
        layout.addLayout(find_layout)

        # Replace
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("Replace:"))
        self.replace_edit = QLineEdit()
        replace_layout.addWidget(self.replace_edit)
        layout.addLayout(replace_layout)

        # Options
        self.case_sensitive_cb = QCheckBox("Case sensitive")
        self.whole_words_cb = QCheckBox("Whole words")
        layout.addWidget(self.case_sensitive_cb)
        layout.addWidget(self.whole_words_cb)

        # Buttons
        button_layout = QHBoxLayout()
        self.find_btn = QPushButton("Find Next")
        self.replace_btn = QPushButton("Replace")
        self.replace_all_btn = QPushButton("Replace All")
        button_layout.addWidget(self.find_btn)
        button_layout.addWidget(self.replace_btn)
        button_layout.addWidget(self.replace_all_btn)
        layout.addLayout(button_layout)

        # Close
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)


class NoteEditorWidget(QWidget):
    """
    Reusable note editor with rich text editing.

    Signals:
        content_changed: Emitted when content changes
        word_count_changed: Emitted when word count changes
    """

    content_changed = pyqtSignal()
    word_count_changed = pyqtSignal(int, int)  # words, chars

    def __init__(self, parent=None):
        super().__init__(parent)
        self.markdown_mode = True
        self.preview_visible = False
        self._setup_ui()
        self._connect_signals()

        # Auto-update word count
        self.word_count_timer = QTimer()
        self.word_count_timer.timeout.connect(self._update_word_count)
        self.word_count_timer.start(1000)  # Update every second

    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        self.toolbar = self._create_toolbar()
        layout.addWidget(self.toolbar)

        # Splitter for editor and preview
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Editor
        self.editor = QTextEdit()
        self.editor.setAcceptRichText(False)  # Start with plain text
        self.editor.setTabStopDistance(40)
        font = QFont("Consolas", 10)
        self.editor.setFont(font)
        self.splitter.addWidget(self.editor)

        # Markdown highlighter
        self.highlighter = MarkdownHighlighter(self.editor.document())

        # Preview
        self.preview = QTextBrowser()
        self.preview.setVisible(False)
        self.splitter.addWidget(self.preview)

        layout.addWidget(self.splitter)

        # Status bar
        status_layout = QHBoxLayout()
        self.word_count_label = QLabel("Words: 0 | Characters: 0")
        self.word_count_label.setStyleSheet("color: #7f8c8d; font-size: 9pt;")
        status_layout.addWidget(self.word_count_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Find/Replace dialog
        self.find_dialog = None

    def _create_toolbar(self) -> QToolBar:
        """Create formatting toolbar."""
        toolbar = QToolBar()
        toolbar.setMovable(False)

        # Bold
        bold_btn = QPushButton("B")
        bold_btn.setToolTip("Bold (Ctrl+B)")
        bold_btn.setFixedSize(30, 30)
        bold_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        bold_btn.clicked.connect(self._toggle_bold)
        toolbar.addWidget(bold_btn)

        # Italic
        italic_btn = QPushButton("I")
        italic_btn.setToolTip("Italic (Ctrl+I)")
        italic_btn.setFixedSize(30, 30)
        italic_btn.setFont(QFont("Arial", 10, QFont.Weight.Normal, italic=True))
        italic_btn.clicked.connect(self._toggle_italic)
        toolbar.addWidget(italic_btn)

        # Underline
        underline_btn = QPushButton("U")
        underline_btn.setToolTip("Underline (Ctrl+U)")
        underline_btn.setFixedSize(30, 30)
        underline_btn.setFont(QFont("Arial", 10, QFont.Weight.Normal))
        underline_btn.clicked.connect(self._toggle_underline)
        toolbar.addWidget(underline_btn)

        toolbar.addSeparator()

        # Heading
        heading_combo = QComboBox()
        heading_combo.addItems(["Normal", "Heading 1", "Heading 2", "Heading 3"])
        heading_combo.currentIndexChanged.connect(self._apply_heading)
        toolbar.addWidget(heading_combo)

        toolbar.addSeparator()

        # Bulleted list
        bullet_btn = QPushButton("• List")
        bullet_btn.setToolTip("Bulleted List")
        bullet_btn.clicked.connect(self._insert_bullet_list)
        toolbar.addWidget(bullet_btn)

        # Numbered list
        number_btn = QPushButton("1. List")
        number_btn.setToolTip("Numbered List")
        number_btn.clicked.connect(self._insert_numbered_list)
        toolbar.addWidget(number_btn)

        # Checkbox list
        checkbox_btn = QPushButton("☐ Task")
        checkbox_btn.setToolTip("Task List")
        checkbox_btn.clicked.connect(self._insert_checkbox_list)
        toolbar.addWidget(checkbox_btn)

        toolbar.addSeparator()

        # Code block
        code_btn = QPushButton("Code")
        code_btn.setToolTip("Code Block")
        code_btn.clicked.connect(self._insert_code_block)
        toolbar.addWidget(code_btn)

        # Table
        table_btn = QPushButton("Table")
        table_btn.setToolTip("Insert Table")
        table_btn.clicked.connect(self._insert_table)
        toolbar.addWidget(table_btn)

        # Image
        image_btn = QPushButton("Image")
        image_btn.setToolTip("Insert Image")
        image_btn.clicked.connect(self._insert_image)
        toolbar.addWidget(image_btn)

        toolbar.addSeparator()

        # Preview toggle
        self.preview_btn = QPushButton("Preview")
        self.preview_btn.setCheckable(True)
        self.preview_btn.setToolTip("Toggle Markdown Preview")
        self.preview_btn.clicked.connect(self._toggle_preview)
        toolbar.addWidget(self.preview_btn)

        # Find/Replace
        find_btn = QPushButton("Find")
        find_btn.setToolTip("Find and Replace (Ctrl+F)")
        find_btn.clicked.connect(self._show_find_dialog)
        toolbar.addWidget(find_btn)

        return toolbar

    def _connect_signals(self):
        """Connect signals."""
        self.editor.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        """Handle text change."""
        self.content_changed.emit()
        if self.preview_visible:
            self._update_preview()

    def _toggle_bold(self):
        """Toggle bold formatting."""
        fmt = self.editor.currentCharFormat()
        fmt.setFontWeight(
            QFont.Weight.Normal if fmt.fontWeight() == QFont.Weight.Bold
            else QFont.Weight.Bold
        )
        self.editor.setCurrentCharFormat(fmt)

    def _toggle_italic(self):
        """Toggle italic formatting."""
        fmt = self.editor.currentCharFormat()
        fmt.setFontItalic(not fmt.fontItalic())
        self.editor.setCurrentCharFormat(fmt)

    def _toggle_underline(self):
        """Toggle underline formatting."""
        fmt = self.editor.currentCharFormat()
        fmt.setFontUnderline(not fmt.fontUnderline())
        self.editor.setCurrentCharFormat(fmt)

    def _apply_heading(self, index: int):
        """Apply heading format."""
        cursor = self.editor.textCursor()
        block_fmt = QTextBlockFormat()

        if index == 0:  # Normal
            block_fmt.setHeadingLevel(0)
            char_fmt = QTextCharFormat()
            char_fmt.setFontPointSize(10)
        elif index == 1:  # H1
            block_fmt.setHeadingLevel(1)
            char_fmt = QTextCharFormat()
            char_fmt.setFontPointSize(18)
            char_fmt.setFontWeight(QFont.Weight.Bold)
        elif index == 2:  # H2
            block_fmt.setHeadingLevel(2)
            char_fmt = QTextCharFormat()
            char_fmt.setFontPointSize(15)
            char_fmt.setFontWeight(QFont.Weight.Bold)
        elif index == 3:  # H3
            block_fmt.setHeadingLevel(3)
            char_fmt = QTextCharFormat()
            char_fmt.setFontPointSize(12)
            char_fmt.setFontWeight(QFont.Weight.Bold)

        cursor.mergeBlockFormat(block_fmt)
        cursor.mergeCharFormat(char_fmt)

    def _insert_bullet_list(self):
        """Insert bulleted list."""
        cursor = self.editor.textCursor()
        cursor.insertList(QTextListFormat.Style.ListDisc)

    def _insert_numbered_list(self):
        """Insert numbered list."""
        cursor = self.editor.textCursor()
        cursor.insertList(QTextListFormat.Style.ListDecimal)

    def _insert_checkbox_list(self):
        """Insert checkbox list."""
        cursor = self.editor.textCursor()
        cursor.insertText("☐ ")

    def _insert_code_block(self):
        """Insert code block."""
        cursor = self.editor.textCursor()
        if self.markdown_mode:
            cursor.insertText("```\n\n```")
            cursor.movePosition(QTextCursor.MoveOperation.PreviousBlock)
        else:
            fmt = QTextCharFormat()
            fmt.setFontFamily("Consolas")
            fmt.setBackground(QColor("#f5f5f5"))
            cursor.setCharFormat(fmt)

    def _insert_table(self):
        """Insert Markdown table."""
        cursor = self.editor.textCursor()
        if self.markdown_mode:
            table = (
                "| Column 1 | Column 2 | Column 3 |\n"
                "|----------|----------|----------|\n"
                "| Cell 1   | Cell 2   | Cell 3   |\n"
            )
            cursor.insertText(table)

    def _insert_image(self):
        """Insert image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if file_path:
            if self.markdown_mode:
                cursor = self.editor.textCursor()
                cursor.insertText(f"![Image]({file_path})")
            else:
                # Embed image directly
                image = QImage(file_path)
                if not image.isNull():
                    cursor = self.editor.textCursor()
                    image_format = QTextImageFormat()
                    image_format.setName(file_path)
                    image_format.setWidth(400)
                    cursor.insertImage(image_format)

    def _toggle_preview(self, checked: bool):
        """Toggle Markdown preview."""
        self.preview_visible = checked
        self.preview.setVisible(checked)
        if checked:
            self._update_preview()
            self.splitter.setSizes([500, 500])

    def _update_preview(self):
        """Update Markdown preview."""
        if not self.preview_visible:
            return

        content = self.editor.toPlainText()
        # Simple Markdown to HTML conversion
        html = self._markdown_to_html(content)
        self.preview.setHtml(html)

    def _markdown_to_html(self, markdown: str) -> str:
        """Convert Markdown to HTML (simplified)."""
        html = markdown

        # Headers
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

        # Bold
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

        # Italic
        html = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', html)

        # Code
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)

        # Links
        html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)

        # Lists
        html = re.sub(r'^\* (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'((?:<li>.+</li>\n?)+)', r'<ul>\1</ul>', html)

        # Checkboxes
        html = re.sub(r'☐ (.+)', r'<input type="checkbox"> \1', html)
        html = re.sub(r'☑ (.+)', r'<input type="checkbox" checked> \1', html)

        # Paragraphs
        html = html.replace('\n\n', '</p><p>')
        html = f'<p>{html}</p>'

        # Styling
        style = """
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
            h2 { color: #34495e; border-bottom: 1px solid #95a5a6; padding-bottom: 3px; }
            h3 { color: #7f8c8d; }
            code { background: #f5f5f5; padding: 2px 5px; border-radius: 3px; font-family: Consolas, monospace; }
            a { color: #3498db; text-decoration: none; }
            a:hover { text-decoration: underline; }
            ul { margin-left: 20px; }
        </style>
        """

        return f"{style}{html}"

    def _show_find_dialog(self):
        """Show find and replace dialog."""
        if not self.find_dialog:
            self.find_dialog = FindReplaceDialog(self)
            self.find_dialog.find_btn.clicked.connect(self._find_next)
            self.find_dialog.replace_btn.clicked.connect(self._replace_current)
            self.find_dialog.replace_all_btn.clicked.connect(self._replace_all)

        self.find_dialog.show()
        self.find_dialog.find_edit.setFocus()

    def _find_next(self):
        """Find next occurrence."""
        if not self.find_dialog:
            return

        text = self.find_dialog.find_edit.text()
        if not text:
            return

        flags = QTextDocument.FindFlag(0)
        if self.find_dialog.case_sensitive_cb.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if self.find_dialog.whole_words_cb.isChecked():
            flags |= QTextDocument.FindFlag.FindWholeWords

        found = self.editor.find(text, flags)
        if not found:
            # Wrap around
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.editor.setTextCursor(cursor)
            self.editor.find(text, flags)

    def _replace_current(self):
        """Replace current selection."""
        if not self.find_dialog:
            return

        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.find_dialog.replace_edit.text())
        self._find_next()

    def _replace_all(self):
        """Replace all occurrences."""
        if not self.find_dialog:
            return

        find_text = self.find_dialog.find_edit.text()
        replace_text = self.find_dialog.replace_edit.text()
        if not find_text:
            return

        content = self.editor.toPlainText()
        if self.find_dialog.case_sensitive_cb.isChecked():
            new_content = content.replace(find_text, replace_text)
        else:
            new_content = re.sub(
                re.escape(find_text),
                replace_text,
                content,
                flags=re.IGNORECASE
            )

        if new_content != content:
            self.editor.setPlainText(new_content)

    def _update_word_count(self):
        """Update word count display."""
        text = self.editor.toPlainText()
        words = len(text.split()) if text else 0
        chars = len(text)

        self.word_count_label.setText(f"Words: {words} | Characters: {chars}")
        self.word_count_changed.emit(words, chars)

    # ========================================================================
    # Public API
    # ========================================================================

    def get_content(self) -> str:
        """Get editor content."""
        return self.editor.toPlainText()

    def set_content(self, content: str):
        """Set editor content."""
        self.editor.setPlainText(content)

    def clear(self):
        """Clear editor."""
        self.editor.clear()

    def export_to_text(self, file_path: Path):
        """Export to plain text."""
        file_path.write_text(self.get_content(), encoding='utf-8')

    def export_to_markdown(self, file_path: Path):
        """Export to Markdown."""
        file_path.write_text(self.get_content(), encoding='utf-8')

    def export_to_html(self, file_path: Path):
        """Export to HTML."""
        html = self._markdown_to_html(self.get_content())
        file_path.write_text(html, encoding='utf-8')

    def export_to_pdf(self, file_path: Path):
        """Export to PDF."""
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtGui import QTextDocument

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(str(file_path))

        doc = QTextDocument()
        doc.setHtml(self._markdown_to_html(self.get_content()))
        doc.print(printer)
