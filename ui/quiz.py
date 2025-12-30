import logging
from typing import Any, Dict, List, Optional, Tuple

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from db import db

logger = logging.getLogger(__name__)

LETTERS = ["A", "B", "C", "D"]


class QuizWidget(QWidget):
    """Widget for taking a quiz."""

    quiz_completed = pyqtSignal(dict)  # emits a results dict
    back_clicked = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.category_id: Optional[int] = None
        self.category_name: Optional[str] = None

        # Expected question tuple:
        # (id, question_text, correct_answer, option_a, option_b, option_c, option_d)
        self.questions: List[Tuple[Any, ...]] = []
        self.current_index: int = 0
        self.answers: Dict[int, str] = {}  # {question_id: selected_letter}

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout()
        self.setLayout(layout)

        header_layout = QHBoxLayout()

        self.back_btn = QPushButton("← Back to Categories")
        self.back_btn.setStyleSheet(
            """
            background-color: #95a5a6; color: white; border: none;
            border-radius: 5px; padding: 10px 20px; font-size: 14px;
            """
        )
        self.back_btn.clicked.connect(self.on_back_clicked)
        header_layout.addWidget(self.back_btn)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.category_label = QLabel("")
        self.category_label.setAlignment(Qt.AlignCenter)
        self.category_label.setStyleSheet(
            """
            font-size: 24px; font-weight: bold; color: #2c3e50; margin: 20px;
            """
        )
        layout.addWidget(self.category_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                height: 25px;
                margin: 0px 40px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
            }
            """
        )
        layout.addWidget(self.progress_bar)

        self.question_num_label = QLabel("")
        self.question_num_label.setAlignment(Qt.AlignCenter)
        self.question_num_label.setStyleSheet(
            """
            font-size: 14px; color: #7f8c8d; margin: 10px;
            """
        )
        layout.addWidget(self.question_num_label)

        self.question_label = QLabel("")
        self.question_label.setWordWrap(True)
        self.question_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.question_label.setStyleSheet(
            """
            font-size: 18px; padding: 20px;
            background-color: #ecf0f1; border-radius: 8px;
            margin: 10px 40px; min-height: 100px;
            """
        )
        layout.addWidget(self.question_label)

        self.button_group = QButtonGroup(self)
        self.radio_buttons: List[QRadioButton] = []

        for i, letter in enumerate(LETTERS):
            radio = QRadioButton(f"{letter}. ")
            radio.setStyleSheet(
                """
                QRadioButton {
                    font-size: 16px;
                    padding: 12px;
                    margin: 5px 60px;
                }
                QRadioButton::indicator {
                    width: 20px;
                    height: 20px;
                }
                """
            )
            self.button_group.addButton(radio, i)
            self.radio_buttons.append(radio)
            layout.addWidget(radio)

        nav_layout = QHBoxLayout()
        nav_layout.addStretch()

        self.prev_btn = QPushButton("⬅ Previous")
        self.prev_btn.setStyleSheet(
            """
            background-color: #95a5a6; color: white; border: none;
            border-radius: 5px; padding: 12px 24px; font-size: 14px;
            margin: 20px 10px;
            """
        )
        self.prev_btn.clicked.connect(self.previous_question)
        nav_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Next ➡")
        self.next_btn.setStyleSheet(
            """
            background-color: #3498db; color: white; border: none;
            border-radius: 5px; padding: 12px 24px; font-size: 14px;
            margin: 20px 10px; font-weight: bold;
            """
        )
        self.next_btn.clicked.connect(self.next_question)
        nav_layout.addWidget(self.next_btn)

        nav_layout.addStretch()
        layout.addLayout(nav_layout)

        self._set_quiz_enabled(False)

    def _set_quiz_enabled(self, enabled: bool) -> None:
        self.back_btn.setEnabled(True)  # always allow back
        self.prev_btn.setEnabled(enabled and self.current_index > 0)
        self.next_btn.setEnabled(enabled)
        for radio in self.radio_buttons:
            radio.setEnabled(enabled)

    def _clear_selection(self) -> None:
        self.button_group.setExclusive(False)
        for radio in self.radio_buttons:
            radio.setChecked(False)
        self.button_group.setExclusive(True)

    def _get_current_question_id(self) -> Optional[int]:
        if not self.questions:
            return None
        return int(self.questions[self.current_index][0])

    def _get_selected_letter(self) -> Optional[str]:
        checked_id = self.button_group.checkedId()
        if checked_id < 0:
            return None
        return LETTERS[checked_id]

    def _save_current_answer(self) -> None:
        q_id = self._get_current_question_id()
        if q_id is None:
            return

        selected = self._get_selected_letter()
        if selected is not None:
            self.answers[q_id] = selected

    def load_quiz(self, category_id: int, category_name: str, limit: int | None = None) -> None:
        """Load quiz for a category.

        Args:
        category_id: Category identifier.
        category_name: Category display name.
        limit: Optional number of questions to load (randomized on DB side).
        """
        self.category_id = category_id
        self.category_name = category_name
        self.category_label.setText(f"🎯 Quiz: {category_name}")

        self._set_quiz_enabled(False)
        self.questions = []
        self.answers = {}
        self.current_index = 0

        # Ensure DB connection exists
        if not db.is_connected():
            if not db.connect():
                QMessageBox.critical(
                    self,
                    "Database Error",
                    "Could not connect to PostgreSQL.\n\nEnsure Docker is running and the database is available.",
                )
                self.back_clicked.emit()
                return

        self.questions = db.get_questions_by_category(category_id, limit)

        if not self.questions:
            QMessageBox.warning(
                self,
                "No Questions",
                f"No questions found for category '{category_name}'.\n\n"
                "Add some questions in the Admin panel first!",
            )
            self.back_clicked.emit()
            return

        self.progress_bar.setMaximum(len(self.questions))
        self.progress_bar.setValue(0)

        self._set_quiz_enabled(True)
        self.display_question()

    def display_question(self) -> None:
        """Display the current question."""
        if not self.questions:
            self._set_quiz_enabled(False)
            return

        q = self.questions[self.current_index]
        q_id = int(q[0])
        q_text = str(q[1])
        opt_a, opt_b, opt_c, opt_d = q[3], q[4], q[5], q[6]

        self.question_num_label.setText(f"Question {self.current_index + 1} of {len(self.questions)}")
        self.progress_bar.setValue(self.current_index + 1)
        self.question_label.setText(q_text)

        options = [opt_a, opt_b, opt_c, opt_d]
        for i, (radio, option_text) in enumerate(zip(self.radio_buttons, options)):
            radio.setText(f"{LETTERS[i]}. {option_text}")

        if q_id in self.answers:
            letter = self.answers[q_id]
            if letter in LETTERS:
                self.radio_buttons[LETTERS.index(letter)].setChecked(True)
            else:
                self._clear_selection()
        else:
            self._clear_selection()

        self.prev_btn.setEnabled(self.current_index > 0)

        is_last = self.current_index == len(self.questions) - 1
        if is_last:
            self.next_btn.setText("Submit ✓")
            self.next_btn.setStyleSheet(
                """
                background-color: #27ae60; color: white; border: none;
                border-radius: 5px; padding: 12px 24px; font-size: 14px;
                margin: 20px 10px; font-weight: bold;
                """
            )
        else:
            self.next_btn.setText("Next ➡")
            self.next_btn.setStyleSheet(
                """
                background-color: #3498db; color: white; border: none;
                border-radius: 5px; padding: 12px 24px; font-size: 14px;
                margin: 20px 10px; font-weight: bold;
                """
            )

    def next_question(self) -> None:
        """Go to next question or submit quiz."""
        if not self.questions:
            return

        self._save_current_answer()

        is_last = self.current_index == len(self.questions) - 1
        if is_last:
            unanswered = len(self.questions) - len(self.answers)
            if unanswered > 0:
                reply = QMessageBox.question(
                    self,
                    "Unanswered Questions",
                    f"You have {unanswered} unanswered question(s).\n\nSubmit anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.No:
                    return

            self.submit_quiz()
            return

        self.current_index += 1
        self.display_question()

    def previous_question(self) -> None:
        """Go to previous question."""
        if not self.questions or self.current_index <= 0:
            return

        self._save_current_answer()
        self.current_index -= 1
        self.display_question()

    def submit_quiz(self) -> None:
        """Submit the quiz and emit results."""
        if not self.questions:
            return

        logger.info("Quiz submitted with %s answers", len(self.answers))
        self._set_quiz_enabled(False)

        results: Dict[str, Any] = {
            "category_id": self.category_id,
            "category_name": self.category_name,
            "total_questions": len(self.questions),
            "answered_count": len(self.answers),
            "questions": self.questions,
            "answers": self.answers,
        }

        self.quiz_completed.emit(results)

    def on_back_clicked(self) -> None:
        """Handle back button click."""
        if self.answers:
            reply = QMessageBox.question(
                self,
                "Quit Quiz",
                "Are you sure you want to quit?\n\nYour progress will be lost.",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        self.back_clicked.emit()
