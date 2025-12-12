"""
Smart Search Test Suite
========================

Suite completa de tests para Smart Search.

Estructura:
-----------
- test_suite.py: Suite completa de tests
- run_tests.py: Runner con múltiples opciones

Categorías de Tests:
--------------------
1. Tests Unitarios:
   - SearchResult
   - SearchQuery
   - Classifier
   - DirectoryTree
   - FileOperations
   - Cache
   - Debouncer

2. Tests de Integración:
   - Backend + Classifier
   - DirectoryTree + UI
   - Search + Cache + Results

3. Tests de UI:
   - Validación de componentes
   - FileType classification
   - Shortcuts

4. Tests de Rendimiento:
   - Search performance
   - Cache performance
   - Memory usage
   - Large result sets

Uso:
----
    # Ejecutar todos los tests
    pytest tests/test_suite.py -v

    # Con el runner
    python tests/run_tests.py

    # Solo unitarios
    python tests/run_tests.py --unit

    # Con cobertura
    python tests/run_tests.py --coverage

    # Test rápido
    python tests/run_tests.py --quick
"""

__version__ = "1.0.0"
__author__ = "Smart Search Team"
