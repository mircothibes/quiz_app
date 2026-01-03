from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from db import db

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _Ui:
    """UI constants for the dashboard layout and styling."""

    CONTENT_MAX_WIDTH: int = 1100

    # Content padding
    PAD: int = 24
    SPACING: int = 18

    # Header
    HEADER_MIN_HEIGHT: int = 110

    # Stats responsiveness
    COLS_1_MAX: int = 720
    COLS_2_MAX: int = 980

    # Recent list
    RECENT_LIMIT: int = 5


C = _Ui()


class DashboardWidget(QWidget):
    """Dashboard screen that shows quick actions, user stats, and recent activity.

    Goals:
        - Make the first action obvious (Start Quiz).
        - Keep Logout accessible but not dominant.
        - Keep content centered on large screens with scroll fallback.
        - Keep stats cards responsive: 1/2/3 columns based on window width.
    """

    browse_categories_clicked = pyqtSignal()
    manage_questions_clicked = pyqtSignal()
    logout_clicked = pyqtSignal()

    def __init__(self, username: str, user_id: int) -> None:
        super().__init__()
        self.username = username
        self.user_id = user_id

        # Stats UI references
        self._stats_total_value: Optional[QLabel] = None
        self._stats_best_value: Optional[QLabel] = None
        self._stats_last_value: Optional[QLabel] = None

        self._stats_total_sub: Optional[QLabel] = None
        self._stats_best_sub: Optional[QLabel] = None
        self._stats_last_sub: Optional[QLabel] = None

        # Recent activity UI references
        self._recent_list_host: Optional[QWidget] = None
        self._recent_list_layout: Optional[QVBoxLayout] = None
        self._recent_info_label: Optional[QLabel] = None

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
        content.setMaximumWidth(C.CONTENT_MAX_WIDTH)
        content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(C.PAD, C.PAD, C.PAD, C.PAD)
        content_layout.setSpacing(C.SPACING)
        content_layout.setAlignment(Qt.AlignTop)

        content_layout.addWidget(self._create_header())
        content_layout.addWidget(self._create_quick_actions())
        content_layout.addWidget(self._create_stats_section())
        content_layout.addWidget(self._create_recent_activity_section())
        content_layout.addStretch(1)

        wrapper_layout.addWidget(content, 0)
        wrapper_layout.addStretch(1)

        scroll.setWidget(wrapper)
        root_layout.addWidget(scroll)

        self._update_responsive_layout()

    # ---------------------------------------------------------------------
    # Header + Quick actions
    # ---------------------------------------------------------------------
    def _create_header(self) -> QFrame:
        """Create the top header with a compact welcome and a small Logout button."""
        header = QFrame()
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header.setMinimumHeight(C.HEADER_MIN_HEIGHT)
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
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        title = QLabel(f"👋 Welcome back, {self.username}")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: white;")
        title.setWordWrap(True)

        logout_btn = QPushButton("🚪 Logout")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setFixedHeight(34)
        logout_btn.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.18);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.22);
                border-radius: 10px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.28); }
            QPushButton:pressed { background-color: rgba(255, 255, 255, 0.22); }
            """
        )
        logout_btn.clicked.connect(self.logout_clicked.emit)

        top_row.addWidget(title, 1)
        top_row.addWidget(logout_btn, 0, Qt.AlignRight)

        subtitle = QLabel("Ready for your next quiz?")
        subtitle.setStyleSheet("font-size: 13px; color: rgba(236, 240, 241, 0.95);")
        subtitle.setWordWrap(True)

        layout.addLayout(top_row)
        layout.addWidget(subtitle)

        return header

    def _create_quick_actions(self) -> QWidget:
        """Create the main action area (the most important actions first)."""
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        title = QLabel("⚡ Quick Actions")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #2c3e50;")
        outer.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(12)

        start_btn = self._create_action_button(
            title="▶ Start Quiz",
            subtitle="Pick a category and begin",
            color="#27ae60",
            is_primary=True,
        )
        start_btn.clicked.connect(self.browse_categories_clicked.emit)

        admin_btn = self._create_action_button(
            title="⚙ Manage Questions",
            subtitle="Add, edit, or delete questions",
            color="#f39c12",
            is_primary=False,
            badge_text="Admin",
        )
        admin_btn.clicked.connect(self.manage_questions_clicked.emit)

        row.addWidget(start_btn)
        row.addWidget(admin_btn)

        outer.addLayout(row)
        return container

    def _create_action_button(
        self,
        title: str,
        subtitle: str,
        color: str,
        is_primary: bool,
        badge_text: Optional[str] = None,
    ) -> QPushButton:
        """Create a large, friendly action button with optional badge."""
        badge = f"   [{badge_text}]" if badge_text else ""
        weight = "800" if is_primary else "700"
        btn = QPushButton(f"{title}{badge}\n{subtitle}")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setMinimumHeight(74)

        btn.setStyleSheet(
            f"""
            QPushButton {{
                text-align: left;
                padding: 16px;
                background-color: {color};
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: {weight};
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

    # ---------------------------------------------------------------------
    # Stats
    # ---------------------------------------------------------------------
    def _create_stats_section(self) -> QWidget:
        """Create the stats cards section (responsive columns + helpful subtext)."""
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        title = QLabel("📊 Your Stats")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #2c3e50;")
        outer.addWidget(title)

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        self._stats_grid = grid

        card_total, self._stats_total_value, self._stats_total_sub = self._create_stat_card(
            title="Total Attempts",
            value="0",
            subtext="—",
            bg_color="#3498db",
        )
        card_best, self._stats_best_value, self._stats_best_sub = self._create_stat_card(
            title="Best Score",
            value="0%",
            subtext="Personal best",
            bg_color="#27ae60",
        )
        card_last, self._stats_last_value, self._stats_last_sub = self._create_stat_card(
            title="Last Score",
            value="0%",
            subtext="Most recent attempt",
            bg_color="#f39c12",
        )

        self._stats_cards = [card_total, card_best, card_last]
        outer.addWidget(grid_host)

        self._reflow_stats_cards(columns=3)
        return container

    def _create_stat_card(
        self,
        title: str,
        value: str,
        subtext: str,
        bg_color: str,
    ) -> tuple[QFrame, QLabel, QLabel]:
        """Create a stat card with colored background and a small helper line.

        Args:
            title: Card title (e.g. "Total Attempts").
            value: Main value string (e.g. "13", "100%").
            subtext: Secondary hint (e.g. "Last 7 days: 3").
            bg_color: Background hex color.

        Returns:
            (frame, value_label, sub_label)
        """
        frame = QFrame()
        frame.setObjectName("statCard")
        frame.setStyleSheet(
            f"""
            QFrame#statCard {{
                background-color: {bg_color};
                border: none;
                border-radius: 12px;
                padding: 16px;
            }}
            """
        )
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        frame.setMinimumHeight(118)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            """
            QLabel {
                background: transparent;
                color: rgba(255, 255, 255, 0.92);
                font-size: 12px;
                font-weight: 700;
            }
            """
        )

        value_label = QLabel(value)
        value_label.setStyleSheet(
            """
            QLabel {
                background: transparent;
                color: white;
                font-size: 30px;
                font-weight: 900;
            }
            """
        )

        sub_label = QLabel(subtext)
        sub_label.setStyleSheet(
            """
            QLabel {
                background: transparent;
                color: rgba(255, 255, 255, 0.85);
                font-size: 12px;
                font-weight: 600;
            }
            """
        )

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(sub_label)
        layout.addStretch(1)

        return frame, value_label, sub_label

    # ---------------------------------------------------------------------
    # Recent activity (list instead of table)
    # ---------------------------------------------------------------------
    def _create_recent_activity_section(self) -> QWidget:
        """Create a compact 'Recent Activity' list (more readable than a table)."""
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)

        title = QLabel("🕒 Recent Activity")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #2c3e50;")
        header_row.addWidget(title, 1)

        outer.addLayout(header_row)

        host = QWidget()
        host_layout = QVBoxLayout(host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        host_layout.setSpacing(10)

        self._recent_list_host = host
        self._recent_list_layout = host_layout

        outer.addWidget(host)

        info = QLabel("")
        info.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        self._recent_info_label = info
        outer.addWidget(info)

        return container

    def _build_recent_item(self, created_at: str, category: str, score_text: str) -> QFrame:
        """Build a single recent activity row as a card."""
        card = QFrame()
        card.setStyleSheet(
            """
            QFrame {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 12px;
            }
            """
        )
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        row = QHBoxLayout(card)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(12)

        left = QVBoxLayout()
        left.setSpacing(2)

        date_lbl = QLabel(created_at)
        date_lbl.setStyleSheet("color: #7f8c8d; font-size: 11px; font-weight: 600;")

        cat_lbl = QLabel(category)
        cat_lbl.setStyleSheet("color: #2c3e50; font-size: 13px; font-weight: 800;")
        cat_lbl.setWordWrap(True)

        left.addWidget(date_lbl)
        left.addWidget(cat_lbl)

        score_badge = QLabel(score_text)
        score_badge.setAlignment(Qt.AlignCenter)
        score_badge.setMinimumWidth(76)
        score_badge.setStyleSheet(
            """
            QLabel {
                background-color: #ecf0f1;
                color: #2c3e50;
                border-radius: 10px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 800;
            }
            """
        )

        row.addLayout(left, 1)
        row.addWidget(score_badge, 0, Qt.AlignRight)

        return card

    # ---------------------------------------------------------------------
    # Responsive behavior
    # ---------------------------------------------------------------------
    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """Update responsive sections when the window size changes."""
        super().resizeEvent(event)
        self._update_responsive_layout()

    def _update_responsive_layout(self) -> None:
        """Adjust stat card columns based on available width."""
        width = self.width()

        if width < C.COLS_1_MAX:
            cols = 1
        elif width < C.COLS_2_MAX:
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

        while self._stats_grid.count():
            item = self._stats_grid.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)

        for idx, card in enumerate(self._stats_cards):
            row = idx // columns
            col = idx % columns
            self._stats_grid.addWidget(card, row, col)

        for c in range(columns):
            self._stats_grid.setColumnStretch(c, 1)

    # ---------------------------------------------------------------------
    # Data refresh
    # ---------------------------------------------------------------------
    def refresh(self) -> None:
        """Refresh stats and recent activity from the database."""
        if self.user_id <= 0:
            logger.warning("Dashboard refresh skipped: invalid user_id=%s", self.user_id)
            return

        total_attempts, best_percent, last_percent = db.get_attempt_stats(self.user_id)

        recent = db.get_recent_attempts(self.user_id, limit=C.RECENT_LIMIT)
        attempts_for_7_days = db.get_recent_attempts(self.user_id, limit=50)

        # Main values
        if self._stats_total_value is not None:
            self._stats_total_value.setText(str(total_attempts))
        if self._stats_best_value is not None:
            self._stats_best_value.setText(f"{best_percent}%")
        if self._stats_last_value is not None:
            self._stats_last_value.setText(f"{last_percent}%")

        # Subtext
        last_7_days = self._count_attempts_last_days(attempts_for_7_days, days=7)
        if self._stats_total_sub is not None:
            self._stats_total_sub.setText(f"Last 7 days: {last_7_days}")

        if self._stats_best_sub is not None:
            self._stats_best_sub.setText("Personal best")

        if self._stats_last_sub is not None:
            if recent:
                self._stats_last_sub.setText(f"Latest: {recent[0][0]}")
            else:
                self._stats_last_sub.setText("No attempts yet")

        self._populate_recent_activity(recent)

    def _count_attempts_last_days(self, rows: list[tuple[str, str, int, int]], days: int) -> int:
        """Count how many attempts happened in the last N days."""
        if not rows:
            return 0

        cutoff = datetime.now() - timedelta(days=days)
        count = 0

        for created_at, _, _, _ in rows:
            try:
                dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M")
            except Exception:
                continue

            if dt >= cutoff:
                count += 1

        return count

    def _populate_recent_activity(self, rows: list[tuple[str, str, int, int]]) -> None:
        """Fill the recent activity list.

        Args:
            rows: (created_at_str, category_name, correct_count, total_questions)
        """
        if self._recent_list_layout is None:
            return

        while self._recent_list_layout.count():
            item = self._recent_list_layout.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)

        if not rows:
            empty = QLabel("No attempts yet. Start a quiz to see your activity here.")
            empty.setStyleSheet("color: #7f8c8d; font-size: 12px;")
            self._recent_list_layout.addWidget(empty)

            if self._recent_info_label is not None:
                self._recent_info_label.setText("")
            return

        for created_at, category_name, correct_count, total_questions in rows:
            score_text = f"{correct_count}/{total_questions}"
            card = self._build_recent_item(created_at, category_name, score_text)
            self._recent_list_layout.addWidget(card)

        if self._recent_info_label is not None:
            self._recent_info_label.setText(f"Showing last {len(rows)} attempt(s).")

    # ---------------------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------------------
    @staticmethod
    def _darken_color(hex_color: str, factor: float = 0.9) -> str:
        """Return a darker version of a hex color."""
        color = hex_color.lstrip("#")
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)

        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

