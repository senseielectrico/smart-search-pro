"""
Smart Search - Script de Instalación
=====================================

Instala y configura el backend de búsqueda.
"""

import sys
import subprocess
import os
from pathlib import Path


def print_header(text):
    """Imprime un encabezado formateado"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def check_python_version():
    """Verifica la versión de Python"""
    print("Verificando versión de Python...")

    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("ERROR: Se requiere Python 3.8 o superior")
        return False

    print("Version OK")
    return True


def install_dependencies():
    """Instala las dependencias"""
    print("\nInstalando dependencias...")

    requirements = [
        'pywin32>=305',
        'comtypes>=1.2.0',
        'send2trash>=1.8.0',
    ]

    for package in requirements:
        print(f"\nInstalando {package}...")
        try:
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', package],
                stdout=subprocess.DEVNULL
            )
            print(f"  {package} instalado correctamente")
        except subprocess.CalledProcessError as e:
            print(f"  ERROR instalando {package}: {e}")
            return False

    return True


def verify_windows_search():
    """Verifica que Windows Search esté disponible"""
    print("\nVerificando Windows Search...")

    try:
        import win32com.client
        import pythoncom

        pythoncom.CoInitialize()

        try:
            connection = win32com.client.Dispatch("ADODB.Connection")
            connection_string = (
                "Provider=Search.CollatorDSO;"
                "Extended Properties='Application=Windows';"
            )
            connection.Open(connection_string)
            connection.Close()

            print("  Windows Search API disponible")
            return True

        except Exception as e:
            print(f"  ADVERTENCIA: Windows Search no disponible: {e}")
            print("  Se usará el motor de búsqueda alternativo")
            return False

        finally:
            pythoncom.CoUninitialize()

    except ImportError:
        print("  pywin32 no instalado aún")
        return False


def test_import():
    """Prueba importar el módulo"""
    print("\nProbando importación del módulo...")

    try:
        # Agregar directorio al path
        script_dir = Path(__file__).parent
        sys.path.insert(0, str(script_dir))

        # Intentar importar
        from backend import SearchService, SearchQuery, FileCategory

        print("  Importación exitosa")

        # Crear instancia de prueba
        service = SearchService(use_windows_search=False)
        print("  Servicio inicializado correctamente")

        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def run_basic_test():
    """Ejecuta un test básico"""
    print("\nEjecutando test básico...")

    try:
        from backend import SearchService, SearchQuery

        service = SearchService(use_windows_search=False)

        # Buscar en directorio local
        test_path = str(Path(__file__).parent)

        query = SearchQuery(
            keywords=['*.py'],
            search_paths=[test_path],
            max_results=5
        )

        print(f"  Buscando archivos Python en: {test_path}")
        results = service.search_sync(query)

        print(f"  Encontrados: {len(results)} archivos")

        if results:
            print(f"  Primer resultado: {results[0].name}")
            return True
        else:
            print("  ADVERTENCIA: No se encontraron resultados")
            return True  # No es error crítico

    except Exception as e:
        print(f"  ERROR en test: {e}")
        return False


def create_example_script():
    """Crea un script de ejemplo"""
    print("\nCreando script de ejemplo...")

    example_script = Path(__file__).parent / "quick_start.py"

    content = '''"""
Quick Start - Smart Search
===========================

Script de inicio rápido para probar el backend.
"""

from backend import SearchService, SearchQuery, FileCategory
import os


def main():
    # Crear servicio
    service = SearchService()

    # Obtener directorio del usuario
    user_docs = os.path.join(os.environ.get('USERPROFILE'), 'Documents')

    # Crear búsqueda
    query = SearchQuery(
        keywords=['*.txt', '*.pdf'],
        search_paths=[user_docs],
        max_results=20
    )

    print(f"Buscando en: {user_docs}")
    print("Buscando archivos: *.txt, *.pdf")
    print()

    # Ejecutar búsqueda
    results = service.search_sync(query)

    print(f"Encontrados: {len(results)} archivos")
    print()

    # Mostrar primeros 10
    for i, result in enumerate(results[:10], 1):
        print(f"{i}. {result.name}")
        print(f"   Categoría: {result.category.value}")
        print(f"   Path: {result.path}")
        print()

    # Clasificar por categoría
    classified = service.classify_results(results)

    print("Resumen por categoría:")
    for category, items in classified.items():
        if items:
            print(f"  {category.value}: {len(items)}")


if __name__ == "__main__":
    main()
'''

    try:
        with open(example_script, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  Script creado: {example_script}")
        return True

    except Exception as e:
        print(f"  ERROR creando script: {e}")
        return False


def print_usage_instructions():
    """Imprime instrucciones de uso"""
    print_header("Instalación Completada")

    print("El backend está instalado y listo para usar.\n")

    print("INICIO RÁPIDO:")
    print("-" * 60)
    print("\n1. Prueba el script de ejemplo:")
    print("   python quick_start.py\n")

    print("2. Importa en tu código:")
    print("   from smart_search import SearchService, SearchQuery\n")

    print("3. Ejemplos completos:")
    print("   python example_usage.py\n")

    print("DOCUMENTACIÓN:")
    print("-" * 60)
    print("Ver README.md para documentación completa\n")

    print("USO BÁSICO:")
    print("-" * 60)
    print("""
from smart_search import SearchService, SearchQuery

# Crear servicio
service = SearchService()

# Crear búsqueda
query = SearchQuery(
    keywords=['documento', '*.pdf'],
    search_paths=[r'C:\\Users\\ramos\\Documents']
)

# Ejecutar
results = service.search_sync(query)

# Procesar resultados
for result in results:
    print(result.name, result.path)
    """)


def main():
    """Función principal de instalación"""
    print_header("Smart Search - Instalación")

    steps = [
        ("Verificar Python", check_python_version),
        ("Instalar dependencias", install_dependencies),
        ("Verificar Windows Search", verify_windows_search),
        ("Probar importación", test_import),
        ("Ejecutar test básico", run_basic_test),
        ("Crear script de ejemplo", create_example_script),
    ]

    for step_name, step_func in steps:
        print(f"\n{'>' * 3} {step_name}")

        if not step_func():
            print(f"\nERROR: Falló el paso '{step_name}'")
            print("La instalación no se completó correctamente.")
            return False

    print_usage_instructions()

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
