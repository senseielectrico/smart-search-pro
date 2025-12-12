"""
Smart Search - Optimized Integration Example
============================================

Ejemplo de integración de las optimizaciones con el código existente.

Este módulo muestra cómo integrar:
- ResultsCache en SearchService
- LazyDirectoryLoader en DirectoryTreeWidget
- VirtualTableModel en ResultsTableWidget
- SearchDebouncer en la UI
- WorkerPool para operaciones paralelas
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime

# Import existing modules
try:
    from backend import SearchService, SearchQuery, SearchResult, FileCategory
    from ui import SmartSearchWindow, DirectoryTreeWidget, ResultsTableWidget
    from optimizations import (
        ResultsCache, LazyDirectoryLoader, SearchDebouncer,
        VirtualTableModel, SearchIndexer, WorkerPool, MemoryManager,
        QueryOptimizer
    )
    HAS_DEPENDENCIES = True
except ImportError as e:
    print(f"Warning: Missing dependencies: {e}")
    HAS_DEPENDENCIES = False

try:
    from PyQt6.QtWidgets import QApplication, QTableView
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal
    HAS_PYQT6 = True
except ImportError:
    HAS_PYQT6 = False


# ============================================================================
# OPTIMIZED SEARCH SERVICE
# ============================================================================

class OptimizedSearchService:
    """
    SearchService mejorado con cache y optimizaciones.

    Mejoras:
    - Cache LRU de resultados
    - Indexador para búsquedas incrementales
    - Worker pool para operaciones paralelas
    - Gestión de memoria
    """

    def __init__(self, use_windows_search: bool = True):
        """Inicializa el servicio optimizado"""
        # Original service
        if HAS_DEPENDENCIES:
            self.service = SearchService(use_windows_search)

        # Optimizations
        self.cache = ResultsCache(
            max_size=500,
            max_memory_mb=50,
            ttl_seconds=300
        )

        self.indexer = SearchIndexer()
        self.worker_pool = WorkerPool(num_workers=4)
        self.memory_manager = MemoryManager(threshold_mb=200)
        self.query_optimizer = QueryOptimizer()

        # Register cleanup
        self.memory_manager.register_cleanup(self.cache.clear)
        self.memory_manager.register_cleanup(self.indexer.clear)

    def search(self, query: SearchQuery,
               use_cache: bool = True,
               callback: Optional[callable] = None) -> List[SearchResult]:
        """
        Búsqueda optimizada con cache.

        Args:
            query: Query de búsqueda
            use_cache: Si usar cache
            callback: Callback para resultados

        Returns:
            Lista de resultados
        """
        # Generate cache key
        cache_params = {
            'keywords': str(query.keywords),
            'paths': str(query.search_paths),
            'content': query.search_content,
            'filename': query.search_filename,
            'max_results': query.max_results
        }
        cache_key = ResultsCache.generate_key(cache_params)

        # Try cache first
        if use_cache:
            cached_results = self.cache.get(cache_key)
            if cached_results is not None:
                print(f"Cache HIT: {len(cached_results)} results")
                return cached_results

        # Optimize query SQL
        if hasattr(query, 'build_sql_query'):
            original_sql = query.build_sql_query()
            optimized_sql = self.query_optimizer.optimize_query(original_sql)
            # Note: Would need to inject optimized SQL back into query

        # Execute search
        print("Cache MISS: Executing search...")
        results = self.service.search_sync(query, callback)

        # Store in cache
        if use_cache:
            self.cache.put(cache_key, results)

        # Index results for fast subsequent searches
        for i, result in enumerate(results):
            self.indexer.add_document({
                'name': result.name,
                'path': result.path,
                'extension': result.extension,
                'category': result.category.value
            }, doc_id=i)

        # Check memory
        self.memory_manager.check_and_cleanup()

        return results

    def incremental_search(self, partial_query: str,
                          previous_results: List[SearchResult]) -> List[SearchResult]:
        """
        Búsqueda incremental sobre resultados previos.

        Args:
            partial_query: Query parcial
            previous_results: Resultados previos a filtrar

        Returns:
            Resultados filtrados
        """
        # Use indexer for fast filtering
        matching_ids = self.indexer.search(partial_query)

        filtered = []
        for doc_id in matching_ids:
            if doc_id < len(previous_results):
                filtered.append(previous_results[doc_id])

        return filtered

    def parallel_file_operations(self, files: List[str],
                                 operation: callable,
                                 progress_callback: Optional[callable] = None):
        """
        Ejecuta operaciones de archivos en paralelo.

        Args:
            files: Lista de archivos
            operation: Función a ejecutar en cada archivo
            progress_callback: Callback de progreso
        """
        tasks = []

        for i, file_path in enumerate(files):
            def task_wrapper(path=file_path, index=i):
                result = operation(path)
                if progress_callback:
                    progress_callback(index, len(files), path)
                return result

            task = self.worker_pool.submit(task_wrapper, priority=i)
            tasks.append(task)

        # Wait for all tasks
        results = []
        for task in tasks:
            task.completed.wait()
            results.append(task.result)

        return results

    def get_cache_stats(self) -> Dict:
        """Obtiene estadísticas del cache"""
        return self.cache.get_stats()

    def cleanup(self):
        """Limpia recursos"""
        self.worker_pool.shutdown()
        self.memory_manager.cleanup()


# ============================================================================
# OPTIMIZED DIRECTORY TREE WIDGET
# ============================================================================

if HAS_PYQT6 and HAS_DEPENDENCIES:
    from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem

    class OptimizedDirectoryTreeWidget(QTreeWidget):
        """
        DirectoryTreeWidget optimizado con lazy loading.

        Mejoras:
        - Carga perezosa de directorios
        - Solo carga cuando se expande
        - Cache de nodos cargados
        - Reducción de memoria
        """

        def __init__(self, parent=None):
            super().__init__(parent)

            self.setHeaderLabel("Directories (Lazy Loaded)")
            self.setMinimumWidth(250)

            # Lazy loader
            self.loader = LazyDirectoryLoader(
                max_depth=3,
                max_children=100
            )

            # Connect expansion signal
            self.itemExpanded.connect(self._on_item_expanded)

            # Initialize with roots only
            self._populate_roots()

        def _populate_roots(self):
            """Puebla solo los directorios raíz"""
            roots = self.loader.load_root_directories()

            for node in roots:
                item = QTreeWidgetItem([node.name])
                item.setCheckState(0, Qt.CheckState.Unchecked)
                item.setData(0, Qt.ItemDataRole.UserRole, node.path)
                item.setToolTip(0, node.path)

                # Add dummy child to show expand arrow
                dummy = QTreeWidgetItem(['Loading...'])
                item.addChild(dummy)

                self.addTopLevelItem(item)

        def _on_item_expanded(self, item: QTreeWidgetItem):
            """Carga hijos cuando se expande un item"""
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if not path:
                return

            # Check if already loaded
            if item.childCount() == 1:
                first_child = item.child(0)
                if first_child.text(0) == 'Loading...':
                    # Not loaded yet, load now
                    item.removeChild(first_child)
                    self._load_children(item, path)

        def _load_children(self, parent_item: QTreeWidgetItem, path: str):
            """Carga los hijos de un directorio"""
            # Get cached node or create new
            node = self.loader.get_cached_node(path)
            if node is None:
                from optimizations import LazyDirectoryNode, DirectoryLoadState
                node = LazyDirectoryNode(path=path, name=os.path.basename(path))

            # Load children
            children = self.loader.load_children(node)

            for child_node in children:
                child_item = QTreeWidgetItem([child_node.name])
                child_item.setCheckState(0, Qt.CheckState.Unchecked)
                child_item.setData(0, Qt.ItemDataRole.UserRole, child_node.path)
                child_item.setToolTip(0, child_node.path)

                # Add dummy if might have children
                try:
                    if os.path.isdir(child_node.path):
                        dummy = QTreeWidgetItem(['Loading...'])
                        child_item.addChild(dummy)
                except:
                    pass

                parent_item.addChild(child_item)


# ============================================================================
# OPTIMIZED RESULTS TABLE WIDGET
# ============================================================================

if HAS_PYQT6:
    class OptimizedResultsTable(QTableView):
        """
        Tabla de resultados optimizada con virtual scrolling.

        Mejoras:
        - Virtual scrolling para millones de filas
        - Solo renderiza filas visibles
        - Ordenamiento eficiente
        - Filtrado rápido
        """

        def __init__(self, parent=None):
            super().__init__(parent)

            # Create virtual model
            headers = ['Name', 'Path', 'Size', 'Modified', 'Type']
            self.model = VirtualTableModel(headers, page_size=100)
            self.setModel(self.model)

            # Configure view
            self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
            self.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
            self.setAlternatingRowColors(True)
            self.setSortingEnabled(True)

            # Optimize for large datasets
            self.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
            self.setHorizontalScrollMode(QTableView.ScrollMode.ScrollPerPixel)

        def add_result(self, result: 'SearchResult'):
            """Añade un resultado a la tabla"""
            row_data = {
                'Name': result.name,
                'Path': result.path,
                'Size': result.size,
                'Modified': result.modified,
                'Type': result.extension.upper() if result.extension else 'FILE'
            }
            self.model.add_row(row_data)

        def add_results_batch(self, results: List['SearchResult']):
            """Añade múltiples resultados eficientemente"""
            rows = []
            for result in results:
                row_data = {
                    'Name': result.name,
                    'Path': result.path,
                    'Size': result.size,
                    'Modified': result.modified,
                    'Type': result.extension.upper() if result.extension else 'FILE'
                }
                rows.append(row_data)

            self.model.add_rows(rows)

        def filter_results(self, filter_text: str):
            """Filtra resultados"""
            if not filter_text:
                self.model.clear_filter()
                return

            filter_lower = filter_text.lower()

            def predicate(row: Dict) -> bool:
                name = str(row.get('Name', '')).lower()
                path = str(row.get('Path', '')).lower()
                return filter_lower in name or filter_lower in path

            self.model.filter(predicate)

        def clear(self):
            """Limpia la tabla"""
            self.model.clear()


# ============================================================================
# OPTIMIZED MAIN WINDOW
# ============================================================================

if HAS_PYQT6 and HAS_DEPENDENCIES:
    from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QSplitter

    class OptimizedSmartSearchWindow(QMainWindow):
        """
        Ventana principal optimizada con todas las mejoras.

        Mejoras:
        - Debounce en búsqueda en tiempo real
        - Virtual table para resultados
        - Lazy loading de directorios
        - Cache de búsquedas
        - Gestión de memoria
        """

        def __init__(self):
            super().__init__()

            # Optimized components
            self.search_service = OptimizedSearchService()
            self.search_debouncer = SearchDebouncer(
                debounce_ms=300,
                throttle_ms=500
            )

            # Connect debouncer
            self.search_debouncer.search_triggered.connect(self._execute_search)

            self._init_ui()

            # Memory monitoring
            self.memory_timer = QTimer()
            self.memory_timer.timeout.connect(self._check_memory)
            self.memory_timer.start(30000)  # Every 30 seconds

        def _init_ui(self):
            """Inicializa la UI"""
            self.setWindowTitle("Smart Search - Optimized")
            self.setMinimumSize(1200, 700)

            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QVBoxLayout(central_widget)

            # Search bar
            search_layout = QHBoxLayout()

            search_label = QLabel("Search:")
            search_layout.addWidget(search_label)

            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Type to search (with debounce)...")
            self.search_input.textChanged.connect(self._on_search_text_changed)
            search_layout.addWidget(self.search_input, stretch=3)

            self.search_btn = QPushButton("Search")
            self.search_btn.clicked.connect(self._start_search)
            search_layout.addWidget(self.search_btn)

            self.stats_label = QLabel("Cache: 0% hit rate")
            search_layout.addWidget(self.stats_label)

            main_layout.addLayout(search_layout)

            # Splitter
            splitter = QSplitter(Qt.Orientation.Horizontal)

            # Optimized directory tree
            self.dir_tree = OptimizedDirectoryTreeWidget()
            splitter.addWidget(self.dir_tree)

            # Optimized results table
            self.results_table = OptimizedResultsTable()
            splitter.addWidget(self.results_table)

            splitter.setStretchFactor(0, 1)
            splitter.setStretchFactor(1, 3)

            main_layout.addWidget(splitter)

            # Status
            self.status_label = QLabel("Ready")
            main_layout.addWidget(self.status_label)

        def _on_search_text_changed(self, text: str):
            """Maneja cambios en el texto de búsqueda (con debounce)"""
            if len(text) >= 3:  # Minimum 3 characters
                self.search_debouncer.search(text)

        def _start_search(self):
            """Inicia búsqueda manual"""
            text = self.search_input.text().strip()
            if text:
                self._execute_search(text, {})

        def _execute_search(self, query_text: str, params: Dict):
            """Ejecuta la búsqueda optimizada"""
            self.status_label.setText(f"Searching for: {query_text}...")

            # Get selected paths
            selected_paths = self.dir_tree.get_selected_paths() if hasattr(self.dir_tree, 'get_selected_paths') else []
            if not selected_paths:
                # Use default paths
                user_profile = os.environ.get('USERPROFILE', '')
                selected_paths = [
                    os.path.join(user_profile, 'Documents'),
                    os.path.join(user_profile, 'Desktop'),
                    os.path.join(user_profile, 'Downloads')
                ]

            # Create query
            from backend import SearchQuery
            query = SearchQuery(
                keywords=[query_text],
                search_paths=selected_paths,
                search_filename=True,
                max_results=1000
            )

            # Clear previous results
            self.results_table.clear()

            # Execute search with cache
            results = self.search_service.search(
                query,
                use_cache=True,
                callback=None
            )

            # Add results in batch
            self.results_table.add_results_batch(results)

            # Update status
            self.status_label.setText(f"Found {len(results)} results")

            # Update cache stats
            stats = self.search_service.get_cache_stats()
            self.stats_label.setText(
                f"Cache: {stats['hit_rate']:.1f}% hit rate, "
                f"{stats['size']}/{stats['max_size']} entries"
            )

        def _check_memory(self):
            """Verifica y limpia memoria si es necesario"""
            self.search_service.memory_manager.check_and_cleanup()

        def closeEvent(self, event):
            """Limpia recursos al cerrar"""
            self.search_service.cleanup()
            super().closeEvent(event)


# ============================================================================
# BENCHMARK AND TESTING
# ============================================================================

def benchmark_optimizations():
    """Benchmark de las optimizaciones"""
    import time

    print("\n=== Smart Search Optimizations Benchmark ===\n")

    # 1. Cache Performance
    print("1. Cache Performance Test:")
    cache = ResultsCache(max_size=1000)

    # Generate test data
    test_queries = [
        {'q': f'test{i}', 'path': 'C:\\Users'}
        for i in range(100)
    ]

    # First pass (all misses)
    start = time.time()
    for params in test_queries:
        key = ResultsCache.generate_key(params)
        result = cache.get(key)
        if result is None:
            cache.put(key, ['file1.txt', 'file2.txt'])
    first_pass_time = time.time() - start

    # Second pass (all hits)
    start = time.time()
    for params in test_queries:
        key = ResultsCache.generate_key(params)
        result = cache.get(key)
    second_pass_time = time.time() - start

    speedup = first_pass_time / second_pass_time if second_pass_time > 0 else 0
    print(f"   First pass (misses): {first_pass_time*1000:.2f}ms")
    print(f"   Second pass (hits): {second_pass_time*1000:.2f}ms")
    print(f"   Speedup: {speedup:.2f}x")

    stats = cache.get_stats()
    print(f"   Hit rate: {stats['hit_rate']:.1f}%\n")

    # 2. Virtual Table Performance
    if HAS_PYQT6:
        print("2. Virtual Table Model Test:")
        model = VirtualTableModel(['Name', 'Path', 'Size'])

        # Add large dataset
        start = time.time()
        large_dataset = [
            {'Name': f'file{i}.txt', 'Path': f'C:\\Users\\file{i}.txt', 'Size': i * 1024}
            for i in range(10000)
        ]
        model.add_rows(large_dataset)
        add_time = time.time() - start

        print(f"   Added 10,000 rows in {add_time*1000:.2f}ms")
        print(f"   Memory efficient: Only visible rows rendered\n")

    # 3. Search Indexer Performance
    print("3. Search Indexer Test:")
    indexer = SearchIndexer()

    # Add documents
    start = time.time()
    for i in range(1000):
        indexer.add_document({
            'name': f'file{i}.txt',
            'content': f'content {i % 100} test data'
        })
    index_time = time.time() - start

    # Search
    start = time.time()
    results = indexer.search('test data')
    search_time = time.time() - start

    print(f"   Indexed 1,000 documents in {index_time*1000:.2f}ms")
    print(f"   Search completed in {search_time*1000:.2f}ms")
    print(f"   Found {len(results)} results\n")

    # 4. Worker Pool Performance
    print("4. Worker Pool Test:")
    pool = WorkerPool(num_workers=4)

    def cpu_task(n):
        # Simulate work
        total = 0
        for i in range(n):
            total += i
        return total

    # Sequential
    start = time.time()
    sequential_results = [cpu_task(10000) for _ in range(20)]
    sequential_time = time.time() - start

    # Parallel
    start = time.time()
    tasks = [pool.submit(cpu_task, 10000) for _ in range(20)]
    for task in tasks:
        task.completed.wait()
    parallel_time = time.time() - start

    speedup = sequential_time / parallel_time if parallel_time > 0 else 0
    print(f"   Sequential: {sequential_time*1000:.2f}ms")
    print(f"   Parallel (4 workers): {parallel_time*1000:.2f}ms")
    print(f"   Speedup: {speedup:.2f}x\n")

    pool.shutdown()

    print("=== Benchmark Complete ===\n")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Función principal"""

    # Run benchmark
    benchmark_optimizations()

    # Launch optimized UI
    if HAS_PYQT6 and HAS_DEPENDENCIES:
        print("Launching optimized Smart Search UI...")
        app = QApplication(sys.argv)
        window = OptimizedSmartSearchWindow()
        window.show()
        sys.exit(app.exec())
    else:
        print("PyQt6 or dependencies not available. Skipping UI.")


if __name__ == '__main__':
    main()
