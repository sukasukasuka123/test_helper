# service/schema.py

class SchemaInitializer:
    def __init__(self, db):
        self.db = db

    def initialize(self):
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS interviewee (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            raw_info TEXT NOT NULL,
            info_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS question_bank (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            q_type TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            content TEXT NOT NULL,
            answer TEXT NOT NULL
        )
        """)

        self.db.execute("""
        CREATE INDEX IF NOT EXISTS idx_q_type_diff
        ON question_bank (q_type, difficulty)
        """)

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS interview_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interviewee_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            score INTEGER,
            answer_snapshot TEXT NOT NULL,
            month TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)
