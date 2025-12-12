#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Search - Dependency Verification Tool
============================================

Verifies that all required dependencies are installed and properly configured.

Usage:
    python verify_setup.py

Exit Codes:
    0: All dependencies OK
    1: Missing or misconfigured dependencies
"""

import sys
import subprocess
import os
from pathlib import Path


class DependencyChecker:
    """Checks and reports on application dependencies"""

    def __init__(self):
        self.results = []
        self.critical_missing = []

    def check_package(self, package_name: str, import_name: str = None,
                     min_version: str = None, critical: bool = False) -> bool:
        """
        Check if a package is installed.

        Args:
            package_name: Package name for pip install
            import_name: Name to use for import (defaults to package_name)
            min_version: Minimum version required
            critical: Whether this is a critical dependency

        Returns:
            True if package is OK, False otherwise
        """
        if import_name is None:
            import_name = package_name.replace("-", "_")

        try:
            module = __import__(import_name)
            version = getattr(module, "__version__", "unknown")
            status = f"OK (version: {version})"

            self.results.append({
                "package": package_name,
                "status": status,
                "ok": True
            })
            return True

        except ImportError:
            status = "MISSING"
            if critical:
                self.critical_missing.append({
                    "package": package_name,
                    "command": f"pip install {package_name}"
                })

            self.results.append({
                "package": package_name,
                "status": status,
                "ok": False,
                "critical": critical
            })
            return False

    def check_python_version(self) -> bool:
        """Check if Python version is adequate"""
        version_info = sys.version_info
        min_major = 3
        min_minor = 8

        if version_info.major >= min_major and version_info.minor >= min_minor:
            status = f"OK (version: {version_info.major}.{version_info.minor}.{version_info.micro})"
            self.results.append({
                "package": "Python",
                "status": status,
                "ok": True
            })
            return True
        else:
            status = f"TOO OLD (version: {version_info.major}.{version_info.minor})"
            self.results.append({
                "package": "Python",
                "status": status,
                "ok": False,
                "critical": True
            })
            self.critical_missing.append({
                "package": "Python",
                "command": "Install Python 3.8 or newer from python.org"
            })
            return False

    def check_windows_platform(self) -> bool:
        """Check if running on Windows"""
        if sys.platform == "win32":
            self.results.append({
                "package": "Windows Platform",
                "status": "OK",
                "ok": True
            })
            return True
        else:
            self.results.append({
                "package": "Windows Platform",
                "status": f"NOT WINDOWS (current: {sys.platform})",
                "ok": False,
                "critical": True
            })
            self.critical_missing.append({
                "package": "Windows OS",
                "command": "Smart Search requires Windows"
            })
            return False

    def check_local_modules(self) -> bool:
        """Check if local modules can be imported"""
        script_dir = Path(__file__).parent

        modules_to_check = [
            ("main.py", "main"),
            ("backend.py", "backend"),
            ("categories.py", "categories"),
            ("classifier.py", "classifier"),
            ("file_manager.py", "file_manager"),
            ("ui.py", "ui"),
            ("utils.py", "utils"),
        ]

        all_ok = True

        for file_name, import_name in modules_to_check:
            file_path = script_dir / file_name
            if file_path.exists():
                try:
                    __import__(import_name)
                    self.results.append({
                        "package": f"Local Module: {import_name}",
                        "status": "OK",
                        "ok": True
                    })
                except Exception as e:
                    self.results.append({
                        "package": f"Local Module: {import_name}",
                        "status": f"ERROR: {str(e)[:50]}",
                        "ok": False,
                        "critical": True
                    })
                    all_ok = False
            else:
                self.results.append({
                    "package": f"Local Module: {import_name}",
                    "status": "FILE NOT FOUND",
                    "ok": False,
                    "critical": True
                })
                all_ok = False

        return all_ok

    def print_report(self):
        """Print a formatted report of all checks"""
        print("\n" + "=" * 70)
        print("SMART SEARCH - DEPENDENCY VERIFICATION REPORT")
        print("=" * 70 + "\n")

        # Print results
        print("Installed Components:")
        print("-" * 70)
        for result in self.results:
            status_symbol = "[OK]" if result.get("ok") else "[FAIL]"
            critical_marker = " [CRITICAL]" if result.get("critical") else ""
            print(f"{status_symbol} {result['package']:<30} {result['status']}{critical_marker}")

        print()

        # Print summary
        total = len(self.results)
        ok_count = sum(1 for r in self.results if r.get("ok"))
        print("-" * 70)
        print(f"Summary: {ok_count}/{total} components OK")

        if self.critical_missing:
            print("\nCRITICAL ISSUES FOUND:")
            print("-" * 70)
            for issue in self.critical_missing:
                print(f"\n{issue['package']}:")
                print(f"  Install command: {issue['command']}")

            return False
        else:
            print("\nAll dependencies OK! Application should run correctly.")
            return True

    def run(self) -> int:
        """Run all checks and return exit code"""
        # Check platform first
        self.check_windows_platform()
        if sys.platform != "win32":
            self.print_report()
            return 1

        # Check Python version
        self.check_python_version()

        # Check critical dependencies
        self.check_package("PyQt6", "PyQt6", critical=True)
        self.check_package("pywin32", "win32com", critical=True)
        self.check_package("comtypes", "comtypes", critical=True)

        # Check optional dependencies
        self.check_package("pytest", "pytest", critical=False)
        self.check_package("coverage", "coverage", critical=False)

        # Check local modules
        self.check_local_modules()

        # Print report
        success = self.print_report()

        print("\n" + "=" * 70 + "\n")

        # Return appropriate exit code
        return 0 if success else 1


def main():
    """Main entry point"""
    checker = DependencyChecker()
    exit_code = checker.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
