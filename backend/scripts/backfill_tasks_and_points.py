"""
补发历史用户的积分和任务

用途：
1. 为已注册用户补发"注册成功"任务和积分
2. 为已有推荐关系的用户补发"邀请好友"任务和积分
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal
from app.services.task_service import TaskService
from app.services.points_service import PointsService
from app.models.user import User
from app.models.referral_relation import ReferralRelation
from app.models.point_transaction import PointTransactionType
from app.models.task import UserTaskStatus, UserTask
from loguru import logger


async def backfill_register_tasks():
    """为所有已注册用户补发注册任务"""
    async with AsyncSessionLocal() as db:
        try:
            # 获取注册任务配置
            register_task = await TaskService.get_task_by_key(db, "user_register")
            if not register_task:
                logger.error("❌ 注册任务配置不存在，请先运行 init_tasks.py")
                return

            # 查询所有用户
            result = await db.execute(select(User))
            users = result.scalars().all()

            logger.info(f"📊 找到 {len(users)} 个用户")

            backfilled_count = 0
            for user in users:
                try:
                    # 检查用户是否已有该任务
                    existing_task = await TaskService.get_user_task(
                        db=db,
                        user_id=user.id,
                        task_id=register_task.id
                    )

                    if existing_task:
                        logger.info(f"⏭️  用户 {user.id} 已有注册任务，跳过")
                        continue

                    # 创建任务实例
                    user_task = await TaskService.assign_task_to_user(
                        db=db,
                        user_id=user.id,
                        task_id=register_task.id
                    )

                    # 完成任务
                    await TaskService.update_task_progress(
                        db=db,
                        user_task_id=user_task.id,
                        progress_delta=1
                    )

                    # 发放积分
                    await PointsService.add_user_points(
                        db=db,
                        user_id=user.id,
                        points=100,
                        transaction_type=PointTransactionType.REGISTER_REWARD,
                        description="注册成功奖励（补发）"
                    )

                    backfilled_count += 1
                    logger.info(f"✅ 补发注册任务: user_id={user.id}, user_task_id={user_task.id}")

                except Exception as e:
                    logger.warning(f"⚠️  用户 {user.id} 补发失败: {e}")
                    continue

            await db.commit()
            logger.info(f"🎉 注册任务补发完成！共补发 {backfilled_count} 个用户")

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 补发注册任务失败: {e}")
            raise


async def backfill_referral_tasks():
    """为已有推荐关系的用户补发邀请任务"""
    async with AsyncSessionLocal() as db:
        try:
            # 获取邀请任务配置
            invite_task = await TaskService.get_task_by_key(db, "invite_friends")
            if not invite_task:
                logger.error("❌ 邀请任务配置不存在，请先运行 init_tasks.py")
                return

            # 查询所有推荐关系，按推荐人分组计数
            result = await db.execute(
                select(
                    ReferralRelation.referrer_id,
                    func.count(ReferralRelation.id).label('invite_count')
                ).where(
                    ReferralRelation.is_active == True
                ).group_by(ReferralRelation.referrer_id)
            )
            referrer_stats = result.all()

            logger.info(f"📊 找到 {len(referrer_stats)} 个推荐人")

            backfilled_count = 0
            total_tasks = 0

            for stat in referrer_stats:
                referrer_id = stat.referrer_id
                invite_count = stat.invite_count

                logger.info(f"📝 处理推荐人 {referrer_id}，已邀请 {invite_count} 人")

                # 查询该推荐人已有的邀请任务数量
                existing_tasks_result = await db.execute(
                    select(func.count(UserTask.id)).where(
                        UserTask.user_id == referrer_id,
                        UserTask.task_id == invite_task.id
                    )
                )
                existing_count = existing_tasks_result.scalar_one() or 0

                # 需要补发的任务数 = 邀请人数 - 已有任务数
                tasks_to_create = invite_count - existing_count

                if tasks_to_create <= 0:
                    logger.info(f"⏭️  推荐人 {referrer_id} 任务已齐全，跳过")
                    continue

                # 补发任务
                for i in range(tasks_to_create):
                    try:
                        # 创建任务实例
                        user_task = await TaskService.assign_task_to_user(
                            db=db,
                            user_id=referrer_id,
                            task_id=invite_task.id
                        )

                        # 完成任务
                        await TaskService.update_task_progress(
                            db=db,
                            user_task_id=user_task.id,
                            progress_delta=1
                        )

                        # 发放积分
                        await PointsService.add_user_points(
                            db=db,
                            user_id=referrer_id,
                            points=100,
                            transaction_type=PointTransactionType.REFERRAL_REWARD,
                            description=f"邀请好友奖励（补发 {i+1}/{tasks_to_create}）"
                        )

                        total_tasks += 1
                        logger.info(f"✅ 补发邀请任务 {i+1}/{tasks_to_create}: user_id={referrer_id}")

                    except Exception as e:
                        logger.warning(f"⚠️  推荐人 {referrer_id} 第 {i+1} 个任务补发失败: {e}")
                        continue

                backfilled_count += 1

            await db.commit()
            logger.info(f"🎉 邀请任务补发完成！共为 {backfilled_count} 个推荐人补发 {total_tasks} 个任务")

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 补发邀请任务失败: {e}")
            raise


async def main():
    """主函数"""
    logger.info("🚀 开始补发历史用户积分和任务...")

    # 1. 补发注册任务
    logger.info("\n" + "="*50)
    logger.info("第1步：补发注册任务")
    logger.info("="*50)
    await backfill_register_tasks()

    # 2. 补发邀请任务
    logger.info("\n" + "="*50)
    logger.info("第2步：补发邀请任务")
    logger.info("="*50)
    await backfill_referral_tasks()

    logger.info("\n" + "="*50)
    logger.info("✨ 所有补发任务完成！")
    logger.info("="*50)


if __name__ == "__main__":
    asyncio.run(main())
