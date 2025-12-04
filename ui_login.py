from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from db import db


class LoginWidget(QWidget):
    """Login form widget."""
    
    # Signal emitted when login is successful
    # Carries user data: (user_id, username)
    login_successful = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the login interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Add some spacing at the top
        layout.addStretch()
        
        # Title
        title = QLabel("🔐 Login")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Please enter your credentials")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: #7f8c8d;
            margin-bottom: 30px;
        """)
        layout.addWidget(subtitle)
        
        # Username input
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setStyleSheet("""
            font-size: 16px;
            padding: 12px;
            border: 2px solid #bdc3c7;
            border-radius: 5px;
            margin: 10px 100px;
        """)
        self.username_input.returnPressed.connect(self.handle_login)
        layout.addWidget(self.username_input)
        
        # Password input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            font-size: 16px;
            padding: 12px;
            border: 2px solid #bdc3c7;
            border-radius: 5px;
            margin: 10px 100px;
        """)
        self.password_input.returnPressed.connect(self.handle_login)
        layout.addWidget(self.password_input)
        
        # Login button
        login_btn = QPushButton("Login")
        login_btn.setStyleSheet("""
            font-size: 16px;
            padding: 12px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            margin: 20px 100px;
            font-weight: bold;
        """)
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)
        
        # Info label (for test credentials)
        info = QLabel("💡 Hint: Try username 'demo' with password 'test123'")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("""
            font-size: 12px;
            color: #95a5a6;
            margin-top: 20px;
        """)
        layout.addWidget(info)
        
        layout.addStretch()
    
    def handle_login(self):
        """Handle login button click."""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        # Validate inputs
        if not username or not password:
            QMessageBox.warning(
                self, 
                "Input Error", 
                "Please enter both username and password."
            )
            return
        
        # Authenticate
        user = db.authenticate_user(username, password)
        
        if user:
            # Success! Emit signal with user data
            self.login_successful.emit(user)
        else:
            # Failed
            QMessageBox.critical(
                self,
                "Login Failed",
                "Invalid username or password.\n\nPlease try again."
            )
            # Clear password field
            self.password_input.clear()
            self.password_input.setFocus()
