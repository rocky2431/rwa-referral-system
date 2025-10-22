"""
问答系统 Pydantic Schemas
"""
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.quiz import QuestionDifficulty, QuestionSource, QuestionStatus


# ============= 题目配置 Schemas =============

class QuestionBase(BaseModel):
    """题目基础信息"""
    question_text: str = Field(..., min_length=5, description="题目文本")
    option_a: str = Field(..., min_length=1, max_length=200, description="选项A")
    option_b: str = Field(..., min_length=1, max_length=200, description="选项B")
    option_c: Optional[str] = Field(None, max_length=200, description="选项C")
    option_d: Optional[str] = Field(None, max_length=200, description="选项D")
    correct_answer: str = Field(..., description="正确答案 (A/B/C/D)")
    difficulty: QuestionDifficulty = Field(..., description="难度")
    category: Optional[str] = Field(None, max_length=50, description="分类")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    reward_points: int = Field(..., gt=0, description="奖励积分")
    valid_from: Optional[datetime] = Field(None, description="生效时间")
    valid_until: Optional[datetime] = Field(None, description="失效时间")

    @field_validator('correct_answer')
    @classmethod
    def validate_correct_answer(cls, v):
        """验证正确答案格式"""
        if v not in ['A', 'B', 'C', 'D']:
            raise ValueError('correct_answer must be A, B, C, or D')
        return v

    @field_validator('valid_until')
    @classmethod
    def check_time_range(cls, v, info):
        """验证时间范围"""
        if v and 'valid_from' in info.data and info.data['valid_from']:
            if v <= info.data['valid_from']:
                raise ValueError('valid_until must be after valid_from')
        return v


class QuestionCreate(QuestionBase):
    """创建题目请求"""
    source: QuestionSource = Field(QuestionSource.ADMIN, description="题目来源")
    submitted_by: Optional[int] = Field(None, gt=0, description="提交者ID")


class QuestionUpdate(BaseModel):
    """更新题目信息"""
    question_text: Optional[str] = Field(None, min_length=5)
    option_a: Optional[str] = Field(None, min_length=1, max_length=200)
    option_b: Optional[str] = Field(None, min_length=1, max_length=200)
    option_c: Optional[str] = Field(None, max_length=200)
    option_d: Optional[str] = Field(None, max_length=200)
    correct_answer: Optional[str] = None
    difficulty: Optional[QuestionDifficulty] = None
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None
    reward_points: Optional[int] = Field(None, gt=0)
    status: Optional[QuestionStatus] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    @field_validator('correct_answer')
    @classmethod
    def validate_correct_answer(cls, v):
        """验证正确答案格式"""
        if v and v not in ['A', 'B', 'C', 'D']:
            raise ValueError('correct_answer must be A, B, C, or D')
        return v


class QuestionReview(BaseModel):
    """审核题目请求"""
    status: QuestionStatus = Field(..., description="审核结果")
    reviewed_by: int = Field(..., gt=0, description="审核者ID")
    reject_reason: Optional[str] = Field(None, description="拒绝原因")


class QuestionResponse(BaseModel):
    """题目响应（隐藏正确答案）"""
    id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: Optional[str]
    option_d: Optional[str]
    difficulty: QuestionDifficulty
    category: Optional[str]
    tags: Optional[List[str]]
    reward_points: int
    source: QuestionSource
    status: QuestionStatus
    total_answers: int
    correct_answers: int
    accuracy_rate: Optional[float]
    valid_from: datetime
    valid_until: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionDetailResponse(QuestionResponse):
    """题目详细响应（含正确答案 - 仅管理员）"""
    correct_answer: str
    submitted_by: Optional[int]
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    reject_reason: Optional[str]


class QuestionListResponse(BaseModel):
    """题目列表响应（分页）"""
    total: int
    page: int
    page_size: int
    data: List[QuestionResponse]


# ============= 答题记录 Schemas =============

class AnswerSubmit(BaseModel):
    """提交答案请求"""
    question_id: int = Field(..., gt=0, description="题目ID")
    user_answer: str = Field(..., description="用户答案 (A/B/C/D)")
    answer_time: Optional[int] = Field(None, ge=0, description="答题耗时(秒)")

    @field_validator('user_answer')
    @classmethod
    def validate_user_answer(cls, v):
        """验证用户答案格式"""
        if v not in ['A', 'B', 'C', 'D']:
            raise ValueError('user_answer must be A, B, C, or D')
        return v


class AnswerResult(BaseModel):
    """答题结果响应"""
    is_correct: bool = Field(..., description="是否正确")
    correct_answer: str = Field(..., description="正确答案")
    points_earned: int = Field(..., description="获得积分")
    explanation: Optional[str] = Field(None, description="解析")


class UserAnswerResponse(BaseModel):
    """答题记录响应"""
    id: int
    user_id: int
    question_id: int
    user_answer: str
    is_correct: bool
    answer_time: Optional[int]
    answered_at: datetime
    points_earned: int
    answer_date: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserAnswerDetailResponse(UserAnswerResponse):
    """答题记录详细响应（含题目信息）"""
    question_text: Optional[str] = None
    correct_answer: Optional[str] = None
    difficulty: Optional[QuestionDifficulty] = None
    category: Optional[str] = None


class UserAnswerListResponse(BaseModel):
    """答题记录列表响应"""
    total: int
    page: int
    page_size: int
    data: List[UserAnswerDetailResponse]


# ============= 答题会话 Schemas =============

class DailyQuizSessionResponse(BaseModel):
    """每日答题会话响应"""
    id: int
    user_id: int
    session_date: date
    questions_answered: int
    correct_count: int
    total_points_earned: int
    accuracy_rate: float
    is_completed: bool
    started_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuizStatistics(BaseModel):
    """用户答题统计"""
    user_id: int
    total_questions_answered: int = Field(..., description="总答题数")
    total_correct_answers: int = Field(..., description="总正确数")
    overall_accuracy_rate: float = Field(..., description="总体正确率")
    total_points_earned: int = Field(..., description="总获得积分")
    total_sessions: int = Field(..., description="总会话数")
    completed_sessions: int = Field(..., description="完成会话数")
    current_streak_days: int = Field(..., description="连续答题天数")


class CategoryStatistics(BaseModel):
    """分类统计"""
    category: str
    total_questions: int
    total_answered: int
    correct_answers: int
    accuracy_rate: float


class DifficultyStatistics(BaseModel):
    """难度统计"""
    difficulty: QuestionDifficulty
    total_answered: int
    correct_answers: int
    accuracy_rate: float
    average_time: Optional[float]  # 平均答题时间(秒)


# ============= 排行榜 Schemas =============

class QuizRankingItem(BaseModel):
    """答题排行榜项"""
    rank: int
    user_id: int
    username: Optional[str]
    avatar_url: Optional[str]
    total_correct: int
    total_answered: int
    accuracy_rate: float
    total_points: int


class QuizRankingResponse(BaseModel):
    """答题排行榜响应"""
    ranking_type: str = Field(..., description="排行榜类型 (correct/accuracy/points)")
    period: str = Field(..., description="周期 (daily/weekly/all_time)")
    data: List[QuizRankingItem]
    my_rank: Optional[QuizRankingItem] = None
