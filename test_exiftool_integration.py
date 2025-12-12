"""
Test ExifTool Integration
Test all ExifTool components and functionality.
"""

import os
import sys
import json
from pathlib import Path

# Set UTF-8 encoding for console output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.exiftool_wrapper import ExifToolWrapper
from tools.metadata_analyzer import MetadataAnalyzer
from tools.metadata_editor import MetadataEditor
from tools.forensic_report import ForensicReportGenerator


def test_exiftool_detection():
    """Test ExifTool detection and initialization"""
    print("=" * 80)
    print("TEST 1: ExifTool Detection")
    print("=" * 80)

    try:
        exiftool = ExifToolWrapper()
        print(f"[OK] ExifTool found at: {exiftool.exiftool_path}")
        print(f"[OK] Version: {exiftool.get_version()}")
        print(f"[OK] Available: {exiftool.is_available()}")
        return exiftool
    except RuntimeError as e:
        print(f"[FAIL] ExifTool not found: {e}")
        return None


def test_metadata_extraction(exiftool):
    """Test metadata extraction"""
    print("\n" + "=" * 80)
    print("TEST 2: Metadata Extraction")
    print("=" * 80)

    # Try to find a test file
    test_files = [
        r"C:\Users\ramos\Pictures\*.jpg",
        r"C:\Users\ramos\Downloads\*.jpg",
        r"C:\Windows\Web\Wallpaper\Windows\*.jpg"
    ]

    test_file = None
    import glob
    for pattern in test_files:
        matches = glob.glob(pattern)
        if matches:
            test_file = matches[0]
            break

    if not test_file:
        print("[WARN] No test image file found")
        return False

    print(f"Test file: {test_file}")

    try:
        # Extract metadata
        metadata = exiftool.extract_metadata(test_file)

        if metadata:
            print(f"[OK] Extracted {len(metadata)} metadata fields")
            print("\nSample fields:")
            for i, (key, value) in enumerate(list(metadata.items())[:10]):
                print(f"  {key}: {value}")
            if len(metadata) > 10:
                print(f"  ... and {len(metadata) - 10} more fields")
            return True
        else:
            print("[FAIL] No metadata extracted")
            return False

    except Exception as e:
        print(f"[FAIL] Error extracting metadata: {e}")
        return False


def test_forensic_analysis(exiftool):
    """Test forensic analysis"""
    print("\n" + "=" * 80)
    print("TEST 3: Forensic Analysis")
    print("=" * 80)

    # Find test file
    import glob
    test_file = None
    for pattern in [r"C:\Users\ramos\Pictures\*.jpg", r"C:\Windows\Web\Wallpaper\Windows\*.jpg"]:
        matches = glob.glob(pattern)
        if matches:
            test_file = matches[0]
            break

    if not test_file:
        print("[WARN] No test file found")
        return False

    print(f"Analyzing: {test_file}")

    try:
        analyzer = MetadataAnalyzer(exiftool)
        analysis = analyzer.analyze_file(test_file)

        print(f"[OK] Analysis complete")
        print(f"\nCamera Info: {len(analysis.get('camera_info', {}))} fields")
        print(f"GPS Info: {len(analysis.get('gps_info', {}))} fields")
        print(f"DateTime Info: {len(analysis.get('datetime_info', {}))} fields")
        print(f"Software Info: {len(analysis.get('software_info', {}))} fields")
        print(f"Anomalies: {len(analysis.get('anomalies', []))} detected")

        if analysis.get('camera_info'):
            print(f"\nCamera: {analysis['camera_info'].get('make', 'N/A')} {analysis['camera_info'].get('model', 'N/A')}")

        if analysis.get('gps_info', {}).get('coordinates'):
            print(f"GPS: {analysis['gps_info']['coordinates']}")

        return True

    except Exception as e:
        print(f"[FAIL] Error in forensic analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_report_generation(exiftool):
    """Test report generation"""
    print("\n" + "=" * 80)
    print("TEST 4: Report Generation")
    print("=" * 80)

    # Find test file
    import glob
    test_file = None
    for pattern in [r"C:\Users\ramos\Pictures\*.jpg", r"C:\Windows\Web\Wallpaper\Windows\*.jpg"]:
        matches = glob.glob(pattern)
        if matches:
            test_file = matches[0]
            break

    if not test_file:
        print("[WARN] No test file found")
        return False

    print(f"Generating report for: {test_file}")

    try:
        analyzer = MetadataAnalyzer(exiftool)
        report_gen = ForensicReportGenerator(exiftool, analyzer)

        # Generate HTML report
        html_report = report_gen.generate_file_report(test_file, 'html')
        print(f"[OK] HTML report generated ({len(html_report)} chars)")

        # Generate text report
        text_report = report_gen.generate_file_report(test_file, 'txt')
        print(f"[OK] Text report generated ({len(text_report)} chars)")

        # Generate JSON report
        json_report = report_gen.generate_file_report(test_file, 'json')
        print(f"[OK] JSON report generated ({len(json_report)} chars)")

        # Save sample HTML report
        output_dir = Path(__file__).parent / "tests"
        output_dir.mkdir(exist_ok=True)

        report_path = output_dir / "sample_forensic_report.html"
        report_gen.save_report(html_report, report_path)
        print(f"[OK] Sample report saved to: {report_path}")

        return True

    except Exception as e:
        print(f"[FAIL] Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metadata_editor(exiftool):
    """Test metadata editor (non-destructive)"""
    print("\n" + "=" * 80)
    print("TEST 5: Metadata Editor")
    print("=" * 80)

    try:
        editor = MetadataEditor(exiftool)
        print("[OK] MetadataEditor initialized")

        # Test template creation
        editor.create_template('test_template', {
            'Artist': 'Test Artist',
            'Copyright': 'Test Copyright'
        })

        templates = editor.get_templates()
        print(f"[OK] Template created: {list(templates.keys())}")

        return True

    except Exception as e:
        print(f"[FAIL] Error in metadata editor: {e}")
        return False


def test_supported_formats(exiftool):
    """Test supported formats listing"""
    print("\n" + "=" * 80)
    print("TEST 6: Supported Formats")
    print("=" * 80)

    try:
        formats = exiftool.get_supported_formats()
        print(f"[OK] ExifTool supports {len(formats)} file formats")
        print("\nSample formats:")
        for fmt in formats[:20]:
            print(f"  {fmt}")
        if len(formats) > 20:
            print(f"  ... and {len(formats) - 20} more")

        return True

    except Exception as e:
        print(f"[FAIL] Error getting formats: {e}")
        return False


def test_batch_operations(exiftool):
    """Test batch operations"""
    print("\n" + "=" * 80)
    print("TEST 7: Batch Operations")
    print("=" * 80)

    # Find multiple test files
    import glob
    test_files = []
    for pattern in [r"C:\Users\ramos\Pictures\*.jpg", r"C:\Windows\Web\Wallpaper\Windows\*.jpg"]:
        test_files.extend(glob.glob(pattern)[:3])

    if len(test_files) < 2:
        print("[WARN] Not enough test files for batch operations")
        return False

    print(f"Testing with {len(test_files)} files")

    try:
        # Batch metadata extraction
        metadata_map = exiftool.extract_metadata_batch(test_files)
        print(f"[OK] Batch extracted metadata from {len(metadata_map)} files")

        # Timeline creation
        analyzer = MetadataAnalyzer(exiftool)
        timeline = analyzer.create_timeline(test_files)
        print(f"[OK] Timeline created with {len(timeline)} events")

        return True

    except Exception as e:
        print(f"[FAIL] Error in batch operations: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("ExifTool Integration Test Suite")
    print("=" * 80)

    # Test 1: Detection
    exiftool = test_exiftool_detection()
    if not exiftool:
        print("\n[FAIL] FAILED: Cannot proceed without ExifTool")
        print("\nTo install ExifTool:")
        print("1. Download from: https://exiftool.org/")
        print("2. Extract to: D:\\MAIN_DATA_CENTER\\Dev_Tools\\ExifTool\\")
        print("3. Or add to your system PATH")
        return False

    # Run remaining tests
    results = {
        'Detection': True,
        'Metadata Extraction': test_metadata_extraction(exiftool),
        'Forensic Analysis': test_forensic_analysis(exiftool),
        'Report Generation': test_report_generation(exiftool),
        'Metadata Editor': test_metadata_editor(exiftool),
        'Supported Formats': test_supported_formats(exiftool),
        'Batch Operations': test_batch_operations(exiftool)
    }

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, passed in results.items():
        status = "[OK] PASSED" if passed else "[FAIL] FAILED"
        print(f"{test_name}: {status}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[OK] ALL TESTS PASSED!")
        return True
    else:
        print(f"\n[FAIL] {total - passed} TEST(S) FAILED")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
