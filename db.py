from __future__ import annotations

import logging
from typing import Any, Optional, Sequence

import psycopg2
from psycopg2 import OperationalError
from psycopg2.extensions import connection as PgConnection

from config import load_config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """PostgreSQL access layer for the Quiz App.

    This class owns a single connection and provides helper methods for:
    - Connecting/disconnecting
    - Running SELECT queries (fetch_one/fetch_all)
    - Running write queries with commit/rollback (execute)
    - Domain queries used by the UI (auth, categories, questions, attempts)
    """

    def __init__(self) -> None:
        self._conn: Optional[PgConnection] = None

    # -------------------------
    # Connection management
    # -------------------------
    def connect(self) -> bool:
        """Open a connection to PostgreSQL.

        Returns:
            True if connected (or already connected), False otherwise.
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
        """Close the connection safely."""
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
        """Raise if there is no active DB connection."""
        if not self.is_connected():
            raise RuntimeError("No database connection. Call db.connect() first.")

    # -------------------------
    # Generic query helpers
    # -------------------------
    def fetch_one(self, query: str, params: Optional[Sequence[Any]] = None) -> Optional[tuple[Any, ...]]:
        """Run a SELECT query and return a single row (or None)."""
        self._ensure_connection()
        assert self._conn is not None

        try:
            with self._conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchone()
        except Exception as exc:
            logger.exception("fetch_one failed: %s", exc)
            return None

    def fetch_all(self, query: str, params: Optional[Sequence[Any]] = None) -> list[tuple[Any, ...]]:
        """Run a SELECT query and return all rows (possibly empty)."""
        self._ensure_connection()
        assert self._conn is not None

        try:
            with self._conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()
        except Exception as exc:
            logger.exception("fetch_all failed: %s", exc)
            return []

    def execute(self, query: str, params: Optional[Sequence[Any]] = None) -> bool:
        """Run an INSERT/UPDATE/DELETE query and commit.

        Returns:
            True on success, False on failure (rollback is performed).
        """
        self._ensure_connection()
        assert self._conn is not None

        try:
            with self._conn.cursor() as cur:
                cur.execute(query, params)
            self._conn.commit()
            return True
        except Exception as exc:
            logger.exception("execute failed: %s", exc)
            try:
                self._conn.rollback()
            except Exception:
                logger.exception("rollback failed")
            return False

    def test_connection(self) -> Optional[str]:
        """Return PostgreSQL version string, or None on failure."""
        row = self.fetch_one("SELECT version();")
        return str(row[0]) if row else None

    # -------------------------
    # Domain methods used by the app
    # -------------------------
    def authenticate_user(self, username: str, password: str) -> Optional[tuple[int, str]]:
        """Authenticate a user.

        Notes:
            This compares plain text password against `password_hash`.
            For production, replace with a proper password hash strategy.
        """
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

    def get_categories(self) -> list[tuple[int, str, str]]:
        """Return all quiz categories."""
        rows = self.fetch_all(
            """
            SELECT id, name, description
            FROM categories
            ORDER BY name ASC
            """
        )
        return [(int(r[0]), str(r[1]), str(r[2] or "")) for r in rows]

    def get_questions_by_category(self, category_id: int) -> list[tuple[Any, ...]]:
        """Return questions for the given category."""
        return self.fetch_all(
            """
            SELECT id, question_text, correct_answer,
                   option_a, option_b, option_c, option_d
            FROM questions
            WHERE category_id = %s
            ORDER BY id
            """,
            (category_id,),
        )

    # -------------------------
    # Quiz history (attempts)
    # -------------------------
    def create_quiz_attempt(
        self,
        user_id: int,
        category_id: int,
        total_questions: int,
        correct_count: int,
        answered_count: int,
    ) -> Optional[int]:
        """Create a quiz attempt and return its id (or None on failure)."""
        self._ensure_connection()
        assert self._conn is not None

        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO quiz_attempts (user_id, category_id, total_questions, correct_count, answered_count)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (user_id, category_id, total_questions, correct_count, answered_count),
                )
                row = cur.fetchone()
            self._conn.commit()

            if not row:
                return None
            return int(row[0])

        except Exception as exc:
            logger.exception("create_quiz_attempt failed: %s", exc)
            try:
                self._conn.rollback()
            except Exception:
                logger.exception("rollback failed")
            return None

    def add_attempt_answer(
        self,
        attempt_id: int,
        question_id: int,
        selected_letter: Optional[str],
        correct_letter: str,
        is_correct: bool,
    ) -> bool:
        """Persist a single answer row for an attempt."""
        return self.execute(
            """
            INSERT INTO quiz_attempt_answers (attempt_id, question_id, selected_letter, correct_letter, is_correct)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (attempt_id, question_id, selected_letter, correct_letter, is_correct),
        )


db = DatabaseManager()

