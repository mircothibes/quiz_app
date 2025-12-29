from __future__ import annotations

import logging
from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from db import db

logger = logging.getLogger(__name__)


class AdminWidget(QWidget):
    """Admin panel to manage quiz questions.

    Features:
    - List questions (with category)
    - Create new question
    - Edit selected question
    - Delete selected question
    """

    back_clicked = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        self._selected_question_id: Optional[int] = None

        self._category_combo: Optional[QComboBox] = None
        self._question_text: Optional[QTextEdit] = None
        self._opt_a: Optional[QLineEdit] = None
        self._opt_b: Optional[QLineEdit] = None
        self._opt_c: Optional[QLineEdit] = None
        self._opt_d: Optional[QLineEdit] = None
        self._correct_combo: Optional[QComboBox] = None

        self._table: Optional[QTableWidget] = None
        self._status: Optional[QLabel] = None

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Build the admin UI layout."""
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # Top bar
        top = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(self.back_clicked.emit)
        back_btn.setStyleSheet(
            "padding: 8px 14px; border-radius: 6px; background: #95a5a6; color: white;"
        )
        top.addWidget(back_btn)

        title = QLabel("🛠️ Admin — Manage Questions")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        top.addWidget(title)
        top.addStretch()
        root.addLayout(top)

        # Main content
        content = QHBoxLayout()
        content.setSpacing(12)
        root.addLayout(content)

        # Left: table
        table_frame = QFrame()
        table_frame.setStyleSheet("QFrame { background: white; border-radius: 10px; }")
        table_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.setSpacing(10)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["ID", "Category", "Question", "Correct"])
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.itemSelectionChanged.connect(self._on_row_selected)

        table_layout.addWidget(self._table)

        self._status = QLabel("")
        self._status.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        table_layout.addWidget(self._status)

        content.addWidget(table_frame, 3)

        # Right: form
        form_frame = QFrame()
        form_frame.setStyleSheet("QFrame { background: white; border-radius: 10px; }")
        form_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(12, 12, 12, 12)
        form_layout.setSpacing(10)

        form_title = QLabel("Question Editor")
        form_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        form_layout.addWidget(form_title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        self._category_combo = QComboBox()
        self._correct_combo = QComboBox()
        self._correct_combo.addItems(["A", "B", "C", "D"])

        self._question_text = QTextEdit()
        self._question_text.setPlaceholderText("Type the question text here...")
        self._question_text.setFixedHeight(120)

        self._opt_a = QLineEdit()
        self._opt_b = QLineEdit()
        self._opt_c = QLineEdit()
        self._opt_d = QLineEdit()

        self._opt_a.setPlaceholderText("Option A")
        self._opt_b.setPlaceholderText("Option B")
        self._opt_c.setPlaceholderText("Option C")
        self._opt_d.setPlaceholderText("Option D")

        grid.addWidget(QLabel("Category"), 0, 0)
        grid.addWidget(self._category_combo, 0, 1)

        grid.addWidget(QLabel("Correct"), 1, 0)
        grid.addWidget(self._correct_combo, 1, 1)

        grid.addWidget(QLabel("Question"), 2, 0, Qt.AlignTop)
        grid.addWidget(self._question_text, 2, 1)

        grid.addWidget(QLabel("A"), 3, 0)
        grid.addWidget(self._opt_a, 3, 1)

        grid.addWidget(QLabel("B"), 4, 0)
        grid.addWidget(self._opt_b, 4, 1)

        grid.addWidget(QLabel("C"), 5, 0)
        grid.addWidget(self._opt_c, 5, 1)

        grid.addWidget(QLabel("D"), 6, 0)
        grid.addWidget(self._opt_d, 6, 1)

        form_layout.addLayout(grid)

        btn_row = QHBoxLayout()
        new_btn = QPushButton("New")
        save_btn = QPushButton("Save")
        del_btn = QPushButton("Delete")

        new_btn.clicked.connect(self._new_question)
        save_btn.clicked.connect(self._save_question)
        del_btn.clicked.connect(self._delete_question)

        new_btn.setStyleSheet("padding: 10px; border-radius: 8px; background: #3498db; color: white;")
        save_btn.setStyleSheet("padding: 10px; border-radius: 8px; background: #27ae60; color: white; font-weight: bold;")
        del_btn.setStyleSheet("padding: 10px; border-radius: 8px; background: #e74c3c; color: white;")

        btn_row.addWidget(new_btn)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(del_btn)
        form_layout.addLayout(btn_row)

        form_layout.addStretch()
        content.addWidget(form_frame, 2)

    def refresh(self) -> None:
        """Reload categories and questions from the database."""
        if not db.is_connected() and not db.connect():
            QMessageBox.critical(self, "Database Error", "Could not connect to PostgreSQL.")
            return

        self._load_categories()
        self._load_questions()
        self._new_question()

    def _load_categories(self) -> None:
        """Fill the category combo."""
        assert self._category_combo is not None

        self._category_combo.clear()
        categories = db.get_categories()
        for cat_id, name, _desc in categories:
            self._category_combo.addItem(name, cat_id)

    def _load_questions(self) -> None:
        """Fill the questions table."""
        assert self._table is not None
        assert self._status is not None

        rows = db.list_questions(limit=200)

        self._table.setRowCount(0)
        for q_id, category_name, question_text, correct in rows:
            r = self._table.rowCount()
            self._table.insertRow(r)
            self._table.setItem(r, 0, QTableWidgetItem(str(q_id)))
            self._table.setItem(r, 1, QTableWidgetItem(category_name))
            self._table.setItem(r, 2, QTableWidgetItem(question_text))
            self._table.setItem(r, 3, QTableWidgetItem(correct))

        self._table.resizeColumnsToContents()
        self._status.setText(f"Loaded {len(rows)} question(s).")

    def _on_row_selected(self) -> None:
        """Load selected row into the editor form."""
        assert self._table is not None
        if not self._table.selectedItems():
            return

        row = self._table.currentRow()
        q_id_item = self._table.item(row, 0)
        if q_id_item is None:
            return

        q_id = int(q_id_item.text())
        full = db.get_question_by_id(q_id)
        if full is None:
            return

        (
            question_id,
            category_id,
            question_text,
            correct_answer,
            opt_a,
            opt_b,
            opt_c,
            opt_d,
        ) = full

        self._selected_question_id = int(question_id)

        assert self._category_combo is not None
        assert self._question_text is not None
        assert self._correct_combo is not None
        assert self._opt_a is not None
        assert self._opt_b is not None
        assert self._opt_c is not None
        assert self._opt_d is not None

        # Set category
        idx = self._category_combo.findData(int(category_id))
        if idx >= 0:
            self._category_combo.setCurrentIndex(idx)

        self._question_text.setPlainText(str(question_text))
        self._correct_combo.setCurrentText(str(correct_answer).strip().upper())

        self._opt_a.setText(str(opt_a))
        self._opt_b.setText(str(opt_b))
        self._opt_c.setText(str(opt_c))
        self._opt_d.setText(str(opt_d))

    def _new_question(self) -> None:
        """Clear the form for creating a new question."""
        self._selected_question_id = None

        assert self._question_text is not None
        assert self._opt_a is not None
        assert self._opt_b is not None
        assert self._opt_c is not None
        assert self._opt_d is not None
        assert self._correct_combo is not None

        self._question_text.clear()
        self._opt_a.clear()
        self._opt_b.clear()
        self._opt_c.clear()
        self._opt_d.clear()
        self._correct_combo.setCurrentText("A")

    def _save_question(self) -> None:
        """Insert or update a question based on selection."""
        assert self._category_combo is not None
        assert self._question_text is not None
        assert self._opt_a is not None
        assert self._opt_b is not None
        assert self._opt_c is not None
        assert self._opt_d is not None
        assert self._correct_combo is not None

        category_id = int(self._category_combo.currentData())
        q_text = self._question_text.toPlainText().strip()
        opt_a = self._opt_a.text().strip()
        opt_b = self._opt_b.text().strip()
        opt_c = self._opt_c.text().strip()
        opt_d = self._opt_d.text().strip()
        correct = self._correct_combo.currentText().strip().upper()

        if not q_text or not opt_a or not opt_b or not opt_c or not opt_d:
            QMessageBox.warning(self, "Validation", "Please fill question text and all options (A-D).")
            return

        if self._selected_question_id is None:
            new_id = db.create_question(category_id, q_text, correct, opt_a, opt_b, opt_c, opt_d)
            if new_id is None:
                QMessageBox.critical(self, "Error", "Could not create question.")
                return
            logger.info("Created question id=%s", new_id)
        else:
            ok = db.update_question(self._selected_question_id, category_id, q_text, correct, opt_a, opt_b, opt_c, opt_d)
            if not ok:
                QMessageBox.critical(self, "Error", "Could not update question.")
                return
            logger.info("Updated question id=%s", self._selected_question_id)

        self.refresh()

    def _delete_question(self) -> None:
        """Delete selected question."""
        if self._selected_question_id is None:
            QMessageBox.information(self, "Delete", "Select a question first.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this question?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        ok = db.delete_question(self._selected_question_id)
        if not ok:
            QMessageBox.critical(self, "Error", "Could not delete question.")
            return

        logger.info("Deleted question id=%s", self._selected_question_id)
        self.refresh()

