from __future__ import annotations

import logging
from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from db import db

logger = logging.getLogger(__name__)


class DashboardWidget(QWidget):
    """Dashboard screen with navigation and user quiz statistics.

    Layout goals:
    - Center content on large screens (avoid "too wide" UI).
    - Keep a scroll fallback for small screens.
    - Make the stats cards responsive: 1/2/3 columns depending on window width.
    """

    browse_categories_clicked = pyqtSignal()
    manage_questions_clicked = pyqtSignal()
    logout_clicked = pyqtSignal()

    def __init__(self, username: str, user_id: int) -> None:
        super().__init__()
        self.username = username
        self.user_id = user_id

        # Stats UI references
        self._stats_total_label: Optional[QLabel] = None
        self._stats_best_label: Optional[QLabel] = None
        self._stats_last_label: Optional[QLabel] = None

        self._attempts_table: Optional[QTableWidget] = None
        self._attempts_info_label: Optional[QLabel] = None

        # Responsive stats cards
        self._stats_cards: list[QFrame] = []
        self._stats_grid: Optional[QGridLayout] = None
        self._stats_columns: int = 3  # current applied columns

        self._build_ui()
        self.refresh()

    # ---------------------------------------------------------------------
    # UI setup
    # ---------------------------------------------------------------------
    def _build_ui(self) -> None:
        """Build the dashboard UI with a centered, scrollable layout."""
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        # Wrapper centers the content
        wrapper = QWidget()
        wrapper_layout = QHBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)

        wrapper_layout.addStretch(1)

        content = QWidget()
        content.setMaximumWidth(1100)  # key: prevents "too wide" on large screens
        content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(18)
        content_layout.setAlignment(Qt.AlignTop)

        content_layout.addWidget(self._create_header())
        content_layout.addWidget(self._create_navigation())
        content_layout.addWidget(self._create_stats_section())
        content_layout.addWidget(self._create_recent_attempts_section())
        content_layout.addStretch(1)

        wrapper_layout.addWidget(content, 0)
        wrapper_layout.addStretch(1)

        scroll.setWidget(wrapper)
        root_layout.addWidget(scroll)

        # Apply initial responsive layout
        self._update_responsive_layout()

    def _create_header(self) -> QFrame:
        """Create the top header with welcome message."""
        header = QFrame()
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header.setMinimumHeight(150)

        header.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9
                );
                border-radius: 12px;
            }
            """
        )

        layout = QVBoxLayout(header)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(6)

        welcome = QLabel(f"👋 Welcome back, {self.username}!")
        welcome.setAlignment(Qt.AlignCenter)
        welcome.setWordWrap(True)
        welcome.setStyleSheet("font-size: 28px; font-weight: bold; color: white;")
        layout.addWidget(welcome)

        subtitle = QLabel("What would you like to do today?")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 14px; color: #ecf0f1;")
        layout.addWidget(subtitle)

        return header

    def _create_navigation(self) -> QWidget:
        """Create the navigation section (categories/admin/logout)."""
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        title = QLabel("📍 Navigation")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        outer.addWidget(title)

        browse_btn = self._create_nav_button(
            "📚 Browse Quiz Categories",
            "Explore available quiz topics and start a quiz",
            "#27ae60",
        )
        browse_btn.clicked.connect(self.browse_categories_clicked.emit)
        outer.addWidget(browse_btn)

        manage_btn = self._create_nav_button(
            "➕ Manage Questions",
            "Add, edit, or delete quiz questions (Admin)",
            "#f39c12",
        )
        manage_btn.clicked.connect(self.manage_questions_clicked.emit)
        outer.addWidget(manage_btn)

        logout_btn = self._create_nav_button(
            "🚪 Logout",
            "Sign out of your account",
            "#e74c3c",
        )
        logout_btn.clicked.connect(self.logout_clicked.emit)
        outer.addWidget(logout_btn)

        return container

    def _create_stats_section(self) -> QWidget:
        """Create the stats cards section (responsive columns)."""
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        title = QLabel("📊 Your Stats")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        outer.addWidget(title)

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        self._stats_grid = grid

        card_total, self._stats_total_label = self._create_stat_card("Total Attempts", "0")
        card_best, self._stats_best_label = self._create_stat_card("Best Score", "0%")
        card_last, self._stats_last_label = self._create_stat_card("Last Score", "0%")

        self._stats_cards = [card_total, card_best, card_last]
        outer.addWidget(grid_host)

        # initial flow
        self._reflow_stats_cards(columns=3)

        return container

    def _create_recent_attempts_section(self) -> QWidget:
        """Create a recent attempts table section."""
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        title = QLabel("🕒 Recent Attempts")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        outer.addWidget(title)

        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["Date", "Category", "Score"])
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.verticalHeader().setVisible(False)

        table.setStyleSheet(
            """
            QTableWidget {
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #ecf0f1;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            """
        )

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setDefaultAlignment(Qt.AlignLeft)

        self._attempts_table = table
        outer.addWidget(table)

        info = QLabel("")
        info.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        self._attempts_info_label = info
        outer.addWidget(info)

        return container

    # ---------------------------------------------------------------------
    # Responsive behavior
    # ---------------------------------------------------------------------
    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """Update responsive sections when the window size changes."""
        super().resizeEvent(event)
        self._update_responsive_layout()

    def _update_responsive_layout(self) -> None:
        """Adjust layouts based on available width."""
        width = self.width()

        if width < 720:
            cols = 1
        elif width < 980:
            cols = 2
        else:
            cols = 3

        if cols != self._stats_columns:
            self._reflow_stats_cards(columns=cols)
            self._stats_columns = cols

    def _reflow_stats_cards(self, columns: int) -> None:
        """Reposition stat cards in the grid using the given column count."""
        if self._stats_grid is None:
            return

        # Clear existing items
        while self._stats_grid.count():
            item = self._stats_grid.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)

        for idx, card in enumerate(self._stats_cards):
            row = idx // columns
            col = idx % columns
            self._stats_grid.addWidget(card, row, col)

        # Improve stretching behavior
        for c in range(columns):
            self._stats_grid.setColumnStretch(c, 1)

    # ---------------------------------------------------------------------
    # Data refresh
    # ---------------------------------------------------------------------
    def refresh(self) -> None:
        """Refresh stats and recent attempts from the database."""
        if self.user_id <= 0:
            logger.warning("Dashboard refresh skipped: invalid user_id=%s", self.user_id)
            return

        total_attempts, best_percent, last_percent = db.get_attempt_stats(self.user_id)
        recent = db.get_recent_attempts(self.user_id, limit=5)

        if self._stats_total_label is not None:
            self._stats_total_label.setText(str(total_attempts))
        if self._stats_best_label is not None:
            self._stats_best_label.setText(f"{best_percent}%")
        if self._stats_last_label is not None:
            self._stats_last_label.setText(f"{last_percent}%")

        self._populate_recent_attempts(recent)

    def _populate_recent_attempts(self, rows: list[tuple[str, str, int, int]]) -> None:
        """Fill recent attempts table.

        Args:
            rows: (created_at_str, category_name, correct_count, total_questions)
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

        self._attempts_table.resizeRowsToContents()

    # ---------------------------------------------------------------------
    # Components
    # ---------------------------------------------------------------------
    def _create_stat_card(self, title: str, value: str) -> tuple[QFrame, QLabel]:
        """Create a stat card widget."""
        frame = QFrame()
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        frame.setMinimumHeight(110)

        frame.setStyleSheet(
            """
            QFrame {
                background-color: white;
                border: 2px solid #ecf0f1;
                border-radius: 12px;
                padding: 12px;
            }
            """
        )

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #7f8c8d; font-size: 12px; font-weight: bold;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet("color: #2c3e50; font-size: 24px; font-weight: bold;")
        layout.addWidget(value_label)

        return frame, value_label

    def _create_nav_button(self, title: str, description: str, color: str) -> QPushButton:
        """Create a styled navigation button with safe sizing."""
        btn = QPushButton(f"{title}\n{description}")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setMinimumHeight(76)

        btn.setStyleSheet(
            f"""
            QPushButton {{
                text-align: left;
                padding: 18px;
                background-color: {color};
                color: white;
                border: none;
                border-radius: 12px;
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
        return btn

    @staticmethod
    def _darken_color(hex_color: str, factor: float = 0.9) -> str:
        """Return a darker version of a hex color."""
        color = hex_color.lstrip("#")
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)

        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"
