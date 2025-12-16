from __future__ import annotations

import logging
from typing import Any, Iterable, Optional, Sequence

import psycopg2
from psycopg2 import OperationalError
from psycopg2.extensions import connection as PgConnection

from config import load_config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Handles all PostgreSQL database interactions."""

    def __init__(self) -> None:
        self._conn: Optional[PgConnection] = None

    def connect(self) -> bool:
        """Establish a connection to PostgreSQL.

        Returns:
            bool: True if connected successfully, False otherwise.
        """
        if self._conn is not None and not self._conn.closed:
            return True

        try:
            cfg = load_config()
            self._conn = psycopg2.connect(
                host=cfg.host,
                port=cfg.port,
                dbname=cfg.name,
                user=cfg.user,
                password=cfg.password,
                connect_timeout=5,
                application_name="quiz_app",
            )
            self._conn.autocommit = False
            logger.info("Connected to PostgreSQL database: %s", cfg.name)
            return True

        except (OperationalError, ValueError) as exc:
            logger.exception("Database connection failed: %s", exc)
            self._conn = None
            return False

    def disconnect(self) -> None:
        """Close database connection safely."""
        if self._conn is None:
            return

        try:
            if not self._conn.closed:
                self._conn.close()
                logger.info("Database connection closed")
        finally:
            self._conn = None

    def is_connected(self) -> bool:
        """Return True if there is an open connection."""
        return self._conn is not None and not self._conn.closed

    def _ensure_connection(self) -> None:
        if not self.is_connected():
            raise RuntimeError("No database connection. Call db.connect() first.")

    def fetch_one(self, query: str, params: Optional[Sequence[Any]] = None) -> Optional[tuple[Any, ...]]:
        """Run a SELECT query and return a single row (or None)."""
        self._ensure_connection()
        assert self._conn is not None

        with self._conn.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return row

    def fetch_all(self, query: str, params: Optional[Sequence[Any]] = None) -> list[tuple[Any, ...]]:
        """Run a SELECT query and return all rows (possibly empty)."""
        self._ensure_connection()
        assert self._conn is not None

        with self._conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            return rows

    def execute(self, query: str, params: Optional[Sequence[Any]] = None) -> None:
        """Run an INSERT/UPDATE/DELETE query and commit."""
        self._ensure_connection()
        assert self._conn is not None

        try:
            with self._conn.cursor() as cur:
                cur.execute(query, params)
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def test_connection(self) -> Optional[str]:
        """Test the connection by returning the PostgreSQL version string."""
        try:
            row = self.fetch_one("SELECT version();")
            return str(row[0]) if row else None
        except Exception as exc:
            logger.exception("Test query failed: %s", exc)
            return None

    def authenticate_user(self, username: str, password: str) -> Optional[tuple[int, str]]:
        """Authenticate a user with username and password.

        WARNING: This uses plain-text password comparison against `password_hash`.
        In production, use hashed passwords (bcrypt, argon2, etc.).
        """
        try:
            row = self.fetch_one(
                """
                SELECT id, username
                FROM users
                WHERE username = %s AND password_hash = %s
                """,
                (username, password),
            )
            if row:
                user_id, user_name = int(row[0]), str(row[1])
                logger.info("User authenticated: %s", user_name)
                return user_id, user_name

            logger.warning("Invalid credentials for username=%s", username)
            return None

        except Exception as exc:
            logger.exception("Authentication error: %s", exc)
            return None

    def get_categories(self) -> list[tuple[int, str, str]]:
        """Get all quiz categories."""
        try:
            rows = self.fetch_all(
                """
                SELECT id, name, description
                FROM categories
                ORDER BY name ASC
                """
            )
            return [(int(r[0]), str(r[1]), str(r[2] or "")) for r in rows]
        except Exception as exc:
            logger.exception("Error fetching categories: %s", exc)
            return []

    def get_questions_by_category(self, category_id: int) -> list[tuple[Any, ...]]:
        """Get all questions for a specific category."""
        try:
            rows = self.fetch_all(
                """
                SELECT id, question_text, correct_answer,
                       option_a, option_b, option_c, option_d
                FROM questions
                WHERE category_id = %s
                ORDER BY id
                """,
                (category_id,),
            )
            return rows
        except Exception as exc:
            logger.exception("Error fetching questions for category %s: %s", category_id, exc)
            return []


# Global instance (Singleton pattern)
db = DatabaseManager()
