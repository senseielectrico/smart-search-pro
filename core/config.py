"""
Configuration system for Smart Search Pro.

Provides YAML-based configuration with validation, defaults,
and runtime updates using dataclasses.
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Self

import yaml

from .exceptions import ConfigLoadError, InvalidConfigError
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration."""

    path: str = "smart_search.db"
    pool_size: int = 5
    timeout: float = 30.0
    check_same_thread: bool = False
    enable_wal: bool = True
    cache_size: int = -64000  # 64MB in KB (negative = KB)
    journal_mode: str = "WAL"
    synchronous: str = "NORMAL"
    temp_store: str = "MEMORY"

    def validate(self) -> None:
        """Validate database configuration."""
        if self.pool_size < 1:
            raise InvalidConfigError("pool_size must be at least 1")
        if self.timeout <= 0:
            raise InvalidConfigError("timeout must be positive")
        if self.journal_mode not in ("DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF"):
            raise InvalidConfigError(f"Invalid journal_mode: {self.journal_mode}")
        if self.synchronous not in ("OFF", "NORMAL", "FULL", "EXTRA"):
            raise InvalidConfigError(f"Invalid synchronous: {self.synchronous}")


@dataclass
class CacheConfig:
    """Cache configuration."""

    max_size: int = 1000
    ttl_seconds: int = 3600  # 1 hour
    cleanup_interval: int = 300  # 5 minutes
    enable_persistence: bool = True
    persistence_path: str | None = None

    def validate(self) -> None:
        """Validate cache configuration."""
        if self.max_size < 1:
            raise InvalidConfigError("max_size must be at least 1")
        if self.ttl_seconds < 0:
            raise InvalidConfigError("ttl_seconds must be non-negative")
        if self.cleanup_interval < 0:
            raise InvalidConfigError("cleanup_interval must be non-negative")


@dataclass
class SearchConfig:
    """Search configuration."""

    max_results: int = 1000
    timeout: float = 30.0
    case_sensitive: bool = False
    whole_word: bool = False
    regex_enabled: bool = True
    fuzzy_threshold: float = 0.7
    max_file_size_mb: int = 100
    excluded_extensions: list[str] = field(default_factory=lambda: [
        ".exe", ".dll", ".so", ".dylib", ".obj", ".o",
        ".zip", ".tar", ".gz", ".7z", ".rar",
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico",
        ".mp3", ".mp4", ".avi", ".mkv", ".mov",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ])
    excluded_dirs: list[str] = field(default_factory=lambda: [
        ".git", ".svn", ".hg", "node_modules", "__pycache__",
        ".venv", "venv", ".env", "dist", "build",
    ])

    def validate(self) -> None:
        """Validate search configuration."""
        if self.max_results < 1:
            raise InvalidConfigError("max_results must be at least 1")
        if self.timeout <= 0:
            raise InvalidConfigError("timeout must be positive")
        if not 0 <= self.fuzzy_threshold <= 1:
            raise InvalidConfigError("fuzzy_threshold must be between 0 and 1")
        if self.max_file_size_mb < 1:
            raise InvalidConfigError("max_file_size_mb must be at least 1")


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    console: bool = True
    file: bool = True
    log_dir: str = "logs"
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    format: str = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"

    def validate(self) -> None:
        """Validate logging configuration."""
        valid_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        if self.level.upper() not in valid_levels:
            raise InvalidConfigError(f"Invalid log level: {self.level}")
        if self.max_bytes < 1024:
            raise InvalidConfigError("max_bytes must be at least 1024")
        if self.backup_count < 0:
            raise InvalidConfigError("backup_count must be non-negative")


@dataclass
class UIConfig:
    """UI configuration."""

    theme: str = "dark"
    accent_color: str = "#00ff00"
    font_family: str = "Consolas"
    font_size: int = 10
    show_line_numbers: bool = True
    show_minimap: bool = True
    word_wrap: bool = False
    tab_size: int = 4
    auto_save: bool = True
    auto_save_interval: int = 30  # seconds

    def validate(self) -> None:
        """Validate UI configuration."""
        if self.theme not in ("dark", "light", "auto"):
            raise InvalidConfigError(f"Invalid theme: {self.theme}")
        if self.font_size < 6 or self.font_size > 72:
            raise InvalidConfigError("font_size must be between 6 and 72")
        if self.tab_size < 1 or self.tab_size > 16:
            raise InvalidConfigError("tab_size must be between 1 and 16")
        if self.auto_save_interval < 1:
            raise InvalidConfigError("auto_save_interval must be at least 1")


@dataclass
class PerformanceConfig:
    """Performance configuration."""

    max_threads: int = 8
    chunk_size: int = 8192
    buffer_size: int = 65536
    enable_profiling: bool = False
    profile_dir: str | None = None
    memory_limit_mb: int = 1024
    enable_gc_optimization: bool = True

    def validate(self) -> None:
        """Validate performance configuration."""
        if self.max_threads < 1:
            raise InvalidConfigError("max_threads must be at least 1")
        if self.chunk_size < 1024:
            raise InvalidConfigError("chunk_size must be at least 1024")
        if self.buffer_size < 1024:
            raise InvalidConfigError("buffer_size must be at least 1024")
        if self.memory_limit_mb < 64:
            raise InvalidConfigError("memory_limit_mb must be at least 64")


@dataclass
class IntegrationConfig:
    """External integration configuration."""

    everything_enabled: bool = True
    everything_path: str | None = None
    git_enabled: bool = True
    vscode_integration: bool = True
    explorer_context_menu: bool = False

    def validate(self) -> None:
        """Validate integration configuration."""
        if self.everything_path and not Path(self.everything_path).exists():
            logger.warning(
                "Everything path does not exist",
                path=self.everything_path,
            )


@dataclass
class Config:
    """Main configuration container."""

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    integration: IntegrationConfig = field(default_factory=IntegrationConfig)

    version: str = "1.0.0"
    app_name: str = "Smart Search Pro"
    data_dir: str = "data"
    config_file: str = "config.yaml"

    def validate(self) -> None:
        """Validate all configuration sections."""
        self.database.validate()
        self.cache.validate()
        self.search.validate()
        self.logging.validate()
        self.ui.validate()
        self.performance.validate()
        self.integration.validate()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """
        Create configuration from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            Config instance
        """
        # Extract nested configurations
        database = DatabaseConfig(**data.get("database", {}))
        cache = CacheConfig(**data.get("cache", {}))
        search = SearchConfig(**data.get("search", {}))
        logging_cfg = LoggingConfig(**data.get("logging", {}))
        ui = UIConfig(**data.get("ui", {}))
        performance = PerformanceConfig(**data.get("performance", {}))
        integration = IntegrationConfig(**data.get("integration", {}))

        # Create main config
        config = cls(
            database=database,
            cache=cache,
            search=search,
            logging=logging_cfg,
            ui=ui,
            performance=performance,
            integration=integration,
        )

        # Set top-level fields
        for key in ("version", "app_name", "data_dir", "config_file"):
            if key in data:
                setattr(config, key, data[key])

        return config

    def save(self, path: Path | str) -> None:
        """
        Save configuration to YAML file.

        Args:
            path: Path to configuration file
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    self.to_dict(),
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    indent=2,
                )
            logger.info("Configuration saved", path=str(path))
        except Exception as e:
            raise ConfigLoadError(
                f"Failed to save configuration: {e}",
                {"path": str(path)},
            ) from e

    @classmethod
    def load(cls, path: Path | str) -> Self:
        """
        Load configuration from YAML file.

        Args:
            path: Path to configuration file

        Returns:
            Config instance

        Raises:
            ConfigLoadError: If configuration cannot be loaded
        """
        path = Path(path)

        if not path.exists():
            logger.warning("Config file not found, using defaults", path=str(path))
            return cls()

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                raise InvalidConfigError("Configuration must be a dictionary")

            config = cls.from_dict(data)
            config.validate()

            logger.info("Configuration loaded", path=str(path))
            return config

        except yaml.YAMLError as e:
            raise ConfigLoadError(
                f"Failed to parse YAML: {e}",
                {"path": str(path)},
            ) from e
        except Exception as e:
            raise ConfigLoadError(
                f"Failed to load configuration: {e}",
                {"path": str(path)},
            ) from e

    def update(self, **kwargs: Any) -> None:
        """
        Update configuration values.

        Args:
            **kwargs: Configuration values to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning("Unknown configuration key", key=key)

        self.validate()

    def get_data_dir(self) -> Path:
        """
        Get data directory path.

        Returns:
            Path to data directory
        """
        return Path(self.data_dir).expanduser().resolve()

    def get_log_dir(self) -> Path:
        """
        Get log directory path.

        Returns:
            Path to log directory
        """
        return Path(self.logging.log_dir).expanduser().resolve()

    def get_database_path(self) -> Path:
        """
        Get database file path.

        Returns:
            Path to database file
        """
        db_path = Path(self.database.path)
        if not db_path.is_absolute():
            db_path = self.get_data_dir() / db_path
        return db_path

    def get_cache_path(self) -> Path | None:
        """
        Get cache persistence path.

        Returns:
            Path to cache file or None if persistence is disabled
        """
        if not self.cache.enable_persistence:
            return None

        if self.cache.persistence_path:
            return Path(self.cache.persistence_path)

        return self.get_data_dir() / "cache.pkl"


# Global configuration instance
_config: Config | None = None


def get_config() -> Config:
    """
    Get global configuration instance.

    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def load_config(path: Path | str) -> Config:
    """
    Load and set global configuration.

    Args:
        path: Path to configuration file

    Returns:
        Config instance
    """
    global _config
    _config = Config.load(path)
    return _config


def save_config(path: Path | str | None = None) -> None:
    """
    Save global configuration.

    Args:
        path: Path to configuration file (uses config.config_file if None)
    """
    config = get_config()
    if path is None:
        path = config.config_file
    config.save(path)
