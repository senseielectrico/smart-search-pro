"""
Integration tests for Duplicates Panel UI and backend connection.

Tests the complete workflow from scanning to deletion.
"""

import sys
import tempfile
import shutil
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.duplicates_panel import DuplicatesPanel
from duplicates.scanner import DuplicateScanner
from duplicates.groups import SelectionStrategy


@pytest.fixture
def qapp():
    """Create QApplication instance for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def temp_test_dir():
    """Create temporary directory with duplicate files"""
    temp_dir = Path(tempfile.mkdtemp(prefix="duplicates_test_"))

    # Create test files
    # Group 1: Three identical text files
    for i in range(3):
        file_path = temp_dir / f"duplicate_{i}.txt"
        file_path.write_text("This is duplicate content")

    # Group 2: Two identical binary files
    for i in range(2):
        file_path = temp_dir / f"binary_{i}.bin"
        file_path.write_bytes(b"\x00\x01\x02" * 1000)

    # Unique file (should not appear in results)
    unique = temp_dir / "unique.txt"
    unique.write_text("This is unique content")

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestDuplicatesPanelIntegration:
    """Integration tests for DuplicatesPanel"""

    def test_panel_initialization(self, qapp):
        """Test that panel initializes correctly"""
        panel = DuplicatesPanel()
        panel.show()  # Must show panel for visibility checks to work

        # Check initial state
        assert panel.scanner is not None
        assert panel.group_manager is None
        assert not panel.is_scanning

        # Check UI elements exist
        assert panel.scan_btn is not None
        assert panel.delete_btn is not None
        assert panel.move_btn is not None
        assert panel.strategy_combo is not None
        assert panel.tree is not None

        # Check initial UI state
        assert panel.scan_btn.isEnabled()
        assert not panel.delete_btn.isEnabled()
        assert not panel.move_btn.isEnabled()
        # Use isHidden() for visibility checks (independent of parent visibility)
        assert not panel.empty_state.isHidden()
        assert panel.tree.isHidden()

    def test_scanner_backend(self, temp_test_dir):
        """Test that scanner backend works correctly"""
        scanner = DuplicateScanner(use_cache=False, max_workers=2)

        # Scan test directory
        manager = scanner.scan([str(temp_test_dir)], recursive=False)

        # Verify results
        assert len(manager.groups) == 2  # Two groups of duplicates

        # Check group sizes
        group_sizes = sorted([g.file_count for g in manager.groups])
        assert group_sizes == [2, 3]  # One group of 2, one group of 3

        # Check wasted space calculation
        total_wasted = sum(g.wasted_space for g in manager.groups)
        assert total_wasted > 0  # Should have wasted space

    def test_selection_strategies(self, temp_test_dir):
        """Test that selection strategies work correctly"""
        scanner = DuplicateScanner(use_cache=False)
        manager = scanner.scan([str(temp_test_dir)], recursive=False)

        # Test "Keep Oldest" strategy
        manager.apply_strategy_to_all(SelectionStrategy.KEEP_OLDEST)

        for group in manager.groups:
            # Should keep exactly 1 file (the oldest)
            assert len(group.selected_for_keeping) == 1
            assert len(group.selected_for_deletion) == group.file_count - 1

            # The kept file should be the oldest
            kept_file = group.selected_for_keeping[0]
            for deleted_file in group.selected_for_deletion:
                assert kept_file.mtime <= deleted_file.mtime

        # Test "Keep Newest" strategy
        manager.apply_strategy_to_all(SelectionStrategy.KEEP_NEWEST)

        for group in manager.groups:
            # Should keep exactly 1 file (the newest)
            assert len(group.selected_for_keeping) == 1

            # The kept file should be the newest
            kept_file = group.selected_for_keeping[0]
            for deleted_file in group.selected_for_deletion:
                assert kept_file.mtime >= deleted_file.mtime

    def test_format_size(self, qapp):
        """Test size formatting"""
        panel = DuplicatesPanel()

        assert panel._format_size(0) == "0.0 B"
        assert panel._format_size(512) == "512.0 B"
        assert panel._format_size(1024) == "1.0 KB"
        assert panel._format_size(1024 * 1024) == "1.0 MB"
        assert panel._format_size(1024 * 1024 * 1024) == "1.0 GB"
        assert panel._format_size(1536) == "1.5 KB"

    def test_stats_display(self, qapp, temp_test_dir):
        """Test that stats are displayed correctly"""
        panel = DuplicatesPanel()
        panel.show()  # Must show panel for visibility checks to work

        # Manually trigger scan completion
        scanner = DuplicateScanner(use_cache=False)
        manager = scanner.scan([str(temp_test_dir)], recursive=False)

        panel.group_manager = manager
        panel._display_results()
        # Also need to update visibility like _scan_completed does
        panel.tree.show()
        panel.empty_state.hide()

        # Check that stats label is updated
        stats_text = panel.stats_label.text()
        assert "groups" in stats_text
        assert "duplicates" in stats_text
        assert "wasted" in stats_text

        # Check tree has correct number of groups
        assert panel.tree.topLevelItemCount() == 2

        # Check tree is visible (use isHidden for more reliable check)
        assert not panel.tree.isHidden()
        assert panel.empty_state.isHidden()

    def test_group_display(self, qapp, temp_test_dir):
        """Test that groups are displayed correctly in tree"""
        panel = DuplicatesPanel()

        scanner = DuplicateScanner(use_cache=False)
        manager = scanner.scan([str(temp_test_dir)], recursive=False)

        panel.group_manager = manager
        panel._display_results()

        # Check each group
        for i in range(panel.tree.topLevelItemCount()):
            group_item = panel.tree.topLevelItem(i)

            # Group item should have correct structure
            assert group_item.text(0).endswith("duplicates")
            assert "B" in group_item.text(1)  # Size column
            assert "Wasted" in group_item.text(2)
            assert "Hash" in group_item.text(3)

            # Group should have children
            assert group_item.childCount() >= 2

            # Check file items
            for j in range(group_item.childCount()):
                file_item = group_item.child(j)

                # File item should have data
                assert file_item.text(0)  # Filename
                assert file_item.text(1)  # Size
                assert file_item.text(2)  # Path
                assert file_item.text(3)  # Modified date

                # File item should have checkbox
                assert file_item.checkState(0) in [Qt.CheckState.Checked, Qt.CheckState.Unchecked]

                # File item should have UserRole data
                file_info = file_item.data(0, Qt.ItemDataRole.UserRole)
                assert file_info is not None
                assert file_info.path.exists()

    def test_strategy_combo_updates_checkboxes(self, qapp, temp_test_dir):
        """Test that changing strategy updates checkboxes"""
        panel = DuplicatesPanel()

        scanner = DuplicateScanner(use_cache=False)
        manager = scanner.scan([str(temp_test_dir)], recursive=False)

        panel.group_manager = manager
        panel._display_results()

        # Initially, no strategy applied, all unchecked
        initial_checked = []
        for i in range(panel.tree.topLevelItemCount()):
            group_item = panel.tree.topLevelItem(i)
            for j in range(group_item.childCount()):
                file_item = group_item.child(j)
                initial_checked.append(file_item.checkState(0))

        # Apply "Keep Oldest" strategy
        panel.strategy_combo.setCurrentIndex(0)  # Keep Oldest
        panel._apply_strategy()

        # Check that some files are now checked
        checked_count = 0
        unchecked_count = 0

        for i in range(panel.tree.topLevelItemCount()):
            group_item = panel.tree.topLevelItem(i)
            group_checked = 0
            group_unchecked = 0

            for j in range(group_item.childCount()):
                file_item = group_item.child(j)
                if file_item.checkState(0) == Qt.CheckState.Checked:
                    checked_count += 1
                    group_checked += 1
                else:
                    unchecked_count += 1
                    group_unchecked += 1

            # Each group should have exactly 1 unchecked (kept) file
            assert group_unchecked == 1
            assert group_checked == group_item.childCount() - 1

        # Overall, should have some checked and some unchecked
        assert checked_count > 0
        assert unchecked_count > 0
        assert checked_count + unchecked_count == 5  # Total files (3+2)


def test_scanner_performance():
    """Test scanner performance with larger dataset"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create 100 files (50 duplicates)
        for i in range(50):
            # Create two identical files
            content = f"Content {i % 25}".encode()

            file1 = temp_path / f"file_{i}_a.txt"
            file2 = temp_path / f"file_{i}_b.txt"

            file1.write_bytes(content)
            file2.write_bytes(content)

        # Scan
        scanner = DuplicateScanner(use_cache=False, max_workers=4)

        import time
        start = time.time()
        manager = scanner.scan([str(temp_path)], recursive=False)
        duration = time.time() - start

        # Check results
        assert len(manager.groups) == 25  # 25 groups (each with 2 files)

        # Performance check (should be fast for 100 small files)
        assert duration < 5.0  # Should complete in under 5 seconds

        print(f"Scanned 100 files in {duration:.2f}s")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
