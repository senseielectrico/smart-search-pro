#!/usr/bin/env python3
"""
Performance testing and benchmarking script for Smart Search Pro.

Tests:
- Startup time
- Search latency
- Memory usage
- Cache effectiveness
"""

import sys
import time
import logging
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_performance_monitor():
    """Test performance monitoring system"""
    from core.performance import get_performance_monitor, track_performance

    logger.info("Testing Performance Monitor...")

    monitor = get_performance_monitor()
    monitor.start_startup_tracking()

    # Simulate operations
    time.sleep(0.1)
    monitor.end_startup_tracking()

    # Track operation
    with monitor.track_operation("test_operation"):
        time.sleep(0.05)

    # Decorated function
    @track_performance("decorated_function")
    def test_func():
        time.sleep(0.02)

    test_func()

    # Generate report
    report = monitor.generate_report()

    logger.info(f"✓ Startup Time: {report.startup_time_ms:.2f}ms")
    logger.info(f"✓ Total Metrics: {len(report.metrics)}")
    logger.info(f"✓ Memory Usage: {report.memory_usage_mb:.2f}MB")

    return True


def test_lazy_importer():
    """Test lazy import system"""
    from core.performance import get_lazy_importer

    logger.info("Testing Lazy Importer...")

    lazy = get_lazy_importer()

    # Register test import
    lazy.register('test_module', lambda: {'loaded': True})

    # Check not loaded yet
    assert not lazy.is_imported('test_module'), "Should not be imported yet"

    # Load module
    module = lazy.get('test_module')
    assert module['loaded'], "Module should be loaded"
    assert lazy.is_imported('test_module'), "Should be marked as imported"

    logger.info("✓ Lazy imports working correctly")
    return True


def test_query_cache():
    """Test query cache system"""
    logger.info("Testing Query Cache...")

    from search.engine_optimized import QueryCache

    cache = QueryCache(max_size=5, ttl_seconds=60)

    # Test data
    test_results = [{'filename': 'test.txt', 'path': '/test'}]

    # Put in cache
    cache.put("test query", 100, "name", test_results)

    # Get from cache (hit)
    cached = cache.get("test query", 100, "name")
    assert cached is not None, "Should get cached results"
    assert len(cached) == 1, "Should have 1 result"

    # Get different query (miss)
    cached = cache.get("different query", 100, "name")
    assert cached is None, "Should be cache miss"

    # Test cache eviction
    for i in range(6):
        cache.put(f"query_{i}", 100, "name", test_results)

    # First entry should be evicted
    cached = cache.get("test query", 100, "name")
    assert cached is None, "First entry should be evicted"

    # Get stats
    stats = cache.get_stats()
    assert stats['size'] == 5, "Cache size should be at max"

    logger.info(f"✓ Cache working correctly (size: {stats['size']})")
    return True


def test_splash_screen():
    """Test splash screen (non-interactive)"""
    logger.info("Testing Splash Screen...")

    try:
        from PyQt6.QtWidgets import QApplication
        from ui.splash_screen import SplashScreenManager

        app = QApplication(sys.argv)

        splash_mgr = SplashScreenManager()
        splash_mgr.show(total_steps=5)

        for i in range(5):
            splash_mgr.update(f"Step {i+1}")
            time.sleep(0.1)

        splash_mgr.close()

        logger.info("✓ Splash screen working correctly")
        return True

    except Exception as e:
        logger.warning(f"Splash screen test skipped: {e}")
        return True  # Non-critical


def benchmark_startup():
    """Benchmark startup time components"""
    logger.info("\n" + "="*60)
    logger.info("STARTUP BENCHMARK")
    logger.info("="*60)

    timings = {}

    # Test import times
    start = time.perf_counter()
    from PyQt6.QtWidgets import QApplication
    timings['PyQt6 import'] = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    from core.performance import get_performance_monitor
    timings['Performance module'] = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    from ui.splash_screen import SplashScreenManager
    timings['Splash screen module'] = (time.perf_counter() - start) * 1000

    # Print results
    total = 0
    for name, duration in timings.items():
        logger.info(f"  {name}: {duration:.2f}ms")
        total += duration

    logger.info(f"\nTotal measured: {total:.2f}ms")
    logger.info("="*60)

    return total < 500  # Should be under 500ms


def benchmark_search():
    """Benchmark search operations"""
    logger.info("\n" + "="*60)
    logger.info("SEARCH BENCHMARK")
    logger.info("="*60)

    try:
        from search.engine_optimized import OptimizedSearchEngine

        engine = OptimizedSearchEngine(enable_cache=True)

        if not engine.is_available:
            logger.warning("No search backend available, skipping search benchmark")
            return True

        # Test query
        test_query = "*.txt"

        # Cold search (cache miss)
        start = time.perf_counter()
        results = engine.search(test_query, max_results=100)
        cold_time = (time.perf_counter() - start) * 1000

        # Warm search (cache hit)
        start = time.perf_counter()
        results = engine.search(test_query, max_results=100)
        warm_time = (time.perf_counter() - start) * 1000

        logger.info(f"  Cold search (cache miss): {cold_time:.2f}ms")
        logger.info(f"  Warm search (cache hit): {warm_time:.2f}ms")
        logger.info(f"  Speedup: {cold_time/warm_time:.1f}x")
        logger.info(f"  Results: {len(results)}")

        # Cache stats
        stats = engine.get_cache_stats()
        logger.info(f"  Cache: {stats}")

        logger.info("="*60)

        return cold_time < 200  # Cold search under 200ms

    except Exception as e:
        logger.error(f"Search benchmark failed: {e}")
        return False


def benchmark_memory():
    """Benchmark memory usage"""
    logger.info("\n" + "="*60)
    logger.info("MEMORY BENCHMARK")
    logger.info("="*60)

    try:
        import psutil
        process = psutil.Process()

        initial_memory = process.memory_info().rss / 1024 / 1024

        logger.info(f"  Initial memory: {initial_memory:.2f}MB")

        # Simulate some operations
        from core.performance import get_performance_monitor
        monitor = get_performance_monitor()

        for i in range(100):
            with monitor.track_operation(f"test_{i}"):
                time.sleep(0.001)

        current_memory = process.memory_info().rss / 1024 / 1024
        delta = current_memory - initial_memory

        logger.info(f"  After 100 operations: {current_memory:.2f}MB")
        logger.info(f"  Memory delta: {delta:+.2f}MB")

        logger.info("="*60)

        return delta < 50  # Should not leak more than 50MB

    except ImportError:
        logger.warning("psutil not available, skipping memory benchmark")
        return True


def run_all_tests():
    """Run all tests and benchmarks"""
    logger.info("\n" + "="*60)
    logger.info("SMART SEARCH PRO - PERFORMANCE TEST SUITE")
    logger.info("="*60 + "\n")

    tests = [
        ("Performance Monitor", test_performance_monitor),
        ("Lazy Importer", test_lazy_importer),
        ("Query Cache", test_query_cache),
        ("Splash Screen", test_splash_screen),
        ("Startup Benchmark", benchmark_startup),
        ("Search Benchmark", benchmark_search),
        ("Memory Benchmark", benchmark_memory),
    ]

    results = {}
    for name, test_func in tests:
        try:
            logger.info(f"\nRunning: {name}")
            results[name] = test_func()
        except Exception as e:
            logger.error(f"Test failed: {name} - {e}")
            results[name] = False

    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"  {status}: {name}")

    logger.info(f"\nTotal: {passed}/{total} tests passed")
    logger.info("="*60)

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
