"""
Simple migration runner for SQLite database
"""
import logging
from pathlib import Path
from typing import List
import sqlite3

from .database import db_manager

logger = logging.getLogger(__name__)


class MigrationRunner:
    """Handles running database migrations"""

    def __init__(self):
        self.migrations_dir = Path(__file__).parent.parent / "migrations"

    def get_migration_files(self) -> List[Path]:
        """Get all migration files sorted by name"""
        if not self.migrations_dir.exists():
            logger.warning(f"Migrations directory not found: {self.migrations_dir}")
            return []

        migration_files = []
        for file_path in self.migrations_dir.glob("*.sql"):
            migration_files.append(file_path)

        # Sort by filename to ensure proper order
        migration_files.sort(key=lambda x: x.name)
        return migration_files

    def create_migrations_table(self) -> None:
        """Create the migrations tracking table if it doesn't exist"""
        with db_manager.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL UNIQUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def is_migration_applied(self, filename: str) -> bool:
        """Check if a migration has already been applied"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM migrations WHERE filename = ?",
                (filename,)
            )
            return cursor.fetchone()[0] > 0

    def mark_migration_applied(self, filename: str) -> None:
        """Mark a migration as applied"""
        with db_manager.get_connection() as conn:
            conn.execute(
                "INSERT INTO migrations (filename) VALUES (?)",
                (filename,)
            )
            conn.commit()

    def run_migration(self, migration_file: Path) -> None:
        """Run a single migration file"""
        filename = migration_file.name

        if self.is_migration_applied(filename):
            logger.debug(f"Migration {filename} already applied, skipping")
            return

        logger.info(f"Applying migration: {filename}")

        try:
            # Read migration content
            migration_sql = migration_file.read_text(encoding="utf-8")

            # Execute migration
            db_manager.execute_migration(migration_sql)

            # Mark as applied
            self.mark_migration_applied(filename)

            logger.info(f"Successfully applied migration: {filename}")

        except Exception as e:
            logger.error(f"Failed to apply migration {filename}: {str(e)}")
            raise

    def run_migrations(self) -> None:
        """Run all pending migrations"""
        logger.info("Starting database migrations...")

        # Ensure migrations table exists
        self.create_migrations_table()

        # Get all migration files
        migration_files = self.get_migration_files()

        if not migration_files:
            logger.info("No migration files found")
            return

        # Apply each migration
        applied_count = 0
        for migration_file in migration_files:
            if not self.is_migration_applied(migration_file.name):
                self.run_migration(migration_file)
                applied_count += 1

        if applied_count > 0:
            logger.info(f"Applied {applied_count} migrations successfully")
        else:
            logger.info("All migrations already applied")


# Global migration runner instance
migration_runner = MigrationRunner()