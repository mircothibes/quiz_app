from __future__ import annotations

import logging
import sys
from typing import Any, Optional, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QMessageBox, QStackedWidget

from db import db
from ui_categories import CategoryWidget
from ui_dashboard import DashboardWidget
from ui_login import LoginWidget
from ui_quiz import QuizWidget
from ui_results import ResultsWidget

logger = logging.getLogger(__name__)


UserData = Tuple[int, str]


class QuizApp(QMainWindow):
    """Main application window.

    Responsibilities:
    - Own the application navigation (QStackedWidget)
    - Connect UI signals to navigation handlers
    - Keep current user state
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

    # -------------------------
    # Setup
    # -------------------------
    def _build_pages(self) -> None:
        """Create and register all pages.

        Notes:
            The dashboard is created after login because it depends on the username.
        """
        self.setWindowTitle("Advanced Quiz App")
        self.setGeometry(100, 100, 900, 700)

        self.login_page = LoginWidget()
        self.categories_page = CategoryWidget()
        self.quiz_page = QuizWidget()
        self.results_page = ResultsWidget()
        self.admin_page = self._create_placeholder("➕ Admin", "Coming soon...")

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.categories_page)
        self.stack.addWidget(self.quiz_page)
        self.stack.addWidget(self.results_page)
        self.stack.addWidget(self.admin_page)

    def _wire_signals(self) -> None:
        """Connect UI signals to handlers."""
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

    def _set_initial_view(self) -> None:
        """Start on login page."""
        self.stack.setCurrentWidget(self.login_page)

    @staticmethod
    def _create_placeholder(title: str, message: str) -> QLabel:
        """Create a placeholder page (temporary screen)."""
        placeholder = QLabel(f"{title}\n\n{message}")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("font-size: 24px; color: #7f8c8d;")
        return placeholder

    # -------------------------
    # Infrastructure
    # -------------------------
    def ensure_database_connection(self) -> bool:
        """Ensure PostgreSQL is reachable, show a friendly error otherwise."""
        if db.connect():
            return True

        QMessageBox.critical(
            self,
            "Database Error",
            "Could not connect to PostgreSQL.\n\n"
            "Ensure Docker is running and the database container is up.",
        )
        return False

    # -------------------------
    # Navigation / handlers
    # -------------------------
    def on_login_success(self, user_data: UserData) -> None:
        """Handle successful login and open the dashboard."""
        user_id, username = user_data
        self.current_user = user_data

        self._create_or_replace_dashboard(username)
        self.stack.setCurrentWidget(self.dashboard_page)

        logger.info("User logged in: %s (id=%s)", username, user_id)

    def _create_or_replace_dashboard(self, username: str) -> None:
        """Create dashboard or replace the current one (username-dependent)."""
        if self.dashboard_page is not None:
            self.stack.removeWidget(self.dashboard_page)
            self.dashboard_page.deleteLater()

        self.dashboard_page = DashboardWidget(username)
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

    def show_categories(self) -> None:
        """Navigate to categories page and refresh its content."""
        self.categories_page.load_categories()
        self.stack.setCurrentWidget(self.categories_page)

    def show_admin(self) -> None:
        """Navigate to admin page (placeholder)."""
        self.stack.setCurrentWidget(self.admin_page)

    def on_category_selected(self, category_id: int, category_name: str) -> None:
        """Load quiz for the chosen category and open quiz page."""
        logger.info("Loading quiz: %s (id=%s)", category_name, category_id)
        self.quiz_page.load_quiz(category_id, category_name)
        self.stack.setCurrentWidget(self.quiz_page)

    def on_quiz_completed(self, results: dict[str, Any]) -> None:
        """Handle quiz completion and show results screen."""
        logger.info("Quiz completed. Opening results page.")
        self.results_page.load_results(results)
        self.stack.setCurrentWidget(self.results_page)

    def on_retake_quiz(self, category_id: int, category_name: str) -> None:
        """Restart quiz for the same category."""
        self.quiz_page.load_quiz(category_id, category_name)
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
    """Application entry point."""
    configure_logging()

    app = QApplication(sys.argv)
    window = QuizApp()

    if not window.ensure_database_connection():
        return 1

    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
