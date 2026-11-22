"""Unified Database Layer (PostgreSQL via DATABASE_URL with automatic SQLite fallback)."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class DatabaseManager:
    """Stores users, sessions, audit logs, AI decisions, and closed trades."""

    def __init__(self, db_path: str | Path = "data/friday_memory.db", database_url: str = ""):
        self.logger = logging.getLogger("FRIDAY")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.database_url = database_url or os.getenv("DATABASE_URL", "").strip()
        self.backend = "sqlite"
        self._pg_mod = None

        if self.database_url.startswith("postgres"):
            try:
                import psycopg  # type: ignore
                self._pg_mod = psycopg
                self.backend = "postgresql"
            except ImportError:
                self.logger.warning("DATABASE_URL set but psycopg not installed; falling back to SQLite.")

        self._init_schema()
        self._ensure_default_admin()

    def _connect(self):
        if self.backend == "postgresql" and self._pg_mod is not None:
            return self._pg_mod.connect(self.database_url)
        return sqlite3.connect(self.db_path)

    def _ph(self) -> str:
        return "%s" if self.backend == "postgresql" else "?"

    def _init_schema(self) -> None:
        id_col = "SERIAL PRIMARY KEY" if self.backend == "postgresql" else "INTEGER PRIMARY KEY AUTOINCREMENT"
        stmts = [
            f"""
            CREATE TABLE IF NOT EXISTS users (
                id {id_col},
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'admin',
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id {id_col},
                timestamp TEXT NOT NULL,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT DEFAULT ''
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS trade_journal (
                id {id_col},
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                session TEXT NOT NULL,
                htf_bias TEXT NOT NULL,
                smc_score INTEGER NOT NULL,
                ai_decision TEXT NOT NULL,
                ai_confidence INTEGER NOT NULL,
                ai_regime TEXT NOT NULL,
                ai_reasoning TEXT NOT NULL,
                entry REAL NOT NULL,
                sl REAL NOT NULL,
                tp REAL NOT NULL,
                lot_size REAL DEFAULT 0.0,
                executed INTEGER DEFAULT 0,
                outcome TEXT DEFAULT 'OPEN',
                pnl REAL DEFAULT 0.0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS closed_deals (
                ticket BIGINT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                pnl REAL NOT NULL,
                outcome TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS kv_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
        ]
        with self._connect() as conn:
            for sql in stmts:
                conn.execute(sql)
            conn.commit()

    @staticmethod
    def _hash_password(password: str, salt: str | None = None) -> str:
        s = salt or secrets.token_hex(16)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), s.encode("utf-8"), 120_000).hex()
        return f"{s}${dk}"

    @classmethod
    def _verify_password(cls, password: str, stored_hash: str) -> bool:
        if "$" not in stored_hash:
            return False
        salt, expected = stored_hash.split("$", 1)
        candidate = cls._hash_password(password, salt).split("$", 1)[1]
        return hmac.compare_digest(candidate, expected)

    def _ensure_default_admin(self) -> None:
        user = os.getenv("FRIDAY_ADMIN_USER", "tatenda").strip() or "tatenda"
        pwd = os.getenv("FRIDAY_ADMIN_PASS", "friday2026").strip() or "friday2026"
        ph = self._ph()
        with self._connect() as conn:
            row = conn.execute(f"SELECT id FROM users WHERE username = {ph}", (user,)).fetchone()
            if not row:
                conn.execute(
                    f"INSERT INTO users (username, password_hash, role, created_at) VALUES ({ph}, {ph}, {ph}, {ph})",
                    (user, self._hash_password(pwd), "admin", datetime.now(timezone.utc).isoformat()),
                )
                conn.commit()

    def create_user(self, username: str, password: str, role: str = "trader") -> bool:
        ph = self._ph()
        try:
            with self._connect() as conn:
                conn.execute(
                    f"INSERT INTO users (username, password_hash, role, created_at) VALUES ({ph}, {ph}, {ph}, {ph})",
                    (username, self._hash_password(password), role, datetime.now(timezone.utc).isoformat()),
                )
                conn.commit()
            return True
        except Exception:
            return False

    def verify_user(self, username: str, password: str) -> bool:
        ph = self._ph()
        with self._connect() as conn:
            row = conn.execute(f"SELECT password_hash FROM users WHERE username = {ph}", (username,)).fetchone()
        if not row:
            return False
        return self._verify_password(password, row[0])

    def create_session(self, username: str, hours: int = 24) -> str:
        token = secrets.token_urlsafe(32)
        exp = (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()
        ph = self._ph()
        with self._connect() as conn:
            conn.execute(f"INSERT INTO sessions (token, username, expires_at) VALUES ({ph}, {ph}, {ph})", (token, username, exp))
            conn.commit()
        return token

    def verify_session(self, token: str) -> Optional[str]:
        if not token:
            return None
        ph = self._ph()
        with self._connect() as conn:
            row = conn.execute(f"SELECT username, expires_at FROM sessions WHERE token = {ph}", (token,)).fetchone()
        if not row:
            return None
        username, exp_str = row
        try:
            if datetime.fromisoformat(exp_str) < datetime.now(timezone.utc):
                return None
        except ValueError:
            return None
        return str(username)

    def delete_session(self, token: str) -> None:
        if not token:
            return
        ph = self._ph()
        with self._connect() as conn:
            conn.execute(f"DELETE FROM sessions WHERE token = {ph}", (token,))
            conn.commit()

    def log_audit(self, username: str, action: str, details: str = "") -> None:
        ph = self._ph()
        with self._connect() as conn:
            conn.execute(
                f"INSERT INTO audit_logs (timestamp, username, action, details) VALUES ({ph}, {ph}, {ph}, {ph})",
                (datetime.now(timezone.utc).isoformat(), username, action, details),
            )
            conn.commit()

    def set_state(self, key: str, value: str) -> None:
        ph = self._ph()
        ts = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            if self.backend == "postgresql":
                conn.execute(
                    f"INSERT INTO kv_state (key, value, updated_at) VALUES ({ph}, {ph}, {ph}) "
                    f"ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = EXCLUDED.updated_at",
                    (key, value, ts),
                )
            else:
                conn.execute(
                    "INSERT OR REPLACE INTO kv_state (key, value, updated_at) VALUES (?, ?, ?)",
                    (key, value, ts),
                )
            conn.commit()

    def get_state(self, key: str, default: str = "") -> str:
        ph = self._ph()
        with self._connect() as conn:
            row = conn.execute(f"SELECT value FROM kv_state WHERE key = {ph}", (key,)).fetchone()
        return str(row[0]) if row else default
