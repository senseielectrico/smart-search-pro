"""
Everything SDK wrapper using ctypes for direct API access.

Provides a high-performance interface to Everything search engine with full API support
and auto-detected optimal workers.
Reference: Everything SDK documentation (https://www.voidtools.com/support/everything/sdk/)
"""

import ctypes
import os
import sys
import subprocess
import threading
from ctypes import (
    POINTER,
    c_bool,
    c_char_p,
    c_int,
    c_uint,
    c_ulonglong,
    c_void_p,
    c_wchar_p,
)
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Callable, List, Optional, Union
import time

# Add parent directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.threading import create_io_executor, ManagedThreadPoolExecutor


class EverythingSDKError(Exception):
    """Exception raised for Everything SDK errors."""

    pass


class EverythingSort(IntEnum):
    """Everything sort options."""

    NAME_ASCENDING = 1
    NAME_DESCENDING = 2
    PATH_ASCENDING = 3
    PATH_DESCENDING = 4
    SIZE_ASCENDING = 5
    SIZE_DESCENDING = 6
    EXTENSION_ASCENDING = 7
    EXTENSION_DESCENDING = 8
    TYPE_NAME_ASCENDING = 9
    TYPE_NAME_DESCENDING = 10
    DATE_CREATED_ASCENDING = 11
    DATE_CREATED_DESCENDING = 12
    DATE_MODIFIED_ASCENDING = 13
    DATE_MODIFIED_DESCENDING = 14
    ATTRIBUTES_ASCENDING = 15
    ATTRIBUTES_DESCENDING = 16
    FILE_LIST_FILENAME_ASCENDING = 17
    FILE_LIST_FILENAME_DESCENDING = 18
    RUN_COUNT_ASCENDING = 19
    RUN_COUNT_DESCENDING = 20
    DATE_RECENTLY_CHANGED_ASCENDING = 21
    DATE_RECENTLY_CHANGED_DESCENDING = 22
    DATE_ACCESSED_ASCENDING = 23
    DATE_ACCESSED_DESCENDING = 24
    DATE_RUN_ASCENDING = 25
    DATE_RUN_DESCENDING = 26


class EverythingRequestFlags(IntEnum):
    """Everything result request flags."""

    FILE_NAME = 0x00000001
    PATH = 0x00000002
    FULL_PATH_AND_FILE_NAME = 0x00000004
    EXTENSION = 0x00000008
    SIZE = 0x00000010
    DATE_CREATED = 0x00000020
    DATE_MODIFIED = 0x00000040
    DATE_ACCESSED = 0x00000080
    ATTRIBUTES = 0x00000100
    FILE_LIST_FILE_NAME = 0x00000200
    RUN_COUNT = 0x00000400
    DATE_RUN = 0x00000800
    DATE_RECENTLY_CHANGED = 0x00001000
    HIGHLIGHTED_FILE_NAME = 0x00002000
    HIGHLIGHTED_PATH = 0x00004000
    HIGHLIGHTED_FULL_PATH_AND_FILE_NAME = 0x00008000


class EverythingErrorCode(IntEnum):
    """Everything error codes."""

    OK = 0
    MEMORY = 1
    IPC = 2
    REGISTERCLASSEX = 3
    CREATEWINDOW = 4
    CREATETHREAD = 5
    INVALIDINDEX = 6
    INVALIDCALL = 7


# Keep backward compatibility
EverythingError = EverythingSDKError


@dataclass
class EverythingResult:
    """Result from Everything search."""

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


class EverythingSDK:
    """
    Everything SDK wrapper for high-performance file searching.

    This class provides a ctypes-based interface to the Everything SDK,
    allowing for fast file and folder searches on Windows. Includes:
    - Asynchronous search with threading
    - Fallback to Windows Search if Everything is unavailable
    - Progress callbacks
    - Result caching
    """

    def __init__(
        self,
        dll_path: Optional[str] = None,
        enable_cache: bool = True,
        cache_ttl: int = 300
    ):
        """
        Initialize Everything SDK.

        Args:
            dll_path: Optional path to Everything64.dll. If not provided,
                     searches in common locations.
            enable_cache: Enable result caching
            cache_ttl: Cache time-to-live in seconds

        Raises:
            EverythingError: If Everything DLL cannot be loaded.
        """
        self._dll = None
        self._is_available = False
        self._use_fallback = False
        self._lock = threading.RLock()
        # Use I/O-optimized executor (Everything queries are I/O bound)
        self._executor = create_io_executor(thread_name_prefix="Everything")

        # Cache
        self._enable_cache = enable_cache
        self._cache_ttl = cache_ttl
        self._cache = {}
        self._cache_times = {}

        try:
            self._dll = self._load_dll(dll_path)
            self._setup_functions()
            self._is_available = self._check_availability()

            if not self._is_available:
                self._try_start_everything()
                self._is_available = self._check_availability()

        except EverythingSDKError as e:
            print(f"Everything SDK not available: {e}")
            print("Falling back to Windows Search")
            self._use_fallback = True

    def _load_dll(self, dll_path: Optional[str] = None) -> ctypes.CDLL:
        """Load Everything DLL."""
        if dll_path and os.path.exists(dll_path):
            try:
                return ctypes.CDLL(dll_path)
            except OSError as e:
                raise EverythingSDKError(f"Failed to load DLL from {dll_path}: {e}")

        # Try common locations
        possible_paths = [
            r"C:\Program Files\Everything\Everything64.dll",
            r"C:\Program Files (x86)\Everything\Everything32.dll",
            r"C:\Program Files\Everything\Everything32.dll",
            os.path.join(os.getenv("PROGRAMFILES", ""), "Everything", "Everything64.dll"),
            os.path.join(
                os.getenv("PROGRAMFILES(X86)", ""), "Everything", "Everything32.dll"
            ),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                try:
                    dll = ctypes.CDLL(path)
                    print(f"Loaded Everything DLL from: {path}")
                    return dll
                except OSError as e:
                    print(f"Failed to load {path}: {e}")
                    continue

        raise EverythingSDKError(
            "Everything DLL not found. Please install Everything or provide dll_path."
        )

    def _try_start_everything(self):
        """Try to start Everything.exe if it's not running."""
        possible_exe_paths = [
            r"C:\Program Files\Everything\Everything.exe",
            r"C:\Program Files (x86)\Everything\Everything.exe",
        ]

        for exe_path in possible_exe_paths:
            if os.path.exists(exe_path):
                try:
                    subprocess.Popen(
                        [exe_path, "-startup"],
                        shell=False,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    print(f"Started Everything from: {exe_path}")
                    time.sleep(2)  # Wait for DB to load
                    return
                except Exception as e:
                    print(f"Failed to start Everything: {e}")

    def _setup_functions(self):
        """Setup function signatures for Everything SDK."""
        # Set search
        self._dll.Everything_SetSearchW.argtypes = [c_wchar_p]
        self._dll.Everything_SetSearchW.restype = None

        # Execute query
        self._dll.Everything_QueryW.argtypes = [c_bool]
        self._dll.Everything_QueryW.restype = c_bool

        # Get result count
        self._dll.Everything_GetNumResults.argtypes = []
        self._dll.Everything_GetNumResults.restype = c_uint

        # Get result details
        self._dll.Everything_GetResultFileNameW.argtypes = [c_uint]
        self._dll.Everything_GetResultFileNameW.restype = c_wchar_p

        self._dll.Everything_GetResultPathW.argtypes = [c_uint]
        self._dll.Everything_GetResultPathW.restype = c_wchar_p

        self._dll.Everything_GetResultFullPathNameW.argtypes = [c_uint, c_wchar_p, c_uint]
        self._dll.Everything_GetResultFullPathNameW.restype = c_uint

        self._dll.Everything_GetResultExtensionW.argtypes = [c_uint]
        self._dll.Everything_GetResultExtensionW.restype = c_wchar_p

        self._dll.Everything_GetResultSize.argtypes = [c_uint, POINTER(c_ulonglong)]
        self._dll.Everything_GetResultSize.restype = c_bool

        self._dll.Everything_GetResultDateCreated.argtypes = [c_uint, POINTER(c_ulonglong)]
        self._dll.Everything_GetResultDateCreated.restype = c_bool

        self._dll.Everything_GetResultDateModified.argtypes = [c_uint, POINTER(c_ulonglong)]
        self._dll.Everything_GetResultDateModified.restype = c_bool

        self._dll.Everything_GetResultDateAccessed.argtypes = [c_uint, POINTER(c_ulonglong)]
        self._dll.Everything_GetResultDateAccessed.restype = c_bool

        self._dll.Everything_GetResultAttributes.argtypes = [c_uint]
        self._dll.Everything_GetResultAttributes.restype = c_uint

        # Sort
        self._dll.Everything_SetSort.argtypes = [c_uint]
        self._dll.Everything_SetSort.restype = None

        # Request flags
        self._dll.Everything_SetRequestFlags.argtypes = [c_uint]
        self._dll.Everything_SetRequestFlags.restype = None

        # Max results
        self._dll.Everything_SetMax.argtypes = [c_uint]
        self._dll.Everything_SetMax.restype = None

        # Offset
        self._dll.Everything_SetOffset.argtypes = [c_uint]
        self._dll.Everything_SetOffset.restype = None

        # Match path
        self._dll.Everything_SetMatchPath.argtypes = [c_bool]
        self._dll.Everything_SetMatchPath.restype = None

        # Match case
        self._dll.Everything_SetMatchCase.argtypes = [c_bool]
        self._dll.Everything_SetMatchCase.restype = None

        # Match whole word
        self._dll.Everything_SetMatchWholeWord.argtypes = [c_bool]
        self._dll.Everything_SetMatchWholeWord.restype = None

        # Regex
        self._dll.Everything_SetRegex.argtypes = [c_bool]
        self._dll.Everything_SetRegex.restype = None

        # Error
        self._dll.Everything_GetLastError.argtypes = []
        self._dll.Everything_GetLastError.restype = c_uint

        # Availability
        self._dll.Everything_IsDBLoaded.argtypes = []
        self._dll.Everything_IsDBLoaded.restype = c_bool

        # Reset
        self._dll.Everything_Reset.argtypes = []
        self._dll.Everything_Reset.restype = None

        # Clean up
        self._dll.Everything_CleanUp.argtypes = []
        self._dll.Everything_CleanUp.restype = None

    def _check_availability(self) -> bool:
        """Check if Everything is running and database is loaded."""
        if not self._dll:
            return False
        try:
            return bool(self._dll.Everything_IsDBLoaded())
        except Exception as e:
            print(f"Error checking Everything availability: {e}")
            return False

    @property
    def is_available(self) -> bool:
        """Check if Everything SDK is available."""
        return self._is_available

    @property
    def is_using_fallback(self) -> bool:
        """Check if using Windows Search fallback."""
        return self._use_fallback

    def _get_cache_key(self, query: str, **kwargs) -> str:
        """Generate cache key from query and parameters."""
        params = sorted(kwargs.items())
        return f"{query}|{params}"

    def _get_cached(self, cache_key: str) -> Optional[List[EverythingResult]]:
        """Get cached results if available and not expired."""
        if not self._enable_cache:
            return None

        if cache_key in self._cache:
            cache_time = self._cache_times.get(cache_key, 0)
            if time.time() - cache_time < self._cache_ttl:
                return self._cache[cache_key]
            else:
                # Expired
                del self._cache[cache_key]
                del self._cache_times[cache_key]
        return None

    def _set_cache(self, cache_key: str, results: List[EverythingResult]):
        """Cache search results."""
        if self._enable_cache:
            self._cache[cache_key] = results
            self._cache_times[cache_key] = time.time()

    def clear_cache(self):
        """Clear all cached results."""
        self._cache.clear()
        self._cache_times.clear()

    def search(
        self,
        query: str,
        max_results: int = 1000,
        offset: int = 0,
        sort: EverythingSort = EverythingSort.NAME_ASCENDING,
        match_path: bool = True,
        match_case: bool = False,
        match_whole_word: bool = False,
        regex: bool = False,
        request_flags: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[EverythingResult]:
        """
        Search for files and folders using Everything.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            offset: Offset for pagination
            sort: Sort order for results
            match_path: Match against full path
            match_case: Case-sensitive search
            match_whole_word: Match whole words only
            regex: Enable regex search
            request_flags: Custom request flags or None for default
            progress_callback: Optional callback(current, total) for progress updates

        Returns:
            List of EverythingResult objects

        Raises:
            EverythingSDKError: If search fails
        """
        # Check cache
        cache_key = self._get_cache_key(
            query, max_results=max_results, offset=offset, sort=sort,
            match_path=match_path, match_case=match_case,
            match_whole_word=match_whole_word, regex=regex
        )
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        # Use fallback if Everything is not available
        if self._use_fallback or not self._is_available:
            return self._search_windows_fallback(query, max_results)

        with self._lock:
            if not self._is_available:
                raise EverythingSDKError(
                    "Everything is not available. Ensure Everything.exe is running."
                )

            # Reset to clear previous search
            self._dll.Everything_Reset()

            # Set search parameters
            self._dll.Everything_SetSearchW(query)
            self._dll.Everything_SetMax(max_results)
            self._dll.Everything_SetOffset(offset)
            self._dll.Everything_SetSort(sort)
            self._dll.Everything_SetMatchPath(match_path)
            self._dll.Everything_SetMatchCase(match_case)
            self._dll.Everything_SetMatchWholeWord(match_whole_word)
            self._dll.Everything_SetRegex(regex)

            # Set request flags
            if request_flags is None:
                request_flags = (
                    EverythingRequestFlags.FILE_NAME
                    | EverythingRequestFlags.PATH
                    | EverythingRequestFlags.FULL_PATH_AND_FILE_NAME
                    | EverythingRequestFlags.EXTENSION
                    | EverythingRequestFlags.SIZE
                    | EverythingRequestFlags.DATE_CREATED
                    | EverythingRequestFlags.DATE_MODIFIED
                    | EverythingRequestFlags.DATE_ACCESSED
                    | EverythingRequestFlags.ATTRIBUTES
                )
            self._dll.Everything_SetRequestFlags(request_flags)

            # Execute query
            if not self._dll.Everything_QueryW(True):
                error_code = self._dll.Everything_GetLastError()
                raise EverythingSDKError(
                    f"Query failed with error code {error_code}: {self._get_error_message(error_code)}"
                )

            # Get results
            num_results = self._dll.Everything_GetNumResults()
            results = []

            for i in range(num_results):
                if progress_callback:
                    progress_callback(i + 1, num_results)

                result = self._get_result(i)
                if result:
                    results.append(result)

            # Cache results
            self._set_cache(cache_key, results)

            return results

    def search_async(
        self,
        query: str,
        callback: Callable[[List[EverythingResult]], None],
        error_callback: Optional[Callable[[Exception], None]] = None,
        **kwargs
    ) -> threading.Thread:
        """
        Perform asynchronous search.

        Args:
            query: Search query
            callback: Callback function to receive results
            error_callback: Optional callback for errors
            **kwargs: Additional arguments passed to search()

        Returns:
            Thread object
        """
        def _search_thread():
            try:
                results = self.search(query, **kwargs)
                callback(results)
            except Exception as e:
                if error_callback:
                    error_callback(e)
                else:
                    print(f"Async search error: {e}")

        thread = threading.Thread(target=_search_thread, daemon=True)
        thread.start()
        return thread

    def _search_windows_fallback(
        self,
        query: str,
        max_results: int = 1000
    ) -> List[EverythingResult]:
        """
        Fallback to Windows Search when Everything is unavailable.

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            List of EverythingResult objects
        """
        results = []

        try:
            # Use PowerShell for Windows Search
            ps_command = f"""
            Get-ChildItem -Path C:\\ -Recurse -ErrorAction SilentlyContinue -Filter "*{query}*" |
            Select-Object -First {max_results} |
            ForEach-Object {{
                [PSCustomObject]@{{
                    Name = $_.Name
                    FullName = $_.FullName
                    Directory = $_.DirectoryName
                    Extension = $_.Extension
                    Length = if ($_.PSIsContainer) {{ 0 }} else {{ $_.Length }}
                    CreationTime = $_.CreationTime.ToFileTime()
                    LastWriteTime = $_.LastWriteTime.ToFileTime()
                    LastAccessTime = $_.LastAccessTime.ToFileTime()
                    Attributes = [int]$_.Attributes
                    IsFolder = $_.PSIsContainer
                }}
            }} | ConvertTo-Json
            """

            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                import json
                data = json.loads(result.stdout)

                # Handle single result (not in array)
                if isinstance(data, dict):
                    data = [data]

                for item in data:
                    results.append(EverythingResult(
                        filename=item.get("Name", ""),
                        path=item.get("Directory", ""),
                        full_path=item.get("FullName", ""),
                        extension=item.get("Extension", "").lstrip("."),
                        size=item.get("Length", 0),
                        date_created=item.get("CreationTime", 0),
                        date_modified=item.get("LastWriteTime", 0),
                        date_accessed=item.get("LastAccessTime", 0),
                        attributes=item.get("Attributes", 0),
                        is_folder=item.get("IsFolder", False)
                    ))

        except Exception as e:
            print(f"Windows Search fallback error: {e}")

        return results

    def _get_result(self, index: int) -> Optional[EverythingResult]:
        """Get result at index."""
        try:
            filename = self._dll.Everything_GetResultFileNameW(index) or ""
            path = self._dll.Everything_GetResultPathW(index) or ""

            # Get full path
            buffer = ctypes.create_unicode_buffer(4096)
            self._dll.Everything_GetResultFullPathNameW(index, buffer, 4096)
            full_path = buffer.value

            extension = self._dll.Everything_GetResultExtensionW(index) or ""

            # Get size
            size_value = c_ulonglong()
            if self._dll.Everything_GetResultSize(index, ctypes.byref(size_value)):
                size = size_value.value
            else:
                size = 0

            # Get dates
            date_created_value = c_ulonglong()
            date_modified_value = c_ulonglong()
            date_accessed_value = c_ulonglong()

            self._dll.Everything_GetResultDateCreated(
                index, ctypes.byref(date_created_value)
            )
            self._dll.Everything_GetResultDateModified(
                index, ctypes.byref(date_modified_value)
            )
            self._dll.Everything_GetResultDateAccessed(
                index, ctypes.byref(date_accessed_value)
            )

            attributes = self._dll.Everything_GetResultAttributes(index)

            # Check if it's a folder (FILE_ATTRIBUTE_DIRECTORY = 0x10)
            is_folder = bool(attributes & 0x10)

            return EverythingResult(
                filename=filename,
                path=path,
                full_path=full_path,
                extension=extension,
                size=size,
                date_created=date_created_value.value,
                date_modified=date_modified_value.value,
                date_accessed=date_accessed_value.value,
                attributes=attributes,
                is_folder=is_folder,
            )
        except Exception as e:
            # Skip failed results
            return None

    def _get_error_message(self, error_code: int) -> str:
        """Get human-readable error message."""
        error_messages = {
            EverythingErrorCode.OK: "No error",
            EverythingErrorCode.MEMORY: "Memory allocation failed",
            EverythingErrorCode.IPC: "IPC communication failed",
            EverythingErrorCode.REGISTERCLASSEX: "Failed to register window class",
            EverythingErrorCode.CREATEWINDOW: "Failed to create window",
            EverythingErrorCode.CREATETHREAD: "Failed to create thread",
            EverythingErrorCode.INVALIDINDEX: "Invalid index",
            EverythingErrorCode.INVALIDCALL: "Invalid call",
        }
        return error_messages.get(error_code, f"Unknown error ({error_code})")

    def get_stats(self) -> dict:
        """Get cache statistics and availability info."""
        return {
            "is_available": self._is_available,
            "is_using_fallback": self._use_fallback,
            "cache_enabled": self._enable_cache,
            "cache_size": len(self._cache),
            "cache_ttl": self._cache_ttl,
        }

    def cleanup(self):
        """Clean up Everything SDK resources."""
        if hasattr(self, "_executor"):
            self._executor.shutdown(wait=False)

        if hasattr(self, "_dll") and self._dll:
            try:
                self._dll.Everything_CleanUp()
            except Exception:
                pass

    def __del__(self):
        """Destructor to clean up resources."""
        self.cleanup()


# Singleton instance
_everything_instance: Optional[EverythingSDK] = None
_instance_lock = threading.Lock()


def get_everything_instance(
    dll_path: Optional[str] = None,
    enable_cache: bool = True,
    cache_ttl: int = 300
) -> EverythingSDK:
    """
    Get singleton instance of EverythingSDK.

    Args:
        dll_path: Optional DLL path
        enable_cache: Enable result caching
        cache_ttl: Cache TTL in seconds

    Returns:
        EverythingSDK instance
    """
    global _everything_instance

    with _instance_lock:
        if _everything_instance is None:
            _everything_instance = EverythingSDK(
                dll_path=dll_path,
                enable_cache=enable_cache,
                cache_ttl=cache_ttl
            )

    return _everything_instance
