"""
Forensic Report Generator - Comprehensive Metadata Reporting
Generate detailed forensic reports from file metadata.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from collections import defaultdict
import logging

from .exiftool_wrapper import ExifToolWrapper
from .metadata_analyzer import MetadataAnalyzer

logger = logging.getLogger(__name__)


class ForensicReportGenerator:
    """
    Generate comprehensive forensic reports from metadata analysis.
    """

    def __init__(
        self,
        exiftool: Optional[ExifToolWrapper] = None,
        analyzer: Optional[MetadataAnalyzer] = None
    ):
        """
        Initialize forensic report generator.

        Args:
            exiftool: ExifToolWrapper instance
            analyzer: MetadataAnalyzer instance
        """
        self.exiftool = exiftool or ExifToolWrapper()
        self.analyzer = analyzer or MetadataAnalyzer(self.exiftool)

    def generate_file_report(
        self,
        file_path: Union[str, Path],
        output_format: str = 'html'
    ) -> str:
        """
        Generate comprehensive forensic report for a single file.

        Args:
            file_path: Path to file
            output_format: Output format ('html', 'json', 'txt')

        Returns:
            Report content as string
        """
        file_path = str(file_path)

        # Analyze file
        analysis = self.analyzer.analyze_file(file_path)

        if output_format == 'html':
            return self._generate_html_report(file_path, analysis)
        elif output_format == 'json':
            return json.dumps(analysis, indent=2, default=str)
        elif output_format == 'txt':
            return self._generate_text_report(file_path, analysis)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def generate_batch_report(
        self,
        file_paths: List[Union[str, Path]],
        output_format: str = 'html'
    ) -> str:
        """
        Generate forensic report for multiple files.

        Args:
            file_paths: List of file paths
            output_format: Output format ('html', 'json', 'txt')

        Returns:
            Report content as string
        """
        file_paths = [str(p) for p in file_paths]

        # Analyze all files
        analyses = {}
        for file_path in file_paths:
            try:
                analyses[file_path] = self.analyzer.analyze_file(file_path)
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")

        if output_format == 'html':
            return self._generate_batch_html_report(analyses)
        elif output_format == 'json':
            return json.dumps(analyses, indent=2, default=str)
        elif output_format == 'txt':
            return self._generate_batch_text_report(analyses)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def generate_timeline_report(
        self,
        file_paths: List[Union[str, Path]],
        output_format: str = 'html'
    ) -> str:
        """
        Generate timeline report showing chronological file activity.

        Args:
            file_paths: List of file paths
            output_format: Output format ('html', 'json', 'txt')

        Returns:
            Report content as string
        """
        timeline = self.analyzer.create_timeline(file_paths)

        if output_format == 'html':
            return self._generate_timeline_html(timeline)
        elif output_format == 'json':
            return json.dumps(timeline, indent=2, default=str)
        elif output_format == 'txt':
            return self._generate_timeline_text(timeline)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def generate_device_report(
        self,
        file_paths: List[Union[str, Path]],
        output_format: str = 'html'
    ) -> str:
        """
        Generate report identifying devices used to create files.

        Args:
            file_paths: List of file paths
            output_format: Output format ('html', 'json', 'txt')

        Returns:
            Report content as string
        """
        # Group files by device fingerprint
        devices = defaultdict(list)

        for file_path in file_paths:
            file_path = str(file_path)
            try:
                analysis = self.analyzer.analyze_file(file_path)
                fingerprint = analysis.get('device_fingerprint', 'unknown')
                devices[fingerprint].append({
                    'path': file_path,
                    'camera_info': analysis.get('camera_info', {}),
                    'software_info': analysis.get('software_info', {})
                })
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")

        if output_format == 'html':
            return self._generate_device_html(devices)
        elif output_format == 'json':
            return json.dumps(dict(devices), indent=2, default=str)
        elif output_format == 'txt':
            return self._generate_device_text(devices)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def generate_gps_report(
        self,
        file_paths: List[Union[str, Path]],
        output_format: str = 'html'
    ) -> str:
        """
        Generate GPS location report with map coordinates.

        Args:
            file_paths: List of file paths
            output_format: Output format ('html', 'json', 'txt')

        Returns:
            Report content as string
        """
        locations = []

        for file_path in file_paths:
            file_path = str(file_path)
            try:
                analysis = self.analyzer.analyze_file(file_path)
                gps_info = analysis.get('gps_info', {})

                if gps_info and 'latitude' in gps_info:
                    locations.append({
                        'file': file_path,
                        'gps': gps_info
                    })
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")

        if output_format == 'html':
            return self._generate_gps_html(locations)
        elif output_format == 'json':
            return json.dumps(locations, indent=2, default=str)
        elif output_format == 'txt':
            return self._generate_gps_text(locations)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _generate_html_report(self, file_path: str, analysis: Dict) -> str:
        """Generate HTML report for single file."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Forensic Metadata Report - {os.path.basename(file_path)}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; border-bottom: 2px solid #ddd; padding-bottom: 5px; }}
        .section {{ margin: 20px 0; }}
        .info-grid {{ display: grid; grid-template-columns: 200px 1fr; gap: 10px; }}
        .info-label {{ font-weight: bold; color: #666; }}
        .info-value {{ color: #333; }}
        .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; }}
        .anomaly {{ background: #f8d7da; border-left: 4px solid #dc3545; padding: 10px; margin: 10px 0; }}
        .success {{ background: #d4edda; border-left: 4px solid #28a745; padding: 10px; margin: 10px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: bold; }}
        .metadata-key {{ font-family: monospace; color: #007bff; }}
        .metadata-value {{ font-family: monospace; color: #333; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Forensic Metadata Report</h1>
        <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>

        <div class="section">
            <h2>File Information</h2>
            <div class="info-grid">
                <div class="info-label">File Path:</div>
                <div class="info-value">{file_path}</div>
                <div class="info-label">File Name:</div>
                <div class="info-value">{os.path.basename(file_path)}</div>
                <div class="info-label">File Size:</div>
                <div class="info-value">{self._format_size(analysis.get('file_size', 0))}</div>
            </div>
        </div>
"""

        # Camera Information
        camera_info = analysis.get('camera_info', {})
        if camera_info:
            html += """
        <div class="section">
            <h2>Camera Information</h2>
            <div class="info-grid">
"""
            for key, value in camera_info.items():
                html += f"""
                <div class="info-label">{key.replace('_', ' ').title()}:</div>
                <div class="info-value">{value}</div>
"""
            html += """
            </div>
        </div>
"""

        # GPS Information
        gps_info = analysis.get('gps_info', {})
        if gps_info:
            html += """
        <div class="section">
            <h2>GPS Location</h2>
            <div class="info-grid">
"""
            for key, value in gps_info.items():
                if key == 'map_link':
                    html += f"""
                <div class="info-label">Map:</div>
                <div class="info-value"><a href="{value}" target="_blank">View on Google Maps</a></div>
"""
                elif key == 'osm_link':
                    html += f"""
                <div class="info-label">OpenStreetMap:</div>
                <div class="info-value"><a href="{value}" target="_blank">View on OSM</a></div>
"""
                else:
                    html += f"""
                <div class="info-label">{key.replace('_', ' ').title()}:</div>
                <div class="info-value">{value}</div>
"""
            html += """
            </div>
        </div>
"""

        # Date/Time Information
        datetime_info = analysis.get('datetime_info', {})
        if datetime_info:
            html += """
        <div class="section">
            <h2>Date/Time Information</h2>
            <div class="info-grid">
"""
            for key, value in datetime_info.items():
                if key != 'warning':
                    html += f"""
                <div class="info-label">{key.replace('_', ' ').title()}:</div>
                <div class="info-value">{value}</div>
"""
            if 'warning' in datetime_info:
                html += f"""
            </div>
            <div class="warning">{datetime_info['warning']}</div>
"""
            else:
                html += """
            </div>
"""
            html += """
        </div>
"""

        # Software Information
        software_info = analysis.get('software_info', {})
        if software_info:
            html += """
        <div class="section">
            <h2>Software Information</h2>
            <div class="info-grid">
"""
            for key, value in software_info.items():
                html += f"""
                <div class="info-label">{key.replace('_', ' ').title()}:</div>
                <div class="info-value">{value}</div>
"""
            html += """
            </div>
        </div>
"""

        # Anomalies
        anomalies = analysis.get('anomalies', [])
        if anomalies:
            html += """
        <div class="section">
            <h2>Detected Anomalies</h2>
"""
            for anomaly in anomalies:
                html += f"""
            <div class="anomaly">{anomaly}</div>
"""
            html += """
        </div>
"""

        # Device Fingerprint
        fingerprint = analysis.get('device_fingerprint', '')
        if fingerprint and fingerprint != 'unknown':
            html += f"""
        <div class="section">
            <h2>Device Fingerprint</h2>
            <div class="success">{fingerprint}</div>
        </div>
"""

        html += """
    </div>
</body>
</html>
"""
        return html

    def _generate_text_report(self, file_path: str, analysis: Dict) -> str:
        """Generate plain text report."""
        lines = [
            "=" * 80,
            "FORENSIC METADATA REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "FILE INFORMATION",
            "-" * 80,
            f"Path: {file_path}",
            f"Name: {os.path.basename(file_path)}",
            f"Size: {self._format_size(analysis.get('file_size', 0))}",
            ""
        ]

        # Camera info
        camera_info = analysis.get('camera_info', {})
        if camera_info:
            lines.append("CAMERA INFORMATION")
            lines.append("-" * 80)
            for key, value in camera_info.items():
                lines.append(f"{key.replace('_', ' ').title()}: {value}")
            lines.append("")

        # GPS info
        gps_info = analysis.get('gps_info', {})
        if gps_info:
            lines.append("GPS LOCATION")
            lines.append("-" * 80)
            for key, value in gps_info.items():
                lines.append(f"{key.replace('_', ' ').title()}: {value}")
            lines.append("")

        # Anomalies
        anomalies = analysis.get('anomalies', [])
        if anomalies:
            lines.append("DETECTED ANOMALIES")
            lines.append("-" * 80)
            for anomaly in anomalies:
                lines.append(f"- {anomaly}")
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def _generate_batch_html_report(self, analyses: Dict) -> str:
        """Generate HTML report for multiple files."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Batch Forensic Metadata Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
        .file-section {{ border: 1px solid #ddd; margin: 20px 0; padding: 15px; background: #fafafa; }}
        .file-section h3 {{ margin-top: 0; color: #007bff; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: bold; }}
        .summary {{ background: #e7f3ff; padding: 15px; margin: 20px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Batch Forensic Metadata Report</h1>
        <div class="summary">
            <strong>Total Files Analyzed:</strong> {len(analyses)}<br>
            <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
"""

        for file_path, analysis in analyses.items():
            html += f"""
        <div class="file-section">
            <h3>{os.path.basename(file_path)}</h3>
            <p><strong>Path:</strong> {file_path}</p>
"""

            # Add key information
            camera_info = analysis.get('camera_info', {})
            if camera_info.get('make'):
                html += f"<p><strong>Camera:</strong> {camera_info.get('make', '')} {camera_info.get('model', '')}</p>"

            gps_info = analysis.get('gps_info', {})
            if gps_info.get('coordinates'):
                html += f"<p><strong>Location:</strong> {gps_info['coordinates']} <a href=\"{gps_info.get('map_link', '')}\" target=\"_blank\">[Map]</a></p>"

            html += """
        </div>
"""

        html += """
    </div>
</body>
</html>
"""
        return html

    def _generate_batch_text_report(self, analyses: Dict) -> str:
        """Generate plain text report for multiple files."""
        lines = [
            "=" * 80,
            "BATCH FORENSIC METADATA REPORT",
            "=" * 80,
            f"Total Files: {len(analyses)}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            ""
        ]

        for file_path, analysis in analyses.items():
            lines.append(f"\nFILE: {os.path.basename(file_path)}")
            lines.append("-" * 80)
            lines.append(f"Path: {file_path}")

            camera_info = analysis.get('camera_info', {})
            if camera_info:
                lines.append(f"Camera: {camera_info.get('make', '')} {camera_info.get('model', '')}")

            gps_info = analysis.get('gps_info', {})
            if gps_info:
                lines.append(f"GPS: {gps_info.get('coordinates', 'N/A')}")

            lines.append("")

        return "\n".join(lines)

    def _generate_timeline_html(self, timeline: List[Dict]) -> str:
        """Generate HTML timeline report."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Timeline Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
        .timeline {{ border-left: 3px solid #007bff; padding-left: 20px; margin: 20px 0; }}
        .event {{ margin: 15px 0; padding: 10px; background: #f8f9fa; border-radius: 5px; }}
        .event-time {{ font-weight: bold; color: #007bff; }}
        .event-file {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Timeline Report</h1>
        <p>Total Events: {len(timeline)}</p>
        <div class="timeline">
"""

        for event in timeline:
            html += f"""
            <div class="event">
                <div class="event-time">{event['timestamp']}</div>
                <div><strong>{event['event']}</strong></div>
                <div class="event-file">{os.path.basename(event['file'])}</div>
            </div>
"""

        html += """
        </div>
    </div>
</body>
</html>
"""
        return html

    def _generate_timeline_text(self, timeline: List[Dict]) -> str:
        """Generate plain text timeline report."""
        lines = [
            "=" * 80,
            "TIMELINE REPORT",
            "=" * 80,
            f"Total Events: {len(timeline)}",
            ""
        ]

        for event in timeline:
            lines.append(f"{event['timestamp']} - {event['event']}")
            lines.append(f"  File: {os.path.basename(event['file'])}")
            lines.append("")

        return "\n".join(lines)

    def _generate_device_html(self, devices: Dict) -> str:
        """Generate HTML device identification report."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Device Identification Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
        .device {{ border: 1px solid #ddd; margin: 20px 0; padding: 15px; background: #fafafa; }}
        .device h3 {{ margin-top: 0; color: #007bff; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ padding: 5px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Device Identification Report</h1>
        <p>Total Devices: {len(devices)}</p>
"""

        for fingerprint, files in devices.items():
            html += f"""
        <div class="device">
            <h3>Device: {fingerprint}</h3>
            <p><strong>Files:</strong> {len(files)}</p>
            <ul>
"""
            for file_info in files[:10]:  # Show first 10
                html += f"""
                <li>{os.path.basename(file_info['path'])}</li>
"""
            if len(files) > 10:
                html += f"""
                <li><em>... and {len(files) - 10} more</em></li>
"""
            html += """
            </ul>
        </div>
"""

        html += """
    </div>
</body>
</html>
"""
        return html

    def _generate_device_text(self, devices: Dict) -> str:
        """Generate plain text device report."""
        lines = [
            "=" * 80,
            "DEVICE IDENTIFICATION REPORT",
            "=" * 80,
            f"Total Devices: {len(devices)}",
            ""
        ]

        for fingerprint, files in devices.items():
            lines.append(f"\nDevice: {fingerprint}")
            lines.append(f"Files: {len(files)}")
            lines.append("-" * 80)
            for file_info in files[:10]:
                lines.append(f"  - {os.path.basename(file_info['path'])}")
            if len(files) > 10:
                lines.append(f"  ... and {len(files) - 10} more")
            lines.append("")

        return "\n".join(lines)

    def _generate_gps_html(self, locations: List[Dict]) -> str:
        """Generate HTML GPS report."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>GPS Location Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
        .location {{ border: 1px solid #ddd; margin: 15px 0; padding: 15px; background: #fafafa; }}
        .location h4 {{ margin-top: 0; }}
        a {{ color: #007bff; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>GPS Location Report</h1>
        <p>Total Locations: {len(locations)}</p>
"""

        for loc in locations:
            gps = loc['gps']
            html += f"""
        <div class="location">
            <h4>{os.path.basename(loc['file'])}</h4>
            <p><strong>Coordinates:</strong> {gps.get('coordinates', 'N/A')}</p>
            <p><strong>Altitude:</strong> {gps.get('altitude', 'N/A')}</p>
            <p>
                <a href="{gps.get('map_link', '#')}" target="_blank">View on Google Maps</a> |
                <a href="{gps.get('osm_link', '#')}" target="_blank">View on OpenStreetMap</a>
            </p>
        </div>
"""

        html += """
    </div>
</body>
</html>
"""
        return html

    def _generate_gps_text(self, locations: List[Dict]) -> str:
        """Generate plain text GPS report."""
        lines = [
            "=" * 80,
            "GPS LOCATION REPORT",
            "=" * 80,
            f"Total Locations: {len(locations)}",
            ""
        ]

        for loc in locations:
            gps = loc['gps']
            lines.append(f"\nFile: {os.path.basename(loc['file'])}")
            lines.append("-" * 80)
            lines.append(f"Coordinates: {gps.get('coordinates', 'N/A')}")
            lines.append(f"Altitude: {gps.get('altitude', 'N/A')}")
            lines.append(f"Map Link: {gps.get('map_link', 'N/A')}")
            lines.append("")

        return "\n".join(lines)

    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def save_report(
        self,
        report_content: str,
        output_path: Union[str, Path],
        format_hint: Optional[str] = None
    ):
        """
        Save report to file.

        Args:
            report_content: Report content
            output_path: Output file path
            format_hint: Format hint ('html', 'json', 'txt') or None to auto-detect
        """
        output_path = str(output_path)

        # Determine format
        if format_hint:
            ext = format_hint
        else:
            _, ext = os.path.splitext(output_path)
            ext = ext.lstrip('.')

        # Set encoding
        encoding = 'utf-8'
        mode = 'w'

        # Write file
        with open(output_path, mode, encoding=encoding) as f:
            f.write(report_content)

        logger.info(f"Report saved to: {output_path}")
