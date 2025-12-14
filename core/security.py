"""
Security module for Smart Search Pro.

Provides centralized input validation, sanitization, and security utilities
to prevent SQL injection, path traversal, command injection, and other attacks.

ROBUSTEZ additions:
- Unicode normalization for cross-platform compatibility
- Long path support (>260 chars) for Windows
- UNC/network path detection and handling
- Locked file detection utilities
"""

import os
import re
import html
import math
import logging
import unicodedata
from pathlib import Path
from typing import Any, Optional, List, Set, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# ROBUSTNESS: UNICODE AND PATH UTILITIES
# ============================================================================

def normalize_unicode_path(path: str) -> str:
    """
    Normalize Unicode for filesystem/SQL compatibility.

    ROBUSTEZ:
    - Normalizes to NFC (composed form) preferred by most filesystems
    - Removes zero-width and control characters that can cause issues
    - Handles emoji and combining characters

    Args:
        path: Path string that may contain Unicode characters

    Returns:
        Normalized path string
    """
    if not path:
        return path

    # Normalize to NFC (composed form) - most filesystems prefer this
    normalized = unicodedata.normalize('NFC', path)

    # Remove zero-width and control characters (except tab/space)
    # Categories: Cc=control, Cf=format, Cs=surrogate, Co=private, Cn=unassigned
    cleaned = ''.join(
        char for char in normalized
        if unicodedata.category(char) not in ('Cc', 'Cf', 'Cs', 'Co', 'Cn')
        or char in (' ', '\t')
    )

    return cleaned


def add_long_path_prefix(path: str) -> str:
    """
    Add \\\\?\\ prefix for long path support on Windows.

    Windows traditionally limits paths to 260 characters (MAX_PATH).
    With the \\\\?\\ prefix, paths up to 32,767 characters are supported.

    Args:
        path: Path string to potentially prefix

    Returns:
        Path with long path prefix if needed, otherwise unchanged
    """
    if os.name != 'nt':
        return path  # Only for Windows

    if not path:
        return path

    # Already has long path prefix
    if path.startswith('\\\\?\\'):
        return path

    # Check if path exceeds MAX_PATH
    if len(path) <= 260:
        return path

    try:
        # Convert to absolute path first
        abs_path = os.path.abspath(path)

        # UNC paths need different prefix
        if abs_path.startswith('\\\\'):
            return '\\\\?\\UNC\\' + abs_path[2:]

        return '\\\\?\\' + abs_path

    except Exception as e:
        logger.warning(f"Could not add long path prefix to {path}: {e}")
        return path


def is_network_path(path: str) -> bool:
    """
    Check if path is on a network drive or UNC path.

    ROBUSTEZ: Network paths may have different timeout behavior
    and require special handling.

    Args:
        path: Path to check

    Returns:
        True if path is a network/UNC path
    """
    if not path:
        return False

    # UNC path (starts with \\)
    if path.startswith('\\\\'):
        return True

    # Check if drive letter maps to network share
    if os.name == 'nt' and len(path) >= 2 and path[1] == ':':
        drive = path[:2]
        try:
            import ctypes
            DRIVE_REMOTE = 4
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive + '\\')
            return drive_type == DRIVE_REMOTE
        except Exception:
            pass

    return False


def validate_path_length(path: str, strict: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate path length against Windows limits.

    Args:
        path: Path to validate
        strict: If True, fail on paths >260; if False, allow with prefix

    Returns:
        Tuple of (is_valid, error_message)
        error_message is None if valid
    """
    if not path:
        return (True, None)

    path_len = len(path)

    # Absolute Windows limit
    if path_len > 32767:
        return (False, f"Path exceeds absolute Windows limit (32767 chars): {path_len}")

    # Traditional MAX_PATH limit
    if path_len > 260:
        if strict:
            return (False, f"Path exceeds MAX_PATH (260 chars): {path_len}")
        else:
            # Check if long paths are enabled
            if os.name == 'nt':
                try:
                    import winreg
                    key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"SYSTEM\CurrentControlSet\Control\FileSystem"
                    )
                    long_paths_enabled, _ = winreg.QueryValueEx(key, "LongPathsEnabled")
                    winreg.CloseKey(key)

                    if not long_paths_enabled:
                        logger.warning(
                            f"Path exceeds MAX_PATH (260) and long paths not enabled. "
                            f"Consider enabling via registry or using shorter paths."
                        )
                except Exception:
                    pass  # Can't check registry, proceed

    return (True, None)


def is_file_locked(filepath: str) -> bool:
    """
    Check if a file is locked by another process (Windows).

    ROBUSTEZ: Useful for detecting locked files before operations.

    Args:
        filepath: Path to file to check

    Returns:
        True if file appears to be locked
    """
    if not os.path.exists(filepath):
        return False

    if os.name != 'nt':
        return False  # Only for Windows

    try:
        # Try to open file exclusively
        import msvcrt
        with open(filepath, 'r+b') as f:
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        return False  # File is not locked

    except (IOError, OSError, PermissionError):
        return True  # File is locked

    except ImportError:
        # msvcrt not available
        return False


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

# SAFE file extensions for open_file() - prevent command injection via os.startfile()
# These are document/media types that are safe to open with default applications
SAFE_FILE_EXTENSIONS: Set[str] = {
    # Documents
    '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.odt', '.ods', '.odp', '.rtf', '.csv', '.tsv',
    # Images
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg', '.webp',
    '.tiff', '.tif', '.raw', '.psd', '.ai', '.eps',
    # Audio
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus',
    # Video
    '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v',
    # Archives (view only, not execute)
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
    # Code/Text (view only)
    '.py', '.js', '.ts', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
    '.md', '.ini', '.cfg', '.conf', '.log', '.sql', '.sh', '.c', '.cpp',
    '.h', '.hpp', '.java', '.cs', '.go', '.rs', '.rb', '.php', '.swift',
    # Other safe formats
    '.epub', '.mobi', '.djvu',
}

# DANGEROUS file extensions - NEVER allow os.startfile() on these
DANGEROUS_FILE_EXTENSIONS: Set[str] = {
    # Executables
    '.exe', '.com', '.scr', '.pif',
    # Scripts
    '.bat', '.cmd', '.ps1', '.psm1', '.vbs', '.vbe', '.js', '.jse',
    '.ws', '.wsf', '.wsc', '.wsh', '.msc',
    # Installers
    '.msi', '.msp', '.msu',
    # Shortcuts and links
    '.lnk', '.url', '.scf',
    # Registry
    '.reg',
    # Other dangerous
    '.hta', '.cpl', '.inf', '.application', '.gadget',
}

# Note: .js is in DANGEROUS for Windows scripting context but allowed in SAFE for code viewing
# The check order is: DANGEROUS first (block), then SAFE (allow), else block


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


def validate_safe_file_type(filepath: str, allow_unknown: bool = False) -> bool:
    """
    Validate that a file is safe to open with os.startfile().

    This prevents command injection attacks by blocking executable file types
    that could run malicious code when opened.

    Args:
        filepath: Path to the file to validate
        allow_unknown: If True, allow files with unknown extensions (default: False)

    Returns:
        True if file is safe to open

    Raises:
        PermissionError: If file type is dangerous or not allowed
        FileNotFoundError: If file doesn't exist
    """
    path_obj = Path(filepath)

    # Check file exists
    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    # Directories are safe (opens in explorer)
    if path_obj.is_dir():
        return True

    # Get extension (lowercase, with dot)
    ext = path_obj.suffix.lower()

    # No extension - treat as unknown
    if not ext:
        if allow_unknown:
            return True
        log_security_event(
            SecurityEvent.COMMAND_INJECTION_ATTEMPT,
            {'filepath': filepath, 'reason': 'no_extension'},
            severity="WARNING"
        )
        raise PermissionError(f"Cannot open file without extension for security: {filepath}")

    # Check DANGEROUS extensions first (block even if in safe list somehow)
    if ext in DANGEROUS_FILE_EXTENSIONS:
        log_security_event(
            SecurityEvent.COMMAND_INJECTION_ATTEMPT,
            {'filepath': filepath, 'extension': ext, 'reason': 'dangerous_extension'},
            severity="ERROR"
        )
        raise PermissionError(
            f"Cannot open potentially dangerous file type '{ext}': {filepath}. "
            f"Use 'Open Location' to navigate to the file instead."
        )

    # Check if extension is in safe list
    if ext in SAFE_FILE_EXTENSIONS:
        return True

    # Unknown extension
    if allow_unknown:
        logger.warning(f"Opening file with unknown extension: {ext}")
        return True

    log_security_event(
        SecurityEvent.COMMAND_INJECTION_ATTEMPT,
        {'filepath': filepath, 'extension': ext, 'reason': 'unknown_extension'},
        severity="WARNING"
    )
    raise PermissionError(
        f"Cannot open file with unknown extension '{ext}': {filepath}. "
        f"Use 'Open Location' to navigate to the file instead."
    )


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
