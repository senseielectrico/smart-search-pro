#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Search - Dependency Checker

This script verifies that all required dependencies for Smart Search are installed.
It checks version compatibility and provides detailed diagnostics.

Usage:
    python check_dependencies.py
"""

import sys
import subprocess
import os
from typing import Dict, Tuple, List
from pathlib import Path

# Handle Windows console encoding
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')


class DependencyChecker:
    """Checks and verifies all project dependencies."""

    # Define all required dependencies with their version requirements
    DEPENDENCIES = {
        'PyQt6': {'min_version': '6.6.0', 'description': 'GUI framework'},
        'PyQt6_sip': {'min_version': '13.6.0', 'description': 'PyQt6 SIP bindings', 'import_name': 'PyQt6_sip'},
        'pywin32': {'min_version': '305', 'description': 'Windows API access'},
        'comtypes': {'min_version': '1.1.14', 'description': 'COM interface support'},
        'send2trash': {'min_version': '1.8.2', 'description': 'Safe file deletion to recycle bin'},
    }

    def __init__(self):
        """Initialize the dependency checker."""
        self.results: Dict[str, Dict] = {}
        self.missing_packages: List[str] = []
        self.version_issues: List[Tuple[str, str, str]] = []  # (package, required, installed)

    def parse_version(self, version_string: str) -> Tuple[int, ...]:
        """
        Parse a version string into a tuple of integers.

        Args:
            version_string: Version string like '6.6.0' or '305'

        Returns:
            Tuple of integers for version comparison
        """
        try:
            # Handle simple integer versions like '305'
            if version_string.isdigit():
                return (int(version_string),)

            # Handle semantic versioning like '6.6.0'
            return tuple(int(x) for x in version_string.split('.')[:3])
        except (ValueError, AttributeError):
            return (0,)

    def compare_versions(self, installed: str, required: str) -> bool:
        """
        Compare version strings.

        Args:
            installed: Currently installed version
            required: Minimum required version

        Returns:
            True if installed >= required
        """
        installed_tuple = self.parse_version(installed)
        required_tuple = self.parse_version(required)

        # Pad to same length
        max_len = max(len(installed_tuple), len(required_tuple))
        installed_tuple = installed_tuple + (0,) * (max_len - len(installed_tuple))
        required_tuple = required_tuple + (0,) * (max_len - len(required_tuple))

        return installed_tuple >= required_tuple

    def check_package(self, package_name: str, import_name: str = None) -> Tuple[bool, str]:
        """
        Check if a package is installed and get its version.

        Args:
            package_name: Name of the package (for pip)
            import_name: Name to use for import (defaults to package_name)

        Returns:
            Tuple of (is_installed, version_string)
        """
        if import_name is None:
            import_name = package_name

        try:
            # Try to import the package
            module = __import__(import_name)

            # Try to get version
            version = getattr(module, '__version__', 'unknown')

            # Handle cases where __version__ might be in submodules
            if version == 'unknown':
                try:
                    # Try common alternative locations
                    version = module.version if hasattr(module, 'version') else 'unknown'
                except:
                    pass

            return True, version
        except ImportError:
            return False, None

    def check_all(self) -> bool:
        """
        Check all dependencies.

        Returns:
            True if all dependencies are satisfied, False otherwise
        """
        print("=" * 60)
        print("Smart Search - Dependency Verification")
        print("=" * 60)
        print()

        all_ok = True

        for package_name, info in self.DEPENDENCIES.items():
            import_name = info.get('import_name', package_name)
            description = info.get('description', '')
            min_version = info.get('min_version', 'any')

            is_installed, version = self.check_package(package_name, import_name)

            status_symbol = "[OK]" if is_installed else "[X]"

            if is_installed:
                # Check version
                if version and version != 'unknown':
                    version_ok = self.compare_versions(version, min_version)
                    if version_ok:
                        print(f"{status_symbol} {package_name:<20} v{version:<15} {description}")
                        self.results[package_name] = {
                            'installed': True,
                            'version': version,
                            'version_ok': True
                        }
                    else:
                        print(f"[X] {package_name:<20} v{version:<15} OUTDATED (requires >={min_version})")
                        self.version_issues.append((package_name, min_version, version))
                        self.results[package_name] = {
                            'installed': True,
                            'version': version,
                            'version_ok': False
                        }
                        all_ok = False
                else:
                    print(f"{status_symbol} {package_name:<20} (version unknown)     {description}")
                    self.results[package_name] = {
                        'installed': True,
                        'version': 'unknown',
                        'version_ok': None
                    }
            else:
                print(f"[X] {package_name:<20} NOT INSTALLED        {description}")
                self.missing_packages.append(package_name)
                self.results[package_name] = {
                    'installed': False,
                    'version': None,
                    'version_ok': False
                }
                all_ok = False

        print()
        print("=" * 60)

        return all_ok

    def print_summary(self):
        """Print a summary of the dependency check."""
        print()

        if self.missing_packages:
            print(f"MISSING PACKAGES ({len(self.missing_packages)}):")
            for package in self.missing_packages:
                print(f"  - {package}")
            print()

        if self.version_issues:
            print(f"VERSION ISSUES ({len(self.version_issues)}):")
            for package, required, installed in self.version_issues:
                print(f"  - {package}: requires >={required}, found {installed}")
            print()

        installed_count = sum(1 for r in self.results.values() if r['installed'])
        total_count = len(self.results)

        print(f"Summary: {installed_count}/{total_count} packages installed")

        if not self.missing_packages and not self.version_issues:
            print("Status: ALL DEPENDENCIES OK")
            return True
        else:
            print("Status: ISSUES FOUND")
            return False

    def suggest_fixes(self):
        """Suggest fixes for any issues found."""
        if not self.missing_packages and not self.version_issues:
            return

        print()
        print("=" * 60)
        print("SUGGESTED ACTIONS:")
        print("=" * 60)

        if self.missing_packages or self.version_issues:
            print()
            print("Option 1: Install from requirements.txt (Recommended)")
            print("  python -m pip install -r requirements.txt")
            print()
            print("Option 2: Install from bat script (Windows)")
            print("  install_dependencies.bat")
            print()
            print("Option 3: Install individually")

            if self.missing_packages:
                print("  python -m pip install " + " ".join(self.missing_packages))

            if self.version_issues:
                for package, required, _ in self.version_issues:
                    print(f"  python -m pip install --upgrade {package}")


def main():
    """Main entry point."""
    checker = DependencyChecker()
    all_ok = checker.check_all()
    summary_ok = checker.print_summary()

    if not (all_ok and summary_ok):
        checker.suggest_fixes()
        sys.exit(1)

    print()
    print("You can now run Smart Search!")
    sys.exit(0)


if __name__ == '__main__':
    main()
