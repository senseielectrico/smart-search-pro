#!/usr/bin/env python3
"""
Smart Search Pro - Test Suite Runner
=====================================

Comprehensive test runner with coverage reporting, parallel execution, and detailed output.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run only unit tests
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --coverage         # Run with coverage report
    python run_tests.py --parallel         # Run tests in parallel
    python run_tests.py --verbose          # Verbose output
    python run_tests.py --module core      # Run specific module tests
    python run_tests.py --html             # Generate HTML report
"""

import sys
import os
import argparse
import subprocess
import time
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")


def print_section(text):
    """Print formatted section"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'-' * len(text)}{Colors.ENDC}")


def print_success(text):
    """Print success message"""
    try:
        print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"{Colors.GREEN}[OK] {text}{Colors.ENDC}")


def print_error(text):
    """Print error message"""
    try:
        print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"{Colors.FAIL}[ERROR] {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message"""
    try:
        print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"{Colors.WARNING}[WARNING] {text}{Colors.ENDC}")


def check_dependencies():
    """Check if required dependencies are installed"""
    print_section("Checking Dependencies")

    required = ['pytest', 'pytest-cov']
    optional = ['pytest-xdist', 'pytest-html', 'pytest-timeout']

    missing_required = []
    missing_optional = []

    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print_success(f"{package} is installed")
        except ImportError:
            missing_required.append(package)
            print_error(f"{package} is NOT installed")

    for package in optional:
        try:
            __import__(package.replace('-', '_'))
            print_success(f"{package} is installed")
        except ImportError:
            missing_optional.append(package)
            print_warning(f"{package} is NOT installed (optional)")

    if missing_required:
        print_error(f"\nMissing required packages: {', '.join(missing_required)}")
        print(f"\nInstall with: pip install {' '.join(missing_required)}")
        return False

    if missing_optional:
        print_warning(f"\nMissing optional packages: {', '.join(missing_optional)}")
        print(f"Install with: pip install {' '.join(missing_optional)}")

    return True


def build_pytest_command(args):
    """Build pytest command based on arguments"""
    cmd = [sys.executable, "-m", "pytest"]

    # Test directory
    if args.module:
        test_file = f"tests/test_{args.module}.py"
        if os.path.exists(test_file):
            cmd.append(test_file)
        else:
            print_error(f"Test file not found: {test_file}")
            return None
    else:
        cmd.append("tests/")

    # Markers
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    elif args.performance:
        cmd.extend(["-m", "performance"])

    # Verbosity
    if args.verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")

    # Coverage
    if args.coverage:
        cmd.extend([
            "--cov=core",
            "--cov=search",
            "--cov=duplicates",
            "--cov=operations",
            "--cov=export",
            "--cov=preview",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
        ])

    # Parallel execution
    if args.parallel:
        try:
            import pytest_xdist
            cmd.extend(["-n", "auto"])
        except ImportError:
            print_warning("pytest-xdist not installed, running sequentially")

    # HTML report
    if args.html:
        try:
            import pytest_html
            cmd.extend(["--html=test_report.html", "--self-contained-html"])
        except ImportError:
            print_warning("pytest-html not installed, skipping HTML report")

    # Timeout
    if args.timeout:
        try:
            import pytest_timeout
            cmd.extend([f"--timeout={args.timeout}"])
        except ImportError:
            print_warning("pytest-timeout not installed, skipping timeout")

    # Additional options
    cmd.extend([
        "--tb=short",
        "--color=yes",
        "--strict-markers"
    ])

    # Fail fast
    if args.failfast:
        cmd.append("-x")

    # Show locals
    if args.showlocals:
        cmd.append("-l")

    return cmd


def run_tests(cmd):
    """Execute pytest command"""
    print_section("Running Tests")
    print(f"Command: {' '.join(cmd)}\n")

    start_time = time.time()

    try:
        result = subprocess.run(cmd, check=False)
        duration = time.time() - start_time

        print(f"\n{Colors.CYAN}Test execution completed in {duration:.2f}s{Colors.ENDC}")

        return result.returncode

    except KeyboardInterrupt:
        print_warning("\n\nTests interrupted by user")
        return 130
    except Exception as e:
        print_error(f"\n\nError running tests: {e}")
        return 1


def generate_coverage_summary():
    """Generate coverage summary if coverage data exists"""
    if os.path.exists(".coverage"):
        print_section("Coverage Summary")
        try:
            subprocess.run([sys.executable, "-m", "coverage", "report"], check=False)
            print_success("\nDetailed HTML coverage report: htmlcov/index.html")
        except Exception as e:
            print_warning(f"Could not generate coverage report: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Smart Search Pro Test Suite Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                     # Run all tests
  python run_tests.py --coverage          # Run with coverage
  python run_tests.py --parallel          # Run in parallel
  python run_tests.py --module core       # Run core module tests
  python run_tests.py --unit --verbose    # Run unit tests with verbose output
        """
    )

    # Test selection
    parser.add_argument('--unit', action='store_true',
                        help='Run only unit tests')
    parser.add_argument('--integration', action='store_true',
                        help='Run only integration tests')
    parser.add_argument('--performance', action='store_true',
                        help='Run only performance tests')
    parser.add_argument('--module', type=str,
                        help='Run specific module tests (e.g., core, search)')

    # Execution options
    parser.add_argument('--parallel', action='store_true',
                        help='Run tests in parallel')
    parser.add_argument('--coverage', action='store_true',
                        help='Generate coverage report')
    parser.add_argument('--html', action='store_true',
                        help='Generate HTML test report')

    # Output options
    parser.add_argument('--verbose', action='store_true',
                        help='Verbose output')
    parser.add_argument('--quiet', action='store_true',
                        help='Minimal output')

    # Behavior options
    parser.add_argument('--failfast', action='store_true',
                        help='Stop on first failure')
    parser.add_argument('--showlocals', action='store_true',
                        help='Show local variables in tracebacks')
    parser.add_argument('--timeout', type=int, default=300,
                        help='Test timeout in seconds (default: 300)')

    # Special modes
    parser.add_argument('--check-only', action='store_true',
                        help='Only check dependencies, do not run tests')

    args = parser.parse_args()

    # Print header
    print_header("Smart Search Pro - Test Suite")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    if args.check_only:
        print_success("\nDependency check complete!")
        sys.exit(0)

    # Build and run pytest command
    cmd = build_pytest_command(args)
    if cmd is None:
        sys.exit(1)

    returncode = run_tests(cmd)

    # Generate coverage summary if coverage was enabled
    if args.coverage and returncode == 0:
        generate_coverage_summary()

    # Print final result
    print_section("Final Result")
    if returncode == 0:
        print_success("All tests passed!")
    else:
        print_error(f"Tests failed with exit code {returncode}")

    # Print reports information
    if args.html and os.path.exists("test_report.html"):
        print(f"\n{Colors.BLUE}HTML Test Report: test_report.html{Colors.ENDC}")

    if args.coverage and os.path.exists("htmlcov/index.html"):
        print(f"{Colors.BLUE}HTML Coverage Report: htmlcov/index.html{Colors.ENDC}")

    sys.exit(returncode)


if __name__ == "__main__":
    main()
