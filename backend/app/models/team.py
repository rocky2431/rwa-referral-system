"""
战队模型
"""
from sqlalchemy import Column, BigInteger, String, Integer, Boolean, TIMESTAMP, Text, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base


class Team(Base):
    """战队表"""

    __tablename__ = "teams"

    # 主键
    id = Column(BigInteger, primary_key=True, index=True)

    # 基本信息
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    logo_url = Column(Text)

    # 队长
    captain_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # 统计数据
    member_count = Column(Integer, default=1, nullable=False)
    total_points = Column(BigInteger, default=0, nullable=False)
    active_member_count = Column(Integer, default=0, nullable=False)

    # 战队等级
    level = Column(Integer, default=1, nullable=False)
    experience = Column(BigInteger, default=0, nullable=False)

    # 奖励池
    reward_pool = Column(BigInteger, default=0, nullable=False)
    last_distribution_at = Column(TIMESTAMP(timezone=True))

    # 设置
    is_public = Column(Boolean, default=True, nullable=False)
    require_approval = Column(Boolean, default=False, nullable=False)
    max_members = Column(Integer, default=100, nullable=False)

    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    disbanded_at = Column(TIMESTAMP(timezone=True))

    # 关系
    captain = relationship("User", foreign_keys=[captain_id], backref="captained_teams")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    tasks = relationship("TeamTask", back_populates="team", cascade="all, delete-orphan")

    # 约束
    __table_args__ = (
        CheckConstraint("member_count >= 0", name="check_member_count_positive"),
        CheckConstraint("total_points >= 0", name="check_total_points_positive"),
        CheckConstraint("level >= 1 AND level <= 100", name="check_level_range"),
        CheckConstraint("reward_pool >= 0", name="check_reward_pool_positive"),
        CheckConstraint("max_members >= 1 AND max_members <= 1000", name="check_max_members_range"),
    )

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}', level={self.level}, members={self.member_count})>"
