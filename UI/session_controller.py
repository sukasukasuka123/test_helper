# UI/session_controller.py
from enum import Enum, auto

class SessionState(Enum):
    INIT = auto()
    INTERVIEWEE_CREATED = auto()
    POOL_LOADED = auto()
    QUESTION_ACTIVE = auto()
    FINISHED = auto()

class InterviewSessionController:
    def __init__(self):
        self.state = SessionState.INIT
        self.current_question_saved = False

    # ---------- 状态推进 ----------
    def set_interviewee_created(self):
        self.state = SessionState.INTERVIEWEE_CREATED

    def set_pool_loaded(self):
        self.state = SessionState.POOL_LOADED

    def start_question(self):
        self.state = SessionState.QUESTION_ACTIVE
        self.current_question_saved = False

    def mark_question_saved(self):
        self.current_question_saved = True

    def abandon_current_question(self):
        self.current_question_saved = True
        self.state = SessionState.POOL_LOADED

    def finish(self):
        self.state = SessionState.FINISHED

    # ---------- 判断 ----------
    def can_load_pool(self):
        return self.state in (
            SessionState.INTERVIEWEE_CREATED,
            SessionState.POOL_LOADED,
            SessionState.QUESTION_ACTIVE,
        )

    def can_next_question(self):
        return self.state in (
            SessionState.POOL_LOADED,
            SessionState.QUESTION_ACTIVE,
        )

    def need_save_before_next(self):
        return (
            self.state == SessionState.QUESTION_ACTIVE
            and not self.current_question_saved
        )
