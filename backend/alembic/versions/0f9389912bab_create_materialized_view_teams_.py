"""create_materialized_view_teams_leaderboard

Revision ID: 0f9389912bab
Revises: 0f71c5eb411b
Create Date: 2025-10-22 01:17:21.351634

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f9389912bab'
down_revision: Union[str, None] = '0f71c5eb411b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建战队排行榜物化视图"""

    # 创建物化视图
    op.execute("""
        CREATE MATERIALIZED VIEW mv_teams_leaderboard AS
        SELECT
            t.id as team_id,
            t.name as team_name,
            t.description,
            t.logo_url,
            t.captain_id,
            u.wallet_address as captain_wallet_address,
            u.username as captain_username,
            u.avatar_url as captain_avatar_url,
            t.member_count,
            t.active_member_count,
            t.total_points,
            t.level,
            t.experience,
            t.reward_pool,
            t.last_distribution_at,
            t.is_public,
            t.max_members,
            t.created_at,
            t.updated_at,
            ROW_NUMBER() OVER (ORDER BY COALESCE(t.total_points, 0) DESC, t.id ASC) as rank
        FROM teams t
        LEFT JOIN users u ON t.captain_id = u.id
        WHERE t.disbanded_at IS NULL
        ORDER BY COALESCE(t.total_points, 0) DESC, t.id ASC;
    """)

    # 创建唯一索引（用于CONCURRENT刷新）
    op.execute("""
        CREATE UNIQUE INDEX idx_mv_teams_leaderboard_team_id
        ON mv_teams_leaderboard(team_id);
    """)

    # 创建排名索引
    op.execute("""
        CREATE INDEX idx_mv_teams_leaderboard_rank
        ON mv_teams_leaderboard(rank);
    """)

    # 创建积分索引
    op.execute("""
        CREATE INDEX idx_mv_teams_leaderboard_total_points
        ON mv_teams_leaderboard(total_points DESC);
    """)


def downgrade() -> None:
    """删除战队排行榜物化视图"""

    # 删除索引
    op.execute("DROP INDEX IF EXISTS idx_mv_teams_leaderboard_total_points;")
    op.execute("DROP INDEX IF EXISTS idx_mv_teams_leaderboard_rank;")
    op.execute("DROP INDEX IF EXISTS idx_mv_teams_leaderboard_team_id;")

    # 删除物化视图
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_teams_leaderboard;")
