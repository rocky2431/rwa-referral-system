"""
TeamService单元测试
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.team_service import TeamService
from app.services.points_service import PointsService
from app.models import Team, TeamMember, User
from app.models.team_member import TeamMemberRole, TeamMemberStatus


class TestTeamService:
    """TeamService测试类"""

    @pytest.mark.asyncio
    async def test_create_team(self, db_session: AsyncSession):
        """测试创建战队"""
        # 创建用户作为队长
        user = await PointsService.get_or_create_user(
            db_session,
            "0xteam_captain_1234567890abcdef1234567890"
        )
        await db_session.commit()

        # 创建战队
        team = await TeamService.create_team(
            db=db_session,
            name="测试战队",
            captain_id=user.id,
            description="这是一个测试战队",
            is_public=True,
            require_approval=False
        )
        await db_session.commit()

        # 验证战队
        assert team.id is not None
        assert team.name == "测试战队"
        assert team.captain_id == user.id
        assert team.member_count == 1  # 队长自动加入

        # 验证队长成员记录
        members = await TeamService.get_team_members(db_session, team.id)
        assert len(members) == 1
        assert members[0].user_id == user.id
        assert members[0].role == TeamMemberRole.CAPTAIN
        assert members[0].status == TeamMemberStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_join_team_no_approval(self, db_session: AsyncSession):
        """测试加入战队（无需审批）"""
        # 创建战队
        captain = await PointsService.get_or_create_user(
            db_session, "0xcaptain2"
        )
        await db_session.commit()

        team = await TeamService.create_team(
            db=db_session,
            name="公开战队",
            captain_id=captain.id,
            require_approval=False  # 不需要审批
        )
        await db_session.commit()

        # 创建新用户加入
        new_user = await PointsService.get_or_create_user(
            db_session, "0xnewmember1"
        )
        await db_session.commit()

        # 加入战队
        member = await TeamService.join_team(
            db=db_session,
            team_id=team.id,
            user_id=new_user.id
        )
        await db_session.commit()

        # 验证
        assert member.team_id == team.id
        assert member.user_id == new_user.id
        assert member.status == TeamMemberStatus.ACTIVE  # 直接激活
        assert member.role == TeamMemberRole.MEMBER

        # 验证战队成员数更新
        from sqlalchemy import select
        result = await db_session.execute(select(Team).where(Team.id == team.id))
        updated_team = result.scalar_one()
        assert updated_team.member_count == 2  # 队长+新成员

    @pytest.mark.asyncio
    async def test_join_team_with_approval(self, db_session: AsyncSession):
        """测试加入战队（需要审批）"""
        # 创建需要审批的战队
        captain = await PointsService.get_or_create_user(db_session, "0xcaptain3")
        await db_session.commit()

        team = await TeamService.create_team(
            db=db_session,
            name="审批战队",
            captain_id=captain.id,
            require_approval=True  # 需要审批
        )
        await db_session.commit()

        # 新用户申请加入
        new_user = await PointsService.get_or_create_user(db_session, "0xnewmember2")
        await db_session.commit()

        member = await TeamService.join_team(
            db=db_session,
            team_id=team.id,
            user_id=new_user.id
        )
        await db_session.commit()

        # 验证状态为pending
        assert member.status == TeamMemberStatus.PENDING
        assert member.joined_at is None  # 未审批前无加入时间

        # 队长审批通过
        approved_member = await TeamService.approve_member(
            db=db_session,
            team_id=team.id,
            user_id=new_user.id,
            approver_id=captain.id,
            approved=True
        )
        await db_session.commit()

        # 验证审批后状态
        assert approved_member.status == TeamMemberStatus.ACTIVE
        assert approved_member.joined_at is not None
        assert approved_member.approved_at is not None

    @pytest.mark.asyncio
    async def test_leave_team(self, db_session: AsyncSession):
        """测试离开战队"""
        # 创建战队和成员
        captain = await PointsService.get_or_create_user(db_session, "0xcaptain4")
        await db_session.commit()

        team = await TeamService.create_team(
            db=db_session,
            name="可离开战队",
            captain_id=captain.id
        )
        await db_session.commit()

        member_user = await PointsService.get_or_create_user(db_session, "0xmember3")
        await db_session.commit()

        await TeamService.join_team(db=db_session, team_id=team.id, user_id=member_user.id)
        await db_session.commit()

        # 成员离开
        result = await TeamService.leave_team(
            db=db_session,
            team_id=team.id,
            user_id=member_user.id
        )

        assert result is True

        # 验证成员状态
        members = await TeamService.get_team_members(
            db=db_session,
            team_id=team.id,
            status=TeamMemberStatus.LEFT
        )
        assert len(members) == 1
        assert members[0].user_id == member_user.id

    @pytest.mark.asyncio
    async def test_captain_cannot_leave(self, db_session: AsyncSession):
        """测试队长不能直接离开战队"""
        captain = await PointsService.get_or_create_user(db_session, "0xcaptain5")
        await db_session.commit()

        team = await TeamService.create_team(
            db=db_session,
            name="队长战队",
            captain_id=captain.id
        )
        await db_session.commit()

        # 队长尝试离开应该抛出异常
        with pytest.raises(PermissionError, match="Captain cannot leave"):
            await TeamService.leave_team(
                db=db_session,
                team_id=team.id,
                user_id=captain.id
            )

    @pytest.mark.asyncio
    async def test_distribute_reward_pool(self, db_session: AsyncSession):
        """测试奖励池分配"""
        # 创建战队
        captain = await PointsService.get_or_create_user(db_session, "0xcaptain6")
        await db_session.commit()

        team = await TeamService.create_team(
            db=db_session,
            name="奖励战队",
            captain_id=captain.id
        )
        await db_session.commit()

        # 添加成员
        member1 = await PointsService.get_or_create_user(db_session, "0xmember4")
        member2 = await PointsService.get_or_create_user(db_session, "0xmember5")
        await db_session.commit()

        await TeamService.join_team(db=db_session, team_id=team.id, user_id=member1.id)
        await TeamService.join_team(db=db_session, team_id=team.id, user_id=member2.id)
        await db_session.commit()

        # 设置成员贡献和奖励池
        from sqlalchemy import select, update
        await db_session.execute(
            update(TeamMember)
            .where(TeamMember.user_id == captain.id)
            .values(contribution_points=100)
        )
        await db_session.execute(
            update(TeamMember)
            .where(TeamMember.user_id == member1.id)
            .values(contribution_points=50)
        )
        await db_session.execute(
            update(TeamMember)
            .where(TeamMember.user_id == member2.id)
            .values(contribution_points=50)
        )
        await db_session.execute(
            update(Team)
            .where(Team.id == team.id)
            .values(reward_pool=1000)
        )
        await db_session.commit()

        # 分配奖励池
        result = await TeamService.distribute_reward_pool(db=db_session, team_id=team.id)
        await db_session.commit()

        # 验证分配结果
        assert result["message"] == "分配成功"
        assert result["total_distributed"] == 1000
        assert result["member_count"] == 3

        # 验证奖励池已清空
        result = await db_session.execute(select(Team).where(Team.id == team.id))
        updated_team = result.scalar_one()
        assert updated_team.reward_pool == 0
        assert updated_team.last_distribution_at is not None

    @pytest.mark.asyncio
    async def test_get_team_leaderboard(self, db_session: AsyncSession):
        """测试战队排行榜"""
        # 创建多个战队
        for i in range(5):
            captain = await PointsService.get_or_create_user(
                db_session, f"0xleaderboard_captain_{i}"
            )
            await db_session.commit()

            await TeamService.create_team(
                db=db_session,
                name=f"排行榜战队{i}",
                captain_id=captain.id
            )
            await db_session.commit()

        # 为战队设置不同的积分
        from sqlalchemy import update
        await db_session.execute(
            update(Team)
            .where(Team.name == "排行榜战队0")
            .values(total_points=1000)
        )
        await db_session.execute(
            update(Team)
            .where(Team.name == "排行榜战队1")
            .values(total_points=800)
        )
        await db_session.commit()

        # 获取排行榜
        leaderboard, total = await TeamService.get_team_leaderboard(
            db=db_session,
            page=1,
            page_size=10
        )

        # 验证
        assert total >= 5
        assert len(leaderboard) >= 5
        # 验证排序（积分降序）
        assert leaderboard[0]["total_points"] >= leaderboard[1]["total_points"]
        # 验证排名
        assert leaderboard[0]["rank"] == 1
        assert leaderboard[1]["rank"] == 2

    @pytest.mark.asyncio
    async def test_update_team(self, db_session: AsyncSession):
        """测试更新战队信息"""
        # 创建战队
        captain = await PointsService.get_or_create_user(db_session, "0xcaptain_update")
        await db_session.commit()

        team = await TeamService.create_team(
            db=db_session,
            name="原始战队",
            captain_id=captain.id,
            description="原始描述"
        )
        await db_session.commit()

        # 更新战队信息
        updated_team = await TeamService.update_team(
            db=db_session,
            team_id=team.id,
            captain_id=captain.id,
            name="更新后战队",
            description="更新后描述",
            is_public=False
        )
        await db_session.commit()

        # 验证更新
        assert updated_team.name == "更新后战队"
        assert updated_team.description == "更新后描述"
        assert updated_team.is_public is False

    @pytest.mark.asyncio
    async def test_update_team_permission_denied(self, db_session: AsyncSession):
        """测试非队长无法更新战队"""
        # 创建战队
        captain = await PointsService.get_or_create_user(db_session, "0xcaptain_perm")
        await db_session.commit()

        team = await TeamService.create_team(
            db=db_session,
            name="权限测试战队",
            captain_id=captain.id
        )
        await db_session.commit()

        # 创建非队长用户
        other_user = await PointsService.get_or_create_user(db_session, "0xother_user")
        await db_session.commit()

        # 尝试更新（应该失败）
        with pytest.raises(PermissionError):
            await TeamService.update_team(
                db=db_session,
                team_id=team.id,
                captain_id=other_user.id,  # 非队长
                name="不应该成功"
            )

    @pytest.mark.asyncio
    async def test_disband_team(self, db_session: AsyncSession):
        """测试解散战队"""
        # 创建战队
        captain = await PointsService.get_or_create_user(db_session, "0xcaptain_disband")
        await db_session.commit()

        team = await TeamService.create_team(
            db=db_session,
            name="待解散战队",
            captain_id=captain.id
        )
        await db_session.commit()

        # 解散战队
        await TeamService.disband_team(
            db=db_session,
            team_id=team.id,
            captain_id=captain.id
        )
        await db_session.commit()

        # 验证解散状态
        from sqlalchemy import select
        result = await db_session.execute(select(Team).where(Team.id == team.id))
        disbanded_team = result.scalar_one()
        assert disbanded_team.disbanded_at is not None

    @pytest.mark.asyncio
    async def test_join_team_already_member(self, db_session: AsyncSession):
        """测试重复加入战队"""
        # 创建战队
        captain = await PointsService.get_or_create_user(db_session, "0xcaptain_duplicate")
        await db_session.commit()

        team = await TeamService.create_team(
            db=db_session,
            name="重复加入测试",
            captain_id=captain.id
        )
        await db_session.commit()

        # 创建用户并加入
        user = await PointsService.get_or_create_user(db_session, "0xmember_dup")
        await db_session.commit()

        await TeamService.join_team(db=db_session, team_id=team.id, user_id=user.id)
        await db_session.commit()

        # 尝试再次加入（应该抛出异常）
        with pytest.raises(ValueError, match="already|exists"):
            await TeamService.join_team(db=db_session, team_id=team.id, user_id=user.id)

    @pytest.mark.asyncio
    async def test_join_team_full(self, db_session: AsyncSession):
        """测试加入已满战队"""
        # 创建小容量战队
        captain = await PointsService.get_or_create_user(db_session, "0xcaptain_full")
        await db_session.commit()

        team = await TeamService.create_team(
            db=db_session,
            name="满员战队",
            captain_id=captain.id,
            max_members=2  # 最大2人
        )
        await db_session.commit()

        # 添加一个成员（此时已满：队长+1成员）
        member1 = await PointsService.get_or_create_user(db_session, "0xmember_full1")
        await db_session.commit()
        await TeamService.join_team(db=db_session, team_id=team.id, user_id=member1.id)
        await db_session.commit()

        # 尝试添加第三个成员（应该失败）
        member2 = await PointsService.get_or_create_user(db_session, "0xmember_full2")
        await db_session.commit()

        with pytest.raises(ValueError, match="full|已满"):
            await TeamService.join_team(db=db_session, team_id=team.id, user_id=member2.id)

    @pytest.mark.asyncio
    async def test_get_team_members_filter_by_status(self, db_session: AsyncSession):
        """测试按状态筛选成员"""
        # 创建需要审批的战队
        captain = await PointsService.get_or_create_user(db_session, "0xcaptain_filter")
        await db_session.commit()

        team = await TeamService.create_team(
            db=db_session,
            name="筛选测试战队",
            captain_id=captain.id,
            require_approval=True
        )
        await db_session.commit()

        # 添加待审批成员
        pending_user = await PointsService.get_or_create_user(db_session, "0xpending")
        await db_session.commit()
        await TeamService.join_team(db=db_session, team_id=team.id, user_id=pending_user.id)
        await db_session.commit()

        # 添加已通过成员
        active_user = await PointsService.get_or_create_user(db_session, "0xactive")
        await db_session.commit()
        await TeamService.join_team(db=db_session, team_id=team.id, user_id=active_user.id)
        await TeamService.approve_member(
            db=db_session,
            team_id=team.id,
            user_id=active_user.id,
            approver_id=captain.id,
            approved=True
        )
        await db_session.commit()

        # 筛选待审批成员
        pending_members = await TeamService.get_team_members(
            db=db_session,
            team_id=team.id,
            status=TeamMemberStatus.PENDING
        )
        assert len(pending_members) == 1
        assert pending_members[0].user_id == pending_user.id

        # 筛选激活成员
        active_members = await TeamService.get_team_members(
            db=db_session,
            team_id=team.id,
            status=TeamMemberStatus.ACTIVE
        )
        assert len(active_members) == 2  # 队长 + 通过的成员

    @pytest.mark.asyncio
    async def test_create_team_task(self, db_session: AsyncSession):
        """测试创建战队任务"""
        from datetime import datetime, timedelta
        from app.models.team_task import TeamTaskStatus

        # 创建战队
        captain = await PointsService.get_or_create_user(db_session, "0xcaptain_task")
        await db_session.commit()

        team = await TeamService.create_team(
            db=db_session,
            name="任务战队",
            captain_id=captain.id
        )
        await db_session.commit()

        # 创建任务
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(days=7)

        task = await TeamService.create_team_task(
            db=db_session,
            team_id=team.id,
            title="测试任务",
            task_type="referral",
            target_value=100,
            reward_points=1000,
            start_time=start_time,
            end_time=end_time,
            description="完成100次推荐"
        )
        await db_session.commit()

        # 验证任务
        assert task.team_id == team.id
        assert task.title == "测试任务"
        assert task.target_value == 100
        assert task.current_value == 0
        assert task.status == TeamTaskStatus.ACTIVE
        assert task.progress_percentage == 0.0

    @pytest.mark.asyncio
    async def test_get_team_tasks(self, db_session: AsyncSession):
        """测试获取战队任务列表"""
        from datetime import datetime, timedelta

        # 创建战队
        captain = await PointsService.get_or_create_user(db_session, "0xcaptain_tasklist")
        await db_session.commit()

        team = await TeamService.create_team(
            db=db_session,
            name="任务列表战队",
            captain_id=captain.id
        )
        await db_session.commit()

        # 创建多个任务
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(days=7)

        for i in range(3):
            await TeamService.create_team_task(
                db=db_session,
                team_id=team.id,
                title=f"任务{i}",
                task_type="referral",
                target_value=100 * (i + 1),
                reward_points=1000 * (i + 1),
                start_time=start_time,
                end_time=end_time
            )
        await db_session.commit()

        # 获取任务列表
        tasks = await TeamService.get_team_tasks(db=db_session, team_id=team.id)

        # 验证
        assert len(tasks) == 3
        assert tasks[0].title in ["任务0", "任务1", "任务2"]
