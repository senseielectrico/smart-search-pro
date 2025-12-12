"""
Smart Search - Ejemplos de Uso
================================

Ejemplos prácticos del backend de búsqueda.
"""

import time
from backend import (
    SearchService,
    SearchQuery,
    FileCategory,
    FileOperations
)


def example_basic_search():
    """Ejemplo 1: Búsqueda básica"""
    print("=" * 60)
    print("EJEMPLO 1: Búsqueda Básica")
    print("=" * 60)

    service = SearchService()

    query = SearchQuery(
        keywords=['python'],
        search_paths=[r'C:\Users\ramos\.local'],
        max_results=10
    )

    print(f"Buscando archivos con 'python' en: {query.search_paths}")
    results = service.search_sync(query)

    print(f"\nEncontrados: {len(results)} resultados\n")

    for i, result in enumerate(results[:5], 1):
        print(f"{i}. {result.name}")
        print(f"   Path: {result.path}")
        print(f"   Categoría: {result.category.value}")
        print(f"   Tamaño: {result._format_size()}")
        print()


def example_wildcard_search():
    """Ejemplo 2: Búsqueda con wildcards"""
    print("=" * 60)
    print("EJEMPLO 2: Búsqueda con Wildcards")
    print("=" * 60)

    service = SearchService()

    query = SearchQuery(
        keywords=['*.py', '*.txt'],
        search_paths=[r'C:\Users\ramos\.local\bin'],
        max_results=20
    )

    print("Buscando archivos *.py y *.txt")
    results = service.search_sync(query)

    print(f"\nEncontrados: {len(results)} resultados")

    # Clasificar por categoría
    classified = service.classify_results(results)

    print("\nResultados por categoría:")
    for category, items in classified.items():
        if items:
            print(f"  {category.value}: {len(items)} archivos")


def example_async_search():
    """Ejemplo 3: Búsqueda asíncrona"""
    print("=" * 60)
    print("EJEMPLO 3: Búsqueda Asíncrona")
    print("=" * 60)

    service = SearchService()

    query = SearchQuery(
        keywords=['document'],
        search_paths=[r'C:\Users\ramos\Documents'],
        max_results=50
    )

    print("Iniciando búsqueda asíncrona...")

    # Callbacks
    result_count = [0]  # Usar lista para modificar desde callback

    def on_result(result):
        result_count[0] += 1
        if result_count[0] % 10 == 0:
            print(f"  Procesados: {result_count[0]} resultados...")

    def on_complete(results):
        print(f"\nBúsqueda completada!")
        print(f"Total: {len(results)} resultados")

    def on_error(error):
        print(f"Error: {error}")

    # Iniciar búsqueda
    search_id = service.search_async(
        query,
        callback=on_result,
        completion_callback=on_complete,
        error_callback=on_error
    )

    print(f"Search ID: {search_id}")

    # Esperar mientras está activa
    while service.is_search_active(search_id):
        time.sleep(0.1)

    # Obtener resultados
    results = service.get_results(search_id)
    if results:
        print(f"\nPrimeros 3 resultados:")
        for i, result in enumerate(results[:3], 1):
            print(f"{i}. {result.name} ({result.category.value})")


def example_category_filter():
    """Ejemplo 4: Filtrado por categoría"""
    print("=" * 60)
    print("EJEMPLO 4: Filtrado por Categoría")
    print("=" * 60)

    service = SearchService()

    # Buscar solo documentos
    query = SearchQuery(
        keywords=['informe', 'reporte'],
        file_categories={FileCategory.DOCUMENT},
        search_paths=[r'C:\Users\ramos\Documents'],
        max_results=20
    )

    print("Buscando solo DOCUMENTOS con 'informe' o 'reporte'")
    results = service.search_sync(query)

    print(f"\nEncontrados: {len(results)} documentos\n")

    for result in results[:5]:
        print(f"- {result.name} ({result.extension})")


def example_file_operations():
    """Ejemplo 5: Operaciones de archivos"""
    print("=" * 60)
    print("EJEMPLO 5: Operaciones de Archivos")
    print("=" * 60)

    ops = FileOperations()

    # Crear archivo de prueba
    test_file = r'C:\Users\ramos\.local\bin\test_file.txt'

    try:
        # Crear archivo
        with open(test_file, 'w') as f:
            f.write("Archivo de prueba")

        print(f"Archivo creado: {test_file}")

        # Obtener propiedades
        props = ops.get_properties(test_file)
        print("\nPropiedades:")
        print(f"  Nombre: {props['name']}")
        print(f"  Tamaño: {props['size']} bytes")
        print(f"  Creado: {props['created']}")
        print(f"  Modificado: {props['modified']}")

        # Abrir ubicación (comentado para no abrir explorador)
        # ops.open_location(test_file)
        print(f"\n(Ubicación: {props['parent']})")

        # Copiar archivo
        copy_dest = r'C:\Users\ramos\.local\bin\test_file_copy.txt'
        ops.copy(test_file, copy_dest)
        print(f"\nArchivo copiado a: {copy_dest}")

        # Eliminar archivos de prueba
        ops.delete(test_file, permanent=True)
        ops.delete(copy_dest, permanent=True)
        print("\nArchivos de prueba eliminados")

    except Exception as e:
        print(f"Error: {e}")


def example_content_search():
    """Ejemplo 6: Búsqueda por contenido"""
    print("=" * 60)
    print("EJEMPLO 6: Búsqueda por Contenido")
    print("=" * 60)

    service = SearchService()

    query = SearchQuery(
        keywords=['python', 'backend'],
        search_content=True,  # Buscar en contenido
        search_filename=True,  # También en nombre
        search_paths=[r'C:\Users\ramos\.local\bin'],
        max_results=15
    )

    print("Buscando 'python' y 'backend' en nombre Y contenido")
    print("(Requiere Windows Search API activo)")

    try:
        results = service.search_sync(query)
        print(f"\nEncontrados: {len(results)} resultados\n")

        for result in results[:5]:
            print(f"- {result.name}")
            print(f"  {result.path}")

    except Exception as e:
        print(f"\nError: {e}")
        print("Tip: Asegúrate de que Windows Search esté activo")


def example_multiple_parallel():
    """Ejemplo 7: Múltiples búsquedas paralelas"""
    print("=" * 60)
    print("EJEMPLO 7: Búsquedas Paralelas")
    print("=" * 60)

    service = SearchService()

    # Definir múltiples búsquedas
    searches = {
        'Python': SearchQuery(
            keywords=['*.py'],
            search_paths=[r'C:\Users\ramos\.local'],
            max_results=10
        ),
        'JavaScript': SearchQuery(
            keywords=['*.js'],
            search_paths=[r'C:\Users\ramos\.local'],
            max_results=10
        ),
        'Texto': SearchQuery(
            keywords=['*.txt'],
            search_paths=[r'C:\Users\ramos\.local'],
            max_results=10
        ),
    }

    print("Iniciando 3 búsquedas en paralelo...")

    # Iniciar todas las búsquedas
    search_ids = {}
    for name, query in searches.items():
        sid = service.search_async(query)
        search_ids[name] = sid
        print(f"  {name}: {sid}")

    # Esperar a que todas terminen
    print("\nEsperando resultados...")
    while any(service.is_search_active(sid) for sid in search_ids.values()):
        time.sleep(0.1)

    # Mostrar resultados
    print("\nResultados:")
    for name, sid in search_ids.items():
        results = service.get_results(sid)
        if results:
            print(f"  {name}: {len(results)} archivos")


def example_advanced_filtering():
    """Ejemplo 8: Filtrado avanzado"""
    print("=" * 60)
    print("EJEMPLO 8: Filtrado Avanzado")
    print("=" * 60)

    service = SearchService()

    query = SearchQuery(
        keywords=['archivo'],
        search_paths=[r'C:\Users\ramos\.local\bin'],
        max_results=100
    )

    print("Buscando archivos y aplicando filtros...")
    results = service.search_sync(query)

    # Filtro 1: Solo archivos grandes (> 1 MB)
    large_files = [r for r in results if r.size > 1024 * 1024]
    print(f"\nArchivos > 1 MB: {len(large_files)}")

    # Filtro 2: Archivos recientes (últimos 30 días)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_files = [
        r for r in results
        if r.modified and r.modified > thirty_days_ago
    ]
    print(f"Archivos recientes: {len(recent_files)}")

    # Filtro 3: Solo archivos de código
    code_files = [r for r in results if r.category == FileCategory.CODE]
    print(f"Archivos de código: {len(code_files)}")

    # Combinar filtros
    large_recent_code = [
        r for r in results
        if r.size > 1024 * 1024
        and r.modified and r.modified > thirty_days_ago
        and r.category == FileCategory.CODE
    ]
    print(f"Archivos grandes, recientes y de código: {len(large_recent_code)}")


def example_export_results():
    """Ejemplo 9: Exportar resultados"""
    print("=" * 60)
    print("EJEMPLO 9: Exportar Resultados")
    print("=" * 60)

    import json

    service = SearchService()

    query = SearchQuery(
        keywords=['*.py'],
        search_paths=[r'C:\Users\ramos\.local\bin'],
        max_results=20
    )

    print("Buscando archivos Python...")
    results = service.search_sync(query)

    # Exportar a JSON
    output_file = r'C:\Users\ramos\.local\bin\search_results.json'

    data = {
        'query': {
            'keywords': query.keywords,
            'paths': query.search_paths,
            'timestamp': datetime.now().isoformat()
        },
        'results': [r.to_dict() for r in results]
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nResultados exportados a: {output_file}")
    print(f"Total de resultados: {len(results)}")

    # Limpiar
    import os
    os.remove(output_file)
    print("Archivo de ejemplo eliminado")


def main():
    """Ejecutar todos los ejemplos"""
    examples = [
        example_basic_search,
        example_wildcard_search,
        example_async_search,
        example_category_filter,
        example_file_operations,
        example_content_search,
        example_multiple_parallel,
        example_advanced_filtering,
        example_export_results,
    ]

    print("\n" + "=" * 60)
    print("SMART SEARCH - EJEMPLOS DE USO")
    print("=" * 60 + "\n")

    for i, example in enumerate(examples, 1):
        try:
            example()
            print()
            time.sleep(1)  # Pausa entre ejemplos
        except Exception as e:
            print(f"\nError en ejemplo {i}: {e}\n")
            continue

    print("=" * 60)
    print("EJEMPLOS COMPLETADOS")
    print("=" * 60)


if __name__ == "__main__":
    main()
