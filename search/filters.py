"""
Filter implementations for search results.

Provides specialized filters for file type, size, date, path, and content filtering.
"""

import os
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Protocol

from .query_parser import DateFilter, DatePreset, PathFilter, SizeFilter, SizeOperator


class SearchResult(Protocol):
    """Protocol for search results that can be filtered."""

    full_path: str
    size: int
    date_modified: int
    date_created: int
    date_accessed: int
    extension: str
    is_folder: bool


class BaseFilter(ABC):
    """Base class for all filters."""

    @abstractmethod
    def matches(self, result: SearchResult) -> bool:
        """Check if result matches filter criteria."""
        pass


class FileTypeFilter(BaseFilter):
    """Filter results by file type/extension."""

    def __init__(self, extensions: set[str]):
        """
        Initialize file type filter.

        Args:
            extensions: Set of file extensions to match (without dot)
        """
        self.extensions = {ext.lower().lstrip(".") for ext in extensions}

    def matches(self, result: SearchResult) -> bool:
        """Check if result's extension matches any allowed extensions."""
        if result.is_folder:
            return False

        ext = result.extension.lower().lstrip(".")
        return ext in self.extensions


class SizeFilterImpl(BaseFilter):
    """Filter results by file size."""

    def __init__(self, size_filters: List[SizeFilter]):
        """
        Initialize size filter.

        Args:
            size_filters: List of size filter specifications
        """
        self.size_filters = size_filters

    def matches(self, result: SearchResult) -> bool:
        """Check if result's size matches all size filters."""
        if result.is_folder:
            return True  # Folders always pass size filters

        for size_filter in self.size_filters:
            if not self._matches_size_filter(result.size, size_filter):
                return False
        return True

    def _matches_size_filter(self, size: int, filter_spec: SizeFilter) -> bool:
        """Check if size matches a single size filter specification."""
        if filter_spec.operator == SizeOperator.GREATER:
            return size > filter_spec.value
        elif filter_spec.operator == SizeOperator.LESS:
            return size < filter_spec.value
        elif filter_spec.operator == SizeOperator.GREATER_EQUAL:
            return size >= filter_spec.value
        elif filter_spec.operator == SizeOperator.LESS_EQUAL:
            return size <= filter_spec.value
        elif filter_spec.operator == SizeOperator.EQUAL:
            # Allow 1% tolerance for equality
            tolerance = max(filter_spec.value * 0.01, 1)
            return abs(size - filter_spec.value) <= tolerance
        return True


class DateFilterImpl(BaseFilter):
    """Filter results by file dates (modified, created, accessed)."""

    def __init__(self, date_filters: List[DateFilter]):
        """
        Initialize date filter.

        Args:
            date_filters: List of date filter specifications
        """
        self.date_filters = date_filters

    def matches(self, result: SearchResult) -> bool:
        """Check if result's dates match all date filters."""
        for date_filter in self.date_filters:
            if not self._matches_date_filter(result, date_filter):
                return False
        return True

    def _matches_date_filter(self, result: SearchResult, filter_spec: DateFilter) -> bool:
        """Check if result matches a single date filter specification."""
        # Get the relevant timestamp
        field_map = {
            "modified": result.date_modified,
            "created": result.date_created,
            "accessed": result.date_accessed,
        }
        timestamp = field_map.get(filter_spec.field, result.date_modified)

        # Convert Windows FILETIME to datetime
        # FILETIME is 100-nanosecond intervals since January 1, 1601
        if timestamp == 0:
            return True  # No timestamp, always pass

        try:
            # Convert FILETIME to Unix timestamp
            unix_timestamp = (timestamp / 10000000.0) - 11644473600
            file_date = datetime.fromtimestamp(unix_timestamp)
        except (ValueError, OSError):
            return True  # Invalid timestamp, pass by default

        # Check against preset
        if filter_spec.preset:
            return self._matches_preset(file_date, filter_spec.preset)

        # Check against specific date
        if filter_spec.date:
            return self._matches_date_comparison(
                file_date, filter_spec.date, filter_spec.operator
            )

        # Check against year/month/day
        if filter_spec.year:
            if filter_spec.day:
                # Exact date
                target_date = datetime(
                    filter_spec.year, filter_spec.month, filter_spec.day
                )
                return self._matches_date_comparison(
                    file_date, target_date, filter_spec.operator
                )
            elif filter_spec.month:
                # Month range
                return file_date.year == filter_spec.year and file_date.month == filter_spec.month
            else:
                # Year range
                return file_date.year == filter_spec.year

        return True

    def _matches_preset(self, file_date: datetime, preset: DatePreset) -> bool:
        """Check if file date matches a preset."""
        now = datetime.now()
        today = datetime(now.year, now.month, now.day)

        if preset == DatePreset.TODAY:
            return file_date.date() == today.date()

        elif preset == DatePreset.YESTERDAY:
            yesterday = today - timedelta(days=1)
            return file_date.date() == yesterday.date()

        elif preset == DatePreset.THIS_WEEK:
            week_start = today - timedelta(days=today.weekday())
            return file_date >= week_start

        elif preset == DatePreset.LAST_WEEK:
            this_week_start = today - timedelta(days=today.weekday())
            last_week_start = this_week_start - timedelta(days=7)
            return last_week_start <= file_date < this_week_start

        elif preset == DatePreset.THIS_MONTH:
            month_start = datetime(today.year, today.month, 1)
            return file_date >= month_start

        elif preset == DatePreset.LAST_MONTH:
            month_start = datetime(today.year, today.month, 1)
            if today.month == 1:
                last_month_start = datetime(today.year - 1, 12, 1)
            else:
                last_month_start = datetime(today.year, today.month - 1, 1)
            return last_month_start <= file_date < month_start

        elif preset == DatePreset.THIS_YEAR:
            year_start = datetime(today.year, 1, 1)
            return file_date >= year_start

        elif preset == DatePreset.LAST_YEAR:
            last_year_start = datetime(today.year - 1, 1, 1)
            this_year_start = datetime(today.year, 1, 1)
            return last_year_start <= file_date < this_year_start

        return True

    def _matches_date_comparison(
        self,
        file_date: datetime,
        target_date: datetime,
        operator: Optional[SizeOperator],
    ) -> bool:
        """Compare file date with target date using operator."""
        if not operator:
            return file_date.date() == target_date.date()

        if operator == SizeOperator.GREATER:
            return file_date > target_date
        elif operator == SizeOperator.LESS:
            return file_date < target_date
        elif operator == SizeOperator.GREATER_EQUAL:
            return file_date >= target_date
        elif operator == SizeOperator.LESS_EQUAL:
            return file_date <= target_date
        elif operator == SizeOperator.EQUAL:
            return file_date.date() == target_date.date()

        return True


class PathFilterImpl(BaseFilter):
    """Filter results by file path."""

    def __init__(self, path_filters: List[PathFilter]):
        """
        Initialize path filter.

        Args:
            path_filters: List of path filter specifications
        """
        self.path_filters = path_filters

    def matches(self, result: SearchResult) -> bool:
        """Check if result's path matches any path filter."""
        if not self.path_filters:
            return True

        full_path = result.full_path.lower()

        for path_filter in self.path_filters:
            filter_path = path_filter.path.lower().replace("/", "\\")

            if path_filter.exact:
                # Exact path match
                if filter_path in full_path:
                    return True
            else:
                # Contains match
                if filter_path in full_path:
                    return True

        return False


class ContentFilter(BaseFilter):
    """
    Filter results by file content.

    Note: This is a basic implementation that reads file content.
    For large files or binary files, this may be slow or ineffective.
    """

    def __init__(
        self,
        keywords: List[str],
        case_sensitive: bool = False,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB default
    ):
        """
        Initialize content filter.

        Args:
            keywords: List of keywords to search for in content
            case_sensitive: Whether search is case-sensitive
            max_file_size: Maximum file size to search (in bytes)
        """
        self.keywords = keywords
        self.case_sensitive = case_sensitive
        self.max_file_size = max_file_size

        # Text file extensions
        self.text_extensions = {
            "txt",
            "md",
            "py",
            "js",
            "ts",
            "java",
            "cpp",
            "c",
            "h",
            "cs",
            "go",
            "rs",
            "rb",
            "php",
            "html",
            "css",
            "xml",
            "json",
            "yaml",
            "yml",
            "toml",
            "ini",
            "cfg",
            "conf",
            "log",
            "csv",
            "sql",
            "sh",
            "bat",
            "ps1",
        }

    def matches(self, result: SearchResult) -> bool:
        """Check if file content contains any of the keywords."""
        if result.is_folder:
            return False

        # Skip if file is too large
        if result.size > self.max_file_size:
            return False

        # Skip if not a text file
        ext = result.extension.lower().lstrip(".")
        if ext not in self.text_extensions:
            return False

        try:
            # Try to read file content
            with open(result.full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if not self.case_sensitive:
                content = content.lower()

            # Check if any keyword matches
            for keyword in self.keywords:
                search_keyword = (
                    keyword if self.case_sensitive else keyword.lower()
                )
                if search_keyword in content:
                    return True

            return False

        except (OSError, UnicodeDecodeError, PermissionError):
            # Skip files that can't be read
            return False


class FilterChain(BaseFilter):
    """Chain multiple filters together with AND logic."""

    def __init__(self, filters: Optional[List[BaseFilter]] = None):
        """
        Initialize filter chain.

        Args:
            filters: List of filters to chain
        """
        self.filters = filters or []

    def add_filter(self, filter_obj: BaseFilter):
        """Add a filter to the chain."""
        self.filters.append(filter_obj)

    def matches(self, result: SearchResult) -> bool:
        """Check if result matches all filters in the chain."""
        for filter_obj in self.filters:
            if not filter_obj.matches(result):
                return False
        return True

    def __len__(self) -> int:
        """Get number of filters in chain."""
        return len(self.filters)


def create_filter_chain_from_query(parsed_query) -> FilterChain:
    """
    Create a filter chain from a parsed query.

    Args:
        parsed_query: ParsedQuery object

    Returns:
        FilterChain with all applicable filters
    """
    chain = FilterChain()

    # Add file type filter
    if parsed_query.extensions:
        chain.add_filter(FileTypeFilter(parsed_query.extensions))

    # Add size filter
    if parsed_query.size_filters:
        chain.add_filter(SizeFilterImpl(parsed_query.size_filters))

    # Add date filter
    if parsed_query.date_filters:
        chain.add_filter(DateFilterImpl(parsed_query.date_filters))

    # Add path filter
    if parsed_query.path_filters:
        chain.add_filter(PathFilterImpl(parsed_query.path_filters))

    # Add content filter
    if parsed_query.content_keywords:
        chain.add_filter(ContentFilter(parsed_query.content_keywords))

    return chain
