"""
测试数据seed脚本

职责：创建测试用户和相关数据，用于开发测试
设计原则：
- KISS：简单直接的数据创建逻辑
- DRY：复用User模型和API逻辑
- YAGNI：只创建当前必需的测试数据
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User
from app.models.user_points import UserPoints
from loguru import logger


async def create_test_users(session: AsyncSession, count: int = 10):
    """
    创建测试用户

    Args:
        session: 数据库会话
        count: 创建用户数量
    """
    test_wallets = [
        f"0x{''.join(['0123456789abcdef'[i % 16] for i in range(j, j+40)])}"
        for j in range(count)
    ]

    users = []
    for idx, wallet in enumerate(test_wallets, 1):
        # 创建用户
        user = User(
            wallet_address=wallet.lower(),
            username=f"TestUser{idx:03d}",
            avatar_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed={idx}",
            level=1 + (idx % 5),  # 等级1-5随机
            experience=idx * 100,
            total_points=idx * 1000,
            total_invited=idx % 10,
            total_tasks_completed=idx * 3,
            total_questions_answered=idx * 5,
            correct_answers=idx * 4,
            is_active=True
        )
        session.add(user)
        users.append(user)

    await session.flush()  # 获取user.id

    # 创建积分账户
    for user in users:
        points = UserPoints(
            user_id=user.id,
            available_points=user.total_points,
            frozen_points=0,
            total_earned=user.total_points + 500,
            total_spent=500,
            points_from_referral=user.total_points // 3,
            points_from_tasks=user.total_points // 3,
            points_from_quiz=user.total_points // 3,
            points_from_team=0,
            points_from_purchase=0
        )
        session.add(points)

    await session.commit()

    logger.info(f"✅ 成功创建 {len(users)} 个测试用户")
    return users


async def main():
    """主函数"""
    logger.info("🚀 开始创建测试数据...")

    # 创建异步引擎（转换为asyncpg驱动）
    database_url = settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # 创建10个测试用户
            users = await create_test_users(session, count=10)

            # 打印创建的用户
            logger.info("\n📋 创建的测试用户列表:")
            logger.info("=" * 80)
            for user in users:
                logger.info(
                    f"ID: {user.id:2d} | "
                    f"用户名: {user.username:15s} | "
                    f"钱包: {user.wallet_address[:12]}... | "
                    f"等级: {user.level} | "
                    f"积分: {user.total_points:6d}"
                )
            logger.info("=" * 80)

            logger.info("\n✅ 测试数据创建完成！")
            logger.info(f"📍 数据库: {settings.DATABASE_URL}")
            logger.info("\n🔗 API测试示例:")
            logger.info(f"  curl http://localhost:8000/api/v1/users/by-wallet/{users[0].wallet_address}")
            logger.info(f"  curl http://localhost:8000/api/v1/users/{users[0].id}")
            logger.info(f"  curl http://localhost:8000/api/v1/points/user/{users[0].id}")

        except Exception as e:
            logger.error(f"❌ 创建测试数据失败: {e}")
            await session.rollback()
            raise

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
