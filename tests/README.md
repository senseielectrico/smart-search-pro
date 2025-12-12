# Smart Search - Test Suite

Suite completa de tests para Smart Search con cobertura exhaustiva de todos los componentes.

## Estructura

```
tests/
├── __init__.py          # Inicialización del paquete
├── test_suite.py        # Suite completa de tests
├── run_tests.py         # Runner con múltiples opciones
└── README.md            # Esta documentación
```

## Categorías de Tests

### 1. Tests Unitarios (70%)

Tests aislados de componentes individuales:

- **SearchResult**: Construcción, clasificación, serialización
- **SearchQuery**: Validación, normalización, construcción SQL
- **Classifier**: Clasificación de archivos, formateo
- **DirectoryTree**: Gestión de árbol, propagación de estados
- **FileOperations**: Copiar, mover, abrir archivos
- **Cache**: Almacenamiento y recuperación
- **Debouncer**: Timing y cancelación

### 2. Tests de Integración (20%)

Tests de interacción entre componentes:

- Backend + Classifier
- DirectoryTree + UI state management
- Search + Cache + Results
- File operations end-to-end

### 3. Tests de UI (5%)

Tests de componentes UI sin PyQt:

- Validación de existencia de clases
- FileType classification
- Keyboard shortcuts
- Signal/slot definitions

### 4. Tests de Rendimiento (5%)

Tests de performance y límites:

- Tiempo de búsqueda < 2s para 1000 archivos
- Cache hit mejora performance
- Memoria no supera 200MB
- Manejo de 10k resultados
- DirectoryTree con 1000+ nodos

## Instalación de Dependencias

```bash
# Instalar dependencias de testing
pip install pytest pytest-cov pytest-html psutil

# Verificar instalación
python tests/run_tests.py --check-deps
```

## Uso

### Ejecución Básica

```bash
# Ejecutar todos los tests
pytest tests/test_suite.py -v

# O con el runner
python tests/run_tests.py
```

### Opciones del Runner

```bash
# Solo tests unitarios
python tests/run_tests.py --unit

# Solo tests de integración
python tests/run_tests.py --integration

# Solo tests de rendimiento
python tests/run_tests.py --performance

# Solo tests de UI
python tests/run_tests.py --ui

# Test rápido de verificación
python tests/run_tests.py --quick

# Con reporte de cobertura
python tests/run_tests.py --coverage

# Con reporte HTML
python tests/run_tests.py --html

# Modo silencioso
python tests/run_tests.py -q

# Verificar dependencias
python tests/run_tests.py --check-deps
```

### Usando pytest directamente

```bash
# Verbose
pytest tests/test_suite.py -v

# Con cobertura
pytest tests/test_suite.py --cov=. --cov-report=html

# Test específico
pytest tests/test_suite.py::TestSearchResult::test_creation_basic -v

# Por categoría (usando markers implícitos)
pytest tests/test_suite.py -k "Test and not Integration" -v  # Solo unitarios
pytest tests/test_suite.py -k "Integration" -v               # Solo integración
pytest tests/test_suite.py -k "Performance" -v               # Solo performance

# Con HTML report
pytest tests/test_suite.py --html=report.html --self-contained-html

# Parallel execution (requiere pytest-xdist)
pytest tests/test_suite.py -n auto
```

## Cobertura de Tests

La suite está diseñada para lograr:

- **Cobertura de líneas**: > 80%
- **Cobertura de funciones**: > 80%
- **Cobertura de branches**: > 70%

### Generar Reporte de Cobertura

```bash
# Generar reporte completo
python tests/run_tests.py --coverage

# El reporte HTML estará en: coverage_html/index.html
```

## Benchmarks de Rendimiento

Los tests de rendimiento validan:

| Métrica | Límite | Test |
|---------|--------|------|
| Búsqueda pequeña | < 2s | `test_search_performance_small_dataset` |
| Cache speedup | 2x más rápido | `test_cache_improves_performance` |
| Memoria | < 200 MB | `test_memory_usage` |
| 10k resultados | < 2s | `test_large_result_set_handling` |
| 1000 directorios | < 1s | `test_directory_tree_performance` |
| 1000 clasificaciones | < 0.1s | `test_classification_performance` |

## Estructura de Tests

Cada test sigue el patrón AAA (Arrange-Act-Assert):

```python
def test_example(self):
    """Test: Descripción clara del objetivo"""
    # Arrange: Preparar datos y estado
    query = SearchQuery(keywords=["test"])

    # Act: Ejecutar la acción
    result = backend.search(query)

    # Assert: Verificar resultados
    assert len(result) > 0
```

## Fixtures Disponibles

```python
# Directorio temporal
def test_example(temp_dir):
    # temp_dir es un Path a directorio temporal limpio
    pass

# Archivos de muestra
def test_example(sample_files):
    # sample_files es una lista de paths a archivos test
    pass

# Estructura de directorios
def test_example(sample_directory_structure):
    # sample_directory_structure es un árbol de directorios
    pass
```

## Mocking

Los tests usan `unittest.mock` para aislar componentes:

```python
from unittest.mock import Mock, patch, MagicMock

# Mock de método
with patch.object(backend, '_execute_search') as mock_search:
    mock_search.return_value = []
    backend.search(query)

# Mock de subprocess
with patch('subprocess.Popen') as mock_popen:
    ops.open_file_location(file_path)
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-html psutil
    - name: Run tests
      run: python tests/run_tests.py --coverage
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
```

## Troubleshooting

### Imports fallan

```bash
# Asegurarse de estar en el directorio correcto
cd C:\Users\ramos\.local\bin\smart_search

# Verificar PYTHONPATH
set PYTHONPATH=%CD%
python tests/run_tests.py
```

### PyQt6 no disponible

Los tests de UI se saltarán automáticamente si PyQt6 no está instalado:

```python
pytest.skip("PyQt6 no disponible")
```

### Tests de rendimiento fallan

Los límites de rendimiento pueden variar según hardware. Ajustar en `test_suite.py`:

```python
# Cambiar de:
assert duration < 2.0

# A:
assert duration < 5.0  # Más permisivo
```

### Problemas de permisos

Ejecutar como administrador si hay errores de permisos en operaciones de archivos.

## Contribuir Tests

### Template para nuevo test

```python
class TestNewComponent:
    """Tests para NuevoComponente"""

    def test_basic_functionality(self):
        """Test: Funcionalidad básica"""
        # Arrange
        component = NewComponent()

        # Act
        result = component.do_something()

        # Assert
        assert result is not None

    def test_edge_case(self):
        """Test: Caso límite específico"""
        # ...
```

### Checklist para PR

- [ ] Tests pasan localmente: `python tests/run_tests.py`
- [ ] Cobertura > 80%: `python tests/run_tests.py --coverage`
- [ ] Sin warnings de pytest
- [ ] Documentación actualizada
- [ ] Tests de rendimiento dentro de límites

## Comandos Rápidos

```bash
# Todo en uno: verificar, ejecutar, reportar
python tests/run_tests.py --coverage --html

# Solo lo esencial (CI/CD)
pytest tests/test_suite.py --tb=short -q

# Debug de test específico
pytest tests/test_suite.py::TestSearchResult::test_creation_basic -vv --tb=long

# Ver warnings
pytest tests/test_suite.py -v -W all

# Ejecutar tests que fallaron anteriormente
pytest tests/test_suite.py --lf  # last failed

# Stop en primer fallo
pytest tests/test_suite.py -x
```

## Métricas Actuales

```
Total Tests: 60+
├── Unitarios: 42
├── Integración: 10
├── UI: 4
├── Rendimiento: 6
└── Configuración/Robustez: 8

Cobertura esperada: > 80%
Tiempo de ejecución: < 30s
```

## Recursos

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [psutil Documentation](https://psutil.readthedocs.io/)

## Licencia

Los tests están bajo la misma licencia que Smart Search.
