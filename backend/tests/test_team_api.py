"""
战队API端点测试
"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.services.team_service import TeamService
from app.services.points_service import PointsService
from app.models.team_member import TeamMemberRole, TeamMemberStatus


@pytest.mark.asyncio
async def test_update_member_role_success_to_admin(db_session: AsyncSession, override_get_db):
    """测试更新成员角色成功 - 普通成员升为管理员"""
    # 创建队长和普通成员
    wallet_captain = "0x1111111111111111111111111111111111111111"
    wallet_member = "0x1111222222222222222222222222222222222222"

    captain_user = await PointsService.get_or_create_user(db_session, wallet_captain)
    member_user = await PointsService.get_or_create_user(db_session, wallet_member)

    # 创建战队
    team = await TeamService.create_team(
        db=db_session,
        name="测试战队A",
        captain_id=captain_user.id,
        description="测试战队描述"
    )

    # 成员加入战队
    member = await TeamService.join_team(
        db=db_session,
        team_id=team.id,
        user_id=member_user.id
    )

    await db_session.commit()

    # 队长将成员升为管理员
    request_data = {
        "user_id": member_user.id,
        "role": "admin"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/teams/{team.id}/members/role",
            json=request_data,
            params={"captain_id": captain_user.id}
        )

    # 调试输出
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.json()}")

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == member_user.id
    assert data["role"] == "admin"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_update_member_role_captain_transfer(db_session: AsyncSession, override_get_db):
    """测试队长转让 - 队长将角色转让给管理员"""
    # 创建队长和成员
    wallet_captain = "0x2222222222222222222222222222222222222222"
    wallet_member = "0x2222333333333333333333333333333333333333"

    captain_user = await PointsService.get_or_create_user(db_session, wallet_captain)
    member_user = await PointsService.get_or_create_user(db_session, wallet_member)

    # 创建战队
    team = await TeamService.create_team(
        db=db_session,
        name="测试战队B",
        captain_id=captain_user.id
    )

    # 成员加入
    await TeamService.join_team(
        db=db_session,
        team_id=team.id,
        user_id=member_user.id
    )

    await db_session.commit()

    # 队长转让给成员
    request_data = {
        "user_id": member_user.id,
        "role": "captain"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/teams/{team.id}/members/role",
            json=request_data,
            params={"captain_id": captain_user.id}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == member_user.id
    assert data["role"] == "captain"

    # 验证原队长降为管理员
    from sqlalchemy import select
    from app.models import TeamMember

    result = await db_session.execute(
        select(TeamMember).where(
            TeamMember.team_id == team.id,
            TeamMember.user_id == captain_user.id
        )
    )
    old_captain = result.scalar_one_or_none()
    assert old_captain is not None
    assert old_captain.role == TeamMemberRole.ADMIN


@pytest.mark.asyncio
async def test_update_member_role_permission_denied(db_session: AsyncSession, override_get_db):
    """测试更新成员角色失败 - 非队长操作"""
    # 创建队长和两个成员
    wallet_captain = "0x3333333333333333333333333333333333333333"
    wallet_member1 = "0x3333444444444444444444444444444444444444"
    wallet_member2 = "0x3333555555555555555555555555555555555555"

    captain_user = await PointsService.get_or_create_user(db_session, wallet_captain)
    member1_user = await PointsService.get_or_create_user(db_session, wallet_member1)
    member2_user = await PointsService.get_or_create_user(db_session, wallet_member2)

    # 创建战队
    team = await TeamService.create_team(
        db=db_session,
        name="测试战队C",
        captain_id=captain_user.id
    )

    # 成员加入
    await TeamService.join_team(db=db_session, team_id=team.id, user_id=member1_user.id)
    await TeamService.join_team(db=db_session, team_id=team.id, user_id=member2_user.id)

    await db_session.commit()

    # 普通成员尝试更新另一个成员的角色
    request_data = {
        "user_id": member2_user.id,
        "role": "admin"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/teams/{team.id}/members/role",
            json=request_data,
            params={"captain_id": member1_user.id}  # 非队长操作
        )

    assert response.status_code == 403
    assert "not the captain" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_member_role_self_modification(db_session: AsyncSession, override_get_db):
    """测试更新成员角色失败 - 队长试图修改自己的角色"""
    # 创建队长
    wallet_captain = "0x4444444444444444444444444444444444444444"
    captain_user = await PointsService.get_or_create_user(db_session, wallet_captain)

    # 创建战队
    team = await TeamService.create_team(
        db=db_session,
        name="测试战队D",
        captain_id=captain_user.id
    )

    await db_session.commit()

    # 队长尝试修改自己的角色
    request_data = {
        "user_id": captain_user.id,
        "role": "member"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/teams/{team.id}/members/role",
            json=request_data,
            params={"captain_id": captain_user.id}
        )

    assert response.status_code == 403
    assert "Cannot change your own role" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_member_role_target_not_found(db_session: AsyncSession, override_get_db):
    """测试更新成员角色失败 - 目标用户不在战队中"""
    # 创建队长和非成员用户
    wallet_captain = "0x5555555555555555555555555555555555555555"
    wallet_outsider = "0x9999999999999999999999999999999999999999"

    captain_user = await PointsService.get_or_create_user(db_session, wallet_captain)
    outsider_user = await PointsService.get_or_create_user(db_session, wallet_outsider)

    # 创建战队
    team = await TeamService.create_team(
        db=db_session,
        name="测试战队E",
        captain_id=captain_user.id
    )

    await db_session.commit()

    # 队长尝试更新非成员的角色
    request_data = {
        "user_id": outsider_user.id,
        "role": "admin"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/teams/{team.id}/members/role",
            json=request_data,
            params={"captain_id": captain_user.id}
        )

    assert response.status_code == 404
    assert "not an active member" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_member_role_demote_admin(db_session: AsyncSession, override_get_db):
    """测试降级管理员为普通成员"""
    # 创建队长和成员
    wallet_captain = "0x6666666666666666666666666666666666666666"
    wallet_member = "0x6666777777777777777777777777777777777777"

    captain_user = await PointsService.get_or_create_user(db_session, wallet_captain)
    member_user = await PointsService.get_or_create_user(db_session, wallet_member)

    # 创建战队
    team = await TeamService.create_team(
        db=db_session,
        name="测试战队F",
        captain_id=captain_user.id
    )

    # 成员加入
    await TeamService.join_team(db=db_session, team_id=team.id, user_id=member_user.id)

    # 先升为管理员
    await TeamService.update_member_role(
        db=db_session,
        team_id=team.id,
        user_id=member_user.id,
        new_role=TeamMemberRole.ADMIN,
        operator_id=captain_user.id
    )

    await db_session.commit()

    # 再降为普通成员
    request_data = {
        "user_id": member_user.id,
        "role": "member"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/teams/{team.id}/members/role",
            json=request_data,
            params={"captain_id": captain_user.id}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == member_user.id
    assert data["role"] == "member"
