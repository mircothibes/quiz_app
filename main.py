import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QLabel
)
from PyQt5.QtCore import Qt
from db import db
from ui_login import LoginWidget
from ui_dashboard import DashboardWidget
from ui_categories import CategoryWidget


class QuizApp(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.dashboard_page = None
        self.init_ui()
        self.test_database_connection()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Advanced Quiz App")
        self.setGeometry(100, 100, 900, 700)
        
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Page 0: Login
        self.login_page = LoginWidget()
        self.login_page.login_successful.connect(self.on_login_success)
        self.stack.addWidget(self.login_page)
        
        # Page 2: Categories (UPDATED - real widget now!)
        self.categories_page = CategoryWidget()
        self.categories_page.back_clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.categories_page.category_selected.connect(self.on_category_selected)
        self.stack.addWidget(self.categories_page)
        
        # Page 3: Quiz (placeholder)
        self.quiz_page = self.create_placeholder("🎯 Quiz", "Coming soon...")
        self.stack.addWidget(self.quiz_page)
        
        # Page 4: Admin (placeholder)
        self.admin_page = self.create_placeholder("➕ Admin", "Coming soon...")
        self.stack.addWidget(self.admin_page)
        
        self.stack.setCurrentIndex(0)
    
    def create_placeholder(self, title, message):
        """Create a placeholder page."""
        placeholder = QLabel(f"{title}\n\n{message}")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("font-size: 24px; color: #7f8c8d;")
        return placeholder
    
    def test_database_connection(self):
        """Test database connection."""
        if not db.connect():
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, "Database Error",
                "Could not connect to PostgreSQL.\n\nEnsure Docker is running."
            )
    
    def on_login_success(self, user_data):
        """Handle successful login."""
        user_id, username = user_data
        self.current_user = user_data
        
        if self.dashboard_page:
            self.stack.removeWidget(self.dashboard_page)
        
        self.dashboard_page = DashboardWidget(username)
        self.dashboard_page.browse_categories_clicked.connect(self.show_categories)
        self.dashboard_page.manage_questions_clicked.connect(self.show_admin)
        self.dashboard_page.logout_clicked.connect(self.logout)
        
        self.stack.insertWidget(1, self.dashboard_page)
        self.stack.setCurrentIndex(1)
        
        print(f"✅ User {username} logged in")
    
    def show_categories(self):
        """Navigate to categories page."""
        self.categories_page.load_categories()  # Refresh data
        self.stack.setCurrentIndex(2)
    
    def show_admin(self):
        """Navigate to admin page."""
        self.stack.setCurrentIndex(4)
    
    def on_category_selected(self, category_id, category_name):
        """Handle category selection.
        
        Args:
            category_id (int): Selected category ID
            category_name (str): Selected category name
        """
        print(f"📚 Starting quiz for category: {category_name} (ID: {category_id})")
        # TODO: Load questions and show quiz page
        self.stack.setCurrentIndex(3)  # Show quiz placeholder for now
    
    def logout(self):
        """Log out."""
        self.current_user = None
        self.stack.setCurrentIndex(0)
        print("🚪 User logged out")
    
    def closeEvent(self, event):
        """Handle window close."""
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
