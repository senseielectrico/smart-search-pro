#!/usr/bin/env python
"""
Comprehensive Test Runner for Smart Search Pro
==============================================

Runs the complete test suite with organized output and reporting.

Usage:
    python run_comprehensive_tests.py [options]

Options:
    --all           Run all tests (default)
    --unit          Run unit tests only
    --integration   Run integration tests only
    --performance   Run performance tests only
    --coverage      Run with coverage report
    --html          Generate HTML report
    --fast          Skip slow tests
    --verbose       Verbose output
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


class TestRunner:
    """Comprehensive test runner with reporting"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.test_file = Path(__file__).parent / "tests" / "test_comprehensive.py"
        self.results = {}

    def run_command(self, cmd, description):
        """Run pytest command and capture results"""
        print(f"\n{'='*70}")
        print(f"Running: {description}")
        print(f"{'='*70}\n")

        if self.verbose:
            print(f"Command: {' '.join(cmd)}\n")

        try:
            result = subprocess.run(
                cmd,
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            # Parse output
            output = result.stdout + result.stderr
            print(output)

            # Extract test results
            if "passed" in output:
                return self.parse_results(output)
            else:
                return {"passed": 0, "failed": 0, "errors": 0, "status": "ERROR"}

        except subprocess.TimeoutExpired:
            print("ERROR: Tests timed out after 5 minutes")
            return {"passed": 0, "failed": 0, "errors": 0, "status": "TIMEOUT"}

        except Exception as e:
            print(f"ERROR: {e}")
            return {"passed": 0, "failed": 0, "errors": 0, "status": "ERROR"}

    def parse_results(self, output):
        """Parse pytest output for results"""
        import re

        results = {"passed": 0, "failed": 0, "errors": 0, "status": "UNKNOWN"}

        # Look for result summary line
        match = re.search(r'(\d+) failed.*?(\d+) passed', output)
        if match:
            results["failed"] = int(match.group(1))
            results["passed"] = int(match.group(2))
            results["status"] = "FAILED" if results["failed"] > 0 else "PASSED"

        match = re.search(r'(\d+) passed', output)
        if match and results["passed"] == 0:
            results["passed"] = int(match.group(1))
            results["status"] = "PASSED"

        match = re.search(r'(\d+) error', output)
        if match:
            results["errors"] = int(match.group(1))

        return results

    def run_all_tests(self):
        """Run all tests"""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_file),
            "-v",
            "--tb=short",
            "--color=yes"
        ]

        return self.run_command(cmd, "All Tests")

    def run_unit_tests(self):
        """Run unit tests only"""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_file),
            "-v",
            "-m", "unit",
            "--tb=short"
        ]

        return self.run_command(cmd, "Unit Tests")

    def run_integration_tests(self):
        """Run integration tests only"""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_file),
            "-v",
            "-m", "integration",
            "--tb=short"
        ]

        return self.run_command(cmd, "Integration Tests")

    def run_performance_tests(self):
        """Run performance tests only"""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_file),
            "-v",
            "-m", "performance",
            "--tb=short"
        ]

        return self.run_command(cmd, "Performance Tests")

    def run_by_category(self):
        """Run tests organized by category"""
        categories = [
            ("TestConfigLoading", "Configuration Tests"),
            ("TestDatabaseOperations", "Database Tests"),
            ("TestEventBusPubSub", "Event Bus Tests"),
            ("TestFileCopier", "File Copier Tests"),
            ("TestDuplicateScanner", "Duplicate Scanner Tests"),
            ("TestHashAlgorithms", "Hash Algorithm Tests"),
        ]

        results = {}
        for test_class, description in categories:
            cmd = [
                sys.executable, "-m", "pytest",
                f"{self.test_file}::{test_class}",
                "-v",
                "--tb=no"
            ]
            results[description] = self.run_command(cmd, description)

        return results

    def run_with_coverage(self):
        """Run tests with coverage report"""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_file),
            "--cov=.",
            "--cov-report=term",
            "--cov-report=html",
            "-v"
        ]

        return self.run_command(cmd, "Tests with Coverage")

    def run_fast_tests(self):
        """Run fast tests only (skip slow tests)"""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_file),
            "-v",
            "-m", "not slow",
            "--tb=short"
        ]

        return self.run_command(cmd, "Fast Tests")

    def generate_html_report(self):
        """Generate HTML test report"""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_file),
            "--html=test_report.html",
            "--self-contained-html",
            "-v"
        ]

        return self.run_command(cmd, "Tests with HTML Report")

    def print_summary(self, results):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)

        if isinstance(results, dict):
            if "passed" in results:
                # Single result
                total = results["passed"] + results["failed"] + results["errors"]
                print(f"\nTotal Tests: {total}")
                print(f"Passed: {results['passed']} ({results['passed']/total*100:.1f}%)")
                print(f"Failed: {results['failed']} ({results['failed']/total*100:.1f}%)")
                if results["errors"] > 0:
                    print(f"Errors: {results['errors']} ({results['errors']/total*100:.1f}%)")
                print(f"\nStatus: {results['status']}")
            else:
                # Category results
                for category, result in results.items():
                    print(f"\n{category}:")
                    if "passed" in result:
                        total = result["passed"] + result["failed"]
                        if total > 0:
                            print(f"  Passed: {result['passed']}/{total} ({result['passed']/total*100:.1f}%)")
                        print(f"  Status: {result['status']}")

        print("\n" + "="*70)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run comprehensive test suite for Smart Search Pro"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests (default)"
    )

    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run unit tests only"
    )

    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests only"
    )

    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run performance tests only"
    )

    parser.add_argument(
        "--category",
        action="store_true",
        help="Run tests by category"
    )

    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage report"
    )

    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML report"
    )

    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip slow tests"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Create runner
    runner = TestRunner(verbose=args.verbose)

    # Determine what to run
    if args.unit:
        results = runner.run_unit_tests()
    elif args.integration:
        results = runner.run_integration_tests()
    elif args.performance:
        results = runner.run_performance_tests()
    elif args.category:
        results = runner.run_by_category()
    elif args.coverage:
        results = runner.run_with_coverage()
    elif args.html:
        results = runner.generate_html_report()
    elif args.fast:
        results = runner.run_fast_tests()
    else:
        # Default: run all tests
        results = runner.run_all_tests()

    # Print summary
    runner.print_summary(results)

    # Exit with appropriate code
    if isinstance(results, dict):
        if "status" in results:
            sys.exit(0 if results["status"] == "PASSED" else 1)
        else:
            # Check if any category failed
            all_passed = all(
                r.get("status") == "PASSED"
                for r in results.values()
                if isinstance(r, dict)
            )
            sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
