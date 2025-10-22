"""
添加新的任务状态枚举值
AVAILABLE（可领取）和 REWARDED（已领奖）
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import engine
from loguru import logger


async def add_new_status_values():
    """添加新的枚举值到user_task_status类型"""
    async with engine.begin() as conn:
        try:
            # 添加 AVAILABLE 状态
            await conn.execute(text(
                "ALTER TYPE user_task_status ADD VALUE IF NOT EXISTS 'available'"
            ))
            logger.info("✅ 添加 AVAILABLE 状态")

            # 添加 REWARDED 状态
            await conn.execute(text(
                "ALTER TYPE user_task_status ADD VALUE IF NOT EXISTS 'rewarded'"
            ))
            logger.info("✅ 添加 REWARDED 状态")

            logger.info("🎉 新状态枚举值添加完成！")

        except Exception as e:
            logger.error(f"❌ 失败: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(add_new_status_values())
