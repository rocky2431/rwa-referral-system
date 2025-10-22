"""
积分系统 Pydantic Schemas
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.point_transaction import PointTransactionType


class UserPointsResponse(BaseModel):
    """用户积分响应模型"""

    user_id: int = Field(..., description="用户ID")
    available_points: int = Field(..., description="可用积分")
    frozen_points: int = Field(..., description="冻结积分")
    total_earned: int = Field(..., description="累计获得")
    total_spent: int = Field(..., description="累计消费")
    points_from_referral: int = Field(..., description="推荐奖励积分")
    points_from_tasks: int = Field(..., description="任务奖励积分")
    points_from_quiz: int = Field(..., description="答题奖励积分")
    points_from_team: int = Field(..., description="战队奖励积分")
    points_from_purchase: int = Field(..., description="购买奖励积分")

    model_config = ConfigDict(from_attributes=True)


class PointTransactionResponse(BaseModel):
    """积分交易流水响应模型"""

    id: int = Field(..., description="交易ID")
    user_id: int = Field(..., description="用户ID")
    transaction_type: PointTransactionType = Field(..., description="交易类型")
    amount: int = Field(..., description="积分数量(正数=获得,负数=消费)")
    balance_after: int = Field(..., description="交易后余额")
    description: Optional[str] = Field(None, description="交易描述")
    status: str = Field(..., description="交易状态")
    created_at: datetime = Field(..., description="创建时间")

    # 关联信息
    related_user_id: Optional[int] = Field(None, description="关联用户ID")
    related_task_id: Optional[int] = Field(None, description="关联任务ID")
    related_team_id: Optional[int] = Field(None, description="关联战队ID")
    related_question_id: Optional[int] = Field(None, description="关联题目ID")

    model_config = ConfigDict(from_attributes=True)


class PointTransactionCreate(BaseModel):
    """创建积分交易请求模型"""

    user_id: int = Field(..., description="用户ID", gt=0)
    amount: int = Field(..., description="积分数量", ne=0)
    transaction_type: PointTransactionType = Field(..., description="交易类型")
    description: Optional[str] = Field(None, description="交易描述", max_length=200)

    # 关联信息(可选)
    related_user_id: Optional[int] = Field(None, description="关联用户ID")
    related_task_id: Optional[int] = Field(None, description="关联任务ID")
    related_team_id: Optional[int] = Field(None, description="关联战队ID")
    related_question_id: Optional[int] = Field(None, description="关联题目ID")

    # 幂等性Key
    idempotency_key: Optional[str] = Field(None, description="幂等性Key", max_length=100)


class PointsHistoryResponse(BaseModel):
    """积分历史响应模型(分页)"""

    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    data: List[PointTransactionResponse] = Field(..., description="交易记录列表")


class PointsStatistics(BaseModel):
    """积分统计模型"""

    total_users: int = Field(..., description="总用户数")
    total_points_distributed: int = Field(..., description="总发放积分")
    total_points_spent: int = Field(..., description="总消费积分")
    referral_points: int = Field(..., description="推荐奖励积分")
    task_points: int = Field(..., description="任务奖励积分")
    quiz_points: int = Field(..., description="答题奖励积分")
    team_points: int = Field(..., description="战队奖励积分")


class PointsExchangeRequest(BaseModel):
    """积分兑换请求模型"""

    user_id: int = Field(..., description="用户ID", gt=0)
    points_amount: int = Field(..., description="兑换积分数量", gt=0)
    exchange_type: str = Field(..., description="兑换类型 (token/nft/privilege)", max_length=50)
    target_address: Optional[str] = Field(None, description="目标接收地址 (代币/NFT)", max_length=100)
    idempotency_key: Optional[str] = Field(None, description="幂等性Key", max_length=100)


class PointsExchangeResponse(BaseModel):
    """积分兑换响应模型"""

    transaction_id: int = Field(..., description="交易ID")
    user_id: int = Field(..., description="用户ID")
    points_spent: int = Field(..., description="消费积分数")
    exchange_type: str = Field(..., description="兑换类型")
    status: str = Field(..., description="兑换状态 (pending/completed/failed)")
    balance_after: int = Field(..., description="兑换后积分余额")
    target_address: Optional[str] = Field(None, description="目标接收地址")
    created_at: datetime = Field(..., description="兑换时间")
