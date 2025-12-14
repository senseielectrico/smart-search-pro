"""
SQLite database manager with connection pooling and migrations.

Provides thread-safe database operations, connection pooling,
automatic migrations, and comprehensive table management.
"""

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Generator, Self

from .exceptions import ConnectionError, IntegrityError, MigrationError, QueryError
from .logger import get_logger
from .security import validate_table_name

logger = get_logger(__name__)


@dataclass
class Migration:
    """Database migration."""

    version: int
    description: str
    sql: str
    rollback_sql: str | None = None


class ConnectionPool:
    """
    Thread-safe connection pool for SQLite.

    Manages a pool of database connections with automatic cleanup
    and connection reuse.
    """

    def __init__(
        self,
        database: str | Path,
        pool_size: int = 5,
        timeout: float = 30.0,
        check_same_thread: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Initialize connection pool.

        Args:
            database: Path to database file
            pool_size: Maximum number of connections
            timeout: Connection timeout in seconds
            check_same_thread: SQLite check_same_thread parameter
            **kwargs: Additional connection parameters
        """
        self._database = str(database)
        self._pool_size = pool_size
        self._timeout = timeout
        self._check_same_thread = check_same_thread
        self._kwargs = kwargs

        self._pool: Queue[sqlite3.Connection] = Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._connection_count = 0
        self._created_connections = 0

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection."""
        try:
            conn = sqlite3.connect(
                self._database,
                timeout=self._timeout,
                check_same_thread=self._check_same_thread,
                **self._kwargs,
            )
            conn.row_factory = sqlite3.Row
            self._created_connections += 1

            logger.debug(
                "Created database connection",
                database=self._database,
                total_connections=self._created_connections,
            )

            return conn

        except sqlite3.Error as e:
            raise ConnectionError(
                f"Failed to create connection: {e}",
                {"database": self._database},
            ) from e

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a connection from the pool.

        Yields:
            Database connection

        Raises:
            ConnectionError: If connection cannot be acquired
        """
        conn = None
        try:
            # Try to get existing connection
            try:
                conn = self._pool.get(timeout=1)
            except Empty:
                # Create new connection if pool not full
                with self._lock:
                    if self._connection_count < self._pool_size:
                        conn = self._create_connection()
                        self._connection_count += 1
                    else:
                        # Wait for available connection
                        conn = self._pool.get(timeout=self._timeout)

            yield conn

        except sqlite3.Error:
            # Let sqlite3 errors propagate to be handled by callers
            raise
        except Exception as e:
            if isinstance(e, ConnectionError):
                raise
            raise ConnectionError(
                f"Connection error: {e}",
                {"database": self._database},
            ) from e

        finally:
            # Return connection to pool
            if conn is not None:
                try:
                    self._pool.put(conn, timeout=1)
                except Exception as e:
                    logger.error("Failed to return connection to pool", error=str(e))

    def close_all(self) -> None:
        """Close all connections in the pool."""
        closed = 0
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
                closed += 1
            except Empty:
                break
            except Exception as e:
                logger.error("Error closing connection", error=str(e))

        with self._lock:
            self._connection_count = 0

        logger.info("Closed all database connections", count=closed)


class Database:
    """
    SQLite database manager with migrations and pooling.

    Provides high-level database operations with automatic schema
    management and connection pooling.
    """

    CURRENT_VERSION = 1

    MIGRATIONS: list[Migration] = [
        Migration(
            version=1,
            description="Initial schema",
            sql="""
                -- Search history
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    query_type TEXT NOT NULL,
                    result_count INTEGER NOT NULL,
                    execution_time REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    filters TEXT,
                    metadata TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_search_history_timestamp
                    ON search_history(timestamp);
                CREATE INDEX IF NOT EXISTS idx_search_history_query
                    ON search_history(query);

                -- Saved searches
                CREATE TABLE IF NOT EXISTS saved_searches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    query TEXT NOT NULL,
                    query_type TEXT NOT NULL,
                    filters TEXT,
                    description TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed REAL
                );
                CREATE INDEX IF NOT EXISTS idx_saved_searches_name
                    ON saved_searches(name);

                -- File hash cache
                CREATE TABLE IF NOT EXISTS hash_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL UNIQUE,
                    file_hash TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    modified_time REAL NOT NULL,
                    created_at REAL NOT NULL,
                    accessed_count INTEGER DEFAULT 0,
                    last_accessed REAL
                );
                CREATE INDEX IF NOT EXISTS idx_hash_cache_path
                    ON hash_cache(file_path);
                CREATE INDEX IF NOT EXISTS idx_hash_cache_hash
                    ON hash_cache(file_hash);

                -- File tags
                CREATE TABLE IF NOT EXISTS file_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    UNIQUE(file_path, tag)
                );
                CREATE INDEX IF NOT EXISTS idx_file_tags_path
                    ON file_tags(file_path);
                CREATE INDEX IF NOT EXISTS idx_file_tags_tag
                    ON file_tags(tag);

                -- Settings
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    value_type TEXT NOT NULL,
                    description TEXT,
                    updated_at REAL NOT NULL
                );

                -- Operation history
                CREATE TABLE IF NOT EXISTS operation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT NOT NULL,
                    operation_data TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    duration REAL,
                    timestamp REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_operation_history_type
                    ON operation_history(operation_type);
                CREATE INDEX IF NOT EXISTS idx_operation_history_timestamp
                    ON operation_history(timestamp);

                -- Preview cache
                CREATE TABLE IF NOT EXISTS preview_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL UNIQUE,
                    preview_data TEXT NOT NULL,
                    preview_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    modified_time REAL NOT NULL,
                    created_at REAL NOT NULL,
                    accessed_count INTEGER DEFAULT 0,
                    last_accessed REAL
                );
                CREATE INDEX IF NOT EXISTS idx_preview_cache_path
                    ON preview_cache(file_path);

                -- Schema version
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at REAL NOT NULL,
                    description TEXT
                );
            """,
            rollback_sql="DROP TABLE IF EXISTS search_history;",
        ),
    ]

    def __init__(
        self,
        database_path: str | Path,
        pool_size: int = 5,
        timeout: float = 30.0,
        check_same_thread: bool = False,
        enable_wal: bool = True,
        cache_size: int = -64000,
        journal_mode: str = "WAL",
        synchronous: str = "NORMAL",
        temp_store: str = "MEMORY",
    ) -> None:
        """
        Initialize database manager.

        Args:
            database_path: Path to database file
            pool_size: Connection pool size
            timeout: Connection timeout
            check_same_thread: SQLite check_same_thread parameter
            enable_wal: Enable Write-Ahead Logging
            cache_size: Cache size in KB (negative) or pages (positive)
            journal_mode: Journal mode (DELETE, TRUNCATE, PERSIST, MEMORY, WAL, OFF)
            synchronous: Synchronous mode (OFF, NORMAL, FULL, EXTRA)
            temp_store: Temporary storage (DEFAULT, FILE, MEMORY)
        """
        self._database_path = Path(database_path)
        self._database_path.parent.mkdir(parents=True, exist_ok=True)

        self._pool = ConnectionPool(
            database=self._database_path,
            pool_size=pool_size,
            timeout=timeout,
            check_same_thread=check_same_thread,
        )

        self._enable_wal = enable_wal
        self._cache_size = cache_size
        self._journal_mode = journal_mode
        self._synchronous = synchronous
        self._temp_store = temp_store

        # Initialize database
        self._initialize()

    def _initialize(self) -> None:
        """Initialize database with pragmas and schema."""
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()

            # Set pragmas for performance
            cursor.execute(f"PRAGMA cache_size = {self._cache_size}")
            cursor.execute(f"PRAGMA journal_mode = {self._journal_mode}")
            cursor.execute(f"PRAGMA synchronous = {self._synchronous}")
            cursor.execute(f"PRAGMA temp_store = {self._temp_store}")
            cursor.execute("PRAGMA foreign_keys = ON")

            conn.commit()

        logger.info(
            "Database initialized",
            path=str(self._database_path),
            journal_mode=self._journal_mode,
        )

        # Run migrations
        self.migrate()

    def migrate(self) -> None:
        """Run database migrations."""
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()

            # Get current version
            try:
                cursor.execute(
                    "SELECT MAX(version) FROM schema_version"
                )
                result = cursor.fetchone()
                current_version = result[0] if result[0] is not None else 0
            except sqlite3.Error:
                current_version = 0

            logger.info("Current schema version", version=current_version)

            # Apply migrations
            for migration in self.MIGRATIONS:
                if migration.version > current_version:
                    logger.info(
                        "Applying migration",
                        version=migration.version,
                        description=migration.description,
                    )

                    try:
                        # Execute migration SQL
                        cursor.executescript(migration.sql)

                        # Record migration
                        cursor.execute(
                            """
                            INSERT INTO schema_version (version, applied_at, description)
                            VALUES (?, ?, ?)
                            """,
                            (migration.version, time.time(), migration.description),
                        )

                        conn.commit()

                        logger.info("Migration applied", version=migration.version)

                    except sqlite3.Error as e:
                        conn.rollback()
                        raise MigrationError(
                            f"Migration {migration.version} failed: {e}",
                            {
                                "version": migration.version,
                                "description": migration.description,
                            },
                        ) from e

    def execute(
        self,
        sql: str,
        parameters: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> sqlite3.Cursor:
        """
        Execute SQL query.

        Args:
            sql: SQL query
            parameters: Query parameters

        Returns:
            Cursor with results

        Raises:
            QueryError: If query fails
        """
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                if parameters:
                    cursor.execute(sql, parameters)
                else:
                    cursor.execute(sql)
                conn.commit()
                return cursor

        except sqlite3.IntegrityError as e:
            raise IntegrityError(
                f"Integrity constraint violated: {e}",
                {"sql": sql},
            ) from e
        except sqlite3.Error as e:
            raise QueryError(
                f"Query failed: {e}",
                {"sql": sql},
            ) from e

    def executemany(
        self,
        sql: str,
        parameters: list[tuple[Any, ...]] | list[dict[str, Any]],
    ) -> sqlite3.Cursor:
        """
        Execute SQL query with multiple parameter sets.

        Args:
            sql: SQL query
            parameters: List of parameter sets

        Returns:
            Cursor with results

        Raises:
            QueryError: If query fails
        """
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(sql, parameters)
                conn.commit()
                return cursor

        except sqlite3.IntegrityError as e:
            raise IntegrityError(
                f"Integrity constraint violated: {e}",
                {"sql": sql},
            ) from e
        except sqlite3.Error as e:
            raise QueryError(
                f"Query failed: {e}",
                {"sql": sql},
            ) from e

    def fetchone(
        self,
        sql: str,
        parameters: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        Fetch one row.

        Args:
            sql: SQL query
            parameters: Query parameters

        Returns:
            Row as dictionary or None
        """
        cursor = self.execute(sql, parameters)
        row = cursor.fetchone()
        return dict(row) if row else None

    def fetchall(
        self,
        sql: str,
        parameters: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch all rows.

        Args:
            sql: SQL query
            parameters: Query parameters

        Returns:
            List of rows as dictionaries
        """
        cursor = self.execute(sql, parameters)
        return [dict(row) for row in cursor.fetchall()]

    def insert(self, table: str, data: dict[str, Any]) -> int:
        """
        Insert row into table.

        Args:
            table: Table name
            data: Column-value mapping

        Returns:
            ID of inserted row
        """
        # VALIDATE table name to prevent SQL injection
        table = validate_table_name(table)

        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" * len(data))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        cursor = self.execute(sql, tuple(data.values()))
        return cursor.lastrowid

    def update(
        self,
        table: str,
        data: dict[str, Any],
        where: str,
        where_params: tuple[Any, ...] | None = None,
    ) -> int:
        """
        Update rows in table.

        Args:
            table: Table name
            data: Column-value mapping
            where: WHERE clause
            where_params: WHERE clause parameters

        Returns:
            Number of rows updated
        """
        # VALIDATE table name to prevent SQL injection
        table = validate_table_name(table)

        set_clause = ", ".join(f"{k} = ?" for k in data.keys())
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"

        params = tuple(data.values())
        if where_params:
            params += where_params

        cursor = self.execute(sql, params)
        return cursor.rowcount

    def delete(
        self,
        table: str,
        where: str,
        where_params: tuple[Any, ...] | None = None,
    ) -> int:
        """
        Delete rows from table.

        Args:
            table: Table name
            where: WHERE clause
            where_params: WHERE clause parameters

        Returns:
            Number of rows deleted
        """
        # VALIDATE table name to prevent SQL injection
        table = validate_table_name(table)

        sql = f"DELETE FROM {table} WHERE {where}"
        cursor = self.execute(sql, where_params)
        return cursor.rowcount

    def vacuum(self) -> None:
        """Vacuum database to reclaim space."""
        with self._pool.get_connection() as conn:
            conn.execute("VACUUM")
            logger.info("Database vacuumed")

    def close(self) -> None:
        """Close all database connections."""
        self._pool.close_all()
        logger.info("Database closed")

    def get_stats(self) -> dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with statistics
        """
        stats = {}

        with self._pool.get_connection() as conn:
            cursor = conn.cursor()

            # Database size
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            stats["size_bytes"] = page_count * page_size

            # Table counts
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [row[0] for row in cursor.fetchall()]

            stats["tables"] = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats["tables"][table] = cursor.fetchone()[0]

            # Schema version
            try:
                cursor.execute("SELECT MAX(version) FROM schema_version")
                stats["schema_version"] = cursor.fetchone()[0]
            except sqlite3.Error:
                stats["schema_version"] = 0

        return stats


def create_database(
    database_path: str | Path,
    **kwargs: Any,
) -> Database:
    """
    Create and initialize database (convenience function).

    Args:
        database_path: Path to database file
        **kwargs: Additional database configuration

    Returns:
        Database instance
    """
    return Database(database_path, **kwargs)
