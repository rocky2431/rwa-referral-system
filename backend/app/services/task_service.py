"""
任务服务
处理所有任务相关的业务逻辑
"""
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_, or_
from loguru import logger

from app.models import Task, UserTask, User, UserPoints
from app.models.task import TaskType, TaskTrigger, UserTaskStatus
from app.models.team_member import TeamMember, TeamMemberStatus  # ✅ 修复导入路径
from app.services.points_service import PointsService
from app.models.point_transaction import PointTransactionType


class TaskService:
    """任务服务类"""

    # ========== 任务配置 CRUD ==========

    @staticmethod
    async def create_task(
        db: AsyncSession,
        task_key: str,
        title: str,
        task_type: TaskType,
        reward_points: int,
        **kwargs
    ) -> Task:
        """
        创建任务配置

        Args:
            db: 数据库会话
            task_key: 任务唯一标识
            title: 任务标题
            task_type: 任务类型
            reward_points: 奖励积分
            **kwargs: 其他可选参数

        Returns:
            Task对象

        Raises:
            ValueError: 任务标识已存在
        """
        try:
            # 1. 检查task_key是否已存在
            result = await db.execute(
                select(Task).where(Task.task_key == task_key)
            )
            if result.scalar_one_or_none():
                raise ValueError(f"Task key '{task_key}' already exists")

            # 2. 创建任务
            task = Task(
                task_key=task_key,
                title=title,
                task_type=task_type,
                reward_points=reward_points,
                **kwargs
            )
            db.add(task)
            await db.commit()
            await db.refresh(task)

            logger.info(f"✅ 任务创建成功: id={task.id}, key={task_key}, type={task_type.value}")
            return task

        except ValueError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 任务创建失败: {e}")
            raise

    @staticmethod
    async def get_task(db: AsyncSession, task_id: int) -> Optional[Task]:
        """根据ID获取任务配置"""
        result = await db.execute(
            select(Task).where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_task_by_key(db: AsyncSession, task_key: str) -> Optional[Task]:
        """根据task_key获取任务配置"""
        result = await db.execute(
            select(Task).where(Task.task_key == task_key)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_tasks(
        db: AsyncSession,
        task_type: Optional[TaskType] = None,
        is_active: Optional[bool] = None,
        is_visible: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Task], int]:
        """
        分页获取任务列表

        Returns:
            (任务列表, 总数)
        """
        query = select(Task)

        # 筛选条件
        if task_type:
            query = query.where(Task.task_type == task_type)
        if is_active is not None:
            query = query.where(Task.is_active == is_active)
        if is_visible is not None:
            query = query.where(Task.is_visible == is_visible)

        # 时间范围筛选（当前时间在任务有效期内）
        now = datetime.utcnow()
        query = query.where(
            or_(
                Task.start_time.is_(None),
                Task.start_time <= now
            )
        ).where(
            or_(
                Task.end_time.is_(None),
                Task.end_time > now
            )
        )

        # 总数查询
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # 分页查询（按优先级和排序顺序）
        query = query.order_by(desc(Task.priority), Task.sort_order)
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        tasks = result.scalars().all()

        return list(tasks), total

    @staticmethod
    async def update_task(
        db: AsyncSession,
        task_id: int,
        **update_data
    ) -> Task:
        """
        更新任务配置

        Args:
            db: 数据库会话
            task_id: 任务ID
            **update_data: 更新数据

        Returns:
            更新后的Task对象

        Raises:
            ValueError: 任务不存在
        """
        try:
            task = await TaskService.get_task(db, task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")

            # 更新字段
            for key, value in update_data.items():
                if hasattr(task, key) and value is not None:
                    setattr(task, key, value)

            await db.commit()
            await db.refresh(task)

            logger.info(f"✅ 任务更新成功: task_id={task_id}")
            return task

        except ValueError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 任务更新失败: {e}")
            raise

    @staticmethod
    async def delete_task(db: AsyncSession, task_id: int) -> bool:
        """
        删除任务配置（软删除：设置为不激活）

        Args:
            db: 数据库会话
            task_id: 任务ID

        Returns:
            是否成功

        Raises:
            ValueError: 任务不存在
        """
        try:
            task = await TaskService.get_task(db, task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")

            task.is_active = False
            task.is_visible = False

            await db.commit()

            logger.info(f"✅ 任务删除成功: task_id={task_id}")
            return True

        except ValueError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 任务删除失败: {e}")
            raise

    # ========== 用户任务管理 ==========

    @staticmethod
    async def assign_task_to_user(
        db: AsyncSession,
        user_id: int,
        task_id: int,
        metadata: Optional[str] = None
    ) -> UserTask:
        """
        为用户分配任务（用户领取任务）

        Args:
            db: 数据库会话
            user_id: 用户ID
            task_id: 任务ID
            metadata: 元数据（JSON字符串）

        Returns:
            UserTask对象

        Raises:
            ValueError: 任务不存在、用户已有该任务、不满足条件等
        """
        try:
            # 1. 获取任务配置
            task = await TaskService.get_task(db, task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")

            if not task.is_active:
                raise ValueError(f"Task {task_id} is not active")

            # 2. 检查时间范围
            now = datetime.utcnow()
            if task.start_time and now < task.start_time:
                raise ValueError(f"Task {task_id} has not started yet")
            if task.end_time and now > task.end_time:
                raise ValueError(f"Task {task_id} has ended")

            # 3. 检查用户等级
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise ValueError(f"User {user_id} not found")

            if user.level < task.min_level_required:
                raise ValueError(
                    f"User level {user.level} is below required level {task.min_level_required}"
                )

            # 4. 检查是否已领取
            result = await db.execute(
                select(UserTask).where(
                    UserTask.user_id == user_id,
                    UserTask.task_id == task_id,
                    UserTask.status.in_([
                        UserTaskStatus.IN_PROGRESS,
                        UserTaskStatus.COMPLETED
                    ])
                )
            )
            if result.scalar_one_or_none():
                raise ValueError(f"User {user_id} already has this task")

            # 5. 检查完成次数限制(可重复任务)
            if task.max_completions_per_user:
                # 查询用户当前任务实例的完成次数
                existing_task_result = await db.execute(
                    select(UserTask).where(
                        UserTask.user_id == user_id,
                        UserTask.task_id == task_id
                    ).order_by(desc(UserTask.created_at))
                )
                existing_task = existing_task_result.scalars().first()

                if existing_task and existing_task.completion_count >= task.max_completions_per_user:
                    raise ValueError(
                        f"User {user_id} has reached max completions ({task.max_completions_per_user})"
                    )

            # 6. 特殊任务检查：战队相关任务
            # 如果是加入战队任务，检查用户是否已加入战队
            if task.task_key in ['join_team', 'create_team']:
                team_member_result = await db.execute(
                    select(TeamMember).where(
                        TeamMember.user_id == user_id,
                        TeamMember.status == TeamMemberStatus.ACTIVE
                    )
                )
                team_member = team_member_result.scalar_one_or_none()

                if team_member:
                    raise ValueError(f"用户已加入战队，无法领取此任务")

            # 7. 计算过期时间
            expires_at = None
            if task.task_type == TaskType.DAILY:
                expires_at = datetime.utcnow() + timedelta(days=1)
            elif task.task_type == TaskType.WEEKLY:
                expires_at = datetime.utcnow() + timedelta(weeks=1)
            elif task.end_time:
                expires_at = task.end_time

            # 8. 创建用户任务
            user_task = UserTask(
                user_id=user_id,
                task_id=task_id,
                target_value=task.target_value,
                reward_points=task.reward_points,
                status=UserTaskStatus.IN_PROGRESS,
                expires_at=expires_at,
                metadata=metadata
            )
            db.add(user_task)
            await db.commit()
            await db.refresh(user_task)

            logger.info(
                f"✅ 用户任务创建成功: user_id={user_id}, task_id={task_id}, "
                f"user_task_id={user_task.id}"
            )
            return user_task

        except ValueError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 用户任务创建失败: {e}")
            raise

    @staticmethod
    async def update_task_progress(
        db: AsyncSession,
        user_task_id: int,
        progress_delta: int
    ) -> UserTask:
        """
        更新任务进度

        Args:
            db: 数据库会话
            user_task_id: 用户任务ID
            progress_delta: 进度增量

        Returns:
            更新后的UserTask对象

        Raises:
            ValueError: 用户任务不存在或已完成
        """
        try:
            # 1. 获取用户任务
            result = await db.execute(
                select(UserTask).where(UserTask.id == user_task_id)
            )
            user_task = result.scalar_one_or_none()
            if not user_task:
                raise ValueError(f"UserTask {user_task_id} not found")

            if user_task.status != UserTaskStatus.IN_PROGRESS:
                raise ValueError(f"UserTask {user_task_id} is not in progress")

            # 2. 检查是否过期
            if user_task.expires_at and datetime.utcnow() > user_task.expires_at:
                user_task.status = UserTaskStatus.EXPIRED
                await db.commit()
                raise ValueError(f"UserTask {user_task_id} has expired")

            # 3. 更新进度
            user_task.current_value = min(
                user_task.current_value + progress_delta,
                user_task.target_value
            )

            # 4. 检查是否完成
            if user_task.current_value >= user_task.target_value:
                user_task.status = UserTaskStatus.COMPLETED
                user_task.completed_at = datetime.utcnow()

                logger.info(
                    f"🎉 任务完成: user_task_id={user_task_id}, "
                    f"user_id={user_task.user_id}, task_id={user_task.task_id}"
                )

            await db.commit()
            await db.refresh(user_task)

            logger.info(
                f"✅ 任务进度更新: user_task_id={user_task_id}, "
                f"progress={user_task.current_value}/{user_task.target_value}"
            )
            return user_task

        except ValueError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 任务进度更新失败: {e}")
            raise

    @staticmethod
    async def claim_task_reward(
        db: AsyncSession,
        user_task_id: int
    ) -> dict:
        """
        领取任务奖励

        新状态流转:
        - COMPLETED → REWARDED (一次性任务,终止)
        - COMPLETED → AVAILABLE (可重复任务,重置)

        Args:
            db: 数据库会话
            user_task_id: 用户任务ID

        Returns:
            奖励信息字典

        Raises:
            ValueError: 用户任务不存在、未完成或已领取
        """
        try:
            # 1. 获取用户任务
            result = await db.execute(
                select(UserTask).where(UserTask.id == user_task_id)
            )
            user_task = result.scalar_one_or_none()
            if not user_task:
                raise ValueError(f"UserTask {user_task_id} not found")

            if user_task.status != UserTaskStatus.COMPLETED:
                raise ValueError(f"UserTask {user_task_id} is not completed")

            if user_task.is_claimed:
                raise ValueError(f"UserTask {user_task_id} reward already claimed")

            # 2. 获取任务配置
            task = await TaskService.get_task(db, user_task.task_id)
            if not task:
                raise ValueError(f"Task {user_task.task_id} not found")

            # 3. 计算总奖励
            total_points = user_task.reward_points + user_task.bonus_points

            # 4. 发放积分奖励
            await PointsService.add_user_points(
                db=db,
                user_id=user_task.user_id,
                points=total_points,
                transaction_type=PointTransactionType.TASK_REWARD,
                description=f"任务奖励 - {task.title}",
                related_task_id=task.id
            )

            # 5. 发放经验奖励（如果有）
            if task.reward_experience > 0:
                # 更新用户经验
                user_result = await db.execute(
                    select(User).where(User.id == user_task.user_id)
                )
                user = user_result.scalar_one_or_none()
                if user:
                    user.experience += task.reward_experience
                    # 这里可以添加升级逻辑

            # 6. 更新用户任务状态
            user_task.is_claimed = True
            user_task.claimed_at = datetime.utcnow()
            user_task.completion_count += 1

            # 7. 判断是否可重复任务
            is_repeatable = task.max_completions_per_user is None or \
                           user_task.completion_count < task.max_completions_per_user

            if is_repeatable:
                # 可重复任务: 重置进度,状态改为AVAILABLE
                user_task.status = UserTaskStatus.AVAILABLE
                user_task.current_value = 0
                user_task.is_claimed = False  # 重置领取标记,允许下次领取
                logger.info(
                    f"🔄 可重复任务已重置: user_task_id={user_task_id}, "
                    f"completion_count={user_task.completion_count}"
                )
            else:
                # 一次性任务或达到次数限制: 标记为REWARDED
                user_task.status = UserTaskStatus.REWARDED
                logger.info(
                    f"✅ 任务已完成: user_task_id={user_task_id}"
                )

            await db.commit()

            logger.info(
                f"✅ 任务奖励领取成功: user_task_id={user_task_id}, "
                f"user_id={user_task.user_id}, points={total_points}, exp={task.reward_experience}"
            )

            return {
                "points_reward": total_points,
                "experience_reward": task.reward_experience,
                "task_title": task.title,
                "is_repeatable": is_repeatable,
                "completion_count": user_task.completion_count
            }

        except ValueError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 任务奖励领取失败: {e}")
            raise

    @staticmethod
    async def get_user_tasks(
        db: AsyncSession,
        user_id: int,
        status: Optional[UserTaskStatus] = None,
        task_type: Optional[TaskType] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[UserTask], int]:
        """
        获取用户任务列表（分页）

        Returns:
            (用户任务列表, 总数)
        """
        query = select(UserTask).where(UserTask.user_id == user_id)

        if status:
            query = query.where(UserTask.status == status)

        # 如果需要按任务类型筛选，需要join
        if task_type:
            query = query.join(Task).where(Task.task_type == task_type)

        # 总数查询
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # 分页查询（按创建时间降序）
        query = query.order_by(desc(UserTask.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        user_tasks = result.scalars().all()

        return list(user_tasks), total

    @staticmethod
    async def get_user_task(
        db: AsyncSession,
        user_id: int,
        task_id: int
    ) -> Optional[UserTask]:
        """获取用户的特定任务"""
        result = await db.execute(
            select(UserTask).where(
                UserTask.user_id == user_id,
                UserTask.task_id == task_id,
                UserTask.status.in_([
                    UserTaskStatus.IN_PROGRESS,
                    UserTaskStatus.COMPLETED
                ])
            ).order_by(desc(UserTask.created_at))
        )
        return result.scalars().first()

    # ========== 任务统计 ==========

    @staticmethod
    async def get_task_statistics(
        db: AsyncSession,
        task_id: int
    ) -> dict:
        """获取任务统计信息"""
        try:
            task = await TaskService.get_task(db, task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")

            # 参与人数
            participants_result = await db.execute(
                select(func.count(func.distinct(UserTask.user_id)))
                .where(UserTask.task_id == task_id)
            )
            total_participants = participants_result.scalar_one()

            # 完成人数
            completed_result = await db.execute(
                select(func.count(func.distinct(UserTask.user_id)))
                .where(
                    UserTask.task_id == task_id,
                    UserTask.status.in_([UserTaskStatus.COMPLETED, UserTaskStatus.REWARDED])
                )
            )
            total_completed = completed_result.scalar_one()

            # 总发放奖励
            rewards_result = await db.execute(
                select(func.sum(UserTask.reward_points + UserTask.bonus_points))
                .where(
                    UserTask.task_id == task_id,
                    UserTask.is_claimed == True
                )
            )
            total_rewards = rewards_result.scalar_one() or 0

            # 完成率
            completion_rate = (total_completed / total_participants * 100) if total_participants > 0 else 0

            return {
                "task_id": task_id,
                "task_key": task.task_key,
                "task_title": task.title,
                "task_type": task.task_type,
                "total_participants": total_participants,
                "total_completed": total_completed,
                "completion_rate": round(completion_rate, 2),
                "total_rewards_distributed": total_rewards
            }

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"❌ 获取任务统计失败: {e}")
            raise

    @staticmethod
    async def get_user_task_summary(
        db: AsyncSession,
        user_id: int
    ) -> dict:
        """获取用户任务汇总"""
        try:
            # 总任务数
            total_result = await db.execute(
                select(func.count(UserTask.id)).where(UserTask.user_id == user_id)
            )
            total_tasks = total_result.scalar_one()

            # 各状态任务数
            status_counts = {}
            for status in UserTaskStatus:
                result = await db.execute(
                    select(func.count(UserTask.id)).where(
                        UserTask.user_id == user_id,
                        UserTask.status == status
                    )
                )
                status_counts[status.value] = result.scalar_one()

            # 总获得积分
            points_result = await db.execute(
                select(func.sum(UserTask.reward_points + UserTask.bonus_points))
                .where(
                    UserTask.user_id == user_id,
                    UserTask.is_claimed == True
                )
            )
            total_points_earned = points_result.scalar_one() or 0

            # 总获得经验（需要join Task表）
            exp_result = await db.execute(
                select(func.sum(Task.reward_experience))
                .join(UserTask, UserTask.task_id == Task.id)
                .where(
                    UserTask.user_id == user_id,
                    UserTask.is_claimed == True
                )
            )
            total_experience_earned = exp_result.scalar_one() or 0

            return {
                "user_id": user_id,
                "total_tasks": total_tasks,
                "available_tasks": status_counts.get(UserTaskStatus.AVAILABLE.value, 0),
                "in_progress_tasks": status_counts.get(UserTaskStatus.IN_PROGRESS.value, 0),
                "completed_tasks": status_counts.get(UserTaskStatus.COMPLETED.value, 0),
                "rewarded_tasks": status_counts.get(UserTaskStatus.REWARDED.value, 0),
                "expired_tasks": status_counts.get(UserTaskStatus.EXPIRED.value, 0),
                "total_points_earned": total_points_earned,
                "total_experience_earned": total_experience_earned
            }

        except Exception as e:
            logger.error(f"❌ 获取用户任务汇总失败: {e}")
            raise

    # ========== 自动任务触发 ==========

    @staticmethod
    async def auto_assign_tasks(
        db: AsyncSession,
        user_id: int
    ) -> List[UserTask]:
        """
        为用户自动分配所有AUTO触发类型的任务

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            自动分配的用户任务列表
        """
        try:
            # 获取所有AUTO触发的激活任务
            result = await db.execute(
                select(Task).where(
                    Task.trigger_type == TaskTrigger.AUTO,
                    Task.is_active == True
                )
            )
            auto_tasks = result.scalars().all()

            assigned_tasks = []
            for task in auto_tasks:
                try:
                    # 尝试为用户分配任务
                    user_task = await TaskService.assign_task_to_user(
                        db=db,
                        user_id=user_id,
                        task_id=task.id
                    )
                    assigned_tasks.append(user_task)
                except ValueError as e:
                    # 如果任务已存在或不满足条件，跳过
                    logger.debug(f"跳过任务 {task.task_key}: {e}")
                    continue

            if assigned_tasks:
                logger.info(
                    f"✅ 自动分配任务: user_id={user_id}, count={len(assigned_tasks)}"
                )

            return assigned_tasks

        except Exception as e:
            logger.error(f"❌ 自动分配任务失败: {e}")
            raise
