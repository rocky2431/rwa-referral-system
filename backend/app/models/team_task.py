"""
战队任务模型
"""
import enum
from sqlalchemy import Column, BigInteger, String, Integer, TIMESTAMP, ForeignKey, Enum, Text, CheckConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base


class TeamTaskStatus(str, enum.Enum):
    """战队任务状态枚举"""
    ACTIVE = "active"        # 进行中
    COMPLETED = "completed"  # 已完成
    EXPIRED = "expired"      # 已过期
    CANCELLED = "cancelled"  # 已取消


class TeamTask(Base):
    """战队任务表"""

    __tablename__ = "team_tasks"

    # 主键
    id = Column(BigInteger, primary_key=True, index=True)

    # 外键
    team_id = Column(
        BigInteger,
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 任务信息
    title = Column(String(100), nullable=False)
    description = Column(Text)
    task_type = Column(String(50))  # 任务类型 (invite_users, complete_quiz, etc.)

    # 目标
    target_value = Column(Integer, nullable=False)  # 目标值 (如：邀请50人)
    current_value = Column(Integer, default=0, nullable=False)  # 当前进度

    # 奖励
    reward_points = Column(BigInteger, nullable=False)  # 奖励积分
    bonus_points = Column(BigInteger, default=0, nullable=False)  # 额外奖励

    # 时间
    start_time = Column(TIMESTAMP(timezone=True), nullable=False)
    end_time = Column(TIMESTAMP(timezone=True), nullable=False)
    completed_at = Column(TIMESTAMP(timezone=True))

    # 状态
    status = Column(
        Enum(TeamTaskStatus, name="team_task_status"),
        default=TeamTaskStatus.ACTIVE,
        nullable=False,
        index=True
    )

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 关系
    team = relationship("Team", back_populates="tasks")

    # 约束
    __table_args__ = (
        CheckConstraint("target_value > 0", name="check_target_value_positive"),
        CheckConstraint("current_value >= 0", name="check_current_value_positive"),
        CheckConstraint("reward_points >= 0", name="check_reward_points_positive"),
        CheckConstraint("bonus_points >= 0", name="check_bonus_points_positive"),
        CheckConstraint("start_time < end_time", name="check_time_range"),
        Index("idx_team_tasks_end_time", "end_time"),
    )

    def __repr__(self):
        return f"<TeamTask(id={self.id}, team_id={self.team_id}, title='{self.title}', progress={self.current_value}/{self.target_value})>"

    @property
    def progress_percentage(self) -> float:
        """计算任务完成百分比"""
        if self.target_value == 0:
            return 0.0
        return min((self.current_value / self.target_value) * 100, 100.0)

    @property
    def is_completed(self) -> bool:
        """判断任务是否完成"""
        return self.current_value >= self.target_value
