"""
推荐关系模型
"""

from sqlalchemy import Column, BigInteger, String, Integer, Boolean, ForeignKey, TIMESTAMP, CheckConstraint, UniqueConstraint
from sqlalchemy.sql import func
from app.db.session import Base


class ReferralRelation(Base):
    """推荐关系表"""

    __tablename__ = "referral_relations"

    # 主键
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)

    # 推荐关系
    referee_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    referrer_id = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)

    # 链上数据
    blockchain_tx_hash = Column(String(66), nullable=True, index=True)
    blockchain_block_number = Column(BigInteger, nullable=True)

    # 层级
    level = Column(Integer, default=1, index=True)

    # 统计
    total_rewards_given = Column(BigInteger, default=0)

    # 状态
    is_active = Column(Boolean, default=True)

    # 时间
    bound_at = Column(TIMESTAMP, server_default=func.now())
    synced_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_at = Column(TIMESTAMP, server_default=func.now())

    # 约束
    __table_args__ = (
        CheckConstraint("referee_id != referrer_id", name="no_self_referral"),
    )

    def __repr__(self):
        return f"<ReferralRelation(referee_id={self.referee_id}, referrer_id={self.referrer_id}, level={self.level})>"
