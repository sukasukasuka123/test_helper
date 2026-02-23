# selector.py
# 题目选择器（随机抽题）
import random
import hashlib

class QuestionSelector:
    def __init__(self, db):
        self.db = db
        self.pool = []

    def load_pool(self, q_type, difficulty, seed_source: str):

        seed = hashlib.sha256(seed_source.encode()).hexdigest()
        rng = random.Random(seed)  # 不污染全局 random

        rows = self.db.fetchall(
            """
            SELECT id FROM question_bank
            WHERE q_type=? AND difficulty=?
            """,
            (q_type, difficulty)
        )

        self.pool = [r[0] for r in rows]
        rng.shuffle(self.pool)

        print(f"[QuestionSelector] 题池【类别：{q_type}/{difficulty}】加载完成，共 {len(self.pool)} 题")

    def next_question(self):
        if not self.pool:
            return None

        qid = self.pool.pop()
        return self.db.fetchall(
            """
            SELECT id, q_type, difficulty, content, answer
            FROM question_bank WHERE id=?
            """,
            (qid,)
        )[0]

    def remaining(self):
        return len(self.pool)
