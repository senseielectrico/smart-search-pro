"""
Smart Search - Comprehensive Test Suite
========================================

Suite completa de tests para Smart Search:
1. Tests Unitarios
2. Tests de Integración
3. Tests de UI (sin PyQt)
4. Tests de Rendimiento

Ejecutar con: python -m pytest tests/test_suite.py -v
O con: python tests/run_tests.py
"""

import sys
import os
import time
import json
import shutil
import tempfile
import threading
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

# Añadir el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

# Imports del proyecto
from backend import SearchResult, SearchQuery
from categories import FileCategory
from classifier import classify_file, get_icon_for_type, format_file_size, format_date
from file_manager import DirectoryNode, DirectoryTree, CheckState, FileOperations
from config import SearchConfig, UIConfig, PerformanceConfig


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir():
    """Crea un directorio temporal para tests"""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def sample_files(temp_dir):
    """Crea archivos de muestra para tests"""
    files = {
        'document.pdf': 1024 * 100,  # 100 KB
        'image.png': 1024 * 500,     # 500 KB
        'video.mp4': 1024 * 1024 * 5,  # 5 MB
        'code.py': 1024 * 10,        # 10 KB
        'archive.zip': 1024 * 200,   # 200 KB
        'text.txt': 1024,            # 1 KB
    }

    created_files = []
    for filename, size in files.items():
        filepath = os.path.join(temp_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(b'0' * size)
        created_files.append(filepath)

    return created_files


@pytest.fixture
def sample_directory_structure(temp_dir):
    """Crea estructura de directorios para tests"""
    structure = {
        'Documents': ['file1.txt', 'file2.pdf'],
        'Images': ['photo1.jpg', 'photo2.png'],
        'Code': ['script.py', 'main.js'],
    }

    for dir_name, files in structure.items():
        dir_path = os.path.join(temp_dir, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        for file in files:
            filepath = os.path.join(dir_path, file)
            with open(filepath, 'w') as f:
                f.write(f"Content of {file}")

    return temp_dir


# ============================================================================
# TESTS UNITARIOS - SearchResult
# ============================================================================

class TestSearchResult:
    """Tests para la clase SearchResult"""

    def test_creation_basic(self):
        """Test: Crear SearchResult básico"""
        result = SearchResult(
            path="C:\\test\\file.txt",
            name="file.txt"
        )
        assert result.path == "C:\\test\\file.txt"
        assert result.name == "file.txt"
        assert result.extension == ".txt"

    def test_classification_document(self):
        """Test: Clasificación automática de documento"""
        result = SearchResult(
            path="C:\\test\\document.pdf",
            name="document.pdf"
        )
        assert result.category == FileCategory.DOCUMENTOS

    def test_classification_image(self):
        """Test: Clasificación automática de imagen"""
        result = SearchResult(
            path="C:\\test\\photo.jpg",
            name="photo.jpg"
        )
        assert result.category == FileCategory.IMAGENES

    def test_classification_code(self):
        """Test: Clasificación automática de código"""
        result = SearchResult(
            path="C:\\test\\script.py",
            name="script.py"
        )
        assert result.category == FileCategory.CODIGO

    def test_size_formatting(self):
        """Test: Formateo de tamaño de archivo"""
        result = SearchResult(
            path="C:\\test\\file.txt",
            name="file.txt",
            size=1024
        )
        # to_dict incluye size_formatted
        data = result.to_dict()
        assert "1.00 KB" == data['size_formatted']

    def test_size_formatting_large(self):
        """Test: Formateo de archivos grandes"""
        result = SearchResult(
            path="C:\\test\\large.dat",
            name="large.dat",
            size=1024 * 1024 * 1024  # 1 GB
        )
        data = result.to_dict()
        assert "1.00 GB" == data['size_formatted']

    def test_to_dict_serialization(self):
        """Test: Serialización a diccionario"""
        result = SearchResult(
            path="C:\\test\\file.txt",
            name="file.txt",
            size=1024,
            modified=datetime(2024, 1, 1, 12, 0, 0)
        )
        data = result.to_dict()

        assert data['path'] == "C:\\test\\file.txt"
        assert data['name'] == "file.txt"
        assert data['size'] == 1024
        assert 'size_formatted' in data
        assert 'modified' in data

    def test_directory_result(self):
        """Test: SearchResult para directorio"""
        result = SearchResult(
            path="C:\\test\\folder",
            name="folder",
            is_directory=True
        )
        assert result.is_directory is True
        assert result.extension == ""


# ============================================================================
# TESTS UNITARIOS - SearchQuery
# ============================================================================

class TestSearchQuery:
    """Tests para la clase SearchQuery"""

    def test_creation_basic(self):
        """Test: Crear SearchQuery básico"""
        query = SearchQuery(keywords=["test"])
        assert query.keywords == ["test"]
        assert query.search_filename is True
        assert query.recursive is True

    def test_keywords_validation(self):
        """Test: Validación de keywords vacíos"""
        with pytest.raises(ValueError):
            SearchQuery(keywords=[])

    def test_keywords_normalization(self):
        """Test: Normalización de keywords"""
        query = SearchQuery(keywords=["  test  ", " query "])
        assert query.keywords == ["test", "query"]

    def test_default_search_paths(self):
        """Test: Paths de búsqueda por defecto"""
        query = SearchQuery(keywords=["test"])
        assert query.search_paths is not None
        assert len(query.search_paths) > 0

    def test_custom_search_paths(self):
        """Test: Paths de búsqueda personalizados"""
        custom_paths = ["C:\\Custom\\Path1", "C:\\Custom\\Path2"]
        query = SearchQuery(
            keywords=["test"],
            search_paths=custom_paths
        )
        assert query.search_paths == custom_paths

    def test_sql_query_building_filename(self):
        """Test: Construcción de consulta SQL para nombre"""
        query = SearchQuery(
            keywords=["test"],
            search_filename=True,
            search_content=False
        )
        sql = query.build_sql_query()
        assert "System.FileName" in sql
        assert "LIKE" in sql

    def test_sql_query_building_content(self):
        """Test: Construcción de consulta SQL para contenido"""
        query = SearchQuery(
            keywords=["test"],
            search_filename=False,
            search_content=True
        )
        sql = query.build_sql_query()
        assert "CONTAINS" in sql

    def test_wildcard_handling(self):
        """Test: Manejo de wildcards en keywords"""
        query = SearchQuery(keywords=["*.txt"])
        sql = query.build_sql_query()
        # El * debe convertirse a % para LIKE
        assert "%" in sql


# ============================================================================
# TESTS UNITARIOS - Classifier
# ============================================================================

class TestClassifier:
    """Tests para funciones de clasificación"""

    def test_classify_document(self):
        """Test: Clasificar documento"""
        category = classify_file("document.pdf")
        assert category == "Documentos"

    def test_classify_image(self):
        """Test: Clasificar imagen"""
        category = classify_file("photo.jpg")
        assert category == "Imágenes"

    def test_classify_video(self):
        """Test: Clasificar video"""
        category = classify_file("movie.mp4")
        assert category == "Videos"

    def test_classify_audio(self):
        """Test: Clasificar audio"""
        category = classify_file("song.mp3")
        assert category == "Audio"

    def test_classify_code(self):
        """Test: Clasificar código"""
        category = classify_file("script.py")
        assert category == "Código"

    def test_classify_unknown(self):
        """Test: Clasificar archivo desconocido"""
        category = classify_file("unknown.xyz")
        assert category == "Otros"

    def test_format_file_size_bytes(self):
        """Test: Formatear tamaño en bytes"""
        formatted = format_file_size(512)
        # Los bytes no tienen decimales
        assert formatted == "512 B"

    def test_format_file_size_kb(self):
        """Test: Formatear tamaño en KB"""
        formatted = format_file_size(1024)
        assert formatted == "1.00 KB"

    def test_format_file_size_mb(self):
        """Test: Formatear tamaño en MB"""
        formatted = format_file_size(1024 * 1024)
        assert formatted == "1.00 MB"

    def test_format_file_size_gb(self):
        """Test: Formatear tamaño en GB"""
        formatted = format_file_size(1024 * 1024 * 1024)
        assert formatted == "1.00 GB"

    def test_format_date(self):
        """Test: Formatear fecha"""
        # format_date espera un timestamp Unix, no un datetime
        timestamp = datetime(2024, 1, 15, 10, 30, 45).timestamp()
        formatted = format_date(timestamp)
        assert "2024" in formatted
        assert "01" in formatted or "15" in formatted


# ============================================================================
# TESTS UNITARIOS - DirectoryTree
# ============================================================================

class TestDirectoryTree:
    """Tests para la clase DirectoryTree"""

    def test_creation(self):
        """Test: Crear DirectoryTree"""
        tree = DirectoryTree()
        assert tree.root_nodes is not None
        assert len(tree.root_nodes) == 0

    def test_add_directory_root(self):
        """Test: Añadir directorio raíz"""
        tree = DirectoryTree()
        node = tree.add_directory("C:\\")
        assert node is not None
        assert node.path == "C:\\"

    def test_add_directory_nested(self):
        """Test: Añadir directorio anidado"""
        tree = DirectoryTree()
        node = tree.add_directory("C:\\Users\\Test\\Documents")
        assert node is not None
        assert node.path == "C:\\Users\\Test\\Documents"

    def test_set_state_node(self):
        """Test: Establecer estado de nodo"""
        tree = DirectoryTree()
        node = tree.add_directory("C:\\Test")
        tree.set_state(node.path, CheckState.CHECKED)
        assert node.state == CheckState.CHECKED

    def test_state_propagation_down(self):
        """Test: Propagación de estado hacia abajo"""
        tree = DirectoryTree()
        parent = tree.add_directory("C:\\Parent")
        child = tree.add_directory("C:\\Parent\\Child")

        tree.set_state(parent.path, CheckState.CHECKED)
        # El hijo debe heredar el estado del padre
        assert child.state == CheckState.CHECKED

    def test_state_propagation_up(self):
        """Test: Propagación de estado hacia arriba"""
        tree = DirectoryTree()
        parent = tree.add_directory("C:\\Parent")
        child1 = tree.add_directory("C:\\Parent\\Child1")
        child2 = tree.add_directory("C:\\Parent\\Child2")

        tree.set_state(child1.path, CheckState.CHECKED)
        tree.set_state(child2.path, CheckState.CHECKED)

        # El padre debe estar marcado si todos los hijos lo están
        assert parent.state == CheckState.CHECKED

    def test_partial_state(self):
        """Test: Estado parcial cuando solo algunos hijos están marcados"""
        tree = DirectoryTree()
        parent = tree.add_directory("C:\\Parent")
        child1 = tree.add_directory("C:\\Parent\\Child1")
        child2 = tree.add_directory("C:\\Parent\\Child2")

        tree.set_state(child1.path, CheckState.CHECKED)
        # Solo un hijo marcado -> padre en estado parcial
        assert parent.state == CheckState.PARTIAL

    def test_get_checked_paths(self):
        """Test: Obtener paths marcados"""
        tree = DirectoryTree()
        tree.add_directory("C:\\Test1")
        tree.add_directory("C:\\Test2")

        tree.set_state("C:\\Test1", CheckState.CHECKED)

        # El método correcto es get_selected_directories
        checked = tree.get_selected_directories()
        assert "C:\\Test1" in checked
        assert "C:\\Test2" not in checked


# ============================================================================
# TESTS UNITARIOS - FileOperations
# ============================================================================

class TestFileOperations:
    """Tests para operaciones de archivos"""

    def test_copy_file(self, temp_dir):
        """Test: Copiar archivo"""
        # Crear archivo fuente
        source = os.path.join(temp_dir, "source.txt")
        with open(source, 'w') as f:
            f.write("test content")

        # Copiar - el destino debe ser el archivo completo, no el directorio
        dest_file = os.path.join(temp_dir, "dest_source.txt")

        ops = FileOperations()
        success = ops.copy_file(source, dest_file)

        assert success is True
        assert os.path.exists(dest_file)

    def test_move_file(self, temp_dir):
        """Test: Mover archivo"""
        # Crear archivo fuente
        source = os.path.join(temp_dir, "source.txt")
        with open(source, 'w') as f:
            f.write("test content")

        # Mover
        dest_dir = os.path.join(temp_dir, "dest")
        os.makedirs(dest_dir, exist_ok=True)

        ops = FileOperations()
        success = ops.move_file(source, dest_dir)

        assert success is True
        assert not os.path.exists(source)
        dest_file = os.path.join(dest_dir, "source.txt")
        assert os.path.exists(dest_file)

    def test_open_file_location(self, temp_dir, sample_files):
        """Test: Abrir ubicación de archivo"""
        ops = FileOperations()

        # Mock del subprocess para evitar abrir explorer
        # El método correcto es open_location, no open_file_location
        with patch('subprocess.run') as mock_run:
            ops.open_location(sample_files[0])
            assert mock_run.called


# ============================================================================
# TESTS UNITARIOS - Cache
# ============================================================================

class TestCache:
    """Tests para sistema de cache"""

    def test_cache_basic(self):
        """Test: SearchService gestiona caché de búsquedas"""
        from backend import SearchService

        service = SearchService(use_windows_search=False)

        # Crear dos búsquedas
        query1 = SearchQuery(keywords=["test"])

        # Mock del motor de búsqueda
        with patch.object(service.engine, 'search') as mock_search:
            mock_search.return_value = [SearchResult(path="C:\\test.txt", name="test.txt")]

            # Primera búsqueda
            search_id = service.search_async(query1)

            # Esperar a que termine
            import time
            time.sleep(0.2)

            # Debe poder recuperar los resultados
            results = service.get_results(search_id)
            assert results is not None
            assert len(results) == 1


# ============================================================================
# TESTS UNITARIOS - Debouncer
# ============================================================================

class TestDebouncer:
    """Tests para mecanismo de debouncing"""

    def test_debouncer_delays_execution(self):
        """Test: Debouncer retrasa la ejecución"""
        call_count = [0]

        def callback():
            call_count[0] += 1

        debouncer = Debouncer(delay_ms=100)

        # Llamar múltiples veces rápidamente
        debouncer.debounce(callback)
        debouncer.debounce(callback)
        debouncer.debounce(callback)

        # No debe ejecutarse inmediatamente
        assert call_count[0] == 0

        # Esperar el delay
        time.sleep(0.15)
        assert call_count[0] == 1  # Solo una ejecución

    def test_debouncer_cancels_previous(self):
        """Test: Debouncer cancela ejecuciones anteriores"""
        results = []

        def callback(value):
            results.append(value)

        debouncer = Debouncer(delay_ms=100)

        debouncer.debounce(lambda: callback(1))
        time.sleep(0.05)
        debouncer.debounce(lambda: callback(2))
        time.sleep(0.05)
        debouncer.debounce(lambda: callback(3))

        time.sleep(0.15)

        # Solo debe ejecutarse la última
        assert len(results) == 1
        assert results[0] == 3


# Implementación simple de Debouncer para tests
class Debouncer:
    """Debouncer simple para tests"""

    def __init__(self, delay_ms):
        self.delay_ms = delay_ms / 1000.0
        self.timer = None

    def debounce(self, callback):
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.delay_ms, callback)
        self.timer.start()


# ============================================================================
# TESTS DE INTEGRACIÓN
# ============================================================================

class TestIntegration:
    """Tests de integración entre componentes"""

    def test_backend_classifier_integration(self, sample_files):
        """Test: Backend + Classifier trabajan juntos"""
        # SearchResult usa el classifier internamente
        for filepath in sample_files:
            name = os.path.basename(filepath)
            result = SearchResult(path=filepath, name=name)

            # Debe tener categoría asignada
            assert result.category is not None
            assert result.category != FileCategory.OTROS or name.endswith('.txt')

    def test_directory_tree_ui_integration(self, sample_directory_structure):
        """Test: DirectoryTree + UI state management"""
        tree = DirectoryTree()

        # Añadir estructura
        for root, dirs, files in os.walk(sample_directory_structure):
            tree.add_directory(root)
            for dir_name in dirs:
                tree.add_directory(os.path.join(root, dir_name))

        # Simular interacción de UI
        docs_path = os.path.join(sample_directory_structure, "Documents")
        tree.set_state(docs_path, CheckState.CHECKED)

        # Usar el método correcto
        checked = tree.get_selected_directories()
        assert docs_path in checked

    def test_search_cache_results_integration(self):
        """Test: Search + Cache + Results"""
        from backend import SearchService

        service = SearchService(use_windows_search=False)

        # Primera búsqueda
        query = SearchQuery(
            keywords=["test"],
            search_paths=[os.path.dirname(__file__)]
        )

        # Mock de la búsqueda real
        with patch.object(service.engine, 'search') as mock_search:
            mock_search.return_value = [
                SearchResult(path="C:\\test1.txt", name="test1.txt"),
                SearchResult(path="C:\\test2.txt", name="test2.txt")
            ]

            # Búsqueda síncrona
            results1 = service.search_sync(query)
            assert len(results1) == 2

            # Segunda búsqueda
            results2 = service.search_sync(query)
            assert len(results2) == 2

            # Cada búsqueda llama al motor (no hay cache automático en sync)
            assert mock_search.call_count == 2


# ============================================================================
# TESTS DE UI (sin PyQt)
# ============================================================================

class TestUIComponents:
    """Tests de componentes UI sin inicializar PyQt"""

    def test_ui_module_imports(self):
        """Test: Módulo UI se puede importar"""
        try:
            import ui
            assert hasattr(ui, 'SmartSearchWindow')
        except ImportError as e:
            pytest.skip(f"PyQt6 no disponible: {e}")

    def test_ui_classes_exist(self):
        """Test: Clases UI existen"""
        try:
            from ui import SmartSearchWindow, SearchWorker, FileOperation, FileType
            assert SmartSearchWindow is not None
            assert SearchWorker is not None
        except ImportError:
            pytest.skip("PyQt6 no disponible")

    def test_file_type_classification(self):
        """Test: FileType.get_category funciona"""
        try:
            from ui import FileType

            assert FileType.get_category("test.pdf") == FileType.DOCUMENTS
            assert FileType.get_category("photo.jpg") == FileType.IMAGES
            assert FileType.get_category("video.mp4") == FileType.VIDEOS
            assert FileType.get_category("song.mp3") == FileType.AUDIO
            assert FileType.get_category("script.py") == FileType.CODE
        except ImportError:
            pytest.skip("PyQt6 no disponible")

    def test_ui_shortcuts_defined(self):
        """Test: Shortcuts están definidos en config"""
        shortcuts = UIConfig.KEYBOARD_SHORTCUTS
        assert 'search' in shortcuts
        assert 'open' in shortcuts
        assert 'copy' in shortcuts


# ============================================================================
# TESTS DE RENDIMIENTO
# ============================================================================

class TestPerformance:
    """Tests de rendimiento del sistema"""

    def test_search_performance_small_dataset(self, sample_files):
        """Test: Búsqueda rápida en dataset pequeño"""
        from backend import SearchService

        service = SearchService(use_windows_search=False)
        query = SearchQuery(
            keywords=["test"],
            search_paths=[os.path.dirname(sample_files[0])]
        )

        start = time.time()
        with patch.object(service.engine, 'search') as mock_search:
            mock_search.return_value = []
            service.search_sync(query)
        end = time.time()

        # Debe ser muy rápido (< 100ms para mock)
        assert (end - start) < 0.1

    def test_cache_improves_performance(self):
        """Test: Cache mejora el rendimiento con búsquedas asíncronas"""
        from backend import SearchService

        service = SearchService(use_windows_search=False)
        query = SearchQuery(keywords=["test"])

        # Simular resultados
        mock_results = [SearchResult(path=f"C:\\test{i}.txt", name=f"test{i}.txt")
                       for i in range(100)]

        with patch.object(service.engine, 'search', return_value=mock_results):
            # Primera búsqueda asíncrona
            start1 = time.time()
            search_id1 = service.search_async(query)
            while service.is_search_active(search_id1):
                time.sleep(0.01)
            time1 = time.time() - start1

            # Segunda búsqueda - recuperar de cache
            start2 = time.time()
            results = service.get_results(search_id1)
            time2 = time.time() - start2

            # Recuperar de cache debe ser más rápido
            assert time2 < time1
            assert len(results) == 100

    def test_memory_usage(self):
        """Test: Uso de memoria bajo límite"""
        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Crear muchos resultados
        results = [
            SearchResult(path=f"C:\\test{i}.txt", name=f"test{i}.txt")
            for i in range(10000)
        ]

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # No debe superar 200 MB adicionales
        assert memory_increase < 200

    def test_large_result_set_handling(self):
        """Test: Manejo de conjuntos grandes de resultados"""
        from backend import SearchService

        service = SearchService(use_windows_search=False)

        # Simular 10000 resultados
        mock_results = [
            SearchResult(path=f"C:\\test{i}.txt", name=f"test{i}.txt")
            for i in range(10000)
        ]

        query = SearchQuery(keywords=["test"], max_results=10000)

        with patch.object(service.engine, 'search', return_value=mock_results):
            start = time.time()
            results = service.search_sync(query)
            duration = time.time() - start

            assert len(results) == 10000
            # Debe procesar 10k resultados en menos de 2 segundos
            assert duration < 2.0

    def test_directory_tree_performance(self):
        """Test: Rendimiento del árbol de directorios"""
        tree = DirectoryTree()

        start = time.time()
        # Añadir 1000 directorios
        for i in range(1000):
            tree.add_directory(f"C:\\Test\\Level1\\Level2\\Dir{i}")
        duration = time.time() - start

        # Debe ser rápido (< 1 segundo para 1000 directorios)
        assert duration < 1.0

    def test_classification_performance(self):
        """Test: Rendimiento de clasificación de archivos"""
        filenames = [f"file{i}.pdf" for i in range(1000)]

        start = time.time()
        for filename in filenames:
            classify_file(filename)
        duration = time.time() - start

        # Clasificar 1000 archivos debe ser muy rápido (< 0.1s)
        assert duration < 0.1


# ============================================================================
# TESTS DE CONFIGURACIÓN
# ============================================================================

class TestConfiguration:
    """Tests de configuración del sistema"""

    def test_search_config_defaults(self):
        """Test: Configuración por defecto"""
        assert SearchConfig.MAX_RESULTS_DEFAULT == 1000
        assert SearchConfig.MAX_CONCURRENT_SEARCHES == 5
        assert SearchConfig.ENABLE_RESULTS_CACHE is True

    def test_ui_config_defaults(self):
        """Test: Configuración UI por defecto"""
        assert UIConfig.THEME in ["dark", "light"]
        assert UIConfig.RESULTS_PER_PAGE > 0

    def test_performance_config_defaults(self):
        """Test: Configuración de rendimiento"""
        assert PerformanceConfig.SEARCH_DEBOUNCE_MS >= 0
        assert PerformanceConfig.MAX_MEMORY_USAGE_MB > 0

    def test_excluded_directories(self):
        """Test: Directorios excluidos"""
        excluded = SearchConfig.EXCLUDED_DIRECTORIES
        assert any("Windows" in path for path in excluded)
        assert any("Program Files" in path for path in excluded)


# ============================================================================
# TESTS DE ROBUSTEZ
# ============================================================================

class TestRobustness:
    """Tests de robustez y manejo de errores"""

    def test_handle_missing_file(self):
        """Test: Manejar archivo que no existe"""
        ops = FileOperations()
        success = ops.copy_file("C:\\nonexistent.txt", "C:\\dest")
        assert success is False

    def test_handle_invalid_path(self):
        """Test: Manejar path inválido"""
        tree = DirectoryTree()
        # Path vacío debe lanzar IndexError o manejarse
        # Actualizar para verificar que se maneja apropiadamente
        with pytest.raises(IndexError):
            node = tree.add_directory("")

    def test_handle_empty_search(self):
        """Test: Manejar búsqueda vacía"""
        with pytest.raises(ValueError):
            SearchQuery(keywords=[])

    def test_thread_safety(self):
        """Test: Thread safety del DirectoryTree"""
        tree = DirectoryTree()
        errors = []

        def add_dirs():
            try:
                for i in range(100):
                    tree.add_directory(f"C:\\Test{threading.current_thread().ident}\\Dir{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=add_dirs) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # No debe haber errores de concurrencia
        assert len(errors) == 0


# ============================================================================
# SUMMARY REPORTER
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def test_summary(request):
    """Genera resumen de tests al finalizar"""
    yield

    if hasattr(request.config, 'pluginmanager'):
        stats = request.config.pluginmanager.get_plugin('terminalreporter').stats

        passed = len(stats.get('passed', []))
        failed = len(stats.get('failed', []))
        skipped = len(stats.get('skipped', []))

        print("\n" + "="*70)
        print("RESUMEN DE TESTS")
        print("="*70)
        print(f"PASSED:  {passed}")
        print(f"FAILED:  {failed}")
        print(f"SKIPPED: {skipped}")
        print(f"TOTAL:   {passed + failed + skipped}")
        print("="*70)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
