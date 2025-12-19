import logging
from typing import Any, Dict, List, Optional, Tuple

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)

LETTERS = ["A", "B", "C", "D"]


class ResultsWidget(QWidget):
    """Widget to display quiz results."""

    retake_quiz_clicked = pyqtSignal(int, str)  # (category_id, category_name)
    back_to_dashboard_clicked = pyqtSignal()
    back_to_categories_clicked = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._last_results: Optional[Dict[str, Any]] = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout()
        self.setLayout(layout)

        header = QHBoxLayout()

        back_dash_btn = QPushButton("← Dashboard")
        back_dash_btn.clicked.connect(self.back_to_dashboard_clicked.emit)
        back_dash_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #7f8c8d; }
            """
        )
        header.addWidget(back_dash_btn)

        back_cat_btn = QPushButton("← Categories")
        back_cat_btn.clicked.connect(self.back_to_categories_clicked.emit)
        back_cat_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #2980b9; }
            """
        )
        header.addWidget(back_cat_btn)

        header.addStretch()
        layout.addLayout(header)

        self.title = QLabel("🏁 Results")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet(
            """
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 10px;
            """
        )
        layout.addWidget(self.title)

        self.summary = QLabel("")
        self.summary.setAlignment(Qt.AlignCenter)
        self.summary.setStyleSheet(
            """
            font-size: 14px;
            color: #7f8c8d;
            margin-bottom: 10px;
            """
        )
        layout.addWidget(self.summary)

        self.score_label = QLabel("")
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setStyleSheet(
            """
            font-size: 18px;
            font-weight: bold;
            color: #27ae60;
            margin-bottom: 15px;
            """
        )
        layout.addWidget(self.score_label)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            """
            QListWidget {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                background-color: white;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #ecf0f1;
            }
            """
        )
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.retake_btn = QPushButton("🔁 Retake Quiz")
        self.retake_btn.setEnabled(False)
        self.retake_btn.clicked.connect(self._on_retake_clicked)
        self.retake_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px 22px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
            QPushButton:disabled { background-color: #bdc3c7; }
            """
        )
        btn_row.addWidget(self.retake_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

    def load_results(self, results: Dict[str, Any]) -> None:
        """Render results produced by QuizWidget."""
        self._last_results = results
        self.retake_btn.setEnabled(True)

        category_name = str(results.get("category_name") or "Unknown")
        total_questions = int(results.get("total_questions") or 0)

        questions: List[Tuple[Any, ...]] = list(results.get("questions") or [])
        answers: Dict[int, str] = dict(results.get("answers") or {})

        if total_questions <= 0:
            total_questions = len(questions)

        correct_count = 0
        answered_count = len(answers)

        self.title.setText(f"🏁 Results — {category_name}")
        self.summary.setText(f"Answered {answered_count} out of {total_questions} questions")

        self.list_widget.clear()

        for q in questions:
            # Expected tuple:
            # (id, question_text, correct_answer, option_a, option_b, option_c, option_d)
            q_id = int(q[0])
            q_text = str(q[1])
            correct = str(q[2]).strip()

            user_letter = str(answers.get(q_id) or "").strip()

            is_correct = (user_letter != "" and user_letter.upper() == correct.upper())
            if is_correct:
                correct_count += 1

            status = "✅" if is_correct else "❌"
            user_display = user_letter if user_letter else "—"
            item_text = f"{status} {q_text}\n   Your answer: {user_display} | Correct: {correct}"

            item = QListWidgetItem(item_text)
            self.list_widget.addItem(item)

        percent = int(round((correct_count / max(total_questions, 1)) * 100))
        self.score_label.setText(f"Score: {correct_count}/{total_questions} ({percent}%)")

        if percent >= 70:
            self.score_label.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #27ae60; margin-bottom: 15px;"
            )
        elif percent >= 40:
            self.score_label.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #f39c12; margin-bottom: 15px;"
            )
        else:
            self.score_label.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #e74c3c; margin-bottom: 15px;"
            )

        logger.info("Results loaded: %s/%s (%s%%)", correct_count, total_questions, percent)

    def _on_retake_clicked(self) -> None:
        if not self._last_results:
            return

        category_id = int(self._last_results.get("category_id") or 0)
        category_name = str(self._last_results.get("category_name") or "")

        if category_id <= 0 or not category_name:
            return

        self.retake_quiz_clicked.emit(category_id, category_name)
