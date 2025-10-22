"""
用户管理API端点

职责：
- 用户注册（首次连接钱包）
- 通过钱包地址查询用户
- 用户信息更新

设计原则：
- SRP（单一职责）：每个端点只做一件事
- DRY（杜绝重复）：共享逻辑提取到service层
- KISS（简单至上）：保持API接口简洁明了
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.db.session import get_db
from app.models.user import User
from app.models.user_points import UserPoints
from app.models.referral_relation import ReferralRelation
from app.models.point_transaction import PointTransactionType
from app.services.points_service import PointsService
from app.services.task_service import TaskService
from app.models.task import UserTaskStatus
from app.schemas.user import (
    UserRegisterRequest,
    UserResponse,
    UserDetailResponse,
    UserUpdateRequest,
    UserByWalletResponse,
)

router = APIRouter()


@router.get("/by-wallet/{wallet_address}", response_model=UserByWalletResponse)
async def get_user_by_wallet(
    wallet_address: str,
    db: AsyncSession = Depends(get_db)
):
    """
    通过钱包地址查询用户信息

    **功能描述：**
    - 查询用户是否存在
    - 返回用户基本信息（ID、用户名、等级、积分）
    - 前端连接钱包后调用此接口获取用户ID

    **返回说明：**
    - exists=true: 用户已注册，返回完整信息
    - exists=false: 用户未注册，需要调用注册接口

    **使用场景：**
    - 用户连接钱包后，首次进入页面
    - 前端需要将wallet_address映射到user_id
    """
    try:
        # 钱包地址规范化（小写）
        normalized_address = wallet_address.lower()

        # 查询用户
        result = await db.execute(
            select(User).where(User.wallet_address == normalized_address)
        )
        user = result.scalar_one_or_none()

        if not user:
            # 用户不存在
            return UserByWalletResponse(
                exists=False,
                user_id=None,
                wallet_address=normalized_address,
                username=None,
                level=None,
                total_points=None
            )

        # 用户存在，返回基本信息
        return UserByWalletResponse(
            exists=True,
            user_id=user.id,
            wallet_address=user.wallet_address,
            username=user.username,
            level=user.level,
            total_points=user.total_points
        )

    except Exception as e:
        logger.error(f"查询用户失败: wallet={wallet_address}, error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询用户失败: {str(e)}"
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    注册新用户

    **功能描述：**
    - 首次连接钱包时自动注册用户
    - 创建用户记录和积分账户
    - 支持可选填写用户名、头像、邮箱

    **幂等性保证：**
    - 如果钱包地址已存在，返回409冲突错误
    - 前端应先调用 /by-wallet/ 检查用户是否存在

    **返回说明：**
    - 返回新创建的用户基本信息
    - 自动初始化用户等级为1，积分为0

    **SOLID原则应用：**
    - SRP：此函数只负责用户注册，积分初始化由数据库默认值完成
    - OCP：未来可扩展注册来源（OAuth、邮箱等）
    """
    try:
        # 钱包地址规范化（小写）
        normalized_address = request.wallet_address.lower()

        # 检查钱包地址是否已注册
        existing = await db.execute(
            select(User).where(User.wallet_address == normalized_address)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"钱包地址 {normalized_address} 已注册"
            )

        # 创建新用户
        new_user = User(
            wallet_address=normalized_address,  # ✅ 使用规范化地址
            username=request.username or f"User_{normalized_address[:8]}",  # 默认用户名
            avatar_url=request.avatar_url,
            email=request.email,
            level=1,
            experience=0,
            total_points=0,
            is_active=True
        )
        db.add(new_user)
        await db.flush()  # 获取user.id

        # 创建用户积分账户（初始化为0）
        user_points = UserPoints(
            user_id=new_user.id,
            available_points=0,
            frozen_points=0,
            total_earned=0,
            total_spent=0,
            points_from_referral=0,
            points_from_tasks=0,
            points_from_quiz=0,
            points_from_team=0,
            points_from_purchase=0
        )
        db.add(user_points)
        await db.flush()

        # 🎁 新用户注册奖励：100积分
        await PointsService.add_user_points(
            db=db,
            user_id=new_user.id,
            points=100,
            transaction_type=PointTransactionType.REGISTER_REWARD,
            description="新用户注册奖励"
        )
        logger.info(f"💰 新用户注册奖励: user_id={new_user.id}, +100积分")

        # 🎁 推荐人奖励：如果有邀请码，给推荐人发100积分
        if request.invite_code:
            try:
                # 解析邀请码获取推荐人ID（格式：USER000001）
                referrer_id = int(request.invite_code[4:])

                # 查询推荐人是否存在
                referrer_result = await db.execute(
                    select(User).where(User.id == referrer_id)
                )
                referrer = referrer_result.scalar_one_or_none()

                if referrer and referrer.id != new_user.id:
                    # 创建推荐关系
                    referral_relation = ReferralRelation(
                        referrer_id=referrer.id,
                        referee_id=new_user.id,
                        is_active=True
                    )
                    db.add(referral_relation)

                    # 更新推荐人的邀请人数
                    referrer.total_invited += 1

                    # 给推荐人发放100积分奖励
                    await PointsService.add_user_points(
                        db=db,
                        user_id=referrer.id,
                        points=100,
                        transaction_type=PointTransactionType.REFERRAL_REWARD,
                        description=f"推荐新用户注册奖励 (被推荐人: {new_user.wallet_address[:10]}...)",
                        related_user_id=new_user.id
                    )
                    logger.info(
                        f"💰 推荐奖励发放: "
                        f"推荐人ID={referrer.id}, "
                        f"被推荐人ID={new_user.id}, "
                        f"+100积分"
                    )

                    # 📝 更新推荐人的"邀请好友"任务进度
                    try:
                        invite_task = await TaskService.get_task_by_key(db, "invite_friends")
                        if invite_task:
                            # 查找推荐人现有的邀请任务实例
                            invite_user_task = await TaskService.get_user_task(
                                db=db,
                                user_id=referrer.id,
                                task_id=invite_task.id
                            )

                            # 如果不存在,创建新实例
                            if not invite_user_task:
                                invite_user_task = await TaskService.assign_task_to_user(
                                    db=db,
                                    user_id=referrer.id,
                                    task_id=invite_task.id
                                )
                                logger.info(f"✅ 创建邀请任务实例: user_id={referrer.id}, user_task_id={invite_user_task.id}")

                            # 更新任务进度(+1邀请)
                            await TaskService.update_task_progress(
                                db=db,
                                user_task_id=invite_user_task.id,
                                progress_delta=1
                            )
                            logger.info(
                                f"✅ 邀请任务进度更新: "
                                f"推荐人ID={referrer.id}, "
                                f"user_task_id={invite_user_task.id}, "
                                f"进度={invite_user_task.current_value}/{invite_user_task.target_value}"
                            )
                    except Exception as e:
                        logger.warning(f"⚠️ 邀请任务更新失败（不影响注册）: {e}")
                else:
                    logger.warning(f"⚠️ 邀请码无效或不能自己推荐自己: {request.invite_code}")
            except (ValueError, IndexError) as e:
                logger.warning(f"⚠️ 邀请码格式错误: {request.invite_code}, error={e}")

        # 📝 创建并完成"注册成功"任务
        try:
            # 获取注册任务配置
            register_task = await TaskService.get_task_by_key(db, "user_register")
            if register_task:
                # 为用户创建任务实例
                user_task = await TaskService.assign_task_to_user(
                    db=db,
                    user_id=new_user.id,
                    task_id=register_task.id
                )
                # 立即完成任务（进度+1）
                await TaskService.update_task_progress(
                    db=db,
                    user_task_id=user_task.id,
                    progress_delta=1
                )
                logger.info(f"✅ 注册任务自动完成: user_id={new_user.id}, user_task_id={user_task.id}")
        except Exception as e:
            logger.warning(f"⚠️ 注册任务创建失败（不影响注册）: {e}")

        await db.commit()
        await db.refresh(new_user)

        logger.info(
            f"✅ 新用户注册成功: "
            f"user_id={new_user.id}, "
            f"wallet={new_user.wallet_address}, "
            f"username={new_user.username}"
        )

        return new_user

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"用户注册失败: wallet={request.wallet_address}, error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"用户注册失败: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户详细信息

    **功能描述：**
    - 查询用户完整信息（包括统计数据）
    - 用于用户个人中心页面

    **返回数据：**
    - 基本信息：钱包地址、用户名、头像、邮箱
    - 等级系统：level、experience
    - 统计数据：总积分、邀请人数、完成任务数、答题数
    - 活跃度：最后活跃时间、连续登录天数
    - 状态：是否活跃、是否被封禁
    """
    try:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"用户ID {user_id} 不存在"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户详情失败: user_id={user_id}, error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户详情失败: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户信息

    **功能描述：**
    - 允许用户更新用户名、头像、邮箱
    - 其他字段（积分、等级等）不可直接修改

    **可更新字段：**
    - username: 用户名
    - avatar_url: 头像URL
    - email: 邮箱

    **设计原则：**
    - YAGNI：只实现当前需要的更新功能
    - SRP：用户信息更新与业务逻辑（积分、等级）分离
    """
    try:
        # 查询用户
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"用户ID {user_id} 不存在"
            )

        # 更新字段（只更新非None的字段）
        if request.username is not None:
            user.username = request.username
        if request.avatar_url is not None:
            user.avatar_url = request.avatar_url
        if request.email is not None:
            user.email = request.email

        await db.commit()
        await db.refresh(user)

        logger.info(f"✅ 用户信息更新成功: user_id={user_id}")

        return user

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新用户信息失败: user_id={user_id}, error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户信息失败: {str(e)}"
        )
