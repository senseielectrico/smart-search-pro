"""
JSON exporter with pretty printing and minified options.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .base import BaseExporter, ExportConfig, ExportError, ExportStats
except ImportError:
    from base import BaseExporter, ExportConfig, ExportError, ExportStats

# Import security functions
try:
    from core.security import sanitize_json_value
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.security import sanitize_json_value


class JSONExporter(BaseExporter):
    """
    Export search results to JSON format.

    Features:
    - Pretty printing or minified output
    - Configurable indentation
    - Custom serialization for complex types
    - Metadata inclusion
    - JSON Lines format support
    - Schema validation (optional)
    """

    def __init__(self, config: Optional[ExportConfig] = None, indent: int = 2, **kwargs):
        """
        Initialize JSON exporter.

        Args:
            config: Export configuration
            indent: JSON indentation (default: 2)
            **kwargs: Additional options
        """
        # Handle direct keyword arguments
        if config is None:
            options = {"indent": indent, **kwargs}
            config = ExportConfig(options=options, overwrite=True)
        super().__init__(config)

        # JSON-specific options
        self.pretty = self.config.options.get("pretty", True)
        self.indent = indent if indent != 2 else self.config.options.get("indent", 2)
        self.include_metadata = self.config.options.get("include_metadata", True)
        self.jsonl = self.config.options.get("jsonl", False)  # JSON Lines format
        self.sort_keys = self.config.options.get("sort_keys", False)
        self.ensure_ascii = self.config.options.get("ensure_ascii", False)

    def export(self, results: List, output_path: Optional[str] = None) -> ExportStats:
        """
        Export results to JSON file.

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
            raise ExportError("Output path is required for JSON export")

        output_path = Path(self.config.output_path)
        self._validate_output_path(output_path)

        # Prepare results
        results = self._prepare_export(results)

        try:
            # Convert to JSON-serializable format
            data = self._convert_results(results)

            # Write to file
            with open(output_path, "w", encoding="utf-8") as f:
                if self.jsonl:
                    # JSON Lines format (one object per line)
                    for item in data if isinstance(data, list) else [data]:
                        f.write(json.dumps(item, ensure_ascii=self.ensure_ascii) + "\n")
                else:
                    # Standard JSON format
                    json.dump(
                        data,
                        f,
                        indent=self.indent if self.pretty else None,
                        sort_keys=self.sort_keys,
                        ensure_ascii=self.ensure_ascii,
                        default=self._json_serializer
                    )

            self.stats.exported_records = len(results)

        except Exception as e:
            self.stats.errors += 1
            raise ExportError(f"Failed to export JSON: {e}") from e

        finally:
            self.stats.duration_seconds = time.time() - start_time

        return self._finalize_stats(output_path)

    def export_to_string(self, results: List) -> str:
        """
        Export results to JSON string.

        Args:
            results: Results to export

        Returns:
            JSON formatted string
        """
        data = self._convert_results(results)

        return json.dumps(
            data,
            indent=self.indent if self.pretty else None,
            sort_keys=self.sort_keys,
            ensure_ascii=self.ensure_ascii,
            default=self._json_serializer
        )

    def _convert_results(self, results: List) -> Dict[str, Any]:
        """
        Convert results to JSON-serializable structure.

        Args:
            results: Search results

        Returns:
            Dictionary ready for JSON serialization
        """
        # Convert each result to dict
        items = []
        for result in results:
            item = {}
            for col in self.config.columns:
                value = self._format_value_for_json(result, col)
                # Sanitize value to prevent JSON injection
                value = sanitize_json_value(value)
                item[col] = value
            items.append(item)

        # Build final structure
        if self.include_metadata:
            return {
                "metadata": self._build_metadata(results),
                "results": items
            }
        else:
            return items

    def _format_value_for_json(self, result, column: str) -> Any:
        """
        Format a value for JSON serialization.

        Args:
            result: Search result
            column: Column name

        Returns:
            JSON-serializable value
        """
        value = self._get_attr(result, column, None)

        # Keep numeric timestamps for JSON (easier to parse)
        if column in ["date_created", "date_modified", "date_accessed"]:
            return value if value else None

        # Keep size as number
        if column == "size":
            return value if value else 0

        # Convert boolean
        if column == "is_folder":
            return bool(value)

        # Convert Path objects to strings
        if isinstance(value, Path):
            return str(value)

        return value

    def _build_metadata(self, results: List) -> Dict[str, Any]:
        """
        Build metadata section.

        Args:
            results: Search results

        Returns:
            Metadata dictionary
        """
        from datetime import datetime

        total_size = sum(self._get_attr(r, 'size', 0) for r in results if not self._get_attr(r, 'is_folder', False))

        return {
            "export_date": datetime.now().isoformat(),
            "total_results": len(results),
            "total_files": sum(1 for r in results if not self._get_attr(r, "is_folder", False)),
            "total_folders": sum(1 for r in results if self._get_attr(r, "is_folder", False)),
            "total_size_bytes": total_size,
            "columns": self.config.columns,
            "format_version": "1.0"
        }

    @staticmethod
    def _json_serializer(obj: Any) -> Any:
        """
        Custom JSON serializer for non-standard types.

        Args:
            obj: Object to serialize

        Returns:
            Serializable representation

        Raises:
            TypeError: If object is not serializable
        """
        if isinstance(obj, Path):
            return str(obj)
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        else:
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class CompactJSONExporter(JSONExporter):
    """
    Compact JSON exporter (minified output).

    Convenience class with compact defaults.
    """

    def __init__(self, config: Optional[ExportConfig] = None):
        """Initialize compact JSON exporter."""
        if config:
            config.options.setdefault("pretty", False)
            config.options.setdefault("indent", None)
        else:
            config = ExportConfig(options={"pretty": False, "indent": None})

        super().__init__(config)


class JSONLinesExporter(JSONExporter):
    """
    JSON Lines exporter (one JSON object per line).

    Useful for streaming processing and big data tools.
    """

    def __init__(self, config: Optional[ExportConfig] = None):
        """Initialize JSON Lines exporter."""
        if config:
            config.options.setdefault("jsonl", True)
            config.options.setdefault("include_metadata", False)
        else:
            config = ExportConfig(
                options={"jsonl": True, "include_metadata": False}
            )

        super().__init__(config)
