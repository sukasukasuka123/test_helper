# service/stats.py
import json
from datetime import datetime


class InterviewStats:
    def __init__(self, db):
        self.db = db
        self.buffer = []

    def add(self, interviewee_id, question_id, snapshot, score=0):
        self.buffer.append({
            "interviewee_id": interviewee_id,
            "question_id": question_id,
            "score": score,
            "snapshot": snapshot,
        })

    def flush(self):
        if not self.buffer:
            return
        now = datetime.now()
        created_at = now.strftime("%Y-%m-%d %H:%M:%S")
        month = now.strftime("%Y-%m")

        rows = []
        for item in self.buffer:
            rows.append((
                item["interviewee_id"],
                item["question_id"],
                item["score"],
                json.dumps(item["snapshot"], ensure_ascii=False),
                month,
                created_at,
            ))
            print(item["interviewee_id"],item["question_id"],item["score"])
        self.db.executemany("""
            INSERT INTO interview_record
            (interviewee_id, question_id, score, answer_snapshot, month, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, rows)

        self.buffer.clear()
