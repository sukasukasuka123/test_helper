# interviewee.py
# 面试者管理
import json
import hashlib
from datetime import datetime
from typing import List


class IntervieweeManager:
    SALT = "LAB_INTERVIEW_SALT_2026"

    def __init__(self, db):
        self.db = db

    def _hash_info(self, raw_info: str) -> str:
        return hashlib.sha256(
            (raw_info + self.SALT).encode("utf-8")
        ).hexdigest()

    def create_interviewee(self, info: dict) -> int:
        raw = json.dumps(info, ensure_ascii=False, sort_keys=True)
        info_hash = self._hash_info(raw)

        cur = self.db.execute(
            """
            INSERT INTO interviewee
            (name, email, phone, raw_info, info_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                info.get("name"),
                info.get("email"),
                info.get("phone"),
                raw,
                info_hash,
                datetime.now().isoformat()
            )
        )
        return cur.lastrowid
    def get_interviewee_inPage(self, page: int,pageSize: int) -> List[dict]:
        cur = self.db.execute(
            """
            SELECT * FROM intervieewee
            limit ? offset ?
            """,
            (pageSize, page)
        )
        results = cur.fetchall()
        return results