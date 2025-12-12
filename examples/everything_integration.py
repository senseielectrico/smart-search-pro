"""
Everything SDK Integration Examples

Demonstrates how to use Everything SDK in Smart Search Pro.
Shows real-world usage patterns and best practices.
"""

import sys
import time
from pathlib import Path
from typing import List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from search.everything_sdk import (
    EverythingResult,
    EverythingSDK,
    EverythingSort,
    get_everything_instance,
)


def example_1_basic_search():
    """Example 1: Basic file search."""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Basic File Search")
    print("=" * 60)

    sdk = get_everything_instance()

    # Search for Python files
    results = sdk.search("*.py", max_results=10)

    print(f"\nFound {len(results)} Python files:")
    for i, result in enumerate(results[:5], 1):
        print(f"{i}. {result.full_path}")


def example_2_filtered_search():
    """Example 2: Filtered search with sorting."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Filtered Search with Sorting")
    print("=" * 60)

    sdk = get_everything_instance()

    # Find large files, sorted by size
    results = sdk.search(
        query="size:>10mb",
        max_results=10,
        sort=EverythingSort.SIZE_DESCENDING
    )

    print(f"\nLarge files (>10MB):")
    for result in results[:5]:
        size_mb = result.size / (1024 * 1024)
        print(f"  {result.filename}: {size_mb:.2f} MB")


def example_3_async_search():
    """Example 3: Asynchronous search with callback."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Asynchronous Search")
    print("=" * 60)

    sdk = get_everything_instance()
    results_container = []

    def on_results(results: List[EverythingResult]):
        results_container.extend(results)
        print(f"  Received {len(results)} results")

    def on_error(error: Exception):
        print(f"  Error: {error}")

    # Start async search
    print("Starting async search for *.log files...")
    thread = sdk.search_async(
        query="*.log",
        callback=on_results,
        error_callback=on_error,
        max_results=20
    )

    # Do other work while search runs
    print("Doing other work...")
    time.sleep(0.1)

    # Wait for completion
    thread.join(timeout=5)

    print(f"Total results: {len(results_container)}")


def example_4_progress_tracking():
    """Example 4: Search with progress tracking."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Progress Tracking")
    print("=" * 60)

    sdk = get_everything_instance()

    progress_data = {"current": 0, "total": 0}

    def on_progress(current: int, total: int):
        progress_data["current"] = current
        progress_data["total"] = total
        if current % 20 == 0 or current == total:
            percent = (current / total * 100) if total > 0 else 0
            print(f"  Progress: {current}/{total} ({percent:.1f}%)")

    results = sdk.search(
        query="*.dll",
        max_results=100,
        progress_callback=on_progress
    )

    print(f"Completed: {len(results)} results")


def example_5_advanced_queries():
    """Example 5: Advanced query syntax."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Advanced Query Syntax")
    print("=" * 60)

    sdk = get_everything_instance()

    queries = [
        ("ext:py;js;ts", "Python, JavaScript, TypeScript files"),
        ("dm:today", "Files modified today"),
        ("folder: size:>100mb", "Large folders"),
        ("!*.tmp !*.cache", "Exclude temp files"),
        ("C:\\Users\\ *.pdf", "PDFs in user directories"),
    ]

    for query, description in queries:
        try:
            results = sdk.search(query, max_results=5)
            print(f"\n{description}:")
            print(f"  Query: {query}")
            print(f"  Results: {len(results)}")
        except Exception as e:
            print(f"\n{description}:")
            print(f"  Query: {query}")
            print(f"  Error: {e}")


def example_6_search_with_stats():
    """Example 6: Search with statistics."""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Search with Statistics")
    print("=" * 60)

    sdk = get_everything_instance()

    # Get SDK stats
    stats = sdk.get_stats()
    print("\nSDK Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Perform search and measure
    query = "*.json"
    start = time.time()
    results = sdk.search(query, max_results=50)
    elapsed = time.time() - start

    print(f"\nSearch Performance:")
    print(f"  Query: {query}")
    print(f"  Results: {len(results)}")
    print(f"  Time: {elapsed*1000:.2f}ms")
    print(f"  Rate: {len(results)/elapsed:.0f} results/sec")

    # Search again (should be cached)
    start = time.time()
    results2 = sdk.search(query, max_results=50)
    elapsed2 = time.time() - start

    print(f"\nCached Search:")
    print(f"  Time: {elapsed2*1000:.3f}ms")
    print(f"  Speedup: {elapsed/elapsed2:.0f}x")


def example_7_folder_search():
    """Example 7: Folder-only search."""
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Folder Search")
    print("=" * 60)

    sdk = get_everything_instance()

    # Find all folders with "test" in name
    results = sdk.search("folder: test", max_results=10)

    print(f"\nFolders containing 'test': {len(results)}")
    for result in results[:5]:
        if result.is_folder:
            print(f"  {result.full_path}")


def example_8_regex_search():
    """Example 8: Regex search."""
    print("\n" + "=" * 60)
    print("EXAMPLE 8: Regex Search")
    print("=" * 60)

    sdk = get_everything_instance()

    # Find files matching regex pattern
    # Pattern: files starting with "test_" and ending with ".py"
    results = sdk.search(
        query="regex:^test_.*\\.py$",
        regex=True,
        max_results=10
    )

    print(f"\nFiles matching 'test_*.py': {len(results)}")
    for result in results[:5]:
        print(f"  {result.filename}")


def example_9_pagination():
    """Example 9: Pagination for large result sets."""
    print("\n" + "=" * 60)
    print("EXAMPLE 9: Pagination")
    print("=" * 60)

    sdk = get_everything_instance()

    page_size = 20
    query = "*.txt"

    print(f"\nSearching '{query}' with pagination:")

    for page in range(3):
        offset = page * page_size
        results = sdk.search(query, max_results=page_size, offset=offset)

        print(f"\nPage {page + 1}:")
        print(f"  Offset: {offset}")
        print(f"  Results: {len(results)}")

        if len(results) < page_size:
            print("  (Last page)")
            break


def example_10_ui_integration():
    """Example 10: UI integration pattern."""
    print("\n" + "=" * 60)
    print("EXAMPLE 10: UI Integration Pattern")
    print("=" * 60)

    sdk = get_everything_instance()

    class SearchController:
        """Example search controller for UI."""

        def __init__(self):
            self.sdk = sdk
            self.current_results = []
            self.is_searching = False

        def search(self, query: str, on_update_callback):
            """Perform search and update UI via callback."""
            if self.is_searching:
                print("Search already in progress")
                return

            self.is_searching = True
            self.current_results = []

            def progress_callback(current, total):
                # Update UI progress bar
                on_update_callback("progress", current, total)

            def search_complete():
                try:
                    results = self.sdk.search(
                        query=query,
                        max_results=100,
                        progress_callback=progress_callback
                    )
                    self.current_results = results
                    on_update_callback("complete", results)
                except Exception as e:
                    on_update_callback("error", e)
                finally:
                    self.is_searching = False

            # Run in background
            import threading
            thread = threading.Thread(target=search_complete, daemon=True)
            thread.start()

    # Example usage
    def ui_callback(event_type, *args):
        if event_type == "progress":
            current, total = args
            print(f"  UI Update: Progress {current}/{total}")
        elif event_type == "complete":
            results = args[0]
            print(f"  UI Update: Search complete with {len(results)} results")
        elif event_type == "error":
            error = args[0]
            print(f"  UI Update: Error - {error}")

    controller = SearchController()
    print("\nSimulating UI search...")
    controller.search("*.py", ui_callback)

    # Wait for search to complete
    time.sleep(0.5)


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("EVERYTHING SDK INTEGRATION EXAMPLES")
    print("=" * 60)

    examples = [
        example_1_basic_search,
        example_2_filtered_search,
        example_3_async_search,
        example_4_progress_tracking,
        example_5_advanced_queries,
        example_6_search_with_stats,
        example_7_folder_search,
        example_8_regex_search,
        example_9_pagination,
        example_10_ui_integration,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nExample failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
