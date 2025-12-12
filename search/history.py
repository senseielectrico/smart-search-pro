"""
Search history management with autocomplete suggestions.

Maintains a persistent history of searches with frequency tracking and smart suggestions.
"""

import json
import os
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class SearchHistoryEntry:
    """Single search history entry."""

    query: str
    timestamp: str
    result_count: int = 0
    execution_time_ms: float = 0.0
    filters_used: List[str] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.filters_used is None:
            self.filters_used = []


class SearchHistory:
    """
    Search history manager with smart autocomplete.

    Features:
    - Persistent storage
    - Frequency tracking
    - Recent searches
    - Popular searches
    - Filter-based suggestions
    """

    def __init__(
        self,
        history_file: Optional[str] = None,
        max_entries: int = 1000,
        max_suggestions: int = 20,
    ):
        """
        Initialize search history.

        Args:
            history_file: Path to history file (default: ~/.smart_search_history.json)
            max_entries: Maximum number of entries to keep
            max_suggestions: Maximum number of suggestions to return
        """
        if history_file is None:
            history_file = os.path.join(
                os.path.expanduser("~"), ".smart_search_history.json"
            )

        self.history_file = Path(history_file)
        self.max_entries = max_entries
        self.max_suggestions = max_suggestions

        self.entries: List[SearchHistoryEntry] = []
        self.query_frequency: Dict[str, int] = defaultdict(int)
        self.filter_frequency: Dict[str, int] = defaultdict(int)

        self._load()

    def add(
        self,
        query: str,
        result_count: int = 0,
        execution_time_ms: float = 0.0,
        filters_used: Optional[List[str]] = None,
    ):
        """
        Add search to history.

        Args:
            query: Search query string
            result_count: Number of results returned
            execution_time_ms: Search execution time in milliseconds
            filters_used: List of filter types used (ext, size, date, etc.)
        """
        if not query.strip():
            return

        # Normalize query
        normalized_query = query.strip()

        # Create entry
        entry = SearchHistoryEntry(
            query=normalized_query,
            timestamp=datetime.now().isoformat(),
            result_count=result_count,
            execution_time_ms=execution_time_ms,
            filters_used=filters_used or [],
        )

        # Add to entries
        self.entries.insert(0, entry)

        # Update frequency
        self.query_frequency[normalized_query] += 1

        # Update filter frequency
        if filters_used:
            for filter_type in filters_used:
                self.filter_frequency[filter_type] += 1

        # Trim to max entries
        self.entries = self.entries[: self.max_entries]

        # Save to disk
        self._save()

    def get_recent(self, limit: int = 10) -> List[SearchHistoryEntry]:
        """
        Get recent searches.

        Args:
            limit: Maximum number of recent searches

        Returns:
            List of recent SearchHistoryEntry objects
        """
        return self.entries[:limit]

    def get_popular(self, limit: int = 10) -> List[str]:
        """
        Get most popular searches.

        Args:
            limit: Maximum number of popular searches

        Returns:
            List of popular query strings
        """
        sorted_queries = sorted(
            self.query_frequency.items(), key=lambda x: x[1], reverse=True
        )
        return [query for query, _ in sorted_queries[:limit]]

    def get_suggestions(
        self, partial_query: str, limit: Optional[int] = None
    ) -> List[str]:
        """
        Get autocomplete suggestions based on partial query.

        Args:
            partial_query: Partial query string
            limit: Maximum number of suggestions (default: max_suggestions)

        Returns:
            List of suggested query strings
        """
        if limit is None:
            limit = self.max_suggestions

        if not partial_query:
            # Return recent searches
            return [entry.query for entry in self.get_recent(limit)]

        partial_lower = partial_query.lower()
        suggestions = []
        seen = set()

        # First priority: Exact prefix matches (case-insensitive)
        for query, freq in sorted(
            self.query_frequency.items(), key=lambda x: x[1], reverse=True
        ):
            if query.lower().startswith(partial_lower):
                if query not in seen:
                    suggestions.append(query)
                    seen.add(query)
                if len(suggestions) >= limit:
                    return suggestions

        # Second priority: Contains matches
        for query, freq in sorted(
            self.query_frequency.items(), key=lambda x: x[1], reverse=True
        ):
            if partial_lower in query.lower() and query not in seen:
                suggestions.append(query)
                seen.add(query)
                if len(suggestions) >= limit:
                    return suggestions

        # Third priority: Recent searches that might be related
        for entry in self.entries:
            query = entry.query
            if any(
                word in query.lower() for word in partial_lower.split()
            ) and query not in seen:
                suggestions.append(query)
                seen.add(query)
                if len(suggestions) >= limit:
                    return suggestions

        return suggestions

    def get_filter_suggestions(self, limit: int = 10) -> List[str]:
        """
        Get popular filter suggestions.

        Args:
            limit: Maximum number of suggestions

        Returns:
            List of popular filter strings
        """
        sorted_filters = sorted(
            self.filter_frequency.items(), key=lambda x: x[1], reverse=True
        )
        return [filter_type for filter_type, _ in sorted_filters[:limit]]

    def search(self, keyword: str, limit: int = 50) -> List[SearchHistoryEntry]:
        """
        Search history for entries matching keyword.

        Args:
            keyword: Keyword to search for
            limit: Maximum number of results

        Returns:
            List of matching SearchHistoryEntry objects
        """
        keyword_lower = keyword.lower()
        matches = []

        for entry in self.entries:
            if keyword_lower in entry.query.lower():
                matches.append(entry)
                if len(matches) >= limit:
                    break

        return matches

    def get_statistics(self) -> Dict:
        """
        Get search history statistics.

        Returns:
            Dictionary with statistics
        """
        total_searches = len(self.entries)
        unique_queries = len(self.query_frequency)

        avg_results = 0
        avg_time = 0
        if self.entries:
            avg_results = sum(e.result_count for e in self.entries) / total_searches
            avg_time = sum(e.execution_time_ms for e in self.entries) / total_searches

        popular_filters = self.get_filter_suggestions(5)

        return {
            "total_searches": total_searches,
            "unique_queries": unique_queries,
            "average_results": round(avg_results, 2),
            "average_time_ms": round(avg_time, 2),
            "popular_filters": popular_filters,
            "most_popular_query": self.get_popular(1)[0] if self.query_frequency else None,
        }

    def clear(self):
        """Clear all history."""
        self.entries.clear()
        self.query_frequency.clear()
        self.filter_frequency.clear()
        self._save()

    def remove_query(self, query: str):
        """
        Remove all instances of a specific query from history.

        Args:
            query: Query string to remove
        """
        self.entries = [e for e in self.entries if e.query != query]
        if query in self.query_frequency:
            del self.query_frequency[query]
        self._save()

    def export_to_json(self, output_file: str):
        """
        Export history to JSON file.

        Args:
            output_file: Path to output file
        """
        data = {
            "entries": [asdict(entry) for entry in self.entries],
            "statistics": self.get_statistics(),
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def import_from_json(self, input_file: str, merge: bool = True):
        """
        Import history from JSON file.

        Args:
            input_file: Path to input file
            merge: If True, merge with existing history; if False, replace
        """
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            imported_entries = [
                SearchHistoryEntry(**entry) for entry in data.get("entries", [])
            ]

            if merge:
                # Merge with existing entries
                existing_queries = {e.query for e in self.entries}
                new_entries = [
                    e for e in imported_entries if e.query not in existing_queries
                ]
                self.entries = new_entries + self.entries
            else:
                # Replace existing entries
                self.entries = imported_entries

            # Rebuild frequency maps
            self._rebuild_frequency_maps()

            # Trim and save
            self.entries = self.entries[: self.max_entries]
            self._save()

        except (OSError, json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to import history: {e}")

    def _rebuild_frequency_maps(self):
        """Rebuild frequency maps from entries."""
        self.query_frequency.clear()
        self.filter_frequency.clear()

        for entry in self.entries:
            self.query_frequency[entry.query] += 1
            for filter_type in entry.filters_used:
                self.filter_frequency[filter_type] += 1

    def _load(self):
        """Load history from disk."""
        if not self.history_file.exists():
            return

        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.entries = [
                SearchHistoryEntry(**entry) for entry in data.get("entries", [])
            ]
            self.query_frequency = defaultdict(
                int, data.get("query_frequency", {})
            )
            self.filter_frequency = defaultdict(
                int, data.get("filter_frequency", {})
            )

        except (OSError, json.JSONDecodeError):
            # If loading fails, start fresh
            self.entries = []
            self.query_frequency = defaultdict(int)
            self.filter_frequency = defaultdict(int)

    def _save(self):
        """Save history to disk."""
        try:
            # Create parent directory if it doesn't exist
            self.history_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "entries": [asdict(entry) for entry in self.entries],
                "query_frequency": dict(self.query_frequency),
                "filter_frequency": dict(self.filter_frequency),
            }

            # Write to temporary file first
            temp_file = self.history_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic replace
            temp_file.replace(self.history_file)

        except OSError:
            # Silently fail if we can't save
            pass

    def __len__(self) -> int:
        """Get number of entries in history."""
        return len(self.entries)

    def __iter__(self):
        """Iterate over history entries."""
        return iter(self.entries)
