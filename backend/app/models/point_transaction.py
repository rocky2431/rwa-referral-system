"""
积分交易流水模型
"""

from sqlalchemy import Column, BigInteger, String, ForeignKey, TIMESTAMP, CheckConstraint, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from app.db.session import Base
import enum


class PointTransactionType(str, enum.Enum):
    """积分交易类型枚举"""
    REGISTER_REWARD = "REGISTER_REWARD"  # 注册奖励
    REFERRAL_REWARD = "REFERRAL_REWARD"  # 推荐人奖励（邀请码被使用）
    REFERRAL_L1 = "REFERRAL_L1"        # 一级推荐奖励
    REFERRAL_L2 = "REFERRAL_L2"        # 二级推荐奖励
    TASK_REWARD = "TASK_REWARD"        # 任务奖励（通用）
    TASK_DAILY = "TASK_DAILY"          # 每日任务
    TASK_WEEKLY = "TASK_WEEKLY"        # 每周任务
    TASK_ONCE = "TASK_ONCE"            # 一次性任务
    QUIZ_CORRECT = "QUIZ_CORRECT"      # 答题正确
    TEAM_REWARD = "TEAM_REWARD"        # 战队奖励
    PURCHASE = "PURCHASE"              # 购买奖励
    ADMIN_GRANT = "ADMIN_GRANT"        # 管理员发放
    EXCHANGE_TOKEN = "EXCHANGE_TOKEN"  # 兑换代币
    SPEND_ITEM = "SPEND_ITEM"          # 消费物品


class PointTransaction(Base):
    """积分流水表"""

    __tablename__ = "point_transactions"

    # 主键
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 交易信息
    transaction_type = Column(
        SQLEnum(PointTransactionType, name="point_transaction_type", create_type=True),
        nullable=False,
        index=True
    )
    amount = Column(BigInteger, nullable=False)  # 正数=获得, 负数=消费
    balance_after = Column(BigInteger, nullable=False)

    # 关联信息
    related_task_id = Column(BigInteger, nullable=True)
    related_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    related_team_id = Column(BigInteger, nullable=True)
    related_question_id = Column(BigInteger, nullable=True)

    # 元数据
    description = Column(String, nullable=True)
    extra_metadata = Column(JSONB, nullable=True)

    # 状态
    status = Column(String(20), default="completed")  # completed/pending/cancelled

    # 时间戳
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)

    # 约束
    __table_args__ = (
        CheckConstraint("amount != 0", name="amount_not_zero"),
    )

    def __repr__(self):
        return f"<PointTransaction(id={self.id}, user_id={self.user_id}, type={self.transaction_type.value}, amount={self.amount})>"
