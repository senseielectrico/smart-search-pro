"""
Test Suite para verificar las correcciones aplicadas en Smart Search
=====================================================================

Ejecutar:
    python test_corrections.py

Tests incluidos:
1. Sistema unificado de categorías
2. Bug _format_size corregido
3. Gestión de memoria
4. Validación de entrada
5. Manejo de errores
"""

import sys
import os
from pathlib import Path

# Añadir directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_categories_unified():
    """Test 1: Sistema unificado de categorías"""
    print("\n[TEST 1] Sistema de Categorías Unificado")
    print("=" * 50)

    try:
        from categories import FileCategory, classify_by_extension

        # Test clasificación básica
        tests = {
            '.py': FileCategory.CODIGO,
            '.pdf': FileCategory.DOCUMENTOS,
            '.zip': FileCategory.COMPRIMIDOS,
            '.exe': FileCategory.EJECUTABLES,
            '.mp3': FileCategory.AUDIO,
            '.jpg': FileCategory.IMAGENES,
            '.mp4': FileCategory.VIDEOS,
            '.db': FileCategory.DATOS,
            '.xyz': FileCategory.OTROS,
            '': FileCategory.OTROS,
        }

        passed = 0
        failed = 0

        for ext, expected in tests.items():
            result = classify_by_extension(ext)
            if result == expected:
                print(f"  ✓ {ext or '(empty)':10} -> {result.value:15} (PASS)")
                passed += 1
            else:
                print(f"  ✗ {ext or '(empty)':10} -> {result.value:15} (FAIL, expected {expected.value})")
                failed += 1

        # Test integración con backend
        from backend import SearchResult

        result = SearchResult(path="test.zip", name="test.zip", size=1000)
        if result.category == FileCategory.COMPRIMIDOS:
            print(f"\n  ✓ Backend usa categorías unificadas (PASS)")
            passed += 1
        else:
            print(f"\n  ✗ Backend NO usa categorías unificadas (FAIL)")
            print(f"    Expected: {FileCategory.COMPRIMIDOS.value}")
            print(f"    Got: {result.category.value}")
            failed += 1

        print(f"\n  Total: {passed} passed, {failed} failed")
        return failed == 0

    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_format_size_no_side_effects():
    """Test 2: _format_size no modifica self.size"""
    print("\n[TEST 2] Bug _format_size Corregido")
    print("=" * 50)

    try:
        from backend import SearchResult

        # Test con diferentes tamaños
        test_cases = [
            (0, "0.00 B"),
            (512, "512.00 B"),
            (1024, "1.00 KB"),
            (1024 * 1024, "1.00 MB"),
            (1024 * 1024 * 1024, "1.00 GB"),
        ]

        passed = 0
        failed = 0

        for size, expected_format in test_cases:
            result = SearchResult(path="test", name="test", size=size)
            original_size = result.size

            # Llamar múltiples veces
            formatted1 = result._format_size()
            formatted2 = result._format_size()

            # Verificar que size no cambió
            if result.size == original_size:
                print(f"  ✓ Size {size:>12} no modificado (PASS)")
                passed += 1
            else:
                print(f"  ✗ Size {size:>12} modificado: {original_size} -> {result.size} (FAIL)")
                failed += 1

            # Verificar que formato es consistente
            if formatted1 == formatted2:
                print(f"    Formato consistente: {formatted1}")
                passed += 1
            else:
                print(f"  ✗ Formato inconsistente: {formatted1} != {formatted2} (FAIL)")
                failed += 1

        print(f"\n  Total: {passed} passed, {failed} failed")
        return failed == 0

    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_cleanup():
    """Test 3: Gestión de memoria con cleanup"""
    print("\n[TEST 3] Gestión de Memoria")
    print("=" * 50)

    try:
        from backend import SearchService

        # Crear servicio con límite bajo para test
        service = SearchService(use_windows_search=False, max_cached_searches=3)

        # Añadir 5 búsquedas
        for i in range(5):
            service._search_results[f"search_{i}"] = []

        initial_count = len(service._search_results)
        print(f"  Búsquedas antes del cleanup: {initial_count}")

        # Ejecutar cleanup
        service._cleanup_old_searches()

        final_count = len(service._search_results)
        print(f"  Búsquedas después del cleanup: {final_count}")

        if final_count == 3:
            print(f"  ✓ Cleanup exitoso: mantuvo {final_count} de {initial_count} (PASS)")
            return True
        else:
            print(f"  ✗ Cleanup falló: esperaba 3, obtuvo {final_count} (FAIL)")
            return False

    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_module_imports():
    """Test 4: Verificar imports correctos"""
    print("\n[TEST 4] Verificación de Imports")
    print("=" * 50)

    modules = {
        'categories': 'Sistema de categorías unificado',
        'backend': 'Motor de búsqueda',
        'ui': 'Interfaz PyQt6 (puede fallar sin PyQt6)',
        'main': 'Aplicación integrada (puede fallar sin PyQt6)',
        'classifier': 'Clasificador de archivos',
        'file_manager': 'Gestor de archivos',
    }

    passed = 0
    failed = 0
    warnings = 0

    for module_name, description in modules.items():
        try:
            __import__(module_name)
            print(f"  ✓ {module_name:15} - {description} (OK)")
            passed += 1
        except ImportError as e:
            if 'PyQt6' in str(e) and module_name in ['ui', 'main']:
                print(f"  ⚠ {module_name:15} - {description} (SKIP - PyQt6 no instalado)")
                warnings += 1
            else:
                print(f"  ✗ {module_name:15} - {description} (FAIL)")
                print(f"    Error: {e}")
                failed += 1
        except Exception as e:
            print(f"  ✗ {module_name:15} - Error: {e}")
            failed += 1

    print(f"\n  Total: {passed} passed, {failed} failed, {warnings} warnings")
    return failed == 0


def test_category_consistency():
    """Test 5: Consistencia entre módulos"""
    print("\n[TEST 5] Consistencia de Categorías entre Módulos")
    print("=" * 50)

    try:
        from categories import FileCategory as CatFC
        from backend import FileCategory as BackFC

        # Verificar que son el mismo Enum
        if CatFC is BackFC:
            print(f"  ✓ backend.FileCategory es categories.FileCategory (PASS)")
            passed = 1
            failed = 0
        else:
            print(f"  ✗ backend.FileCategory NO es categories.FileCategory (FAIL)")
            print(f"    categories: {CatFC}")
            print(f"    backend: {BackFC}")
            failed = 1
            passed = 0

        # Verificar categoría COMPRIMIDOS existe
        if hasattr(CatFC, 'COMPRIMIDOS'):
            print(f"  ✓ FileCategory.COMPRIMIDOS existe (PASS)")
            passed += 1
        else:
            print(f"  ✗ FileCategory.COMPRIMIDOS NO existe (FAIL)")
            failed += 1

        # Verificar que no existe ARCHIVE (nombre antiguo)
        if not hasattr(CatFC, 'ARCHIVE'):
            print(f"  ✓ FileCategory.ARCHIVE eliminado (migración completa) (PASS)")
            passed += 1
        else:
            print(f"  ⚠ FileCategory.ARCHIVE aún existe (migración incompleta) (WARNING)")

        # Test con ui.py (puede fallar si PyQt6 no está instalado)
        try:
            from ui import FileType

            if hasattr(FileType, 'COMPRIMIDOS') or hasattr(FileType, 'get_category'):
                print(f"  ✓ ui.FileType integrado con categories.py (PASS)")
                passed += 1
            else:
                print(f"  ⚠ ui.FileType usa fallback (PyQt6 no disponible)")
        except ImportError:
            print(f"  ⚠ ui.py no disponible (PyQt6 no instalado)")

        print(f"\n  Total: {passed} passed, {failed} failed")
        return failed == 0

    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Ejecuta todos los tests"""
    print("\n" + "=" * 70)
    print(" SMART SEARCH - TEST SUITE DE CORRECCIONES")
    print("=" * 70)

    tests = [
        ("Sistema de Categorías Unificado", test_categories_unified),
        ("Bug _format_size Corregido", test_format_size_no_side_effects),
        ("Gestión de Memoria", test_memory_cleanup),
        ("Verificación de Imports", test_module_imports),
        ("Consistencia entre Módulos", test_category_consistency),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n  ✗ Test '{test_name}' falló con excepción: {e}")
            results.append((test_name, False))

    # Resumen final
    print("\n" + "=" * 70)
    print(" RESUMEN DE RESULTADOS")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status:8} - {test_name}")

    print("\n" + "-" * 70)
    print(f"  Total: {passed}/{len(results)} tests pasaron")
    print("=" * 70)

    if passed == len(results):
        print("\n  ✅ TODOS LOS TESTS PASARON - CORRECCIONES VERIFICADAS")
        return 0
    else:
        print(f"\n  ⚠️  {failed} TEST(S) FALLARON - REVISAR CORRECCIONES")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
