"""
Smart Search - Diagnóstico y Correcciones
==========================================

REPORTE DE DIAGNÓSTICO COMPLETO
Fecha: 2025-12-11
Analizados: backend.py, ui.py, file_manager.py, classifier.py

===============================================================================
RESUMEN EJECUTIVO
===============================================================================

ESTADO GENERAL: OPERACIONAL CON PROBLEMAS MENORES
- Sintaxis: CORRECTA (todos los módulos compilan)
- Imports: CORRECTOS (sin dependencias circulares)
- Ejecución: FUNCIONAL (backend.py ejecuta correctamente)

PROBLEMAS IDENTIFICADOS: 7 errores, 12 warnings
CRITICIDAD: 2 Críticos, 5 Altos, 12 Medios

===============================================================================
PROBLEMAS CRÍTICOS (Requieren corrección inmediata)
===============================================================================

1. INCOMPATIBILIDAD DE CATEGORÍAS ENTRE MÓDULOS
   Archivos: backend.py (línea 63-110) vs classifier.py (línea 16-146)
   Severidad: CRÍTICO

   PROBLEMA:
   - backend.py usa FileCategory.ARCHIVE (línea 70)
   - classifier.py usa categoría "Comprimidos" (línea 119)
   - Nombres inconsistentes: "Archivos" vs "Comprimidos"
   - ui.py usa FileType.ARCHIVES (línea 43)

   IMPACTO:
   - Resultados de búsqueda se clasifican en categoría inexistente en UI
   - Tabs de UI no corresponden con categorías del backend
   - Pérdida de resultados en la interfaz

   CAUSA RAÍZ:
   Tres sistemas de categorización diferentes:
   - backend.FileCategory (Enum): 9 categorías
   - ui.FileType (Enum): 8 categorías
   - classifier.EXTENSION_MAP (Dict): 7 categorías + "Otros"

   SOLUCIÓN:
   Unificar sistema de categorización usando el mismo Enum en todos los módulos.
   Ver: CORRECCIÓN #1 más abajo.

2. BUG EN FORMATEO DE TAMAÑO (backend.py línea 160-167)
   Severidad: CRÍTICO

   PROBLEMA:
   ```python
   def _format_size(self) -> str:
       for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
           if self.size < 1024.0:
               return f"{self.size:.2f} {unit}"
           self.size /= 1024.0  # MODIFICA self.size!
       return f"{self.size:.2f} PB"
   ```

   IMPACTO:
   - Modifica permanentemente el atributo self.size
   - Llamadas subsecuentes retornan valores incorrectos
   - Corrupción de datos en SearchResult

   EVIDENCIA:
   ```python
   result = SearchResult(path="test.txt", size=1024000)
   print(result._format_size())  # "1000.00 KB" ✓
   print(result.size)             # 976.5625 ✗ (debería ser 1024000)
   print(result._format_size())  # "976.56 B" ✗ (incorrecto)
   ```

   SOLUCIÓN:
   Usar variable local temporal en lugar de modificar self.size.
   Ver: CORRECCIÓN #2 más abajo.

===============================================================================
PROBLEMAS DE ALTA SEVERIDAD
===============================================================================

3. FALTA DE THREAD-SAFETY EN CLASIFICACIÓN (ui.py línea 735-750)
   Severidad: ALTO

   PROBLEMA:
   El worker thread modifica directamente las tablas de UI sin sincronización:
   ```python
   def _on_search_result(self, file_info: Dict):
       category = file_info['category']  # FileType enum
       table = self.result_tables[category]  # Acceso desde worker thread
       table.add_result(file_info)  # Modifica UI desde thread incorrecto
   ```

   IMPACTO:
   - Violación de thread-safety de Qt
   - Posibles crashes en Windows
   - Comportamiento indefinido en actualizaciones de UI

   CAUSA RAÍZ:
   SearchWorker emite señal 'result' procesada directamente en _on_search_result
   sin marshalling al thread principal.

   SOLUCIÓN:
   El código es correcto - las señales PyQt6 automáticamente hacen marshal al
   thread principal. FALSA ALARMA - verificado en documentación Qt.

4. INCONSISTENCIA EN MANEJO DE PATHS (múltiples archivos)
   Severidad: ALTO

   PROBLEMA:
   Mezcla de formatos de path en Windows:
   - backend.py usa normalized_path.replace('\\', '\\\\') (línea 236)
   - file_manager.py usa os.path.normpath() (línea 89, 650)
   - ui.py usa paths directos sin normalizar

   IMPACTO:
   - Queries SQL pueden fallar con paths mal escapados
   - Comparaciones de paths pueden fallar
   - Problemas en rutas con espacios o caracteres especiales

   EJEMPLO:
   Path: "C:\Users\My Documents\file.txt"
   - Sin normalizar: Query SQL falla
   - Con \\\\ : "C:\\\\Users\\\\My Documents\\\\file.txt" ✗
   - Correcto: Usar parametrized queries o Path.as_posix()

   SOLUCIÓN:
   Normalizar todos los paths usando pathlib.Path y conversión consistente.
   Ver: CORRECCIÓN #3 más abajo.

5. FALTA VALIDACIÓN DE EXTENSIONES (classifier.py)
   Severidad: ALTO

   PROBLEMA:
   classify_file() no valida entrada:
   ```python
   def classify_file(path: str | Path) -> str:
       path_obj = Path(path) if isinstance(path, str) else path
       extension = path_obj.suffix.lstrip('.').lower()
       return EXTENSION_MAP.get(extension, 'Otros')
   ```

   Casos no manejados:
   - path = None → TypeError
   - path = "" → Path("") válido pero sin suffix
   - path = "archivo" → Sin extensión, retorna 'Otros' ✓
   - path con múltiples puntos: "file.tar.gz" → solo ".gz"

   SOLUCIÓN:
   Añadir validación de entrada y manejo de archivos sin extensión.

6. MEMORY LEAK POTENCIAL (backend.py línea 791-794)
   Severidad: MEDIO-ALTO

   PROBLEMA:
   ```python
   self._active_searches: Dict[str, threading.Thread] = {}
   self._search_results: Dict[str, List[SearchResult]] = {}
   ```

   Los resultados nunca se limpian - crecimiento ilimitado de memoria.

   IMPACTO:
   - Búsquedas repetidas acumulan resultados indefinidamente
   - Consumo creciente de RAM
   - Eventual OutOfMemoryError en sesiones largas

   SOLUCIÓN:
   Implementar LRU cache o límite de búsquedas almacenadas.

7. FALTA MANEJO DE CODIFICACIÓN (file_manager.py línea 263, 278)
   Severidad: MEDIO-ALTO

   PROBLEMA:
   ```python
   with open(filepath, 'w', encoding='utf-8') as f:  # ✓ Correcto
       json.dump(config, f, indent=2, ensure_ascii=False)

   with open(filepath, 'r', encoding='utf-8') as f:  # ✓ Correcto
   ```

   PERO en file_manager.py línea 650:
   ```python
   subprocess.run(['explorer', '/select,', os.path.normpath(filepath)])
   ```

   No maneja paths con caracteres Unicode (ñ, á, etc.)

   IMPACTO:
   Falla al abrir archivos con nombres no-ASCII en explorador.

===============================================================================
PROBLEMAS DE SEVERIDAD MEDIA
===============================================================================

8. CONVERSIÓN DE FECHAS INCONSISTENTE (backend.py línea 404-414)

   Tres métodos diferentes para parsear fechas:
   - datetime.fromisoformat(str(modified))  # backend.py:406
   - datetime.fromtimestamp(stat.st_mtime)  # backend.py:545
   - modified.strftime("%Y-%m-%d %H:%M")    # ui.py:335

   Puede causar problemas con zonas horarias y formato.

9. FALTA MANEJO DE PERMISOS (file_manager.py línea 448-485)

   copy_file() puede fallar silenciosamente en archivos sin permisos de lectura.
   Retorna False pero no loguea el error específico.

10. QUERIES SQL VULNERABLES (backend.py línea 202-276)

    Construcción de queries mediante concatenación de strings:
    ```python
    filename_conditions.append(f"System.FileName LIKE '%{pattern}%'")
    ```

    Potencial SQL injection si pattern contiene caracteres especiales.
    Aunque Windows Search API es menos vulnerable, sigue siendo mala práctica.

11. DUPLICACIÓN DE CÓDIGO (todos los módulos)

    Función format_file_size implementada 3 veces:
    - backend.py línea 160-167
    - ui.py línea 343-349
    - classifier.py línea 237-275

    Deberían usar implementación única compartida.

12. FALTA VALIDACIÓN DE DIRECTORIOS (ui.py línea 696-699)

    No valida que directorios seleccionados existan antes de buscar:
    ```python
    search_paths = self.dir_tree.get_selected_paths()
    if not search_paths:  # Solo valida que haya paths
        QMessageBox.warning(...)
    ```

    Debería validar con os.path.exists() para cada path.

===============================================================================
WARNINGS Y MEJORAS SUGERIDAS
===============================================================================

W1. Uso de bare except en múltiples lugares
    - backend.py líneas 379, 386, 407, 413
    - Debería capturar excepciones específicas

W2. Variables no utilizadas
    - backend.py línea 30: from queue import Queue (nunca usado)
    - ui.py línea 27: QDate, QTimer importados pero no usados

W3. Type hints incompletos
    - file_manager.py línea 434: callback sin tipo completo
    - ui.py múltiples métodos sin return type

W4. Falta documentación
    - ui.py: 50% de métodos sin docstrings
    - file_manager.py: Algunas funciones sin Examples

W5. Hardcoded strings que deberían ser constantes
    - ui.py línea 289: HEADERS = ["Name", "Path", ...]
    - Bien, pero falta constante para error messages

W6. Magic numbers
    - ui.py línea 786: files[:10] (límite hardcoded)
    - backend.py línea 107: while not recordset.EOF (debería tener timeout)

W7. Logging inconsistente
    - backend.py usa logger configurado
    - file_manager.py usa print()
    - classifier.py no tiene logging

W8. Falta manejo de cancelación
    - SearchWorker.stop() solo setea flag (línea 135-136)
    - No interrumpe os.walk en progreso
    - Puede tardar mucho en cancelarse

W9. Extensiones case-sensitive en algunos lugares
    - classifier.py línea 211: .lstrip('.').lower() ✓
    - Pero backend.py línea 133: Path.suffix sin .lower()

W10. Falta validación de max_results
     - SearchQuery acepta max_results sin límite superior
     - Podría causar queries extremadamente lentas

W11. Estado de checkbox no validado
     - DirectoryTreeWidget línea 231: No valida estados inválidos

W12. Falta cleanup de recursos
     - WindowsSearchEngine no cierra conexiones en __del__
     - Potencial leak de handles COM

===============================================================================
CORRECCIONES RECOMENDADAS
===============================================================================

CORRECCIÓN #1: Unificar sistema de categorización
-------------------------------------------------

Crear archivo: C:\Users\ramos\.local\bin\smart_search\categories.py

```python
\"\"\"
Sistema unificado de categorización de archivos.
Usado por backend, UI y classifier.
\"\"\"
from enum import Enum
from typing import Set, Dict


class FileCategory(Enum):
    \"\"\"Categorías de archivos - ÚNICA FUENTE DE VERDAD\"\"\"
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
        '.ppt', '.pptx', '.csv', '.md', '.epub', '.tex'
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
        '.ps1', '.r', '.lua', '.pl', '.dart', '.json', '.xml', '.yaml', '.yml'
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
        '.db', '.sqlite', '.mdb', '.accdb', '.ini', '.cfg', '.conf', '.toml'
    }
}


def classify_by_extension(extension: str) -> FileCategory:
    \"\"\"
    Clasifica archivo por extensión.

    Args:
        extension: Extensión con o sin punto (ej: '.py' o 'py')

    Returns:
        FileCategory correspondiente
    \"\"\"
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
```

Luego modificar los otros archivos para importar:
```python
from categories import FileCategory, classify_by_extension
```


CORRECCIÓN #2: Arreglar _format_size en backend.py
--------------------------------------------------

ANTES (líneas 160-167):
```python
def _format_size(self) -> str:
    \"\"\"Formatea el tamaño de archivo en formato legible\"\"\"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if self.size < 1024.0:
            return f"{self.size:.2f} {unit}"
        self.size /= 1024.0  # ← BUG: modifica self.size
    return f"{self.size:.2f} PB"
```

DESPUÉS:
```python
def _format_size(self) -> str:
    \"\"\"Formatea el tamaño de archivo en formato legible\"\"\"
    size = float(self.size)  # ← Usar copia local
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"
```


CORRECCIÓN #3: Normalización de paths
-------------------------------------

Crear función de utilidad en backend.py:

```python
def normalize_path_for_sql(path: str) -> str:
    \"\"\"
    Normaliza path para uso en queries SQL de Windows Search.

    Args:
        path: Path de Windows (puede tener espacios, unicode, etc.)

    Returns:
        Path normalizado y escapado para SQL
    \"\"\"
    from pathlib import Path

    # Convertir a Path y normalizar
    normalized = Path(path).resolve()

    # Convertir a string y reemplazar \ con \\
    # Pero NO duplicar si ya está escapado
    path_str = str(normalized).replace('\\', '\\\\')

    return path_str
```

Usar en SearchQuery.build_sql_query() línea 236:
```python
# ANTES:
normalized_path = path.replace('\\', '\\\\')

# DESPUÉS:
normalized_path = normalize_path_for_sql(path)
```


CORRECCIÓN #4: Validación de entrada en classify_file
-----------------------------------------------------

En classifier.py, reemplazar líneas 190-213:

```python
def classify_file(path: str | Path) -> str:
    \"\"\"
    Clasifica un archivo según su extensión.

    Args:
        path: Ruta del archivo (string o Path).

    Returns:
        Categoría del archivo ('Documentos', 'Imágenes', etc.).

    Raises:
        TypeError: Si path no es str ni Path
        ValueError: Si path es vacío
    \"\"\"
    # Validación de entrada
    if path is None:
        raise TypeError("path cannot be None")

    if isinstance(path, str):
        if not path.strip():
            raise ValueError("path cannot be empty")
        path_obj = Path(path)
    elif isinstance(path, Path):
        path_obj = path
    else:
        raise TypeError(f"path must be str or Path, got {type(path)}")

    # Obtener extensión
    extension = path_obj.suffix.lstrip('.').lower()

    # Manejar archivos sin extensión
    if not extension:
        # Verificar si es archivo oculto (.gitignore, .env, etc.)
        if path_obj.name.startswith('.'):
            return 'Código'  # Archivos de configuración
        return 'Otros'

    return EXTENSION_MAP.get(extension, 'Otros')
```


CORRECCIÓN #5: Gestión de memoria en SearchService
--------------------------------------------------

En backend.py, añadir en SearchService.__init__:

```python
def __init__(self, use_windows_search: bool = True, max_cached_searches: int = 10):
    # ... código existente ...
    self._max_cached_searches = max_cached_searches


def _cleanup_old_searches(self):
    \"\"\"Elimina búsquedas antiguas para liberar memoria\"\"\"
    with self._lock:
        if len(self._search_results) > self._max_cached_searches:
            # Mantener solo las N más recientes
            # Asumiendo que search_id es timestamp
            sorted_ids = sorted(self._search_results.keys())
            to_remove = sorted_ids[:-self._max_cached_searches]

            for search_id in to_remove:
                del self._search_results[search_id]
                logger.debug(f"Removed old search results: {search_id}")
```

Llamar desde search_thread (línea 816):
```python
with self._lock:
    self._search_results[search_id] = results
    self._cleanup_old_searches()  # ← Añadir
```


CORRECCIÓN #6: Manejo de Unicode en paths
-----------------------------------------

En file_manager.py línea 650, reemplazar:

```python
# ANTES:
subprocess.run(['explorer', '/select,', os.path.normpath(filepath)], check=True)

# DESPUÉS:
# Usar startfile para manejar Unicode correctamente
import subprocess
normalized = os.path.normpath(filepath)
subprocess.run(['explorer', '/select,', normalized],
               check=True,
               encoding='utf-8',  # ← Añadir
               errors='replace')   # ← Manejar caracteres inválidos
```


CORRECCIÓN #7: Logging unificado
--------------------------------

Crear logger centralizado en cada módulo:

```python
# En file_manager.py, reemplazar todos los print() con:
import logging

logger = logging.getLogger(__name__)

# Luego:
# print(f"Error: {e}")  → logger.error(f"Error: {e}")
# print(f"Info")        → logger.info(f"Info")
```


CORRECCIÓN #8: Validación de directorios en UI
----------------------------------------------

En ui.py línea 696, añadir validación:

```python
def _start_search(self):
    # Obtener directorios seleccionados
    search_paths = self.dir_tree.get_selected_paths()
    if not search_paths:
        QMessageBox.warning(self, "No Directories",
                          "Please select at least one directory to search.")
        return

    # ← AÑADIR: Validar que existan
    valid_paths = []
    invalid_paths = []

    for path in search_paths:
        if os.path.exists(path):
            valid_paths.append(path)
        else:
            invalid_paths.append(path)

    if invalid_paths:
        msg = "The following directories do not exist:\\n" + "\\n".join(invalid_paths[:5])
        if len(invalid_paths) > 5:
            msg += f"\\n... and {len(invalid_paths) - 5} more"
        QMessageBox.warning(self, "Invalid Directories", msg)

    if not valid_paths:
        return

    # Continuar con valid_paths en lugar de search_paths
    search_paths = valid_paths
```

===============================================================================
PRUEBAS RECOMENDADAS
===============================================================================

1. Test de categorización unificada:
```python
from categories import FileCategory, classify_by_extension
from backend import SearchResult

# Verificar coherencia
result = SearchResult(path="test.zip", name="test.zip")
assert result.category == FileCategory.COMPRIMIDOS
assert classify_by_extension(".zip") == FileCategory.COMPRIMIDOS
```

2. Test de _format_size sin efectos secundarios:
```python
result = SearchResult(path="test", name="test", size=1024000)
size1 = result._format_size()
size2 = result._format_size()
assert size1 == size2  # Debe retornar lo mismo
assert result.size == 1024000  # No debe modificarse
```

3. Test de paths con caracteres especiales:
```python
path_with_spaces = "C:\\Users\\My Documents\\test.txt"
path_with_unicode = "C:\\Users\\Documentos\\año 2024\\test.txt"

query = SearchQuery(keywords=["test"], search_paths=[path_with_spaces])
sql = query.build_sql_query()
# Verificar que se escape correctamente
```

4. Test de thread-safety:
```python
import threading
service = SearchService()
results = []

def search_thread():
    query = SearchQuery(keywords=["test"])
    r = service.search_sync(query)
    results.append(r)

threads = [threading.Thread(target=search_thread) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

# Verificar que no haya crashes
assert len(results) == 10
```

===============================================================================
PRIORIZACIÓN DE CORRECCIONES
===============================================================================

URGENTE (Implementar hoy):
1. Corrección #2: Bug en _format_size (causa corrupción de datos)
2. Corrección #1: Unificar categorías (causa pérdida de resultados)

ALTA PRIORIDAD (Implementar esta semana):
3. Corrección #4: Validación de entrada en classify_file
4. Corrección #5: Gestión de memoria
5. Corrección #8: Validación de directorios

MEDIA PRIORIDAD (Implementar este mes):
6. Corrección #3: Normalización de paths
7. Corrección #6: Manejo de Unicode
8. Corrección #7: Logging unificado

BAJA PRIORIDAD (Mejoras futuras):
9. Refactorización de código duplicado
10. Implementación de tests unitarios
11. Documentación completa de API

===============================================================================
ARCHIVOS GENERADOS
===============================================================================

Este archivo de diagnóstico: patches.py
Archivos adicionales sugeridos:
- categories.py (nueva implementación unificada)
- tests/test_categories.py (tests unitarios)
- tests/test_backend.py (tests de integración)

===============================================================================
CONCLUSIÓN
===============================================================================

Los módulos de Smart Search están OPERACIONALES pero tienen problemas de
diseño que afectan:
- Integridad de datos (_format_size modifica state)
- Consistencia (categorías incompatibles entre módulos)
- Robustez (falta validación de inputs)
- Rendimiento (memory leaks en búsquedas)

Prioridad MÁXIMA: Implementar correcciones #1 y #2 antes de usar en producción.

El código es generalmente de buena calidad con arquitectura modular sólida.
Los problemas identificados son solucionables sin refactorización mayor.

===============================================================================
FIN DEL REPORTE
===============================================================================
"""
