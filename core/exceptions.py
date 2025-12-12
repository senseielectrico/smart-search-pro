"""
Custom exception hierarchy for Smart Search Pro.

This module defines all custom exceptions used throughout the application,
providing a clear hierarchy for error handling and debugging.
"""

from typing import Any


class SmartSearchError(Exception):
    """Base exception for all Smart Search Pro errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """
        Initialize the exception.

        Args:
            message: Human-readable error message
            details: Additional context about the error
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


# Configuration Errors
class ConfigurationError(SmartSearchError):
    """Raised when there's a configuration issue."""
    pass


class InvalidConfigError(ConfigurationError):
    """Raised when configuration values are invalid."""
    pass


class ConfigLoadError(ConfigurationError):
    """Raised when configuration cannot be loaded."""
    pass


# Database Errors
class DatabaseError(SmartSearchError):
    """Base exception for database-related errors."""
    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class MigrationError(DatabaseError):
    """Raised when database migration fails."""
    pass


class IntegrityError(DatabaseError):
    """Raised when database integrity constraint is violated."""
    pass


class QueryError(DatabaseError):
    """Raised when a database query fails."""
    pass


# Cache Errors
class CacheError(SmartSearchError):
    """Base exception for cache-related errors."""
    pass


class CacheFullError(CacheError):
    """Raised when cache is full and cannot evict entries."""
    pass


class CacheExpiredError(CacheError):
    """Raised when attempting to access expired cache entry."""
    pass


# Search Errors
class SearchError(SmartSearchError):
    """Base exception for search-related errors."""
    pass


class InvalidQueryError(SearchError):
    """Raised when search query is invalid."""
    pass


class SearchTimeoutError(SearchError):
    """Raised when search operation times out."""
    pass


class NoResultsError(SearchError):
    """Raised when search returns no results."""
    pass


# File System Errors
class FileSystemError(SmartSearchError):
    """Base exception for file system errors."""
    pass


class PathNotFoundError(FileSystemError):
    """Raised when a path does not exist."""
    pass


class PermissionError(FileSystemError):
    """Raised when lacking permissions to access a path."""
    pass


class InvalidPathError(FileSystemError):
    """Raised when a path is invalid or malformed."""
    pass


# Index Errors
class IndexError(SmartSearchError):
    """Base exception for indexing errors."""
    pass


class IndexCorruptedError(IndexError):
    """Raised when index is corrupted."""
    pass


class IndexNotFoundError(IndexError):
    """Raised when index does not exist."""
    pass


# Plugin Errors
class PluginError(SmartSearchError):
    """Base exception for plugin-related errors."""
    pass


class PluginLoadError(PluginError):
    """Raised when plugin cannot be loaded."""
    pass


class PluginNotFoundError(PluginError):
    """Raised when plugin is not found."""
    pass


# Network Errors
class NetworkError(SmartSearchError):
    """Base exception for network-related errors."""
    pass


class APIError(NetworkError):
    """Raised when API call fails."""
    pass


class RateLimitError(NetworkError):
    """Raised when rate limit is exceeded."""
    pass


# Validation Errors
class ValidationError(SmartSearchError):
    """Raised when input validation fails."""
    pass


class SchemaError(ValidationError):
    """Raised when data doesn't match expected schema."""
    pass


# Resource Errors
class ResourceError(SmartSearchError):
    """Base exception for resource-related errors."""
    pass


class ResourceNotFoundError(ResourceError):
    """Raised when a resource is not found."""
    pass


class ResourceExhaustedError(ResourceError):
    """Raised when a resource is exhausted."""
    pass


class ResourceLockedError(ResourceError):
    """Raised when a resource is locked."""
    pass
