# Smart Search - Suite de Tests

## Descripción General

Suite completa de tests para Smart Search con cobertura de:
- Tests Unitarios
- Tests de Integración
- Tests de Seguridad
- Tests de Rendimiento
- Tests de UI (sin PyQt)

## Estructura de Tests

```
tests/
├── conftest.py              # Fixtures compartidos y configuración
├── test_mocks.py           # Mocks para Windows APIs
├── test_suite.py           # Suite principal de tests
├── test_utils.py           # Tests de funciones de utilidad
├── test_security.py        # Tests de seguridad
└── README_TESTS.md         # Esta documentación
```

## Ejecutar Tests

### Todos los tests
```bash
python -m pytest tests/ -v
```

### Tests específicos
```bash
# Solo tests unitarios
python -m pytest tests/test_suite.py::TestSearchResult -v

# Solo tests de utilidades
python -m pytest tests/test_utils.py -v

# Solo tests de seguridad
python -m pytest tests/test_security.py -v
```

### Con cobertura
```bash
python run_tests_with_coverage.py
```

O directamente:
```bash
python -m pytest tests/ --cov=. --cov-report=html --cov-report=term-missing
```

### Tests por categoría
```bash
# Tests rápidos (unit)
python -m pytest tests/ -m unit

# Tests de integración
python -m pytest tests/ -m integration

# Tests de performance
python -m pytest tests/ -m performance

# Tests de seguridad
python -m pytest tests/ -k security
```

## Categorías de Tests

### 1. Tests Unitarios (test_suite.py)

#### SearchResult
- `test_creation_basic` - Creación básica
- `test_classification_*` - Clasificación por tipo
- `test_size_formatting` - Formateo de tamaños
- `test_to_dict_serialization` - Serialización

#### SearchQuery
- `test_creation_basic` - Creación básica
- `test_keywords_validation` - Validación de keywords
- `test_sql_query_building_*` - Construcción de queries SQL
- `test_wildcard_handling` - Manejo de wildcards

#### DirectoryTree
- `test_creation` - Creación del árbol
- `test_add_directory_*` - Añadir directorios
- `test_state_propagation_*` - Propagación de estados
- `test_get_checked_paths` - Obtener paths marcados

#### FileOperations
- `test_copy_file` - Copiar archivos
- `test_move_file` - Mover archivos
- `test_open_file_location` - Abrir ubicación

#### Cache
- `test_cache_basic` - Funcionamiento básico del caché

#### Debouncer
- `test_debouncer_delays_execution` - Retraso de ejecución
- `test_debouncer_cancels_previous` - Cancelación de anteriores

### 2. Tests de Integración (test_suite.py)

- `test_backend_classifier_integration` - Backend + Classifier
- `test_directory_tree_ui_integration` - DirectoryTree + UI
- `test_search_cache_results_integration` - Search + Cache + Results

### 3. Tests de Rendimiento (test_suite.py)

- `test_search_performance_small_dataset` - Performance en dataset pequeño
- `test_cache_improves_performance` - Mejora por caché
- `test_memory_usage` - Uso de memoria
- `test_large_result_set_handling` - Manejo de resultados grandes
- `test_directory_tree_performance` - Performance del árbol
- `test_classification_performance` - Performance de clasificación

### 4. Tests de Utilidades (test_utils.py)

#### format_file_size
- Tests de formateo para bytes, KB, MB, GB, TB, PB
- Tests de valores negativos y flotantes
- Tests de valores límite
- Tests de consistencia

#### format_date
- Tests con timestamps válidos
- Tests con epoch time
- Tests con fechas futuras
- Tests con valores inválidos
- Tests de consistencia

#### Performance
- `test_format_file_size_performance` - 10k formatos en < 0.1s
- `test_format_date_performance` - 10k formatos en < 0.5s

### 5. Tests de Seguridad (test_security.py)

#### SQL Injection Prevention
- `test_sql_injection_in_keywords` - Keywords maliciosos bloqueados
- `test_sql_injection_in_paths` - Paths maliciosos bloqueados
- `test_wildcard_sanitization` - Wildcards sanitizados
- `test_special_chars_in_filename_search` - Caracteres especiales manejados

#### Path Traversal Prevention
- `test_path_traversal_attempts` - Intentos de traversal bloqueados
- `test_protected_paths_cannot_be_destination` - Paths protegidos
- `test_relative_path_resolution` - Resolución de paths relativos
- `test_symlink_handling` - Manejo de symlinks

#### Input Validation
- `test_empty_keywords_rejected` - Keywords vacíos rechazados
- `test_null_bytes_in_paths` - Null bytes manejados
- `test_extremely_long_paths` - Paths largos manejados
- `test_unicode_in_paths` - Unicode en paths
- `test_control_characters_in_keywords` - Caracteres de control
- `test_max_results_validation` - Validación de max_results

#### Dangerous Operations
- `test_cannot_delete_system_directories` - Directorios del sistema protegidos
- `test_cannot_move_to_protected_locations` - Ubicaciones protegidas

#### Race Conditions
- `test_concurrent_file_operations` - Operaciones concurrentes seguras
- `test_directory_tree_thread_safety` - Thread-safety del árbol

#### Search Security
- `test_search_respects_permissions` - Respeto de permisos
- `test_no_command_injection_in_file_operations` - No inyección de comandos
- `test_sanitize_output_paths` - Sanitización de paths de salida

#### Fuzzing Básico
- `test_random_keywords_dont_crash` - Keywords aleatorios
- `test_random_paths_dont_crash` - Paths aleatorios

## Fixtures Disponibles (conftest.py)

### Archivos y Directorios
- `temp_dir` - Directorio temporal único
- `sample_files` - Archivos de muestra (PDF, imagen, video, código, etc.)
- `sample_directory_structure` - Estructura de directorios completa
- `large_directory_structure` - Estructura grande para performance

### Objetos del Dominio
- `sample_search_results` - SearchResult de muestra
- `sample_search_query` - SearchQuery configurado
- `directory_tree` - DirectoryTree limpio
- `file_operations` - FileOperations para tests

### Mocks
- `mock_backend` - Backend mockeado
- `mock_search_records` - Registros ADO simulados

### Helpers
- `assert_file_exists` - Verificar existencia de archivos
- `assert_directory_exists` - Verificar existencia de directorios
- `create_test_file` - Crear archivos de test rápidamente
- `performance_timer` - Timer para medir performance

## Markers de Tests

```python
@pytest.mark.unit           # Tests unitarios
@pytest.mark.integration    # Tests de integración
@pytest.mark.performance    # Tests de performance
@pytest.mark.ui             # Tests de UI
@pytest.mark.slow           # Tests lentos
@pytest.mark.windows_only   # Tests específicos de Windows
```

## Configuración de Cobertura

El archivo `.coveragerc` define:
- Archivos a incluir/excluir
- Umbrales mínimos de cobertura
- Formatos de reporte

### Umbrales Objetivo
- Cobertura de líneas: 80%+
- Cobertura de branches: 75%+
- Cobertura de funciones: 80%+

## Mejores Prácticas

### Nombrado de Tests
- Usar nombres descriptivos: `test_<accion>_<escenario>_<resultado_esperado>`
- Ejemplos:
  - `test_copy_file_success_when_file_exists`
  - `test_search_query_raises_error_when_keywords_empty`

### Estructura de Tests
```python
def test_nombre_descriptivo(self):
    """Docstring explicando el test"""
    # Arrange - Preparar
    data = prepare_test_data()

    # Act - Ejecutar
    result = function_under_test(data)

    # Assert - Verificar
    assert result == expected_value
```

### Aislamiento
- Cada test debe ser independiente
- Usar fixtures para setup/teardown
- No depender del orden de ejecución
- Limpiar recursos en teardown

### Mocking
- Mockear dependencias externas (Windows COM, APIs, filesystem cuando apropiado)
- No mockear el código bajo test
- Usar `patch` con contexto manager

### Assertions
- Usar assertions específicas de pytest
- Mensajes descriptivos en assertions complejas
- Un concepto por test cuando sea posible

## Ejecución en CI/CD

### GitHub Actions (ejemplo)
```yaml
- name: Run tests
  run: |
    pip install pytest pytest-cov
    pytest tests/ --cov=. --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Troubleshooting

### Tests lentos
```bash
# Identificar tests lentos
python -m pytest tests/ --durations=10
```

### Fallas intermitentes
```bash
# Ejecutar múltiples veces
python -m pytest tests/ --count=10
```

### Debug
```bash
# Modo verbose con traceback completo
python -m pytest tests/test_file.py::test_name -vvv --tb=long

# Parar en primer fallo
python -m pytest tests/ -x

# Entrar en pdb en fallo
python -m pytest tests/ --pdb
```

## Reportes

### Generación de Reportes

```bash
# HTML
python -m pytest tests/ --html=report.html

# JUnit XML (para CI)
python -m pytest tests/ --junit-xml=results.xml

# JSON
python -m pytest tests/ --json=results.json
```

## Estado Actual

### Estadísticas (Última Ejecución)
- Total de Tests: 111+
- Tests Pasando: ~100
- Tests Fallando: ~5
- Tests Skipped: 3
- Cobertura Estimada: 75-85%

### Por Módulo
- `backend.py`: 80%+
- `classifier.py`: 90%+
- `file_manager.py`: 75%+
- `categories.py`: 90%+
- `config.py`: 85%+

## Próximos Pasos

### Tests Faltantes
- [ ] Tests para señales de UI (open_requested, etc.)
- [ ] Tests para sanitize_sql_input()
- [ ] Tests para validate_path_safety()
- [ ] Tests end-to-end completos
- [ ] Tests de carga más extensivos

### Mejoras
- [ ] Aumentar cobertura a 90%+
- [ ] Añadir property-based testing (hypothesis)
- [ ] Añadir mutation testing
- [ ] Integración continua automática
- [ ] Benchmarks de performance

## Recursos

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Testing Best Practices (Real Python)](https://realpython.com/pytest-python-testing/)

## Contacto y Contribución

Para contribuir con nuevos tests:
1. Seguir la estructura existente
2. Añadir documentación
3. Verificar que todos los tests pasen
4. Mantener o mejorar la cobertura
5. Actualizar este README si es necesario
