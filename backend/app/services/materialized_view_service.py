"""
物化视图服务
管理所有物化视图的刷新操作
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger
from datetime import datetime
from typing import Literal


class MaterializedViewService:
    """物化视图服务类 - 单一职责：管理物化视图刷新"""

    # 物化视图名称常量
    MV_POINTS_LEADERBOARD = "mv_points_leaderboard"
    MV_TEAMS_LEADERBOARD = "mv_teams_leaderboard"
    MV_QUIZ_LEADERBOARD = "mv_quiz_leaderboard"

    @staticmethod
    async def refresh_view(
        db: AsyncSession,
        view_name: str,
        concurrent: bool = True
    ) -> bool:
        """
        刷新指定的物化视图

        Args:
            db: 数据库会话
            view_name: 视图名称
            concurrent: 是否使用CONCURRENT模式（默认True，不阻塞查询）

        Returns:
            是否成功
        """
        try:
            start_time = datetime.utcnow()

            # CONCURRENT模式需要唯一索引，但不会阻塞SELECT查询
            concurrent_sql = "CONCURRENTLY" if concurrent else ""
            sql = text(f"REFRESH MATERIALIZED VIEW {concurrent_sql} {view_name};")

            await db.execute(sql)
            await db.commit()

            duration = (datetime.utcnow() - start_time).total_seconds()

            logger.info(
                f"✅ 物化视图刷新成功: view={view_name}, "
                f"concurrent={concurrent}, duration={duration:.3f}s"
            )

            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 物化视图刷新失败: view={view_name}, error={e}")
            raise

    @staticmethod
    async def refresh_points_leaderboard(
        db: AsyncSession,
        concurrent: bool = True
    ) -> bool:
        """
        刷新积分排行榜物化视图

        Args:
            db: 数据库会话
            concurrent: 是否使用CONCURRENT模式

        Returns:
            是否成功
        """
        return await MaterializedViewService.refresh_view(
            db=db,
            view_name=MaterializedViewService.MV_POINTS_LEADERBOARD,
            concurrent=concurrent
        )

    @staticmethod
    async def refresh_teams_leaderboard(
        db: AsyncSession,
        concurrent: bool = True
    ) -> bool:
        """
        刷新战队排行榜物化视图

        Args:
            db: 数据库会话
            concurrent: 是否使用CONCURRENT模式

        Returns:
            是否成功
        """
        return await MaterializedViewService.refresh_view(
            db=db,
            view_name=MaterializedViewService.MV_TEAMS_LEADERBOARD,
            concurrent=concurrent
        )

    @staticmethod
    async def refresh_quiz_leaderboard(
        db: AsyncSession,
        concurrent: bool = True
    ) -> bool:
        """
        刷新问答排行榜物化视图

        Args:
            db: 数据库会话
            concurrent: 是否使用CONCURRENT模式

        Returns:
            是否成功
        """
        return await MaterializedViewService.refresh_view(
            db=db,
            view_name=MaterializedViewService.MV_QUIZ_LEADERBOARD,
            concurrent=concurrent
        )

    @staticmethod
    async def refresh_all_leaderboards(
        db: AsyncSession,
        concurrent: bool = True
    ) -> dict:
        """
        刷新所有排行榜物化视图

        Args:
            db: 数据库会话
            concurrent: 是否使用CONCURRENT模式

        Returns:
            刷新结果字典
        """
        results = {
            "points": False,
            "teams": False,
            "quiz": False
        }

        try:
            # 刷新积分排行榜
            results["points"] = await MaterializedViewService.refresh_points_leaderboard(
                db, concurrent
            )
        except Exception as e:
            logger.error(f"积分排行榜刷新失败: {e}")

        try:
            # 刷新战队排行榜（如果已创建）
            results["teams"] = await MaterializedViewService.refresh_teams_leaderboard(
                db, concurrent
            )
        except Exception as e:
            logger.warning(f"战队排行榜刷新失败（可能未创建）: {e}")

        try:
            # 刷新问答排行榜（如果已创建）
            results["quiz"] = await MaterializedViewService.refresh_quiz_leaderboard(
                db, concurrent
            )
        except Exception as e:
            logger.warning(f"问答排行榜刷新失败（可能未创建）: {e}")

        success_count = sum(1 for v in results.values() if v)
        logger.info(f"📊 物化视图批量刷新完成: {success_count}/3 成功")

        return results

    @staticmethod
    async def get_view_stats(
        db: AsyncSession,
        view_name: str
    ) -> dict:
        """
        获取物化视图统计信息

        Args:
            db: 数据库会话
            view_name: 视图名称

        Returns:
            统计信息字典
        """
        try:
            # 查询行数
            count_sql = text(f"SELECT COUNT(*) as count FROM {view_name};")
            result = await db.execute(count_sql)
            count = result.scalar_one()

            # 查询视图大小
            size_sql = text("""
                SELECT pg_size_pretty(pg_total_relation_size(:view_name::regclass)) as size;
            """)
            result = await db.execute(size_sql, {"view_name": view_name})
            size = result.scalar_one()

            return {
                "view_name": view_name,
                "row_count": count,
                "size": size
            }

        except Exception as e:
            logger.error(f"❌ 获取视图统计失败: view={view_name}, error={e}")
            return {
                "view_name": view_name,
                "row_count": 0,
                "size": "0 bytes",
                "error": str(e)
            }
