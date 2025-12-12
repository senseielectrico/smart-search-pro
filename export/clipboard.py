"""
Clipboard exporter for quick copy-paste operations.
"""

from typing import List, Optional

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

try:
    from .base import BaseExporter, ExportConfig, ExportError, ExportStats
except ImportError:
    from base import BaseExporter, ExportConfig, ExportError, ExportStats

try:
    from .csv_exporter import CSVExporter
    from .json_exporter import JSONExporter
except ImportError:
    from csv_exporter import CSVExporter
    from json_exporter import JSONExporter



class ClipboardExporter(BaseExporter):
    """
    Export search results to clipboard in various formats.

    Features:
    - Multiple format support (CSV, TSV, JSON, text)
    - Configurable columns
    - Automatic format detection
    - Fallback to Windows clipboard API
    """

    def __init__(self, config: Optional[ExportConfig] = None):
        """
        Initialize clipboard exporter.

        Args:
            config: Export configuration

        Raises:
            ImportError: If clipboard support is not available
        """
        super().__init__(config)

        # Clipboard-specific options
        self.format = self.config.options.get("format", "csv")  # csv, tsv, json, text, paths
        self.separator = self.config.options.get("separator", "\n")

        # Check availability
        self._check_clipboard_support()

    def export(self, results: List) -> ExportStats:
        """
        Export results to clipboard.

        Args:
            results: Search results to export

        Returns:
            Export statistics

        Raises:
            ExportError: If export fails
        """
        import time
        start_time = time.time()

        # Prepare results
        results = self._prepare_export(results)

        try:
            # Generate content based on format
            content = self._generate_content(results)

            # Copy to clipboard
            self._copy_to_clipboard(content)

            self.stats.exported_records = len(results)

        except Exception as e:
            self.stats.errors += 1
            raise ExportError(f"Failed to copy to clipboard: {e}") from e

        finally:
            self.stats.duration_seconds = time.time() - start_time

        return self.stats

    def _generate_content(self, results: List) -> str:
        """
        Generate content based on format.

        Args:
            results: Search results

        Returns:
            Formatted string
        """
        format_lower = self.format.lower()

        if format_lower == "csv":
            return self._generate_csv(results)
        elif format_lower == "tsv":
            return self._generate_tsv(results)
        elif format_lower == "json":
            return self._generate_json(results)
        elif format_lower == "text":
            return self._generate_text(results)
        elif format_lower == "paths":
            return self._generate_paths(results)
        else:
            raise ExportError(f"Unsupported clipboard format: {self.format}")

    def _generate_csv(self, results: List) -> str:
        """Generate CSV format."""
        exporter = CSVExporter(self.config)
        return exporter.export_to_string(results)

    def _generate_tsv(self, results: List) -> str:
        """Generate TSV format."""
        from .csv_exporter import TSVExporter
        config = ExportConfig(
            columns=self.config.columns,
            include_headers=self.config.include_headers,
            options={"delimiter": "\t"}
        )
        exporter = TSVExporter(config)
        return exporter.export_to_string(results)

    def _generate_json(self, results: List) -> str:
        """Generate JSON format."""
        exporter = JSONExporter(self.config)
        return exporter.export_to_string(results)

    def _generate_text(self, results: List) -> str:
        """Generate plain text format."""
        lines = []

        # Add header if requested
        if self.config.include_headers:
            header = " | ".join(col.replace("_", " ").title() for col in self.config.columns)
            lines.append(header)
            lines.append("-" * len(header))

        # Add data rows
        for result in results:
            row_values = [str(self._format_value(result, col)) for col in self.config.columns]
            lines.append(" | ".join(row_values))

        return "\n".join(lines)

    def _generate_paths(self, results: List) -> str:
        """Generate simple list of paths."""
        paths = [result.full_path for result in results if result.full_path]
        return self.separator.join(paths)

    def _copy_to_clipboard(self, content: str) -> None:
        """
        Copy content to clipboard.

        Args:
            content: Text to copy

        Raises:
            ExportError: If copy fails
        """
        if PYPERCLIP_AVAILABLE:
            try:
                pyperclip.copy(content)
                return
            except Exception:
                pass  # Fall through to Windows API

        # Fallback to Windows API
        try:
            self._copy_to_clipboard_windows(content)
        except Exception as e:
            raise ExportError(f"Failed to access clipboard: {e}") from e

    @staticmethod
    def _copy_to_clipboard_windows(content: str) -> None:
        """
        Copy to clipboard using Windows API.

        Args:
            content: Text to copy

        Raises:
            ExportError: If copy fails
        """
        try:
            import win32clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(content, win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
        except ImportError:
            raise ExportError(
                "Clipboard support not available. "
                "Install pyperclip: pip install pyperclip"
            )

    def _check_clipboard_support(self) -> None:
        """
        Check if clipboard support is available.

        Raises:
            ExportError: If clipboard is not supported
        """
        if not PYPERCLIP_AVAILABLE:
            try:
                import win32clipboard  # noqa: F401
            except ImportError:
                raise ExportError(
                    "Clipboard support not available. "
                    "Install pyperclip: pip install pyperclip"
                )


def copy_to_clipboard(
    results: List,
    format: str = "csv",
    columns: Optional[List[str]] = None,
    include_headers: bool = True
) -> int:
    """
    Quick function to copy results to clipboard.

    Args:
        results: Search results to copy
        format: Output format (csv, tsv, json, text, paths)
        columns: Columns to include (None = all)
        include_headers: Include header row

    Returns:
        Number of results copied

    Raises:
        ExportError: If copy fails

    Example:
        >>> results = search_engine.search("*.txt")
        >>> copy_to_clipboard(results, format="paths")
        >>> # Now paste in any application
    """
    config = ExportConfig(
        columns=columns or [
            "filename", "path", "size", "date_modified"
        ],
        include_headers=include_headers,
        options={"format": format}
    )

    exporter = ClipboardExporter(config)
    stats = exporter.export(results)

    return stats.exported_records


def get_from_clipboard() -> str:
    """
    Get text from clipboard.

    Returns:
        Clipboard content

    Raises:
        ExportError: If clipboard access fails
    """
    if PYPERCLIP_AVAILABLE:
        try:
            return pyperclip.paste()
        except Exception:
            pass

    # Fallback to Windows API
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        try:
            data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
        finally:
            win32clipboard.CloseClipboard()
        return data
    except ImportError:
        raise ExportError(
            "Clipboard support not available. "
            "Install pyperclip: pip install pyperclip"
        )
