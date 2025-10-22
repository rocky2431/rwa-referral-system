"""
初始化任务配置

用途：创建"注册成功"和"邀请好友"任务配置
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.services.task_service import TaskService
from app.models.task import TaskType, TaskTrigger
from loguru import logger


async def init_tasks():
    """初始化任务配置"""
    async with AsyncSessionLocal() as db:
        try:
            # 1. 创建"注册成功"任务
            try:
                register_task = await TaskService.create_task(
                    db=db,
                    task_key="user_register",
                    title="注册成功",
                    description="完成账户注册，开启你的Web3之旅！",
                    task_type=TaskType.ONCE,
                    trigger_type=TaskTrigger.AUTO,
                    target_type="register",
                    target_value=1,
                    reward_points=100,
                    reward_experience=50,
                    min_level_required=1,
                    max_completions_per_user=1,
                    priority=10,
                    sort_order=1,
                    is_active=True,
                    is_visible=True
                )
                logger.info(f"✅ 注册任务创建成功: id={register_task.id}")
            except ValueError as e:
                logger.warning(f"⚠️ 注册任务已存在: {e}")

            # 2. 创建"邀请好友"任务 - 每邀请1人完成一次
            try:
                invite_task = await TaskService.create_task(
                    db=db,
                    task_key="invite_friends",
                    title="邀请好友",
                    description="分享你的邀请码，邀请新用户注册！每成功邀请1位好友获得100积分。",
                    task_type=TaskType.ONCE,  # 使用一次性任务，每次邀请都创建新的任务实例
                    trigger_type=TaskTrigger.AUTO,
                    target_type="invite_users",
                    target_value=1,
                    reward_points=100,
                    reward_experience=30,
                    min_level_required=1,
                    max_completions_per_user=None,  # 无限次
                    priority=9,
                    sort_order=2,
                    is_active=True,
                    is_visible=True
                )
                logger.info(f"✅ 邀请任务创建成功: id={invite_task.id}")
            except ValueError as e:
                logger.warning(f"⚠️ 邀请任务已存在: {e}")

            # 3. 创建"加入战队"任务
            try:
                join_team_task = await TaskService.create_task(
                    db=db,
                    task_key="join_team",
                    title="加入战队",
                    description="加入一个战队，与队友一起战斗！首次加入战队获得50积分。",
                    task_type=TaskType.ONCE,
                    trigger_type=TaskTrigger.AUTO,
                    target_type="join_team",
                    target_value=1,
                    reward_points=50,
                    reward_experience=20,
                    min_level_required=1,
                    max_completions_per_user=1,
                    priority=8,
                    sort_order=3,
                    is_active=True,
                    is_visible=True
                )
                logger.info(f"✅ 加入战队任务创建成功: id={join_team_task.id}")
            except ValueError as e:
                logger.warning(f"⚠️ 加入战队任务已存在: {e}")

            logger.info("🎉 任务初始化完成！")

        except Exception as e:
            logger.error(f"❌ 任务初始化失败: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(init_tasks())
