"""
Pytest配置和通用fixtures
"""
import asyncio
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.models import Base
from app.db.session import get_db
from app.main import app
from app.core.config import settings
from app.utils.redis_client import redis_client


# 测试数据库URL（使用独立的测试数据库）
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    "rwa_referral",
    "rwa_referral_test"
).replace('postgresql://', 'postgresql+asyncpg://')


# 创建测试引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool  # 测试时不使用连接池
)

# 创建测试会话工厂
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    创建测试数据库会话

    每个测试函数都会创建一个新的会话，并在测试结束时回滚所有更改
    """
    # 清理Redis锁（每个测试开始前）
    try:
        client = redis_client._client
        if client:
            keys = await client.keys("lock:*")
            if keys:
                await client.delete(*keys)
            # 清理幂等性键
            idempotency_keys = await client.keys("idempotency:*")
            if idempotency_keys:
                await client.delete(*idempotency_keys)
    except Exception as e:
        print(f"清理Redis失败: {e}")

    # 清理所有表数据（解决统计测试的数据隔离问题）
    async with test_engine.begin() as conn:
        # 按依赖顺序删除数据
        await conn.execute(Base.metadata.tables['point_transactions'].delete())
        await conn.execute(Base.metadata.tables['user_points'].delete())
        await conn.execute(Base.metadata.tables['team_members'].delete())
        await conn.execute(Base.metadata.tables['teams'].delete())
        await conn.execute(Base.metadata.tables['users'].delete())

    async with test_engine.begin() as connection:
        async with TestSessionLocal(bind=connection) as session:
            # 开启嵌套事务
            await connection.begin_nested()

            yield session

            # 测试结束后回滚
            await session.rollback()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    设置测试数据库和Redis连接

    在所有测试开始前创建表并连接Redis，结束后删除表并断开Redis
    """
    # 初始化Redis连接
    try:
        await redis_client.connect()
        print("✅ Redis测试连接初始化成功")
    except Exception as e:
        print(f"⚠️ Redis测试连接失败: {e}")

    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # 删除所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # 断开Redis连接
    try:
        await redis_client.disconnect()
    except Exception as e:
        print(f"⚠️ Redis断开连接失败: {e}")


@pytest.fixture
def override_get_db(db_session: AsyncSession):
    """覆盖FastAPI的数据库依赖"""
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()
