"""
问答系统模型
"""
import enum
from sqlalchemy import Column, BigInteger, String, Integer, Boolean, TIMESTAMP, Text, ForeignKey, CheckConstraint, ARRAY, Enum as SQLEnum, DECIMAL, Date, CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base


class QuestionDifficulty(str, enum.Enum):
    """题目难度枚举"""
    EASY = "easy"       # 简单
    MEDIUM = "medium"   # 中等
    HARD = "hard"       # 困难


class QuestionSource(str, enum.Enum):
    """题目来源枚举"""
    ADMIN = "admin"              # 管理员创建
    USER_SUBMIT = "user_submit"  # 用户提交
    API = "api"                  # API导入


class QuestionStatus(str, enum.Enum):
    """题目状态枚举"""
    PENDING = "pending"      # 待审核
    APPROVED = "approved"    # 已批准
    REJECTED = "rejected"    # 已拒绝
    ACTIVE = "active"        # 激活中
    DISABLED = "disabled"    # 已禁用


class Question(Base):
    """题库表"""

    __tablename__ = "questions"

    # 主键
    id = Column(BigInteger, primary_key=True, index=True)

    # 题目内容
    question_text = Column(Text, nullable=False)
    option_a = Column(String(200), nullable=False)
    option_b = Column(String(200), nullable=False)
    option_c = Column(String(200))
    option_d = Column(String(200))
    correct_answer = Column(CHAR(1), nullable=False)

    # 难度与分类
    difficulty = Column(SQLEnum(QuestionDifficulty, name="question_difficulty"), nullable=False, index=True)
    category = Column(String(50), index=True)
    tags = Column(ARRAY(String(100)))

    # 奖励
    reward_points = Column(Integer, nullable=False)

    # 来源
    source = Column(SQLEnum(QuestionSource, name="question_source"), default=QuestionSource.ADMIN)
    submitted_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"))

    # 统计
    total_answers = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    accuracy_rate = Column(DECIMAL(5, 2))

    # 审核
    status = Column(SQLEnum(QuestionStatus, name="question_status"), default=QuestionStatus.PENDING, index=True)
    reviewed_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at = Column(TIMESTAMP(timezone=True))
    reject_reason = Column(Text)

    # 时效
    valid_from = Column(TIMESTAMP(timezone=True), server_default=func.now())
    valid_until = Column(TIMESTAMP(timezone=True))

    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    user_answers = relationship("UserAnswer", back_populates="question", cascade="all, delete-orphan")

    # 约束
    __table_args__ = (
        CheckConstraint("correct_answer IN ('A', 'B', 'C', 'D')", name="check_correct_answer_valid"),
        CheckConstraint("reward_points > 0", name="check_reward_points_positive"),
        CheckConstraint("total_answers >= 0", name="check_total_answers_non_negative"),
        CheckConstraint("correct_answers >= 0", name="check_correct_answers_non_negative"),
        CheckConstraint("correct_answers <= total_answers", name="check_correct_lte_total"),
    )

    def __repr__(self):
        return f"<Question(id={self.id}, difficulty={self.difficulty.value}, category='{self.category}', status={self.status.value})>"


class UserAnswer(Base):
    """答题记录表"""

    __tablename__ = "user_answers"

    # 主键
    id = Column(BigInteger, primary_key=True, index=True)

    # 关联
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    question_id = Column(
        BigInteger,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 答题信息
    user_answer = Column(CHAR(1), nullable=False)
    is_correct = Column(Boolean, nullable=False)

    # 时间
    answer_time = Column(Integer)  # 答题耗时(秒)
    answered_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # 奖励
    points_earned = Column(Integer, default=0)

    # 日期 (用于限制每日答题次数)
    answer_date = Column(Date, server_default=func.current_date(), index=True)

    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # 关系
    question = relationship("Question", back_populates="user_answers")

    # 约束
    __table_args__ = (
        CheckConstraint("user_answer IN ('A', 'B', 'C', 'D')", name="check_user_answer_valid"),
        CheckConstraint("points_earned >= 0", name="check_points_earned_non_negative"),
        CheckConstraint("answer_time >= 0", name="check_answer_time_non_negative"),
    )

    def __repr__(self):
        return f"<UserAnswer(id={self.id}, user_id={self.user_id}, question_id={self.question_id}, is_correct={self.is_correct})>"


class DailyQuizSession(Base):
    """每日答题会话表"""

    __tablename__ = "daily_quiz_sessions"

    # 主键
    id = Column(BigInteger, primary_key=True, index=True)

    # 关联
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    session_date = Column(Date, server_default=func.current_date())

    # 统计
    questions_answered = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    total_points_earned = Column(Integer, default=0)

    # 时间
    started_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    completed_at = Column(TIMESTAMP(timezone=True))

    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # 约束
    __table_args__ = (
        CheckConstraint("questions_answered >= 0", name="check_questions_answered_non_negative"),
        CheckConstraint("questions_answered <= 5", name="check_max_questions"),
        CheckConstraint("correct_count >= 0", name="check_correct_count_non_negative"),
        CheckConstraint("correct_count <= questions_answered", name="check_correct_lte_answered"),
        CheckConstraint("total_points_earned >= 0", name="check_total_points_non_negative"),
    )

    @property
    def accuracy_rate(self) -> float:
        """计算正确率"""
        if self.questions_answered == 0:
            return 0.0
        return (self.correct_count / self.questions_answered) * 100

    @property
    def is_completed(self) -> bool:
        """判断是否已完成（达到5题）"""
        return self.questions_answered >= 5

    def __repr__(self):
        return f"<DailyQuizSession(id={self.id}, user_id={self.user_id}, date={self.session_date}, answered={self.questions_answered}/5, correct={self.correct_count})>"
