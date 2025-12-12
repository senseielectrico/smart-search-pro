"""
Sistema unificado de categorización de archivos.
Usado por backend, UI y classifier.
"""
from enum import Enum
from typing import Set, Dict


class FileCategory(Enum):
    """Categorías de archivos - ÚNICA FUENTE DE VERDAD"""
    DOCUMENTOS = "Documentos"
    IMAGENES = "Imágenes"
    VIDEOS = "Videos"
    AUDIO = "Audio"
    CODIGO = "Código"
    COMPRIMIDOS = "Comprimidos"
    EJECUTABLES = "Ejecutables"
    DATOS = "Datos"
    OTROS = "Otros"


# Mapeo extensiones → categoría
CATEGORY_EXTENSIONS: Dict[FileCategory, Set[str]] = {
    FileCategory.DOCUMENTOS: {
        '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx',
        '.ppt', '.pptx', '.csv', '.md', '.epub', '.tex', '.ods', '.odp'
    },
    FileCategory.IMAGENES: {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico', '.webp',
        '.tiff', '.tif', '.raw', '.psd', '.ai', '.cr2', '.nef'
    },
    FileCategory.VIDEOS: {
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v',
        '.mpg', '.mpeg', '.3gp', '.f4v'
    },
    FileCategory.AUDIO: {
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus',
        '.ape', '.alac', '.aiff'
    },
    FileCategory.CODIGO: {
        '.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb',
        '.go', '.rs', '.swift', '.kt', '.ts', '.jsx', '.tsx', '.vue',
        '.html', '.css', '.scss', '.sass', '.less', '.sql', '.sh', '.bat',
        '.ps1', '.r', '.lua', '.pl', '.dart', '.json', '.xml', '.yaml',
        '.yml', '.toml', '.ini', '.conf', '.hpp', '.vim', '.zsh', '.bash'
    },
    FileCategory.COMPRIMIDOS: {
        '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso', '.dmg',
        '.tgz', '.tbz2', '.pkg'
    },
    FileCategory.EJECUTABLES: {
        '.exe', '.msi', '.app', '.deb', '.rpm', '.apk', '.jar', '.dll',
        '.so', '.dylib', '.cmd'
    },
    FileCategory.DATOS: {
        '.db', '.sqlite', '.mdb', '.accdb', '.cfg'
    }
}


def classify_by_extension(extension: str) -> FileCategory:
    """
    Clasifica archivo por extensión.

    Args:
        extension: Extensión con o sin punto (ej: '.py' o 'py')

    Returns:
        FileCategory correspondiente

    Examples:
        >>> classify_by_extension('.py')
        <FileCategory.CODIGO: 'Código'>
        >>> classify_by_extension('pdf')
        <FileCategory.DOCUMENTOS: 'Documentos'>
        >>> classify_by_extension('')
        <FileCategory.OTROS: 'Otros'>
    """
    if not extension:
        return FileCategory.OTROS

    # Normalizar: minúsculas y con punto
    ext = extension.lower()
    if not ext.startswith('.'):
        ext = '.' + ext

    # Buscar en mapeo
    for category, extensions in CATEGORY_EXTENSIONS.items():
        if ext in extensions:
            return category

    return FileCategory.OTROS


def get_extensions_for_category(category: FileCategory) -> Set[str]:
    """
    Obtiene todas las extensiones para una categoría.

    Args:
        category: FileCategory

    Returns:
        Set de extensiones (con punto, ej: {'.py', '.js'})
    """
    return CATEGORY_EXTENSIONS.get(category, set())


def get_all_categories() -> list[FileCategory]:
    """Retorna todas las categorías disponibles."""
    return list(FileCategory)


if __name__ == '__main__':
    # Test básico
    import doctest
    doctest.testmod()

    print("=== Sistema de Categorización Unificado ===\n")

    for category in FileCategory:
        exts = get_extensions_for_category(category)
        print(f"{category.value:15} {len(exts):3} extensiones")

    # Test de clasificación
    test_files = [
        "documento.pdf", "imagen.png", "video.mp4", "audio.mp3",
        "script.py", "archivo.zip", "programa.exe", "datos.db", "unknown.xyz"
    ]

    print("\nEjemplos de clasificación:")
    for file in test_files:
        ext = '.' + file.split('.')[-1]
        cat = classify_by_extension(ext)
        print(f"  {file:20} -> {cat.value}")
