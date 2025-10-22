"""
PointsService单元测试
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.points_service import PointsService
from app.models import User, UserPoints, PointTransaction
from app.models.point_transaction import PointTransactionType


class TestPointsService:
    """PointsService测试类"""

    @pytest.mark.asyncio
    async def test_get_or_create_user(self, db_session: AsyncSession):
        """测试获取或创建用户"""
        wallet_address = "0x1234567890abcdef1234567890abcdef12345678"

        # 第一次调用 - 创建用户
        user1 = await PointsService.get_or_create_user(db_session, wallet_address)
        await db_session.commit()

        assert user1 is not None
        assert user1.wallet_address == wallet_address.lower()
        assert user1.id is not None

        # 第二次调用 - 获取已存在用户
        user2 = await PointsService.get_or_create_user(db_session, wallet_address)
        await db_session.commit()

        assert user2.id == user1.id
        assert user2.wallet_address == user1.wallet_address

    @pytest.mark.asyncio
    async def test_get_or_create_user_points(self, db_session: AsyncSession):
        """测试获取或创建用户积分账户"""
        # 先创建用户
        wallet_address = "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"
        user = await PointsService.get_or_create_user(db_session, wallet_address)
        await db_session.commit()

        # 第一次调用 - 创建积分账户
        points1 = await PointsService.get_or_create_user_points(db_session, user.id)
        await db_session.commit()

        assert points1 is not None
        assert points1.user_id == user.id
        assert points1.available_points == 0
        assert points1.total_earned == 0

        # 第二次调用 - 获取已存在积分账户
        points2 = await PointsService.get_or_create_user_points(db_session, user.id)
        await db_session.commit()

        assert points2.user_id == points1.user_id

    @pytest.mark.asyncio
    async def test_add_user_points_positive(self, db_session: AsyncSession):
        """测试添加积分（正数）"""
        # 创建用户
        wallet_address = "0x1111111111111111111111111111111111111111"
        user = await PointsService.get_or_create_user(db_session, wallet_address)
        await db_session.commit()

        # 添加100积分
        transaction = await PointsService.add_user_points(
            db=db_session,
            user_id=user.id,
            points=100,
            transaction_type=PointTransactionType.TASK_DAILY,
            description="每日任务奖励"
        )
        await db_session.commit()

        # 验证交易记录
        assert transaction.user_id == user.id
        assert transaction.amount == 100
        assert transaction.balance_after == 100
        assert transaction.transaction_type == PointTransactionType.TASK_DAILY

        # 验证用户积分账户
        user_points = await PointsService.get_user_points(db_session, user.id)
        assert user_points.available_points == 100
        assert user_points.total_earned == 100
        assert user_points.points_from_tasks == 100

        # 验证用户总积分
        result = await db_session.execute(select(User).where(User.id == user.id))
        updated_user = result.scalar_one()
        assert updated_user.total_points == 100

    @pytest.mark.asyncio
    async def test_add_user_points_negative(self, db_session: AsyncSession):
        """测试扣除积分（负数）"""
        # 创建用户并初始化积分
        wallet_address = "0x2222222222222222222222222222222222222222"
        user = await PointsService.get_or_create_user(db_session, wallet_address)
        await db_session.commit()

        # 先添加200积分
        await PointsService.add_user_points(
            db=db_session,
            user_id=user.id,
            points=200,
            transaction_type=PointTransactionType.TASK_DAILY,
            description="初始积分"
        )
        await db_session.commit()

        # 扣除50积分
        transaction = await PointsService.add_user_points(
            db=db_session,
            user_id=user.id,
            points=-50,
            transaction_type=PointTransactionType.REDEEM,
            description="兑换商品"
        )
        await db_session.commit()

        # 验证交易记录
        assert transaction.amount == -50
        assert transaction.balance_after == 150

        # 验证用户积分账户
        user_points = await PointsService.get_user_points(db_session, user.id)
        assert user_points.available_points == 150
        assert user_points.total_earned == 200
        assert user_points.total_spent == 50

    @pytest.mark.asyncio
    async def test_add_user_points_multiple_sources(self, db_session: AsyncSession):
        """测试不同来源积分统计"""
        # 创建用户
        wallet_address = "0x3333333333333333333333333333333333333333"
        user = await PointsService.get_or_create_user(db_session, wallet_address)
        await db_session.commit()

        # 添加不同来源的积分
        await PointsService.add_user_points(
            db=db_session,
            user_id=user.id,
            points=100,
            transaction_type=PointTransactionType.TASK_DAILY,
            description="任务奖励"
        )
        await PointsService.add_user_points(
            db=db_session,
            user_id=user.id,
            points=50,
            transaction_type=PointTransactionType.REFERRAL_L1,
            description="推荐奖励"
        )
        await PointsService.add_user_points(
            db=db_session,
            user_id=user.id,
            points=30,
            transaction_type=PointTransactionType.QUIZ_CORRECT,
            description="答题奖励"
        )
        await db_session.commit()

        # 验证各来源积分统计
        user_points = await PointsService.get_user_points(db_session, user.id)
        assert user_points.available_points == 180
        assert user_points.points_from_tasks == 100
        assert user_points.points_from_referral == 50
        assert user_points.points_from_quiz == 30

    @pytest.mark.asyncio
    async def test_get_point_transactions(self, db_session: AsyncSession):
        """测试查询积分交易历史"""
        # 创建用户
        wallet_address = "0x4444444444444444444444444444444444444444"
        user = await PointsService.get_or_create_user(db_session, wallet_address)
        await db_session.commit()

        # 创建多条交易记录
        for i in range(5):
            await PointsService.add_user_points(
                db=db_session,
                user_id=user.id,
                points=10 * (i + 1),
                transaction_type=PointTransactionType.TASK_DAILY,
                description=f"交易{i+1}"
            )
        await db_session.commit()

        # 查询第1页（每页3条）
        transactions, total = await PointsService.get_point_transactions(
            db=db_session,
            user_id=user.id,
            page=1,
            page_size=3
        )

        assert total == 5
        assert len(transactions) == 3
        # 应该按时间倒序排列
        assert transactions[0].amount == 50
        assert transactions[1].amount == 40
        assert transactions[2].amount == 30

        # 查询第2页
        transactions, total = await PointsService.get_point_transactions(
            db=db_session,
            user_id=user.id,
            page=2,
            page_size=3
        )

        assert total == 5
        assert len(transactions) == 2
        assert transactions[0].amount == 20
        assert transactions[1].amount == 10

    @pytest.mark.asyncio
    async def test_get_point_transactions_with_filter(self, db_session: AsyncSession):
        """测试按类型筛选交易历史"""
        # 创建用户
        wallet_address = "0x5555555555555555555555555555555555555555"
        user = await PointsService.get_or_create_user(db_session, wallet_address)
        await db_session.commit()

        # 创建不同类型的交易
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

        # 仅查询任务类型
        transactions, total = await PointsService.get_point_transactions(
            db=db_session,
            user_id=user.id,
            transaction_type=PointTransactionType.TASK_DAILY
        )

        assert total == 2
        assert len(transactions) == 2
        assert all(t.transaction_type == PointTransactionType.TASK_DAILY for t in transactions)

    @pytest.mark.asyncio
    async def test_get_user_balance(self, db_session: AsyncSession):
        """测试查询用户余额"""
        wallet_address = "0x6666666666666666666666666666666666666666"

        # 用户不存在时返回None
        balance = await PointsService.get_user_balance(db_session, wallet_address)
        assert balance is None

        # 创建用户并添加积分
        user = await PointsService.get_or_create_user(db_session, wallet_address)
        await PointsService.add_user_points(
            db=db_session,
            user_id=user.id,
            points=250,
            transaction_type=PointTransactionType.TASK_DAILY
        )
        await db_session.commit()

        # 查询余额
        balance = await PointsService.get_user_balance(db_session, wallet_address)
        assert balance == 250
