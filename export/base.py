"""
Base exporter class with common functionality for all exporters.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    # For type checking, try to import SearchResult
    try:
        from ..search.engine import SearchResult
    except ImportError:
        SearchResult = Any
else:
    # At runtime, SearchResult can be any object with the expected attributes
    SearchResult = Any


@dataclass
class ExportConfig:
    """Configuration for export operations."""

    # Output settings
    output_path: Optional[Path] = None
    overwrite: bool = False

    # Column settings
    columns: List[str] = field(default_factory=lambda: [
        "filename", "path", "full_path", "extension", "size",
        "date_modified", "date_created", "is_folder"
    ])
    include_headers: bool = True

    # Filtering
    max_results: Optional[int] = None
    filter_empty: bool = False

    # Formatting
    date_format: str = "%Y-%m-%d %H:%M:%S"
    size_format: str = "human"  # "bytes", "human", "kb", "mb", "gb"

    # Batch processing
    batch_size: int = 1000
    use_batch: bool = False

    # Callbacks
    progress_callback: Optional[Callable[[int, int, str], None]] = None

    # Additional options (format-specific)
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportStats:
    """Statistics from an export operation."""

    total_records: int = 0
    exported_records: int = 0
    skipped_records: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    output_file: Optional[Path] = None
    output_size_bytes: int = 0

    def __str__(self) -> str:
        """Human-readable summary."""
        return (
            f"Export Stats:\n"
            f"  Total: {self.total_records}\n"
            f"  Exported: {self.exported_records}\n"
            f"  Skipped: {self.skipped_records}\n"
            f"  Errors: {self.errors}\n"
            f"  Duration: {self.duration_seconds:.2f}s\n"
            f"  Output: {self.output_file}\n"
            f"  Size: {self._format_size(self.output_size_bytes)}"
        )

    @staticmethod
    def _format_size(size: int) -> str:
        """Format size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"


class BaseExporter(ABC):
    """
    Abstract base class for all exporters.

    Provides common functionality:
    - Progress tracking and callbacks
    - Batch processing
    - Data formatting
    - Error handling
    - Statistics collection
    """

    def __init__(self, config: Optional[ExportConfig] = None):
        """
        Initialize exporter.

        Args:
            config: Export configuration
        """
        self.config = config or ExportConfig()
        self.stats = ExportStats()

    @abstractmethod
    def export(self, results: List[Any]) -> ExportStats:
        """
        Export search results.

        Args:
            results: List of search results to export

        Returns:
            Export statistics

        Raises:
            ExportError: If export fails
        """
        pass

    def _prepare_export(self, results: List[Any]) -> List[Any]:
        """
        Prepare results for export.

        Args:
            results: Raw search results

        Returns:
            Processed results ready for export
        """
        start_time = time.time()
        self.stats.total_records = len(results)

        # Apply max_results limit
        if self.config.max_results:
            results = results[: self.config.max_results]

        # Filter empty results
        if self.config.filter_empty:
            results = [r for r in results if r.filename and r.path]

        self.stats.duration_seconds = time.time() - start_time
        return results

    def _format_value(self, result: Any, column: str) -> Any:
        """
        Format a single value for export.

        Args:
            result: Search result
            column: Column name

        Returns:
            Formatted value
        """
        value = getattr(result, column, "")

        # Handle special formatting
        if column in ["date_created", "date_modified", "date_accessed"]:
            return self._format_date(value)
        elif column == "size":
            return self._format_size(value)
        elif column == "is_folder":
            return "Yes" if value else "No"

        return value

    def _format_date(self, timestamp: int) -> str:
        """
        Format timestamp to string.

        Args:
            timestamp: Unix timestamp

        Returns:
            Formatted date string
        """
        if not timestamp:
            return ""

        try:
            from datetime import datetime
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime(self.config.date_format)
        except (ValueError, OSError):
            return str(timestamp)

    def _format_size(self, size: int) -> Any:
        """
        Format file size.

        Args:
            size: Size in bytes

        Returns:
            Formatted size (string or int depending on config)
        """
        if not size:
            return 0

        format_type = self.config.size_format.lower()

        if format_type == "bytes":
            return size
        elif format_type == "human":
            return self._format_size_human(size)
        elif format_type == "kb":
            return size / 1024
        elif format_type == "mb":
            return size / (1024 ** 2)
        elif format_type == "gb":
            return size / (1024 ** 3)

        return size

    @staticmethod
    def _format_size_human(size: int) -> str:
        """
        Format size in human-readable format.

        Args:
            size: Size in bytes

        Returns:
            Human-readable size string
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def _report_progress(self, current: int, total: int, message: str = ""):
        """
        Report progress via callback if configured.

        Args:
            current: Current progress
            total: Total items
            message: Optional progress message
        """
        if self.config.progress_callback:
            try:
                self.config.progress_callback(current, total, message)
            except Exception:
                # Don't let callback errors break the export
                pass

    def _batch_process(
        self,
        results: List[Any],
        process_func: Callable[[List[Any]], None]
    ) -> None:
        """
        Process results in batches.

        Args:
            results: All results to process
            process_func: Function to process each batch
        """
        batch_size = self.config.batch_size
        total = len(results)

        for i in range(0, total, batch_size):
            batch = results[i: i + batch_size]
            process_func(batch)
            self._report_progress(
                min(i + batch_size, total),
                total,
                f"Processing batch {i // batch_size + 1}"
            )

    def _finalize_stats(self, output_path: Optional[Path] = None) -> ExportStats:
        """
        Finalize export statistics.

        Args:
            output_path: Path to output file

        Returns:
            Completed statistics
        """
        if output_path and output_path.exists():
            self.stats.output_file = output_path
            self.stats.output_size_bytes = output_path.stat().st_size

        return self.stats

    def _validate_output_path(self, output_path: Path) -> None:
        """
        Validate and prepare output path.

        Args:
            output_path: Destination path

        Raises:
            ValueError: If path is invalid
            FileExistsError: If file exists and overwrite is False
        """
        # Check if file exists
        if output_path.exists() and not self.config.overwrite:
            raise FileExistsError(
                f"Output file already exists: {output_path}. "
                "Set overwrite=True to replace."
            )

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)


class ExportError(Exception):
    """Base exception for export errors."""
    pass


class UnsupportedFormatError(ExportError):
    """Raised when export format is not supported."""
    pass


class ExportValidationError(ExportError):
    """Raised when export validation fails."""
    pass
