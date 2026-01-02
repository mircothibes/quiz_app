from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from db import db

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _UiConstants:
    """Central place for UI constants used in the login screen."""

    # Layout
    MARGIN_LEFT: int = 60
    MARGIN_TOP: int = 30
    MARGIN_RIGHT: int = 60
    MARGIN_BOTTOM: int = 30
    SPACING: int = 12

    # Logo
    LOGO_FILENAME: str = "quiz_app.png"
    LOGO_TARGET_HEIGHT: int = 720  # adjust freely (e.g., 520, 600, 720)

    # Validation
    MIN_USERNAME_LEN: int = 3
    MIN_PASSWORD_LEN: int = 4


C = _UiConstants()


def _trim_transparent_borders(img: QImage) -> QImage:
    """Crop fully-transparent borders from an image (PNG with alpha).

    This fixes a common issue where a logo PNG has a large transparent canvas.
    Without trimming, scaling the pixmap to a height (e.g., 720px) makes the
    *transparent area* huge, pushing the rest of the UI down.

    Args:
        img: Source image (ideally with alpha channel).

    Returns:
        Cropped QImage. If the image has no alpha channel or cropping fails,
        returns the original image.
    """
    if img.isNull() or not img.hasAlphaChannel():
        return img

    w, h = img.width(), img.height()
    left, right = w, -1
    top, bottom = h, -1

    for y in range(h):
        for x in range(w):
            if img.pixelColor(x, y).alpha() > 0:
                if x < left:
                    left = x
                if x > right:
                    right = x
                if y < top:
                    top = y
                if y > bottom:
                    bottom = y

    if right >= left and bottom >= top:
        return img.copy(QRect(left, top, right - left + 1, bottom - top + 1))

    return img


class RegisterDialog(QDialog):
    """Dialog window to capture user credentials for account creation.

    This dialog performs only UI validation (length checks, password match).
    The actual DB insert is done by LoginWidget after the dialog is accepted.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
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

        self._build_ui()
        self._wire_signals()

    def _build_ui(self) -> None:
        """Build dialog widgets and layout."""
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
        title.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #2c3e50; margin: 8px 0;"
        )

        root.addWidget(title)
        root.addLayout(form)
        root.addSpacing(8)
        root.addLayout(btn_row)

    def _wire_signals(self) -> None:
        """Connect dialog events to handlers."""
        self.cancel_btn.clicked.connect(self.reject)
        self.create_btn.clicked.connect(self._on_create_clicked)

        # Enter key behavior
        self.confirm_input.returnPressed.connect(self._on_create_clicked)

    def _on_create_clicked(self) -> None:
        """Validate inputs and accept dialog if valid."""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        if len(username) < C.MIN_USERNAME_LEN:
            QMessageBox.warning(
                self,
                "Invalid Username",
                f"Username must be at least {C.MIN_USERNAME_LEN} characters.",
            )
            return

        if len(password) < C.MIN_PASSWORD_LEN:
            QMessageBox.warning(
                self,
                "Invalid Password",
                f"Password must be at least {C.MIN_PASSWORD_LEN} characters.",
            )
            return

        if password != confirm:
            QMessageBox.warning(self, "Password Mismatch", "Passwords do not match.")
            return

        self.accept()

    def get_values(self) -> Tuple[str, str]:
        """Return (username, password) typed in the dialog."""
        return self.username_input.text().strip(), self.password_input.text()


class LoginWidget(QWidget):
    """Login page with Create Account option.

    Signals:
        login_successful(username, user_id): emitted after a successful login/registration.
        login_success(username, user_id): alias for compatibility.
    """

    login_successful = pyqtSignal(str, int)  # (username, user_id)
    login_success = pyqtSignal(str, int)     # alias for compatibility

    def __init__(self) -> None:
        super().__init__()
        self._build_ui()
        self._wire_signals()

    # ------------------------------------------------------------------
    # UI building
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        """Build the full login UI layout."""
        root = QVBoxLayout(self)
        root.setContentsMargins(C.MARGIN_LEFT, C.MARGIN_TOP, C.MARGIN_RIGHT, C.MARGIN_BOTTOM)
        root.setSpacing(C.SPACING)
        root.setAlignment(Qt.AlignTop)

        self._add_logo(root)
        self._add_title(root)
        self._add_inputs(root)
        self._add_status(root)
        self._add_buttons(root)

        # NOTE:
        # Do NOT add root.addStretch(1) here.
        # Stretch can push content away depending on widget size policies.

    def _add_logo(self, root: QVBoxLayout) -> None:
        """Add the logo label at the top (with transparency trimming)."""
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        logo_path = Path(__file__).resolve().parents[1] / "assets" / C.LOGO_FILENAME

        img = QImage(str(logo_path))
        if img.isNull():
            logger.warning("Logo not found or invalid image: %s", logo_path)
            return

        img = _trim_transparent_borders(img)
        pixmap = QPixmap.fromImage(img)

        scaled = pixmap.scaledToHeight(C.LOGO_TARGET_HEIGHT, Qt.SmoothTransformation)
        self.logo_label.setPixmap(scaled)

        # Important: avoid label expanding vertically and creating huge empty space.
        self.logo_label.setFixedHeight(scaled.height())

        root.addWidget(self.logo_label)

    def _add_title(self, root: QVBoxLayout) -> None:
        """Add title + subtitle labels."""
        title = QLabel("🔐 Advanced Quiz App")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #2c3e50;")
        root.addWidget(title)

        subtitle = QLabel("Login to continue")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #7f8c8d; margin-bottom: 6px;")
        root.addWidget(subtitle)

    def _add_inputs(self, root: QVBoxLayout) -> None:
        """Add username + password inputs."""
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(40)
        self.username_input.setStyleSheet(self._input_style())
        root.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        self.password_input.setStyleSheet(self._input_style())
        root.addWidget(self.password_input)

    def _add_status(self, root: QVBoxLayout) -> None:
        """Add a label for success/error hints."""
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        root.addWidget(self.status_label)

    def _add_buttons(self, root: QVBoxLayout) -> None:
        """Add Login + Create Account buttons."""
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

    def _wire_signals(self) -> None:
        """Connect widget events to handlers."""
        self.login_btn.clicked.connect(self._on_login_clicked)
        self.create_btn.clicked.connect(self._on_create_account_clicked)
        self.password_input.returnPressed.connect(self._on_login_clicked)

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------
    @staticmethod
    def _input_style() -> str:
        """Return stylesheet for text inputs."""
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

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------
    def _ensure_db(self) -> bool:
        """Ensure the database is connected, showing a friendly error if not."""
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

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _on_login_clicked(self) -> None:
        """Validate user input, authenticate, and emit login signals on success."""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Missing Fields", "Please enter username and password.")
            return

        if not self._ensure_db():
            return

        self._set_status("Checking credentials...", "#7f8c8d")

        result = db.authenticate_user(username, password)
        if not result:
            self._set_status("❌ Invalid username or password.", "#e74c3c")
            return

        user_id, user_name = int(result[0]), str(result[1])

        self._set_status("✅ Login successful.", "#27ae60")
        logger.info("Login successful for username=%s", user_name)

        self.login_successful.emit(user_name, user_id)
        self.login_success.emit(user_name, user_id)

    def _on_create_account_clicked(self) -> None:
        """Open registration dialog, create user, and log in automatically."""
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
        self._set_status("✅ Account created and logged in.", "#27ae60")

        self.login_successful.emit(username, int(created_id))
        self.login_success.emit(username, int(created_id))

    def _set_status(self, text: str, color_hex: str) -> None:
        """Update status label text and color."""
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"font-size: 12px; color: {color_hex};")

