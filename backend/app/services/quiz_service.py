"""
问答系统服务层
"""
from typing import List, Optional, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy import select, func, and_, or_, desc, case
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models import Question, UserAnswer, DailyQuizSession, User
from app.models.quiz import QuestionDifficulty, QuestionSource, QuestionStatus
from app.models.point_transaction import PointTransactionType
from app.services.points_service import PointsService


class QuizService:
    """问答服务类"""

    # ============= 题目管理 =============

    @staticmethod
    async def create_question(
        db: AsyncSession,
        question_text: str,
        option_a: str,
        option_b: str,
        correct_answer: str,
        difficulty: QuestionDifficulty,
        reward_points: int,
        option_c: Optional[str] = None,
        option_d: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source: QuestionSource = QuestionSource.ADMIN,
        submitted_by: Optional[int] = None,
        valid_from: Optional[datetime] = None,
        valid_until: Optional[datetime] = None,
    ) -> Question:
        """创建题目"""
        try:
            # 创建题目
            question = Question(
                question_text=question_text,
                option_a=option_a,
                option_b=option_b,
                option_c=option_c,
                option_d=option_d,
                correct_answer=correct_answer,
                difficulty=difficulty,
                category=category,
                tags=tags,
                reward_points=reward_points,
                source=source,
                submitted_by=submitted_by,
                status=QuestionStatus.ACTIVE if source == QuestionSource.ADMIN else QuestionStatus.PENDING,
                valid_from=valid_from or datetime.now(),
                valid_until=valid_until,
            )

            db.add(question)
            await db.commit()
            await db.refresh(question)

            logger.info(f"✅ 题目创建成功: ID={question.id}, 难度={difficulty.value}, 分类={category}")
            return question

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 题目创建失败: {e}")
            raise

    @staticmethod
    async def get_question(db: AsyncSession, question_id: int) -> Optional[Question]:
        """获取题目详情"""
        try:
            result = await db.execute(
                select(Question).where(Question.id == question_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ 获取题目失败: {e}")
            raise

    @staticmethod
    async def get_questions(
        db: AsyncSession,
        difficulty: Optional[QuestionDifficulty] = None,
        category: Optional[str] = None,
        status: Optional[QuestionStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Question], int]:
        """获取题目列表（分页）"""
        try:
            # 构建查询条件
            conditions = []

            if difficulty:
                conditions.append(Question.difficulty == difficulty)
            if category:
                conditions.append(Question.category == category)
            if status:
                conditions.append(Question.status == status)
            else:
                # 默认只返回激活状态的题目
                conditions.append(Question.status == QuestionStatus.ACTIVE)

            # 时效性检查
            now = datetime.now()
            conditions.append(Question.valid_from <= now)
            conditions.append(
                or_(
                    Question.valid_until.is_(None),
                    Question.valid_until > now
                )
            )

            # 查询总数
            count_query = select(func.count(Question.id)).where(and_(*conditions))
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # 查询数据（按创建时间降序）
            query = (
                select(Question)
                .where(and_(*conditions))
                .order_by(desc(Question.created_at))
                .offset((page - 1) * page_size)
                .limit(page_size)
            )

            result = await db.execute(query)
            questions = list(result.scalars().all())

            logger.info(f"✅ 获取题目列表: 共{total}条, 返回{len(questions)}条")
            return questions, total

        except Exception as e:
            logger.error(f"❌ 获取题目列表失败: {e}")
            raise

    @staticmethod
    async def update_question(
        db: AsyncSession,
        question_id: int,
        **update_data
    ) -> Question:
        """更新题目"""
        try:
            question = await QuizService.get_question(db, question_id)
            if not question:
                raise ValueError(f"题目ID {question_id} 不存在")

            # 更新字段
            for key, value in update_data.items():
                if value is not None and hasattr(question, key):
                    setattr(question, key, value)

            await db.commit()
            await db.refresh(question)

            logger.info(f"✅ 题目更新成功: ID={question_id}")
            return question

        except ValueError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 题目更新失败: {e}")
            raise

    @staticmethod
    async def delete_question(db: AsyncSession, question_id: int) -> None:
        """删除题目（软删除 - 设为禁用状态）"""
        try:
            question = await QuizService.get_question(db, question_id)
            if not question:
                raise ValueError(f"题目ID {question_id} 不存在")

            question.status = QuestionStatus.DISABLED
            await db.commit()

            logger.info(f"✅ 题目已禁用: ID={question_id}")

        except ValueError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 题目删除失败: {e}")
            raise

    @staticmethod
    async def review_question(
        db: AsyncSession,
        question_id: int,
        status: QuestionStatus,
        reviewed_by: int,
        reject_reason: Optional[str] = None
    ) -> Question:
        """审核题目"""
        try:
            question = await QuizService.get_question(db, question_id)
            if not question:
                raise ValueError(f"题目ID {question_id} 不存在")

            question.status = status
            question.reviewed_by = reviewed_by
            question.reviewed_at = datetime.now()

            if status == QuestionStatus.REJECTED:
                question.reject_reason = reject_reason

            await db.commit()
            await db.refresh(question)

            logger.info(f"✅ 题目审核完成: ID={question_id}, 状态={status.value}")
            return question

        except ValueError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 题目审核失败: {e}")
            raise

    # ============= 答题功能 =============

    @staticmethod
    async def get_random_question(
        db: AsyncSession,
        user_id: int,
        difficulty: Optional[QuestionDifficulty] = None,
        category: Optional[str] = None,
        exclude_answered_today: bool = True
    ) -> Optional[Question]:
        """获取随机题目（排除已答过的）"""
        try:
            # 构建查询条件
            conditions = [
                Question.status == QuestionStatus.ACTIVE,
                Question.valid_from <= datetime.now(),
                or_(
                    Question.valid_until.is_(None),
                    Question.valid_until > datetime.now()
                )
            ]

            if difficulty:
                conditions.append(Question.difficulty == difficulty)
            if category:
                conditions.append(Question.category == category)

            # 排除今日已答过的题目
            if exclude_answered_today:
                today = date.today()
                subquery = (
                    select(UserAnswer.question_id)
                    .where(
                        and_(
                            UserAnswer.user_id == user_id,
                            UserAnswer.answer_date == today
                        )
                    )
                )
                conditions.append(Question.id.not_in(subquery))

            # 随机获取一道题目
            query = (
                select(Question)
                .where(and_(*conditions))
                .order_by(func.random())
                .limit(1)
            )

            result = await db.execute(query)
            question = result.scalar_one_or_none()

            if question:
                logger.info(f"✅ 获取随机题目: ID={question.id}, 用户={user_id}")
            else:
                logger.warning(f"⚠️ 无可用题目: 用户={user_id}")

            return question

        except Exception as e:
            logger.error(f"❌ 获取随机题目失败: {e}")
            raise

    @staticmethod
    async def get_daily_session(
        db: AsyncSession,
        user_id: int,
        session_date: Optional[date] = None
    ) -> DailyQuizSession:
        """获取或创建今日答题会话"""
        try:
            if not session_date:
                session_date = date.today()

            # 查询是否存在今日会话
            result = await db.execute(
                select(DailyQuizSession).where(
                    and_(
                        DailyQuizSession.user_id == user_id,
                        DailyQuizSession.session_date == session_date
                    )
                )
            )
            session = result.scalar_one_or_none()

            # 如果不存在，创建新会话
            if not session:
                session = DailyQuizSession(
                    user_id=user_id,
                    session_date=session_date
                )
                db.add(session)
                await db.commit()
                await db.refresh(session)
                logger.info(f"✅ 创建答题会话: 用户={user_id}, 日期={session_date}")

            return session

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 获取答题会话失败: {e}")
            raise

    @staticmethod
    async def check_daily_limit(
        db: AsyncSession,
        user_id: int
    ) -> Tuple[bool, int]:
        """
        检查每日答题次数限制

        Returns:
            (can_answer, remaining_count): 是否可以答题, 剩余次数
        """
        try:
            session = await QuizService.get_daily_session(db, user_id)

            max_questions = 5  # 每日最多5题
            remaining = max_questions - session.questions_answered
            can_answer = remaining > 0

            logger.info(f"✅ 每日答题检查: 用户={user_id}, 已答={session.questions_answered}, 剩余={remaining}")
            return can_answer, max(0, remaining)

        except Exception as e:
            logger.error(f"❌ 检查每日限制失败: {e}")
            raise

    @staticmethod
    async def submit_answer(
        db: AsyncSession,
        user_id: int,
        question_id: int,
        user_answer: str,
        answer_time: Optional[int] = None
    ) -> dict:
        """
        提交答案

        Returns:
            {
                'is_correct': bool,
                'correct_answer': str,
                'points_earned': int,
                'user_answer_id': int
            }
        """
        try:
            # 1. 检查每日答题次数
            can_answer, remaining = await QuizService.check_daily_limit(db, user_id)
            if not can_answer:
                raise ValueError("今日答题次数已用完")

            # 2. 获取题目
            question = await QuizService.get_question(db, question_id)
            if not question:
                raise ValueError(f"题目ID {question_id} 不存在")

            if question.status != QuestionStatus.ACTIVE:
                raise ValueError("题目未激活")

            # 3. 判断答案是否正确
            is_correct = user_answer == question.correct_answer
            points_earned = question.reward_points if is_correct else 0

            # 4. 创建答题记录
            user_answer_record = UserAnswer(
                user_id=user_id,
                question_id=question_id,
                user_answer=user_answer,
                is_correct=is_correct,
                answer_time=answer_time,
                points_earned=points_earned,
                answer_date=date.today()
            )
            db.add(user_answer_record)

            # 5. 更新题目统计
            question.total_answers += 1
            if is_correct:
                question.correct_answers += 1

            # 计算正确率
            if question.total_answers > 0:
                question.accuracy_rate = (question.correct_answers / question.total_answers) * 100

            # 6. 更新今日会话
            session = await QuizService.get_daily_session(db, user_id)
            session.questions_answered += 1
            if is_correct:
                session.correct_count += 1
            session.total_points_earned += points_earned

            # 如果答完5题，标记为完成
            if session.questions_answered >= 5:
                session.completed_at = datetime.now()

            # 7. 发放积分奖励（如果答对）
            if is_correct and points_earned > 0:
                await PointsService.add_user_points(
                    db=db,
                    user_id=user_id,
                    points=points_earned,
                    transaction_type=PointTransactionType.QUIZ_CORRECT,
                    description=f"答题正确奖励 (题目ID: {question_id})",
                    related_question_id=question_id
                )

            # 8. 更新用户统计
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.total_questions_answered += 1
                if is_correct:
                    user.correct_answers += 1

            await db.commit()
            await db.refresh(user_answer_record)

            logger.info(
                f"✅ 答题提交成功: 用户={user_id}, 题目={question_id}, "
                f"正确={is_correct}, 积分={points_earned}"
            )

            return {
                "is_correct": is_correct,
                "correct_answer": question.correct_answer,
                "points_earned": points_earned,
                "user_answer_id": user_answer_record.id,
                "remaining_questions": max(0, 5 - session.questions_answered)
            }

        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 提交答案失败: {e}")
            raise

    # ============= 查询功能 =============

    @staticmethod
    async def get_user_answers(
        db: AsyncSession,
        user_id: int,
        is_correct: Optional[bool] = None,
        answer_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[UserAnswer], int]:
        """获取用户答题记录"""
        try:
            conditions = [UserAnswer.user_id == user_id]

            if is_correct is not None:
                conditions.append(UserAnswer.is_correct == is_correct)
            if answer_date:
                conditions.append(UserAnswer.answer_date == answer_date)

            # 查询总数
            count_query = select(func.count(UserAnswer.id)).where(and_(*conditions))
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # 查询数据（按答题时间降序）
            query = (
                select(UserAnswer)
                .where(and_(*conditions))
                .order_by(desc(UserAnswer.answered_at))
                .offset((page - 1) * page_size)
                .limit(page_size)
            )

            result = await db.execute(query)
            answers = list(result.scalars().all())

            logger.info(f"✅ 获取答题记录: 用户={user_id}, 共{total}条")
            return answers, total

        except Exception as e:
            logger.error(f"❌ 获取答题记录失败: {e}")
            raise

    @staticmethod
    async def get_user_answer(
        db: AsyncSession,
        user_answer_id: int
    ) -> Optional[UserAnswer]:
        """获取单条答题记录"""
        try:
            result = await db.execute(
                select(UserAnswer).where(UserAnswer.id == user_answer_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ 获取答题记录失败: {e}")
            raise

    # ============= 统计功能 =============

    @staticmethod
    async def get_quiz_statistics(
        db: AsyncSession,
        user_id: int
    ) -> dict:
        """获取用户答题统计"""
        try:
            # 1. 用户基本统计（从User表）
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                raise ValueError(f"用户ID {user_id} 不存在")

            total_answered = user.total_questions_answered
            correct_answers = user.correct_answers
            wrong_answers = total_answered - correct_answers
            accuracy_rate = (correct_answers / total_answered * 100) if total_answered > 0 else 0

            # 2. 总获得积分
            total_points_result = await db.execute(
                select(func.sum(UserAnswer.points_earned))
                .where(UserAnswer.user_id == user_id)
            )
            total_points = total_points_result.scalar() or 0

            # 3. 平均答题时间和最后答题时间
            avg_time_result = await db.execute(
                select(
                    func.avg(UserAnswer.answer_time).label('avg_time'),
                    func.max(UserAnswer.answered_at).label('last_answer_date')
                )
                .where(UserAnswer.user_id == user_id)
            )
            avg_stats = avg_time_result.one()
            average_answer_time = float(avg_stats.avg_time) if avg_stats.avg_time else None
            last_answer_date = avg_stats.last_answer_date

            # 4. 连续答题天数（当前和最高）
            current_streak = await QuizService._calculate_streak_days(db, user_id)

            # 计算最高连续天数
            max_streak_result = await db.execute(
                select(func.max(DailyQuizSession.questions_answered))
                .where(DailyQuizSession.user_id == user_id)
            )
            # TODO: 这里简化处理，实际应该计算历史最长连续天数
            max_streak = current_streak

            # 5. 各难度统计
            difficulty_stats_result = await db.execute(
                select(
                    Question.difficulty,
                    func.count(UserAnswer.id).label('answered'),
                    func.sum(case((UserAnswer.is_correct == True, 1), else_=0)).label('correct')
                )
                .join(Question, UserAnswer.question_id == Question.id)
                .where(UserAnswer.user_id == user_id)
                .group_by(Question.difficulty)
            )

            # 初始化难度统计
            easy_answered, easy_correct = 0, 0
            medium_answered, medium_correct = 0, 0
            hard_answered, hard_correct = 0, 0

            for row in difficulty_stats_result.all():
                if row.difficulty == QuestionDifficulty.EASY:
                    easy_answered, easy_correct = row.answered, row.correct
                elif row.difficulty == QuestionDifficulty.MEDIUM:
                    medium_answered, medium_correct = row.answered, row.correct
                elif row.difficulty == QuestionDifficulty.HARD:
                    hard_answered, hard_correct = row.answered, row.correct

            # 6. 最擅长的分类
            favorite_category_result = await db.execute(
                select(
                    Question.category,
                    func.count(UserAnswer.id).label('count')
                )
                .join(Question, UserAnswer.question_id == Question.id)
                .where(UserAnswer.user_id == user_id)
                .group_by(Question.category)
                .order_by(desc('count'))
                .limit(1)
            )
            fav_cat_row = favorite_category_result.first()
            favorite_category = fav_cat_row.category if fav_cat_row else None

            return {
                "user_id": user_id,
                "total_questions_answered": total_answered,
                "correct_answers": correct_answers,
                "wrong_answers": wrong_answers,
                "accuracy_rate": round(accuracy_rate, 2),
                "total_points_earned": int(total_points),
                "average_answer_time": average_answer_time,
                "current_streak_days": current_streak,
                "max_streak_days": max_streak,
                "last_answer_date": last_answer_date.isoformat() if last_answer_date else None,
                "easy_answered": easy_answered,
                "easy_correct": easy_correct,
                "medium_answered": medium_answered,
                "medium_correct": medium_correct,
                "hard_answered": hard_answered,
                "hard_correct": hard_correct,
                "favorite_category": favorite_category
            }

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"❌ 获取答题统计失败: {e}")
            raise

    @staticmethod
    async def _calculate_streak_days(db: AsyncSession, user_id: int) -> int:
        """计算连续答题天数"""
        try:
            # 获取最近的答题日期（降序）
            result = await db.execute(
                select(DailyQuizSession.session_date)
                .where(
                    and_(
                        DailyQuizSession.user_id == user_id,
                        DailyQuizSession.questions_answered > 0
                    )
                )
                .order_by(desc(DailyQuizSession.session_date))
                .limit(100)  # 最多查100天
            )
            dates = [row[0] for row in result.all()]

            if not dates:
                return 0

            # 检查今天或昨天是否有记录
            today = date.today()
            yesterday = today - timedelta(days=1)

            if dates[0] not in [today, yesterday]:
                return 0  # 断签了

            # 计算连续天数
            streak = 1
            current_date = dates[0]

            for next_date in dates[1:]:
                expected_date = current_date - timedelta(days=1)
                if next_date == expected_date:
                    streak += 1
                    current_date = next_date
                else:
                    break

            return streak

        except Exception as e:
            logger.error(f"❌ 计算连续天数失败: {e}")
            return 0

    @staticmethod
    async def get_category_statistics(
        db: AsyncSession,
        user_id: int
    ) -> List[dict]:
        """获取分类统计"""
        try:
            result = await db.execute(
                select(
                    Question.category,
                    func.count(UserAnswer.id).label('total_answered'),
                    func.sum(case((UserAnswer.is_correct == True, 1), else_=0)).label('correct_answers')
                )
                .join(Question, UserAnswer.question_id == Question.id)
                .where(UserAnswer.user_id == user_id)
                .group_by(Question.category)
            )

            stats = []
            for row in result.all():
                total = row.total_answered
                correct = row.correct_answers
                accuracy = (correct / total * 100) if total > 0 else 0

                stats.append({
                    "category": row.category or "未分类",
                    "total_answered": total,
                    "correct_answers": correct,
                    "accuracy_rate": round(accuracy, 2)
                })

            return stats

        except Exception as e:
            logger.error(f"❌ 获取分类统计失败: {e}")
            raise

    @staticmethod
    async def get_difficulty_statistics(
        db: AsyncSession,
        user_id: int
    ) -> List[dict]:
        """获取难度统计"""
        try:
            result = await db.execute(
                select(
                    Question.difficulty,
                    func.count(UserAnswer.id).label('total_answered'),
                    func.sum(case((UserAnswer.is_correct == True, 1), else_=0)).label('correct_answers'),
                    func.avg(UserAnswer.answer_time).label('avg_time')
                )
                .join(Question, UserAnswer.question_id == Question.id)
                .where(UserAnswer.user_id == user_id)
                .group_by(Question.difficulty)
            )

            stats = []
            for row in result.all():
                total = row.total_answered
                correct = row.correct_answers
                accuracy = (correct / total * 100) if total > 0 else 0

                stats.append({
                    "difficulty": row.difficulty,
                    "total_answered": total,
                    "correct_answers": correct,
                    "accuracy_rate": round(accuracy, 2),
                    "average_time": round(float(row.avg_time), 2) if row.avg_time else None
                })

            return stats

        except Exception as e:
            logger.error(f"❌ 获取难度统计失败: {e}")
            raise

    # ============= 排行榜功能 =============

    @staticmethod
    async def get_quiz_ranking(
        db: AsyncSession,
        ranking_type: str = "correct",  # correct/accuracy/points
        period: str = "all_time",  # daily/weekly/all_time
        limit: int = 100,
        user_id: Optional[int] = None
    ) -> dict:
        """
        获取答题排行榜

        Args:
            ranking_type: correct(正确数), accuracy(正确率), points(积分)
            period: daily(今日), weekly(本周), all_time(全部)
        """
        try:
            # 构建时间筛选条件
            time_condition = None
            if period == "daily":
                time_condition = UserAnswer.answer_date == date.today()
            elif period == "weekly":
                week_start = date.today() - timedelta(days=date.today().weekday())
                time_condition = UserAnswer.answer_date >= week_start

            # 构建查询
            if ranking_type == "correct":
                # 按正确数排行
                query = (
                    select(
                        User.id.label('user_id'),
                        User.username,
                        User.avatar_url,
                        func.sum(case((UserAnswer.is_correct == True, 1), else_=0)).label('total_correct'),
                        func.count(UserAnswer.id).label('total_answered'),
                        func.sum(UserAnswer.points_earned).label('total_points')
                    )
                    .join(UserAnswer, User.id == UserAnswer.user_id)
                )

                if time_condition is not None:
                    query = query.where(time_condition)

                query = (
                    query.group_by(User.id, User.username, User.avatar_url)
                    .order_by(desc('total_correct'), desc('total_answered'))
                    .limit(limit)
                )

            elif ranking_type == "accuracy":
                # 按正确率排行（至少答对5题）
                query = (
                    select(
                        User.id.label('user_id'),
                        User.username,
                        User.avatar_url,
                        func.sum(case((UserAnswer.is_correct == True, 1), else_=0)).label('total_correct'),
                        func.count(UserAnswer.id).label('total_answered'),
                        func.sum(UserAnswer.points_earned).label('total_points')
                    )
                    .join(UserAnswer, User.id == UserAnswer.user_id)
                )

                if time_condition is not None:
                    query = query.where(time_condition)

                query = (
                    query.group_by(User.id, User.username, User.avatar_url)
                    .having(func.count(UserAnswer.id) >= 5)  # 至少答5题
                    .order_by(
                        desc(func.sum(case((UserAnswer.is_correct == True, 1), else_=0)) / func.count(UserAnswer.id)),
                        desc('total_correct')
                    )
                    .limit(limit)
                )

            else:  # points
                # 按积分排行
                query = (
                    select(
                        User.id.label('user_id'),
                        User.username,
                        User.avatar_url,
                        func.sum(case((UserAnswer.is_correct == True, 1), else_=0)).label('total_correct'),
                        func.count(UserAnswer.id).label('total_answered'),
                        func.sum(UserAnswer.points_earned).label('total_points')
                    )
                    .join(UserAnswer, User.id == UserAnswer.user_id)
                )

                if time_condition is not None:
                    query = query.where(time_condition)

                query = (
                    query.group_by(User.id, User.username, User.avatar_url)
                    .order_by(desc('total_points'), desc('total_correct'))
                    .limit(limit)
                )

            # 执行查询
            result = await db.execute(query)
            rows = result.all()

            # 构建排行榜数据
            ranking_data = []
            my_rank_data = None

            for idx, row in enumerate(rows, start=1):
                total_answered = row.total_answered
                total_correct = row.total_correct
                accuracy = (total_correct / total_answered * 100) if total_answered > 0 else 0

                item = {
                    "rank": idx,
                    "user_id": row.user_id,
                    "username": row.username,
                    "avatar_url": row.avatar_url,
                    "total_correct": total_correct,
                    "total_answered": total_answered,
                    "accuracy_rate": round(accuracy, 2),
                    "total_points": row.total_points or 0
                }

                ranking_data.append(item)

                # 记录当前用户的排名
                if user_id and row.user_id == user_id:
                    my_rank_data = item

            logger.info(f"✅ 获取排行榜: 类型={ranking_type}, 周期={period}, 共{len(ranking_data)}条")

            return {
                "ranking_type": ranking_type,
                "period": period,
                "data": ranking_data,
                "my_rank": my_rank_data
            }

        except Exception as e:
            logger.error(f"❌ 获取排行榜失败: {e}")
            raise
