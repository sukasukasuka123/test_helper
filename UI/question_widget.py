# UI/question_widget.py
from UI.base_panel import PanelFrame
from PySide6.QtWidgets import (
    QLabel,
    QTextEdit,
    QSpinBox
)
from PySide6.QtGui import QFont


class QuestionWidget(PanelFrame):
    def __init__(self, q_type, difficulty, content, answer):
        super().__init__()

        self.q_type = q_type
        self.difficulty = difficulty
        self.content = content
        self.answer = answer

        # ===== 题目信息 =====
        title = QLabel(f"[{q_type} | {difficulty}]")
        title.setStyleSheet("color: #555; font-weight: bold;")
        self.layout.addWidget(title)

        question_label = QLabel(content)
        question_label.setWordWrap(True)
        question_label.setStyleSheet("font-size: 14px;")
        self.layout.addWidget(question_label)

        # ===== 评分 =====
        score_label = QLabel("评分（0-10）")
        self.layout.addWidget(score_label)

        self.score_box = QSpinBox()
        self.score_box.setRange(0, 10)
        self.layout.addWidget(self.score_box)

        # ===== 备注 =====
        self.remark = QTextEdit()
        self.remark.setPlaceholderText("评分说明 / 备注")
        self.remark.setFixedHeight(80)
        self.layout.addWidget(self.remark)

        # ===== 标准答案（只读）=====
        answer_title = QLabel("参考答案")
        answer_title.setStyleSheet("color: #888; margin-top: 6px;")
        self.layout.addWidget(answer_title)

        self.answer_view = QTextEdit()
        self.answer_view.setReadOnly(True)
        self.answer_view.setText(answer)
        self.answer_view.setFixedHeight(80)
        self.answer_view.setStyleSheet("""
            QTextEdit {
                background-color: #f7f7f7;
                color: #555;
                border: 1px solid #ddd;
            }
        """)
        self.layout.addWidget(self.answer_view)

    # ===== 对外接口 =====
    def get_score(self):
        return self.score_box.value()

    def get_snapshot(self):
        return {
            "type": self.q_type,
            "difficulty": self.difficulty,
            "content": self.content,
            "answer": self.answer,
            "remark": self.remark.toPlainText()
        }
