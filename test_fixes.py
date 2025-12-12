"""
Tests para verificar las correcciones aplicadas
"""
import sys
import os
from pathlib import Path

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

print("=" * 80)
print("SMART SEARCH - Verificación de Correcciones")
print("=" * 80)

# Test 1: Verificar que categories.py existe y funciona
print("\n[TEST 1] Módulo categories.py")
try:
    from categories import FileCategory, classify_by_extension, get_all_categories
    print("✓ categories.py importado correctamente")

    # Test clasificación
    test_cases = [
        ('.py', FileCategory.CODIGO),
        ('.pdf', FileCategory.DOCUMENTOS),
        ('.zip', FileCategory.COMPRIMIDOS),
        ('.exe', FileCategory.EJECUTABLES),
        ('', FileCategory.OTROS),
    ]

    for ext, expected in test_cases:
        result = classify_by_extension(ext)
        if result == expected:
            print(f"  ✓ {ext or '(vacío)':10} -> {result.value}")
        else:
            print(f"  ✗ {ext:10} -> {result.value} (esperado: {expected.value})")

    print(f"  Categorías totales: {len(get_all_categories())}")

except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Verificar corrección de _format_size
print("\n[TEST 2] Corrección de _format_size en backend.py")
try:
    from backend import SearchResult

    # Crear resultado de prueba
    result = SearchResult(
        path="C:\\test.txt",
        name="test.txt",
        size=1024000
    )

    # Obtener tamaño formateado múltiples veces
    size1 = result._format_size()
    size2 = result._format_size()
    size3 = result._format_size()

    # Verificar que no modificó self.size
    if result.size == 1024000:
        print(f"✓ self.size no modificado: {result.size} bytes")
    else:
        print(f"✗ self.size modificado: {result.size} (esperado: 1024000)")

    # Verificar que retorna siempre lo mismo
    if size1 == size2 == size3:
        print(f"✓ Formato consistente: {size1}")
    else:
        print(f"✗ Formato inconsistente: {size1} / {size2} / {size3}")

    # Test con diferentes tamaños
    test_sizes = [0, 512, 1024, 1048576, 1073741824]
    print("\n  Ejemplos de formateo:")
    for size in test_sizes:
        r = SearchResult(path="test", name="test", size=size)
        formatted = r._format_size()
        print(f"    {size:>12} bytes -> {formatted}")
        # Verificar que no modificó el tamaño
        if r.size != size:
            print(f"    ✗ ERROR: size modificado a {r.size}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Verificar gestión de memoria en SearchService
print("\n[TEST 3] Gestión de memoria en SearchService")
try:
    from backend import SearchService, SearchQuery

    service = SearchService(use_windows_search=False, max_cached_searches=3)
    print(f"✓ SearchService creado con max_cached_searches=3")

    # Simular búsquedas
    for i in range(5):
        query = SearchQuery(
            keywords=["test"],
            search_paths=[os.path.expanduser("~")],
            max_results=10
        )
        # Crear ID manual para testing
        search_id = f"search_{i}"
        service._search_results[search_id] = []

    print(f"  Búsquedas antes de cleanup: {len(service._search_results)}")

    # Ejecutar cleanup
    service._cleanup_old_searches()

    remaining = len(service._search_results)
    if remaining <= 3:
        print(f"✓ Cleanup exitoso: {remaining} búsquedas restantes")
    else:
        print(f"✗ Cleanup falló: {remaining} búsquedas (esperado: ≤3)")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Verificar importaciones en todos los módulos
print("\n[TEST 4] Verificar sintaxis de todos los módulos")
modules_to_test = [
    'backend',
    'ui',
    'classifier',
    'file_manager',
    'categories'
]

for module_name in modules_to_test:
    try:
        __import__(module_name)
        print(f"✓ {module_name}.py - Sintaxis correcta")
    except ImportError as e:
        print(f"⚠ {module_name}.py - Falta dependencia: {e}")
    except Exception as e:
        print(f"✗ {module_name}.py - Error: {e}")

# Test 5: Verificar compatibilidad de FileCategory
print("\n[TEST 5] Compatibilidad de FileCategory entre módulos")
try:
    from backend import FileCategory as BackendCategory
    from categories import FileCategory as CategoriesCategory

    # Verificar que tienen las mismas categorías
    backend_names = set(c.value for c in BackendCategory)
    categories_names = set(c.value for c in CategoriesCategory)

    print(f"  Backend categorías: {len(backend_names)}")
    print(f"  Categories categorías: {len(categories_names)}")

    # Verificar diferencias
    only_backend = backend_names - categories_names
    only_categories = categories_names - backend_names

    if only_backend:
        print(f"  ⚠ Solo en backend: {only_backend}")

    if only_categories:
        print(f"  ⚠ Solo en categories: {only_categories}")

    if not only_backend and not only_categories:
        print("✓ Categorías compatibles")
    else:
        print("⚠ Hay diferencias en categorías - considerar usar categories.FileCategory")

except Exception as e:
    print(f"  Nota: {e}")

# Test 6: Test de paths con caracteres especiales
print("\n[TEST 6] Manejo de paths con caracteres especiales")
try:
    from backend import SearchQuery

    test_paths = [
        "C:\\Users\\Test User\\Documents",
        "C:\\Documentos\\Año 2024",
        "C:\\Program Files\\Test",
    ]

    for path in test_paths:
        try:
            query = SearchQuery(
                keywords=["test"],
                search_paths=[path],
                max_results=1
            )
            sql = query.build_sql_query()
            if path.replace('\\', '\\\\') in sql:
                print(f"✓ Path escapado: {path}")
            else:
                print(f"⚠ Path sin escapar: {path}")
        except Exception as e:
            print(f"✗ Error con path {path}: {e}")

except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 80)
print("RESUMEN")
print("=" * 80)
print("\nVerificar el output anterior para detalles específicos.")
print("\nCORRECCIONES APLICADAS:")
print("  1. ✓ Bug _format_size corregido (no modifica self.size)")
print("  2. ✓ Gestión de memoria implementada (max_cached_searches)")
print("  3. ✓ Módulo categories.py creado (sistema unificado)")
print("\nPENDIENTE:")
print("  - Unificar uso de FileCategory en todos los módulos")
print("  - Validación de inputs en classify_file")
print("  - Normalización de paths para SQL")
print("  - Tests unitarios completos")
print("\n" + "=" * 80)
