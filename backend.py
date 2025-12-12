"""
Smart Search Backend - Windows Search API Integration
------------------------------------------------------
Arquitectura modular para búsqueda avanzada en Windows usando COM/WMI.

Características:
- Búsqueda por nombre y contenido usando Windows Search API
- Soporte para wildcards múltiples (*)
- Filtrado por directorios específicos
- Clasificación por tipo de archivo
- Threading para operaciones no bloqueantes
- Manejo robusto de errores
- Operaciones de archivos (copiar, mover, abrir)

Dependencias:
- pywin32: pip install pywin32
- comtypes: pip install comtypes
"""

import os
import shutil
import subprocess
import threading
import logging
from pathlib import Path
from typing import List, Dict, Callable, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from queue import Queue
import time

# Importar utilidades compartidas
from utils import format_file_size
from core.security import (
    sanitize_sql_input,
    validate_search_input,
    sanitize_cli_argument,
    validate_subprocess_path,
    log_security_event,
    SecurityEvent
)

# Windows COM imports
try:
    import win32com.client
    import pythoncom
    HAS_WIN32COM = True
except ImportError:
    HAS_WIN32COM = False
    logging.warning("pywin32 not installed. Install with: pip install pywin32")

try:
    import comtypes
    import comtypes.client
    HAS_COMTYPES = True
except ImportError:
    HAS_COMTYPES = False
    logging.warning("comtypes not installed. Install with: pip install comtypes")


# ============================================================================
# CONFIGURACIÓN Y CONSTANTES
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Importar sistema unificado de categorías
from categories import FileCategory, CATEGORY_EXTENSIONS, classify_by_extension

# Backward compatibility: usar el mapeo de categories.py
FILE_CATEGORY_MAP = CATEGORY_EXTENSIONS


# ============================================================================
# MODELOS DE DATOS
# ============================================================================

@dataclass
class SearchResult:
    """Representa un resultado de búsqueda"""
    path: str
    name: str
    size: int = 0
    modified: Optional[datetime] = None
    created: Optional[datetime] = None
    extension: str = ""
    category: FileCategory = FileCategory.OTROS
    is_directory: bool = False
    attributes: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Inicialización post-creación"""
        if not self.extension and not self.is_directory:
            self.extension = Path(self.path).suffix.lower()

        if self.category == FileCategory.OTROS and self.extension:
            self.category = self._classify_file()

    def _classify_file(self) -> FileCategory:
        """Clasifica el archivo por su extensión"""
        # Usar función centralizada de categories.py
        return classify_by_extension(self.extension)

    def to_dict(self) -> Dict:
        """Convierte a diccionario serializable"""
        return {
            'path': self.path,
            'name': self.name,
            'size': self.size,
            'size_formatted': format_file_size(self.size),
            'modified': self.modified.isoformat() if self.modified else None,
            'created': self.created.isoformat() if self.created else None,
            'extension': self.extension,
            'category': self.category.value,
            'is_directory': self.is_directory,
            'attributes': self.attributes
        }



@dataclass
class SearchQuery:
    """Representa una consulta de búsqueda"""
    keywords: List[str]
    search_paths: Optional[List[str]] = None
    search_content: bool = False
    search_filename: bool = True
    file_categories: Optional[Set[FileCategory]] = None
    max_results: int = 1000
    recursive: bool = True

    def __post_init__(self):
        """Validación y normalización"""
        if not self.keywords:
            raise ValueError("Se requiere al menos una palabra clave")

        # Normalizar wildcards
        self.keywords = [kw.strip() for kw in self.keywords if kw.strip()]

        # Si no se especifican paths, buscar en todo el sistema
        if not self.search_paths:
            self.search_paths = self._get_default_search_paths()

    @staticmethod
    def _get_default_search_paths() -> List[str]:
        """Obtiene los paths de búsqueda predeterminados"""
        user_profile = os.environ.get('USERPROFILE', 'C:\\Users')
        return [
            os.path.join(user_profile, 'Documents'),
            os.path.join(user_profile, 'Desktop'),
            os.path.join(user_profile, 'Downloads'),
        ]

    # NOTE: sanitize_sql_input and validate_search_input moved to core.security module

    def build_sql_query(self) -> str:
        """Construye la consulta SQL para Windows Search"""
        # Construir condición de búsqueda
        conditions = []

        if self.search_filename:
            # Buscar en nombre de archivo
            filename_conditions = []
            for keyword in self.keywords:
                # Validar input
                try:
                    validate_search_input(keyword)
                except ValueError as e:
                    log_security_event(
                        SecurityEvent.SQL_INJECTION_ATTEMPT,
                        {'keyword': keyword, 'error': str(e)},
                        severity="ERROR"
                    )
                    raise

                # SECURITY FIX CVE-001: Sanitizar ANTES de convertir wildcards
                # Esto previene SQL injection mientras preserva wildcards legítimos
                sanitized = sanitize_sql_input(
                    keyword,
                    escape_percent=True  # Escapar TODOS los % del usuario
                )

                # Ahora convertir wildcards * a % de forma segura
                # (los % inyectados por el usuario ya están escapados como [%])
                sanitized_with_wildcards = sanitized.replace('*', '%')

                filename_conditions.append(f"System.FileName LIKE '%{sanitized_with_wildcards}%'")

            if filename_conditions:
                conditions.append(f"({' OR '.join(filename_conditions)})")

        if self.search_content:
            # Buscar en contenido
            content_conditions = []
            for keyword in self.keywords:
                # Validar input
                try:
                    validate_search_input(keyword)
                except ValueError as e:
                    log_security_event(
                        SecurityEvent.SQL_INJECTION_ATTEMPT,
                        {'keyword': keyword, 'error': str(e)},
                        severity="ERROR"
                    )
                    raise

                # Sanitizar keyword para CONTAINS
                sanitized = sanitize_sql_input(keyword)

                # CONTAINS para búsqueda full-text
                content_conditions.append(f"CONTAINS('{sanitized}')")

            if content_conditions:
                conditions.append(f"({' OR '.join(content_conditions)})")

        # Construir WHERE clause
        where_clause = ' OR '.join(conditions) if conditions else "1=1"

        # Filtrar por paths
        if self.search_paths:
            path_conditions = []
            for path in self.search_paths:
                # Validar que el path no contenga patrones peligrosos
                try:
                    validate_search_input(path)
                except ValueError as e:
                    log_security_event(
                        SecurityEvent.SQL_INJECTION_ATTEMPT,
                        {'path': path, 'error': str(e)},
                        severity="ERROR"
                    )
                    raise

                # Sanitizar el path
                sanitized_path = sanitize_sql_input(path, max_length=500)

                # Normalizar path para Windows Search
                # Nota: las barras invertidas ya están escapadas por sanitize_sql_input
                if self.recursive:
                    path_conditions.append(
                        f"System.ItemPathDisplay LIKE '{sanitized_path}%'"
                    )
                else:
                    path_conditions.append(
                        f"DIRECTORY='{sanitized_path}'"
                    )

            if path_conditions:
                where_clause += f" AND ({' OR '.join(path_conditions)})"

        # Filtrar por categorías de archivo
        if self.file_categories:
            extensions = set()
            for category in self.file_categories:
                extensions.update(FILE_CATEGORY_MAP.get(category, set()))

            if extensions:
                ext_conditions = []
                for ext in extensions:
                    # Validar extensión
                    try:
                        validate_search_input(ext)
                    except ValueError as e:
                        log_security_event(
                            SecurityEvent.SQL_INJECTION_ATTEMPT,
                            {'extension': ext, 'error': str(e)},
                            severity="ERROR"
                        )
                        raise

                    # Sanitizar extensión
                    sanitized_ext = sanitize_sql_input(ext, max_length=20)

                    ext_conditions.append(
                        f"System.FileExtension='{sanitized_ext}'"
                    )

                where_clause += f" AND ({' OR '.join(ext_conditions)})"

        # Construir query completa
        query = f"""
        SELECT TOP {self.max_results}
            System.ItemPathDisplay,
            System.FileName,
            System.Size,
            System.DateModified,
            System.DateCreated,
            System.FileExtension,
            System.ItemType
        FROM SystemIndex
        WHERE {where_clause}
        ORDER BY System.DateModified DESC
        """

        return query.strip()


# ============================================================================
# MOTOR DE BÚSQUEDA
# ============================================================================

class WindowsSearchEngine:
    """Motor de búsqueda usando Windows Search API (COM)"""

    def __init__(self):
        """Inicializa el motor de búsqueda"""
        self._validate_dependencies()
        self._connection = None
        self._lock = threading.Lock()

    @staticmethod
    def _validate_dependencies():
        """Valida que las dependencias necesarias estén instaladas"""
        if not HAS_WIN32COM:
            raise ImportError(
                "pywin32 no está instalado. Ejecute: pip install pywin32"
            )

    def _get_connection(self):
        """Obtiene una conexión ADO para Windows Search"""
        # Inicializar COM en este thread
        pythoncom.CoInitialize()

        try:
            # Crear conexión ADO
            connection = win32com.client.Dispatch("ADODB.Connection")
            connection_string = (
                "Provider=Search.CollatorDSO;"
                "Extended Properties='Application=Windows';"
            )
            connection.Open(connection_string)
            return connection
        except Exception as e:
            logger.error(f"Error al conectar con Windows Search: {e}")
            raise ConnectionError(
                "No se pudo conectar con Windows Search. "
                "Verifique que el servicio Windows Search esté activo."
            ) from e

    def search(
        self,
        query: SearchQuery,
        callback: Optional[Callable[[SearchResult], None]] = None
    ) -> List[SearchResult]:
        """
        Ejecuta una búsqueda

        Args:
            query: Objeto SearchQuery con los parámetros
            callback: Función opcional para procesar resultados en tiempo real

        Returns:
            Lista de SearchResult
        """
        results = []
        connection = None
        recordset = None

        try:
            # Obtener conexión
            connection = self._get_connection()

            # Construir y ejecutar query SQL
            sql_query = query.build_sql_query()
            logger.info(f"Ejecutando query: {sql_query}")

            # Crear recordset
            recordset = win32com.client.Dispatch("ADODB.Recordset")
            recordset.Open(sql_query, connection)

            # Procesar resultados
            while not recordset.EOF:
                try:
                    result = self._parse_record(recordset)
                    results.append(result)

                    # Callback para procesamiento en tiempo real
                    if callback:
                        callback(result)

                except Exception as e:
                    logger.warning(f"Error procesando registro: {e}")

                recordset.MoveNext()

            logger.info(f"Búsqueda completada: {len(results)} resultados")
            return results

        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            raise

        finally:
            # Limpiar recursos
            if recordset:
                try:
                    recordset.Close()
                except Exception as e:
                    logger.debug(f"Error closing recordset: {e}")

            if connection:
                try:
                    connection.Close()
                except Exception as e:
                    logger.debug(f"Error closing connection: {e}")

            # Liberar COM
            pythoncom.CoUninitialize()

    @staticmethod
    def _parse_record(recordset) -> SearchResult:
        """Parsea un registro de ADO a SearchResult"""
        try:
            path = recordset.Fields("System.ItemPathDisplay").Value or ""
            name = recordset.Fields("System.FileName").Value or ""
            size = recordset.Fields("System.Size").Value or 0

            # Fechas
            modified = recordset.Fields("System.DateModified").Value
            created = recordset.Fields("System.DateCreated").Value

            # Convertir fechas de COM a datetime
            if modified:
                try:
                    modified = datetime.fromisoformat(str(modified))
                except (ValueError, TypeError, AttributeError) as e:
                    logger.debug(f"Error parsing modified date: {e}")
                    modified = None

            if created:
                try:
                    created = datetime.fromisoformat(str(created))
                except (ValueError, TypeError, AttributeError) as e:
                    logger.debug(f"Error parsing created date: {e}")
                    created = None

            # Extensión y tipo
            extension = recordset.Fields("System.FileExtension").Value or ""
            item_type = recordset.Fields("System.ItemType").Value or ""

            # Determinar si es directorio
            is_directory = os.path.isdir(path) if path else False

            return SearchResult(
                path=path,
                name=name,
                size=size if size else 0,
                modified=modified,
                created=created,
                extension=extension.lower() if extension else "",
                is_directory=is_directory,
                attributes={'item_type': item_type}
            )

        except Exception as e:
            logger.warning(f"Error parseando registro: {e}")
            raise


class FallbackSearchEngine:
    """Motor de búsqueda alternativo usando sistema de archivos"""

    def search(
        self,
        query: SearchQuery,
        callback: Optional[Callable[[SearchResult], None]] = None
    ) -> List[SearchResult]:
        """
        Búsqueda manual del sistema de archivos

        Args:
            query: Objeto SearchQuery
            callback: Callback opcional

        Returns:
            Lista de SearchResult
        """
        results = []

        for search_path in query.search_paths or []:
            if not os.path.exists(search_path):
                logger.warning(f"Path no existe: {search_path}")
                continue

            try:
                results.extend(
                    self._search_directory(search_path, query, callback)
                )
            except Exception as e:
                logger.error(f"Error buscando en {search_path}: {e}")

        # Limitar resultados
        results = results[:query.max_results]

        # Ordenar por fecha modificación
        results.sort(key=lambda r: r.modified or datetime.min, reverse=True)

        return results

    def _search_directory(
        self,
        path: str,
        query: SearchQuery,
        callback: Optional[Callable]
    ) -> List[SearchResult]:
        """Busca recursivamente en un directorio"""
        results = []

        try:
            for root, dirs, files in os.walk(path):
                # Buscar en archivos
                for filename in files:
                    if self._matches_query(filename, query):
                        full_path = os.path.join(root, filename)
                        result = self._create_result(full_path, filename)

                        if result:
                            results.append(result)

                            if callback:
                                callback(result)

                            # Limitar resultados
                            if len(results) >= query.max_results:
                                return results

                # Si no es recursivo, no continuar
                if not query.recursive:
                    break

        except PermissionError:
            logger.warning(f"Permiso denegado: {path}")
        except Exception as e:
            logger.error(f"Error en {path}: {e}")

        return results

    @staticmethod
    def _matches_query(filename: str, query: SearchQuery) -> bool:
        """Verifica si un archivo coincide con la query"""
        if not query.search_filename:
            return False

        filename_lower = filename.lower()

        # Verificar cada keyword
        for keyword in query.keywords:
            # Convertir * a patrón simple
            pattern = keyword.lower().replace('*', '')

            if pattern in filename_lower:
                return True

        return False

    @staticmethod
    def _create_result(path: str, filename: str) -> Optional[SearchResult]:
        """Crea un SearchResult desde un path"""
        try:
            stat = os.stat(path)

            return SearchResult(
                path=path,
                name=filename,
                size=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime),
                created=datetime.fromtimestamp(stat.st_ctime),
                is_directory=os.path.isdir(path)
            )
        except Exception as e:
            logger.warning(f"Error creando resultado para {path}: {e}")
            return None


# ============================================================================
# GESTOR DE OPERACIONES DE ARCHIVOS
# ============================================================================

class FileOperations:
    """Maneja operaciones sobre archivos y directorios"""

    @staticmethod
    def copy(source: str, destination: str, overwrite: bool = False) -> bool:
        """
        Copia un archivo o directorio

        Args:
            source: Path origen
            destination: Path destino
            overwrite: Si sobrescribir si existe

        Returns:
            True si éxito
        """
        try:
            if not os.path.exists(source):
                raise FileNotFoundError(f"Origen no existe: {source}")

            # Si es directorio
            if os.path.isdir(source):
                if os.path.exists(destination) and not overwrite:
                    raise FileExistsError(f"Destino ya existe: {destination}")

                if os.path.exists(destination):
                    shutil.rmtree(destination)

                shutil.copytree(source, destination)
            else:
                # Es archivo
                if os.path.exists(destination) and not overwrite:
                    raise FileExistsError(f"Destino ya existe: {destination}")

                shutil.copy2(source, destination)

            logger.info(f"Copiado: {source} -> {destination}")
            return True

        except Exception as e:
            logger.error(f"Error copiando {source}: {e}")
            raise

    @staticmethod
    def move(source: str, destination: str, overwrite: bool = False) -> bool:
        """
        Mueve un archivo o directorio

        Args:
            source: Path origen
            destination: Path destino
            overwrite: Si sobrescribir si existe

        Returns:
            True si éxito
        """
        try:
            if not os.path.exists(source):
                raise FileNotFoundError(f"Origen no existe: {source}")

            if os.path.exists(destination) and not overwrite:
                raise FileExistsError(f"Destino ya existe: {destination}")

            if os.path.exists(destination):
                if os.path.isdir(destination):
                    shutil.rmtree(destination)
                else:
                    os.remove(destination)

            shutil.move(source, destination)
            logger.info(f"Movido: {source} -> {destination}")
            return True

        except Exception as e:
            logger.error(f"Error moviendo {source}: {e}")
            raise

    @staticmethod
    def open_file(path: str) -> bool:
        """
        Abre un archivo con la aplicación predeterminada

        Args:
            path: Path del archivo

        Returns:
            True si éxito
        """
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Archivo no existe: {path}")

            # Usar el comando de Windows para abrir
            os.startfile(path)
            logger.info(f"Abierto: {path}")
            return True

        except Exception as e:
            logger.error(f"Error abriendo {path}: {e}")
            raise

    @staticmethod
    def open_location(path: str) -> bool:
        """
        Abre la ubicación del archivo en el explorador

        Args:
            path: Path del archivo o directorio

        Returns:
            True si éxito
        """
        try:
            # Validar y sanitizar el path
            validated_path = validate_subprocess_path(path)

            # Si es directorio, abrirlo directamente
            if validated_path.is_dir():
                os.startfile(str(validated_path))
            else:
                # Si es archivo, abrir el directorio padre y seleccionarlo
                # Usar lista de argumentos (NO string) para prevenir command injection
                subprocess.run(
                    ['explorer', '/select,', str(validated_path)],
                    check=True,
                    timeout=5,
                    shell=False  # CRITICAL: Never use shell=True
                )

            logger.info(f"Ubicación abierta: {path}")
            return True

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout opening location: {path}")
            raise
        except Exception as e:
            logger.error(f"Error abriendo ubicación {path}: {e}")
            raise

    @staticmethod
    def delete(path: str, permanent: bool = False) -> bool:
        """
        Elimina un archivo o directorio

        Args:
            path: Path a eliminar
            permanent: Si True, eliminación permanente. Si False, a papelera

        Returns:
            True si éxito
        """
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Path no existe: {path}")

            if permanent:
                # Eliminación permanente
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            else:
                # Mover a papelera (requiere send2trash)
                try:
                    import send2trash
                    send2trash.send2trash(path)
                except ImportError:
                    logger.warning(
                        "send2trash no instalado. Eliminación permanente."
                    )
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)

            logger.info(f"Eliminado: {path}")
            return True

        except Exception as e:
            logger.error(f"Error eliminando {path}: {e}")
            raise

    @staticmethod
    def get_properties(path: str) -> Dict:
        """
        Obtiene propiedades detalladas de un archivo

        Args:
            path: Path del archivo

        Returns:
            Diccionario con propiedades
        """
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Path no existe: {path}")

            stat = os.stat(path)

            return {
                'path': path,
                'name': os.path.basename(path),
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'accessed': datetime.fromtimestamp(stat.st_atime),
                'is_directory': os.path.isdir(path),
                'is_file': os.path.isfile(path),
                'extension': Path(path).suffix,
                'parent': str(Path(path).parent),
                'absolute_path': os.path.abspath(path)
            }

        except Exception as e:
            logger.error(f"Error obteniendo propiedades de {path}: {e}")
            raise


# ============================================================================
# SERVICIO DE BÚSQUEDA CON THREADING
# ============================================================================

class SearchService:
    """Servicio de búsqueda con soporte para threading"""

    def __init__(self, use_windows_search: bool = True, max_cached_searches: int = 10):
        """
        Inicializa el servicio

        Args:
            use_windows_search: Si usar Windows Search API o fallback
            max_cached_searches: Número máximo de búsquedas en caché
        """
        self.use_windows_search = use_windows_search and HAS_WIN32COM

        if self.use_windows_search:
            self.engine = WindowsSearchEngine()
            logger.info("Usando Windows Search API")
        else:
            self.engine = FallbackSearchEngine()
            logger.info("Usando motor de búsqueda alternativo")

        self.file_ops = FileOperations()
        self._active_searches: Dict[str, threading.Thread] = {}
        self._search_results: Dict[str, List[SearchResult]] = {}
        self._lock = threading.Lock()
        self._max_cached_searches = max_cached_searches

    def _cleanup_old_searches(self):
        """Elimina búsquedas antiguas para liberar memoria"""
        with self._lock:
            if len(self._search_results) > self._max_cached_searches:
                # Mantener solo las N más recientes (basado en timestamp en ID)
                sorted_ids = sorted(self._search_results.keys())
                to_remove = sorted_ids[:-self._max_cached_searches]

                for search_id in to_remove:
                    del self._search_results[search_id]
                    logger.debug(f"Removed old search results: {search_id}")

    def search_async(
        self,
        query: SearchQuery,
        callback: Optional[Callable[[SearchResult], None]] = None,
        completion_callback: Optional[Callable[[List[SearchResult]], None]] = None,
        error_callback: Optional[Callable[[Exception], None]] = None
    ) -> str:
        """
        Ejecuta una búsqueda asíncrona

        Args:
            query: SearchQuery
            callback: Callback para cada resultado
            completion_callback: Callback al completar
            error_callback: Callback para errores

        Returns:
            ID de búsqueda
        """
        search_id = f"search_{int(time.time() * 1000)}"

        def search_thread():
            try:
                results = self.engine.search(query, callback)

                with self._lock:
                    self._search_results[search_id] = results
                    self._cleanup_old_searches()  # Limpiar búsquedas antiguas

                if completion_callback:
                    completion_callback(results)

            except Exception as e:
                logger.error(f"Error en búsqueda {search_id}: {e}")
                if error_callback:
                    error_callback(e)
            finally:
                with self._lock:
                    if search_id in self._active_searches:
                        del self._active_searches[search_id]

        thread = threading.Thread(target=search_thread, daemon=True)

        with self._lock:
            self._active_searches[search_id] = thread

        thread.start()
        logger.info(f"Búsqueda asíncrona iniciada: {search_id}")

        return search_id

    def search_sync(
        self,
        query: SearchQuery,
        callback: Optional[Callable[[SearchResult], None]] = None
    ) -> List[SearchResult]:
        """
        Ejecuta una búsqueda síncrona

        Args:
            query: SearchQuery
            callback: Callback opcional

        Returns:
            Lista de resultados
        """
        return self.engine.search(query, callback)

    def cancel_search(self, search_id: str) -> bool:
        """
        Cancela una búsqueda activa

        Args:
            search_id: ID de búsqueda

        Returns:
            True si se canceló
        """
        with self._lock:
            if search_id in self._active_searches:
                # Nota: threading.Thread no tiene método stop()
                # La cancelación debe manejarse con flags en el motor
                logger.warning(
                    f"Cancelación de {search_id} solicitada "
                    "(no implementado completamente)"
                )
                return True

        return False

    def get_results(self, search_id: str) -> Optional[List[SearchResult]]:
        """
        Obtiene resultados de una búsqueda

        Args:
            search_id: ID de búsqueda

        Returns:
            Lista de resultados o None
        """
        with self._lock:
            return self._search_results.get(search_id)

    def is_search_active(self, search_id: str) -> bool:
        """
        Verifica si una búsqueda está activa

        Args:
            search_id: ID de búsqueda

        Returns:
            True si está activa
        """
        with self._lock:
            return search_id in self._active_searches

    def classify_results(
        self,
        results: List[SearchResult]
    ) -> Dict[FileCategory, List[SearchResult]]:
        """
        Clasifica resultados por categoría

        Args:
            results: Lista de resultados

        Returns:
            Diccionario con resultados por categoría
        """
        classified = {category: [] for category in FileCategory}

        for result in results:
            classified[result.category].append(result)

        return classified


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

def main():
    """Ejemplo de uso del backend"""

    # Crear servicio
    service = SearchService(use_windows_search=True)

    # Crear query de ejemplo
    query = SearchQuery(
        keywords=['python', '*.py'],
        search_paths=[
            r'C:\Users\ramos\Documents',
            r'C:\Users\ramos\.local'
        ],
        search_content=False,
        search_filename=True,
        max_results=100
    )

    print("Iniciando búsqueda...")
    print(f"Query SQL: {query.build_sql_query()}")
    print()

    # Callback para resultados en tiempo real
    def on_result(result: SearchResult):
        print(f"Encontrado: {result.name} ({result.category.value})")

    # Callback de completado
    def on_complete(results: List[SearchResult]):
        print(f"\nBúsqueda completada: {len(results)} resultados")

        # Clasificar por categoría
        classified = service.classify_results(results)

        print("\nResultados por categoría:")
        for category, items in classified.items():
            if items:
                print(f"  {category.value}: {len(items)}")

    # Callback de error
    def on_error(error: Exception):
        print(f"Error: {error}")

    # Búsqueda asíncrona
    search_id = service.search_async(
        query,
        callback=on_result,
        completion_callback=on_complete,
        error_callback=on_error
    )

    print(f"Search ID: {search_id}")

    # Esperar a que termine
    while service.is_search_active(search_id):
        time.sleep(0.1)

    # Obtener resultados finales
    results = service.get_results(search_id)

    if results:
        print(f"\nPrimeros 5 resultados:")
        for i, result in enumerate(results[:5], 1):
            print(f"{i}. {result.to_dict()}")

        # Ejemplo de operaciones de archivos
        if results:
            first_result = results[0]
            print(f"\nPropiedades de {first_result.name}:")
            props = service.file_ops.get_properties(first_result.path)
            for key, value in props.items():
                print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
