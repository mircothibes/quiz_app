import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from db import db

logger = logging.getLogger(__name__)


class LoginWidget(QWidget):
    """Login form widget."""

    # Emits a user payload (dict/tuple) on success
    login_successful = pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addStretch()

        title = QLabel("🔐 Login")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            """
            font-size: 32px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            """
        )
        layout.addWidget(title)

        subtitle = QLabel("Please enter your credentials")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            """
            font-size: 14px;
            color: #7f8c8d;
            margin-bottom: 30px;
            """
        )
        layout.addWidget(subtitle)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setStyleSheet(
            """
            font-size: 16px;
            padding: 12px;
            border: 2px solid #bdc3c7;
            border-radius: 5px;
            margin: 10px 100px;
            """
        )
        self.username_input.returnPressed.connect(self.handle_login)
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(
            """
            font-size: 16px;
            padding: 12px;
            border: 2px solid #bdc3c7;
            border-radius: 5px;
            margin: 10px 100px;
            """
        )
        self.password_input.returnPressed.connect(self.handle_login)
        layout.addWidget(self.password_input)

        self.login_btn = QPushButton("Login")
        self.login_btn.setStyleSheet(
            """
            font-size: 16px;
            padding: 12px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            margin: 20px 100px;
            font-weight: bold;
            """
        )
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)

        # Optional: keep this for learning/demo, but you may remove it later for a portfolio polish.
        info = QLabel("💡 Hint: Try username 'demo' with password 'test123'")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet(
            """
            font-size: 12px;
            color: #95a5a6;
            margin-top: 20px;
            """
        )
        layout.addWidget(info)

        layout.addStretch()

        self.username_input.setFocus()

    def _set_loading(self, is_loading: bool) -> None:
        self.login_btn.setDisabled(is_loading)
        self.username_input.setDisabled(is_loading)
        self.password_input.setDisabled(is_loading)

    def handle_login(self) -> None:
        """Handle login button click."""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(
                self,
                "Input Error",
                "Please enter both username and password.",
            )
            return

        self._set_loading(True)
        try:
            # Ensure DB connection exists (important for a smooth UX)
            if not db.is_connected():
                if not db.connect():
                    QMessageBox.critical(
                        self,
                        "Database Error",
                        "Could not connect to PostgreSQL.\n\nEnsure Docker is running and the database is available.",
                    )
                    return

            user = db.authenticate_user(username, password)

            if user:
                logger.info("Login successful for username=%s", username)
                self.login_successful.emit(user)
                # Optional cleanup after success
                self.password_input.clear()
                return

            QMessageBox.critical(
                self,
                "Login Failed",
                "Invalid username or password.\n\nPlease try again.",
            )
            self.password_input.clear()
            self.password_input.setFocus()

        except Exception as exc:
            logger.exception("Unexpected login error: %s", exc)
            QMessageBox.critical(
                self,
                "Unexpected Error",
                "An unexpected error occurred during login.\n\nPlease try again.",
            )
        finally:
            self._set_loading(False)
