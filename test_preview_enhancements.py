#!/usr/bin/env python3
"""
Test Preview Enhancements
Tests all new preview features
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from ui.preview_panel_enhanced import EnhancedPreviewPanel
from preview.text_preview import TextPreviewer
from preview.image_preview import ImagePreviewer
from preview.document_preview import DocumentPreviewer


class PreviewTestWindow(QMainWindow):
    """Test window for preview enhancements"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Preview Enhancements Test")
        self.setGeometry(100, 100, 1200, 800)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Test buttons
        button_row = QHBoxLayout()

        test_text_btn = QPushButton("Test Text Preview (Python)")
        test_text_btn.clicked.connect(self.test_text_preview)
        button_row.addWidget(test_text_btn)

        test_json_btn = QPushButton("Test JSON Preview")
        test_json_btn.clicked.connect(self.test_json_preview)
        button_row.addWidget(test_json_btn)

        test_md_btn = QPushButton("Test Markdown Preview")
        test_md_btn.clicked.connect(self.test_markdown_preview)
        button_row.addWidget(test_md_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_preview)
        button_row.addWidget(clear_btn)

        layout.addLayout(button_row)

        # Preview panel
        self.preview_panel = EnhancedPreviewPanel()
        self.preview_panel.open_requested.connect(self.on_open_file)
        layout.addWidget(self.preview_panel)

        # Status
        self.print_capabilities()

    def print_capabilities(self):
        """Print available preview capabilities"""
        print("\n=== Preview Capabilities ===")

        text_prev = TextPreviewer()
        print(f"Pygments available: {text_prev._pygments_available}")
        print(f"Markdown available: {text_prev._markdown_available}")
        print(f"Supported languages: {len(text_prev.LANGUAGE_MAP)}")

        img_prev = ImagePreviewer()
        print(f"Pillow available: {img_prev._pillow_available}")
        print(f"EXIF support: {img_prev._exif_available}")

        doc_prev = DocumentPreviewer()
        print(f"PDF support: {doc_prev._pypdf_available}")
        print(f"PDF rendering: {doc_prev._pdf2image_available}")

        print("=" * 30 + "\n")

    def test_text_preview(self):
        """Test text preview with syntax highlighting"""
        # Create test Python file
        test_file = Path(__file__).parent / "test_preview_sample.py"
        content = '''#!/usr/bin/env python3
"""
Sample Python file for testing syntax highlighting
"""

import os
import sys
from typing import Optional, List, Dict

class SampleClass:
    """Sample class for testing"""

    def __init__(self, name: str):
        self.name = name
        self.counter = 0

    def increment(self) -> int:
        """Increment counter"""
        self.counter += 1
        return self.counter

    def process_data(self, data: List[Dict[str, str]]) -> Optional[str]:
        """Process data and return result"""
        if not data:
            return None

        results = []
        for item in data:
            if 'name' in item:
                results.append(f"Hello, {item['name']}!")

        return "\\n".join(results)


def main():
    """Main function"""
    obj = SampleClass("Test")
    print(f"Counter: {obj.increment()}")

    data = [
        {"name": "Alice"},
        {"name": "Bob"},
        {"name": "Charlie"}
    ]

    result = obj.process_data(data)
    print(result)


if __name__ == "__main__":
    main()
'''
        test_file.write_text(content, encoding='utf-8')
        self.preview_panel.set_file(str(test_file))
        print(f"Testing text preview: {test_file}")

    def test_json_preview(self):
        """Test JSON preview with formatting"""
        test_file = Path(__file__).parent / "test_preview_sample.json"
        content = '''{
"name": "Smart Search Pro",
"version": "2.0.0",
"features": [
"Instant search with Everything SDK",
"Advanced filters",
"Duplicate detection",
"Export to multiple formats",
"Enhanced preview with 40+ languages"
],
"config": {
"cache_size": 100,
"max_results": 10000,
"themes": ["light", "dark", "auto"]
},
"metadata": {
"author": "Development Team",
"license": "MIT",
"created": "2024-12-12"
}
}'''
        test_file.write_text(content, encoding='utf-8')
        self.preview_panel.set_file(str(test_file))
        print(f"Testing JSON preview: {test_file}")

    def test_markdown_preview(self):
        """Test Markdown preview with rendering"""
        test_file = Path(__file__).parent / "test_preview_sample.md"
        content = '''# Preview Enhancements

## New Features

This document demonstrates the **enhanced preview** capabilities.

### Syntax Highlighting

Support for **40+ programming languages**:

- Python, JavaScript, TypeScript
- C, C++, C#, Java
- Go, Rust, Swift, Kotlin
- Ruby, PHP, Perl, Lua
- And many more...

### Code Block Example

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("World"))
```

### Table Example

| Feature | Status | Notes |
|---------|--------|-------|
| Line numbers | ✅ | Toggle on/off |
| Word wrap | ✅ | Toggle on/off |
| Find in preview | ✅ | Ctrl+F |
| Image zoom | ✅ | 10% - 400% |
| EXIF metadata | ✅ | For photos |
| PDF multi-page | ✅ | Scrollable |

### Image Features

- Zoom controls (10% - 400%)
- Fit to view
- Rotation (90°, 180°, 270°)
- EXIF metadata display
- Thumbnail caching

### Text Features

- Syntax highlighting for 40+ languages
- Line numbers (toggleable)
- Word wrap (toggleable)
- Find in preview (Ctrl+F)
- JSON formatting
- Markdown rendering

### Performance

- **Lazy loading**: Preview loaded in background thread
- **Animated placeholder**: Shows while loading
- **Thumbnail cache**: Disk cache for images
- **Memory efficient**: Large files handled gracefully

> Preview system is optimized for speed and handles large files without lag.

### Links

- [GitHub](https://github.com)
- [Documentation](https://docs.example.com)

---

*Generated for testing preview enhancements*
'''
        test_file.write_text(content, encoding='utf-8')
        self.preview_panel.set_file(str(test_file))
        print(f"Testing Markdown preview: {test_file}")

    def clear_preview(self):
        """Clear preview"""
        self.preview_panel.clear()
        print("Preview cleared")

    def on_open_file(self, file_path: str):
        """Handle open file request"""
        print(f"Open requested: {file_path}")
        os.startfile(file_path)

    def closeEvent(self, event):
        """Cleanup on close"""
        self.preview_panel.cleanup()
        event.accept()


def main():
    """Run test application"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = PreviewTestWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
