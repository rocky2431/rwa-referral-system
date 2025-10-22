"""
缓存服务
提供Redis缓存抽象层，遵循SOLID原则
"""

import json
from typing import Optional, Any, Callable
from functools import wraps
from loguru import logger

from app.utils.redis_client import redis_client


class CacheService:
    """缓存服务类 - 单一职责：管理所有缓存操作"""

    # 缓存键前缀
    KEY_PREFIX_USER_POINTS = "points:user:"
    KEY_PREFIX_USER_BALANCE = "balance:user:"
    KEY_PREFIX_LEADERBOARD = "leaderboard:"
    KEY_PREFIX_TEAM_STATS = "team:stats:"

    # 缓存过期时间（秒）
    TTL_USER_POINTS = 300  # 5分钟
    TTL_USER_BALANCE = 60  # 1分钟
    TTL_LEADERBOARD = 600  # 10分钟
    TTL_TEAM_STATS = 300  # 5分钟

    @staticmethod
    async def get_user_points_cache(user_id: int) -> Optional[dict]:
        """
        获取用户积分缓存

        Args:
            user_id: 用户ID

        Returns:
            缓存的积分数据，不存在返回None
        """
        try:
            key = f"{CacheService.KEY_PREFIX_USER_POINTS}{user_id}"
            cached_data = await redis_client.get(key)

            if cached_data:
                logger.debug(f"🎯 缓存命中: user_points:user_id={user_id}")
                return json.loads(cached_data)

            logger.debug(f"❌ 缓存未命中: user_points:user_id={user_id}")
            return None

        except Exception as e:
            logger.warning(f"⚠️  获取缓存失败: {e}")
            return None

    @staticmethod
    async def set_user_points_cache(user_id: int, data: dict) -> bool:
        """
        设置用户积分缓存

        Args:
            user_id: 用户ID
            data: 积分数据

        Returns:
            是否成功
        """
        try:
            key = f"{CacheService.KEY_PREFIX_USER_POINTS}{user_id}"
            value = json.dumps(data, ensure_ascii=False)
            success = await redis_client.set(
                key,
                value,
                ex=CacheService.TTL_USER_POINTS
            )

            if success:
                logger.debug(f"✅ 缓存设置成功: user_points:user_id={user_id}")

            return success

        except Exception as e:
            logger.warning(f"⚠️  设置缓存失败: {e}")
            return False

    @staticmethod
    async def invalidate_user_points_cache(user_id: int):
        """
        使用户积分缓存失效

        Args:
            user_id: 用户ID
        """
        try:
            key = f"{CacheService.KEY_PREFIX_USER_POINTS}{user_id}"
            await redis_client.delete(key)
            logger.debug(f"🗑️  缓存失效: user_points:user_id={user_id}")

        except Exception as e:
            logger.warning(f"⚠️  缓存失效失败: {e}")

    @staticmethod
    async def get_user_balance_cache(user_id: int) -> Optional[int]:
        """
        获取用户积分余额缓存（快速查询）

        Args:
            user_id: 用户ID

        Returns:
            积分余额，不存在返回None
        """
        try:
            key = f"{CacheService.KEY_PREFIX_USER_BALANCE}{user_id}"
            cached_balance = await redis_client.get(key)

            if cached_balance:
                logger.debug(f"🎯 缓存命中: balance:user_id={user_id}")
                return int(cached_balance)

            logger.debug(f"❌ 缓存未命中: balance:user_id={user_id}")
            return None

        except Exception as e:
            logger.warning(f"⚠️  获取余额缓存失败: {e}")
            return None

    @staticmethod
    async def set_user_balance_cache(user_id: int, balance: int) -> bool:
        """
        设置用户积分余额缓存

        Args:
            user_id: 用户ID
            balance: 积分余额

        Returns:
            是否成功
        """
        try:
            key = f"{CacheService.KEY_PREFIX_USER_BALANCE}{user_id}"
            success = await redis_client.set(
                key,
                str(balance),
                ex=CacheService.TTL_USER_BALANCE
            )

            if success:
                logger.debug(f"✅ 余额缓存设置: user_id={user_id}, balance={balance}")

            return success

        except Exception as e:
            logger.warning(f"⚠️  设置余额缓存失败: {e}")
            return False

    @staticmethod
    async def invalidate_user_balance_cache(user_id: int):
        """
        使用户余额缓存失效

        Args:
            user_id: 用户ID
        """
        try:
            key = f"{CacheService.KEY_PREFIX_USER_BALANCE}{user_id}"
            await redis_client.delete(key)
            logger.debug(f"🗑️  余额缓存失效: user_id={user_id}")

        except Exception as e:
            logger.warning(f"⚠️  余额缓存失效失败: {e}")

    @staticmethod
    async def invalidate_user_all_cache(user_id: int):
        """
        使用户所有缓存失效

        Args:
            user_id: 用户ID
        """
        await CacheService.invalidate_user_points_cache(user_id)
        await CacheService.invalidate_user_balance_cache(user_id)

    @staticmethod
    async def get_leaderboard_cache(leaderboard_type: str, page: int = 1) -> Optional[list]:
        """
        获取排行榜缓存

        Args:
            leaderboard_type: 排行榜类型 (points/teams/quiz)
            page: 页码

        Returns:
            缓存的排行榜数据
        """
        try:
            key = f"{CacheService.KEY_PREFIX_LEADERBOARD}{leaderboard_type}:page:{page}"
            cached_data = await redis_client.get(key)

            if cached_data:
                logger.debug(f"🎯 排行榜缓存命中: {leaderboard_type}:page={page}")
                return json.loads(cached_data)

            return None

        except Exception as e:
            logger.warning(f"⚠️  获取排行榜缓存失败: {e}")
            return None

    @staticmethod
    async def set_leaderboard_cache(
        leaderboard_type: str,
        page: int,
        data: list
    ) -> bool:
        """
        设置排行榜缓存

        Args:
            leaderboard_type: 排行榜类型
            page: 页码
            data: 排行榜数据

        Returns:
            是否成功
        """
        try:
            key = f"{CacheService.KEY_PREFIX_LEADERBOARD}{leaderboard_type}:page:{page}"
            value = json.dumps(data, ensure_ascii=False, default=str)
            success = await redis_client.set(
                key,
                value,
                ex=CacheService.TTL_LEADERBOARD
            )

            if success:
                logger.debug(f"✅ 排行榜缓存设置: {leaderboard_type}:page={page}")

            return success

        except Exception as e:
            logger.warning(f"⚠️  设置排行榜缓存失败: {e}")
            return False

    @staticmethod
    async def invalidate_leaderboard_cache(leaderboard_type: str):
        """
        使排行榜缓存失效（所有页）

        Args:
            leaderboard_type: 排行榜类型
        """
        try:
            # 删除所有相关页的缓存
            pattern = f"{CacheService.KEY_PREFIX_LEADERBOARD}{leaderboard_type}:page:*"
            # Redis SCAN命令遍历删除
            keys = []
            cursor = 0
            while True:
                cursor, partial_keys = await redis_client.client.scan(
                    cursor,
                    match=pattern,
                    count=100
                )
                keys.extend(partial_keys)
                if cursor == 0:
                    break

            if keys:
                await redis_client.delete(*keys)
                logger.debug(f"🗑️  排行榜缓存失效: {leaderboard_type}, 删除{len(keys)}个键")

        except Exception as e:
            logger.warning(f"⚠️  排行榜缓存失效失败: {e}")


def with_cache(
    cache_getter: Callable,
    cache_setter: Callable,
    cache_key_generator: Callable[[Any], str]
):
    """
    缓存装饰器 - 遵循开闭原则，通过装饰器扩展功能

    Args:
        cache_getter: 获取缓存的函数
        cache_setter: 设置缓存的函数
        cache_key_generator: 生成缓存键的函数

    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = cache_key_generator(*args, **kwargs)

            # 尝试从缓存获取
            try:
                cached_result = await cache_getter(cache_key)
                if cached_result is not None:
                    logger.debug(f"🎯 [Cache Hit] {func.__name__}: key={cache_key}")
                    return cached_result
            except Exception as e:
                logger.warning(f"⚠️  缓存读取失败: {e}")

            # 缓存未命中，执行原函数
            result = await func(*args, **kwargs)

            # 保存到缓存
            try:
                await cache_setter(cache_key, result)
            except Exception as e:
                logger.warning(f"⚠️  缓存写入失败: {e}")

            return result

        return wrapper
    return decorator
