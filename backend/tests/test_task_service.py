"""
TaskService单元测试
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.task_service import TaskService
from app.services.points_service import PointsService
from app.models import Task, UserTask, User
from app.models.task import TaskType, TaskTrigger, UserTaskStatus


class TestTaskService:
    """TaskService测试类"""

    @pytest.mark.asyncio
    async def test_create_task(self, db_session: AsyncSession):
        """测试创建任务配置"""
        task = await TaskService.create_task(
            db=db_session,
            task_key="test_daily_login",
            title="每日登录",
            task_type=TaskType.DAILY,
            reward_points=100,
            description="每日登录获得奖励",
            target_value=1,
            trigger_type=TaskTrigger.AUTO
        )
        await db_session.commit()

        # 验证任务
        assert task.id is not None
        assert task.task_key == "test_daily_login"
        assert task.title == "每日登录"
        assert task.task_type == TaskType.DAILY
        assert task.reward_points == 100
        assert task.trigger_type == TaskTrigger.AUTO
        assert task.is_active is True

    @pytest.mark.asyncio
    async def test_create_task_duplicate_key(self, db_session: AsyncSession):
        """测试创建重复task_key的任务"""
        # 创建第一个任务
        await TaskService.create_task(
            db=db_session,
            task_key="duplicate_key",
            title="任务1",
            task_type=TaskType.ONCE,
            reward_points=100
        )
        await db_session.commit()

        # 尝试创建重复key的任务（应该失败）
        with pytest.raises(ValueError, match="already exists"):
            await TaskService.create_task(
                db=db_session,
                task_key="duplicate_key",
                title="任务2",
                task_type=TaskType.ONCE,
                reward_points=200
            )

    @pytest.mark.asyncio
    async def test_get_tasks_filter_by_type(self, db_session: AsyncSession):
        """测试按类型筛选任务列表"""
        # 创建不同类型的任务
        await TaskService.create_task(
            db=db_session,
            task_key="daily_1",
            title="每日任务1",
            task_type=TaskType.DAILY,
            reward_points=100
        )
        await TaskService.create_task(
            db=db_session,
            task_key="weekly_1",
            title="每周任务1",
            task_type=TaskType.WEEKLY,
            reward_points=500
        )
        await db_session.commit()

        # 筛选每日任务
        daily_tasks, total = await TaskService.get_tasks(
            db=db_session,
            task_type=TaskType.DAILY
        )
        assert total >= 1
        assert all(task.task_type == TaskType.DAILY for task in daily_tasks)

    @pytest.mark.asyncio
    async def test_update_task(self, db_session: AsyncSession):
        """测试更新任务配置"""
        # 创建任务
        task = await TaskService.create_task(
            db=db_session,
            task_key="update_test",
            title="原始标题",
            task_type=TaskType.ONCE,
            reward_points=100
        )
        await db_session.commit()

        # 更新任务
        updated_task = await TaskService.update_task(
            db=db_session,
            task_id=task.id,
            title="更新后标题",
            reward_points=200,
            description="更新后的描述"
        )
        await db_session.commit()

        # 验证更新
        assert updated_task.title == "更新后标题"
        assert updated_task.reward_points == 200
        assert updated_task.description == "更新后的描述"

    @pytest.mark.asyncio
    async def test_delete_task(self, db_session: AsyncSession):
        """测试删除任务（软删除）"""
        # 创建任务
        task = await TaskService.create_task(
            db=db_session,
            task_key="delete_test",
            title="待删除任务",
            task_type=TaskType.ONCE,
            reward_points=100
        )
        await db_session.commit()

        # 删除任务
        result = await TaskService.delete_task(db=db_session, task_id=task.id)
        await db_session.commit()

        assert result is True

        # 验证任务状态
        from sqlalchemy import select
        task_result = await db_session.execute(select(Task).where(Task.id == task.id))
        deleted_task = task_result.scalar_one()
        assert deleted_task.is_active is False
        assert deleted_task.is_visible is False

    @pytest.mark.asyncio
    async def test_assign_task_to_user(self, db_session: AsyncSession):
        """测试用户领取任务"""
        # 创建用户
        user = await PointsService.get_or_create_user(
            db_session,
            "0xtask_user_1234567890abcdef1234567890"
        )
        await db_session.commit()

        # 创建任务
        task = await TaskService.create_task(
            db=db_session,
            task_key="invite_friends",
            title="邀请好友",
            task_type=TaskType.ONCE,
            reward_points=500,
            target_value=5,
            trigger_type=TaskTrigger.MANUAL
        )
        await db_session.commit()

        # 用户领取任务
        user_task = await TaskService.assign_task_to_user(
            db=db_session,
            user_id=user.id,
            task_id=task.id
        )
        await db_session.commit()

        # 验证用户任务
        assert user_task.id is not None
        assert user_task.user_id == user.id
        assert user_task.task_id == task.id
        assert user_task.status == UserTaskStatus.IN_PROGRESS
        assert user_task.current_value == 0
        assert user_task.target_value == 5
        assert user_task.reward_points == 500

    @pytest.mark.asyncio
    async def test_assign_task_duplicate(self, db_session: AsyncSession):
        """测试重复领取任务"""
        # 创建用户和任务
        user = await PointsService.get_or_create_user(db_session, "0xuser_dup")
        await db_session.commit()

        task = await TaskService.create_task(
            db=db_session,
            task_key="dup_task",
            title="测试任务",
            task_type=TaskType.ONCE,
            reward_points=100
        )
        await db_session.commit()

        # 第一次领取
        await TaskService.assign_task_to_user(
            db=db_session,
            user_id=user.id,
            task_id=task.id
        )
        await db_session.commit()

        # 第二次领取（应该失败）
        with pytest.raises(ValueError, match="already has this task"):
            await TaskService.assign_task_to_user(
                db=db_session,
                user_id=user.id,
                task_id=task.id
            )

    @pytest.mark.asyncio
    async def test_update_task_progress(self, db_session: AsyncSession):
        """测试更新任务进度"""
        # 创建用户和任务
        user = await PointsService.get_or_create_user(db_session, "0xuser_progress")
        await db_session.commit()

        task = await TaskService.create_task(
            db=db_session,
            task_key="progress_task",
            title="进度任务",
            task_type=TaskType.ONCE,
            reward_points=1000,
            target_value=10
        )
        await db_session.commit()

        # 领取任务
        user_task = await TaskService.assign_task_to_user(
            db=db_session,
            user_id=user.id,
            task_id=task.id
        )
        await db_session.commit()

        # 更新进度
        updated_task = await TaskService.update_task_progress(
            db=db_session,
            user_task_id=user_task.id,
            progress_delta=3
        )
        await db_session.commit()

        # 验证进度
        assert updated_task.current_value == 3
        assert updated_task.status == UserTaskStatus.IN_PROGRESS
        assert updated_task.progress_percentage == 30.0

    @pytest.mark.asyncio
    async def test_task_auto_complete(self, db_session: AsyncSession):
        """测试任务自动完成"""
        # 创建用户和任务
        user = await PointsService.get_or_create_user(db_session, "0xuser_complete")
        await db_session.commit()

        task = await TaskService.create_task(
            db=db_session,
            task_key="complete_task",
            title="完成任务",
            task_type=TaskType.ONCE,
            reward_points=500,
            target_value=5
        )
        await db_session.commit()

        # 领取任务
        user_task = await TaskService.assign_task_to_user(
            db=db_session,
            user_id=user.id,
            task_id=task.id
        )
        await db_session.commit()

        # 更新进度至完成
        completed_task = await TaskService.update_task_progress(
            db=db_session,
            user_task_id=user_task.id,
            progress_delta=5
        )
        await db_session.commit()

        # 验证完成状态
        assert completed_task.current_value == 5
        assert completed_task.status == UserTaskStatus.COMPLETED
        assert completed_task.is_completed is True
        assert completed_task.completed_at is not None
        assert completed_task.progress_percentage == 100.0

    @pytest.mark.asyncio
    async def test_claim_task_reward(self, db_session: AsyncSession):
        """测试领取任务奖励"""
        # 创建用户和任务
        user = await PointsService.get_or_create_user(db_session, "0xuser_claim")
        await db_session.commit()

        task = await TaskService.create_task(
            db=db_session,
            task_key="claim_task",
            title="领取奖励任务",
            task_type=TaskType.ONCE,
            reward_points=1000,
            reward_experience=50,
            target_value=3
        )
        await db_session.commit()

        # 领取并完成任务
        user_task = await TaskService.assign_task_to_user(
            db=db_session,
            user_id=user.id,
            task_id=task.id
        )
        await TaskService.update_task_progress(
            db=db_session,
            user_task_id=user_task.id,
            progress_delta=3
        )
        await db_session.commit()

        # 获取用户当前积分
        from sqlalchemy import select
        user_points_result = await db_session.execute(
            select(User).where(User.id == user.id)
        )
        user_before = user_points_result.scalar_one()
        initial_experience = user_before.experience

        # 领取奖励
        reward_result = await TaskService.claim_task_reward(
            db=db_session,
            user_task_id=user_task.id
        )
        await db_session.commit()

        # 验证奖励发放
        assert reward_result["points_reward"] == 1000
        assert reward_result["experience_reward"] == 50

        # 验证用户任务状态
        from app.models import UserPoints
        user_points = await db_session.execute(
            select(UserPoints).where(UserPoints.user_id == user.id)
        )
        updated_points = user_points.scalar_one()
        assert updated_points.available_points >= 1000

        # 验证用户经验增加
        user_after_result = await db_session.execute(
            select(User).where(User.id == user.id)
        )
        user_after = user_after_result.scalar_one()
        assert user_after.experience == initial_experience + 50

    @pytest.mark.asyncio
    async def test_claim_reward_not_completed(self, db_session: AsyncSession):
        """测试未完成任务不能领取奖励"""
        # 创建用户和任务
        user = await PointsService.get_or_create_user(db_session, "0xuser_not_complete")
        await db_session.commit()

        task = await TaskService.create_task(
            db=db_session,
            task_key="not_complete_task",
            title="未完成任务",
            task_type=TaskType.ONCE,
            reward_points=500,
            target_value=10
        )
        await db_session.commit()

        # 领取任务但未完成
        user_task = await TaskService.assign_task_to_user(
            db=db_session,
            user_id=user.id,
            task_id=task.id
        )
        await TaskService.update_task_progress(
            db=db_session,
            user_task_id=user_task.id,
            progress_delta=5  # 只完成一半
        )
        await db_session.commit()

        # 尝试领取奖励（应该失败）
        with pytest.raises(ValueError, match="not completed"):
            await TaskService.claim_task_reward(
                db=db_session,
                user_task_id=user_task.id
            )

    @pytest.mark.asyncio
    async def test_claim_reward_already_claimed(self, db_session: AsyncSession):
        """测试重复领取奖励"""
        # 创建用户和任务
        user = await PointsService.get_or_create_user(db_session, "0xuser_reclaim")
        await db_session.commit()

        task = await TaskService.create_task(
            db=db_session,
            task_key="reclaim_task",
            title="重复领取测试",
            task_type=TaskType.ONCE,
            reward_points=500,
            target_value=1
        )
        await db_session.commit()

        # 完成任务
        user_task = await TaskService.assign_task_to_user(
            db=db_session,
            user_id=user.id,
            task_id=task.id
        )
        await TaskService.update_task_progress(
            db=db_session,
            user_task_id=user_task.id,
            progress_delta=1
        )
        await db_session.commit()

        # 第一次领取
        await TaskService.claim_task_reward(
            db=db_session,
            user_task_id=user_task.id
        )
        await db_session.commit()

        # 第二次领取（应该失败）
        with pytest.raises(ValueError, match="already claimed"):
            await TaskService.claim_task_reward(
                db=db_session,
                user_task_id=user_task.id
            )

    @pytest.mark.asyncio
    async def test_get_user_tasks(self, db_session: AsyncSession):
        """测试获取用户任务列表"""
        # 创建用户
        user = await PointsService.get_or_create_user(db_session, "0xuser_tasklist")
        await db_session.commit()

        # 创建多个任务并让用户领取
        for i in range(3):
            task = await TaskService.create_task(
                db=db_session,
                task_key=f"user_task_{i}",
                title=f"用户任务{i}",
                task_type=TaskType.DAILY if i % 2 == 0 else TaskType.WEEKLY,
                reward_points=100 * (i + 1)
            )
            await TaskService.assign_task_to_user(
                db=db_session,
                user_id=user.id,
                task_id=task.id
            )
        await db_session.commit()

        # 获取用户任务列表
        user_tasks, total = await TaskService.get_user_tasks(
            db=db_session,
            user_id=user.id
        )

        # 验证
        assert total >= 3
        assert len(user_tasks) >= 3
        assert all(ut.user_id == user.id for ut in user_tasks)

    @pytest.mark.asyncio
    async def test_get_user_tasks_filter_by_status(self, db_session: AsyncSession):
        """测试按状态筛选用户任务"""
        # 创建用户
        user = await PointsService.get_or_create_user(db_session, "0xuser_filter")
        await db_session.commit()

        # 创建任务
        task1 = await TaskService.create_task(
            db=db_session,
            task_key="filter_task_1",
            title="进行中任务",
            task_type=TaskType.ONCE,
            reward_points=100,
            target_value=10
        )
        task2 = await TaskService.create_task(
            db=db_session,
            task_key="filter_task_2",
            title="已完成任务",
            task_type=TaskType.ONCE,
            reward_points=200,
            target_value=5
        )
        await db_session.commit()

        # 领取任务
        user_task1 = await TaskService.assign_task_to_user(
            db=db_session,
            user_id=user.id,
            task_id=task1.id
        )
        user_task2 = await TaskService.assign_task_to_user(
            db=db_session,
            user_id=user.id,
            task_id=task2.id
        )
        await db_session.commit()

        # 完成第二个任务
        await TaskService.update_task_progress(
            db=db_session,
            user_task_id=user_task2.id,
            progress_delta=5
        )
        await db_session.commit()

        # 筛选已完成任务
        completed_tasks, total = await TaskService.get_user_tasks(
            db=db_session,
            user_id=user.id,
            status=UserTaskStatus.COMPLETED
        )

        assert total >= 1
        assert all(ut.status == UserTaskStatus.COMPLETED for ut in completed_tasks)

    @pytest.mark.asyncio
    async def test_get_task_statistics(self, db_session: AsyncSession):
        """测试获取任务统计"""
        # 创建任务
        task = await TaskService.create_task(
            db=db_session,
            task_key="stats_task",
            title="统计任务",
            task_type=TaskType.ONCE,
            reward_points=500,
            target_value=5
        )
        await db_session.commit()

        # 创建用户并完成任务
        for i in range(3):
            user = await PointsService.get_or_create_user(db_session, f"0xstats_user_{i}")
            await db_session.commit()

            user_task = await TaskService.assign_task_to_user(
                db=db_session,
                user_id=user.id,
                task_id=task.id
            )
            await TaskService.update_task_progress(
                db=db_session,
                user_task_id=user_task.id,
                progress_delta=5
            )
        await db_session.commit()

        # 获取统计信息
        stats = await TaskService.get_task_statistics(db=db_session, task_id=task.id)

        # 验证
        assert stats["task_id"] == task.id
        assert stats["total_participants"] >= 3
        assert stats["total_completed"] >= 3
        assert stats["completion_rate"] == 100.0

    @pytest.mark.asyncio
    async def test_get_user_task_summary(self, db_session: AsyncSession):
        """测试获取用户任务汇总"""
        # 创建用户
        user = await PointsService.get_or_create_user(db_session, "0xuser_summary")
        await db_session.commit()

        # 创建并完成任务
        task1 = await TaskService.create_task(
            db=db_session,
            task_key="summary_task_1",
            title="任务1",
            task_type=TaskType.ONCE,
            reward_points=100,
            target_value=5
        )
        task2 = await TaskService.create_task(
            db=db_session,
            task_key="summary_task_2",
            title="任务2",
            task_type=TaskType.ONCE,
            reward_points=200,
            target_value=10
        )
        await db_session.commit()

        # 领取任务
        user_task1 = await TaskService.assign_task_to_user(
            db=db_session,
            user_id=user.id,
            task_id=task1.id
        )
        user_task2 = await TaskService.assign_task_to_user(
            db=db_session,
            user_id=user.id,
            task_id=task2.id
        )
        await db_session.commit()

        # 完成第一个任务并领取奖励
        await TaskService.update_task_progress(
            db=db_session,
            user_task_id=user_task1.id,
            progress_delta=5
        )
        await TaskService.claim_task_reward(
            db=db_session,
            user_task_id=user_task1.id
        )
        await db_session.commit()

        # 获取汇总
        summary = await TaskService.get_user_task_summary(db=db_session, user_id=user.id)

        # 验证
        assert summary["user_id"] == user.id
        assert summary["total_tasks"] >= 2
        assert summary["claimed_tasks"] >= 1
        assert summary["in_progress_tasks"] >= 1
        assert summary["total_points_earned"] >= 100

    @pytest.mark.asyncio
    async def test_auto_assign_tasks(self, db_session: AsyncSession):
        """测试自动分配任务"""
        # 创建用户
        user = await PointsService.get_or_create_user(db_session, "0xuser_auto")
        await db_session.commit()

        # 创建AUTO触发类型的任务
        await TaskService.create_task(
            db=db_session,
            task_key="auto_task_1",
            title="自动任务1",
            task_type=TaskType.DAILY,
            reward_points=50,
            trigger_type=TaskTrigger.AUTO
        )
        await TaskService.create_task(
            db=db_session,
            task_key="auto_task_2",
            title="自动任务2",
            task_type=TaskType.WEEKLY,
            reward_points=100,
            trigger_type=TaskTrigger.AUTO
        )
        await db_session.commit()

        # 自动分配任务
        assigned_tasks = await TaskService.auto_assign_tasks(
            db=db_session,
            user_id=user.id
        )

        # 验证
        assert len(assigned_tasks) >= 2
        assert all(ut.user_id == user.id for ut in assigned_tasks)
        assert all(ut.status == UserTaskStatus.IN_PROGRESS for ut in assigned_tasks)

    @pytest.mark.asyncio
    async def test_task_expiration(self, db_session: AsyncSession):
        """测试任务过期"""
        from datetime import datetime, timedelta

        # 创建用户
        user = await PointsService.get_or_create_user(db_session, "0xuser_expire")
        await db_session.commit()

        # 创建有时间限制的任务
        now = datetime.utcnow()
        task = await TaskService.create_task(
            db=db_session,
            task_key="expire_task",
            title="过期任务",
            task_type=TaskType.ONCE,
            reward_points=500,
            target_value=10,
            start_time=now - timedelta(days=1),
            end_time=now + timedelta(hours=1)  # 1小时后过期
        )
        await db_session.commit()

        # 领取任务
        user_task = await TaskService.assign_task_to_user(
            db=db_session,
            user_id=user.id,
            task_id=task.id
        )
        await db_session.commit()

        # 验证过期时间已设置
        assert user_task.expires_at is not None
        assert user_task.expires_at <= now + timedelta(hours=2)

    @pytest.mark.asyncio
    async def test_task_level_requirement(self, db_session: AsyncSession):
        """测试任务等级限制"""
        # 创建低等级用户
        user = await PointsService.get_or_create_user(db_session, "0xuser_lowlevel")
        await db_session.commit()

        # 创建高等级要求的任务
        task = await TaskService.create_task(
            db=db_session,
            task_key="highlevel_task",
            title="高等级任务",
            task_type=TaskType.ONCE,
            reward_points=1000,
            min_level_required=10  # 需要10级
        )
        await db_session.commit()

        # 尝试领取（应该失败）
        with pytest.raises(ValueError, match="below required level"):
            await TaskService.assign_task_to_user(
                db=db_session,
                user_id=user.id,
                task_id=task.id
            )

    @pytest.mark.asyncio
    async def test_task_max_completions(self, db_session: AsyncSession):
        """测试任务完成次数限制"""
        # 创建用户
        user = await PointsService.get_or_create_user(db_session, "0xuser_maxcomp")
        await db_session.commit()

        # 创建限制完成次数的任务
        task = await TaskService.create_task(
            db=db_session,
            task_key="max_comp_task",
            title="限次任务",
            task_type=TaskType.DAILY,
            reward_points=100,
            target_value=1,
            max_completions_per_user=1  # 最多完成1次
        )
        await db_session.commit()

        # 第一次完成
        user_task1 = await TaskService.assign_task_to_user(
            db=db_session,
            user_id=user.id,
            task_id=task.id
        )
        await TaskService.update_task_progress(
            db=db_session,
            user_task_id=user_task1.id,
            progress_delta=1
        )
        await TaskService.claim_task_reward(
            db=db_session,
            user_task_id=user_task1.id
        )
        await db_session.commit()

        # 尝试第二次领取（应该失败）
        with pytest.raises(ValueError, match="reached max completions"):
            await TaskService.assign_task_to_user(
                db=db_session,
                user_id=user.id,
                task_id=task.id
            )
