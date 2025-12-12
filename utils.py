"""
Utilidades compartidas para Smart Search
========================================

Módulo centralizado con funciones comunes utilizadas en múltiples módulos
de la aplicación Smart Search.

Funciones:
- format_file_size: Formatea bytes a formato legible (KB, MB, GB, etc.)
- format_date: Formatea timestamp Unix a string legible

Autor: Smart Search Team
Fecha: 2025-12-11
"""

from datetime import datetime
from typing import Union


def format_file_size(size_bytes: int) -> str:
    """
    Formatea un tamaño en bytes a una cadena legible.

    Args:
        size_bytes: Tamaño en bytes.

    Returns:
        String formateado (ej: "1.5 MB", "256 KB", "0 B").

    Examples:
        >>> format_file_size(0)
        '0 B'
        >>> format_file_size(1024)
        '1.00 KB'
        >>> format_file_size(1536)
        '1.50 KB'
        >>> format_file_size(1048576)
        '1.00 MB'
        >>> format_file_size(1536000000)
        '1.43 GB'
    """
    if size_bytes == 0:
        return "0 B"

    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0
    size = float(size_bytes)

    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    # Formatear con precisión apropiada
    if unit_index == 0:  # Bytes
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"


def format_date(timestamp: Union[float, int]) -> str:
    """
    Formatea un timestamp Unix a una cadena legible.

    Args:
        timestamp: Timestamp Unix (segundos desde epoch).

    Returns:
        String formateado (ej: "2025-12-11 14:30:45") o "Fecha inválida" si hay error.

    Examples:
        >>> format_date(1702305045.0)
        '2023-12-11 14:30:45'
        >>> format_date(0)
        '1970-01-01 00:00:00'
    """
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError, OverflowError):
        return "Fecha inválida"


if __name__ == '__main__':
    # Pruebas básicas
    print("=== Utilidades Smart Search ===\n")

    # Ejemplo 1: Formateo de tamaños
    print("1. Formateo de tamaños:")
    sizes = [0, 512, 1024, 1536, 1048576, 1536000000, 1099511627776]
    for size in sizes:
        print(f"   {size:>15} bytes -> {format_file_size(size)}")

    # Ejemplo 2: Formateo de fechas
    print("\n2. Formateo de fechas:")
    timestamps = [0, 1702305045.0, 1733934000.0]
    for ts in timestamps:
        print(f"   {ts:>15} -> {format_date(ts)}")

    # Ejemplo 3: Casos edge
    print("\n3. Casos especiales:")
    print(f"   Fecha inválida (999999999999999): {format_date(999999999999999)}")
    print(f"   Tamaño 0 bytes: {format_file_size(0)}")
    print(f"   1 PB: {format_file_size(1125899906842624)}")
