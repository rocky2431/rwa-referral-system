"""
问答系统服务层测试
"""
import pytest
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.quiz_service import QuizService
from app.services.points_service import PointsService
from app.models.quiz import QuestionDifficulty, QuestionSource, QuestionStatus


class TestQuestionManagement:
    """题目管理测试"""

    @pytest.mark.asyncio
    async def test_create_question(self, db_session: AsyncSession):
        """测试创建题目"""
        question = await QuizService.create_question(
            db=db_session,
            question_text="什么是区块链？",
            option_a="分布式账本技术",
            option_b="中心化数据库",
            option_c="云计算技术",
            option_d="人工智能",
            correct_answer="A",
            difficulty=QuestionDifficulty.EASY,
            category="Web3基础",
            reward_points=10
        )
        await db_session.commit()

        assert question.id is not None
        assert question.question_text == "什么是区块链？"
        assert question.correct_answer == "A"
        assert question.difficulty == QuestionDifficulty.EASY
        assert question.status == QuestionStatus.ACTIVE
        assert question.reward_points == 10

    @pytest.mark.asyncio
    async def test_get_question(self, db_session: AsyncSession):
        """测试获取题目详情"""
        # 创建题目
        question = await QuizService.create_question(
            db=db_session,
            question_text="什么是DeFi？",
            option_a="去中心化金融",
            option_b="传统金融",
            correct_answer="A",
            difficulty=QuestionDifficulty.MEDIUM,
            reward_points=15
        )
        await db_session.commit()

        # 获取题目
        retrieved = await QuizService.get_question(db_session, question.id)
        assert retrieved is not None
        assert retrieved.id == question.id
        assert retrieved.question_text == "什么是DeFi？"

    @pytest.mark.asyncio
    async def test_get_questions(self, db_session: AsyncSession):
        """测试获取题目列表"""
        # 创建多个题目
        for i in range(3):
            await QuizService.create_question(
                db=db_session,
                question_text=f"题目{i+1}",
                option_a="选项A",
                option_b="选项B",
                correct_answer="A",
                difficulty=QuestionDifficulty.EASY if i < 2 else QuestionDifficulty.HARD,
                category="测试分类" if i < 2 else "其他分类",
                reward_points=10
            )
        await db_session.commit()

        # 获取所有题目
        questions, total = await QuizService.get_questions(
            db=db_session,
            page=1,
            page_size=10
        )
        assert total >= 3
        assert len(questions) >= 3

        # 按难度筛选
        easy_questions, easy_total = await QuizService.get_questions(
            db=db_session,
            difficulty=QuestionDifficulty.EASY,
            page=1,
            page_size=10
        )
        assert easy_total >= 2

        # 按分类筛选
        category_questions, category_total = await QuizService.get_questions(
            db=db_session,
            category="测试分类",
            page=1,
            page_size=10
        )
        assert category_total >= 2

    @pytest.mark.asyncio
    async def test_update_question(self, db_session: AsyncSession):
        """测试更新题目"""
        question = await QuizService.create_question(
            db=db_session,
            question_text="原始题目",
            option_a="选项A",
            option_b="选项B",
            correct_answer="A",
            difficulty=QuestionDifficulty.EASY,
            reward_points=10
        )
        await db_session.commit()

        # 更新题目
        updated = await QuizService.update_question(
            db=db_session,
            question_id=question.id,
            question_text="更新后的题目",
            difficulty=QuestionDifficulty.HARD,
            reward_points=20
        )
        await db_session.commit()

        assert updated.question_text == "更新后的题目"
        assert updated.difficulty == QuestionDifficulty.HARD
        assert updated.reward_points == 20

    @pytest.mark.asyncio
    async def test_delete_question(self, db_session: AsyncSession):
        """测试删除题目（软删除）"""
        question = await QuizService.create_question(
            db=db_session,
            question_text="待删除题目",
            option_a="选项A",
            option_b="选项B",
            correct_answer="A",
            difficulty=QuestionDifficulty.EASY,
            reward_points=10
        )
        await db_session.commit()

        # 删除题目
        await QuizService.delete_question(db_session, question.id)
        await db_session.commit()

        # 验证状态变为禁用
        deleted = await QuizService.get_question(db_session, question.id)
        assert deleted.status == QuestionStatus.DISABLED

    @pytest.mark.asyncio
    async def test_review_question(self, db_session: AsyncSession):
        """测试审核题目"""
        # 创建用户提交的题目
        user = await PointsService.get_or_create_user(db_session, "0xreviewer")
        await db_session.commit()

        question = await QuizService.create_question(
            db=db_session,
            question_text="用户提交的题目",
            option_a="选项A",
            option_b="选项B",
            correct_answer="A",
            difficulty=QuestionDifficulty.EASY,
            reward_points=10,
            source=QuestionSource.USER_SUBMIT,
            submitted_by=user.id
        )
        await db_session.commit()

        assert question.status == QuestionStatus.PENDING

        # 审核通过
        reviewed = await QuizService.review_question(
            db=db_session,
            question_id=question.id,
            status=QuestionStatus.APPROVED,
            reviewed_by=user.id
        )
        await db_session.commit()

        assert reviewed.status == QuestionStatus.APPROVED
        assert reviewed.reviewed_by == user.id
        assert reviewed.reviewed_at is not None


class TestQuizFeatures:
    """答题功能测试"""

    @pytest.mark.asyncio
    async def test_get_random_question(self, db_session: AsyncSession):
        """测试获取随机题目"""
        user = await PointsService.get_or_create_user(db_session, "0xquiz_user")
        await db_session.commit()

        # 创建题目
        for i in range(5):
            await QuizService.create_question(
                db=db_session,
                question_text=f"随机题目{i+1}",
                option_a="选项A",
                option_b="选项B",
                correct_answer="A",
                difficulty=QuestionDifficulty.EASY,
                reward_points=10
            )
        await db_session.commit()

        # 获取随机题目
        question = await QuizService.get_random_question(
            db=db_session,
            user_id=user.id
        )

        assert question is not None
        assert question.status == QuestionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_submit_answer_correct(self, db_session: AsyncSession):
        """测试提交正确答案"""
        user = await PointsService.get_or_create_user(db_session, "0xanswer_user")
        await db_session.commit()

        # 创建题目
        question = await QuizService.create_question(
            db=db_session,
            question_text="测试题目",
            option_a="正确答案",
            option_b="错误答案",
            correct_answer="A",
            difficulty=QuestionDifficulty.EASY,
            reward_points=20
        )
        await db_session.commit()

        # 提交正确答案
        result = await QuizService.submit_answer(
            db=db_session,
            user_id=user.id,
            question_id=question.id,
            user_answer="A",
            answer_time=15
        )
        await db_session.commit()

        assert result["is_correct"] is True
        assert result["correct_answer"] == "A"
        assert result["points_earned"] == 20
        assert result["user_answer_id"] is not None

        # 验证统计更新
        updated_question = await QuizService.get_question(db_session, question.id)
        assert updated_question.total_answers == 1
        assert updated_question.correct_answers == 1

    @pytest.mark.asyncio
    async def test_submit_answer_incorrect(self, db_session: AsyncSession):
        """测试提交错误答案"""
        user = await PointsService.get_or_create_user(db_session, "0xwrong_user")
        await db_session.commit()

        question = await QuizService.create_question(
            db=db_session,
            question_text="测试题目",
            option_a="正确答案",
            option_b="错误答案",
            correct_answer="A",
            difficulty=QuestionDifficulty.EASY,
            reward_points=20
        )
        await db_session.commit()

        # 提交错误答案
        result = await QuizService.submit_answer(
            db=db_session,
            user_id=user.id,
            question_id=question.id,
            user_answer="B",
            answer_time=10
        )
        await db_session.commit()

        assert result["is_correct"] is False
        assert result["correct_answer"] == "A"
        assert result["points_earned"] == 0

    @pytest.mark.asyncio
    async def test_daily_limit(self, db_session: AsyncSession):
        """测试每日答题次数限制"""
        user = await PointsService.get_or_create_user(db_session, "0xlimit_user")
        await db_session.commit()

        # 创建5道题目
        questions = []
        for i in range(5):
            q = await QuizService.create_question(
                db=db_session,
                question_text=f"限制测试题目{i+1}",
                option_a="选项A",
                option_b="选项B",
                correct_answer="A",
                difficulty=QuestionDifficulty.EASY,
                reward_points=10
            )
            questions.append(q)
        await db_session.commit()

        # 答完5题
        for i in range(5):
            await QuizService.submit_answer(
                db=db_session,
                user_id=user.id,
                question_id=questions[i].id,
                user_answer="A"
            )
        await db_session.commit()

        # 检查限制
        can_answer, remaining = await QuizService.check_daily_limit(
            db=db_session,
            user_id=user.id
        )

        assert can_answer is False
        assert remaining == 0

        # 尝试答第6题应该失败
        extra_question = await QuizService.create_question(
            db=db_session,
            question_text="第6题",
            option_a="选项A",
            option_b="选项B",
            correct_answer="A",
            difficulty=QuestionDifficulty.EASY,
            reward_points=10
        )
        await db_session.commit()

        with pytest.raises(ValueError, match="今日答题次数已用完"):
            await QuizService.submit_answer(
                db=db_session,
                user_id=user.id,
                question_id=extra_question.id,
                user_answer="A"
            )

    @pytest.mark.asyncio
    async def test_get_daily_session(self, db_session: AsyncSession):
        """测试获取每日会话"""
        user = await PointsService.get_or_create_user(db_session, "0xsession_user")
        await db_session.commit()

        # 首次获取会话（自动创建）
        session = await QuizService.get_daily_session(
            db=db_session,
            user_id=user.id
        )
        await db_session.commit()

        assert session is not None
        assert session.user_id == user.id
        assert session.session_date == date.today()
        assert session.questions_answered == 0
        assert session.correct_count == 0

        # 再次获取应返回同一会话
        session2 = await QuizService.get_daily_session(
            db=db_session,
            user_id=user.id
        )

        assert session2.id == session.id


class TestQuizQueries:
    """查询功能测试"""

    @pytest.mark.asyncio
    async def test_get_user_answers(self, db_session: AsyncSession):
        """测试获取用户答题记录"""
        user = await PointsService.get_or_create_user(db_session, "0xrecord_user")
        await db_session.commit()

        # 创建题目并答题
        for i in range(3):
            question = await QuizService.create_question(
                db=db_session,
                question_text=f"记录测试题目{i+1}",
                option_a="选项A",
                option_b="选项B",
                correct_answer="A",
                difficulty=QuestionDifficulty.EASY,
                reward_points=10
            )
            await db_session.commit()

            await QuizService.submit_answer(
                db=db_session,
                user_id=user.id,
                question_id=question.id,
                user_answer="A" if i < 2 else "B"  # 前2题正确，第3题错误
            )
        await db_session.commit()

        # 获取所有记录
        all_answers, total = await QuizService.get_user_answers(
            db=db_session,
            user_id=user.id,
            page=1,
            page_size=10
        )
        assert total == 3
        assert len(all_answers) == 3

        # 只获取正确的记录
        correct_answers, correct_total = await QuizService.get_user_answers(
            db=db_session,
            user_id=user.id,
            is_correct=True,
            page=1,
            page_size=10
        )
        assert correct_total == 2


class TestQuizStatistics:
    """统计功能测试"""

    @pytest.mark.asyncio
    async def test_quiz_statistics(self, db_session: AsyncSession):
        """测试用户答题统计"""
        user = await PointsService.get_or_create_user(db_session, "0xstats_user")
        await db_session.commit()

        # 创建题目并答题
        for i in range(5):
            question = await QuizService.create_question(
                db=db_session,
                question_text=f"统计测试题目{i+1}",
                option_a="选项A",
                option_b="选项B",
                correct_answer="A",
                difficulty=QuestionDifficulty.EASY,
                reward_points=10
            )
            await db_session.commit()

            await QuizService.submit_answer(
                db=db_session,
                user_id=user.id,
                question_id=question.id,
                user_answer="A" if i < 3 else "B"  # 前3题正确，后2题错误
            )
        await db_session.commit()

        # 获取统计
        stats = await QuizService.get_quiz_statistics(db_session, user.id)

        assert stats["user_id"] == user.id
        assert stats["total_questions_answered"] == 5
        assert stats["total_correct_answers"] == 3
        assert stats["overall_accuracy_rate"] == 60.0
        assert stats["total_points_earned"] == 30  # 3题 × 10分
        assert stats["completed_sessions"] == 1  # 答完5题，完成1个会话

    @pytest.mark.asyncio
    async def test_category_statistics(self, db_session: AsyncSession):
        """测试分类统计"""
        user = await PointsService.get_or_create_user(db_session, "0xcategory_user")
        await db_session.commit()

        # 创建不同分类的题目
        categories = ["Web3", "DeFi", "NFT"]
        for category in categories:
            for i in range(2):
                question = await QuizService.create_question(
                    db=db_session,
                    question_text=f"{category}题目{i+1}",
                    option_a="选项A",
                    option_b="选项B",
                    correct_answer="A",
                    difficulty=QuestionDifficulty.EASY,
                    category=category,
                    reward_points=10
                )
                await db_session.commit()

                await QuizService.submit_answer(
                    db=db_session,
                    user_id=user.id,
                    question_id=question.id,
                    user_answer="A" if i == 0 else "B"  # 每个分类第1题正确，第2题错误
                )
        await db_session.commit()

        # 获取分类统计
        stats = await QuizService.get_category_statistics(db_session, user.id)

        assert len(stats) == 3
        for stat in stats:
            assert stat["total_answered"] == 2
            assert stat["correct_answers"] == 1
            assert stat["accuracy_rate"] == 50.0

    @pytest.mark.asyncio
    async def test_difficulty_statistics(self, db_session: AsyncSession):
        """测试难度统计"""
        user = await PointsService.get_or_create_user(db_session, "0xdifficulty_user")
        await db_session.commit()

        # 创建不同难度的题目
        difficulties = [QuestionDifficulty.EASY, QuestionDifficulty.MEDIUM, QuestionDifficulty.HARD]
        for difficulty in difficulties:
            for i in range(2):
                question = await QuizService.create_question(
                    db=db_session,
                    question_text=f"{difficulty.value}题目{i+1}",
                    option_a="选项A",
                    option_b="选项B",
                    correct_answer="A",
                    difficulty=difficulty,
                    reward_points=10 if difficulty == QuestionDifficulty.EASY else 20
                )
                await db_session.commit()

                await QuizService.submit_answer(
                    db=db_session,
                    user_id=user.id,
                    question_id=question.id,
                    user_answer="A",
                    answer_time=10 + i * 5
                )
        await db_session.commit()

        # 获取难度统计
        stats = await QuizService.get_difficulty_statistics(db_session, user.id)

        assert len(stats) == 3
        for stat in stats:
            assert stat["total_answered"] == 2
            assert stat["correct_answers"] == 2
            assert stat["accuracy_rate"] == 100.0
            assert stat["average_time"] is not None


class TestQuizRanking:
    """排行榜功能测试"""

    @pytest.mark.asyncio
    async def test_quiz_ranking(self, db_session: AsyncSession):
        """测试答题排行榜"""
        # 创建多个用户
        users = []
        for i in range(3):
            user = await PointsService.get_or_create_user(db_session, f"0xrank_user_{i}")
            users.append(user)
        await db_session.commit()

        # 创建题目
        questions = []
        for i in range(5):
            q = await QuizService.create_question(
                db=db_session,
                question_text=f"排行测试题目{i+1}",
                option_a="选项A",
                option_b="选项B",
                correct_answer="A",
                difficulty=QuestionDifficulty.EASY,
                reward_points=10
            )
            questions.append(q)
        await db_session.commit()

        # 用户答题（不同正确率）
        # User 0: 5题全对
        for q in questions:
            await QuizService.submit_answer(
                db=db_session,
                user_id=users[0].id,
                question_id=q.id,
                user_answer="A"
            )

        # User 1: 3题对
        for i, q in enumerate(questions[:3]):
            await QuizService.submit_answer(
                db=db_session,
                user_id=users[1].id,
                question_id=q.id,
                user_answer="A"
            )

        # User 2: 1题对
        await QuizService.submit_answer(
            db=db_session,
            user_id=users[2].id,
            question_id=questions[0].id,
            user_answer="A"
        )

        await db_session.commit()

        # 获取按正确数排行
        ranking = await QuizService.get_quiz_ranking(
            db=db_session,
            ranking_type="correct",
            period="all_time",
            limit=10
        )

        assert len(ranking["data"]) >= 3
        assert ranking["data"][0]["total_correct"] >= ranking["data"][1]["total_correct"]
        assert ranking["data"][1]["total_correct"] >= ranking["data"][2]["total_correct"]

        # 获取特定用户排名
        ranking_with_user = await QuizService.get_quiz_ranking(
            db=db_session,
            ranking_type="correct",
            period="all_time",
            limit=10,
            user_id=users[0].id
        )

        assert ranking_with_user["my_rank"] is not None
        assert ranking_with_user["my_rank"]["user_id"] == users[0].id
