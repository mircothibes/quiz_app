from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QRadioButton, QButtonGroup, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from db import db


class QuizWidget(QWidget):
    """Widget for taking a quiz."""
    
    # Signals
    quiz_completed = pyqtSignal(dict)  # Emits answers dict when done
    back_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.category_id = None
        self.category_name = None
        self.questions = []
        self.current_index = 0
        self.answers = {}  # {question_id: selected_answer}
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header with back button
        header_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Back to Categories")
        back_btn.setStyleSheet("""
            background-color: #95a5a6; color: white; border: none;
            border-radius: 5px; padding: 10px 20px; font-size: 14px;
        """)
        back_btn.clicked.connect(self.on_back_clicked)
        header_layout.addWidget(back_btn)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Category title
        self.category_label = QLabel("")
        self.category_label.setAlignment(Qt.AlignCenter)  # type: ignore[reportAttributeAccessIssue]
        self.category_label.setStyleSheet("""
            font-size: 24px; font-weight: bold; color: #2c3e50; margin: 20px;
        """)
        layout.addWidget(self.category_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
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
        """)
        layout.addWidget(self.progress_bar)
        
        # Question number
        self.question_num_label = QLabel("")
        self.question_num_label.setAlignment(Qt.AlignCenter)  # type: ignore[reportAttributeAccessIssue]
        self.question_num_label.setStyleSheet("""
            font-size: 14px; color: #7f8c8d; margin: 10px;
        """)
        layout.addWidget(self.question_num_label)
        
        # Question text
        self.question_label = QLabel("")
        self.question_label.setWordWrap(True)
        self.question_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # type: ignore[reportAttributeAccessIssue]
        self.question_label.setStyleSheet("""
            font-size: 18px; padding: 20px; 
            background-color: #ecf0f1; border-radius: 8px;
            margin: 10px 40px; min-height: 100px;
        """)
        layout.addWidget(self.question_label)
        
        # Options
        self.button_group = QButtonGroup()
        self.radio_buttons = []
        
        for i, letter in enumerate(['A', 'B', 'C', 'D']):
            radio = QRadioButton(f"{letter}. ")
            radio.setStyleSheet("""
                QRadioButton {
                    font-size: 16px;
                    padding: 12px;
                    margin: 5px 60px;
                }
                QRadioButton::indicator {
                    width: 20px;
                    height: 20px;
                }
            """)
            self.button_group.addButton(radio, i)
            self.radio_buttons.append(radio)
            layout.addWidget(radio)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()
        
        self.prev_btn = QPushButton("⬅ Previous")
        self.prev_btn.setStyleSheet("""
            background-color: #95a5a6; color: white; border: none;
            border-radius: 5px; padding: 12px 24px; font-size: 14px;
            margin: 20px 10px;
        """)
        self.prev_btn.clicked.connect(self.previous_question)
        nav_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("Next ➡")
        self.next_btn.setStyleSheet("""
            background-color: #3498db; color: white; border: none;
            border-radius: 5px; padding: 12px 24px; font-size: 14px;
            margin: 20px 10px; font-weight: bold;
        """)
        self.next_btn.clicked.connect(self.next_question)
        nav_layout.addWidget(self.next_btn)
        
        nav_layout.addStretch()
        layout.addLayout(nav_layout)
    
    def load_quiz(self, category_id, category_name):
        """Load quiz for a category.
        
        Args:
            category_id (int): Category ID
            category_name (str): Category name
        """
        self.category_id = category_id
        self.category_name = category_name
        self.category_label.setText(f"🎯 Quiz: {category_name}")
        
        # Load questions
        self.questions = db.get_questions_by_category(category_id)
        
        if not self.questions:
            QMessageBox.warning(
                self, "No Questions",
                f"No questions found for category '{category_name}'.\n\n"
                "Add some questions in the Admin panel first!"
            )
            self.back_clicked.emit()
            return
        
        # Reset state
        self.current_index = 0
        self.answers = {}
        
        # Update progress bar
        self.progress_bar.setMaximum(len(self.questions))
        
        # Display first question
        self.display_question()
    
    def display_question(self):
        """Display the current question."""
        if not self.questions:
            return
        
        q_id, q_text, correct, opt_a, opt_b, opt_c, opt_d = self.questions[self.current_index]
        
        # Update question number
        self.question_num_label.setText(
            f"Question {self.current_index + 1} of {len(self.questions)}"
        )
        
        # Update progress
        self.progress_bar.setValue(self.current_index + 1)
        
        # Update question text
        self.question_label.setText(q_text)
        
        # Update options
        options = [opt_a, opt_b, opt_c, opt_d]
        for radio, option_text in zip(self.radio_buttons, options):
            radio.setText(f"{radio.text()[0]}. {option_text}")
        
        # Restore previous answer if exists
        if q_id in self.answers:
            answer = self.answers[q_id]
            index = ['A', 'B', 'C', 'D'].index(answer)
            self.radio_buttons[index].setChecked(True)
        else:
            self.button_group.setExclusive(False)
            for radio in self.radio_buttons:
                radio.setChecked(False)
            self.button_group.setExclusive(True)
        
        # Update button states
        self.prev_btn.setEnabled(self.current_index > 0)
        
        is_last = self.current_index == len(self.questions) - 1
        if is_last:
            self.next_btn.setText("Submit ✓")
            self.next_btn.setStyleSheet("""
                background-color: #27ae60; color: white; border: none;
                border-radius: 5px; padding: 12px 24px; font-size: 14px;
                margin: 20px 10px; font-weight: bold;
            """)
        else:
            self.next_btn.setText("Next ➡")
            self.next_btn.setStyleSheet("""
                background-color: #3498db; color: white; border: none;
                border-radius: 5px; padding: 12px 24px; font-size: 14px;
                margin: 20px 10px; font-weight: bold;
            """)
    
    def next_question(self):
        """Go to next question or submit quiz."""
        # Save current answer
        q_id = self.questions[self.current_index][0]
        selected_id = self.button_group.checkedId()
        
        if selected_id >= 0:
            answer = ['A', 'B', 'C', 'D'][selected_id]
            self.answers[q_id] = answer
        
        # Check if this is the last question
        if self.current_index == len(self.questions) - 1:
            # Submit quiz
            if len(self.answers) < len(self.questions):
                unanswered = len(self.questions) - len(self.answers)
                reply = QMessageBox.question(
                    self, "Unanswered Questions",
                    f"You have {unanswered} unanswered question(s).\n\n"
                    "Submit anyway?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            self.submit_quiz()
        else:
            # Go to next question
            self.current_index += 1
            self.display_question()
    
    def previous_question(self):
        """Go to previous question."""
        if self.current_index > 0:
            # Save current answer
            q_id = self.questions[self.current_index][0]
            selected_id = self.button_group.checkedId()
            
            if selected_id >= 0:
                answer = ['A', 'B', 'C', 'D'][selected_id]
                self.answers[q_id] = answer
            
            self.current_index -= 1
            self.display_question()
    
    def submit_quiz(self):
        """Submit the quiz and emit results."""
        print(f"📝 Quiz submitted with {len(self.answers)} answers")
        
        # Build results data
        results = {
            'category_id': self.category_id,
            'category_name': self.category_name,
            'questions': self.questions,
            'answers': self.answers
        }
        
        self.quiz_completed.emit(results)
    
    def on_back_clicked(self):
        """Handle back button click."""
        if self.answers:
            reply = QMessageBox.question(
                self, "Quit Quiz",
                "Are you sure you want to quit?\n\nYour progress will be lost.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        self.back_clicked.emit()
