# UI/export_panel.py
from PySide6.QtWidgets import (
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox
)
from UI.base_panel import PanelFrame


class ExportPanel(PanelFrame):
    def __init__(self, exporter):
        super().__init__("📤 数据导出")

        self.exporter = exporter

        self.status = QLabel("未导出数据")
        self.status.setStyleSheet("color: #666;")

        export_all_btn = QPushButton("导出所有面试记录")
        export_all_btn.clicked.connect(self._export_all)

        self.layout.addWidget(export_all_btn)
        self.layout.addWidget(self.status)

    def _export_all(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "保存导出文件",
            "面试记录.xlsx",
            "Excel 文件 (*.xlsx)"
        )

        if not path:
            return

        try:
            count = self.exporter.export_all_records(path)
            self.status.setText(f"成功导出 {count} 条记录")
            QMessageBox.information(
                self,
                "导出成功",
                f"已导出 {count} 条记录到:\n{path}"
            )
        except Exception as e:
            self.status.setText(f"导出失败: {e}")
            QMessageBox.critical(
                self,
                "导出失败",
                f"导出过程中发生错误:\n{str(e)}"
            )