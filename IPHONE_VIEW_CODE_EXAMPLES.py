"""
iPhone View - Code Examples
Complete code snippets for common use cases
"""

# ============================================================================
# EXAMPLE 1: Basic Usage - Minimal Setup
# ============================================================================

def example_1_basic_usage():
    """Minimal code to show iPhone view"""
    from PyQt6.QtWidgets import QApplication
    from views.iphone_view import iPhoneFileView
    import sys
    import os

    app = QApplication(sys.argv)

    # Create and show view
    view = iPhoneFileView()
    view.resize(1200, 800)

    # Set path
    docs = os.path.join(os.environ['USERPROFILE'], 'Documents')
    view.set_path(docs)

    view.show()
    sys.exit(app.exec())


# ============================================================================
# EXAMPLE 2: Integration with Main Window
# ============================================================================

def example_2_main_window_integration():
    """Integrate iPhone view into QMainWindow with tabs"""
    from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
    from views.iphone_view import iPhoneFileView
    import sys

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("My App with iPhone View")
            self.resize(1400, 900)

            # Create tabs
            tabs = QTabWidget()
            self.setCentralWidget(tabs)

            # Add iPhone view
            self.iphone_view = iPhoneFileView()
            tabs.addTab(self.iphone_view, "Browse Files")

            # Connect signals
            self.iphone_view.category_selected.connect(self.on_category_selected)
            self.iphone_view.file_opened.connect(self.on_file_opened)

        def on_category_selected(self, category):
            print(f"Category: {category.value}")

        def on_file_opened(self, path):
            print(f"Opened: {path}")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


# ============================================================================
# EXAMPLE 3: Custom Scanning with Parameters
# ============================================================================

def example_3_custom_scanning():
    """Custom directory scanning with various options"""
    from views.category_scanner import CategoryScanner
    from categories import FileCategory

    scanner = CategoryScanner(cache_enabled=True)

    # Scan with custom parameters
    categories = scanner.scan_directory(
        path='C:/Users/Public',
        max_depth=3,              # Limit recursion depth
        include_hidden=False,      # Skip hidden files
        follow_symlinks=False      # Don't follow symlinks
    )

    # Get breakdown
    breakdown = scanner.get_category_breakdown(categories)

    print(f"Total Files: {breakdown['total_files']}")
    print(f"Total Size: {breakdown['formatted_size']}")
    print("\nCategories:")

    for cat_name, stats in breakdown['categories'].items():
        print(f"  {cat_name:15} {stats['count']:6} files  "
              f"{stats['formatted_size']:>10}  ({stats['percentage']:.1f}%)")

    # Get specific category data
    images = categories[FileCategory.IMAGENES]
    print(f"\nImages: {images.file_count} files")

    # Iterate through image files
    for file_info in images.files[:5]:  # First 5
        print(f"  - {file_info['name']} ({file_info['size']} bytes)")


# ============================================================================
# EXAMPLE 4: Background Scanning (Non-Blocking)
# ============================================================================

def example_4_background_scanning():
    """Perform scanning in background thread"""
    from views.category_scanner import CategoryScanner, BackgroundScanner
    from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
    from PyQt6.QtCore import QTimer
    import sys

    class ScanWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Background Scanning Example")

            central = QWidget()
            layout = QVBoxLayout(central)
            self.setCentralWidget(central)

            self.status_label = QLabel("Starting scan...")
            layout.addWidget(self.status_label)

            # Start background scan
            self.scanner = CategoryScanner()
            self.bg_scanner = BackgroundScanner(
                scanner=self.scanner,
                path='C:/Users',
                callback=self.on_scan_complete
            )
            self.bg_scanner.start()

        def on_scan_complete(self, categories):
            # This runs when scan is done
            breakdown = self.scanner.get_category_breakdown(categories)
            self.status_label.setText(
                f"Scan complete!\n"
                f"Total Files: {breakdown['total_files']}\n"
                f"Total Size: {breakdown['formatted_size']}"
            )

    app = QApplication(sys.argv)
    window = ScanWindow()
    window.show()
    sys.exit(app.exec())


# ============================================================================
# EXAMPLE 5: Search and Filter
# ============================================================================

def example_5_search_and_filter():
    """Search for files within categories"""
    from views.iphone_view import iPhoneFileView
    from categories import FileCategory

    view = iPhoneFileView()

    # Set path and wait for scan
    import os
    view.set_path(os.path.join(os.environ['USERPROFILE'], 'Documents'))

    # Search in specific category
    results = view.search_in_category(
        category=FileCategory.IMAGENES,
        query="vacation"
    )

    print(f"Found {len(results)} images matching 'vacation':")
    for file_info in results:
        print(f"  - {file_info['name']}")

    # Get recent files across all categories
    recent = view.get_recent_files(limit=10)

    print(f"\n{len(recent)} most recent files:")
    from datetime import datetime
    for file_info in recent:
        dt = datetime.fromtimestamp(file_info['modified'])
        print(f"  - {file_info['name']} ({dt.strftime('%Y-%m-%d %H:%M')})")


# ============================================================================
# EXAMPLE 6: Custom Category Colors and Icons
# ============================================================================

def example_6_customize_appearance():
    """Customize category colors and icons"""
    from ui.iphone_widgets import CategoryIconWidget
    from PyQt6.QtGui import QColor
    from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout
    import sys

    # Modify colors (do this before creating widgets)
    CategoryIconWidget.CATEGORY_COLORS['Photos'] = QColor(255, 0, 100)  # Custom pink
    CategoryIconWidget.CATEGORY_ICONS['Photos'] = '📷'  # Camera icon

    # Create application
    app = QApplication(sys.argv)

    # Create window with custom icons
    window = QWidget()
    layout = QHBoxLayout(window)

    # Add category icons
    categories = ['Photos', 'Videos', 'Music', 'Documents']
    for category in categories:
        icon = CategoryIconWidget(category, size=80)
        layout.addWidget(icon)

    window.show()
    sys.exit(app.exec())


# ============================================================================
# EXAMPLE 7: Theme Switching
# ============================================================================

def example_7_theme_switching():
    """Switch between light and dark themes"""
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
    from views.iphone_view import iPhoneFileView
    from ui.themes import get_theme_manager, Theme
    import sys

    class ThemedWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.theme_manager = get_theme_manager()

            # Create layout
            central = QWidget()
            layout = QVBoxLayout(central)
            self.setCentralWidget(central)

            # Theme toggle button
            self.theme_btn = QPushButton("Switch to Dark Theme")
            self.theme_btn.clicked.connect(self.toggle_theme)
            layout.addWidget(self.theme_btn)

            # iPhone view
            self.view = iPhoneFileView()
            layout.addWidget(self.view)

        def toggle_theme(self):
            current = self.theme_manager.current_theme

            if current == Theme.LIGHT:
                self.theme_manager.set_theme(Theme.DARK)
                self.theme_btn.setText("Switch to Light Theme")
            else:
                self.theme_manager.set_theme(Theme.LIGHT)
                self.theme_btn.setText("Switch to Dark Theme")

            # Apply theme
            app = QApplication.instance()
            app.setStyleSheet(self.theme_manager.get_stylesheet())

    app = QApplication(sys.argv)
    window = ThemedWindow()
    window.show()
    sys.exit(app.exec())


# ============================================================================
# EXAMPLE 8: Statistics and Analytics
# ============================================================================

def example_8_statistics():
    """Get detailed statistics about files"""
    from views.category_scanner import CategoryScanner
    from categories import FileCategory
    import os

    scanner = CategoryScanner()

    # Scan directory
    path = os.path.join(os.environ['USERPROFILE'], 'Documents')
    categories = scanner.scan_directory(path, max_depth=2)

    # Get comprehensive breakdown
    breakdown = scanner.get_category_breakdown(categories)

    print("=== File Statistics ===\n")
    print(f"Total Files: {breakdown['total_files']}")
    print(f"Total Size: {breakdown['formatted_size']}")
    print("\nCategory Breakdown:")

    for cat_name, stats in breakdown['categories'].items():
        print(f"\n{cat_name}:")
        print(f"  Count: {stats['count']}")
        print(f"  Size: {stats['formatted_size']}")
        print(f"  Percentage: {stats['percentage']:.1f}%")
        print(f"  Average File Size: {stats['average_size']} bytes")

    # Get largest category
    if breakdown['categories']:
        largest = max(
            breakdown['categories'].items(),
            key=lambda x: x[1]['count']
        )
        print(f"\nLargest Category: {largest[0]} ({largest[1]['count']} files)")


# ============================================================================
# EXAMPLE 9: Custom Category Browser
# ============================================================================

def example_9_custom_browser():
    """Show category browser with custom data"""
    from PyQt6.QtWidgets import QApplication
    from ui.category_browser import CategoryBrowser
    from views.category_scanner import CategoryData
    from categories import FileCategory
    import sys

    # Create test data
    test_data = CategoryData(category=FileCategory.IMAGENES)

    # Add sample files
    for i in range(50):
        test_data.add_file({
            'name': f'photo_{i:03d}.jpg',
            'path': f'C:/Photos/photo_{i:03d}.jpg',
            'size': 1024 * 1024 * (i % 10 + 1),  # 1-10 MB
            'modified': 1700000000 + i * 3600,
            'accessed': 1700000000 + i * 3600,
            'created': 1700000000,
            'extension': '.jpg',
            'mime_type': 'image/jpeg',
        })

    # Show browser
    app = QApplication(sys.argv)
    browser = CategoryBrowser(FileCategory.IMAGENES, test_data)
    browser.exec()


# ============================================================================
# EXAMPLE 10: Complete Application with All Features
# ============================================================================

def example_10_complete_application():
    """Complete application with all iPhone view features"""
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QTabWidget,
        QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog
    )
    from views.iphone_view import iPhoneFileView
    from ui.themes import get_theme_manager, Theme
    from categories import FileCategory
    import sys
    import os

    class CompleteApp(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Complete iPhone View App")
            self.resize(1400, 900)

            self.theme_manager = get_theme_manager()

            # Create tabs
            tabs = QTabWidget()
            self.setCentralWidget(tabs)

            # Tab 1: iPhone View
            self.iphone_view = iPhoneFileView()
            tabs.addTab(self.iphone_view, "Browse Files")

            # Tab 2: Control Panel
            control_panel = self._create_control_panel()
            tabs.addTab(control_panel, "Controls")

            # Set default path
            default_path = os.path.join(os.environ['USERPROFILE'], 'Documents')
            self.iphone_view.set_path(default_path)

            # Connect signals
            self.iphone_view.category_selected.connect(self.on_category_selected)
            self.iphone_view.file_opened.connect(self.on_file_opened)
            self.iphone_view.path_changed.connect(self.on_path_changed)

            # Apply theme
            self._apply_theme()

        def _create_control_panel(self):
            panel = QWidget()
            layout = QVBoxLayout(panel)
            layout.setSpacing(10)
            layout.setContentsMargins(20, 20, 20, 20)

            # Title
            title = QLabel("Control Panel")
            title.setStyleSheet("font-size: 18pt; font-weight: bold;")
            layout.addWidget(title)

            # Browse button
            browse_btn = QPushButton("Browse Different Folder")
            browse_btn.clicked.connect(self.browse_folder)
            layout.addWidget(browse_btn)

            # Refresh button
            refresh_btn = QPushButton("Refresh Current View")
            refresh_btn.clicked.connect(self.refresh_view)
            layout.addWidget(refresh_btn)

            # Theme button
            self.theme_btn = QPushButton("Switch to Dark Theme")
            self.theme_btn.clicked.connect(self.toggle_theme)
            layout.addWidget(self.theme_btn)

            # Statistics display
            layout.addWidget(QLabel("Statistics:"))
            self.stats_label = QLabel("No data")
            self.stats_label.setStyleSheet("padding: 10px; background: palette(base);")
            layout.addWidget(self.stats_label)

            # Recent files button
            recent_btn = QPushButton("Show Recent Files")
            recent_btn.clicked.connect(self.show_recent)
            layout.addWidget(recent_btn)

            layout.addStretch()
            return panel

        def browse_folder(self):
            path = QFileDialog.getExistingDirectory(self, "Select Folder")
            if path:
                self.iphone_view.set_path(path)

        def refresh_view(self):
            self.iphone_view.refresh()
            self.update_stats()

        def toggle_theme(self):
            if self.theme_manager.current_theme == Theme.LIGHT:
                self.theme_manager.set_theme(Theme.DARK)
                self.theme_btn.setText("Switch to Light Theme")
            else:
                self.theme_manager.set_theme(Theme.LIGHT)
                self.theme_btn.setText("Switch to Dark Theme")
            self._apply_theme()

        def _apply_theme(self):
            app = QApplication.instance()
            app.setStyleSheet(self.theme_manager.get_stylesheet())

        def update_stats(self):
            stats = self.iphone_view.get_statistics()
            text = f"Total Files: {stats['total_files']}\n"
            text += f"Total Size: {stats['formatted_size']}\n\n"
            text += "Categories:\n"
            for cat, data in stats['categories'].items():
                text += f"  {cat}: {data['count']} files\n"
            self.stats_label.setText(text)

        def show_recent(self):
            recent = self.iphone_view.get_recent_files(10)
            print("\nRecent Files:")
            from datetime import datetime
            for f in recent:
                dt = datetime.fromtimestamp(f['modified'])
                print(f"  {f['name']} - {dt.strftime('%Y-%m-%d %H:%M')}")

        def on_category_selected(self, category):
            print(f"Selected: {category.value}")
            self.update_stats()

        def on_file_opened(self, path):
            print(f"Opened: {path}")

        def on_path_changed(self, path):
            print(f"Path changed to: {path}")
            self.update_stats()

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = CompleteApp()
    window.show()
    sys.exit(app.exec())


# ============================================================================
# Run Examples
# ============================================================================

if __name__ == '__main__':
    import sys

    print("iPhone View - Code Examples")
    print("=" * 60)
    print("\nAvailable examples:")
    print("1. Basic Usage")
    print("2. Main Window Integration")
    print("3. Custom Scanning")
    print("4. Background Scanning")
    print("5. Search and Filter")
    print("6. Customize Appearance")
    print("7. Theme Switching")
    print("8. Statistics")
    print("9. Custom Browser")
    print("10. Complete Application")
    print("\nUsage: python IPHONE_VIEW_CODE_EXAMPLES.py [example_number]")

    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        example_func = f"example_{example_num}_*"

        # Find and run example
        examples = {
            '1': example_1_basic_usage,
            '2': example_2_main_window_integration,
            '3': example_3_custom_scanning,
            '4': example_4_background_scanning,
            '5': example_5_search_and_filter,
            '6': example_6_customize_appearance,
            '7': example_7_theme_switching,
            '8': example_8_statistics,
            '9': example_9_custom_browser,
            '10': example_10_complete_application,
        }

        if example_num in examples:
            print(f"\nRunning Example {example_num}...")
            examples[example_num]()
        else:
            print(f"\nError: Example {example_num} not found")
    else:
        print("\nNo example specified. Running Example 10 (Complete Application)...")
        example_10_complete_application()
