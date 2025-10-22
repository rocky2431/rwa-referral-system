"""
迁移可重复任务模型
添加completion_count字段，合并重复的UserTask实例
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal, engine
from app.models.task import UserTask
from loguru import logger


async def add_completion_count_column():
    """添加completion_count列到user_tasks表"""
    async with engine.begin() as conn:
        try:
            # 检查列是否已存在
            result = await conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='user_tasks' AND column_name='completion_count'
            """))

            if result.scalar_one_or_none():
                logger.info("✅ completion_count列已存在，跳过创建")
                return

            # 添加列
            await conn.execute(text("""
                ALTER TABLE user_tasks
                ADD COLUMN completion_count INTEGER DEFAULT 0 NOT NULL
            """))

            logger.info("✅ 成功添加completion_count列")

        except Exception as e:
            logger.error(f"❌ 添加列失败: {e}")
            raise


async def merge_duplicate_user_tasks():
    """合并同一用户同一任务的多个实例"""
    async with AsyncSessionLocal() as db:
        try:
            # 查找所有邀请任务的重复实例
            query = text("""
                SELECT user_id, task_id, COUNT(*) as count
                FROM user_tasks
                WHERE task_id IN (SELECT id FROM tasks WHERE task_key = 'invite_friends')
                GROUP BY user_id, task_id
                HAVING COUNT(*) > 1
            """)

            result = await db.execute(query)
            duplicates = result.fetchall()

            logger.info(f"📋 找到 {len(duplicates)} 个用户有重复的邀请任务实例")

            for user_id, task_id, count in duplicates:
                # 获取该用户该任务的所有实例（按时间排序）
                instances_result = await db.execute(
                    select(UserTask)
                    .where(UserTask.user_id == user_id, UserTask.task_id == task_id)
                    .order_by(UserTask.created_at.asc())
                )
                instances = list(instances_result.scalars().all())

                if not instances:
                    continue

                # 保留第一个实例，合并其他实例的数据
                primary = instances[0]
                duplicates_to_delete = instances[1:]

                # 统计总完成次数
                total_completions = sum(
                    1 for inst in instances
                    if inst.status in ['completed', 'claimed']
                )

                # 更新主实例
                primary.completion_count = total_completions

                # 如果有任何一个实例已领取，设置为已领取
                if any(inst.status == 'claimed' for inst in instances):
                    primary.status = 'claimed'
                    primary.is_claimed = True
                    primary.claimed_at = max(
                        (inst.claimed_at for inst in instances if inst.claimed_at),
                        default=None
                    )
                # 否则检查是否有完成的
                elif any(inst.status == 'completed' for inst in instances):
                    primary.status = 'completed'
                    primary.completed_at = max(
                        (inst.completed_at for inst in instances if inst.completed_at),
                        default=None
                    )

                # 删除重复实例
                for duplicate in duplicates_to_delete:
                    await db.delete(duplicate)
                    logger.info(
                        f"🗑️  删除重复实例: "
                        f"user_id={user_id}, "
                        f"user_task_id={duplicate.id}"
                    )

                logger.info(
                    f"✅ 合并完成: "
                    f"user_id={user_id}, "
                    f"保留ID={primary.id}, "
                    f"删除{len(duplicates_to_delete)}个实例, "
                    f"总完成次数={total_completions}"
                )

            await db.commit()
            logger.info(f"🎉 合并完成！处理了{len(duplicates)}个用户的重复任务")

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 合并失败: {e}")
            raise


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始迁移可重复任务模型")
    logger.info("=" * 60)

    # 步骤1: 添加completion_count列
    logger.info("\n步骤1: 添加completion_count列")
    await add_completion_count_column()

    # 步骤2: 合并重复的UserTask实例
    logger.info("\n步骤2: 合并重复的UserTask实例")
    await merge_duplicate_user_tasks()

    logger.info("\n" + "=" * 60)
    logger.info("✅ 迁移完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
