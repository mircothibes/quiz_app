from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal


class DashboardWidget(QWidget):
    """Main dashboard with navigation buttons."""
    
    # Signals for navigation
    browse_categories_clicked = pyqtSignal()
    manage_questions_clicked = pyqtSignal()
    logout_clicked = pyqtSignal()
    
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dashboard interface."""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Header section
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Navigation buttons section
        nav_section = self.create_navigation()
        main_layout.addWidget(nav_section)
        
        # Footer
        main_layout.addStretch()
        
    def create_header(self):
        """Create header with welcome message."""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9
                );
                border-radius: 10px;
                padding: 20px;
                margin: 20px;
            }
        """)
        
        layout = QVBoxLayout()
        header_frame.setLayout(layout)
        
        # Welcome message
        welcome_label = QLabel(f"👋 Welcome back, {self.username}!")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: white;
        """)
        layout.addWidget(welcome_label)
        
        # Subtitle
        subtitle = QLabel("What would you like to do today?")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: #ecf0f1;
            margin-top: 5px;
        """)
        layout.addWidget(subtitle)
        
        return header_frame
    
    def create_navigation(self):
        """Create navigation button grid."""
        nav_widget = QWidget()
        layout = QVBoxLayout()
        nav_widget.setLayout(layout)
        
        # Title
        title = QLabel("📍 Navigation")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            margin: 20px 20px 10px 20px;
        """)
        layout.addWidget(title)
        
        # Button container
        button_layout = QVBoxLayout()
        button_layout.setSpacing(15)
        
        # Browse Categories button
        browse_btn = self.create_nav_button(
            "📚 Browse Quiz Categories",
            "Explore available quiz topics and start a quiz",
            "#27ae60"
        )
        browse_btn.clicked.connect(self.browse_categories_clicked.emit)
        button_layout.addWidget(browse_btn)
        
        # Manage Questions button
        manage_btn = self.create_nav_button(
            "➕ Manage Questions",
            "Add, edit, or delete quiz questions (Admin)",
            "#f39c12"
        )
        manage_btn.clicked.connect(self.manage_questions_clicked.emit)
        button_layout.addWidget(manage_btn)
        
        # Logout button
        logout_btn = self.create_nav_button(
            "🚪 Logout",
            "Sign out of your account",
            "#e74c3c"
        )
        logout_btn.clicked.connect(self.logout_clicked.emit)
        button_layout.addWidget(logout_btn)
        
        # Add button layout to main layout
        button_container = QWidget()
        button_container.setLayout(button_layout)
        button_container.setStyleSheet("margin: 0px 40px;")
        layout.addWidget(button_container)
        
        return nav_widget
    
    def create_nav_button(self, title, description, color):
        """Create a styled navigation button.
        
        Args:
            title (str): Button title
            description (str): Button description
            color (str): Background color
        
        Returns:
            QPushButton: Styled button
        """
        btn = QPushButton(f"{title}\n{description}")
        btn.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: 20px;
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 0.8)};
            }}
        """)
        btn.setCursor(Qt.PointingHandCursor)
        return btn
    
    def darken_color(self, hex_color, factor=0.9):
        """Darken a hex color by a factor.
        
        Args:
            hex_color (str): Hex color like "#3498db"
            factor (float): Darkening factor (0.0-1.0)
        
        Returns:
            str: Darkened hex color
        """
        # Remove '#' and convert to RGB
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        
        # Darken
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
