"""Phase 6: Relax NOT NULL on tasks.backlog_id and tasks.backlog_key

これらのカラムは Phase 7 で完全に DROP される予定だが、それまでの間、
新規タスク作成 (Backlog 連携なし) を可能にするため NOT NULL 制約を解除する。

Revision ID: a1_phase6_relax_task_backlog
Revises: ab30ced40f83
Create Date: 2026-05-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1_phase6_relax_task_backlog'
down_revision: Union[str, None] = 'ab30ced40f83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('tasks', 'backlog_id', nullable=True, schema='team_insight')
    op.alter_column('tasks', 'backlog_key', nullable=True, schema='team_insight')


def downgrade() -> None:
    # 注意: 既存データに NULL があると失敗する。Phase 7 で DROP 済の場合は不要。
    op.alter_column('tasks', 'backlog_key', nullable=False, schema='team_insight')
    op.alter_column('tasks', 'backlog_id', nullable=False, schema='team_insight')
