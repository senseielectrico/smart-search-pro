"""
Export module for Smart Search Pro.

Provides various export formats for search results:
- CSV: Simple tabular export
- Excel: Multi-sheet workbooks with formatting
- HTML: Interactive reports with sorting and theming
- JSON: Structured data export
- Clipboard: Quick copy to clipboard

All exporters support progress callbacks and batch operations.
"""

from .base import BaseExporter, ExportConfig, ExportStats
from .csv_exporter import CSVExporter
from .excel_exporter import ExcelExporter
from .html_exporter import HTMLExporter
from .json_exporter import JSONExporter
from .clipboard import ClipboardExporter, copy_to_clipboard

__all__ = [
    # Base classes
    "BaseExporter",
    "ExportConfig",
    "ExportStats",

    # Exporters
    "CSVExporter",
    "ExcelExporter",
    "HTMLExporter",
    "JSONExporter",
    "ClipboardExporter",

    # Utilities
    "copy_to_clipboard",
]

__version__ = "1.0.0"
