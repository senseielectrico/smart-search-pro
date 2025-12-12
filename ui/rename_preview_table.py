"""
Rename Preview Table - Show original and new names with conflict detection
"""

from typing import List, Tuple, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QPushButton, QCheckBox, QComboBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QFont


class RenamePreviewTable(QWidget):
    """
    Preview table showing old and new file names

    Features:
    - Color-coded changes (green=change, red=conflict, gray=no change)
    - Highlight differences
    - Filter by status
    - Select/deselect files
    - Statistics
    """

    selection_changed = pyqtSignal(list)  # List of selected row indices

    def __init__(self, parent=None):
        super().__init__(parent)
        self.previews: List[Tuple[str, str, bool]] = []  # (old, new, has_conflict)
        self._init_ui()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header = QHBoxLayout()

        title = QLabel("Preview")
        title.setStyleSheet("font-weight: bold; font-size: 11pt;")
        header.addWidget(title)

        # Statistics
        self.stats_label = QLabel("0 files")
        self.stats_label.setStyleSheet("color: #666;")
        header.addWidget(self.stats_label)

        header.addStretch()

        # Filter
        header.addWidget(QLabel("Show:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Files", "all")
        self.filter_combo.addItem("Changed Only", "changed")
        self.filter_combo.addItem("Conflicts Only", "conflicts")
        self.filter_combo.addItem("No Change", "unchanged")
        self.filter_combo.currentIndexChanged.connect(self._apply_filter)
        header.addWidget(self.filter_combo)

        layout.addLayout(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Original Name", "New Name", "Status"])

        # Column settings
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 100)

        # Selection
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        # Styling
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 4px;
            }
        """)

        layout.addWidget(self.table)

        # Legend
        legend = QHBoxLayout()
        legend.addWidget(self._create_legend_item("✓ Will rename", "#4CAF50"))
        legend.addWidget(self._create_legend_item("⚠ Conflict", "#F44336"))
        legend.addWidget(self._create_legend_item("- No change", "#9E9E9E"))
        legend.addStretch()
        layout.addLayout(legend)

    def _create_legend_item(self, text: str, color: str) -> QLabel:
        """Create a legend label"""
        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 9pt;
                padding: 2px 8px;
            }}
        """)
        return label

    def set_previews(self, previews: List[Tuple[str, str, bool]]):
        """
        Set preview data

        Args:
            previews: List of (old_name, new_name, has_conflict) tuples
        """
        self.previews = previews
        self._populate_table()
        self._update_stats()

    def _populate_table(self):
        """Populate table with preview data"""
        self.table.setRowCount(0)

        for old_name, new_name, has_conflict in self.previews:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Original name
            old_item = QTableWidgetItem(old_name)
            old_item.setFlags(old_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, old_item)

            # New name
            new_item = QTableWidgetItem(new_name)
            new_item.setFlags(new_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Determine status and color
            no_change = old_name == new_name

            if has_conflict:
                status = "⚠ Conflict"
                color = QColor("#F44336")
                new_item.setForeground(QBrush(color))
                old_item.setForeground(QBrush(color))
            elif no_change:
                status = "- No change"
                color = QColor("#9E9E9E")
                new_item.setForeground(QBrush(color))
                old_item.setForeground(QBrush(color))
            else:
                status = "✓ Will rename"
                color = QColor("#4CAF50")
                new_item.setForeground(QBrush(color))

                # Bold for changed files
                font = new_item.font()
                font.setBold(True)
                new_item.setFont(font)

            self.table.setItem(row, 1, new_item)

            # Status
            status_item = QTableWidgetItem(status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            status_item.setForeground(QBrush(color))
            self.table.setItem(row, 2, status_item)

    def _update_stats(self):
        """Update statistics label"""
        total = len(self.previews)
        conflicts = sum(1 for _, _, conflict in self.previews if conflict)
        changes = sum(1 for old, new, _ in self.previews if old != new)
        no_change = total - changes

        stats = f"{total} files"
        if changes > 0:
            stats += f" • {changes} will rename"
        if conflicts > 0:
            stats += f" • {conflicts} conflicts"
        if no_change > 0:
            stats += f" • {no_change} unchanged"

        self.stats_label.setText(stats)

    def _apply_filter(self):
        """Apply filter to table"""
        filter_type = self.filter_combo.currentData()

        for row in range(self.table.rowCount()):
            if row >= len(self.previews):
                break

            old_name, new_name, has_conflict = self.previews[row]
            no_change = old_name == new_name

            show = True
            if filter_type == "changed":
                show = not no_change
            elif filter_type == "conflicts":
                show = has_conflict
            elif filter_type == "unchanged":
                show = no_change

            self.table.setRowHidden(row, not show)

    def _on_selection_changed(self):
        """Handle selection change"""
        selected_rows = [item.row() for item in self.table.selectedItems()]
        selected_rows = list(set(selected_rows))  # Unique rows
        self.selection_changed.emit(selected_rows)

    def has_conflicts(self) -> bool:
        """Check if there are any conflicts"""
        return any(conflict for _, _, conflict in self.previews)

    def get_conflict_count(self) -> int:
        """Get number of conflicts"""
        return sum(1 for _, _, conflict in self.previews if conflict)

    def get_change_count(self) -> int:
        """Get number of files that will change"""
        return sum(1 for old, new, _ in self.previews if old != new)

    def get_selected_indices(self) -> List[int]:
        """Get indices of selected rows"""
        return list(set(item.row() for item in self.table.selectedItems()))

    def select_all(self):
        """Select all rows"""
        self.table.selectAll()

    def deselect_all(self):
        """Deselect all rows"""
        self.table.clearSelection()

    def select_conflicts(self):
        """Select only rows with conflicts"""
        self.table.clearSelection()
        for row, (_, _, has_conflict) in enumerate(self.previews):
            if has_conflict:
                self.table.selectRow(row)

    def clear(self):
        """Clear table"""
        self.previews.clear()
        self.table.setRowCount(0)
        self.stats_label.setText("0 files")

    def export_to_csv(self, file_path: str) -> bool:
        """
        Export preview to CSV file

        Returns:
            True if exported successfully
        """
        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Original Name', 'New Name', 'Has Conflict'])

                for old_name, new_name, has_conflict in self.previews:
                    writer.writerow([old_name, new_name, 'Yes' if has_conflict else 'No'])

            return True
        except Exception:
            return False

    def highlight_differences(self, row: int):
        """
        Highlight character differences between old and new names

        This is a visual enhancement for showing exactly what changed
        """
        if row >= len(self.previews):
            return

        old_name, new_name, _ = self.previews[row]

        # Simple diff - highlight first difference
        min_len = min(len(old_name), len(new_name))
        diff_start = -1

        for i in range(min_len):
            if old_name[i] != new_name[i]:
                diff_start = i
                break

        # Could use HTML to highlight, but keeping it simple for now
        # Future enhancement: use rich text to show character-level diffs
