"""
排行榜服务
提供所有排行榜查询功能，基于物化视图实现高性能查询
"""
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger

from app.services.cache_service import CacheService
from app.services.materialized_view_service import MaterializedViewService


class LeaderboardService:
    """排行榜服务类"""

    @staticmethod
    async def get_points_leaderboard(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 50,
        use_cache: bool = True
    ) -> Tuple[List[dict], int]:
        """
        获取积分排行榜（基于物化视图）

        Args:
            db: 数据库会话
            page: 页码（从1开始）
            page_size: 每页大小
            use_cache: 是否使用缓存

        Returns:
            (排行榜数据, 总数)
        """
        try:
            # 1. 尝试从缓存获取
            if use_cache:
                cached_data = await CacheService.get_leaderboard_cache("points", page)
                if cached_data:
                    logger.debug(f"🎯 积分排行榜缓存命中: page={page}")
                    return cached_data["data"], cached_data["total"]

            # 2. 缓存未命中，从物化视图查询
            offset = (page - 1) * page_size

            # 查询总数
            count_sql = text("SELECT COUNT(*) FROM mv_points_leaderboard;")
            total_result = await db.execute(count_sql)
            total = total_result.scalar_one()

            # 分页查询
            query_sql = text("""
                SELECT
                    rank,
                    user_id,
                    wallet_address,
                    username,
                    avatar_url,
                    total_points,
                    level,
                    total_invited,
                    total_tasks_completed,
                    total_questions_answered,
                    correct_answers,
                    available_points,
                    total_earned,
                    total_spent,
                    points_from_referral,
                    points_from_tasks,
                    points_from_quiz,
                    points_from_team,
                    points_from_purchase,
                    created_at,
                    last_active_at
                FROM mv_points_leaderboard
                ORDER BY rank ASC
                LIMIT :limit OFFSET :offset;
            """)

            result = await db.execute(
                query_sql,
                {"limit": page_size, "offset": offset}
            )

            rows = result.fetchall()

            # 转换为字典列表
            leaderboard = []
            for row in rows:
                leaderboard.append({
                    "rank": row.rank,
                    "user_id": row.user_id,
                    "wallet_address": row.wallet_address,
                    "username": row.username,
                    "avatar_url": row.avatar_url,
                    "total_points": row.total_points,
                    "level": row.level,
                    "total_invited": row.total_invited,
                    "total_tasks_completed": row.total_tasks_completed,
                    "total_questions_answered": row.total_questions_answered,
                    "correct_answers": row.correct_answers,
                    "available_points": row.available_points,
                    "total_earned": row.total_earned,
                    "total_spent": row.total_spent,
                    "points_from_referral": row.points_from_referral,
                    "points_from_tasks": row.points_from_tasks,
                    "points_from_quiz": row.points_from_quiz,
                    "points_from_team": row.points_from_team,
                    "points_from_purchase": row.points_from_purchase,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "last_active_at": row.last_active_at.isoformat() if row.last_active_at else None
                })

            # 3. 写入缓存
            if use_cache:
                cache_data = {"data": leaderboard, "total": total}
                await CacheService.set_leaderboard_cache("points", page, cache_data)
                logger.debug(f"💾 积分排行榜已缓存: page={page}, count={len(leaderboard)}")

            logger.info(
                f"📊 积分排行榜查询成功: page={page}, "
                f"page_size={page_size}, total={total}, count={len(leaderboard)}"
            )

            return leaderboard, total

        except Exception as e:
            logger.error(f"❌ 积分排行榜查询失败: {e}")
            raise

    @staticmethod
    async def get_user_rank(
        db: AsyncSession,
        user_id: int
    ) -> Optional[dict]:
        """
        查询用户在积分排行榜中的排名

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            用户排名数据，不存在返回None
        """
        try:
            query_sql = text("""
                SELECT
                    rank,
                    user_id,
                    wallet_address,
                    username,
                    total_points,
                    level,
                    available_points
                FROM mv_points_leaderboard
                WHERE user_id = :user_id;
            """)

            result = await db.execute(query_sql, {"user_id": user_id})
            row = result.fetchone()

            if not row:
                return None

            return {
                "rank": row.rank,
                "user_id": row.user_id,
                "wallet_address": row.wallet_address,
                "username": row.username,
                "total_points": row.total_points,
                "level": row.level,
                "available_points": row.available_points
            }

        except Exception as e:
            logger.error(f"❌ 查询用户排名失败: user_id={user_id}, error={e}")
            return None

    @staticmethod
    async def get_top_users(
        db: AsyncSession,
        limit: int = 10
    ) -> List[dict]:
        """
        获取积分Top N用户（快速查询）

        Args:
            db: 数据库会话
            limit: 数量限制

        Returns:
            Top N用户列表
        """
        try:
            query_sql = text("""
                SELECT
                    rank,
                    user_id,
                    wallet_address,
                    username,
                    avatar_url,
                    total_points,
                    level
                FROM mv_points_leaderboard
                ORDER BY rank ASC
                LIMIT :limit;
            """)

            result = await db.execute(query_sql, {"limit": limit})
            rows = result.fetchall()

            top_users = []
            for row in rows:
                top_users.append({
                    "rank": row.rank,
                    "user_id": row.user_id,
                    "wallet_address": row.wallet_address,
                    "username": row.username,
                    "avatar_url": row.avatar_url,
                    "total_points": row.total_points,
                    "level": row.level
                })

            return top_users

        except Exception as e:
            logger.error(f"❌ 查询Top用户失败: {e}")
            return []

    @staticmethod
    async def get_leaderboard_stats(db: AsyncSession) -> dict:
        """
        获取排行榜统计信息

        Args:
            db: 数据库会话

        Returns:
            统计信息字典
        """
        try:
            stats_sql = text("""
                SELECT
                    COUNT(*) as total_users,
                    SUM(total_points) as total_points_distributed,
                    AVG(total_points) as avg_points_per_user,
                    MAX(total_points) as max_points,
                    MIN(total_points) as min_points
                FROM mv_points_leaderboard;
            """)

            result = await db.execute(stats_sql)
            row = result.fetchone()

            return {
                "total_users": row.total_users or 0,
                "total_points_distributed": int(row.total_points_distributed or 0),
                "avg_points_per_user": float(row.avg_points_per_user or 0),
                "max_points": row.max_points or 0,
                "min_points": row.min_points or 0
            }

        except Exception as e:
            logger.error(f"❌ 获取排行榜统计失败: {e}")
            return {
                "total_users": 0,
                "total_points_distributed": 0,
                "avg_points_per_user": 0.0,
                "max_points": 0,
                "min_points": 0
            }
