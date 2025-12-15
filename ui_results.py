from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal


class ResultsWidget(QWidget):
    """Widget to display quiz results."""
    
    # Signals
    retake_quiz_clicked = pyqtSignal(int, str)  # (category_id, category_name)
    back_to_dashboard_clicked = pyqtSignal()
    back_to_categories_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI."""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Score header container (will be populated dynamically)
        self.score_container = QWidget()
        main_layout.addWidget(self.score_container)
        
        # Scrollable results area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout()
        self.results_widget.setLayout(self.results_layout)
        
        scroll.setWidget(self.results_widget)
        main_layout.addWidget(scroll)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        retake_btn = QPushButton("🔄 Retake Quiz")
        retake_btn.setStyleSheet("""
            background-color: #f39c12; color: white; border: none;
            border-radius: 5px; padding: 12px 24px; font-size: 14px;
            font-weight: bold; margin: 10px;
        """)
        retake_btn.clicked.connect(self.on_retake_clicked)
        buttons_layout.addWidget(retake_btn)
        self.retake_btn = retake_btn
        
        categories_btn = QPushButton("📚 Browse Categories")
        categories_btn.setStyleSheet("""
            background-color: #3498db; color: white; border: none;
            border-radius: 5px; padding: 12px 24px; font-size: 14px;
            font-weight: bold; margin: 10px;
        """)
        categories_btn.clicked.connect(self.back_to_categories_clicked.emit)
        buttons_layout.addWidget(categories_btn)
        
        dashboard_btn = QPushButton("🏠 Dashboard")
        dashboard_btn.setStyleSheet("""
            background-color: #95a5a6; color: white; border: none;
            border-radius: 5px; padding: 12px 24px; font-size: 14px;
            margin: 10px;
        """)
        dashboard_btn.clicked.connect(self.back_to_dashboard_clicked.emit)
        buttons_layout.addWidget(dashboard_btn)
        
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)
    
    def display_results(self, results):
        """Display quiz results.
        
        Args:
            results (dict): Contains category_id, category_name, questions, answers
        """
        self.results_data = results
        
        # Calculate score
        score_data = self.calculate_score(results)
        
        # Display score header
        self.display_score_header(score_data, results['category_name'])
        
        # Display question breakdown
        self.display_breakdown(score_data['breakdown'])
    
    def calculate_score(self, results):
        """Calculate quiz score.
        
        Args:
            results (dict): Quiz results data
        
        Returns:
            dict: Score data with breakdown
        """
        questions = results['questions']
        answers = results['answers']
        
        breakdown = []
        correct_count = 0
        
        for q in questions:
            q_id, q_text, correct_answer, opt_a, opt_b, opt_c, opt_d = q
            
            user_answer = answers.get(q_id, None)
            is_correct = user_answer == correct_answer
            
            if is_correct:
                correct_count += 1
            
            breakdown.append({
                'question': q_text,
                'options': {'A': opt_a, 'B': opt_b, 'C': opt_c, 'D': opt_d},
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct
            })
        
        total = len(questions)
        percentage = (correct_count / total * 100) if total > 0 else 0
        
        return {
            'correct': correct_count,
            'total': total,
            'percentage': percentage,
            'breakdown': breakdown
        }
    
    def display_score_header(self, score_data, category_name):
        """Display score header.
        
        Args:
            score_data (dict): Calculated scores
            category_name (str): Quiz category name
        """
        # Clear existing
        if self.score_container.layout():
            QWidget().setLayout(self.score_container.layout())
        
        layout = QVBoxLayout()
        self.score_container.setLayout(layout)
        
        # Title
        title = QLabel(f"📊 Results: {category_name}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 24px; font-weight: bold; color: #2c3e50; margin: 20px;
        """)
        layout.addWidget(title)
        
        # Score card
        score_frame = QFrame()
        percentage = score_data['percentage']
        
        # Color based on score
        if percentage >= 80:
            color = "#27ae60"  # Green
            emoji = "🎉"
            message = "Excellent!"
        elif percentage >= 60:
            color = "#f39c12"  # Orange
            emoji = "👍"
            message = "Good job!"
        else:
            color = "#e74c3c"  # Red
            emoji = "📖"
            message = "Keep practicing!"
        
        score_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                padding: 30px;
                margin: 10px 80px;
            }}
        """)
        
        score_layout = QVBoxLayout()
        score_frame.setLayout(score_layout)
        
        # Emoji and message
        emoji_label = QLabel(f"{emoji} {message}")
        emoji_label.setAlignment(Qt.AlignCenter)
        emoji_label.setStyleSheet("font-size: 22px; color: white; font-weight: bold;")
        score_layout.addWidget(emoji_label)
        
        # Score
        score_label = QLabel(f"{score_data['correct']} / {score_data['total']}")
        score_label.setAlignment(Qt.AlignCenter)
        score_label.setStyleSheet("font-size: 48px; color: white; font-weight: bold; margin: 10px;")
        score_layout.addWidget(score_label)
        
        # Percentage
        percent_label = QLabel(f"{percentage:.1f}%")
        percent_label.setAlignment(Qt.AlignCenter)
        percent_label.setStyleSheet("font-size: 28px; color: white;")
        score_layout.addWidget(percent_label)
        
        layout.addWidget(score_frame)
    
    def display_breakdown(self, breakdown):
        """Display question-by-question breakdown.
        
        Args:
            breakdown (list): List of question result dicts
        """
        # Clear existing
        for i in reversed(range(self.results_layout.count())): 
            self.results_layout.itemAt(i).widget().setParent(None)
        
        # Title
        title = QLabel("📝 Question Breakdown")
        title.setStyleSheet("""
            font-size: 20px; font-weight: bold; color: #2c3e50; 
            margin: 20px 20px 10px 20px;
        """)
        self.results_layout.addWidget(title)
        
        # Each question
        for i, item in enumerate(breakdown, 1):
            q_frame = self.create_question_card(i, item)
            self.results_layout.addWidget(q_frame)
        
        self.results_layout.addStretch()
    
    def create_question_card(self, num, item):
        """Create a card for one question result.
        
        Args:
            num (int): Question number
            item (dict): Question result data
        
        Returns:
            QFrame: Question card widget
        """
        frame = QFrame()
        
        # Color based on correctness
        if item['is_correct']:
            border_color = "#27ae60"
            icon = "✅"
        elif item['user_answer'] is None:
            border_color = "#95a5a6"
            icon = "⊘"
        else:
            border_color = "#e74c3c"
            icon = "❌"
        
        frame.setStyleSheet(f"""
            QFrame {{
                border-left: 5px solid {border_color};
                background-color: #ecf0f1;
                border-radius: 5px;
                padding: 15px;
                margin: 5px 20px;
            }}
        """)
        
        layout = QVBoxLayout()
        frame.setLayout(layout)
        
        # Question text
        q_label = QLabel(f"{icon} <b>Question {num}:</b> {item['question']}")
        q_label.setWordWrap(True)
        q_label.setStyleSheet("font-size: 14px; color: #2c3e50;")
        layout.addWidget(q_label)
        
        # User's answer
        user_ans = item['user_answer']
        if user_ans:
            user_text = item['options'][user_ans]
            user_label = QLabel(f"<b>Your answer:</b> {user_ans}. {user_text}")
            user_label.setStyleSheet(f"color: {border_color}; margin-left: 20px;")
        else:
            user_label = QLabel("<b>Your answer:</b> (Not answered)")
            user_label.setStyleSheet("color: #95a5a6; margin-left: 20px;")
        layout.addWidget(user_label)
        
        # Correct answer (if wrong or skipped)
        if not item['is_correct']:
            correct_ans = item['correct_answer']
            correct_text = item['options'][correct_ans]
            correct_label = QLabel(f"<b>Correct answer:</b> {correct_ans}. {correct_text}")
            correct_label.setStyleSheet("color: #27ae60; margin-left: 20px;")
            layout.addWidget(correct_label)
        
        return frame
    
    def on_retake_clicked(self):
        """Handle retake button click."""
        cat_id = self.results_data['category_id']
        cat_name = self.results_data['category_name']
        self.retake_quiz_clicked.emit(cat_id, cat_name)
