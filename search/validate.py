"""
Validation script for Smart Search Pro search module.

Checks imports, basic functionality, and configuration.
"""

import sys
from pathlib import Path


def validate_imports():
    """Validate all module imports."""
    print("Validating imports...")

    try:
        from . import (
            SearchEngine,
            SearchResult,
            QueryParser,
            ParsedQuery,
            FileTypeFilter,
            SizeFilter,
            DateFilter,
            PathFilter,
            ContentFilter,
            FilterChain,
            SearchHistory,
            EverythingSDK,
            EverythingError,
        )
        print("  All imports successful")
        return True
    except ImportError as e:
        print(f"  Import error: {e}")
        return False


def validate_query_parser():
    """Validate query parser."""
    print("\nValidating query parser...")

    try:
        from .query_parser import QueryParser

        parser = QueryParser()

        # Test basic query
        result = parser.parse("test ext:pdf size:>10mb")
        assert "test" in result.keywords
        assert "pdf" in result.extensions
        assert len(result.size_filters) > 0

        print("  Query parser working correctly")
        return True
    except Exception as e:
        print(f"  Query parser error: {e}")
        return False


def validate_everything_sdk():
    """Validate Everything SDK."""
    print("\nValidating Everything SDK...")

    try:
        from .everything_sdk import EverythingSDK, EverythingSDKError

        try:
            sdk = EverythingSDK()
            if sdk.is_available:
                print("  Everything SDK available and working")
                print(f"  DLL loaded successfully")
                return True
            else:
                print("  Everything SDK loaded but database not available")
                print("  (Everything.exe may not be running)")
                return True  # Not an error, just not running
        except EverythingSDKError as e:
            print(f"  Everything SDK not available: {e}")
            print("  (This is OK if Everything is not installed)")
            return True  # Not an error

    except Exception as e:
        print(f"  Everything SDK error: {e}")
        return False


def validate_search_engine():
    """Validate search engine."""
    print("\nValidating search engine...")

    try:
        from .engine import SearchEngine

        engine = SearchEngine()

        if engine.is_available:
            print(f"  Search engine available")
            print(f"  Backend: {'Everything SDK' if engine.use_everything else 'Windows Search'}")

            # Test basic search
            try:
                results = engine.search("test", max_results=1)
                print(f"  Basic search working (found {len(results)} results)")
            except Exception as e:
                print(f"  Search test failed: {e}")
                return False

            return True
        else:
            print("  No search backend available")
            print("  Install Everything or enable Windows Search")
            return False

    except Exception as e:
        print(f"  Search engine error: {e}")
        return False


def validate_filters():
    """Validate filters."""
    print("\nValidating filters...")

    try:
        from .filters import (
            FileTypeFilter,
            SizeFilterImpl,
            FilterChain,
            create_filter_chain_from_query,
        )
        from .query_parser import QueryParser
        from .engine import SearchResult

        # Create test result
        result = SearchResult(
            filename="test.pdf",
            path="C:\\test",
            full_path="C:\\test\\test.pdf",
            extension="pdf",
            size=5 * 1024 * 1024,
            is_folder=False,
        )

        # Test file type filter
        filter_obj = FileTypeFilter({"pdf"})
        assert filter_obj.matches(result)

        # Test filter chain
        parser = QueryParser()
        parsed = parser.parse("ext:pdf")
        chain = create_filter_chain_from_query(parsed)
        assert chain.matches(result)

        print("  Filters working correctly")
        return True

    except Exception as e:
        print(f"  Filter error: {e}")
        return False


def validate_history():
    """Validate search history."""
    print("\nValidating search history...")

    try:
        from .history import SearchHistory
        import tempfile
        import os

        # Create temporary history file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_file = f.name

        try:
            history = SearchHistory(history_file=temp_file)

            # Test add
            history.add("test query", result_count=10)
            assert len(history) == 1

            # Test suggestions
            suggestions = history.get_suggestions("test")
            assert len(suggestions) > 0

            # Test statistics
            stats = history.get_statistics()
            assert stats["total_searches"] == 1

            print("  Search history working correctly")
            return True

        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    except Exception as e:
        print(f"  History error: {e}")
        return False


def validate_all():
    """Run all validations."""
    print("=" * 60)
    print("Smart Search Pro - Module Validation")
    print("=" * 60)

    results = {
        "Imports": validate_imports(),
        "Query Parser": validate_query_parser(),
        "Everything SDK": validate_everything_sdk(),
        "Search Engine": validate_search_engine(),
        "Filters": validate_filters(),
        "History": validate_history(),
    }

    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)

    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        symbol = "[OK]" if result else "[FAIL]"
        print(f"{symbol} {name:20} {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("All validations passed!")
        print("\nThe search module is ready to use.")
    else:
        print("Some validations failed!")
        print("\nPlease check the errors above.")

    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    # Allow running as script
    if __package__ is None:
        # Add parent directory to path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        # Set package name
        __package__ = "smart_search.search"

    success = validate_all()
    sys.exit(0 if success else 1)
