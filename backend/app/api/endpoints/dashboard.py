"""
仪表板API端点
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Optional

from app.db.session import get_db
from app.models import User, UserPoints, ReferralRelation

router = APIRouter()


class DashboardData(BaseModel):
    """仪表板数据"""
    total_rewards: str
    referred_count: int
    is_active: bool
    days_since_active: int
    referrer: str
    invite_code: str
    referral_link: str


@router.get("/{address}", response_model=DashboardData)
async def get_dashboard(address: str, db: AsyncSession = Depends(get_db)):
    """
    获取用户仪表板数据（基于数据库）

    包含用户的总奖励、推荐人数、活跃状态等信息
    """
    try:
        # 查询用户信息
        user_query = select(User).where(User.wallet_address == address.lower())
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            # 用户不存在，返回默认值
            return {
                "total_rewards": "0",
                "referred_count": 0,
                "is_active": False,
                "days_since_active": -1,
                "referrer": "0x0000000000000000000000000000000000000000",
                "invite_code": "",
                "referral_link": ""
            }

        # 查询用户积分信息
        points_query = select(UserPoints).where(UserPoints.user_id == user.id)
        points_result = await db.execute(points_query)
        points = points_result.scalar_one_or_none()

        # 计算总积分（作为奖励）
        total_points = points.available_points + points.frozen_points if points else 0

        # 查询推荐人数
        referral_count_query = select(func.count(ReferralRelation.id)).where(
            ReferralRelation.referrer_id == user.id,
            ReferralRelation.is_active == True
        )
        referral_count_result = await db.execute(referral_count_query)
        referred_count = referral_count_result.scalar() or 0

        # 查询推荐人信息
        referrer_query = select(User).join(
            ReferralRelation,
            ReferralRelation.referrer_id == User.id
        ).where(ReferralRelation.referee_id == user.id)
        referrer_result = await db.execute(referrer_query)
        referrer_user = referrer_result.scalar_one_or_none()

        referrer_address = referrer_user.wallet_address if referrer_user else "0x0000000000000000000000000000000000000000"

        # 计算最后活跃天数
        if user.last_active_at:
            days_ago = (datetime.utcnow() - user.last_active_at).days
        else:
            days_ago = -1

        # 判断是否活跃（7天内有活动）
        is_active = days_ago >= 0 and days_ago < 7

        # 生成邀请码和推荐链接
        invite_code = f"USER{user.id:06d}"
        referral_link = f"http://localhost:5173/?ref={invite_code}"

        return {
            "total_rewards": str(total_points),
            "referred_count": int(referred_count),
            "is_active": is_active,
            "days_since_active": days_ago,
            "referrer": referrer_address,
            "invite_code": invite_code,
            "referral_link": referral_link
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表板数据失败: {str(e)}")
