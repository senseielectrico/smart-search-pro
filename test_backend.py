"""
Smart Search - Suite de Tests
==============================

Tests unitarios y de integración para el backend.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import time
from datetime import datetime


# Agregar directorio al path
sys.path.insert(0, str(Path(__file__).parent))

from backend import (
    SearchService,
    SearchQuery,
    SearchResult,
    FileCategory,
    FileOperations,
    FallbackSearchEngine,
    FILE_CATEGORY_MAP
)


class TestRunner:
    """Ejecuta y gestiona los tests"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def run_test(self, test_func):
        """Ejecuta un test individual"""
        test_name = test_func.__name__

        try:
            print(f"\n{'=' * 60}")
            print(f"TEST: {test_name}")
            print(f"{'=' * 60}")

            test_func()

            print(f"RESULTADO: PASSED")
            self.passed += 1
            return True

        except AssertionError as e:
            print(f"RESULTADO: FAILED - {e}")
            self.failed += 1
            self.errors.append((test_name, str(e)))
            return False

        except Exception as e:
            print(f"RESULTADO: ERROR - {e}")
            self.failed += 1
            self.errors.append((test_name, f"Error: {e}"))
            return False

    def print_summary(self):
        """Imprime resumen de tests"""
        print(f"\n{'=' * 60}")
        print("RESUMEN DE TESTS")
        print(f"{'=' * 60}")
        print(f"Total: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")

        if self.errors:
            print(f"\nERRORES:")
            for test_name, error in self.errors:
                print(f"  - {test_name}: {error}")

        print(f"{'=' * 60}\n")


# ============================================================================
# TESTS DE MODELOS
# ============================================================================

def test_search_result_creation():
    """Test: Creación de SearchResult"""
    result = SearchResult(
        path=r"C:\test\file.py",
        name="file.py",
        size=1024
    )

    assert result.path == r"C:\test\file.py"
    assert result.name == "file.py"
    assert result.size == 1024
    assert result.extension == ".py"
    assert result.category == FileCategory.CODE

    print("  SearchResult creado correctamente")
    print(f"  Categoría: {result.category.value}")


def test_search_result_classification():
    """Test: Clasificación automática de archivos"""
    test_cases = [
        ("document.pdf", FileCategory.DOCUMENT),
        ("image.png", FileCategory.IMAGE),
        ("video.mp4", FileCategory.VIDEO),
        ("audio.mp3", FileCategory.AUDIO),
        ("script.py", FileCategory.CODE),
        ("archive.zip", FileCategory.ARCHIVE),
        ("program.exe", FileCategory.EXECUTABLE),
        ("data.json", FileCategory.DATA),
        ("unknown.xyz", FileCategory.OTHER),
    ]

    for filename, expected_category in test_cases:
        result = SearchResult(
            path=f"C:\\test\\{filename}",
            name=filename
        )

        assert result.category == expected_category, \
            f"{filename} clasificado como {result.category}, esperado {expected_category}"

        print(f"  {filename} -> {result.category.value} OK")


def test_search_result_to_dict():
    """Test: Conversión a diccionario"""
    result = SearchResult(
        path=r"C:\test\file.txt",
        name="file.txt",
        size=2048,
        modified=datetime.now()
    )

    data = result.to_dict()

    assert isinstance(data, dict)
    assert data['path'] == result.path
    assert data['name'] == result.name
    assert data['size'] == result.size
    assert 'size_formatted' in data

    print("  to_dict() funciona correctamente")
    print(f"  Keys: {list(data.keys())}")


def test_search_query_creation():
    """Test: Creación de SearchQuery"""
    query = SearchQuery(
        keywords=['python', '*.py'],
        search_paths=[r'C:\test']
    )

    assert len(query.keywords) == 2
    assert query.search_paths == [r'C:\test']
    assert query.search_filename is True
    assert query.search_content is False

    print("  SearchQuery creado correctamente")
    print(f"  Keywords: {query.keywords}")


def test_search_query_sql_generation():
    """Test: Generación de SQL"""
    query = SearchQuery(
        keywords=['test'],
        search_paths=[r'C:\Users\Test'],
        max_results=100
    )

    sql = query.build_sql_query()

    assert 'SELECT TOP 100' in sql
    assert 'System.FileName' in sql
    assert 'test' in sql

    print("  SQL generado correctamente")
    print(f"  SQL: {sql[:100]}...")


# ============================================================================
# TESTS DE BÚSQUEDA
# ============================================================================

def test_fallback_search_engine():
    """Test: Motor de búsqueda fallback"""
    # Crear directorio temporal con archivos de prueba
    temp_dir = tempfile.mkdtemp()

    try:
        # Crear archivos de prueba
        test_files = [
            'test_python.py',
            'test_doc.txt',
            'other_file.js',
            'python_script.py',
        ]

        for filename in test_files:
            with open(os.path.join(temp_dir, filename), 'w') as f:
                f.write(f"Test content for {filename}")

        # Crear búsqueda
        query = SearchQuery(
            keywords=['python'],
            search_paths=[temp_dir],
            max_results=10
        )

        # Ejecutar con fallback engine
        engine = FallbackSearchEngine()
        results = engine.search(query)

        # Verificar resultados
        assert len(results) > 0, "No se encontraron resultados"

        python_files = [r for r in results if 'python' in r.name.lower()]
        assert len(python_files) >= 2, f"Esperados 2+ archivos, encontrados {len(python_files)}"

        print(f"  Encontrados: {len(results)} archivos")
        print(f"  Con 'python': {len(python_files)}")

    finally:
        # Limpiar
        shutil.rmtree(temp_dir)


def test_search_service_sync():
    """Test: Búsqueda síncrona"""
    temp_dir = tempfile.mkdtemp()

    try:
        # Crear archivos
        for i in range(5):
            with open(os.path.join(temp_dir, f'file_{i}.txt'), 'w') as f:
                f.write(f"Content {i}")

        # Crear servicio (con fallback)
        service = SearchService(use_windows_search=False)

        # Buscar
        query = SearchQuery(
            keywords=['*.txt'],
            search_paths=[temp_dir]
        )

        results = service.search_sync(query)

        assert len(results) == 5, f"Esperados 5 archivos, encontrados {len(results)}"

        print(f"  Búsqueda síncrona: {len(results)} resultados")

    finally:
        shutil.rmtree(temp_dir)


def test_search_service_async():
    """Test: Búsqueda asíncrona"""
    temp_dir = tempfile.mkdtemp()

    try:
        # Crear archivos
        for i in range(3):
            with open(os.path.join(temp_dir, f'async_{i}.py'), 'w') as f:
                f.write(f"# Python script {i}")

        # Crear servicio
        service = SearchService(use_windows_search=False)

        # Callbacks
        callback_results = []
        completed = [False]

        def on_result(result):
            callback_results.append(result)

        def on_complete(results):
            completed[0] = True

        # Buscar
        query = SearchQuery(
            keywords=['*.py'],
            search_paths=[temp_dir]
        )

        search_id = service.search_async(
            query,
            callback=on_result,
            completion_callback=on_complete
        )

        # Esperar
        timeout = 5
        start = time.time()

        while not completed[0] and (time.time() - start) < timeout:
            time.sleep(0.1)

        assert completed[0], "Búsqueda no completada"
        assert len(callback_results) == 3, f"Esperados 3 callbacks, recibidos {len(callback_results)}"

        print(f"  Búsqueda asíncrona: {search_id}")
        print(f"  Callbacks: {len(callback_results)}")

    finally:
        shutil.rmtree(temp_dir)


def test_search_classification():
    """Test: Clasificación de resultados"""
    temp_dir = tempfile.mkdtemp()

    try:
        # Crear archivos de diferentes tipos
        files = {
            'doc.pdf': FileCategory.DOCUMENT,
            'pic.jpg': FileCategory.IMAGE,
            'script.py': FileCategory.CODE,
            'data.json': FileCategory.DATA,
        }

        for filename in files.keys():
            with open(os.path.join(temp_dir, filename), 'w') as f:
                f.write("test")

        # Buscar
        service = SearchService(use_windows_search=False)

        query = SearchQuery(
            keywords=['*'],
            search_paths=[temp_dir]
        )

        results = service.search_sync(query)

        # Clasificar
        classified = service.classify_results(results)

        # Verificar
        for category, items in classified.items():
            if items:
                print(f"  {category.value}: {len(items)} archivos")

        assert len(results) == len(files), "No todos los archivos encontrados"

    finally:
        shutil.rmtree(temp_dir)


# ============================================================================
# TESTS DE OPERACIONES DE ARCHIVOS
# ============================================================================

def test_file_operations_copy():
    """Test: Copiar archivo"""
    temp_dir = tempfile.mkdtemp()

    try:
        # Crear archivo origen
        source = os.path.join(temp_dir, 'source.txt')
        dest = os.path.join(temp_dir, 'dest.txt')

        with open(source, 'w') as f:
            f.write("Test content")

        # Copiar
        ops = FileOperations()
        result = ops.copy(source, dest)

        assert result is True
        assert os.path.exists(dest), "Archivo destino no existe"

        # Verificar contenido
        with open(dest, 'r') as f:
            content = f.read()

        assert content == "Test content", "Contenido no coincide"

        print("  Archivo copiado correctamente")

    finally:
        shutil.rmtree(temp_dir)


def test_file_operations_move():
    """Test: Mover archivo"""
    temp_dir = tempfile.mkdtemp()

    try:
        # Crear archivo
        source = os.path.join(temp_dir, 'source.txt')
        dest = os.path.join(temp_dir, 'moved.txt')

        with open(source, 'w') as f:
            f.write("Move test")

        # Mover
        ops = FileOperations()
        result = ops.move(source, dest)

        assert result is True
        assert not os.path.exists(source), "Archivo origen aún existe"
        assert os.path.exists(dest), "Archivo destino no existe"

        print("  Archivo movido correctamente")

    finally:
        shutil.rmtree(temp_dir)


def test_file_operations_delete():
    """Test: Eliminar archivo"""
    temp_dir = tempfile.mkdtemp()

    try:
        # Crear archivo
        test_file = os.path.join(temp_dir, 'delete_me.txt')

        with open(test_file, 'w') as f:
            f.write("Delete test")

        assert os.path.exists(test_file)

        # Eliminar permanentemente
        ops = FileOperations()
        result = ops.delete(test_file, permanent=True)

        assert result is True
        assert not os.path.exists(test_file), "Archivo no eliminado"

        print("  Archivo eliminado correctamente")

    finally:
        # Limpiar solo si temp_dir existe
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_file_operations_properties():
    """Test: Obtener propiedades"""
    temp_dir = tempfile.mkdtemp()

    try:
        # Crear archivo
        test_file = os.path.join(temp_dir, 'props.txt')

        with open(test_file, 'w') as f:
            f.write("Property test")

        # Obtener propiedades
        ops = FileOperations()
        props = ops.get_properties(test_file)

        assert isinstance(props, dict)
        assert props['name'] == 'props.txt'
        assert props['size'] > 0
        assert 'created' in props
        assert 'modified' in props

        print(f"  Propiedades obtenidas correctamente")
        print(f"  Size: {props['size']} bytes")

    finally:
        shutil.rmtree(temp_dir)


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Ejecuta todos los tests"""
    print("\n" + "=" * 60)
    print("SMART SEARCH - SUITE DE TESTS")
    print("=" * 60 + "\n")

    runner = TestRunner()

    # Tests de modelos
    print("\n>>> TESTS DE MODELOS")
    runner.run_test(test_search_result_creation)
    runner.run_test(test_search_result_classification)
    runner.run_test(test_search_result_to_dict)
    runner.run_test(test_search_query_creation)
    runner.run_test(test_search_query_sql_generation)

    # Tests de búsqueda
    print("\n>>> TESTS DE BÚSQUEDA")
    runner.run_test(test_fallback_search_engine)
    runner.run_test(test_search_service_sync)
    runner.run_test(test_search_service_async)
    runner.run_test(test_search_classification)

    # Tests de operaciones
    print("\n>>> TESTS DE OPERACIONES DE ARCHIVOS")
    runner.run_test(test_file_operations_copy)
    runner.run_test(test_file_operations_move)
    runner.run_test(test_file_operations_delete)
    runner.run_test(test_file_operations_properties)

    # Resumen
    runner.print_summary()

    return runner.failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
