#!/usr/bin/env python3
"""
Smart Search - Requirements.txt Updater

This script updates requirements.txt with the latest versions of installed packages,
or recreates it with specific version constraints.

Usage:
    python update_requirements.py
    python update_requirements.py --upgrade     # Upgrade to latest
    python update_requirements.py --reset       # Reset to defaults
    python update_requirements.py --current     # Show currently installed versions
"""

import sys
import subprocess
import json
from typing import Dict, List, Optional
from pathlib import Path


class RequirementsUpdater:
    """Manages requirements.txt updates and version tracking."""

    # Default minimum versions for Smart Search
    REQUIRED_PACKAGES = {
        'PyQt6': '6.6.0',
        'PyQt6-Qt6': '6.6.0',
        'PyQt6-sip': '13.6.0',
        'pywin32': '305',
        'comtypes': '1.1.14',
        'send2trash': '1.8.2',
    }

    def __init__(self, requirements_file: str = 'requirements.txt'):
        """Initialize the updater."""
        self.requirements_file = Path(requirements_file)
        self.current_versions: Dict[str, str] = {}

    def get_installed_version(self, package_name: str) -> Optional[str]:
        """
        Get the currently installed version of a package.

        Args:
            package_name: Name of the package

        Returns:
            Version string or None if not installed
        """
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', package_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        return line.split(':', 1)[1].strip()
        except Exception as e:
            print(f"Error getting version for {package_name}: {e}")
        return None

    def get_latest_version(self, package_name: str) -> Optional[str]:
        """
        Get the latest available version of a package from PyPI.

        Args:
            package_name: Name of the package

        Returns:
            Latest version string or None if not found
        """
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'index', 'versions', package_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Available versions:' in line:
                        # Extract versions from the output
                        versions = line.split('Available versions:')[1].strip()
                        # Get the first (latest) version
                        latest = versions.split(',')[0].strip()
                        return latest
        except Exception:
            # Fallback: try using pip install with --dry-run
            pass

        # Alternative method using pip install --dry-run
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--dry-run', '--upgrade', package_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Would install' in line or 'Collecting' in line:
                        # Try to extract version
                        parts = line.split('-')
                        if len(parts) >= 2:
                            version = parts[-1].split()[0]
                            if version and version[0].isdigit():
                                return version
        except Exception:
            pass

        return None

    def read_current_requirements(self) -> Dict[str, str]:
        """
        Read current requirements from file.

        Returns:
            Dict of package_name -> version_spec
        """
        requirements = {}
        if self.requirements_file.exists():
            with open(self.requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Parse "package>=version" format
                        for op in ['>=', '==', '<=', '>', '<', '~=']:
                            if op in line:
                                pkg, ver = line.split(op, 1)
                                requirements[pkg.strip()] = f"{op}{ver.strip()}"
                                break
        return requirements

    def write_requirements(self, packages: Dict[str, str]):
        """
        Write requirements to file.

        Args:
            packages: Dict of package_name -> version_spec
        """
        with open(self.requirements_file, 'w') as f:
            for pkg_name in sorted(packages.keys()):
                f.write(f"{pkg_name}{packages[pkg_name]}\n")

    def show_current_versions(self):
        """Display currently installed versions."""
        print("=" * 60)
        print("Smart Search - Currently Installed Versions")
        print("=" * 60)
        print()

        for pkg_name in self.REQUIRED_PACKAGES.keys():
            installed = self.get_installed_version(pkg_name)
            required = self.REQUIRED_PACKAGES[pkg_name]

            if installed:
                status = "OK" if self._compare_versions(installed, required) >= 0 else "OUTDATED"
                print(f"[{status}] {pkg_name:<20} Installed: {installed:<12} Required: >={required}")
            else:
                print(f"[NOT] {pkg_name:<20} NOT INSTALLED        Required: >={required}")

        print()

    def reset_to_defaults(self):
        """Reset requirements.txt to default versions."""
        print("Resetting requirements.txt to default versions...")
        requirements = {}
        for pkg_name, version in self.REQUIRED_PACKAGES.items():
            requirements[pkg_name] = f">={version}"
        self.write_requirements(requirements)
        print(f"Updated: {self.requirements_file}")
        self.show_current_versions()

    def upgrade_to_current(self):
        """Upgrade requirements.txt to currently installed versions."""
        print("Updating requirements.txt to current installed versions...")
        requirements = {}

        for pkg_name in self.REQUIRED_PACKAGES.keys():
            installed = self.get_installed_version(pkg_name)
            if installed:
                requirements[pkg_name] = f">={installed}"
                print(f"  {pkg_name}: {installed}")
            else:
                # Use default if not installed
                requirements[pkg_name] = f">={self.REQUIRED_PACKAGES[pkg_name]}"
                print(f"  {pkg_name}: {self.REQUIRED_PACKAGES[pkg_name]} (default)")

        self.write_requirements(requirements)
        print(f"\nUpdated: {self.requirements_file}")

    def upgrade_to_latest(self):
        """Upgrade requirements.txt to latest available versions."""
        print("Checking for latest versions available on PyPI...")
        print("(This may take a moment...)")
        print()

        requirements = {}

        for pkg_name in self.REQUIRED_PACKAGES.keys():
            print(f"Checking {pkg_name}...", end=" ", flush=True)
            latest = self.get_latest_version(pkg_name)
            if latest:
                requirements[pkg_name] = f">={latest}"
                print(f"OK ({latest})")
            else:
                # Fallback to installed version
                installed = self.get_installed_version(pkg_name)
                if installed:
                    requirements[pkg_name] = f">={installed}"
                    print(f"Using installed ({installed})")
                else:
                    requirements[pkg_name] = f">={self.REQUIRED_PACKAGES[pkg_name]}"
                    print(f"Using default ({self.REQUIRED_PACKAGES[pkg_name]})")

        print()
        self.write_requirements(requirements)
        print(f"Updated: {self.requirements_file}")

    @staticmethod
    def _compare_versions(v1: str, v2: str) -> int:
        """
        Compare two version strings.

        Returns:
            1 if v1 > v2, -1 if v1 < v2, 0 if equal
        """
        def parse(v):
            return tuple(int(x) for x in v.split('.') if x.isdigit())

        try:
            p1 = parse(v1)
            p2 = parse(v2)
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
            else:
                return 0
        except:
            return 0


def main():
    """Main entry point."""
    updater = RequirementsUpdater()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == '--current':
            updater.show_current_versions()
        elif command == '--upgrade':
            updater.upgrade_to_current()
        elif command == '--latest':
            updater.upgrade_to_latest()
        elif command == '--reset':
            updater.reset_to_defaults()
        elif command in ['-h', '--help']:
            print(__doc__)
        else:
            print(f"Unknown command: {command}")
            print(__doc__)
            sys.exit(1)
    else:
        # Default: show current and reset to defaults
        print("Usage: python update_requirements.py [command]")
        print()
        print("Commands:")
        print("  --current     Show currently installed versions")
        print("  --upgrade     Update to current installed versions")
        print("  --latest      Update to latest available versions")
        print("  --reset       Reset to default versions (default)")
        print("  --help        Show this help message")
        print()
        updater.show_current_versions()


if __name__ == '__main__':
    main()
