"""
用户模型
"""

from sqlalchemy import Column, BigInteger, String, Integer, Boolean, TIMESTAMP, DATE, CheckConstraint
from sqlalchemy.sql import func
from app.db.session import Base


class User(Base):
    """用户表"""

    __tablename__ = "users"

    # 主键
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)

    # 基本信息
    wallet_address = Column(String(42), unique=True, nullable=False, index=True)
    username = Column(String(50), nullable=True)
    avatar_url = Column(String, nullable=True)
    email = Column(String(100), nullable=True)

    # 等级系统
    level = Column(Integer, default=1, index=True)
    experience = Column(BigInteger, default=0)

    # 统计数据
    total_points = Column(BigInteger, default=0, index=True)
    total_invited = Column(Integer, default=0)
    total_tasks_completed = Column(Integer, default=0)
    total_questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)

    # 活跃度
    last_active_at = Column(TIMESTAMP, nullable=True, index=True)
    consecutive_login_days = Column(Integer, default=0)
    last_login_date = Column(DATE, nullable=True)

    # 状态
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    banned_until = Column(TIMESTAMP, nullable=True)

    # 时间戳
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # 约束
    __table_args__ = (
        CheckConstraint(
            "wallet_address ~ '^0x[a-fA-F0-9]{40}$'",
            name="wallet_address_format"
        ),
    )

    def __repr__(self):
        return f"<User(id={self.id}, wallet={self.wallet_address[:10]}...)>"
