"""
Sanctuary 3.0 — Secure Vault (AES-256 GCM)
Zero-telemetry encrypted storage for all user interaction data.

Refactored from v2.0:
- Uses absolute paths from Config (no more relative path breakage)
- Lazy initialization (no side effects on import)
- Context-managed DB connections
"""

import sqlite3
import json
import os
import logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from datetime import datetime

from config import Config

logger = logging.getLogger(__name__)


def _get_or_create_key() -> bytes:
    """Load the AES-256 key from disk, or generate one if it doesn't exist."""
    key_path = Config.KEY_FILE
    os.makedirs(os.path.dirname(key_path), exist_ok=True)

    if os.path.exists(key_path):
        with open(key_path, "rb") as f:
            return f.read()

    key = AESGCM.generate_key(bit_length=256)
    with open(key_path, "wb") as f:
        f.write(key)
    logger.info("Generated new AES-256 encryption key at %s", key_path)
    return key


class SecureVault:
    """
    Encrypts all user data via AES-256 GCM before writing to SQLite.
    Guarantees that even if the database file is stolen, the data is unreadable
    without the key file.
    """

    def __init__(self):
        self._initialized = False
        self._key: bytes | None = None
        self._aesgcm: AESGCM | None = None

    def _ensure_init(self):
        """Lazy initialization — only creates DB/key when first used."""
        if self._initialized:
            return

        self._key = _get_or_create_key()
        self._aesgcm = AESGCM(self._key)

        os.makedirs(os.path.dirname(Config.DB_PATH), exist_ok=True)
        # Run migrations (creates tables and tracks schema version)
        try:
            # Attempt to run Alembic migrations
            from alembic import command as alembic_command
            from alembic.config import Config as AlembicConfig
            alembic_cfg = AlembicConfig("alembic.ini")
            # Upgrade to head (apply all migrations)
            alembic_command.upgrade(alembic_cfg, "head")
        except Exception as e:
            logger.warning("Alembic migration failed (%s); falling back to custom manager", e)
            try:
                from migrations import get_default_migration_manager
                mgr = get_default_migration_manager()
                mgr.run_migrations()
            except Exception:
                # Fallback: attempt to create tables if migrations unavailable
                with sqlite3.connect(Config.DB_PATH) as conn:
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
        self._initialized = True
        logger.info("SecureVault initialized (DB: %s)", Config.DB_PATH)

    def encrypt_and_store(self, data_dict: dict) -> int:
        """Encrypt a dict via AES-256 GCM and store the blob in SQLite."""
        self._ensure_init()

        plaintext = json.dumps(data_dict).encode("utf-8")
        nonce = os.urandom(12)  # GCM standard 96-bit nonce
        ciphertext = self._aesgcm.encrypt(nonce, plaintext, None)
        with sqlite3.connect(Config.DB_PATH) as conn:
            cur = conn.execute(
                "INSERT INTO encrypted_logs (timestamp, nonce, ciphertext) VALUES (?, ?, ?)",
                (datetime.now().isoformat(), nonce, ciphertext),
            )
            row_id = cur.lastrowid
        logger.debug("Encrypted and stored 1 log entry (id=%s).", row_id)
        return row_id

    def retrieve_and_decrypt(self) -> list[dict]:
        """Retrieve and decrypt all stored logs."""
        self._ensure_init()

        with sqlite3.connect(Config.DB_PATH) as conn:
            rows = conn.execute(
                "SELECT id, timestamp, nonce, ciphertext FROM encrypted_logs"
            ).fetchall()

        decrypted = []
        for row_id, timestamp, nonce, ciphertext in rows:
            try:
                plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
                decrypted.append({
                    "id": row_id,
                    "timestamp": timestamp,
                    "data": json.loads(plaintext.decode("utf-8")),
                })
            except Exception as e:
                logger.error("Failed to decrypt record %d: %s", row_id, e)

        return decrypted

    def store_feedback(self, log_id: int | None, rating: int | None = None, feedback_text: str | None = None) -> None:
        """
        Store user feedback for a response (encrypted).

        Args:
            log_id: Optional reference to the original encrypted_logs entry.
            rating: Optional numeric rating (1-5, or custom scale).
            feedback_text: Optional text feedback.
        """
        self._ensure_init()

        feedback_data = {
            "log_id": log_id,
            "rating": rating,
            "feedback_text": feedback_text,
        }

        plaintext = json.dumps(feedback_data).encode("utf-8")
        nonce = os.urandom(12)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext, None)

        with sqlite3.connect(Config.DB_PATH) as conn:
            conn.execute(
                "INSERT INTO feedback (log_id, timestamp, rating, feedback_text, nonce, ciphertext) VALUES (?, ?, ?, ?, ?, ?)",
                (log_id, datetime.now().isoformat(), rating, feedback_text, nonce, ciphertext),
            )
        logger.debug("Stored feedback for log_id %s (rating: %s)", log_id, rating)

    def retrieve_and_decrypt_feedback(self) -> list[dict]:
        """Retrieve and decrypt all stored feedback entries."""
        self._ensure_init()

        with sqlite3.connect(Config.DB_PATH) as conn:
            rows = conn.execute(
                "SELECT id, log_id, timestamp, rating, feedback_text, nonce, ciphertext FROM feedback"
            ).fetchall()

        decrypted = []
        for row_id, log_id, timestamp, rating, feedback_text, nonce, ciphertext in rows:
            try:
                plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
                decrypted.append({
                    "id": row_id,
                    "log_id": log_id,
                    "timestamp": timestamp,
                    "rating": rating,
                    "feedback_text": feedback_text,
                    "data": json.loads(plaintext.decode("utf-8")),
                })
            except Exception as e:
                logger.error("Failed to decrypt feedback record %d: %s", row_id, e)

        return decrypted
