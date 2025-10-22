"""
推荐系统API端点
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
import secrets
import string

from app.db.session import get_db
from app.models import User, UserPoints, ReferralRelation
from app.core.config import settings

router = APIRouter()


class ReferralLinkRequest(BaseModel):
    """生成推荐链接请求"""
    address: str = Field(..., description="用户钱包地址")


class ReferralLinkResponse(BaseModel):
    """推荐链接响应"""
    referral_link: str
    invite_code: str
    referrer_address: str


class UserInfoResponse(BaseModel):
    """用户信息响应"""
    address: str
    referrer: str
    reward: int
    referred_count: int
    last_active_timestamp: int
    has_referrer: bool
    is_active: bool


@router.post("/generate-link", response_model=ReferralLinkResponse)
async def generate_referral_link(request: ReferralLinkRequest, db: AsyncSession = Depends(get_db)):
    """
    生成推荐链接

    生成用户专属的推荐链接和邀请码
    """
    # 查询用户是否存在
    user_query = select(User).where(User.wallet_address == request.address.lower())
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()

    if user:
        # 使用用户ID生成邀请码
        code = f"USER{user.id:06d}"
    else:
        # 生成6位随机邀请码
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

    # 生成推荐链接
    app_url = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "http://localhost:5173"
    link = f"{app_url}?ref={code}"

    return {
        "referral_link": link,
        "invite_code": code,
        "referrer_address": request.address
    }


@router.get("/user/{address}", response_model=UserInfoResponse)
async def get_user_info(address: str, db: AsyncSession = Depends(get_db)):
    """
    获取用户推荐信息（基于数据库）

    查询用户的推荐关系、奖励、推荐人数等信息
    """
    try:
        # 查询用户
        user_query = select(User).where(User.wallet_address == address.lower())
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            # 用户不存在，返回默认值
            return {
                "address": address.lower(),
                "referrer": "0x0000000000000000000000000000000000000000",
                "reward": 0,
                "referred_count": 0,
                "last_active_timestamp": 0,
                "has_referrer": False,
                "is_active": False
            }

        # 查询推荐人
        referrer_query = select(ReferralRelation).where(
            ReferralRelation.referee_id == user.id,
            ReferralRelation.is_active == True
        )
        referrer_result = await db.execute(referrer_query)
        referrer_relation = referrer_result.scalar_one_or_none()

        referrer_address = "0x0000000000000000000000000000000000000000"
        if referrer_relation:
            referrer_user_query = select(User).where(User.id == referrer_relation.referrer_id)
            referrer_user_result = await db.execute(referrer_user_query)
            referrer_user = referrer_user_result.scalar_one_or_none()
            if referrer_user:
                referrer_address = referrer_user.wallet_address

        # 查询推荐人数
        referred_count_query = select(func.count(ReferralRelation.id)).where(
            ReferralRelation.referrer_id == user.id,
            ReferralRelation.is_active == True
        )
        referred_count_result = await db.execute(referred_count_query)
        referred_count = referred_count_result.scalar() or 0

        # 查询积分奖励
        points_query = select(UserPoints).where(UserPoints.user_id == user.id)
        points_result = await db.execute(points_query)
        points = points_result.scalar_one_or_none()
        total_reward = points.points_from_referral if points else 0

        # 计算活跃状态
        last_active_timestamp = int(user.last_active_at.timestamp()) if user.last_active_at else 0
        is_active = False
        if user.last_active_at:
            days_ago = (datetime.utcnow() - user.last_active_at).days
            is_active = days_ago < settings.INACTIVE_DAYS

        return {
            "address": address.lower(),
            "referrer": referrer_address,
            "reward": total_reward,
            "referred_count": int(referred_count),
            "last_active_timestamp": last_active_timestamp,
            "has_referrer": referrer_address != "0x0000000000000000000000000000000000000000",
            "is_active": is_active
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户信息失败: {str(e)}")


@router.get("/config")
async def get_referral_config():
    """
    获取推荐系统配置（基于环境变量）

    返回推荐奖励比例、活跃时间等配置信息
    """
    try:
        # 从环境变量读取配置
        level1_rate = settings.LEVEL_1_BONUS_RATE  # 15%
        level2_rate = settings.LEVEL_2_BONUS_RATE  # 5%
        inactive_days = settings.INACTIVE_DAYS  # 30天
        total_bonus_rate = level1_rate + level2_rate  # 20%

        return {
            "decimals": 18,  # BNB标准精度
            "referral_bonus": f"{total_bonus_rate}%",
            "seconds_until_inactive": inactive_days * 86400,
            "inactive_days": inactive_days,
            "level1_bonus": f"{level1_rate}%",
            "level2_bonus": f"{level2_rate}%",
            "level_1_bonus_rate": level1_rate * 100,  # 1500 (15%)
            "level_2_bonus_rate": level2_rate * 100,  # 500 (5%)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


class BindReferrerRequest(BaseModel):
    """绑定推荐人请求"""
    referee_address: str = Field(..., description="被推荐人钱包地址")
    referrer_address: str = Field(..., description="推荐人钱包地址")


class BindReferrerResponse(BaseModel):
    """绑定推荐人响应"""
    success: bool
    message: str
    referee_address: str
    referrer_address: str


@router.get("/resolve-code/{invite_code}")
async def resolve_invite_code(invite_code: str, db: AsyncSession = Depends(get_db)):
    """
    通过邀请码查找推荐人地址

    将邀请码（如USER000001）解析为推荐人的钱包地址
    """
    try:
        # 尝试从邀请码提取用户ID（格式：USER000001）
        if invite_code.startswith("USER") and len(invite_code) == 10:
            try:
                user_id = int(invite_code[4:])

                # 查询用户
                user_query = select(User).where(User.id == user_id)
                user_result = await db.execute(user_query)
                user = user_result.scalar_one_or_none()

                if user:
                    return {
                        "success": True,
                        "invite_code": invite_code,
                        "referrer_address": user.wallet_address,
                        "referrer_username": user.username
                    }
            except ValueError:
                pass

        # 如果不是标准格式，返回未找到
        raise HTTPException(status_code=404, detail="邀请码无效或推荐人不存在")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析邀请码失败: {str(e)}")


class BindReferrerByCodeRequest(BaseModel):
    """通过邀请码绑定推荐人请求"""
    referee_address: str = Field(..., description="被推荐人钱包地址")
    invite_code: str = Field(..., description="邀请码")


@router.post("/bind-referrer-by-code", response_model=BindReferrerResponse)
async def bind_referrer_by_code(request: BindReferrerByCodeRequest, db: AsyncSession = Depends(get_db)):
    """
    通过邀请码绑定推荐关系

    使用邀请码而非钱包地址绑定推荐关系，用户体验更好
    """
    try:
        # 1. 解析邀请码获取推荐人地址
        if request.invite_code.startswith("USER") and len(request.invite_code) == 10:
            try:
                referrer_user_id = int(request.invite_code[4:])

                # 查询推荐人
                referrer_query = select(User).where(User.id == referrer_user_id)
                referrer_result = await db.execute(referrer_query)
                referrer = referrer_result.scalar_one_or_none()

                if not referrer:
                    raise HTTPException(status_code=404, detail="邀请码无效：推荐人不存在")

                referrer_address = referrer.wallet_address
            except ValueError:
                raise HTTPException(status_code=400, detail="邀请码格式无效")
        else:
            raise HTTPException(status_code=400, detail="邀请码格式无效")

        # 2. 调用原有的绑定逻辑
        referee_address = request.referee_address.lower()

        # 验证地址格式
        if not referee_address.startswith('0x') or len(referee_address) != 42:
            raise HTTPException(status_code=400, detail="被推荐人地址格式无效")

        # 不能推荐自己
        if referee_address == referrer_address:
            raise HTTPException(status_code=400, detail="不能使用自己的邀请码")

        # 查询被推荐人
        referee_query = select(User).where(User.wallet_address == referee_address)
        referee_result = await db.execute(referee_query)
        referee = referee_result.scalar_one_or_none()

        if not referee:
            raise HTTPException(status_code=404, detail="被推荐人未注册，请先注册")

        # 检查是否已经绑定过推荐人
        existing_relation_query = select(ReferralRelation).where(
            ReferralRelation.referee_id == referee.id,
            ReferralRelation.is_active == True
        )
        existing_relation_result = await db.execute(existing_relation_query)
        existing_relation = existing_relation_result.scalar_one_or_none()

        if existing_relation:
            raise HTTPException(status_code=400, detail="已经绑定过推荐人，每个用户只能绑定一次")

        # 检查循环推荐
        async def check_circular_referral(current_user_id: int, target_user_id: int, depth: int = 0) -> bool:
            if depth > 10:
                return False

            query = select(ReferralRelation).where(
                ReferralRelation.referee_id == current_user_id,
                ReferralRelation.is_active == True
            )
            result = await db.execute(query)
            relations = result.scalars().all()

            for relation in relations:
                if relation.referrer_id == target_user_id:
                    return True
                if await check_circular_referral(relation.referrer_id, target_user_id, depth + 1):
                    return True

            return False

        if await check_circular_referral(referrer.id, referee.id):
            raise HTTPException(status_code=400, detail="无法绑定：会形成循环推荐")

        # 创建推荐关系
        new_relation = ReferralRelation(
            referrer_id=referrer.id,
            referee_id=referee.id,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(new_relation)

        # 更新用户的推荐人数
        referrer.total_invited += 1

        await db.commit()

        return {
            "success": True,
            "message": "推荐关系绑定成功",
            "referee_address": referee_address,
            "referrer_address": referrer_address
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"绑定推荐关系失败: {str(e)}")


@router.get("/leaderboard")
async def get_referral_leaderboard(
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    获取推荐排行榜

    基于用户的推荐奖励和推荐人数排序
    """
    try:
        # 计算偏移量
        offset = (page - 1) * page_size

        # 测试账号地址模式（排除这些明显的测试数据）
        test_address_patterns = [
            '0x0123456789abcdef0123456789abcdef01234567',
            '0x123456789abcdef0123456789abcdef012345678',
            '0x23456789abcdef0123456789abcdef0123456789',
            '0x3456789abcdef0123456789abcdef0123456789a',
            '0x456789abcdef0123456789abcdef0123456789ab',
            '0x56789abcdef0123456789abcdef0123456789abc',
            '0x6789abcdef0123456789abcdef0123456789abcd',
            '0x789abcdef0123456789abcdef0123456789abcde',
            '0x89abcdef0123456789abcdef0123456789abcdef',
            '0x9abcdef0123456789abcdef0123456789abcdef0',
            '0x1111111111111111111111111111111111111111'
        ]

        # 查询总数（排除测试账号）
        total_query = select(func.count(User.id)).where(
            User.is_active == True,
            User.wallet_address.notin_(test_address_patterns)
        )
        total_result = await db.execute(total_query)
        total = total_result.scalar() or 0

        # 查询排行榜数据（排除测试账号）
        query = select(
            User.wallet_address,
            User.total_invited,
            UserPoints.total_earned  # 改为总积分
        ).join(
            UserPoints, User.id == UserPoints.user_id, isouter=True
        ).where(
            User.is_active == True,
            User.wallet_address.notin_(test_address_patterns)
        ).order_by(
            func.coalesce(UserPoints.total_earned, 0).desc(),  # 按总积分排序
            User.total_invited.desc()
        ).offset(offset).limit(page_size)

        result = await db.execute(query)
        rows = result.all()

        # 构建排行榜数据
        data = []
        for rank, row in enumerate(rows, start=offset + 1):
            # 使用总积分
            total_rewards = row.total_earned or 0

            data.append({
                "rank": rank,
                "address": row.wallet_address,
                "total_rewards": str(total_rewards),
                "referred_count": row.total_invited or 0
            })

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取推荐排行榜失败: {str(e)}")


@router.post("/bind-referrer", response_model=BindReferrerResponse)
async def bind_referrer(request: BindReferrerRequest, db: AsyncSession = Depends(get_db)):
    """
    绑定推荐关系

    将被推荐人与推荐人建立推荐关系
    """
    try:
        referee_address = request.referee_address.lower()
        referrer_address = request.referrer_address.lower()

        # 1. 验证地址格式
        if not referee_address.startswith('0x') or len(referee_address) != 42:
            raise HTTPException(status_code=400, detail="被推荐人地址格式无效")
        if not referrer_address.startswith('0x') or len(referrer_address) != 42:
            raise HTTPException(status_code=400, detail="推荐人地址格式无效")

        # 2. 不能推荐自己
        if referee_address == referrer_address:
            raise HTTPException(status_code=400, detail="不能推荐自己")

        # 3. 不能是零地址
        zero_address = "0x0000000000000000000000000000000000000000"
        if referrer_address == zero_address:
            raise HTTPException(status_code=400, detail="推荐人地址无效")

        # 4. 查询或创建被推荐人
        referee_query = select(User).where(User.wallet_address == referee_address)
        referee_result = await db.execute(referee_query)
        referee = referee_result.scalar_one_or_none()

        if not referee:
            raise HTTPException(status_code=404, detail="被推荐人未注册，请先注册")

        # 5. 检查是否已经绑定过推荐人
        existing_relation_query = select(ReferralRelation).where(
            ReferralRelation.referee_id == referee.id,
            ReferralRelation.is_active == True
        )
        existing_relation_result = await db.execute(existing_relation_query)
        existing_relation = existing_relation_result.scalar_one_or_none()

        if existing_relation:
            raise HTTPException(status_code=400, detail="已经绑定过推荐人，每个用户只能绑定一次")

        # 6. 查询或创建推荐人
        referrer_query = select(User).where(User.wallet_address == referrer_address)
        referrer_result = await db.execute(referrer_query)
        referrer = referrer_result.scalar_one_or_none()

        if not referrer:
            raise HTTPException(status_code=404, detail="推荐人不存在")

        # 7. 检查循环推荐：推荐人不能是被推荐人的下级
        async def check_circular_referral(current_user_id: int, target_user_id: int, depth: int = 0) -> bool:
            """递归检查是否形成循环推荐"""
            if depth > 10:  # 防止无限递归
                return False

            # 查询当前用户的所有推荐人
            query = select(ReferralRelation).where(
                ReferralRelation.referee_id == current_user_id,
                ReferralRelation.is_active == True
            )
            result = await db.execute(query)
            relations = result.scalars().all()

            for relation in relations:
                if relation.referrer_id == target_user_id:
                    return True  # 发现循环
                # 递归检查推荐人的推荐人
                if await check_circular_referral(relation.referrer_id, target_user_id, depth + 1):
                    return True

            return False

        if await check_circular_referral(referrer.id, referee.id):
            raise HTTPException(status_code=400, detail="无法绑定：会形成循环推荐")

        # 8. 创建推荐关系
        new_relation = ReferralRelation(
            referrer_id=referrer.id,
            referee_id=referee.id,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(new_relation)

        # 9. 更新用户的推荐人数
        referrer.total_invited += 1

        await db.commit()

        return {
            "success": True,
            "message": "推荐关系绑定成功",
            "referee_address": referee_address,
            "referrer_address": referrer_address
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"绑定推荐关系失败: {str(e)}")
