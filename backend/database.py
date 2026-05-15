"""
Sanctuary 3.0 — Secure Vault (AES-256 GCM)
Supports session-based chat history and encrypted feedback storage.
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
    key_path = Config.KEY_FILE
    os.makedirs(os.path.dirname(key_path), exist_ok=True)
    if os.path.exists(key_path):
        with open(key_path, "rb") as f: return f.read()
    key = AESGCM.generate_key(bit_length=256)
    with open(key_path, "wb") as f: f.write(key)
    return key

class SecureVault:
    def __init__(self):
        self._initialized = False
        self._key: bytes | None = None
        self._aesgcm: AESGCM | None = None

    def _ensure_init(self):
        if self._initialized: return
        self._key = _get_or_create_key()
        self._aesgcm = AESGCM(self._key)
        os.makedirs(os.path.dirname(Config.DB_PATH), exist_ok=True)
        with sqlite3.connect(Config.DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS encrypted_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT DEFAULT 'legacy',
                    timestamp TEXT NOT NULL,
                    nonce BLOB NOT NULL,
                    ciphertext BLOB NOT NULL
                )
            """)
            try: conn.execute("ALTER TABLE encrypted_logs ADD COLUMN session_id TEXT DEFAULT 'legacy'")
            except sqlite3.OperationalError: pass
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

    def encrypt_and_store(self, data_dict: dict, session_id: str = "legacy") -> int:
        self._ensure_init()
        plaintext = json.dumps(data_dict).encode("utf-8")
        nonce = os.urandom(12)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext, None)
        with sqlite3.connect(Config.DB_PATH) as conn:
            cur = conn.execute(
                "INSERT INTO encrypted_logs (session_id, timestamp, nonce, ciphertext) VALUES (?, ?, ?, ?)",
                (session_id, datetime.now().isoformat(), nonce, ciphertext),
            )
            return cur.lastrowid

    def retrieve_session_history(self, session_id: str) -> list[dict]:
        self._ensure_init()
        with sqlite3.connect(Config.DB_PATH) as conn:
            rows = conn.execute(
                "SELECT id, timestamp, nonce, ciphertext FROM encrypted_logs WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,)
            ).fetchall()
        decrypted = []
        for row_id, timestamp, nonce, ciphertext in rows:
            try:
                plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
                data = json.loads(plaintext.decode("utf-8"))
                decrypted.append({"role": "user" if "original_text" in data else "assistant", "text": data.get("original_text") or data.get("response", ""), "timestamp": timestamp, "data": data})
            except: pass
        return decrypted

    def list_sessions(self) -> list[dict]:
        self._ensure_init()
        with sqlite3.connect(Config.DB_PATH) as conn:
            rows = conn.execute("SELECT session_id, MIN(timestamp), nonce, ciphertext FROM encrypted_logs GROUP BY session_id ORDER BY MIN(timestamp) DESC").fetchall()
        sessions = []
        for sid, start, nonce, ciphertext in rows:
            try:
                plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
                data = json.loads(plaintext.decode("utf-8"))
                preview = data.get("original_text") or data.get("response", "")
                sessions.append({"id": sid, "start_time": start, "preview": preview[:50] + "..." if len(preview) > 50 else preview})
            except: sessions.append({"id": sid, "start_time": start, "preview": "Encrypted session"})
        return sessions

    def store_feedback(self, log_id: int | None, rating: int | None = None, feedback_text: str | None = None) -> None:
        self._ensure_init()
        data = {"log_id": log_id, "rating": rating, "feedback_text": feedback_text}
        plaintext = json.dumps(data).encode("utf-8")
        nonce = os.urandom(12)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext, None)
        with sqlite3.connect(Config.DB_PATH) as conn:
            conn.execute("INSERT INTO feedback (log_id, timestamp, rating, feedback_text, nonce, ciphertext) VALUES (?, ?, ?, ?, ?, ?)", (log_id, datetime.now().isoformat(), rating, feedback_text, nonce, ciphertext))

    def retrieve_and_decrypt_feedback(self) -> list[dict]:
        self._ensure_init()
        with sqlite3.connect(Config.DB_PATH) as conn:
            rows = conn.execute("SELECT id, log_id, timestamp, rating, feedback_text, nonce, ciphertext FROM feedback").fetchall()
        decrypted = []
        for rid, lid, ts, rate, ftext, nonce, ciphertext in rows:
            try:
                plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
                decrypted.append({"id": rid, "log_id": lid, "timestamp": ts, "rating": rate, "feedback_text": ftext, "data": json.loads(plaintext.decode("utf-8"))})
            except: pass
        return decrypted
