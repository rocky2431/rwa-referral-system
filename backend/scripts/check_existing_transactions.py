"""
检查现有积分流水记录的transaction_type
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from loguru import logger


async def check_transactions():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text(
            "SELECT DISTINCT transaction_type FROM point_transactions ORDER BY transaction_type"
        ))
        types = [row[0] for row in result.fetchall()]

        logger.info("📋 现有的 transaction_type 值:")
        for t in types:
            logger.info(f"  - {t}")


if __name__ == "__main__":
    asyncio.run(check_transactions())
