# UI/stats_panel.py
# 记录保存
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox
from UI.base_panel import PanelFrame
class StatsPanel(PanelFrame):
    def __init__(self, stats_manager, session):
        super().__init__("面试记录")
        self.stats = stats_manager
        self.session = session

        save_btn = QPushButton("结束面试并保存")
        save_btn.clicked.connect(self._finish)

        self.status = QLabel("未保存")

        self.layout.addWidget(save_btn)
        self.layout.addWidget(self.status)

    def _finish(self):
        self.stats.flush()
        self.session.finish()
        self.status.setText("面试记录已保存")
