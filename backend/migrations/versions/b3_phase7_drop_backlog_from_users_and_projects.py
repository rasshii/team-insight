"""Phase 7: Drop backlog columns from users and projects, clean up data

users から backlog_id, user_id (Backlog 由来) 列を削除、projects から backlog_id を削除。
非 superuser ユーザーと全 projects (cascade で関連 tasks/team_members 等も) を削除し、
新規スタートに備える (MIGRATION_PLAN.md L60)。

Revision ID: b3_phase7_drop_user_project_backlog
Revises: b2_phase7_drop_oauth_sync_tables
Create Date: 2026-05-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3_phase7_drop_user_proj_backlog'
down_revision: Union[str, None] = 'b2_phase7_drop_oauth_sync_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 関連データを削除 (FK 制約の順序を考慮)
    op.execute("DELETE FROM team_insight.team_members")
    op.execute("DELETE FROM team_insight.teams")
    op.execute("DELETE FROM team_insight.project_members")
    op.execute("DELETE FROM team_insight.report_delivery_history")
    op.execute("DELETE FROM team_insight.report_schedules")
    op.execute("DELETE FROM team_insight.activity_logs")
    op.execute("DELETE FROM team_insight.login_history")
    op.execute("DELETE FROM team_insight.user_preferences")
    op.execute("DELETE FROM team_insight.user_roles")
    op.execute("DELETE FROM team_insight.projects")
    op.execute("DELETE FROM team_insight.users WHERE is_superuser = false")

    # users から Backlog 関連列 (NULL 許容) を削除
    op.drop_index('ix_team_insight_users_backlog_id', table_name='users', schema='team_insight')
    op.drop_index('ix_team_insight_users_user_id', table_name='users', schema='team_insight')
    op.drop_column('users', 'backlog_id', schema='team_insight')
    op.drop_column('users', 'user_id', schema='team_insight')

    # projects から Backlog ID を削除
    op.drop_column('projects', 'backlog_id', schema='team_insight')


def downgrade() -> None:
    op.add_column('projects', sa.Column('backlog_id', sa.Integer(), nullable=True), schema='team_insight')
    op.create_unique_constraint(
        'projects_backlog_id_key', 'projects', ['backlog_id'], schema='team_insight'
    )

    op.add_column('users', sa.Column('user_id', sa.String(), nullable=True), schema='team_insight')
    op.add_column('users', sa.Column('backlog_id', sa.Integer(), nullable=True), schema='team_insight')
    op.create_index('ix_team_insight_users_user_id', 'users', ['user_id'], unique=True, schema='team_insight')
    op.create_index('ix_team_insight_users_backlog_id', 'users', ['backlog_id'], unique=True, schema='team_insight')
