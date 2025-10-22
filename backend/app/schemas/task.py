"""
任务系统 Pydantic Schemas
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.task import TaskType, TaskTrigger, UserTaskStatus


# ============= 任务配置 Schemas =============

class TaskBase(BaseModel):
    """任务基础信息"""
    task_key: str = Field(..., min_length=2, max_length=50, description="任务唯一标识")
    title: str = Field(..., min_length=2, max_length=100, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    icon_url: Optional[str] = Field(None, description="任务图标URL")
    task_type: TaskType = Field(..., description="任务类型")
    trigger_type: TaskTrigger = Field(TaskTrigger.MANUAL, description="触发方式")
    target_type: Optional[str] = Field(None, max_length=50, description="目标类型")
    target_value: int = Field(1, ge=1, description="目标值")
    reward_points: int = Field(..., gt=0, description="奖励积分")
    reward_experience: int = Field(0, ge=0, description="奖励经验")
    bonus_multiplier: float = Field(1.0, ge=1.0, le=5.0, description="奖励倍数")
    min_level_required: int = Field(1, ge=1, le=100, description="最低等级要求")
    max_completions_per_user: Optional[int] = Field(None, ge=1, description="每人最大完成次数")
    priority: int = Field(0, ge=0, description="优先级")
    sort_order: int = Field(0, description="排序顺序")
    is_active: bool = Field(True, description="是否激活")
    is_visible: bool = Field(True, description="是否可见")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")

    @field_validator('end_time')
    @classmethod
    def check_time_range(cls, v, info):
        """验证时间范围"""
        if v and 'start_time' in info.data and info.data['start_time']:
            if v <= info.data['start_time']:
                raise ValueError('end_time must be after start_time')
        return v


class TaskCreate(TaskBase):
    """创建任务请求"""
    pass


class TaskUpdate(BaseModel):
    """更新任务信息"""
    title: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    icon_url: Optional[str] = None
    trigger_type: Optional[TaskTrigger] = None
    target_type: Optional[str] = Field(None, max_length=50)
    target_value: Optional[int] = Field(None, ge=1)
    reward_points: Optional[int] = Field(None, gt=0)
    reward_experience: Optional[int] = Field(None, ge=0)
    bonus_multiplier: Optional[float] = Field(None, ge=1.0, le=5.0)
    min_level_required: Optional[int] = Field(None, ge=1, le=100)
    max_completions_per_user: Optional[int] = Field(None, ge=1)
    priority: Optional[int] = Field(None, ge=0)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    is_visible: Optional[bool] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class TaskResponse(TaskBase):
    """任务配置响应"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    """任务列表响应（分页）"""
    total: int
    page: int
    page_size: int
    data: List[TaskResponse]


# ============= 用户任务进度 Schemas =============

class UserTaskBase(BaseModel):
    """用户任务基础信息"""
    task_id: int = Field(..., gt=0, description="任务ID")
    current_value: int = Field(0, ge=0, description="当前进度")
    target_value: int = Field(..., ge=1, description="目标值")
    reward_points: int = Field(..., gt=0, description="奖励积分")
    bonus_points: int = Field(0, ge=0, description="额外奖励")
    status: UserTaskStatus = Field(UserTaskStatus.IN_PROGRESS, description="任务状态")


class UserTaskCreate(BaseModel):
    """领取/创建用户任务"""
    task_id: int = Field(..., gt=0, description="任务ID")
    user_id: int = Field(..., gt=0, description="用户ID")


class UserTaskProgress(BaseModel):
    """更新任务进度"""
    progress_delta: int = Field(..., ge=1, description="进度增量")


class UserTaskClaim(BaseModel):
    """领取任务奖励"""
    user_task_id: int = Field(..., gt=0, description="用户任务ID")


class UserTaskResponse(BaseModel):
    """用户任务响应"""
    id: int
    user_id: int
    task_id: int
    current_value: int
    target_value: int
    status: UserTaskStatus
    reward_points: int
    bonus_points: int
    is_claimed: bool
    progress_percentage: float
    is_completed: bool
    started_at: datetime
    completed_at: Optional[datetime]
    claimed_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    task_metadata: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserTaskDetailResponse(UserTaskResponse):
    """用户任务详细信息（含任务配置）"""
    task_title: Optional[str] = None
    task_description: Optional[str] = None
    task_icon_url: Optional[str] = None
    task_type: Optional[TaskType] = None


class UserTaskListResponse(BaseModel):
    """用户任务列表响应"""
    total: int
    page: int
    page_size: int
    data: List[UserTaskDetailResponse]


# ============= 任务统计 Schemas =============

class TaskStatistics(BaseModel):
    """任务统计信息"""
    task_id: int
    task_key: str
    task_title: str
    task_type: TaskType
    total_participants: int = Field(..., description="参与人数")
    total_completed: int = Field(..., description="完成人数")
    completion_rate: float = Field(..., description="完成率")
    total_rewards_distributed: int = Field(..., description="总发放奖励")
    average_completion_time: Optional[float] = Field(None, description="平均完成时间(秒)")


class UserTaskSummary(BaseModel):
    """用户任务汇总"""
    user_id: int
    total_tasks: int = Field(..., description="总任务数")
    available_tasks: int = Field(..., description="可领取")
    in_progress_tasks: int = Field(..., description="进行中")
    completed_tasks: int = Field(..., description="已完成")
    rewarded_tasks: int = Field(..., description="已领奖")
    expired_tasks: int = Field(..., description="已过期")
    total_points_earned: int = Field(..., description="总获得积分")
    total_experience_earned: int = Field(..., description="总获得经验")


# ============= 任务类型统计 Schemas =============

class TaskTypeStatistics(BaseModel):
    """任务类型统计"""
    task_type: TaskType
    total_tasks: int
    active_tasks: int
    total_completions: int
    total_rewards: int
