"""
Pruebas de integración para validar que FileOperations usa validate_path_safety
"""

import os
import sys
import tempfile
from file_manager import FileOperations


def test_copy_file_security():
    """Prueba que copy_file bloquee paths maliciosos"""
    print("\n=== Test: FileOperations.copy_file Security ===")

    with tempfile.NamedTemporaryFile(delete=False, mode='w') as src_file:
        src_file.write("test content")
        src_path = src_file.name

    try:
        # Caso 1: Intento de copiar a System32
        dst_path = r"C:\Windows\System32\evil.dll"
        result = FileOperations.copy_file(src_path, dst_path)
        if result:
            print("FAIL: copy_file permitió escritura en System32")
            return False
        else:
            print("PASS: copy_file bloqueó escritura en System32")

        # Caso 2: Intento de path traversal
        dst_path = r"..\..\..\Windows\evil.exe"
        result = FileOperations.copy_file(src_path, dst_path)
        if result:
            print("FAIL: copy_file permitió path traversal")
            return False
        else:
            print("PASS: copy_file bloqueó path traversal")

        # Caso 3: Operación válida
        with tempfile.TemporaryDirectory() as temp_dir:
            dst_path = os.path.join(temp_dir, "valid_copy.txt")
            result = FileOperations.copy_file(src_path, dst_path)
            if result and os.path.exists(dst_path):
                print("PASS: copy_file permitió operación válida")
                return True
            else:
                print("FAIL: copy_file bloqueó operación válida")
                return False

    finally:
        if os.path.exists(src_path):
            os.remove(src_path)


def test_move_file_security():
    """Prueba que move_file bloquee paths maliciosos"""
    print("\n=== Test: FileOperations.move_file Security ===")

    with tempfile.NamedTemporaryFile(delete=False, mode='w') as src_file:
        src_file.write("test content")
        src_path = src_file.name

    try:
        # Caso 1: Intento de mover a Program Files
        dst_path = r"C:\Program Files\evil.exe"
        result = FileOperations.move_file(src_path, dst_path)
        if result:
            print("FAIL: move_file permitió escritura en Program Files")
            return False
        else:
            print("PASS: move_file bloqueó escritura en Program Files")

        # Verificar que el archivo origen sigue existiendo (no se movió)
        if not os.path.exists(src_path):
            print("FAIL: move_file eliminó el archivo origen a pesar de fallar")
            return False

        return True

    finally:
        if os.path.exists(src_path):
            os.remove(src_path)


def test_copy_directory_security():
    """Prueba que copy_directory bloquee paths maliciosos"""
    print("\n=== Test: FileOperations.copy_directory Security ===")

    with tempfile.TemporaryDirectory() as src_dir:
        # Crear estructura de prueba
        test_file = os.path.join(src_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")

        # Caso 1: Intento de copiar a Windows
        dst_path = r"C:\Windows\malicious_dir"
        result = FileOperations.copy_directory(src_dir, dst_path)
        if result:
            print("FAIL: copy_directory permitió escritura en Windows")
            return False
        else:
            print("PASS: copy_directory bloqueó escritura en Windows")

        # Caso 2: Operación válida
        with tempfile.TemporaryDirectory() as temp_dst:
            dst_path = os.path.join(temp_dst, "valid_copy")
            result = FileOperations.copy_directory(src_dir, dst_path)
            if result and os.path.exists(os.path.join(dst_path, "test.txt")):
                print("PASS: copy_directory permitió operación válida")
                return True
            else:
                print("FAIL: copy_directory bloqueó operación válida")
                return False


def test_move_directory_security():
    """Prueba que move_directory bloquee paths maliciosos"""
    print("\n=== Test: FileOperations.move_directory Security ===")

    with tempfile.TemporaryDirectory() as temp_parent:
        # Crear directorio a mover
        src_dir = os.path.join(temp_parent, "src_dir")
        os.makedirs(src_dir)
        test_file = os.path.join(src_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")

        # Caso 1: Intento de mover a System32
        dst_path = r"C:\Windows\System32\malicious_dir"
        result = FileOperations.move_directory(src_dir, dst_path)
        if result:
            print("FAIL: move_directory permitió escritura en System32")
            return False
        else:
            print("PASS: move_directory bloqueó escritura en System32")

        # Verificar que el directorio origen sigue existiendo
        if not os.path.exists(src_dir):
            print("FAIL: move_directory eliminó el directorio origen a pesar de fallar")
            return False

        return True


def main():
    """Ejecuta todas las pruebas de integración"""
    print("=" * 70)
    print("PRUEBAS DE INTEGRACION - FileOperations Security")
    print("=" * 70)

    tests = [
        ("copy_file Security", test_copy_file_security),
        ("move_file Security", test_move_file_security),
        ("copy_directory Security", test_copy_directory_security),
        ("move_directory Security", test_move_directory_security),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\nERROR en {test_name}: {e}")
            import traceback
            traceback.print_exc()
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
        print("\nTODAS LAS PRUEBAS DE INTEGRACION PASARON")
        return 0
    else:
        print(f"\nALGUNAS PRUEBAS FALLARON ({total - passed} fallos)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
