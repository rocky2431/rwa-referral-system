"""
幂等性机制测试
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.main import app
from app.services.points_service import PointsService
from app.services.idempotency import IdempotencyService
from app.models import PointTransaction
from app.models.point_transaction import PointTransactionType


@pytest.mark.asyncio
async def test_idempotency_key_generation():
    """测试幂等性Key生成"""
    key1 = IdempotencyService.generate_idempotency_key(
        user_id=1,
        transaction_type="TASK_DAILY",
        amount=100
    )

    key2 = IdempotencyService.generate_idempotency_key(
        user_id=1,
        transaction_type="TASK_DAILY",
        amount=100
    )

    # 相同参数应生成相同Key
    assert key1 == key2

    # 不同参数应生成不同Key
    key3 = IdempotencyService.generate_idempotency_key(
        user_id=1,
        transaction_type="TASK_DAILY",
        amount=200  # 不同的amount
    )
    assert key1 != key3


@pytest.mark.asyncio
async def test_add_points_with_idempotency_key_first_time(
    db_session: AsyncSession,
    override_get_db
):
    """测试使用幂等性Key首次添加积分"""
    # 创建用户
    wallet_address = "0xidempotent1234567890abcdef1234567890ab"
    user = await PointsService.get_or_create_user(db_session, wallet_address)
    await db_session.commit()

    # 首次请求
    request_data = {
        "user_id": user.id,
        "amount": 100,
        "transaction_type": "TASK_DAILY",
        "description": "幂等性测试",
        "idempotency_key": "test_key_12345"
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/points/add", json=request_data)

    assert response.status_code == 200
    data = response.json()
    first_transaction_id = data["id"]
    assert data["amount"] == 100
    assert data["balance_after"] == 100

    # 验证积分账户
    user_points = await PointsService.get_user_points(db_session, user.id)
    assert user_points.available_points == 100


@pytest.mark.asyncio
async def test_add_points_with_idempotency_key_duplicate(
    db_session: AsyncSession,
    override_get_db
):
    """测试使用相同幂等性Key重复添加积分"""
    # 创建用户
    wallet_address = "0xidempotent2234567890abcdef1234567890ab"
    user = await PointsService.get_or_create_user(db_session, wallet_address)
    await db_session.commit()

    request_data = {
        "user_id": user.id,
        "amount": 150,
        "transaction_type": "TASK_DAILY",
        "description": "幂等性重复测试",
        "idempotency_key": "test_duplicate_key_67890"
    }

    # 第一次请求
    async with AsyncClient(app=app, base_url="http://test") as client:
        response1 = await client.post("/api/v1/points/add", json=request_data)

    assert response1.status_code == 200
    data1 = response1.json()
    first_transaction_id = data1["id"]

    # 第二次请求（相同幂等性Key）
    async with AsyncClient(app=app, base_url="http://test") as client:
        response2 = await client.post("/api/v1/points/add", json=request_data)

    assert response2.status_code == 200
    data2 = response2.json()

    # 应返回相同的交易记录
    assert data2["id"] == first_transaction_id
    assert data2["amount"] == 150

    # 积分不应重复发放
    user_points = await PointsService.get_user_points(db_session, user.id)
    assert user_points.available_points == 150  # 仍然是150，不是300

    # 数据库中只应有1条交易记录
    result = await db_session.execute(
        select(PointTransaction).where(PointTransaction.user_id == user.id)
    )
    transactions = result.scalars().all()
    assert len(transactions) == 1


@pytest.mark.asyncio
async def test_add_points_without_idempotency_key_allows_duplicates(
    db_session: AsyncSession,
    override_get_db
):
    """测试不使用幂等性Key允许重复添加"""
    # 创建用户
    wallet_address = "0xnokey1234567890abcdef1234567890abcdef12"
    user = await PointsService.get_or_create_user(db_session, wallet_address)
    await db_session.commit()

    request_data = {
        "user_id": user.id,
        "amount": 50,
        "transaction_type": "TASK_DAILY",
        "description": "无幂等性Key测试"
        # 不提供 idempotency_key
    }

    # 第一次请求
    async with AsyncClient(app=app, base_url="http://test") as client:
        response1 = await client.post("/api/v1/points/add", json=request_data)
    assert response1.status_code == 200

    # 第二次请求（相同数据但无幂等性Key）
    async with AsyncClient(app=app, base_url="http://test") as client:
        response2 = await client.post("/api/v1/points/add", json=request_data)
    assert response2.status_code == 200

    # 积分应重复发放
    user_points = await PointsService.get_user_points(db_session, user.id)
    assert user_points.available_points == 100  # 50 + 50

    # 数据库中应有2条交易记录
    result = await db_session.execute(
        select(PointTransaction).where(PointTransaction.user_id == user.id)
    )
    transactions = result.scalars().all()
    assert len(transactions) == 2


@pytest.mark.asyncio
async def test_concurrent_requests_with_lock(
    db_session: AsyncSession,
    override_get_db
):
    """测试并发请求时的锁机制"""
    import asyncio

    # 创建用户
    wallet_address = "0xconcurrent1234567890abcdef1234567890ab"
    user = await PointsService.get_or_create_user(db_session, wallet_address)
    await db_session.commit()

    async def make_request(idempotency_key: str):
        """发起添加积分请求"""
        request_data = {
            "user_id": user.id,
            "amount": 10,
            "transaction_type": "TASK_DAILY",
            "description": f"并发测试 {idempotency_key}",
            "idempotency_key": idempotency_key
        }
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/points/add", json=request_data)
        return response

    # 同时发起10个请求，使用不同的幂等性Key
    tasks = [make_request(f"concurrent_key_{i}") for i in range(10)]
    responses = await asyncio.gather(*tasks)

    # 所有请求都应成功
    assert all(r.status_code == 200 for r in responses)

    # 验证积分正确累加
    user_points = await PointsService.get_user_points(db_session, user.id)
    assert user_points.available_points == 100  # 10 * 10

    # 验证有10条交易记录
    result = await db_session.execute(
        select(PointTransaction).where(PointTransaction.user_id == user.id)
    )
    transactions = result.scalars().all()
    assert len(transactions) == 10


@pytest.mark.asyncio
async def test_idempotency_key_with_different_amounts(
    db_session: AsyncSession,
    override_get_db
):
    """测试不同金额使用不同幂等性Key"""
    # 创建用户
    wallet_address = "0xdiffamount1234567890abcdef1234567890ab"
    user = await PointsService.get_or_create_user(db_session, wallet_address)
    await db_session.commit()

    # 第一个请求：100积分
    request1 = {
        "user_id": user.id,
        "amount": 100,
        "transaction_type": "TASK_DAILY",
        "idempotency_key": "amount_test_key"
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response1 = await client.post("/api/v1/points/add", json=request1)
    assert response1.status_code == 200

    # 第二个请求：200积分（不同金额，相同Key会如何？）
    # 注意：实际上应该使用不同的幂等性Key，这里测试边界情况
    request2 = {
        "user_id": user.id,
        "amount": 200,
        "transaction_type": "TASK_DAILY",
        "idempotency_key": "amount_test_key"  # 相同Key
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response2 = await client.post("/api/v1/points/add", json=request2)
    assert response2.status_code == 200

    # 应返回第一次的结果（幂等性保护）
    data2 = response2.json()
    assert data2["amount"] == 100  # 不是200

    # 总积分应该是100，不是300
    user_points = await PointsService.get_user_points(db_session, user.id)
    assert user_points.available_points == 100
