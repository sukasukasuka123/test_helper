# UI/import_panel.py
# 题库导入面板
from PySide6.QtWidgets import (
    QPushButton,
    QLabel,
    QFileDialog
)
from UI.base_panel import PanelFrame


class QuestionImportPanel(PanelFrame):
    def __init__(self, importer):
        super().__init__("📥 题库导入")

        self.importer = importer

        self.status = QLabel("未导入题库")

        btn = QPushButton("从 CSV 导入题库")
        btn.clicked.connect(self._import)

        # 用父类的 layout
        self.layout.addWidget(btn)
        self.layout.addWidget(self.status)

    def _import(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择题库文件",
            "",
            "表格文件 (*.csv *.xlsx *.xls)"
        )
        if not path:
            return

        try:
            result = self.importer.import_from_file(path)
            self.status.setText(f"成功导入 {result['inserted']} 道题")
        except Exception as e:
            self.status.setText(f"导入失败: {e}")
