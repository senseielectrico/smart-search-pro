"""
Standalone test for export module without complex imports.
"""

import sys
import io
import tempfile
from pathlib import Path
from dataclasses import dataclass

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


@dataclass
class MockSearchResult:
    """Mock search result for testing."""
    filename: str
    path: str
    full_path: str
    extension: str = ""
    size: int = 0
    date_created: int = 0
    date_modified: int = 0
    date_accessed: int = 0
    attributes: int = 0
    is_folder: bool = False
    relevance_score: float = 1.0


def test_base_classes():
    """Test base exporter classes."""
    print("Testing base classes...")

    from base import ExportConfig, ExportStats

    # Test config
    config = ExportConfig(
        output_path=Path("test.csv"),
        columns=["filename", "size"],
        overwrite=True
    )
    assert config.output_path == Path("test.csv")
    assert "filename" in config.columns
    print("  ✓ ExportConfig works")

    # Test stats
    stats = ExportStats(total_records=100, exported_records=100)
    assert stats.total_records == 100
    assert "Total: 100" in str(stats)
    print("  ✓ ExportStats works")


def test_csv_export():
    """Test CSV export."""
    print("\nTesting CSV export...")

    from csv_exporter import CSVExporter
    from base import ExportConfig

    results = [
        MockSearchResult(
            filename="test.txt",
            path="C:\\temp",
            full_path="C:\\temp\\test.txt",
            size=1024
        )
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.csv"

        config = ExportConfig(
            output_path=output_path,
            columns=["filename", "size"],
            overwrite=True
        )

        exporter = CSVExporter(config)
        stats = exporter.export(results)

        assert output_path.exists()
        assert stats.exported_records == 1

        content = output_path.read_text()
        assert "test.txt" in content

    print("  ✓ CSV export works")


def test_json_export():
    """Test JSON export."""
    print("\nTesting JSON export...")

    import json
    from json_exporter import JSONExporter
    from base import ExportConfig

    results = [
        MockSearchResult(
            filename="test.txt",
            path="C:\\temp",
            full_path="C:\\temp\\test.txt",
            size=1024
        )
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.json"

        config = ExportConfig(
            output_path=output_path,
            columns=["filename", "size"],
            overwrite=True
        )

        exporter = JSONExporter(config)
        stats = exporter.export(results)

        assert output_path.exists()
        assert stats.exported_records == 1

        data = json.loads(output_path.read_text())
        assert "results" in data or isinstance(data, list)

    print("  ✓ JSON export works")


def test_html_export():
    """Test HTML export."""
    print("\nTesting HTML export...")

    from html_exporter import HTMLExporter
    from base import ExportConfig

    results = [
        MockSearchResult(
            filename="test.txt",
            path="C:\\temp",
            full_path="C:\\temp\\test.txt",
            size=1024
        )
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.html"

        config = ExportConfig(
            output_path=output_path,
            columns=["filename", "size"],
            overwrite=True
        )

        exporter = HTMLExporter(config)
        stats = exporter.export(results)

        assert output_path.exists()
        assert stats.exported_records == 1

        content = output_path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "test.txt" in content

    print("  ✓ HTML export works")


def test_excel_export():
    """Test Excel export if available."""
    print("\nTesting Excel export...")

    try:
        import openpyxl
        from excel_exporter import ExcelExporter
        from base import ExportConfig

        results = [
            MockSearchResult(
                filename="test.txt",
                path="C:\\temp",
                full_path="C:\\temp\\test.txt",
                size=1024
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.xlsx"

            config = ExportConfig(
                output_path=output_path,
                columns=["filename", "size"],
                overwrite=True
            )

            exporter = ExcelExporter(config)
            stats = exporter.export(results)

            assert output_path.exists()
            assert stats.exported_records == 1

        print("  ✓ Excel export works")

    except ImportError:
        print("  ⚠ Excel export skipped (openpyxl not installed)")


def run_tests():
    """Run all tests."""
    print("=" * 60)
    print("Export Module Standalone Tests")
    print("=" * 60 + "\n")

    try:
        test_base_classes()
        test_csv_export()
        test_json_export()
        test_html_export()
        test_excel_export()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
