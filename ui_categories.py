from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from db import db


class CategoryWidget(QWidget):
    """Widget to display and select quiz categories."""
    
    # Signals
    category_selected = pyqtSignal(int, str)  # (category_id, category_name)
    back_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.categories = []
        self.init_ui()
        self.load_categories()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Back button
        back_btn = QPushButton("← Back to Dashboard")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        back_btn.clicked.connect(self.back_clicked.emit)
        header_layout.addWidget(back_btn)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        refresh_btn.clicked.connect(self.load_categories)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Title
        title = QLabel("📚 Select a Quiz Category")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 26px;
            font-weight: bold;
            color: #2c3e50;
            margin: 20px;
        """)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Choose a topic to start your quiz")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: #7f8c8d;
            margin-bottom: 20px;
        """)
        layout.addWidget(subtitle)
        
        # Category list
        self.category_list = QListWidget()
        self.category_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                background-color: white;
            }
            QListWidget::item {
                padding: 15px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:hover {
                background-color: #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        self.category_list.itemDoubleClicked.connect(self.on_category_double_clicked)
        layout.addWidget(self.category_list)
        
        # Info label
        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("""
            font-size: 12px;
            color: #7f8c8d;
            margin: 10px;
        """)
        layout.addWidget(self.info_label)
        
        # Select button
        select_btn = QPushButton("Start Quiz with Selected Category")
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                margin: 10px 40px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        select_btn.clicked.connect(self.on_select_category)
        layout.addWidget(select_btn)
        self.select_btn = select_btn
        self.select_btn.setEnabled(False)  # Disabled until selection
        
        # Connect selection change
        self.category_list.itemSelectionChanged.connect(self.on_selection_changed)
    
    def load_categories(self):
        """Load categories from database and populate list."""
        self.category_list.clear()
        self.categories = db.get_categories()
        
        if not self.categories:
            self.info_label.setText("⚠️ No categories found. Add some in the admin panel!")
            self.info_label.setStyleSheet("color: #e74c3c; font-size: 14px;")
            return
        
        # Populate list
        for cat_id, name, description in self.categories:
            item = QListWidgetItem()
            
            # Format: Name (bold) + description
            item_text = f"{name}\n  {description or 'No description'}"
            item.setText(item_text)
            
            # Store category ID in item data
            item.setData(Qt.UserRole, cat_id)
            
            self.category_list.addItem(item)
        
        self.info_label.setText(f"✅ Found {len(self.categories)} categories")
        self.info_label.setStyleSheet("color: #27ae60; font-size: 12px;")
    
    def on_selection_changed(self):
        """Handle category selection change."""
        selected_items = self.category_list.selectedItems()
        self.select_btn.setEnabled(len(selected_items) > 0)
    
    def on_select_category(self):
        """Handle 'Select Category' button click."""
        selected_items = self.category_list.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a category first.")
            return
        
        item = selected_items[0]
        category_id = item.data(Qt.UserRole)
        category_name = item.text().split('\n')[0]  # Get first line (name)
        
        print(f"✅ Selected category: {category_name} (ID: {category_id})")
        self.category_selected.emit(category_id, category_name)
    
    def on_category_double_clicked(self, item):
        """Handle double-click on a category (quick select)."""
        category_id = item.data(Qt.UserRole)
        category_name = item.text().split('\n')[0]
        
        print(f"✅ Double-clicked category: {category_name} (ID: {category_id})")
        self.category_selected.emit(category_id, category_name)
