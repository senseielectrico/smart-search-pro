"""
Script de prueba para validar la seguridad contra Path Traversal en file_manager.py

Este script prueba varios escenarios de ataque y valida que la función
validate_path_safety() los detecte y bloquee correctamente.
"""

import os
import sys
import tempfile
from pathlib import Path

# Importar el módulo a probar
from file_manager import validate_path_safety, PROTECTED_PATHS


def test_path_traversal_attack():
    """Prueba detección de path traversal con secuencias '..'"""
    print("\n=== Test 1: Path Traversal Attack (..) ===")

    # Crear archivos temporales para pruebas
    with tempfile.NamedTemporaryFile(delete=False) as src_file:
        src_path = src_file.name

    try:
        # Caso 1: Intento de path traversal
        dst_path = r"..\..\..\..\Windows\System32\evil.exe"
        try:
            validate_path_safety(src_path, dst_path)
            print("FAIL: Path traversal no fue detectado")
            return False
        except PermissionError as e:
            print(f"PASS: Path traversal bloqueado - {e}")

        # Caso 2: Intento de path traversal con path absoluto
        dst_path = r"C:\temp\..\..\..\Windows\System32\evil.exe"
        try:
            validate_path_safety(src_path, dst_path)
            print("FAIL: Path traversal con path absoluto no fue detectado")
            return False
        except PermissionError as e:
            print(f"PASS: Path traversal absoluto bloqueado - {e}")

        return True

    finally:
        # Limpiar
        if os.path.exists(src_path):
            os.remove(src_path)


def test_protected_paths():
    """Prueba protección de directorios del sistema"""
    print("\n=== Test 2: Protected System Paths ===")

    # Crear archivo temporal para pruebas
    with tempfile.NamedTemporaryFile(delete=False) as src_file:
        src_path = src_file.name

    try:
        success = True

        # Probar cada path protegido
        protected_tests = [
            r"C:\Windows\test.txt",
            r"C:\Windows\System32\evil.dll",
            r"C:\Program Files\test.exe",
            r"C:\Program Files (x86)\test.exe",
        ]

        for dst_path in protected_tests:
            try:
                validate_path_safety(src_path, dst_path)
                print(f"FAIL: Acceso a {dst_path} no fue bloqueado")
                success = False
            except PermissionError as e:
                print(f"PASS: Path protegido bloqueado - {dst_path}")

        return success

    finally:
        # Limpiar
        if os.path.exists(src_path):
            os.remove(src_path)


def test_allowed_base_restriction():
    """Prueba restricción a directorio base específico"""
    print("\n=== Test 3: Allowed Base Directory Restriction ===")

    # Crear directorio temporal
    with tempfile.TemporaryDirectory() as temp_dir:
        # Crear archivo de prueba
        src_path = os.path.join(temp_dir, "test_src.txt")
        with open(src_path, 'w') as f:
            f.write("test")

        try:
            # Caso 1: Destino dentro del directorio permitido (debe pasar)
            dst_path = os.path.join(temp_dir, "subdir", "test_dst.txt")
            try:
                validate_path_safety(src_path, dst_path, allowed_base=temp_dir)
                print(f"PASS: Destino dentro de allowed_base permitido")
            except PermissionError as e:
                print(f"FAIL: Destino válido fue bloqueado - {e}")
                return False

            # Caso 2: Destino fuera del directorio permitido (debe fallar)
            dst_path = r"C:\temp\outside.txt"
            try:
                validate_path_safety(src_path, dst_path, allowed_base=temp_dir)
                print("FAIL: Destino fuera de allowed_base no fue bloqueado")
                return False
            except PermissionError as e:
                print(f"PASS: Destino fuera de allowed_base bloqueado")

            return True

        finally:
            # Limpiar archivo de prueba
            if os.path.exists(src_path):
                os.remove(src_path)


def test_absolute_path_injection():
    """Prueba inyección de paths absolutos maliciosos"""
    print("\n=== Test 4: Absolute Path Injection ===")

    with tempfile.NamedTemporaryFile(delete=False) as src_file:
        src_path = src_file.name

    try:
        # Intentos de inyección con paths absolutos a directorios críticos
        malicious_paths = [
            r"C:\Windows\System32\drivers\etc\hosts",
            r"C:\Windows\System32\config\SAM",
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup\evil.exe",
        ]

        success = True
        for dst_path in malicious_paths:
            try:
                validate_path_safety(src_path, dst_path)
                print(f"FAIL: Path malicioso no bloqueado - {dst_path}")
                success = False
            except PermissionError as e:
                print(f"PASS: Path malicioso bloqueado - {dst_path}")

        return success

    finally:
        if os.path.exists(src_path):
            os.remove(src_path)


def test_valid_operations():
    """Prueba que operaciones legítimas sigan funcionando"""
    print("\n=== Test 5: Valid Operations Should Pass ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Crear archivo de prueba
        src_path = os.path.join(temp_dir, "test_src.txt")
        with open(src_path, 'w') as f:
            f.write("test content")

        try:
            # Caso 1: Copia normal en el mismo directorio
            dst_path = os.path.join(temp_dir, "test_dst.txt")
            try:
                validate_path_safety(src_path, dst_path)
                print("PASS: Operación válida en mismo directorio")
            except PermissionError as e:
                print(f"FAIL: Operación válida fue bloqueada - {e}")
                return False

            # Caso 2: Copia a subdirectorio
            subdir = os.path.join(temp_dir, "subdir")
            os.makedirs(subdir, exist_ok=True)
            dst_path = os.path.join(subdir, "test_dst.txt")
            try:
                validate_path_safety(src_path, dst_path)
                print("PASS: Operación válida a subdirectorio")
            except PermissionError as e:
                print(f"FAIL: Operación válida a subdirectorio fue bloqueada - {e}")
                return False

            # Caso 3: Copia a directorio temporal del usuario
            user_temp = tempfile.gettempdir()
            dst_path = os.path.join(user_temp, "test_dst.txt")
            try:
                validate_path_safety(src_path, dst_path)
                print("PASS: Operación válida a directorio temporal")
            except PermissionError as e:
                print(f"FAIL: Operación válida a temp fue bloqueada - {e}")
                return False

            return True

        finally:
            if os.path.exists(src_path):
                os.remove(src_path)


def test_nonexistent_source():
    """Prueba que se detecten archivos origen inexistentes"""
    print("\n=== Test 6: Non-existent Source File ===")

    src_path = r"C:\nonexistent\source.txt"
    dst_path = r"C:\temp\destination.txt"

    try:
        validate_path_safety(src_path, dst_path)
        print("FAIL: Archivo origen inexistente no fue detectado")
        return False
    except FileNotFoundError as e:
        print(f"PASS: Archivo origen inexistente detectado - {e}")
        return True
    except Exception as e:
        print(f"FAIL: Excepción inesperada - {e}")
        return False


def main():
    """Ejecuta todas las pruebas de seguridad"""
    print("=" * 70)
    print("PRUEBAS DE SEGURIDAD - Path Traversal Protection")
    print("=" * 70)

    tests = [
        ("Path Traversal Attack", test_path_traversal_attack),
        ("Protected System Paths", test_protected_paths),
        ("Allowed Base Restriction", test_allowed_base_restriction),
        ("Absolute Path Injection", test_absolute_path_injection),
        ("Valid Operations", test_valid_operations),
        ("Non-existent Source", test_nonexistent_source),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\nERROR en {test_name}: {e}")
            results.append((test_name, False))

    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN DE PRUEBAS")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {test_name}")

    print(f"\nResultado: {passed}/{total} pruebas pasadas")

    if passed == total:
        print("\nTODAS LAS PRUEBAS DE SEGURIDAD PASARON")
        return 0
    else:
        print(f"\nALGUNAS PRUEBAS FALLARON ({total - passed} fallos)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
