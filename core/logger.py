"""
Logging configuration for Smart Search Pro.

Provides centralized logging with file rotation, console output,
and structured logging capabilities.
"""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.logging import RichHandler


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""

    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


class StructuredLogger:
    """
    Structured logger with support for contextual information.

    Provides methods for logging with additional structured data
    that can be used for analysis and debugging.
    """

    def __init__(self, name: str, logger: logging.Logger) -> None:
        """
        Initialize structured logger.

        Args:
            name: Logger name
            logger: Underlying logger instance
        """
        self.name = name
        self._logger = logger
        self._context: dict[str, Any] = {}

    def set_context(self, **kwargs: Any) -> None:
        """
        Set persistent context for all log messages.

        Args:
            **kwargs: Context key-value pairs
        """
        self._context.update(kwargs)

    def clear_context(self) -> None:
        """Clear all context."""
        self._context.clear()

    def _format_message(self, msg: str, extra: dict[str, Any] | None = None) -> str:
        """
        Format message with context and extra data.

        Args:
            msg: Base message
            extra: Additional data for this message

        Returns:
            Formatted message string
        """
        data = {**self._context}
        if extra:
            data.update(extra)

        if data:
            parts = [f"{k}={v}" for k, v in data.items()]
            return f"{msg} | {' '.join(parts)}"
        return msg

    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log debug message with context."""
        self._logger.debug(self._format_message(msg, kwargs))

    def info(self, msg: str, **kwargs: Any) -> None:
        """Log info message with context."""
        self._logger.info(self._format_message(msg, kwargs))

    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log warning message with context."""
        self._logger.warning(self._format_message(msg, kwargs))

    def error(self, msg: str, **kwargs: Any) -> None:
        """Log error message with context."""
        self._logger.error(self._format_message(msg, kwargs))

    def critical(self, msg: str, **kwargs: Any) -> None:
        """Log critical message with context."""
        self._logger.critical(self._format_message(msg, kwargs))

    def exception(self, msg: str, **kwargs: Any) -> None:
        """Log exception with context."""
        self._logger.exception(self._format_message(msg, kwargs))


class LoggerManager:
    """
    Centralized logger management.

    Handles logger creation, configuration, and lifecycle.
    """

    _instance: "LoggerManager | None" = None
    _initialized: bool = False

    def __new__(cls) -> "LoggerManager":
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize logger manager (only once)."""
        if not self._initialized:
            self._loggers: dict[str, StructuredLogger] = {}
            self._log_dir: Path | None = None
            self._log_level: int = logging.INFO
            self._console_enabled: bool = True
            self._file_enabled: bool = True
            self._console: Console = Console()
            LoggerManager._initialized = True

    def setup(
        self,
        log_dir: Path | str | None = None,
        level: int | str = logging.INFO,
        console: bool = True,
        file: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
    ) -> None:
        """
        Setup logging configuration.

        Args:
            log_dir: Directory for log files
            level: Logging level (int or string)
            console: Enable console logging
            file: Enable file logging
            max_bytes: Maximum size per log file
            backup_count: Number of backup files to keep
        """
        if isinstance(level, str):
            level = getattr(logging, level.upper())

        self._log_level = level
        self._console_enabled = console
        self._file_enabled = file

        if log_dir:
            self._log_dir = Path(log_dir)
            self._log_dir.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.handlers.clear()

        # File handler with rotation
        if file and self._log_dir:
            log_file = self._log_dir / f"smart_search_{datetime.now():%Y%m%d}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_formatter = logging.Formatter(
                "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(level)
            root_logger.addHandler(file_handler)

        # Console handler with rich formatting
        if console:
            console_handler = RichHandler(
                console=self._console,
                rich_tracebacks=True,
                tracebacks_show_locals=True,
                markup=True,
            )
            console_handler.setLevel(level)
            root_logger.addHandler(console_handler)

    def get_logger(self, name: str) -> StructuredLogger:
        """
        Get or create a structured logger.

        Args:
            name: Logger name (usually __name__)

        Returns:
            StructuredLogger instance
        """
        if name not in self._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(self._log_level)
            self._loggers[name] = StructuredLogger(name, logger)

        return self._loggers[name]

    def set_level(self, level: int | str) -> None:
        """
        Set logging level for all loggers.

        Args:
            level: Logging level (int or string)
        """
        if isinstance(level, str):
            level = getattr(logging, level.upper())

        self._log_level = level
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        for handler in root_logger.handlers:
            handler.setLevel(level)

        for structured_logger in self._loggers.values():
            structured_logger._logger.setLevel(level)

    def disable_console(self) -> None:
        """Disable console logging."""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, RichHandler):
                root_logger.removeHandler(handler)
        self._console_enabled = False

    def enable_console(self) -> None:
        """Enable console logging."""
        if not self._console_enabled:
            root_logger = logging.getLogger()
            console_handler = RichHandler(
                console=self._console,
                rich_tracebacks=True,
                tracebacks_show_locals=True,
                markup=True,
            )
            console_handler.setLevel(self._log_level)
            root_logger.addHandler(console_handler)
            self._console_enabled = True

    def get_log_file_path(self) -> Path | None:
        """
        Get current log file path.

        Returns:
            Path to log file or None if file logging is disabled
        """
        if self._log_dir:
            return self._log_dir / f"smart_search_{datetime.now():%Y%m%d}.log"
        return None


# Global logger manager instance
_manager = LoggerManager()


def setup_logging(
    log_dir: Path | str | None = None,
    level: int | str = logging.INFO,
    console: bool = True,
    file: bool = True,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """
    Setup logging configuration (convenience function).

    Args:
        log_dir: Directory for log files
        level: Logging level (int or string)
        console: Enable console logging
        file: Enable file logging
        max_bytes: Maximum size per log file
        backup_count: Number of backup files to keep
    """
    _manager.setup(log_dir, level, console, file, max_bytes, backup_count)


def get_logger(name: str) -> StructuredLogger:
    """
    Get or create a structured logger (convenience function).

    Args:
        name: Logger name (usually __name__)

    Returns:
        StructuredLogger instance
    """
    return _manager.get_logger(name)


def set_log_level(level: int | str) -> None:
    """
    Set logging level for all loggers (convenience function).

    Args:
        level: Logging level (int or string)
    """
    _manager.set_level(level)


def get_log_file() -> Path | None:
    """
    Get current log file path (convenience function).

    Returns:
        Path to log file or None if file logging is disabled
    """
    return _manager.get_log_file_path()
