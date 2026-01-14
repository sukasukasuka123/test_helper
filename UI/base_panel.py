from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class PanelFrame(QFrame):
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)

        self.setObjectName("PanelFrame")

        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)

        self.setStyleSheet("""
        QFrame#PanelFrame {
            border: 1px solid #C0C0C0;
            border-radius: 8px;
        }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(8)

        if title:
            self.title_label = QLabel(title)
            self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.title_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 13px;
            }
            """)
            self.layout.addWidget(self.title_label)
        else:
            self.title_label = None
