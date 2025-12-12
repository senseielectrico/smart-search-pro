"""
Test suite for security fixes.

Tests all critical security vulnerabilities that were patched:
1. SQL Injection (CVE-001)
2. Path Traversal (CVE-002)
3. Command Injection (CVE-003)
4. Database Input Validation (CVE-004)
5. Export Module Injection (CVE-005)
6. Elevation Handler (CVE-006)
"""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


class TestSQLInjectionPrevention:
    """Test SQL injection prevention (CVE-001)."""

    def test_dangerous_patterns_rejected(self):
        """Test that dangerous SQL patterns are rejected."""
        from core.security import validate_search_input

        malicious_inputs = [
            "'; DROP TABLE users; --",  # Has 'drop ' keyword
            "test; DELETE FROM search_history",  # Has ';' and 'delete '
            "test UNION SELECT * FROM users",  # Has 'union '
            "test<script>",  # Has '<'
            "test exec('code')",  # Has 'exec'
        ]

        for input_val in malicious_inputs:
            with pytest.raises(ValueError) as exc_info:
                validate_search_input(input_val)
            assert "dangerous pattern" in str(exc_info.value).lower()

    def test_sanitize_sql_input(self):
        """Test SQL input sanitization."""
        from core.security import sanitize_sql_input

        # Test quote escaping
        assert sanitize_sql_input("test'value") == "test''value"

        # Test wildcard escaping
        assert sanitize_sql_input("test%value") == "test[%]value"
        assert sanitize_sql_input("test_value") == "test[_]value"

        # Test bracket escaping
        assert sanitize_sql_input("test[value]") == "test[[]value]"

    def test_wildcard_preservation(self):
        """Test that wildcards are preserved when escape_percent=False."""
        from core.security import sanitize_sql_input

        result = sanitize_sql_input("test%", escape_percent=False)
        assert "%" in result
        assert "[%]" not in result


class TestPathTraversalPrevention:
    """Test path traversal prevention (CVE-002)."""

    def test_dangerous_patterns_blocked(self):
        """Test that dangerous path patterns are blocked."""
        from core.security import validate_path_safety

        # Create a safe source file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            safe_src = tmp.name

        try:
            malicious_paths = [
                r"C:\Temp\..\Windows\System32\config",
                r"C:\Users\Public\..\..\..\Windows",
            ]

            for path in malicious_paths:
                with pytest.raises(PermissionError):
                    validate_path_safety(safe_src, path)
        finally:
            if os.path.exists(safe_src):
                os.remove(safe_src)

    def test_protected_paths_blocked(self):
        """Test that protected system paths are blocked."""
        from core.security import validate_path_safety, PROTECTED_PATHS
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            safe_src = tmp.name

        try:
            # Test only a few protected paths that don't have special chars
            test_protected = [
                r'C:\Windows',
                r'C:\Program Files',
                r'C:\Recovery',
            ]
            for protected in test_protected:
                test_path = os.path.join(protected, "test.txt")
                with pytest.raises(PermissionError) as exc_info:
                    validate_path_safety(safe_src, test_path)
                # Check that error message mentions protection
                assert "protected" in str(exc_info.value).lower() or "denied" in str(exc_info.value).lower()
        finally:
            if os.path.exists(safe_src):
                os.remove(safe_src)

    def test_safe_paths_allowed(self):
        """Test that safe paths are allowed."""
        from core.security import validate_path_safety
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            src = os.path.join(tmpdir, "source.txt")
            dst = os.path.join(tmpdir, "dest.txt")

            # Create source file
            with open(src, "w") as f:
                f.write("test")

            # Should not raise
            assert validate_path_safety(src, dst)


class TestCommandInjectionPrevention:
    """Test command injection prevention (CVE-003)."""

    def test_dangerous_characters_rejected(self):
        """Test that dangerous CLI characters are rejected."""
        from core.security import sanitize_cli_argument

        malicious_args = [
            '"; calc.exe; "',
            "test & whoami",
            "test | dir",
            "test;ls",
            "test<file.txt",
            "test>output.txt",
        ]

        for arg in malicious_args:
            with pytest.raises(ValueError, match="dangerous character"):
                sanitize_cli_argument(arg)

    def test_safe_arguments_allowed(self):
        """Test that safe arguments are allowed."""
        from core.security import sanitize_cli_argument

        safe_args = [
            "test",
            "--verbose",
            "--output=file.txt",
            "C:\\Users\\Test\\file.txt",
        ]

        for arg in safe_args:
            # Should not raise
            assert sanitize_cli_argument(arg) == arg

    def test_subprocess_path_validation(self):
        """Test subprocess path validation."""
        from core.security import validate_subprocess_path
        import tempfile

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            safe_path = tmp.name

        try:
            # Should not raise
            validated = validate_subprocess_path(safe_path)
            assert validated.exists()
        finally:
            if os.path.exists(safe_path):
                os.remove(safe_path)


class TestDatabaseValidation:
    """Test database input validation (CVE-004)."""

    def test_invalid_table_names_rejected(self):
        """Test that invalid table names are rejected."""
        from core.security import validate_table_name

        invalid_tables = [
            "users; DROP TABLE users; --",
            "test_table' OR '1'='1",
            "../../../etc/passwd",
            "unknown_table",  # Not in whitelist
        ]

        for table in invalid_tables:
            with pytest.raises(ValueError):
                validate_table_name(table)

    def test_valid_table_names_allowed(self):
        """Test that valid table names are allowed."""
        from core.security import validate_table_name

        valid_tables = [
            "search_history",
            "saved_searches",
            "hash_cache",
            "file_tags",
        ]

        for table in valid_tables:
            # Should not raise
            assert validate_table_name(table) == table


class TestExportSanitization:
    """Test export module sanitization (CVE-005)."""

    def test_csv_injection_prevention(self):
        """Test CSV injection prevention."""
        from core.security import sanitize_csv_cell

        dangerous_values = [
            "=1+1",
            "+cmd|'/c calc.exe'!A1",
            "@SUM(A1:A10)",
            "-2+3+cmd|' /C calc'!A0",
        ]

        for value in dangerous_values:
            sanitized = sanitize_csv_cell(value)
            # Should be prefixed with single quote
            assert sanitized.startswith("'")
            assert sanitized == f"'{value}"

    def test_html_xss_prevention(self):
        """Test HTML XSS prevention."""
        from core.security import sanitize_html_output

        dangerous_values = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "test&<>\"'",
        ]

        for value in dangerous_values:
            sanitized = sanitize_html_output(value)
            # Should not contain dangerous characters
            assert "<script>" not in sanitized
            assert "<img" not in sanitized
            assert "&lt;" in sanitized or "&gt;" in sanitized or "&quot;" in sanitized

    def test_json_value_sanitization(self):
        """Test JSON value sanitization."""
        from core.security import sanitize_json_value
        import math

        # Test NaN/Inf handling
        assert sanitize_json_value(float('nan')) is None
        assert sanitize_json_value(float('inf')) is None

        # Test Path object handling
        from pathlib import Path
        path = Path("C:\\test\\file.txt")
        assert isinstance(sanitize_json_value(path), str)

        # Test None handling
        assert sanitize_json_value(None) is None


class TestElevationSecurity:
    """Test elevation handler security (CVE-006)."""

    def test_cli_argument_sanitization(self):
        """Test that CLI arguments are sanitized."""
        from core.security import sanitize_cli_argument

        # Test single-dash rejection (security measure)
        with pytest.raises(ValueError, match="Single-dash"):
            sanitize_cli_argument("-v")

        # Test double-dash acceptance
        assert sanitize_cli_argument("--verbose") == "--verbose"

    def test_length_validation(self):
        """Test input length validation."""
        from core.security import validate_input_length

        # Test exceeding max length
        long_value = "a" * 10000
        with pytest.raises(ValueError, match="too long"):
            validate_input_length(long_value, "search_query")

        # Test within max length
        short_value = "test"
        assert validate_input_length(short_value, "search_query") == short_value


class TestSecurityLogging:
    """Test security event logging."""

    def test_security_event_logging(self):
        """Test that security events are logged."""
        from core.security import log_security_event, SecurityEvent

        # Should not raise
        log_security_event(
            SecurityEvent.SQL_INJECTION_ATTEMPT,
            {"input": "test' OR '1'='1", "source": "test"},
            severity="WARNING"
        )


def run_tests():
    """Run all security tests."""
    import subprocess

    print("=" * 70)
    print("SECURITY FIXES TEST SUITE")
    print("=" * 70)
    print()

    # Run pytest
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=False
    )

    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
