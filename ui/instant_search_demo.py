#!/usr/bin/env python3
"""
Instant Search Demo - Standalone demo of instant search functionality

This demo shows the instant search feature working independently.
Run this file to test the instant search without the full application.

Usage:
    python instant_search_demo.py
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit
from PyQt6.QtCore import QTimer, pyqtSlot

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.search_panel import SearchPanel


class InstantSearchDemo(QMainWindow):
    """Demo window for instant search"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Instant Search Demo - Smart Search Pro")
        self.setGeometry(100, 100, 800, 600)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Search panel
        self.search_panel = SearchPanel()
        layout.addWidget(self.search_panel)

        # Output area
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        # Connect signals
        self.search_panel.instant_search_requested.connect(self._on_instant_search)
        self.search_panel.search_requested.connect(self._on_explicit_search)
        self.search_panel.filter_changed.connect(self._on_filter_changed)

        # Demo info
        self._show_info()

    def _show_info(self):
        """Show demo information"""
        info = """
=== Instant Search Demo ===

Features demonstrated:
1. Type in the search box - search triggers after 200ms of no typing
2. "⏳ Searching..." indicator appears while searching
3. Press Enter to trigger explicit search
4. Use quick filter buttons to add filters
5. Click "Advanced" for advanced search options

Try it:
- Type slowly: Each pause triggers a search
- Type fast: Only final query is searched
- Keep typing: Previous searches are cancelled
- Press Enter: Immediate explicit search

The demo logs all search requests below.
---
"""
        self.output.setText(info)

    @pyqtSlot(dict)
    def _on_instant_search(self, params):
        """Handle instant search request"""
        query = params.get('query', '')
        self._log_search("INSTANT SEARCH", query, params)

        # Simulate search completion after delay
        QTimer.singleShot(100, self.search_panel.set_search_complete)

    @pyqtSlot(dict)
    def _on_explicit_search(self, params):
        """Handle explicit search request"""
        query = params.get('query', '')
        self._log_search("EXPLICIT SEARCH", query, params)

        # Simulate search completion after delay
        QTimer.singleShot(100, self.search_panel.set_search_complete)

    @pyqtSlot(dict)
    def _on_filter_changed(self, filters):
        """Handle filter change"""
        self._log(f"FILTER CHANGED: {filters}")

    def _log_search(self, search_type: str, query: str, params: dict):
        """Log search request"""
        import time
        timestamp = time.strftime("%H:%M:%S")

        log_entry = f"[{timestamp}] {search_type}\n"
        log_entry += f"  Query: '{query}'\n"

        if params.get('instant'):
            log_entry += f"  Mode: Instant (debounced)\n"
        else:
            log_entry += f"  Mode: Explicit (Enter/Button)\n"

        # Show active filters
        filters = {k: v for k, v in params.items()
                  if k not in ['query', 'instant', 'paths']}
        if filters:
            log_entry += f"  Filters: {filters}\n"

        log_entry += "\n"

        self._log(log_entry)

    def _log(self, message: str):
        """Add message to output"""
        self.output.append(message)
        # Auto-scroll to bottom
        scrollbar = self.output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


def main():
    """Run demo application"""
    app = QApplication(sys.argv)

    # Apply basic styling
    app.setStyle('Fusion')

    demo = InstantSearchDemo()
    demo.show()

    print("Instant Search Demo Running")
    print("=" * 40)
    print("Features:")
    print("  - 200ms debounce delay")
    print("  - Automatic search on typing")
    print("  - Visual 'Searching...' indicator")
    print("  - Enter key for explicit search")
    print("  - Previous searches cancelled")
    print("=" * 40)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
