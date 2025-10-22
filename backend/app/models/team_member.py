"""
战队成员模型
"""
import enum
from sqlalchemy import Column, BigInteger, Integer, TIMESTAMP, ForeignKey, Enum, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base


class TeamMemberRole(str, enum.Enum):
    """战队成员角色枚举"""
    CAPTAIN = "captain"    # 队长
    ADMIN = "admin"        # 管理员
    MEMBER = "member"      # 普通成员


class TeamMemberStatus(str, enum.Enum):
    """战队成员状态枚举"""
    ACTIVE = "active"      # 活跃
    PENDING = "pending"    # 待审批
    REJECTED = "rejected"  # 已拒绝
    LEFT = "left"          # 已离开


class TeamMember(Base):
    """战队成员表"""

    __tablename__ = "team_members"

    # 主键
    id = Column(BigInteger, primary_key=True, index=True)

    # 外键
    team_id = Column(
        BigInteger,
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 角色
    role = Column(
        Enum(TeamMemberRole, name="team_member_role"),
        default=TeamMemberRole.MEMBER,
        nullable=False
    )

    # 贡献统计
    contribution_points = Column(BigInteger, default=0, nullable=False)
    tasks_completed = Column(Integer, default=0, nullable=False)

    # 状态
    status = Column(
        Enum(TeamMemberStatus, name="team_member_status"),
        default=TeamMemberStatus.PENDING,
        nullable=False,
        index=True
    )

    # 时间
    joined_at = Column(TIMESTAMP(timezone=True))
    approved_at = Column(TIMESTAMP(timezone=True))
    left_at = Column(TIMESTAMP(timezone=True))

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 关系
    team = relationship("Team", back_populates="members")
    user = relationship("User", backref="team_memberships")

    # 约束
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="unique_team_user"),
        CheckConstraint("contribution_points >= 0", name="check_contribution_positive"),
        CheckConstraint("tasks_completed >= 0", name="check_tasks_completed_positive"),
        Index("idx_team_members_role", "role"),
        Index("idx_team_members_contribution", "contribution_points"),
    )

    def __repr__(self):
        return f"<TeamMember(team_id={self.team_id}, user_id={self.user_id}, role={self.role.value}, status={self.status.value})>"
