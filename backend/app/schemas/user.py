"""
用户系统 Pydantic Schemas

职责：用户注册、查询、更新的请求和响应模型
设计原则：SRP（单一职责），每个模型专注于特定场景
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re


class UserRegisterRequest(BaseModel):
    """用户注册请求模型"""

    wallet_address: str = Field(
        ...,
        description="钱包地址",
        min_length=42,
        max_length=42,
        pattern=r"^0x[a-fA-F0-9]{40}$"
    )
    username: Optional[str] = Field(
        None,
        description="用户名（可选）",
        min_length=2,
        max_length=50
    )
    avatar_url: Optional[str] = Field(None, description="头像URL（可选）")
    email: Optional[str] = Field(None, description="邮箱（可选）", max_length=100)
    invite_code: Optional[str] = Field(
        None,
        description="邀请码（可选，格式：USER000001）",
        min_length=10,
        max_length=10,
        pattern=r"^USER\d{6}$"
    )

    @field_validator("wallet_address")
    @classmethod
    def normalize_wallet_address(cls, v: str) -> str:
        """钱包地址规范化：转为小写"""
        return v.lower()


class UserResponse(BaseModel):
    """用户基础信息响应模型"""

    id: int = Field(..., description="用户ID")
    wallet_address: str = Field(..., description="钱包地址")
    username: Optional[str] = Field(None, description="用户名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    level: int = Field(..., description="等级")
    experience: int = Field(..., description="经验值")
    total_points: int = Field(..., description="总积分")
    is_active: bool = Field(..., description="是否活跃")
    created_at: datetime = Field(..., description="创建时间")

    model_config = ConfigDict(from_attributes=True)


class UserDetailResponse(BaseModel):
    """用户详细信息响应模型（包含统计数据）"""

    id: int = Field(..., description="用户ID")
    wallet_address: str = Field(..., description="钱包地址")
    username: Optional[str] = Field(None, description="用户名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    email: Optional[str] = Field(None, description="邮箱")

    # 等级系统
    level: int = Field(..., description="等级")
    experience: int = Field(..., description="经验值")

    # 统计数据
    total_points: int = Field(..., description="总积分")
    total_invited: int = Field(..., description="邀请总人数")
    total_tasks_completed: int = Field(..., description="完成任务数")
    total_questions_answered: int = Field(..., description="答题总数")
    correct_answers: int = Field(..., description="答对题数")

    # 活跃度
    last_active_at: Optional[datetime] = Field(None, description="最后活跃时间")
    consecutive_login_days: int = Field(..., description="连续登录天数")
    last_login_date: Optional[datetime] = Field(None, description="最后登录日期")

    # 状态
    is_active: bool = Field(..., description="是否活跃")
    is_banned: bool = Field(..., description="是否被封禁")
    banned_until: Optional[datetime] = Field(None, description="封禁截止时间")

    # 时间戳
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class UserUpdateRequest(BaseModel):
    """用户信息更新请求模型"""

    username: Optional[str] = Field(None, description="用户名", min_length=2, max_length=50)
    avatar_url: Optional[str] = Field(None, description="头像URL")
    email: Optional[str] = Field(None, description="邮箱", max_length=100)


class UserByWalletResponse(BaseModel):
    """通过钱包地址查询用户响应（快速查询）"""

    exists: bool = Field(..., description="用户是否存在")
    user_id: Optional[int] = Field(None, description="用户ID（如果存在）")
    wallet_address: str = Field(..., description="钱包地址")
    username: Optional[str] = Field(None, description="用户名")
    level: Optional[int] = Field(None, description="等级")
    total_points: Optional[int] = Field(None, description="总积分")
