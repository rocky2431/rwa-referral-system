"""
更新数据库枚举类型
添加新的积分交易类型
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import engine
from loguru import logger


async def update_enum_types():
    """更新枚举类型"""
    async with engine.begin() as conn:
        try:
            # 添加新的枚举值
            await conn.execute(text(
                "ALTER TYPE point_transaction_type ADD VALUE IF NOT EXISTS 'register_reward'"
            ))
            logger.info("✅ 添加 register_reward 枚举值")

            await conn.execute(text(
                "ALTER TYPE point_transaction_type ADD VALUE IF NOT EXISTS 'referral_reward'"
            ))
            logger.info("✅ 添加 referral_reward 枚举值")

            await conn.execute(text(
                "ALTER TYPE point_transaction_type ADD VALUE IF NOT EXISTS 'task_reward'"
            ))
            logger.info("✅ 添加 task_reward 枚举值")

            # 查询所有枚举值
            result = await conn.execute(text(
                """
                SELECT enumlabel
                FROM pg_enum
                WHERE enumtypid = 'point_transaction_type'::regtype
                ORDER BY enumsortorder
                """
            ))
            enum_values = [row[0] for row in result.fetchall()]

            logger.info("📋 当前所有枚举值:")
            for val in enum_values:
                logger.info(f"  - {val}")

            logger.info("🎉 枚举类型更新完成！")

        except Exception as e:
            logger.error(f"❌ 更新枚举类型失败: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(update_enum_types())
