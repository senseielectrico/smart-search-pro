"""
Smart Search - Quick Example
Demonstrates basic usage and customization
"""

import sys
from PyQt6.QtWidgets import QApplication
from ui import SmartSearchWindow


def example_basic():
    """Basic usage - just launch the application"""
    app = QApplication(sys.argv)

    # Create and show window
    window = SmartSearchWindow()
    window.show()

    sys.exit(app.exec())


def example_custom_start():
    """Example with custom initial configuration"""
    app = QApplication(sys.argv)

    # Create window
    window = SmartSearchWindow()

    # Pre-fill search term
    window.search_input.setText("*.pdf")

    # Enable dark mode by default
    window.theme_btn.setChecked(True)
    window._toggle_theme(True)

    # Pre-check some directories (example)
    # You can programmatically check specific directories
    tree = window.dir_tree
    for i in range(tree.topLevelItemCount()):
        item = tree.topLevelItem(i)
        item_text = item.text(0)
        # Check "Documents" and "Downloads" by default
        if item_text in ["Documents", "Downloads"]:
            item.setCheckState(0, 2)  # Qt.CheckState.Checked = 2

    window.show()

    sys.exit(app.exec())


def example_programmatic_search():
    """Example of programmatic search (for automation)"""
    app = QApplication(sys.argv)

    window = SmartSearchWindow()

    # Setup search parameters
    window.search_input.setText("example")
    window.case_sensitive_cb.setChecked(False)

    # Check specific directory
    tree = window.dir_tree
    for i in range(tree.topLevelItemCount()):
        item = tree.topLevelItem(i)
        if item.text(0) == "Documents":
            item.setCheckState(0, 2)
            break

    # Note: To start search programmatically after window is shown:
    # window.show()
    # QTimer.singleShot(500, window._start_search)

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    # Run basic example
    example_basic()

    # Uncomment to try other examples:
    # example_custom_start()
    # example_programmatic_search()
