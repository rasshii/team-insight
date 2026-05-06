"""Phase 7: Drop backlog-derived columns from tasks

tasks テーブルから Backlog 連携由来のカラムを完全削除し、既存データも全削除する
(MIGRATION_PLAN.md L60: 全データ削除して新規スタート方針)。

Revision ID: b1_phase7_drop_task_backlog_cols
Revises: a1_phase6_relax_task_backlog
Create Date: 2026-05-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1_phase7_drop_task_backlog_cols'
down_revision: Union[str, None] = 'a1_phase6_relax_task_backlog'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_BACKLOG_TASK_COLUMNS = [
    'backlog_id',
    'backlog_key',
    'status_id',
    'priority',
    'issue_type_id',
    'issue_type_name',
    'milestone_id',
    'milestone_name',
    'category_names',
    'version_names',
]


def upgrade() -> None:
    # 既存タスクは MIGRATION_PLAN.md の方針に従い全削除して新規スタート
    op.execute("DELETE FROM team_insight.tasks")

    # Index/Unique 制約を先に削除 (backlog_key 列削除前に必要)
    op.drop_index('ix_team_insight_tasks_backlog_id', table_name='tasks', schema='team_insight')
    op.drop_constraint('tasks_backlog_key_key', 'tasks', schema='team_insight', type_='unique')

    # Backlog 由来の列を全削除
    for column_name in _BACKLOG_TASK_COLUMNS:
        op.drop_column('tasks', column_name, schema='team_insight')


def downgrade() -> None:
    # 列を nullable=True で再追加 (元のデータは復元できない)
    op.add_column('tasks', sa.Column('version_names', sa.Text(), nullable=True), schema='team_insight')
    op.add_column('tasks', sa.Column('category_names', sa.Text(), nullable=True), schema='team_insight')
    op.add_column('tasks', sa.Column('milestone_name', sa.String(255), nullable=True), schema='team_insight')
    op.add_column('tasks', sa.Column('milestone_id', sa.Integer(), nullable=True), schema='team_insight')
    op.add_column('tasks', sa.Column('issue_type_name', sa.String(100), nullable=True), schema='team_insight')
    op.add_column('tasks', sa.Column('issue_type_id', sa.Integer(), nullable=True), schema='team_insight')
    op.add_column('tasks', sa.Column('priority', sa.Integer(), nullable=True), schema='team_insight')
    op.add_column('tasks', sa.Column('status_id', sa.Integer(), nullable=True), schema='team_insight')
    op.add_column('tasks', sa.Column('backlog_key', sa.String(255), nullable=True), schema='team_insight')
    op.add_column('tasks', sa.Column('backlog_id', sa.Integer(), nullable=True), schema='team_insight')

    # Index/Unique 制約を再作成
    op.create_unique_constraint('tasks_backlog_key_key', 'tasks', ['backlog_key'], schema='team_insight')
    op.create_index('ix_team_insight_tasks_backlog_id', 'tasks', ['backlog_id'], unique=True, schema='team_insight')
