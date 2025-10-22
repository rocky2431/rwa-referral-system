"""
任务系统API端点
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.task_service import TaskService
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    UserTaskCreate,
    UserTaskProgress,
    UserTaskClaim,
    UserTaskResponse,
    UserTaskDetailResponse,
    UserTaskListResponse,
    TaskStatistics,
    UserTaskSummary,
)
from app.models.task import TaskType, UserTaskStatus
from loguru import logger

router = APIRouter()


# ============= 任务配置 API =============

@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    request: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建任务配置

    **权限**: 管理员
    **注意**: 生产环境需要添加管理员权限验证
    """
    try:
        task = await TaskService.create_task(
            db=db,
            **request.model_dump()
        )
        return task

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取任务配置详情

    **权限**: 公开访问
    """
    try:
        task = await TaskService.get_task(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"任务ID {task_id} 不存在")
        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务失败: {str(e)}")


@router.get("/", response_model=TaskListResponse)
async def get_tasks(
    task_type: Optional[TaskType] = Query(None, description="任务类型"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    is_visible: Optional[bool] = Query(None, description="是否可见"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取任务列表（分页）

    **排序**: 按优先级降序、排序顺序升序
    **筛选**: 可按任务类型、激活状态、可见状态筛选
    **时间**: 自动筛选当前时间在有效期内的任务
    """
    try:
        tasks, total = await TaskService.get_tasks(
            db=db,
            task_type=task_type,
            is_active=is_active,
            is_visible=is_visible,
            page=page,
            page_size=page_size
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": tasks
        }

    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    request: TaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新任务配置

    **权限**: 管理员
    **注意**: 生产环境需要添加管理员权限验证
    """
    try:
        # 准备更新数据
        update_data = request.model_dump(exclude_unset=True)

        task = await TaskService.update_task(
            db=db,
            task_id=task_id,
            **update_data
        )
        return task

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新任务失败: {str(e)}")


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除任务配置（软删除）

    **权限**: 管理员
    **注意**: 生产环境需要添加管理员权限验证
    **效果**: 将任务设置为不激活和不可见
    """
    try:
        await TaskService.delete_task(db, task_id)
        return {"message": "任务已删除", "task_id": task_id}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")


# ============= 用户任务 API =============

@router.post("/user-tasks", response_model=UserTaskResponse)
async def assign_task_to_user(
    request: UserTaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    用户领取任务

    **权限**: 任何已登录用户
    **验证**:
    - 任务是否存在且激活
    - 用户等级是否满足要求
    - 用户是否已领取该任务
    - 完成次数是否超限
    """
    try:
        user_task = await TaskService.assign_task_to_user(
            db=db,
            user_id=request.user_id,
            task_id=request.task_id
        )
        return user_task

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"领取任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"领取任务失败: {str(e)}")


@router.put("/user-tasks/{user_task_id}/progress", response_model=UserTaskResponse)
async def update_task_progress(
    user_task_id: int,
    request: UserTaskProgress,
    db: AsyncSession = Depends(get_db)
):
    """
    更新任务进度

    **权限**: 任务所属用户或系统
    **注意**: 生产环境需要验证操作者权限
    """
    try:
        user_task = await TaskService.update_task_progress(
            db=db,
            user_task_id=user_task_id,
            progress_delta=request.progress_delta
        )
        return user_task

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新任务进度失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新任务进度失败: {str(e)}")


@router.post("/user-tasks/{user_task_id}/claim")
async def claim_task_reward(
    user_task_id: int,
    user_id: int = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    领取任务奖励

    **权限**: 任务所属用户
    **条件**: 任务状态为已完成且未领取
    **效果**: 发放积分和经验奖励
    """
    try:
        # TODO: 验证user_id是否为任务所属用户
        result = await TaskService.claim_task_reward(
            db=db,
            user_task_id=user_task_id
        )
        return {
            "message": "奖励领取成功",
            "user_task_id": user_task_id,
            **result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"领取奖励失败: {e}")
        raise HTTPException(status_code=500, detail=f"领取奖励失败: {str(e)}")


@router.get("/user-tasks/user/{user_id}", response_model=UserTaskListResponse)
async def get_user_tasks(
    user_id: int,
    status: Optional[UserTaskStatus] = Query(None, description="任务状态筛选"),
    task_type: Optional[TaskType] = Query(None, description="任务类型筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的任务列表（分页）

    **权限**: 用户本人或管理员
    **排序**: 按创建时间降序
    **筛选**: 可按任务状态和类型筛选
    """
    try:
        user_tasks, total = await TaskService.get_user_tasks(
            db=db,
            user_id=user_id,
            status=status,
            task_type=task_type,
            page=page,
            page_size=page_size
        )

        # 构建详细任务信息（包含任务配置）
        from sqlalchemy import select
        from app.models import Task

        detailed_tasks = []
        for user_task in user_tasks:
            # 查询任务配置
            result = await db.execute(select(Task).where(Task.id == user_task.task_id))
            task = result.scalar_one_or_none()

            # 计算进度百分比
            progress_percentage = round((user_task.current_value / user_task.target_value) * 100, 2) if user_task.target_value > 0 else 0
            # 判断是否完成
            is_completed = user_task.status in [UserTaskStatus.COMPLETED, UserTaskStatus.CLAIMED]

            task_dict = {
                **user_task.__dict__,
                "progress_percentage": progress_percentage,
                "is_completed": is_completed,
                "task_title": task.title if task else None,
                "task_description": task.description if task else None,
                "task_icon_url": task.icon_url if task else None,
                "task_type": task.task_type if task else None,
            }
            detailed_tasks.append(task_dict)

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": detailed_tasks
        }

    except Exception as e:
        logger.error(f"获取用户任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户任务列表失败: {str(e)}")


@router.get("/user-tasks/{user_id}/task/{task_id}", response_model=UserTaskResponse)
async def get_user_task(
    user_id: int,
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的特定任务

    **权限**: 用户本人或管理员
    **返回**: 最新的进行中或已完成的任务记录
    """
    try:
        user_task = await TaskService.get_user_task(
            db=db,
            user_id=user_id,
            task_id=task_id
        )

        if not user_task:
            raise HTTPException(
                status_code=404,
                detail=f"用户 {user_id} 的任务 {task_id} 不存在"
            )

        return user_task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户任务失败: {str(e)}")


# ============= 任务统计 API =============

@router.get("/{task_id}/statistics", response_model=TaskStatistics)
async def get_task_statistics(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取任务统计信息

    **权限**: 公开访问
    **数据**: 参与人数、完成人数、完成率、总发放奖励等
    """
    try:
        stats = await TaskService.get_task_statistics(db, task_id)
        return stats

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取任务统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务统计失败: {str(e)}")


@router.get("/user-tasks/user/{user_id}/summary", response_model=UserTaskSummary)
async def get_user_task_summary(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户任务汇总

    **权限**: 用户本人或管理员
    **数据**: 总任务数、各状态任务数、总获得积分和经验
    """
    try:
        summary = await TaskService.get_user_task_summary(db, user_id)
        return summary

    except Exception as e:
        logger.error(f"获取用户任务汇总失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户任务汇总失败: {str(e)}")


# ============= 自动任务触发 API =============

@router.post("/user-tasks/auto-assign/{user_id}")
async def auto_assign_tasks(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    为用户自动分配所有AUTO触发类型的任务

    **权限**: 系统内部调用
    **场景**: 用户注册、每日登录等
    **注意**: 生产环境建议限制调用来源
    """
    try:
        assigned_tasks = await TaskService.auto_assign_tasks(db, user_id)

        return {
            "message": "自动分配任务完成",
            "user_id": user_id,
            "assigned_count": len(assigned_tasks),
            "tasks": [
                {"user_task_id": ut.id, "task_id": ut.task_id}
                for ut in assigned_tasks
            ]
        }

    except Exception as e:
        logger.error(f"自动分配任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"自动分配任务失败: {str(e)}")
