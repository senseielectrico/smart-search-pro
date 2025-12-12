"""
Test script for advanced filters UI

Run this to test the filter integration without running the full app.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit
from PyQt6.QtCore import Qt
from ui.search_panel import SearchPanel
from ui.filter_integration import FilterIntegration


class FilterTestWindow(QMainWindow):
    """Test window for filter UI"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Search Pro - Filter Test")
        self.setMinimumSize(1000, 600)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setSpacing(12)

        # Search panel
        self.search_panel = SearchPanel()
        self.search_panel.search_requested.connect(self.on_search_requested)
        self.search_panel.filter_changed.connect(self.on_filter_changed)
        self.search_panel.instant_search_requested.connect(self.on_instant_search)
        layout.addWidget(self.search_panel)

        # Output display
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Search output will appear here...")
        layout.addWidget(self.output)

        self._log("Filter test window initialized")
        self._log("Try clicking filter chips and entering search queries")
        self._log("-" * 80)

    def on_search_requested(self, params: dict):
        """Handle search request"""
        self._log("\n=== SEARCH REQUESTED ===")
        self._log(f"Query: {params.get('query', '')}")
        self._log(f"Original Query: {params.get('original_query', '')}")
        self._log(f"Filters: {params.get('filters', {})}")
        self._log(f"Summary: {params.get('filter_summary', '')}")
        self._log("-" * 80)

    def on_filter_changed(self, filters: dict):
        """Handle filter change"""
        self._log("\n=== FILTERS CHANGED ===")
        self._log(f"Active Filters: {filters}")

        if filters:
            summary = FilterIntegration.get_filter_summary(filters)
            self._log(f"Summary: {summary}")

            # Show validation
            is_valid, error = FilterIntegration.validate_filters(filters)
            if is_valid:
                self._log("Validation: OK")
            else:
                self._log(f"Validation: FAILED - {error}")

            # Show query conversion
            test_query = "test"
            converted = FilterIntegration.ui_filters_to_query(test_query, filters)
            self._log(f"Query conversion: '{test_query}' -> '{converted}'")
        else:
            self._log("No filters active")

        self._log("-" * 80)

    def on_instant_search(self, params: dict):
        """Handle instant search"""
        self._log(f"\n[Instant Search] Query: {params.get('query', '')}")

    def _log(self, message: str):
        """Add message to output"""
        self.output.append(message)
        # Auto-scroll to bottom
        scrollbar = self.output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


def test_filter_integration():
    """Test FilterIntegration utility functions"""
    print("\n=== Testing FilterIntegration ===\n")

    # Test 1: UI filters to query
    print("Test 1: UI filters to query conversion")
    filters = {
        'size': '>1mb',
        'type': 'document',
        'modified': 'today'
    }
    query = FilterIntegration.ui_filters_to_query("invoice", filters)
    print(f"Filters: {filters}")
    print(f"Query: {query}")
    print()

    # Test 2: Filter validation
    print("Test 2: Filter validation")
    valid_filters = {
        'size': '>100mb',
        'type': 'video',
        'extensions': ['mp4', 'mkv']
    }
    is_valid, error = FilterIntegration.validate_filters(valid_filters)
    print(f"Valid filters: {valid_filters}")
    print(f"Is valid: {is_valid}, Error: {error}")
    print()

    invalid_filters = {
        'size': 'invalid_size',
        'type': 'unknown_type'
    }
    is_valid, error = FilterIntegration.validate_filters(invalid_filters)
    print(f"Invalid filters: {invalid_filters}")
    print(f"Is valid: {is_valid}, Error: {error}")
    print()

    # Test 3: Filter summary
    print("Test 3: Filter summary")
    filters = {
        'size': '>100mb',
        'type': 'video',
        'modified': 'thisweek',
        'extensions': ['mp4', 'mkv', 'avi']
    }
    summary = FilterIntegration.get_filter_summary(filters)
    print(f"Filters: {filters}")
    print(f"Summary: {summary}")
    print()

    # Test 4: Filter merging
    print("Test 4: Filter merging")
    filters1 = {'size': '>1mb', 'type': 'document'}
    filters2 = {'modified': 'today', 'extensions': ['pdf']}
    merged = FilterIntegration.merge_filters(filters1, filters2)
    print(f"Filters 1: {filters1}")
    print(f"Filters 2: {filters2}")
    print(f"Merged: {merged}")
    print()

    # Test 5: String to dict
    print("Test 5: Filter string to dict")
    filter_string = "size:>1mb type:document modified:today ext:pdf ext:doc"
    parsed = FilterIntegration.filter_to_dict(filter_string)
    print(f"String: {filter_string}")
    print(f"Parsed: {parsed}")
    print()

    print("=== FilterIntegration tests complete ===\n")


def main():
    """Main test function"""
    # Run unit tests first
    test_filter_integration()

    # Launch GUI test
    print("Launching GUI test window...")
    print("Try the following:")
    print("  1. Click different filter chips")
    print("  2. Enter text in search box")
    print("  3. Expand 'More Filters' panel")
    print("  4. Enter custom filters")
    print("  5. Click Search button")
    print("  6. Click Clear All button")
    print("\nClose the window to exit.\n")

    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    window = FilterTestWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
