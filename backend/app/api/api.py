"""
API路由聚合
"""
from fastapi import APIRouter

from app.api.endpoints import referral, dashboard, leaderboard, points, teams, tasks, quiz, users

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(
    referral.router,
    prefix="/referral",
    tags=["推荐系统"]
)

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["仪表板"]
)

api_router.include_router(
    leaderboard.router,
    prefix="/leaderboard",
    tags=["排行榜"]
)

api_router.include_router(
    points.router,
    prefix="/points",
    tags=["积分系统"]
)

api_router.include_router(
    teams.router,
    prefix="/teams",
    tags=["战队系统"]
)

api_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["任务系统"]
)

api_router.include_router(
    quiz.router,
    prefix="/quiz",
    tags=["问答系统"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["用户管理"]
)
