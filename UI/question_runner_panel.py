from PySide6.QtWidgets import (
    QVBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
    QWidget
)
from UI.base_panel import PanelFrame


class QuestionRunnerPanel(PanelFrame):
    def __init__(self, selector, question_widget_cls, session, parent=None):
        super().__init__("抽题区", parent)

        self.selector = selector
        self.QuestionWidgetCls = question_widget_cls
        self.session = session

        self.current_question_id = None
        self.current_widget = None
        self.auto_save_hook = None

        # 内容容器（关键）
        self.content_container = QWidget(self)
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        self.next_btn = QPushButton("下一题")
        self.next_btn.clicked.connect(self._next)

        self.layout.addWidget(self.next_btn)
        self.layout.addWidget(self.content_container)

    def _clear_content(self):
        """安全清空内容区"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        self.current_widget = None
        self.current_question_id = None

    def _next(self):
        if not self.session.can_next_question():
            QMessageBox.warning(self, "流程错误", "请先创建面试者")
            return

        # 如果有未保存题，自动保存
        if self.session.need_save_before_next():
            result = self.get_current_result()
            if result and self.auto_save_hook:
                self.auto_save_hook(result)
                self.session.mark_question_saved()

        self._clear_content()

        data = self.selector.next_question()
        if not data:
            self.content_layout.addWidget(QLabel("题目已抽完"))
            return

        qid, q_type, diff, content, answer = data
        self.current_question_id = qid

        widget = self.QuestionWidgetCls(q_type, diff, content, answer)
        self.current_widget = widget
        self.content_layout.addWidget(widget)

        self.session.start_question()

    def get_current_result(self):
        if not self.current_widget:
            return None

        return (
            self.current_question_id,
            self.current_widget.get_score(),
            self.current_widget.get_snapshot()
        )

