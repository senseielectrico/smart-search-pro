"""
Examples for using the export module.
"""

from pathlib import Path
from typing import List

from .base import ExportConfig
from .csv_exporter import CSVExporter, TSVExporter
from .excel_exporter import ExcelExporter
from .html_exporter import HTMLExporter
from .json_exporter import JSONExporter, CompactJSONExporter, JSONLinesExporter
from .clipboard import ClipboardExporter, copy_to_clipboard


def example_csv_export(results, output_path: str = "results.csv"):
    """
    Example: Export to CSV with custom columns.

    Args:
        results: Search results
        output_path: Output file path
    """
    config = ExportConfig(
        output_path=Path(output_path),
        columns=["filename", "path", "size", "date_modified"],
        include_headers=True,
        size_format="human",
        date_format="%Y-%m-%d %H:%M",
        overwrite=True
    )

    exporter = CSVExporter(config)
    stats = exporter.export(results)

    print(f"Exported {stats.exported_records} records to {output_path}")
    print(f"File size: {stats.output_size_bytes} bytes")
    print(f"Duration: {stats.duration_seconds:.2f} seconds")


def example_excel_export(results, output_path: str = "results.xlsx"):
    """
    Example: Export to Excel with multiple sheets.

    Args:
        results: Search results
        output_path: Output file path
    """
    config = ExportConfig(
        output_path=Path(output_path),
        columns=["filename", "extension", "size", "date_modified", "path"],
        overwrite=True,
        options={
            "split_by": "extension",  # Create sheet per file type
            "include_summary": True,
            "freeze_panes": True,
            "auto_filter": True,
            "use_tables": True,
            "add_hyperlinks": True,
        }
    )

    exporter = ExcelExporter(config)
    stats = exporter.export(results)

    print(f"Exported {stats.exported_records} records to {output_path}")


def example_html_export(results, output_path: str = "results.html"):
    """
    Example: Export to interactive HTML report.

    Args:
        results: Search results
        output_path: Output file path
    """
    config = ExportConfig(
        output_path=Path(output_path),
        columns=["filename", "size", "date_modified", "path"],
        overwrite=True,
        options={
            "title": "Search Results",
            "theme": "auto",  # auto, light, dark
            "sortable": True,
            "searchable": True,
            "include_icons": True,
        }
    )

    exporter = HTMLExporter(config)
    stats = exporter.export(results)

    print(f"Exported {stats.exported_records} records to {output_path}")
    print(f"Open in browser: file:///{output_path}")


def example_json_export(results, output_path: str = "results.json"):
    """
    Example: Export to pretty-printed JSON.

    Args:
        results: Search results
        output_path: Output file path
    """
    config = ExportConfig(
        output_path=Path(output_path),
        columns=["filename", "path", "size", "date_modified", "is_folder"],
        overwrite=True,
        options={
            "pretty": True,
            "indent": 2,
            "include_metadata": True,
            "sort_keys": True,
        }
    )

    exporter = JSONExporter(config)
    stats = exporter.export(results)

    print(f"Exported {stats.exported_records} records to {output_path}")


def example_clipboard_export(results):
    """
    Example: Copy results to clipboard in various formats.

    Args:
        results: Search results
    """
    # CSV format
    count = copy_to_clipboard(results, format="csv")
    print(f"Copied {count} results to clipboard as CSV")

    # Paths only
    count = copy_to_clipboard(
        results,
        format="paths",
        columns=["full_path"],
        include_headers=False
    )
    print(f"Copied {count} file paths to clipboard")

    # JSON format
    config = ExportConfig(
        columns=["filename", "size", "path"],
        options={"format": "json", "pretty": True}
    )
    exporter = ClipboardExporter(config)
    stats = exporter.export(results)
    print(f"Copied {stats.exported_records} results to clipboard as JSON")


def example_batch_export(results, output_dir: str = "exports"):
    """
    Example: Export to multiple formats at once.

    Args:
        results: Search results
        output_dir: Output directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Common columns
    columns = ["filename", "extension", "size", "date_modified", "path"]

    # Export to CSV
    csv_config = ExportConfig(
        output_path=output_path / "results.csv",
        columns=columns,
        overwrite=True
    )
    CSVExporter(csv_config).export(results)
    print(f"✓ CSV exported")

    # Export to Excel
    excel_config = ExportConfig(
        output_path=output_path / "results.xlsx",
        columns=columns,
        overwrite=True,
        options={"split_by": "extension"}
    )
    ExcelExporter(excel_config).export(results)
    print(f"✓ Excel exported")

    # Export to HTML
    html_config = ExportConfig(
        output_path=output_path / "results.html",
        columns=columns,
        overwrite=True,
        options={"theme": "auto"}
    )
    HTMLExporter(html_config).export(results)
    print(f"✓ HTML exported")

    # Export to JSON
    json_config = ExportConfig(
        output_path=output_path / "results.json",
        columns=columns,
        overwrite=True,
        options={"pretty": True}
    )
    JSONExporter(json_config).export(results)
    print(f"✓ JSON exported")

    print(f"\nAll exports completed in: {output_path}")


def example_with_progress(results, output_path: str = "results.csv"):
    """
    Example: Export with progress callback.

    Args:
        results: Search results
        output_path: Output file path
    """
    def progress_callback(current: int, total: int, message: str):
        """Progress callback function."""
        percent = (current / total * 100) if total > 0 else 0
        print(f"\r{message}: {current}/{total} ({percent:.1f}%)", end="")
        if current == total:
            print()  # New line when complete

    config = ExportConfig(
        output_path=Path(output_path),
        columns=["filename", "size", "path"],
        overwrite=True,
        use_batch=True,
        batch_size=1000,
        progress_callback=progress_callback
    )

    exporter = CSVExporter(config)
    stats = exporter.export(results)

    print(f"Export complete: {stats}")


def example_filtered_export(results, output_path: str = "large_files.csv"):
    """
    Example: Export only filtered results.

    Args:
        results: Search results
        output_path: Output file path
    """
    # Filter large files (>100MB)
    large_files = [r for r in results if r.size > 100 * 1024 * 1024]

    config = ExportConfig(
        output_path=Path(output_path),
        columns=["filename", "size", "path"],
        size_format="human",
        overwrite=True
    )

    exporter = CSVExporter(config)
    stats = exporter.export(large_files)

    print(f"Exported {stats.exported_records} large files")


def example_custom_formatting(results, output_path: str = "formatted.csv"):
    """
    Example: Export with custom date and size formatting.

    Args:
        results: Search results
        output_path: Output file path
    """
    config = ExportConfig(
        output_path=Path(output_path),
        columns=["filename", "size", "date_modified", "date_created"],
        date_format="%d/%m/%Y %H:%M",  # European date format
        size_format="mb",  # Size in megabytes
        overwrite=True
    )

    exporter = CSVExporter(config)
    stats = exporter.export(results)

    print(f"Exported with custom formatting: {output_path}")


def example_tsv_export(results, output_path: str = "results.tsv"):
    """
    Example: Export to tab-separated values.

    Args:
        results: Search results
        output_path: Output file path
    """
    config = ExportConfig(
        output_path=Path(output_path),
        columns=["filename", "size", "path"],
        overwrite=True
    )

    exporter = TSVExporter(config)
    stats = exporter.export(results)

    print(f"Exported {stats.exported_records} records to TSV")


def example_json_lines_export(results, output_path: str = "results.jsonl"):
    """
    Example: Export to JSON Lines format (for big data tools).

    Args:
        results: Search results
        output_path: Output file path
    """
    config = ExportConfig(
        output_path=Path(output_path),
        columns=["filename", "size", "path", "date_modified"],
        overwrite=True
    )

    exporter = JSONLinesExporter(config)
    stats = exporter.export(results)

    print(f"Exported {stats.exported_records} records to JSON Lines")


if __name__ == "__main__":
    # Demo with sample data
    from ..search.engine import SearchResult

    # Create sample results
    sample_results = [
        SearchResult(
            filename="document.pdf",
            path="C:\\Users\\test\\Documents",
            full_path="C:\\Users\\test\\Documents\\document.pdf",
            extension=".pdf",
            size=1024000,
            date_modified=1700000000,
            is_folder=False
        ),
        SearchResult(
            filename="image.jpg",
            path="C:\\Users\\test\\Pictures",
            full_path="C:\\Users\\test\\Pictures\\image.jpg",
            extension=".jpg",
            size=2048000,
            date_modified=1700000000,
            is_folder=False
        ),
    ]

    print("Export Examples\n" + "=" * 50)

    print("\n1. CSV Export:")
    example_csv_export(sample_results, "demo_results.csv")

    print("\n2. JSON Export:")
    example_json_export(sample_results, "demo_results.json")

    print("\n3. Clipboard Export:")
    example_clipboard_export(sample_results)
