"""
Smart Search Performance Optimizations Module
==============================================

Módulo completo de optimizaciones de rendimiento para Smart Search.

Características:
- ResultsCache: Sistema de caché LRU para resultados de búsqueda
- LazyDirectoryLoader: Carga perezosa del árbol de directorios
- SearchDebouncer: Debounce y throttle para búsquedas
- VirtualTableModel: Virtual scrolling para tablas grandes
- SearchIndexer: Índice en memoria para búsquedas rápidas
- WorkerPool: Pool de workers para operaciones paralelas
- QueryOptimizer: Optimizador de consultas SQL
- MemoryManager: Gestor de memoria y limpieza de recursos

Performance Targets:
- Búsquedas < 100ms para resultados cacheados
- UI responsiva con 100k+ resultados
- Memoria estable bajo carga continua
- Threading eficiente con cancelación
"""

import os
import sys
import time
import threading
import hashlib
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional, Callable, Any, Tuple, Generator
from dataclasses import dataclass, field
from collections import OrderedDict, defaultdict
from enum import Enum
import weakref
from queue import Queue, PriorityQueue, Empty
import logging

try:
    from PyQt6.QtCore import (
        Qt, QAbstractTableModel, QModelIndex, QVariant, QTimer,
        QThread, pyqtSignal, QObject, QRunnable, QThreadPool
    )
    from PyQt6.QtWidgets import QAbstractItemView
    HAS_PYQT6 = True
except ImportError:
    HAS_PYQT6 = False
    print("Warning: PyQt6 not available. UI optimizations disabled.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CACHE SYSTEM - LRU Cache for Search Results
# ============================================================================

class CacheEntry:
    """Entry in the cache with metadata"""
    __slots__ = ('key', 'value', 'timestamp', 'hits', 'size')

    def __init__(self, key: str, value: Any, size: int = 0):
        self.key = key
        self.value = value
        self.timestamp = time.time()
        self.hits = 0
        self.size = size


class ResultsCache:
    """
    LRU Cache optimizado para resultados de búsqueda.

    Características:
    - LRU (Least Recently Used) eviction policy
    - Tamaño máximo configurable en memoria
    - TTL (Time To Live) para entries
    - Thread-safe
    - Estadísticas de uso (hit rate, miss rate)
    """

    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100, ttl_seconds: int = 300):
        """
        Args:
            max_size: Número máximo de entries
            max_memory_mb: Memoria máxima en MB
            ttl_seconds: Tiempo de vida de las entries en segundos
        """
        self.max_size = max_size
        self.max_memory = max_memory_mb * 1024 * 1024  # Convert to bytes
        self.ttl = ttl_seconds

        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._current_memory = 0

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del cache"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[key]

            # Check TTL
            if time.time() - entry.timestamp > self.ttl:
                self._remove(key)
                self._misses += 1
                return None

            # Update LRU - move to end
            self._cache.move_to_end(key)
            entry.hits += 1
            self._hits += 1

            return entry.value

    def put(self, key: str, value: Any, size: Optional[int] = None):
        """Almacena un valor en el cache"""
        if size is None:
            # Estimate size
            size = sys.getsizeof(value)

        with self._lock:
            # Remove existing if present
            if key in self._cache:
                self._remove(key)

            # Evict if necessary
            while (len(self._cache) >= self.max_size or
                   self._current_memory + size > self.max_memory):
                if not self._cache:
                    break
                self._evict_lru()

            # Add new entry
            entry = CacheEntry(key, value, size)
            self._cache[key] = entry
            self._current_memory += size

    def _remove(self, key: str):
        """Elimina una entry del cache"""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._current_memory -= entry.size

    def _evict_lru(self):
        """Elimina la entry menos recientemente usada"""
        if self._cache:
            key, entry = self._cache.popitem(last=False)
            self._current_memory -= entry.size
            self._evictions += 1

    def clear(self):
        """Limpia todo el cache"""
        with self._lock:
            self._cache.clear()
            self._current_memory = 0
            self._hits = 0
            self._misses = 0
            self._evictions = 0

    def invalidate(self, pattern: Optional[str] = None):
        """Invalida entries que coincidan con un patrón"""
        with self._lock:
            if pattern is None:
                self.clear()
                return

            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                self._remove(key)

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'memory_used_mb': self._current_memory / 1024 / 1024,
                'max_memory_mb': self.max_memory / 1024 / 1024,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'evictions': self._evictions
            }

    @staticmethod
    def generate_key(query_params: Dict[str, Any]) -> str:
        """Genera una clave única para los parámetros de búsqueda"""
        # Sort for consistency
        sorted_params = sorted(query_params.items())
        key_string = str(sorted_params)
        return hashlib.md5(key_string.encode()).hexdigest()


# ============================================================================
# LAZY DIRECTORY LOADER - On-demand directory tree loading
# ============================================================================

class DirectoryLoadState(Enum):
    """Estados de carga de un directorio"""
    UNLOADED = 0
    LOADING = 1
    LOADED = 2
    ERROR = 3


@dataclass
class LazyDirectoryNode:
    """Nodo de directorio con carga perezosa"""
    path: str
    name: str
    state: DirectoryLoadState = DirectoryLoadState.UNLOADED
    children: Optional[List['LazyDirectoryNode']] = None
    error: Optional[str] = None

    def __hash__(self):
        return hash(self.path)


class LazyDirectoryLoader:
    """
    Cargador perezoso del árbol de directorios.

    Características:
    - Carga directorios solo cuando se expanden
    - Cache de nodos cargados
    - Loading en background threads
    - Limitación de profundidad
    - Filtrado de directorios (system, hidden)
    """

    def __init__(self, max_depth: int = 3, max_children: int = 1000,
                 cache_size: int = 500):
        """
        Args:
            max_depth: Profundidad máxima a cargar automáticamente
            max_children: Número máximo de hijos por directorio
            cache_size: Tamaño del cache de nodos
        """
        self.max_depth = max_depth
        self.max_children = max_children

        self._cache: OrderedDict[str, LazyDirectoryNode] = OrderedDict()
        self._cache_size = cache_size
        self._lock = threading.RLock()

        # Thread pool for loading
        if HAS_PYQT6:
            self._thread_pool = QThreadPool.globalInstance()
            self._thread_pool.setMaxThreadCount(4)

        # System directories to skip
        self._skip_dirs = {
            '$Recycle.Bin', 'System Volume Information',
            'Windows', 'Program Files', 'Program Files (x86)',
            'ProgramData', 'Recovery', 'PerfLogs',
            'AppData', '.git', 'node_modules', '__pycache__'
        }

    def load_root_directories(self) -> List[LazyDirectoryNode]:
        """Carga solo los directorios raíz principales"""
        roots = []

        # Common user directories
        user_profile = os.environ.get('USERPROFILE', '')
        if user_profile:
            common_dirs = [
                ('Desktop', os.path.join(user_profile, 'Desktop')),
                ('Documents', os.path.join(user_profile, 'Documents')),
                ('Downloads', os.path.join(user_profile, 'Downloads')),
                ('Pictures', os.path.join(user_profile, 'Pictures')),
                ('Videos', os.path.join(user_profile, 'Videos')),
                ('Music', os.path.join(user_profile, 'Music')),
            ]

            for name, path in common_dirs:
                if os.path.exists(path):
                    node = LazyDirectoryNode(path=path, name=name)
                    roots.append(node)
                    self._add_to_cache(node)

        # Drives
        import string
        from ctypes import windll

        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    node = LazyDirectoryNode(path=drive, name=drive)
                    roots.append(node)
                    self._add_to_cache(node)
            bitmask >>= 1

        return roots

    def load_children(self, node: LazyDirectoryNode,
                     callback: Optional[Callable] = None) -> List[LazyDirectoryNode]:
        """
        Carga los hijos de un nodo.

        Args:
            node: Nodo padre
            callback: Callback opcional cuando termina la carga

        Returns:
            Lista de nodos hijos
        """
        # Check cache first
        with self._lock:
            if node.state == DirectoryLoadState.LOADED and node.children is not None:
                return node.children

            if node.state == DirectoryLoadState.LOADING:
                # Already loading, wait or return empty
                return []

            node.state = DirectoryLoadState.LOADING

        try:
            children = self._load_children_sync(node.path)

            with self._lock:
                node.children = children
                node.state = DirectoryLoadState.LOADED

                # Add children to cache
                for child in children:
                    self._add_to_cache(child)

            if callback:
                callback(node, children)

            return children

        except Exception as e:
            logger.error(f"Error loading children for {node.path}: {e}")
            with self._lock:
                node.state = DirectoryLoadState.ERROR
                node.error = str(e)
            return []

    def _load_children_sync(self, path: str) -> List[LazyDirectoryNode]:
        """Carga síncrona de hijos"""
        children = []

        try:
            # List directory contents
            entries = os.listdir(path)
            entries.sort()

            count = 0
            for entry in entries:
                if count >= self.max_children:
                    break

                # Skip hidden and system directories
                if entry.startswith('.') or entry in self._skip_dirs:
                    continue

                entry_path = os.path.join(path, entry)

                # Only directories
                try:
                    if os.path.isdir(entry_path):
                        node = LazyDirectoryNode(path=entry_path, name=entry)
                        children.append(node)
                        count += 1
                except (PermissionError, OSError):
                    continue

        except (PermissionError, OSError) as e:
            logger.warning(f"Permission denied or error accessing {path}: {e}")

        return children

    def _add_to_cache(self, node: LazyDirectoryNode):
        """Añade un nodo al cache"""
        with self._lock:
            if node.path in self._cache:
                self._cache.move_to_end(node.path)
            else:
                self._cache[node.path] = node

                # Evict if necessary
                while len(self._cache) > self._cache_size:
                    self._cache.popitem(last=False)

    def get_cached_node(self, path: str) -> Optional[LazyDirectoryNode]:
        """Obtiene un nodo del cache"""
        with self._lock:
            return self._cache.get(path)

    def clear_cache(self):
        """Limpia el cache"""
        with self._lock:
            self._cache.clear()


# ============================================================================
# SEARCH DEBOUNCER - Debounce and throttle for search
# ============================================================================

class SearchDebouncer(QObject if HAS_PYQT6 else object):
    """
    Debouncer para búsquedas en tiempo real.

    Características:
    - Debounce: Espera a que el usuario deje de escribir
    - Throttle: Limita la frecuencia de búsquedas
    - Cancelación de búsquedas pendientes
    - Queue de búsquedas pendientes
    """

    if HAS_PYQT6:
        search_triggered = pyqtSignal(str, dict)  # query, params

    def __init__(self, debounce_ms: int = 300, throttle_ms: int = 500):
        """
        Args:
            debounce_ms: Tiempo de espera después del último input (ms)
            throttle_ms: Tiempo mínimo entre búsquedas (ms)
        """
        if HAS_PYQT6:
            super().__init__()

        self.debounce_ms = debounce_ms
        self.throttle_ms = throttle_ms

        self._last_search_time = 0
        self._pending_search = None
        self._lock = threading.Lock()

        if HAS_PYQT6:
            self._debounce_timer = QTimer()
            self._debounce_timer.setSingleShot(True)
            self._debounce_timer.timeout.connect(self._execute_pending_search)

    def search(self, query: str, params: Optional[Dict] = None):
        """
        Solicita una búsqueda (con debounce).

        Args:
            query: Texto de búsqueda
            params: Parámetros adicionales
        """
        if params is None:
            params = {}

        with self._lock:
            # Store pending search
            self._pending_search = (query, params)

            # Restart debounce timer
            if HAS_PYQT6:
                self._debounce_timer.stop()
                self._debounce_timer.start(self.debounce_ms)

    def _execute_pending_search(self):
        """Ejecuta la búsqueda pendiente (con throttle)"""
        with self._lock:
            if self._pending_search is None:
                return

            current_time = time.time() * 1000  # ms
            time_since_last = current_time - self._last_search_time

            # Check throttle
            if time_since_last < self.throttle_ms:
                # Schedule for later
                delay = int(self.throttle_ms - time_since_last)
                if HAS_PYQT6:
                    self._debounce_timer.start(delay)
                return

            # Execute search
            query, params = self._pending_search
            self._pending_search = None
            self._last_search_time = current_time

        # Trigger search
        if HAS_PYQT6:
            self.search_triggered.emit(query, params)

    def cancel(self):
        """Cancela la búsqueda pendiente"""
        with self._lock:
            self._pending_search = None
            if HAS_PYQT6:
                self._debounce_timer.stop()


# ============================================================================
# VIRTUAL TABLE MODEL - Virtual scrolling for large result sets
# ============================================================================

if HAS_PYQT6:
    class VirtualTableModel(QAbstractTableModel):
        """
        Modelo de tabla con virtual scrolling para resultados grandes.

        Características:
        - Solo renderiza las filas visibles
        - Soporta millones de filas sin degradación
        - Ordenamiento eficiente
        - Filtrado rápido
        - Paginación automática
        """

        def __init__(self, headers: List[str], page_size: int = 100):
            """
            Args:
                headers: Nombres de las columnas
                page_size: Tamaño de página para carga
            """
            super().__init__()

            self._headers = headers
            self._page_size = page_size

            # Data storage
            self._data: List[Dict[str, Any]] = []
            self._filtered_indices: Optional[List[int]] = None
            self._sort_column = -1
            self._sort_order = Qt.SortOrder.AscendingOrder

            # Cache for formatted data
            self._format_cache: Dict[Tuple[int, int], str] = {}

        def rowCount(self, parent=QModelIndex()) -> int:
            """Número de filas"""
            if parent.isValid():
                return 0

            if self._filtered_indices is not None:
                return len(self._filtered_indices)
            return len(self._data)

        def columnCount(self, parent=QModelIndex()) -> int:
            """Número de columnas"""
            if parent.isValid():
                return 0
            return len(self._headers)

        def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
            """Obtiene datos de una celda"""
            if not index.isValid():
                return QVariant()

            row = index.row()
            col = index.column()

            # Get actual row index
            if self._filtered_indices is not None:
                if row >= len(self._filtered_indices):
                    return QVariant()
                actual_row = self._filtered_indices[row]
            else:
                actual_row = row

            if actual_row >= len(self._data):
                return QVariant()

            if role == Qt.ItemDataRole.DisplayRole:
                # Check cache
                cache_key = (actual_row, col)
                if cache_key in self._format_cache:
                    return self._format_cache[cache_key]

                # Get data
                row_data = self._data[actual_row]
                header = self._headers[col]
                value = row_data.get(header, '')

                # Format value
                formatted = self._format_value(value)

                # Cache (limit cache size)
                if len(self._format_cache) < 10000:
                    self._format_cache[cache_key] = formatted

                return formatted

            elif role == Qt.ItemDataRole.UserRole:
                # Raw data
                row_data = self._data[actual_row]
                header = self._headers[col]
                return row_data.get(header)

            return QVariant()

        def headerData(self, section: int, orientation: Qt.Orientation,
                      role: int = Qt.ItemDataRole.DisplayRole):
            """Datos del header"""
            if role == Qt.ItemDataRole.DisplayRole:
                if orientation == Qt.Orientation.Horizontal:
                    if 0 <= section < len(self._headers):
                        return self._headers[section]
            return QVariant()

        def add_row(self, row_data: Dict[str, Any]):
            """Añade una fila"""
            row = len(self._data)
            self.beginInsertRows(QModelIndex(), row, row)
            self._data.append(row_data)
            self.endInsertRows()

            # Clear cache
            self._format_cache.clear()

        def add_rows(self, rows: List[Dict[str, Any]]):
            """Añade múltiples filas eficientemente"""
            if not rows:
                return

            start_row = len(self._data)
            end_row = start_row + len(rows) - 1

            self.beginInsertRows(QModelIndex(), start_row, end_row)
            self._data.extend(rows)
            self.endInsertRows()

            # Clear cache
            self._format_cache.clear()

        def clear(self):
            """Limpia todos los datos"""
            self.beginResetModel()
            self._data.clear()
            self._filtered_indices = None
            self._format_cache.clear()
            self.endResetModel()

        def filter(self, predicate: Callable[[Dict], bool]):
            """
            Filtra filas según un predicado.

            Args:
                predicate: Función que retorna True si la fila debe incluirse
            """
            self.beginResetModel()

            indices = []
            for i, row in enumerate(self._data):
                if predicate(row):
                    indices.append(i)

            self._filtered_indices = indices if indices != list(range(len(self._data))) else None
            self._format_cache.clear()

            self.endResetModel()

        def clear_filter(self):
            """Limpia el filtro"""
            self.beginResetModel()
            self._filtered_indices = None
            self._format_cache.clear()
            self.endResetModel()

        def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder):
            """Ordena por columna"""
            if column < 0 or column >= len(self._headers):
                return

            self.beginResetModel()

            header = self._headers[column]
            reverse = (order == Qt.SortOrder.DescendingOrder)

            # Sort data
            self._data.sort(key=lambda x: x.get(header, ''), reverse=reverse)

            self._sort_column = column
            self._sort_order = order
            self._format_cache.clear()

            self.endResetModel()

        def get_row_data(self, row: int) -> Optional[Dict[str, Any]]:
            """Obtiene los datos completos de una fila"""
            if self._filtered_indices is not None:
                if row >= len(self._filtered_indices):
                    return None
                actual_row = self._filtered_indices[row]
            else:
                actual_row = row

            if actual_row >= len(self._data):
                return None

            return self._data[actual_row]

        @staticmethod
        def _format_value(value: Any) -> str:
            """Formatea un valor para mostrar"""
            if value is None:
                return ''

            if isinstance(value, datetime):
                return value.strftime('%Y-%m-%d %H:%M:%S')

            if isinstance(value, (int, float)):
                if isinstance(value, int) and value > 1024:
                    # Format file size
                    return VirtualTableModel._format_size(value)
                return str(value)

            return str(value)

        @staticmethod
        def _format_size(size: int) -> str:
            """Formatea tamaño de archivo"""
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} PB"


# ============================================================================
# SEARCH INDEXER - In-memory index for fast searches
# ============================================================================

class SearchIndexer:
    """
    Índice en memoria para búsquedas rápidas.

    Características:
    - Índice invertido por palabras
    - Búsqueda full-text básica
    - Actualización incremental
    - Persistencia opcional
    """

    def __init__(self):
        self._index: Dict[str, Set[int]] = defaultdict(set)  # word -> row indices
        self._documents: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    def add_document(self, doc: Dict[str, Any], doc_id: Optional[int] = None) -> int:
        """
        Añade un documento al índice.

        Args:
            doc: Documento a indexar
            doc_id: ID opcional del documento

        Returns:
            ID del documento
        """
        with self._lock:
            if doc_id is None:
                doc_id = len(self._documents)
                self._documents.append(doc)
            else:
                # Update existing
                if doc_id < len(self._documents):
                    self._documents[doc_id] = doc
                else:
                    self._documents.append(doc)

            # Index all text fields
            for key, value in doc.items():
                if isinstance(value, str):
                    words = self._tokenize(value)
                    for word in words:
                        self._index[word].add(doc_id)

            return doc_id

    def search(self, query: str) -> List[int]:
        """
        Busca documentos que contengan el query.

        Args:
            query: Texto de búsqueda

        Returns:
            Lista de IDs de documentos
        """
        words = self._tokenize(query)
        if not words:
            return []

        with self._lock:
            # Get documents containing all words (AND logic)
            result_sets = [self._index.get(word, set()) for word in words]

            if not result_sets:
                return []

            # Intersection of all sets
            result = set.intersection(*result_sets) if result_sets else set()
            return sorted(list(result))

    def get_document(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene un documento por ID"""
        with self._lock:
            if 0 <= doc_id < len(self._documents):
                return self._documents[doc_id]
            return None

    def clear(self):
        """Limpia el índice"""
        with self._lock:
            self._index.clear()
            self._documents.clear()

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Tokeniza texto en palabras"""
        # Simple tokenization: lowercase, split by non-alphanumeric
        import re
        text = text.lower()
        words = re.findall(r'\w+', text)
        return words


# ============================================================================
# WORKER POOL - Thread pool for parallel operations
# ============================================================================

class WorkerTask:
    """Tarea para el worker pool"""
    def __init__(self, func: Callable, args: Tuple = (), kwargs: Dict = None,
                 priority: int = 0, callback: Optional[Callable] = None):
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.priority = priority
        self.callback = callback
        self.result = None
        self.error = None
        self.completed = threading.Event()

    def __lt__(self, other):
        # For priority queue (higher priority = lower number)
        return self.priority < other.priority


class WorkerPool:
    """
    Pool de workers para operaciones paralelas.

    Características:
    - Número configurable de workers
    - Queue con prioridades
    - Cancelación de tareas pendientes
    - Callbacks de completado
    - Gestión de errores
    """

    def __init__(self, num_workers: int = 4):
        """
        Args:
            num_workers: Número de threads workers
        """
        self.num_workers = num_workers
        self._task_queue: PriorityQueue[Tuple[int, WorkerTask]] = PriorityQueue()
        self._workers: List[threading.Thread] = []
        self._shutdown = threading.Event()
        self._lock = threading.Lock()

        # Start workers
        self._start_workers()

    def _start_workers(self):
        """Inicia los workers"""
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"WorkerPool-{i}",
                daemon=True
            )
            worker.start()
            self._workers.append(worker)

    def _worker_loop(self):
        """Loop principal del worker"""
        while not self._shutdown.is_set():
            try:
                # Get task with timeout
                priority, task = self._task_queue.get(timeout=0.5)

                try:
                    # Execute task
                    result = task.func(*task.args, **task.kwargs)
                    task.result = result

                    # Call callback if provided
                    if task.callback:
                        task.callback(result)

                except Exception as e:
                    logger.error(f"Worker task error: {e}")
                    task.error = e

                finally:
                    task.completed.set()
                    self._task_queue.task_done()

            except Empty:
                continue

    def submit(self, func: Callable, *args, priority: int = 0,
               callback: Optional[Callable] = None, **kwargs) -> WorkerTask:
        """
        Envía una tarea al pool.

        Args:
            func: Función a ejecutar
            *args: Argumentos posicionales
            priority: Prioridad (menor = mayor prioridad)
            callback: Callback al completar
            **kwargs: Argumentos keyword

        Returns:
            WorkerTask que puede usarse para esperar el resultado
        """
        task = WorkerTask(func, args, kwargs, priority, callback)
        self._task_queue.put((priority, task))
        return task

    def shutdown(self, wait: bool = True):
        """
        Apaga el pool.

        Args:
            wait: Si True, espera a que terminen las tareas
        """
        self._shutdown.set()

        if wait:
            # Wait for queue to empty
            self._task_queue.join()

            # Wait for workers
            for worker in self._workers:
                worker.join(timeout=5.0)

    def clear_pending(self):
        """Limpia las tareas pendientes"""
        while not self._task_queue.empty():
            try:
                self._task_queue.get_nowait()
                self._task_queue.task_done()
            except Empty:
                break


# ============================================================================
# MEMORY MANAGER - Memory optimization and cleanup
# ============================================================================

class MemoryManager:
    """
    Gestor de memoria y limpieza de recursos.

    Características:
    - Monitoreo de uso de memoria
    - Limpieza automática bajo presión
    - Weak references para objetos grandes
    - Garbage collection forzado cuando necesario
    """

    def __init__(self, threshold_mb: int = 500):
        """
        Args:
            threshold_mb: Umbral de memoria en MB para trigger cleanup
        """
        self.threshold = threshold_mb * 1024 * 1024
        self._weak_refs: List[weakref.ref] = []
        self._cleanups: List[Callable] = []
        self._lock = threading.Lock()

    def register_cleanup(self, cleanup_func: Callable):
        """Registra una función de limpieza"""
        with self._lock:
            self._cleanups.append(cleanup_func)

    def register_object(self, obj: Any):
        """Registra un objeto con weak reference"""
        with self._lock:
            self._weak_refs.append(weakref.ref(obj))

    def get_memory_usage(self) -> int:
        """Obtiene el uso de memoria actual en bytes"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss

    def cleanup(self):
        """Ejecuta limpieza de recursos"""
        logger.info("Executing memory cleanup...")

        with self._lock:
            # Execute registered cleanups
            for cleanup in self._cleanups:
                try:
                    cleanup()
                except Exception as e:
                    logger.error(f"Cleanup error: {e}")

            # Clean dead weak references
            self._weak_refs = [ref for ref in self._weak_refs if ref() is not None]

        # Force garbage collection
        import gc
        gc.collect()

        logger.info(f"Memory cleanup complete. Usage: {self.get_memory_usage() / 1024 / 1024:.1f} MB")

    def check_and_cleanup(self):
        """Verifica memoria y limpia si es necesario"""
        current_usage = self.get_memory_usage()
        if current_usage > self.threshold:
            logger.warning(f"Memory threshold exceeded: {current_usage / 1024 / 1024:.1f} MB")
            self.cleanup()


# ============================================================================
# QUERY OPTIMIZER - SQL Query optimization
# ============================================================================

class QueryOptimizer:
    """
    Optimizador de consultas SQL para Windows Search.

    Características:
    - Análisis de queries
    - Sugerencias de índices
    - Reescritura de queries ineficientes
    - Cache de planes de ejecución
    """

    def __init__(self):
        self._query_cache: Dict[str, str] = {}
        self._lock = threading.Lock()

    def optimize_query(self, query: str) -> str:
        """
        Optimiza una query SQL.

        Args:
            query: Query SQL original

        Returns:
            Query optimizada
        """
        # Check cache
        with self._lock:
            if query in self._query_cache:
                return self._query_cache[query]

        optimized = query

        # Optimizations
        optimized = self._add_limits(optimized)
        optimized = self._optimize_wildcards(optimized)
        optimized = self._add_indexes_hints(optimized)

        # Cache result
        with self._lock:
            self._query_cache[query] = optimized

        return optimized

    def _add_limits(self, query: str) -> str:
        """Añade LIMIT si no existe"""
        if 'TOP' not in query.upper() and 'LIMIT' not in query.upper():
            # Insert TOP after SELECT
            import re
            query = re.sub(
                r'SELECT\s+',
                'SELECT TOP 1000 ',
                query,
                flags=re.IGNORECASE
            )
        return query

    def _optimize_wildcards(self, query: str) -> str:
        """Optimiza uso de wildcards"""
        # Convert leading wildcards to more efficient patterns when possible
        # This is a simplified version
        return query

    def _add_indexes_hints(self, query: str) -> str:
        """Añade hints de índices cuando sea beneficioso"""
        # This would require knowledge of available indexes
        return query


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def example_usage():
    """Ejemplo de uso de las optimizaciones"""

    print("=== Smart Search Optimizations Demo ===\n")

    # 1. Results Cache
    print("1. Results Cache:")
    cache = ResultsCache(max_size=100, max_memory_mb=10)

    # Simulate search
    search_params = {'query': 'test', 'path': 'C:\\Users'}
    cache_key = ResultsCache.generate_key(search_params)

    # First search (miss)
    results = cache.get(cache_key)
    print(f"   First access (miss): {results}")

    # Store results
    cache.put(cache_key, ['file1.txt', 'file2.txt', 'file3.txt'])

    # Second search (hit)
    results = cache.get(cache_key)
    print(f"   Second access (hit): {results}")

    stats = cache.get_stats()
    print(f"   Cache stats: {stats}\n")

    # 2. Lazy Directory Loader
    print("2. Lazy Directory Loader:")
    loader = LazyDirectoryLoader(max_depth=2)
    roots = loader.load_root_directories()
    print(f"   Loaded {len(roots)} root directories")
    for root in roots[:3]:
        print(f"   - {root.name}: {root.path}")
    print()

    # 3. Search Indexer
    print("3. Search Indexer:")
    indexer = SearchIndexer()

    # Add documents
    indexer.add_document({'name': 'test.txt', 'path': 'C:\\test.txt', 'content': 'hello world'})
    indexer.add_document({'name': 'data.txt', 'path': 'C:\\data.txt', 'content': 'hello python'})
    indexer.add_document({'name': 'file.py', 'path': 'C:\\file.py', 'content': 'import sys'})

    # Search
    results = indexer.search('hello')
    print(f"   Search 'hello': {len(results)} results")
    for doc_id in results:
        doc = indexer.get_document(doc_id)
        print(f"   - {doc['name']}")
    print()

    # 4. Worker Pool
    print("4. Worker Pool:")
    pool = WorkerPool(num_workers=4)

    def slow_task(n):
        time.sleep(0.1)
        return n * 2

    # Submit tasks
    tasks = []
    for i in range(10):
        task = pool.submit(slow_task, i, priority=i)
        tasks.append(task)

    # Wait for completion
    for task in tasks:
        task.completed.wait()
        print(f"   Task result: {task.result}")

    pool.shutdown()
    print()

    # 5. Memory Manager
    print("5. Memory Manager:")
    mem_manager = MemoryManager(threshold_mb=100)

    cleanup_called = False
    def test_cleanup():
        global cleanup_called
        cleanup_called = True
        print("   Cleanup function called!")

    mem_manager.register_cleanup(test_cleanup)
    mem_manager.cleanup()
    print()

    print("=== Demo Complete ===")


if __name__ == '__main__':
    example_usage()
