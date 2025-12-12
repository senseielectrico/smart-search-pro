"""
Export Dialog - Configure and execute export operations
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QLineEdit, QPushButton, QCheckBox, QSpinBox,
    QFileDialog, QLabel, QProgressDialog, QMessageBox, QRadioButton,
    QButtonGroup, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon


class ExportWorker(QThread):
    """Worker thread for export operations"""

    # Signals
    progress_update = pyqtSignal(int, int, str)  # current, total, message
    export_complete = pyqtSignal(str)  # output file path
    export_error = pyqtSignal(str)  # error message

    def __init__(self, exporter, results, parent=None):
        super().__init__(parent)
        self.exporter = exporter
        self.results = results
        self.is_cancelled = False

    def run(self):
        """Execute export in background"""
        try:
            stats = self.exporter.export(self.results)

            if not self.is_cancelled and stats.output_file:
                self.export_complete.emit(str(stats.output_file))
            elif not self.is_cancelled:
                self.export_complete.emit("Clipboard")

        except Exception as e:
            if not self.is_cancelled:
                self.export_error.emit(str(e))

    def cancel(self):
        """Cancel export operation"""
        self.is_cancelled = True


class ExportDialog(QDialog):
    """Dialog for configuring and executing exports"""

    def __init__(self, results: List[Dict], parent=None):
        super().__init__(parent)

        self.results = results
        self.output_path = None
        self.worker = None

        self._init_ui()
        self.setWindowTitle("Export Results")
        self.setModal(True)
        self.resize(600, 500)

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header = QLabel(f"<h3>Export {len(self.results):,} Results</h3>")
        layout.addWidget(header)

        # Format selection
        format_group = QGroupBox("Export Format")
        format_layout = QVBoxLayout(format_group)

        self.format_group = QButtonGroup(self)

        self.csv_radio = QRadioButton("CSV - Comma-separated values")
        self.excel_radio = QRadioButton("Excel - XLSX with formatting")
        self.html_radio = QRadioButton("HTML - Interactive report")
        self.json_radio = QRadioButton("JSON - Structured data")
        self.clipboard_radio = QRadioButton("Clipboard - Quick copy")

        self.format_group.addButton(self.csv_radio, 0)
        self.format_group.addButton(self.excel_radio, 1)
        self.format_group.addButton(self.html_radio, 2)
        self.format_group.addButton(self.json_radio, 3)
        self.format_group.addButton(self.clipboard_radio, 4)

        format_layout.addWidget(self.csv_radio)
        format_layout.addWidget(self.excel_radio)
        format_layout.addWidget(self.html_radio)
        format_layout.addWidget(self.json_radio)
        format_layout.addWidget(self.clipboard_radio)

        self.csv_radio.setChecked(True)
        self.format_group.buttonClicked.connect(self._on_format_changed)

        layout.addWidget(format_group)

        # Tabbed options
        self.options_tabs = QTabWidget()

        # General options tab
        general_tab = self._create_general_tab()
        self.options_tabs.addTab(general_tab, "General")

        # Format-specific options tab
        self.format_options_tab = self._create_csv_options()
        self.options_tabs.addTab(self.format_options_tab, "CSV Options")

        layout.addWidget(self.options_tabs)

        # Output file selection
        output_group = QGroupBox("Output Location")
        output_layout = QHBoxLayout(output_group)

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Select output file...")
        output_layout.addWidget(self.output_edit)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(self.browse_btn)

        layout.addWidget(output_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.export_btn = QPushButton("Export")
        self.export_btn.setDefault(True)
        self.export_btn.clicked.connect(self._start_export)
        button_layout.addWidget(self.export_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        # Initial state
        self._update_output_visibility()

    def _create_general_tab(self) -> QWidget:
        """Create general options tab"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Column selection
        self.columns_all_check = QCheckBox("Export all columns")
        self.columns_all_check.setChecked(True)
        layout.addRow("Columns:", self.columns_all_check)

        # Headers
        self.headers_check = QCheckBox("Include column headers")
        self.headers_check.setChecked(True)
        layout.addRow("Headers:", self.headers_check)

        # Max results
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setMinimum(0)
        self.max_results_spin.setMaximum(10000000)
        self.max_results_spin.setValue(0)
        self.max_results_spin.setSpecialValueText("All")
        layout.addRow("Max results:", self.max_results_spin)

        # Date format
        self.date_format_edit = QLineEdit("%Y-%m-%d %H:%M:%S")
        layout.addRow("Date format:", self.date_format_edit)

        # Size format
        self.size_format_combo = QComboBox()
        self.size_format_combo.addItems(["Human (1.5 MB)", "Bytes", "KB", "MB", "GB"])
        layout.addRow("Size format:", self.size_format_combo)

        return widget

    def _create_csv_options(self) -> QWidget:
        """Create CSV-specific options"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Delimiter
        self.delimiter_combo = QComboBox()
        self.delimiter_combo.addItems(["Comma (,)", "Semicolon (;)", "Tab", "Pipe (|)"])
        layout.addRow("Delimiter:", self.delimiter_combo)

        # Encoding
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(["UTF-8 with BOM (Excel)", "UTF-8", "UTF-16", "ASCII"])
        layout.addRow("Encoding:", self.encoding_combo)

        # Quote character
        self.quote_edit = QLineEdit('"')
        self.quote_edit.setMaxLength(1)
        layout.addRow("Quote char:", self.quote_edit)

        # Excel compatible
        self.excel_compat_check = QCheckBox("Excel compatible format")
        self.excel_compat_check.setChecked(True)
        layout.addRow("", self.excel_compat_check)

        return widget

    def _create_excel_options(self) -> QWidget:
        """Create Excel-specific options"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Sheet name
        self.sheet_name_edit = QLineEdit("Results")
        layout.addRow("Sheet name:", self.sheet_name_edit)

        # Formatting options
        self.freeze_panes_check = QCheckBox("Freeze header row")
        self.freeze_panes_check.setChecked(True)
        layout.addRow("", self.freeze_panes_check)

        self.auto_filter_check = QCheckBox("Enable auto-filter")
        self.auto_filter_check.setChecked(True)
        layout.addRow("", self.auto_filter_check)

        self.use_tables_check = QCheckBox("Format as Excel table")
        self.use_tables_check.setChecked(True)
        layout.addRow("", self.use_tables_check)

        self.add_hyperlinks_check = QCheckBox("Add hyperlinks to file paths")
        self.add_hyperlinks_check.setChecked(True)
        layout.addRow("", self.add_hyperlinks_check)

        # Summary sheet
        self.include_summary_check = QCheckBox("Include summary sheet")
        self.include_summary_check.setChecked(True)
        layout.addRow("", self.include_summary_check)

        # Split by
        self.split_by_combo = QComboBox()
        self.split_by_combo.addItems(["None (single sheet)", "File extension", "Folder", "File type"])
        layout.addRow("Split sheets by:", self.split_by_combo)

        return widget

    def _create_html_options(self) -> QWidget:
        """Create HTML-specific options"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Title
        self.html_title_edit = QLineEdit("Smart Search Results")
        layout.addRow("Report title:", self.html_title_edit)

        # Theme
        self.html_theme_combo = QComboBox()
        self.html_theme_combo.addItems(["Auto (system)", "Light", "Dark"])
        layout.addRow("Theme:", self.html_theme_combo)

        # Features
        self.sortable_check = QCheckBox("Sortable columns")
        self.sortable_check.setChecked(True)
        layout.addRow("", self.sortable_check)

        self.searchable_check = QCheckBox("Search/filter box")
        self.searchable_check.setChecked(True)
        layout.addRow("", self.searchable_check)

        self.include_icons_check = QCheckBox("File type icons")
        self.include_icons_check.setChecked(True)
        layout.addRow("", self.include_icons_check)

        return widget

    def _create_json_options(self) -> QWidget:
        """Create JSON-specific options"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Pretty print
        self.pretty_print_check = QCheckBox("Pretty print (formatted)")
        self.pretty_print_check.setChecked(True)
        layout.addRow("", self.pretty_print_check)

        # Indent
        self.indent_spin = QSpinBox()
        self.indent_spin.setMinimum(0)
        self.indent_spin.setMaximum(8)
        self.indent_spin.setValue(2)
        layout.addRow("Indent spaces:", self.indent_spin)

        # Metadata
        self.include_metadata_check = QCheckBox("Include metadata")
        self.include_metadata_check.setChecked(True)
        layout.addRow("", self.include_metadata_check)

        # Sort keys
        self.sort_keys_check = QCheckBox("Sort keys alphabetically")
        layout.addRow("", self.sort_keys_check)

        # Format
        self.jsonl_check = QCheckBox("JSON Lines format (one per line)")
        layout.addRow("", self.jsonl_check)

        return widget

    def _create_clipboard_options(self) -> QWidget:
        """Create clipboard-specific options"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Format
        self.clipboard_format_combo = QComboBox()
        self.clipboard_format_combo.addItems(["CSV", "TSV (Tab-separated)", "JSON", "Plain text", "Paths only"])
        layout.addRow("Format:", self.clipboard_format_combo)

        # Separator for paths
        self.separator_combo = QComboBox()
        self.separator_combo.addItems(["Newline", "Semicolon", "Comma"])
        layout.addRow("Path separator:", self.separator_combo)

        return widget

    def _on_format_changed(self, button):
        """Handle format selection change"""
        # Update format-specific options tab
        old_widget = self.options_tabs.widget(1)

        if button == self.csv_radio:
            new_widget = self._create_csv_options()
            title = "CSV Options"
        elif button == self.excel_radio:
            new_widget = self._create_excel_options()
            title = "Excel Options"
        elif button == self.html_radio:
            new_widget = self._create_html_options()
            title = "HTML Options"
        elif button == self.json_radio:
            new_widget = self._create_json_options()
            title = "JSON Options"
        else:  # clipboard
            new_widget = self._create_clipboard_options()
            title = "Clipboard Options"

        self.options_tabs.removeTab(1)
        self.format_options_tab = new_widget
        self.options_tabs.insertTab(1, new_widget, title)

        # Update output visibility
        self._update_output_visibility()

        # Update suggested filename
        self._update_suggested_filename()

    def _update_output_visibility(self):
        """Show/hide output file selection based on format"""
        is_clipboard = self.clipboard_radio.isChecked()

        self.output_edit.setVisible(not is_clipboard)
        self.browse_btn.setVisible(not is_clipboard)
        self.output_edit.parent().setVisible(not is_clipboard)

    def _update_suggested_filename(self):
        """Update suggested output filename"""
        if self.clipboard_radio.isChecked():
            return

        extensions = {
            0: ".csv",
            1: ".xlsx",
            2: ".html",
            3: ".json",
        }

        ext = extensions.get(self.format_group.checkedId(), ".csv")

        # Generate filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"search_results_{timestamp}{ext}"

        # Set default location (user's Documents)
        default_dir = Path.home() / "Documents"
        suggested_path = default_dir / filename

        self.output_edit.setText(str(suggested_path))

    def _browse_output(self):
        """Browse for output file"""
        format_id = self.format_group.checkedId()

        filters = {
            0: "CSV Files (*.csv);;All Files (*.*)",
            1: "Excel Files (*.xlsx);;All Files (*.*)",
            2: "HTML Files (*.html *.htm);;All Files (*.*)",
            3: "JSON Files (*.json);;All Files (*.*)",
        }

        filter_str = filters.get(format_id, "All Files (*.*)")

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Export As",
            self.output_edit.text() or str(Path.home() / "Documents"),
            filter_str
        )

        if filename:
            self.output_edit.setText(filename)

    def _start_export(self):
        """Start export operation"""
        # Validate
        if not self.clipboard_radio.isChecked():
            output_path = self.output_edit.text().strip()
            if not output_path:
                QMessageBox.warning(self, "No Output File", "Please select an output file.")
                return
            self.output_path = Path(output_path)
        else:
            self.output_path = None

        # Build configuration
        try:
            exporter = self._create_exporter()
        except ImportError as e:
            QMessageBox.critical(self, "Missing Dependency", f"Export failed:\n{e}")
            return

        # Create progress dialog
        progress = QProgressDialog("Exporting results...", "Cancel", 0, len(self.results), self)
        progress.setWindowTitle("Export Progress")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(500)

        # Create worker
        self.worker = ExportWorker(exporter, self.results, self)
        self.worker.progress_update.connect(lambda c, t, m: progress.setValue(c))
        self.worker.export_complete.connect(lambda path: self._on_export_complete(path, progress))
        self.worker.export_error.connect(lambda err: self._on_export_error(err, progress))
        progress.canceled.connect(self.worker.cancel)

        # Start export
        self.worker.start()

    def _create_exporter(self):
        """Create appropriate exporter based on settings"""
        from export.base import ExportConfig

        # Build column list
        columns = [
            "filename", "path", "full_path", "extension", "size",
            "date_modified", "date_created", "is_folder"
        ] if self.columns_all_check.isChecked() else ["filename", "path", "size"]

        # Build base config
        config = ExportConfig(
            output_path=self.output_path,
            overwrite=True,
            columns=columns,
            include_headers=self.headers_check.isChecked(),
            max_results=self.max_results_spin.value() if self.max_results_spin.value() > 0 else None,
            date_format=self.date_format_edit.text(),
            size_format=self._get_size_format(),
        )

        # Format-specific options
        format_id = self.format_group.checkedId()

        if format_id == 0:  # CSV
            from export.csv_exporter import CSVExporter

            config.options = {
                "delimiter": self._get_delimiter(),
                "encoding": self._get_encoding(),
                "quotechar": self.quote_edit.text() or '"',
                "excel_compatible": self.excel_compat_check.isChecked(),
            }
            return CSVExporter(config)

        elif format_id == 1:  # Excel
            from export.excel_exporter import ExcelExporter

            config.options = {
                "freeze_panes": self.freeze_panes_check.isChecked(),
                "auto_filter": self.auto_filter_check.isChecked(),
                "use_tables": self.use_tables_check.isChecked(),
                "add_hyperlinks": self.add_hyperlinks_check.isChecked(),
                "include_summary": self.include_summary_check.isChecked(),
                "split_by": self._get_split_by(),
            }
            return ExcelExporter(config)

        elif format_id == 2:  # HTML
            from export.html_exporter import HTMLExporter

            config.options = {
                "title": self.html_title_edit.text(),
                "theme": self._get_html_theme(),
                "sortable": self.sortable_check.isChecked(),
                "searchable": self.searchable_check.isChecked(),
                "include_icons": self.include_icons_check.isChecked(),
            }
            return HTMLExporter(config)

        elif format_id == 3:  # JSON
            from export.json_exporter import JSONExporter

            config.options = {
                "pretty": self.pretty_print_check.isChecked(),
                "indent": self.indent_spin.value(),
                "include_metadata": self.include_metadata_check.isChecked(),
                "sort_keys": self.sort_keys_check.isChecked(),
                "jsonl": self.jsonl_check.isChecked(),
            }
            return JSONExporter(config)

        else:  # Clipboard
            from export.clipboard import ClipboardExporter

            config.options = {
                "format": self._get_clipboard_format(),
                "separator": self._get_separator(),
            }
            return ClipboardExporter(config)

    def _get_delimiter(self) -> str:
        """Get CSV delimiter"""
        delimiters = {
            "Comma (,)": ",",
            "Semicolon (;)": ";",
            "Tab": "\t",
            "Pipe (|)": "|",
        }
        return delimiters.get(self.delimiter_combo.currentText(), ",")

    def _get_encoding(self) -> str:
        """Get CSV encoding"""
        encodings = {
            "UTF-8 with BOM (Excel)": "utf-8-sig",
            "UTF-8": "utf-8",
            "UTF-16": "utf-16",
            "ASCII": "ascii",
        }
        return encodings.get(self.encoding_combo.currentText(), "utf-8-sig")

    def _get_size_format(self) -> str:
        """Get size format"""
        formats = {
            "Human (1.5 MB)": "human",
            "Bytes": "bytes",
            "KB": "kb",
            "MB": "mb",
            "GB": "gb",
        }
        return formats.get(self.size_format_combo.currentText(), "human")

    def _get_split_by(self) -> Optional[str]:
        """Get Excel split option"""
        splits = {
            "None (single sheet)": None,
            "File extension": "extension",
            "Folder": "folder",
            "File type": "type",
        }
        return splits.get(self.split_by_combo.currentText(), None)

    def _get_html_theme(self) -> str:
        """Get HTML theme"""
        themes = {
            "Auto (system)": "auto",
            "Light": "light",
            "Dark": "dark",
        }
        return themes.get(self.html_theme_combo.currentText(), "auto")

    def _get_clipboard_format(self) -> str:
        """Get clipboard format"""
        formats = {
            "CSV": "csv",
            "TSV (Tab-separated)": "tsv",
            "JSON": "json",
            "Plain text": "text",
            "Paths only": "paths",
        }
        return formats.get(self.clipboard_format_combo.currentText(), "csv")

    def _get_separator(self) -> str:
        """Get path separator"""
        separators = {
            "Newline": "\n",
            "Semicolon": ";",
            "Comma": ",",
        }
        return separators.get(self.separator_combo.currentText(), "\n")

    @pyqtSlot(str, QProgressDialog)
    def _on_export_complete(self, output_path: str, progress: QProgressDialog):
        """Handle export completion"""
        progress.close()

        if output_path == "Clipboard":
            QMessageBox.information(
                self,
                "Export Complete",
                f"{len(self.results):,} results copied to clipboard!"
            )
        else:
            reply = QMessageBox.information(
                self,
                "Export Complete",
                f"Successfully exported {len(self.results):,} results to:\n{output_path}\n\nOpen the file?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                try:
                    os.startfile(output_path)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to open file:\n{e}")

        self.accept()

    @pyqtSlot(str, QProgressDialog)
    def _on_export_error(self, error: str, progress: QProgressDialog):
        """Handle export error"""
        progress.close()
        QMessageBox.critical(self, "Export Failed", f"Export failed:\n{error}")
