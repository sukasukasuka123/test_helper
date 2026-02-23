# UI/analysis_panel.py
from PySide6.QtWidgets import (
    QComboBox,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QWidget,
    QMessageBox
)
from PySide6.QtCore import Qt
from UI.base_panel import PanelFrame
import math


class RadarChartWidget(QWidget):
    """雷达图绘制组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = {}  # {类型: 分数}
        self.max_score = 10  # 默认最大分数
        self.setMinimumSize(400, 400)

    def set_data(self, data: dict, max_score: float = 10):
        """设置雷达图数据"""
        self.data = data
        self.max_score = max(max_score, 1)  # 避免除零
        self.update()

    def paintEvent(self, event):
        if not self.data:
            return

        from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF, QFont
        from PySide6.QtCore import QPointF

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # ===== 计算参数 =====
        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 2 - 60

        categories = list(self.data.keys())
        n = len(categories)

        if n == 0:
            return

        angle_step = 2 * math.pi / n

        # ===== 绘制背景网格 =====
        painter.setPen(QPen(QColor("#E0E0E0"), 1))
        for level in range(1, 6):  # 5个层级
            scale = level / 5
            points = []
            for i in range(n):
                angle = i * angle_step - math.pi / 2
                x = center_x + radius * scale * math.cos(angle)
                y = center_y + radius * scale * math.sin(angle)
                points.append(QPointF(x, y))

            polygon = QPolygonF(points)
            painter.drawPolygon(polygon)

        # ===== 绘制轴线 =====
        painter.setPen(QPen(QColor("#C0C0C0"), 1))
        for i in range(n):
            angle = i * angle_step - math.pi / 2
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            painter.drawLine(int(center_x), int(center_y), int(x), int(y))

        # ===== 绘制标签 =====
        painter.setPen(QPen(QColor("#333333"), 1))
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)

        for i, category in enumerate(categories):
            angle = i * angle_step - math.pi / 2
            label_radius = radius + 30
            x = center_x + label_radius * math.cos(angle)
            y = center_y + label_radius * math.sin(angle)

            # 文字居中对齐
            text_rect = painter.fontMetrics().boundingRect(category)
            painter.drawText(
                int(x - text_rect.width() / 2),
                int(y + text_rect.height() / 4),
                category
            )

        # ===== 绘制数据多边形 =====
        data_points = []
        for i, category in enumerate(categories):
            score = self.data[category]
            scale = score / self.max_score
            angle = i * angle_step - math.pi / 2
            x = center_x + radius * scale * math.cos(angle)
            y = center_y + radius * scale * math.sin(angle)
            data_points.append(QPointF(x, y))

        # 填充
        painter.setBrush(QBrush(QColor(68, 114, 196, 100)))
        painter.setPen(QPen(QColor(68, 114, 196), 2))
        polygon = QPolygonF(data_points)
        painter.drawPolygon(polygon)

        # ===== 绘制数据点 =====
        painter.setBrush(QBrush(QColor(68, 114, 196)))
        for point in data_points:
            painter.drawEllipse(point, 4, 4)


class AnalysisPanel(PanelFrame):
    def __init__(self, analyzer):
        super().__init__("📊 用户属性分析")

        self.analyzer = analyzer

        # ===== 面试者选择 =====
        self.interviewee_combo = QComboBox()
        self.interviewee_combo.addItem("请选择面试者", None)

        refresh_btn = QPushButton("刷新列表")
        refresh_btn.clicked.connect(self._refresh_list)

        analyze_btn = QPushButton("分析")
        analyze_btn.clicked.connect(self._analyze)

        # ===== 信息展示 =====
        self.info_label = QLabel("未选择面试者")
        self.info_label.setStyleSheet("color: #666; font-size: 12px;")
        self.info_label.setWordWrap(True)

        # ===== 雷达图 =====
        self.radar_chart = RadarChartWidget()

        # ===== 布局 =====
        self.layout.addWidget(QLabel("选择面试者"))
        self.layout.addWidget(self.interviewee_combo)
        self.layout.addWidget(refresh_btn)
        self.layout.addWidget(analyze_btn)
        self.layout.addWidget(self.info_label)
        self.layout.addWidget(self.radar_chart)

        # 初始加载
        self._refresh_list()

    def _refresh_list(self):
        """刷新面试者列表"""
        self.interviewee_combo.clear()
        self.interviewee_combo.addItem("请选择面试者", None)

        interviewees = self.analyzer.get_all_interviewees()
        for iid, name in interviewees:
            self.interviewee_combo.addItem(f"{name} (ID:{iid})", iid)

    def _analyze(self):
        """执行分析"""
        interviewee_id = self.interviewee_combo.currentData()

        if interviewee_id is None:
            QMessageBox.warning(self, "提示", "请先选择面试者")
            return

        # ===== 获取基本信息 =====
        info = self.analyzer.get_interviewee_info(interviewee_id)
        if not info:
            QMessageBox.warning(self, "错误", "未找到该面试者")
            return

        # ===== 获取统计信息 =====
        stats = self.analyzer.get_statistics(interviewee_id)

        # ===== 计算各类型加权分数 =====
        type_scores = self.analyzer.calculate_type_scores(interviewee_id)

        if not type_scores:
            QMessageBox.information(self, "提示", "该面试者尚无答题记录")
            self.info_label.setText(f"面试者: {info['name']}\n尚无答题记录")
            self.radar_chart.set_data({})
            return

        # ===== 补全所有题型（未答题的类型分数为0）=====
        all_types = self.analyzer.get_all_question_types()
        for q_type in all_types:
            if q_type not in type_scores:
                type_scores[q_type] = 0.0

        # ===== 更新信息显示 =====
        info_text = f"""
面试者: {info['name']}
邮箱: {info.get('email') or '未填写'}
答题总数: {stats['total_questions']} 题
平均分: {stats['avg_score']} 分
最高分: {stats['max_score']} 分
最低分: {stats['min_score']} 分
        """.strip()

        self.info_label.setText(info_text)

        # ===== 更新雷达图 =====
        max_score = max(type_scores.values()) if type_scores else 10
        self.radar_chart.set_data(type_scores, max_score)