from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Optional, Tuple

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QStackedWidget

from db import db
from ui.admin import AdminWidget
from ui.categories import CategoryWidget
from ui.dashboard import DashboardWidget
from ui.login import LoginWidget
from ui.quiz import QuizWidget
from ui.results import ResultsWidget

logger = logging.getLogger(__name__)

UserData = Tuple[int, str]  # (user_id, username)


def resource_path(relative_path: str) -> str:
    """Return an absolute path to a resource.

    This works both:
    - in development (running `python main.py`)
    - in PyInstaller builds (where files are extracted to a temp folder)

    Args:
        relative_path: Path relative to the project root (e.g., "assets/quiz_app.png").

    Returns:
        Absolute path to the resource as a string.
    """
    # PyInstaller sets sys._MEIPASS to the extraction folder at runtime
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base_dir / relative_path)


class QuizApp(QMainWindow):
    """Main application window.

    Responsibilities:
    - Own application navigation (QStackedWidget)
    - Connect UI signals to navigation handlers
    - Keep current user state
    - Persist quiz attempts when a quiz is submitted
    """

    def __init__(self) -> None:
        super().__init__()

        self.current_user: Optional[UserData] = None
        self.dashboard_page: Optional[DashboardWidget] = None

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self._build_pages()
        self._wire_signals()
        self._set_initial_view()

    # ---------------------------------------------------------------------
    # Setup
    # ---------------------------------------------------------------------
    def _build_pages(self) -> None:
        """Create and register all pages.

        Notes:
            The dashboard is created after login because it depends on username/user_id.
        """
        self.setWindowTitle("Advanced Quiz App")
        self.setGeometry(100, 100, 900, 700)

        self.login_page = LoginWidget()
        self.categories_page = CategoryWidget()
        self.quiz_page = QuizWidget()
        self.results_page = ResultsWidget()
        self.admin_page = AdminWidget()

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.categories_page)
        self.stack.addWidget(self.quiz_page)
        self.stack.addWidget(self.results_page)
        self.stack.addWidget(self.admin_page)

    def _wire_signals(self) -> None:
        """Connect UI signals to navigation handlers."""
        # Login
        self.login_page.login_successful.connect(self.on_login_success)

        # Categories
        self.categories_page.back_clicked.connect(self.show_dashboard)
        self.categories_page.category_selected.connect(self.on_category_selected)

        # Quiz
        self.quiz_page.quiz_completed.connect(self.on_quiz_completed)
        self.quiz_page.back_clicked.connect(self.show_categories)

        # Results
        self.results_page.retake_quiz_clicked.connect(self.on_retake_quiz)
        self.results_page.back_to_dashboard_clicked.connect(self.show_dashboard)
        self.results_page.back_to_categories_clicked.connect(self.show_categories)

        # Admin
        self.admin_page.back_clicked.connect(self.show_dashboard)

    def _set_initial_view(self) -> None:
        """Start on login page."""
        self.stack.setCurrentWidget(self.login_page)

    # ---------------------------------------------------------------------
    # Infrastructure
    # ---------------------------------------------------------------------
    def ensure_database_connection(self) -> bool:
        """Ensure PostgreSQL is reachable, otherwise show a user-friendly error.

        Returns:
            True if the connection is available, False otherwise.
        """
        if db.connect():
            return True

        QMessageBox.critical(
            self,
            "Database Error",
            "Could not connect to PostgreSQL.\n\n"
            "Ensure Docker is running and the database container is up.",
        )
        return False

    # ---------------------------------------------------------------------
    # Navigation / handlers
    # ---------------------------------------------------------------------
    def on_login_success(self, username: str, user_id: int) -> None:
        """Handle successful login and open the dashboard.

        Args:
            username: Authenticated username.
            user_id: Authenticated user id.
        """
        self.current_user = (user_id, username)

        self._create_or_replace_dashboard(username=username, user_id=user_id)
        self.stack.setCurrentWidget(self.dashboard_page)

        logger.info("User logged in: %s (id=%s)", username, user_id)

    def _create_or_replace_dashboard(self, username: str, user_id: int) -> None:
        """Create dashboard or replace the existing one (username/user_id-dependent)."""
        if self.dashboard_page is not None:
            self.stack.removeWidget(self.dashboard_page)
            self.dashboard_page.deleteLater()

        self.dashboard_page = DashboardWidget(username=username, user_id=user_id)
        self.dashboard_page.browse_categories_clicked.connect(self.show_categories)
        self.dashboard_page.manage_questions_clicked.connect(self.show_admin)
        self.dashboard_page.logout_clicked.connect(self.logout)

        self.stack.addWidget(self.dashboard_page)

    def show_dashboard(self) -> None:
        """Navigate to dashboard if logged in, otherwise return to login."""
        if self.dashboard_page is None or self.current_user is None:
            self.stack.setCurrentWidget(self.login_page)
            return

        self.stack.setCurrentWidget(self.dashboard_page)
        self.dashboard_page.refresh()

    def show_categories(self) -> None:
        """Navigate to categories page and refresh its content."""
        self.categories_page.load_categories()
        self.stack.setCurrentWidget(self.categories_page)

    def show_admin(self) -> None:
        """Navigate to admin page."""
        self.admin_page.refresh()
        self.stack.setCurrentWidget(self.admin_page)

    def on_category_selected(self, category_id: int, category_name: str, limit: int) -> None:
        """Load quiz for the selected category and open quiz page."""
        logger.info("Loading quiz: %s (id=%s, limit=%s)", category_name, category_id, limit)
        self.quiz_page.load_quiz(category_id, category_name, limit)
        self.stack.setCurrentWidget(self.quiz_page)

    def on_quiz_completed(self, results: dict[str, Any]) -> None:
        """Handle quiz completion: persist attempt (if logged in) and show results."""
        logger.info("Quiz completed. Persisting attempt (if possible) and opening results page.")

        user_id = self.current_user[0] if self.current_user else None
        category_id = int(results.get("category_id") or 0)

        questions = list(results.get("questions", []))
        answers: dict[int, str] = dict(results.get("answers", {}))

        total_questions = len(questions)
        answered_count = len(answers)

        correct_count = 0
        per_question: list[tuple[int, Optional[str], str, bool]] = []

        for q in questions:
            q_id = int(q[0])
            correct_letter = str(q[2]).strip().upper()

            selected = answers.get(q_id)
            selected_letter = str(selected).strip().upper() if selected else None

            is_correct = selected_letter is not None and selected_letter == correct_letter
            if is_correct:
                correct_count += 1

            per_question.append((q_id, selected_letter, correct_letter, is_correct))

        if user_id is not None and category_id > 0 and total_questions > 0:
            attempt_id = db.create_quiz_attempt(
                user_id=user_id,
                category_id=category_id,
                total_questions=total_questions,
                correct_count=correct_count,
                answered_count=answered_count,
            )

            if attempt_id is not None:
                for q_id, selected_letter, correct_letter, is_correct in per_question:
                    db.add_attempt_answer(
                        attempt_id=attempt_id,
                        question_id=q_id,
                        selected_letter=selected_letter,
                        correct_letter=correct_letter,
                        is_correct=is_correct,
                    )

        self.results_page.load_results(results)
        self.stack.setCurrentWidget(self.results_page)

    def on_retake_quiz(self, category_id: int, category_name: str) -> None:
        """Restart quiz for the same category.

        Note:
            If you want to preserve the last chosen 'limit', store it in app state.
        """
        self.quiz_page.load_quiz(category_id, category_name, limit=10)
        self.stack.setCurrentWidget(self.quiz_page)

    def logout(self) -> None:
        """Clear user state and return to login."""
        self.current_user = None
        self.stack.setCurrentWidget(self.login_page)
        logger.info("User logged out.")

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Close DB connection on app exit."""
        db.disconnect()
        event.accept()


def configure_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main() -> int:
    """Application entry point.

    Returns:
        Process exit code (0 on normal exit, non-zero on error).
    """
    configure_logging()

    app = QApplication(sys.argv)

    icon_path = resource_path("assets/quiz_app.png")
    app_icon = QIcon(icon_path)

    # Set application-level icon (used across windows/dialogs)
    app.setWindowIcon(app_icon)

    window = QuizApp()
    # Ensure the main window also has the icon explicitly (some OS/themes require it)
    window.setWindowIcon(app_icon)

    if not window.ensure_database_connection():
        return 1

    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())

