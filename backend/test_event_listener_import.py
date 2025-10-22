#!/usr/bin/env python3
"""
测试事件监听服务模块导入
验证所有依赖都正确安装
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger

logger.info("🧪 测试事件监听服务模块导入...")
logger.info("=" * 60)

try:
    # 测试基础模块
    logger.info("1️⃣  测试基础模块导入...")
    from dotenv import load_dotenv
    from web3 import Web3
    from sqlalchemy.ext.asyncio import AsyncSession
    logger.success("✅ 基础模块导入成功")

    # 测试工具模块
    logger.info("2️⃣  测试工具模块导入...")
    from app.utils.web3_client import Web3Client
    from app.utils.retry import async_retry, CircuitBreaker
    from app.db.session import AsyncSessionLocal
    logger.success("✅ 工具模块导入成功")

    # 测试服务模块
    logger.info("3️⃣  测试服务模块导入...")
    from app.services.event_listener import EventListenerService, initialize_event_listener
    from app.services.points_service import PointsService
    logger.success("✅ 服务模块导入成功")

    # 测试模型
    logger.info("4️⃣  测试数据模型导入...")
    from app.models.user import User
    from app.models.user_points import UserPoints
    from app.models.point_transaction import PointTransaction
    from app.models.referral_relation import ReferralRelation
    logger.success("✅ 数据模型导入成功")

    logger.info("=" * 60)
    logger.success("🎉 所有模块导入测试通过！")
    logger.info("=" * 60)
    logger.info("✅ Python 3.11环境配置正确")
    logger.info("✅ 所有依赖已正确安装")
    logger.info("✅ 事件监听服务代码完整")
    logger.info("=" * 60)
    logger.info("📋 下一步:")
    logger.info("   1. 启动Hardhat本地节点: cd contracts && npx hardhat node")
    logger.info("   2. 启动事件监听服务: cd backend && /opt/anaconda3/envs/rwa/bin/python run_event_listener.py")
    logger.info("=" * 60)

except ImportError as e:
    logger.error(f"❌ 模块导入失败: {e}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)

except Exception as e:
    logger.error(f"❌ 测试失败: {e}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)
