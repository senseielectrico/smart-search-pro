# Archive Module Integration Guide

Complete guide for integrating the archive module into Smart Search Pro.

## Quick Start

### 1. Prerequisites Check

Ensure 7-Zip is installed:

```python
from archive.sevenzip_manager import SevenZipManager

try:
    manager = SevenZipManager()
    print(f"7-Zip found at: {manager.seven_zip_path}")
except FileNotFoundError:
    print("Please install 7-Zip from https://www.7-zip.org/")
```

### 2. Add Archive Tab to Main Window

```python
# In main_window.py

from ui.archive_panel import ArchivePanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... existing code ...

        # Add archive tab
        self.archive_panel = ArchivePanel(self)
        self.tab_widget.addTab(self.archive_panel, "Archives")

        # Connect signals
        self.archive_panel.archive_opened.connect(self._on_archive_opened)
        self.archive_panel.extraction_completed.connect(self._on_extraction_completed)

    def _on_archive_opened(self, archive_path: str):
        """Handle archive opened event"""
        self.statusBar().showMessage(f"Opened archive: {archive_path}")

    def _on_extraction_completed(self, destination: str):
        """Handle extraction completed event"""
        self.statusBar().showMessage(f"Extracted to: {destination}")
        # Optionally refresh file browser or search results
```

### 3. Add Archive Detection to Search Results

```python
# In results_panel.py

from archive.sevenzip_manager import SevenZipManager

class ResultsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.seven_zip = SevenZipManager()

    def _create_context_menu(self, position):
        """Create context menu for search results"""
        menu = QMenu()

        selected = self.table.selectedItems()
        if not selected:
            return

        file_path = self._get_selected_file_path()

        # Check if it's an archive
        if self.seven_zip.is_archive(file_path):
            # Add archive-specific actions
            menu.addAction("Open in Archive Manager", lambda: self._open_in_archive_manager(file_path))
            menu.addAction("Extract Here", lambda: self._extract_here(file_path))
            menu.addAction("Extract To...", lambda: self._extract_to(file_path))
            menu.addSeparator()

        # ... existing menu items ...

        menu.exec(self.table.viewport().mapToGlobal(position))

    def _open_in_archive_manager(self, file_path: str):
        """Open file in archive manager"""
        # Switch to archive tab and load archive
        main_window = self.window()
        main_window.tab_widget.setCurrentWidget(main_window.archive_panel)
        main_window.archive_panel.load_archive(file_path)

    def _extract_here(self, file_path: str):
        """Extract archive to same directory"""
        archive_dir = os.path.dirname(file_path)
        archive_name = Path(file_path).stem
        destination = os.path.join(archive_dir, archive_name)

        # Use extraction dialog
        from ui.extract_dialog import ExtractDialog

        dialog = ExtractDialog(file_path, self)
        dialog.dest_input.setText(destination)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            options = dialog.get_options()
            # Perform extraction...

    def _extract_to(self, file_path: str):
        """Extract archive with dialog"""
        from ui.extract_dialog import ExtractDialog

        dialog = ExtractDialog(file_path, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            options = dialog.get_options()
            # Perform extraction...
```

### 4. Add Archive Indicators to File Icons

```python
# In widgets.py or file_icon.py

class FileIcon(QLabel):
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

        # Check if archive
        from archive.sevenzip_manager import SevenZipManager
        seven_zip = SevenZipManager()

        if seven_zip.is_archive(file_path):
            # Use archive icon
            self.setPixmap(self._get_archive_icon())
            self.setToolTip("Archive file - Right-click for archive options")
        else:
            # Regular file icon
            self.setPixmap(self._get_file_icon())

    def _get_archive_icon(self):
        """Get archive icon based on format"""
        ext = Path(self.file_path).suffix.lower()

        icon_map = {
            '.7z': 'icon_7z.png',
            '.zip': 'icon_zip.png',
            '.rar': 'icon_rar.png',
            '.tar': 'icon_tar.png',
            '.gz': 'icon_gz.png',
            '.iso': 'icon_iso.png',
        }

        icon_file = icon_map.get(ext, 'icon_archive.png')
        # Load and return icon...
```

## Advanced Integration

### 5. Archive Preview in Preview Panel

```python
# In preview_panel.py

from archive.archive_analyzer import ArchiveAnalyzer

class PreviewPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.analyzer = ArchiveAnalyzer()

    def show_preview(self, file_path: str):
        """Show file preview"""
        if self.seven_zip.is_archive(file_path):
            # Show archive preview
            self._show_archive_preview(file_path)
        else:
            # Regular preview
            self._show_regular_preview(file_path)

    def _show_archive_preview(self, archive_path: str):
        """Show archive contents preview"""
        try:
            # Get text preview
            preview = self.analyzer.preview_as_text(archive_path, max_items=100)

            # Display in text widget
            self.preview_text.setPlainText(preview)

            # Show statistics
            stats = self.analyzer.analyze(archive_path)

            info_text = f"""
Archive Information:
- Files: {stats.total_files}
- Folders: {stats.total_folders}
- Size: {self._format_size(stats.total_size)}
- Compressed: {self._format_size(stats.packed_size)}
- Ratio: {stats.compression_ratio:.1f}%
- Encrypted: {'Yes' if stats.is_encrypted else 'No'}
            """

            self.info_label.setText(info_text)

        except Exception as e:
            self.preview_text.setPlainText(f"Error previewing archive: {str(e)}")
```

### 6. Batch Archive Operations

```python
# In operations_panel.py

from archive.sevenzip_manager import SevenZipManager, ArchiveFormat, CompressionLevel

class OperationsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.seven_zip = SevenZipManager()

    def add_batch_archive_operation(self):
        """Add batch archive creation to operations"""
        # Get selected files
        selected_files = self._get_selected_files()

        if not selected_files:
            return

        # Show archive creation dialog
        archive_name, ok = QInputDialog.getText(
            self,
            "Create Archive",
            "Archive name:"
        )

        if ok and archive_name:
            # Add to operations queue
            operation = {
                'type': 'create_archive',
                'files': selected_files,
                'archive_name': archive_name,
                'format': ArchiveFormat.SEVEN_ZIP,
                'compression': CompressionLevel.NORMAL
            }

            self._add_operation(operation)

    def add_batch_extract_operation(self):
        """Add batch extraction to operations"""
        # Get selected archives
        archives = [f for f in self._get_selected_files() if self.seven_zip.is_archive(f)]

        if not archives:
            QMessageBox.information(self, "No Archives", "No archives selected")
            return

        # Choose destination
        destination = QFileDialog.getExistingDirectory(self, "Extract All To")

        if destination:
            for archive in archives:
                operation = {
                    'type': 'extract_archive',
                    'archive': archive,
                    'destination': os.path.join(destination, Path(archive).stem)
                }

                self._add_operation(operation)

    def _execute_create_archive(self, operation: dict):
        """Execute archive creation operation"""
        try:
            self.seven_zip.create_archive(
                archive_path=operation['archive_name'],
                source_paths=operation['files'],
                format=operation['format'],
                compression_level=operation['compression']
            )
            return True, "Archive created successfully"
        except Exception as e:
            return False, str(e)

    def _execute_extract_archive(self, operation: dict):
        """Execute archive extraction operation"""
        try:
            self.seven_zip.extract(
                archive_path=operation['archive'],
                destination=operation['destination']
            )
            return True, "Archive extracted successfully"
        except Exception as e:
            return False, str(e)
```

### 7. Search Inside Archives

```python
# In search_panel.py or backend.py

from archive.sevenzip_manager import SevenZipManager

class SearchEngine:
    def __init__(self):
        self.seven_zip = SevenZipManager()

    def search_with_archives(self, query: str, search_in_archives: bool = False):
        """Search files including inside archives"""
        results = []

        # Regular file search
        regular_results = self._search_files(query)
        results.extend(regular_results)

        if search_in_archives:
            # Find all archives
            archives = [f for f in regular_results if self.seven_zip.is_archive(f.path)]

            # Search inside each archive
            for archive in archives:
                try:
                    entries = self.seven_zip.list_contents(archive.path)

                    for entry in entries:
                        path = entry.get('Path', '')

                        if query.lower() in path.lower():
                            # Add as virtual result
                            results.append({
                                'path': f"{archive.path}::{path}",
                                'name': os.path.basename(path),
                                'size': entry.get('Size', 0),
                                'type': 'archive_entry',
                                'parent_archive': archive.path
                            })

                except Exception:
                    pass  # Skip problematic archives

        return results
```

### 8. Settings Integration

```python
# In settings_dialog.py

class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self._add_archive_settings()

    def _add_archive_settings(self):
        """Add archive settings page"""
        archive_page = QWidget()
        layout = QVBoxLayout(archive_page)

        # 7-Zip path
        path_group = QGroupBox("7-Zip Configuration")
        path_layout = QFormLayout(path_group)

        self.sevenzip_path = QLineEdit()
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_sevenzip)

        path_row = QHBoxLayout()
        path_row.addWidget(self.sevenzip_path)
        path_row.addWidget(browse_btn)

        path_layout.addRow("7-Zip Path:", path_row)
        layout.addWidget(path_group)

        # Default compression
        comp_group = QGroupBox("Default Settings")
        comp_layout = QFormLayout(comp_group)

        self.default_format = QComboBox()
        self.default_format.addItems(['7z', 'zip', 'tar'])

        self.default_compression = QSlider(Qt.Orientation.Horizontal)
        self.default_compression.setRange(0, 9)
        self.default_compression.setValue(5)

        comp_layout.addRow("Default Format:", self.default_format)
        comp_layout.addRow("Default Compression:", self.default_compression)

        layout.addWidget(comp_group)

        # Extraction options
        extract_group = QGroupBox("Extraction Options")
        extract_layout = QVBoxLayout(extract_group)

        self.auto_extract_nested = QCheckBox("Auto-extract nested archives")
        self.preserve_structure = QCheckBox("Preserve directory structure")
        self.preserve_structure.setChecked(True)

        extract_layout.addWidget(self.auto_extract_nested)
        extract_layout.addWidget(self.preserve_structure)

        layout.addWidget(extract_group)

        # Add to settings
        self.settings_tabs.addTab(archive_page, "Archives")

    def _browse_sevenzip(self):
        """Browse for 7z.exe"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select 7z.exe",
            "C:\\Program Files\\7-Zip",
            "7-Zip Executable (7z.exe)"
        )

        if path:
            self.sevenzip_path.setText(path)
```

## Keyboard Shortcuts

Add keyboard shortcuts for archive operations:

```python
# In main_window.py

def _setup_shortcuts(self):
    """Setup keyboard shortcuts"""
    # ... existing shortcuts ...

    # Archive shortcuts
    QShortcut(QKeySequence("Ctrl+E"), self, self._extract_selected)
    QShortcut(QKeySequence("Ctrl+Shift+A"), self, self._create_archive)
    QShortcut(QKeySequence("Ctrl+T"), self, self._test_archive)
```

## Performance Considerations

1. **Background Processing**: Always run extraction in background threads
2. **Progress Updates**: Throttle progress updates to ~100ms intervals
3. **Large Archives**: Use streaming for archives >100MB
4. **Caching**: Cache archive contents list for frequently accessed archives
5. **Batch Operations**: Process archives in parallel with ThreadPoolExecutor

## Security Best Practices

1. **Path Validation**: Always validate extraction paths to prevent path traversal
2. **Password Storage**: Never store passwords in plaintext
3. **Temp Files**: Always cleanup temporary files, even on error
4. **User Confirmation**: Ask before extracting archives with many files
5. **Sandbox**: Consider sandboxing extraction for untrusted archives

## Testing

Run integration tests:

```bash
# Test archive module
python archive/test_archive_integration.py

# Test UI integration
python ui/test_archive_panel.py

# Test full integration
python test_smart_search_archives.py
```

## Troubleshooting

### 7-Zip not found
Add to PATH or set in settings dialog

### Extraction fails
Check disk space, permissions, and archive integrity

### Password issues
Verify password encoding and special characters

### Performance problems
Enable multi-threading, use faster compression, or extract to SSD

## Future Enhancements

- Archive repair tools
- Archive conversion (zip ↔ 7z)
- Cloud archive support
- Archive diff/patch
- Integration with Everything SDK for instant archive search
- Archive encryption beyond passwords (certificates)
- Archive splitting/joining UI
- Thumbnail preview of images in archives

## Support

For issues or questions:
1. Check README.md in archive/
2. Run test suite
3. Check 7-Zip documentation: https://www.7-zip.org/
4. Review example_usage.py

## License

Part of Smart Search Pro - All Rights Reserved
