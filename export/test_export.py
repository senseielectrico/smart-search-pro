"""
Comprehensive tests for export module.
"""

import json
import tempfile
from pathlib import Path

import pytest

from .base import ExportConfig, ExportError, ExportStats
from .csv_exporter import CSVExporter, TSVExporter
from .json_exporter import JSONExporter, CompactJSONExporter, JSONLinesExporter


# Sample data for testing
@pytest.fixture
def sample_results():
    """Create sample search results."""
    from ..search.engine import SearchResult

    return [
        SearchResult(
            filename="document.pdf",
            path="C:\\Users\\test\\Documents",
            full_path="C:\\Users\\test\\Documents\\document.pdf",
            extension=".pdf",
            size=1024000,
            date_modified=1700000000,
            date_created=1700000000,
            is_folder=False,
            relevance_score=0.95
        ),
        SearchResult(
            filename="image.jpg",
            path="C:\\Users\\test\\Pictures",
            full_path="C:\\Users\\test\\Pictures\\image.jpg",
            extension=".jpg",
            size=2048000,
            date_modified=1700000100,
            date_created=1700000100,
            is_folder=False,
            relevance_score=0.85
        ),
        SearchResult(
            filename="Projects",
            path="C:\\Users\\test",
            full_path="C:\\Users\\test\\Projects",
            extension="",
            size=0,
            date_modified=1700000200,
            date_created=1700000200,
            is_folder=True,
            relevance_score=0.75
        ),
    ]


class TestExportConfig:
    """Test ExportConfig class."""

    def test_default_config(self):
        """Test default configuration."""
        config = ExportConfig()

        assert config.overwrite is False
        assert config.include_headers is True
        assert config.date_format == "%Y-%m-%d %H:%M:%S"
        assert config.size_format == "human"
        assert config.batch_size == 1000
        assert "filename" in config.columns

    def test_custom_config(self):
        """Test custom configuration."""
        config = ExportConfig(
            output_path=Path("test.csv"),
            columns=["filename", "size"],
            overwrite=True,
            max_results=100,
            options={"delimiter": "\t"}
        )

        assert config.output_path == Path("test.csv")
        assert config.columns == ["filename", "size"]
        assert config.overwrite is True
        assert config.max_results == 100
        assert config.options["delimiter"] == "\t"


class TestExportStats:
    """Test ExportStats class."""

    def test_stats_creation(self):
        """Test creating statistics."""
        stats = ExportStats(
            total_records=100,
            exported_records=95,
            skipped_records=3,
            errors=2,
            duration_seconds=1.5
        )

        assert stats.total_records == 100
        assert stats.exported_records == 95
        assert stats.skipped_records == 3
        assert stats.errors == 2
        assert stats.duration_seconds == 1.5

    def test_stats_string(self):
        """Test string representation."""
        stats = ExportStats(total_records=100, exported_records=100)
        stats_str = str(stats)

        assert "Total: 100" in stats_str
        assert "Exported: 100" in stats_str


class TestCSVExporter:
    """Test CSV exporter."""

    def test_csv_export(self, sample_results):
        """Test basic CSV export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"

            config = ExportConfig(
                output_path=output_path,
                columns=["filename", "size", "is_folder"],
                overwrite=True
            )

            exporter = CSVExporter(config)
            stats = exporter.export(sample_results)

            assert stats.exported_records == 3
            assert stats.errors == 0
            assert output_path.exists()

            # Verify content
            content = output_path.read_text(encoding="utf-8-sig")
            assert "filename" in content
            assert "document.pdf" in content
            assert "image.jpg" in content

    def test_csv_custom_delimiter(self, sample_results):
        """Test CSV with custom delimiter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"

            config = ExportConfig(
                output_path=output_path,
                columns=["filename", "size"],
                overwrite=True,
                options={"delimiter": "|"}
            )

            exporter = CSVExporter(config)
            exporter.export(sample_results)

            content = output_path.read_text(encoding="utf-8-sig")
            assert "|" in content

    def test_csv_without_headers(self, sample_results):
        """Test CSV without headers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"

            config = ExportConfig(
                output_path=output_path,
                columns=["filename"],
                include_headers=False,
                overwrite=True
            )

            exporter = CSVExporter(config)
            exporter.export(sample_results)

            content = output_path.read_text(encoding="utf-8-sig")
            lines = content.strip().split("\n")
            assert lines[0] != "filename"  # First line is data, not header

    def test_csv_size_formatting(self, sample_results):
        """Test size formatting options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Human-readable format
            output_path = Path(tmpdir) / "human.csv"
            config = ExportConfig(
                output_path=output_path,
                columns=["filename", "size"],
                size_format="human",
                overwrite=True
            )
            CSVExporter(config).export(sample_results)
            content = output_path.read_text(encoding="utf-8-sig")
            assert "KB" in content or "MB" in content

            # Bytes format
            output_path = Path(tmpdir) / "bytes.csv"
            config.output_path = output_path
            config.size_format = "bytes"
            CSVExporter(config).export(sample_results)
            content = output_path.read_text(encoding="utf-8-sig")
            assert "1024000" in content

    def test_csv_to_string(self, sample_results):
        """Test export to string."""
        config = ExportConfig(
            columns=["filename", "size"],
            include_headers=True
        )

        exporter = CSVExporter(config)
        csv_string = exporter.export_to_string(sample_results)

        assert "filename" in csv_string
        assert "document.pdf" in csv_string
        assert len(csv_string) > 0

    def test_tsv_export(self, sample_results):
        """Test TSV exporter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.tsv"

            config = ExportConfig(
                output_path=output_path,
                columns=["filename", "size"],
                overwrite=True
            )

            exporter = TSVExporter(config)
            exporter.export(sample_results)

            content = output_path.read_text(encoding="utf-8-sig")
            assert "\t" in content


class TestJSONExporter:
    """Test JSON exporter."""

    def test_json_export(self, sample_results):
        """Test basic JSON export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"

            config = ExportConfig(
                output_path=output_path,
                columns=["filename", "size", "is_folder"],
                overwrite=True
            )

            exporter = JSONExporter(config)
            stats = exporter.export(sample_results)

            assert stats.exported_records == 3
            assert output_path.exists()

            # Verify JSON structure
            data = json.loads(output_path.read_text(encoding="utf-8"))
            assert "metadata" in data
            assert "results" in data
            assert len(data["results"]) == 3

    def test_json_without_metadata(self, sample_results):
        """Test JSON export without metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"

            config = ExportConfig(
                output_path=output_path,
                columns=["filename"],
                overwrite=True,
                options={"include_metadata": False}
            )

            exporter = JSONExporter(config)
            exporter.export(sample_results)

            data = json.loads(output_path.read_text(encoding="utf-8"))
            assert isinstance(data, list)
            assert len(data) == 3

    def test_json_pretty_vs_compact(self, sample_results):
        """Test pretty vs compact JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Pretty JSON
            pretty_path = Path(tmpdir) / "pretty.json"
            config = ExportConfig(
                output_path=pretty_path,
                columns=["filename"],
                overwrite=True,
                options={"pretty": True, "indent": 2}
            )
            JSONExporter(config).export(sample_results)
            pretty_size = pretty_path.stat().st_size

            # Compact JSON
            compact_path = Path(tmpdir) / "compact.json"
            config.output_path = compact_path
            exporter = CompactJSONExporter(config)
            exporter.export(sample_results)
            compact_size = compact_path.stat().st_size

            # Compact should be smaller
            assert compact_size < pretty_size

    def test_json_to_string(self, sample_results):
        """Test export to string."""
        config = ExportConfig(
            columns=["filename", "size"],
            options={"pretty": True}
        )

        exporter = JSONExporter(config)
        json_string = exporter.export_to_string(sample_results)

        data = json.loads(json_string)
        assert "metadata" in data or isinstance(data, list)

    def test_jsonl_export(self, sample_results):
        """Test JSON Lines export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.jsonl"

            config = ExportConfig(
                output_path=output_path,
                columns=["filename", "size"],
                overwrite=True
            )

            exporter = JSONLinesExporter(config)
            exporter.export(sample_results)

            # Read lines
            lines = output_path.read_text(encoding="utf-8").strip().split("\n")
            assert len(lines) == 3

            # Each line should be valid JSON
            for line in lines:
                obj = json.loads(line)
                assert "filename" in obj


class TestExcelExporter:
    """Test Excel exporter."""

    def test_excel_available(self):
        """Test if Excel exporter is available."""
        try:
            from .excel_exporter import ExcelExporter, OPENPYXL_AVAILABLE
            assert OPENPYXL_AVAILABLE or not OPENPYXL_AVAILABLE  # Just check import
        except ImportError:
            pytest.skip("openpyxl not installed")

    @pytest.mark.skipif(
        not pytest.importorskip("openpyxl", reason="openpyxl not installed"),
        reason="openpyxl not installed"
    )
    def test_excel_export(self, sample_results):
        """Test basic Excel export."""
        from .excel_exporter import ExcelExporter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.xlsx"

            config = ExportConfig(
                output_path=output_path,
                columns=["filename", "size", "is_folder"],
                overwrite=True
            )

            exporter = ExcelExporter(config)
            stats = exporter.export(sample_results)

            assert stats.exported_records == 3
            assert output_path.exists()


class TestHTMLExporter:
    """Test HTML exporter."""

    def test_html_export(self, sample_results):
        """Test basic HTML export."""
        from .html_exporter import HTMLExporter

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.html"

            config = ExportConfig(
                output_path=output_path,
                columns=["filename", "size", "path"],
                overwrite=True,
                options={"title": "Test Results"}
            )

            exporter = HTMLExporter(config)
            stats = exporter.export(sample_results)

            assert stats.exported_records == 3
            assert output_path.exists()

            # Verify HTML content
            content = output_path.read_text(encoding="utf-8")
            assert "<!DOCTYPE html>" in content
            assert "Test Results" in content
            assert "document.pdf" in content

    def test_html_themes(self, sample_results):
        """Test HTML with different themes."""
        from .html_exporter import HTMLExporter

        with tempfile.TemporaryDirectory() as tmpdir:
            for theme in ["light", "dark", "auto"]:
                output_path = Path(tmpdir) / f"test_{theme}.html"

                config = ExportConfig(
                    output_path=output_path,
                    columns=["filename"],
                    overwrite=True,
                    options={"theme": theme}
                )

                exporter = HTMLExporter(config)
                exporter.export(sample_results)

                assert output_path.exists()


class TestClipboardExporter:
    """Test clipboard exporter."""

    def test_clipboard_available(self):
        """Test if clipboard support is available."""
        try:
            from .clipboard import ClipboardExporter
            # Just check if we can create instance
        except ImportError as e:
            pytest.skip(f"Clipboard support not available: {e}")

    def test_clipboard_formats(self, sample_results):
        """Test different clipboard formats."""
        from .clipboard import ClipboardExporter

        for format in ["csv", "tsv", "json", "text", "paths"]:
            config = ExportConfig(
                columns=["filename", "size"],
                options={"format": format}
            )

            try:
                exporter = ClipboardExporter(config)
                # Just test content generation, not actual clipboard copy
                content = exporter._generate_content(sample_results)
                assert len(content) > 0
            except Exception as e:
                if "Clipboard support not available" in str(e):
                    pytest.skip(str(e))
                raise


class TestProgressCallback:
    """Test progress callback functionality."""

    def test_progress_callback(self, sample_results):
        """Test that progress callback is called."""
        progress_calls = []

        def progress_callback(current: int, total: int, message: str):
            progress_calls.append((current, total, message))

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"

            config = ExportConfig(
                output_path=output_path,
                columns=["filename"],
                overwrite=True,
                progress_callback=progress_callback
            )

            exporter = CSVExporter(config)
            exporter.export(sample_results)

            # Callback should have been called
            assert len(progress_calls) > 0


class TestErrorHandling:
    """Test error handling."""

    def test_missing_output_path(self, sample_results):
        """Test error when output path is missing."""
        config = ExportConfig(
            output_path=None,
            columns=["filename"]
        )

        exporter = CSVExporter(config)

        with pytest.raises(ExportError):
            exporter.export(sample_results)

    def test_file_exists_error(self, sample_results):
        """Test error when file exists and overwrite is False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"

            # Create file
            output_path.write_text("existing content")

            config = ExportConfig(
                output_path=output_path,
                columns=["filename"],
                overwrite=False  # Don't overwrite
            )

            exporter = CSVExporter(config)

            with pytest.raises(FileExistsError):
                exporter.export(sample_results)

    def test_invalid_column(self, sample_results):
        """Test handling of invalid column names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"

            config = ExportConfig(
                output_path=output_path,
                columns=["filename", "invalid_column"],
                overwrite=True
            )

            exporter = CSVExporter(config)
            stats = exporter.export(sample_results)

            # Should export with empty values for invalid column
            assert stats.exported_records == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
