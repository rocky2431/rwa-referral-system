"""
幂等性服务
处理API请求的幂等性，防止重复操作
"""
from typing import Optional
import json
import hashlib
from datetime import datetime
from loguru import logger

from app.utils.redis_client import redis_client
from app.models.point_transaction import PointTransaction


class IdempotencyService:
    """幂等性服务类"""

    # 幂等性Key前缀
    IDEMPOTENCY_KEY_PREFIX = "idempotency:points:"
    # 默认过期时间（24小时）
    DEFAULT_TTL = 86400

    @staticmethod
    def generate_idempotency_key(
        user_id: int,
        transaction_type: str,
        amount: int,
        **kwargs
    ) -> str:
        """
        生成幂等性Key

        Args:
            user_id: 用户ID
            transaction_type: 交易类型
            amount: 积分数量
            **kwargs: 其他参数

        Returns:
            幂等性Key
        """
        # 构建参数字典
        params = {
            "user_id": user_id,
            "transaction_type": transaction_type,
            "amount": amount,
            **kwargs
        }

        # 排序并序列化
        sorted_params = json.dumps(params, sort_keys=True)

        # 生成哈希
        hash_value = hashlib.sha256(sorted_params.encode()).hexdigest()[:16]

        return f"{IdempotencyService.IDEMPOTENCY_KEY_PREFIX}{hash_value}"

    @staticmethod
    async def check_idempotency(
        idempotency_key: str
    ) -> Optional[dict]:
        """
        检查幂等性Key是否已存在

        Args:
            idempotency_key: 幂等性Key

        Returns:
            已存在的交易记录（JSON），不存在返回None
        """
        try:
            key = f"{IdempotencyService.IDEMPOTENCY_KEY_PREFIX}{idempotency_key}"
            result = await redis_client.get(key)

            if result:
                logger.info(f"🔍 幂等性检查: Key={idempotency_key} 已存在")
                return json.loads(result)

            return None

        except Exception as e:
            logger.error(f"幂等性检查失败: {e}")
            # 幂等性检查失败不应阻塞业务，返回None继续处理
            return None

    @staticmethod
    async def store_idempotency(
        idempotency_key: str,
        transaction: PointTransaction,
        ttl: int = DEFAULT_TTL
    ) -> bool:
        """
        存储幂等性记录

        Args:
            idempotency_key: 幂等性Key
            transaction: 积分交易记录
            ttl: 过期时间（秒）

        Returns:
            是否存储成功
        """
        try:
            key = f"{IdempotencyService.IDEMPOTENCY_KEY_PREFIX}{idempotency_key}"

            # 构建存储数据
            data = {
                "transaction_id": transaction.id,
                "user_id": transaction.user_id,
                "transaction_type": transaction.transaction_type.value,
                "amount": transaction.amount,
                "balance_after": transaction.balance_after,
                "status": transaction.status,
                "created_at": transaction.created_at.isoformat()
            }

            # 存储到Redis
            await redis_client.set(
                key,
                json.dumps(data),
                ex=ttl
            )

            logger.info(
                f"💾 幂等性记录已存储: Key={idempotency_key}, "
                f"transaction_id={transaction.id}, TTL={ttl}s"
            )

            return True

        except Exception as e:
            logger.error(f"存储幂等性记录失败: {e}")
            # 存储失败不应阻塞业务
            return False

    @staticmethod
    async def delete_idempotency(idempotency_key: str) -> bool:
        """
        删除幂等性记录

        Args:
            idempotency_key: 幂等性Key

        Returns:
            是否删除成功
        """
        try:
            key = f"{IdempotencyService.IDEMPOTENCY_KEY_PREFIX}{idempotency_key}"
            await redis_client.delete(key)
            logger.info(f"🗑️  幂等性记录已删除: Key={idempotency_key}")
            return True

        except Exception as e:
            logger.error(f"删除幂等性记录失败: {e}")
            return False

    @staticmethod
    async def acquire_operation_lock(
        user_id: int,
        operation: str,
        timeout: int = 10,
        blocking_timeout: int = 5
    ):
        """
        获取操作锁（防止并发操作）

        Args:
            user_id: 用户ID
            operation: 操作类型
            timeout: 锁超时时间（秒）
            blocking_timeout: 阻塞等待时间（秒）

        Returns:
            Lock对象，获取失败返回None
        """
        lock_name = f"lock:points:{operation}:{user_id}"

        try:
            lock = await redis_client.acquire_lock(
                lock_name,
                timeout=timeout,
                blocking_timeout=blocking_timeout
            )

            if lock:
                logger.debug(f"🔒 操作锁已获取: {lock_name}")
            else:
                logger.warning(f"⏳ 操作锁获取超时: {lock_name}")

            return lock

        except Exception as e:
            logger.error(f"获取操作锁失败: {e}")
            return None

    @staticmethod
    async def release_operation_lock(lock):
        """
        释放操作锁

        Args:
            lock: Lock对象
        """
        try:
            if lock:
                await redis_client.release_lock(lock)
                logger.debug("🔓 操作锁已释放")
        except Exception as e:
            logger.error(f"释放操作锁失败: {e}")
