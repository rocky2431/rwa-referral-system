"""
数据库模型模块
"""

from app.db.session import Base
from .user import User
from .user_points import UserPoints
from .point_transaction import PointTransaction, PointTransactionType
from .referral_relation import ReferralRelation
from .team import Team
from .team_member import TeamMember, TeamMemberRole, TeamMemberStatus
from .team_task import TeamTask, TeamTaskStatus
from .task import Task, UserTask, TaskType, TaskTrigger, UserTaskStatus
from .quiz import Question, UserAnswer, DailyQuizSession, QuestionDifficulty, QuestionSource, QuestionStatus

__all__ = [
    "Base",
    "User",
    "UserPoints",
    "PointTransaction",
    "PointTransactionType",
    "ReferralRelation",
    "Team",
    "TeamMember",
    "TeamMemberRole",
    "TeamMemberStatus",
    "TeamTask",
    "TeamTaskStatus",
    "Task",
    "UserTask",
    "TaskType",
    "TaskTrigger",
    "UserTaskStatus",
    "Question",
    "UserAnswer",
    "DailyQuizSession",
    "QuestionDifficulty",
    "QuestionSource",
    "QuestionStatus",
]
