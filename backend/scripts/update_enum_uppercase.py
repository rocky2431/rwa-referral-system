"""
添加大写的枚举值
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import engine
from loguru import logger


async def add_uppercase_enums():
    async with engine.begin() as conn:
        try:
            await conn.execute(text(
                "ALTER TYPE point_transaction_type ADD VALUE IF NOT EXISTS 'REGISTER_REWARD'"
            ))
            logger.info("✅ 添加 REGISTER_REWARD")

            await conn.execute(text(
                "ALTER TYPE point_transaction_type ADD VALUE IF NOT EXISTS 'REFERRAL_REWARD'"
            ))
            logger.info("✅ 添加 REFERRAL_REWARD")

            await conn.execute(text(
                "ALTER TYPE point_transaction_type ADD VALUE IF NOT EXISTS 'TASK_REWARD'"
            ))
            logger.info("✅ 添加 TASK_REWARD")

            logger.info("🎉 大写枚举值添加完成！")

        except Exception as e:
            logger.error(f"❌ 失败: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(add_uppercase_enums())
