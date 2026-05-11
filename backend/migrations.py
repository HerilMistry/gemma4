"""
Lightweight migration manager for SQLite used by SecureVault.

This simple system stores a `schema_version` key in a meta table and
applies migrations in order. It's intentionally small to avoid adding an ORM.
"""

import sqlite3
import logging
from typing import Callable, List

from config import Config

logger = logging.getLogger(__name__)


class MigrationManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.migrations: List[tuple[int, Callable[[sqlite3.Connection], None]]] = []

    def add_migration(self, version: int, fn: Callable[[sqlite3.Connection], None]):
        self.migrations.append((version, fn))

    def _ensure_meta(self, conn: sqlite3.Connection):
        conn.execute(
            "CREATE TABLE IF NOT EXISTS _meta (k TEXT PRIMARY KEY, v TEXT)"
        )

    def _get_current_version(self, conn: sqlite3.Connection) -> int:
        row = conn.execute("SELECT v FROM _meta WHERE k='schema_version'").fetchone()
        if row:
            try:
                return int(row[0])
            except Exception:
                return 0
        return 0

    def _set_version(self, conn: sqlite3.Connection, version: int):
        conn.execute("REPLACE INTO _meta (k, v) VALUES ('schema_version', ?)", (str(version),))

    def run_migrations(self):
        logger.info("Running migrations on %s", self.db_path)
        with sqlite3.connect(self.db_path) as conn:
            self._ensure_meta(conn)
            current = self._get_current_version(conn)
            logger.info("Current DB schema version: %d", current)
            for version, fn in sorted(self.migrations):
                if version > current:
                    logger.info("Applying migration %d", version)
                    fn(conn)
                    self._set_version(conn, version)
                    conn.commit()
            logger.info("Migrations complete. DB schema version now %d", self._get_current_version(conn))


# Define migrations
def init_migration(conn: sqlite3.Connection):
    # Create the expected tables matching current SecureVault implementation
    conn.execute("""
        CREATE TABLE IF NOT EXISTS encrypted_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            nonce BLOB NOT NULL,
            ciphertext BLOB NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_id INTEGER,
            timestamp TEXT NOT NULL,
            rating INTEGER,
            feedback_text TEXT,
            nonce BLOB NOT NULL,
            ciphertext BLOB NOT NULL
        )
    """)


def get_default_migration_manager():
    mgr = MigrationManager(Config.DB_PATH)
    mgr.add_migration(1, init_migration)
    return mgr
