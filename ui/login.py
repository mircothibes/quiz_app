from __future__ import annotations

import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from db import db

logger = logging.getLogger(__name__)


class RegisterDialog(QDialog):
    """Dialog to create a new user account."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Account")
        self.setModal(True)
        self.setMinimumWidth(380)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Choose a username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Choose a password")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Confirm password")
        self.confirm_input.setEchoMode(QLineEdit.Password)

        form = QFormLayout()
        form.addRow("Username:", self.username_input)
        form.addRow("Password:", self.password_input)
        form.addRow("Confirm:", self.confirm_input)

        self.create_btn = QPushButton("Create")
        self.cancel_btn = QPushButton("Cancel")

        self.create_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
            """
        )
        self.cancel_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #7f8c8d; }
            """
        )

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.create_btn)

        root = QVBoxLayout(self)
        title = QLabel("🆕 Create a new account")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin: 8px 0;")
        root.addWidget(title)
        root.addLayout(form)
        root.addSpacing(8)
        root.addLayout(btn_row)

        self.cancel_btn.clicked.connect(self.reject)
        self.create_btn.clicked.connect(self._on_create_clicked)

    def _on_create_clicked(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        if len(username) < 3:
            QMessageBox.warning(self, "Invalid Username", "Username must be at least 3 characters.")
            return

        if len(password) < 4:
            QMessageBox.warning(self, "Invalid Password", "Password must be at least 4 characters.")
            return

        if password != confirm:
            QMessageBox.warning(self, "Password Mismatch", "Passwords do not match.")
            return

        self.accept()

    def get_values(self) -> tuple[str, str]:
        return self.username_input.text().strip(), self.password_input.text()


class LoginWidget(QWidget):
    """Login page with Create Account option."""

    login_successful = pyqtSignal(str, int)  # (username, user_id)
    login_success = pyqtSignal(str, int)     # alias for compatibility

    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(60, 40, 60, 40)
        root.setSpacing(14)

        title = QLabel("🔐 Advanced Quiz App")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #2c3e50;")
        root.addWidget(title)

        subtitle = QLabel("Login to continue")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #7f8c8d; margin-bottom: 6px;")
        root.addWidget(subtitle)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(40)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)

        self.username_input.setStyleSheet(self._input_style())
        self.password_input.setStyleSheet(self._input_style())

        root.addWidget(self.username_input)
        root.addWidget(self.password_input)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        root.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.login_btn = QPushButton("Login")
        self.create_btn = QPushButton("Create Account")

        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.create_btn.setCursor(Qt.PointingHandCursor)

        self.login_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 18px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
            """
        )
        self.create_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 18px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #27ae60; }
            """
        )

        btn_row.addWidget(self.login_btn)
        btn_row.addWidget(self.create_btn)
        root.addLayout(btn_row)

        root.addStretch(1)

        self.login_btn.clicked.connect(self._on_login_clicked)
        self.create_btn.clicked.connect(self._on_create_account_clicked)
        self.password_input.returnPressed.connect(self._on_login_clicked)

    @staticmethod
    def _input_style() -> str:
        return """
        QLineEdit {
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            padding: 10px;
            font-size: 14px;
            background-color: white;
        }
        QLineEdit:focus {
            border: 2px solid #3498db;
        }
        """

    def _ensure_db(self) -> bool:
        if db.is_connected():
            return True

        if db.connect():
            return True

        QMessageBox.critical(
            self,
            "Database Error",
            "Could not connect to PostgreSQL.\n\nEnsure Docker is running and the database is available.",
        )
        return False

    def _on_login_clicked(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Missing Fields", "Please enter username and password.")
            return

        if not self._ensure_db():
            return

        self.status_label.setText("Checking credentials...")
        self.status_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")

        result = db.authenticate_user(username, password)
        if not result:
            self.status_label.setText("❌ Invalid username or password.")
            self.status_label.setStyleSheet("font-size: 12px; color: #e74c3c;")
            return

        user_id, user_name = result[0], result[1]
        self.status_label.setText("✅ Login successful.")
        self.status_label.setStyleSheet("font-size: 12px; color: #27ae60;")

        logger.info("Login successful for username=%s", user_name)

        self.login_successful.emit(user_name, user_id)
        self.login_success.emit(user_name, user_id)

    def _on_create_account_clicked(self) -> None:
        if not self._ensure_db():
            return

        dlg = RegisterDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return

        username, password = dlg.get_values()

        created_id = db.create_user(username, password)
        if created_id is None:
            QMessageBox.warning(
                self,
                "Create Account Failed",
                "Could not create the account.\n\nIf the username already exists, try another one.",
            )
            return

        QMessageBox.information(self, "Account Created", "✅ Account created successfully! You are now logged in.")

        self.username_input.setText(username)
        self.password_input.setText("")
        self.status_label.setText("✅ Account created and logged in.")
        self.status_label.setStyleSheet("font-size: 12px; color: #27ae60;")

        self.login_successful.emit(username, created_id)
        self.login_success.emit(username, created_id)
