"""
重试机制工具
实现指数退避重试策略
"""

import asyncio
from typing import Callable, Any, Optional, Type
from functools import wraps
from loguru import logger


class RetryConfig:
    """重试配置"""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        exceptions: tuple = (Exception,)
    ):
        """
        初始化重试配置

        Args:
            max_retries: 最大重试次数
            initial_delay: 初始延迟（秒）
            max_delay: 最大延迟（秒）
            exponential_base: 指数基数
            exceptions: 需要重试的异常类型元组
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.exceptions = exceptions


async def retry_async(
    func: Callable,
    config: RetryConfig,
    *args,
    **kwargs
) -> Any:
    """
    异步函数重试装饰器

    Args:
        func: 要重试的异步函数
        config: 重试配置
        *args: 函数参数
        **kwargs: 函数关键字参数

    Returns:
        函数执行结果

    Raises:
        最后一次重试的异常
    """
    last_exception = None
    delay = config.initial_delay

    for attempt in range(config.max_retries + 1):
        try:
            result = await func(*args, **kwargs)
            if attempt > 0:
                logger.success(f"✅ 重试成功 (第{attempt}次尝试): {func.__name__}")
            return result

        except config.exceptions as e:
            last_exception = e

            if attempt < config.max_retries:
                logger.warning(
                    f"⚠️  操作失败，{delay:.1f}秒后重试 "
                    f"(尝试 {attempt + 1}/{config.max_retries}): {e}"
                )
                await asyncio.sleep(delay)

                # 指数退避
                delay = min(delay * config.exponential_base, config.max_delay)
            else:
                logger.error(
                    f"❌ 重试失败，已达最大重试次数 ({config.max_retries}): {e}"
                )

    raise last_exception


def async_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    异步函数重试装饰器工厂

    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟（秒）
        max_delay: 最大延迟（秒）
        exponential_base: 指数基数
        exceptions: 需要重试的异常类型元组

    Returns:
        装饰器函数
    """
    config = RetryConfig(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        exceptions=exceptions
    )

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(func, config, *args, **kwargs)
        return wrapper

    return decorator


class CircuitBreaker:
    """
    熔断器模式
    防止系统在故障时持续重试
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        """
        初始化熔断器

        Args:
            failure_threshold: 失败阈值（连续失败次数）
            recovery_timeout: 恢复超时时间（秒）
            expected_exception: 预期的异常类型
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half_open

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        通过熔断器调用函数

        Args:
            func: 要调用的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果

        Raises:
            Exception: 熔断器打开时抛出异常
        """
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
                logger.info("🔄 熔断器进入半开状态，尝试恢复")
            else:
                raise Exception(
                    f"熔断器已打开，剩余恢复时间: "
                    f"{self.recovery_timeout - (asyncio.get_event_loop().time() - self.last_failure_time):.1f}秒"
                )

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置熔断器"""
        if self.last_failure_time is None:
            return True

        return (asyncio.get_event_loop().time() - self.last_failure_time) >= self.recovery_timeout

    def _on_success(self):
        """成功回调"""
        if self.state == "half_open":
            logger.success("✅ 熔断器恢复，进入关闭状态")
            self.state = "closed"
            self.failure_count = 0

    def _on_failure(self):
        """失败回调"""
        self.failure_count += 1
        self.last_failure_time = asyncio.get_event_loop().time()

        if self.failure_count >= self.failure_threshold:
            if self.state != "open":
                logger.error(
                    f"❌ 熔断器打开！连续失败 {self.failure_count} 次，"
                    f"{self.recovery_timeout}秒后尝试恢复"
                )
                self.state = "open"

    def reset(self):
        """手动重置熔断器"""
        self.state = "closed"
        self.failure_count = 0
        self.last_failure_time = None
        logger.info("🔄 熔断器已重置")
