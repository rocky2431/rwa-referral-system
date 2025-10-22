"""create_materialized_view_points_leaderboard

Revision ID: 1d298e2ed413
Revises: 22898c94ef5f
Create Date: 2025-10-22 01:12:07.252874

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d298e2ed413'
down_revision: Union[str, None] = '22898c94ef5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建积分排行榜物化视图"""

    # 创建物化视图
    op.execute("""
        CREATE MATERIALIZED VIEW mv_points_leaderboard AS
        SELECT
            u.id as user_id,
            u.wallet_address,
            u.username,
            u.avatar_url,
            u.total_points,
            u.level,
            u.total_invited,
            u.total_tasks_completed,
            u.total_questions_answered,
            u.correct_answers,
            COALESCE(up.available_points, 0) as available_points,
            COALESCE(up.total_earned, 0) as total_earned,
            COALESCE(up.total_spent, 0) as total_spent,
            COALESCE(up.points_from_referral, 0) as points_from_referral,
            COALESCE(up.points_from_tasks, 0) as points_from_tasks,
            COALESCE(up.points_from_quiz, 0) as points_from_quiz,
            COALESCE(up.points_from_team, 0) as points_from_team,
            COALESCE(up.points_from_purchase, 0) as points_from_purchase,
            u.created_at,
            u.last_active_at,
            ROW_NUMBER() OVER (ORDER BY COALESCE(u.total_points, 0) DESC, u.id ASC) as rank
        FROM users u
        LEFT JOIN user_points up ON u.id = up.user_id
        WHERE u.is_active = true AND (u.is_banned = false OR u.is_banned IS NULL)
        ORDER BY COALESCE(u.total_points, 0) DESC, u.id ASC;
    """)

    # 创建唯一索引（用于CONCURRENT刷新）
    op.execute("""
        CREATE UNIQUE INDEX idx_mv_points_leaderboard_user_id
        ON mv_points_leaderboard(user_id);
    """)

    # 创建排名索引
    op.execute("""
        CREATE INDEX idx_mv_points_leaderboard_rank
        ON mv_points_leaderboard(rank);
    """)

    # 创建积分索引
    op.execute("""
        CREATE INDEX idx_mv_points_leaderboard_total_points
        ON mv_points_leaderboard(total_points DESC);
    """)


def downgrade() -> None:
    """删除积分排行榜物化视图"""

    # 删除索引
    op.execute("DROP INDEX IF EXISTS idx_mv_points_leaderboard_total_points;")
    op.execute("DROP INDEX IF EXISTS idx_mv_points_leaderboard_rank;")
    op.execute("DROP INDEX IF EXISTS idx_mv_points_leaderboard_user_id;")

    # 删除物化视图
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_points_leaderboard;")
