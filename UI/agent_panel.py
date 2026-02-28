# UI/agent_panel.py
"""
Agent 交互面板
提供用户与 Agent 的聊天界面
"""
import markdown
from PySide6.QtWidgets import (
    QPushButton,
    QLineEdit,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QWidget,
    QFrame,
    QDialog,
    QDialogButtonBox,
    QSizePolicy,
    QGraphicsDropShadowEffect, QTextBrowser,
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PySide6.QtGui import QColor, QFont, QIcon
from UI.base_panel import PanelFrame


# ─────────────────────────────────────────────
# 工具弹窗
# ─────────────────────────────────────────────

class ToolsPopup(QDialog):
    """可用工具详情弹窗"""

    def __init__(self, tools: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("可用工具列表")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(420)
        self.setMaximumHeight(560)

        # 外层容器（带圆角阴影）
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)

        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet("""
            QFrame#card {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E0E0E0;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        card.setGraphicsEffect(shadow)
        outer.addWidget(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # ── 标题栏 ──────────────────────────────
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #1A1A2E;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 14, 14)

        title_label = QLabel(f"🛠  可用工具  ({len(tools)} 个)")
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #AAAAAA;
                border: none;
                border-radius: 14px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.15);
                color: #FFFFFF;
            }
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        card_layout.addWidget(header)

        # ── 工具滚动列表 ─────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                width: 6px;
                background: #F5F5F5;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #CCCCCC;
                border-radius: 3px;
                min-height: 20px;
            }
        """)

        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(14, 12, 14, 16)
        content_layout.setSpacing(8)

        if not tools:
            empty = QLabel("暂无可用工具")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #999; font-size: 13px; padding: 20px;")
            content_layout.addWidget(empty)
        else:
            for idx, tool_obj in enumerate(tools):
                row = self._make_tool_row(idx + 1, tool_obj)
                content_layout.addWidget(row)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        card_layout.addWidget(scroll)

    def _make_tool_row(self, index: int, tool_obj) -> QFrame:
        """构建单个工具行"""
        row = QFrame()
        row.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border-radius: 8px;
                border: 1px solid #EEEEEE;
            }
            QFrame:hover {
                background-color: #EEF2FF;
                border-color: #C7D2FE;
            }
        """)

        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(12, 10, 12, 10)
        row_layout.setSpacing(4)

        # 工具名称行
        name_row = QHBoxLayout()
        name_row.setSpacing(8)

        badge = QLabel(str(index))
        badge.setFixedSize(22, 22)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet("""
            QLabel {
                background-color: #4F46E5;
                color: white;
                border-radius: 11px;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        name_row.addWidget(badge)

        name_label = QLabel(getattr(tool_obj, "name", str(tool_obj)))
        name_label.setStyleSheet("""
            QLabel {
                color: #1A1A2E;
                font-size: 13px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        name_row.addWidget(name_label)
        name_row.addStretch()
        row_layout.addLayout(name_row)

        # 工具描述
        desc_text = getattr(tool_obj, "description", "无描述")
        # 截断过长描述
        if len(desc_text) > 120:
            desc_text = desc_text[:117] + "..."
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel {
                color: #555555;
                font-size: 11px;
                background: transparent;
                border: none;
                padding-left: 30px;
            }
        """)
        row_layout.addWidget(desc_label)

        return row

    def show_near(self, trigger_widget: QWidget):
        """在触发按钮旁边显示弹窗"""
        self.adjustSize()
        # 计算位置：触发按钮上方
        global_pos = trigger_widget.mapToGlobal(QPoint(0, 0))
        popup_x = global_pos.x()
        popup_y = global_pos.y() - self.height() - 8

        # 防止超出屏幕顶部
        if popup_y < 0:
            popup_y = global_pos.y() + trigger_widget.height() + 8

        self.move(popup_x, popup_y)
        self.exec()


# ─────────────────────────────────────────────
# 消息气泡
# ─────────────────────────────────────────────

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
        browser = QTextBrowser()
        browser.setMarkdown(content)
        browser.setOpenExternalLinks(True)  # 允许点击链接
        browser.setStyleSheet("""
            QTextBrowser {
                font-size: 13px;
                padding: 4px;
                border: 1px solid #000;
                color: #666;
            }
        """)

        layout.addWidget(browser)

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


# ─────────────────────────────────────────────
# 聊天历史
# ─────────────────────────────────────────────

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

        if self.layout.count() > 0:
            self.layout.takeAt(self.layout.count() - 1)

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


# ─────────────────────────────────────────────
# Agent 主面板
# ─────────────────────────────────────────────

class AgentPanel(PanelFrame):
    """Agent 主面板"""

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

        # ===== 输入区（含工具按钮） =====
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        # 工具查看按钮（紧凑，放在输入框左侧）
        self.tools_btn = QPushButton("🛠 工具")
        self.tools_btn.setFixedHeight(36)
        self.tools_btn.setFixedWidth(72)
        self.tools_btn.setCursor(Qt.PointingHandCursor)
        self.tools_btn.setToolTip("点击查看所有可用工具")
        self.tools_btn.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                color: #374151;
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                padding: 0 8px;
            }
            QPushButton:hover {
                background-color: #E0E7FF;
                border-color: #6366F1;
                color: #4F46E5;
            }
            QPushButton:pressed {
                background-color: #C7D2FE;
            }
        """)
        self.tools_btn.clicked.connect(self._show_tools_popup)
        input_layout.addWidget(self.tools_btn)

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

        # 更新工具数量角标
        self._update_tools_badge()

    def _update_tools_badge(self):
        """更新工具按钮上的数量提示"""
        tools = self.agent.get_tools()
        count = len(tools) if tools else 0
        self.tools_btn.setText(f"🛠 工具 {count}" if count else "🛠 工具")

    def _show_tools_popup(self):
        """弹出工具列表弹窗"""
        tools = self.agent.get_tools()
        popup = ToolsPopup(tools, parent=self)
        popup.show_near(self.tools_btn)

    def _send_message(self):
        """发送消息"""
        user_input = self.input_box.text().strip()

        if not user_input:
            return

        self.chat_history.add_message("user", user_input)
        self.input_box.clear()

        try:
            response = self.agent.chat(user_input)
            self.chat_history.add_message("assistant", response)
        except Exception as e:
            error_msg = f"**** 处理失败: {str(e)}"
            self.chat_history.add_message("assistant", error_msg)

        self.message_sent.emit(user_input)

    def _clear_conversation(self):
        """清空对话"""
        self.chat_history.clear_messages()
        self.agent.clear_conversation()

        welcome = "————对话已清空,请继续提问!————"
        self.chat_history.add_message("assistant", welcome)