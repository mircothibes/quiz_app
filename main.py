import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QLabel
)
from PyQt5.QtCore import Qt
from db import db
from ui_login import LoginWidget


class QuizApp(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.current_user = None  # Store logged-in user
        self.init_ui()
        self.test_database_connection()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Advanced Quiz App")
        self.setGeometry(100, 100, 800, 600)
        
        # Use QStackedWidget to switch between pages
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Page 0: Login
        self.login_page = LoginWidget()
        self.login_page.login_successful.connect(self.on_login_success)
        self.stack.addWidget(self.login_page)
        
        # Page 1: Dashboard (placeholder for now)
        self.dashboard_page = QLabel("Welcome to Dashboard!")
        self.dashboard_page.setAlignment(Qt.AlignCenter)
        self.dashboard_page.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #27ae60;
        """)
        self.stack.addWidget(self.dashboard_page)
        
        # Start with login page
        self.stack.setCurrentIndex(0)
    
    def test_database_connection(self):
        """Test database connection on startup."""
        if not db.connect():
            # Show error dialog
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Database Error",
                "Could not connect to PostgreSQL database.\n\n"
                "Please ensure Docker is running:\n"
                "  docker compose up -d"
            )
    
    def on_login_success(self, user_data):
        """Called when user logs in successfully.
        
        Args:
            user_data (tuple): (user_id, username)
        """
        user_id, username = user_data
        self.current_user = user_data
        
        # Update dashboard with username
        self.dashboard_page.setText(f"✅ Welcome, {username}!")
        
        # Switch to dashboard
        self.stack.setCurrentIndex(1)
        
        print(f"✅ User {username} (ID: {user_id}) logged in")
    
    def closeEvent(self, event):
        """Called when window is closed."""
        db.disconnect()
        event.accept()


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    window = QuizApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
