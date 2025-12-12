"""
Test/Demo for Batch Rename Dialog UI
"""

import sys
import os
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt

from ui.batch_rename_dialog import BatchRenameDialog


class TestWindow(QWidget):
    """Test window for batch rename dialog"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Batch Rename Dialog - Test")
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Batch Rename Dialog Test")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Info
        info = QLabel(
            "This test creates temporary files and opens the batch rename dialog.\n\n"
            "Features to test:\n"
            "• Drag & drop files into dialog\n"
            "• Pattern-based renaming\n"
            "• Find & replace\n"
            "• Case conversion\n"
            "• Preview with conflict detection\n"
            "• Apply rename\n"
            "• Undo capability"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addStretch()

        # Test buttons
        btn1 = QPushButton("Open with Sample Files")
        btn1.clicked.connect(self.open_with_samples)
        layout.addWidget(btn1)

        btn2 = QPushButton("Open Empty")
        btn2.clicked.connect(self.open_empty)
        layout.addWidget(btn2)

        # Temp directory for test files
        self.tmpdir = None

    def create_sample_files(self) -> list:
        """Create sample files for testing"""
        if self.tmpdir:
            self.tmpdir.cleanup()

        self.tmpdir = tempfile.TemporaryDirectory()
        tmppath = Path(self.tmpdir.name)

        # Create various test files
        samples = [
            "Document 1.pdf",
            "Document 2.pdf",
            "Photo_IMG_001.jpg",
            "Photo_IMG_002.jpg",
            "Photo_IMG_003.jpg",
            "video_clip_01.mp4",
            "video_clip_02.mp4",
            "UPPERCASE_FILE.TXT",
            "lowercase_file.txt",
            "Mixed-Case-File.dat",
            "file with spaces.doc",
            "file_with_underscores.xls",
            "File!!!Special###Chars.txt",
        ]

        files = []
        for name in samples:
            file = tmppath / name
            file.write_text(f"Sample content for {name}")
            files.append(str(file))

        print(f"Created {len(files)} sample files in {tmppath}")
        return files

    def open_with_samples(self):
        """Open dialog with sample files"""
        files = self.create_sample_files()

        dialog = BatchRenameDialog(initial_files=files, parent=self)
        dialog.files_renamed.connect(self.on_files_renamed)

        result = dialog.exec()
        if result:
            print("Dialog accepted")
        else:
            print("Dialog rejected")

    def open_empty(self):
        """Open empty dialog"""
        dialog = BatchRenameDialog(parent=self)
        dialog.files_renamed.connect(self.on_files_renamed)

        result = dialog.exec()
        if result:
            print("Dialog accepted")
        else:
            print("Dialog rejected")

    def on_files_renamed(self, count: int):
        """Handle files renamed signal"""
        print(f"✓ {count} files renamed successfully")

    def closeEvent(self, event):
        """Clean up on close"""
        if self.tmpdir:
            self.tmpdir.cleanup()
        event.accept()


def main():
    """Run test application"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    window = TestWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
