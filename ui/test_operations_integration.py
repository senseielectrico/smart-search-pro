#!/usr/bin/env python3
"""
Test script for Operations Panel integration with backend.
Demonstrates all features: drag & drop, copy, move, pause, resume, cancel.
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget
from PyQt6.QtCore import Qt

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.operations_panel import OperationsPanel
from ui.themes import ThemeManager
from operations.manager import OperationsManager


class OperationsTestWindow(QMainWindow):
    """Test window for operations panel"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Search Pro - Operations Panel Test")
        self.setMinimumSize(900, 600)

        # Create operations manager
        history_file = Path.home() / ".smart_search_test" / "operations_history.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)

        self.operations_manager = OperationsManager(
            max_concurrent_operations=2,
            history_file=str(history_file),
            auto_save_history=True
        )

        # Apply theme
        theme_manager = ThemeManager()
        theme_manager.apply_theme(self, "light")

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)

        # Create tabs
        tabs = QTabWidget()

        # Operations panel
        self.operations_panel = OperationsPanel(
            parent=self,
            operations_manager=self.operations_manager
        )
        tabs.addTab(self.operations_panel, "File Operations")

        # Info tab
        info_widget = self._create_info_widget()
        tabs.addTab(info_widget, "How to Use")

        layout.addWidget(tabs)

        print("Operations Panel Test Window initialized")
        print(f"History file: {history_file}")
        print("\nFeatures to test:")
        print("1. Drag & drop files into the operations panel")
        print("2. Use 'Select Files' and 'Select Destination' buttons")
        print("3. Click 'Copy' or 'Move' to start operation")
        print("4. Watch real-time progress with speed graph")
        print("5. Test Pause/Resume/Cancel buttons")
        print("6. Clear completed operations")

    def _create_info_widget(self) -> QWidget:
        """Create info widget with instructions"""
        from PyQt6.QtWidgets import QTextEdit

        widget = QWidget()
        layout = QVBoxLayout(widget)

        info = QTextEdit()
        info.setReadOnly(True)
        info.setHtml("""
        <h2>Operations Panel - Integration Test</h2>

        <h3>Features Implemented:</h3>
        <ul>
            <li><b>Drag & Drop:</b> Drag files from Explorer into the panel</li>
            <li><b>File Selection:</b> Use buttons to select files and destination</li>
            <li><b>Copy Operations:</b> Copy files with hash verification</li>
            <li><b>Move Operations:</b> Move files (instant rename on same volume)</li>
            <li><b>Real-time Progress:</b> Live progress bars and speed graphs</li>
            <li><b>Pause/Resume:</b> Pause and resume operations</li>
            <li><b>Cancel:</b> Cancel operations with confirmation</li>
            <li><b>Speed Tracking:</b> Real-time speed calculation and ETA</li>
            <li><b>Hash Verification:</b> Automatic verification after copy</li>
            <li><b>Operation History:</b> Persistent history saved to disk</li>
        </ul>

        <h3>How to Test:</h3>
        <ol>
            <li>Go to the "File Operations" tab</li>
            <li>Drag some files from Windows Explorer into the panel</li>
            <li>Click "Select Destination" to choose where to copy/move</li>
            <li>Click "Copy" or "Move" to start the operation</li>
            <li>Watch the real-time progress bar and speed graph</li>
            <li>Try pausing and resuming with the pause button</li>
            <li>Test cancellation (will ask for confirmation)</li>
            <li>Click "Clear Completed" to remove finished operations</li>
        </ol>

        <h3>Backend Integration:</h3>
        <ul>
            <li><b>OperationsManager:</b> Manages operation queue and workers</li>
            <li><b>FileCopier:</b> Multi-threaded copying with adaptive buffers</li>
            <li><b>FileMover:</b> Optimized moving (rename or copy+delete)</li>
            <li><b>FileVerifier:</b> Hash verification (MD5/SHA256/CRC32)</li>
            <li><b>ProgressTracker:</b> Real-time progress with speed calculation</li>
        </ul>

        <h3>Performance Features:</h3>
        <ul>
            <li>Adaptive buffer sizing (4KB to 128MB)</li>
            <li>Multi-threaded operations (configurable workers)</li>
            <li>Same-volume optimization (instant rename)</li>
            <li>Windows CopyFileEx API when available</li>
            <li>Rolling average for speed calculation</li>
            <li>Automatic retry on failure (3 attempts)</li>
        </ul>

        <h3>UI Features:</h3>
        <ul>
            <li>Progress cards with shadow effects</li>
            <li>Real-time speed graph</li>
            <li>Drag & drop visual feedback</li>
            <li>Empty state placeholder</li>
            <li>Status indicators and ETA</li>
            <li>File count and size display</li>
        </ul>
        """)

        layout.addWidget(info)
        return widget

    def closeEvent(self, event):
        """Handle close event"""
        # Shutdown operations panel (will check for active operations)
        self.operations_panel.closeEvent(event)
        if event.isAccepted():
            # Cleanup operations manager
            self.operations_manager.shutdown()
            super().closeEvent(event)


def main():
    """Run the test application"""
    app = QApplication(sys.argv)
    app.setApplicationName("Smart Search Pro - Operations Test")
    app.setOrganizationName("SmartSearch")

    # Create and show window
    window = OperationsTestWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
