"""
Search engine that integrates Everything SDK with fallback to Windows Search API.

Provides high-performance file search with async support, cancellation, and progress tracking
with auto-detected optimal workers.
"""

import os
import sys
import threading
import time
from concurrent.futures import as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

# Add parent directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.threading import create_mixed_executor, ManagedThreadPoolExecutor

try:
    import win32com.client
    WINDOWS_SEARCH_AVAILABLE = True
except ImportError:
    WINDOWS_SEARCH_AVAILABLE = False

from .everything_sdk import EverythingSDKError, EverythingSDK, EverythingSort
from .filters import FilterChain, create_filter_chain_from_query
from .query_parser import ParsedQuery, QueryParser
from .mime_filter import MimeFilter, parse_mime_query


@dataclass
class SearchResult:
    """Unified search result representation."""

    filename: str
    path: str
    full_path: str
    extension: str = ""
    size: int = 0
    date_created: int = 0
    date_modified: int = 0
    date_accessed: int = 0
    attributes: int = 0
    is_folder: bool = False
    relevance_score: float = 1.0

    def __post_init__(self):
        """Ensure full_path is set."""
        if not self.full_path and self.path and self.filename:
            self.full_path = os.path.join(self.path, self.filename)


class SearchEngine:
    """
    High-performance search engine with Everything SDK integration.

    Features:
    - Primary: Everything SDK for instant search
    - Fallback: Windows Search API
    - Advanced filtering (size, date, content, etc.)
    - Threading for async operations
    - Cancellation support
    - Progress callbacks
    """

    def __init__(
        self,
        everything_dll_path: Optional[str] = None,
        max_workers: Optional[int] = None,
    ):
        """
        Initialize search engine with auto-detected optimal workers.

        Args:
            everything_dll_path: Optional path to Everything DLL
            max_workers: Maximum number of worker threads (None = auto-detect for mixed workload)
        """
        self.query_parser = QueryParser()
        self.max_workers = max_workers
        self._cancel_flag = threading.Event()
        self._executor = create_mixed_executor(
            max_workers=max_workers,
            thread_name_prefix="Search"
        )

        # Try to initialize Everything SDK
        self.everything_sdk = None
        self.use_everything = False

        try:
            self.everything_sdk = EverythingSDK(dll_path=everything_dll_path)
            self.use_everything = self.everything_sdk.is_available
        except EverythingSDKError:
            pass

        # Check Windows Search availability
        self.windows_search_available = WINDOWS_SEARCH_AVAILABLE

        # Initialize MIME filter
        self.mime_filter = MimeFilter()

    @property
    def is_available(self) -> bool:
        """Check if any search backend is available."""
        return self.use_everything or self.windows_search_available

    def search(
        self,
        query: str,
        max_results: int = 1000,
        sort_by: str = "name",
        ascending: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[SearchResult]:
        """
        Search for files and folders synchronously.

        Args:
            query: Search query string
            max_results: Maximum number of results
            sort_by: Sort field (name, path, size, modified, created)
            ascending: Sort in ascending order
            progress_callback: Optional callback for progress updates (current, total)

        Returns:
            List of SearchResult objects

        Raises:
            ValueError: If no search backend is available
        """
        if not self.is_available:
            raise ValueError(
                "No search backend available. Install Everything or ensure Windows Search is enabled."
            )

        # Reset cancel flag
        self._cancel_flag.clear()

        # Parse query
        parsed_query = self.query_parser.parse(query)

        # Search using available backend
        if self.use_everything:
            results = self._search_everything(
                parsed_query, max_results, sort_by, ascending
            )
        else:
            results = self._search_windows(parsed_query, max_results)

        # Apply additional filters
        if parsed_query.has_filters():
            filter_chain = create_filter_chain_from_query(parsed_query)
            if len(filter_chain) > 0:
                results = self._apply_filters(
                    results, filter_chain, progress_callback
                )

        # Apply MIME filters if present
        mime_criteria = parse_mime_query(query)
        if mime_criteria:
            results = self._apply_mime_filter(results, mime_criteria, progress_callback)

        # Limit results
        results = results[:max_results]

        # Final progress update
        if progress_callback:
            progress_callback(len(results), len(results))

        return results

    def search_async(
        self,
        query: str,
        max_results: int = 1000,
        sort_by: str = "name",
        ascending: bool = True,
        callback: Optional[Callable[[List[SearchResult]], None]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> threading.Thread:
        """
        Search for files and folders asynchronously.

        Args:
            query: Search query string
            max_results: Maximum number of results
            sort_by: Sort field
            ascending: Sort in ascending order
            callback: Callback function to receive results
            progress_callback: Optional callback for progress updates

        Returns:
            Thread object for the search operation
        """

        def search_thread():
            try:
                results = self.search(
                    query, max_results, sort_by, ascending, progress_callback
                )
                if callback and not self._cancel_flag.is_set():
                    callback(results)
            except Exception as e:
                if callback:
                    callback([])

        thread = threading.Thread(target=search_thread, daemon=True)
        thread.start()
        return thread

    def cancel(self):
        """Cancel ongoing search operation."""
        self._cancel_flag.set()

    def _search_everything(
        self,
        parsed_query: ParsedQuery,
        max_results: int,
        sort_by: str,
        ascending: bool,
    ) -> List[SearchResult]:
        """Search using Everything SDK."""
        # Build Everything query
        everything_query = self.query_parser.build_everything_query(parsed_query)

        # Map sort options
        sort_map = {
            "name": (
                EverythingSort.NAME_ASCENDING
                if ascending
                else EverythingSort.NAME_DESCENDING
            ),
            "path": (
                EverythingSort.PATH_ASCENDING
                if ascending
                else EverythingSort.PATH_DESCENDING
            ),
            "size": (
                EverythingSort.SIZE_ASCENDING
                if ascending
                else EverythingSort.SIZE_DESCENDING
            ),
            "modified": (
                EverythingSort.DATE_MODIFIED_ASCENDING
                if ascending
                else EverythingSort.DATE_MODIFIED_DESCENDING
            ),
            "created": (
                EverythingSort.DATE_CREATED_ASCENDING
                if ascending
                else EverythingSort.DATE_CREATED_DESCENDING
            ),
            "accessed": (
                EverythingSort.DATE_ACCESSED_ASCENDING
                if ascending
                else EverythingSort.DATE_ACCESSED_DESCENDING
            ),
        }
        sort_option = sort_map.get(sort_by, EverythingSort.NAME_ASCENDING)

        # Execute search
        everything_results = self.everything_sdk.search(
            query=everything_query,
            max_results=max_results,
            sort=sort_option,
            regex=parsed_query.is_regex,
        )

        # Convert to unified SearchResult format
        results = []
        for er in everything_results:
            if self._cancel_flag.is_set():
                break

            result = SearchResult(
                filename=er.filename,
                path=er.path,
                full_path=er.full_path,
                extension=er.extension,
                size=er.size,
                date_created=er.date_created,
                date_modified=er.date_modified,
                date_accessed=er.date_accessed,
                attributes=er.attributes,
                is_folder=er.is_folder,
            )
            results.append(result)

        return results

    def _search_windows(
        self, parsed_query: ParsedQuery, max_results: int
    ) -> List[SearchResult]:
        """Search using Windows Search API."""
        if not WINDOWS_SEARCH_AVAILABLE:
            return []

        try:
            connection = win32com.client.Dispatch("ADODB.Connection")
            recordset = win32com.client.Dispatch("ADODB.Recordset")

            connection.Open("Provider=Search.CollatorDSO;Extended Properties='Application=Windows';")

            # Build SQL query
            sql_query = self._build_windows_search_query(parsed_query, max_results)

            recordset.Open(sql_query, connection)

            results = []
            while not recordset.EOF and not self._cancel_flag.is_set():
                try:
                    full_path = recordset.Fields("System.ItemPathDisplay").Value
                    if full_path:
                        path_obj = Path(full_path)

                        result = SearchResult(
                            filename=path_obj.name,
                            path=str(path_obj.parent),
                            full_path=full_path,
                            extension=path_obj.suffix.lstrip("."),
                            size=recordset.Fields("System.Size").Value or 0,
                            is_folder=path_obj.is_dir(),
                        )
                        results.append(result)

                except Exception:
                    pass

                recordset.MoveNext()

            recordset.Close()
            connection.Close()

            return results

        except Exception:
            return []

    def _build_windows_search_query(
        self, parsed_query: ParsedQuery, max_results: int
    ) -> str:
        """Build SQL query for Windows Search."""
        conditions = []

        # Add keyword conditions
        if parsed_query.keywords:
            keyword_conditions = [
                f"CONTAINS(System.FileName, '\"{kw}\"')" for kw in parsed_query.keywords
            ]
            conditions.append(f"({' OR '.join(keyword_conditions)})")

        # Add extension conditions
        if parsed_query.extensions:
            ext_conditions = [
                f"System.FileExtension = '.{ext}'" for ext in parsed_query.extensions
            ]
            conditions.append(f"({' OR '.join(ext_conditions)})")

        # Add path conditions
        if parsed_query.path_filters:
            path_conditions = [
                f"CONTAINS(System.ItemPathDisplay, '\"{pf.path}\"')"
                for pf in parsed_query.path_filters
            ]
            conditions.append(f"({' OR '.join(path_conditions)})")

        # Combine conditions
        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
        SELECT TOP {max_results}
            System.ItemPathDisplay,
            System.FileName,
            System.Size,
            System.DateModified,
            System.DateCreated
        FROM SystemIndex
        WHERE {where_clause}
        ORDER BY System.DateModified DESC
        """

        return query

    def _apply_filters(
        self,
        results: List[SearchResult],
        filter_chain: FilterChain,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[SearchResult]:
        """Apply filter chain to results with optional threading."""
        if len(results) < 100:
            # Small result set, filter directly
            filtered = []
            total = len(results)
            for i, result in enumerate(results):
                if self._cancel_flag.is_set():
                    break

                if filter_chain.matches(result):
                    filtered.append(result)

                if progress_callback and i % 10 == 0:
                    progress_callback(i, total)

            return filtered

        # Large result set, use threading
        filtered = []
        total = len(results)
        chunk_size = max(10, len(results) // self.max_workers)

        def filter_chunk(chunk):
            """Filter a chunk of results."""
            return [r for r in chunk if filter_chain.matches(r)]

        # Split results into chunks
        chunks = [
            results[i : i + chunk_size]
            for i in range(0, len(results), chunk_size)
        ]

        # Process chunks in parallel
        futures = {
            self._executor.submit(filter_chunk, chunk): i
            for i, chunk in enumerate(chunks)
        }

        processed = 0
        for future in as_completed(futures):
            if self._cancel_flag.is_set():
                break

            chunk_results = future.result()
            filtered.extend(chunk_results)

            processed += 1
            if progress_callback:
                progress_callback(
                    processed * chunk_size, total
                )

        return filtered

    def _apply_mime_filter(
        self,
        results: List[SearchResult],
        criteria,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[SearchResult]:
        """Apply MIME filter to results."""
        filtered = []
        total = len(results)

        for i, result in enumerate(results):
            if self._cancel_flag.is_set():
                break

            # Apply MIME filter
            if self.mime_filter.matches(result.full_path, criteria):
                filtered.append(result)

            if progress_callback and i % 10 == 0:
                progress_callback(i, total)

        return filtered

    def get_suggestions(self, partial_query: str, limit: int = 10) -> List[str]:
        """
        Get search suggestions based on partial query.

        Args:
            partial_query: Partial search query
            limit: Maximum number of suggestions

        Returns:
            List of suggested queries
        """
        suggestions = []

        # File type suggestions
        if "ext:" in partial_query or "type:" in partial_query:
            common_types = ["pdf", "docx", "xlsx", "jpg", "png", "mp4", "zip"]
            suggestions.extend(
                [f"ext:{t}" for t in common_types if t.startswith(partial_query[-3:])]
            )

        # Date suggestions
        if "modified:" in partial_query or "created:" in partial_query:
            date_presets = [
                "today",
                "yesterday",
                "thisweek",
                "lastweek",
                "thismonth",
                "lastmonth",
            ]
            prefix = "modified:" if "modified:" in partial_query else "created:"
            suggestions.extend([f"{prefix}{p}" for p in date_presets])

        # Size suggestions
        if "size:" in partial_query:
            size_examples = [">10mb", "<1gb", ">100kb", "<500mb"]
            suggestions.extend([f"size:{s}" for s in size_examples])

        # MIME type suggestions
        if "mime:" in partial_query:
            mime_examples = ["image/*", "video/*", "audio/*", "application/pdf"]
            suggestions.extend([f"mime:{m}" for m in mime_examples])

        # Type category suggestions
        if "type:" in partial_query:
            type_examples = ["image", "video", "audio", "document", "archive"]
            suggestions.extend([f"type:{t}" for t in type_examples])

        return suggestions[:limit]

    def shutdown(self):
        """Shutdown search engine and clean up resources."""
        self.cancel()
        self._executor.shutdown(wait=True)
        if self.everything_sdk:
            self.everything_sdk.cleanup()

    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.shutdown()
        except Exception:
            pass
