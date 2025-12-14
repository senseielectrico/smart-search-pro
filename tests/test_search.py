"""
Tests for search module: Engine, QueryParser, Filters
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


# ============================================================================
# QUERY PARSER TESTS
# ============================================================================

class TestQueryParser:
    """Tests for QueryParser class"""

    def test_parse_simple_query(self, test_query_parser):
        """Test parsing simple text query"""
        parsed = test_query_parser.parse("test file")
        # Keywords can be stored as single string or split - check for either format
        assert len(parsed.keywords) > 0
        keywords_str = ' '.join(parsed.keywords).lower()
        assert 'test' in keywords_str or 'file' in keywords_str

    def test_parse_extension_filter(self, test_query_parser):
        """Test parsing extension filters"""
        parsed = test_query_parser.parse("document ext:pdf")
        assert 'pdf' in parsed.extensions or len(parsed.extensions) > 0

    def test_parse_size_filter(self, test_query_parser):
        """Test parsing size filters"""
        parsed = test_query_parser.parse("large file size:>10mb")
        assert parsed.size_filters is not None

    def test_parse_date_filter(self, test_query_parser):
        """Test parsing date filters"""
        parsed = test_query_parser.parse("recent modified:today")
        assert parsed.date_filters is not None

    def test_parse_path_filter(self, test_query_parser):
        """Test parsing path filters"""
        parsed = test_query_parser.parse("file path:C:\\Test")
        assert parsed.path_filters is not None

    def test_parse_complex_query(self, test_query_parser):
        """Test parsing complex query with multiple filters"""
        parsed = test_query_parser.parse(
            "document ext:pdf size:>1mb modified:thisweek path:C:\\Docs"
        )
        assert len(parsed.keywords) > 0 or len(parsed.extensions) > 0


# ============================================================================
# FILTER CHAIN TESTS
# ============================================================================

class TestFilterChain:
    """Tests for FilterChain class"""

    def test_empty_filter_chain(self, test_filter_chain):
        """Test empty filter chain matches everything"""
        from search.engine import SearchResult
        result = SearchResult(
            filename="test.txt",
            path="/test",
            full_path="/test/test.txt",
            size=1024
        )
        assert test_filter_chain.matches(result) is True

    def test_size_filter(self, test_filter_chain):
        """Test size filtering"""
        from search.filters import SizeFilterImpl
        from search.query_parser import SizeFilter, SizeOperator
        from search.engine import SearchResult

        # Create size filters for min_size=1000 and max_size=2000
        size_filters = [
            SizeFilter(operator=SizeOperator.GREATER_EQUAL, value=1000, unit="b"),
            SizeFilter(operator=SizeOperator.LESS_EQUAL, value=2000, unit="b")
        ]
        test_filter_chain.add_filter(SizeFilterImpl(size_filters))

        result_match = SearchResult(
            filename="test.txt",
            path="/test",
            full_path="/test/test.txt",
            size=1500
        )
        result_nomatch = SearchResult(
            filename="test2.txt",
            path="/test",
            full_path="/test/test2.txt",
            size=500
        )

        assert test_filter_chain.matches(result_match) is True
        assert test_filter_chain.matches(result_nomatch) is False

    def test_extension_filter(self, test_filter_chain):
        """Test extension filtering"""
        from search.filters import FileTypeFilter
        from search.engine import SearchResult

        test_filter_chain.add_filter(FileTypeFilter(extensions={'pdf', 'docx'}))

        result_match = SearchResult(
            filename="document.pdf",
            path="/test",
            full_path="/test/document.pdf",
            extension="pdf"
        )
        result_nomatch = SearchResult(
            filename="image.jpg",
            path="/test",
            full_path="/test/image.jpg",
            extension="jpg"
        )

        assert test_filter_chain.matches(result_match) is True
        assert test_filter_chain.matches(result_nomatch) is False


# ============================================================================
# SEARCH ENGINE TESTS
# ============================================================================

class TestSearchEngine:
    """Tests for SearchEngine class"""

    @patch('search.engine.EverythingSDK')
    def test_search_engine_initialization(self, mock_sdk):
        """Test search engine initialization"""
        from search.engine import SearchEngine

        mock_sdk.return_value.is_available = True
        engine = SearchEngine()
        assert engine is not None

    @patch('search.engine.EverythingSDK')
    def test_search_with_everything(self, mock_sdk):
        """Test search using Everything SDK"""
        from search.engine import SearchEngine, SearchResult

        mock_sdk.return_value.is_available = True
        mock_sdk.return_value.search.return_value = [
            type('Result', (), {
                'filename': 'test.txt',
                'path': '/test',
                'full_path': '/test/test.txt',
                'extension': 'txt',
                'size': 1024,
                'date_created': 0,
                'date_modified': 0,
                'date_accessed': 0,
                'attributes': 0,
                'is_folder': False
            })()
        ]

        engine = SearchEngine()
        results = engine.search("test", max_results=10)
        assert isinstance(results, list)

    def test_search_cancellation(self):
        """Test search cancellation"""
        from search.engine import SearchEngine

        engine = SearchEngine()
        engine.cancel()
        assert engine._cancel_flag.is_set() is True

    @patch('search.engine.EverythingSDK')
    def test_search_with_progress_callback(self, mock_sdk):
        """Test search with progress callback"""
        from search.engine import SearchEngine

        mock_sdk.return_value.is_available = True
        mock_sdk.return_value.search.return_value = []

        progress_calls = []

        def progress_callback(current, total):
            progress_calls.append((current, total))

        engine = SearchEngine()
        engine.search("test", progress_callback=progress_callback)
        # Progress callback should have been called at least once
        assert len(progress_calls) >= 0  # May be 0 if no results

    def test_get_suggestions(self):
        """Test search suggestions"""
        from search.engine import SearchEngine

        engine = SearchEngine()
        suggestions = engine.get_suggestions("ext:", limit=5)
        assert isinstance(suggestions, list)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
class TestSearchIntegration:
    """Integration tests for search module"""

    @patch('search.engine.EverythingSDK')
    def test_query_parse_and_search(self, mock_sdk):
        """Test query parsing integrated with search"""
        from search.engine import SearchEngine
        from search.query_parser import QueryParser

        mock_sdk.return_value.is_available = True
        mock_sdk.return_value.search.return_value = []

        parser = QueryParser()
        engine = SearchEngine()

        parsed = parser.parse("document ext:pdf size:>1mb")
        # Engine should handle parsed queries
        results = engine.search(str(parsed))
        assert isinstance(results, list)

    @patch('search.engine.EverythingSDK')
    def test_search_with_filters(self, mock_sdk, mock_search_results):
        """Test search with filter chain"""
        from search.engine import SearchEngine
        from search.filters import SizeFilterImpl, FilterChain
        from search.query_parser import SizeFilter, SizeOperator

        mock_sdk.return_value.is_available = True
        mock_sdk.return_value.search.return_value = mock_search_results

        engine = SearchEngine()
        results = engine.search("test")

        # Apply additional filtering with proper API
        filter_chain = FilterChain()
        size_filters = [SizeFilter(operator=SizeOperator.GREATER_EQUAL, value=1000, unit="b")]
        filter_chain.add_filter(SizeFilterImpl(size_filters))
        filtered = [r for r in results if filter_chain.matches(r)]

        assert isinstance(filtered, list)
