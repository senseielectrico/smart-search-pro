# SECURITY FIXES IMPLEMENTATION GUIDE
## Smart Search Pro - Quick Reference

**Date:** 2025-12-12
**Priority:** CRITICAL - Implement immediately

---

## CRITICAL FIXES - IMPLEMENT FIRST

### Fix 1: SQL Injection Prevention (backend.py)

**Location:** `backend.py`, lines 246-351
**Severity:** CRITICAL
**Estimated Time:** 2-3 hours

**Implementation:**

```python
# File: backend.py
# Replace build_sql_query() method

def build_sql_query(self) -> str:
    """Construye la consulta SQL para Windows Search - SECURE VERSION."""
    conditions = []

    if self.search_filename:
        filename_conditions = []
        for keyword in self.keywords:
            # 1. VALIDATE input first
            self.validate_search_input(keyword)

            # 2. Sanitize with proper escaping
            # Convert * to % for wildcards
            keyword_pattern = keyword.replace('*', '%')

            # 3. Escape SQL special characters
            # CRITICAL: Escape % as [%], _ as [_], [ as [[]
            sanitized = keyword_pattern.replace('[', '[[]')
            sanitized = sanitized.replace('%', '[%]')
            sanitized = sanitized.replace('_', '[_]')
            sanitized = sanitized.replace("'", "''")

            # 4. Use parameterized-style construction
            # Note: Windows Search doesn't support full parameterization,
            # but we ensure all inputs are properly escaped
            filename_conditions.append(
                f"System.FileName LIKE '{sanitized}'"
            )

        if filename_conditions:
            conditions.append(f"({' OR '.join(filename_conditions)})")

    # ... rest of method with same sanitization pattern ...
```

**Testing:**
```python
# Test with malicious inputs
test_inputs = [
    "test' OR '1'='1",
    "test%' AND 1=1 --",
    "'; DROP TABLE users; --"
]

for input_val in test_inputs:
    try:
        query = SearchQuery(keywords=[input_val])
        sql = query.build_sql_query()
        print(f"Input: {input_val}")
        print(f"SQL: {sql}")
        # Should not contain unescaped quotes or SQL commands
        assert "OR '1'='1" not in sql
        assert "DROP TABLE" not in sql
        print("✓ PASS")
    except ValueError as e:
        print(f"✓ Rejected: {e}")
```

---

### Fix 2: Path Traversal Protection (file_manager.py)

**Location:** `file_manager.py`, lines 446-504
**Severity:** CRITICAL
**Estimated Time:** 3-4 hours

**Implementation:**

```python
# File: file_manager.py
# Replace validate_path_safety() function

import re
from pathlib import Path

# Enhanced protected paths list
PROTECTED_PATHS = [
    r'C:\Windows',
    r'C:\Windows\System32',
    r'C:\Windows\SysWOW64',
    r'C:\Program Files',
    r'C:\Program Files (x86)',
    r'C:\ProgramData\Microsoft',
    r'C:\Users\All Users',
    r'C:\$Recycle.Bin',
    r'C:\System Volume Information',
    r'C:\Recovery',
    r'C:\PerfLogs',
    r'C:\Boot',
    r'C:\Config.Msi',
]

DANGEROUS_PATH_PATTERNS = [
    r'\.\.',           # Parent directory traversal
    r'~',              # User expansion
    r'\$[A-Za-z]',     # Environment variables
    r'file://',        # URI schemes
    r'\\\\localhost',  # Localhost UNC
]

def validate_path_safety(src: str, dst: str, allowed_base: Optional[str] = None) -> bool:
    """
    Enhanced path validation with multiple security layers.

    Args:
        src: Source path
        dst: Destination path
        allowed_base: Optional base directory restriction

    Returns:
        True if safe

    Raises:
        PermissionError: If unsafe path detected
        FileNotFoundError: If source doesn't exist
    """
    try:
        # 1. Check for dangerous patterns BEFORE resolution
        for pattern in DANGEROUS_PATH_PATTERNS:
            if re.search(pattern, dst, re.IGNORECASE):
                logger.warning(f"Dangerous path pattern detected: {pattern} in {dst}")
                security_logger.log_security_event(
                    SecurityEvent.PATH_TRAVERSAL_ATTEMPT,
                    {'source': src, 'destination': dst, 'pattern': pattern},
                    severity="ERROR"
                )
                raise PermissionError(f"Dangerous path pattern not allowed: {pattern}")

        # 2. Resolve paths (handles symlinks and relative paths)
        try:
            src_path = Path(src).resolve(strict=True)  # Must exist
            dst_path = Path(dst).resolve(strict=False)  # May not exist yet
        except (RuntimeError, OSError) as e:
            raise PermissionError(f"Path resolution failed: {e}")

        # 3. Convert to absolute and normalize
        src_real = src_path.absolute()
        dst_real = dst_path.absolute()

        # 4. Validate source exists
        if not src_real.exists():
            raise FileNotFoundError(f"Source path does not exist: {src}")

        # 5. Check destination against protected paths
        for protected in PROTECTED_PATHS:
            try:
                protected_path = Path(protected).resolve(strict=False).absolute()

                # Check if destination is within protected path
                dst_real.relative_to(protected_path)

                # If we get here, dst is within protected path - DENY
                logger.warning(f"Attempt to access protected path: {dst_real} -> {protected}")
                security_logger.log_security_event(
                    SecurityEvent.ACCESS_DENIED,
                    {'source': str(src_real), 'destination': str(dst_real), 'protected': protected},
                    severity="ERROR"
                )
                raise PermissionError(f"Access to protected directory denied: {protected}")

            except ValueError:
                # ValueError means dst is NOT within protected path - OK
                continue

        # 6. If allowed_base specified, enforce it
        if allowed_base:
            try:
                allowed_path = Path(allowed_base).resolve(strict=False).absolute()
                dst_real.relative_to(allowed_path)
            except ValueError:
                logger.warning(f"Destination outside allowed base: {dst_real} not in {allowed_base}")
                raise PermissionError(f"Destination must be within {allowed_base}")

        # 7. Prevent source == destination
        if src_real == dst_real:
            raise PermissionError("Source and destination cannot be the same")

        # 8. Check disk space
        if src_real.is_file():
            import shutil
            src_size = src_real.stat().st_size
            dst_drive = dst_real.drive if dst_real.drive else dst_real.parts[0]
            try:
                free_space = shutil.disk_usage(dst_drive).free
                if src_size > free_space:
                    raise PermissionError(f"Insufficient disk space: {src_size} bytes needed, {free_space} available")
            except Exception as e:
                logger.warning(f"Could not check disk space: {e}")

        logger.debug(f"Path validation passed: {src} -> {dst}")
        return True

    except (PermissionError, FileNotFoundError) as e:
        # Re-raise security exceptions
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error in path validation: {e}")
        raise PermissionError(f"Path validation failed: {e}")
```

**Testing:**
```python
# Test suite for path validation
def test_path_traversal_protection():
    """Test various path traversal attempts."""
    test_cases = [
        # (src, dst, should_pass)
        (r"C:\Temp\test.txt", r"C:\Temp\backup\test.txt", True),
        (r"C:\Temp\test.txt", r"C:\Temp\..\Temp\test.txt", True),  # Resolves to valid path
        (r"C:\Temp\test.txt", r"C:\Windows\System32\test.txt", False),
        (r"C:\Temp\test.txt", r"C:\Program Files\test.txt", False),
        (r"C:\Temp\test.txt", r"C:\Temp\..\..\Windows\test.txt", False),
        (r"C:\Temp\test.txt", r"\\localhost\c$\Windows\test.txt", False),
    ]

    for src, dst, should_pass in test_cases:
        # Create test source file
        Path(src).parent.mkdir(parents=True, exist_ok=True)
        Path(src).touch()

        try:
            result = validate_path_safety(src, dst)
            if should_pass:
                print(f"✓ PASS: {dst} allowed as expected")
            else:
                print(f"✗ FAIL: {dst} should have been blocked!")
        except PermissionError as e:
            if not should_pass:
                print(f"✓ PASS: {dst} blocked as expected - {e}")
            else:
                print(f"✗ FAIL: {dst} should have been allowed! - {e}")
        finally:
            # Cleanup
            try:
                Path(src).unlink()
            except:
                pass
```

---

### Fix 3: Command Injection Prevention (file_manager.py & backend.py)

**Location:** `file_manager.py` line 742, `backend.py` line 756
**Severity:** CRITICAL
**Estimated Time:** 2 hours

**Implementation:**

```python
# File: file_manager.py
# Replace open_location() method in FileOperations class

import subprocess
from pathlib import Path

def open_location_safe(filepath: str) -> bool:
    """
    Safely opens file location in explorer.

    Args:
        filepath: Path to file

    Returns:
        True if successful

    Raises:
        ValueError: If path is invalid
        PermissionError: If path is protected
    """
    try:
        # 1. Validate and resolve path
        path = Path(filepath).resolve(strict=True)

        # 2. Security validation
        validate_path_safety(str(path), str(path))

        # 3. Execute command safely
        # CRITICAL: Use list format (NOT string concatenation)
        # CRITICAL: shell=False (NEVER use shell=True)
        if path.is_dir():
            # Open directory
            result = subprocess.run(
                ['explorer', str(path)],
                check=True,
                timeout=5,
                shell=False,  # CRITICAL: Prevents command injection
                capture_output=True,
                text=True
            )
        else:
            # Open parent and select file
            # Windows explorer handles /select, properly
            result = subprocess.run(
                ['explorer', '/select,', str(path)],
                check=True,
                timeout=5,
                shell=False,
                capture_output=True,
                text=True
            )

        logger.info(f"Opened location: {path}")
        return True

    except subprocess.TimeoutExpired:
        logger.error(f"Timeout opening location: {filepath}")
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to open location: {e.stderr}")
        raise
    except FileNotFoundError:
        logger.error(f"Path not found: {filepath}")
        raise
    except Exception as e:
        logger.error(f"Error opening location: {e}")
        raise
```

**Testing:**
```python
def test_command_injection_prevention():
    """Test command injection is prevented."""
    # Create test file
    test_dir = Path(r"C:\Temp\security_test")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / "test.txt"
    test_file.write_text("test")

    # These should all be safe
    safe_paths = [
        str(test_file),
        str(test_dir),
    ]

    for path in safe_paths:
        try:
            # Should not raise exception
            open_location_safe(path)
            print(f"✓ Safe path handled: {path}")
        except Exception as e:
            print(f"✗ Error with safe path: {e}")

    # Malicious paths should be blocked by path validation
    malicious_paths = [
        r'C:\Temp\test.txt" & calc.exe & "',
        r'C:\Temp\test.txt"; whoami; "',
        r'C:\Temp\test.txt | dir',
    ]

    for path in malicious_paths:
        try:
            open_location_safe(path)
            print(f"✗ FAIL: Malicious path not blocked: {path}")
        except Exception as e:
            print(f"✓ PASS: Malicious path blocked: {path} - {e}")

    # Cleanup
    test_file.unlink()
    test_dir.rmdir()
```

---

## HIGH PRIORITY FIXES

### Fix 4: Database Table Name Validation (core/database.py)

**Location:** `core/database.py`, lines 519-585
**Severity:** HIGH
**Estimated Time:** 1-2 hours

**Implementation:**

```python
# File: core/database.py
# Add at the top of the Database class

import re

# Whitelist of allowed tables
ALLOWED_TABLES = {
    'search_history',
    'saved_searches',
    'hash_cache',
    'file_tags',
    'settings',
    'operation_history',
    'preview_cache',
    'schema_version'
}

@staticmethod
def validate_table_name(table: str) -> str:
    """
    Validate table name against whitelist.

    Args:
        table: Table name to validate

    Returns:
        Validated table name

    Raises:
        ValueError: If table name is invalid
    """
    table = table.strip()

    # Check whitelist
    if table not in ALLOWED_TABLES:
        logger.warning(f"Attempt to access non-whitelisted table: {table}")
        security_logger.log_security_event(
            SecurityEvent.INVALID_INPUT,
            {'table': table, 'allowed': list(ALLOWED_TABLES)},
            severity="WARNING"
        )
        raise ValueError(f"Table not allowed: {table}")

    # Additional format validation
    if not re.match(r'^[a-z_][a-z0-9_]*$', table):
        raise ValueError(f"Invalid table name format: {table}")

    return table

# Update insert(), update(), delete() methods:

def insert(self, table: str, data: dict[str, Any]) -> int:
    """Insert row into table with validation."""
    table = self.validate_table_name(table)  # VALIDATE
    # ... rest of method unchanged ...

def update(self, table: str, data: dict[str, Any], where: str,
           where_params: tuple[Any, ...] | None = None) -> int:
    """Update rows with validation."""
    table = self.validate_table_name(table)  # VALIDATE
    # ... rest of method unchanged ...

def delete(self, table: str, where: str,
           where_params: tuple[Any, ...] | None = None) -> int:
    """Delete rows with validation."""
    table = self.validate_table_name(table)  # VALIDATE
    # ... rest of method unchanged ...
```

---

### Fix 5: Export Module Input Sanitization

**Locations:** `export/csv_exporter.py`, `export/html_exporter.py`, `export/json_exporter.py`
**Severity:** HIGH
**Estimated Time:** 2-3 hours

**CSV Exporter Fix:**

```python
# File: export/csv_exporter.py
# Add function before CSVExporter class

def sanitize_csv_cell(value) -> str:
    """
    Sanitize CSV cell to prevent formula injection.

    Args:
        value: Cell value

    Returns:
        Sanitized value
    """
    if value is None:
        return ""

    value = str(value)

    # Formula injection characters
    dangerous_chars = ['=', '+', '-', '@', '|', '%', '0x09', '0x0D']

    # If starts with dangerous char, prefix with single quote
    if value and value[0] in dangerous_chars:
        return "'" + value

    # Remove newlines and carriage returns
    value = value.replace('\r', '').replace('\n', ' ')

    # Limit length
    if len(value) > 32767:  # Excel cell limit
        value = value[:32764] + "..."

    return value

# In CSVExporter._export_direct() method:
def _export_direct(self, results: List, output_path: Path) -> None:
    """Export with sanitization."""
    with open(output_path, "w", newline="", encoding=self.encoding) as f:
        writer = self._create_writer(f)

        if self.config.include_headers:
            writer.writerow(self.config.columns)

        total = len(results)
        for i, result in enumerate(results):
            # SANITIZE each cell
            row = [
                sanitize_csv_cell(self._format_value(result, col))
                for col in self.config.columns
            ]
            writer.writerow(row)

            if i % 100 == 0:
                self._report_progress(i + 1, total, "Writing CSV")

        self._report_progress(total, total, "CSV export complete")
```

**HTML Exporter Fix:**

```python
# File: export/html_exporter.py
import html

# In HTMLExporter._html_table() method:
def _html_table(self, results: List) -> str:
    """Generate results table with XSS protection."""
    # Build header (column names are trusted)
    header_cells = []
    for col in self.config.columns:
        label = col.replace("_", " ").title()
        header_cells.append(f"<th onclick='sortTable({len(header_cells)})'>{html.escape(label)}</th>")

    header = "<tr>" + "".join(header_cells) + "</tr>"

    # Build rows
    rows = []
    for result in results:
        cells = []
        for col in self.config.columns:
            value = self._format_value(result, col)

            # CRITICAL: HTML escape ALL user content
            value_escaped = html.escape(str(value), quote=True)

            # Add icon for filename (icon class is from whitelist)
            if col == "filename" and self.include_icons:
                icon_class = self._get_icon_class(result)
                # Validate icon class
                allowed_icons = {
                    'folder-icon', 'file-icon', 'image-icon',
                    'video-icon', 'audio-icon', 'archive-icon', 'code-icon'
                }
                if icon_class in allowed_icons:
                    value_escaped = f'<span class="{icon_class}"></span>{value_escaped}'

            # Make path clickable (but sanitized)
            if col == "full_path" and value:
                try:
                    # Validate path before creating link
                    validated_path = Path(value).resolve()
                    # Double escape for URL
                    path_url = html.escape(str(validated_path), quote=True)
                    value_escaped = f'<a href="file:///{path_url}" style="color: var(--accent-color);">{value_escaped}</a>'
                except:
                    # If path validation fails, just show escaped value
                    pass

            cells.append(f"<td>{value_escaped}</td>")

        rows.append("<tr>" + "".join(cells) + "</tr>")

    # ... rest of method ...
```

---

## DEPLOYMENT CHECKLIST

### Pre-Deployment

- [ ] Backup current production code
- [ ] Review all changes with team
- [ ] Test all fixes in isolated environment
- [ ] Run security test suite
- [ ] Document changes in CHANGELOG.md

### Deployment

- [ ] Deploy to staging environment
- [ ] Run full regression test suite
- [ ] Conduct manual security testing
- [ ] Monitor logs for errors
- [ ] Deploy to production

### Post-Deployment

- [ ] Monitor security logs for 24 hours
- [ ] Verify all functionality works as expected
- [ ] Update user documentation
- [ ] Schedule follow-up security audit in 1 month

---

## TESTING COMMANDS

Run these commands after implementing fixes:

```bash
# Run security-specific tests
pytest tests/test_security_*.py -v

# Run full test suite
pytest tests/ -v --cov=. --cov-report=html

# Static analysis
bandit -r . -ll -i

# Dependency check
safety check

# Type checking
mypy backend.py core/ export/ operations/
```

---

## MONITORING

Add these logging statements to track security events:

```python
# Example: In validate_path_safety()
logger.info(f"Path validation: {src} -> {dst}")

# In SQL query building
logger.debug(f"Built SQL query: {query[:100]}...")

# In file operations
logger.info(f"File operation: {operation_type} {src} -> {dst}")
```

Monitor these log files:
- `logs/security_events.log` - Security-specific events
- `logs/application.log` - General application logs
- `logs/operations.log` - File operation logs

---

## SUPPORT

For questions or issues during implementation:
1. Review full SECURITY_AUDIT.md report
2. Check test cases in each fix
3. Consult team lead before making architectural changes

---

**Implementation Status Tracking:**

| Fix # | Component | Status | Tested | Deployed |
|-------|-----------|--------|--------|----------|
| 1 | SQL Injection | ⬜ | ⬜ | ⬜ |
| 2 | Path Traversal | ⬜ | ⬜ | ⬜ |
| 3 | Command Injection | ⬜ | ⬜ | ⬜ |
| 4 | Table Validation | ⬜ | ⬜ | ⬜ |
| 5 | Export Sanitization | ⬜ | ⬜ | ⬜ |

**Target Completion Date:** 2025-12-15
**Responsible Team:** Security & Development
