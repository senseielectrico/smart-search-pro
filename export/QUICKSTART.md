# Export Module - Quick Start Guide

Get started with Smart Search Pro export functionality in 5 minutes.

## Installation

```bash
cd C:\Users\ramos\.local\bin\smart_search\export
pip install -r requirements.txt
```

## Basic Usage

### 1. CSV Export (Simplest)

```python
from smart_search.export import CSVExporter, ExportConfig
from pathlib import Path

# Configure export
config = ExportConfig(
    output_path=Path("my_results.csv"),
    columns=["filename", "size", "path"],
    overwrite=True
)

# Export
exporter = CSVExporter(config)
stats = exporter.export(search_results)
print(f"Exported {stats.exported_records} records")
```

### 2. Excel Export (Professional)

```python
from smart_search.export import ExcelExporter, ExportConfig
from pathlib import Path

config = ExportConfig(
    output_path=Path("my_results.xlsx"),
    options={
        "split_by": "extension",  # Separate sheet per file type
        "include_summary": True   # Add statistics sheet
    }
)

ExcelExporter(config).export(search_results)
```

### 3. HTML Report (Interactive)

```python
from smart_search.export import HTMLExporter, ExportConfig
from pathlib import Path

config = ExportConfig(
    output_path=Path("my_report.html"),
    options={
        "theme": "dark",      # dark, light, or auto
        "sortable": True,     # Click to sort columns
        "searchable": True    # Search box
    }
)

HTMLExporter(config).export(search_results)
```

### 4. Quick Clipboard Copy

```python
from smart_search.export import copy_to_clipboard

# Copy as CSV
copy_to_clipboard(search_results, format="csv")

# Copy just the file paths
copy_to_clipboard(search_results, format="paths")
```

## Complete Example

```python
from pathlib import Path
from smart_search.search.engine import SearchEngine
from smart_search.export import (
    CSVExporter,
    ExcelExporter,
    HTMLExporter,
    copy_to_clipboard,
    ExportConfig
)

# 1. Search for files
engine = SearchEngine()
results = engine.search("*.pdf")

# 2. Export to multiple formats
output_dir = Path("exports")
output_dir.mkdir(exist_ok=True)

columns = ["filename", "size", "date_modified", "path"]

# CSV
csv_config = ExportConfig(
    output_path=output_dir / "pdfs.csv",
    columns=columns,
    overwrite=True
)
CSVExporter(csv_config).export(results)
print("✓ CSV exported")

# Excel
excel_config = ExportConfig(
    output_path=output_dir / "pdfs.xlsx",
    columns=columns,
    overwrite=True,
    options={"include_summary": True}
)
ExcelExporter(excel_config).export(results)
print("✓ Excel exported")

# HTML
html_config = ExportConfig(
    output_path=output_dir / "pdfs.html",
    columns=columns,
    overwrite=True,
    options={"theme": "auto", "sortable": True}
)
HTMLExporter(html_config).export(results)
print("✓ HTML exported")

# Clipboard
copy_to_clipboard(results, format="paths")
print("✓ Paths copied to clipboard")

print(f"\nAll exports in: {output_dir}")
```

## Common Patterns

### Progress Tracking

```python
def show_progress(current, total, message):
    print(f"\r{message}: {current}/{total}", end="")

config = ExportConfig(
    output_path=Path("results.csv"),
    progress_callback=show_progress
)
```

### Custom Formatting

```python
config = ExportConfig(
    output_path=Path("results.csv"),
    date_format="%d/%m/%Y",      # European date
    size_format="mb",             # Megabytes
    columns=["filename", "size", "date_modified"]
)
```

### Large Datasets

```python
config = ExportConfig(
    output_path=Path("big_export.csv"),
    use_batch=True,               # Process in batches
    batch_size=5000,              # 5000 records per batch
    max_results=100000            # Limit results
)
```

### Filter Before Export

```python
# Export only large files
large_files = [r for r in results if r.size > 100_000_000]

config = ExportConfig(
    output_path=Path("large_files.csv"),
    columns=["filename", "size", "path"],
    size_format="human"
)
CSVExporter(config).export(large_files)
```

## Available Columns

Choose from these columns:

- `filename` - File/folder name
- `path` - Parent directory
- `full_path` - Complete path
- `extension` - File extension (e.g., ".pdf")
- `size` - File size in bytes
- `date_created` - Creation date
- `date_modified` - Last modified date
- `date_accessed` - Last access date
- `is_folder` - True for folders
- `relevance_score` - Search relevance

## Format Options

### CSV Options

```python
options={
    "delimiter": ",",           # or "\t" for TSV
    "encoding": "utf-8-sig",    # BOM for Excel
    "excel_compatible": True
}
```

### Excel Options

```python
options={
    "split_by": "extension",    # None, "extension", "folder", "type"
    "include_summary": True,    # Statistics sheet
    "freeze_panes": True,       # Freeze header row
    "auto_filter": True,        # Enable filters
    "use_tables": True,         # Format as Excel table
    "add_hyperlinks": True      # Clickable paths
}
```

### HTML Options

```python
options={
    "title": "My Report",       # Page title
    "theme": "auto",            # "light", "dark", "auto"
    "sortable": True,           # Sortable columns
    "searchable": True,         # Search box
    "include_icons": True       # File type icons
}
```

### JSON Options

```python
options={
    "pretty": True,             # Pretty print
    "indent": 2,                # Indentation
    "include_metadata": True,   # Export metadata
    "sort_keys": True           # Sort object keys
}
```

## Troubleshooting

### Excel export fails

```bash
pip install openpyxl
```

### Clipboard not working

```bash
pip install pyperclip
```

### File exists error

Set `overwrite=True` in config:

```python
config = ExportConfig(
    output_path=Path("results.csv"),
    overwrite=True  # Replace existing file
)
```

## Next Steps

- Read [README.md](README.md) for complete documentation
- Check [examples.py](examples.py) for more examples
- Run tests: `pytest test_export.py -v`

## Getting Help

```python
# Get help on any exporter
help(CSVExporter)
help(ExcelExporter)
help(ExportConfig)
```
