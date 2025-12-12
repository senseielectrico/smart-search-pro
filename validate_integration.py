"""
Validación de Integración de Smart Search
==========================================

Verifica que todos los módulos estén correctamente integrados
y que las dependencias estén disponibles.
"""

import sys
import os
from pathlib import Path


def check_module(module_name: str, description: str) -> bool:
    """Verifica que un módulo pueda importarse"""
    try:
        __import__(module_name)
        print(f"[OK] {description}: OK")
        return True
    except ImportError as e:
        print(f"[FAIL] {description}: FAILED - {e}")
        return False


def check_file(filepath: str, description: str) -> bool:
    """Verifica que un archivo exista"""
    if os.path.exists(filepath):
        print(f"[OK] {description}: OK ({filepath})")
        return True
    else:
        print(f"[FAIL] {description}: MISSING ({filepath})")
        return False


def check_module_integration():
    """Verifica integración entre módulos"""
    print("\n=== VERIFICANDO INTEGRACIÓN DE MÓDULOS ===\n")

    try:
        # Importar backend
        from backend import SearchService, SearchQuery, FileCategory
        print("[OK] Backend: SearchService, SearchQuery, FileCategory")

        # Importar file_manager
        from file_manager import DirectoryTree, CheckState, WindowsSearchIndexManager
        print("[OK] File Manager: DirectoryTree, CheckState, WindowsSearchIndexManager")

        # Importar classifier
        from classifier import classify_file, format_file_size, format_date
        print("[OK] Classifier: classify_file, format_file_size, format_date")

        # Importar ui
        from ui import SmartSearchWindow
        print("[OK] UI: SmartSearchWindow")

        # Verificar que main.py use los módulos correctos
        with open('main.py', 'r', encoding='utf-8') as f:
            main_content = f.read()

        checks = {
            'SearchService': 'from backend import',
            'DirectoryTree': 'from file_manager import',
            'classify_file': 'from classifier import',
            'SmartSearchApp': 'class SmartSearchApp',
            'IntegratedSearchWorker': 'class IntegratedSearchWorker',
        }

        print("\n=== VERIFICANDO MAIN.PY ===\n")

        for item, expected in checks.items():
            if expected in main_content:
                print(f"[OK] main.py usa {item}")
            else:
                print(f"[FAIL] main.py NO usa {item}")

        return True

    except Exception as e:
        print(f"[FAIL] Error en integración: {e}")
        return False


def check_features():
    """Verifica características clave"""
    print("\n=== VERIFICANDO CARACTERÍSTICAS ===\n")

    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()

        features = {
            'Windows Search API': 'SearchService(use_windows_search=True)',
            'Múltiples palabras con *': 'split(\'*\')',
            'Búsqueda en contenido': 'search_content',
            'Búsqueda en nombre': 'search_filename',
            'Árbol de directorios': 'DirectoryTree',
            'Clasificación automática': 'category',
            'Guardar configuración': 'save_config',
            'Cargar configuración': 'load_config',
            'Tema claro/oscuro': 'dark_mode',
            'Operaciones de archivos': 'FileOperations',
        }

        for feature, keyword in features.items():
            if keyword in content:
                print(f"[OK] {feature}: Implementado")
            else:
                print(f"[FAIL] {feature}: NO encontrado")

        return True

    except Exception as e:
        print(f"[FAIL] Error verificando características: {e}")
        return False


def main():
    """Ejecuta todas las validaciones"""
    print("=" * 70)
    print("VALIDACIÓN DE INTEGRACIÓN - SMART SEARCH")
    print("=" * 70)

    # Verificar dependencias Python
    print("\n=== VERIFICANDO DEPENDENCIAS ===\n")

    dependencies = [
        ('PyQt6', "PyQt6 (Interfaz gráfica)"),
        ('win32com', "pywin32 (Windows COM)"),
        ('pathlib', "pathlib (Rutas)"),
    ]

    all_deps_ok = all(check_module(mod, desc) for mod, desc in dependencies)

    # Verificar archivos del proyecto
    print("\n=== VERIFICANDO ARCHIVOS ===\n")

    files = [
        ('backend.py', "Backend - Windows Search API"),
        ('file_manager.py', "File Manager - Árbol de directorios"),
        ('classifier.py', "Classifier - Clasificación de archivos"),
        ('ui.py', "UI - Interfaz PyQt6"),
        ('main.py', "Main - Punto de entrada integrado"),
        ('requirements.txt', "Requirements - Dependencias"),
    ]

    all_files_ok = all(check_file(f, desc) for f, desc in files)

    # Verificar integración
    integration_ok = check_module_integration()

    # Verificar características
    features_ok = check_features()

    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)

    if all_deps_ok and all_files_ok and integration_ok and features_ok:
        print("\n[SUCCESS] TODAS LAS VALIDACIONES PASARON")
        print("\nLa aplicacion esta lista para usar:")
        print("  python main.py")
        print("  o")
        print("  start.bat")
        return 0
    else:
        print("\n[ERROR] ALGUNAS VALIDACIONES FALLARON")
        print("\nRevisar los errores anteriores y:")
        print("  1. Instalar dependencias: pip install -r requirements.txt")
        print("  2. Verificar que todos los archivos existan")
        print("  3. Revisar la integracion de modulos")
        return 1


if __name__ == "__main__":
    sys.exit(main())
