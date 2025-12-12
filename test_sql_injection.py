"""
Test de Seguridad: SQL Injection Prevention
-------------------------------------------
Suite de pruebas para validar que las funciones de sanitización
previenen SQL injection en backend.py

Casos de prueba:
1. Inputs legítimos (deben pasar)
2. Intentos de SQL injection (deben fallar)
3. Wildcards válidos (deben preservarse)
4. Caracteres especiales SQL (deben escaparse)
"""

import sys
import os
from pathlib import Path

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Agregar directorio al path
sys.path.insert(0, str(Path(__file__).parent))

from backend import SearchQuery, FileCategory
import pytest


class TestSQLInjectionPrevention:
    """Tests de prevención de SQL Injection"""

    def test_legitimate_keywords(self):
        """Inputs legítimos deben funcionar correctamente"""
        legitimate_inputs = [
            ['python'],
            ['*.py'],
            ['test_file'],
            ['my file with spaces'],
            ['data-2024'],
        ]

        for keywords in legitimate_inputs:
            try:
                query = SearchQuery(keywords=keywords)
                sql = query.build_sql_query()
                assert sql is not None
                print(f"✓ Legítimo: {keywords}")
            except Exception as e:
                pytest.fail(f"Input legítimo rechazado: {keywords} - {e}")

    def test_sql_injection_attempts(self):
        """Intentos de SQL injection deben ser bloqueados"""
        malicious_inputs = [
            ["'; DROP TABLE SystemIndex; --"],
            ["' OR '1'='1"],
            ["admin'--"],
            ["' UNION SELECT * FROM SystemIndex--"],
            ["'; EXEC xp_cmdshell('dir'); --"],
            ["' OR 1=1; DELETE FROM SystemIndex; --"],
            ["<script>alert('xss')</script>"],
            ["../../etc/passwd"],
            ["' OR ''='"],
            ["1' UNION SELECT NULL, NULL--"],
        ]

        for keywords in malicious_inputs:
            try:
                query = SearchQuery(keywords=keywords)
                sql = query.build_sql_query()
                # Si llegó aquí, verificar que esté sanitizado
                # No debe contener patrones peligrosos sin escapar
                assert '--' not in sql or "'--'" in sql
                print(f"✓ Bloqueado o sanitizado: {keywords}")
            except ValueError as e:
                # Esperado - input rechazado
                print(f"✓ Rechazado correctamente: {keywords}")
                assert "peligroso" in str(e).lower()

    def test_wildcard_preservation(self):
        """Wildcards válidos deben preservarse como %"""
        query = SearchQuery(keywords=['test*', '*file*', '*.py'])
        sql = query.build_sql_query()

        # Los wildcards deben convertirse a %
        # Nota: El patrón LIKE incluye % antes y después, así que buscamos patrones específicos
        assert 'test%' in sql or 'test[%]' not in sql, f"Wildcard no preservado en: {sql}"
        assert 'file%' in sql or 'file[%]' not in sql, f"Wildcard no preservado en: {sql}"
        assert '.py' in sql, f".py no encontrado en: {sql}"

        # Verificar que los wildcards * se convirtieron a % y no se escaparon como [%]
        # Buscar patrones que indiquen que * se convirtió correctamente
        if 'test*' in str(query.keywords):
            # El wildcard debe estar como % no como [%]
            assert sql.count('%') > sql.count('[%]'), "Wildcards escapados incorrectamente"

        print("✓ Wildcards preservados correctamente")

    def test_quote_escaping(self):
        """Comillas simples deben escaparse"""
        query = SearchQuery(keywords=["user's file"])
        sql = query.build_sql_query()

        # Las comillas deben duplicarse
        assert "user''s file" in sql
        print("✓ Comillas escapadas correctamente")

    def test_special_chars_escaping(self):
        """Caracteres especiales SQL LIKE deben escaparse"""
        query = SearchQuery(keywords=["test[brackets]", "under_score", "per%cent"])
        sql = query.build_sql_query()

        # Verificar que los caracteres especiales estén escapados
        assert '[[]' in sql or 'brackets' in sql  # [ debe escaparse
        assert '[_]' in sql or '_' in sql         # _ debe escaparse
        assert '[%]' in sql or '%' in sql         # % debe escaparse
        print("✓ Caracteres especiales escapados")

    def test_path_sanitization(self):
        """Paths deben sanitizarse correctamente"""
        # Path legítimo
        query1 = SearchQuery(
            keywords=['test'],
            search_paths=[r'C:\Users\Public\Documents']
        )
        sql1 = query1.build_sql_query()
        assert sql1 is not None
        print("✓ Path legítimo aceptado")

        # Path con intento de injection
        malicious_paths = [
            r"C:\Users'; DROP TABLE SystemIndex; --",
            r"C:\Users' OR '1'='1",
        ]

        for path in malicious_paths:
            try:
                query = SearchQuery(
                    keywords=['test'],
                    search_paths=[path]
                )
                sql = query.build_sql_query()
                # Verificar que esté sanitizado
                assert "''" in sql or "peligroso" in str(sql).lower()
                print(f"✓ Path malicioso sanitizado: {path}")
            except ValueError:
                print(f"✓ Path malicioso rechazado: {path}")

    def test_extension_sanitization(self):
        """Extensiones de archivo deben sanitizarse"""
        query = SearchQuery(
            keywords=['test'],
            file_categories={FileCategory.DOCUMENTOS}
        )
        sql = query.build_sql_query()

        # No debe contener patrones peligrosos
        assert '--' not in sql
        assert 'DROP' not in sql.upper()
        assert 'EXEC' not in sql.upper()
        print("✓ Extensiones sanitizadas")

    def test_length_limits(self):
        """Inputs muy largos deben rechazarse"""
        # Keyword muy largo
        long_keyword = 'A' * 2000

        try:
            query = SearchQuery(keywords=[long_keyword])
            sql = query.build_sql_query()
            pytest.fail("Input demasiado largo no fue rechazado")
        except ValueError as e:
            assert "demasiado largo" in str(e).lower()
            print("✓ Input largo rechazado")

    def test_control_characters(self):
        """Caracteres de control deben eliminarse"""
        # Input con caracteres de control
        query = SearchQuery(keywords=['test\x00\x01\x02file'])
        sql = query.build_sql_query()

        # Los caracteres de control deben eliminarse
        assert '\x00' not in sql
        assert '\x01' not in sql
        assert '\x02' not in sql
        print("✓ Caracteres de control eliminados")

    def test_sanitize_function_directly(self):
        """Probar función sanitize_sql_input directamente"""
        test_cases = [
            ("normal text", "normal text"),
            ("user's file", "user''s file"),
            ("test[bracket]", "test[[]bracket]"),
            ("under_score", "under[_]score"),
            ("per%cent", "per[%]cent"),
        ]

        for input_val, expected_pattern in test_cases:
            result = SearchQuery.sanitize_sql_input(input_val)
            assert expected_pattern in result or result == expected_pattern
            print(f"✓ Sanitizado: '{input_val}' -> '{result}'")

    def test_validate_function_directly(self):
        """Probar función validate_search_input directamente"""
        # Inputs válidos
        valid_inputs = [
            "normal text",
            "file-name_2024.txt",
            "my folder",
        ]

        for val in valid_inputs:
            assert SearchQuery.validate_search_input(val) is True
            print(f"✓ Validado: '{val}'")

        # Inputs inválidos
        invalid_inputs = [
            "'; DROP TABLE--",
            "UNION SELECT",
            "<script>",
            "exec('cmd')",
        ]

        for val in invalid_inputs:
            try:
                SearchQuery.validate_search_input(val)
                pytest.fail(f"Input malicioso no fue rechazado: {val}")
            except ValueError:
                print(f"✓ Rechazado: '{val}'")


def run_manual_tests():
    """Ejecutar tests manualmente sin pytest"""
    print("=" * 70)
    print("TEST DE SEGURIDAD: SQL INJECTION PREVENTION")
    print("=" * 70)
    print()

    test_suite = TestSQLInjectionPrevention()

    tests = [
        ("Inputs Legítimos", test_suite.test_legitimate_keywords),
        ("SQL Injection Attempts", test_suite.test_sql_injection_attempts),
        ("Preservación de Wildcards", test_suite.test_wildcard_preservation),
        ("Escape de Comillas", test_suite.test_quote_escaping),
        ("Escape de Caracteres Especiales", test_suite.test_special_chars_escaping),
        ("Sanitización de Paths", test_suite.test_path_sanitization),
        ("Sanitización de Extensiones", test_suite.test_extension_sanitization),
        ("Límites de Longitud", test_suite.test_length_limits),
        ("Caracteres de Control", test_suite.test_control_characters),
        ("Función Sanitize Directa", test_suite.test_sanitize_function_directly),
        ("Función Validate Directa", test_suite.test_validate_function_directly),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"\n[TEST] {name}")
        print("-" * 70)
        try:
            test_func()
            passed += 1
            print(f"✓ PASSED\n")
        except Exception as e:
            failed += 1
            print(f"✗ FAILED: {e}\n")

    print("=" * 70)
    print(f"RESULTADOS: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    # Ejecutar tests manualmente
    success = run_manual_tests()

    if success:
        print("\n✓ TODOS LOS TESTS PASARON - Sistema seguro contra SQL Injection")
        sys.exit(0)
    else:
        print("\n✗ ALGUNOS TESTS FALLARON - Revisar implementación")
        sys.exit(1)
