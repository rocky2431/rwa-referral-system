"""
Redis客户端封装
"""
from typing import Optional
import redis.asyncio as redis
from loguru import logger

from app.core.config import settings


class RedisClient:
    """Redis异步客户端封装"""

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    async def connect(self):
        """建立Redis连接"""
        if self._client is None:
            try:
                self._client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    retry_on_timeout=True
                )
                # 测试连接
                await self._client.ping()
                logger.info(f"✅ Redis连接成功: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            except Exception as e:
                logger.error(f"❌ Redis连接失败: {e}")
                raise

    async def disconnect(self):
        """断开Redis连接"""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("👋 Redis连接已关闭")

    @property
    def client(self) -> redis.Redis:
        """获取Redis客户端"""
        if self._client is None:
            raise RuntimeError("Redis client is not connected. Call connect() first.")
        return self._client

    async def get(self, key: str) -> Optional[str]:
        """获取键值"""
        return await self.client.get(key)

    async def set(
        self,
        key: str,
        value: str,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """
        设置键值

        Args:
            key: 键
            value: 值
            ex: 过期时间（秒）
            px: 过期时间（毫秒）
            nx: 仅当键不存在时设置
            xx: 仅当键存在时设置

        Returns:
            是否设置成功
        """
        return await self.client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)

    async def delete(self, *keys: str) -> int:
        """删除键"""
        return await self.client.delete(*keys)

    async def exists(self, *keys: str) -> int:
        """检查键是否存在"""
        return await self.client.exists(*keys)

    async def expire(self, key: str, seconds: int) -> bool:
        """设置键过期时间"""
        return await self.client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """获取键剩余生存时间"""
        return await self.client.ttl(key)

    async def incr(self, key: str) -> int:
        """递增"""
        return await self.client.incr(key)

    async def decr(self, key: str) -> int:
        """递减"""
        return await self.client.decr(key)

    async def hset(self, name: str, mapping: dict) -> int:
        """设置哈希表"""
        return await self.client.hset(name, mapping=mapping)

    async def hget(self, name: str, key: str) -> Optional[str]:
        """获取哈希表字段值"""
        return await self.client.hget(name, key)

    async def hgetall(self, name: str) -> dict:
        """获取哈希表所有字段"""
        return await self.client.hgetall(name)

    async def hdel(self, name: str, *keys: str) -> int:
        """删除哈希表字段"""
        return await self.client.hdel(name, *keys)

    async def acquire_lock(
        self,
        lock_name: str,
        timeout: int = 10,
        blocking_timeout: Optional[int] = None
    ) -> Optional[redis.lock.Lock]:
        """
        获取分布式锁

        Args:
            lock_name: 锁名称
            timeout: 锁超时时间（秒）
            blocking_timeout: 阻塞等待时间（秒），None表示不等待

        Returns:
            Lock对象，获取失败返回None
        """
        try:
            lock = self.client.lock(
                lock_name,
                timeout=timeout,
                blocking_timeout=blocking_timeout
            )
            acquired = await lock.acquire(blocking=blocking_timeout is not None)
            if acquired:
                return lock
            return None
        except Exception as e:
            logger.error(f"获取锁失败: {lock_name}, error={e}")
            return None

    async def release_lock(self, lock: redis.lock.Lock):
        """释放分布式锁"""
        try:
            await lock.release()
        except Exception as e:
            logger.warning(f"释放锁失败: {e}")


# 创建全局Redis客户端实例
redis_client = RedisClient()
