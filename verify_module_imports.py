#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive import verification for smart_search modules.
Tests actual module structure and reports detailed diagnostics.
"""

import sys
import importlib
import traceback
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Fix Windows console encoding before anything else
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except Exception:
        pass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


class Colors:
    """ANSI color codes for output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class ModuleVerifier:
    """Verify module imports and structure."""

    def __init__(self):
        self.results: List[Tuple[str, bool, str]] = []
        self.core_modules = {
            'core.database': ['Database', 'ConnectionPool', 'Migration'],
            'core.cache': ['LRUCache', 'CacheManager', 'CacheEntry', 'CacheStats'],
            'core.config': ['Config', 'DatabaseConfig', 'CacheConfig', 'SearchConfig',
                           'LoggingConfig', 'UIConfig', 'PerformanceConfig', 'IntegrationConfig'],
            'core.security': ['sanitize_sql_input', 'validate_path', 'validate_table_name',
                             'sanitize_cli_argument', 'PROTECTED_PATHS', 'ALLOWED_TABLES'],
            'core.logger': ['get_logger', 'setup_logging'],
            'core.eventbus': ['EventBus', 'Event'],
            'core.performance': ['PerformanceMonitor'],
            'core.threading': ['ThreadPoolManager'],
            'core.window_state': ['WindowStateManager'],
        }

        self.system_modules = {
            'system.admin_console': ['AdminConsoleManager', 'ConsoleType', 'ConsoleConfig', 'ConsoleSession'],
            'system.elevation': ['ElevationManager', 'ShowWindow'],
            'system.hotkeys': ['HotkeyManager', 'ModifierKeys', 'VirtualKeys', 'HotkeyInfo'],
            'system.single_instance': ['SingleInstanceManager'],
            'system.autostart': ['AutostartManager'],
            'system.shell_integration': ['ShellIntegration'],
            'system.tray': ['TrayManager'],
            'system.privilege_manager': ['PrivilegeManager'],
        }

    def verify_import(self, module_name: str) -> Tuple[bool, str, Any]:
        """
        Verify module can be imported.

        Returns:
            (success, message, module_object)
        """
        try:
            module = importlib.import_module(module_name)
            return True, f"Successfully imported {module_name}", module
        except ImportError as e:
            return False, f"Import error: {e}", None
        except Exception as e:
            return False, f"Unexpected error: {e}", None

    def verify_attributes(self, module_name: str, module, expected_attrs: List[str]) -> List[Tuple[str, bool, str]]:
        """
        Verify module has expected attributes.

        Returns:
            List of (attribute_name, exists, message)
        """
        results = []
        for attr in expected_attrs:
            has_attr = hasattr(module, attr)
            if has_attr:
                results.append((attr, True, f"  ✓ {attr}"))
            else:
                # Check if it's available via dir()
                available = [a for a in dir(module) if not a.startswith('_')]
                results.append((attr, False, f"  ✗ {attr} (Available: {', '.join(available[:5])}...)"))
        return results

    def test_core_modules(self) -> Dict[str, Any]:
        """Test all core modules."""
        print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}CORE MODULES VERIFICATION{Colors.END}")
        print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")

        results = {}

        for module_name, expected_attrs in self.core_modules.items():
            print(f"{Colors.BLUE}Testing {module_name}...{Colors.END}")

            # Try to import
            success, message, module = self.verify_import(module_name)

            if success:
                print(f"  {Colors.GREEN}✓ Import successful{Colors.END}")

                # Verify attributes
                attr_results = self.verify_attributes(module_name, module, expected_attrs)

                passed = sum(1 for _, exists, _ in attr_results if exists)
                total = len(attr_results)

                for attr_name, exists, msg in attr_results:
                    color = Colors.GREEN if exists else Colors.RED
                    print(f"  {color}{msg}{Colors.END}")

                results[module_name] = {
                    'import': True,
                    'attributes': attr_results,
                    'score': f"{passed}/{total}"
                }

                print(f"  {Colors.YELLOW}Score: {passed}/{total}{Colors.END}\n")
            else:
                print(f"  {Colors.RED}✗ {message}{Colors.END}\n")
                results[module_name] = {
                    'import': False,
                    'error': message
                }

        return results

    def test_system_modules(self) -> Dict[str, Any]:
        """Test all system modules."""
        print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}SYSTEM MODULES VERIFICATION{Colors.END}")
        print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")

        results = {}

        for module_name, expected_attrs in self.system_modules.items():
            print(f"{Colors.BLUE}Testing {module_name}...{Colors.END}")

            # Try to import
            success, message, module = self.verify_import(module_name)

            if success:
                print(f"  {Colors.GREEN}✓ Import successful{Colors.END}")

                # Verify attributes
                attr_results = self.verify_attributes(module_name, module, expected_attrs)

                passed = sum(1 for _, exists, _ in attr_results if exists)
                total = len(attr_results)

                for attr_name, exists, msg in attr_results:
                    color = Colors.GREEN if exists else Colors.RED
                    print(f"  {color}{msg}{Colors.END}")

                results[module_name] = {
                    'import': True,
                    'attributes': attr_results,
                    'score': f"{passed}/{total}"
                }

                print(f"  {Colors.YELLOW}Score: {passed}/{total}{Colors.END}\n")
            else:
                print(f"  {Colors.RED}✗ {message}{Colors.END}\n")
                results[module_name] = {
                    'import': False,
                    'error': message
                }

        return results

    def test_basic_functionality(self):
        """Test basic functionality of core components."""
        print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}BASIC FUNCTIONALITY TESTS{Colors.END}")
        print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")

        tests = []

        # Test 1: Database basic operations
        print(f"{Colors.BLUE}Testing Database basic operations...{Colors.END}")
        try:
            from core.database import Database
            db = Database(":memory:")

            # Test execute
            db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
            db.execute("INSERT INTO test (value) VALUES (?)", ("test",))

            # Test fetch
            rows = db.fetch_all("SELECT * FROM test")
            assert len(rows) > 0, "No rows returned"

            print(f"  {Colors.GREEN}✓ Database operations work{Colors.END}")
            tests.append(('Database', True, 'Operations successful'))
        except Exception as e:
            print(f"  {Colors.RED}✗ Database test failed: {e}{Colors.END}")
            tests.append(('Database', False, str(e)))

        # Test 2: Cache basic operations
        print(f"\n{Colors.BLUE}Testing Cache basic operations...{Colors.END}")
        try:
            from core.cache import LRUCache
            cache = LRUCache(max_size=100)

            cache.set("key1", "value1")
            value = cache.get("key1")
            assert value == "value1", f"Expected 'value1', got {value}"

            print(f"  {Colors.GREEN}✓ Cache operations work{Colors.END}")
            tests.append(('Cache', True, 'Operations successful'))
        except Exception as e:
            print(f"  {Colors.RED}✗ Cache test failed: {e}{Colors.END}")
            tests.append(('Cache', False, str(e)))

        # Test 3: Config loading
        print(f"\n{Colors.BLUE}Testing Config loading...{Colors.END}")
        try:
            from core.config import Config
            config = Config()
            config.validate()

            print(f"  {Colors.GREEN}✓ Config operations work{Colors.END}")
            tests.append(('Config', True, 'Operations successful'))
        except Exception as e:
            print(f"  {Colors.RED}✗ Config test failed: {e}{Colors.END}")
            tests.append(('Config', False, str(e)))

        # Test 4: Security validation
        print(f"\n{Colors.BLUE}Testing Security validation...{Colors.END}")
        try:
            from core.security import sanitize_sql_input, validate_table_name

            # Test SQL sanitization
            sanitized = sanitize_sql_input("test'value")

            # Test table name validation
            is_valid = validate_table_name("search_history")
            assert is_valid, "Should validate allowed table"

            print(f"  {Colors.GREEN}✓ Security operations work{Colors.END}")
            tests.append(('Security', True, 'Operations successful'))
        except Exception as e:
            print(f"  {Colors.RED}✗ Security test failed: {e}{Colors.END}")
            tests.append(('Security', False, str(e)))

        # Test 5: System modules
        print(f"\n{Colors.BLUE}Testing System modules...{Colors.END}")
        try:
            from system.elevation import ElevationManager
            elevation = ElevationManager()
            is_admin = elevation.is_admin()

            print(f"  {Colors.GREEN}✓ System modules work (is_admin={is_admin}){Colors.END}")
            tests.append(('System', True, f'is_admin={is_admin}'))
        except Exception as e:
            print(f"  {Colors.RED}✗ System test failed: {e}{Colors.END}")
            tests.append(('System', False, str(e)))

        return tests

    def print_summary(self, core_results: Dict, system_results: Dict, func_tests: List):
        """Print comprehensive summary."""
        print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")

        # Core modules summary
        core_passed = sum(1 for r in core_results.values() if r.get('import', False))
        core_total = len(core_results)

        print(f"{Colors.BOLD}Core Modules:{Colors.END}")
        print(f"  Total: {core_total}")
        print(f"  Passed: {core_passed}")
        print(f"  Failed: {core_total - core_passed}")
        print(f"  Success Rate: {100*core_passed/core_total:.1f}%\n")

        # System modules summary
        system_passed = sum(1 for r in system_results.values() if r.get('import', False))
        system_total = len(system_results)

        print(f"{Colors.BOLD}System Modules:{Colors.END}")
        print(f"  Total: {system_total}")
        print(f"  Passed: {system_passed}")
        print(f"  Failed: {system_total - system_passed}")
        print(f"  Success Rate: {100*system_passed/system_total:.1f}%\n")

        # Functionality tests summary
        func_passed = sum(1 for _, success, _ in func_tests if success)
        func_total = len(func_tests)

        print(f"{Colors.BOLD}Functionality Tests:{Colors.END}")
        print(f"  Total: {func_total}")
        print(f"  Passed: {func_passed}")
        print(f"  Failed: {func_total - func_passed}")
        print(f"  Success Rate: {100*func_passed/func_total:.1f}%\n")

        # Overall
        total_tests = core_total + system_total + func_total
        total_passed = core_passed + system_passed + func_passed

        print(f"{Colors.BOLD}Overall:{Colors.END}")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {total_passed}")
        print(f"  Failed: {total_tests - total_passed}")

        if total_passed == total_tests:
            print(f"\n{Colors.GREEN}{Colors.BOLD}ALL TESTS PASSED!{Colors.END}")
            return True
        else:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}SOME TESTS FAILED{Colors.END}")
            return False


def main():
    """Main test runner."""
    verifier = ModuleVerifier()

    # Run all tests
    core_results = verifier.test_core_modules()
    system_results = verifier.test_system_modules()
    func_tests = verifier.test_basic_functionality()

    # Print summary
    all_passed = verifier.print_summary(core_results, system_results, func_tests)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
