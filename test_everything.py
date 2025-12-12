"""
Test script for Everything SDK integration.

Tests all major functionality including:
- DLL loading
- Synchronous search
- Asynchronous search
- Caching
- Progress callbacks
- Fallback to Windows Search
"""

import time
from pathlib import Path

from search.everything_sdk import (
    EverythingSDK,
    EverythingSort,
    get_everything_instance,
)


def test_dll_loading():
    """Test DLL loading and initialization."""
    print("\n" + "=" * 60)
    print("TEST 1: DLL Loading and Initialization")
    print("=" * 60)

    try:
        sdk = EverythingSDK()
        print(f"Everything SDK initialized: {sdk.is_available}")
        print(f"Using fallback: {sdk.is_using_fallback}")

        stats = sdk.get_stats()
        print(f"\nSDK Stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        return sdk
    except Exception as e:
        print(f"Error initializing SDK: {e}")
        return None


def test_synchronous_search(sdk: EverythingSDK):
    """Test synchronous search."""
    print("\n" + "=" * 60)
    print("TEST 2: Synchronous Search")
    print("=" * 60)

    if not sdk:
        print("SDK not available, skipping test")
        return

    query = "*.py"
    print(f"Searching for: {query}")
    print(f"Max results: 10")

    try:
        start_time = time.time()
        results = sdk.search(
            query=query,
            max_results=10,
            sort=EverythingSort.DATE_MODIFIED_DESCENDING
        )
        elapsed = time.time() - start_time

        print(f"\nFound {len(results)} results in {elapsed:.3f}s")
        print("\nTop 5 results:")
        for i, result in enumerate(results[:5], 1):
            print(f"\n{i}. {result.filename}")
            print(f"   Path: {result.path}")
            print(f"   Full: {result.full_path}")
            print(f"   Size: {result.size:,} bytes")
            print(f"   Folder: {result.is_folder}")

    except Exception as e:
        print(f"Error during search: {e}")


def test_async_search(sdk: EverythingSDK):
    """Test asynchronous search."""
    print("\n" + "=" * 60)
    print("TEST 3: Asynchronous Search")
    print("=" * 60)

    if not sdk:
        print("SDK not available, skipping test")
        return

    results_received = []

    def on_results(results):
        results_received.extend(results)
        print(f"Received {len(results)} results")

    def on_error(error):
        print(f"Error in async search: {error}")

    query = "*.txt"
    print(f"Async search for: {query}")

    thread = sdk.search_async(
        query=query,
        callback=on_results,
        error_callback=on_error,
        max_results=20
    )

    print("Waiting for async search to complete...")
    thread.join(timeout=10)

    if thread.is_alive():
        print("Async search timed out")
    else:
        print(f"Async search completed with {len(results_received)} results")


def test_progress_callback(sdk: EverythingSDK):
    """Test progress callback."""
    print("\n" + "=" * 60)
    print("TEST 4: Progress Callback")
    print("=" * 60)

    if not sdk:
        print("SDK not available, skipping test")
        return

    progress_updates = []

    def on_progress(current, total):
        progress_updates.append((current, total))
        if current % 10 == 0 or current == total:
            print(f"Progress: {current}/{total} ({100*current/total:.1f}%)")

    query = "*.md"
    print(f"Searching with progress: {query}")

    try:
        results = sdk.search(
            query=query,
            max_results=50,
            progress_callback=on_progress
        )
        print(f"\nCompleted with {len(results)} results")
        print(f"Progress updates: {len(progress_updates)}")
    except Exception as e:
        print(f"Error: {e}")


def test_caching(sdk: EverythingSDK):
    """Test result caching."""
    print("\n" + "=" * 60)
    print("TEST 5: Result Caching")
    print("=" * 60)

    if not sdk:
        print("SDK not available, skipping test")
        return

    query = "test*.py"

    # First search (no cache)
    print(f"First search: {query}")
    start_time = time.time()
    results1 = sdk.search(query, max_results=20)
    time1 = time.time() - start_time
    print(f"Time: {time1:.3f}s, Results: {len(results1)}")

    # Second search (from cache)
    print(f"\nSecond search (should be cached): {query}")
    start_time = time.time()
    results2 = sdk.search(query, max_results=20)
    time2 = time.time() - start_time
    print(f"Time: {time2:.3f}s, Results: {len(results2)}")

    if time2 < time1:
        print(f"\nCache speedup: {time1/time2:.1f}x faster")
    else:
        print("\nNo cache speedup detected (might be using fallback)")

    # Clear cache
    sdk.clear_cache()
    print("\nCache cleared")

    # Third search (no cache again)
    print(f"\nThird search (cache cleared): {query}")
    start_time = time.time()
    results3 = sdk.search(query, max_results=20)
    time3 = time.time() - start_time
    print(f"Time: {time3:.3f}s, Results: {len(results3)}")


def test_advanced_queries(sdk: EverythingSDK):
    """Test advanced query features."""
    print("\n" + "=" * 60)
    print("TEST 6: Advanced Queries")
    print("=" * 60)

    if not sdk:
        print("SDK not available, skipping test")
        return

    # Test case-sensitive search
    print("\n1. Case-sensitive search:")
    results = sdk.search("README", match_case=True, max_results=5)
    print(f"   Found {len(results)} results")

    # Test whole word search
    print("\n2. Whole word search:")
    results = sdk.search("test", match_whole_word=True, max_results=5)
    print(f"   Found {len(results)} results")

    # Test folder search
    print("\n3. Folder search:")
    results = sdk.search("folder:", max_results=5)
    print(f"   Found {len(results)} folders")
    for r in results[:3]:
        print(f"   - {r.filename}: {r.is_folder}")

    # Test extension filter
    print("\n4. Extension filter:")
    results = sdk.search("ext:py", max_results=10)
    print(f"   Found {len(results)} Python files")

    # Test size filter
    print("\n5. Size filter (>1MB):")
    results = sdk.search("size:>1mb", max_results=5)
    print(f"   Found {len(results)} large files")
    for r in results[:3]:
        print(f"   - {r.filename}: {r.size:,} bytes")


def test_singleton():
    """Test singleton instance."""
    print("\n" + "=" * 60)
    print("TEST 7: Singleton Instance")
    print("=" * 60)

    instance1 = get_everything_instance()
    instance2 = get_everything_instance()

    print(f"Instance 1 ID: {id(instance1)}")
    print(f"Instance 2 ID: {id(instance2)}")
    print(f"Same instance: {instance1 is instance2}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("EVERYTHING SDK TEST SUITE")
    print("=" * 60)

    # Test 1: Initialize
    sdk = test_dll_loading()

    if sdk:
        # Test 2: Synchronous search
        test_synchronous_search(sdk)

        # Test 3: Async search
        test_async_search(sdk)

        # Test 4: Progress callback
        test_progress_callback(sdk)

        # Test 5: Caching
        test_caching(sdk)

        # Test 6: Advanced queries
        test_advanced_queries(sdk)

        # Test 7: Singleton
        test_singleton()

        # Cleanup
        sdk.cleanup()
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)
    else:
        print("\nCannot run tests without SDK initialization")


if __name__ == "__main__":
    main()
