# UI/question_select_panel.py
from PySide6.QtWidgets import (
    QComboBox,
    QPushButton,
    QLabel,
    QMessageBox,
)
from UI.base_panel import PanelFrame


class QuestionSelectPanel(PanelFrame):
    def __init__(self, meta_manager, selector, session, parent=None):
        super().__init__("题库选择", parent)

        self.meta = meta_manager
        self.selector = selector
        self.session = session

        self.type_box = QComboBox()
        self.diff_box = QComboBox()

        self.type_box.addItems(self.meta.get_types())
        self.diff_box.addItems(self.meta.get_difficulties())

        self.status = QLabel("未加载题池")
        self.status.setStyleSheet("color: #666;")

        self.load_btn = QPushButton("加载题池")
        self.hint = QLabel("提示：切换题型 / 难度前，请先点击「下一题」保存当前题；如不作答可直接跳过。")
        self.hint.setStyleSheet("color: #888; font-size: 11px;")
        self.load_btn.clicked.connect(self._load_pool)

        self.layout.addWidget(QLabel("题目类型"))
        self.layout.addWidget(self.type_box)

        self.layout.addWidget(QLabel("难度等级"))
        self.layout.addWidget(self.diff_box)

        self.layout.addSpacing(6)
        self.layout.addWidget(self.load_btn)
        self.layout.addWidget(self.hint)
        self.layout.addWidget(self.status)

        self.layout.addStretch()

    def _load_pool(self):
        if not self.session.can_load_pool():
            QMessageBox.warning(self, "流程错误", "请先创建面试者")
            return

        if self.session.need_save_before_next():
            ret = QMessageBox.question(
                self,
                "未保存提示",
                "当前题目回答结果尚未保存，是否继续切换题池？（将丢失该题记录）",
                QMessageBox.Yes | QMessageBox.No
            )
            if ret != QMessageBox.Yes:
                return

            self.session.abandon_current_question()

        q_type = self.type_box.currentText()
        diff = self.diff_box.currentText()
        seed = f"{q_type}|{diff}"

        self.selector.load_pool(q_type, diff, seed)
        self.status.setText(f"题池已加载：{q_type} / {diff}，题池初始共{self.selector.remaining()}道题目")
        self.session.set_pool_loaded()

