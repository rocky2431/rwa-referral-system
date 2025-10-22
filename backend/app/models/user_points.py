"""
用户积分模型
"""

from sqlalchemy import Column, BigInteger, ForeignKey, TIMESTAMP, CheckConstraint, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class UserPoints(Base):
    """用户积分账户表"""

    __tablename__ = "user_points"

    # 主键
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # 积分账户
    available_points = Column(BigInteger, default=0, index=True)
    frozen_points = Column(BigInteger, default=0)
    total_earned = Column(BigInteger, default=0)
    total_spent = Column(BigInteger, default=0)

    # 统计（按来源）
    points_from_referral = Column(BigInteger, default=0)
    points_from_tasks = Column(BigInteger, default=0)
    points_from_quiz = Column(BigInteger, default=0)
    points_from_team = Column(BigInteger, default=0)
    points_from_purchase = Column(BigInteger, default=0)

    # 时间戳
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # 关系
    # user = relationship("User", back_populates="points")

    # 约束
    __table_args__ = (
        CheckConstraint("available_points >= 0", name="points_non_negative"),
        CheckConstraint("frozen_points >= 0", name="frozen_non_negative"),
    )

    def __repr__(self):
        return f"<UserPoints(user_id={self.user_id}, available={self.available_points})>"
