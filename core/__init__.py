"""
Smart Search Pro - Core Module

Provides foundational components for the application including:
- Configuration management
- Database operations with connection pooling
- LRU cache with TTL
- Event bus for loose coupling
- Structured logging
- Custom exception hierarchy
"""

from .cache import CacheManager, LRUCache, get_cache
from .config import (
    CacheConfig,
    Config,
    DatabaseConfig,
    IntegrationConfig,
    LoggingConfig,
    PerformanceConfig,
    SearchConfig,
    UIConfig,
    get_config,
    load_config,
    save_config,
)
from .database import ConnectionPool, Database, Migration, create_database
from .eventbus import Event, EventBus, EventPriority, get_event_bus, publish, subscribe
from .exceptions import (
    APIError,
    CacheError,
    CacheExpiredError,
    CacheFullError,
    ConfigLoadError,
    ConfigurationError,
    ConnectionError,
    DatabaseError,
    FileSystemError,
    IndexCorruptedError,
    IndexError,
    IndexNotFoundError,
    IntegrityError,
    InvalidConfigError,
    InvalidPathError,
    InvalidQueryError,
    MigrationError,
    NetworkError,
    NoResultsError,
    PathNotFoundError,
    PermissionError,
    PluginError,
    PluginLoadError,
    PluginNotFoundError,
    QueryError,
    RateLimitError,
    ResourceError,
    ResourceExhaustedError,
    ResourceLockedError,
    ResourceNotFoundError,
    SchemaError,
    SearchError,
    SearchTimeoutError,
    SmartSearchError,
    ValidationError,
)
from .logger import (
    LoggerManager,
    StructuredLogger,
    get_log_file,
    get_logger,
    set_log_level,
    setup_logging,
)

__version__ = "1.0.0"
__author__ = "Smart Search Pro Team"

__all__ = [
    # Cache
    "LRUCache",
    "CacheManager",
    "get_cache",
    # Config
    "Config",
    "DatabaseConfig",
    "CacheConfig",
    "SearchConfig",
    "LoggingConfig",
    "UIConfig",
    "PerformanceConfig",
    "IntegrationConfig",
    "get_config",
    "load_config",
    "save_config",
    # Database
    "Database",
    "ConnectionPool",
    "Migration",
    "create_database",
    # Event Bus
    "EventBus",
    "Event",
    "EventPriority",
    "get_event_bus",
    "publish",
    "subscribe",
    # Logger
    "StructuredLogger",
    "LoggerManager",
    "setup_logging",
    "get_logger",
    "set_log_level",
    "get_log_file",
    # Exceptions - Base
    "SmartSearchError",
    # Exceptions - Configuration
    "ConfigurationError",
    "InvalidConfigError",
    "ConfigLoadError",
    # Exceptions - Database
    "DatabaseError",
    "ConnectionError",
    "MigrationError",
    "IntegrityError",
    "QueryError",
    # Exceptions - Cache
    "CacheError",
    "CacheFullError",
    "CacheExpiredError",
    # Exceptions - Search
    "SearchError",
    "InvalidQueryError",
    "SearchTimeoutError",
    "NoResultsError",
    # Exceptions - File System
    "FileSystemError",
    "PathNotFoundError",
    "PermissionError",
    "InvalidPathError",
    # Exceptions - Index
    "IndexError",
    "IndexCorruptedError",
    "IndexNotFoundError",
    # Exceptions - Plugin
    "PluginError",
    "PluginLoadError",
    "PluginNotFoundError",
    # Exceptions - Network
    "NetworkError",
    "APIError",
    "RateLimitError",
    # Exceptions - Validation
    "ValidationError",
    "SchemaError",
    # Exceptions - Resource
    "ResourceError",
    "ResourceNotFoundError",
    "ResourceExhaustedError",
    "ResourceLockedError",
]


def initialize(
    config_path: str | None = None,
    log_dir: str | None = None,
    log_level: str = "INFO",
) -> tuple[Config, Database]:
    """
    Initialize core components.

    This is a convenience function that sets up configuration,
    logging, and database in one call.

    Args:
        config_path: Path to configuration file (None = use defaults)
        log_dir: Directory for log files (None = use config value)
        log_level: Logging level

    Returns:
        Tuple of (Config, Database) instances

    Example:
        >>> from core import initialize
        >>> config, db = initialize("config.yaml", "logs", "DEBUG")
        >>> logger = get_logger(__name__)
        >>> logger.info("Application initialized")
    """
    # Load configuration
    if config_path:
        config = load_config(config_path)
    else:
        config = get_config()

    # Setup logging
    log_directory = log_dir or config.get_log_dir()
    setup_logging(
        log_dir=log_directory,
        level=log_level or config.logging.level,
        console=config.logging.console,
        file=config.logging.file,
        max_bytes=config.logging.max_bytes,
        backup_count=config.logging.backup_count,
    )

    logger = get_logger(__name__)
    logger.info(
        "Initializing Smart Search Pro",
        version=__version__,
        config_path=config_path or "defaults",
    )

    # Initialize database
    db = create_database(
        database_path=config.get_database_path(),
        pool_size=config.database.pool_size,
        timeout=config.database.timeout,
        check_same_thread=config.database.check_same_thread,
        enable_wal=config.database.enable_wal,
        cache_size=config.database.cache_size,
        journal_mode=config.database.journal_mode,
        synchronous=config.database.synchronous,
        temp_store=config.database.temp_store,
    )

    logger.info("Core components initialized successfully")

    return config, db
