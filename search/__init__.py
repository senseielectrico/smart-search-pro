"""
Smart Search Pro - Advanced Search Module

This module provides comprehensive search functionality with Everything SDK integration
and Windows Search API fallback.
"""

from .engine import SearchEngine, SearchResult
from .query_parser import QueryParser, ParsedQuery
from .filters import (
    FileTypeFilter,
    SizeFilter,
    DateFilter,
    PathFilter,
    ContentFilter,
    FilterChain,
)
from .history import SearchHistory
from .everything_sdk import EverythingSDK, EverythingSDKError, EverythingError

__all__ = [
    # Core search
    "SearchEngine",
    "SearchResult",
    # Query parsing
    "QueryParser",
    "ParsedQuery",
    # Filters
    "FileTypeFilter",
    "SizeFilter",
    "DateFilter",
    "PathFilter",
    "ContentFilter",
    "FilterChain",
    # History
    "SearchHistory",
    # Everything SDK
    "EverythingSDK",
    "EverythingSDKError",
    "EverythingError",  # Backward compatibility
]

__version__ = "1.0.0"
