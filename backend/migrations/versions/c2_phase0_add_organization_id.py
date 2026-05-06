"""Phase 0: Add organization_id (NOT NULL) to projects, teams, tasks

各テナントスコープエンティティに organization_id を追加する。
Phase 7 で全データ削除済 (b3) のため backfill ロジックは保険として残すのみ。

Revision ID: c2_phase0_add_organization_id
Revises: c1_phase0_create_org_tables
Create Date: 2026-05-06 10:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2_phase0_add_organization_id'
down_revision: Union[str, None] = 'c1_phase0_create_org_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_DEFAULT_ORG_SUBQUERY = "(SELECT id FROM team_insight.organizations WHERE slug = 'default' LIMIT 1)"


def _add_org_id_column(table_name: str) -> None:
    """対象テーブルに organization_id を nullable 追加 → backfill → NOT NULL → index 作成"""
    op.add_column(
        table_name,
        sa.Column(
            'organization_id',
            sa.Integer(),
            sa.ForeignKey('team_insight.organizations.id', ondelete='CASCADE'),
            nullable=True,
        ),
        schema='team_insight',
    )

    op.execute(
        f"UPDATE team_insight.{table_name} SET organization_id = {_DEFAULT_ORG_SUBQUERY} "
        f"WHERE organization_id IS NULL"
    )

    op.alter_column(
        table_name,
        'organization_id',
        existing_type=sa.Integer(),
        nullable=False,
        schema='team_insight',
    )

    op.create_index(
        f'idx_{table_name}_org', table_name, ['organization_id'], schema='team_insight'
    )


def _drop_org_id_column(table_name: str) -> None:
    op.drop_index(f'idx_{table_name}_org', table_name=table_name, schema='team_insight')
    op.drop_column(table_name, 'organization_id', schema='team_insight')


def upgrade() -> None:
    _add_org_id_column('projects')
    _add_org_id_column('teams')
    _add_org_id_column('tasks')


def downgrade() -> None:
    _drop_org_id_column('tasks')
    _drop_org_id_column('teams')
    _drop_org_id_column('projects')
