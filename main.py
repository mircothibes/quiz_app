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


class QuizApp(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()

        self.current_user: Optional[Tuple[int, str]] = None
        self.dashboard_page: Optional[DashboardWidget] = None

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self._build_pages()
        self._wire_signals()
        self._set_initial_view()

    def _build_pages(self) -> None:
        """Create and register all base pages (except dashboard, which is created after login)."""
        self.setWindowTitle("Advanced Quiz App")
        self.setGeometry(100, 100, 900, 700)

        # Login
        self.login_page = LoginWidget()
        self.stack.addWidget(self.login_page)

        # Categories
        self.categories_page = CategoryWidget()
        self.stack.addWidget(self.categories_page)

        # Quiz (FIX: this page existed in logic but was never created/added)
        self.quiz_page = QuizWidget()
        self.stack.addWidget(self.quiz_page)

        # Results
        self.results_page = ResultsWidget()
        self.stack.addWidget(self.results_page)

        # Admin (placeholder for now)
        self.admin_page = self._create_placeholder("➕ Admin", "Coming soon...")
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

        # Results
        self.results_page.retake_quiz_clicked.connect(self.on_retake_quiz)
        self.results_page.back_to_dashboard_clicked.connect(self.show_dashboard)
        self.results_page.back_to_categories_clicked.connect(self.show_categories)

    def _set_initial_view(self) -> None:
        """Start on login page."""
        self.stack.setCurrentWidget(self.login_page)

    def _create_placeholder(self, title: str, message: str) -> QLabel:
        """Create a placeholder page."""
        placeholder = QLabel(f"{title}\n\n{message}")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("font-size: 24px; color: #7f8c8d;")
        return placeholder

    def test_database_connection(self) -> bool:
        """Test database connection and show a user-friendly error if it fails."""
        if db.connect():
            return True

        QMessageBox.critical(
            self,
            "Database Error",
            "Could not connect to PostgreSQL.\n\nEnsure Docker is running and the database container is up.",
        )
        return False

    def on_login_success(self, user_data: Tuple[int, str]) -> None:
        """Handle successful login."""
        user_id, username = user_data
        self.current_user = user_data

        # Recreate dashboard with the correct username
        if self.dashboard_page is not None:
            self.stack.removeWidget(self.dashboard_page)
            self.dashboard_page.deleteLater()

        self.dashboard_page = DashboardWidget(username)
        self.dashboard_page.browse_categories_clicked.connect(self.show_categories)
        self.dashboard_page.manage_questions_clicked.connect(self.show_admin)
        self.dashboard_page.logout_clicked.connect(self.logout)

        # Add dashboard to stack (position does not matter because we navigate by widget ref)
        self.stack.addWidget(self.dashboard_page)
        self.stack.setCurrentWidget(self.dashboard_page)

        logger.info("User logged in: %s (id=%s)", username, user_id)

    def show_dashboard(self) -> None:
        """Navigate to dashboard if logged in, otherwise go to login."""
        if self.dashboard_page is None or self.current_user is None:
            self.stack.setCurrentWidget(self.login_page)
            return

        self.stack.setCurrentWidget(self.dashboard_page)

    def show_categories(self) -> None:
        """Navigate to categories page."""
        self.categories_page.load_categories()
        self.stack.setCurrentWidget(self.categories_page)

    def show_admin(self) -> None:
        """Navigate to admin page (placeholder)."""
        self.stack.setCurrentWidget(self.admin_page)

    def on_category_selected(self, category_id: int, category_name: str) -> None:
        """Handle category selection."""
        logger.info("Loading quiz: %s (id=%s)", category_name, category_id)
        self.quiz_page.load_quiz(category_id, category_name)
        self.stack.setCurrentWidget(self.quiz_page)

    def on_quiz_completed(self, results: dict[str, Any]) -> None:
        """Handle quiz completion."""
        logger.info("Quiz completed.")

        # If ResultsWidget has a method to render results, use it (optional, future-proof)
        if hasattr(self.results_page, "load_results"):
            try:
                self.results_page.load_results(results)  # type: ignore[attr-defined]
                self.stack.setCurrentWidget(self.results_page)
                return
            except Exception:
                logger.exception("ResultsWidget.load_results failed; falling back to message box.")

        QMessageBox.information(
            self,
            "Quiz Complete",
            f"You answered {len(results.get('answers', []))} questions!",
        )
        self.show_categories()

    def on_retake_quiz(self, category_id: int, category_name: str) -> None:
        """Handle quiz retake."""
        self.quiz_page.load_quiz(category_id, category_name)
        self.stack.setCurrentWidget(self.quiz_page)

    def logout(self) -> None:
        """Log out."""
        self.current_user = None
        self.stack.setCurrentWidget(self.login_page)
        logger.info("User logged out.")

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Handle window close."""
        db.disconnect()
        event.accept()


def main() -> int:
    """Application entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = QApplication(sys.argv)
    window = QuizApp()

    if not window.test_database_connection():
        return 1

    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
