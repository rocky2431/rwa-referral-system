"""create_materialized_view_quiz_leaderboard

Revision ID: 2ea80b4db404
Revises: 0f9389912bab
Create Date: 2025-10-22 01:17:44.788563

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ea80b4db404'
down_revision: Union[str, None] = '0f9389912bab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建问答排行榜物化视图"""

    # 创建物化视图
    op.execute("""
        CREATE MATERIALIZED VIEW mv_quiz_leaderboard AS
        SELECT
            u.id as user_id,
            u.wallet_address,
            u.username,
            u.avatar_url,
            u.level,
            COALESCE(u.total_questions_answered, 0) as total_questions_answered,
            COALESCE(u.correct_answers, 0) as correct_answers,
            CASE
                WHEN COALESCE(u.total_questions_answered, 0) = 0 THEN 0
                ELSE ROUND((COALESCE(u.correct_answers, 0)::decimal / u.total_questions_answered::decimal * 100), 2)
            END as accuracy_rate,
            COALESCE(up.points_from_quiz, 0) as points_from_quiz,
            u.created_at,
            u.last_active_at,
            ROW_NUMBER() OVER (ORDER BY COALESCE(u.correct_answers, 0) DESC, u.id ASC) as rank
        FROM users u
        LEFT JOIN user_points up ON u.id = up.user_id
        WHERE u.is_active = true
          AND (u.is_banned = false OR u.is_banned IS NULL)
          AND COALESCE(u.total_questions_answered, 0) > 0
        ORDER BY COALESCE(u.correct_answers, 0) DESC, u.id ASC;
    """)

    # 创建唯一索引（用于CONCURRENT刷新）
    op.execute("""
        CREATE UNIQUE INDEX idx_mv_quiz_leaderboard_user_id
        ON mv_quiz_leaderboard(user_id);
    """)

    # 创建排名索引
    op.execute("""
        CREATE INDEX idx_mv_quiz_leaderboard_rank
        ON mv_quiz_leaderboard(rank);
    """)

    # 创建正确答案数索引
    op.execute("""
        CREATE INDEX idx_mv_quiz_leaderboard_correct_answers
        ON mv_quiz_leaderboard(correct_answers DESC);
    """)

    # 创建准确率索引
    op.execute("""
        CREATE INDEX idx_mv_quiz_leaderboard_accuracy_rate
        ON mv_quiz_leaderboard(accuracy_rate DESC);
    """)


def downgrade() -> None:
    """删除问答排行榜物化视图"""

    # 删除索引
    op.execute("DROP INDEX IF EXISTS idx_mv_quiz_leaderboard_accuracy_rate;")
    op.execute("DROP INDEX IF EXISTS idx_mv_quiz_leaderboard_correct_answers;")
    op.execute("DROP INDEX IF EXISTS idx_mv_quiz_leaderboard_rank;")
    op.execute("DROP INDEX IF EXISTS idx_mv_quiz_leaderboard_user_id;")

    # 删除物化视图
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_quiz_leaderboard;")
