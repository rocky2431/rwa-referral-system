"""
任务系统模型
"""
import enum
from sqlalchemy import Column, BigInteger, String, Integer, Boolean, TIMESTAMP, Text, ForeignKey, CheckConstraint, ARRAY, Enum as SQLEnum, DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base


class TaskType(str, enum.Enum):
    """任务类型枚举"""
    DAILY = "daily"      # 每日任务
    WEEKLY = "weekly"    # 每周任务
    ONCE = "once"        # 一次性任务
    TEAM = "team"        # 战队任务


class TaskTrigger(str, enum.Enum):
    """任务触发方式"""
    AUTO = "auto"        # 自动触发
    MANUAL = "manual"    # 手动领取
    EVENT = "event"      # 事件触发


class UserTaskStatus(str, enum.Enum):
    """用户任务状态"""
    AVAILABLE = "AVAILABLE"      # 可领取（未开始）
    IN_PROGRESS = "IN_PROGRESS"  # 进行中
    COMPLETED = "COMPLETED"      # 已完成（待领奖）
    REWARDED = "REWARDED"        # 已领奖
    EXPIRED = "EXPIRED"          # 已过期

    # 兼容旧状态（将被废弃）
    CLAIMED = "CLAIMED"          # 已领取（映射到REWARDED）


class Task(Base):
    """任务配置表"""

    __tablename__ = "tasks"

    # 主键
    id = Column(BigInteger, primary_key=True, index=True)

    # 任务标识
    task_key = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    icon_url = Column(Text)

    # 任务类型
    task_type = Column(SQLEnum(TaskType, name="task_type"), nullable=False, index=True)
    trigger_type = Column(SQLEnum(TaskTrigger, name="task_trigger"), default=TaskTrigger.MANUAL)

    # 目标配置
    target_type = Column(String(50))  # 目标类型 (invite_users/share/purchase等)
    target_value = Column(Integer, default=1)

    # 奖励配置
    reward_points = Column(Integer, nullable=False)
    reward_experience = Column(Integer, default=0)
    bonus_multiplier = Column(DECIMAL(3, 2), default=1.0)

    # 限制条件
    min_level_required = Column(Integer, default=1)
    max_completions_per_user = Column(Integer)  # None表示无限制

    # 优先级和排序
    priority = Column(Integer, default=0, index=True)
    sort_order = Column(Integer, default=0)

    # 状态
    is_active = Column(Boolean, default=True, index=True)
    is_visible = Column(Boolean, default=True)

    # 时间配置
    start_time = Column(TIMESTAMP(timezone=True))
    end_time = Column(TIMESTAMP(timezone=True))

    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    user_tasks = relationship("UserTask", back_populates="task", cascade="all, delete-orphan")

    # 约束
    __table_args__ = (
        CheckConstraint("target_value >= 1", name="check_target_value_positive"),
        CheckConstraint("reward_points > 0", name="check_reward_points_positive"),
        CheckConstraint("reward_experience >= 0", name="check_reward_exp_non_negative"),
        CheckConstraint("min_level_required >= 1 AND min_level_required <= 100", name="check_min_level_range"),
        CheckConstraint("priority >= 0", name="check_priority_non_negative"),
    )

    def __repr__(self):
        return f"<Task(id={self.id}, key='{self.task_key}', type={self.task_type.value}, points={self.reward_points})>"


class UserTask(Base):
    """用户任务进度表"""

    __tablename__ = "user_tasks"

    # 主键
    id = Column(BigInteger, primary_key=True, index=True)

    # 关联
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    task_id = Column(
        BigInteger,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 进度
    current_value = Column(Integer, default=0)
    target_value = Column(Integer, nullable=False)  # 从tasks复制

    # 状态
    status = Column(
        SQLEnum(UserTaskStatus, name="user_task_status"),
        default=UserTaskStatus.IN_PROGRESS,
        index=True
    )

    # 奖励
    reward_points = Column(Integer, nullable=False)  # 从tasks复制
    bonus_points = Column(Integer, default=0)
    is_claimed = Column(Boolean, default=False)

    # 完成次数（用于可重复任务）
    completion_count = Column(Integer, default=0, nullable=False)

    # 时间
    started_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    completed_at = Column(TIMESTAMP(timezone=True))
    claimed_at = Column(TIMESTAMP(timezone=True))
    expires_at = Column(TIMESTAMP(timezone=True), index=True)

    # 元数据
    task_metadata = Column(Text)  # JSON字符串

    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    task = relationship("Task", back_populates="user_tasks")

    # 约束
    __table_args__ = (
        CheckConstraint("current_value >= 0", name="check_current_value_non_negative"),
        CheckConstraint("target_value >= 1", name="check_ut_target_value_positive"),
        CheckConstraint("reward_points > 0", name="check_ut_reward_points_positive"),
        CheckConstraint("bonus_points >= 0", name="check_bonus_points_non_negative"),
    )

    @property
    def progress_percentage(self) -> float:
        """计算完成进度百分比"""
        if self.target_value == 0:
            return 0.0
        return min((self.current_value / self.target_value) * 100, 100.0)

    @property
    def is_completed(self) -> bool:
        """判断是否已完成"""
        return self.current_value >= self.target_value

    def __repr__(self):
        return f"<UserTask(id={self.id}, user_id={self.user_id}, task_id={self.task_id}, status={self.status.value}, progress={self.current_value}/{self.target_value})>"
