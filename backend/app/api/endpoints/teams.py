"""
战队系统API端点
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.team_service import TeamService
from app.schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamDetailResponse,
    TeamListResponse,
    TeamMemberJoinRequest,
    TeamMemberResponse,
    TeamMemberDetailResponse,
    TeamMemberListResponse,
    TeamMemberUpdateRole,
    TeamMemberApproval,
    TeamLeaderboardResponse,
    TeamTaskCreate,
    TeamTaskResponse,
    TeamTaskListResponse,
)
from app.models.team_member import TeamMemberStatus
from app.models.team_task import TeamTaskStatus
from loguru import logger

router = APIRouter()


# ============= 战队CRUD API =============

@router.post("/", response_model=TeamResponse, status_code=201)
async def create_team(
    request: TeamCreate,
    captain_id: int = Query(..., description="队长用户ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    创建战队

    **权限**: 任何用户都可以创建战队
    **限制**:
    - 每个用户只能担任一个战队的队长
    - 战队名称不能重复
    """
    try:
        team = await TeamService.create_team(
            db=db,
            name=request.name,
            captain_id=captain_id,
            description=request.description,
            logo_url=request.logo_url,
            is_public=request.is_public,
            require_approval=request.require_approval,
            max_members=request.max_members
        )
        return team

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建战队失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建战队失败: {str(e)}")


# ============= 战队排行榜 API =============

@router.get("/leaderboard", response_model=TeamLeaderboardResponse)
async def get_team_leaderboard(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取战队排行榜

    **排序**: 按总积分降序
    **权限**: 公开访问
    """
    try:
        leaderboard, total = await TeamService.get_team_leaderboard(
            db=db,
            page=page,
            page_size=page_size
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": leaderboard
        }

    except Exception as e:
        logger.error(f"获取排行榜失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取排行榜失败: {str(e)}")


# ============= 用户战队查询 API =============

@router.get("/user/{user_id}/team", response_model=Optional[TeamResponse])
async def get_user_team(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户所在的战队

    **权限**: 公开访问
    **返回**: 用户当前活跃的战队信息，如果用户未加入任何战队则返回None
    """
    try:
        from sqlalchemy import select
        from app.models.team_member import TeamMember
        from app.models.team import Team

        # 查找用户的活跃战队成员记录
        query = select(TeamMember).where(
            TeamMember.user_id == user_id,
            TeamMember.status == TeamMemberStatus.ACTIVE
        )
        result = await db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            return None

        # 获取战队详情
        team = await TeamService.get_team(db, member.team_id)
        return team

    except Exception as e:
        logger.error(f"获取用户战队失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户战队失败: {str(e)}")


# ============= 战队CRUD API (续) =============

@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取战队详情

    **权限**: 公开访问
    """
    try:
        team = await TeamService.get_team(db, team_id)
        if not team:
            raise HTTPException(status_code=404, detail=f"战队ID {team_id} 不存在")
        return team

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取战队失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取战队失败: {str(e)}")


@router.get("/", response_model=TeamListResponse)
async def get_teams(
    is_public: Optional[bool] = Query(None, description="是否公开"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取战队列表（分页）

    **排序**: 按总积分降序
    **筛选**: 可选择仅显示公开战队
    """
    try:
        teams, total = await TeamService.get_teams(
            db=db,
            is_public=is_public,
            page=page,
            page_size=page_size
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": teams
        }

    except Exception as e:
        logger.error(f"获取战队列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取战队列表失败: {str(e)}")


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    request: TeamUpdate,
    captain_id: int = Query(..., description="操作者用户ID（需为队长）"),
    db: AsyncSession = Depends(get_db)
):
    """
    更新战队信息

    **权限**: 仅队长可操作
    """
    try:
        # 准备更新数据
        update_data = request.model_dump(exclude_unset=True)

        team = await TeamService.update_team(
            db=db,
            team_id=team_id,
            captain_id=captain_id,
            **update_data
        )
        return team

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"更新战队失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新战队失败: {str(e)}")


@router.delete("/{team_id}")
async def disband_team(
    team_id: int,
    captain_id: int = Query(..., description="操作者用户ID（需为队长）"),
    db: AsyncSession = Depends(get_db)
):
    """
    解散战队

    **权限**: 仅队长可操作
    **效果**: 标记为已解散，不会删除数据
    """
    try:
        await TeamService.disband_team(db, team_id, captain_id)
        return {"message": "战队已解散", "team_id": team_id}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"解散战队失败: {e}")
        raise HTTPException(status_code=500, detail=f"解散战队失败: {str(e)}")


# ============= 成员管理 API =============

@router.post("/join", response_model=TeamMemberResponse)
async def join_team(
    request: TeamMemberJoinRequest,
    user_id: int = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    加入战队

    **权限**: 任何用户
    **流程**:
    - 如果战队需要审批：状态为pending，等待队长/管理员审批
    - 如果战队不需要审批：状态为active，直接加入
    """
    try:
        member = await TeamService.join_team(
            db=db,
            team_id=request.team_id,
            user_id=user_id
        )
        return member

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"加入战队失败: {e}")
        raise HTTPException(status_code=500, detail=f"加入战队失败: {str(e)}")


@router.post("/{team_id}/approve", response_model=TeamMemberResponse)
async def approve_member(
    team_id: int,
    request: TeamMemberApproval,
    approver_id: int = Query(..., description="审批人用户ID（需为队长/管理员）"),
    db: AsyncSession = Depends(get_db)
):
    """
    审批成员申请

    **权限**: 队长或管理员
    **操作**:
    - approved=true: 通过申请，成员状态变为active
    - approved=false: 拒绝申请，成员状态变为rejected
    """
    try:
        member = await TeamService.approve_member(
            db=db,
            team_id=team_id,
            user_id=request.user_id,
            approver_id=approver_id,
            approved=request.approved
        )
        return member

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"审批成员失败: {e}")
        raise HTTPException(status_code=500, detail=f"审批成员失败: {str(e)}")


@router.post("/{team_id}/leave")
async def leave_team(
    team_id: int,
    user_id: int = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    离开战队

    **权限**: 仅自己可操作
    **限制**: 队长不能直接离开，需先转让队长职位
    """
    try:
        await TeamService.leave_team(db, team_id, user_id)
        return {"message": "已离开战队", "team_id": team_id, "user_id": user_id}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"离开战队失败: {e}")
        raise HTTPException(status_code=500, detail=f"离开战队失败: {str(e)}")


@router.get("/{team_id}/members", response_model=TeamMemberListResponse)
async def get_team_members(
    team_id: int,
    status: Optional[TeamMemberStatus] = Query(None, description="成员状态筛选"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取战队成员列表

    **权限**: 公开访问
    **筛选**: 可按状态筛选（active/pending/rejected/left）
    **排序**: 按贡献积分降序
    """
    try:
        members = await TeamService.get_team_members(
            db=db,
            team_id=team_id,
            status=status
        )

        # 构建详细成员信息（包含用户信息）
        from sqlalchemy import select
        from app.models import User

        detailed_members = []
        for member in members:
            # 查询用户信息
            result = await db.execute(select(User).where(User.id == member.user_id))
            user = result.scalar_one_or_none()

            member_dict = {
                **member.__dict__,
                "username": user.username if user else None,
                "wallet_address": user.wallet_address if user else None,
                "avatar_url": user.avatar_url if user else None,
            }
            detailed_members.append(member_dict)

        return {
            "total": len(detailed_members),
            "data": detailed_members
        }

    except Exception as e:
        logger.error(f"获取成员列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取成员列表失败: {str(e)}")


@router.put("/{team_id}/members/role", response_model=TeamMemberResponse)
async def update_member_role(
    team_id: int,
    request: TeamMemberUpdateRole,
    captain_id: int = Query(..., description="操作者用户ID（需为队长）"),
    db: AsyncSession = Depends(get_db)
):
    """
    更新成员角色

    **权限**: 仅队长可操作

    **支持的角色**:
    - **member**: 普通成员
    - **admin**: 管理员（可审批成员申请）
    - **captain**: 队长（转让队长职位）

    **队长转让逻辑**:
    - 当new_role为captain时，执行队长转让
    - 原队长自动降为管理员
    - 目标用户成为新队长
    - 战队的captain_id同步更新

    **限制**:
    - 队长不能修改自己的角色（防止自我降权）
    - 目标用户必须是活跃成员
    - 只有队长可以执行此操作
    """
    try:
        # 调用Service层更新角色
        member = await TeamService.update_member_role(
            db=db,
            team_id=team_id,
            user_id=request.user_id,
            new_role=request.role,
            operator_id=captain_id
        )

        return member

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"更新成员角色失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新成员角色失败: {str(e)}")


# ============= 战队任务 API =============

@router.post("/{team_id}/tasks", response_model=TeamTaskResponse)
async def create_team_task(
    team_id: int,
    request: TeamTaskCreate,
    creator_id: int = Query(..., description="创建者用户ID（需为队长/管理员）"),
    db: AsyncSession = Depends(get_db)
):
    """
    创建战队任务

    **权限**: 队长或管理员
    """
    try:
        # TODO: 验证权限（需为队长或管理员）

        task = await TeamService.create_team_task(
            db=db,
            team_id=team_id,
            title=request.title,
            task_type=request.task_type,
            target_value=request.target_value,
            reward_points=request.reward_points,
            start_time=request.start_time,
            end_time=request.end_time,
            description=request.description,
            bonus_points=request.bonus_points
        )
        return task

    except Exception as e:
        logger.error(f"创建战队任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.get("/{team_id}/tasks", response_model=TeamTaskListResponse)
async def get_team_tasks(
    team_id: int,
    status: Optional[TeamTaskStatus] = Query(None, description="任务状态筛选"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取战队任务列表

    **权限**: 公开访问
    **筛选**: 可按任务状态筛选
    **排序**: 按创建时间降序
    """
    try:
        tasks = await TeamService.get_team_tasks(
            db=db,
            team_id=team_id,
            status=status
        )

        return {
            "total": len(tasks),
            "data": tasks
        }

    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


# ============= 奖励池分配 API =============

@router.post("/{team_id}/distribute-rewards")
async def distribute_team_rewards(
    team_id: int,
    captain_id: int = Query(..., description="操作者用户ID（需为队长）"),
    db: AsyncSession = Depends(get_db)
):
    """
    分配战队奖励池

    **权限**: 仅队长可操作
    **机制**: 按成员贡献积分比例分配奖励池
    **效果**:
    - 按贡献比例给所有活跃成员发放积分
    - 清空奖励池
    - 记录分配时间
    """
    try:
        # TODO: 验证是否为队长

        result = await TeamService.distribute_reward_pool(db, team_id)
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"分配奖励池失败: {e}")
        raise HTTPException(status_code=500, detail=f"分配奖励池失败: {str(e)}")
