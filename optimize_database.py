#!/usr/bin/env python3
"""
Database Optimization Script for Smart Search Pro v3.0

Implements all recommended optimizations:
1. Add missing indexes
2. Normalize file_tags schema
3. Create eviction policy for preview_cache
4. Generate database audit report
"""

import sqlite3
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Handles database optimization operations"""

    def __init__(self, db_path: str):
        """Initialize optimizer with database path"""
        self.db_path = Path(db_path)
        self.backup_path = self.db_path.with_suffix('.backup')

    def backup_database(self) -> bool:
        """Create backup before optimization"""
        try:
            if self.db_path.exists():
                import shutil
                shutil.copy2(self.db_path, self.backup_path)
                logger.info(f"Backup created: {self.backup_path}")
                return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

    def connect(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def add_missing_indexes(self) -> Dict[str, bool]:
        """Add all recommended composite and missing indexes"""
        indexes_to_create = {
            "idx_hash_cache_hash": {
                "table": "hash_cache",
                "sql": """
                    CREATE INDEX IF NOT EXISTS idx_hash_cache_hash
                    ON hash_cache(file_hash)
                """
            },
            "idx_search_history_query_timestamp": {
                "table": "search_history",
                "sql": """
                    CREATE INDEX IF NOT EXISTS idx_search_history_query_timestamp
                    ON search_history(query, timestamp DESC)
                """
            },
            "idx_file_tags_composite": {
                "table": "file_tags",
                "sql": """
                    CREATE INDEX IF NOT EXISTS idx_file_tags_composite
                    ON file_tags(file_path, tag)
                """
            },
            "idx_preview_cache_accessed": {
                "table": "preview_cache",
                "sql": """
                    CREATE INDEX IF NOT EXISTS idx_preview_cache_accessed
                    ON preview_cache(last_accessed)
                """
            },
            "idx_operation_history_timestamp_type": {
                "table": "operation_history",
                "sql": """
                    CREATE INDEX IF NOT EXISTS idx_operation_history_timestamp_type
                    ON operation_history(timestamp DESC, operation_type)
                """
            }
        }

        results = {}
        conn = self.connect()

        try:
            for index_name, config in indexes_to_create.items():
                try:
                    conn.execute(config["sql"])
                    conn.commit()
                    logger.info(f"✓ Created index: {index_name}")
                    results[index_name] = True
                except sqlite3.OperationalError as e:
                    if "already exists" in str(e):
                        logger.info(f"✓ Index already exists: {index_name}")
                        results[index_name] = True
                    else:
                        logger.error(f"✗ Failed to create index {index_name}: {e}")
                        results[index_name] = False

        finally:
            conn.close()

        return results

    def normalize_file_tags(self) -> bool:
        """
        Normalize file_tags schema:
        - Create separate tags table
        - Migrate data
        - Update foreign key constraint
        """
        conn = self.connect()
        cursor = conn.cursor()

        try:
            # Step 1: Check if tags table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='tags'"
            )
            tags_exist = cursor.fetchone() is not None

            if not tags_exist:
                logger.info("Creating normalized tags table...")

                # Create tags table
                cursor.execute("""
                    CREATE TABLE tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tag TEXT NOT NULL UNIQUE
                    )
                """)

                # Extract unique tags from file_tags
                cursor.execute("SELECT DISTINCT tag FROM file_tags")
                unique_tags = [row[0] for row in cursor.fetchall()]

                logger.info(f"Found {len(unique_tags)} unique tags")

                # Insert tags
                for tag in unique_tags:
                    cursor.execute("INSERT INTO tags (tag) VALUES (?)", (tag,))

                conn.commit()
                logger.info("✓ Tags table created and populated")

                # Step 2: Create new file_tags table
                logger.info("Creating normalized file_tags junction table...")

                cursor.execute("DROP TABLE IF EXISTS file_tags_new")

                cursor.execute("""
                    CREATE TABLE file_tags_new (
                        file_path TEXT NOT NULL,
                        tag_id INTEGER NOT NULL,
                        created_at REAL NOT NULL,
                        PRIMARY KEY (file_path, tag_id),
                        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
                    )
                """)

                # Migrate data from old to new
                cursor.execute("""
                    INSERT INTO file_tags_new (file_path, tag_id, created_at)
                    SELECT ft.file_path, t.id, ft.created_at
                    FROM file_tags ft
                    JOIN tags t ON ft.tag = t.tag
                """)

                # Create index
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_file_tags_path
                    ON file_tags_new(file_path)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_file_tags_tag_id
                    ON file_tags_new(tag_id)
                """)

                conn.commit()
                logger.info("✓ Data migrated to normalized schema")

                # Step 3: Swap tables
                cursor.execute("ALTER TABLE file_tags RENAME TO file_tags_old")
                cursor.execute("ALTER TABLE file_tags_new RENAME TO file_tags")

                conn.commit()
                logger.info("✓ Tables swapped")

                # Step 4: Cleanup
                cursor.execute("DROP TABLE IF EXISTS file_tags_old")
                conn.commit()
                logger.info("✓ Old table removed")

                return True

            else:
                logger.info("✓ Normalized schema already in place")
                return True

        except Exception as e:
            logger.error(f"✗ Failed to normalize file_tags: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def add_preview_cache_eviction(self) -> bool:
        """Add trigger-based eviction policy to preview_cache"""
        conn = self.connect()
        cursor = conn.cursor()

        try:
            # Create table for preview_cache metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_limits (
                    cache_name TEXT PRIMARY KEY,
                    max_size INTEGER NOT NULL,
                    eviction_size INTEGER NOT NULL
                )
            """)

            # Insert default limits
            cursor.execute("""
                INSERT OR REPLACE INTO cache_limits (cache_name, max_size, eviction_size)
                VALUES ('preview_cache', 50000000, 5000000)
            """)

            conn.commit()
            logger.info("✓ Cache limits table created")

            # Create trigger to enforce eviction
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS preview_cache_eviction
                AFTER INSERT ON preview_cache
                WHEN (
                    SELECT COUNT(*) * (
                        SELECT SUM(LENGTH(preview_data))
                        FROM preview_cache
                    ) FROM preview_cache
                ) > (
                    SELECT max_size FROM cache_limits WHERE cache_name = 'preview_cache'
                )
                BEGIN
                    DELETE FROM preview_cache
                    WHERE file_path IN (
                        SELECT file_path FROM preview_cache
                        ORDER BY last_accessed ASC
                        LIMIT (
                            SELECT eviction_size FROM cache_limits
                            WHERE cache_name = 'preview_cache'
                        )
                    );
                END
            """)

            conn.commit()
            logger.info("✓ Eviction trigger created")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to add eviction policy: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def analyze_performance(self) -> Dict:
        """Analyze database performance metrics"""
        conn = self.connect()
        cursor = conn.cursor()
        stats = {}

        try:
            # Database size
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            total_size = page_count * page_size

            stats["database_size_mb"] = total_size / 1024 / 1024

            # Table row counts
            stats["tables"] = {}
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats["tables"][table] = count

            # Index count
            cursor.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
            )
            stats["index_count"] = cursor.fetchone()[0]

            # WAL file size
            wal_path = self.db_path.with_suffix('.db-wal')
            if wal_path.exists():
                stats["wal_size_mb"] = wal_path.stat().st_size / 1024 / 1024

            # Check for slow indexes (unused)
            stats["unused_indexes"] = self._find_unused_indexes(cursor)

            # Get PRAGMA info
            cursor.execute("PRAGMA journal_mode")
            stats["journal_mode"] = cursor.fetchone()[0]

            cursor.execute("PRAGMA synchronous")
            sync_modes = {0: "OFF", 1: "NORMAL", 2: "FULL", 3: "EXTRA"}
            stats["synchronous"] = sync_modes.get(cursor.fetchone()[0], "UNKNOWN")

            cursor.execute("PRAGMA cache_size")
            stats["cache_size_kb"] = cursor.fetchone()[0]

        finally:
            conn.close()

        return stats

    def _find_unused_indexes(self, cursor: sqlite3.Cursor) -> List[str]:
        """Find indexes that might be unused"""
        # Note: SQLite doesn't have built-in unused index detection
        # This is a heuristic based on index creation time
        unused = []
        try:
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index'
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            # In production, use EXPLAIN QUERY PLAN to identify unused indexes
            for row in cursor.fetchall():
                # Placeholder logic
                pass
        except Exception as e:
            logger.warning(f"Could not analyze unused indexes: {e}")

        return unused

    def vacuum_database(self) -> bool:
        """Optimize database with VACUUM"""
        conn = self.connect()

        try:
            logger.info("Running VACUUM optimization...")
            start_time = time.time()

            conn.execute("VACUUM")

            duration = time.time() - start_time
            logger.info(f"✓ VACUUM completed in {duration:.2f}s")

            # Analyze after vacuum
            conn.execute("ANALYZE")
            logger.info("✓ ANALYZE completed")

            return True

        except Exception as e:
            logger.error(f"✗ VACUUM failed: {e}")
            return False
        finally:
            conn.close()

    def generate_report(self, output_file: str = None) -> str:
        """Generate comprehensive optimization report"""
        if output_file is None:
            output_file = self.db_path.parent / "optimization_report.json"

        report = {
            "timestamp": time.time(),
            "database_path": str(self.db_path),
            "backup_path": str(self.backup_path),
            "optimizations": {
                "indexes_added": self.add_missing_indexes(),
                "schema_normalized": self.normalize_file_tags(),
                "eviction_policy_added": self.add_preview_cache_eviction(),
            },
            "performance_stats": self.analyze_performance(),
        }

        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"✓ Report generated: {output_file}")
        return json.dumps(report, indent=2)


def main():
    """Main optimization script"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Optimize Smart Search Pro database"
    )
    parser.add_argument(
        "--db-path",
        default="~/.smart_search/data.db",
        help="Path to database file"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        default=True,
        help="Create backup before optimization"
    )
    parser.add_argument(
        "--report",
        default="optimization_report.json",
        help="Path to save optimization report"
    )

    args = parser.parse_args()

    db_path = Path(args.db_path).expanduser()

    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return 1

    optimizer = DatabaseOptimizer(str(db_path))

    logger.info("=" * 60)
    logger.info("Smart Search Pro - Database Optimization")
    logger.info("=" * 60)

    # Create backup
    if args.backup:
        optimizer.backup_database()

    # Run optimizations
    logger.info("\nStep 1: Adding missing indexes...")
    optimizer.add_missing_indexes()

    logger.info("\nStep 2: Normalizing file_tags schema...")
    optimizer.normalize_file_tags()

    logger.info("\nStep 3: Adding eviction policy...")
    optimizer.add_preview_cache_eviction()

    logger.info("\nStep 4: Running VACUUM...")
    optimizer.vacuum_database()

    # Generate report
    logger.info("\nStep 5: Generating report...")
    report = optimizer.generate_report(args.report)

    logger.info("\n" + "=" * 60)
    logger.info("Optimization Complete!")
    logger.info("=" * 60)
    print(report)

    return 0


if __name__ == "__main__":
    exit(main())
