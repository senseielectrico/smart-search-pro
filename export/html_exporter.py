"""
HTML exporter with responsive design, sortable tables, and theming.
"""

import time
from pathlib import Path
from typing import List, Optional

try:
    from .base import BaseExporter, ExportConfig, ExportError, ExportStats
except ImportError:
    from base import BaseExporter, ExportConfig, ExportError, ExportStats

# Import security functions
try:
    from core.security import sanitize_html_output
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.security import sanitize_html_output


class HTMLExporter(BaseExporter):
    """
    Export search results to interactive HTML report.

    Features:
    - Responsive design (mobile-friendly)
    - Sortable tables with JavaScript
    - Dark/light theme toggle
    - File type icons
    - Summary statistics dashboard
    - Search/filter within results
    - Pagination for large datasets
    - Export to CSV from browser
    """

    def __init__(self, config: Optional[ExportConfig] = None, title: str = "Smart Search Results", **kwargs):
        """
        Initialize HTML exporter.

        Args:
            config: Export configuration
            title: HTML page title
            **kwargs: Additional options
        """
        # Handle direct keyword arguments
        if config is None:
            options = {"title": title, **kwargs}
            config = ExportConfig(options=options, overwrite=True)
        super().__init__(config)

        # HTML-specific options
        self.theme = self.config.options.get("theme", "auto")  # "light", "dark", "auto"
        self.include_icons = self.config.options.get("include_icons", True)
        self.sortable = self.config.options.get("sortable", True)
        self.searchable = self.config.options.get("searchable", True)
        self.paginate = self.config.options.get("paginate", True)
        self.page_size = self.config.options.get("page_size", 100)
        self.title = title if title != "Smart Search Results" else self.config.options.get("title", "Smart Search Results")

    def export(self, results: List, output_path: Optional[str] = None) -> ExportStats:
        """
        Export results to HTML file.

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
            raise ExportError("Output path is required for HTML export")

        output_path = Path(self.config.output_path)
        self._validate_output_path(output_path)

        # Prepare results
        results = self._prepare_export(results)

        try:
            # Generate HTML
            html_content = self._generate_html(results)

            # Write to file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            self.stats.exported_records = len(results)

        except Exception as e:
            self.stats.errors += 1
            raise ExportError(f"Failed to export HTML: {e}") from e

        finally:
            self.stats.duration_seconds = time.time() - start_time

        return self._finalize_stats(output_path)

    def _generate_html(self, results: List) -> str:
        """
        Generate complete HTML document.

        Args:
            results: Search results

        Returns:
            HTML string
        """
        # Calculate statistics
        stats = self._calculate_stats(results)

        # Build HTML sections
        html_parts = [
            self._html_header(),
            self._html_styles(),
            "</head><body>",
            self._html_navbar(stats),
            self._html_stats_dashboard(stats),
            self._html_controls() if self.searchable else "",
            self._html_table(results),
            self._html_footer(),
            self._html_scripts() if self.sortable or self.searchable else "",
            "</body></html>"
        ]

        return "\n".join(html_parts)

    def _html_header(self) -> str:
        """Generate HTML header."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>"""

    def _html_styles(self) -> str:
        """Generate CSS styles."""
        return """
    <style>
        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f5f5f5;
            --text-primary: #333333;
            --text-secondary: #666666;
            --border-color: #dddddd;
            --accent-color: #366092;
            --hover-color: #f0f0f0;
        }

        [data-theme="dark"] {
            --bg-primary: #1e1e1e;
            --bg-secondary: #2d2d2d;
            --text-primary: #e0e0e0;
            --text-secondary: #a0a0a0;
            --border-color: #404040;
            --accent-color: #5a9fd4;
            --hover-color: #333333;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg-secondary);
            color: var(--text-primary);
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .navbar {
            background-color: var(--bg-primary);
            border-bottom: 2px solid var(--accent-color);
            padding: 15px 0;
            margin-bottom: 20px;
        }

        .navbar h1 {
            font-size: 24px;
            color: var(--accent-color);
        }

        .theme-toggle {
            float: right;
            padding: 8px 16px;
            background-color: var(--accent-color);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }

        .stats-dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }

        .stat-card {
            background-color: var(--bg-primary);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid var(--accent-color);
        }

        .stat-label {
            font-size: 12px;
            color: var(--text-secondary);
            text-transform: uppercase;
            margin-bottom: 5px;
        }

        .stat-value {
            font-size: 28px;
            font-weight: bold;
            color: var(--text-primary);
        }

        .controls {
            background-color: var(--bg-primary);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }

        .search-box {
            width: 100%;
            padding: 10px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            font-size: 14px;
            background-color: var(--bg-secondary);
            color: var(--text-primary);
        }

        .table-container {
            background-color: var(--bg-primary);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        thead {
            background-color: var(--accent-color);
            color: white;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        th {
            padding: 12px;
            text-align: left;
            font-weight: 600;
            cursor: pointer;
            user-select: none;
        }

        th:hover {
            background-color: rgba(255,255,255,0.1);
        }

        th::after {
            content: ' ⇅';
            opacity: 0.3;
        }

        td {
            padding: 10px 12px;
            border-bottom: 1px solid var(--border-color);
        }

        tr:hover {
            background-color: var(--hover-color);
        }

        .file-icon {
            margin-right: 8px;
            font-size: 16px;
        }

        .folder-icon::before { content: "📁"; }
        .file-icon::before { content: "📄"; }
        .image-icon::before { content: "🖼️"; }
        .video-icon::before { content: "🎬"; }
        .audio-icon::before { content: "🎵"; }
        .archive-icon::before { content: "📦"; }
        .code-icon::before { content: "💻"; }

        .footer {
            text-align: center;
            padding: 20px;
            color: var(--text-secondary);
            font-size: 12px;
        }

        @media (max-width: 768px) {
            .stats-dashboard {
                grid-template-columns: 1fr;
            }

            table {
                font-size: 12px;
            }

            th, td {
                padding: 8px;
            }
        }
    </style>"""

    def _html_navbar(self, stats: dict) -> str:
        """Generate navigation bar."""
        return f"""
    <div class="navbar">
        <div class="container">
            <h1>{self.title}</h1>
            <button class="theme-toggle" onclick="toggleTheme()">🌓 Toggle Theme</button>
        </div>
    </div>"""

    def _html_stats_dashboard(self, stats: dict) -> str:
        """Generate statistics dashboard."""
        return f"""
    <div class="container">
        <div class="stats-dashboard">
            <div class="stat-card">
                <div class="stat-label">Total Results</div>
                <div class="stat-value">{stats['total']:,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Files</div>
                <div class="stat-value">{stats['files']:,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Folders</div>
                <div class="stat-value">{stats['folders']:,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Size</div>
                <div class="stat-value">{stats['total_size']}</div>
            </div>
        </div>
    </div>"""

    def _html_controls(self) -> str:
        """Generate search/filter controls."""
        return """
    <div class="container">
        <div class="controls">
            <input type="text" class="search-box" id="searchBox" placeholder="Search results...">
        </div>
    </div>"""

    def _html_table(self, results: List) -> str:
        """Generate results table."""
        # Build header
        header_cells = []
        for col in self.config.columns:
            label = col.replace("_", " ").title()
            header_cells.append(f"<th onclick='sortTable({len(header_cells)})'>{label}</th>")

        header = "<tr>" + "".join(header_cells) + "</tr>"

        # Build rows
        rows = []
        for result in results:
            cells = []
            for col in self.config.columns:
                value = self._format_value(result, col)

                # CRITICAL: HTML escape all values to prevent XSS
                value = sanitize_html_output(value)

                # Add icon for filename (icon class should be trusted/validated)
                if col == "filename" and self.include_icons:
                    icon_class = self._get_icon_class(result)
                    # Note: icon_class is internally generated, but we escape value
                    value = f'<span class="{icon_class}"></span>{value}'

                # Make path clickable (sanitized)
                if col == "full_path" and value:
                    # Value is already escaped, safe to use in href
                    value = f'<a href="file:///{value}" style="color: var(--accent-color);">{value}</a>'

                cells.append(f"<td>{value}</td>")

            rows.append("<tr>" + "".join(cells) + "</tr>")

        return f"""
    <div class="container">
        <div class="table-container">
            <table id="resultsTable">
                <thead>{header}</thead>
                <tbody>{"".join(rows)}</tbody>
            </table>
        </div>
    </div>"""

    def _html_footer(self) -> str:
        """Generate footer."""
        return f"""
    <div class="footer">
        <p>Generated by Smart Search Pro | {self.stats.exported_records if hasattr(self.stats, 'exported_records') else 0} results</p>
    </div>"""

    def _html_scripts(self) -> str:
        """Generate JavaScript."""
        return """
    <script>
        // Theme toggle
        function toggleTheme() {
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        }

        // Load saved theme
        const savedTheme = localStorage.getItem('theme') ||
            (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
        document.documentElement.setAttribute('data-theme', savedTheme);

        // Table sorting
        function sortTable(columnIndex) {
            const table = document.getElementById('resultsTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            const isNumeric = !isNaN(parseFloat(rows[0].cells[columnIndex].textContent));

            rows.sort((a, b) => {
                const aVal = a.cells[columnIndex].textContent.trim();
                const bVal = b.cells[columnIndex].textContent.trim();

                if (isNumeric) {
                    return parseFloat(aVal) - parseFloat(bVal);
                }
                return aVal.localeCompare(bVal);
            });

            rows.forEach(row => tbody.appendChild(row));
        }

        // Search functionality
        const searchBox = document.getElementById('searchBox');
        if (searchBox) {
            searchBox.addEventListener('input', function(e) {
                const searchTerm = e.target.value.toLowerCase();
                const rows = document.querySelectorAll('#resultsTable tbody tr');

                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                });
            });
        }
    </script>"""

    def _calculate_stats(self, results: List) -> dict:
        """Calculate summary statistics."""
        total_size = sum(self._get_attr(r, 'size', 0) for r in results if not self._get_attr(r, 'is_folder', False))

        return {
            "total": len(results),
            "files": sum(1 for r in results if not self._get_attr(r, "is_folder", False)),
            "folders": sum(1 for r in results if self._get_attr(r, "is_folder", False)),
            "total_size": self._format_size_human(total_size),
        }

    def _get_icon_class(self, result) -> str:
        """Get icon class for file type."""
        if self._get_attr(result, 'is_folder', False):
            return "folder-icon"

        ext = (self._get_attr(result, 'extension', '') or '').lower()

        if ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"]:
            return "image-icon"
        elif ext in [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"]:
            return "video-icon"
        elif ext in [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"]:
            return "audio-icon"
        elif ext in [".zip", ".rar", ".7z", ".tar", ".gz"]:
            return "archive-icon"
        elif ext in [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".go", ".rs"]:
            return "code-icon"

        return "file-icon"

    @staticmethod
    def _format_size_human(size: int) -> str:
        """Format size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
