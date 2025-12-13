"""
Smart Search - Windows Search API Backend
==========================================

Modulo principal para busqueda avanzada en Windows.
"""

try:
    from .backend import (
        # Modelos
        SearchQuery,
        SearchResult,
        FileCategory,
        # Servicios
        SearchService,
        WindowsSearchEngine,
        FallbackSearchEngine,
        FileOperations,
        # Constantes
        FILE_CATEGORY_MAP,
    )
except ImportError:
    # Fallback for direct execution or pytest
    from backend import (
        SearchQuery,
        SearchResult,
        FileCategory,
        SearchService,
        WindowsSearchEngine,
        FallbackSearchEngine,
        FileOperations,
        FILE_CATEGORY_MAP,
    )

__version__ = "1.0.0"
__author__ = "Smart Search Team"

__all__ = [
    'SearchQuery',
    'SearchResult',
    'FileCategory',
    'SearchService',
    'WindowsSearchEngine',
    'FallbackSearchEngine',
    'FileOperations',
    'FILE_CATEGORY_MAP',
]
