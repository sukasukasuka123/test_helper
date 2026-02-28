# main.py
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget,
    QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget
)
from PySide6.QtCore import Qt

from service.db import DatabaseManager
from service.interviewee import IntervieweeManager
from service.meta import QuestionMetaManager
from service.selector import QuestionSelector
from service.stats import InterviewStats
from service.schema import SchemaInitializer
from service.importer import QuestionImporter
from service.exporter import DataExporter
from service.analyzer import IntervieweeAnalyzer

# ===== Agent 模块导入 =====
from service.agent_core import Agent
from service.agent_tools import register_default_tools

from UI.session_controller import InterviewSessionController
from UI.interviewee_panel import IntervieweePanel
from UI.question_select_panel import QuestionSelectPanel
from UI.question_runner_panel import QuestionRunnerPanel
from UI.question_widget import QuestionWidget
from UI.stats_panel import StatsPanel
from UI.import_panel import QuestionImportPanel
from UI.export_panel import ExportPanel
from UI.analysis_panel import AnalysisPanel

# ===== Agent UI 导入 =====
from UI.agent_panel import AgentPanel


def main():
    app = QApplication(sys.argv)

    # ---- DB & Service ----
    db = DatabaseManager("interview.db")
    SchemaInitializer(db).initialize()

    interviewee_mgr = IntervieweeManager(db)
    meta_mgr = QuestionMetaManager(db)
    selector = QuestionSelector(db)
    importer = QuestionImporter(db)
    stats_mgr = InterviewStats(db)
    exporter = DataExporter(db)
    analyzer = IntervieweeAnalyzer(db)

    # ===== Agent 初始化 =====
    agent = Agent(db, system_prompt="""
你是一个实验室面试助手 Agent。
你可以使用工具来帮助用户:
- 查询题库统计信息
- 分析面试者表现
- 生成面试报告

请根据用户需求,选择合适的工具来完成任务。
    """)

    # 注册默认工具
    register_default_tools(agent, db)

    # ---- Session Controller ----
    session = InterviewSessionController()

    # ---- UI Components ----
    import_panel = QuestionImportPanel(importer)
    interviewee_panel = IntervieweePanel(interviewee_mgr, session)
    export_panel = ExportPanel(exporter)
    analysis_panel = AnalysisPanel(analyzer)

    # ===== Agent 面板 =====
    agent_panel = AgentPanel(agent)

    select_panel = QuestionSelectPanel(meta_mgr, selector, session)
    runner_panel = QuestionRunnerPanel(selector, QuestionWidget, session)
    stats_panel = StatsPanel(stats_mgr, session)

    def auto_save_current_question(result):
        interviewee_id = interviewee_panel.get_interviewee_id()
        if not interviewee_id:
            return

        qid, score, snapshot = result
        stats_mgr.add(interviewee_id, qid, snapshot, score)

    runner_panel.auto_save_hook = auto_save_current_question

    # =========================
    # 左侧:管理区(使用 Tab)
    # =========================
    left_tabs = QTabWidget()

    # Tab 1: 准备区
    prepare_tab = QWidget()
    prepare_layout = QVBoxLayout(prepare_tab)
    prepare_layout.addWidget(import_panel)
    prepare_layout.addWidget(interviewee_panel)
    prepare_layout.addStretch()

    # Tab 2: 数据分析
    analysis_tab = QWidget()
    analysis_layout = QVBoxLayout(analysis_tab)
    analysis_layout.addWidget(export_panel)
    analysis_layout.addWidget(analysis_panel)

    # ===== Tab 3: AI 助手 =====
    agent_tab = QWidget()
    agent_layout = QVBoxLayout(agent_tab)
    agent_layout.addWidget(agent_panel)

    left_tabs.addTab(prepare_tab, "准备区")
    left_tabs.addTab(analysis_tab, "数据分析")
    left_tabs.addTab(agent_tab, "AI 助手")

    # =========================
    # 右侧:面试区
    # =========================
    right_container = QWidget()
    right_layout = QVBoxLayout(right_container)
    right_layout.addWidget(select_panel)
    right_layout.addWidget(runner_panel, stretch=1)
    right_layout.addWidget(stats_panel)

    # =========================
    # 主分割器
    # =========================
    splitter = QSplitter(Qt.Horizontal)
    splitter.addWidget(left_tabs)
    splitter.addWidget(right_container)

    splitter.setStretchFactor(0, 1)  # 左侧
    splitter.setStretchFactor(1, 3)  # 右侧(核心区域)

    # =========================
    # Root
    # =========================
    root = QWidget()
    root_layout = QHBoxLayout(root)
    root_layout.addWidget(splitter)

    root.setWindowTitle("实验室面试协助工具（包括记录溯源和面试协助）")
    root.resize(1400, 800)
    root.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()