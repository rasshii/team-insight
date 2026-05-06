"""Phase 7: Drop oauth_tokens, oauth_states, sync_histories tables

Backlog OAuth 連携と同期履歴のテーブルを完全削除する (Phase 6 でモデル/コードは
削除済、本マイグレーションでスキーマからも除去)。

Revision ID: b2_phase7_drop_oauth_sync_tables
Revises: b1_phase7_drop_task_backlog_cols
Create Date: 2026-05-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2_phase7_drop_oauth_sync_tables'
down_revision: Union[str, None] = 'b1_phase7_drop_task_backlog_cols'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('sync_histories', schema='team_insight')
    op.drop_table('oauth_tokens', schema='team_insight')
    op.drop_table('oauth_states', schema='team_insight')

    # 関連 ENUM 型を削除
    op.execute("DROP TYPE IF EXISTS team_insight.synctype")
    op.execute("DROP TYPE IF EXISTS team_insight.syncstatus")
    op.execute("DROP TYPE IF EXISTS synctype")
    op.execute("DROP TYPE IF EXISTS syncstatus")


def downgrade() -> None:
    # ENUM 型を再作成
    sync_type_enum = sa.Enum(
        'USER_TASKS', 'PROJECT_TASKS', 'ALL_PROJECTS', 'SINGLE_ISSUE',
        'PROJECT_MEMBERS', 'ALL_USERS', name='synctype'
    )
    sync_status_enum = sa.Enum('STARTED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', name='syncstatus')
    sync_type_enum.create(op.get_bind(), checkfirst=True)
    sync_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'oauth_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('state', sa.String(255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['team_insight.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='team_insight',
    )
    op.create_index('ix_team_insight_oauth_states_id', 'oauth_states', ['id'], schema='team_insight')
    op.create_index('ix_team_insight_oauth_states_state', 'oauth_states', ['state'], unique=True, schema='team_insight')

    op.create_table(
        'oauth_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('backlog_space_key', sa.String(100), nullable=True),
        sa.Column('backlog_user_id', sa.String(100), nullable=True),
        sa.Column('backlog_user_email', sa.String(255), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['team_insight.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='team_insight',
    )
    op.create_index('ix_team_insight_oauth_tokens_id', 'oauth_tokens', ['id'], schema='team_insight')

    op.create_table(
        'sync_histories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('sync_type', sync_type_enum, nullable=False),
        sa.Column('status', sync_status_enum, nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('target_name', sa.String(255), nullable=True),
        sa.Column('items_created', sa.Integer(), nullable=True),
        sa.Column('items_updated', sa.Integer(), nullable=True),
        sa.Column('items_failed', sa.Integer(), nullable=True),
        sa.Column('total_items', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('sync_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['team_insight.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='team_insight',
    )
    op.create_index('ix_team_insight_sync_histories_id', 'sync_histories', ['id'], schema='team_insight')
