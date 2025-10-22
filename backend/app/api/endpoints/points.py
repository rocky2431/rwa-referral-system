"""
积分系统API端点
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.points_service import PointsService
from app.services.idempotency import IdempotencyService
from app.schemas.points import (
    UserPointsResponse,
    PointTransactionResponse,
    PointTransactionCreate,
    PointsHistoryResponse,
    PointsExchangeRequest,
    PointsExchangeResponse,
    PointsStatistics
)
from app.models.point_transaction import PointTransactionType
from loguru import logger

router = APIRouter()


@router.get("/user/{user_id}", response_model=UserPointsResponse)
async def get_user_points(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户积分信息

    返回用户的完整积分账户信息，包括：
    - 可用积分、冻结积分
    - 累计获得、累计消费
    - 各来源积分统计（推荐、任务、答题、战队、购买）
    """
    try:
        user_points = await PointsService.get_user_points(db, user_id)

        if not user_points:
            raise HTTPException(
                status_code=404,
                detail=f"用户ID {user_id} 的积分账户不存在"
            )

        return user_points

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户积分失败: user_id={user_id}, error={e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取用户积分失败: {str(e)}"
        )


@router.get("/transactions/{user_id}", response_model=PointsHistoryResponse)
async def get_user_transactions(
    user_id: int,
    transaction_type: Optional[PointTransactionType] = Query(None, description="交易类型筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db)
):
    """
    查询用户积分交易历史（分页）

    支持按交易类型筛选，返回交易记录列表和总数
    """
    try:
        transactions, total = await PointsService.get_point_transactions(
            db=db,
            user_id=user_id,
            transaction_type=transaction_type,
            page=page,
            page_size=page_size
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": transactions
        }

    except Exception as e:
        logger.error(f"查询交易历史失败: user_id={user_id}, error={e}")
        raise HTTPException(
            status_code=500,
            detail=f"查询交易历史失败: {str(e)}"
        )


@router.post("/add", response_model=PointTransactionResponse)
async def add_user_points(
    request: PointTransactionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    添加用户积分（系统/管理员端点）

    用于系统或管理员手动发放/扣除积分
    支持正数（获得）和负数（消费）

    **幂等性保证**:
    - 如果提供 idempotency_key，系统会检查是否已处理过相同请求
    - 重复请求将返回之前的交易记录，不会重复发放积分

    **注意**: 此端点应受到权限保护，仅限系统或管理员调用
    """
    lock = None
    try:
        # 1. 幂等性检查
        if request.idempotency_key:
            existing = await IdempotencyService.check_idempotency(request.idempotency_key)
            if existing:
                logger.info(
                    f"🔁 幂等性拦截: 请求已处理过 "
                    f"idempotency_key={request.idempotency_key}, "
                    f"transaction_id={existing.get('transaction_id')}"
                )
                # 返回之前的交易记录（从数据库查询完整对象）
                from sqlalchemy import select
                from app.models.point_transaction import PointTransaction
                result = await db.execute(
                    select(PointTransaction).where(
                        PointTransaction.id == existing['transaction_id']
                    )
                )
                previous_transaction = result.scalar_one_or_none()
                if previous_transaction:
                    return previous_transaction

        # 2. 获取操作锁（防止并发操作同一用户）
        lock = await IdempotencyService.acquire_operation_lock(
            user_id=request.user_id,
            operation="add_points",
            timeout=10,
            blocking_timeout=5
        )

        if not lock:
            raise HTTPException(
                status_code=409,
                detail="系统繁忙，请稍后重试（并发操作冲突）"
            )

        # 3. 执行积分添加
        transaction = await PointsService.add_user_points(
            db=db,
            user_id=request.user_id,
            points=request.amount,
            transaction_type=request.transaction_type,
            description=request.description,
            related_user_id=request.related_user_id,
            related_task_id=request.related_task_id,
            related_team_id=request.related_team_id,
            related_question_id=request.related_question_id,
            extra_metadata={
                "idempotency_key": request.idempotency_key
            } if request.idempotency_key else None
        )

        # 4. 存储幂等性记录
        if request.idempotency_key:
            await IdempotencyService.store_idempotency(
                idempotency_key=request.idempotency_key,
                transaction=transaction,
                ttl=86400  # 24小时
            )

        return transaction

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加积分失败: user_id={request.user_id}, error={e}")
        raise HTTPException(
            status_code=500,
            detail=f"添加积分失败: {str(e)}"
        )
    finally:
        # 5. 释放锁
        if lock:
            await IdempotencyService.release_operation_lock(lock)


@router.get("/balance/{wallet_address}", response_model=dict)
async def get_user_balance_by_wallet(
    wallet_address: str,
    db: AsyncSession = Depends(get_db)
):
    """
    通过钱包地址查询积分余额

    快速查询接口，仅返回可用积分余额
    """
    try:
        balance = await PointsService.get_user_balance(db, wallet_address)

        if balance is None:
            return {
                "wallet_address": wallet_address.lower(),
                "available_points": 0,
                "exists": False
            }

        return {
            "wallet_address": wallet_address.lower(),
            "available_points": balance,
            "exists": True
        }

    except Exception as e:
        logger.error(f"查询余额失败: wallet={wallet_address}, error={e}")
        raise HTTPException(
            status_code=500,
            detail=f"查询余额失败: {str(e)}"
        )


@router.post("/exchange", response_model=PointsExchangeResponse)
async def exchange_points(
    request: PointsExchangeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    积分兑换

    支持的兑换类型：
    - **token**: 积分兑换代币
    - **nft**: 积分兑换NFT
    - **privilege**: 积分兑换权益

    **幂等性保证**:
    - 如果提供 idempotency_key，系统会检查是否已处理过相同请求
    - 重复请求将返回之前的兑换记录，不会重复扣除积分

    **余额检查**:
    - 自动验证用户可用积分是否充足
    - 余额不足时返回400错误

    **注意**:
    - 此端点应受到权限保护，建议实施用户认证
    - 兑换金额为正整数，系统自动扣除积分
    """
    lock = None
    try:
        # 1. 幂等性检查
        if request.idempotency_key:
            existing = await IdempotencyService.check_idempotency(request.idempotency_key)
            if existing:
                logger.info(
                    f"🔁 幂等性拦截: 兑换请求已处理 "
                    f"idempotency_key={request.idempotency_key}, "
                    f"transaction_id={existing.get('transaction_id')}"
                )
                # 返回之前的兑换记录
                from sqlalchemy import select
                from app.models.point_transaction import PointTransaction
                result = await db.execute(
                    select(PointTransaction).where(
                        PointTransaction.id == existing['transaction_id']
                    )
                )
                previous_transaction = result.scalar_one_or_none()
                if previous_transaction:
                    return PointsExchangeResponse(
                        transaction_id=previous_transaction.id,
                        user_id=previous_transaction.user_id,
                        points_spent=abs(previous_transaction.amount),
                        exchange_type=request.exchange_type,
                        status=previous_transaction.status,
                        balance_after=previous_transaction.balance_after,
                        target_address=request.target_address,
                        created_at=previous_transaction.created_at
                    )

        # 2. 获取操作锁
        lock = await IdempotencyService.acquire_operation_lock(
            user_id=request.user_id,
            operation="exchange_points",
            timeout=10,
            blocking_timeout=5
        )

        if not lock:
            raise HTTPException(
                status_code=409,
                detail="系统繁忙，请稍后重试（并发操作冲突）"
            )

        # 3. 执行积分兑换
        transaction = await PointsService.exchange_points(
            db=db,
            user_id=request.user_id,
            points_amount=request.points_amount,
            exchange_type=request.exchange_type,
            target_address=request.target_address,
            idempotency_key=request.idempotency_key
        )

        # 4. 存储幂等性记录
        if request.idempotency_key:
            await IdempotencyService.store_idempotency(
                idempotency_key=request.idempotency_key,
                transaction=transaction,
                ttl=86400  # 24小时
            )

        # 5. 构建响应
        response = PointsExchangeResponse(
            transaction_id=transaction.id,
            user_id=transaction.user_id,
            points_spent=abs(transaction.amount),
            exchange_type=request.exchange_type,
            status=transaction.status,
            balance_after=transaction.balance_after,
            target_address=request.target_address,
            created_at=transaction.created_at
        )

        return response

    except ValueError as e:
        # 业务逻辑错误（如余额不足）
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"积分兑换失败: user_id={request.user_id}, error={e}")
        raise HTTPException(
            status_code=500,
            detail=f"积分兑换失败: {str(e)}"
        )
    finally:
        # 6. 释放锁
        if lock:
            await IdempotencyService.release_operation_lock(lock)


@router.get("/statistics", response_model=PointsStatistics)
async def get_points_statistics(
    db: AsyncSession = Depends(get_db)
):
    """
    获取积分系统全局统计数据

    返回以下统计信息：
    - **total_users**: 总用户数（拥有积分账户的用户）
    - **total_points_distributed**: 总发放积分（所有用户累计获得）
    - **total_points_spent**: 总消费积分（所有用户累计花费）
    - **referral_points**: 推荐奖励积分总和
    - **task_points**: 任务奖励积分总和
    - **quiz_points**: 答题奖励积分总和
    - **team_points**: 战队奖励积分总和

    **权限**: 公开访问（可添加管理员权限限制）

    **缓存策略**: 建议在高流量场景下添加Redis缓存，TTL 5分钟
    """
    try:
        statistics = await PointsService.get_points_statistics(db)
        return PointsStatistics(**statistics)

    except Exception as e:
        logger.error(f"获取积分统计失败: error={e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取积分统计失败: {str(e)}"
        )
