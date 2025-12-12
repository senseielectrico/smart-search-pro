#!/usr/bin/env python
"""
Test export integration with UI
"""

import sys
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import QApplication

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ui.main_window import MainWindow


def generate_test_data(count=100):
    """Generate test search results data"""
    import random

    extensions = ['.txt', '.pdf', '.docx', '.xlsx', '.jpg', '.png', '.mp4', '.zip']
    folders = ['Documents', 'Downloads', 'Pictures', 'Videos', 'Projects']

    results = []
    base_path = Path.home()

    for i in range(count):
        ext = random.choice(extensions)
        folder = random.choice(folders)
        filename = f"file_{i:04d}{ext}"
        file_path = base_path / folder / filename

        result = {
            'name': filename,
            'filename': filename,
            'path': str(file_path.parent),
            'full_path': str(file_path),
            'extension': ext,
            'size': random.randint(1024, 10 * 1024 * 1024),
            'date_modified': datetime.now().timestamp() - random.randint(0, 365*24*3600),
            'date_created': datetime.now().timestamp() - random.randint(365*24*3600, 2*365*24*3600),
            'is_folder': False
        }
        results.append(result)

    return results


def main():
    """Main test function"""
    app = QApplication(sys.argv)

    # Create main window
    window = MainWindow()

    # Generate and load test data
    print("Generating test data...")
    test_results = generate_test_data(500)

    # Populate results panel
    print(f"Loading {len(test_results)} test results...")
    window.results_panel.set_results(test_results)

    print("\nExport Integration Test")
    print("=" * 50)
    print(f"✓ Loaded {len(test_results)} test results")
    print("\nTest the following:")
    print("  1. File > Export > Export All Results (Ctrl+E)")
    print("  2. File > Export > Export Selected (Ctrl+Shift+E)")
    print("  3. File > Export > Quick Export to CSV")
    print("  4. File > Export > Copy to Clipboard (Ctrl+Shift+C)")
    print("  5. Toolbar: 💾 Export button")
    print("  6. Toolbar: 📄 Copy to clipboard button")
    print("  7. Right-click context menu > Export options")
    print("\nExport Formats Available:")
    print("  • CSV - Comma-separated values")
    print("  • Excel - XLSX with formatting and summary")
    print("  • HTML - Interactive report with search/sort")
    print("  • JSON - Structured data")
    print("  • Clipboard - Quick copy")
    print("=" * 50)

    # Show window
    window.show()

    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
