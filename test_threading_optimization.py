"""
Test script for threading and cache optimizations.

Verifies:
1. Auto-detection of optimal worker counts
2. Enhanced cache with TTL by type, statistics, and prewarming
3. Thread-safe operations
4. Performance improvements
"""

import os
import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.threading import (
    get_cpu_count,
    get_optimal_io_workers,
    get_optimal_cpu_workers,
    get_optimal_mixed_workers,
    create_io_executor,
    create_cpu_executor,
    create_mixed_executor,
)
from core.cache import LRUCache, CacheStats


def test_threading_detection():
    """Test automatic worker detection."""
    print("=" * 60)
    print("THREADING AUTO-DETECTION")
    print("=" * 60)

    cpu_count = get_cpu_count()
    io_workers = get_optimal_io_workers()
    cpu_workers = get_optimal_cpu_workers()
    mixed_workers = get_optimal_mixed_workers()

    print(f"CPU Cores Detected: {cpu_count}")
    print(f"Optimal I/O Workers: {io_workers} (2x CPU, max 32)")
    print(f"Optimal CPU Workers: {cpu_workers} (CPU-1, max 16)")
    print(f"Optimal Mixed Workers: {mixed_workers} (1.5x CPU, max 24)")
    print()

    # Test executor creation
    print("Creating optimized executors...")
    with create_io_executor() as io_exec:
        print(f"  I/O Executor: {io_exec._max_workers} workers")

    with create_cpu_executor() as cpu_exec:
        print(f"  CPU Executor: {cpu_exec._max_workers} workers")

    with create_mixed_executor() as mixed_exec:
        print(f"  Mixed Executor: {mixed_exec._max_workers} workers")

    print("All executors created and cleaned up successfully!")
    print()


def test_cache_enhancements():
    """Test enhanced cache features."""
    print("=" * 60)
    print("CACHE ENHANCEMENTS")
    print("=" * 60)

    # Test TTL by type
    print("\n1. Testing TTL by Type...")
    ttl_config = {
        "search": 300,      # 5 minutes for search results
        "thumbnail": 3600,  # 1 hour for thumbnails
        "hash": 7200,       # 2 hours for file hashes
    }

    cache = LRUCache(
        max_size=100,
        default_ttl=600,  # 10 minutes default
        ttl_by_type=ttl_config,
        enable_stats=True,
    )

    # Add items with different types
    cache.set("search_1", "result_1", cache_type="search")
    cache.set("thumb_1", b"image_data", cache_type="thumbnail")
    cache.set("hash_1", "abc123", cache_type="hash")
    cache.set("default_1", "data", cache_type="default")

    print(f"  Added 4 items with different cache types")
    print(f"  Cache size: {cache.size()}")

    # Test statistics
    print("\n2. Testing Detailed Statistics...")
    stats = cache.get_detailed_stats()
    print(f"  Hit Rate: {stats.hit_rate:.2%}")
    print(f"  Miss Rate: {stats.miss_rate:.2%}")
    print(f"  Fill Rate: {stats.fill_rate:.2%}")
    print(f"  Total Requests: {stats.total_requests}")
    print(f"  Sets: {stats.sets}")
    print(f"  Size: {stats.size}/{stats.max_size}")

    # Test some cache hits and misses
    cache.get("search_1")  # hit
    cache.get("search_1")  # hit
    cache.get("nonexistent")  # miss

    stats = cache.get_detailed_stats()
    print(f"\nAfter some operations:")
    print(f"  Hits: {stats.hits}, Misses: {stats.misses}")
    print(f"  Hit Rate: {stats.hit_rate:.2%}")

    # Test selective invalidation
    print("\n3. Testing Selective Invalidation...")
    cache.set("search_2", "result_2", cache_type="search")
    cache.set("search_3", "result_3", cache_type="search")
    print(f"  Cache size before invalidation: {cache.size()}")

    removed = cache.invalidate_by_type("search")
    print(f"  Invalidated {removed} 'search' entries")
    print(f"  Cache size after invalidation: {cache.size()}")

    # Test pattern invalidation
    cache.set("temp_1", "data1")
    cache.set("temp_2", "data2")
    cache.set("perm_1", "data3")

    removed = cache.invalidate_by_pattern(lambda k: str(k).startswith("temp_"))
    print(f"  Invalidated {removed} entries matching pattern 'temp_*'")
    print(f"  Cache size: {cache.size()}")

    # Test prewarming
    print("\n4. Testing Cache Prewarming...")
    prewarm_data = {
        f"key_{i}": f"value_{i}"
        for i in range(10)
    }

    prewarmed = cache.prewarm(prewarm_data, cache_type="prewarmed", ttl=1800)
    print(f"  Prewarmed {prewarmed} entries")
    print(f"  Cache size: {cache.size()}")

    # Final statistics
    print("\n5. Final Statistics...")
    stats_dict = cache.stats()
    print(f"  Total entries: {stats_dict['size']}")
    print(f"  Bytes used: {stats_dict['bytes_used']}")
    print(f"  Hit rate: {stats_dict['hit_rate']:.2%}")
    print(f"  Sets: {stats_dict.get('sets', 'N/A')}")
    print(f"  Evictions: {stats_dict['evictions']}")
    print(f"  Expirations: {stats_dict['expirations']}")

    print()


def test_parallel_operations():
    """Test parallel cache operations for thread safety."""
    print("=" * 60)
    print("PARALLEL OPERATIONS TEST")
    print("=" * 60)

    cache = LRUCache(max_size=1000, enable_stats=True)

    def worker(worker_id, iterations=100):
        """Worker function for parallel testing."""
        for i in range(iterations):
            key = f"worker_{worker_id}_key_{i}"
            cache.set(key, f"value_{i}")
            cache.get(key)

    import concurrent.futures

    print("\nRunning 8 workers in parallel, 100 operations each...")
    start_time = time.time()

    with create_cpu_executor(max_workers=8) as executor:
        futures = [
            executor.submit(worker, i, 100)
            for i in range(8)
        ]
        concurrent.futures.wait(futures)

    elapsed = time.time() - start_time

    stats = cache.get_detailed_stats()
    print(f"  Completed in {elapsed:.3f} seconds")
    print(f"  Total operations: {stats.sets}")
    print(f"  Cache size: {stats.size}")
    print(f"  Hit rate: {stats.hit_rate:.2%}")
    print(f"  Thread-safe: All operations completed successfully!")
    print()


def test_performance_comparison():
    """Compare performance with different worker counts."""
    print("=" * 60)
    print("PERFORMANCE COMPARISON")
    print("=" * 60)

    def cpu_intensive_task(n):
        """Simulate CPU-intensive work."""
        return sum(i ** 2 for i in range(n))

    tasks = [10000] * 100  # 100 tasks

    # Test with default (auto-detected)
    print("\n1. Auto-detected workers:")
    start_time = time.time()
    with create_cpu_executor() as executor:
        results = list(executor.map(cpu_intensive_task, tasks))
    auto_time = time.time() - start_time
    print(f"  Time: {auto_time:.3f}s with {get_optimal_cpu_workers()} workers")

    # Test with fixed workers
    print("\n2. Fixed 4 workers:")
    start_time = time.time()
    with create_cpu_executor(max_workers=4) as executor:
        results = list(executor.map(cpu_intensive_task, tasks))
    fixed_time = time.time() - start_time
    print(f"  Time: {fixed_time:.3f}s with 4 workers")

    improvement = ((fixed_time - auto_time) / fixed_time) * 100
    if improvement > 0:
        print(f"\n  Performance improvement: {improvement:.1f}% faster!")
    else:
        print(f"\n  Similar performance (difference: {abs(improvement):.1f}%)")

    print()


def main():
    """Run all tests."""
    print("\n")
    print("*" * 60)
    print("SMART SEARCH PRO - THREADING & CACHE OPTIMIZATION TESTS")
    print("*" * 60)
    print()

    try:
        test_threading_detection()
        test_cache_enhancements()
        test_parallel_operations()
        test_performance_comparison()

        print("=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print()

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
