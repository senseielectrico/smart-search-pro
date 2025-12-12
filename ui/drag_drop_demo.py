"""
Drag & Drop Demo for Smart Search Pro
Demonstrates all drag & drop features in a standalone window.
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QSplitter
)
from PyQt6.QtCore import Qt

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.results_panel import ResultsPanel
from ui.operations_panel import OperationsPanel
from ui.directory_tree import DirectoryTree
from datetime import datetime


class DragDropDemo(QMainWindow):
    """Demo window showing all drag & drop features"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Search Pro - Drag & Drop Demo")
        self.setMinimumSize(1400, 800)

        self._init_ui()
        self._add_sample_data()
        self._connect_signals()

    def _init_ui(self):
        """Initialize UI"""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Title and instructions
        title = QLabel("🎯 Drag & Drop Feature Demo")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px;")
        main_layout.addWidget(title)

        instructions = QLabel(
            "Try these features:\n"
            "1. DRAG files FROM Results Panel → Drop to Windows Explorer or Operations Panel\n"
            "2. DROP files TO Operations Panel → Context menu appears (Copy/Move)\n"
            "3. DROP folders TO Directory Tree → Adds to search paths\n"
            "4. Use Ctrl=Copy, Shift=Move while dragging\n"
            "5. Multi-select files and drag them together"
        )
        instructions.setStyleSheet("""
            QLabel {
                background-color: #F0F8FF;
                border: 1px solid #0078D4;
                border-radius: 6px;
                padding: 12px;
                font-size: 13px;
            }
        """)
        main_layout.addWidget(instructions)

        # Main content - 3 column layout
        content_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Directory Tree
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        dir_label = QLabel("📁 Directory Tree (Drop Zone)")
        dir_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 8px;")
        left_layout.addWidget(dir_label)

        self.directory_tree = DirectoryTree()
        left_layout.addWidget(self.directory_tree)

        drop_hint1 = QLabel("💡 Drop folders here to add to search")
        drop_hint1.setStyleSheet("color: #605E5C; font-size: 11px; padding: 4px;")
        left_layout.addWidget(drop_hint1)

        content_splitter.addWidget(left_panel)

        # Center: Results Panel
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)

        results_label = QLabel("📊 Search Results (Drag Source)")
        results_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 8px;")
        center_layout.addWidget(results_label)

        self.results_panel = ResultsPanel()
        center_layout.addWidget(self.results_panel)

        drag_hint = QLabel("💡 Select files and drag to Explorer or Operations panel")
        drag_hint.setStyleSheet("color: #605E5C; font-size: 11px; padding: 4px;")
        center_layout.addWidget(drag_hint)

        content_splitter.addWidget(center_panel)

        # Right: Operations Panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        ops_label = QLabel("⚙ Operations Panel (Drop Zone)")
        ops_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 8px;")
        right_layout.addWidget(ops_label)

        self.operations_panel = OperationsPanel()
        right_layout.addWidget(self.operations_panel)

        drop_hint2 = QLabel("💡 Drop files here, set destination, then copy/move")
        drop_hint2.setStyleSheet("color: #605E5C; font-size: 11px; padding: 4px;")
        right_layout.addWidget(drop_hint2)

        content_splitter.addWidget(right_panel)

        # Set splitter proportions
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 2)
        content_splitter.setStretchFactor(2, 1)

        main_layout.addWidget(content_splitter)

        # Event log at bottom
        log_label = QLabel("📋 Event Log")
        log_label.setStyleSheet("font-weight: bold; font-size: 12px; padding: 8px;")
        main_layout.addWidget(log_label)

        self.event_log = QTextEdit()
        self.event_log.setReadOnly(True)
        self.event_log.setMaximumHeight(150)
        self.event_log.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #3C3C3C;
                border-radius: 4px;
            }
        """)
        main_layout.addWidget(self.event_log)

        # Control buttons
        button_layout = QHBoxLayout()

        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.event_log.clear)
        button_layout.addWidget(clear_log_btn)

        add_sample_btn = QPushButton("Add More Sample Files")
        add_sample_btn.clicked.connect(self._add_sample_data)
        button_layout.addWidget(add_sample_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close Demo")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        main_layout.addLayout(button_layout)

        # Log welcome message
        self._log("Demo started. Try dragging and dropping!")

    def _add_sample_data(self):
        """Add sample data to results panel"""
        import random

        # Sample file data
        sample_files = [
            {"name": "document.pdf", "path": str(Path.home() / "Documents" / "document.pdf"),
             "size": 1024 * 512, "modified": datetime.now()},
            {"name": "image.jpg", "path": str(Path.home() / "Pictures" / "image.jpg"),
             "size": 1024 * 256, "modified": datetime.now()},
            {"name": "video.mp4", "path": str(Path.home() / "Videos" / "video.mp4"),
             "size": 1024 * 1024 * 50, "modified": datetime.now()},
            {"name": "report.docx", "path": str(Path.home() / "Documents" / "report.docx"),
             "size": 1024 * 128, "modified": datetime.now()},
            {"name": "presentation.pptx", "path": str(Path.home() / "Documents" / "presentation.pptx"),
             "size": 1024 * 1024 * 5, "modified": datetime.now()},
            {"name": "spreadsheet.xlsx", "path": str(Path.home() / "Documents" / "spreadsheet.xlsx"),
             "size": 1024 * 256, "modified": datetime.now()},
            {"name": "music.mp3", "path": str(Path.home() / "Music" / "music.mp3"),
             "size": 1024 * 1024 * 4, "modified": datetime.now()},
            {"name": "photo.png", "path": str(Path.home() / "Pictures" / "photo.png"),
             "size": 1024 * 512, "modified": datetime.now()},
        ]

        # Randomize some properties
        for file in sample_files:
            file["size"] = file["size"] + random.randint(-50000, 50000)

        self.results_panel.add_results(sample_files)
        self._log(f"Added {len(sample_files)} sample files to Results Panel")

    def _connect_signals(self):
        """Connect signals for event logging"""
        # Results panel drag events
        self.results_panel.drag_handler.drag_started.connect(
            lambda files: self._log(f"DRAG START: {len(files)} file(s) from Results Panel")
        )
        self.results_panel.drag_handler.drag_completed.connect(
            lambda op: self._log(f"DRAG COMPLETE: Operation = {op.upper()}")
        )

        # Operations panel drop events
        self.operations_panel.drag_handler.files_dropped.connect(
            lambda files, zone: self._log(
                f"DROP: {len(files)} file(s) dropped to {zone}"
            )
        )

        # Directory tree drop events
        self.directory_tree.files_dropped_to_search.connect(
            lambda folders: self._log(
                f"DROP: {len(folders)} folder(s) added to Directory Tree search paths"
            )
        )

        # File selection
        self.results_panel.files_selected.connect(
            lambda files: self._log(f"SELECTION: {len(files)} file(s) selected")
        )

    def _log(self, message: str):
        """Add message to event log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.event_log.append(f"[{timestamp}] {message}")
        # Scroll to bottom
        self.event_log.verticalScrollBar().setValue(
            self.event_log.verticalScrollBar().maximum()
        )


def main():
    """Run the demo"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    # Create and show demo window
    demo = DragDropDemo()
    demo.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
