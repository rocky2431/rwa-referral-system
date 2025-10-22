"""
战队服务
处理所有战队相关的业务逻辑
"""
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_, or_
from loguru import logger

from app.models import Team, TeamMember, TeamTask, User
from app.models.team_member import TeamMemberRole, TeamMemberStatus
from app.models.team_task import TeamTaskStatus
from app.services.points_service import PointsService
from app.services.cache_service import CacheService
from app.services.task_service import TaskService
from app.models.point_transaction import PointTransactionType


class TeamService:
    """战队服务类"""

    # ========== 战队CRUD ==========

    @staticmethod
    async def create_team(
        db: AsyncSession,
        name: str,
        captain_id: int,
        description: Optional[str] = None,
        logo_url: Optional[str] = None,
        is_public: bool = True,
        require_approval: bool = False,
        max_members: int = 100
    ) -> Team:
        """
        创建战队

        Args:
            db: 数据库会话
            name: 战队名称
            captain_id: 队长用户ID
            description: 战队描述
            logo_url: Logo URL
            is_public: 是否公开
            require_approval: 是否需要审批
            max_members: 最大成员数

        Returns:
            Team对象
        """
        try:
            # 1. 检查用户是否已是其他战队队长
            result = await db.execute(
                select(Team).where(
                    Team.captain_id == captain_id,
                    Team.disbanded_at.is_(None)
                )
            )
            existing_captain_team = result.scalar_one_or_none()
            if existing_captain_team:
                raise ValueError(f"User {captain_id} is already a captain of team {existing_captain_team.name}")

            # 2. 检查战队名称是否已存在
            result = await db.execute(
                select(Team).where(Team.name == name)
            )
            if result.scalar_one_or_none():
                raise ValueError(f"Team name '{name}' already exists")

            # 3. 创建战队
            team = Team(
                name=name,
                captain_id=captain_id,
                description=description,
                logo_url=logo_url,
                is_public=is_public,
                require_approval=require_approval,
                max_members=max_members
            )
            db.add(team)
            await db.flush()

            # 4. 队长自动加入战队
            captain_member = TeamMember(
                team_id=team.id,
                user_id=captain_id,
                role=TeamMemberRole.CAPTAIN,
                status=TeamMemberStatus.ACTIVE,
                joined_at=datetime.utcnow(),
                approved_at=datetime.utcnow()
            )
            db.add(captain_member)

            await db.commit()
            await db.refresh(team)

            logger.info(f"✅ 战队创建成功: id={team.id}, name={name}, captain_id={captain_id}")
            return team

        except ValueError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 战队创建失败: {e}")
            raise

    @staticmethod
    async def get_team(db: AsyncSession, team_id: int) -> Optional[Team]:
        """获取战队信息"""
        result = await db.execute(
            select(Team).where(
                Team.id == team_id,
                Team.disbanded_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_teams(
        db: AsyncSession,
        is_public: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Team], int]:
        """
        分页获取战队列表

        Returns:
            (战队列表, 总数)
        """
        query = select(Team).where(Team.disbanded_at.is_(None))

        if is_public is not None:
            query = query.where(Team.is_public == is_public)

        # 总数查询
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # 分页查询
        query = query.order_by(desc(Team.total_points))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        teams = result.scalars().all()

        return list(teams), total

    @staticmethod
    async def update_team(
        db: AsyncSession,
        team_id: int,
        captain_id: int,
        **update_data
    ) -> Team:
        """
        更新战队信息（仅队长可操作）

        Args:
            db: 数据库会话
            team_id: 战队ID
            captain_id: 操作者用户ID（需验证是否为队长）
            **update_data: 更新数据

        Returns:
            更新后的Team对象
        """
        try:
            team = await TeamService.get_team(db, team_id)
            if not team:
                raise ValueError(f"Team {team_id} not found")

            if team.captain_id != captain_id:
                raise PermissionError(f"User {captain_id} is not the captain of team {team_id}")

            # 更新字段
            for key, value in update_data.items():
                if hasattr(team, key) and value is not None:
                    setattr(team, key, value)

            await db.commit()
            await db.refresh(team)

            logger.info(f"✅ 战队更新成功: team_id={team_id}")
            return team

        except (ValueError, PermissionError):
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 战队更新失败: {e}")
            raise

    @staticmethod
    async def disband_team(db: AsyncSession, team_id: int, captain_id: int) -> bool:
        """
        解散战队（仅队长可操作）

        Args:
            db: 数据库会话
            team_id: 战队ID
            captain_id: 操作者用户ID

        Returns:
            是否成功
        """
        try:
            team = await TeamService.get_team(db, team_id)
            if not team:
                raise ValueError(f"Team {team_id} not found")

            if team.captain_id != captain_id:
                raise PermissionError(f"User {captain_id} is not the captain")

            # 标记为已解散
            team.disbanded_at = datetime.utcnow()

            await db.commit()

            logger.info(f"✅ 战队解散成功: team_id={team_id}")
            return True

        except (ValueError, PermissionError):
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 战队解散失败: {e}")
            raise

    # ========== 成员管理 ==========

    @staticmethod
    async def join_team(
        db: AsyncSession,
        team_id: int,
        user_id: int
    ) -> TeamMember:
        """
        加入战队

        Args:
            db: 数据库会话
            team_id: 战队ID
            user_id: 用户ID

        Returns:
            TeamMember对象
        """
        try:
            # 1. 检查战队是否存在
            team = await TeamService.get_team(db, team_id)
            if not team:
                raise ValueError(f"Team {team_id} not found")

            # 2. 检查用户是否已在战队中
            result = await db.execute(
                select(TeamMember).where(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == user_id,
                    TeamMember.status.in_([TeamMemberStatus.ACTIVE, TeamMemberStatus.PENDING])
                )
            )
            if result.scalar_one_or_none():
                raise ValueError(f"User {user_id} already in team or pending")

            # 3. 检查战队人数是否已满
            if team.member_count >= team.max_members:
                raise ValueError(f"Team {team_id} is full")

            # 4. 创建成员记录
            status = TeamMemberStatus.PENDING if team.require_approval else TeamMemberStatus.ACTIVE
            member = TeamMember(
                team_id=team_id,
                user_id=user_id,
                role=TeamMemberRole.MEMBER,
                status=status,
                joined_at=datetime.utcnow() if not team.require_approval else None,
                approved_at=datetime.utcnow() if not team.require_approval else None
            )
            db.add(member)

            # 5. 如果不需要审批，直接增加成员数
            if not team.require_approval:
                team.member_count += 1

            await db.commit()
            await db.refresh(member)

            # 6. 如果是直接加入（不需要审批），完成"加入战队"任务并发放积分
            if not team.require_approval:
                try:
                    join_task = await TaskService.get_task_by_key(db, "join_team")
                    if join_task:
                        # 创建任务实例
                        user_task = await TaskService.assign_task_to_user(
                            db=db,
                            user_id=user_id,
                            task_id=join_task.id
                        )
                        # 立即完成任务
                        await TaskService.update_task_progress(
                            db=db,
                            user_task_id=user_task.id,
                            progress_delta=1
                        )
                        logger.info(f"✅ 加入战队任务自动完成: user_id={user_id}")
                except Exception as e:
                    logger.warning(f"⚠️ 加入战队任务创建失败（不影响加入）: {e}")

            logger.info(
                f"✅ 用户加入战队: user_id={user_id}, team_id={team_id}, status={status.value}"
            )
            return member

        except ValueError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 加入战队失败: {e}")
            raise

    @staticmethod
    async def approve_member(
        db: AsyncSession,
        team_id: int,
        user_id: int,
        approver_id: int,
        approved: bool
    ) -> TeamMember:
        """
        审批成员申请（队长/管理员可操作）

        Args:
            db: 数据库会话
            team_id: 战队ID
            user_id: 申请用户ID
            approver_id: 审批人ID
            approved: True=通过, False=拒绝

        Returns:
            TeamMember对象
        """
        try:
            # 1. 检查审批人权限
            result = await db.execute(
                select(TeamMember).where(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == approver_id,
                    TeamMember.role.in_([TeamMemberRole.CAPTAIN, TeamMemberRole.ADMIN]),
                    TeamMember.status == TeamMemberStatus.ACTIVE
                )
            )
            if not result.scalar_one_or_none():
                raise PermissionError(f"User {approver_id} is not authorized to approve")

            # 2. 获取待审批的成员
            result = await db.execute(
                select(TeamMember).where(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == user_id,
                    TeamMember.status == TeamMemberStatus.PENDING
                )
            )
            member = result.scalar_one_or_none()
            if not member:
                raise ValueError(f"No pending application found for user {user_id}")

            # 3. 更新状态
            if approved:
                member.status = TeamMemberStatus.ACTIVE
                member.joined_at = datetime.utcnow()
                member.approved_at = datetime.utcnow()

                # 增加战队成员数
                team = await TeamService.get_team(db, team_id)
                if team:
                    team.member_count += 1
            else:
                member.status = TeamMemberStatus.REJECTED

            await db.commit()
            await db.refresh(member)

            # 4. 如果审批通过，完成"加入战队"任务并发放积分
            if approved:
                try:
                    join_task = await TaskService.get_task_by_key(db, "join_team")
                    if join_task:
                        # 创建任务实例
                        user_task = await TaskService.assign_task_to_user(
                            db=db,
                            user_id=user_id,
                            task_id=join_task.id
                        )
                        # 立即完成任务
                        await TaskService.update_task_progress(
                            db=db,
                            user_task_id=user_task.id,
                            progress_delta=1
                        )
                        logger.info(f"✅ 加入战队任务自动完成（审批通过）: user_id={user_id}")
                except Exception as e:
                    logger.warning(f"⚠️ 加入战队任务创建失败（不影响审批）: {e}")

            logger.info(
                f"✅ 成员申请审批完成: user_id={user_id}, team_id={team_id}, "
                f"approved={approved}"
            )
            return member

        except (ValueError, PermissionError):
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 审批成员失败: {e}")
            raise

    @staticmethod
    async def update_member_role(
        db: AsyncSession,
        team_id: int,
        user_id: int,
        new_role: TeamMemberRole,
        operator_id: int
    ) -> TeamMember:
        """
        更新成员角色（仅队长可操作）

        Args:
            db: 数据库会话
            team_id: 战队ID
            user_id: 目标用户ID
            new_role: 新角色 (member/admin/captain)
            operator_id: 操作者ID（需验证是否为队长）

        Returns:
            更新后的TeamMember对象

        Raises:
            ValueError: 成员不存在或参数无效
            PermissionError: 操作者无权限
        """
        try:
            # 1. 验证操作者权限（必须是队长）
            operator_result = await db.execute(
                select(TeamMember).where(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == operator_id,
                    TeamMember.role == TeamMemberRole.CAPTAIN,
                    TeamMember.status == TeamMemberStatus.ACTIVE
                )
            )
            operator = operator_result.scalar_one_or_none()
            if not operator:
                raise PermissionError(
                    f"User {operator_id} is not the captain of team {team_id}"
                )

            # 2. 获取目标成员
            target_result = await db.execute(
                select(TeamMember).where(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == user_id,
                    TeamMember.status == TeamMemberStatus.ACTIVE
                )
            )
            target_member = target_result.scalar_one_or_none()
            if not target_member:
                raise ValueError(
                    f"User {user_id} is not an active member of team {team_id}"
                )

            # 3. 防止操作者给自己降权
            if operator_id == user_id:
                raise PermissionError(
                    "Cannot change your own role. Please transfer captain role first."
                )

            # 4. 处理队长转让（特殊逻辑）
            if new_role == TeamMemberRole.CAPTAIN:
                # 队长转让：将当前队长降为管理员
                operator.role = TeamMemberRole.ADMIN
                target_member.role = TeamMemberRole.CAPTAIN

                # 更新战队的队长ID
                team = await TeamService.get_team(db, team_id)
                if team:
                    team.captain_id = user_id

                logger.info(
                    f"👑 队长转让: team_id={team_id}, "
                    f"from={operator_id} to={user_id}"
                )
            else:
                # 普通角色更新
                old_role = target_member.role
                target_member.role = new_role

                logger.info(
                    f"✅ 成员角色更新: team_id={team_id}, user_id={user_id}, "
                    f"{old_role.value} → {new_role.value}"
                )

            await db.commit()
            await db.refresh(target_member)

            return target_member

        except (ValueError, PermissionError):
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 角色更新失败: {e}")
            raise

    @staticmethod
    async def leave_team(db: AsyncSession, team_id: int, user_id: int) -> bool:
        """
        离开战队

        Args:
            db: 数据库会话
            team_id: 战队ID
            user_id: 用户ID

        Returns:
            是否成功
        """
        try:
            # 1. 获取成员记录
            result = await db.execute(
                select(TeamMember).where(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == user_id,
                    TeamMember.status == TeamMemberStatus.ACTIVE
                )
            )
            member = result.scalar_one_or_none()
            if not member:
                raise ValueError(f"User {user_id} is not an active member of team {team_id}")

            # 2. 队长不能直接离开（需先转让队长）
            if member.role == TeamMemberRole.CAPTAIN:
                raise PermissionError("Captain cannot leave the team directly. Transfer captain role first.")

            # 3. 更新状态
            member.status = TeamMemberStatus.LEFT
            member.left_at = datetime.utcnow()

            # 4. 减少战队成员数
            team = await TeamService.get_team(db, team_id)
            if team:
                team.member_count -= 1

            await db.commit()

            logger.info(f"✅ 用户离开战队: user_id={user_id}, team_id={team_id}")
            return True

        except (ValueError, PermissionError):
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 离开战队失败: {e}")
            raise

    @staticmethod
    async def get_team_members(
        db: AsyncSession,
        team_id: int,
        status: Optional[TeamMemberStatus] = None
    ) -> List[TeamMember]:
        """获取战队成员列表"""
        query = select(TeamMember).where(TeamMember.team_id == team_id)

        if status:
            query = query.where(TeamMember.status == status)

        query = query.order_by(desc(TeamMember.contribution_points))

        result = await db.execute(query)
        return list(result.scalars().all())

    # ========== 战队任务系统 ==========

    @staticmethod
    async def create_team_task(
        db: AsyncSession,
        team_id: int,
        title: str,
        task_type: str,
        target_value: int,
        reward_points: int,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        bonus_points: int = 0
    ) -> TeamTask:
        """创建战队任务"""
        try:
            task = TeamTask(
                team_id=team_id,
                title=title,
                description=description,
                task_type=task_type,
                target_value=target_value,
                reward_points=reward_points,
                bonus_points=bonus_points,
                start_time=start_time,
                end_time=end_time
            )
            db.add(task)
            await db.commit()
            await db.refresh(task)

            logger.info(f"✅ 战队任务创建成功: team_id={team_id}, task_id={task.id}")
            return task

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 创建战队任务失败: {e}")
            raise

    @staticmethod
    async def get_team_tasks(
        db: AsyncSession,
        team_id: int,
        status: Optional[TeamTaskStatus] = None
    ) -> List[TeamTask]:
        """获取战队任务列表"""
        query = select(TeamTask).where(TeamTask.team_id == team_id)

        if status:
            query = query.where(TeamTask.status == status)

        query = query.order_by(desc(TeamTask.created_at))

        result = await db.execute(query)
        return list(result.scalars().all())

    # ========== 奖励池分配 ==========

    @staticmethod
    async def add_to_reward_pool(
        db: AsyncSession,
        team_id: int,
        amount: int,
        source_description: str = "战队奖励"
    ) -> bool:
        """
        向战队奖励池注入积分

        Args:
            db: 数据库会话
            team_id: 战队ID
            amount: 注入积分数量
            source_description: 来源描述

        Returns:
            是否成功
        """
        try:
            team = await TeamService.get_team(db, team_id)
            if not team:
                raise ValueError(f"Team {team_id} not found")

            if amount <= 0:
                raise ValueError(f"Amount must be positive: {amount}")

            # 增加奖励池
            team.reward_pool += amount

            await db.commit()

            logger.info(
                f"💰 战队奖励池注入: team_id={team_id}, "
                f"amount={amount}, source={source_description}, "
                f"new_pool={team.reward_pool}"
            )

            return True

        except ValueError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 奖励池注入失败: {e}")
            raise

    @staticmethod
    async def distribute_reward_pool(
        db: AsyncSession,
        team_id: int,
        min_distribution_interval_hours: int = 24
    ) -> dict:
        """
        分配战队奖励池（改进版）

        按成员贡献积分比例分配奖励池积分，处理四舍五入误差

        Args:
            db: 数据库会话
            team_id: 战队ID
            min_distribution_interval_hours: 最小分配间隔（小时）

        Returns:
            分配结果字典
        """
        try:
            # 1. 获取战队
            team = await TeamService.get_team(db, team_id)
            if not team:
                raise ValueError(f"Team {team_id} not found")

            if team.reward_pool <= 0:
                return {"message": "奖励池为空", "distributed": 0}

            # 2. 检查分配间隔（防止频繁分配）
            if team.last_distribution_at:
                from datetime import timedelta
                time_since_last = datetime.utcnow() - team.last_distribution_at
                if time_since_last < timedelta(hours=min_distribution_interval_hours):
                    remaining = min_distribution_interval_hours - (time_since_last.total_seconds() / 3600)
                    return {
                        "message": f"距离上次分配不足{min_distribution_interval_hours}小时",
                        "distributed": 0,
                        "remaining_hours": round(remaining, 2)
                    }

            # 3. 获取所有活跃成员（按贡献降序）
            members_result = await db.execute(
                select(TeamMember).where(
                    TeamMember.team_id == team_id,
                    TeamMember.status == TeamMemberStatus.ACTIVE
                ).order_by(desc(TeamMember.contribution_points))
            )
            active_members = list(members_result.scalars().all())

            if not active_members:
                return {"message": "无活跃成员", "distributed": 0}

            # 4. 计算总贡献
            total_contribution = sum(m.contribution_points for m in active_members)

            if total_contribution == 0:
                # 如果总贡献为0，平均分配
                logger.warning(f"⚠️  战队 {team_id} 总贡献为0，将平均分配奖励池")
                pool_amount = team.reward_pool
                member_count = len(active_members)
                share_per_member = pool_amount // member_count
                remainder = pool_amount % member_count

                distribution_records = []
                for idx, member in enumerate(active_members):
                    # 余数分配给贡献最高的成员（前几名）
                    member_share = share_per_member + (1 if idx < remainder else 0)

                    if member_share > 0:
                        await PointsService.add_user_points(
                            db=db,
                            user_id=member.user_id,
                            points=member_share,
                            transaction_type=PointTransactionType.TEAM_REWARD,
                            description=f"战队奖励池平均分配 - {team.name}",
                            related_team_id=team_id
                        )

                        distribution_records.append({
                            "user_id": member.user_id,
                            "points": member_share,
                            "contribution": 0,
                            "share_ratio": round(1 / member_count, 4)
                        })
            else:
                # 5. 按贡献比例分配（处理四舍五入误差）
                pool_amount = team.reward_pool
                distribution_records = []
                total_distributed = 0

                # 计算每个成员的份额
                member_shares = []
                for member in active_members:
                    if member.contribution_points > 0:
                        share_ratio = member.contribution_points / total_contribution
                        member_share = int(share_ratio * pool_amount)
                        member_shares.append({
                            "member": member,
                            "share": member_share,
                            "ratio": share_ratio,
                            "fractional_part": (share_ratio * pool_amount) - member_share
                        })
                        total_distributed += member_share

                # 处理四舍五入误差：将剩余积分分配给小数部分最大的成员
                remainder = pool_amount - total_distributed
                if remainder > 0:
                    # 按小数部分降序排序
                    member_shares.sort(key=lambda x: x["fractional_part"], reverse=True)
                    for i in range(remainder):
                        if i < len(member_shares):
                            member_shares[i]["share"] += 1

                # 发放积分
                for item in member_shares:
                    member = item["member"]
                    member_share = item["share"]

                    if member_share > 0:
                        await PointsService.add_user_points(
                            db=db,
                            user_id=member.user_id,
                            points=member_share,
                            transaction_type=PointTransactionType.TEAM_REWARD,
                            description=f"战队奖励池分配 - {team.name}",
                            related_team_id=team_id
                        )

                        distribution_records.append({
                            "user_id": member.user_id,
                            "points": member_share,
                            "contribution": member.contribution_points,
                            "share_ratio": round(item["ratio"], 4)
                        })

            # 6. 清空奖励池并记录时间
            distributed_amount = team.reward_pool
            team.reward_pool = 0
            team.last_distribution_at = datetime.utcnow()

            await db.commit()

            # 7. 使战队相关缓存失效
            await CacheService.invalidate_leaderboard_cache("teams")

            # 使每个成员的积分缓存失效
            for record in distribution_records:
                await CacheService.invalidate_user_all_cache(record["user_id"])

            logger.info(
                f"✅ 奖励池分配完成: team_id={team_id}, "
                f"total={distributed_amount}, members={len(distribution_records)}"
            )

            return {
                "message": "分配成功",
                "total_distributed": distributed_amount,
                "member_count": len(distribution_records),
                "total_contribution": total_contribution,
                "records": distribution_records
            }

        except ValueError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 奖励池分配失败: {e}")
            raise

    # ========== 战队排行榜 ==========

    @staticmethod
    async def get_team_leaderboard(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[dict], int]:
        """
        获取战队排行榜

        Returns:
            (排行榜数据, 总数)
        """
        try:
            # 基础查询：未解散的战队
            query = select(Team).where(Team.disbanded_at.is_(None))

            # 总数
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar_one()

            # 排序：总积分降序
            query = query.order_by(desc(Team.total_points))
            query = query.offset((page - 1) * page_size).limit(page_size)

            result = await db.execute(query)
            teams = result.scalars().all()

            # 构建排行榜数据
            leaderboard = []
            rank = (page - 1) * page_size + 1

            for team in teams:
                # 查询队长信息
                captain_result = await db.execute(
                    select(User).where(User.id == team.captain_id)
                )
                captain = captain_result.scalar_one_or_none()

                leaderboard.append({
                    "rank": rank,
                    "team_id": team.id,
                    "team_name": team.name,
                    "team_logo_url": team.logo_url,
                    "total_points": team.total_points,
                    "member_count": team.member_count,
                    "level": team.level,
                    "captain_name": captain.username if captain else None
                })
                rank += 1

            return leaderboard, total

        except Exception as e:
            logger.error(f"❌ 获取排行榜失败: {e}")
            raise
