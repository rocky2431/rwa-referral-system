"""
删除补发的历史任务记录
因为现在用户可以手动领取奖励了
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, select
from app.db.session import AsyncSessionLocal
from app.models.task import UserTask
from loguru import logger


async def delete_backfilled_tasks():
    """删除所有补发的任务记录"""
    async with AsyncSessionLocal() as db:
        try:
            # 查询所有补发的任务（task_id = 4 或 5，且已完成但未领取）
            result = await db.execute(
                select(UserTask).where(
                    UserTask.task_id.in_([4, 5]),  # 注册任务和邀请任务
                    UserTask.status == 'completed',
                    UserTask.is_claimed == False
                )
            )
            backfilled_tasks = result.scalars().all()

            logger.info(f"📋 找到 {len(backfilled_tasks)} 个补发的任务记录")

            # 删除这些任务
            for task in backfilled_tasks:
                await db.delete(task)
                logger.info(f"🗑️  删除: user_id={task.user_id}, task_id={task.task_id}")

            await db.commit()
            logger.info(f"✅ 成功删除 {len(backfilled_tasks)} 个补发任务记录！")

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 删除失败: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(delete_backfilled_tasks())
