"""
Quick Test - Smart Search Backend
==================================

Test rápido para verificar funcionamiento del backend.
"""

import sys
import os
from pathlib import Path

# Agregar directorio al path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from backend import (
        SearchService,
        SearchQuery,
        FileCategory,
        FileOperations
    )
    print("Importación exitosa")
except ImportError as e:
    print(f"ERROR: No se pudo importar el módulo: {e}")
    print("\nInstala las dependencias:")
    print("  pip install pywin32 comtypes send2trash")
    sys.exit(1)


def test_basic_search():
    """Test de búsqueda básica"""
    print("\n" + "=" * 60)
    print("TEST: Búsqueda Básica")
    print("=" * 60)

    try:
        # Crear servicio con fallback (siempre funciona)
        service = SearchService(use_windows_search=False)
        print("Servicio creado (modo: fallback)")

        # Buscar archivos Python en el directorio actual
        current_dir = str(Path(__file__).parent)

        query = SearchQuery(
            keywords=['*.py'],
            search_paths=[current_dir],
            max_results=10
        )

        print(f"\nBuscando archivos *.py en: {current_dir}")

        results = service.search_sync(query)

        print(f"\nResultados: {len(results)} archivos encontrados")

        if results:
            print("\nPrimeros 5 archivos:")
            for i, result in enumerate(results[:5], 1):
                print(f"{i}. {result.name}")
                print(f"   Size: {result._format_size()}")
                print(f"   Category: {result.category.value}")

            # Clasificar
            classified = service.classify_results(results)

            print("\nPor categoría:")
            for category, items in classified.items():
                if items:
                    print(f"  {category.value}: {len(items)}")

            return True
        else:
            print("ADVERTENCIA: No se encontraron archivos")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_operations():
    """Test de operaciones de archivos"""
    print("\n" + "=" * 60)
    print("TEST: Operaciones de Archivos")
    print("=" * 60)

    try:
        import tempfile

        ops = FileOperations()

        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_file = f.name
            f.write("Test content")

        print(f"Archivo temporal creado: {temp_file}")

        # Obtener propiedades
        props = ops.get_properties(temp_file)

        print("\nPropiedades:")
        print(f"  Nombre: {props['name']}")
        print(f"  Size: {props['size']} bytes")
        print(f"  Creado: {props['created']}")
        print(f"  Modificado: {props['modified']}")

        # Copiar
        copy_dest = temp_file.replace('.txt', '_copy.txt')
        ops.copy(temp_file, copy_dest)
        print(f"\nCopiado a: {copy_dest}")

        # Eliminar
        ops.delete(temp_file, permanent=True)
        ops.delete(copy_dest, permanent=True)
        print("Archivos temporales eliminados")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_classification():
    """Test de clasificación de archivos"""
    print("\n" + "=" * 60)
    print("TEST: Clasificación de Archivos")
    print("=" * 60)

    try:
        from backend import SearchResult

        test_files = [
            ('document.pdf', FileCategory.DOCUMENT),
            ('image.png', FileCategory.IMAGE),
            ('video.mp4', FileCategory.VIDEO),
            ('audio.mp3', FileCategory.AUDIO),
            ('script.py', FileCategory.CODE),
            ('archive.zip', FileCategory.ARCHIVE),
        ]

        print("\nVerificando clasificación automática:")

        all_ok = True
        for filename, expected in test_files:
            result = SearchResult(
                path=f"C:\\test\\{filename}",
                name=filename
            )

            status = "OK" if result.category == expected else "FAIL"
            print(f"  {filename}: {result.category.value} [{status}]")

            if result.category != expected:
                all_ok = False

        return all_ok

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_windows_search():
    """Test de Windows Search API"""
    print("\n" + "=" * 60)
    print("TEST: Windows Search API")
    print("=" * 60)

    try:
        service = SearchService(use_windows_search=True)
        print("Windows Search API disponible")

        # Intentar búsqueda simple
        user_docs = os.path.join(os.environ.get('USERPROFILE', 'C:\\Users'), 'Documents')

        query = SearchQuery(
            keywords=['*.txt'],
            search_paths=[user_docs],
            max_results=5
        )

        print(f"\nBuscando en: {user_docs}")

        results = service.search_sync(query)
        print(f"Resultados: {len(results)} archivos")

        return True

    except ConnectionError as e:
        print(f"ADVERTENCIA: Windows Search no disponible: {e}")
        print("Esto es normal si el servicio Windows Search está desactivado")
        return True  # No es error crítico

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecuta todos los tests"""
    print("\n" + "=" * 70)
    print(" SMART SEARCH BACKEND - QUICK TEST")
    print("=" * 70)

    tests = [
        ("Búsqueda Básica", test_basic_search),
        ("Operaciones de Archivos", test_file_operations),
        ("Clasificación", test_classification),
        ("Windows Search API", test_windows_search),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        result = test_func()

        if result:
            passed += 1
        else:
            failed += 1

    # Resumen
    print("\n" + "=" * 70)
    print(" RESUMEN")
    print("=" * 70)
    print(f"Total: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\nTodos los tests pasaron correctamente")
        print("El backend está listo para usar")
    else:
        print(f"\nALERTA: {failed} test(s) fallaron")
        print("Revisa los errores arriba")

    print("=" * 70 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
