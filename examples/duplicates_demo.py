"""
Duplicates Panel Demo

Demonstrates the fully functional duplicate file finder UI.

Usage:
    python examples/duplicates_demo.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt
from ui.duplicates_panel import DuplicatesPanel


class DuplicatesDemoWindow(QMainWindow):
    """Demo window for duplicates panel"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Search Pro - Duplicates Finder Demo")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("Duplicate File Finder")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #0078D4;")
        layout.addWidget(header)

        # Subheader
        subheader = QLabel(
            "Find and remove duplicate files to free up disk space. "
            "Click 'Scan for Duplicates' to get started."
        )
        subheader.setWordWrap(True)
        subheader.setStyleSheet("font-size: 12px; color: #605E5C; margin-bottom: 10px;")
        layout.addWidget(subheader)

        # Add duplicates panel
        self.duplicates_panel = DuplicatesPanel()
        layout.addWidget(self.duplicates_panel, stretch=1)

        # Connect signals (optional)
        self.duplicates_panel.delete_requested.connect(self._on_delete_requested)

        # Apply basic styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
            QPushButton:disabled {
                background-color: #E1DFDD;
                color: #A19F9D;
            }
            QPushButton[secondary="true"] {
                background-color: #F3F3F3;
                color: #000000;
                border: 1px solid #8A8886;
            }
            QPushButton[secondary="true"]:hover {
                background-color: #E1DFDD;
            }
            QLabel[heading="true"] {
                font-size: 16pt;
                font-weight: bold;
            }
            QLabel[subheading="true"] {
                font-size: 11pt;
                font-weight: bold;
                color: #605E5C;
            }
            QTreeWidget {
                border: 1px solid #E1DFDD;
                border-radius: 4px;
                background-color: white;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:hover {
                background-color: #F3F3F3;
            }
            QTreeWidget::item:selected {
                background-color: #E5F3FF;
                color: #000000;
            }
            QComboBox {
                border: 1px solid #8A8886;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #0078D4;
            }
            QProgressBar {
                border: 1px solid #E1DFDD;
                border-radius: 4px;
                text-align: center;
                background-color: #F3F3F3;
            }
            QProgressBar::chunk {
                background-color: #0078D4;
                border-radius: 3px;
            }
        """)

    def _on_delete_requested(self, paths):
        """Handle delete request signal"""
        print(f"Delete requested for {len(paths)} files")
        # Could add additional confirmation or logging here


def main():
    """Run the demo"""
    app = QApplication(sys.argv)

    # Set application info
    app.setApplicationName("Smart Search Pro - Duplicates Demo")
    app.setOrganizationName("Smart Search")

    # Create and show window
    window = DuplicatesDemoWindow()
    window.show()

    # Print instructions
    print("=" * 60)
    print("DUPLICATES FINDER DEMO")
    print("=" * 60)
    print("\nFeatures demonstrated:")
    print("  1. Click 'Scan for Duplicates' to select a folder")
    print("  2. Watch real-time progress during scan")
    print("  3. View duplicate groups sorted by wasted space")
    print("  4. Use 'Auto-select' dropdown to apply strategies:")
    print("     - Keep Oldest: Keeps oldest file, marks others for deletion")
    print("     - Keep Newest: Keeps newest file, marks others for deletion")
    print("     - Keep Shortest Path: Keeps file with shortest path")
    print("     - Keep First Alphabetical: Keeps first alphabetically")
    print("  5. Manually check/uncheck files")
    print("  6. Right-click files for context menu:")
    print("     - Keep This, Delete Others")
    print("     - Open File Location")
    print("  7. Click 'Delete Selected' to remove duplicates")
    print("  8. Click 'Move Selected' to move duplicates to folder")
    print("\nBackend features:")
    print("  - Multi-threaded scanning (4 workers)")
    print("  - Hash caching for performance")
    print("  - Three-pass algorithm (size -> quick hash -> full hash)")
    print("  - Safe deletion via Recycle Bin (if send2trash installed)")
    print("  - Audit logging of all operations")
    print("  - Real-time progress updates")
    print("\nStats displayed:")
    print("  - Number of duplicate groups")
    print("  - Total duplicate files")
    print("  - Total wasted space")
    print("=" * 60)
    print("\nClose the window to exit.\n")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
