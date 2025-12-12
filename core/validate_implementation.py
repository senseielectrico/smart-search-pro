"""
Validation script for Smart Search Pro core module.

Performs comprehensive checks to ensure all components are
production-ready and meet requirements.
"""

import sys
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def validate_imports():
    """Validate all imports work correctly."""
    print("Validating imports...")

    try:
        from core import (
            # Config
            Config,
            DatabaseConfig,
            CacheConfig,
            SearchConfig,
            LoggingConfig,
            UIConfig,
            PerformanceConfig,
            IntegrationConfig,
            # Database
            Database,
            ConnectionPool,
            Migration,
            # Cache
            LRUCache,
            CacheManager,
            # Event Bus
            EventBus,
            Event,
            EventPriority,
            # Logger
            StructuredLogger,
            LoggerManager,
            # Exceptions
            SmartSearchError,
            DatabaseError,
            CacheError,
            SearchError,
            # Functions
            initialize,
            get_config,
            get_logger,
            get_cache,
            get_event_bus,
        )
        print("  ✓ All imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def validate_type_hints():
    """Validate type hints are present."""
    print("\nValidating type hints...")

    import inspect
    from core import Database, LRUCache, EventBus, Config

    classes_to_check = [Database, LRUCache, EventBus, Config]
    total_methods = 0
    typed_methods = 0

    for cls in classes_to_check:
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if name.startswith("_") and name != "__init__":
                continue
            total_methods += 1
            sig = inspect.signature(method)
            if sig.return_annotation != inspect.Signature.empty:
                typed_methods += 1

    coverage = (typed_methods / total_methods * 100) if total_methods > 0 else 0
    print(f"  Type hint coverage: {coverage:.1f}% ({typed_methods}/{total_methods})")

    if coverage >= 80:
        print("  ✓ Type hint coverage is good")
        return True
    else:
        print("  ✗ Type hint coverage is low")
        return False


def validate_docstrings():
    """Validate docstrings are present."""
    print("\nValidating docstrings...")

    import inspect
    from core import Database, LRUCache, EventBus, Config, logger, cache

    modules_to_check = [Database, LRUCache, EventBus, Config]
    total_items = 0
    documented_items = 0

    for item in modules_to_check:
        if inspect.isclass(item):
            total_items += 1
            if item.__doc__:
                documented_items += 1

            for name, method in inspect.getmembers(item, predicate=inspect.isfunction):
                if name.startswith("_") and name != "__init__":
                    continue
                total_items += 1
                if method.__doc__:
                    documented_items += 1

    coverage = (documented_items / total_items * 100) if total_items > 0 else 0
    print(f"  Documentation coverage: {coverage:.1f}% ({documented_items}/{total_items})")

    if coverage >= 80:
        print("  ✓ Documentation coverage is good")
        return True
    else:
        print("  ✗ Documentation coverage is low")
        return False


def validate_database_schema():
    """Validate database schema is correct."""
    print("\nValidating database schema...")

    import tempfile
    from core import Database

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    try:
        db = Database(db_path)

        required_tables = [
            "search_history",
            "saved_searches",
            "hash_cache",
            "file_tags",
            "settings",
            "operation_history",
            "preview_cache",
            "schema_version",
        ]

        stats = db.get_stats()
        existing_tables = list(stats["tables"].keys())

        missing_tables = set(required_tables) - set(existing_tables)

        if missing_tables:
            print(f"  ✗ Missing tables: {missing_tables}")
            db.close()
            db_path.unlink()
            return False

        print(f"  ✓ All {len(required_tables)} required tables present")

        # Validate schema version
        if stats["schema_version"] != 1:
            print(f"  ✗ Wrong schema version: {stats['schema_version']}")
            db.close()
            db_path.unlink()
            return False

        print("  ✓ Schema version is correct")

        db.close()
        db_path.unlink()
        return True

    except Exception as e:
        print(f"  ✗ Database validation failed: {e}")
        if db_path.exists():
            db_path.unlink()
        return False


def validate_functionality():
    """Validate basic functionality of all components."""
    print("\nValidating functionality...")

    import tempfile
    import time
    from core import initialize, get_cache, get_event_bus, publish, subscribe

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config_file = tmp_path / "config.yaml"

        try:
            # Initialize
            from core import Config
            config = Config()
            config.data_dir = str(tmp_path / "data")
            config.save(config_file)

            loaded_config, db = initialize(
                config_path=str(config_file),
                log_dir=None,
                log_level="ERROR",  # Quiet mode
            )

            print("  ✓ Initialization works")

            # Test cache
            cache = get_cache("test", max_size=10)
            cache.set("key", "value")
            assert cache.get("key") == "value"
            print("  ✓ Cache works")

            # Test events
            results = []
            subscribe("test.event", lambda e: results.append(e.data))
            publish("test.event", {"value": 42})
            assert len(results) == 1
            print("  ✓ Event bus works")

            # Test database
            row_id = db.insert("search_history", {
                "query": "test",
                "query_type": "text",
                "result_count": 1,
                "execution_time": 0.1,
                "timestamp": time.time()
            })
            assert row_id > 0
            print("  ✓ Database works")

            db.close()
            return True

        except Exception as e:
            print(f"  ✗ Functionality test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def validate_thread_safety():
    """Validate thread safety of components."""
    print("\nValidating thread safety...")

    import threading
    import time
    from core import LRUCache

    cache = LRUCache[str, int](max_size=100)
    errors = []

    def worker(worker_id):
        try:
            for i in range(100):
                cache.set(f"key{worker_id}_{i}", i)
                value = cache.get(f"key{worker_id}_{i}")
                assert value == i or value is None  # May be evicted
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    if errors:
        print(f"  ✗ Thread safety issues: {errors}")
        return False

    print("  ✓ Cache is thread-safe")
    return True


def validate_files():
    """Validate all required files exist."""
    print("\nValidating files...")

    core_dir = Path(__file__).parent
    required_files = [
        "__init__.py",
        "exceptions.py",
        "logger.py",
        "config.py",
        "cache.py",
        "eventbus.py",
        "database.py",
        "test_core.py",
        "requirements.txt",
        "README.md",
        "config.example.yaml",
    ]

    missing_files = []
    for file in required_files:
        if not (core_dir / file).exists():
            missing_files.append(file)

    if missing_files:
        print(f"  ✗ Missing files: {missing_files}")
        return False

    print(f"  ✓ All {len(required_files)} required files present")
    return True


def validate_performance():
    """Validate performance characteristics."""
    print("\nValidating performance...")

    import time
    from core import LRUCache

    # Cache performance
    cache = LRUCache[int, str](max_size=10000)

    start = time.time()
    for i in range(10000):
        cache.set(i, f"value{i}")
    set_time = time.time() - start

    start = time.time()
    for i in range(10000):
        cache.get(i)
    get_time = time.time() - start

    print(f"  Cache set: {set_time:.3f}s (10k ops)")
    print(f"  Cache get: {get_time:.3f}s (10k ops)")

    if set_time > 1.0 or get_time > 1.0:
        print("  ✗ Cache performance is slow")
        return False

    print("  ✓ Cache performance is good")
    return True


def main():
    """Run all validations."""
    print("=" * 70)
    print("SMART SEARCH PRO - CORE MODULE VALIDATION")
    print("=" * 70)

    validations = [
        ("Imports", validate_imports),
        ("Type Hints", validate_type_hints),
        ("Docstrings", validate_docstrings),
        ("Database Schema", validate_database_schema),
        ("Functionality", validate_functionality),
        ("Thread Safety", validate_thread_safety),
        ("Files", validate_files),
        ("Performance", validate_performance),
    ]

    results = {}
    for name, validator in validations:
        try:
            results[name] = validator()
        except Exception as e:
            print(f"\n✗ {name} validation crashed: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {name}")

    print("=" * 70)
    print(f"RESULT: {passed}/{total} validations passed ({passed/total*100:.1f}%)")
    print("=" * 70)

    if passed == total:
        print("\n✓✓✓ ALL VALIDATIONS PASSED - PRODUCTION READY ✓✓✓\n")
        return 0
    else:
        print(f"\n✗✗✗ {total - passed} VALIDATION(S) FAILED ✗✗✗\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
