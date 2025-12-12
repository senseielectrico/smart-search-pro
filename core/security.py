"""
Security module for Smart Search Pro.

Provides centralized input validation, sanitization, and security utilities
to prevent SQL injection, path traversal, command injection, and other attacks.
"""

import os
import re
import html
import math
import logging
from pathlib import Path
from typing import Any, Optional, List, Set

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

# Protected system paths (Windows)
PROTECTED_PATHS: List[str] = [
    r'C:\Windows',
    r'C:\Program Files',
    r'C:\Program Files (x86)',
    r'C:\ProgramData\Microsoft',
    r'C:\System Volume Information',
    r'C:\Recovery',
    r'C:\$Recycle.Bin',
]

# Dangerous path patterns
DANGEROUS_PATH_PATTERNS: List[str] = [
    r'\.\.',           # Parent directory
    r'~',              # User expansion (except Windows paths)
    r'file://',        # URI schemes
    r'\\\\localhost',  # UNC paths to localhost
]

# Allowed table names for database operations
ALLOWED_TABLES: Set[str] = {
    'search_history',
    'saved_searches',
    'hash_cache',
    'file_tags',
    'settings',
    'operation_history',
    'preview_cache',
    'schema_version',
    # Notes system tables
    'notes',
    'notes_fts',
    'note_categories',
    'note_tags',
    'note_versions'
}

# Maximum input lengths
MAX_LENGTHS = {
    'filename': 255,
    'path': 32767,  # Windows max path with long path support
    'search_query': 1000,
    'table_name': 64,
    'column_name': 64,
    'cli_argument': 8192,
}

# Dangerous characters for CLI arguments
DANGEROUS_CLI_CHARS: List[str] = ['&', '|', ';', '<', '>', '^', '`', '\n', '\r']


# ============================================================================
# SQL INJECTION PREVENTION
# ============================================================================

def sanitize_sql_input(value: str, max_length: int = 1000, escape_percent: bool = True) -> str:
    """
    Sanitize input to prevent SQL injection.

    Args:
        value: Value to sanitize
        max_length: Maximum allowed length
        escape_percent: If True, escape % (SQL wildcard)

    Returns:
        Sanitized string

    Raises:
        ValueError: If input contains dangerous patterns or is too long
    """
    if not value:
        return ""

    # Validate length
    if len(value) > max_length:
        raise ValueError(f"Input too long: {len(value)} > {max_length}")

    # Remove control characters (except spaces and tabs)
    sanitized = ''.join(
        char for char in value
        if char.isprintable() or char in (' ', '\t')
    )

    # Escape single quotes by doubling them (SQL standard)
    sanitized = sanitized.replace("'", "''")

    # Escape SQL LIKE special characters
    # In Windows Search, these must be escaped with []
    sanitized = sanitized.replace('[', '[[]')  # Escape [ first

    # Escape % only if specified (allows preserving wildcards)
    if escape_percent:
        sanitized = sanitized.replace('%', '[%]')

    sanitized = sanitized.replace('_', '[_]')

    return sanitized


def validate_search_input(value: str) -> bool:
    """
    Validate that input doesn't contain dangerous patterns.

    Args:
        value: Value to validate

    Returns:
        True if valid

    Raises:
        ValueError: If contains dangerous patterns
    """
    if not value:
        return True

    # Common SQL injection patterns
    dangerous_patterns = [
        '--',           # SQL comments
        '/*',           # Multi-line comments
        '*/',           # Multi-line comments
        'xp_',          # Extended procedures
        'sp_',          # System procedures
        ';',            # Command separator
        'exec',         # Command execution
        'execute',      # Command execution
        'drop ',        # DROP TABLE/DATABASE
        'delete ',      # DELETE FROM
        'insert ',      # INSERT INTO
        'update ',      # UPDATE
        'union ',       # UNION SELECT
        'script',       # Script tags
        '<',            # HTML/XML tags
        '>',            # HTML/XML tags
        'char(',        # Character conversion
        'concat(',      # Concatenation
    ]

    value_lower = value.lower()

    for pattern in dangerous_patterns:
        if pattern in value_lower:
            raise ValueError(f"Input contains dangerous pattern: '{pattern}'")

    return True


# ============================================================================
# PATH TRAVERSAL PREVENTION
# ============================================================================

def validate_path_safety(src: str, dst: str, allowed_base: Optional[str] = None) -> bool:
    """
    Enhanced path validation with multiple security layers.

    Args:
        src: Source path
        dst: Destination path
        allowed_base: Optional base directory that dst must be within

    Returns:
        True if safe

    Raises:
        PermissionError: If path is unsafe
        FileNotFoundError: If source doesn't exist
    """
    # 1. Check for dangerous patterns BEFORE path resolution
    for pattern in DANGEROUS_PATH_PATTERNS:
        if re.search(pattern, dst, re.IGNORECASE):
            logger.warning(f"Dangerous path pattern detected: {pattern} in {dst}")
            raise PermissionError(f"Dangerous path pattern detected: {pattern}")

    # 2. Normalize paths (resolve symlinks, relative paths, etc.)
    try:
        src_real = Path(src).resolve(strict=False)
        dst_real = Path(dst).resolve(strict=False)
    except Exception as e:
        logger.error(f"Path resolution failed: {e}")
        raise PermissionError(f"Path resolution failed: {e}")

    # 3. Convert to absolute paths and normalize
    src_real = src_real.absolute()
    dst_real = dst_real.absolute()

    # 4. Check against protected paths (use normalized paths)
    for protected in PROTECTED_PATHS:
        try:
            protected_real = Path(protected).resolve(strict=False).absolute()

            # Check if destination is within or equal to protected path
            dst_real.relative_to(protected_real)
            logger.warning(f"Attempt to access protected directory: {dst_real} -> {protected_real}")
            raise PermissionError(f"Access to protected directory denied: {protected}")
        except ValueError:
            # Not a subdirectory - this is OK
            pass

    # 5. If allowed_base specified, ensure destination is within it
    if allowed_base:
        try:
            allowed_real = Path(allowed_base).resolve(strict=False).absolute()
            dst_real.relative_to(allowed_real)
        except ValueError:
            logger.warning(f"Destination outside allowed base: {dst_real} not in {allowed_real}")
            raise PermissionError(f"Destination must be within {allowed_base}")

    # 6. Check if source exists (for copy/move operations)
    if not src_real.exists():
        raise FileNotFoundError(f"Source does not exist: {src}")

    # 7. Prevent overwriting source with destination
    if src_real == dst_real:
        raise PermissionError("Source and destination are the same")

    return True


# ============================================================================
# COMMAND INJECTION PREVENTION
# ============================================================================

def sanitize_cli_argument(arg: str) -> str:
    """
    Sanitize command-line argument for Windows.

    Args:
        arg: Argument to sanitize

    Returns:
        Sanitized argument

    Raises:
        ValueError: If argument contains dangerous characters
    """
    # Check length
    if len(arg) > MAX_LENGTHS['cli_argument']:
        raise ValueError(f"Argument too long: {len(arg)} > {MAX_LENGTHS['cli_argument']}")

    # Disallow shell metacharacters
    for char in DANGEROUS_CLI_CHARS:
        if char in arg:
            logger.warning(f"Dangerous character in CLI argument: {char}")
            raise ValueError(f"Argument contains dangerous character: {char}")

    # Validate argument doesn't start with single dash (double dash is OK)
    if arg.startswith('-') and not arg.startswith('--'):
        raise ValueError("Single-dash arguments not allowed for security")

    return arg


def validate_subprocess_path(path: str) -> Path:
    """
    Validate path for subprocess operations.

    Args:
        path: Path to validate

    Returns:
        Validated Path object

    Raises:
        ValueError: If path is invalid
        PermissionError: If path is protected
    """
    try:
        # Resolve to absolute path
        path_obj = Path(path).resolve(strict=True)

        # Check against protected paths
        for protected in PROTECTED_PATHS:
            protected_real = Path(protected).resolve(strict=False).absolute()
            try:
                path_obj.relative_to(protected_real)
                raise PermissionError(f"Access to protected path denied: {protected}")
            except ValueError:
                pass

        return path_obj

    except Exception as e:
        logger.error(f"Path validation failed: {e}")
        raise


# ============================================================================
# EXPORT SANITIZATION
# ============================================================================

def sanitize_csv_cell(value: Any) -> str:
    """
    Sanitize cell value to prevent CSV injection.

    Args:
        value: Cell value

    Returns:
        Sanitized value
    """
    if not isinstance(value, str):
        return str(value) if value is not None else ""

    # Characters that trigger formula execution
    dangerous_chars = ['=', '+', '-', '@', '|', '%']

    # If starts with dangerous char, prefix with single quote
    if value and value[0] in dangerous_chars:
        return "'" + value

    # Remove potential command injection (newlines, carriage returns)
    value = value.replace('\r', '').replace('\n', ' ')

    return value


def sanitize_html_output(value: Any) -> str:
    """
    Sanitize value for HTML output to prevent XSS.

    Args:
        value: Value to sanitize

    Returns:
        HTML-escaped value
    """
    if value is None:
        return ""

    # Convert to string and escape HTML
    return html.escape(str(value), quote=True)


def sanitize_json_value(value: Any) -> Any:
    """
    Sanitize value for JSON export.

    Args:
        value: Value to sanitize

    Returns:
        Sanitized value
    """
    # Handle None
    if value is None:
        return None

    # Handle Path objects
    if isinstance(value, Path):
        return str(value)

    # For string values, remove control characters
    if isinstance(value, str):
        value = ''.join(
            char for char in value
            if char.isprintable() or char in ('\t', '\n')
        )

    # Validate numeric values
    if isinstance(value, (int, float)):
        if math.isnan(value) or math.isinf(value):
            return None

    return value


# ============================================================================
# DATABASE VALIDATION
# ============================================================================

def validate_table_name(table: str) -> str:
    """
    Validate and sanitize table name.

    Args:
        table: Table name to validate

    Returns:
        Validated table name

    Raises:
        ValueError: If table name is invalid
    """
    # Remove whitespace
    table = table.strip()

    # Check if table is in whitelist
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Table not allowed: {table}")

    # Additional validation: only alphanumeric and underscore
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table):
        raise ValueError(f"Invalid table name format: {table}")

    # Check length
    if len(table) > MAX_LENGTHS['table_name']:
        raise ValueError(f"Table name too long: {len(table)} > {MAX_LENGTHS['table_name']}")

    return table


# ============================================================================
# INPUT LENGTH VALIDATION
# ============================================================================

def validate_input_length(value: str, field: str) -> str:
    """
    Validate input length.

    Args:
        value: Value to validate
        field: Field name (to determine max length)

    Returns:
        Validated value

    Raises:
        ValueError: If value is too long
    """
    max_length = MAX_LENGTHS.get(field, 255)

    if len(value) > max_length:
        raise ValueError(f"{field} too long: {len(value)} > {max_length}")

    return value


# ============================================================================
# SECURITY LOGGING
# ============================================================================

class SecurityEvent:
    """Security event types."""
    AUTH_FAILURE = "authentication_failure"
    ACCESS_DENIED = "access_denied"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    PATH_TRAVERSAL_ATTEMPT = "path_traversal_attempt"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    COMMAND_INJECTION_ATTEMPT = "command_injection_attempt"
    INVALID_INPUT = "invalid_input"


def log_security_event(event_type: str, details: dict, severity: str = "WARNING") -> None:
    """
    Log security event.

    Args:
        event_type: Type of security event
        details: Event details
        severity: Log severity (WARNING, ERROR, CRITICAL)
    """
    import json
    import time

    log_entry = {
        'event_type': event_type,
        'timestamp': time.time(),
        'details': details,
        'user': os.getenv('USERNAME', 'unknown'),
        'process_id': os.getpid()
    }

    log_message = f"SECURITY EVENT - {event_type}: {json.dumps(log_entry)}"

    if severity == "CRITICAL":
        logger.critical(log_message)
    elif severity == "ERROR":
        logger.error(log_message)
    else:
        logger.warning(log_message)


# ============================================================================
# SAFE ERROR MESSAGES
# ============================================================================

def safe_error_message(e: Exception, user_facing: bool = True) -> str:
    """
    Generate safe error message.

    Args:
        e: Exception
        user_facing: If True, return generic message; if False, return detailed

    Returns:
        Error message
    """
    if user_facing:
        # Generic message for users
        return "An error occurred. Please check the logs for details."
    else:
        # Detailed message for logs only
        return str(e)
