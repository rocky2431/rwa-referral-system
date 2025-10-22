"""
迁移现有任务状态到新的状态系统
CLAIMED → REWARDED
COMPLETED 保持不变（表示已完成待领奖）
IN_PROGRESS 保持不变
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from loguru import logger


async def migrate_statuses():
    """迁移所有CLAIMED状态到REWARDED"""
    async with AsyncSessionLocal() as db:
        try:
            # 1. 统计当前状态分布
            logger.info("📊 统计当前状态分布...")
            result = await db.execute(text("""
                SELECT status, COUNT(*) as count
                FROM user_tasks
                GROUP BY status
                ORDER BY count DESC
            """))

            stats = result.fetchall()
            logger.info("当前状态统计:")
            for status, count in stats:
                logger.info(f"  {status}: {count}条")

            # 2. 将 CLAIMED 迁移到 REWARDED
            logger.info("\n🔄 开始迁移 CLAIMED → REWARDED...")
            result = await db.execute(text("""
                UPDATE user_tasks
                SET status = 'rewarded'
                WHERE status = 'claimed'
                RETURNING id
            """))

            migrated_ids = [row[0] for row in result.fetchall()]
            logger.info(f"✅ 成功迁移 {len(migrated_ids)} 条记录")

            await db.commit()

            # 3. 验证迁移结果
            logger.info("\n✅ 迁移完成，验证结果...")
            result = await db.execute(text("""
                SELECT status, COUNT(*) as count
                FROM user_tasks
                GROUP BY status
                ORDER BY count DESC
            """))

            stats = result.fetchall()
            logger.info("迁移后状态统计:")
            for status, count in stats:
                logger.info(f"  {status}: {count}条")

            # 4. 检查是否还有CLAIMED状态
            result = await db.execute(text("""
                SELECT COUNT(*) FROM user_tasks WHERE status = 'claimed'
            """))
            claimed_count = result.scalar()

            if claimed_count == 0:
                logger.info("🎉 所有CLAIMED状态已成功迁移！")
            else:
                logger.warning(f"⚠️  仍有 {claimed_count} 条CLAIMED状态记录")

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 迁移失败: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(migrate_statuses())
