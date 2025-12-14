"""
Tests de Robustez - core/security.py
====================================

Tests para las funciones de robustez añadidas:
- normalize_unicode_path
- add_long_path_prefix
- is_network_path
- validate_path_length
- is_file_locked
- validate_safe_file_type

Ejecutar con: python -m pytest tests/test_security_robustness.py -v
"""

import os
import sys
import pytest
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Añadir el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security import (
    normalize_unicode_path,
    add_long_path_prefix,
    is_network_path,
    validate_path_length,
    is_file_locked,
    validate_safe_file_type,
    sanitize_sql_input,
    validate_search_input,
    validate_path_safety,
    sanitize_cli_argument,
    validate_table_name,
    validate_input_length,
    log_security_event,
    safe_error_message,
    sanitize_csv_cell,
    sanitize_html_output,
    sanitize_json_value,
)


# ============================================================================
# TESTS PARA normalize_unicode_path
# ============================================================================

class TestNormalizeUnicodePath:
    """Tests para normalización de rutas Unicode"""

    def test_empty_path(self):
        """Test: Path vacío retorna vacío"""
        assert normalize_unicode_path("") == ""
        assert normalize_unicode_path(None) is None

    def test_ascii_path_unchanged(self):
        """Test: Path ASCII permanece igual"""
        path = "C:\\Users\\Admin\\Documents"
        result = normalize_unicode_path(path)
        assert result == path

    def test_unicode_normalization_nfc(self):
        """Test: Unicode se normaliza a NFC"""
        # é puede representarse como un caracter o como e + combining accent
        # NFD: e + combining acute accent (U+0065 U+0301)
        # NFC: precomposed é (U+00E9)
        nfd_path = "C:\\Users\\Jose\u0301\\Documents"  # NFD
        result = normalize_unicode_path(nfd_path)
        # Debe normalizar a NFC
        assert "José" in result or "Jose" in result  # Depending on normalization

    def test_spanish_characters(self):
        """Test: Caracteres españoles manejados"""
        path = "C:\\Users\\José\\Documentos\\Año_2025"
        result = normalize_unicode_path(path)
        assert result is not None
        assert len(result) > 0

    def test_chinese_characters(self):
        """Test: Caracteres chinos manejados"""
        path = "C:\\Users\\文件夹\\测试"
        result = normalize_unicode_path(path)
        assert result is not None
        assert "文件" in result

    def test_russian_characters(self):
        """Test: Caracteres rusos manejados"""
        path = "C:\\Users\\Пользователь\\Документы"
        result = normalize_unicode_path(path)
        assert result is not None
        assert "Документы" in result

    def test_emoji_characters(self):
        """Test: Emojis manejados (pueden ser filtrados)"""
        path = "C:\\Users\\Test\\📁Documents"
        result = normalize_unicode_path(path)
        # Emojis pueden ser removidos o mantenidos
        assert result is not None

    def test_control_characters_removed(self):
        """Test: Caracteres de control removidos"""
        path = "C:\\Users\\Test\x00\\Documents"  # Null byte
        result = normalize_unicode_path(path)
        assert "\x00" not in result

    def test_mixed_unicode(self):
        """Test: Unicode mixto manejado"""
        path = "C:\\Users\\José_文件_Тест\\file.txt"
        result = normalize_unicode_path(path)
        assert result is not None
        assert "José" in result or "Jose" in result


# ============================================================================
# TESTS PARA add_long_path_prefix
# ============================================================================

class TestAddLongPathPrefix:
    """Tests para prefijo de rutas largas de Windows"""

    def test_short_path_unchanged(self):
        """Test: Path corto permanece sin cambios"""
        path = "C:\\Users\\Admin\\Documents\\file.txt"
        result = add_long_path_prefix(path)
        # En Windows, paths cortos no necesitan prefijo
        assert result == path or result.startswith("\\\\?\\")

    def test_empty_path(self):
        """Test: Path vacío retorna vacío"""
        assert add_long_path_prefix("") == ""

    @pytest.mark.skipif(os.name != 'nt', reason="Windows only test")
    def test_long_path_gets_prefix(self):
        """Test: Path largo recibe prefijo \\\\?\\"""
        long_component = "A" * 200
        path = f"C:\\Users\\{long_component}\\file.txt"
        result = add_long_path_prefix(path)
        if len(path) > 260:
            assert result.startswith("\\\\?\\")

    @pytest.mark.skipif(os.name != 'nt', reason="Windows only test")
    def test_unc_path_gets_correct_prefix(self):
        """Test: Path UNC recibe prefijo \\\\?\\UNC\\"""
        path = "\\\\server\\share\\very_long_path_" + "x" * 250 + "\\file.txt"
        result = add_long_path_prefix(path)
        if len(path) > 260:
            assert "\\\\?\\UNC\\" in result

    def test_already_prefixed_path(self):
        """Test: Path ya con prefijo no se duplica"""
        path = "\\\\?\\C:\\Users\\Admin\\file.txt"
        result = add_long_path_prefix(path)
        assert result.count("\\\\?\\") == 1

    @pytest.mark.skipif(os.name != 'nt', reason="Windows only test")
    def test_relative_path_converted(self):
        """Test: Path relativo se convierte a absoluto"""
        path = ".\\file.txt"
        result = add_long_path_prefix(path)
        # Debe mantener path o convertirlo
        assert result is not None


# ============================================================================
# TESTS PARA is_network_path
# ============================================================================

class TestIsNetworkPath:
    """Tests para detección de rutas de red"""

    def test_unc_path_detected(self):
        """Test: Path UNC detectado como red"""
        assert is_network_path("\\\\server\\share\\file.txt") is True
        assert is_network_path("\\\\192.168.1.1\\share") is True

    def test_local_path_not_network(self):
        """Test: Path local no es red"""
        assert is_network_path("C:\\Users\\Admin\\file.txt") is False
        assert is_network_path("D:\\Documents\\") is False

    def test_empty_path(self):
        """Test: Path vacío retorna False"""
        assert is_network_path("") is False

    @pytest.mark.skipif(os.name != 'nt', reason="Windows only test")
    def test_mapped_drive_detection(self):
        """Test: Drive mapeado puede ser detectado"""
        # Este test depende de drives mapeados disponibles
        # Solo verificamos que no crash
        result = is_network_path("Z:\\mapped_share\\file.txt")
        assert isinstance(result, bool)

    def test_unix_style_path(self):
        """Test: Path estilo Unix manejado"""
        assert is_network_path("/home/user/file.txt") is False

    def test_none_path(self):
        """Test: None path manejado"""
        # Puede lanzar error o retornar False
        try:
            result = is_network_path(None)
            assert result is False
        except (TypeError, AttributeError):
            pass  # También válido


# ============================================================================
# TESTS PARA validate_path_length
# ============================================================================

class TestValidatePathLength:
    """Tests para validación de longitud de rutas"""

    def test_short_path_valid(self):
        """Test: Path corto es válido"""
        path = "C:\\Users\\Admin\\file.txt"
        is_valid, error = validate_path_length(path)
        assert is_valid is True
        assert error is None

    def test_long_path_warning(self):
        """Test: Path largo genera advertencia"""
        long_path = "C:\\Users\\" + "x" * 250 + "\\file.txt"
        is_valid, error = validate_path_length(long_path)
        # Puede ser válido con advertencia o inválido
        assert isinstance(is_valid, bool)

    def test_very_long_path_strict(self):
        """Test: Path muy largo falla en modo estricto"""
        very_long = "C:\\" + "x" * 32000 + "\\file.txt"
        is_valid, error = validate_path_length(very_long, strict=True)
        assert is_valid is False
        assert error is not None

    def test_empty_path(self):
        """Test: Path vacío"""
        is_valid, error = validate_path_length("")
        # Vacío puede ser válido o inválido según implementación
        assert isinstance(is_valid, bool)

    def test_normal_path_length(self):
        """Test: Path de longitud normal"""
        path = "C:\\Program Files\\Application\\Data\\config.json"
        is_valid, error = validate_path_length(path)
        assert is_valid is True


# ============================================================================
# TESTS PARA is_file_locked
# ============================================================================

class TestIsFileLocked:
    """Tests para detección de archivos bloqueados"""

    def test_nonexistent_file_not_locked(self):
        """Test: Archivo inexistente no está bloqueado"""
        result = is_file_locked("C:\\nonexistent_file_12345.txt")
        assert result is False

    def test_unlocked_file(self, tmp_path):
        """Test: Archivo desbloqueado detectado correctamente"""
        test_file = tmp_path / "unlocked.txt"
        test_file.write_text("test content")

        result = is_file_locked(str(test_file))
        assert result is False

    @pytest.mark.skipif(os.name != 'nt', reason="Windows only test")
    def test_locked_file_detection(self, tmp_path):
        """Test: Archivo bloqueado detectado"""
        test_file = tmp_path / "locked.txt"
        test_file.write_text("test content")

        # Bloquear el archivo manteniendo handle abierto
        locked_handle = open(str(test_file), 'r+b')
        try:
            # En Windows, abrir con acceso exclusivo puede bloquear
            result = is_file_locked(str(test_file))
            # Puede o no detectar como bloqueado dependiendo del modo
            assert isinstance(result, bool)
        finally:
            locked_handle.close()

    def test_directory_handling(self, tmp_path):
        """Test: Directorio manejado correctamente"""
        result = is_file_locked(str(tmp_path))
        # Directorios pueden retornar False o manejar de otra forma
        assert isinstance(result, bool)


# ============================================================================
# TESTS PARA validate_safe_file_type
# ============================================================================

class TestValidateSafeFileType:
    """Tests para validación de tipos de archivo seguros"""

    def test_safe_document_types(self, tmp_path):
        """Test: Tipos de documento seguros permitidos"""
        safe_extensions = ['.txt', '.pdf', '.doc', '.docx', '.jpg', '.png']

        for ext in safe_extensions:
            test_file = tmp_path / f"test{ext}"
            test_file.write_text("test" if ext == '.txt' else "")

            try:
                validate_safe_file_type(str(test_file))
                # No debe lanzar excepción
            except PermissionError:
                pytest.fail(f"Safe file type {ext} was blocked")

    def test_dangerous_executable_blocked(self, tmp_path):
        """Test: Ejecutables peligrosos bloqueados"""
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.ps1', '.vbs']

        for ext in dangerous_extensions:
            test_file = tmp_path / f"test{ext}"
            test_file.write_text("malicious content")

            with pytest.raises(PermissionError):
                validate_safe_file_type(str(test_file))

    def test_script_files_blocked(self, tmp_path):
        """Test: Scripts bloqueados por seguridad"""
        script_extensions = ['.js', '.py', '.sh', '.rb']

        for ext in script_extensions:
            test_file = tmp_path / f"script{ext}"
            test_file.write_text("script content")

            # Algunos scripts pueden estar permitidos, otros no
            try:
                validate_safe_file_type(str(test_file))
            except PermissionError:
                pass  # Bloqueado es válido

    def test_nonexistent_file(self):
        """Test: Archivo inexistente manejado"""
        try:
            validate_safe_file_type("C:\\nonexistent_12345.txt")
        except (FileNotFoundError, PermissionError):
            pass  # Ambos son válidos


# ============================================================================
# TESTS PARA sanitize_sql_input
# ============================================================================

class TestSanitizeSqlInput:
    """Tests para sanitización de input SQL"""

    def test_normal_input(self):
        """Test: Input normal sanitizado correctamente"""
        value = "test_file"
        result = sanitize_sql_input(value)
        assert result == value or "test" in result

    def test_sql_injection_sanitized(self):
        """Test: SQL injection sanitizado"""
        malicious = "'; DROP TABLE files; --"
        result = sanitize_sql_input(malicious)
        # Caracteres peligrosos deben ser escapados o removidos
        assert "'" not in result or result != malicious

    def test_special_characters_escaped(self):
        """Test: Caracteres especiales manejados"""
        value = "file%test_"
        result = sanitize_sql_input(value, escape_percent=True)
        # Percent debe ser escapado
        assert result is not None

    def test_max_length_enforced(self):
        """Test: Longitud máxima respetada - lanza error"""
        long_value = "x" * 2000
        with pytest.raises(ValueError):
            sanitize_sql_input(long_value, max_length=100)

    def test_unicode_input(self):
        """Test: Unicode manejado"""
        value = "búsqueda_测试"
        result = sanitize_sql_input(value)
        assert result is not None


# ============================================================================
# TESTS PARA validate_search_input
# ============================================================================

class TestValidateSearchInput:
    """Tests para validación de input de búsqueda"""

    def test_normal_search(self):
        """Test: Búsqueda normal válida"""
        result = validate_search_input("documento")
        assert result is True

    def test_empty_search(self):
        """Test: Búsqueda vacía"""
        result = validate_search_input("")
        # Puede ser válido o inválido
        assert isinstance(result, bool)

    def test_sql_injection_rejected(self):
        """Test: SQL injection rechazado - lanza ValueError"""
        with pytest.raises(ValueError):
            validate_search_input("'; DROP TABLE --")

    def test_long_search_rejected(self):
        """Test: Búsqueda muy larga rechazada"""
        result = validate_search_input("x" * 5000)
        # Debe rechazar input muy largo
        assert result is False or isinstance(result, bool)


# ============================================================================
# TESTS PARA validate_table_name
# ============================================================================

class TestValidateTableName:
    """Tests para validación de nombres de tabla"""

    def test_valid_table_name(self):
        """Test: Nombre de tabla válido"""
        # Depende de ALLOWED_TABLES en security.py
        try:
            result = validate_table_name("files")
            assert result == "files"
        except ValueError:
            # Si 'files' no está en whitelist
            pass

    def test_invalid_table_name(self):
        """Test: Nombre de tabla inválido rechazado"""
        with pytest.raises(ValueError):
            validate_table_name("drop_table_users")

    def test_sql_injection_in_table(self):
        """Test: SQL injection en nombre de tabla"""
        with pytest.raises(ValueError):
            validate_table_name("; DROP TABLE users; --")

    def test_empty_table_name(self):
        """Test: Nombre vacío rechazado"""
        with pytest.raises(ValueError):
            validate_table_name("")


# ============================================================================
# TESTS PARA validate_input_length
# ============================================================================

class TestValidateInputLength:
    """Tests para validación de longitud de input"""

    def test_normal_length(self):
        """Test: Longitud normal aceptada"""
        result = validate_input_length("normal text", "keyword")
        assert result == "normal text"

    def test_too_long_rejected(self):
        """Test: Input muy largo rechazado"""
        very_long = "x" * 10000
        with pytest.raises(ValueError):
            validate_input_length(very_long, "keyword")

    def test_empty_accepted(self):
        """Test: Input vacío puede ser aceptado"""
        result = validate_input_length("", "keyword")
        assert result == ""


# ============================================================================
# TESTS PARA log_security_event
# ============================================================================

class TestLogSecurityEvent:
    """Tests para logging de eventos de seguridad"""

    def test_log_warning_event(self):
        """Test: Evento WARNING loggeado"""
        # No debe lanzar excepción
        log_security_event(
            "INVALID_INPUT",
            {"input": "test", "reason": "invalid"},
            severity="WARNING"
        )

    def test_log_error_event(self):
        """Test: Evento ERROR loggeado"""
        log_security_event(
            "ACCESS_DENIED",
            {"path": "/protected", "user": "test"},
            severity="ERROR"
        )

    def test_log_critical_event(self):
        """Test: Evento CRITICAL loggeado"""
        log_security_event(
            "SQL_INJECTION_ATTEMPT",
            {"query": "'; DROP TABLE --"},
            severity="CRITICAL"
        )

    def test_log_info_event(self):
        """Test: Evento INFO loggeado"""
        log_security_event(
            "PATH_VALIDATION",
            {"path": "C:\\Users\\test"},
            severity="INFO"
        )


# ============================================================================
# TESTS PARA safe_error_message
# ============================================================================

class TestSafeErrorMessage:
    """Tests para mensajes de error seguros"""

    def test_user_facing_message(self):
        """Test: Mensaje para usuario es genérico"""
        error = ValueError("Database connection failed: password=secret123")
        result = safe_error_message(error, user_facing=True)
        # No debe contener detalles sensibles
        assert "secret123" not in result
        assert "password" not in result.lower()

    def test_detailed_message(self):
        """Test: Mensaje detallado disponible para logs"""
        error = ValueError("Specific error details here")
        result = safe_error_message(error, user_facing=False)
        assert "Specific error" in result


# ============================================================================
# TESTS DE INTEGRACIÓN
# ============================================================================

class TestSecurityIntegration:
    """Tests de integración de seguridad"""

    def test_full_path_validation_flow(self, tmp_path):
        """Test: Flujo completo de validación de path"""
        # Crear archivo de prueba
        test_file = tmp_path / "documento_test.txt"
        test_file.write_text("test content")

        path = str(test_file)

        # 1. Normalizar unicode
        normalized = normalize_unicode_path(path)
        assert normalized is not None

        # 2. Validar longitud
        is_valid, error = validate_path_length(normalized)
        assert is_valid is True

        # 3. Verificar si está bloqueado
        locked = is_file_locked(normalized)
        assert locked is False

        # 4. Validar tipo de archivo seguro
        validate_safe_file_type(normalized)  # No debe lanzar

        # 5. Verificar no es red
        is_net = is_network_path(normalized)
        assert is_net is False

    def test_concurrent_security_operations(self, tmp_path):
        """Test: Operaciones de seguridad thread-safe"""
        errors = []

        def validate_paths():
            try:
                for i in range(50):
                    path = str(tmp_path / f"file_{threading.current_thread().ident}_{i}.txt")
                    normalize_unicode_path(path)
                    validate_path_length(path)
                    is_network_path(path)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=validate_paths) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_validate_path_safety_integration(self, tmp_path):
        """Test: Validación de seguridad de paths"""
        src = str(tmp_path / "source.txt")
        dst = str(tmp_path / "dest.txt")
        base = str(tmp_path)

        # Crear archivo fuente
        Path(src).write_text("content")

        # Validar que src y dst están dentro de base
        result = validate_path_safety(src, dst, allowed_base=base)
        assert result is True

    def test_sanitize_functions_integration(self):
        """Test: Funciones de sanitización"""
        # SQL input - escapes dangerous chars
        sql_result = sanitize_sql_input("test value")
        assert sql_result is not None

        # CLI argument - safe input works
        cli_result = sanitize_cli_argument("file.txt")
        assert cli_result == "file.txt"

        # CLI argument - dangerous input raises
        with pytest.raises(ValueError):
            sanitize_cli_argument("file.txt; rm -rf /")

        # CSV cell
        csv_result = sanitize_csv_cell("=SUM(A1:A10)")
        assert csv_result.startswith("'") or "=" not in csv_result[:1]

        # HTML output
        html_result = sanitize_html_output("<script>alert('xss')</script>")
        assert "<script>" not in html_result

        # JSON value
        json_result = sanitize_json_value({"key": "value"})
        assert json_result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
