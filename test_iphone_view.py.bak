"""
Test iPhone View - Test the iOS-style file browser
"""

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt6.QtCore import Qt
import sys
import os

# Import the iPhone view components
from views.iphone_view import iPhoneFileView
from ui.iphone_view_panel import iPhoneViewPanel
from ui.iphone_widgets import (
    CategoryCardWidget, CategoryIconWidget,
    iOSToggleSwitch, RoundedCardWidget
)
from categories import FileCategory


class TestWindow(QMainWindow):
    """Test window for iPhone view components"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("iPhone View Test - Smart Search Pro")
        self.resize(1200, 800)

        # Create tab widget
        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        # Tab 1: Full iPhone View
        self._create_full_view_tab(tabs)

        # Tab 2: Widget Gallery
        self._create_widget_gallery_tab(tabs)

        # Tab 3: Category Browser Test
        self._create_browser_test_tab(tabs)

    def _create_full_view_tab(self, tabs: QTabWidget):
        """Create full iPhone view tab"""
        view = iPhoneFileView()

        # Set default path
        default_path = os.path.join(
            os.environ.get('USERPROFILE', ''),
            'Documents'
        )

        if os.path.exists(default_path):
            view.set_path(default_path)

        # Connect signals
        view.category_selected.connect(
            lambda cat: print(f"Category selected: {cat.value}")
        )
        view.file_opened.connect(
            lambda path: print(f"File opened: {path}")
        )

        tabs.addTab(view, "Full View")

    def _create_widget_gallery_tab(self, tabs: QTabWidget):
        """Create widget gallery tab"""
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title = QLabel("iOS Widget Gallery")
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Category cards grid
        cards_label = QLabel("Category Cards:")
        layout.addWidget(cards_label)

        grid = QGridLayout()
        grid.setSpacing(16)

        categories = [
            FileCategory.IMAGENES,
            FileCategory.VIDEOS,
            FileCategory.AUDIO,
            FileCategory.DOCUMENTOS,
            FileCategory.CODIGO,
            FileCategory.COMPRIMIDOS,
        ]

        for i, category in enumerate(categories):
            card = CategoryCardWidget(
                category.value,
                count=100 + i * 50,
                size=f"{i + 1} GB"
            )
            card.clicked.connect(
                lambda c=category: print(f"Card clicked: {c.value}")
            )
            grid.addWidget(card, i // 3, i % 3)

        layout.addLayout(grid)

        # Toggle switches
        toggle_label = QLabel("iOS Toggle Switches:")
        layout.addWidget(toggle_label)

        from PyQt6.QtWidgets import QHBoxLayout

        toggle_layout = QHBoxLayout()
        toggle_layout.setSpacing(20)

        for i in range(3):
            toggle = iOSToggleSwitch()
            toggle.setChecked(i % 2 == 0)
            toggle.toggled.connect(
                lambda state, n=i: print(f"Toggle {n}: {state}")
            )
            toggle_layout.addWidget(toggle)

        toggle_layout.addStretch()
        layout.addLayout(toggle_layout)

        layout.addStretch()

        tabs.addTab(widget, "Widget Gallery")

    def _create_browser_test_tab(self, tabs: QTabWidget):
        """Create category browser test tab"""
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
        from views.category_scanner import CategoryData

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title
        title = QLabel("Category Browser Test")
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Info
        info = QLabel(
            "Click buttons to test category browser with sample data:"
        )
        layout.addWidget(info)

        # Test buttons
        from ui.category_browser import CategoryBrowser

        def show_browser(category: FileCategory):
            """Show browser with test data"""
            # Create test data
            test_data = CategoryData(category=category)

            for i in range(20):
                ext = {
                    FileCategory.IMAGENES: '.jpg',
                    FileCategory.VIDEOS: '.mp4',
                    FileCategory.AUDIO: '.mp3',
                    FileCategory.DOCUMENTOS: '.pdf',
                    FileCategory.CODIGO: '.py',
                }.get(category, '.txt')

                test_data.add_file({
                    'name': f'test_file_{i}{ext}',
                    'path': f'C:/test/test_file_{i}{ext}',
                    'size': 1024 * (i + 1) * 100,
                    'modified': 1700000000 + i * 3600,
                    'accessed': 1700000000 + i * 3600,
                    'created': 1700000000,
                    'extension': ext,
                    'mime_type': 'application/octet-stream',
                })

            # Show browser
            browser = CategoryBrowser(category, test_data, self)
            browser.exec()

        test_categories = [
            FileCategory.IMAGENES,
            FileCategory.VIDEOS,
            FileCategory.AUDIO,
            FileCategory.DOCUMENTOS,
            FileCategory.CODIGO,
        ]

        for category in test_categories:
            btn = QPushButton(f"Test {category.value} Browser")
            btn.clicked.connect(lambda checked, c=category: show_browser(c))
            layout.addWidget(btn)

        layout.addStretch()

        tabs.addTab(widget, "Browser Test")


def main():
    """Run test application"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Create and show test window
    window = TestWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
