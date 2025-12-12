# Quick Start - Tests de Smart Search

## Ejecutar Todos los Tests

```bash
# Básico
python -m pytest tests/

# Con verbose
python -m pytest tests/ -v

# Con salida resumida
python -m pytest tests/ -q
```

## Ejecutar Tests Específicos

```bash
# Solo test_suite.py
python -m pytest tests/test_suite.py -v

# Solo test_utils.py
python -m pytest tests/test_utils.py -v

# Solo test_security.py
python -m pytest tests/test_security.py -v

# Una clase específica
python -m pytest tests/test_suite.py::TestSearchResult -v

# Un test específico
python -m pytest tests/test_suite.py::TestSearchResult::test_creation_basic -v
```

## Tests con Cobertura

```bash
# Usando el script
python run_tests_with_coverage.py

# Directo con pytest-cov
python -m pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

# Solo mostrar líneas faltantes
python -m pytest tests/ --cov=. --cov-report=term-missing
```

## Tests por Categoría

```bash
# Solo unitarios
python -m pytest tests/ -m unit

# Solo integración
python -m pytest tests/ -m integration

# Solo performance
python -m pytest tests/ -m performance

# Solo tests rápidos (excluir slow)
python -m pytest tests/ -m "not slow"
```

## Debug

```bash
# Parar en primer fallo
python -m pytest tests/ -x

# Mostrar variables locales en fallo
python -m pytest tests/ -l

# Traceback completo
python -m pytest tests/ --tb=long

# Entrar en debugger en fallo
python -m pytest tests/ --pdb

# Modo super verbose
python -m pytest tests/ -vvv
```

## Performance

```bash
# Mostrar 10 tests más lentos
python -m pytest tests/ --durations=10

# Ejecutar tests en paralelo (requiere pytest-xdist)
python -m pytest tests/ -n auto
```

## Utilidades

```bash
# Listar tests sin ejecutar
python -m pytest tests/ --collect-only

# Ejecutar solo tests que fallaron la última vez
python -m pytest tests/ --lf

# Ejecutar primero los que fallaron
python -m pytest tests/ --ff

# Crear reporte HTML
python -m pytest tests/ --html=report.html
```

## Ver Cobertura

```bash
# Generar y abrir reporte HTML
python -m pytest tests/ --cov=. --cov-report=html
# Luego abrir: htmlcov/index.html
```

## Instalación de Dependencias

```bash
# Instalar pytest y plugins
pip install pytest pytest-cov pytest-html pytest-xdist

# Instalar psutil (para tests de memoria)
pip install psutil
```

## Tests por Módulo

```bash
# Tests de backend
python -m pytest tests/ -k "backend or SearchResult or SearchQuery"

# Tests de seguridad
python -m pytest tests/ -k "security or injection or traversal"

# Tests de utilidades
python -m pytest tests/ -k "format_file_size or format_date"
```

## Resultados Esperados

```
tests/test_suite.py ........................ [ 56%]
tests/test_utils.py ........................ [ 78%]
tests/test_security.py ..................... [100%]

=========== 100+ passed, 3 skipped in 1.5s ============
```

## Archivos Generados

Después de ejecutar con cobertura:
- `htmlcov/index.html` - Reporte HTML interactivo
- `.coverage` - Datos de cobertura
- `report.html` - Reporte de tests (si usas --html)

## Troubleshooting

### "pytest: command not found"
```bash
pip install pytest
```

### "No module named 'pytest_cov'"
```bash
pip install pytest-cov
```

### Tests muy lentos
```bash
# Ejecutar solo tests rápidos
python -m pytest tests/ -m "not slow"

# Paralelizar
pip install pytest-xdist
python -m pytest tests/ -n auto
```

### Fallas intermitentes
```bash
# Ejecutar múltiples veces
python -m pytest tests/ --count=10
```

## Más Información

Ver documentación completa en:
- `tests/README_TESTS.md` - Documentación detallada
- `tests/SUMMARY.md` - Resumen de cambios
- `TESTS_FINAL_REPORT.md` - Reporte final

## Contacto

Para preguntas o problemas con los tests, consultar la documentación o abrir un issue.
