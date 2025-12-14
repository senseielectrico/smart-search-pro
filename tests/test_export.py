"""
Tests for export module: CSV, JSON, HTML, Excel exporters
"""

import pytest
import os
import json
import csv


# ============================================================================
# CSV EXPORTER TESTS
# ============================================================================

class TestCSVExporter:
    """Tests for CSV exporter"""

    def test_csv_initialization(self, test_csv_exporter):
        """Test CSV exporter initialization"""
        assert test_csv_exporter is not None

    def test_export_to_csv(self, test_csv_exporter, sample_export_data, temp_dir):
        """Test exporting data to CSV"""
        output_file = os.path.join(temp_dir, "export.csv")

        test_csv_exporter.export(sample_export_data, output_file)

        assert os.path.exists(output_file)
        # Verify content
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == len(sample_export_data)

    def test_export_empty_data(self, test_csv_exporter, temp_dir):
        """Test exporting empty data"""
        output_file = os.path.join(temp_dir, "empty.csv")
        test_csv_exporter.export([], output_file)
        assert os.path.exists(output_file)

    def test_export_with_custom_delimiter(self, temp_dir, sample_export_data):
        """Test exporting with custom delimiter"""
        from export.csv_exporter import CSVExporter

        exporter = CSVExporter(delimiter=';')
        output_file = os.path.join(temp_dir, "custom_delim.csv")

        exporter.export(sample_export_data, output_file)
        assert os.path.exists(output_file)


# ============================================================================
# JSON EXPORTER TESTS
# ============================================================================

class TestJSONExporter:
    """Tests for JSON exporter"""

    def test_json_initialization(self, test_json_exporter):
        """Test JSON exporter initialization"""
        assert test_json_exporter is not None

    def test_export_to_json(self, test_json_exporter, sample_export_data, temp_dir):
        """Test exporting data to JSON"""
        output_file = os.path.join(temp_dir, "export.json")

        test_json_exporter.export(sample_export_data, output_file)

        assert os.path.exists(output_file)
        # Verify content
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert len(data) == len(sample_export_data)

    def test_export_with_indent(self, temp_dir, sample_export_data):
        """Test exporting with indentation"""
        from export.json_exporter import JSONExporter

        exporter = JSONExporter(indent=2)
        output_file = os.path.join(temp_dir, "indented.json")

        exporter.export(sample_export_data, output_file)
        assert os.path.exists(output_file)

    def test_export_empty_json(self, test_json_exporter, temp_dir):
        """Test exporting empty data to JSON"""
        output_file = os.path.join(temp_dir, "empty.json")
        test_json_exporter.export([], output_file)
        assert os.path.exists(output_file)


# ============================================================================
# HTML EXPORTER TESTS
# ============================================================================

class TestHTMLExporter:
    """Tests for HTML exporter"""

    def test_html_initialization(self, test_html_exporter):
        """Test HTML exporter initialization"""
        assert test_html_exporter is not None

    def test_export_to_html(self, test_html_exporter, sample_export_data, temp_dir):
        """Test exporting data to HTML"""
        output_file = os.path.join(temp_dir, "export.html")

        test_html_exporter.export(sample_export_data, output_file)

        assert os.path.exists(output_file)
        # Verify it's valid HTML
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '<html' in content.lower()
            assert '<table' in content.lower()

    def test_export_with_title(self, temp_dir, sample_export_data):
        """Test exporting with custom title"""
        from export.html_exporter import HTMLExporter

        exporter = HTMLExporter(title="Test Export Report")
        output_file = os.path.join(temp_dir, "titled.html")

        exporter.export(sample_export_data, output_file)
        assert os.path.exists(output_file)

        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'Test Export Report' in content

    def test_export_empty_html(self, test_html_exporter, temp_dir):
        """Test exporting empty data to HTML"""
        output_file = os.path.join(temp_dir, "empty.html")
        test_html_exporter.export([], output_file)
        assert os.path.exists(output_file)


# ============================================================================
# EXCEL EXPORTER TESTS
# ============================================================================

class TestExcelExporter:
    """Tests for Excel exporter"""

    def test_excel_exporter_available(self):
        """Test if Excel exporter is available"""
        try:
            from export.excel_exporter import ExcelExporter
            exporter = ExcelExporter()
            assert exporter is not None
        except ImportError:
            pytest.skip("openpyxl not installed")

    def test_export_to_excel(self, sample_export_data, temp_dir):
        """Test exporting data to Excel"""
        try:
            from export.excel_exporter import ExcelExporter
        except ImportError:
            pytest.skip("openpyxl not installed")

        exporter = ExcelExporter()
        output_file = os.path.join(temp_dir, "export.xlsx")

        exporter.export(sample_export_data, output_file)
        assert os.path.exists(output_file)


# ============================================================================
# BASE EXPORTER TESTS
# ============================================================================

class TestBaseExporter:
    """Tests for base exporter functionality"""

    def test_exporter_interface(self):
        """Test exporter interface"""
        from export.base import BaseExporter

        class TestExporter(BaseExporter):
            def export(self, data, output_path):
                with open(output_path, 'w') as f:
                    f.write("test")

        exporter = TestExporter()
        assert exporter is not None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
class TestExportIntegration:
    """Integration tests for export module"""

    def test_export_all_formats(self, sample_export_data, temp_dir):
        """Test exporting to all supported formats"""
        from export.csv_exporter import CSVExporter
        from export.json_exporter import JSONExporter
        from export.html_exporter import HTMLExporter

        formats = {
            'csv': CSVExporter(),
            'json': JSONExporter(),
            'html': HTMLExporter()
        }

        for fmt, exporter in formats.items():
            output_file = os.path.join(temp_dir, f"export.{fmt}")
            exporter.export(sample_export_data, output_file)
            assert os.path.exists(output_file)
            assert os.path.getsize(output_file) > 0

    def test_export_large_dataset(self, temp_dir):
        """Test exporting large dataset"""
        from export.json_exporter import JSONExporter
        from datetime import datetime

        # Create large dataset
        large_data = [
            {
                'id': i,
                'filename': f'file_{i}.txt',
                'path': f'/test/path_{i}',
                'size': i * 1024,
                'modified': datetime.now().isoformat()
            }
            for i in range(1000)
        ]

        exporter = JSONExporter()
        output_file = os.path.join(temp_dir, "large_export.json")
        exporter.export(large_data, output_file)

        assert os.path.exists(output_file)
        with open(output_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
            # JSON export includes metadata and results keys
            results = loaded.get('results', loaded) if isinstance(loaded, dict) else loaded
            assert len(results) == 1000

    def test_export_with_special_characters(self, temp_dir):
        """Test exporting data with special characters"""
        from export.csv_exporter import CSVExporter

        data = [
            {
                'filename': 'test,file.txt',  # Comma
                'path': '/test/path"with"quotes',  # Quotes
                'content': 'Line 1\nLine 2'  # Newlines
            }
        ]

        exporter = CSVExporter()
        output_file = os.path.join(temp_dir, "special_chars.csv")
        exporter.export(data, output_file)

        assert os.path.exists(output_file)
        # Verify data can be read back
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
