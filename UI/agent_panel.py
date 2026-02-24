# UI/agent_panel.py
"""
Agent 交互面板
提供用户与 Agent 的聊天界面
"""
from PySide6.QtWidgets import (
    QPushButton,
    QLineEdit,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QWidget,
    QFrame
)
from PySide6.QtCore import Qt, Signal
from UI.base_panel import PanelFrame


class MessageBubble(QFrame):
    """消息气泡组件"""

    def __init__(self, role: str, content: str, parent=None):
        super().__init__(parent)

        self.role = role
        self.content = content

        self.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)

        # 角色标签
        role_label = QLabel(f"{'agent助手' if role == 'assistant' else '你'}")
        role_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 11px;
                color: #666;
            }
        """)
        layout.addWidget(role_label)

        # 消息内容
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                padding: 4px;
                border: 1px solid #000;
                color: #666;
            }
        """)
        layout.addWidget(content_label)

        # 样式
        if role == "assistant":
            self.setStyleSheet("""
                QFrame {
                    background-color: #F0F0F0;
                    border-radius: 8px;
                    border: 1px solid #000;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #E3F2FD;
                    border-radius: 8px;
                    border: 1px solid #000;
                }
            """)


class ChatHistoryWidget(QWidget):
    """聊天历史显示组件"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        self.layout.addStretch()

    def add_message(self, role: str, content: str):
        """添加消息气泡"""
        bubble = MessageBubble(role, content)

        # 移除 stretch
        if self.layout.count() > 0:
            item = self.layout.takeAt(self.layout.count() - 1)

        self.layout.addWidget(bubble)
        self.layout.addStretch()

    def clear_messages(self):
        """清空所有消息"""
        while self.layout.count() > 1:
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()


class AgentPanel(PanelFrame):
    """Agent 主面板"""

    # 定义信号
    message_sent = Signal(str)

    def __init__(self, agent, parent=None):
        super().__init__("AI 助手", parent)

        self.agent = agent

        # ===== 提示信息 =====
        hint_label = QLabel("你可以向助手提问,例如:\n"
                            "  - 统计题库信息\n"
                            "  - 分析面试者 ID=1 的表现\n")
        hint_label.setStyleSheet("""
            QLabel {
                color: #000;
                font-size: 11px;
                background-color: #FFFDE7;
                border: 1px solid #FFF9C4;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        hint_label.setWordWrap(True)
        self.layout.addWidget(hint_label)

        # ===== 聊天历史区域 =====
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background-color: white;
            }
        """)

        self.chat_history = ChatHistoryWidget()
        scroll_area.setWidget(self.chat_history)

        self.layout.addWidget(scroll_area, stretch=1)

        # ===== 工具列表 =====
        tools_label = QLabel("可用工具:")
        tools_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        self.layout.addWidget(tools_label)

        self.tools_display = QLabel("")
        self.tools_display.setStyleSheet("""
            QLabel {
                color: #555;
                font-size: 11px;
                padding: 6px;
                background-color: #F5F5F5;
                border-radius: 4px;
            }
        """)
        self.tools_display.setWordWrap(True)
        self.layout.addWidget(self.tools_display)

        self._update_tools_display()

        # ===== 输入区 =====
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("输入你的问题...")
        self.input_box.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                font-size: 13px;
            }
        """)
        self.input_box.returnPressed.connect(self._send_message)

        send_btn = QPushButton("发送")
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        send_btn.clicked.connect(self._send_message)

        clear_btn = QPushButton("清空")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        clear_btn.clicked.connect(self._clear_conversation)

        input_layout.addWidget(self.input_box, stretch=1)
        input_layout.addWidget(send_btn)
        input_layout.addWidget(clear_btn)

        self.layout.addLayout(input_layout)

    def _update_tools_display(self):
        """更新工具列表显示"""
        # 使用 agent.get_tools() 获取工具对象列表
        tools = self.agent.get_tools()

        if not tools:
            self.tools_display.setText("暂无可用工具")
            return

        tools_text = "\n".join([
            f"  • {tool.name}: {tool.description}"
            for tool in tools
        ])

        self.tools_display.setText(tools_text)

    def _send_message(self):
        """发送消息"""
        user_input = self.input_box.text().strip()

        if not user_input:
            return

        # 显示用户消息
        self.chat_history.add_message("user", user_input)

        # 清空输入框
        self.input_box.clear()

        # 调用 Agent 处理
        try:
            response = self.agent.chat(user_input)
            self.chat_history.add_message("assistant", response)
        except Exception as e:
            error_msg = f"**** 处理失败: {str(e)}"
            self.chat_history.add_message("assistant", error_msg)

        # 发出信号
        self.message_sent.emit(user_input)

    def _clear_conversation(self):
        """清空对话"""
        self.chat_history.clear_messages()
        self.agent.clear_conversation()

        # 显示欢迎消息
        welcome = "————对话已清空,请继续提问!————"
        self.chat_history.add_message("assistant", welcome)