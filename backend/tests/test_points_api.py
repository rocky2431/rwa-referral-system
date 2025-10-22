"""
积分API端点测试
"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.services.points_service import PointsService
from app.models.point_transaction import PointTransactionType


@pytest.mark.asyncio
async def test_get_user_points_not_found(db_session: AsyncSession, override_get_db):
    """测试查询不存在的用户积分"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/points/user/999999")

    assert response.status_code == 404
    assert "不存在" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_user_points_success(db_session: AsyncSession, override_get_db):
    """测试查询用户积分成功"""
    # 创建用户并添加积分
    wallet_address = "0x1234567890123456789012345678901234567890"
    user = await PointsService.get_or_create_user(db_session, wallet_address)
    await PointsService.add_user_points(
        db=db_session,
        user_id=user.id,
        points=150,
        transaction_type=PointTransactionType.TASK_DAILY
    )
    await db_session.commit()

    # 查询积分
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/api/v1/points/user/{user.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user.id
    assert data["available_points"] == 150
    assert data["total_earned"] == 150


@pytest.mark.asyncio
async def test_get_user_transactions(db_session: AsyncSession, override_get_db):
    """测试查询用户交易历史"""
    # 创建用户并添加多笔交易
    wallet_address = "0x2222222222222222222222222222222222222222"
    user = await PointsService.get_or_create_user(db_session, wallet_address)

    for i in range(10):
        await PointsService.add_user_points(
            db=db_session,
            user_id=user.id,
            points=10 * (i + 1),
            transaction_type=PointTransactionType.TASK_DAILY,
            description=f"交易{i+1}"
        )
    await db_session.commit()

    # 查询第1页（默认50条）
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/api/v1/points/transactions/{user.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 10
    assert len(data["data"]) == 10
    assert data["page"] == 1
    assert data["page_size"] == 50


@pytest.mark.asyncio
async def test_get_user_transactions_pagination(db_session: AsyncSession, override_get_db):
    """测试交易历史分页"""
    # 创建用户并添加交易
    wallet_address = "0x3333333333333333333333333333333333333333"
    user = await PointsService.get_or_create_user(db_session, wallet_address)

    for i in range(25):
        await PointsService.add_user_points(
            db=db_session,
            user_id=user.id,
            points=10,
            transaction_type=PointTransactionType.TASK_DAILY
        )
    await db_session.commit()

    # 查询第2页，每页10条
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/points/transactions/{user.id}",
            params={"page": 2, "page_size": 10}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 25
    assert len(data["data"]) == 10
    assert data["page"] == 2
    assert data["page_size"] == 10


@pytest.mark.asyncio
async def test_get_user_transactions_with_filter(db_session: AsyncSession, override_get_db):
    """测试按类型筛选交易历史"""
    # 创建用户并添加不同类型交易
    wallet_address = "0x4444444444444444444444444444444444444444"
    user = await PointsService.get_or_create_user(db_session, wallet_address)

    await PointsService.add_user_points(
        db=db_session,
        user_id=user.id,
        points=100,
        transaction_type=PointTransactionType.TASK_DAILY
    )
    await PointsService.add_user_points(
        db=db_session,
        user_id=user.id,
        points=50,
        transaction_type=PointTransactionType.REFERRAL_L1
    )
    await PointsService.add_user_points(
        db=db_session,
        user_id=user.id,
        points=30,
        transaction_type=PointTransactionType.TASK_DAILY
    )
    await db_session.commit()

    # 仅查询推荐类型
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/points/transactions/{user.id}",
            params={"transaction_type": "referral_l1"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["data"]) == 1
    assert data["data"][0]["transaction_type"] == "referral_l1"


@pytest.mark.asyncio
async def test_add_user_points_success(db_session: AsyncSession, override_get_db):
    """测试添加积分成功"""
    # 创建用户
    wallet_address = "0x5555555555555555555555555555555555555555"
    user = await PointsService.get_or_create_user(db_session, wallet_address)
    await db_session.commit()

    # 添加积分
    request_data = {
        "user_id": user.id,
        "amount": 200,
        "transaction_type": "task_daily",
        "description": "测试奖励"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/points/add", json=request_data)

    # 调试输出
    if response.status_code != 200:
        print(f"Error response: {response.json()}")

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user.id
    assert data["amount"] == 200
    assert data["balance_after"] == 200


@pytest.mark.asyncio
async def test_get_user_balance_by_wallet_exists(db_session: AsyncSession, override_get_db):
    """测试通过钱包地址查询余额（用户存在）"""
    # 创建用户并添加积分
    wallet_address = "0x6666666666666666666666666666666666666666"
    user = await PointsService.get_or_create_user(db_session, wallet_address)
    await PointsService.add_user_points(
        db=db_session,
        user_id=user.id,
        points=300,
        transaction_type=PointTransactionType.TASK_DAILY
    )
    await db_session.commit()

    # 查询余额
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/api/v1/points/balance/{wallet_address}")

    assert response.status_code == 200
    data = response.json()
    assert data["wallet_address"] == wallet_address.lower()
    assert data["available_points"] == 300
    assert data["exists"] is True


@pytest.mark.asyncio
async def test_get_user_balance_by_wallet_not_exists(db_session: AsyncSession, override_get_db):
    """测试通过钱包地址查询余额（用户不存在）"""
    wallet_address = "0x9999999999999999999999999999999999999999"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/api/v1/points/balance/{wallet_address}")

    assert response.status_code == 200
    data = response.json()
    assert data["wallet_address"] == wallet_address.lower()
    assert data["available_points"] == 0
    assert data["exists"] is False


@pytest.mark.asyncio
async def test_exchange_points_success(db_session: AsyncSession, override_get_db):
    """测试积分兑换成功 - token类型"""
    # 创建用户并添加积分
    wallet_address = "0x7777777777777777777777777777777777777777"
    user = await PointsService.get_or_create_user(db_session, wallet_address)
    await PointsService.add_user_points(
        db=db_session,
        user_id=user.id,
        points=1000,
        transaction_type=PointTransactionType.TASK_DAILY
    )
    await db_session.commit()

    # 兑换100积分为token
    request_data = {
        "user_id": user.id,
        "points_amount": 100,
        "exchange_type": "token",
        "target_address": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/points/exchange", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user.id
    assert data["points_spent"] == 100
    assert data["exchange_type"] == "token"
    assert data["status"] == "completed"
    assert data["balance_after"] == 900
    assert data["target_address"] == "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


@pytest.mark.asyncio
async def test_exchange_points_insufficient_balance(db_session: AsyncSession, override_get_db):
    """测试积分兑换失败 - 余额不足"""
    # 创建用户，积分不足
    wallet_address = "0x8888888888888888888888888888888888888888"
    user = await PointsService.get_or_create_user(db_session, wallet_address)
    await PointsService.add_user_points(
        db=db_session,
        user_id=user.id,
        points=50,
        transaction_type=PointTransactionType.TASK_DAILY
    )
    await db_session.commit()

    # 尝试兑换100积分
    request_data = {
        "user_id": user.id,
        "points_amount": 100,
        "exchange_type": "token"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/points/exchange", json=request_data)

    assert response.status_code == 400
    assert "余额不足" in response.json()["detail"]


@pytest.mark.asyncio
async def test_exchange_points_invalid_type(db_session: AsyncSession, override_get_db):
    """测试积分兑换失败 - 无效兑换类型"""
    # 创建用户并添加积分
    wallet_address = "0x9999999999999999999999999999999999999998"
    user = await PointsService.get_or_create_user(db_session, wallet_address)
    await PointsService.add_user_points(
        db=db_session,
        user_id=user.id,
        points=1000,
        transaction_type=PointTransactionType.TASK_DAILY
    )
    await db_session.commit()

    # 使用无效类型
    request_data = {
        "user_id": user.id,
        "points_amount": 100,
        "exchange_type": "invalid_type"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/points/exchange", json=request_data)

    assert response.status_code == 400
    assert "无效的兑换类型" in response.json()["detail"]


@pytest.mark.asyncio
async def test_exchange_points_idempotency(db_session: AsyncSession, override_get_db):
    """测试积分兑换幂等性 - 重复请求返回相同结果"""
    # 创建用户并添加积分
    wallet_address = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaab"
    user = await PointsService.get_or_create_user(db_session, wallet_address)
    await PointsService.add_user_points(
        db=db_session,
        user_id=user.id,
        points=1000,
        transaction_type=PointTransactionType.TASK_DAILY
    )
    await db_session.commit()

    # 第一次兑换
    request_data = {
        "user_id": user.id,
        "points_amount": 100,
        "exchange_type": "nft",
        "idempotency_key": "test_idempotency_key_123"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response1 = await client.post("/api/v1/points/exchange", json=request_data)

    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["balance_after"] == 900

    # 第二次相同请求（幂等）
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response2 = await client.post("/api/v1/points/exchange", json=request_data)

    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["balance_after"] == 900  # 余额不变
    assert data2["transaction_id"] == data1["transaction_id"]  # 返回相同交易


@pytest.mark.asyncio
async def test_get_points_statistics_empty(db_session: AsyncSession, override_get_db):
    """测试积分统计 - 无用户时"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/points/statistics")

    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] == 0
    assert data["total_points_distributed"] == 0
    assert data["total_points_spent"] == 0
    assert data["referral_points"] == 0
    assert data["task_points"] == 0
    assert data["quiz_points"] == 0
    assert data["team_points"] == 0


@pytest.mark.asyncio
async def test_get_points_statistics_with_data(db_session: AsyncSession, override_get_db):
    """测试积分统计 - 有数据时"""
    # 创建多个用户并添加不同来源积分
    wallet1 = "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    wallet2 = "0xcccccccccccccccccccccccccccccccccccccccc"

    user1 = await PointsService.get_or_create_user(db_session, wallet1)
    user2 = await PointsService.get_or_create_user(db_session, wallet2)

    # 用户1：任务奖励200 + 推荐奖励50
    await PointsService.add_user_points(
        db=db_session,
        user_id=user1.id,
        points=200,
        transaction_type=PointTransactionType.TASK_DAILY
    )
    await PointsService.add_user_points(
        db=db_session,
        user_id=user1.id,
        points=50,
        transaction_type=PointTransactionType.REFERRAL_L1
    )

    # 用户2：答题奖励30 + 战队奖励70
    await PointsService.add_user_points(
        db=db_session,
        user_id=user2.id,
        points=30,
        transaction_type=PointTransactionType.QUIZ_CORRECT
    )
    await PointsService.add_user_points(
        db=db_session,
        user_id=user2.id,
        points=70,
        transaction_type=PointTransactionType.TEAM_REWARD
    )

    # 用户1消费50积分
    await PointsService.add_user_points(
        db=db_session,
        user_id=user1.id,
        points=-50,
        transaction_type=PointTransactionType.EXCHANGE_TOKEN
    )

    await db_session.commit()

    # 查询统计
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/points/statistics")

    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] == 2
    assert data["total_points_distributed"] == 350  # 200+50+30+70
    assert data["total_points_spent"] == 50
    assert data["referral_points"] == 50
    assert data["task_points"] == 200
    assert data["quiz_points"] == 30
    assert data["team_points"] == 70
