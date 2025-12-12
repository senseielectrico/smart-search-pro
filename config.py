"""
Smart Search - Configuración
=============================

Configuración centralizada para el backend.
"""

import os
from pathlib import Path
from typing import List, Dict


class SearchConfig:
    """Configuración global de búsqueda"""

    # Directorios de búsqueda predeterminados
    DEFAULT_SEARCH_PATHS: List[str] = [
        os.path.join(os.environ.get('USERPROFILE', 'C:\\Users'), 'Documents'),
        os.path.join(os.environ.get('USERPROFILE', 'C:\\Users'), 'Desktop'),
        os.path.join(os.environ.get('USERPROFILE', 'C:\\Users'), 'Downloads'),
        os.path.join(os.environ.get('USERPROFILE', 'C:\\Users'), 'Pictures'),
    ]

    # Límites de resultados
    MAX_RESULTS_DEFAULT: int = 1000
    MAX_RESULTS_HARD_LIMIT: int = 10000

    # Threading
    MAX_CONCURRENT_SEARCHES: int = 5
    SEARCH_TIMEOUT_SECONDS: int = 300  # 5 minutos

    # Windows Search API
    USE_WINDOWS_SEARCH_BY_DEFAULT: bool = True
    WINDOWS_SEARCH_CONNECTION_STRING: str = (
        "Provider=Search.CollatorDSO;"
        "Extended Properties='Application=Windows';"
    )

    # Fallback Engine
    FALLBACK_FOLLOW_SYMLINKS: bool = False
    FALLBACK_IGNORE_HIDDEN: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Cache
    ENABLE_RESULTS_CACHE: bool = True
    CACHE_TTL_SECONDS: int = 300  # 5 minutos
    MAX_CACHED_SEARCHES: int = 100

    # Operaciones de archivos
    FILE_OPERATION_BUFFER_SIZE: int = 1024 * 1024  # 1 MB
    USE_RECYCLE_BIN: bool = True

    # Directorios excluidos por defecto
    EXCLUDED_DIRECTORIES: List[str] = [
        r'C:\Windows',
        r'C:\Program Files',
        r'C:\Program Files (x86)',
        r'C:\ProgramData',
        r'C:\$Recycle.Bin',
        r'C:\System Volume Information',
    ]

    # Extensiones por categoría (para clasificación personalizada)
    CUSTOM_EXTENSIONS: Dict[str, List[str]] = {
        # Agregar extensiones personalizadas aquí
        # 'DOCUMENT': ['.custom_doc'],
    }

    # Performance
    ENABLE_MULTITHREADING: bool = True
    THREAD_POOL_SIZE: int = 4

    @classmethod
    def get_user_search_paths(cls) -> List[str]:
        """
        Obtiene los paths de búsqueda del usuario

        Returns:
            Lista de paths válidos
        """
        paths = []
        for path in cls.DEFAULT_SEARCH_PATHS:
            if os.path.exists(path):
                paths.append(path)
        return paths

    @classmethod
    def is_excluded_directory(cls, path: str) -> bool:
        """
        Verifica si un directorio está excluido

        Args:
            path: Path a verificar

        Returns:
            True si está excluido
        """
        path_lower = path.lower()
        for excluded in cls.EXCLUDED_DIRECTORIES:
            if path_lower.startswith(excluded.lower()):
                return True
        return False

    @classmethod
    def get_safe_search_paths(cls) -> List[str]:
        """
        Obtiene paths seguros (excluye directorios del sistema)

        Returns:
            Lista de paths seguros
        """
        paths = cls.get_user_search_paths()
        return [p for p in paths if not cls.is_excluded_directory(p)]


class UIConfig:
    """Configuración de UI (para futura integración)"""

    # Tema
    THEME: str = "dark"

    # Colores
    PRIMARY_COLOR: str = "#007acc"
    SECONDARY_COLOR: str = "#2d2d30"
    BACKGROUND_COLOR: str = "#1e1e1e"
    TEXT_COLOR: str = "#cccccc"

    # Paginación
    RESULTS_PER_PAGE: int = 50
    ENABLE_INFINITE_SCROLL: bool = True

    # Vista
    DEFAULT_VIEW: str = "list"  # list, grid, details
    SHOW_FILE_ICONS: bool = True
    SHOW_PREVIEW: bool = True

    # Atajos de teclado
    KEYBOARD_SHORTCUTS: Dict[str, str] = {
        'search': 'Ctrl+F',
        'open': 'Enter',
        'open_location': 'Ctrl+Enter',
        'copy': 'Ctrl+C',
        'delete': 'Delete',
    }


class PerformanceConfig:
    """Configuración de rendimiento"""

    # Indexación
    ENABLE_LOCAL_INDEX: bool = False
    INDEX_UPDATE_INTERVAL_MINUTES: int = 30

    # Cache
    ENABLE_THUMBNAIL_CACHE: bool = True
    THUMBNAIL_CACHE_SIZE_MB: int = 100

    # Búsqueda
    SEARCH_DEBOUNCE_MS: int = 300
    MIN_SEARCH_LENGTH: int = 2

    # Memoria
    MAX_MEMORY_USAGE_MB: int = 500
    ENABLE_MEMORY_CLEANUP: bool = True


# Singleton de configuración global
config = SearchConfig()
ui_config = UIConfig()
perf_config = PerformanceConfig()
