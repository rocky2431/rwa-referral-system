#!/usr/bin/env python3
"""
链上事件监听服务启动脚本
监听RWAReferral合约事件并同步到数据库
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from loguru import logger

from app.utils.web3_client import Web3Client
from app.services.event_listener import initialize_event_listener


async def main():
    """主函数"""
    # 加载环境变量
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    logger.info("=" * 60)
    logger.info("🚀 RWA推荐系统 - 链上事件监听服务")
    logger.info("=" * 60)

    # 读取配置
    network = os.getenv("BSC_NETWORK", "local")
    contract_address = os.getenv("REFERRAL_CONTRACT_ADDRESS")

    if network == "local":
        rpc_url = os.getenv("LOCAL_RPC_URL", "http://127.0.0.1:8545")
        chain_id = int(os.getenv("LOCAL_CHAIN_ID", "31337"))
    elif network == "testnet":
        rpc_url = os.getenv("BSC_TESTNET_RPC_URL")
        chain_id = int(os.getenv("BSC_TESTNET_CHAIN_ID", "97"))
    else:  # mainnet
        rpc_url = os.getenv("BSC_MAINNET_RPC_URL")
        chain_id = int(os.getenv("BSC_MAINNET_CHAIN_ID", "56"))

    if not contract_address or contract_address == "0x0000000000000000000000000000000000000000":
        logger.error("❌ 错误: REFERRAL_CONTRACT_ADDRESS 未配置")
        logger.info("💡 提示: 请在 .env 文件中设置合约地址")
        sys.exit(1)

    logger.info(f"📡 网络: {network}")
    logger.info(f"🔗 RPC: {rpc_url}")
    logger.info(f"🆔 链ID: {chain_id}")
    logger.info(f"📝 合约地址: {contract_address}")
    logger.info("=" * 60)

    try:
        # 初始化Web3客户端
        logger.info("🔧 初始化Web3客户端...")
        web3_client = Web3Client(
            rpc_url=rpc_url,
            chain_id=chain_id,
            contract_address=contract_address
        )

        # 获取起始区块（可选：从环境变量读取）
        start_block_env = os.getenv("EVENT_LISTENER_START_BLOCK")
        start_block = int(start_block_env) if start_block_env else None

        # 轮询间隔（秒）
        poll_interval = int(os.getenv("EVENT_LISTENER_POLL_INTERVAL", "5"))

        # 初始化事件监听服务
        logger.info("🎧 初始化事件监听服务...")
        event_listener = initialize_event_listener(
            web3_client=web3_client,
            start_block=start_block,
            poll_interval=poll_interval
        )

        logger.info("✅ 初始化完成，开始监听事件...")
        logger.info("=" * 60)
        logger.info("💡 按 Ctrl+C 停止监听")
        logger.info("=" * 60)

        # 启动事件监听
        await event_listener.start()

    except KeyboardInterrupt:
        logger.info("\n⏹️  收到停止信号，正在关闭...")
        if 'event_listener' in locals():
            await event_listener.stop()
        logger.info("👋 事件监听服务已停止")

    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())
