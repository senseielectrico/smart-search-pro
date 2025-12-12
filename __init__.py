"""
Smart Search - Windows Search API Backend
==========================================

Módulo principal para búsqueda avanzada en Windows.
"""

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
