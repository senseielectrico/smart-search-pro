"""
Demo UI for Folder Comparison

Standalone demo that can be run independently to test the comparison UI.

Usage:
    python comparison/demo_ui.py
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.comparison_panel import ComparisonPanel
from ui.comparison_dialog import ComparisonDialog


class ComparisonDemo(QMainWindow):
    """Demo window for folder comparison."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Folder Comparison Demo - Smart Search Pro")
        self.setGeometry(100, 100, 1200, 800)

        # Create tab widget
        tabs = QTabWidget()

        # Add comparison panel
        self.comparison_panel = ComparisonPanel()
        tabs.addTab(self.comparison_panel, "Full Comparison")

        # Add quick comparison button
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

        quick_widget = QWidget()
        quick_layout = QVBoxLayout(quick_widget)

        quick_layout.addStretch()

        label = QLabel("Quick Comparison Dialog")
        label.setProperty("heading", True)
        label.setAlignment(0x0004)  # AlignCenter
        quick_layout.addWidget(label)

        open_dialog_btn = QPushButton("Open Quick Comparison Dialog")
        open_dialog_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                padding: 12px 24px;
                border-radius: 4px;
                font-size: 14pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
        """)
        open_dialog_btn.clicked.connect(self.open_quick_dialog)
        quick_layout.addWidget(open_dialog_btn, 0, 0x0004)  # AlignCenter

        quick_layout.addStretch()

        tabs.addTab(quick_widget, "Quick Dialog Demo")

        self.setCentralWidget(tabs)

        # Apply styles
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
            QLabel[heading="true"] {
                font-size: 18pt;
                font-weight: bold;
                color: #000000;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #CCCCCC;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: #0078D4;
            }
        """)

    def open_quick_dialog(self):
        """Open quick comparison dialog."""
        dialog = ComparisonDialog(self)

        # Set example directories (update these to real paths)
        dialog.source_combo.setCurrentText(str(Path.home() / 'Documents'))
        dialog.target_combo.setCurrentText(str(Path.home() / 'Desktop'))

        dialog.exec()


def main():
    """Run the demo."""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Create and show demo window
    demo = ComparisonDemo()
    demo.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    print("=" * 80)
    print("Folder Comparison Demo - Smart Search Pro")
    print("=" * 80)
    print("\nThis demo shows the folder comparison and sync features.")
    print("\nFeatures:")
    print("  - Compare two directories")
    print("  - Multiple comparison modes (content, size+name, name only)")
    print("  - Filter results by status")
    print("  - Batch actions (copy, delete, sync)")
    print("  - Export reports (CSV, HTML)")
    print("  - Quick comparison dialog")
    print("\nUsage:")
    print("  1. Select source and target directories")
    print("  2. Choose comparison mode")
    print("  3. Click 'Compare Directories'")
    print("  4. View results and perform actions")
    print("=" * 80)
    print("\nStarting application...\n")

    main()
