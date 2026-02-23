# service/analyzer.py
import json
from typing import Dict, List, Tuple


class IntervieweeAnalyzer:
    """面试者数据分析服务"""

    # 难度系数
    DIFFICULTY_WEIGHTS = {
        "简单": 0.2,
        "中等": 0.5,
        "困难": 0.3
    }

    def __init__(self, db):
        self.db = db

    def get_all_interviewees(self) -> List[Tuple[int, str]]:
        """获取所有面试者列表 (id, name)"""
        rows = self.db.fetchall("""
                                SELECT id, name
                                FROM interviewee
                                ORDER BY created_at DESC
                                """)
        return rows

    def get_interviewee_info(self, interviewee_id: int) -> dict:
        """获取面试者基本信息"""
        row = self.db.fetchall(
            "SELECT name, email, phone, created_at FROM interviewee WHERE id=?",
            (interviewee_id,)
        )

        if not row:
            return None

        name, email, phone, created_at = row[0]
        return {
            "id": interviewee_id,
            "name": name,
            "email": email,
            "phone": phone,
            "created_at": created_at
        }

    def calculate_type_scores(self, interviewee_id: int) -> Dict[str, float]:
        """
        计算各题目类型的加权总分
        返回: {题目类型: 加权总分}
        """
        # 获取该面试者所有答题记录
        rows = self.db.fetchall("""
                                SELECT score, answer_snapshot
                                FROM interview_record
                                WHERE interviewee_id = ?
                                """, (interviewee_id,))

        if not rows:
            return {}

        # 按题目类型分组统计
        type_stats = {}  # {q_type: [(score, difficulty), ...]}

        for score, snapshot_json in rows:
            snapshot = json.loads(snapshot_json)
            q_type = snapshot.get("type", "未知")
            difficulty = snapshot.get("difficulty", "中等")

            if q_type not in type_stats:
                type_stats[q_type] = []

            type_stats[q_type].append((score, difficulty))

        # 计算每个类型的加权总分
        type_scores = {}

        for q_type, records in type_stats.items():
            total_weighted_score = 0.0

            for score, difficulty in records:
                weight = self.DIFFICULTY_WEIGHTS.get(difficulty, 0.5)
                weighted_score = score * weight
                total_weighted_score += weighted_score

            type_scores[q_type] = round(total_weighted_score, 2)

        return type_scores

    def get_all_question_types(self) -> List[str]:
        """获取数据库中所有题目类型"""
        rows = self.db.fetchall("""
                                SELECT DISTINCT q_type
                                FROM question_bank
                                ORDER BY q_type
                                """)
        return [r[0] for r in rows]

    def get_statistics(self, interviewee_id: int) -> dict:
        """获取面试者统计信息"""
        rows = self.db.fetchall("""
                                SELECT score, answer_snapshot
                                FROM interview_record
                                WHERE interviewee_id = ?
                                """, (interviewee_id,))

        if not rows:
            return {
                "total_questions": 0,
                "avg_score": 0,
                "max_score": 0,
                "min_score": 0
            }

        scores = [r[0] for r in rows]

        return {
            "total_questions": len(scores),
            "avg_score": round(sum(scores) / len(scores), 2),
            "max_score": max(scores),
            "min_score": min(scores)
        }