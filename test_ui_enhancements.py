"""
Unit Tests for Smart Search UI Enhancements

Run tests:
    python -m pytest test_ui_enhancements.py -v

Or with coverage:
    python -m pytest test_ui_enhancements.py --cov=ui_enhancements --cov-report=html
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Ensure QApplication exists for tests
@pytest.fixture(scope='session')
def qapp():
    """Create QApplication for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


# Import components to test
from ui_enhancements import (
    SearchPreset, SearchHistory, SearchHistoryWidget,
    QuickFilterChips, EnhancedDirectoryTree, FilePreviewPanel,
    GridViewWidget, SearchPresetsDialog, ExportDialog,
    show_notification
)


# ========================================
# DATA MODEL TESTS
# ========================================

class TestSearchPreset:
    """Test SearchPreset data model"""

    def test_create_preset(self):
        """Test creating a preset"""
        preset = SearchPreset(
            name="Test Preset",
            search_term="*.py",
            paths=["C:\\Users", "C:\\Projects"],
            case_sensitive=True,
            file_types=[".py", ".js"]
        )

        assert preset.name == "Test Preset"
        assert preset.search_term == "*.py"
        assert len(preset.paths) == 2
        assert preset.case_sensitive is True
        assert ".py" in preset.file_types

    def test_preset_to_dict(self):
        """Test converting preset to dictionary"""
        preset = SearchPreset(
            name="Test",
            search_term="test",
            paths=["/path"],
            case_sensitive=False
        )

        data = preset.to_dict()

        assert isinstance(data, dict)
        assert data['name'] == "Test"
        assert data['search_term'] == "test"
        assert data['case_sensitive'] is False

    def test_preset_from_dict(self):
        """Test creating preset from dictionary"""
        data = {
            'name': "Test",
            'search_term': "test",
            'paths': ["/path"],
            'case_sensitive': True,
            'file_types': [".txt"]
        }

        preset = SearchPreset.from_dict(data)

        assert preset.name == "Test"
        assert preset.search_term == "test"
        assert preset.case_sensitive is True


class TestSearchHistory:
    """Test SearchHistory data model"""

    def test_create_history(self):
        """Test creating history entry"""
        history = SearchHistory(
            term="report",
            timestamp=datetime.now(),
            paths=["C:\\Documents"],
            results_count=50
        )

        assert history.term == "report"
        assert history.results_count == 50
        assert isinstance(history.timestamp, datetime)

    def test_history_to_dict(self):
        """Test converting history to dictionary"""
        now = datetime.now()
        history = SearchHistory(
            term="test",
            timestamp=now,
            paths=["/path"],
            results_count=10
        )

        data = history.to_dict()

        assert isinstance(data, dict)
        assert data['term'] == "test"
        assert data['results_count'] == 10
        assert 'timestamp' in data

    def test_history_from_dict(self):
        """Test creating history from dictionary"""
        now = datetime.now()
        data = {
            'term': "test",
            'timestamp': now.isoformat(),
            'paths': ["/path"],
            'results_count': 10
        }

        history = SearchHistory.from_dict(data)

        assert history.term == "test"
        assert history.results_count == 10
        assert isinstance(history.timestamp, datetime)


# ========================================
# WIDGET TESTS
# ========================================

class TestSearchHistoryWidget:
    """Test SearchHistoryWidget"""

    def test_create_widget(self, qapp):
        """Test creating widget"""
        widget = SearchHistoryWidget()
        assert widget is not None
        assert widget.max_history == 50
        assert len(widget.history) == 0

    def test_add_search(self, qapp):
        """Test adding search to history"""
        widget = SearchHistoryWidget()

        widget.add_search("test", ["/path"], 10)

        assert len(widget.history) == 1
        assert widget.history[0].term == "test"
        assert widget.history[0].results_count == 10

    def test_history_limit(self, qapp):
        """Test history size limit"""
        widget = SearchHistoryWidget()
        widget.max_history = 5

        # Add more than max
        for i in range(10):
            widget.add_search(f"search{i}", ["/path"], i)

        assert len(widget.history) == 5
        # Should keep most recent
        assert widget.history[0].term == "search9"

    def test_remove_duplicates(self, qapp):
        """Test removing duplicate searches"""
        widget = SearchHistoryWidget()

        widget.add_search("test", ["/path"], 10)
        widget.add_search("other", ["/path"], 5)
        widget.add_search("test", ["/path"], 15)  # Duplicate term

        assert len(widget.history) == 2
        assert widget.history[0].term == "test"
        assert widget.history[0].results_count == 15  # Updated count

    def test_get_terms(self, qapp):
        """Test getting search terms"""
        widget = SearchHistoryWidget()

        widget.add_search("test1", ["/path"], 10)
        widget.add_search("test2", ["/path"], 20)

        terms = widget.get_terms()

        assert len(terms) == 2
        assert "test1" in terms
        assert "test2" in terms

    @patch('ui_enhancements.Path.home')
    def test_save_history(self, mock_home, qapp, tmp_path):
        """Test saving history to file"""
        mock_home.return_value = tmp_path

        widget = SearchHistoryWidget()
        widget.add_search("test", ["/path"], 10)
        widget._save_history()

        history_file = tmp_path / '.smart_search_history.json'
        assert history_file.exists()

        with open(history_file) as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]['term'] == "test"


class TestQuickFilterChips:
    """Test QuickFilterChips"""

    def test_create_widget(self, qapp):
        """Test creating widget"""
        widget = QuickFilterChips()
        assert widget is not None

    def test_default_filter(self, qapp):
        """Test default filter selection"""
        widget = QuickFilterChips()
        selected = widget.get_selected_filter()

        assert selected == []  # "All Files" selected by default

    def test_filter_buttons(self, qapp):
        """Test filter buttons exist"""
        widget = QuickFilterChips()

        # Should have buttons for all filter types
        assert widget.button_group.buttons()
        assert len(widget.button_group.buttons()) == len(QuickFilterChips.FILTERS)

    def test_signal_emission(self, qapp):
        """Test filter changed signal"""
        widget = QuickFilterChips()

        # Mock signal handler
        mock_handler = Mock()
        widget.filter_changed.connect(mock_handler)

        # Click a button
        buttons = widget.button_group.buttons()
        if len(buttons) > 1:
            buttons[1].click()  # Click second button (Images)

            # Signal should be emitted
            mock_handler.assert_called_once()


class TestEnhancedDirectoryTree:
    """Test EnhancedDirectoryTree"""

    def test_create_widget(self, qapp):
        """Test creating widget"""
        widget = EnhancedDirectoryTree()
        assert widget is not None
        assert len(widget.favorites) == 0

    def test_add_favorite(self, qapp):
        """Test adding favorite"""
        widget = EnhancedDirectoryTree()

        widget.add_favorite("C:\\Test")

        assert "C:\\Test" in widget.favorites

    def test_remove_favorite(self, qapp):
        """Test removing favorite"""
        widget = EnhancedDirectoryTree()

        widget.add_favorite("C:\\Test")
        widget.remove_favorite("C:\\Test")

        assert "C:\\Test" not in widget.favorites

    def test_format_size(self, qapp):
        """Test size formatting"""
        widget = EnhancedDirectoryTree()

        assert widget._format_size(500) == "500.0 B"
        assert widget._format_size(1024) == "1.0 KB"
        assert widget._format_size(1024 * 1024) == "1.0 MB"
        assert widget._format_size(1024 * 1024 * 1024) == "1.0 GB"


class TestFilePreviewPanel:
    """Test FilePreviewPanel"""

    def test_create_widget(self, qapp):
        """Test creating widget"""
        widget = FilePreviewPanel()
        assert widget is not None
        assert widget.current_file is None

    def test_format_size(self, qapp):
        """Test size formatting"""
        widget = FilePreviewPanel()

        assert widget._format_size(500) == "500.0 B"
        assert widget._format_size(1024) == "1.0 KB"
        assert widget._format_size(1024 * 1024) == "1.0 MB"

    def test_clear_preview(self, qapp):
        """Test clearing preview"""
        widget = FilePreviewPanel()

        widget.current_file = "test.txt"
        widget.clear()

        assert widget.current_file is None

    def test_preview_nonexistent_file(self, qapp):
        """Test previewing non-existent file"""
        widget = FilePreviewPanel()

        widget.preview_file("/nonexistent/file.txt")

        # Should show error, not crash
        assert widget.info_label.isVisible()

    def test_preview_text_file(self, qapp, tmp_path):
        """Test previewing text file"""
        # Create temp text file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        widget = FilePreviewPanel()
        widget.preview_file(str(test_file))

        assert widget.current_file == str(test_file)
        assert widget.text_preview.isVisible()
        assert "Hello, World!" in widget.text_preview.toPlainText()


class TestGridViewWidget:
    """Test GridViewWidget"""

    def test_create_widget(self, qapp):
        """Test creating widget"""
        widget = GridViewWidget()
        assert widget is not None
        assert len(widget.items) == 0

    def test_add_item(self, qapp):
        """Test adding item"""
        widget = GridViewWidget()

        file_info = {
            'name': 'test.txt',
            'path': '/path/test.txt',
            'size': 1024,
            'modified': datetime.now()
        }

        widget.add_item(file_info)

        assert len(widget.items) == 1
        assert widget.items[0]['name'] == 'test.txt'

    def test_clear_items(self, qapp):
        """Test clearing items"""
        widget = GridViewWidget()

        widget.add_item({
            'name': 'test.txt',
            'path': '/path/test.txt',
            'size': 1024,
            'modified': datetime.now()
        })

        widget.clear()

        assert len(widget.items) == 0


class TestSearchPresetsDialog:
    """Test SearchPresetsDialog"""

    def test_create_dialog(self, qapp):
        """Test creating dialog"""
        dialog = SearchPresetsDialog()
        assert dialog is not None
        assert len(dialog.presets) == 0

    def test_add_preset(self, qapp):
        """Test adding preset"""
        dialog = SearchPresetsDialog()

        preset = SearchPreset(
            name="Test",
            search_term="*.py",
            paths=["/path"],
            case_sensitive=False
        )

        dialog.add_preset(preset)

        assert len(dialog.presets) == 1
        assert dialog.presets[0].name == "Test"

    @patch('ui_enhancements.Path.home')
    def test_save_presets(self, mock_home, qapp, tmp_path):
        """Test saving presets to file"""
        mock_home.return_value = tmp_path

        dialog = SearchPresetsDialog()

        preset = SearchPreset(
            name="Test",
            search_term="*.py",
            paths=["/path"],
            case_sensitive=False
        )

        dialog.add_preset(preset)

        presets_file = tmp_path / '.smart_search_presets.json'
        assert presets_file.exists()


class TestExportDialog:
    """Test ExportDialog"""

    def test_create_dialog(self, qapp):
        """Test creating dialog"""
        results = [
            {
                'name': 'test.txt',
                'path': '/path/test.txt',
                'size': 1024,
                'modified': datetime.now()
            }
        ]

        dialog = ExportDialog(results)
        assert dialog is not None

    def test_export_csv(self, qapp, tmp_path):
        """Test exporting to CSV"""
        results = [
            {
                'name': 'test.txt',
                'path': '/path/test.txt',
                'size': 1024,
                'modified': datetime.now()
            }
        ]

        dialog = ExportDialog(results)

        # Mock file dialog to return temp file
        csv_file = tmp_path / "export.csv"

        with patch('ui_enhancements.QFileDialog.getSaveFileName') as mock_dialog:
            mock_dialog.return_value = (str(csv_file), "CSV Files (*.csv)")

            dialog._export()

            # Check file was created
            assert csv_file.exists()

            # Check content
            content = csv_file.read_text()
            assert 'test.txt' in content


# ========================================
# INTEGRATION TESTS
# ========================================

class TestIntegration:
    """Integration tests for component interaction"""

    def test_search_history_persistence(self, qapp, tmp_path):
        """Test history persistence across widget instances"""
        with patch('ui_enhancements.Path.home', return_value=tmp_path):
            # Create first widget and add history
            widget1 = SearchHistoryWidget()
            widget1.add_search("test", ["/path"], 10)

            # Create second widget (should load from file)
            widget2 = SearchHistoryWidget()

            assert len(widget2.history) == 1
            assert widget2.history[0].term == "test"

    def test_favorites_persistence(self, qapp, tmp_path):
        """Test favorites persistence"""
        with patch('ui_enhancements.Path.home', return_value=tmp_path):
            # Create first tree and add favorite
            tree1 = EnhancedDirectoryTree()
            tree1.add_favorite("C:\\Test")

            # Create second tree (should load from file)
            tree2 = EnhancedDirectoryTree()

            assert "C:\\Test" in tree2.favorites

    def test_preview_panel_with_grid_view(self, qapp):
        """Test preview panel integration with grid view"""
        preview = FilePreviewPanel()
        grid = GridViewWidget()

        # Connect signals
        grid.item_selected.connect(preview.preview_file)

        # Add item and simulate selection
        file_info = {
            'name': 'test.txt',
            'path': __file__,  # Use this file for testing
            'size': 1024,
            'modified': datetime.now()
        }

        grid.add_item(file_info)
        grid._on_item_clicked(0)

        # Preview should be updated
        assert preview.current_file == __file__


# ========================================
# PERFORMANCE TESTS
# ========================================

class TestPerformance:
    """Performance tests"""

    def test_large_history(self, qapp):
        """Test handling large history"""
        widget = SearchHistoryWidget()

        # Add many items
        for i in range(100):
            widget.add_search(f"search{i}", ["/path"], i)

        # Should maintain size limit
        assert len(widget.history) <= widget.max_history

    def test_large_grid(self, qapp):
        """Test grid with many items"""
        widget = GridViewWidget()

        # Add many items
        for i in range(100):
            widget.add_item({
                'name': f'file{i}.txt',
                'path': f'/path/file{i}.txt',
                'size': 1024,
                'modified': datetime.now()
            })

        assert len(widget.items) == 100

    def test_favorites_performance(self, qapp):
        """Test favorites with many paths"""
        tree = EnhancedDirectoryTree()

        # Add many favorites
        for i in range(100):
            tree.add_favorite(f"C:\\Path{i}")

        assert len(tree.favorites) == 100


# ========================================
# ERROR HANDLING TESTS
# ========================================

class TestErrorHandling:
    """Test error handling"""

    def test_invalid_preset_data(self, qapp):
        """Test handling invalid preset data"""
        with pytest.raises(Exception):
            SearchPreset.from_dict({})  # Missing required fields

    def test_corrupted_history_file(self, qapp, tmp_path):
        """Test handling corrupted history file"""
        with patch('ui_enhancements.Path.home', return_value=tmp_path):
            # Create corrupted file
            history_file = tmp_path / '.smart_search_history.json'
            history_file.write_text("invalid json{")

            # Should not crash, just start with empty history
            widget = SearchHistoryWidget()
            assert len(widget.history) == 0

    def test_preview_permission_error(self, qapp):
        """Test handling permission errors in preview"""
        widget = FilePreviewPanel()

        # Try to preview system file (might fail)
        widget.preview_file("C:\\Windows\\System32\\config\\SAM")

        # Should show error, not crash
        assert widget.info_label.isVisible() or widget.text_preview.isVisible()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
