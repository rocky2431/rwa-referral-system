"""
事件监听器与数据库集成测试
测试完整的事件驱动积分发放流程
"""

import asyncio
from web3 import Web3
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.web3_client import Web3Client
from app.services.event_listener import EventListenerService
from app.db.session import AsyncSessionLocal, engine
from app.models import User, UserPoints, PointTransaction, ReferralRelation
from loguru import logger


async def cleanup_database():
    """清理测试数据"""
    logger.info("🧹 清理测试数据...")

    async with AsyncSessionLocal() as db:
        # 按依赖顺序删除数据
        await db.execute(text("DELETE FROM point_transactions"))
        await db.execute(text("DELETE FROM referral_relations"))
        await db.execute(text("DELETE FROM user_points"))
        await db.execute(text("DELETE FROM users"))
        await db.commit()

    logger.success("✅ 测试数据清理完成")


async def check_database_records():
    """检查数据库记录"""
    logger.info("\n📊 检查数据库记录...")

    async with AsyncSessionLocal() as db:
        # 检查用户
        result = await db.execute(select(User))
        users = result.scalars().all()
        logger.info(f"   👥 用户数量: {len(users)}")
        for user in users:
            logger.info(f"      - {user.wallet_address[:10]}... 积分:{user.total_points}")

        # 检查积分账户
        result = await db.execute(select(UserPoints))
        points_accounts = result.scalars().all()
        logger.info(f"   💰 积分账户数量: {len(points_accounts)}")
        for account in points_accounts:
            logger.info(f"      - user_id={account.user_id} 可用:{account.available_points} 总赚:{account.total_earned}")

        # 检查交易记录
        result = await db.execute(select(PointTransaction))
        transactions = result.scalars().all()
        logger.info(f"   📝 交易记录数量: {len(transactions)}")
        for tx in transactions:
            logger.info(f"      - {tx.transaction_type.value} 数量:{tx.amount} 余额后:{tx.balance_after}")

        # 检查推荐关系
        result = await db.execute(select(ReferralRelation))
        relations = result.scalars().all()
        logger.info(f"   🤝 推荐关系数量: {len(relations)}")
        for rel in relations:
            logger.info(f"      - 推荐人ID:{rel.referrer_id} 被推荐人ID:{rel.referee_id} 总奖励:{rel.total_rewards_given}")


async def simulate_contract_interaction():
    """模拟合约交互，触发事件"""
    logger.info("\n🎬 模拟合约交互...")

    # 读取配置
    import os
    from dotenv import load_dotenv
    load_dotenv()

    rpc_url = os.getenv("BSC_TESTNET_RPC_URL", "http://localhost:8545")
    contract_address = os.getenv("REFERRAL_CONTRACT_ADDRESS")

    logger.info(f"   RPC: {rpc_url}")
    logger.info(f"   合约地址: {contract_address}")

    # 连接本地 Hardhat 节点
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    if not w3.is_connected():
        logger.error("❌ 无法连接到区块链节点")
        return False

    logger.success("✅ 区块链连接成功")
    logger.info(f"   当前区块: {w3.eth.block_number}")

    # 加载合约 ABI
    import json
    abi_path = "/Users/rocky243/Desktop/paimon.dex/socialtest2/backend/app/utils/RWAReferral_ABI.json"
    with open(abi_path, 'r') as f:
        contract_abi = json.load(f)

    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    # 获取测试账户
    accounts = w3.eth.accounts
    if len(accounts) < 3:
        logger.error("❌ 需要至少3个测试账户")
        return False

    user1 = accounts[0]  # 一级推荐人
    user2 = accounts[1]  # 二级推荐人
    user3 = accounts[2]  # 购买者

    logger.info(f"\n   测试账户:")
    logger.info(f"   - User1 (L1推荐人): {user1[:10]}...")
    logger.info(f"   - User2 (L2推荐人): {user2[:10]}...")
    logger.info(f"   - User3 (购买者):    {user3[:10]}...")

    # 1. 注册推荐关系: user3 -> user2 -> user1
    logger.info(f"\n   📝 注册推荐关系...")

    # user2 的推荐人是 user1
    try:
        tx_hash = contract.functions.addReferrer(user1).transact({
            'from': user2,
            'gas': 200000
        })
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        logger.success(f"   ✅ User2 注册推荐人 User1 (tx: {tx_hash.hex()[:10]}...)")
    except Exception as e:
        logger.warning(f"   ⚠️  User2->User1 关系可能已存在: {e}")

    # user3 的推荐人是 user2
    try:
        tx_hash = contract.functions.addReferrer(user2).transact({
            'from': user3,
            'gas': 200000
        })
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        logger.success(f"   ✅ User3 注册推荐人 User2 (tx: {tx_hash.hex()[:10]}...)")
    except Exception as e:
        logger.warning(f"   ⚠️  User3->User2 关系可能已存在: {e}")

    # 2. 触发购买，发放积分
    logger.info(f"\n   💰 User3 购买 2 BNB，触发积分奖励...")

    purchase_amount = w3.to_wei(2, 'ether')
    tx_hash = contract.functions.triggerReward(purchase_amount).transact({
        'from': user3,
        'gas': 300000
    })
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    logger.success(f"   ✅ 购买交易成功 (tx: {tx_hash.hex()[:10]}...)")
    logger.info(f"   区块号: {receipt['blockNumber']}")
    logger.info(f"   Gas消耗: {receipt['gasUsed']}")

    # 解析事件
    reward_events = contract.events.RewardCalculated().get_logs(
        fromBlock=receipt['blockNumber'],
        toBlock=receipt['blockNumber']
    )

    logger.info(f"\n   🎁 RewardCalculated 事件数量: {len(reward_events)}")
    for event in reward_events:
        args = event['args']
        logger.info(f"      - L{args['level']}: {args['pointsAmount']} 积分 -> {args['referrer'][:10]}...")

    return True


async def test_event_listener():
    """测试事件监听器"""
    logger.info("\n🎧 测试事件监听器...")

    # 读取配置
    import os
    from dotenv import load_dotenv
    load_dotenv()

    rpc_url = os.getenv("BSC_TESTNET_RPC_URL", "http://localhost:8545")
    contract_address = os.getenv("REFERRAL_CONTRACT_ADDRESS")

    # 创建 Web3 客户端
    web3_client = Web3Client(
        rpc_url=rpc_url,
        chain_id=31337,  # Hardhat 本地网络
        contract_address=contract_address,
        contract_abi_path="/Users/rocky243/Desktop/paimon.dex/socialtest2/backend/app/utils/RWAReferral_ABI.json"
    )

    current_block = web3_client.get_latest_block()
    logger.info(f"   当前区块: {current_block}")

    # 创建事件监听服务（从当前区块开始扫描）
    listener = EventListenerService(
        web3_client=web3_client,
        start_block=max(0, current_block - 10),  # 扫描最近10个区块
        poll_interval=1  # 1秒轮询一次
    )

    # 执行一次轮询
    logger.info("   执行事件轮询...")
    await listener._poll_events()

    logger.success("   ✅ 事件监听器测试完成")


async def main():
    """主测试流程"""
    logger.info("=" * 80)
    logger.info("🚀 开始事件监听器与数据库集成测试")
    logger.info("=" * 80)

    try:
        # 1. 清理测试数据
        await cleanup_database()

        # 2. 模拟合约交互
        success = await simulate_contract_interaction()
        if not success:
            logger.error("❌ 合约交互失败")
            return

        # 等待一下，确保事件已写入区块
        await asyncio.sleep(2)

        # 3. 测试事件监听器
        await test_event_listener()

        # 等待一下，确保数据库写入完成
        await asyncio.sleep(2)

        # 4. 检查数据库记录
        await check_database_records()

        logger.info("\n" + "=" * 80)
        logger.success("✅ 集成测试完成!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
