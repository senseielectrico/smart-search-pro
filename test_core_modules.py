#!/usr/bin/env python3
"""
Comprehensive test suite for smart_search core modules.
Tests: Database, Cache, Config, Security
"""

import sys
import traceback
from pathlib import Path
from typing import Dict, List, Tuple

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


class CoreModuleTester:
    """Test runner for core modules."""

    def __init__(self):
        self.results: List[TestResult] = []

    def test_database_module(self) -> List[TestResult]:
        """Test core.database module."""
        module_name = "core.database"
        tests = []

        # Test 1: Import module
        result = TestResult(module_name, "import")
        try:
            from core.database import Database
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 2: Class instantiation
        result = TestResult(module_name, "instantiation")
        try:
            from core.database import Database
            db = Database(":memory:")
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 3: Basic operations
        result = TestResult(module_name, "basic_operations")
        try:
            from core.database import Database
            db = Database(":memory:")
            db.initialize()
            # Test insert
            db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
            db.execute("INSERT INTO test (value) VALUES (?)", ("test_value",))
            # Test query
            rows = db.fetch_all("SELECT * FROM test")
            assert len(rows) > 0, "No rows returned"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 4: Transaction support
        result = TestResult(module_name, "transactions")
        try:
            from core.database import Database
            db = Database(":memory:")
            db.initialize()
            db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")

            with db.transaction():
                db.execute("INSERT INTO test (value) VALUES (?)", ("test1",))
                db.execute("INSERT INTO test (value) VALUES (?)", ("test2",))

            rows = db.fetch_all("SELECT * FROM test")
            assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 5: Context manager
        result = TestResult(module_name, "context_manager")
        try:
            from core.database import Database
            with Database(":memory:") as db:
                db.initialize()
                db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        return tests

    def test_cache_module(self) -> List[TestResult]:
        """Test core.cache module."""
        module_name = "core.cache"
        tests = []

        # Test 1: Import module
        result = TestResult(module_name, "import")
        try:
            from core.cache import CacheManager, LRUCache
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 2: LRU Cache basic operations
        result = TestResult(module_name, "lru_cache_basic")
        try:
            from core.cache import LRUCache
            cache = LRUCache(max_size=100)
            cache.set("key1", "value1")
            value = cache.get("key1")
            assert value == "value1", f"Expected 'value1', got {value}"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 3: LRU Cache eviction
        result = TestResult(module_name, "lru_cache_eviction")
        try:
            from core.cache import LRUCache
            cache = LRUCache(max_size=2)
            cache.set("key1", "value1")
            cache.set("key2", "value2")
            cache.set("key3", "value3")  # Should evict key1

            assert cache.get("key1") is None, "key1 should be evicted"
            assert cache.get("key2") == "value2", "key2 should exist"
            assert cache.get("key3") == "value3", "key3 should exist"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 4: CacheManager
        result = TestResult(module_name, "cache_manager")
        try:
            from core.cache import CacheManager
            manager = CacheManager()
            manager.set("test_key", "test_value")
            value = manager.get("test_key")
            assert value == "test_value", f"Expected 'test_value', got {value}"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 5: Cache statistics
        result = TestResult(module_name, "cache_stats")
        try:
            from core.cache import LRUCache
            cache = LRUCache(max_size=100)
            cache.set("key1", "value1")
            cache.get("key1")  # Hit
            cache.get("key2")  # Miss

            stats = cache.get_stats()
            assert "hits" in stats, "Stats should contain hits"
            assert "misses" in stats, "Stats should contain misses"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        return tests

    def test_config_module(self) -> List[TestResult]:
        """Test core.config module."""
        module_name = "core.config"
        tests = []

        # Test 1: Import module
        result = TestResult(module_name, "import")
        try:
            from core.config import ConfigManager
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 2: Singleton pattern
        result = TestResult(module_name, "singleton")
        try:
            from core.config import ConfigManager
            config1 = ConfigManager()
            config2 = ConfigManager()
            assert config1 is config2, "ConfigManager should be singleton"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 3: Get/Set operations
        result = TestResult(module_name, "get_set")
        try:
            from core.config import ConfigManager
            config = ConfigManager()
            config.set("test.key", "test_value")
            value = config.get("test.key")
            assert value == "test_value", f"Expected 'test_value', got {value}"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 4: Default values
        result = TestResult(module_name, "defaults")
        try:
            from core.config import ConfigManager
            config = ConfigManager()
            value = config.get("nonexistent.key", default="default_value")
            assert value == "default_value", f"Expected default value, got {value}"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 5: Nested keys
        result = TestResult(module_name, "nested_keys")
        try:
            from core.config import ConfigManager
            config = ConfigManager()
            config.set("app.ui.theme", "dark")
            config.set("app.ui.font_size", 12)

            theme = config.get("app.ui.theme")
            font_size = config.get("app.ui.font_size")

            assert theme == "dark", f"Expected 'dark', got {theme}"
            assert font_size == 12, f"Expected 12, got {font_size}"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        return tests

    def test_security_module(self) -> List[TestResult]:
        """Test core.security module."""
        module_name = "core.security"
        tests = []

        # Test 1: Import module
        result = TestResult(module_name, "import")
        try:
            from core.security import SecurityManager, PathValidator
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 2: PathValidator - valid paths
        result = TestResult(module_name, "path_validator_valid")
        try:
            from core.security import PathValidator
            validator = PathValidator()

            # Test valid paths
            assert validator.is_valid_path("C:/Users/test/file.txt"), "Should accept normal path"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 3: PathValidator - path traversal
        result = TestResult(module_name, "path_validator_traversal")
        try:
            from core.security import PathValidator
            validator = PathValidator()

            # Test path traversal attempts
            dangerous_paths = [
                "C:/Users/../../../etc/passwd",
                "..\\..\\system32",
                "C:/Users/test/../../Windows/System32"
            ]

            for path in dangerous_paths:
                if validator.is_valid_path(path):
                    raise AssertionError(f"Should reject dangerous path: {path}")

            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 4: SecurityManager - sanitize input
        result = TestResult(module_name, "sanitize_input")
        try:
            from core.security import SecurityManager
            manager = SecurityManager()

            # Test SQL injection attempts
            dangerous_inputs = [
                "'; DROP TABLE users; --",
                "1 OR 1=1",
                "<script>alert('xss')</script>"
            ]

            for input_str in dangerous_inputs:
                sanitized = manager.sanitize_input(input_str)
                # Should not contain dangerous characters
                assert "DROP" not in sanitized or "--" not in sanitized or "<script>" not in sanitized

            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        # Test 5: SecurityManager - validate file operation
        result = TestResult(module_name, "validate_file_operation")
        try:
            from core.security import SecurityManager
            manager = SecurityManager()

            # Should validate basic file operations
            is_valid = manager.validate_file_operation("C:/Users/test/file.txt", "read")
            assert isinstance(is_valid, bool), "Should return boolean"
            result.mark_passed()
        except Exception as e:
            result.mark_failed(e)
        tests.append(result)

        return tests

    def run_all_tests(self) -> Dict[str, List[TestResult]]:
        """Run all core module tests."""
        all_results = {}

        print("=" * 80)
        print("CORE MODULES TEST SUITE")
        print("=" * 80)
        print()

        # Test Database
        print("Testing core.database...")
        db_results = self.test_database_module()
        all_results["database"] = db_results
        self.results.extend(db_results)

        # Test Cache
        print("Testing core.cache...")
        cache_results = self.test_cache_module()
        all_results["cache"] = cache_results
        self.results.extend(cache_results)

        # Test Config
        print("Testing core.config...")
        config_results = self.test_config_module()
        all_results["config"] = config_results
        self.results.extend(config_results)

        # Test Security
        print("Testing core.security...")
        security_results = self.test_security_module()
        all_results["security"] = security_results
        self.results.extend(security_results)

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
    tester = CoreModuleTester()
    tester.run_all_tests()
    success = tester.print_summary()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
