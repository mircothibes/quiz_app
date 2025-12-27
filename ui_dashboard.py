from __future__ import annotations

import logging
from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from db import db

logger = logging.getLogger(__name__)


class DashboardWidget(QWidget):
    """Main dashboard with navigation buttons and user quiz stats.

    Features:
    - Welcome header
    - Navigation actions (categories, admin, logout)
    - User stats (total attempts, best score, last score)
    - Recent attempts table
    """

    browse_categories_clicked = pyqtSignal()
    manage_questions_clicked = pyqtSignal()
    logout_clicked = pyqtSignal()

    def __init__(self, username: str, user_id: int) -> None:
        super().__init__()
        self.username = username
        self.user_id = user_id

        self._stats_total_label: Optional[QLabel] = None
        self._stats_best_label: Optional[QLabel] = None
        self._stats_last_label: Optional[QLabel] = None
        self._attempts_table: Optional[QTableWidget] = None
        self._attempts_info_label: Optional[QLabel] = None

        self.init_ui()
        self.refresh()

    # ---------------------------------------------------------------------
    # UI setup
    # ---------------------------------------------------------------------
    def init_ui(self) -> None:
        """Initialize the dashboard interface."""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addWidget(self._create_header())
        main_layout.addWidget(self._create_navigation())
        main_layout.addWidget(self._create_stats_section())
        main_layout.addWidget(self._create_recent_attempts_section())

        main_layout.addStretch()

    def _create_header(self) -> QFrame:
        """Create header with welcome message."""
        header_frame = QFrame()
        header_frame.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9
                );
                border-radius: 10px;
                padding: 20px;
                margin: 20px;
            }
            """
        )

        layout = QVBoxLayout()
        header_frame.setLayout(layout)

        welcome_label = QLabel(f"👋 Welcome back, {self.username}!")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet(
            """
            font-size: 28px;
            font-weight: bold;
            color: white;
            """
        )
        layout.addWidget(welcome_label)

        subtitle = QLabel("What would you like to do today?")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            """
            font-size: 14px;
            color: #ecf0f1;
            margin-top: 5px;
            """
        )
        layout.addWidget(subtitle)

        return header_frame

    def _create_navigation(self) -> QWidget:
        """Create navigation button grid."""
        nav_widget = QWidget()
        layout = QVBoxLayout()
        nav_widget.setLayout(layout)

        title = QLabel("📍 Navigation")
        title.setStyleSheet(
            """
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            margin: 20px 20px 10px 20px;
            """
        )
        layout.addWidget(title)

        button_layout = QVBoxLayout()
        button_layout.setSpacing(15)

        browse_btn = self._create_nav_button(
            "📚 Browse Quiz Categories",
            "Explore available quiz topics and start a quiz",
            "#27ae60",
        )
        browse_btn.clicked.connect(self.browse_categories_clicked.emit)
        button_layout.addWidget(browse_btn)

        manage_btn = self._create_nav_button(
            "➕ Manage Questions",
            "Add, edit, or delete quiz questions (Admin)",
            "#f39c12",
        )
        manage_btn.clicked.connect(self.manage_questions_clicked.emit)
        button_layout.addWidget(manage_btn)

        logout_btn = self._create_nav_button(
            "🚪 Logout",
            "Sign out of your account",
            "#e74c3c",
        )
        logout_btn.clicked.connect(self.logout_clicked.emit)
        button_layout.addWidget(logout_btn)

        button_container = QWidget()
        button_container.setLayout(button_layout)
        button_container.setStyleSheet("margin: 0px 40px;")
        layout.addWidget(button_container)

        return nav_widget

    def _create_stats_section(self) -> QWidget:
        """Create the stats section (total attempts, best score, last score)."""
        container = QWidget()
        outer = QVBoxLayout()
        container.setLayout(outer)

        title = QLabel("📊 Your Stats")
        title.setStyleSheet(
            """
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            margin: 20px 20px 10px 20px;
            """
        )
        outer.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(15)

        card_total, self._stats_total_label = self._create_stat_card("Total Attempts", "0")
        card_best, self._stats_best_label = self._create_stat_card("Best Score", "0%")
        card_last, self._stats_last_label = self._create_stat_card("Last Score", "0%")

        grid.addWidget(card_total, 0, 0)
        grid.addWidget(card_best, 0, 1)
        grid.addWidget(card_last, 0, 2)

        wrapper = QWidget()
        wrapper.setLayout(grid)
        wrapper.setStyleSheet("margin: 0px 40px;")
        outer.addWidget(wrapper)

        return container

    def _create_recent_attempts_section(self) -> QWidget:
        """Create a table for recent attempts."""
        container = QWidget()
        outer = QVBoxLayout()
        container.setLayout(outer)

        title = QLabel("🕒 Recent Attempts")
        title.setStyleSheet(
            """
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            margin: 20px 20px 10px 20px;
            """
        )
        outer.addWidget(title)

        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["Date", "Category", "Score"])
        table.setStyleSheet(
            """
            QTableWidget {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
                margin: 0px 40px;
            }
            QHeaderView::section {
                background-color: #ecf0f1;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            """
        )
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)

        self._attempts_table = table
        outer.addWidget(table)

        info = QLabel("")
        info.setStyleSheet("color: #7f8c8d; font-size: 12px; margin: 8px 40px;")
        self._attempts_info_label = info
        outer.addWidget(info)

        return container

    # ---------------------------------------------------------------------
    # Data refresh
    # ---------------------------------------------------------------------
    def refresh(self) -> None:
        """Refresh stats and recent attempts from the database."""
        if self.user_id <= 0:
            logger.warning("Dashboard refresh skipped: invalid user_id=%s", self.user_id)
            return

        try:
            total_attempts, best_percent, last_percent = db.get_attempt_stats(self.user_id)
            recent = db.get_recent_attempts(self.user_id, limit=5)

            if self._stats_total_label is not None:
                self._stats_total_label.setText(str(total_attempts))
            if self._stats_best_label is not None:
                self._stats_best_label.setText(f"{best_percent}%")
            if self._stats_last_label is not None:
                self._stats_last_label.setText(f"{last_percent}%")

            self._populate_recent_attempts(recent)

        except Exception as exc:
            logger.exception("Dashboard refresh failed: %s", exc)
            if self._attempts_info_label is not None:
                self._attempts_info_label.setText("⚠️ Could not load stats from database.")

    def _populate_recent_attempts(self, rows: list[tuple[str, str, int, int]]) -> None:
        """Fill recent attempts table.

        Args:
            rows: list of (created_at_str, category_name, correct_count, total_questions)
        """
        if self._attempts_table is None:
            return

        self._attempts_table.setRowCount(0)

        if not rows:
            if self._attempts_info_label is not None:
                self._attempts_info_label.setText("No attempts yet. Start a quiz to see your history here.")
            return

        for created_at, category_name, correct_count, total_questions in rows:
            row_idx = self._attempts_table.rowCount()
            self._attempts_table.insertRow(row_idx)

            score_text = f"{correct_count}/{total_questions}"

            self._attempts_table.setItem(row_idx, 0, QTableWidgetItem(created_at))
            self._attempts_table.setItem(row_idx, 1, QTableWidgetItem(category_name))
            self._attempts_table.setItem(row_idx, 2, QTableWidgetItem(score_text))

        if self._attempts_info_label is not None:
            self._attempts_info_label.setText(f"Showing last {len(rows)} attempt(s).")

        self._attempts_table.resizeColumnsToContents()

    # ---------------------------------------------------------------------
    # Components
    # ---------------------------------------------------------------------
    def _create_stat_card(self, title: str, value: str) -> tuple[QFrame, QLabel]:
        """Create a small stat card component.

        Returns:
            (frame, value_label)
        """
        frame = QFrame()
        frame.setStyleSheet(
            """
            QFrame {
                background-color: white;
                border: 2px solid #ecf0f1;
                border-radius: 10px;
                padding: 12px;
            }
            """
        )

        layout = QVBoxLayout()
        frame.setLayout(layout)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #7f8c8d; font-size: 12px; font-weight: bold;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet("color: #2c3e50; font-size: 24px; font-weight: bold;")
        layout.addWidget(value_label)

        layout.setAlignment(Qt.AlignTop)
        return frame, value_label

    def _create_nav_button(self, title: str, description: str, color: str) -> QPushButton:
        """Create a styled navigation button."""
        btn = QPushButton(f"{title}\n{description}")
        btn.setStyleSheet(
            f"""
            QPushButton {{
                text-align: left;
                padding: 20px;
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(color, 0.8)};
            }}
            """
        )
        btn.setCursor(Qt.PointingHandCursor)
        return btn

    @staticmethod
    def _darken_color(hex_color: str, factor: float = 0.9) -> str:
        """Darken a hex color by a factor."""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"
