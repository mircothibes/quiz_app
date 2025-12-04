import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, 
    QVBoxLayout, QLabel
)
from PyQt5.QtCore import Qt

class QuizApp(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Window properties
        self.setWindowTitle("Advanced Quiz App")
        self.setGeometry(100, 100, 800, 600)  # x, y, width, height
        
        # Central widget (required for QMainWindow)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Title label
        title_label = QLabel("🎯 Welcome to the Advanced Quiz App")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 28px; 
            font-weight: bold; 
            color: #2c3e50;
            margin: 20px;
        """)
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Your journey to mastering Python, SQL, and Docker starts here")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            font-size: 14px; 
            color: #7f8c8d;
            margin-bottom: 40px;
        """)
        layout.addWidget(subtitle_label)
        
        # Database status (placeholder)
        self.status_label = QLabel("📊 Database Status: Not Connected")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            font-size: 16px;
            padding: 15px;
            background-color: #f39c12;
            color: white;
            border-radius: 5px;
            margin: 20px 40px;
        """)
        layout.addWidget(self.status_label)
        
        # Add stretch to push everything to the top
        layout.addStretch()


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    window = QuizApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
