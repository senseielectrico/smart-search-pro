"""
Everything SDK Performance Benchmark

Comprehensive performance testing and comparison between:
- Everything SDK (primary)
- Windows Search (fallback)
- Cached vs uncached results
"""

import time
import statistics
from typing import List, Tuple
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from search.everything_sdk import (
    EverythingSDK,
    EverythingSort,
    get_everything_instance,
)


class Benchmark:
    """Performance benchmark runner."""

    def __init__(self):
        self.results = []

    def run(self, name: str, func, iterations: int = 5) -> dict:
        """Run benchmark and collect timing data."""
        print(f"\n{name}...")

        times = []
        result_counts = []

        for i in range(iterations):
            start = time.perf_counter()
            results = func()
            elapsed = time.perf_counter() - start

            times.append(elapsed * 1000)  # Convert to ms
            result_counts.append(len(results))

            # Progress indicator
            print(f"  Run {i+1}/{iterations}: {elapsed*1000:.2f}ms, {len(results)} results")

        stats = {
            "name": name,
            "iterations": iterations,
            "min_ms": min(times),
            "max_ms": max(times),
            "avg_ms": statistics.mean(times),
            "median_ms": statistics.median(times),
            "stddev_ms": statistics.stdev(times) if len(times) > 1 else 0,
            "total_results": statistics.mean(result_counts),
        }

        self.results.append(stats)
        return stats

    def print_summary(self):
        """Print benchmark summary table."""
        print("\n" + "=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)

        print(f"\n{'Test Name':<40} {'Avg (ms)':<12} {'Min (ms)':<12} {'Max (ms)':<12} {'Results':<10}")
        print("-" * 86)

        for stat in self.results:
            print(
                f"{stat['name']:<40} "
                f"{stat['avg_ms']:>10.2f}  "
                f"{stat['min_ms']:>10.2f}  "
                f"{stat['max_ms']:>10.2f}  "
                f"{stat['total_results']:>8.0f}"
            )

        print("\n" + "=" * 80)


def benchmark_basic_queries(sdk: EverythingSDK, bench: Benchmark):
    """Benchmark basic query types."""
    print("\n" + "=" * 80)
    print("BENCHMARK 1: Basic Queries")
    print("=" * 80)

    queries = [
        ("Simple wildcard (*.py)", "*.py", 100),
        ("Extension filter (ext:py)", "ext:py", 100),
        ("Multiple extensions (ext:py;js;ts)", "ext:py;js;ts", 100),
        ("Text search (test)", "test", 50),
        ("Folder search (folder:)", "folder:", 50),
    ]

    for name, query, max_results in queries:
        bench.run(
            name,
            lambda q=query, m=max_results: sdk.search(q, max_results=m),
            iterations=5
        )


def benchmark_advanced_queries(sdk: EverythingSDK, bench: Benchmark):
    """Benchmark advanced query features."""
    print("\n" + "=" * 80)
    print("BENCHMARK 2: Advanced Queries")
    print("=" * 80)

    queries = [
        ("Size filter (size:>10mb)", "size:>10mb", 50),
        ("Date filter (dm:today)", "dm:today", 50),
        ("Path filter (C:\\Users\\)", "C:\\Users\\", 100),
        ("Boolean NOT (!*.tmp)", "!*.tmp", 100),
        ("Case sensitive (Test)", "Test", 50, True),
    ]

    for query_data in queries:
        name, query, max_results = query_data[:3]
        match_case = query_data[3] if len(query_data) > 3 else False

        bench.run(
            name,
            lambda q=query, m=max_results, mc=match_case: sdk.search(
                q, max_results=m, match_case=mc
            ),
            iterations=5
        )


def benchmark_sorting(sdk: EverythingSDK, bench: Benchmark):
    """Benchmark different sort orders."""
    print("\n" + "=" * 80)
    print("BENCHMARK 3: Sorting")
    print("=" * 80)

    sorts = [
        ("Sort by name", EverythingSort.NAME_ASCENDING),
        ("Sort by path", EverythingSort.PATH_ASCENDING),
        ("Sort by size", EverythingSort.SIZE_DESCENDING),
        ("Sort by date modified", EverythingSort.DATE_MODIFIED_DESCENDING),
    ]

    for name, sort_order in sorts:
        bench.run(
            name,
            lambda s=sort_order: sdk.search("*.dll", max_results=100, sort=s),
            iterations=5
        )


def benchmark_result_counts(sdk: EverythingSDK, bench: Benchmark):
    """Benchmark different result set sizes."""
    print("\n" + "=" * 80)
    print("BENCHMARK 4: Result Set Sizes")
    print("=" * 80)

    counts = [10, 50, 100, 500, 1000]

    for count in counts:
        bench.run(
            f"Results: {count}",
            lambda c=count: sdk.search("*.txt", max_results=c),
            iterations=5
        )


def benchmark_caching(sdk: EverythingSDK, bench: Benchmark):
    """Benchmark caching performance."""
    print("\n" + "=" * 80)
    print("BENCHMARK 5: Caching")
    print("=" * 80)

    query = "*.json"

    # Uncached
    sdk.clear_cache()
    bench.run(
        "Uncached search",
        lambda: sdk.search(query, max_results=100),
        iterations=5
    )

    # Cached (prime cache first)
    sdk.search(query, max_results=100)
    bench.run(
        "Cached search",
        lambda: sdk.search(query, max_results=100),
        iterations=5
    )

    # Calculate speedup
    uncached_avg = bench.results[-2]["avg_ms"]
    cached_avg = bench.results[-1]["avg_ms"]
    speedup = uncached_avg / cached_avg if cached_avg > 0 else 0

    print(f"\nCache speedup: {speedup:.0f}x")


def benchmark_pagination(sdk: EverythingSDK, bench: Benchmark):
    """Benchmark pagination."""
    print("\n" + "=" * 80)
    print("BENCHMARK 6: Pagination")
    print("=" * 80)

    page_size = 100
    offsets = [0, 100, 500, 1000]

    for offset in offsets:
        bench.run(
            f"Offset: {offset}",
            lambda o=offset: sdk.search("*.log", max_results=page_size, offset=o),
            iterations=5
        )


def benchmark_concurrent_searches(sdk: EverythingSDK, bench: Benchmark):
    """Benchmark concurrent search performance."""
    print("\n" + "=" * 80)
    print("BENCHMARK 7: Concurrent Searches")
    print("=" * 80)

    import threading

    def run_concurrent(num_threads: int):
        results_container = []
        threads = []

        def search_worker():
            results = sdk.search("*.py", max_results=50)
            results_container.extend(results)

        start = time.perf_counter()

        for _ in range(num_threads):
            t = threading.Thread(target=search_worker)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        elapsed = time.perf_counter() - start

        print(f"  {num_threads} threads: {elapsed*1000:.2f}ms total, {len(results_container)} total results")
        return results_container

    for num_threads in [1, 2, 4, 8]:
        bench.run(
            f"Concurrent ({num_threads} threads)",
            lambda n=num_threads: run_concurrent(n),
            iterations=3
        )


def benchmark_memory_usage(sdk: EverythingSDK):
    """Benchmark memory usage."""
    print("\n" + "=" * 80)
    print("BENCHMARK 8: Memory Usage")
    print("=" * 80)

    import psutil
    import os

    process = psutil.Process(os.getpid())

    mem_before = process.memory_info().rss / 1024 / 1024  # MB

    # Perform large search
    results = sdk.search("*", max_results=10000)

    mem_after = process.memory_info().rss / 1024 / 1024  # MB

    print(f"\nMemory before: {mem_before:.2f} MB")
    print(f"Memory after: {mem_after:.2f} MB")
    print(f"Memory delta: {mem_after - mem_before:.2f} MB")
    print(f"Results: {len(results)}")
    print(f"Memory per result: {(mem_after - mem_before) * 1024 / len(results):.2f} KB")


def benchmark_vs_fallback(sdk: EverythingSDK, bench: Benchmark):
    """Compare Everything SDK vs Windows Search fallback."""
    print("\n" + "=" * 80)
    print("BENCHMARK 9: SDK vs Fallback Comparison")
    print("=" * 80)

    if sdk.is_using_fallback:
        print("Already using fallback mode, cannot compare")
        return

    query = "test*.py"

    # SDK search
    bench.run(
        "Everything SDK",
        lambda: sdk.search(query, max_results=20),
        iterations=3
    )

    sdk_time = bench.results[-1]["avg_ms"]

    # Fallback search
    fallback_results = sdk._search_windows_fallback(query, max_results=20)
    print(f"\nFallback search completed: {len(fallback_results)} results")

    # Note: Timing fallback properly would require multiple iterations
    # but it's very slow, so we just note the difference
    print(f"\nEverything SDK average: {sdk_time:.2f}ms")
    print("Windows Search fallback: 1000-5000ms typical (not benchmarked due to slowness)")


def system_info():
    """Print system information."""
    print("\n" + "=" * 80)
    print("SYSTEM INFORMATION")
    print("=" * 80)

    import platform
    import psutil

    print(f"\nOS: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print(f"CPU: {psutil.cpu_count()} cores")
    print(f"RAM: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f} GB")

    sdk = get_everything_instance()
    stats = sdk.get_stats()

    print(f"\nEverything SDK:")
    print(f"  Available: {stats['is_available']}")
    print(f"  Using fallback: {stats['is_using_fallback']}")
    print(f"  Cache enabled: {stats['cache_enabled']}")
    print(f"  Cache TTL: {stats['cache_ttl']}s")


def main():
    """Run all benchmarks."""
    print("\n" + "=" * 80)
    print("EVERYTHING SDK PERFORMANCE BENCHMARK")
    print("=" * 80)

    # System info
    system_info()

    # Initialize SDK
    sdk = get_everything_instance()

    if not sdk.is_available:
        print("\nWARNING: Everything SDK not available, using fallback mode")
        print("Benchmark results will be significantly slower")

    # Create benchmark runner
    bench = Benchmark()

    # Run benchmarks
    benchmark_basic_queries(sdk, bench)
    benchmark_advanced_queries(sdk, bench)
    benchmark_sorting(sdk, bench)
    benchmark_result_counts(sdk, bench)
    benchmark_caching(sdk, bench)
    benchmark_pagination(sdk, bench)

    try:
        benchmark_concurrent_searches(sdk, bench)
    except Exception as e:
        print(f"Concurrent benchmark failed: {e}")

    try:
        import psutil
        benchmark_memory_usage(sdk)
    except ImportError:
        print("\npsutil not installed, skipping memory benchmark")

    if sdk.is_available and not sdk.is_using_fallback:
        benchmark_vs_fallback(sdk, bench)

    # Print summary
    bench.print_summary()

    print("\n" + "=" * 80)
    print("BENCHMARK COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
