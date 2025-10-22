"""
战队系统 Pydantic Schemas
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.team_member import TeamMemberRole, TeamMemberStatus
from app.models.team_task import TeamTaskStatus


# ============= 战队 Schemas =============

class TeamBase(BaseModel):
    """战队基础信息"""
    name: str = Field(..., min_length=2, max_length=50, description="战队名称")
    description: Optional[str] = Field(None, max_length=500, description="战队描述")
    logo_url: Optional[str] = Field(None, description="战队Logo URL")
    is_public: bool = Field(True, description="是否公开")
    require_approval: bool = Field(False, description="是否需要审批")
    max_members: int = Field(100, ge=1, le=1000, description="最大成员数")


class TeamCreate(TeamBase):
    """创建战队请求"""
    pass


class TeamUpdate(BaseModel):
    """更新战队信息"""
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = None
    is_public: Optional[bool] = None
    require_approval: Optional[bool] = None
    max_members: Optional[int] = Field(None, ge=1, le=1000)


class TeamResponse(TeamBase):
    """战队响应"""
    id: int
    captain_id: int
    member_count: int
    total_points: int
    active_member_count: int
    level: int
    experience: int
    reward_pool: int
    last_distribution_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    disbanded_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class TeamDetailResponse(TeamResponse):
    """战队详细信息（包含队长信息）"""
    captain_name: Optional[str] = None
    captain_wallet: Optional[str] = None


class TeamListResponse(BaseModel):
    """战队列表响应（分页）"""
    total: int
    page: int
    page_size: int
    data: List[TeamResponse]


# ============= 战队成员 Schemas =============

class TeamMemberBase(BaseModel):
    """战队成员基础"""
    team_id: int
    user_id: int


class TeamMemberJoinRequest(BaseModel):
    """加入战队请求"""
    team_id: int = Field(..., gt=0, description="战队ID")


class TeamMemberResponse(BaseModel):
    """战队成员响应"""
    id: int
    team_id: int
    user_id: int
    role: TeamMemberRole
    contribution_points: int
    tasks_completed: int
    status: TeamMemberStatus
    joined_at: Optional[datetime]
    approved_at: Optional[datetime]
    left_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamMemberDetailResponse(TeamMemberResponse):
    """战队成员详细信息（含用户信息）"""
    username: Optional[str] = None
    wallet_address: Optional[str] = None
    avatar_url: Optional[str] = None


class TeamMemberListResponse(BaseModel):
    """战队成员列表响应"""
    total: int
    data: List[TeamMemberDetailResponse]


class TeamMemberUpdateRole(BaseModel):
    """更新成员角色"""
    user_id: int = Field(..., gt=0)
    role: TeamMemberRole = Field(...)


class TeamMemberApproval(BaseModel):
    """审批成员申请"""
    user_id: int = Field(..., gt=0)
    approved: bool = Field(..., description="true=通过, false=拒绝")


# ============= 战队任务 Schemas =============

class TeamTaskBase(BaseModel):
    """战队任务基础"""
    title: str = Field(..., min_length=2, max_length=100, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    task_type: str = Field(..., description="任务类型")
    target_value: int = Field(..., gt=0, description="目标值")
    reward_points: int = Field(..., ge=0, description="奖励积分")
    bonus_points: int = Field(0, ge=0, description="额外奖励")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")

    @field_validator('end_time')
    @classmethod
    def check_time_range(cls, v, info):
        """验证时间范围"""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('end_time must be after start_time')
        return v


class TeamTaskCreate(TeamTaskBase):
    """创建战队任务"""
    team_id: int = Field(..., gt=0, description="战队ID")


class TeamTaskUpdate(BaseModel):
    """更新战队任务"""
    title: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    target_value: Optional[int] = Field(None, gt=0)
    reward_points: Optional[int] = Field(None, ge=0)
    bonus_points: Optional[int] = Field(None, ge=0)
    end_time: Optional[datetime] = None


class TeamTaskResponse(TeamTaskBase):
    """战队任务响应"""
    id: int
    team_id: int
    current_value: int
    progress_percentage: float
    is_completed: bool
    status: TeamTaskStatus
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamTaskListResponse(BaseModel):
    """战队任务列表响应"""
    total: int
    data: List[TeamTaskResponse]


# ============= 战队排行榜 Schemas =============

class TeamLeaderboardItem(BaseModel):
    """战队排行榜项"""
    rank: int
    team_id: int
    team_name: str
    team_logo_url: Optional[str]
    total_points: int
    member_count: int
    level: int
    captain_name: Optional[str]


class TeamLeaderboardResponse(BaseModel):
    """战队排行榜响应"""
    total: int
    page: int
    page_size: int
    data: List[TeamLeaderboardItem]


# ============= 战队统计 Schemas =============

class TeamStatistics(BaseModel):
    """战队统计信息"""
    team_id: int
    total_members: int
    active_members: int
    total_points: int
    total_tasks: int
    completed_tasks: int
    reward_pool: int
    average_contribution: float
