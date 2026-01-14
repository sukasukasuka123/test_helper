# UI/interviewee_panel.py
# 面试者信息填写
from PySide6.QtWidgets import  QVBoxLayout, QLineEdit, QPushButton, QLabel
from UI.base_panel import PanelFrame
class IntervieweePanel(PanelFrame):
    def __init__(self, interviewee_manager, session):
        super().__init__()
        self.manager = interviewee_manager
        self.session = session
        self.interviewee_id = None

        self.name = QLineEdit()
        self.name.setPlaceholderText("姓名")
        self.email = QLineEdit()
        self.email.setPlaceholderText("邮箱")
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("电话")

        self.status = QLabel("未创建")

        submit = QPushButton("创建面试者")
        submit.clicked.connect(self._submit)

        for w in (self.name, self.email, self.phone, submit, self.status):
            self.layout.addWidget(w)

    def _submit(self):
        info = {
            "name": self.name.text(),
            "email": self.email.text(),
            "phone": self.phone.text()
        }
        self.interviewee_id = self.manager.create_interviewee(info)
        self.session.set_interviewee_created()
        self.status.setText(f"面试者已创建 ID={self.interviewee_id}")

    def get_interviewee_id(self):
        return self.interviewee_id