"""
排行榜API端点
基于物化视图提供高性能排行榜查询
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.services.leaderboard_service import LeaderboardService
from app.services.materialized_view_service import MaterializedViewService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


# ========== Response Models ==========

class LeaderboardEntry(BaseModel):
    """积分排行榜条目"""
    rank: int = Field(..., description="排名")
    user_id: int = Field(..., description="用户ID")
    wallet_address: str = Field(..., description="钱包地址")
    username: Optional[str] = Field(None, description="用户名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    total_points: int = Field(..., description="总积分")
    level: int = Field(..., description="等级")
    total_invited: int = Field(0, description="邀请人数")
    total_tasks_completed: int = Field(0, description="完成任务数")
    available_points: int = Field(..., description="可用积分")
    total_earned: int = Field(..., description="累计获得积分")
    points_from_referral: int = Field(0, description="推荐奖励积分")
    points_from_tasks: int = Field(0, description="任务积分")
    points_from_quiz: int = Field(0, description="问答积分")
    points_from_team: int = Field(0, description="战队积分")
    created_at: Optional[str] = Field(None, description="创建时间")
    last_active_at: Optional[str] = Field(None, description="最后活跃时间")


class LeaderboardResponse(BaseModel):
    """排行榜响应"""
    total: int = Field(..., description="总用户数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    entries: List[LeaderboardEntry] = Field(..., description="排行榜条目")


class UserRankResponse(BaseModel):
    """用户排名响应"""
    rank: Optional[int] = Field(None, description="排名")
    user_id: int = Field(..., description="用户ID")
    wallet_address: str = Field(..., description="钱包地址")
    username: Optional[str] = Field(None, description="用户名")
    total_points: int = Field(..., description="总积分")
    level: int = Field(..., description="等级")
    available_points: int = Field(..., description="可用积分")


class LeaderboardStatsResponse(BaseModel):
    """排行榜统计响应"""
    total_users: int = Field(..., description="总用户数")
    total_points_distributed: int = Field(..., description="已分配总积分")
    avg_points_per_user: float = Field(..., description="人均积分")
    max_points: int = Field(..., description="最高积分")
    min_points: int = Field(..., description="最低积分")


class RefreshResponse(BaseModel):
    """刷新响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")


# ========== API Endpoints ==========

@router.get("/points", response_model=LeaderboardResponse)
async def get_points_leaderboard(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取积分排行榜

    基于物化视图提供高性能查询，支持分页
    """
    try:
        leaderboard, total = await LeaderboardService.get_points_leaderboard(
            db=db,
            page=page,
            page_size=page_size,
            use_cache=True
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "entries": leaderboard
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询排行榜失败: {str(e)}")


@router.get("/points/user/{user_id}", response_model=UserRankResponse)
async def get_user_rank(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    查询指定用户的排名

    返回用户在积分排行榜中的位置和基本信息
    """
    try:
        rank_data = await LeaderboardService.get_user_rank(db=db, user_id=user_id)

        if not rank_data:
            raise HTTPException(status_code=404, detail="用户未找到或未上榜")

        return rank_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询用户排名失败: {str(e)}")


@router.get("/points/top/{limit}")
async def get_top_users(
    limit: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取积分Top N用户（快速查询）

    用于首页展示、榜单预览等场景
    """
    try:
        top_users = await LeaderboardService.get_top_users(db=db, limit=limit)
        return {"count": len(top_users), "users": top_users}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询Top用户失败: {str(e)}")


@router.get("/points/stats", response_model=LeaderboardStatsResponse)
async def get_leaderboard_stats(db: AsyncSession = Depends(get_db)):
    """
    获取排行榜统计信息

    包括总用户数、总积分、平均积分等
    """
    try:
        stats = await LeaderboardService.get_leaderboard_stats(db=db)
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_leaderboard(
    concurrent: bool = Query(True, description="是否并发刷新"),
    db: AsyncSession = Depends(get_db)
):
    """
    手动刷新积分排行榜物化视图

    注意：此操作需要管理员权限（实际使用时应添加权限验证）
    """
    try:
        success = await MaterializedViewService.refresh_points_leaderboard(
            db=db,
            concurrent=concurrent
        )

        return {
            "success": success,
            "message": "积分排行榜刷新成功" if success else "刷新失败"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新失败: {str(e)}")
