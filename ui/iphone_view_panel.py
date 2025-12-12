"""
iPhone View Panel - iOS-style file categorization view
Main panel showing category cards grid with smooth animations
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox,
    QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QIcon

from typing import Dict, Optional
import os

from categories import FileCategory
from views.category_scanner import CategoryScanner, CategoryData, BackgroundScanner
from ui.iphone_widgets import (
    CategoryCardWidget, SmoothScrollArea,
    PullToRefreshWidget, BlurBackgroundWidget
)
from ui.category_browser import CategoryBrowser
from utils import format_file_size


class iPhoneViewPanel(QWidget):
    """
    iOS-style file categorization panel
    Shows category cards in a grid with smooth animations
    """

    category_selected = pyqtSignal(FileCategory)
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scanner = CategoryScanner(cache_enabled=True)
        self.categories_data: Dict[FileCategory, CategoryData] = {}
        self.current_path: Optional[str] = None
        self._background_scanner: Optional[BackgroundScanner] = None

        self._setup_ui()
        self._setup_default_scan()

    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self._create_header(layout)

        # Content area with smooth scrolling
        self._create_content_area(layout)

        # Apply theme
        self._apply_ios_theme()

    def _create_header(self, parent_layout: QVBoxLayout):
        """Create header with title and controls"""
        header = QWidget()
        header.setObjectName("iPhoneViewHeader")
        header.setMinimumHeight(60)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        header_layout.setSpacing(12)

        # Title
        title = QLabel("Browse Files")
        title.setObjectName("iPhoneViewTitle")
        font = title.font()
        font.setPointSize(18)
        font.setBold(True)
        title.setFont(font)
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Path selector
        self.path_combo = QComboBox()
        self.path_combo.setMinimumWidth(200)
        self.path_combo.addItem("Documents", os.path.join(
            os.environ.get('USERPROFILE', ''), 'Documents'
        ))
        self.path_combo.addItem("Downloads", os.path.join(
            os.environ.get('USERPROFILE', ''), 'Downloads'
        ))
        self.path_combo.addItem("Desktop", os.path.join(
            os.environ.get('USERPROFILE', ''), 'Desktop'
        ))
        self.path_combo.addItem("Pictures", os.path.join(
            os.environ.get('USERPROFILE', ''), 'Pictures'
        ))
        self.path_combo.currentIndexChanged.connect(self._on_path_changed)
        header_layout.addWidget(QLabel("Location:"))
        header_layout.addWidget(self.path_combo)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_scan)
        header_layout.addWidget(refresh_btn)

        parent_layout.addWidget(header)

        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Plain)
        parent_layout.addWidget(separator)

    def _create_content_area(self, parent_layout: QVBoxLayout):
        """Create scrollable content area with category cards"""
        # Smooth scroll area
        self.scroll_area = SmoothScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Content widget
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(20)

        # Stats section
        self._create_stats_section()

        # Categories grid
        self._create_categories_grid()

        # Recent files section
        self._create_recent_section()

        self.content_layout.addStretch()

        self.scroll_area.setWidget(content_widget)
        parent_layout.addWidget(self.scroll_area)

    def _create_stats_section(self):
        """Create statistics summary section"""
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(20)

        # Total files stat
        self.total_files_label = self._create_stat_card("Total Files", "0")
        stats_layout.addWidget(self.total_files_label)

        # Total size stat
        self.total_size_label = self._create_stat_card("Total Size", "0 B")
        stats_layout.addWidget(self.total_size_label)

        # Categories count stat
        self.categories_count_label = self._create_stat_card("Categories", "0")
        stats_layout.addWidget(self.categories_count_label)

        stats_layout.addStretch()

        self.content_layout.addWidget(stats_widget)

    def _create_stat_card(self, title: str, value: str) -> QWidget:
        """Create a stat card widget"""
        card = QWidget()
        card.setMinimumWidth(150)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        font = value_label.font()
        font.setPointSize(20)
        font.setBold(True)
        value_label.setFont(font)

        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        title_label.setStyleSheet("color: #8E8E93;")

        layout.addWidget(value_label)
        layout.addWidget(title_label)

        # Store value label for updates
        card.value_label = value_label

        return card

    def _create_categories_grid(self):
        """Create grid of category cards"""
        # Section title
        section_title = QLabel("Categories")
        font = section_title.font()
        font.setPointSize(14)
        font.setBold(True)
        section_title.setFont(font)
        self.content_layout.addWidget(section_title)

        # Grid container
        grid_widget = QWidget()
        self.grid_layout = QGridLayout(grid_widget)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        # Create cards for each category
        self.category_cards: Dict[FileCategory, CategoryCardWidget] = {}

        categories = [
            FileCategory.IMAGENES,
            FileCategory.VIDEOS,
            FileCategory.AUDIO,
            FileCategory.DOCUMENTOS,
            FileCategory.CODIGO,
            FileCategory.COMPRIMIDOS,
            FileCategory.EJECUTABLES,
            FileCategory.DATOS,
        ]

        for i, category in enumerate(categories):
            card = CategoryCardWidget(
                category.value,
                count=0,
                size="0 B"
            )
            card.clicked.connect(lambda c=category: self._on_category_clicked(c))

            row = i // 4
            col = i % 4

            self.grid_layout.addWidget(card, row, col)
            self.category_cards[category] = card

        self.content_layout.addWidget(grid_widget)

    def _create_recent_section(self):
        """Create recent files section"""
        # Section title
        section_title = QLabel("Recent Files")
        font = section_title.font()
        font.setPointSize(14)
        font.setBold(True)
        section_title.setFont(font)
        self.content_layout.addWidget(section_title)

        # Recent files list (placeholder)
        self.recent_widget = QLabel("No recent files")
        self.recent_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.recent_widget.setMinimumHeight(100)
        self.recent_widget.setStyleSheet("color: #8E8E93;")
        self.content_layout.addWidget(self.recent_widget)

    def _apply_ios_theme(self):
        """Apply iOS-inspired styling"""
        self.setStyleSheet("""
            #iPhoneViewHeader {
                background-color: palette(base);
                border-bottom: 1px solid palette(mid);
            }

            #iPhoneViewTitle {
                color: palette(text);
            }

            #statValue {
                color: palette(text);
            }

            #statTitle {
                color: #8E8E93;
            }
        """)

    def _setup_default_scan(self):
        """Setup and perform initial scan"""
        # Get default path (Documents)
        default_path = self.path_combo.itemData(0)
        if default_path and os.path.exists(default_path):
            self.current_path = default_path
            self._start_scan(default_path)

    def _on_path_changed(self, index: int):
        """Handle path selection change"""
        path = self.path_combo.itemData(index)
        if path and os.path.exists(path):
            self.current_path = path
            self._start_scan(path)

    def _start_scan(self, path: str):
        """Start background scan of directory"""
        # Stop any existing scan
        if self._background_scanner and self._background_scanner.is_alive():
            self._background_scanner.stop()

        # Start new scan in background
        self._background_scanner = BackgroundScanner(
            self.scanner,
            path,
            self._on_scan_complete
        )
        self._background_scanner.start()

        # Show loading state
        self._show_loading_state()

    def _show_loading_state(self):
        """Show loading indicators"""
        for card in self.category_cards.values():
            card.updateData(0, "Loading...")

    def _on_scan_complete(self, categories: Dict[FileCategory, CategoryData]):
        """Handle scan completion"""
        self.categories_data = categories

        # Update stats
        breakdown = self.scanner.get_category_breakdown(categories)

        self.total_files_label.value_label.setText(str(breakdown['total_files']))
        self.total_size_label.value_label.setText(breakdown['formatted_size'])

        active_categories = sum(
            1 for data in categories.values() if data.file_count > 0
        )
        self.categories_count_label.value_label.setText(str(active_categories))

        # Update category cards
        for category, card in self.category_cards.items():
            data = categories.get(category)
            if data:
                card.updateData(data.file_count, data.formatted_size)
            else:
                card.updateData(0, "0 B")

        # Update recent files
        self._update_recent_files(categories)

    def _update_recent_files(self, categories: Dict[FileCategory, CategoryData]):
        """Update recent files display"""
        recent = self.scanner.get_recent_files(categories, limit=5)

        if recent:
            from datetime import datetime

            recent_text = "<table width='100%' style='color: palette(text);'>"
            for file_info in recent:
                name = file_info['name']
                if len(name) > 40:
                    name = name[:37] + "..."

                dt = datetime.fromtimestamp(file_info['modified'])
                date_str = dt.strftime('%Y-%m-%d %H:%M')

                recent_text += f"<tr><td>{name}</td><td align='right' style='color: #8E8E93;'>{date_str}</td></tr>"

            recent_text += "</table>"

            self.recent_widget.setText(recent_text)
            self.recent_widget.setTextFormat(Qt.TextFormat.RichText)
        else:
            self.recent_widget.setText("No recent files")

    def _on_category_clicked(self, category: FileCategory):
        """Handle category card click"""
        self.category_selected.emit(category)

        # Show category browser
        self._show_category_browser(category)

    def _show_category_browser(self, category: FileCategory):
        """Show browser for category files"""
        data = self.categories_data.get(category)

        if not data or data.file_count == 0:
            return

        # Create and show category browser dialog
        browser = CategoryBrowser(
            category=category,
            category_data=data,
            parent=self
        )
        browser.exec()

    def _refresh_scan(self):
        """Refresh current scan"""
        if self.current_path:
            self.scanner.clear_cache(self.current_path)
            self._start_scan(self.current_path)

        self.refresh_requested.emit()

    def set_path(self, path: str):
        """
        Set path to scan

        Args:
            path: Directory path to scan
        """
        if os.path.exists(path):
            self.current_path = path

            # Update combo box
            for i in range(self.path_combo.count()):
                if self.path_combo.itemData(i) == path:
                    self.path_combo.setCurrentIndex(i)
                    return

            # Add custom path
            self.path_combo.addItem(os.path.basename(path), path)
            self.path_combo.setCurrentIndex(self.path_combo.count() - 1)

    def get_category_data(self, category: FileCategory) -> Optional[CategoryData]:
        """
        Get data for a category

        Args:
            category: FileCategory to get data for

        Returns:
            CategoryData or None
        """
        return self.categories_data.get(category)


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Test panel
    panel = iPhoneViewPanel()
    panel.setWindowTitle("iPhone View Test")
    panel.resize(1000, 700)
    panel.show()

    sys.exit(app.exec())
