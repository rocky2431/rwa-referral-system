"""
积分发放服务
处理所有积分相关的业务逻辑
"""

from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from loguru import logger

from app.models import User, UserPoints, PointTransaction, PointTransactionType, ReferralRelation
from app.services.cache_service import CacheService


class PointsService:
    """积分服务类"""

    @staticmethod
    async def get_or_create_user(
        db: AsyncSession,
        wallet_address: str
    ) -> User:
        """
        获取或创建用户

        Args:
            db: 数据库会话
            wallet_address: 钱包地址

        Returns:
            User对象
        """
        # 查询用户
        result = await db.execute(
            select(User).where(User.wallet_address == wallet_address.lower())
        )
        user = result.scalar_one_or_none()

        # 不存在则创建
        if not user:
            user = User(wallet_address=wallet_address.lower())
            db.add(user)
            await db.flush()
            logger.info(f"✨ 创建新用户: {wallet_address[:10]}...")

        return user

    @staticmethod
    async def get_or_create_user_points(
        db: AsyncSession,
        user_id: int
    ) -> UserPoints:
        """
        获取或创建用户积分账户

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            UserPoints对象
        """
        # 查询积分账户
        result = await db.execute(
            select(UserPoints).where(UserPoints.user_id == user_id)
        )
        user_points = result.scalar_one_or_none()

        # 不存在则创建
        if not user_points:
            user_points = UserPoints(user_id=user_id)
            db.add(user_points)
            await db.flush()
            logger.info(f"💰 创建积分账户: user_id={user_id}")

        return user_points

    @staticmethod
    async def award_referral_points(
        db: AsyncSession,
        referrer_address: str,
        purchaser_address: str,
        points_amount: int,
        level: int,
        purchase_amount: int,
        tx_hash: str,
        block_number: int
    ) -> bool:
        """
        发放推荐积分奖励

        Args:
            db: 数据库会话
            referrer_address: 推荐人钱包地址
            purchaser_address: 购买者钱包地址
            points_amount: 积分数量
            level: 推荐层级 (1或2)
            purchase_amount: 购买金额 (wei)
            tx_hash: 交易哈希
            block_number: 区块号

        Returns:
            是否成功
        """
        try:
            # 1. 获取或创建用户
            referrer = await PointsService.get_or_create_user(db, referrer_address)
            purchaser = await PointsService.get_or_create_user(db, purchaser_address)

            # 2. 获取或创建积分账户
            referrer_points = await PointsService.get_or_create_user_points(db, referrer.id)

            # 3. 增加积分
            referrer_points.available_points += points_amount
            referrer_points.total_earned += points_amount
            referrer_points.points_from_referral += points_amount

            # 4. 更新用户总积分
            referrer.total_points += points_amount

            # 5. 记录交易流水
            transaction_type = (
                PointTransactionType.REFERRAL_L1 if level == 1
                else PointTransactionType.REFERRAL_L2
            )

            transaction = PointTransaction(
                user_id=referrer.id,
                transaction_type=transaction_type,
                amount=points_amount,
                balance_after=referrer_points.available_points,
                related_user_id=purchaser.id,
                description=f"L{level} 推荐奖励 - 来自 {purchaser_address[:10]}...",
                extra_metadata={
                    "purchase_amount_wei": str(purchase_amount),
                    "tx_hash": tx_hash,
                    "block_number": block_number,
                    "level": level
                },
                status="completed"
            )
            db.add(transaction)

            # 6. 更新推荐关系统计
            result = await db.execute(
                select(ReferralRelation).where(
                    ReferralRelation.referee_id == purchaser.id,
                    ReferralRelation.referrer_id == referrer.id
                )
            )
            referral_relation = result.scalar_one_or_none()
            if referral_relation:
                referral_relation.total_rewards_given += points_amount

            await db.commit()

            logger.info(
                f"✅ 积分发放成功: "
                f"推荐人={referrer_address[:10]}... "
                f"购买者={purchaser_address[:10]}... "
                f"积分={points_amount} "
                f"层级=L{level} "
                f"余额={referrer_points.available_points}"
            )

            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 积分发放失败: {e}")
            raise

    @staticmethod
    async def sync_referral_relation(
        db: AsyncSession,
        referee_address: str,
        referrer_address: str,
        tx_hash: str,
        block_number: int
    ) -> bool:
        """
        同步推荐关系到数据库

        Args:
            db: 数据库会话
            referee_address: 被推荐人地址
            referrer_address: 推荐人地址
            tx_hash: 交易哈希
            block_number: 区块号

        Returns:
            是否成功
        """
        try:
            # 1. 获取或创建用户
            referee = await PointsService.get_or_create_user(db, referee_address)
            referrer = await PointsService.get_or_create_user(db, referrer_address)

            # 2. 检查是否已存在推荐关系
            result = await db.execute(
                select(ReferralRelation).where(
                    ReferralRelation.referee_id == referee.id
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.warning(
                    f"⚠️  推荐关系已存在: "
                    f"被推荐人={referee_address[:10]}... "
                    f"已有推荐人ID={existing.referrer_id}"
                )
                return False

            # 3. 创建推荐关系
            referral_relation = ReferralRelation(
                referee_id=referee.id,
                referrer_id=referrer.id,
                blockchain_tx_hash=tx_hash,
                blockchain_block_number=block_number,
                level=1,
                is_active=True
            )
            db.add(referral_relation)

            # 4. 更新推荐人的邀请统计
            referrer.total_invited += 1

            await db.commit()

            logger.info(
                f"🤝 推荐关系同步成功: "
                f"推荐人={referrer_address[:10]}... "
                f"被推荐人={referee_address[:10]}..."
            )

            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 推荐关系同步失败: {e}")
            raise

    @staticmethod
    async def get_user_balance(
        db: AsyncSession,
        wallet_address: str
    ) -> Optional[int]:
        """
        查询用户积分余额（带缓存，快速查询场景）

        Args:
            db: 数据库会话
            wallet_address: 钱包地址

        Returns:
            积分余额，不存在返回None
        """
        # 1. 查询用户
        result = await db.execute(
            select(User).where(User.wallet_address == wallet_address.lower())
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        # 2. 尝试从缓存获取余额
        cached_balance = await CacheService.get_user_balance_cache(user.id)
        if cached_balance is not None:
            logger.debug(f"🎯 余额缓存命中: user_id={user.id}, balance={cached_balance}")
            return cached_balance

        # 3. 缓存未命中，从数据库查询
        result = await db.execute(
            select(UserPoints).where(UserPoints.user_id == user.id)
        )
        user_points = result.scalar_one_or_none()
        balance = user_points.available_points if user_points else 0

        # 4. 写入缓存
        await CacheService.set_user_balance_cache(user.id, balance)
        logger.debug(f"💾 余额已缓存: user_id={user.id}, balance={balance}")

        return balance

    @staticmethod
    async def add_user_points(
        db: AsyncSession,
        user_id: int,
        points: int,
        transaction_type: PointTransactionType,
        description: Optional[str] = None,
        related_user_id: Optional[int] = None,
        related_task_id: Optional[int] = None,
        related_team_id: Optional[int] = None,
        related_question_id: Optional[int] = None,
        extra_metadata: Optional[dict] = None
    ) -> PointTransaction:
        """
        通用的添加用户积分方法（幂等性设计）

        Args:
            db: 数据库会话
            user_id: 用户ID
            points: 积分数量(正数=获得,负数=消费)
            transaction_type: 交易类型
            description: 交易描述
            related_user_id: 关联用户ID
            related_task_id: 关联任务ID
            related_team_id: 关联战队ID
            related_question_id: 关联题目ID
            extra_metadata: 额外元数据

        Returns:
            PointTransaction: 交易记录
        """
        try:
            # 1. 获取或创建用户积分账户
            user_points = await PointsService.get_or_create_user_points(db, user_id)

            # 2. 更新可用积分
            user_points.available_points += points

            # 3. 更新统计信息
            if points > 0:
                user_points.total_earned += points
            else:
                user_points.total_spent += abs(points)

            # 4. 根据交易类型更新来源统计
            if transaction_type in [PointTransactionType.REFERRAL_L1, PointTransactionType.REFERRAL_L2]:
                user_points.points_from_referral += points
            elif transaction_type in [PointTransactionType.TASK_DAILY, PointTransactionType.TASK_WEEKLY, PointTransactionType.TASK_ONCE]:
                user_points.points_from_tasks += points
            elif transaction_type == PointTransactionType.QUIZ_CORRECT:
                user_points.points_from_quiz += points
            elif transaction_type == PointTransactionType.TEAM_REWARD:
                user_points.points_from_team += points
            elif transaction_type == PointTransactionType.PURCHASE:
                user_points.points_from_purchase += points

            # 5. 创建交易流水
            transaction = PointTransaction(
                user_id=user_id,
                transaction_type=transaction_type,
                amount=points,
                balance_after=user_points.available_points,
                description=description,
                related_user_id=related_user_id,
                related_task_id=related_task_id,
                related_team_id=related_team_id,
                related_question_id=related_question_id,
                extra_metadata=extra_metadata or {},
                status="completed"
            )
            db.add(transaction)

            # 6. 更新用户总积分
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.total_points = user_points.available_points

            await db.commit()
            await db.refresh(transaction)

            # 使缓存失效（写后失效策略）
            await CacheService.invalidate_user_all_cache(user_id)

            logger.info(
                f"✅ 积分变动成功: user_id={user_id} "
                f"变动={points:+d} 类型={transaction_type.value} "
                f"余额={user_points.available_points}"
            )

            return transaction

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 积分变动失败: {e}")
            raise

    @staticmethod
    async def get_user_points(
        db: AsyncSession,
        user_id: int
    ) -> Optional[UserPoints]:
        """
        获取用户完整积分信息（带缓存）

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            UserPoints对象,不存在返回None
        """
        # 1. 尝试从缓存获取
        cached_data = await CacheService.get_user_points_cache(user_id)
        if cached_data:
            logger.debug(f"🎯 积分缓存命中: user_id={user_id}")
            # 从缓存构建UserPoints对象（仅包含核心字段）
            user_points = UserPoints(
                id=cached_data.get('id'),
                user_id=user_id,
                available_points=cached_data.get('available_points', 0),
                frozen_points=cached_data.get('frozen_points', 0),
                total_earned=cached_data.get('total_earned', 0),
                total_spent=cached_data.get('total_spent', 0),
                points_from_referral=cached_data.get('points_from_referral', 0),
                points_from_tasks=cached_data.get('points_from_tasks', 0),
                points_from_quiz=cached_data.get('points_from_quiz', 0),
                points_from_team=cached_data.get('points_from_team', 0),
                points_from_purchase=cached_data.get('points_from_purchase', 0)
            )
            return user_points

        # 2. 缓存未命中，从数据库查询
        result = await db.execute(
            select(UserPoints).where(UserPoints.user_id == user_id)
        )
        user_points = result.scalar_one_or_none()

        # 3. 如果查询到数据，写入缓存
        if user_points:
            cache_data = {
                'id': user_points.id,
                'user_id': user_points.user_id,
                'available_points': user_points.available_points,
                'frozen_points': user_points.frozen_points,
                'total_earned': user_points.total_earned,
                'total_spent': user_points.total_spent,
                'points_from_referral': user_points.points_from_referral,
                'points_from_tasks': user_points.points_from_tasks,
                'points_from_quiz': user_points.points_from_quiz,
                'points_from_team': user_points.points_from_team,
                'points_from_purchase': user_points.points_from_purchase
            }
            await CacheService.set_user_points_cache(user_id, cache_data)
            logger.debug(f"💾 积分数据已缓存: user_id={user_id}")

        return user_points

    @staticmethod
    async def get_point_transactions(
        db: AsyncSession,
        user_id: int,
        transaction_type: Optional[PointTransactionType] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[PointTransaction], int]:
        """
        分页查询用户积分流水

        Args:
            db: 数据库会话
            user_id: 用户ID
            transaction_type: 交易类型筛选(可选)
            page: 页码(从1开始)
            page_size: 每页大小

        Returns:
            (交易记录列表, 总记录数)
        """
        # 构建基础查询
        query = select(PointTransaction).where(
            PointTransaction.user_id == user_id
        )

        # 添加类型筛选
        if transaction_type:
            query = query.where(
                PointTransaction.transaction_type == transaction_type
            )

        # 获取总数
        from sqlalchemy import func
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # 分页查询
        query = query.order_by(desc(PointTransaction.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        transactions = result.scalars().all()

        return list(transactions), total

    @staticmethod
    async def exchange_points(
        db: AsyncSession,
        user_id: int,
        points_amount: int,
        exchange_type: str,
        target_address: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> PointTransaction:
        """
        积分兑换功能

        支持的兑换类型:
        - token: 兑换代币
        - nft: 兑换NFT
        - privilege: 兑换权益

        Args:
            db: 数据库会话
            user_id: 用户ID
            points_amount: 兑换积分数量
            exchange_type: 兑换类型
            target_address: 目标接收地址(可选)
            idempotency_key: 幂等性Key(可选)

        Returns:
            PointTransaction: 交易记录

        Raises:
            ValueError: 余额不足或参数无效
        """
        try:
            # 1. 验证兑换类型
            valid_types = ['token', 'nft', 'privilege']
            if exchange_type not in valid_types:
                raise ValueError(
                    f"无效的兑换类型: {exchange_type}. "
                    f"支持的类型: {', '.join(valid_types)}"
                )

            # 2. 获取用户积分账户
            user_points = await PointsService.get_or_create_user_points(db, user_id)

            # 3. 检查余额
            if user_points.available_points < points_amount:
                raise ValueError(
                    f"积分余额不足! "
                    f"当前可用: {user_points.available_points}, "
                    f"需要: {points_amount}"
                )

            # 4. 扣除积分 (使用负数表示消费)
            transaction_type_map = {
                'token': PointTransactionType.EXCHANGE_TOKEN,
                'nft': PointTransactionType.SPEND_ITEM,  # 暂用SPEND_ITEM
                'privilege': PointTransactionType.SPEND_ITEM
            }
            transaction_type = transaction_type_map.get(
                exchange_type,
                PointTransactionType.SPEND_ITEM
            )

            description = f"积分兑换 - {exchange_type}"
            if target_address:
                description += f" (目标地址: {target_address[:10]}...)"

            # 5. 执行积分扣除 (负数表示消费)
            transaction = await PointsService.add_user_points(
                db=db,
                user_id=user_id,
                points=-points_amount,  # 负数 = 消费
                transaction_type=transaction_type,
                description=description,
                extra_metadata={
                    'exchange_type': exchange_type,
                    'target_address': target_address,
                    'idempotency_key': idempotency_key
                }
            )

            logger.info(
                f"✅ 积分兑换成功: "
                f"user_id={user_id} "
                f"类型={exchange_type} "
                f"消费={points_amount} "
                f"余额={transaction.balance_after}"
            )

            return transaction

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"❌ 积分兑换失败: {e}")
            raise

    @staticmethod
    async def get_points_statistics(
        db: AsyncSession
    ) -> dict:
        """
        获取积分系统全局统计数据

        Returns:
            统计数据字典
        """
        from sqlalchemy import func

        try:
            # 1. 统计总用户数
            total_users_result = await db.execute(
                select(func.count(UserPoints.id))
            )
            total_users = total_users_result.scalar_one()

            # 2. 统计总发放积分 (sum of total_earned)
            total_earned_result = await db.execute(
                select(func.sum(UserPoints.total_earned))
            )
            total_distributed = total_earned_result.scalar_one() or 0

            # 3. 统计总消费积分 (sum of total_spent)
            total_spent_result = await db.execute(
                select(func.sum(UserPoints.total_spent))
            )
            total_spent = total_spent_result.scalar_one() or 0

            # 4. 统计各来源积分
            referral_result = await db.execute(
                select(func.sum(UserPoints.points_from_referral))
            )
            referral_points = referral_result.scalar_one() or 0

            task_result = await db.execute(
                select(func.sum(UserPoints.points_from_tasks))
            )
            task_points = task_result.scalar_one() or 0

            quiz_result = await db.execute(
                select(func.sum(UserPoints.points_from_quiz))
            )
            quiz_points = quiz_result.scalar_one() or 0

            team_result = await db.execute(
                select(func.sum(UserPoints.points_from_team))
            )
            team_points = team_result.scalar_one() or 0

            statistics = {
                'total_users': total_users,
                'total_points_distributed': total_distributed,
                'total_points_spent': total_spent,
                'referral_points': referral_points,
                'task_points': task_points,
                'quiz_points': quiz_points,
                'team_points': team_points
            }

            logger.debug(f"📊 积分统计查询成功: {statistics}")

            return statistics

        except Exception as e:
            logger.error(f"❌ 积分统计查询失败: {e}")
            raise
