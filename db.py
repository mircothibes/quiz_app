from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Any, Optional, Sequence

import psycopg2
from psycopg2 import OperationalError
from psycopg2.extensions import connection as PgConnection

from config import load_config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """PostgreSQL access layer for the Quiz App.

    This class owns a single database connection and provides:
    - Connection management (connect/disconnect/is_connected)
    - Query helpers (fetch_one/fetch_all/execute) with safe error handling
    - Domain-level methods used by the UI (auth, users, categories, questions)
    - Quiz history persistence and queries (attempts, stats)
    """

    def __init__(self) -> None:
        self._conn: Optional[PgConnection] = None

    # ---------------------------------------------------------------------
    # Connection management
    # ---------------------------------------------------------------------
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
                host=cfg.db_host,
                port=cfg.db_port,
                name=cfg.db_name,
                user=cfg.db_user,
                password=cfg.db_password,
                connect_timeout=5,
                application_name="quiz_app",
            )
            self._conn.autocommit = False
            logger.info("Connected to PostgreSQL database: %s", cfg.db_name)
            return True
        except (OperationalError, ValueError) as exc:
            logger.exception("Database connection failed: %s", exc)
            self._conn = None
            return False

    def disconnect(self) -> None:
        """Close the connection safely (if open)."""
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

    # ---------------------------------------------------------------------
    # Generic query helpers
    # ---------------------------------------------------------------------
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

    # ---------------------------------------------------------------------
    # Password hashing helpers
    # ---------------------------------------------------------------------
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using PBKDF2 (no external dependencies)."""
        salt = os.urandom(16)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
        return f"pbkdf2_sha256${salt.hex()}${dk.hex()}"

    @staticmethod
    def _verify_password(password: str, stored: str) -> bool:
        """Verify password against stored hash.

        Backward compatible:
        - If stored starts with 'pbkdf2_sha256$', verify PBKDF2.
        - Otherwise, fallback to plain-text comparison (legacy).
        """
        if stored.startswith("pbkdf2_sha256$"):
            try:
                _, salt_hex, hash_hex = stored.split("$", 2)
                salt = bytes.fromhex(salt_hex)
                expected = bytes.fromhex(hash_hex)
                dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
                return hmac.compare_digest(dk, expected)
            except Exception:
                return False

        return password == stored

    # ---------------------------------------------------------------------
    # Users (auth + registration)
    # ---------------------------------------------------------------------
    def create_user(self, username: str, password: str) -> Optional[int]:
        """Create a new user and return its id, or None if it fails."""
        self._ensure_connection()
        assert self._conn is not None

        username = username.strip()
        if not username or not password:
            return None

        password_hash = self._hash_password(password)

        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (username, password_hash)
                    VALUES (%s, %s)
                    RETURNING id
                    """,
                    (username, password_hash),
                )
                row = cur.fetchone()

            self._conn.commit()
            return int(row[0]) if row else None

        except Exception as exc:
            logger.exception("create_user failed: %s", exc)
            try:
                self._conn.rollback()
            except Exception:
                logger.exception("rollback failed")
            return None

    def authenticate_user(self, username: str, password: str) -> Optional[tuple[int, str]]:
        """Authenticate a user.

        Notes:
            This verifies password against `users.password_hash`.
            Supports:
            - PBKDF2 hashes generated by this app
            - Legacy plain-text values previously stored in password_hash
        """
        row = self.fetch_one(
            """
            SELECT id, username, password_hash
            FROM users
            WHERE username = %s
            """,
            (username,),
        )

        if not row:
            logger.warning("Invalid credentials for username=%s", username)
            return None

        user_id = int(row[0])
        user_name = str(row[1])
        stored = str(row[2] or "")

        if self._verify_password(password, stored):
            logger.info("User authenticated: %s", user_name)
            return user_id, user_name

        logger.warning("Invalid credentials for username=%s", username)
        return None

    # ---------------------------------------------------------------------
    # Domain methods used by the app
    # ---------------------------------------------------------------------
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

    def get_quiz_questions(self, category_id: int, limit: int) -> list[tuple[Any, ...]]:
        """Return a randomized subset of questions for a quiz run."""
        safe_limit = max(1, int(limit))

        return self.fetch_all(
            """
            SELECT id, question_text, correct_answer,
                   option_a, option_b, option_c, option_d
            FROM questions
            WHERE category_id = %s
            ORDER BY RANDOM()
            LIMIT %s
            """,
            (category_id, safe_limit),
        )

    def get_questions_by_category(self, category_id: int, limit: Optional[int] = None) -> list[tuple[Any, ...]]:
        """Return questions for the given category.

        Args:
            category_id: Category identifier.
            limit: If provided, return at most this many questions.

        Returns:
            A list of rows: (id, question_text, correct_answer, option_a, option_b, option_c, option_d)
        """
        if limit is None:
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

        return self.fetch_all(
            """
            SELECT id, question_text, correct_answer,
                   option_a, option_b, option_c, option_d
            FROM questions
            WHERE category_id = %s
            ORDER BY RANDOM()
            LIMIT %s
            """,
            (category_id, limit),
        )

    def list_questions(self, limit: int = 200) -> list[tuple[int, str, str, str]]:
        """Return a list of questions (lightweight) for the admin table.

        Returns:
            List of (question_id, category_name, question_text, correct_answer)
        """
        rows = self.fetch_all(
            """
            SELECT q.id, c.name, q.question_text, q.correct_answer
            FROM questions q
            JOIN categories c ON c.id = q.category_id
            ORDER BY q.id DESC
            LIMIT %s
            """,
            (limit,),
        )
        return [(int(r[0]), str(r[1]), str(r[2]), str(r[3])) for r in rows]

    def get_question_by_id(self, question_id: int) -> Optional[tuple[int, int, str, str, str, str, str, str]]:
        """Return full question data by id.

        Returns:
            (id, category_id, question_text, correct_answer, option_a, option_b, option_c, option_d)
        """
        row = self.fetch_one(
            """
            SELECT id, category_id, question_text, correct_answer,
                   option_a, option_b, option_c, option_d
            FROM questions
            WHERE id = %s
            """,
            (question_id,),
        )
        if not row:
            return None

        return (
            int(row[0]),
            int(row[1]),
            str(row[2]),
            str(row[3]),
            str(row[4]),
            str(row[5]),
            str(row[6]),
            str(row[7]),
        )

    def create_question(
        self,
        category_id: int,
        question_text: str,
        correct_answer: str,
        option_a: str,
        option_b: str,
        option_c: str,
        option_d: str,
    ) -> Optional[int]:
        """Create a question and return its id."""
        self._ensure_connection()
        assert self._conn is not None

        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO questions (category_id, question_text, correct_answer, option_a, option_b, option_c, option_d)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (category_id, question_text, correct_answer, option_a, option_b, option_c, option_d),
                )
                row = cur.fetchone()
            self._conn.commit()

            return int(row[0]) if row else None
        except Exception as exc:
            logger.exception("create_question failed: %s", exc)
            try:
                self._conn.rollback()
            except Exception:
                logger.exception("rollback failed")
            return None

    def update_question(
        self,
        question_id: int,
        category_id: int,
        question_text: str,
        correct_answer: str,
        option_a: str,
        option_b: str,
        option_c: str,
        option_d: str,
    ) -> bool:
        """Update an existing question."""
        return self.execute(
            """
            UPDATE questions
            SET category_id = %s,
                question_text = %s,
                correct_answer = %s,
                option_a = %s,
                option_b = %s,
                option_c = %s,
                option_d = %s
            WHERE id = %s
            """,
            (category_id, question_text, correct_answer, option_a, option_b, option_c, option_d, question_id),
        )

    def delete_question(self, question_id: int) -> bool:
        """Delete a question by id."""
        return self.execute("DELETE FROM questions WHERE id = %s", (question_id,))

    # ---------------------------------------------------------------------
    # Quiz history (attempts)
    # ---------------------------------------------------------------------
    def create_quiz_attempt(
        self,
        user_id: int,
        category_id: int,
        total_questions: int,
        correct_count: int,
        answered_count: int,
    ) -> Optional[int]:
        """Create a quiz attempt and return its id.

        Returns:
            attempt_id (int) on success, None on failure.
        """
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
        """Persist a single answer row for an attempt.

        Returns:
            True if the insert succeeded, False otherwise.
        """
        return self.execute(
            """
            INSERT INTO quiz_attempt_answers (attempt_id, question_id, selected_letter, correct_letter, is_correct)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (attempt_id, question_id, selected_letter, correct_letter, is_correct),
        )

    def get_recent_attempts(self, user_id: int, limit: int = 5) -> list[tuple[str, str, int, int]]:
        """Return recent attempts for a user.

        Returns:
            A list of tuples:
            (created_at_str, category_name, correct_count, total_questions)
        """
        rows = self.fetch_all(
            """
            SELECT
                to_char(a.created_at, 'YYYY-MM-DD HH24:MI') AS created_at,
                c.name AS category_name,
                a.correct_count,
                a.total_questions
            FROM quiz_attempts a
            JOIN categories c ON c.id = a.category_id
            WHERE a.user_id = %s
            ORDER BY a.created_at DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        return [(str(r[0]), str(r[1]), int(r[2]), int(r[3])) for r in rows]

    def get_attempt_stats(self, user_id: int) -> tuple[int, int, int]:
        """Return attempt stats for a user.

        Returns:
            (total_attempts, best_percent, last_percent)
        """
        total_row = self.fetch_one(
            "SELECT COUNT(*) FROM quiz_attempts WHERE user_id = %s",
            (user_id,),
        )
        total_attempts = int(total_row[0]) if total_row else 0

        best_row = self.fetch_one(
            """
            SELECT MAX(ROUND((correct_count::float / NULLIF(total_questions, 0)) * 100))
            FROM quiz_attempts
            WHERE user_id = %s
            """,
            (user_id,),
        )
        best_percent = int(best_row[0]) if best_row and best_row[0] is not None else 0

        last_row = self.fetch_one(
            """
            SELECT ROUND((correct_count::float / NULLIF(total_questions, 0)) * 100)
            FROM quiz_attempts
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,),
        )
        last_percent = int(last_row[0]) if last_row and last_row[0] is not None else 0

        return total_attempts, best_percent, last_percent


db = DatabaseManager()

