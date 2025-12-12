"""
Example usage of Smart Search Pro search module.

Demonstrates various search capabilities and advanced features.
"""

import time
from pathlib import Path

from .engine import SearchEngine
from .history import SearchHistory
from .query_parser import QueryParser


def example_basic_search():
    """Example: Basic file search."""
    print("=" * 60)
    print("Example 1: Basic Search")
    print("=" * 60)

    engine = SearchEngine()

    if not engine.is_available:
        print("Error: No search backend available!")
        print("Please install Everything or enable Windows Search.")
        return

    print(f"Search backend: {'Everything SDK' if engine.use_everything else 'Windows Search'}")
    print()

    # Simple keyword search
    query = "python"
    print(f"Searching for: {query}")

    start_time = time.time()
    results = engine.search(query, max_results=10)
    elapsed_time = (time.time() - start_time) * 1000

    print(f"Found {len(results)} results in {elapsed_time:.2f}ms")
    print()

    for i, result in enumerate(results[:5], 1):
        size_mb = result.size / (1024 * 1024) if result.size else 0
        print(f"{i}. {result.filename}")
        print(f"   Path: {result.path}")
        print(f"   Size: {size_mb:.2f} MB")
        print()


def example_advanced_filters():
    """Example: Advanced filtering."""
    print("=" * 60)
    print("Example 2: Advanced Filters")
    print("=" * 60)

    engine = SearchEngine()

    if not engine.is_available:
        print("Error: No search backend available!")
        return

    # Multiple filters
    queries = [
        "ext:pdf size:>10mb",
        "type:image modified:thisweek",
        "python * tutorial ext:pdf",
        "path:documents size:<1mb modified:today",
        "report created:2024 ext:docx",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        start_time = time.time()
        results = engine.search(query, max_results=5)
        elapsed_time = (time.time() - start_time) * 1000

        print(f"Results: {len(results)} files in {elapsed_time:.2f}ms")

        if results:
            for result in results[:3]:
                print(f"  - {result.filename} ({result.size / 1024:.1f} KB)")


def example_query_parsing():
    """Example: Query parsing and filter extraction."""
    print("=" * 60)
    print("Example 3: Query Parsing")
    print("=" * 60)

    parser = QueryParser()

    queries = [
        "python tutorial",
        "report * analysis ext:pdf",
        "size:>100mb type:video",
        "modified:today path:downloads",
        'regex:test_.*\\.py',
        "vacation ext:jpg ext:png size:>5mb created:2024",
    ]

    for query in queries:
        print(f"\nOriginal query: {query}")
        parsed = parser.parse(query)

        print(f"Keywords: {parsed.keywords}")
        if parsed.extensions:
            print(f"Extensions: {parsed.extensions}")
        if parsed.file_types:
            print(f"File types: {parsed.file_types}")
        if parsed.size_filters:
            print(f"Size filters: {len(parsed.size_filters)}")
        if parsed.date_filters:
            print(f"Date filters: {len(parsed.date_filters)}")
        if parsed.path_filters:
            print(f"Path filters: {[pf.path for pf in parsed.path_filters]}")
        if parsed.is_regex:
            print(f"Regex pattern: {parsed.regex_pattern}")

        # Build Everything query
        everything_query = parser.build_everything_query(parsed)
        print(f"Everything query: {everything_query}")


def example_async_search():
    """Example: Asynchronous search with progress callback."""
    print("=" * 60)
    print("Example 4: Async Search with Progress")
    print("=" * 60)

    engine = SearchEngine()

    if not engine.is_available:
        print("Error: No search backend available!")
        return

    def progress_callback(current, total):
        """Progress callback function."""
        if total > 0:
            percent = (current / total) * 100
            print(f"\rProgress: {current}/{total} ({percent:.1f}%)", end="", flush=True)

    def results_callback(results):
        """Results callback function."""
        print(f"\n\nSearch completed! Found {len(results)} results")
        for i, result in enumerate(results[:5], 1):
            print(f"{i}. {result.filename}")

    query = "type:image size:>1mb"
    print(f"Starting async search: {query}")

    thread = engine.search_async(
        query,
        max_results=100,
        callback=results_callback,
        progress_callback=progress_callback,
    )

    # Wait for completion
    thread.join()
    print("\nAsync search finished!")


def example_search_history():
    """Example: Search history and autocomplete."""
    print("=" * 60)
    print("Example 5: Search History")
    print("=" * 60)

    # Create temporary history
    history = SearchHistory(history_file=".temp_search_history.json")

    # Add some searches
    print("Adding search history entries...")
    history.add("python tutorial", result_count=150, execution_time_ms=45.2)
    history.add("javascript guide", result_count=200, execution_time_ms=38.7)
    history.add("python examples", result_count=300, execution_time_ms=52.1)
    history.add("python", result_count=1000, execution_time_ms=120.5)
    history.add("react components", result_count=80, execution_time_ms=28.3)

    # Get recent searches
    print("\nRecent searches:")
    for entry in history.get_recent(limit=3):
        print(f"  - {entry.query} ({entry.result_count} results)")

    # Get popular searches
    print("\nPopular searches:")
    for query in history.get_popular(limit=3):
        freq = history.query_frequency[query]
        print(f"  - {query} ({freq} times)")

    # Get autocomplete suggestions
    print("\nAutocomplete suggestions for 'pyth':")
    suggestions = history.get_suggestions("pyth", limit=5)
    for suggestion in suggestions:
        print(f"  - {suggestion}")

    # Search history
    print("\nSearching history for 'python':")
    results = history.search("python", limit=5)
    for entry in results:
        print(f"  - {entry.query}")

    # Statistics
    print("\nHistory statistics:")
    stats = history.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Clean up
    import os
    if os.path.exists(".temp_search_history.json"):
        os.unlink(".temp_search_history.json")


def example_size_and_date_filters():
    """Example: Size and date filters."""
    print("=" * 60)
    print("Example 6: Size and Date Filters")
    print("=" * 60)

    engine = SearchEngine()

    if not engine.is_available:
        print("Error: No search backend available!")
        return

    # Size filters
    print("\nSize filter examples:")
    size_queries = [
        "size:>100mb",  # Larger than 100MB
        "size:<1gb",  # Smaller than 1GB
        "size:>=500kb",  # At least 500KB
        "size:<=10mb",  # At most 10MB
    ]

    for query in size_queries:
        results = engine.search(query, max_results=3)
        print(f"{query}: {len(results)} results")

    # Date filters
    print("\nDate filter examples:")
    date_queries = [
        "modified:today",  # Modified today
        "created:thisweek",  # Created this week
        "modified:2024",  # Modified in 2024
        "created:>2024-01-01",  # Created after Jan 1, 2024
    ]

    for query in date_queries:
        results = engine.search(query, max_results=3)
        print(f"{query}: {len(results)} results")


def example_complex_query():
    """Example: Complex multi-filter query."""
    print("=" * 60)
    print("Example 7: Complex Query")
    print("=" * 60)

    engine = SearchEngine()

    if not engine.is_available:
        print("Error: No search backend available!")
        return

    # Complex query with multiple filters
    query = "report * analysis ext:pdf ext:docx size:>1mb size:<50mb modified:thismonth path:documents"

    print(f"Complex query: {query}")
    print("\nParsing query...")

    parser = QueryParser()
    parsed = parser.parse(query)

    print(f"\nExtracted components:")
    print(f"  Keywords: {parsed.keywords}")
    print(f"  Extensions: {parsed.extensions}")
    print(f"  Size filters: {len(parsed.size_filters)}")
    print(f"  Date filters: {len(parsed.date_filters)}")
    print(f"  Path filters: {[pf.path for pf in parsed.path_filters]}")

    print(f"\nExecuting search...")
    start_time = time.time()
    results = engine.search(query, max_results=20)
    elapsed_time = (time.time() - start_time) * 1000

    print(f"\nFound {len(results)} results in {elapsed_time:.2f}ms")

    if results:
        print("\nTop results:")
        for i, result in enumerate(results[:5], 1):
            size_mb = result.size / (1024 * 1024)
            print(f"{i}. {result.filename}")
            print(f"   Path: {result.path}")
            print(f"   Size: {size_mb:.2f} MB")
            print()


def example_performance_comparison():
    """Example: Performance comparison."""
    print("=" * 60)
    print("Example 8: Performance Test")
    print("=" * 60)

    engine = SearchEngine()

    if not engine.is_available:
        print("Error: No search backend available!")
        return

    test_queries = [
        "python",
        "ext:pdf",
        "size:>10mb",
        "modified:today",
        "type:image size:>1mb",
    ]

    print(f"Backend: {'Everything SDK' if engine.use_everything else 'Windows Search'}")
    print()

    for query in test_queries:
        # Run search 3 times and get average
        times = []
        result_count = 0

        for _ in range(3):
            start_time = time.time()
            results = engine.search(query, max_results=100)
            elapsed_time = (time.time() - start_time) * 1000
            times.append(elapsed_time)
            result_count = len(results)

        avg_time = sum(times) / len(times)
        print(f"Query: {query:30} | Results: {result_count:4} | Avg Time: {avg_time:6.2f}ms")


def main():
    """Run all examples."""
    examples = [
        ("Basic Search", example_basic_search),
        ("Advanced Filters", example_advanced_filters),
        ("Query Parsing", example_query_parsing),
        ("Async Search", example_async_search),
        ("Search History", example_search_history),
        ("Size and Date Filters", example_size_and_date_filters),
        ("Complex Query", example_complex_query),
        ("Performance Test", example_performance_comparison),
    ]

    print("\n" + "=" * 60)
    print("Smart Search Pro - Example Usage")
    print("=" * 60)
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")

    print("\n0. Run all examples")
    print()

    try:
        choice = input("Enter example number (0-8): ").strip()

        if choice == "0":
            for name, func in examples:
                print("\n" * 2)
                func()
                input("\nPress Enter to continue...")
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            examples[int(choice) - 1][1]()
        else:
            print("Invalid choice!")

    except KeyboardInterrupt:
        print("\n\nExamples interrupted!")
    except Exception as e:
        print(f"\nError running example: {e}")


if __name__ == "__main__":
    main()
