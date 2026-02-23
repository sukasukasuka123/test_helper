# meta.py
# 题库元数据管理，即统计出筛选的条件有哪些
class QuestionMetaManager:
    def __init__(self, db):
        self.db = db

    def get_types(self):
        return [r[0] for r in self.db.fetchall(
            "SELECT DISTINCT q_type FROM question_bank"
        )]

    def get_difficulties(self):
        return [r[0] for r in self.db.fetchall(
            "SELECT DISTINCT difficulty FROM question_bank"
        )]

    def count(self, q_type, difficulty):
        return self.db.fetchall(
            """
            SELECT COUNT(*) FROM question_bank
            WHERE q_type=? AND difficulty=?
            """,
            (q_type, difficulty)
        )[0][0]
