"""
Validation script for export module.

Run this to verify the export module is working correctly.
"""

import sys
import os
from pathlib import Path
from typing import List

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_sample_results():
    """Create sample search results for testing."""
    from search.engine import SearchResult

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
            filename="script.py",
            path="C:\\Users\\test\\Code",
            full_path="C:\\Users\\test\\Code\\script.py",
            extension=".py",
            size=5120,
            date_modified=1700000200,
            date_created=1700000200,
            is_folder=False,
            relevance_score=0.90
        ),
        SearchResult(
            filename="Projects",
            path="C:\\Users\\test",
            full_path="C:\\Users\\test\\Projects",
            extension="",
            size=0,
            date_modified=1700000300,
            date_created=1700000300,
            is_folder=True,
            relevance_score=0.75
        ),
    ]


def validate_imports():
    """Validate all imports work."""
    print("Validating imports...")

    try:
        from export import (
            BaseExporter,
            ExportConfig,
            ExportStats,
            CSVExporter,
            ExcelExporter,
            HTMLExporter,
            JSONExporter,
            ClipboardExporter,
            copy_to_clipboard,
        )
        print("  ✓ All imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def validate_csv_export():
    """Validate CSV export."""
    print("\nValidating CSV export...")

    try:
        from export import CSVExporter, ExportConfig
        import tempfile

        results = create_sample_results()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"

            config = ExportConfig(
                output_path=output_path,
                columns=["filename", "size", "path"],
                overwrite=True
            )

            exporter = CSVExporter(config)
            stats = exporter.export(results)

            if stats.exported_records == 4 and output_path.exists():
                print(f"  ✓ CSV export successful ({stats.exported_records} records)")
                return True
            else:
                print(f"  ✗ CSV export failed (exported {stats.exported_records})")
                return False

    except Exception as e:
        print(f"  ✗ CSV export error: {e}")
        return False


def validate_excel_export():
    """Validate Excel export."""
    print("\nValidating Excel export...")

    try:
        from export import ExcelExporter, ExportConfig
        import tempfile

        results = create_sample_results()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.xlsx"

            config = ExportConfig(
                output_path=output_path,
                columns=["filename", "size", "extension"],
                overwrite=True,
                options={"include_summary": True}
            )

            exporter = ExcelExporter(config)
            stats = exporter.export(results)

            if stats.exported_records == 4 and output_path.exists():
                print(f"  ✓ Excel export successful ({stats.exported_records} records)")
                return True
            else:
                print(f"  ✗ Excel export failed")
                return False

    except ImportError:
        print("  ⚠ Excel export skipped (openpyxl not installed)")
        print("    Install with: pip install openpyxl")
        return True  # Not a failure, just missing optional dependency
    except Exception as e:
        print(f"  ✗ Excel export error: {e}")
        return False


def validate_html_export():
    """Validate HTML export."""
    print("\nValidating HTML export...")

    try:
        from export import HTMLExporter, ExportConfig
        import tempfile

        results = create_sample_results()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.html"

            config = ExportConfig(
                output_path=output_path,
                columns=["filename", "size", "path"],
                overwrite=True,
                options={"theme": "light", "sortable": True}
            )

            exporter = HTMLExporter(config)
            stats = exporter.export(results)

            if stats.exported_records == 4 and output_path.exists():
                content = output_path.read_text(encoding="utf-8")
                if "<!DOCTYPE html>" in content and "document.pdf" in content:
                    print(f"  ✓ HTML export successful ({stats.exported_records} records)")
                    return True

        print("  ✗ HTML export failed")
        return False

    except Exception as e:
        print(f"  ✗ HTML export error: {e}")
        return False


def validate_json_export():
    """Validate JSON export."""
    print("\nValidating JSON export...")

    try:
        from export import JSONExporter, ExportConfig
        import tempfile
        import json

        results = create_sample_results()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"

            config = ExportConfig(
                output_path=output_path,
                columns=["filename", "size", "is_folder"],
                overwrite=True,
                options={"pretty": True, "include_metadata": True}
            )

            exporter = JSONExporter(config)
            stats = exporter.export(results)

            if stats.exported_records == 4 and output_path.exists():
                # Verify JSON is valid
                data = json.loads(output_path.read_text(encoding="utf-8"))
                if "metadata" in data and "results" in data:
                    print(f"  ✓ JSON export successful ({stats.exported_records} records)")
                    return True

        print("  ✗ JSON export failed")
        return False

    except Exception as e:
        print(f"  ✗ JSON export error: {e}")
        return False


def validate_clipboard():
    """Validate clipboard functionality."""
    print("\nValidating clipboard export...")

    try:
        from export import ClipboardExporter, ExportConfig

        results = create_sample_results()

        config = ExportConfig(
            columns=["filename", "size"],
            options={"format": "csv"}
        )

        exporter = ClipboardExporter(config)

        # Just test content generation, not actual clipboard copy
        content = exporter._generate_content(results)

        if len(content) > 0 and "document.pdf" in content:
            print("  ✓ Clipboard export successful")
            return True
        else:
            print("  ✗ Clipboard export failed")
            return False

    except ImportError:
        print("  ⚠ Clipboard export skipped (pyperclip not installed)")
        print("    Install with: pip install pyperclip")
        return True  # Not a failure
    except Exception as e:
        print(f"  ✗ Clipboard export error: {e}")
        return False


def validate_export_config():
    """Validate ExportConfig functionality."""
    print("\nValidating ExportConfig...")

    try:
        from export.base import ExportConfig

        # Test default config
        config1 = ExportConfig()
        assert config1.overwrite is False
        assert config1.include_headers is True

        # Test custom config
        config2 = ExportConfig(
            output_path=Path("test.csv"),
            columns=["filename", "size"],
            overwrite=True,
            options={"delimiter": "\t"}
        )
        assert config2.output_path == Path("test.csv")
        assert config2.overwrite is True
        assert config2.options["delimiter"] == "\t"

        print("  ✓ ExportConfig validation successful")
        return True

    except Exception as e:
        print(f"  ✗ ExportConfig validation error: {e}")
        return False


def validate_export_stats():
    """Validate ExportStats functionality."""
    print("\nValidating ExportStats...")

    try:
        from export.base import ExportStats

        stats = ExportStats(
            total_records=100,
            exported_records=95,
            skipped_records=3,
            errors=2,
            duration_seconds=1.5
        )

        assert stats.total_records == 100
        assert stats.exported_records == 95

        # Test string representation
        stats_str = str(stats)
        assert "Total: 100" in stats_str

        print("  ✓ ExportStats validation successful")
        return True

    except Exception as e:
        print(f"  ✗ ExportStats validation error: {e}")
        return False


def run_all_validations():
    """Run all validation checks."""
    print("=" * 60)
    print("Export Module Validation")
    print("=" * 60)

    results = {
        "Imports": validate_imports(),
        "ExportConfig": validate_export_config(),
        "ExportStats": validate_export_stats(),
        "CSV Export": validate_csv_export(),
        "Excel Export": validate_excel_export(),
        "HTML Export": validate_html_export(),
        "JSON Export": validate_json_export(),
        "Clipboard": validate_clipboard(),
    }

    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:20s} {status}")

    print("=" * 60)
    print(f"Result: {passed}/{total} checks passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All validations passed! Export module is ready to use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} validation(s) failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_validations())
