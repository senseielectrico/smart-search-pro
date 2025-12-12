"""
Test suite for Smart Search Pro search module.

Run with: pytest test_search.py -v
"""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from .engine import SearchEngine, SearchResult
from .filters import (
    ContentFilter,
    DateFilterImpl,
    FileTypeFilter,
    FilterChain,
    PathFilterImpl,
    SizeFilterImpl,
)
from .history import SearchHistory, SearchHistoryEntry
from .query_parser import (
    DateFilter,
    DatePreset,
    ParsedQuery,
    PathFilter,
    QueryParser,
    SizeFilter,
    SizeOperator,
)


class TestQueryParser:
    """Test query parser functionality."""

    def test_basic_keywords(self):
        """Test basic keyword parsing."""
        parser = QueryParser()
        result = parser.parse("test document")

        assert "test" in result.keywords or "document" in result.keywords

    def test_multiple_keywords_with_separator(self):
        """Test multiple keywords with * separator."""
        parser = QueryParser()
        result = parser.parse("python * javascript * rust")

        assert "python" in result.keywords
        assert "javascript" in result.keywords
        assert "rust" in result.keywords

    def test_extension_filter(self):
        """Test file extension filter."""
        parser = QueryParser()
        result = parser.parse("report ext:pdf")

        assert "pdf" in result.extensions

    def test_multiple_extensions(self):
        """Test multiple extension filters."""
        parser = QueryParser()
        result = parser.parse("document ext:pdf ext:docx")

        assert "pdf" in result.extensions
        assert "docx" in result.extensions

    def test_file_type_filter(self):
        """Test file type filter expansion."""
        parser = QueryParser()
        result = parser.parse("vacation type:image")

        assert "image" in result.file_types
        assert "jpg" in result.extensions
        assert "png" in result.extensions

    def test_size_filter_greater(self):
        """Test size filter with greater than."""
        parser = QueryParser()
        result = parser.parse("video size:>100mb")

        assert len(result.size_filters) == 1
        assert result.size_filters[0].operator == SizeOperator.GREATER
        assert result.size_filters[0].value == 100 * 1024 * 1024

    def test_size_filter_less(self):
        """Test size filter with less than."""
        parser = QueryParser()
        result = parser.parse("config size:<1kb")

        assert len(result.size_filters) == 1
        assert result.size_filters[0].operator == SizeOperator.LESS
        assert result.size_filters[0].value == 1024

    def test_date_filter_preset(self):
        """Test date filter with preset."""
        parser = QueryParser()
        result = parser.parse("log modified:today")

        assert len(result.date_filters) == 1
        assert result.date_filters[0].preset == DatePreset.TODAY

    def test_date_filter_year(self):
        """Test date filter with year."""
        parser = QueryParser()
        result = parser.parse("photo created:2024")

        assert len(result.date_filters) == 1
        assert result.date_filters[0].year == 2024

    def test_path_filter(self):
        """Test path filter."""
        parser = QueryParser()
        result = parser.parse("readme path:documents")

        assert len(result.path_filters) == 1
        assert result.path_filters[0].path == "documents"

    def test_content_filter(self):
        """Test content filter."""
        parser = QueryParser()
        result = parser.parse("content:password")

        assert "password" in result.content_keywords

    def test_regex_filter(self):
        """Test regex filter."""
        parser = QueryParser()
        result = parser.parse('regex:test_.*\\.py')

        assert result.is_regex
        assert result.regex_pattern == 'test_.*\\.py'

    def test_complex_query(self):
        """Test complex query with multiple filters."""
        parser = QueryParser()
        result = parser.parse(
            "report * analysis ext:pdf size:>10mb modified:thisweek path:documents"
        )

        assert "report" in result.keywords
        assert "analysis" in result.keywords
        assert "pdf" in result.extensions
        assert len(result.size_filters) == 1
        assert len(result.date_filters) == 1
        assert len(result.path_filters) == 1

    def test_build_everything_query(self):
        """Test building Everything query string."""
        parser = QueryParser()
        parsed = parser.parse("test ext:pdf size:>10mb")
        query = parser.build_everything_query(parsed)

        assert "test" in query.lower()
        assert "*.pdf" in query.lower()
        assert "size:" in query.lower()


class TestFilters:
    """Test filter implementations."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample search result."""
        return SearchResult(
            filename="test.pdf",
            path="C:\\Users\\test\\Documents",
            full_path="C:\\Users\\test\\Documents\\test.pdf",
            extension="pdf",
            size=5 * 1024 * 1024,  # 5MB
            date_modified=0,
            date_created=0,
            date_accessed=0,
            is_folder=False,
        )

    def test_file_type_filter_matches(self, sample_result):
        """Test file type filter matching."""
        filter_obj = FileTypeFilter({"pdf", "docx"})
        assert filter_obj.matches(sample_result)

    def test_file_type_filter_no_match(self, sample_result):
        """Test file type filter non-matching."""
        filter_obj = FileTypeFilter({"jpg", "png"})
        assert not filter_obj.matches(sample_result)

    def test_size_filter_greater(self, sample_result):
        """Test size filter with greater than."""
        size_spec = SizeFilter(
            operator=SizeOperator.GREATER, value=1 * 1024 * 1024, unit="mb"
        )
        filter_obj = SizeFilterImpl([size_spec])
        assert filter_obj.matches(sample_result)

    def test_size_filter_less(self, sample_result):
        """Test size filter with less than."""
        size_spec = SizeFilter(
            operator=SizeOperator.LESS, value=10 * 1024 * 1024, unit="mb"
        )
        filter_obj = SizeFilterImpl([size_spec])
        assert filter_obj.matches(sample_result)

    def test_path_filter_matches(self, sample_result):
        """Test path filter matching."""
        path_spec = PathFilter(path="Documents", exact=False)
        filter_obj = PathFilterImpl([path_spec])
        assert filter_obj.matches(sample_result)

    def test_path_filter_no_match(self, sample_result):
        """Test path filter non-matching."""
        path_spec = PathFilter(path="Downloads", exact=False)
        filter_obj = PathFilterImpl([path_spec])
        assert not filter_obj.matches(sample_result)

    def test_filter_chain(self, sample_result):
        """Test filter chain with multiple filters."""
        chain = FilterChain()
        chain.add_filter(FileTypeFilter({"pdf"}))
        chain.add_filter(
            SizeFilterImpl(
                [SizeFilter(SizeOperator.GREATER, 1 * 1024 * 1024, "mb")]
            )
        )
        chain.add_filter(PathFilterImpl([PathFilter("Documents", False)]))

        assert chain.matches(sample_result)


class TestSearchHistory:
    """Test search history functionality."""

    @pytest.fixture
    def temp_history_file(self):
        """Create temporary history file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_path = f.name
        yield temp_path
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_add_entry(self, temp_history_file):
        """Test adding entry to history."""
        history = SearchHistory(history_file=temp_history_file)
        history.add("test query", result_count=10, execution_time_ms=50.5)

        assert len(history) == 1
        assert history.entries[0].query == "test query"
        assert history.entries[0].result_count == 10

    def test_get_recent(self, temp_history_file):
        """Test getting recent searches."""
        history = SearchHistory(history_file=temp_history_file)
        history.add("query1")
        history.add("query2")
        history.add("query3")

        recent = history.get_recent(limit=2)
        assert len(recent) == 2
        assert recent[0].query == "query3"
        assert recent[1].query == "query2"

    def test_get_popular(self, temp_history_file):
        """Test getting popular searches."""
        history = SearchHistory(history_file=temp_history_file)
        history.add("query1")
        history.add("query2")
        history.add("query1")
        history.add("query1")

        popular = history.get_popular(limit=2)
        assert popular[0] == "query1"

    def test_suggestions_prefix(self, temp_history_file):
        """Test autocomplete suggestions with prefix match."""
        history = SearchHistory(history_file=temp_history_file)
        history.add("python tutorial")
        history.add("python examples")
        history.add("javascript basics")

        suggestions = history.get_suggestions("pyth")
        assert "python tutorial" in suggestions
        assert "python examples" in suggestions

    def test_suggestions_contains(self, temp_history_file):
        """Test autocomplete suggestions with contains match."""
        history = SearchHistory(history_file=temp_history_file)
        history.add("learn python programming")
        history.add("advanced python")

        suggestions = history.get_suggestions("python")
        assert len(suggestions) >= 2

    def test_search_history(self, temp_history_file):
        """Test searching history."""
        history = SearchHistory(history_file=temp_history_file)
        history.add("python tutorial")
        history.add("javascript guide")
        history.add("python advanced")

        results = history.search("python")
        assert len(results) == 2

    def test_statistics(self, temp_history_file):
        """Test history statistics."""
        history = SearchHistory(history_file=temp_history_file)
        history.add("query1", result_count=10, execution_time_ms=50)
        history.add("query2", result_count=20, execution_time_ms=100)

        stats = history.get_statistics()
        assert stats["total_searches"] == 2
        assert stats["unique_queries"] == 2
        assert stats["average_results"] == 15.0
        assert stats["average_time_ms"] == 75.0

    def test_clear_history(self, temp_history_file):
        """Test clearing history."""
        history = SearchHistory(history_file=temp_history_file)
        history.add("query1")
        history.add("query2")
        history.clear()

        assert len(history) == 0

    def test_remove_query(self, temp_history_file):
        """Test removing specific query."""
        history = SearchHistory(history_file=temp_history_file)
        history.add("query1")
        history.add("query2")
        history.add("query1")

        history.remove_query("query1")
        assert len(history) == 1
        assert history.entries[0].query == "query2"

    def test_persistence(self, temp_history_file):
        """Test history persistence."""
        # Add entries
        history1 = SearchHistory(history_file=temp_history_file)
        history1.add("query1")
        history1.add("query2")

        # Load in new instance
        history2 = SearchHistory(history_file=temp_history_file)
        assert len(history2) == 2
        assert history2.entries[0].query == "query2"
        assert history2.entries[1].query == "query1"


class TestSearchEngine:
    """Test search engine functionality."""

    def test_engine_initialization(self):
        """Test search engine initialization."""
        engine = SearchEngine()
        assert engine is not None

    def test_availability(self):
        """Test search backend availability check."""
        engine = SearchEngine()
        # Should have at least one backend available
        assert isinstance(engine.is_available, bool)

    def test_suggestions(self):
        """Test search suggestions."""
        engine = SearchEngine()
        suggestions = engine.get_suggestions("ext:", limit=5)
        assert isinstance(suggestions, list)

    def test_cancel(self):
        """Test search cancellation."""
        engine = SearchEngine()
        engine.cancel()
        assert engine._cancel_flag.is_set()


def test_integration_everything_query():
    """Integration test: Parse query and build Everything query."""
    parser = QueryParser()
    parsed = parser.parse("python * tutorial ext:pdf size:>5mb modified:thisweek")
    everything_query = parser.build_everything_query(parsed)

    assert "python" in everything_query.lower()
    assert "tutorial" in everything_query.lower()
    assert "*.pdf" in everything_query.lower()
    assert "size:" in everything_query.lower()


def test_integration_filter_chain():
    """Integration test: Create filter chain from parsed query."""
    from .filters import create_filter_chain_from_query

    parser = QueryParser()
    parsed = parser.parse("report ext:pdf size:>10mb path:documents")
    filter_chain = create_filter_chain_from_query(parsed)

    assert len(filter_chain) >= 3  # Type, size, and path filters


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
