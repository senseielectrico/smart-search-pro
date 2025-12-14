"""
CSV exporter with configurable columns and encoding.
"""

import csv
import time
from pathlib import Path
from typing import List, Optional

try:
    from .base import BaseExporter, ExportConfig, ExportError, ExportStats
except ImportError:
    from base import BaseExporter, ExportConfig, ExportError, ExportStats

# Import security functions
try:
    from core.security import sanitize_csv_cell
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.security import sanitize_csv_cell


class CSVExporter(BaseExporter):
    """
    Export search results to CSV format.

    Features:
    - Configurable columns and delimiters
    - Multiple encoding options (UTF-8, UTF-16, ASCII)
    - Quote handling
    - Excel-compatible format option
    - Progress tracking
    - Batch writing for large datasets
    """

    def __init__(self, config: Optional[ExportConfig] = None, delimiter: str = ",", **kwargs):
        """
        Initialize CSV exporter.

        Args:
            config: Export configuration
            delimiter: CSV delimiter (default: comma)
            **kwargs: Additional options
        """
        # Handle direct keyword arguments
        if config is None:
            options = {"delimiter": delimiter, **kwargs}
            config = ExportConfig(options=options, overwrite=True)
        super().__init__(config)

        # CSV-specific options
        self.delimiter = delimiter if delimiter != "," else self.config.options.get("delimiter", ",")
        self.quotechar = self.config.options.get("quotechar", '"')
        self.encoding = self.config.options.get("encoding", "utf-8-sig")  # BOM for Excel
        self.line_terminator = self.config.options.get("line_terminator", "\n")
        self.excel_compatible = self.config.options.get("excel_compatible", True)

    def export(self, results: List, output_path: Optional[str] = None) -> ExportStats:
        """
        Export results to CSV file.

        Args:
            results: Search results to export
            output_path: Optional output file path (overrides config)

        Returns:
            Export statistics

        Raises:
            ExportError: If export fails
        """
        start_time = time.time()

        # Use provided output_path or fall back to config
        if output_path:
            self.config.output_path = Path(output_path)

        # Validate output path
        if not self.config.output_path:
            raise ExportError("Output path is required for CSV export")

        output_path = Path(self.config.output_path)
        self._validate_output_path(output_path)

        # Prepare results
        results = self._prepare_export(results)

        try:
            # Export to CSV
            if self.config.use_batch:
                self._export_batched(results, output_path)
            else:
                self._export_direct(results, output_path)

            self.stats.exported_records = len(results)

        except Exception as e:
            self.stats.errors += 1
            raise ExportError(f"Failed to export CSV: {e}") from e

        finally:
            self.stats.duration_seconds = time.time() - start_time

        return self._finalize_stats(output_path)

    def _export_direct(self, results: List, output_path: Path) -> None:
        """
        Export all results at once.

        Args:
            results: Results to export
            output_path: Destination file
        """
        with open(output_path, "w", newline="", encoding=self.encoding) as f:
            writer = self._create_writer(f)

            # Write header
            if self.config.include_headers:
                writer.writerow(self.config.columns)

            # Write data rows
            total = len(results)
            for i, result in enumerate(results):
                # Sanitize each cell to prevent CSV injection
                row = [
                    sanitize_csv_cell(self._format_value(result, col))
                    for col in self.config.columns
                ]
                writer.writerow(row)

                # Report progress periodically
                if i % 100 == 0:
                    self._report_progress(i + 1, total, "Writing CSV")

            self._report_progress(total, total, "CSV export complete")

    def _export_batched(self, results: List, output_path: Path) -> None:
        """
        Export results in batches for memory efficiency.

        Args:
            results: Results to export
            output_path: Destination file
        """
        with open(output_path, "w", newline="", encoding=self.encoding) as f:
            writer = self._create_writer(f)

            # Write header
            if self.config.include_headers:
                writer.writerow(self.config.columns)

            # Write batches
            def write_batch(batch: List) -> None:
                for result in batch:
                    # Sanitize each cell to prevent CSV injection
                    row = [
                        sanitize_csv_cell(self._format_value(result, col))
                        for col in self.config.columns
                    ]
                    writer.writerow(row)

            self._batch_process(results, write_batch)

    def _create_writer(self, file_handle):
        """
        Create CSV writer with appropriate settings.

        Args:
            file_handle: Open file handle

        Returns:
            CSV writer instance
        """
        if self.excel_compatible:
            return csv.writer(
                file_handle,
                dialect="excel",
                delimiter=self.delimiter,
                quotechar=self.quotechar,
                lineterminator=self.line_terminator,
            )
        else:
            return csv.writer(
                file_handle,
                delimiter=self.delimiter,
                quotechar=self.quotechar,
                quoting=csv.QUOTE_MINIMAL,
                lineterminator=self.line_terminator,
            )

    def export_to_string(self, results: List) -> str:
        """
        Export results to CSV string (for clipboard, etc.).

        Args:
            results: Results to export

        Returns:
            CSV formatted string
        """
        import io

        output = io.StringIO()
        writer = self._create_writer(output)

        # Write header
        if self.config.include_headers:
            writer.writerow(self.config.columns)

        # Write data
        for result in results:
            row = [self._format_value(result, col) for col in self.config.columns]
            writer.writerow(row)

        return output.getvalue()


class TSVExporter(CSVExporter):
    """
    Tab-separated values exporter.

    Convenience class that uses tab delimiter by default.
    """

    def __init__(self, config: Optional[ExportConfig] = None):
        """Initialize TSV exporter."""
        if config:
            config.options.setdefault("delimiter", "\t")
        else:
            config = ExportConfig(options={"delimiter": "\t"})

        super().__init__(config)
