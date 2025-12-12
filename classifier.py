"""
Módulo de clasificación de archivos por tipo.

Proporciona funcionalidades para categorizar archivos, obtener iconos,
formatear tamaños y fechas, y agrupar resultados por categoría.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
import os
import re

# Importar utilidades compartidas
from utils import format_file_size, format_date

# Try to use centralized logger, fallback to standard logging
try:
    from core.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# Security constants
MAX_PATH_LENGTH = 32767  # Windows MAX_PATH extended
MAX_EXTENSION_LENGTH = 32  # Reasonable max extension length
DANGEROUS_PATTERNS = re.compile(r'[\x00-\x1f]|\.\.[\\/]')  # Null bytes and path traversal


def _validate_path(path: Union[str, Path]) -> Path:
    """
    Validate and sanitize file path input.

    Args:
        path: File path to validate.

    Returns:
        Validated Path object.

    Raises:
        ValueError: If path is invalid or potentially malicious.
        TypeError: If path is not a string or Path object.
    """
    if path is None:
        raise TypeError("Path cannot be None")

    if not isinstance(path, (str, Path)):
        raise TypeError(f"Path must be str or Path, not {type(path).__name__}")

    path_str = str(path)

    # Check for empty path
    if not path_str or not path_str.strip():
        raise ValueError("Path cannot be empty")

    # Check path length
    if len(path_str) > MAX_PATH_LENGTH:
        raise ValueError(f"Path exceeds maximum length of {MAX_PATH_LENGTH}")

    # Check for dangerous patterns (null bytes, path traversal)
    if DANGEROUS_PATTERNS.search(path_str):
        logger.warning(f"Potentially malicious path pattern detected")
        raise ValueError("Path contains invalid characters or patterns")

    return Path(path_str) if isinstance(path, str) else path


def _validate_extension(extension: str) -> str:
    """
    Validate file extension input.

    Args:
        extension: Extension to validate.

    Returns:
        Validated and normalized extension (lowercase, no leading dot).

    Raises:
        ValueError: If extension is invalid.
        TypeError: If extension is not a string.
    """
    if not isinstance(extension, str):
        raise TypeError(f"Extension must be str, not {type(extension).__name__}")

    ext = extension.lstrip('.').lower()

    if len(ext) > MAX_EXTENSION_LENGTH:
        raise ValueError(f"Extension exceeds maximum length of {MAX_EXTENSION_LENGTH}")

    # Only allow alphanumeric extensions
    if ext and not ext.replace('_', '').replace('-', '').isalnum():
        raise ValueError("Extension contains invalid characters")

    return ext


# Mapeo completo de extensiones a categorías
EXTENSION_MAP: Dict[str, str] = {
    # Documentos
    'pdf': 'Documentos',
    'doc': 'Documentos',
    'docx': 'Documentos',
    'xls': 'Documentos',
    'xlsx': 'Documentos',
    'ppt': 'Documentos',
    'pptx': 'Documentos',
    'txt': 'Documentos',
    'rtf': 'Documentos',
    'odt': 'Documentos',
    'ods': 'Documentos',
    'odp': 'Documentos',
    'csv': 'Documentos',
    'md': 'Documentos',
    'tex': 'Documentos',

    # Imágenes
    'jpg': 'Imágenes',
    'jpeg': 'Imágenes',
    'png': 'Imágenes',
    'gif': 'Imágenes',
    'bmp': 'Imágenes',
    'svg': 'Imágenes',
    'webp': 'Imágenes',
    'ico': 'Imágenes',
    'tiff': 'Imágenes',
    'tif': 'Imágenes',
    'psd': 'Imágenes',
    'ai': 'Imágenes',
    'raw': 'Imágenes',
    'cr2': 'Imágenes',
    'nef': 'Imágenes',

    # Videos
    'mp4': 'Videos',
    'avi': 'Videos',
    'mkv': 'Videos',
    'mov': 'Videos',
    'wmv': 'Videos',
    'flv': 'Videos',
    'webm': 'Videos',
    'mpeg': 'Videos',
    'mpg': 'Videos',
    'm4v': 'Videos',
    '3gp': 'Videos',
    'f4v': 'Videos',

    # Audio
    'mp3': 'Audio',
    'wav': 'Audio',
    'flac': 'Audio',
    'aac': 'Audio',
    'ogg': 'Audio',
    'wma': 'Audio',
    'm4a': 'Audio',
    'opus': 'Audio',
    'ape': 'Audio',
    'alac': 'Audio',
    'aiff': 'Audio',

    # Código
    'py': 'Código',
    'js': 'Código',
    'ts': 'Código',
    'tsx': 'Código',
    'jsx': 'Código',
    'java': 'Código',
    'cpp': 'Código',
    'c': 'Código',
    'h': 'Código',
    'hpp': 'Código',
    'cs': 'Código',
    'html': 'Código',
    'css': 'Código',
    'scss': 'Código',
    'sass': 'Código',
    'less': 'Código',
    'json': 'Código',
    'xml': 'Código',
    'yaml': 'Código',
    'yml': 'Código',
    'toml': 'Código',
    'ini': 'Código',
    'conf': 'Código',
    'php': 'Código',
    'rb': 'Código',
    'go': 'Código',
    'rs': 'Código',
    'swift': 'Código',
    'kt': 'Código',
    'dart': 'Código',
    'r': 'Código',
    'sql': 'Código',
    'sh': 'Código',
    'bash': 'Código',
    'zsh': 'Código',
    'vim': 'Código',
    'lua': 'Código',
    'pl': 'Código',

    # Comprimidos
    'zip': 'Comprimidos',
    'rar': 'Comprimidos',
    '7z': 'Comprimidos',
    'tar': 'Comprimidos',
    'gz': 'Comprimidos',
    'bz2': 'Comprimidos',
    'xz': 'Comprimidos',
    'tgz': 'Comprimidos',
    'tbz2': 'Comprimidos',
    'iso': 'Comprimidos',
    'dmg': 'Comprimidos',
    'pkg': 'Comprimidos',

    # Ejecutables
    'exe': 'Ejecutables',
    'msi': 'Ejecutables',
    'bat': 'Ejecutables',
    'cmd': 'Ejecutables',
    'ps1': 'Ejecutables',
    'app': 'Ejecutables',
    'deb': 'Ejecutables',
    'rpm': 'Ejecutables',
    'apk': 'Ejecutables',
    'jar': 'Ejecutables',
    'dll': 'Ejecutables',
    'so': 'Ejecutables',
    'dylib': 'Ejecutables',
}


# Mapeo de categorías a iconos de sistema (usando nombres estándar de Qt)
CATEGORY_ICONS: Dict[str, str] = {
    'Documentos': 'SP_FileIcon',
    'Imágenes': 'SP_FileIcon',
    'Videos': 'SP_FileIcon',
    'Audio': 'SP_FileIcon',
    'Código': 'SP_FileIcon',
    'Comprimidos': 'SP_FileIcon',
    'Ejecutables': 'SP_FileIcon',
    'Otros': 'SP_FileIcon',
}


@dataclass
class ResultItem:
    """Representa un archivo resultado de búsqueda."""

    name: str
    path: str
    size: int
    date: float
    type: str
    extension: str

    @property
    def formatted_size(self) -> str:
        """Retorna el tamaño formateado."""
        return format_file_size(self.size)

    @property
    def formatted_date(self) -> str:
        """Retorna la fecha formateada."""
        return format_date(self.date)

    def __repr__(self) -> str:
        return (
            f"ResultItem(name={self.name!r}, path={self.path!r}, "
            f"size={self.formatted_size}, type={self.type})"
        )


def classify_file(path: Union[str, Path]) -> str:
    """
    Clasifica un archivo según su extensión.

    Args:
        path: Ruta del archivo (string o Path).

    Returns:
        Categoría del archivo ('Documentos', 'Imágenes', etc.).

    Raises:
        ValueError: If path is invalid.
        TypeError: If path is not a string or Path object.

    Examples:
        >>> classify_file("documento.pdf")
        'Documentos'
        >>> classify_file("imagen.png")
        'Imágenes'
        >>> classify_file("script.py")
        'Código'
        >>> classify_file("archivo.xyz")
        'Otros'
    """
    try:
        path_obj = _validate_path(path)
        extension = path_obj.suffix.lstrip('.').lower()
        return EXTENSION_MAP.get(extension, 'Otros')
    except (ValueError, TypeError) as e:
        logger.warning(f"classify_file validation error: {e}")
        raise


def get_icon_for_type(extension: str) -> str:
    """
    Obtiene el nombre del icono de Qt para una extensión.

    Args:
        extension: Extensión del archivo (con o sin punto).

    Returns:
        Nombre del icono estándar de Qt (SP_FileIcon, etc.).

    Raises:
        ValueError: If extension is invalid.
        TypeError: If extension is not a string.

    Examples:
        >>> get_icon_for_type('.pdf')
        'SP_FileIcon'
        >>> get_icon_for_type('png')
        'SP_FileIcon'
    """
    try:
        ext = _validate_extension(extension)
        category = EXTENSION_MAP.get(ext, 'Otros')
        return CATEGORY_ICONS.get(category, 'SP_FileIcon')
    except (ValueError, TypeError) as e:
        logger.warning(f"get_icon_for_type validation error: {e}")
        return 'SP_FileIcon'  # Safe fallback






def create_result_item(path: Union[str, Path]) -> Optional[ResultItem]:
    """
    Crea un ResultItem desde una ruta de archivo.

    Args:
        path: Ruta del archivo.

    Returns:
        ResultItem o None si el archivo no existe o hay error.

    Examples:
        >>> item = create_result_item("C:/example.pdf")
        >>> item.type
        'Documentos'
    """
    try:
        path_obj = _validate_path(path)

        if not path_obj.exists():
            return None

        stat = path_obj.stat()
        extension = path_obj.suffix.lstrip('.').lower()
        file_type = classify_file(path_obj)

        return ResultItem(
            name=path_obj.name,
            path=str(path_obj.absolute()),
            size=stat.st_size,
            date=stat.st_mtime,
            type=file_type,
            extension=extension
        )
    except (OSError, PermissionError, ValueError, TypeError) as e:
        logger.debug(f"create_result_item failed for path: {e}")
        return None


def group_results_by_type(results: List[ResultItem]) -> Dict[str, List[ResultItem]]:
    """
    Agrupa una lista de ResultItems por categoría.

    Args:
        results: Lista de ResultItem.

    Returns:
        Diccionario con categorías como keys y listas de ResultItem como values.
        Las categorías están ordenadas alfabéticamente.

    Examples:
        >>> results = [
        ...     ResultItem("doc.pdf", "/path/doc.pdf", 1024, 0.0, "Documentos", "pdf"),
        ...     ResultItem("img.png", "/path/img.png", 2048, 0.0, "Imágenes", "png"),
        ...     ResultItem("doc2.docx", "/path/doc2.docx", 512, 0.0, "Documentos", "docx")
        ... ]
        >>> grouped = group_results_by_type(results)
        >>> len(grouped['Documentos'])
        2
        >>> len(grouped['Imágenes'])
        1
    """
    grouped: Dict[str, List[ResultItem]] = {}

    for item in results:
        category = item.type
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(item)

    # Ordenar las listas dentro de cada categoría por nombre
    for category in grouped:
        grouped[category].sort(key=lambda x: x.name.lower())

    # Retornar diccionario ordenado por categoría
    return dict(sorted(grouped.items()))


def get_all_categories() -> List[str]:
    """
    Retorna todas las categorías disponibles.

    Returns:
        Lista de categorías ordenadas alfabéticamente.

    Examples:
        >>> categories = get_all_categories()
        >>> 'Documentos' in categories
        True
        >>> 'Código' in categories
        True
    """
    categories = set(EXTENSION_MAP.values())
    categories.add('Otros')
    return sorted(categories)


def get_extensions_for_category(category: str) -> List[str]:
    """
    Retorna todas las extensiones para una categoría dada.

    Args:
        category: Nombre de la categoría.

    Returns:
        Lista de extensiones (sin punto) ordenadas alfabéticamente.

    Raises:
        TypeError: If category is not a string.

    Examples:
        >>> exts = get_extensions_for_category('Documentos')
        >>> 'pdf' in exts
        True
        >>> 'docx' in exts
        True
    """
    if not isinstance(category, str):
        raise TypeError(f"Category must be str, not {type(category).__name__}")

    extensions = [ext for ext, cat in EXTENSION_MAP.items() if cat == category]
    return sorted(extensions)


def get_category_stats(results: List[ResultItem]) -> Dict[str, Dict[str, int | float]]:
    """
    Genera estadísticas por categoría de una lista de resultados.

    Args:
        results: Lista de ResultItem.

    Returns:
        Diccionario con estadísticas por categoría:
        - count: número de archivos
        - total_size: tamaño total en bytes
        - avg_size: tamaño promedio en bytes

    Examples:
        >>> results = [
        ...     ResultItem("doc.pdf", "/path/doc.pdf", 1024, 0.0, "Documentos", "pdf"),
        ...     ResultItem("doc2.pdf", "/path/doc2.pdf", 2048, 0.0, "Documentos", "pdf")
        ... ]
        >>> stats = get_category_stats(results)
        >>> stats['Documentos']['count']
        2
        >>> stats['Documentos']['total_size']
        3072
    """
    stats: Dict[str, Dict[str, int | float]] = {}

    for item in results:
        category = item.type
        if category not in stats:
            stats[category] = {
                'count': 0,
                'total_size': 0,
                'avg_size': 0.0
            }

        stats[category]['count'] += 1
        stats[category]['total_size'] += item.size

    # Calcular promedios
    for category in stats:
        count = stats[category]['count']
        if count > 0:
            stats[category]['avg_size'] = stats[category]['total_size'] / count

    return stats


if __name__ == '__main__':
    # Pruebas básicas del módulo
    import doctest
    doctest.testmod()

    # Ejemplos de uso
    print("=== Clasificador de Archivos ===\n")

    # Ejemplo 1: Clasificar archivos
    test_files = [
        "documento.pdf",
        "imagen.png",
        "video.mp4",
        "audio.mp3",
        "script.py",
        "archivo.zip",
        "programa.exe",
        "desconocido.xyz"
    ]

    print("1. Clasificación de archivos:")
    for file in test_files:
        print(f"   {file:20} -> {classify_file(file)}")

    # Ejemplo 2: Formateo de tamaños
    print("\n2. Formateo de tamaños:")
    sizes = [0, 512, 1024, 1536, 1048576, 1536000000]
    for size in sizes:
        print(f"   {size:>12} bytes -> {format_file_size(size)}")

    # Ejemplo 3: Categorías disponibles
    print("\n3. Categorías disponibles:")
    for category in get_all_categories():
        exts = get_extensions_for_category(category)
        print(f"   {category}: {len(exts)} extensiones")

    # Ejemplo 4: Estadísticas
    print("\n4. Ejemplo de estadísticas:")
    example_results = [
        ResultItem("doc1.pdf", "/path/doc1.pdf", 1024000, 0.0, "Documentos", "pdf"),
        ResultItem("doc2.docx", "/path/doc2.docx", 2048000, 0.0, "Documentos", "docx"),
        ResultItem("img1.png", "/path/img1.png", 512000, 0.0, "Imágenes", "png"),
        ResultItem("script.py", "/path/script.py", 4096, 0.0, "Código", "py"),
    ]

    stats = get_category_stats(example_results)
    for category, data in stats.items():
        print(f"   {category}:")
        print(f"      Archivos: {data['count']}")
        print(f"      Total: {format_file_size(data['total_size'])}")
        print(f"      Promedio: {format_file_size(int(data['avg_size']))}")
