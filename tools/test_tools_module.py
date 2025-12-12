"""
Comprehensive Test Suite for Smart Search Tools Module
Tests all components: ExifToolWrapper, FileDecryptor, FileUnlocker, MetadataAnalyzer
"""

import sys
import os
import tempfile
import logging
from pathlib import Path
from typing import Dict, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ToolsModuleTester:
    """
    Test suite for verifying tools module functionality.
    """

    def __init__(self):
        self.results: Dict[str, Dict] = {}
        self.temp_dir = tempfile.mkdtemp(prefix='smart_search_test_')
        logger.info(f"Temporary test directory: {self.temp_dir}")

    def run_all_tests(self) -> Dict[str, Dict]:
        """
        Run all tests and return results.

        Returns:
            Dictionary of test results
        """
        logger.info("=" * 70)
        logger.info("SMART SEARCH TOOLS MODULE - COMPREHENSIVE TEST SUITE")
        logger.info("=" * 70)

        # Test imports
        self.test_imports()

        # Test individual components
        self.test_exiftool_wrapper()
        self.test_file_decryptor()
        self.test_file_unlocker()
        self.test_metadata_analyzer()

        # Print summary
        self.print_summary()

        return self.results

    def test_imports(self):
        """Test that all modules can be imported."""
        logger.info("\n[1/5] Testing Module Imports...")

        test_name = "imports"
        self.results[test_name] = {
            'passed': 0,
            'failed': 0,
            'errors': [],
            'details': []
        }

        # Test individual imports
        imports_to_test = [
            ('ExifToolWrapper', 'from tools.exiftool_wrapper import ExifToolWrapper'),
            ('FileDecryptor', 'from tools.file_decryptor import FileDecryptor'),
            ('FileUnlocker', 'from tools.file_unlocker import FileUnlocker'),
            ('MetadataAnalyzer', 'from tools.metadata_analyzer import MetadataAnalyzer'),
            ('PermissionFixer', 'from tools.permission_fixer import PermissionFixer'),
            ('CADFileHandler', 'from tools.cad_file_handler import CADFileHandler'),
            ('MetadataEditor', 'from tools.metadata_editor import MetadataEditor'),
            ('ForensicReportGenerator', 'from tools.forensic_report import ForensicReportGenerator'),
        ]

        for name, import_statement in imports_to_test:
            try:
                exec(import_statement)
                self.results[test_name]['passed'] += 1
                self.results[test_name]['details'].append(f"✓ {name} imported successfully")
                logger.info(f"  ✓ {name} imported successfully")
            except ImportError as e:
                self.results[test_name]['failed'] += 1
                error_msg = f"✗ {name} import failed: {e}"
                self.results[test_name]['errors'].append(error_msg)
                self.results[test_name]['details'].append(error_msg)
                logger.error(f"  ✗ {name} import failed: {e}")
            except Exception as e:
                self.results[test_name]['failed'] += 1
                error_msg = f"✗ {name} unexpected error: {e}"
                self.results[test_name]['errors'].append(error_msg)
                self.results[test_name]['details'].append(error_msg)
                logger.error(f"  ✗ {name} unexpected error: {e}")

        # Test package-level import
        try:
            from tools import (
                FileUnlocker,
                FileDecryptor,
                ExifToolWrapper,
                MetadataAnalyzer
            )
            self.results[test_name]['passed'] += 1
            self.results[test_name]['details'].append("✓ Package-level imports successful")
            logger.info("  ✓ Package-level imports successful")
        except Exception as e:
            self.results[test_name]['failed'] += 1
            error_msg = f"✗ Package-level import failed: {e}"
            self.results[test_name]['errors'].append(error_msg)
            self.results[test_name]['details'].append(error_msg)
            logger.error(f"  ✗ Package-level import failed: {e}")

    def test_exiftool_wrapper(self):
        """Test ExifToolWrapper functionality."""
        logger.info("\n[2/5] Testing ExifToolWrapper...")

        test_name = "exiftool_wrapper"
        self.results[test_name] = {
            'passed': 0,
            'failed': 0,
            'errors': [],
            'details': []
        }

        try:
            from tools.exiftool_wrapper import ExifToolWrapper

            # Test initialization
            try:
                wrapper = ExifToolWrapper()
                self.results[test_name]['passed'] += 1
                self.results[test_name]['details'].append("✓ ExifToolWrapper initialized")
                logger.info("  ✓ ExifToolWrapper initialized")
            except RuntimeError as e:
                self.results[test_name]['failed'] += 1
                error_msg = f"✗ ExifTool not found: {e}"
                self.results[test_name]['errors'].append(error_msg)
                self.results[test_name]['details'].append(error_msg)
                logger.error(f"  ✗ ExifTool not found: {e}")
                return  # Skip remaining tests if ExifTool not available

            # Test version check
            try:
                version = wrapper.get_version()
                self.results[test_name]['passed'] += 1
                self.results[test_name]['details'].append(f"✓ ExifTool version: {version}")
                logger.info(f"  ✓ ExifTool version: {version}")
            except Exception as e:
                self.results[test_name]['failed'] += 1
                error_msg = f"✗ Version check failed: {e}"
                self.results[test_name]['errors'].append(error_msg)
                self.results[test_name]['details'].append(error_msg)
                logger.error(f"  ✗ Version check failed: {e}")

            # Test availability check
            try:
                is_available = wrapper.is_available()
                if is_available:
                    self.results[test_name]['passed'] += 1
                    self.results[test_name]['details'].append("✓ ExifTool is available")
                    logger.info("  ✓ ExifTool is available")
                else:
                    self.results[test_name]['failed'] += 1
                    error_msg = "✗ ExifTool not available"
                    self.results[test_name]['errors'].append(error_msg)
                    self.results[test_name]['details'].append(error_msg)
                    logger.error("  ✗ ExifTool not available")
            except Exception as e:
                self.results[test_name]['failed'] += 1
                error_msg = f"✗ Availability check failed: {e}"
                self.results[test_name]['errors'].append(error_msg)
                self.results[test_name]['details'].append(error_msg)
                logger.error(f"  ✗ Availability check failed: {e}")

            # Test metadata extraction on test file
            test_file = self._create_test_file("test.txt", "Test content")
            try:
                metadata = wrapper.extract_metadata(test_file)
                if metadata:
                    self.results[test_name]['passed'] += 1
                    self.results[test_name]['details'].append(
                        f"✓ Metadata extraction successful ({len(metadata)} fields)"
                    )
                    logger.info(f"  ✓ Metadata extraction successful ({len(metadata)} fields)")
                else:
                    # Empty metadata is OK for text files
                    self.results[test_name]['passed'] += 1
                    self.results[test_name]['details'].append("✓ Metadata extraction returned empty (expected for text file)")
                    logger.info("  ✓ Metadata extraction returned empty (expected for text file)")
            except Exception as e:
                self.results[test_name]['failed'] += 1
                error_msg = f"✗ Metadata extraction failed: {e}"
                self.results[test_name]['errors'].append(error_msg)
                self.results[test_name]['details'].append(error_msg)
                logger.error(f"  ✗ Metadata extraction failed: {e}")

        except Exception as e:
            self.results[test_name]['failed'] += 1
            error_msg = f"✗ ExifToolWrapper test failed: {e}"
            self.results[test_name]['errors'].append(error_msg)
            self.results[test_name]['details'].append(error_msg)
            logger.error(f"  ✗ ExifToolWrapper test failed: {e}")

    def test_file_decryptor(self):
        """Test FileDecryptor functionality."""
        logger.info("\n[3/5] Testing FileDecryptor...")

        test_name = "file_decryptor"
        self.results[test_name] = {
            'passed': 0,
            'failed': 0,
            'errors': [],
            'details': []
        }

        try:
            from tools.file_decryptor import FileDecryptor

            # Test initialization
            try:
                decryptor = FileDecryptor()
                self.results[test_name]['passed'] += 1
                self.results[test_name]['details'].append("✓ FileDecryptor initialized")
                logger.info("  ✓ FileDecryptor initialized")
            except Exception as e:
                self.results[test_name]['failed'] += 1
                error_msg = f"✗ Initialization failed: {e}"
                self.results[test_name]['errors'].append(error_msg)
                self.results[test_name]['details'].append(error_msg)
                logger.error(f"  ✗ Initialization failed: {e}")
                return

            # Test encryption detection on non-encrypted file
            test_file = self._create_test_file("test_decrypt.txt", "Not encrypted")
            try:
                result = decryptor.detect_encryption(test_file)
                if 'encrypted' in result:
                    self.results[test_name]['passed'] += 1
                    self.results[test_name]['details'].append(
                        f"✓ Encryption detection works (encrypted: {result['encrypted']})"
                    )
                    logger.info(f"  ✓ Encryption detection works (encrypted: {result['encrypted']})")
                else:
                    self.results[test_name]['failed'] += 1
                    error_msg = "✗ Encryption detection returned unexpected format"
                    self.results[test_name]['errors'].append(error_msg)
                    self.results[test_name]['details'].append(error_msg)
                    logger.error("  ✗ Encryption detection returned unexpected format")
            except Exception as e:
                self.results[test_name]['failed'] += 1
                error_msg = f"✗ Encryption detection failed: {e}"
                self.results[test_name]['errors'].append(error_msg)
                self.results[test_name]['details'].append(error_msg)
                logger.error(f"  ✗ Encryption detection failed: {e}")

            # Test context manager
            try:
                with FileDecryptor() as decryptor_cm:
                    self.results[test_name]['passed'] += 1
                    self.results[test_name]['details'].append("✓ Context manager works")
                    logger.info("  ✓ Context manager works")
            except Exception as e:
                self.results[test_name]['failed'] += 1
                error_msg = f"✗ Context manager failed: {e}"
                self.results[test_name]['errors'].append(error_msg)
                self.results[test_name]['details'].append(error_msg)
                logger.error(f"  ✗ Context manager failed: {e}")

        except Exception as e:
            self.results[test_name]['failed'] += 1
            error_msg = f"✗ FileDecryptor test failed: {e}"
            self.results[test_name]['errors'].append(error_msg)
            self.results[test_name]['details'].append(error_msg)
            logger.error(f"  ✗ FileDecryptor test failed: {e}")

    def test_file_unlocker(self):
        """Test FileUnlocker functionality."""
        logger.info("\n[4/5] Testing FileUnlocker...")

        test_name = "file_unlocker"
        self.results[test_name] = {
            'passed': 0,
            'failed': 0,
            'errors': [],
            'details': []
        }

        try:
            from tools.file_unlocker import FileUnlocker

            # Test initialization
            try:
                unlocker = FileUnlocker()
                self.results[test_name]['passed'] += 1
                self.results[test_name]['details'].append("✓ FileUnlocker initialized")
                logger.info("  ✓ FileUnlocker initialized")
            except Exception as e:
                self.results[test_name]['failed'] += 1
                error_msg = f"✗ Initialization failed: {e}"
                self.results[test_name]['errors'].append(error_msg)
                self.results[test_name]['details'].append(error_msg)
                logger.error(f"  ✗ Initialization failed: {e}")
                return

            # Test admin check
            try:
                is_admin = unlocker.is_admin()
                self.results[test_name]['passed'] += 1
                self.results[test_name]['details'].append(
                    f"✓ Admin check works (is_admin: {is_admin})"
                )
                logger.info(f"  ✓ Admin check works (is_admin: {is_admin})")

                if not is_admin:
                    logger.warning("  ⚠ Not running as admin - some features will be limited")
                    self.results[test_name]['details'].append(
                        "⚠ Not running as admin - some features will be limited"
                    )
            except Exception as e:
                self.results[test_name]['failed'] += 1
                error_msg = f"✗ Admin check failed: {e}"
                self.results[test_name]['errors'].append(error_msg)
                self.results[test_name]['details'].append(error_msg)
                logger.error(f"  ✗ Admin check failed: {e}")

            # Test attribute removal on test file
            test_file = self._create_test_file("test_unlock.txt", "Test content")
            try:
                result = unlocker.remove_file_attributes(test_file)
                self.results[test_name]['passed'] += 1
                self.results[test_name]['details'].append(
                    f"✓ Attribute removal works (result: {result})"
                )
                logger.info(f"  ✓ Attribute removal works (result: {result})")
            except Exception as e:
                self.results[test_name]['failed'] += 1
                error_msg = f"✗ Attribute removal failed: {e}"
                self.results[test_name]['errors'].append(error_msg)
                self.results[test_name]['details'].append(error_msg)
                logger.error(f"  ✗ Attribute removal failed: {e}")

        except Exception as e:
            self.results[test_name]['failed'] += 1
            error_msg = f"✗ FileUnlocker test failed: {e}"
            self.results[test_name]['errors'].append(error_msg)
            self.results[test_name]['details'].append(error_msg)
            logger.error(f"  ✗ FileUnlocker test failed: {e}")

    def test_metadata_analyzer(self):
        """Test MetadataAnalyzer functionality."""
        logger.info("\n[5/5] Testing MetadataAnalyzer...")

        test_name = "metadata_analyzer"
        self.results[test_name] = {
            'passed': 0,
            'failed': 0,
            'errors': [],
            'details': []
        }

        try:
            from tools.metadata_analyzer import MetadataAnalyzer
            from tools.exiftool_wrapper import ExifToolWrapper

            # Test initialization
            try:
                analyzer = MetadataAnalyzer()
                self.results[test_name]['passed'] += 1
                self.results[test_name]['details'].append("✓ MetadataAnalyzer initialized")
                logger.info("  ✓ MetadataAnalyzer initialized")
            except RuntimeError as e:
                # ExifTool might not be available
                self.results[test_name]['failed'] += 1
                error_msg = f"✗ Initialization failed (ExifTool required): {e}"
                self.results[test_name]['errors'].append(error_msg)
                self.results[test_name]['details'].append(error_msg)
                logger.error(f"  ✗ Initialization failed (ExifTool required): {e}")
                return
            except Exception as e:
                self.results[test_name]['failed'] += 1
                error_msg = f"✗ Initialization failed: {e}"
                self.results[test_name]['errors'].append(error_msg)
                self.results[test_name]['details'].append(error_msg)
                logger.error(f"  ✗ Initialization failed: {e}")
                return

            # Test file analysis
            test_file = self._create_test_file("test_analyze.txt", "Test content for analysis")
            try:
                analysis = analyzer.analyze_file(test_file)
                if 'file_path' in analysis:
                    self.results[test_name]['passed'] += 1
                    self.results[test_name]['details'].append("✓ File analysis works")
                    logger.info("  ✓ File analysis works")

                    # Check for expected fields
                    expected_fields = ['camera_info', 'gps_info', 'datetime_info', 'software_info']
                    found_fields = [f for f in expected_fields if f in analysis]
                    self.results[test_name]['details'].append(
                        f"  - Analysis contains {len(found_fields)}/{len(expected_fields)} expected fields"
                    )
                    logger.info(f"    - Analysis contains {len(found_fields)}/{len(expected_fields)} expected fields")
                else:
                    self.results[test_name]['failed'] += 1
                    error_msg = "✗ Analysis returned unexpected format"
                    self.results[test_name]['errors'].append(error_msg)
                    self.results[test_name]['details'].append(error_msg)
                    logger.error("  ✗ Analysis returned unexpected format")
            except Exception as e:
                self.results[test_name]['failed'] += 1
                error_msg = f"✗ File analysis failed: {e}"
                self.results[test_name]['errors'].append(error_msg)
                self.results[test_name]['details'].append(error_msg)
                logger.error(f"  ✗ File analysis failed: {e}")

            # Test comparison
            test_file2 = self._create_test_file("test_analyze2.txt", "Another test file")
            try:
                comparison = analyzer.compare_metadata(test_file, test_file2)
                if 'similarities' in comparison and 'differences' in comparison:
                    self.results[test_name]['passed'] += 1
                    self.results[test_name]['details'].append("✓ Metadata comparison works")
                    logger.info("  ✓ Metadata comparison works")
                else:
                    self.results[test_name]['failed'] += 1
                    error_msg = "✗ Comparison returned unexpected format"
                    self.results[test_name]['errors'].append(error_msg)
                    self.results[test_name]['details'].append(error_msg)
                    logger.error("  ✗ Comparison returned unexpected format")
            except Exception as e:
                self.results[test_name]['failed'] += 1
                error_msg = f"✗ Metadata comparison failed: {e}"
                self.results[test_name]['errors'].append(error_msg)
                self.results[test_name]['details'].append(error_msg)
                logger.error(f"  ✗ Metadata comparison failed: {e}")

        except Exception as e:
            self.results[test_name]['failed'] += 1
            error_msg = f"✗ MetadataAnalyzer test failed: {e}"
            self.results[test_name]['errors'].append(error_msg)
            self.results[test_name]['details'].append(error_msg)
            logger.error(f"  ✗ MetadataAnalyzer test failed: {e}")

    def _create_test_file(self, filename: str, content: str) -> str:
        """Create a test file in temp directory."""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path

    def print_summary(self):
        """Print test summary."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST SUMMARY")
        logger.info("=" * 70)

        total_passed = 0
        total_failed = 0
        total_errors = []

        for test_name, result in self.results.items():
            passed = result.get('passed', 0)
            failed = result.get('failed', 0)
            errors = result.get('errors', [])

            total_passed += passed
            total_failed += failed
            total_errors.extend(errors)

            status = "✓ PASSED" if failed == 0 else "✗ FAILED"
            logger.info(f"\n{test_name.upper()}: {status}")
            logger.info(f"  Passed: {passed}")
            logger.info(f"  Failed: {failed}")

            if errors:
                logger.info("  Errors:")
                for error in errors:
                    logger.error(f"    - {error}")

        logger.info("\n" + "=" * 70)
        logger.info(f"TOTAL TESTS PASSED: {total_passed}")
        logger.info(f"TOTAL TESTS FAILED: {total_failed}")
        logger.info(f"SUCCESS RATE: {total_passed / (total_passed + total_failed) * 100:.1f}%")
        logger.info("=" * 70)

        if total_failed == 0:
            logger.info("\n✓✓✓ ALL TESTS PASSED! ✓✓✓")
        else:
            logger.warning(f"\n⚠⚠⚠ {total_failed} TEST(S) FAILED ⚠⚠⚠")

    def cleanup(self):
        """Clean up temporary files."""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info(f"\nCleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Failed to clean up temp directory: {e}")


def main():
    """Main test runner."""
    tester = ToolsModuleTester()

    try:
        results = tester.run_all_tests()
        return results
    finally:
        tester.cleanup()


if __name__ == '__main__':
    results = main()
    sys.exit(0 if all(r.get('failed', 0) == 0 for r in results.values()) else 1)
