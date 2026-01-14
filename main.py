# main.py
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget,
    QVBoxLayout, QHBoxLayout,
    QSplitter
)
from PySide6.QtCore import Qt

from service.db import DatabaseManager
from service.interviewee import IntervieweeManager
from service.meta import QuestionMetaManager
from service.selector import QuestionSelector
from service.stats import InterviewStats
from service.schema import SchemaInitializer
from service.importer import QuestionImporter

from UI.session_controller import InterviewSessionController
from UI.interviewee_panel import IntervieweePanel
from UI.question_select_panel import QuestionSelectPanel
from UI.question_runner_panel import QuestionRunnerPanel
from UI.question_widget import QuestionWidget
from UI.stats_panel import StatsPanel
from UI.import_panel import QuestionImportPanel

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

    # ---- Session Controller ----
    session = InterviewSessionController()

    # ---- UI Components ----
    import_panel = QuestionImportPanel(importer)
    interviewee_panel = IntervieweePanel(interviewee_mgr, session)

    select_panel = QuestionSelectPanel(meta_mgr, selector, session)
    runner_panel = QuestionRunnerPanel(selector, QuestionWidget, session)
    stats_panel = StatsPanel(stats_mgr, session)



    def auto_save_current_question(result):
        interviewee_id = interviewee_panel.get_interviewee_id()
        if not interviewee_id:
            return

        qid,score, snapshot = result
        stats_mgr.add(interviewee_id, qid, snapshot,score)


    runner_panel.auto_save_hook = auto_save_current_question
    # =========================
    # 左侧：准备区
    # =========================
    left_container = QWidget()
    left_layout = QVBoxLayout(left_container)
    left_layout.addWidget(import_panel)
    left_layout.addWidget(interviewee_panel)
    left_layout.addStretch()

    # =========================
    # 右侧：面试区
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
    splitter.addWidget(left_container)
    splitter.addWidget(right_container)

    splitter.setStretchFactor(0, 1)  # 左侧
    splitter.setStretchFactor(1, 3)  # 右侧（核心区域）

    # =========================
    # Root
    # =========================
    root = QWidget()
    root_layout = QHBoxLayout(root)
    root_layout.addWidget(splitter)

    root.setWindowTitle("实验室面试追溯工具")
    root.resize(1300, 750)
    root.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

