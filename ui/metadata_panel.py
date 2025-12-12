"""
Metadata Panel - Comprehensive Metadata Viewer and Editor
View, search, compare, and edit file metadata with ExifTool integration.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QToolBar, QSplitter,
    QTextEdit, QTabWidget, QGroupBox, QMessageBox, QFileDialog,
    QProgressDialog, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QIcon

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.exiftool_wrapper import ExifToolWrapper
from tools.metadata_analyzer import MetadataAnalyzer
from tools.forensic_report import ForensicReportGenerator


class MetadataPanel(QWidget):
    """
    Advanced metadata viewer panel with forensic analysis capabilities.
    """

    # Signals
    metadata_changed = pyqtSignal(str)  # File path
    export_requested = pyqtSignal(str, str)  # File path, format

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_file: Optional[str] = None
        self.current_metadata: Dict[str, Any] = {}
        self.comparison_file: Optional[str] = None

        # Initialize ExifTool components
        try:
            self.exiftool = ExifToolWrapper()
            self.analyzer = MetadataAnalyzer(self.exiftool)
            self.report_gen = ForensicReportGenerator(self.exiftool, self.analyzer)
            self.exiftool_available = True
        except RuntimeError as e:
            self.exiftool = None
            self.analyzer = None
            self.report_gen = None
            self.exiftool_available = False
            self.error_message = str(e)

        self._init_ui()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create toolbar
        self._create_toolbar(layout)

        # Check if ExifTool is available
        if not self.exiftool_available:
            self._show_exiftool_error(layout)
            return

        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Metadata viewer tab
        self._create_metadata_tab()

        # Forensic analysis tab
        self._create_forensic_tab()

        # Comparison tab
        self._create_comparison_tab()

    def _create_toolbar(self, parent_layout):
        """Create toolbar with actions"""
        toolbar = QToolBar()
        toolbar.setMovable(False)

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search metadata...")
        self.search_box.setMaximumWidth(300)
        self.search_box.textChanged.connect(self._filter_metadata)
        toolbar.addWidget(self.search_box)

        toolbar.addSeparator()

        # Export buttons
        export_json_btn = QPushButton("Export JSON")
        export_json_btn.clicked.connect(lambda: self._export_metadata('json'))
        toolbar.addWidget(export_json_btn)

        export_csv_btn = QPushButton("Export CSV")
        export_csv_btn.clicked.connect(lambda: self._export_metadata('csv'))
        toolbar.addWidget(export_csv_btn)

        toolbar.addSeparator()

        # Generate report button
        report_btn = QPushButton("Generate Report")
        report_btn.clicked.connect(self._generate_report)
        toolbar.addWidget(report_btn)

        toolbar.addSeparator()

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_metadata)
        toolbar.addWidget(refresh_btn)

        parent_layout.addWidget(toolbar)

    def _show_exiftool_error(self, parent_layout):
        """Show error message when ExifTool is not available"""
        error_widget = QWidget()
        error_layout = QVBoxLayout(error_widget)

        error_label = QLabel(
            "<h2>ExifTool Not Found</h2>"
            "<p>ExifTool is required for metadata analysis but was not found on your system.</p>"
            f"<p style='color: red;'>{self.error_message}</p>"
            "<p><b>To install ExifTool:</b></p>"
            "<ol>"
            "<li>Download from: <a href='https://exiftool.org/'>https://exiftool.org/</a></li>"
            "<li>Extract to: D:\\MAIN_DATA_CENTER\\Dev_Tools\\ExifTool\\</li>"
            "<li>Or add to your system PATH</li>"
            "</ol>"
        )
        error_label.setWordWrap(True)
        error_label.setOpenExternalLinks(True)
        error_layout.addWidget(error_label)

        error_layout.addStretch()

        parent_layout.addWidget(error_widget)

    def _create_metadata_tab(self):
        """Create metadata viewer tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Create tree widget for metadata
        self.metadata_tree = QTreeWidget()
        self.metadata_tree.setHeaderLabels(['Field', 'Value'])
        self.metadata_tree.setAlternatingRowColors(True)
        self.metadata_tree.setColumnWidth(0, 300)

        # Enable selection
        self.metadata_tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)

        layout.addWidget(self.metadata_tree)

        # Add edit button
        edit_layout = QHBoxLayout()
        edit_btn = QPushButton("Edit Selected Field")
        edit_btn.clicked.connect(self._edit_selected_field)
        edit_layout.addWidget(edit_btn)

        strip_btn = QPushButton("Strip All Metadata")
        strip_btn.clicked.connect(self._strip_metadata)
        edit_layout.addWidget(strip_btn)

        edit_layout.addStretch()
        layout.addLayout(edit_layout)

        self.tabs.addTab(tab, "Metadata")

    def _create_forensic_tab(self):
        """Create forensic analysis tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Analysis results
        self.forensic_text = QTextEdit()
        self.forensic_text.setReadOnly(True)
        self.forensic_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.forensic_text)

        # Buttons
        btn_layout = QHBoxLayout()

        analyze_btn = QPushButton("Run Forensic Analysis")
        analyze_btn.clicked.connect(self._run_forensic_analysis)
        btn_layout.addWidget(analyze_btn)

        save_report_btn = QPushButton("Save Report")
        save_report_btn.clicked.connect(lambda: self._save_forensic_report())
        btn_layout.addWidget(save_report_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.tabs.addTab(tab, "Forensic Analysis")

    def _create_comparison_tab(self):
        """Create comparison tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # File selection
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Compare with:"))

        self.compare_file_label = QLabel("No file selected")
        select_layout.addWidget(self.compare_file_label)

        select_btn = QPushButton("Select File...")
        select_btn.clicked.connect(self._select_comparison_file)
        select_layout.addWidget(select_btn)

        compare_btn = QPushButton("Compare")
        compare_btn.clicked.connect(self._compare_files)
        select_layout.addWidget(compare_btn)

        select_layout.addStretch()
        layout.addLayout(select_layout)

        # Comparison results
        self.comparison_text = QTextEdit()
        self.comparison_text.setReadOnly(True)
        self.comparison_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.comparison_text)

        self.tabs.addTab(tab, "Comparison")

    def load_file(self, file_path: str):
        """
        Load and display metadata for a file.

        Args:
            file_path: Path to file
        """
        if not self.exiftool_available:
            return

        self.current_file = file_path

        # Extract metadata
        try:
            self.current_metadata = self.exiftool.extract_metadata(file_path, groups=True)

            # Display in tree
            self._populate_metadata_tree(self.current_metadata)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to extract metadata:\n{str(e)}"
            )

    def _populate_metadata_tree(self, metadata: Dict[str, Any]):
        """Populate metadata tree widget"""
        self.metadata_tree.clear()

        if not metadata:
            item = QTreeWidgetItem(['No metadata found', ''])
            self.metadata_tree.addTopLevelItem(item)
            return

        # Group by category
        groups = {}
        for key, value in metadata.items():
            # Extract group name
            if ':' in key:
                group, field = key.split(':', 1)
            else:
                group = 'Other'
                field = key

            if group not in groups:
                groups[group] = {}

            groups[group][field] = value

        # Create tree items
        for group_name in sorted(groups.keys()):
            group_item = QTreeWidgetItem([group_name, ''])
            group_item.setFont(0, QFont('Arial', 10, QFont.Weight.Bold))

            for field, value in sorted(groups[group_name].items()):
                # Format value
                if isinstance(value, (list, dict)):
                    value_str = json.dumps(value, indent=2)
                else:
                    value_str = str(value)

                field_item = QTreeWidgetItem([field, value_str])
                group_item.addChild(field_item)

            self.metadata_tree.addTopLevelItem(group_item)
            group_item.setExpanded(True)

    def _filter_metadata(self, search_text: str):
        """Filter metadata tree based on search text"""
        if not search_text:
            # Show all
            for i in range(self.metadata_tree.topLevelItemCount()):
                item = self.metadata_tree.topLevelItem(i)
                item.setHidden(False)
                for j in range(item.childCount()):
                    item.child(j).setHidden(False)
            return

        search_text = search_text.lower()

        # Filter items
        for i in range(self.metadata_tree.topLevelItemCount()):
            group_item = self.metadata_tree.topLevelItem(i)
            group_visible = False

            for j in range(group_item.childCount()):
                child_item = group_item.child(j)
                field = child_item.text(0).lower()
                value = child_item.text(1).lower()

                visible = search_text in field or search_text in value
                child_item.setHidden(not visible)

                if visible:
                    group_visible = True

            group_item.setHidden(not group_visible)

    def _edit_selected_field(self):
        """Edit selected metadata field"""
        if not self.current_file:
            return

        selected = self.metadata_tree.selectedItems()
        if not selected:
            QMessageBox.information(self, "Info", "Please select a field to edit")
            return

        item = selected[0]
        if not item.parent():  # Group item
            return

        field_name = item.text(0)
        current_value = item.text(1)

        # Simple edit dialog
        from PyQt6.QtWidgets import QInputDialog
        new_value, ok = QInputDialog.getText(
            self,
            "Edit Metadata",
            f"Edit {field_name}:",
            text=current_value
        )

        if ok and new_value:
            # Update metadata
            success = self.exiftool.set_tag(self.current_file, field_name, new_value)

            if success:
                QMessageBox.information(self, "Success", "Metadata updated successfully")
                self._refresh_metadata()
                self.metadata_changed.emit(self.current_file)
            else:
                QMessageBox.critical(self, "Error", "Failed to update metadata")

    def _strip_metadata(self):
        """Remove all metadata from current file"""
        if not self.current_file:
            return

        reply = QMessageBox.question(
            self,
            "Confirm",
            "Remove all metadata from this file?\nThis cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success = self.exiftool.remove_all_metadata(self.current_file)

            if success:
                QMessageBox.information(self, "Success", "All metadata removed")
                self._refresh_metadata()
                self.metadata_changed.emit(self.current_file)
            else:
                QMessageBox.critical(self, "Error", "Failed to remove metadata")

    def _refresh_metadata(self):
        """Refresh metadata for current file"""
        if self.current_file:
            self.exiftool.clear_cache()
            self.load_file(self.current_file)

    def _export_metadata(self, format_type: str):
        """Export metadata to file"""
        if not self.current_metadata:
            QMessageBox.information(self, "Info", "No metadata to export")
            return

        # Get save path
        ext = 'json' if format_type == 'json' else 'csv'
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Metadata",
            f"metadata.{ext}",
            f"{ext.upper()} Files (*.{ext})"
        )

        if not file_path:
            return

        try:
            if format_type == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_metadata, f, indent=2, default=str)
            elif format_type == 'csv':
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Field', 'Value'])
                    for key, value in self.current_metadata.items():
                        writer.writerow([key, str(value)])

            QMessageBox.information(self, "Success", f"Metadata exported to:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export metadata:\n{str(e)}")

    def _run_forensic_analysis(self):
        """Run forensic analysis on current file"""
        if not self.current_file:
            return

        try:
            # Run analysis
            analysis = self.analyzer.analyze_file(self.current_file)

            # Format results
            result_text = self._format_forensic_results(analysis)
            self.forensic_text.setPlainText(result_text)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to run forensic analysis:\n{str(e)}"
            )

    def _format_forensic_results(self, analysis: Dict) -> str:
        """Format forensic analysis results for display"""
        lines = [
            "=" * 80,
            "FORENSIC ANALYSIS RESULTS",
            "=" * 80,
            ""
        ]

        # Camera info
        camera_info = analysis.get('camera_info', {})
        if camera_info:
            lines.append("CAMERA INFORMATION:")
            for key, value in camera_info.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        # GPS info
        gps_info = analysis.get('gps_info', {})
        if gps_info:
            lines.append("GPS LOCATION:")
            for key, value in gps_info.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        # Date/Time info
        datetime_info = analysis.get('datetime_info', {})
        if datetime_info:
            lines.append("DATE/TIME INFORMATION:")
            for key, value in datetime_info.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        # Software info
        software_info = analysis.get('software_info', {})
        if software_info:
            lines.append("SOFTWARE INFORMATION:")
            for key, value in software_info.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        # Anomalies
        anomalies = analysis.get('anomalies', [])
        if anomalies:
            lines.append("DETECTED ANOMALIES:")
            for anomaly in anomalies:
                lines.append(f"  - {anomaly}")
            lines.append("")

        # Device fingerprint
        fingerprint = analysis.get('device_fingerprint', '')
        if fingerprint:
            lines.append("DEVICE FINGERPRINT:")
            lines.append(f"  {fingerprint}")
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def _generate_report(self):
        """Generate comprehensive forensic report"""
        if not self.current_file:
            return

        # Ask for format
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Generate Report")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Select report format:"))

        html_radio = QRadioButton("HTML Report")
        html_radio.setChecked(True)
        layout.addWidget(html_radio)

        text_radio = QRadioButton("Text Report")
        layout.addWidget(text_radio)

        json_radio = QRadioButton("JSON Report")
        layout.addWidget(json_radio)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        # Determine format
        if html_radio.isChecked():
            format_type = 'html'
            ext = 'html'
        elif text_radio.isChecked():
            format_type = 'txt'
            ext = 'txt'
        else:
            format_type = 'json'
            ext = 'json'

        # Get save path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            f"forensic_report.{ext}",
            f"{ext.upper()} Files (*.{ext})"
        )

        if not file_path:
            return

        try:
            # Generate report
            report = self.report_gen.generate_file_report(self.current_file, format_type)

            # Save report
            self.report_gen.save_report(report, file_path)

            QMessageBox.information(
                self,
                "Success",
                f"Forensic report saved to:\n{file_path}"
            )

            # Open report
            reply = QMessageBox.question(
                self,
                "Open Report",
                "Would you like to open the report now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                os.startfile(file_path)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate report:\n{str(e)}"
            )

    def _save_forensic_report(self):
        """Save current forensic analysis"""
        text = self.forensic_text.toPlainText()
        if not text:
            QMessageBox.information(self, "Info", "No analysis results to save")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Analysis",
            "forensic_analysis.txt",
            "Text Files (*.txt)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                QMessageBox.information(self, "Success", "Analysis saved")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save:\n{str(e)}")

    def _select_comparison_file(self):
        """Select file for comparison"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Compare",
            "",
            "All Files (*.*)"
        )

        if file_path:
            self.comparison_file = file_path
            self.compare_file_label.setText(os.path.basename(file_path))

    def _compare_files(self):
        """Compare current file with selected file"""
        if not self.current_file:
            QMessageBox.information(self, "Info", "No current file")
            return

        if not self.comparison_file:
            QMessageBox.information(self, "Info", "Please select a file to compare")
            return

        try:
            # Compare
            comparison = self.analyzer.compare_metadata(
                self.current_file,
                self.comparison_file
            )

            # Format results
            result_text = self._format_comparison_results(comparison)
            self.comparison_text.setPlainText(result_text)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to compare files:\n{str(e)}"
            )

    def _format_comparison_results(self, comparison: Dict) -> str:
        """Format comparison results"""
        lines = [
            "=" * 80,
            "METADATA COMPARISON RESULTS",
            "=" * 80,
            f"Similarity Score: {comparison['similarity_score']:.2%}",
            ""
        ]

        # Similarities
        similarities = comparison.get('similarities', {})
        if similarities:
            lines.append(f"COMMON FIELDS ({len(similarities)}):")
            for key, value in list(similarities.items())[:20]:  # Show first 20
                lines.append(f"  {key}: {value}")
            if len(similarities) > 20:
                lines.append(f"  ... and {len(similarities) - 20} more")
            lines.append("")

        # Differences
        differences = comparison.get('differences', {})
        if differences:
            lines.append(f"DIFFERENT VALUES ({len(differences)}):")
            for key, values in list(differences.items())[:20]:
                lines.append(f"  {key}:")
                lines.append(f"    File 1: {values['file1']}")
                lines.append(f"    File 2: {values['file2']}")
            if len(differences) > 20:
                lines.append(f"  ... and {len(differences) - 20} more")
            lines.append("")

        # Only in file 1
        only_1 = comparison.get('only_in_file1', {})
        if only_1:
            lines.append(f"ONLY IN FILE 1 ({len(only_1)}):")
            for key in list(only_1.keys())[:10]:
                lines.append(f"  {key}")
            if len(only_1) > 10:
                lines.append(f"  ... and {len(only_1) - 10} more")
            lines.append("")

        # Only in file 2
        only_2 = comparison.get('only_in_file2', {})
        if only_2:
            lines.append(f"ONLY IN FILE 2 ({len(only_2)}):")
            for key in list(only_2.keys())[:10]:
                lines.append(f"  {key}")
            if len(only_2) > 10:
                lines.append(f"  ... and {len(only_2) - 10} more")
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)
