"""
Comparison Dialog - Quick comparison dialog for fast directory comparisons

Features:
- Compact dialog for quick comparisons
- Recent directories history
- Swap source/target button
- Quick results summary
- Launch full comparison panel
"""

import json
import sys
from pathlib import Path
from typing import List, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFileDialog, QMessageBox, QGroupBox,
    QProgressBar, QTextEdit, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from comparison.folder_comparator import (
    FolderComparator,
    ComparisonMode,
    ComparisonResult,
    format_size
)
from core.logger import get_logger

logger = get_logger(__name__)


class ComparisonDialog(QDialog):
    """
    Quick comparison dialog for fast directory comparisons.

    Usage:
        dialog = ComparisonDialog(parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            result = dialog.get_result()
    """

    comparison_requested = pyqtSignal(Path, Path)  # source, target

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Quick Folder Comparison")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        # State
        self.comparison_result: Optional[ComparisonResult] = None
        self.history_file = Path.home() / '.cache' / 'smart_search' / 'comparison_history.json'
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

        self._init_ui()
        self._load_history()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header = QLabel("Quick Folder Comparison")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)

        # Directory selection group
        dir_group = QGroupBox("Directories")
        dir_layout = QVBoxLayout(dir_group)

        # Source directory
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Source:"))

        self.source_combo = QComboBox()
        self.source_combo.setEditable(True)
        self.source_combo.setMinimumWidth(350)
        source_layout.addWidget(self.source_combo, 1)

        source_browse_btn = QPushButton("Browse...")
        source_browse_btn.clicked.connect(self._browse_source)
        source_layout.addWidget(source_browse_btn)

        dir_layout.addLayout(source_layout)

        # Target directory
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Target:"))

        self.target_combo = QComboBox()
        self.target_combo.setEditable(True)
        self.target_combo.setMinimumWidth(350)
        target_layout.addWidget(self.target_combo, 1)

        target_browse_btn = QPushButton("Browse...")
        target_browse_btn.clicked.connect(self._browse_target)
        target_layout.addWidget(target_browse_btn)

        dir_layout.addLayout(target_layout)

        # Swap button
        swap_layout = QHBoxLayout()
        swap_layout.addStretch()
        swap_btn = QPushButton("⇅ Swap Directories")
        swap_btn.clicked.connect(self._swap_directories)
        swap_layout.addWidget(swap_btn)
        dir_layout.addLayout(swap_layout)

        layout.addWidget(dir_group)

        # Options group
        options_group = QGroupBox("Options")
        options_layout = QHBoxLayout(options_group)

        options_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Content Hash", ComparisonMode.CONTENT_HASH)
        self.mode_combo.addItem("Size + Name", ComparisonMode.SIZE_NAME)
        self.mode_combo.addItem("Name Only", ComparisonMode.NAME_ONLY)
        options_layout.addWidget(self.mode_combo)

        self.recursive_check = QCheckBox("Recursive")
        self.recursive_check.setChecked(True)
        options_layout.addWidget(self.recursive_check)

        options_layout.addStretch()

        layout.addWidget(options_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Results
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(200)
        self.results_text.setPlainText("Click 'Compare' to start comparison...")
        results_layout.addWidget(self.results_text)

        layout.addWidget(results_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.compare_btn = QPushButton("Compare")
        self.compare_btn.setDefault(True)
        self.compare_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                padding: 8px 24px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
        """)
        self.compare_btn.clicked.connect(self._compare)
        button_layout.addWidget(self.compare_btn)

        self.full_view_btn = QPushButton("Full View")
        self.full_view_btn.clicked.connect(self._open_full_view)
        self.full_view_btn.setEnabled(False)
        button_layout.addWidget(self.full_view_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _browse_source(self):
        """Browse for source directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Source Directory",
            self.source_combo.currentText()
        )
        if directory:
            self.source_combo.setCurrentText(directory)

    def _browse_target(self):
        """Browse for target directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Target Directory",
            self.target_combo.currentText()
        )
        if directory:
            self.target_combo.setCurrentText(directory)

    def _swap_directories(self):
        """Swap source and target directories."""
        source_text = self.source_combo.currentText()
        target_text = self.target_combo.currentText()

        self.source_combo.setCurrentText(target_text)
        self.target_combo.setCurrentText(source_text)

    def _compare(self):
        """Execute comparison."""
        source_path = Path(self.source_combo.currentText())
        target_path = Path(self.target_combo.currentText())

        # Validate
        if not source_path.exists() or not source_path.is_dir():
            QMessageBox.warning(self, "Invalid Source", "Source directory does not exist.")
            return

        if not target_path.exists() or not target_path.is_dir():
            QMessageBox.warning(self, "Invalid Target", "Target directory does not exist.")
            return

        if source_path == target_path:
            QMessageBox.warning(self, "Same Directory", "Source and target cannot be the same.")
            return

        # Get options
        mode = self.mode_combo.currentData()
        recursive = self.recursive_check.isChecked()

        # Show progress
        self.progress_bar.show()
        self.progress_bar.setMaximum(0)  # Indeterminate
        self.compare_btn.setEnabled(False)
        self.results_text.setPlainText("Comparing directories...\n")

        try:
            # Run comparison
            comparator = FolderComparator(mode=mode)

            def progress_callback(current, total):
                if total > 0:
                    self.progress_bar.setMaximum(total)
                    self.progress_bar.setValue(current)

            result = comparator.compare(
                source=source_path,
                target=target_path,
                recursive=recursive,
                progress_callback=progress_callback
            )

            self.comparison_result = result
            self._display_results(result)
            self._save_history(source_path, target_path)
            self.full_view_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Comparison Failed", f"Error: {e}")
            self.results_text.setPlainText(f"Comparison failed: {e}")

        finally:
            self.progress_bar.hide()
            self.compare_btn.setEnabled(True)

    def _display_results(self, result: ComparisonResult):
        """Display comparison results."""
        lines = []
        lines.append("=" * 60)
        lines.append("COMPARISON RESULTS")
        lines.append("=" * 60)
        lines.append(f"Source: {result.source_dir}")
        lines.append(f"Target: {result.target_dir}")
        lines.append(f"Mode: {result.mode.value}")
        lines.append(f"Duration: {result.duration:.2f}s")
        lines.append("-" * 60)

        stats = result.stats
        lines.append(f"Total Files: {stats.total_files}")
        lines.append(f"  ✓ Same: {stats.same_files}")
        lines.append(f"  ⚠ Different: {stats.different_files}")
        lines.append(f"  ← Missing in Target: {stats.missing_in_target}")
        lines.append(f"  → Extra in Target: {stats.extra_in_target}")
        lines.append("-" * 60)
        lines.append(f"Source Size: {format_size(stats.total_source_size)}")
        lines.append(f"Target Size: {format_size(stats.total_target_size)}")
        lines.append(f"Missing Size: {format_size(stats.missing_size)}")
        lines.append(f"Extra Size: {format_size(stats.extra_size)}")
        lines.append(f"Duplicate Size: {format_size(stats.duplicate_size)}")
        lines.append(f"Space Savings Potential: {format_size(stats.space_savings_potential)}")
        lines.append("=" * 60)

        # Show sample files
        if stats.missing_in_target > 0:
            lines.append("\nSample Missing Files (up to 5):")
            missing = result.get_missing_files()[:5]
            for comp in missing:
                lines.append(f"  ← {comp.relative_path}")

        if stats.extra_in_target > 0:
            lines.append("\nSample Extra Files (up to 5):")
            extra = result.get_extra_files()[:5]
            for comp in extra:
                lines.append(f"  → {comp.relative_path}")

        if stats.different_files > 0:
            lines.append("\nSample Different Files (up to 5):")
            different = result.get_different_files()[:5]
            for comp in different:
                lines.append(f"  ⚠ {comp.relative_path}")

        self.results_text.setPlainText('\n'.join(lines))

    def _open_full_view(self):
        """Open full comparison panel."""
        if self.comparison_result:
            source = self.comparison_result.source_dir
            target = self.comparison_result.target_dir
            self.comparison_requested.emit(source, target)
            self.accept()

    def _load_history(self):
        """Load directory history."""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    history = json.load(f)

                sources = history.get('sources', [])
                targets = history.get('targets', [])

                self.source_combo.addItems(sources)
                self.target_combo.addItems(targets)

        except Exception as e:
            logger.error(f"Failed to load history: {e}")

    def _save_history(self, source: Path, target: Path):
        """Save directory to history."""
        try:
            # Load existing history
            history = {'sources': [], 'targets': []}
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    history = json.load(f)

            # Add to history (avoid duplicates, limit to 10)
            source_str = str(source)
            target_str = str(target)

            if source_str in history['sources']:
                history['sources'].remove(source_str)
            history['sources'].insert(0, source_str)
            history['sources'] = history['sources'][:10]

            if target_str in history['targets']:
                history['targets'].remove(target_str)
            history['targets'].insert(0, target_str)
            history['targets'] = history['targets'][:10]

            # Save
            with open(self.history_file, 'w') as f:
                json.dumps(history, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def get_result(self) -> Optional[ComparisonResult]:
        """Get comparison result."""
        return self.comparison_result

    def set_directories(self, source: Path, target: Path):
        """Set initial directories."""
        self.source_combo.setCurrentText(str(source))
        self.target_combo.setCurrentText(str(target))


# Convenience function
def quick_compare(source: Path, target: Path, parent=None) -> Optional[ComparisonResult]:
    """
    Show quick comparison dialog and return result.

    Args:
        source: Source directory
        target: Target directory
        parent: Parent widget

    Returns:
        ComparisonResult if comparison was performed, None otherwise
    """
    dialog = ComparisonDialog(parent)
    dialog.set_directories(source, target)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_result()

    return None
