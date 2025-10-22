"""
智能合约事件监听服务
监听RWAReferral合约的RewardCalculated事件，发放积分奖励
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from web3.exceptions import Web3Exception

from app.utils.web3_client import Web3Client
from app.db.session import AsyncSessionLocal
from app.utils.retry import async_retry, CircuitBreaker


class EventListenerService:
    """事件监听服务类"""

    def __init__(
        self,
        web3_client: Web3Client,
        start_block: Optional[int] = None,
        poll_interval: int = 5,
        max_retries: int = 3
    ):
        """
        初始化事件监听服务

        Args:
            web3_client: Web3客户端实例
            start_block: 起始区块号（None则从最新区块开始）
            poll_interval: 轮询间隔（秒）
            max_retries: 最大重试次数
        """
        self.web3_client = web3_client
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.is_running = False
        self.last_processed_block = start_block or web3_client.get_latest_block()

        # 熔断器（防止持续失败）
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
            expected_exception=Exception
        )

        # 错误统计
        self.error_count = 0
        self.last_error_time: Optional[datetime] = None

        logger.info(f"🎧 事件监听服务初始化完成")
        logger.info(f"📍 起始区块: {self.last_processed_block}")
        logger.info(f"⏱️  轮询间隔: {poll_interval}秒")
        logger.info(f"🔄 最大重试次数: {max_retries}")

    async def start(self):
        """启动事件监听"""
        if self.is_running:
            logger.warning("⚠️  事件监听服务已在运行中")
            return

        self.is_running = True
        logger.info("🚀 启动事件监听服务...")

        try:
            while self.is_running:
                await self._poll_events()
                await asyncio.sleep(self.poll_interval)

        except Exception as e:
            logger.error(f"❌ 事件监听服务异常: {e}")
            raise
        finally:
            self.is_running = False
            logger.info("⏹️  事件监听服务已停止")

    async def stop(self):
        """停止事件监听"""
        logger.info("🛑 正在停止事件监听服务...")
        self.is_running = False

    async def _check_connection(self) -> bool:
        """
        检查Web3连接状态

        Returns:
            连接是否正常
        """
        try:
            is_connected = self.web3_client.is_connected()
            if not is_connected:
                logger.warning("⚠️  Web3连接断开，尝试重连...")
                # TODO: 实现重连逻辑
                return False
            return True

        except Exception as e:
            logger.error(f"❌ 检查连接失败: {e}")
            return False

    async def _poll_events(self):
        """轮询事件（单次）"""
        # 检查连接状态
        if not await self._check_connection():
            logger.warning("⚠️  跳过本次轮询（连接异常）")
            return

        try:
            # 通过熔断器执行轮询
            await self.circuit_breaker.call(self._do_poll_events)

        except Exception as e:
            self.error_count += 1
            self.last_error_time = datetime.now()
            logger.error(f"❌ 轮询事件失败 (错误次数: {self.error_count}): {e}")
            # 不抛出异常，继续下一轮轮询

    @async_retry(
        max_retries=3,
        initial_delay=2.0,
        max_delay=30.0,
        exceptions=(Web3Exception, ConnectionError, TimeoutError)
    )
    async def _do_poll_events(self):
        """执行实际的事件轮询（带重试机制）"""
        current_block = self.web3_client.get_latest_block()

        # 如果没有新区块，跳过
        if current_block <= self.last_processed_block:
            return

        # 获取事件日志
        from_block = self.last_processed_block + 1
        to_block = current_block

        logger.debug(f"📊 扫描区块 {from_block} 到 {to_block}")

        # 监听多个事件
        await self._process_reward_calculated_events(from_block, to_block)
        await self._process_user_purchased_events(from_block, to_block)
        await self._process_referrer_registered_events(from_block, to_block)

        # 更新最后处理的区块
        self.last_processed_block = current_block

    async def _process_reward_calculated_events(
        self,
        from_block: int,
        to_block: int
    ):
        """
        处理RewardCalculated事件

        Args:
            from_block: 起始区块
            to_block: 结束区块
        """
        try:
            logs = self.web3_client.get_logs(
                event_name='RewardCalculated',
                from_block=from_block,
                to_block=to_block
            )

            if not logs:
                return

            logger.info(f"🎁 发现 {len(logs)} 个RewardCalculated事件")

            async with AsyncSessionLocal() as db:
                for log in logs:
                    try:
                        event_data = self.web3_client.decode_event(log)
                        await self._handle_reward_calculated(db, event_data)
                    except Exception as e:
                        logger.error(
                            f"❌ 处理单个RewardCalculated事件失败 "
                            f"(tx={log.transactionHash.hex()[:10]}...): {e}"
                        )
                        # 继续处理下一个事件，不中断整个批次

        except Exception as e:
            logger.error(f"❌ 处理RewardCalculated事件失败: {e}")

    async def _process_user_purchased_events(
        self,
        from_block: int,
        to_block: int
    ):
        """
        处理UserPurchased事件

        Args:
            from_block: 起始区块
            to_block: 结束区块
        """
        try:
            logs = self.web3_client.get_logs(
                event_name='UserPurchased',
                from_block=from_block,
                to_block=to_block
            )

            if not logs:
                return

            logger.info(f"🛒 发现 {len(logs)} 个UserPurchased事件")

            async with AsyncSessionLocal() as db:
                for log in logs:
                    try:
                        event_data = self.web3_client.decode_event(log)
                        await self._handle_user_purchased(db, event_data)
                    except Exception as e:
                        logger.error(
                            f"❌ 处理单个UserPurchased事件失败 "
                            f"(tx={log.transactionHash.hex()[:10]}...): {e}"
                        )

        except Exception as e:
            logger.error(f"❌ 处理UserPurchased事件失败: {e}")

    async def _process_referrer_registered_events(
        self,
        from_block: int,
        to_block: int
    ):
        """
        处理RegisteredReferrer事件

        Args:
            from_block: 起始区块
            to_block: 结束区块
        """
        try:
            logs = self.web3_client.get_logs(
                event_name='RegisteredReferrer',
                from_block=from_block,
                to_block=to_block
            )

            if not logs:
                return

            logger.info(f"🤝 发现 {len(logs)} 个RegisteredReferrer事件")

            async with AsyncSessionLocal() as db:
                for log in logs:
                    try:
                        event_data = self.web3_client.decode_event(log)
                        await self._handle_referrer_registered(db, event_data)
                    except Exception as e:
                        logger.error(
                            f"❌ 处理单个RegisteredReferrer事件失败 "
                            f"(tx={log.transactionHash.hex()[:10]}...): {e}"
                        )

        except Exception as e:
            logger.error(f"❌ 处理RegisteredReferrer事件失败: {e}")

    async def _handle_reward_calculated(
        self,
        db: AsyncSession,
        event_data: Dict[str, Any]
    ):
        """
        处理单个RewardCalculated事件

        事件参数:
        - purchaser: 购买者地址
        - referrer: 推荐人地址
        - purchaseAmount: 购买金额 (wei)
        - pointsAmount: 积分数量
        - level: 推荐层级 (1或2)
        - timestamp: 事件时间戳

        Args:
            db: 数据库会话
            event_data: 事件数据
        """
        from app.services.points_service import PointsService

        args = event_data['args']
        tx_hash = event_data['transaction_hash']
        block_number = event_data['block_number']

        logger.info(
            f"💰 处理积分奖励: "
            f"推荐人={args['referrer'][:10]}... "
            f"购买者={args['purchaser'][:10]}... "
            f"积分={args['pointsAmount']} "
            f"层级={args['level']}"
        )

        try:
            # 发放推荐积分
            success = await PointsService.award_referral_points(
                db=db,
                referrer_address=args['referrer'],
                purchaser_address=args['purchaser'],
                points_amount=int(args['pointsAmount']),
                level=int(args['level']),
                purchase_amount=int(args['purchaseAmount']),
                tx_hash=tx_hash,
                block_number=block_number
            )

            if success:
                logger.success(
                    f"✅ 积分发放完成: "
                    f"{args['pointsAmount']} 积分 → {args['referrer'][:10]}..."
                )
            else:
                logger.warning(f"⚠️  积分发放未成功")

        except Exception as e:
            logger.error(f"❌ 积分发放异常: {e}")
            raise

    async def _handle_user_purchased(
        self,
        db: AsyncSession,
        event_data: Dict[str, Any]
    ):
        """
        处理UserPurchased事件

        事件参数:
        - user: 购买者地址
        - amount: 购买金额 (wei)
        - timestamp: 购买时间戳

        Args:
            db: 数据库会话
            event_data: 事件数据
        """
        args = event_data['args']

        logger.info(
            f"🛒 用户购买: "
            f"用户={args['user'][:10]}... "
            f"金额={args['amount']} wei"
        )

        # TODO: 记录购买历史
        logger.debug(f"📝 事件详情: {event_data}")

    async def _handle_referrer_registered(
        self,
        db: AsyncSession,
        event_data: Dict[str, Any]
    ):
        """
        处理RegisteredReferrer事件

        事件参数:
        - referee: 被推荐人地址
        - referrer: 推荐人地址

        Args:
            db: 数据库会话
            event_data: 事件数据
        """
        from app.services.points_service import PointsService

        args = event_data['args']
        tx_hash = event_data['transaction_hash']
        block_number = event_data['block_number']

        logger.info(
            f"🤝 推荐关系建立: "
            f"推荐人={args['referrer'][:10]}... "
            f"被推荐人={args['referee'][:10]}..."
        )

        try:
            # 同步推荐关系到数据库
            success = await PointsService.sync_referral_relation(
                db=db,
                referee_address=args['referee'],
                referrer_address=args['referrer'],
                tx_hash=tx_hash,
                block_number=block_number
            )

            if success:
                logger.success(
                    f"✅ 推荐关系同步成功: "
                    f"{args['referee'][:10]}... → {args['referrer'][:10]}..."
                )
            else:
                logger.warning(f"⚠️  推荐关系同步未成功（可能已存在）")

        except Exception as e:
            logger.error(f"❌ 推荐关系同步异常: {e}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """
        获取监听服务状态

        Returns:
            状态信息字典
        """
        return {
            "is_running": self.is_running,
            "last_processed_block": self.last_processed_block,
            "current_block": self.web3_client.get_latest_block(),
            "poll_interval": self.poll_interval,
            "chain_id": self.web3_client.chain_id,
            "contract_address": self.web3_client.contract_address
        }


# 全局服务实例
_event_listener_service: Optional[EventListenerService] = None


def get_event_listener_service() -> EventListenerService:
    """获取事件监听服务全局实例"""
    global _event_listener_service

    if _event_listener_service is None:
        raise RuntimeError("事件监听服务未初始化，请先调用 initialize_event_listener()")

    return _event_listener_service


def initialize_event_listener(
    web3_client: Web3Client,
    start_block: Optional[int] = None,
    poll_interval: int = 5
) -> EventListenerService:
    """
    初始化事件监听服务

    Args:
        web3_client: Web3客户端实例
        start_block: 起始区块号
        poll_interval: 轮询间隔（秒）

    Returns:
        EventListenerService实例
    """
    global _event_listener_service

    _event_listener_service = EventListenerService(
        web3_client=web3_client,
        start_block=start_block,
        poll_interval=poll_interval
    )

    return _event_listener_service
