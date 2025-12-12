# Smart Search Pro - Export Module

Comprehensive export functionality for search results with support for multiple formats and advanced features.

## Features

- **Multiple Formats**: CSV, Excel, HTML, JSON, Clipboard
- **Advanced Excel**: Multi-sheet workbooks, formatting, statistics, charts
- **Interactive HTML**: Sortable tables, dark/light themes, responsive design
- **Flexible Configuration**: Customizable columns, formatting, filtering
- **Progress Tracking**: Callbacks for long-running exports
- **Batch Processing**: Memory-efficient handling of large datasets

## Installation

Required dependencies:

```bash
pip install openpyxl  # For Excel export
pip install pyperclip  # For clipboard support (optional)
```

## Quick Start

```python
from smart_search.export import CSVExporter, ExcelExporter, HTMLExporter, copy_to_clipboard
from smart_search.export.base import ExportConfig
from pathlib import Path

# Perform search
results = search_engine.search("*.pdf")

# Export to CSV
config = ExportConfig(
    output_path=Path("results.csv"),
    columns=["filename", "size", "date_modified", "path"],
    overwrite=True
)
exporter = CSVExporter(config)
stats = exporter.export(results)

# Export to Excel with multiple sheets
excel_config = ExportConfig(
    output_path=Path("results.xlsx"),
    options={"split_by": "extension", "include_summary": True}
)
ExcelExporter(excel_config).export(results)

# Export to HTML
html_config = ExportConfig(
    output_path=Path("results.html"),
    options={"theme": "dark", "sortable": True}
)
HTMLExporter(html_config).export(results)

# Quick copy to clipboard
copy_to_clipboard(results, format="paths")
```

## Exporters

### CSV Exporter

Simple, efficient CSV export with configurable delimiters and encoding.

```python
from smart_search.export import CSVExporter, ExportConfig

config = ExportConfig(
    output_path=Path("results.csv"),
    columns=["filename", "path", "size"],
    include_headers=True,
    size_format="human",  # "bytes", "human", "kb", "mb", "gb"
    date_format="%Y-%m-%d %H:%M:%S",
    options={
        "delimiter": ",",
        "encoding": "utf-8-sig",  # BOM for Excel compatibility
        "excel_compatible": True
    }
)

exporter = CSVExporter(config)
stats = exporter.export(results)
print(f"Exported {stats.exported_records} records")
```

### Excel Exporter

Professional Excel workbooks with formatting and statistics.

```python
from smart_search.export import ExcelExporter, ExportConfig

config = ExportConfig(
    output_path=Path("results.xlsx"),
    columns=["filename", "extension", "size", "date_modified", "path"],
    options={
        "split_by": "extension",  # Create sheet per file type
        "include_summary": True,  # Add statistics sheet
        "freeze_panes": True,
        "auto_filter": True,
        "use_tables": True,
        "add_hyperlinks": True,  # Make paths clickable
        "max_rows_per_sheet": 1000000
    }
)

exporter = ExcelExporter(config)
stats = exporter.export(results)
```

**Split Options:**
- `None`: Single sheet with all results
- `"extension"`: Separate sheet per file extension
- `"folder"`: Separate sheet per parent folder
- `"type"`: Separate sheets for files and folders

### HTML Exporter

Interactive HTML reports with modern styling.

```python
from smart_search.export import HTMLExporter, ExportConfig

config = ExportConfig(
    output_path=Path("results.html"),
    columns=["filename", "size", "date_modified", "path"],
    options={
        "title": "Search Results Report",
        "theme": "auto",  # "light", "dark", "auto"
        "sortable": True,  # Click columns to sort
        "searchable": True,  # Search box for filtering
        "include_icons": True,  # File type icons
        "paginate": True,
        "page_size": 100
    }
)

exporter = HTMLExporter(config)
stats = exporter.export(results)
```

**Features:**
- Responsive design (mobile-friendly)
- Dark/light theme toggle
- Click column headers to sort
- Live search/filter
- File type icons
- Summary statistics dashboard

### JSON Exporter

Structured JSON output with metadata.

```python
from smart_search.export import JSONExporter, CompactJSONExporter, JSONLinesExporter
from smart_search.export.base import ExportConfig

# Pretty-printed JSON
config = ExportConfig(
    output_path=Path("results.json"),
    options={
        "pretty": True,
        "indent": 2,
        "include_metadata": True,  # Add export metadata
        "sort_keys": True,
        "ensure_ascii": False
    }
)
exporter = JSONExporter(config)
stats = exporter.export(results)

# Compact (minified) JSON
compact_exporter = CompactJSONExporter(config)

# JSON Lines (one object per line)
jsonl_exporter = JSONLinesExporter(config)
```

### Clipboard Exporter

Quick copy-paste functionality.

```python
from smart_search.export import copy_to_clipboard

# Copy as CSV
copy_to_clipboard(results, format="csv")

# Copy paths only
copy_to_clipboard(results, format="paths", include_headers=False)

# Copy as JSON
copy_to_clipboard(results, format="json", columns=["filename", "size"])

# Advanced usage
from smart_search.export import ClipboardExporter, ExportConfig

config = ExportConfig(
    columns=["filename", "path"],
    options={"format": "tsv"}  # tab-separated
)
exporter = ClipboardExporter(config)
stats = exporter.export(results)
```

**Supported Formats:**
- `"csv"`: Comma-separated values
- `"tsv"`: Tab-separated values
- `"json"`: JSON format
- `"text"`: Plain text table
- `"paths"`: Simple list of file paths

## Configuration

### ExportConfig

Main configuration class for all exporters:

```python
from smart_search.export.base import ExportConfig
from pathlib import Path

config = ExportConfig(
    # Output settings
    output_path=Path("output.csv"),
    overwrite=False,

    # Column settings
    columns=["filename", "path", "size", "date_modified"],
    include_headers=True,

    # Filtering
    max_results=1000,
    filter_empty=False,

    # Formatting
    date_format="%Y-%m-%d %H:%M:%S",
    size_format="human",  # "bytes", "human", "kb", "mb", "gb"

    # Batch processing
    batch_size=1000,
    use_batch=False,

    # Progress tracking
    progress_callback=my_progress_function,

    # Format-specific options
    options={
        "delimiter": ",",
        "theme": "dark",
        "split_by": "extension"
    }
)
```

### Available Columns

Standard columns from `SearchResult`:

- `filename`: File/folder name
- `path`: Parent directory path
- `full_path`: Complete path
- `extension`: File extension (e.g., ".txt")
- `size`: Size in bytes
- `date_created`: Creation timestamp
- `date_modified`: Modification timestamp
- `date_accessed`: Last access timestamp
- `attributes`: File attributes
- `is_folder`: Boolean (folder vs file)
- `relevance_score`: Search relevance score

## Progress Tracking

Monitor export progress with callbacks:

```python
def progress_callback(current: int, total: int, message: str):
    percent = (current / total * 100) if total > 0 else 0
    print(f"\r{message}: {current}/{total} ({percent:.1f}%)", end="")

config = ExportConfig(
    output_path=Path("results.csv"),
    progress_callback=progress_callback,
    use_batch=True,
    batch_size=1000
)

exporter = CSVExporter(config)
stats = exporter.export(results)
```

## Batch Processing

For large datasets, enable batch processing to reduce memory usage:

```python
config = ExportConfig(
    output_path=Path("large_export.csv"),
    use_batch=True,
    batch_size=5000,  # Process 5000 records at a time
    progress_callback=progress_callback
)
```

## Export Statistics

All exporters return statistics:

```python
stats = exporter.export(results)

print(f"Total records: {stats.total_records}")
print(f"Exported: {stats.exported_records}")
print(f"Skipped: {stats.skipped_records}")
print(f"Errors: {stats.errors}")
print(f"Duration: {stats.duration_seconds:.2f}s")
print(f"Output file: {stats.output_file}")
print(f"File size: {stats.output_size_bytes} bytes")

# Or use the string representation
print(stats)
```

## Examples

### Export Multiple Formats

```python
from smart_search.export import CSVExporter, ExcelExporter, HTMLExporter, JSONExporter
from smart_search.export.base import ExportConfig
from pathlib import Path

def export_all_formats(results, output_dir="exports"):
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    columns = ["filename", "extension", "size", "date_modified", "path"]

    # CSV
    CSVExporter(ExportConfig(
        output_path=output_path / "results.csv",
        columns=columns,
        overwrite=True
    )).export(results)

    # Excel
    ExcelExporter(ExportConfig(
        output_path=output_path / "results.xlsx",
        columns=columns,
        overwrite=True,
        options={"split_by": "extension"}
    )).export(results)

    # HTML
    HTMLExporter(ExportConfig(
        output_path=output_path / "results.html",
        columns=columns,
        overwrite=True,
        options={"theme": "auto"}
    )).export(results)

    # JSON
    JSONExporter(ExportConfig(
        output_path=output_path / "results.json",
        columns=columns,
        overwrite=True,
        options={"pretty": True}
    )).export(results)
```

### Filter Before Export

```python
# Export only large files
large_files = [r for r in results if r.size > 100 * 1024 * 1024]

config = ExportConfig(
    output_path=Path("large_files.csv"),
    columns=["filename", "size", "path"],
    size_format="human"
)

CSVExporter(config).export(large_files)
```

### Custom Date/Size Formatting

```python
config = ExportConfig(
    output_path=Path("formatted.csv"),
    columns=["filename", "size", "date_modified"],
    date_format="%d/%m/%Y %H:%M",  # European format
    size_format="mb"  # Megabytes
)
```

## Error Handling

```python
from smart_search.export.base import ExportError, UnsupportedFormatError

try:
    exporter = CSVExporter(config)
    stats = exporter.export(results)
except FileExistsError as e:
    print(f"File exists: {e}")
    # Set config.overwrite = True to replace
except ExportError as e:
    print(f"Export failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Tips

1. **Use batch processing** for large datasets (>10,000 records)
2. **Limit columns** to only what you need
3. **Filter results** before export rather than after
4. **Use CSV** for fastest exports
5. **Disable features** you don't need (hyperlinks, icons, etc.)

## API Reference

See inline documentation for detailed API reference:

```python
help(CSVExporter)
help(ExcelExporter)
help(HTMLExporter)
help(JSONExporter)
help(ClipboardExporter)
help(ExportConfig)
```

## License

Part of Smart Search Pro - see main project license.
