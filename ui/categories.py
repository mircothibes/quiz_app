import logging
from typing import Any, List, Tuple

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from db import db

logger = logging.getLogger(__name__)


class CategoryWidget(QWidget):
    """Widget to display and select quiz categories."""

    category_selected = pyqtSignal(int, str)  # (category_id, category_name)
    back_clicked = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.categories: List[Tuple[int, str, str]] = []
        self._build_ui()
        # NOTE: We intentionally do not auto-load here.
        # The main window should call load_categories() when navigating to this page.

    def _build_ui(self) -> None:
        layout = QVBoxLayout()
        self.setLayout(layout)

        header_layout = QHBoxLayout()

        self.back_btn = QPushButton("← Back to Dashboard")
        self.back_btn.setStyleSheet(
            """
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
            """
        )
        self.back_btn.clicked.connect(self.back_clicked.emit)
        header_layout.addWidget(self.back_btn)

        header_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet(
            """
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
            """
        )
        self.refresh_btn.clicked.connect(self.load_categories)
        header_layout.addWidget(self.refresh_btn)

        layout.addLayout(header_layout)

        title = QLabel("📚 Select a Quiz Category")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            """
            font-size: 26px;
            font-weight: bold;
            color: #2c3e50;
            margin: 20px;
            """
        )
        layout.addWidget(title)

        subtitle = QLabel("Choose a topic to start your quiz")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            """
            font-size: 14px;
            color: #7f8c8d;
            margin-bottom: 20px;
            """
        )
        layout.addWidget(subtitle)

        self.category_list = QListWidget()
        self.category_list.setStyleSheet(
            """
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
            """
        )
        self.category_list.itemDoubleClicked.connect(self.on_category_double_clicked)
        self.category_list.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.category_list)

        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet(
            """
            font-size: 12px;
            color: #7f8c8d;
            margin: 10px;
            """
        )
        layout.addWidget(self.info_label)

        self.select_btn = QPushButton("Start Quiz with Selected Category")
        self.select_btn.setStyleSheet(
            """
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
            """
        )
        self.select_btn.clicked.connect(self.on_select_category)
        self.select_btn.setEnabled(False)
        layout.addWidget(self.select_btn)

    def _set_loading(self, is_loading: bool) -> None:
        self.refresh_btn.setDisabled(is_loading)
        self.back_btn.setDisabled(is_loading)
        self.select_btn.setDisabled(is_loading or len(self.category_list.selectedItems()) == 0)
        self.category_list.setDisabled(is_loading)

        if is_loading:
            self.info_label.setText("Loading categories...")
            self.info_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")

    def load_categories(self) -> None:
        """Load categories from database and populate list."""
        self._set_loading(True)
        self.category_list.clear()
        self.categories = []

        try:
            if not db.is_connected():
                if not db.connect():
                    self.info_label.setText("❌ Database connection failed.")
                    self.info_label.setStyleSheet("color: #e74c3c; font-size: 14px;")
                    return

            self.categories = db.get_categories()

            if not self.categories:
                self.info_label.setText("⚠️ No categories found. Add some in the admin panel!")
                self.info_label.setStyleSheet("color: #e74c3c; font-size: 14px;")
                return

            for cat_id, name, description in self.categories:
                item = QListWidgetItem()
                item_text = f"{name}\n  {description or 'No description'}"
                item.setText(item_text)
                item.setData(Qt.UserRole, cat_id)
                item.setToolTip(description or "")
                self.category_list.addItem(item)

            self.info_label.setText(f"✅ Found {len(self.categories)} categories")
            self.info_label.setStyleSheet("color: #27ae60; font-size: 12px;")

        except Exception as exc:
            logger.exception("Error loading categories: %s", exc)
            QMessageBox.critical(
                self,
                "Error",
                "An unexpected error occurred while loading categories.\n\nPlease try again.",
            )
            self.info_label.setText("❌ Failed to load categories.")
            self.info_label.setStyleSheet("color: #e74c3c; font-size: 14px;")
        finally:
            self._set_loading(False)

    def on_selection_changed(self) -> None:
        selected_items = self.category_list.selectedItems()
        self.select_btn.setEnabled(len(selected_items) > 0)

    def on_select_category(self) -> None:
        selected_items = self.category_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a category first.")
            return

        item = selected_items[0]
        category_id = int(item.data(Qt.UserRole))
        category_name = item.text().split("\n")[0].strip()

        logger.info("Selected category: %s (id=%s)", category_name, category_id)
        self.category_selected.emit(category_id, category_name)

    def on_category_double_clicked(self, item: QListWidgetItem) -> None:
        category_id = int(item.data(Qt.UserRole))
        category_name = item.text().split("\n")[0].strip()

        logger.info("Double-clicked category: %s (id=%s)", category_name, category_id)
        self.category_selected.emit(category_id, category_name)
