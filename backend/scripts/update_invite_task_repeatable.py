"""
更新邀请好友任务为可重复任务
每邀请1人可获得100积分，无限次
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.task import Task
from loguru import logger


async def update_invite_task():
    """更新邀请好友任务配置"""
    async with AsyncSessionLocal() as db:
        try:
            # 查找邀请好友任务
            result = await db.execute(
                select(Task).where(Task.task_key == "invite_friends")
            )
            invite_task = result.scalar_one_or_none()

            if not invite_task:
                logger.error("❌ 未找到邀请好友任务")
                return

            logger.info(f"📋 当前任务配置:")
            logger.info(f"   task_type: {invite_task.task_type}")
            logger.info(f"   max_completions_per_user: {invite_task.max_completions_per_user}")

            # 更新任务配置
            # 保持 task_type 为 ONCE，但移除完成次数限制
            # 这样每次邀请都会创建新的任务实例
            invite_task.max_completions_per_user = None  # 无限次

            await db.commit()
            await db.refresh(invite_task)

            logger.info(f"✅ 邀请好友任务已更新为可重复任务:")
            logger.info(f"   task_type: {invite_task.task_type}")
            logger.info(f"   max_completions_per_user: {invite_task.max_completions_per_user} (无限次)")
            logger.info(f"   每次邀请1人可获得 {invite_task.reward_points} 积分")

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 更新失败: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(update_invite_task())
