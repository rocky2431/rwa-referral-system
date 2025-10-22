"""
修复枚举大小写问题并迁移数据
1. 添加大写版本的新枚举值(AVAILABLE, REWARDED)
2. 迁移 CLAIMED → REWARDED
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import engine, AsyncSessionLocal
from loguru import logger


async def fix_enum_and_migrate():
    """修复枚举值并迁移数据"""

    # Step 1: 添加大写版本的枚举值
    async with engine.begin() as conn:
        try:
            logger.info("📝 步骤1: 添加大写枚举值...")

            await conn.execute(text(
                "ALTER TYPE user_task_status ADD VALUE IF NOT EXISTS 'AVAILABLE'"
            ))
            logger.info("✅ 添加 AVAILABLE (大写)")

            await conn.execute(text(
                "ALTER TYPE user_task_status ADD VALUE IF NOT EXISTS 'REWARDED'"
            ))
            logger.info("✅ 添加 REWARDED (大写)")

        except Exception as e:
            logger.error(f"❌ 添加枚举值失败: {e}")
            raise

    # Step 2: 迁移数据
    async with AsyncSessionLocal() as db:
        try:
            logger.info("\n📊 步骤2: 统计当前状态分布...")
            result = await db.execute(text("""
                SELECT status, COUNT(*) as count
                FROM user_tasks
                GROUP BY status
                ORDER BY count DESC
            """))

            stats = result.fetchall()
            logger.info("迁移前状态统计:")
            for status, count in stats:
                logger.info(f"  {status}: {count}条")

            logger.info("\n🔄 步骤3: 迁移 CLAIMED → REWARDED...")
            result = await db.execute(text("""
                UPDATE user_tasks
                SET status = 'REWARDED'
                WHERE status = 'CLAIMED'
                RETURNING id
            """))

            migrated_ids = [row[0] for row in result.fetchall()]
            logger.info(f"✅ 成功迁移 {len(migrated_ids)} 条记录")

            await db.commit()

            logger.info("\n📊 步骤4: 验证迁移结果...")
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

            # 检查是否还有CLAIMED状态
            result = await db.execute(text("""
                SELECT COUNT(*) FROM user_tasks WHERE status = 'CLAIMED'
            """))
            claimed_count = result.scalar()

            if claimed_count == 0:
                logger.info("\n🎉 所有CLAIMED状态已成功迁移到REWARDED！")
            else:
                logger.warning(f"\n⚠️  仍有 {claimed_count} 条CLAIMED状态记录")

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 迁移失败: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(fix_enum_and_migrate())
