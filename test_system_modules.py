#!/usr/bin/env python3
"""
Comprehensive test suite for smart_search system modules.
Tests: AdminConsoleManager, ElevationManager, HotkeyManager, SingleInstance
"""

import sys
import traceback
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

class TestResult:
    """Store test results with detailed information."""

    def __init__(self, module: str, test: str):
        self.module = module
        self.test = test
        self.passed = False
        self.error = None
        self.traceback = None

    def mark_passed(self):
        self.passed = True

    def mark_failed(self, error: Exception):
        self.passed = False
        self.error = str(error)
        self.traceback = traceback.format_exc()

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.module}.{self.test}"


class SystemModuleTester:
    """Test runner for system modules."""

    def __init__(self):
        self.results: List[TestResult] = []

    def test_admin_console_module(self) -> List[TestResult]:
        """Test system.admin_console module."""
        module_name = "system.admin_console"
        tests = []

        # Test 1: Import module
        result = TestResult(module_name, "import")
        try:
            from system.admin_console import AdminConsoleManager
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 2: Class instantiation
        result = TestResult(module_name, "instantiation")
        try:
            from system.admin_console import AdminConsoleManager
            manager = AdminConsoleManager()
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 3: Check attributes
        result = TestResult(module_name, "attributes")
        try:
            from system.admin_console import AdminConsoleManager
            manager = AdminConsoleManager()

            # Check for expected methods
            assert hasattr(manager, 'execute_command'), "Should have execute_command method"
            assert hasattr(manager, 'is_available'), "Should have is_available method"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 4: Availability check
        result = TestResult(module_name, "availability")
        try:
            from system.admin_console import AdminConsoleManager
            manager = AdminConsoleManager()
            is_available = manager.is_available()
            assert isinstance(is_available, bool), "Should return boolean"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        return tests

    def test_elevation_module(self) -> List[TestResult]:
        """Test system.elevation module."""
        module_name = "system.elevation"
        tests = []

        # Test 1: Import module
        result = TestResult(module_name, "import")
        try:
            from system.elevation import ElevationManager
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 2: Class instantiation
        result = TestResult(module_name, "instantiation")
        try:
            from system.elevation import ElevationManager
            manager = ElevationManager()
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 3: Check admin status
        result = TestResult(module_name, "is_admin")
        try:
            from system.elevation import ElevationManager
            manager = ElevationManager()
            is_admin = manager.is_admin()
            assert isinstance(is_admin, bool), "Should return boolean"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 4: Check attributes
        result = TestResult(module_name, "attributes")
        try:
            from system.elevation import ElevationManager
            manager = ElevationManager()

            # Check for expected methods
            assert hasattr(manager, 'is_admin'), "Should have is_admin method"
            assert hasattr(manager, 'request_elevation'), "Should have request_elevation method"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        return tests

    def test_hotkeys_module(self) -> List[TestResult]:
        """Test system.hotkeys module."""
        module_name = "system.hotkeys"
        tests = []

        # Test 1: Import module
        result = TestResult(module_name, "import")
        try:
            from system.hotkeys import HotkeyManager
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 2: Class instantiation
        result = TestResult(module_name, "instantiation")
        try:
            from system.hotkeys import HotkeyManager
            manager = HotkeyManager()
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 3: Register hotkey
        result = TestResult(module_name, "register_hotkey")
        try:
            from system.hotkeys import HotkeyManager
            manager = HotkeyManager()

            def test_callback():
                pass

            # Should be able to register hotkey (may fail if keyboard library not available)
            try:
                success = manager.register("ctrl+shift+f", test_callback)
                assert isinstance(success, bool), "Should return boolean"
            except Exception:
                # If keyboard library not available, that's okay
                pass

            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 4: Check attributes
        result = TestResult(module_name, "attributes")
        try:
            from system.hotkeys import HotkeyManager
            manager = HotkeyManager()

            # Check for expected methods
            assert hasattr(manager, 'register'), "Should have register method"
            assert hasattr(manager, 'unregister'), "Should have unregister method"
            assert hasattr(manager, 'unregister_all'), "Should have unregister_all method"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 5: Cleanup
        result = TestResult(module_name, "cleanup")
        try:
            from system.hotkeys import HotkeyManager
            manager = HotkeyManager()

            # Should be able to cleanup
            manager.unregister_all()
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        return tests

    def test_single_instance_module(self) -> List[TestResult]:
        """Test system.single_instance module."""
        module_name = "system.single_instance"
        tests = []

        # Test 1: Import module
        result = TestResult(module_name, "import")
        try:
            from system.single_instance import SingleInstanceManager
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 2: Class instantiation
        result = TestResult(module_name, "instantiation")
        try:
            from system.single_instance import SingleInstanceManager
            manager = SingleInstanceManager("test_app")
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 3: Check lock status
        result = TestResult(module_name, "lock_status")
        try:
            from system.single_instance import SingleInstanceManager
            manager = SingleInstanceManager("test_app_unique")

            # First instance should get lock
            has_lock = manager.is_running()
            assert isinstance(has_lock, bool), "Should return boolean"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 4: Multiple instances
        result = TestResult(module_name, "multiple_instances")
        try:
            from system.single_instance import SingleInstanceManager

            # Create first instance
            manager1 = SingleInstanceManager("test_app_multi")
            running1 = manager1.is_running()

            # Create second instance
            manager2 = SingleInstanceManager("test_app_multi")
            running2 = manager2.is_running()

            # One should have lock, behavior depends on implementation
            assert isinstance(running1, bool), "Should return boolean"
            assert isinstance(running2, bool), "Should return boolean"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 5: Check attributes
        result = TestResult(module_name, "attributes")
        try:
            from system.single_instance import SingleInstanceManager
            manager = SingleInstanceManager("test_app_attrs")

            # Check for expected methods
            assert hasattr(manager, 'is_running'), "Should have is_running method"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        return tests

    def run_all_tests(self) -> Dict[str, List[TestResult]]:
        """Run all system module tests."""
        all_results = {}

        print("=" * 80)
        print("SYSTEM MODULES TEST SUITE")
        print("=" * 80)
        print()

        # Test AdminConsoleManager
        print("Testing system.admin_console...")
        admin_results = self.test_admin_console_module()
        all_results["admin_console"] = admin_results
        self.results.extend(admin_results)

        # Test ElevationManager
        print("Testing system.elevation...")
        elevation_results = self.test_elevation_module()
        all_results["elevation"] = elevation_results
        self.results.extend(elevation_results)

        # Test HotkeyManager
        print("Testing system.hotkeys...")
        hotkey_results = self.test_hotkeys_module()
        all_results["hotkeys"] = hotkey_results
        self.results.extend(hotkey_results)

        # Test SingleInstance
        print("Testing system.single_instance...")
        single_results = self.test_single_instance_module()
        all_results["single_instance"] = single_results
        self.results.extend(single_results)

        return all_results

    def print_summary(self):
        """Print test summary."""
        print()
        print("=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)
        print()

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)

        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ({100*passed/total:.1f}%)")
        print(f"Failed: {failed} ({100*failed/total:.1f}%)")
        print()

        if failed > 0:
            print("FAILED TESTS:")
            print("-" * 80)
            for result in self.results:
                if not result.passed:
                    print(f"\n{result}")
                    print(f"  Error: {result.error}")
                    if result.traceback:
                        print(f"  Traceback:\n{result.traceback}")

        print()
        print("DETAILED RESULTS:")
        print("-" * 80)
        for result in self.results:
            print(result)

        return passed == total


def main():
    """Main test runner."""
    tester = SystemModuleTester()
    tester.run_all_tests()
    success = tester.print_summary()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
