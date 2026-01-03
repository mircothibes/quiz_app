from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from db import db

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _Ui:
    """UI constants for the dashboard screen."""

    # Centered layout
    CONTENT_MAX_WIDTH: int = 1100
    CONTENT_MARGIN: int = 24
    CONTENT_SPACING: int = 18

    # Breakpoints
    BP_ONE_COL: int = 720
    BP_TWO_COL: int = 980

    # Grid spacing
    GRID_H_SPACING: int = 14
    GRID_V_SPACING: int = 14

    # Header
    HEADER_MIN_HEIGHT: int = 140

    # Cards
    ACTION_CARD_MIN_HEIGHT: int = 84
    ACTION_CARD_MIN_HEIGHT_COMPACT: int = 68

    STAT_CARD_MIN_HEIGHT: int = 118
    STAT_CARD_MIN_HEIGHT_COMPACT: int = 108

    ACTIVITY_CARD_MIN_HEIGHT: int = 72
    ACTIVITY_SCORE_PILL_MIN_WIDTH: int = 68


UI = _Ui()


class _ClickableCard(QFrame):
    """A clickable card widget (QFrame) that emits a clicked signal.

    This is used instead of QPushButton to allow rich layout (title/subtitle)
    without HTML rendering issues.
    """

    clicked = pyqtSignal()

    def __init__(self, object_name: str = "clickableCard") -> None:
        super().__init__()
        self.setObjectName(object_name)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class DashboardWidget(QWidget):
    """Dashboard screen: quick actions, stats, and recent activity.

    Responsibilities:
    - Provide main actions (start quiz, admin, logout)
    - Display lightweight user stats
    - Display recent attempts as compact activity cards
    - Keep layout responsive and centered
    """

    browse_categories_clicked = pyqtSignal()
    manage_questions_clicked = pyqtSignal()
    logout_clicked = pyqtSignal()

    def __init__(self, username: str, user_id: int) -> None:
        super().__init__()
        self.username = username
        self.user_id = user_id

        # Responsive state
        self._compact_mode: bool = False
        self._quick_columns: int = 2
        self._stats_columns: int = 3

        # Quick actions
        self._quick_grid: Optional[QGridLayout] = None
        self._quick_cards: list[_ClickableCard] = []

        # Stats
        self._stats_grid: Optional[QGridLayout] = None
        self._stats_cards: list[QFrame] = []

        self._stats_total_value: Optional[QLabel] = None
        self._stats_total_footer: Optional[QLabel] = None
        self._stats_best_value: Optional[QLabel] = None
        self._stats_best_footer: Optional[QLabel] = None
        self._stats_last_value: Optional[QLabel] = None
        self._stats_last_footer: Optional[QLabel] = None

        # Activity list
        self._activity_list: Optional[QVBoxLayout] = None
        self._activity_info: Optional[QLabel] = None

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

        wrapper = QWidget()
        wrapper_layout = QHBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addStretch(1)

        content = QWidget()
        content.setMaximumWidth(UI.CONTENT_MAX_WIDTH)
        content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(UI.CONTENT_MARGIN, UI.CONTENT_MARGIN, UI.CONTENT_MARGIN, UI.CONTENT_MARGIN)
        content_layout.setSpacing(UI.CONTENT_SPACING)
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

        self._apply_styles()
        self._update_responsive_layout()

    def _apply_styles(self) -> None:
        """Apply global styles for cards (hover/pressed effects, etc.)."""
        self.setStyleSheet(
            """
            QFrame#clickableCard {
                border-radius: 14px;
                border: none;
            }
            QFrame#clickableCard:hover {
                opacity: 0.98;
            }
            QFrame#activityCard {
                background-color: white;
                border: 2px solid #dfe6e9;
                border-radius: 14px;
            }
            """
        )

    def _create_header(self) -> QFrame:
        """Create header with welcome + subtitle + logout."""
        header = QFrame()
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header.setMinimumHeight(UI.HEADER_MIN_HEIGHT)
        header.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9
                );
                border-radius: 14px;
            }
            """
        )

        outer = QVBoxLayout(header)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        self._welcome_label = QLabel(f"👋 Welcome back, {self.username}")
        self._welcome_label.setWordWrap(True)
        self._welcome_label.setStyleSheet("font-size: 26px; font-weight: 800; color: white;")

        self._logout_btn = QLabel("🚪  Logout")
        self._logout_btn.setAlignment(Qt.AlignCenter)
        self._logout_btn.setFixedHeight(34)
        self._logout_btn.setMinimumWidth(110)
        self._logout_btn.setCursor(Qt.PointingHandCursor)
        self._logout_btn.setStyleSheet(
            """
            QLabel {
                background-color: rgba(255, 255, 255, 0.18);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 10px;
                padding: 0 10px;
                font-size: 13px;
                font-weight: 700;
            }
            """
        )
        self._logout_btn.mousePressEvent = self._on_logout_clicked  # type: ignore[method-assign]

        top_row.addWidget(self._welcome_label, 1)
        top_row.addStretch(1)
        top_row.addWidget(self._logout_btn, 0, Qt.AlignRight)

        self._subtitle_label = QLabel("Ready for your next quiz?")
        self._subtitle_label.setWordWrap(True)
        self._subtitle_label.setStyleSheet("font-size: 14px; color: rgba(255, 255, 255, 0.92);")

        outer.addLayout(top_row)
        outer.addWidget(self._subtitle_label)

        return header

    def _on_logout_clicked(self, event) -> None:
        """Emit logout when the logout label is clicked."""
        self.logout_clicked.emit()

    def _create_quick_actions(self) -> QWidget:
        """Create quick actions section (clickable cards)."""
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        title = QLabel("⚡ Quick Actions")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #2c3e50;")
        outer.addWidget(title)

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(UI.GRID_H_SPACING)
        grid.setVerticalSpacing(UI.GRID_V_SPACING)
        self._quick_grid = grid

        start_card = self._create_action_card(
            title="▶ Start Quiz",
            subtitle="Pick a category and begin",
            color="#27ae60",
        )
        start_card.clicked.connect(self.browse_categories_clicked.emit)

        admin_card = self._create_action_card(
            title="⚙ Manage Questions    [Admin]",
            subtitle="Add, edit, or delete questions",
            color="#f39c12",
        )
        admin_card.clicked.connect(self.manage_questions_clicked.emit)

        self._quick_cards = [start_card, admin_card]
        outer.addWidget(grid_host)

        self._reflow_quick_actions(columns=2)
        return container

    def _create_stats_section(self) -> QWidget:
        """Create stats section with responsive cards."""
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        title = QLabel("📊 Your Stats")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #2c3e50;")
        outer.addWidget(title)

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(UI.GRID_H_SPACING)
        grid.setVerticalSpacing(UI.GRID_V_SPACING)
        self._stats_grid = grid

        card_total, self._stats_total_value, self._stats_total_footer = self._create_stat_card(
            title="Total Attempts",
            value="0",
            footer="Last 7 days: 0",
            bg_color="#e74c3c",
        )
        card_best, self._stats_best_value, self._stats_best_footer = self._create_stat_card(
            title="Best Score",
            value="0%",
            footer="Personal best",
            bg_color="#8e44ad",
        )
        card_last, self._stats_last_value, self._stats_last_footer = self._create_stat_card(
            title="Last Score",
            value="0%",
            footer="Latest: —",
            bg_color="#f1c40f",
        )

        self._stats_cards = [card_total, card_best, card_last]
        outer.addWidget(grid_host)

        self._reflow_stats_cards(columns=3)
        return container

    def _create_recent_activity_section(self) -> QWidget:
        """Create recent activity as a vertical list of cards."""
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        title = QLabel("🕒 Recent Activity")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #2c3e50;")
        outer.addWidget(title)

        list_host = QWidget()
        list_layout = QVBoxLayout(list_host)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(12)
        list_layout.setAlignment(Qt.AlignTop)

        self._activity_list = list_layout
        outer.addWidget(list_host)

        info = QLabel("")
        info.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        self._activity_info = info
        outer.addWidget(info)

        return container

    # ---------------------------------------------------------------------
    # Responsive behavior
    # ---------------------------------------------------------------------
    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """Reflow responsive sections when window size changes."""
        super().resizeEvent(event)
        self._update_responsive_layout()

    def _update_responsive_layout(self) -> None:
        """Adjust responsive grids and compact mode based on window width."""
        width = self.width()

        compact = width < UI.BP_ONE_COL
        if compact != self._compact_mode:
            self._compact_mode = compact
            self._apply_compact_mode(compact)

        quick_cols = 1 if width < UI.BP_ONE_COL else 2
        if quick_cols != self._quick_columns:
            self._reflow_quick_actions(columns=quick_cols)
            self._quick_columns = quick_cols

        if width < UI.BP_ONE_COL:
            stats_cols = 1
        elif width < UI.BP_TWO_COL:
            stats_cols = 2
        else:
            stats_cols = 3

        if stats_cols != self._stats_columns:
            self._reflow_stats_cards(columns=stats_cols)
            self._stats_columns = stats_cols

    def _apply_compact_mode(self, compact: bool) -> None:
        """Apply compact spacing/sizing for small windows."""
        if compact:
            self._welcome_label.setStyleSheet("font-size: 22px; font-weight: 800; color: white;")
            self._subtitle_label.setStyleSheet("font-size: 13px; color: rgba(255, 255, 255, 0.92);")
        else:
            self._welcome_label.setStyleSheet("font-size: 26px; font-weight: 800; color: white;")
            self._subtitle_label.setStyleSheet("font-size: 14px; color: rgba(255, 255, 255, 0.92);")

        for card in self._quick_cards:
            min_h = UI.ACTION_CARD_MIN_HEIGHT_COMPACT if compact else UI.ACTION_CARD_MIN_HEIGHT
            card.setMinimumHeight(min_h)
            card.setProperty("compact", compact)
            card.style().unpolish(card)
            card.style().polish(card)

        for card in self._stats_cards:
            min_h = UI.STAT_CARD_MIN_HEIGHT_COMPACT if compact else UI.STAT_CARD_MIN_HEIGHT
            card.setMinimumHeight(min_h)

    def _reflow_quick_actions(self, columns: int) -> None:
        """Reposition quick action cards in the grid."""
        if self._quick_grid is None:
            return

        while self._quick_grid.count():
            item = self._quick_grid.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)

        for idx, card in enumerate(self._quick_cards):
            row = idx // columns
            col = idx % columns
            self._quick_grid.addWidget(card, row, col)

        for c in range(columns):
            self._quick_grid.setColumnStretch(c, 1)

    def _reflow_stats_cards(self, columns: int) -> None:
        """Reposition stats cards in the grid."""
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
        recent = db.get_recent_attempts(self.user_id, limit=5)

        last_7_days = self._get_attempts_last_days(user_id=self.user_id, days=7)
        latest_created_at = recent[0][0] if recent else "—"

        if self._stats_total_value is not None:
            self._stats_total_value.setText(str(total_attempts))
        if self._stats_total_footer is not None:
            self._stats_total_footer.setText(f"Last 7 days: {last_7_days}")

        if self._stats_best_value is not None:
            self._stats_best_value.setText(f"{best_percent}%")
        if self._stats_best_footer is not None:
            self._stats_best_footer.setText("Personal best")

        if self._stats_last_value is not None:
            self._stats_last_value.setText(f"{last_percent}%")
        if self._stats_last_footer is not None:
            self._stats_last_footer.setText(f"Latest: {latest_created_at}")

        self._populate_recent_activity(recent)

    def _get_attempts_last_days(self, user_id: int, days: int) -> int:
        """Return attempts count for the last N days.

        If db.fetch_one() is not available, returns 0 safely.
        """
        if not hasattr(db, "fetch_one"):
            return 0

        try:
            row = db.fetch_one(
                """
                SELECT COUNT(*)
                FROM quiz_attempts
                WHERE user_id = %s
                  AND created_at >= (NOW() - (%s || ' days')::interval)
                """,
                (user_id, int(days)),
            )
            return int(row[0]) if row and row[0] is not None else 0
        except Exception:
            logger.exception("Failed to compute attempts for last %s days", days)
            return 0

    def _populate_recent_activity(self, rows: list[tuple[str, str, int, int]]) -> None:
        """Populate the recent activity list.

        Args:
            rows: (created_at_str, category_name, correct_count, total_questions)
        """
        if self._activity_list is None:
            return

        self._clear_layout(self._activity_list)

        if not rows:
            empty = QLabel("No attempts yet. Start a quiz to see your activity here.")
            empty.setStyleSheet("color: #7f8c8d; font-size: 13px;")
            self._activity_list.addWidget(empty)

            if self._activity_info is not None:
                self._activity_info.setText("")
            return

        for created_at, category_name, correct_count, total_questions in rows:
            score_text = f"{correct_count}/{total_questions}"
            card = self._create_activity_card(created_at=created_at, category=category_name, score=score_text)
            self._activity_list.addWidget(card)

        if self._activity_info is not None:
            self._activity_info.setText(f"Showing last {len(rows)} attempt(s).")

    @staticmethod
    def _clear_layout(layout: QVBoxLayout) -> None:
        """Remove all widgets from a layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                w.setParent(None)

    # ---------------------------------------------------------------------
    # Components
    # ---------------------------------------------------------------------
    def _create_action_card(self, title: str, subtitle: str, color: str) -> _ClickableCard:
        """Create a clickable action card with title + subtitle."""
        card = _ClickableCard()
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setMinimumHeight(UI.ACTION_CARD_MIN_HEIGHT)

        card.setStyleSheet(
            f"""
            QFrame#clickableCard {{
                background-color: {color};
                border-radius: 14px;
            }}
            QFrame#clickableCard:hover {{
                background-color: {self._darken_color(color)};
            }}
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: white; font-size: 16px; font-weight: 900;")
        title_lbl.setWordWrap(True)

        subtitle_lbl = QLabel(subtitle)
        subtitle_lbl.setStyleSheet("color: rgba(255,255,255,0.92); font-size: 12px; font-weight: 600;")
        subtitle_lbl.setWordWrap(True)

        layout.addWidget(title_lbl)
        layout.addWidget(subtitle_lbl)
        layout.addStretch(1)

        return card

    def _create_stat_card(self, title: str, value: str, footer: str, bg_color: str) -> tuple[QFrame, QLabel, QLabel]:
        """Create a stat card with title, value, and footer line."""
        frame = QFrame()
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {bg_color};
                border: none;
                border-radius: 14px;
            }}
            """
        )
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        frame.setMinimumHeight(UI.STAT_CARD_MIN_HEIGHT)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: rgba(255,255,255,0.90); font-size: 12px; font-weight: 800;")

        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 30px; font-weight: 950;")

        footer_label = QLabel(footer)
        footer_label.setStyleSheet("color: rgba(255,255,255,0.88); font-size: 12px; font-weight: 700;")

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(footer_label)
        layout.addStretch(1)

        return frame, value_label, footer_label

    def _create_activity_card(self, created_at: str, category: str, score: str) -> QFrame:
        """Create a compact card representing one recent attempt."""
        frame = QFrame()
        frame.setObjectName("activityCard")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        frame.setMinimumHeight(UI.ACTIVITY_CARD_MIN_HEIGHT)

        outer = QHBoxLayout(frame)
        outer.setContentsMargins(14, 10, 14, 10)
        outer.setSpacing(12)

        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(4)

        date_lbl = QLabel(created_at)
        date_lbl.setStyleSheet("color: #7f8c8d; font-size: 12px; font-weight: 800;")

        cat_lbl = QLabel(category)
        cat_lbl.setStyleSheet("color: #2c3e50; font-size: 14px; font-weight: 950;")
        cat_lbl.setWordWrap(True)

        left_col.addWidget(date_lbl)
        left_col.addWidget(cat_lbl)

        pill = QLabel(score)
        pill.setAlignment(Qt.AlignCenter)
        pill.setMinimumWidth(UI.ACTIVITY_SCORE_PILL_MIN_WIDTH)
        pill.setStyleSheet(
            """
            QLabel {
                background-color: #ecf0f1;
                border: 1px solid #d0d7de;
                border-radius: 14px;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: 950;
                color: #2c3e50;
            }
            """
        )

        outer.addLayout(left_col, 1)
        outer.addWidget(pill, 0, Qt.AlignRight | Qt.AlignVCenter)

        return frame

    @staticmethod
    def _darken_color(hex_color: str, factor: float = 0.9) -> str:
        """Return a darker version of a hex color."""
        color = hex_color.lstrip("#")
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)

        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"




