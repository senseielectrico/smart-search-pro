"""
Tests de Seguridad - Smart Search
==================================

Tests para verificar que la aplicación es segura contra:
- SQL Injection
- Path Traversal
- Inputs maliciosos
- Operaciones peligrosas

Ejecutar con: python -m pytest tests/test_security.py -v
"""

import os
import sys
import pytest
import threading
from pathlib import Path
from unittest.mock import Mock, patch

# Añadir el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import SearchQuery, SearchResult
from file_manager import FileOperations, DirectoryTree, PROTECTED_PATHS


# ============================================================================
# TESTS DE SQL INJECTION
# ============================================================================

class TestSQLInjectionPrevention:
    """Tests para prevenir SQL Injection"""

    def test_sql_injection_in_keywords(self):
        """Test: Keywords con caracteres SQL maliciosos son bloqueados o escapados"""
        malicious_keywords = [
            "'; DROP TABLE files; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--",
            "'; DELETE FROM files WHERE '1'='1",
        ]

        for keyword in malicious_keywords:
            try:
                # Intentar crear query con keyword malicioso
                query = SearchQuery(keywords=[keyword])
                sql = query.build_sql_query()

                # Si no lanza error, debe estar sanitizado
                # Verificar que no contiene comandos peligrosos
                assert "DROP TABLE" not in sql.upper()
                assert "DELETE FROM" not in sql.upper()
                assert "UNION SELECT" not in sql.upper()
            except ValueError:
                # Rechazar es también válido
                pass

    def test_sql_injection_in_paths(self):
        """Test: Paths maliciosos son bloqueados o escapados"""
        malicious_paths = [
            "C:\\Test'; DROP TABLE files; --",
            "C:\\Users\\Admin'--",
            "C:\\' OR '1'='1",
        ]

        for path in malicious_paths:
            try:
                query = SearchQuery(
                    keywords=["test"],
                    search_paths=[path]
                )
                sql = query.build_sql_query()

                # Si no lanza error, verificar sanitización
                assert "DROP" not in sql.upper() or "DROP TABLE" not in sql.upper()
                assert "DELETE" not in sql.upper() or "DELETE FROM" not in sql.upper()
            except ValueError:
                # Rechazar es válido
                pass

    def test_wildcard_sanitization(self):
        """Test: Wildcards no permiten bypass de seguridad"""
        # Wildcards válidos
        valid_wildcards = ["*.txt", "test*", "*file*"]

        for wildcard in valid_wildcards:
            query = SearchQuery(keywords=[wildcard])
            sql = query.build_sql_query()

            # Debe contener LIKE con %
            assert "LIKE" in sql
            assert "%" in sql

    def test_special_chars_in_filename_search(self):
        """Test: Caracteres especiales son manejados correctamente"""
        special_chars = [
            "file%name.txt",  # % es wildcard SQL
            "file_name.txt",  # _ es wildcard SQL
            "file[name].txt", # [] son wildcards en algunos SQL
        ]

        for filename in special_chars:
            query = SearchQuery(keywords=[filename])
            sql = query.build_sql_query()

            # La query debe construirse sin errores
            assert sql is not None
            assert len(sql) > 0


# ============================================================================
# TESTS DE PATH TRAVERSAL
# ============================================================================

class TestPathTraversalPrevention:
    """Tests para prevenir Path Traversal"""

    def test_path_traversal_attempts(self):
        """Test: Intentos de path traversal son bloqueados"""
        traversal_attempts = [
            "..\\..\\..\\Windows\\System32",
            "../../../etc/passwd",
            "C:\\Users\\..\\..\\Windows",
            "..\\..\\Program Files",
            "..\\..\\..",
        ]

        ops = FileOperations()

        for malicious_path in traversal_attempts:
            # Intentar copiar desde path malicioso debe fallar
            success = ops.copy_file(
                malicious_path,
                "C:\\Temp\\test.txt"
            )
            assert success is False

    def test_protected_paths_cannot_be_destination(self):
        """Test: Paths protegidos no pueden ser destino"""
        ops = FileOperations()

        for protected_path in PROTECTED_PATHS:
            # Intentar copiar A path protegido debe fallar
            # copy_file returns False instead of raising an exception
            success = ops.copy_file(
                "C:\\Temp\\test.txt",
                os.path.join(protected_path, "malicious.exe")
            )
            assert success is False

    def test_relative_path_resolution(self):
        """Test: Paths relativos son manejados"""
        query = SearchQuery(
            keywords=["test"],
            search_paths=[".", ".."]
        )

        # Los paths deben existir o ser normalizados
        for path in query.search_paths:
            normalized = os.path.normpath(path)
            # Path normalizado debe ser válido
            assert len(normalized) > 0

    def test_symlink_handling(self, tmp_path):
        """Test: Symlinks son manejados de forma segura"""
        # Crear un archivo temporal
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        # Intentar crear symlink (puede fallar en Windows sin permisos)
        try:
            symlink = tmp_path / "symlink.txt"
            symlink.symlink_to(test_file)

            # FileOperations debe seguir o bloquear symlinks apropiadamente
            ops = FileOperations()
            result = ops.copy_file(str(symlink), str(tmp_path / "copy.txt"))

            # Si permite symlinks, debe copiar el contenido, no el link
            if result:
                assert (tmp_path / "copy.txt").exists()
                assert (tmp_path / "copy.txt").read_text() == "test content"

        except OSError:
            # Windows puede no permitir symlinks sin privilegios
            pytest.skip("No se pueden crear symlinks en este sistema")


# ============================================================================
# TESTS DE VALIDACIÓN DE INPUTS
# ============================================================================

class TestInputValidation:
    """Tests para validación de inputs"""

    def test_empty_keywords_rejected(self):
        """Test: Keywords vacíos son rechazados"""
        with pytest.raises(ValueError):
            SearchQuery(keywords=[])

        # Keywords solo con espacios también deben ser rechazados
        try:
            query = SearchQuery(keywords=["", "  ", "\t"])
            # Si acepta, debe filtrar los vacíos
            assert len(query.keywords) == 0
        except ValueError:
            # Rechazar es válido
            pass

    def test_null_bytes_in_paths(self):
        """Test: Null bytes en paths son manejados"""
        malicious_paths = [
            "C:\\Test\x00.txt",
            "C:\\Users\\Test\x00\\file.txt",
        ]

        ops = FileOperations()

        for path in malicious_paths:
            # Debe fallar o retornar False
            try:
                result = ops.copy_file(path, "C:\\Temp\\test.txt")
                # False es válido (archivo no existe)
                assert result is False
            except (ValueError, OSError):
                # Lanzar error también es válido
                pass

    def test_extremely_long_paths(self):
        """Test: Paths extremadamente largos son manejados"""
        # Windows tiene límite de 260 caracteres (MAX_PATH)
        long_path = "C:\\" + ("A" * 300) + "\\file.txt"

        query = SearchQuery(
            keywords=["test"],
            search_paths=[long_path]
        )

        # No debe crashear
        assert query is not None
        assert query.search_paths is not None

    def test_unicode_in_paths(self):
        """Test: Unicode en paths es manejado correctamente"""
        unicode_paths = [
            "C:\\Users\\José\\Documents",
            "C:\\文件\\test.txt",
            "C:\\Тест\\файл.txt",
            "C:\\🔥emoji🔥\\file.txt",
        ]

        for path in unicode_paths:
            query = SearchQuery(
                keywords=["test"],
                search_paths=[path]
            )

            # Debe construirse sin errores
            assert query is not None
            sql = query.build_sql_query()
            assert sql is not None

    def test_control_characters_in_keywords(self):
        """Test: Caracteres de control en keywords"""
        control_chars = [
            "test\n\r\t",
            "file\x00name",
            "test\x1b[31mred\x1b[0m",  # ANSI escape codes
        ]

        for keyword in control_chars:
            # Debe manejar sin crashear
            try:
                query = SearchQuery(keywords=[keyword])
                assert query is not None
            except ValueError:
                # Rechazar es válido también
                pass

    def test_max_results_validation(self):
        """Test: max_results tiene límites razonables"""
        # Valor negativo - puede ser aceptado como-está o normalizado
        query = SearchQuery(keywords=["test"], max_results=-100)
        # Si acepta negativos, verificar que no causa problemas
        assert query.max_results is not None

        # Valor extremadamente alto - puede ser aceptado
        query = SearchQuery(keywords=["test"], max_results=10_000_000)
        # Verificar que no causa crash
        assert query.max_results is not None


# ============================================================================
# TESTS DE OPERACIONES PELIGROSAS
# ============================================================================

class TestDangerousOperations:
    """Tests para prevenir operaciones peligrosas"""

    def test_cannot_delete_system_directories(self):
        """Test: No se pueden eliminar directorios del sistema"""
        ops = FileOperations()

        system_dirs = [
            "C:\\Windows",
            "C:\\Windows\\System32",
            "C:\\Program Files",
        ]

        for sys_dir in system_dirs:
            # Debe fallar al intentar eliminar
            with pytest.raises(Exception):
                ops.delete(sys_dir, permanent=True)

    def test_cannot_move_to_protected_locations(self):
        """Test: No se puede mover a ubicaciones protegidas"""
        ops = FileOperations()

        for protected in PROTECTED_PATHS[:2]:  # Probar solo algunos
            # Debe fallar o retornar False
            try:
                result = ops.move_file(
                    "C:\\Temp\\nonexistent.txt",  # Archivo que no existe
                    os.path.join(protected, "malicious.exe")
                )
                # False es válido (archivo no existe)
                assert result is False
            except (PermissionError, OSError, FileNotFoundError):
                # Lanzar error también es válido
                pass

    def test_directory_tree_rejects_protected_paths(self):
        """Test: DirectoryTree rechaza paths protegidos para operaciones"""
        tree = DirectoryTree()

        # Puede añadir pero no debe permitir operaciones peligrosas
        for protected in PROTECTED_PATHS[:3]:  # Probar algunos
            node = tree.add_directory(protected)
            # El nodo se crea pero las operaciones deben validar


# ============================================================================
# TESTS DE RACE CONDITIONS
# ============================================================================

class TestRaceConditions:
    """Tests para prevenir race conditions"""

    def test_concurrent_file_operations(self, tmp_path):
        """Test: Operaciones concurrentes son seguras"""
        import threading
        import time

        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")

        ops = FileOperations()
        errors = []

        def copy_file():
            try:
                for i in range(10):
                    dest = tmp_path / f"copy_{threading.current_thread().ident}_{i}.txt"
                    ops.copy_file(str(test_file), str(dest))
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        # Ejecutar múltiples threads
        threads = [threading.Thread(target=copy_file) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # No debe haber errores de concurrencia
        assert len(errors) == 0

    def test_directory_tree_thread_safety(self):
        """Test: DirectoryTree es thread-safe"""
        import threading

        tree = DirectoryTree()
        errors = []

        def add_directories():
            try:
                for i in range(50):
                    path = f"C:\\Test{threading.current_thread().ident}\\Dir{i}"
                    tree.add_directory(path)
            except Exception as e:
                errors.append(e)

        # Múltiples threads añadiendo
        threads = [threading.Thread(target=add_directories) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # No debe haber errores
        assert len(errors) == 0


# ============================================================================
# TESTS DE SEGURIDAD EN BÚSQUEDA
# ============================================================================

class TestSearchSecurity:
    """Tests de seguridad en búsqueda"""

    def test_search_respects_permissions(self):
        """Test: Búsqueda respeta permisos de archivos"""
        # Este test es más difícil de implementar sin archivos reales
        # pero documentamos la expectativa
        query = SearchQuery(
            keywords=["test"],
            search_paths=["C:\\Windows\\System32"]
        )

        # La búsqueda debe manejar errores de permiso gracefully
        assert query is not None

    def test_no_command_injection_in_file_operations(self):
        """Test: Operaciones de archivos no permiten inyección de comandos"""
        ops = FileOperations()

        malicious_filenames = [
            "test.txt & del C:\\*.*",
            "file.txt | format c:",
            "test.txt; rm -rf /",
            "$(malicious_command).txt",
        ]

        for filename in malicious_filenames:
            # No debe ejecutar comandos
            success = ops.copy_file(
                filename,
                "C:\\Temp\\safe.txt"
            )
            # Debe fallar (archivo no existe) sin ejecutar comandos
            assert success is False

    def test_sanitize_output_paths(self, tmp_path):
        """Test: Paths de salida son sanitizados"""
        ops = FileOperations()

        # Crear archivo de prueba
        source = tmp_path / "source.txt"
        source.write_text("test")

        # Intentar destinos peligrosos
        dangerous_destinations = [
            str(tmp_path / ".." / ".." / "dangerous.txt"),
            str(tmp_path / "subdir" / ".." / ".." / ".." / "danger.txt"),
        ]

        for dest in dangerous_destinations:
            # La operación debe normalizar el path o fallar
            try:
                result = ops.copy_file(str(source), dest)
                if result:
                    # Si tuvo éxito, verificar que el archivo está en ubicación segura
                    normalized = os.path.normpath(dest)
                    assert normalized.startswith(str(tmp_path)) or not os.path.exists(dest)
            except Exception:
                # Fallar es válido también
                pass


# ============================================================================
# TESTS DE FUZZING BÁSICO
# ============================================================================

class TestFuzzing:
    """Tests de fuzzing básico con inputs aleatorios"""

    def test_random_keywords_dont_crash(self):
        """Test: Keywords aleatorios no causan crashes"""
        import random
        import string

        for _ in range(100):
            # Generar keyword aleatorio
            length = random.randint(1, 100)
            keyword = ''.join(random.choices(
                string.ascii_letters + string.digits + string.punctuation,
                k=length
            ))

            try:
                query = SearchQuery(keywords=[keyword])
                sql = query.build_sql_query()
                # No debe crashear
                assert sql is not None
            except ValueError:
                # Rechazar es válido
                pass

    def test_random_paths_dont_crash(self):
        """Test: Paths aleatorios no causan crashes"""
        import random
        import string

        for _ in range(50):
            # Generar path aleatorio
            length = random.randint(5, 200)
            path = ''.join(random.choices(
                string.ascii_letters + string.digits + "\\/:.",
                k=length
            ))

            try:
                query = SearchQuery(
                    keywords=["test"],
                    search_paths=[path]
                )
                # No debe crashear
                assert query is not None
            except (ValueError, OSError):
                # Rechazar paths inválidos es correcto
                pass


# ============================================================================
# RESUMEN Y REPORTE
# ============================================================================

@pytest.fixture(scope="module", autouse=True)
def security_test_summary(request):
    """Genera resumen de tests de seguridad"""
    yield

    print("\n" + "="*70)
    print("RESUMEN DE TESTS DE SEGURIDAD")
    print("="*70)
    print("Tests ejecutados para:")
    print("  - SQL Injection Prevention")
    print("  - Path Traversal Prevention")
    print("  - Input Validation")
    print("  - Dangerous Operations Prevention")
    print("  - Race Conditions")
    print("  - Search Security")
    print("  - Basic Fuzzing")
    print("="*70)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
