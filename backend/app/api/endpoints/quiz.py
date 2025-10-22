"""
问答系统API端点
"""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.quiz_service import QuizService
from app.schemas.quiz import (
    QuestionCreate,
    QuestionUpdate,
    QuestionReview,
    QuestionResponse,
    QuestionDetailResponse,
    QuestionListResponse,
    AnswerSubmit,
    AnswerResult,
    UserAnswerResponse,
    UserAnswerDetailResponse,
    UserAnswerListResponse,
    DailyQuizSessionResponse,
    QuizStatistics,
    CategoryStatistics,
    DifficultyStatistics,
    QuizRankingResponse,
)
from app.models.quiz import QuestionDifficulty, QuestionStatus
from loguru import logger

router = APIRouter()


# ============= 题目管理 API =============

@router.post("/questions", response_model=QuestionDetailResponse, status_code=201)
async def create_question(
    request: QuestionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建题目

    **权限**: 管理员
    **注意**: 生产环境需要添加管理员权限验证
    """
    try:
        question = await QuizService.create_question(
            db=db,
            **request.model_dump()
        )
        return question

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建题目失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建题目失败: {str(e)}")


@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取题目详情（不包含正确答案）

    **权限**: 公开访问
    """
    try:
        question = await QuizService.get_question(db, question_id)
        if not question:
            raise HTTPException(status_code=404, detail=f"题目ID {question_id} 不存在")
        return question

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取题目失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取题目失败: {str(e)}")


@router.get("/questions/{question_id}/detail", response_model=QuestionDetailResponse)
async def get_question_detail(
    question_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取题目详细信息（包含正确答案 - 仅管理员）

    **权限**: 管理员
    **注意**: 生产环境需要添加管理员权限验证
    """
    try:
        question = await QuizService.get_question(db, question_id)
        if not question:
            raise HTTPException(status_code=404, detail=f"题目ID {question_id} 不存在")
        return question

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取题目详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取题目详情失败: {str(e)}")


@router.get("/questions", response_model=QuestionListResponse)
async def get_questions(
    difficulty: Optional[QuestionDifficulty] = Query(None, description="难度筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    status: Optional[QuestionStatus] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取题目列表（分页）

    **排序**: 按创建时间降序
    **筛选**: 可按难度、分类、状态筛选
    **时效**: 自动筛选当前时间在有效期内的题目
    """
    try:
        questions, total = await QuizService.get_questions(
            db=db,
            difficulty=difficulty,
            category=category,
            status=status,
            page=page,
            page_size=page_size
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": questions
        }

    except Exception as e:
        logger.error(f"获取题目列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取题目列表失败: {str(e)}")


@router.put("/questions/{question_id}", response_model=QuestionDetailResponse)
async def update_question(
    question_id: int,
    request: QuestionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新题目

    **权限**: 管理员
    **注意**: 生产环境需要添加管理员权限验证
    """
    try:
        update_data = request.model_dump(exclude_unset=True)
        question = await QuizService.update_question(
            db=db,
            question_id=question_id,
            **update_data
        )
        return question

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新题目失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新题目失败: {str(e)}")


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除题目（软删除 - 设为禁用状态）

    **权限**: 管理员
    **注意**: 生产环境需要添加管理员权限验证
    """
    try:
        await QuizService.delete_question(db, question_id)
        return {"message": "题目已删除", "question_id": question_id}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"删除题目失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除题目失败: {str(e)}")


@router.post("/questions/{question_id}/review", response_model=QuestionDetailResponse)
async def review_question(
    question_id: int,
    request: QuestionReview,
    db: AsyncSession = Depends(get_db)
):
    """
    审核题目

    **权限**: 管理员
    **注意**: 生产环境需要添加管理员权限验证
    """
    try:
        question = await QuizService.review_question(
            db=db,
            question_id=question_id,
            status=request.status,
            reviewed_by=request.reviewed_by,
            reject_reason=request.reject_reason
        )
        return question

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"审核题目失败: {e}")
        raise HTTPException(status_code=500, detail=f"审核题目失败: {str(e)}")


# ============= 答题 API =============

@router.get("/random", response_model=QuestionResponse)
async def get_random_question(
    user_id: int = Query(..., description="用户ID"),
    difficulty: Optional[QuestionDifficulty] = Query(None, description="难度筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    exclude_answered_today: bool = Query(True, description="排除今日已答"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取随机题目

    **权限**: 已登录用户
    **特性**: 自动排除今日已答过的题目
    """
    try:
        question = await QuizService.get_random_question(
            db=db,
            user_id=user_id,
            difficulty=difficulty,
            category=category,
            exclude_answered_today=exclude_answered_today
        )

        if not question:
            raise HTTPException(status_code=404, detail="暂无可用题目")

        return question

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取随机题目失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取随机题目失败: {str(e)}")


@router.post("/submit", response_model=AnswerResult)
async def submit_answer(
    user_id: int = Query(..., description="用户ID"),
    request: AnswerSubmit = ...,
    db: AsyncSession = Depends(get_db)
):
    """
    提交答案

    **权限**: 已登录用户
    **限制**: 每日最多5题
    **奖励**: 答对自动发放积分
    """
    try:
        result = await QuizService.submit_answer(
            db=db,
            user_id=user_id,
            question_id=request.question_id,
            user_answer=request.user_answer,
            answer_time=request.answer_time
        )

        return {
            "is_correct": result["is_correct"],
            "correct_answer": result["correct_answer"],
            "points_earned": result["points_earned"],
            "explanation": None  # 可以添加题目解析
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"提交答案失败: {e}")
        raise HTTPException(status_code=500, detail=f"提交答案失败: {str(e)}")


@router.get("/daily-session", response_model=DailyQuizSessionResponse)
async def get_daily_session(
    user_id: int = Query(..., description="用户ID"),
    session_date: Optional[date] = Query(None, description="会话日期"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取每日答题会话

    **权限**: 用户本人
    **说明**: 如果不存在会自动创建
    """
    try:
        session = await QuizService.get_daily_session(
            db=db,
            user_id=user_id,
            session_date=session_date
        )
        return session

    except Exception as e:
        logger.error(f"获取答题会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取答题会话失败: {str(e)}")


@router.get("/daily-limit")
async def check_daily_limit(
    user_id: int = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    检查每日答题次数限制

    **权限**: 用户本人
    **返回**: 是否可答题、剩余次数
    """
    try:
        can_answer, remaining = await QuizService.check_daily_limit(db, user_id)

        return {
            "can_answer": can_answer,
            "remaining_count": remaining,
            "max_questions_per_day": 5
        }

    except Exception as e:
        logger.error(f"检查每日限制失败: {e}")
        raise HTTPException(status_code=500, detail=f"检查每日限制失败: {str(e)}")


# ============= 答题记录 API =============

@router.get("/user-answers/user/{user_id}", response_model=UserAnswerListResponse)
async def get_user_answers(
    user_id: int,
    is_correct: Optional[bool] = Query(None, description="筛选正确/错误"),
    answer_date: Optional[date] = Query(None, description="答题日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户答题记录（分页）

    **权限**: 用户本人或管理员
    **排序**: 按答题时间降序
    """
    try:
        answers, total = await QuizService.get_user_answers(
            db=db,
            user_id=user_id,
            is_correct=is_correct,
            answer_date=answer_date,
            page=page,
            page_size=page_size
        )

        # 构建详细记录（包含题目信息）
        from sqlalchemy import select
        from app.models import Question

        detailed_answers = []
        for answer in answers:
            # 查询题目信息
            result = await db.execute(select(Question).where(Question.id == answer.question_id))
            question = result.scalar_one_or_none()

            answer_dict = {
                **answer.__dict__,
                "question_text": question.question_text if question else None,
                "correct_answer": question.correct_answer if question else None,
                "difficulty": question.difficulty if question else None,
                "category": question.category if question else None,
            }
            detailed_answers.append(answer_dict)

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": detailed_answers
        }

    except Exception as e:
        logger.error(f"获取答题记录失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取答题记录失败: {str(e)}")


@router.get("/user-answers/{answer_id}", response_model=UserAnswerResponse)
async def get_user_answer(
    answer_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取单条答题记录

    **权限**: 用户本人或管理员
    """
    try:
        answer = await QuizService.get_user_answer(db, answer_id)
        if not answer:
            raise HTTPException(status_code=404, detail=f"答题记录ID {answer_id} 不存在")
        return answer

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取答题记录失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取答题记录失败: {str(e)}")


# ============= 统计 API =============

@router.get("/statistics/user/{user_id}", response_model=QuizStatistics)
async def get_quiz_statistics(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户答题统计

    **权限**: 用户本人或管理员
    **数据**: 总答题数、正确率、总积分、连续天数等
    """
    try:
        stats = await QuizService.get_quiz_statistics(db, user_id)
        return stats

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取答题统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取答题统计失败: {str(e)}")


@router.get("/statistics/category/{user_id}", response_model=list[CategoryStatistics])
async def get_category_statistics(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户分类统计

    **权限**: 用户本人或管理员
    **数据**: 各分类的答题数、正确率
    """
    try:
        stats = await QuizService.get_category_statistics(db, user_id)
        return stats

    except Exception as e:
        logger.error(f"获取分类统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分类统计失败: {str(e)}")


@router.get("/statistics/difficulty/{user_id}", response_model=list[DifficultyStatistics])
async def get_difficulty_statistics(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户难度统计

    **权限**: 用户本人或管理员
    **数据**: 各难度的答题数、正确率、平均耗时
    """
    try:
        stats = await QuizService.get_difficulty_statistics(db, user_id)
        return stats

    except Exception as e:
        logger.error(f"获取难度统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取难度统计失败: {str(e)}")


# ============= 排行榜 API =============

@router.get("/ranking", response_model=QuizRankingResponse)
async def get_quiz_ranking(
    ranking_type: str = Query("correct", description="排行类型: correct/accuracy/points"),
    period: str = Query("all_time", description="周期: daily/weekly/all_time"),
    limit: int = Query(100, ge=1, le=500, description="排行榜人数"),
    user_id: Optional[int] = Query(None, description="用户ID（返回我的排名）"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取答题排行榜

    **排行类型**:
    - correct: 按正确数排行
    - accuracy: 按正确率排行（至少答5题）
    - points: 按获得积分排行

    **周期**:
    - daily: 今日
    - weekly: 本周
    - all_time: 全部

    **权限**: 公开访问
    """
    try:
        if ranking_type not in ["correct", "accuracy", "points"]:
            raise HTTPException(status_code=400, detail="无效的排行类型")

        if period not in ["daily", "weekly", "all_time"]:
            raise HTTPException(status_code=400, detail="无效的周期")

        ranking = await QuizService.get_quiz_ranking(
            db=db,
            ranking_type=ranking_type,
            period=period,
            limit=limit,
            user_id=user_id
        )

        return ranking

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取排行榜失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取排行榜失败: {str(e)}")
